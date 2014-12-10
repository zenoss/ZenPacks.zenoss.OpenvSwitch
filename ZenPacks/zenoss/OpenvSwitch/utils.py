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


