##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# Zope Imports
from zope.interface import implements
from zope.component import adapts

# Zenoss Imports
from Products.Zuul.interfaces import IReportable, IReportableFactory

# Analytics Imports
from ZenPacks.zenoss.ZenETL.reportable import (
    BaseReportable,
    DeviceReportable,
    DeviceReportableFactory,
    MARKER_LENGTH,
    DEFAULT_STRING_LENGTH,
    )

# ZenPack Imports
from .OpenvSwitch import OpenvSwitch
from .ManagedObject import ManagedObject


class OVSDeviceReportableFactory(DeviceReportableFactory):

    """Reportable factory for OpenvSwitch.

    This custom factory causes each OpenvSwitch instance to be exported into
    dim_device and dim_Open_vSwitch. Standard device properties
    reported by DeviceReportable will be in dim_device. Those same
    properties plus OpenvSwitch-specific properties will be in
    dim_Open_vSwitch. This avoids the need to always join on
    dim_device.

    This works by making IReportable(OpenvSwitch) find the OVSDeviceReportable
    adapter, then having this factory explicitly yield
    DeviceReportable(OpenvSwitch).

    """

    implements(IReportableFactory)
    adapts(OpenvSwitch)

    def exports(self):
        """Generate IReportable adapters."""
        for reportable in super(OVSDeviceReportableFactory, self).exports():
            yield reportable

        yield DeviceReportable(self.context)


class OVSDeviceReportable(DeviceReportable):

    """Reportable adapter for OpenvSwitch."""

    implements(IReportable)
    adapts(OpenvSwitch)

    entity_class_name = 'open_vswitch'

    def reportProperties(self):
        properties = super(OVSDeviceReportable, self).reportProperties()

        str_properties = (
            'ovsTitle',
            'ovsDBVersion',
            'ovsVersion',
        )

        int_properties = (
            'numberBridges',
            'numberPorts',
            'numberFlows',
            'numberInterfaces',
        )

        for str_property in str_properties:
            properties.append((
                str_property,
                'string',
                getattr(self.context, str_property, None),
                DEFAULT_STRING_LENGTH))

        for int_property in int_properties:
            properties.append((
                int_property,
                'int',
                getattr(self.context, int_property, None),
                MARKER_LENGTH))

        return properties

class ManagedObjectReportable(BaseReportable):

    """Reportable adapter for ManagedObject.

    Generic reportable for all ManagedObject subclass instances. Extends
    BaseReportable so all properties and relationships are automatically
    captured.

    """

    implements(IReportable)
    adapts(ManagedObject)

    @property
    def entity_class_name(self):
        """Return entity class name for adapted object."""
        return 'openvswitch_{}'.format({
            'Bridge': 'bridge',
            'Port': 'port',
            'Flow': 'flow',
            'Interface': 'interface',
            }[self.context.__class__.__name__])

    def reportProperties(self):
        """Return report properties for adapted object."""
        properties = list(
            super(ManagedObjectReportable, self).reportProperties())

        property_names = {p[0] for p in properties}

        # Every component should have component_key.
        if 'component_key' not in property_names:
            properties.append((
                'component_key',
                'reference',
                IReportable(self.context).sid,
                MARKER_LENGTH))

        # Every component should have a name.
        namekey = '_'.join((self.entity_class_name, 'name'))
        if namekey not in property_names:
            properties.append((
                namekey,
                'string',
                self.context.name(),
                DEFAULT_STRING_LENGTH))

        # Every component should have device_key and openvswitch_key.
        for keyname in ('device_key', 'openvswitch_key'):
            if keyname not in property_names:
                properties.append((
                    keyname,
                    'reference',
                    IReportable(self.context.device()).sid,
                    MARKER_LENGTH))

        return properties
