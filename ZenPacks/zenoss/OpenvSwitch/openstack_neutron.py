##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from zope.interface import implements

from Products.Zuul.interfaces import ICatalogTool
from ZenPacks.zenoss.OpenStackInfrastructure.interfaces \
    import INeutronImplementationPlugin
from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
    import BaseNeutronImplementationPlugin, split_list

from ZenPacks.zenoss.OpenvSwitch.Port import Port
from ZenPacks.zenoss.OpenvSwitch.Interface import Interface


class OpenvSwitchNeutronImplementationPlugin(BaseNeutronImplementationPlugin):
    implements(INeutronImplementationPlugin)

    @classmethod
    def ini_required(cls):
        return []

    @classmethod
    def ini_process(cls, filename, section_name, option_name, value):
        # The management server IPs are specified as a comma-separated list.
        # we transform this to an actual list so that we can refer to it that
        # way elsewhere.
        if option_name == 'management_server_ips':
            return split_list(value)

        return value

    def getPortIntegrationKeys(self, osi_port):
        keys = []
        # Use short name from OSI port ID as a clue to find the port on
        # OVS side. Use that OVS port to determine the OVS host IP
        short_osi_port_id = osi_port.id[5:16]

        # there could be multiple OVS devices, and we don't yet know
        # which device has the port corresponding to osi_port
        # loop thru all ovs devices
        device_class = osi_port.dmd.Devices.getOrganizer(
                '/Network/OpenvSwitch')
        for ovs_device in device_class.devices():
            ovs_bridges = ovs_device.getDeviceComponents(
                type='OpenvSwitchBridge')
            ovs_ports = ovs_device.getDeviceComponents(
                type='OpenvSwitchPort')
            ovs_ifaces = ovs_device.getDeviceComponents(
                type='OpenvSwitchInterface')

            for port in ovs_ports:
                if short_osi_port_id not in port.name():
                    continue

                keyvalues = (port.device().manageIp, 'port', port.getPrimaryId())
                keys.append('ml2.openvswitch:' + '|'.join(keyvalues))

                port_keys = port.getNeutronIntegrationKeys()
                keys.extend(port_keys)

                # port's immediate parent is ports. ports' parent is bridge
                bridge_for_port = port.getPrimaryParent().getPrimaryParent()
                for bridge in ovs_bridges:
                    if bridge.id == bridge_for_port.id:
                        bridge_keys = bridge.getNeutronIntegrationKeys()
                        keys.extend(bridge_keys)
                        break

                # if we reach here, then osi_port is taken care of
                break

            for iface in ovs_ifaces:
                # not all ports have mac address
                if not hasattr(osi_port, 'mac_address') or \
                        not osi_port.mac_address or \
                        osi_port.mac_address != iface.amac:
                    continue

                iface_keys = iface.getNeutronIntegrationKeys()
                keys.extend(iface_keys)

            # if keys populated then we can quit here
            if keys:
                break

        return keys

    @classmethod
    def reindex_implementation_components(cls, dmd):
        device_class = dmd.Devices.getOrganizer('/Network/OpenvSwitch')
        results = ICatalogTool(device_class).search(
            ('ZenPacks.zenoss.OpenvSwitch.Bridge.Bridge',
             'ZenPacks.zenoss.OpenvSwitch.Port.Port',
             'ZenPacks.zenoss.OpenvSwitch.Interface.Interface',)
        )
        for brain in results:
            obj = brain.getObject()
            obj.index_object()
