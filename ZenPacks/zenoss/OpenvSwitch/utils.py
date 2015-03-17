##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os
import time
from datetime import datetime
import uuid

import logging
LOG = logging.getLogger('zen.OpenvSwitch.utils')


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

def bridge_stats_data_to_dict(bridge_stats):
    # convert ovs-ofctl dump-aggregate data to dict
    flowstats_dct = {}
    bridgestatslst = bridge_stats.split('\n')
    name = ''                                      # used to identify stats
    for bstat in bridgestatslst:
        if len(bstat) == 0:
            continue

        elif bstat.find('name') > -1:              # bridge name
            bridgename = bstat[bstat.index(':') + 1:].strip()
            if bridgename not in flowstats_dct:    # a new bridge name
                flowstats_dct[bridgename] = {}
                name = bridgename                  # update bridge name
        elif bstat.find('_uuid') > -1:             # bridge uuid
            flowstats_dct[name]['uuid'] = bstat[bstat.index(':') + 1:].strip()
        elif bstat.strip() in flowstats_dct:       # update bridge name
            name = bstat.strip()
        elif bstat.find('NXST_AGGREGATE') > -1:    # aggregate data
            countlst = bstat[bstat.index(':') + 1:].split(' ')
            for count in countlst:
                if len(count.strip()) == 0:
                    continue

                flowstats_dct[name][count.split('=')[0]] = int(count.split('=')[1])
        else:                                      # nothing interesting to see
            continue

    return flowstats_dct

def create_fuid(bridgename, flowdict):
    # flowdict in input parameter list is a dict
    # by default, flow does not have a unique ID
    # use info provided by flowdict to create a unique, static flow id
    # but see this: http://lwn.net/Articles/629741/
    # openvswitch: Introduce 128-bit unique flow identifiers.
    # FUID coming soon, maybe?

    if not bridgename:
        return None

    funame = bridgename

    if 'priority' in flowdict:
        funame += str(flowdict['priority'])
    if 'table' in flowdict:
        funame += str(flowdict['table'])
    if 'proto' in flowdict:
        funame += str(flowdict['proto'])
    if 'in_port' in flowdict:
        funame += str(flowdict['in_port'])
    if 'nw_proto' in flowdict:
        funame += str(flowdict['nw_proto'])
    if 'nw_src' in flowdict:
        funame += str(flowdict['nw_src'])
    if 'nw_dst' in flowdict:
        funame += str(flowdict['nw_dst'])
    if 'ipv6_src' in flowdict:
        funame += str(flowdict['ipv6_src'])
    if 'ipv6_dst' in flowdict:
        funame += str(flowdict['ipv6_dst'])
    if 'dl_vlan' in flowdict:
        funame += str(flowdict['dl_vlan'])               # data link layer VLAN
    if 'dl_vlan_pcp' in flowdict:
        funame += str(flowdict['dl_vlan_pcp'])           # data link layer VLAN Priority Code Point
    if 'dl_src' in flowdict:
        funame += str(flowdict['dl_src'])                # data link layer source
    if 'dl_dst' in flowdict:
        funame += str(flowdict['dl_dst'])                # data link layer destination
    if 'dl_type' in flowdict:
        funame += str(flowdict['dl_type'])               # data link layer type
    if 'metadata' in flowdict:
        funame += str(flowdict['metadata'])              # metadata
    if 'vlan_tci' in flowdict:
        funame += str(flowdict['vlan_tci'])              # VLAN TCI
    if 'icmp_code' in flowdict:
        funame += str(flowdict['icmp_code'])
    if 'mpls_label' in flowdict:
        funame += str(flowdict['mpls_label'])
    if 'actions' in flowdict:
        funame += str(flowdict['actions'])

    return str(uuid.uuid5(uuid.NAMESPACE_OID, funame))

def get_ovsdb_records(logs, component, cycleTime, timedelta):
    # get unique records in terms of summary
    def in_records(summary, records):
        return len([record for record in records if summary in record.values()]) > 0

    utcoffset = datetime.utcnow() - datetime.now()
    zenossepoch = int(time.time()) + int(round(utcoffset.total_seconds()))
    recordpattern1 = '%Y-%m-%d %H:%M:%S'           # for '2015-03-10 08:35:31'
    recordpattern2 = '%Y-%m-%d %H:%M:%S.%f'        # for '2015-03-10 08:35:31.xxx'

    records = []
    rcrd_index = len(logs)
    while rcrd_index > 0:

        item = {}
        rcrd_title = 'record ' + str(rcrd_index)
        rcrd = logs[rcrd_title]
        rcrd_index -= 1

        marker = len(rcrd)
        if marker < 25:
            # timestamp only, nothing else
            continue

        # component: bridge name
        if component not in rcrd:
            # this record has nothing to do with this bridge
            continue

        if '"ovs-vsctl:' in rcrd:
            marker = min(rcrd.index('"ovs-vsctl:') - 1, len(rcrd))

        # record time is always UTC time
        timestr = rcrd[:marker]
        try:
            recordepoch = int(time.mktime(time.strptime(timestr, recordpattern1)))
        except ValueError:
            recordepoch = int(time.mktime(time.strptime(timestr, recordpattern2)))

        # we only consider records within cycletime
        if zenossepoch - cycleTime > (recordepoch + timedelta):
            continue

        summary = ''
        if 'add-br' in rcrd:
            name = rcrd[rcrd.index('add-') + len('add-br '):]
            summary = 'add bridge: ' + name
        elif 'del-br' in rcrd:
            name = rcrd[rcrd.index('del-') + len('del-br '):]
            summary = 'del bridge: ' + name
        elif 'add-port' in rcrd:
            name = rcrd[rcrd.index('add-') + len('add-port '):]
            if ' -- set Interface' in name:
                name = name[:name.index(' -- set Interface')]
            summary = 'add port: ' + name
        elif 'del-port' in rcrd:
            name = rcrd[rcrd.index('del-') + len('del-port '):]
            summary = 'del port: ' + name

        # have we seen this summary before?
        if summary and not in_records(summary, records):
            item['name'] = name
            item['summary'] = summary
            item['time'] = timestr
            records.append(item)

    return records
