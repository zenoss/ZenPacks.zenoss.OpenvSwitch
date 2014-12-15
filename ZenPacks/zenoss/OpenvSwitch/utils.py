##############################################################################
#
# GPLv2
#
# You should have received a copy of the GNU General Public License
# along with this ZenPack. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import re

from Products.AdvancedQuery import And, Eq
from ZODB.transact import transact

from Products.Zuul.interfaces import ICatalogTool

from Products.ZenUtils.guid.interfaces import IGlobalIdentifier
from collections import deque
import dateutil
import datetime
import functools
import importlib
import pytz
import time

from twisted.internet import reactor
from twisted.internet.error import ConnectionRefusedError, TimeoutError
from twisted.internet.task import deferLater

import logging
LOG = logging.getLogger('zen.OpenvSwitch.utils')


def zenpack_path(path):
    return os.path.join(os.path.dirname(__file__), path)


def zenpack_path(path):
    return os.path.join(os.path.dirname(__file__), path)


def add_local_lib_path():
    '''
    Helper to add the ZenPack's lib directory to sys.path.
    '''
    import site

    # The novaclient library does some elaborate things to figure out
    # what version of itself is installed. These seem to not work in
    # our environment for some reason, so we override that and have
    # it report a dummy version that nobody will look at anyway.
    #
    # So, if you're wondering why novaclient.__version__ is 1.2.3.4.5,
    # this is why.
    os.environ['PBR_VERSION'] = '1.2.3.4.5'

    site.addsitedir(os.path.join(os.path.dirname(__file__), '.'))
    site.addsitedir(os.path.join(os.path.dirname(__file__), 'lib'))

add_local_lib_path()

# The following methods are used to parse strings from SSH commands
# If the code is confusing to you, here is FYI that the coder himself
# is not exactly proud of it himself.
def str_to_dict(original):
    original = original.split('\n')
    # remove '' from head and tail
    if not original[0]:
        del original[0]
    if not original[-1]:
        del original[-1]

    rets = []
    ret = {}
    for orig in original:
        # an empty string as an item
        if not orig:
            rets.append(ret)
            ret = {}
            continue

        if orig.find(':') > -1:           # key-value pair
            pair = orig.split(':', 1)
            ret[pair[0].strip()] = localparser(pair[1].strip())

    # add the last item to rets
    rets.append(ret)

    return rets

def localparser(text):
    text = text.strip()

    if text.find('{') == 0 and text.find('}') == (len(text) - 1):        # dict
        ret = {}
        if text.rindex('}') > text.index('{') + 1:                        # dict not empty
            # we are looking at something like {'x'="y", 'u'="v", 'a'='5'}
            content = text.strip('{}')
            if content.find(', ') > -1:
                clst = content.split(', ')
                for cl in clst:
                    if cl.find('=') > -1:
                        lst = cl.split('=')
                        if lst[1].find('"') > -1:
                            ret[lst[0]] = lst[1].strip('"')
                        elif str.isdigit(lst[1]):
                            ret[lst[0]] = int(lst[1])
                        else:
                            ret[lst[0]] = lst[1]
            elif content.find('=') > -1:
                lst = content.split('=')
                if lst[1].find('"') > -1:
                    ret[lst[0]] = lst[1].strip('"')
                elif str.isdigit(lst[1]):
                    ret[lst[0]] = int(lst[1])
                else:
                    ret[lst[0]] = lst[1]
            else:
                ret = content
    elif text.find('[') == 0 and text.find(']') == (len(text) - 1):        # list
        ret = []
        if (text.rindex(']') > text.index('[') + 1):
            if text.find(', ') > -1:
                ret = text.strip('[]').split(', ')
            else:
                ret.append(text.strip('[]'))
    elif text.find('"') > -1:        # string
        ret = text.strip('"')
    elif str.isdigit(text):
        ret = int(text)
    elif text == 'false':
        ret = False
    else:
        ret = text

    return ret

def bridge_flow_data_to_dict(flow_data_list):
    # convert ovs-ofctl dump-flows data to dict
    # it looks something like this:
    # cookie=0x0, duration=1167.96s, table=0, n_packets=0, n_bytes=0,
    # idle_age=1167, ip,in_port=1,nw_src=192.168.56.121 actions=output:3,output:4

    # here we collect table number; priority; action, bytes, and packets

    flow_dct = {}
    for entry in flow_data_list:
        if entry.find('NXST_AGGREGATE') > -1:
            dct = {}
            statlst = entry[entry.index(':') + 1:].strip().split(' ')
            for stat in statlst:
                if stat.find('packet_count=') > -1:
                    dct['packet_count'] = int(stat[stat.index('=') + 1:])
                elif stat.find('byte_count=') > -1:
                    dct['byte_count'] = int(stat[stat.index('=') + 1:])
                elif stat.find('flow_count=') > -1:
                    dct['flow_count'] = int(stat[stat.index('=') + 1:])

            flow_dct[bridge_name].append(dct)

        elif entry.find('cookie=') > -1:
            # flow table entries
            dct = {}
            statlst = entry.strip().split(',')
            for stat in statlst:
                # skip these
                if  stat.find('cookie=') > -1 or \
                    stat.find('duration=') > -1 or \
                    stat.find('idle_age=') > -1:
                    continue

                # no ', ' separating from action ???
                elif stat.find(' actions=') > -1:
                    statlstlst = stat.strip().split(' ')
                    keyname = statlstlst[0][:statlstlst[0].index('=')]
                    dct[keyname] = statlstlst[0][statlstlst[0].index('=') + 1:]

                    dct['actions'] = statlstlst[1][statlstlst[1].index('=') + 1:]
                    for i in range(statlst.index(stat) + 1, len(statlst)):
                        dct['actions'] += ',' + statlst[i]
                    break
                elif stat.find('priority=') > -1:
                    dct['priority'] = int(stat[stat.index('=') + 1:].strip())
                elif stat.find('table=') > -1:
                    dct['table'] = int(stat[stat.index('=') + 1:].strip())
                elif stat.find('n_bytes=') > -1:
                    dct['bytes'] = int(stat[stat.index('=') + 1:].strip())
                elif stat.find('n_packets=') > -1:
                    dct['packets'] = int(stat[stat.index('=') + 1:].strip())
                elif stat.find('in_port=') > -1:
                    dct['in_port'] = int(stat[stat.index('=') + 1:])
                elif stat.find('nw_src=') > -1:
                    dct['nw_src'] = stat[stat.index('=') + 1:].strip()
                elif stat.find('nw_dst=') > -1:
                    dct['nw_dst'] = stat[stat.index('=') + 1:].strip()
                elif stat.find('=') == -1 and len(stat.strip()) > 0:
                    dct['proto'] = stat.strip()

            flow_dct[bridge_name].append(dct)

        elif  entry.find('NXST_FLOW') == -1 and \
                        entry.find('cookie=') == -1:
            bridge_name = entry.strip()
            flow_dct[bridge_name] = []

    return flow_dct
