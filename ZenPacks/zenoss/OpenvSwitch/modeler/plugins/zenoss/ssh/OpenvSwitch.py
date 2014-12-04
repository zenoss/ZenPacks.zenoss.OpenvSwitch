##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
LOG = logging.getLogger('zen.OpenvSwitch')

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap

from ZenPacks.zenoss.OpenvSwitch.utils import add_local_lib_path, str_to_dict
add_local_lib_path()


class OpenvSwitch(CommandPlugin):
    command = (
        '('
        'ovs-vsctl --columns=_uuid,statistics,external_ids,db_version,ovs_version,bridges list Open_vSwitch ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl --columns=_uuid,name,external_ids,ports,datapath_id,datapath_type,flood_vlans,flow_tables,status list bridge ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl --columns=_uuid,name,mac,lacp,external_ids,interfaces,tag,trunks,vlan_mode,status,statistics list port ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl list interface ; '
        'echo "__COMMAND__" ; '
        ')'
        )

    def process(self, device, results, unused):
        LOG.info('Processing plugin results on %s', device.id)

        command_strings = results.split('__COMMAND__')

        # OVSs
        ovss = str_to_dict(command_strings[0])
        ovses = []
        for ovs in ovss:
            if 'name' in ovs:
                ovs_name = ovs['name']
            else:
                ovs_name = 'Open_vSwitch'
            ovses.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.OVS',
                data={
                'id':          'ovs-{0}'.format(ovs['_uuid']),
                'title':       ovs_name,
                'ovsId':       ovs['_uuid'],
                'DB_version':  ovs['db_version'],
                'OVS_version': ovs['ovs_version'],
                }))


        if len(ovses) > 0:
            LOG.info('Found %d ovses on %s', len(ovses), device.id)
        else:
            LOG.info('No ovs found on %s', device.id)
            return None

        # bridges
        brdgs = str_to_dict(command_strings[1])
        bridges = []
        for brdg in brdgs:
            ovsid = [ovs['_uuid'] for ovs in ovss \
                    if brdg['_uuid'] in ovs['bridges']]
            bridges.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Bridge',
                data={
                'id':       'bridge-{0}'.format(brdg['_uuid']),
                'title':    brdg['name'],
                'bridgeId': brdg['_uuid'],
                'set_ovs':  'ovs-{0}'.format(ovsid[0]),
                }))


        if len(bridges) > 0:
            LOG.info('Found %d bridges on %s', len(bridges), device.id)
        else:
            LOG.info('No bridge found on %s', device.id)
            return None

        # ports
        prts = str_to_dict(command_strings[2])
        ports = []
        for port in prts:
            brdgId = [brdg['_uuid'] for brdg in brdgs \
                       if port['_uuid'] in brdg['ports']]
            ports.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Port',
                data={
                'id':         'port-{0}'.format(port['_uuid']),
                'title':      port['name'],
                'portId':     port['_uuid'],
                'tag_':       port['tag'],
                'set_bridge': 'bridge-{0}'.format(brdgId[0]),
                }))


        if len(ports) > 0:
            LOG.info('Found %d ports on %s', len(ports), device.id)
        else:
            LOG.info('No port found on %s', device.id)
            return None

        # interfaces
        ifaces = str_to_dict(command_strings[3])
        interfaces = []
        for iface in ifaces:
            if iface['link_speed'] == 10000000000:
                lspd = '10 Gb'
            elif iface['link_speed'] == 1000000000:
                lspd = '1 Gb'
            elif iface['link_speed'] == 100000000:
                lspd = '100 Mb'
            else:
                lspd = 'unknown'
            amac = ''
            if 'attached-mac' in iface['external_ids']:
                amac = iface['external_ids']['attached-mac'].upper()
            prtid = [prt['_uuid'] for prt in prts \
                    if iface['_uuid'] in prt['interfaces']]
            interfaces.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Interface',
                data={
                'id':          'interface-{0}'.format(iface['_uuid']),
                'title':       iface['name'],
                'interfaceId': iface['_uuid'],
                'type_':       iface['type'],
                'mac':         iface['mac_in_use'].upper(),
                'amac':        amac,
                'lstate':      iface['link_state'].upper(),
                'astate':      iface['admin_state'].upper(),
                'lspeed':      lspd,
                'mtu':         iface['mtu'],
                'duplex':      iface['duplex'],
                'set_port':    'port-{0}'.format(prtid[0]),
                }))


        if len(interfaces) > 0:
            LOG.info('Found %d interfaces on %s', len(interfaces), device.id)
        else:
            LOG.info('No interface found on %s', device.id)
            return None

        objmaps = {
            'ovses': ovses,
            'bridges': bridges,
            'ports': ports,
            'interfaces': interfaces,
            }

        # Apply the objmaps in the right order.
        componentsMap = RelationshipMap(relname='components')
        for i in ('ovses', 'bridges', 'ports', 'interfaces',):
            for objmap in objmaps[i]:
                componentsMap.append(objmap)

        return componentsMap
