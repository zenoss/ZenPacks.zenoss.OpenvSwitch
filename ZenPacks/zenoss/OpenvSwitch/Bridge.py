##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.OpenvSwitch.Bridge')

from zope.interface import implements

from . import schema

try:
    from ZenPacks.zenoss.OpenStackInfrastructure.interfaces \
        import INeutronImplementationComponent
    from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
        import index_implementation_object, unindex_implementation_object
    openstack = True
except ImportError:
    openstack = False


class Bridge(schema.Bridge):
    if openstack:
        implements(INeutronImplementationComponent)

    # The "integration key(s)" for this component must be made up of
    # a set of values that uniquely identify this resource and are
    # known to both this zenpack and the openstack zenpack.  They may
    # involve modeled properties, zProperties, and values from the neutron
    # configuration files on the openstack host.
    def getNeutronIntegrationKeys(self):
        keyvalues = (self.device().manageIp, 'bridge', self.getPrimaryId())

        log.info("Integration key: %s", 'ml2.openvswitch:' + \
                                        '|'.join(keyvalues))
        return ['ml2.openvswitch:' + '|'.join(keyvalues)]

    def has_osi_devices(self):
        device_class = self.dmd.Devices.getOrganizer('/Devices/OpenStack/Infrastructure')
        return len(device_class.devices()) > 0

    def index_object(self, idxs=None):
        super(Bridge, self).index_object(idxs=idxs)
        if openstack and self.has_osi_devices():
            index_implementation_object(self)

    def unindex_object(self):
        super(Bridge, self).unindex_object()
        if openstack:
            unindex_implementation_object(self)
