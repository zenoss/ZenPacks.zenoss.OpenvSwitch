##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.OpenvSwitch.ml2')

from zope.interface import implements
from zope.event import notify
from zope.container.interfaces import IObjectRemovedEvent

from Products.Zuul.catalog.events import IndexingEvent
from Products.Zuul.interfaces import ICatalogTool

try:
    from ZenPacks.zenoss.OpenStackInfrastructure.interfaces \
        import INeutronImplementationPlugin
    from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
        import BaseNeutronImplementationPlugin, split_list, reindex_core_components
    openstack = True
except ImportError:
    log.error("failed to import %s and/or %s",
              "INeutronImplementationPlugin",
              "BaseNeutronImplementationPlugin")
    openstack = False

if openstack:
    class OpenvSwitchNeutronImplementationPlugin(BaseNeutronImplementationPlugin):
        implements(INeutronImplementationPlugin)

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

                if hasattr(osi_port, 'mac_address') and osi_port.mac_address:
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


def onOpenStackHostAdded(obj, event):
    if not IObjectRemovedEvent.providedBy(event):
        # If a host is added to the system, we need to reindex the openstack
        # ports, since a portion of their integration key is based on the hosts'
        # manageIps.
        endpoint = obj.endpoint()

        log.info("A new host (%s) has been added to openstack endpoint %s - reindexing port components",
                 obj.titleOrId(), endpoint.titleOrId())

        results = ICatalogTool(endpoint).search(('ZenPacks.zenoss.OpenStackInfrastructure.Port.Port',))
        for brain in results:
            try:
                port = brain.getObject()
            except Exception, e:
                log.error("Error loading port %s: %s", brain, e)
                continue

            try:
                port.index_object()
                notify(IndexingEvent(port))
            except Exception, e:
                log.error("Error reindexing port %s: %s", port, e)
