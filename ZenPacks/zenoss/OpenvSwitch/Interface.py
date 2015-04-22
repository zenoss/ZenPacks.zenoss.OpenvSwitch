##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.OpenvSwitch.Interface')

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


class Interface(schema.Interface):
    if openstack:
        implements(INeutronImplementationComponent)

    # The "integration key(s)" for this component must be made up of
    # a set of values that uniquely identify this resource and are
    # known to both this zenpack and the openstack zenpack.  They may
    # involve modeled properties, zProperties, and values from the neutron
    # configuration files on the openstack host.
    def getNeutronIntegrationKeys(self):
        keyvalues = (self.device().manageIp, 'interface', self.amac)

        log.info("Integration key: %s", 'ml2.openvswitch:' + \
                                        '|'.join(keyvalues))
        return ['ml2.openvswitch:' + '|'.join(keyvalues)]

    def index_object(self, idxs=None):
        super(Interface, self).index_object(idxs=idxs)
        if openstack:
            index_implementation_object(self)

    def unindex_object(self):
        super(Interface, self).unindex_object()
        if openstack:
            unindex_implementation_object(self)
