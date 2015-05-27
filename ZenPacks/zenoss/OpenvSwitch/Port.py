##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.OpenvSwitch.Port')

from zope.interface import implements

try:
    from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration import get_neutron_components
    OSI_INSTALLED = True
except ImportError:
    OSI_INSTALLED = False

from . import schema

try:
    from ZenPacks.zenoss.OpenStackInfrastructure.interfaces \
        import INeutronImplementationComponent
    from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
        import index_implementation_object, unindex_implementation_object
    from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
        import get_neutron_components
    openstack = True
except ImportError:
    openstack = False


class Port(schema.Port):
    if openstack:
        implements(INeutronImplementationComponent)

    # The "integration key(s)" for this component must be made up of
    # a set of values that uniquely identify this resource and are
    # known to both this zenpack and the openstack zenpack.  They may
    # involve modeled properties, zProperties, and values from the neutron
    # configuration files on the openstack host.
    def getNeutronIntegrationKeys(self):
        # port name looks like: 'Port-qvo031752ba-0d'
        # we take the last ten digits
        keys = []
        shortened_name = self.name()[8:]
        keyvalues = (self.device().manageIp, 'port', shortened_name)
        log.debug("Integration key: %s", 'ml2.openvswitch:' + \
                                        '|'.join(keyvalues))
        keys.append('ml2.openvswitch:' + '|'.join(keyvalues))

        return keys

    def index_object(self, idxs=None):
        super(Port, self).index_object(idxs=idxs)
        if openstack:
            index_implementation_object(self)
            #import pdb;pdb.set_trace()
            osiport = self.get_osi_object(self.dmd, 'Port', self.name()[(len(self.name()) - 11):])
            if osiport:
                osiport.index_object(idxs)

    def unindex_object(self):
        super(Port, self).unindex_object()
        if openstack:
            unindex_implementation_object(self)

    def openstack_core_components(self):
        # openstack infrastructure integration
        #import pdb;pdb.set_trace()
        if OSI_INSTALLED:
            return get_neutron_components(self)
        else:
            return []

    def get_osi_object(self, dmd, type, ovs_obj_clue):
        #import pdb;pdb.set_trace()
        obj = None
        ositype = 'OpenStackInfrastructure' + type.title()
        osi_device_class = dmd.Devices.getOrganizer('/OpenStack/Infrastructure')
        for osi_device in osi_device_class.devices():
            osi_objs = osi_device.getDeviceComponents(type=ositype)
            for osi_obj in osi_objs:
                if ovs_obj_clue in osi_obj.id:
                    obj = osi_obj
                if obj:
                    break
            if obj:
                break

        return obj

