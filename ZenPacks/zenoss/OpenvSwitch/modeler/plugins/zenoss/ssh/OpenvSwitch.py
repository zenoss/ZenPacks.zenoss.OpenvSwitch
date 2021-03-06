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
        '/usr/bin/sudo ovs-vsctl --columns=_uuid,statistics,external_ids,db_version,ovs_version,bridges list Open_vSwitch 2>&1; '
        'echo "__COMMAND__" ; '
        '/usr/bin/sudo ovs-vsctl --columns=_uuid,name,external_ids,ports,datapath_id,datapath_type,flood_vlans,flow_tables,status list bridge 2>&1; '
        'echo "__COMMAND__" ; '
        '/usr/bin/sudo ovs-vsctl --columns=_uuid,name,mac,lacp,external_ids,interfaces,tag,trunks,vlan_mode,status,statistics list port 2>&1; '
        'echo "__COMMAND__" ; '
        'for x in $(/usr/bin/sudo ovs-vsctl --columns=name list bridge); do if [ $x != \'name\' ] && [ $x != \':\' ] ; then x=$(echo $x | tr -d \'"\' ); echo $x; /usr/bin/sudo ovs-ofctl dump-flows $x; fi; done 2>&1; '
        'echo "__COMMAND__" ; '
        '/usr/bin/sudo ovs-vsctl list interface 2>&1; '
        ')'
    )

    bad_ifaces = 0

    def process(self, device, results, unused):
        LOG.info('Processing plugin results on %s', device.id)

        if results.find('command not found') > -1:
            LOG.error('ovs-vsctl not found on %s', device.id)
            return None

        if  'database connection failed' in results or \
                'No such file or directory' in results or \
                    'connection attempt failed (Connection refused)' in results:
            LOG.info('service openvswitch or one of its daemons not running on %s', device.id)
            return None

        command_strings = results.split('__COMMAND__')

        # sanity check first
        # no need for the 1st command_string
        if len(max(command_strings)) < 4:
            LOG.error('No meaningful data found on %s', device.id)
            return None

        # OVS as device. there should be only one OVS DB entry per ovs host
        ovsdata = str_to_dict(command_strings[0])[0]

        # this happens on CentOS 7 if Zenoss user is not allowed
        # to run SSH remotely
        if 'sudo' in ovsdata and \
                ('sorry, you must have a tty to run sudo' in ovsdata['sudo'] or \
                         'no tty present and no askpass program specified' in ovsdata['sudo']):
            LOG.error(
                'Zenoss user (%s) could not run SSH commands for the' + \
                ' device (%s) at (%s)' + \
                ' remotely. Please consult Zenoss Wiki page for OpenvSwitch ZenPack',
                device.zCommandUsername, device.id, device.manageIp)
            return None

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
            LOG.info('Found %d BRIDGES on %s for user %s', len(brdgs), device.id, device.zCommandUsername)
        else:
            LOG.info('No BRIDGE found on %s for user %s', device.id, device.zCommandUsername)

        if len(prts) > 0:
            LOG.info('Found %d PORTS on %s for user %s', len(prts), device.id, device.zCommandUsername)
        else:
            LOG.info('No PORT found on %s for user %s', device.id, device.zCommandUsername)

        flowcount = 0
        for brdg in flws.keys():
            flowcount += len(flws[brdg])
        if flowcount > 0:
            LOG.info('Found %d FLOWS on %s for user %s', flowcount, device.id, device.zCommandUsername)
        else:
            LOG.info('No FLOW found on %s for user %s', device.id, device.zCommandUsername)

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
            'numberFlows':       flowcount,
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

        if len(ifaces) - self.bad_ifaces > 0:
            LOG.info('Found %d INTERFACES on %s for user %s',
                      len(ifaces) - self.bad_ifaces,
                      device.id,
                      device.zCommandUsername)
        else:
            LOG.info('No INTERFACE found on %s for user %s',
                      device.id,
                      device.zCommandUsername)

        maps.append(RelationshipMap(
            relname=classname,
            modname='ZenPacks.zenoss.OpenvSwitch.Bridge',
            objmaps=bridges))
        maps.extend(rel_maps)

        # in case we have bad interfaces
        # we need to adjust the values displayed on device overview page
        if self.bad_ifaces > 0:
            modifiedOvsObjMap = self.objectMap({
                'ovsTitle':          ovs_name,
                'ovsId':             ovsdata['_uuid'],
                'numberInterfaces':  len(ifaces) - self.bad_ifaces,
            })

            maps.append(modifiedOvsObjMap)

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

            # taking care of possible very bad items
            if iface['link_state'] == 'up' and not iface['mac_in_use']:
                self.bad_ifaces += 1
                continue

            if  not iface['link_state'] and \
                    not iface['admin_state'] and \
                    not iface['mac_in_use'] and \
                    iface['ofport'] == '-1':
                self.bad_ifaces += 1
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
            astate = 'UNKNOWN'
            if iface['admin_state']:
                astate = iface['admin_state'].upper()
            lstate = 'UNKNOWN'
            if iface['link_state']:
                lstate = iface['link_state'].upper()

            interfaces.append(ObjectMap(
                data={
                    'id':          'interface-{0}'.format(iface['_uuid']),
                    'title':       'Interface-' + iface['name'],
                    'interfaceId': iface['_uuid'],
                    'type_':       iface['type'],
                    'mac':         imac,
                    'amac':        amac,
                    'ofport':      iface['ofport'],
                    'lstate':      lstate,
                    'astate':      astate,
                    'lspeed':      lspd,
                    'mtu':         iface['mtu'],
                    'duplex':      iface['duplex'],
                    }))


        return RelationshipMap(
            compname=compname,
            relname=classname,
            modname='ZenPacks.zenoss.OpenvSwitch.Interface',
            objmaps=interfaces)
