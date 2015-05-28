##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from zope.interface import implements
from zope.event import notify

from Products.Zuul.catalog.events import IndexingEvent
from Products.Zuul.interfaces import ICatalogTool

from ZenPacks.zenoss.OpenStackInfrastructure.interfaces \
    import INeutronImplementationPlugin
from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
    import BaseNeutronImplementationPlugin, split_list


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
        # Use short name from OSI port ID as a clue to find the port on
        # OVS side. Use that OVS port to determine the OVS host IP
        short_osi_port_id = osi_port.id[5:16]

        # Get a list of all IPs of all hosts in the openstack environment
        manageIps = set()
        for host in osi_port.endpoint().getDeviceComponents(type='OpenStackInfrastructureHost'):
            manageIps.add(host.proxy_device().manageIp)

        keys = []
        for manageIp in manageIps:
            keyvalues = (manageIp, 'port', short_osi_port_id)
            keys.append('ml2.openvswitch:' + '|'.join(keyvalues))

            keyvalues = (manageIp, 'interface', osi_port.mac_address)
            keys.append('ml2.openvswitch:' + '|'.join(keyvalues))

        return keys

    @classmethod
    def reindex_implementation_components(cls, dmd):
        device_class = dmd.Devices.getOrganizer('/Network/OpenvSwitch')
        results = ICatalogTool(device_class).search(
            ('ZenPacks.zenoss.OpenvSwitch.Port.Port',
             'ZenPacks.zenoss.OpenvSwitch.Interface.Interface',)
        )

        for brain in results:
            obj = brain.getObject()
            obj.index_object()
            notify(IndexingEvent(obj))
