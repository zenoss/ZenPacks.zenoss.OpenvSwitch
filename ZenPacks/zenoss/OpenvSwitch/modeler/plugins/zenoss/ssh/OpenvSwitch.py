##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
LOG = logging.getLogger('zen.OpenvSwitch')

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap

from ZenPacks.zenoss.OpenvSwitch.utils import add_local_lib_path, \
                                              str_to_dict, \
                                              bridge_flow_data_to_dict, \
                                              create_fuid
add_local_lib_path()


class OpenvSwitch(CommandPlugin):
    command = (
        '('
        '/usr/bin/sudo ovs-vsctl --columns=_uuid,statistics,external_ids,db_version,ovs_version,bridges list Open_vSwitch ; '
        'echo "__COMMAND__" ; '
        '/usr/bin/sudo ovs-vsctl --columns=_uuid,name,external_ids,ports,datapath_id,datapath_type,flood_vlans,flow_tables,status list bridge ; '
        'echo "__COMMAND__" ; '
        '/usr/bin/sudo ovs-vsctl --columns=_uuid,name,mac,lacp,external_ids,interfaces,tag,trunks,vlan_mode,status,statistics list port ; '
        'echo "__COMMAND__" ; '
        'for x in $(/usr/bin/sudo ovs-vsctl --columns=name list bridge); do if [ $x != \'name\' ] && [ $x != \':\' ] ; then  echo $x; /usr/bin/sudo ovs-ofctl dump-flows $x; fi; done ; '
        'echo "__COMMAND__" ; '
        '/usr/bin/sudo ovs-vsctl list interface ; '
        ')'
    )

    def process(self, device, results, unused):
        LOG.info('Processing plugin results on %s', device.id)

        if results.find('command not found') > -1:
            LOG.error('ovs-vsctl not found on %s', device.id)
            return None

        if  results.find('database connection failed') > -1 and \
            results.find('No such file or directory') > -1:
            LOG.error('service openvswitch not running on %s', device.id)
            return None

        command_strings = results.split('__COMMAND__')

        # sanity check first
        # no need for the 1st command_string
        for i in range(1, len(command_strings)):
            if len(command_strings[i]) < 4:
                LOG.error('No meaningful data found on %s', device.id)
                return None

        # OVS as device. there should be only one OVS DB entry per ovs host
        ovsdata = str_to_dict(command_strings[0])[0]
        brdgs = str_to_dict(command_strings[1])
        prts = str_to_dict(command_strings[2])
        flws = bridge_flow_data_to_dict(command_strings[3].split('\n')[1:-1])
        ifaces = str_to_dict(command_strings[4])
        if ovsdata:
            LOG.info('Found OVS DB on %s for user %s', device.id, device.zCommandUsername)
        else:
            LOG.info('No OVS DB found on %s for user %s', device.id, device.zCommandUsername)
            return None

        if len(brdgs) > 0:
            LOG.info('Found %d bridges on %s for user %s', len(brdgs), device.id, device.zCommandUsername)
        else:
            LOG.info('No bridge found on %s for user %s', device.id, device.zCommandUsername)

        if len(prts) > 0:
            LOG.info('Found %d ports on %s for user %s', len(prts), device.id, device.zCommandUsername)
        else:
            LOG.info('No port found on %s for user %s', device.id, device.zCommandUsername)

        if len(flws) > 0:
            LOG.info('Found %d flows on %s for user %s', len(flws), device.id, device.zCommandUsername)
        else:
            LOG.info('No flow found on %s for user %s', device.id, device.zCommandUsername)

        if len(ifaces) > 0:
            LOG.info('Found %d interfaces on %s for user %s', len(ifaces), device.id, device.zCommandUsername)
        else:
            LOG.info('No interface found on %s for user %s', device.id, device.zCommandUsername)

        maps = []

        if 'name' in ovsdata:
            ovs_name = ovsdata['name']
        else:
            ovs_name = 'Open_vSwitch'
        ovsObjMap = self.objectMap({
            'ovsTitle':          ovs_name,
            'ovsId':             ovsdata['_uuid'],
            'ovsDBVersion':      ovsdata['db_version'],
            'ovsVersion':        ovsdata['ovs_version'],
            'numberBridges':     len(brdgs),
            'numberPorts':       len(prts),
            'numberFlows':       len(flws),
            'numberInterfaces':  len(ifaces),
            })

        maps.append(ovsObjMap)

        # bridges
        bridges = []
        rel_maps = []
        classname = 'bridges'
        for brdg in brdgs:
            bridge_id = 'bridge-{0}'.format(brdg['_uuid'])
            bridges.append(ObjectMap(
                data={
                'id':       bridge_id,
                'title':    brdg['name'],
                'bridgeId': brdg['_uuid'],
                }))

            # ports
            ports = self.getPortRelMap(prts, ifaces,
                                       classname + \
                                       '/%s' % bridge_id, brdg['ports'])
            # flows
            flows = self.getFlowRelMap(flws,
                                       classname + \
                                       '/%s' % bridge_id, brdg['name'])

            # excluding empty RelationshipMaps
            if ports and len(ports) > 0 and len(ports[0].maps) > 0:
                rel_maps.extend(ports)
            if flows and len(flows.maps) > 0:
                rel_maps.append(flows)

        maps.append(RelationshipMap(
            relname=classname,
            modname='ZenPacks.zenoss.OpenvSwitch.Bridge',
            objmaps=bridges))
        maps.extend(rel_maps)

        return maps


    def getPortRelMap(self, prts, ifaces, compname, bridgeports):
        # ports
        rel_maps = []
        ports = []
        classname = 'ports'
        for port in prts:
            if port['_uuid'] not in bridgeports:
                continue

            port_id = 'port-{0}'.format(port['_uuid'])
            ports.append(ObjectMap(
                data={
                'id':         port_id,
                'title':      'Port-' + port['name'],
                'portId':     port['_uuid'],
                'tag_':       port['tag'],
                }))

            interfaces = self.getInterfaceRelMap(ifaces,
                     '%s/%s/%s' % (compname, classname, port_id), port['interfaces'])

            rel_maps.append(interfaces)

        return [RelationshipMap(
            compname=compname,
            relname=classname,
            modname='ZenPacks.zenoss.OpenvSwitch.Port',
            objmaps=ports)] + rel_maps


    def getFlowRelMap(self, flws, compname, bridgename):
        # flows
        flows = []
        classname = 'flows'
        for key in flws.keys():
            # key is the bridge name
            if key != bridgename:
                continue

            for flow in flws[key]:
                priority = None
                if 'priority' in flow:
                    priority = flow['priority']
                protoname = None
                if 'proto' in flow:
                    protoname = flow['proto']
                inport = None
                if 'in_port' in flow:
                    inport = flow['in_port']
                nwsrc = None
                if 'nw_src' in flow:
                    nwsrc = flow['nw_src']
                nwdst = None
                if 'nw_dst' in flow:
                    nwdst = flow['nw_dst']

                fuid = create_fuid(key, flow)
                flows.append(ObjectMap(
                    data={
                        'id':       'flow-{0}'.format(fuid),
                        'flowId':    fuid,
                        'title':    'flow-{0}'.format(fuid),
                        'table':    flow['table'],
                        'priority': priority,
                        'protocol': protoname,
                        'inport':   inport,
                        'nwsrc':    nwsrc,
                        'nwdst':    nwdst,
                        'action':   flow['actions'].upper(),
                    }))


        return RelationshipMap(
            compname=compname,
            relname=classname,
            modname='ZenPacks.zenoss.OpenvSwitch.Flow',
            objmaps=flows)

    def getInterfaceRelMap(self, ifaces, compname, pinterfaces):
        # interfaces
        interfaces = []
        classname = 'interfaces'
        for iface in ifaces:
            if iface['_uuid'] not in pinterfaces:
                continue

            if iface['link_speed'] == 10000000000:
                lspd = '10 Gb'
            elif iface['link_speed'] == 1000000000:
                lspd = '1 Gb'
            elif iface['link_speed'] == 100000000:
                lspd = '100 Mb'
            else:
                lspd = 'unknown'
            imac = ''
            if iface['mac_in_use']:
                imac = iface['mac_in_use'].upper()
            amac = ''
            if 'attached-mac' in iface['external_ids']:
                amac = iface['external_ids']['attached-mac'].upper()
            interfaces.append(ObjectMap(
                data={
                'id':          'interface-{0}'.format(iface['_uuid']),
                'title':       'Interface-' + iface['name'],
                'interfaceId': iface['_uuid'],
                'type_':       iface['type'],
                'mac':         imac,
                'amac':        amac,
                'ofport':      iface['ofport'],
                'lstate':      iface['link_state'].upper(),
                'astate':      iface['admin_state'].upper(),
                'lspeed':      lspd,
                'mtu':         iface['mtu'],
                'duplex':      iface['duplex'],
                }))


        return RelationshipMap(
            compname=compname,
            relname=classname,
            modname='ZenPacks.zenoss.OpenvSwitch.Interface',
            objmaps=interfaces)
