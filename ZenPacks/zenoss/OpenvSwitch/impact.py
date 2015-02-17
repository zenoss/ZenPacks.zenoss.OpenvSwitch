##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from zope.component import adapts
from zope.interface import implements

from Products.ZenUtils.guid.interfaces import IGlobalIdentifier
from ZenPacks.zenoss.Impact.impactd.relations import ImpactEdge
from ZenPacks.zenoss.Impact.impactd.interfaces import IRelationshipDataProvider

from Products.ZenModel.Device import Device

from . import __name__ as ZENPACK_NAME
from OpenvSwitch import OpenvSwitch
from Bridge import Bridge
from Port import Port

# Lazy imports to make this module not require Impact.
ImpactEdge = None
Trigger = None

# Constants to avoid typos.
AVAILABILITY = 'AVAILABILITY'
PERCENT = 'policyPercentageTrigger'
THRESHOLD = 'policyThresholdTrigger'
DOWN = 'DOWN'
DEGRADED = 'DEGRADED'
ATRISK = 'ATRISK'


def guid(obj):
    """Return GUID for obj."""
    return IGlobalIdentifier(obj).getGUID()


class BaseImpactAdapterFactory(object):

    """Abstract base for Impact adapter factories."""

    def __init__(self, adapted):
        self.adapted = adapted

    def guid(self):
        if not hasattr(self, '_guid'):
            self._guid = guid(self.adapted)

        return self._guid


class BaseRelationshipDataProvider(object):
    '''
    Abstract base for IRelationshipDataProvider adapter factories.
    '''
    implements(IRelationshipDataProvider)

    relationship_provider = ZENPACK_NAME

    impacts = None
    impacted_by = None

    def __init__(self, adapted):
        self.adapted = adapted

    def belongsInImpactGraph(self):
        """Return True so generated edges will show in impact graph.

        Required by IRelationshipDataProvider.

        """
        return True

    def getEdges(self):
        """Generate ImpactEdge instances for adapted object.

        Required by IRelationshipDataProvider.

        """
        provider = self.relationship_provider
        myguid = IGlobalIdentifier(self.adapted).getGUID()

        if self.impacted_by:
            for methodname in self.impacted_by:
                for impactor_guid in self.get_remote_guids(methodname):
                    yield ImpactEdge(impactor_guid, myguid, provider)

        if self.impacts:
            for methodname in self.impacts:
                for impactee_guid in self.get_remote_guids(methodname):
                    yield ImpactEdge(myguid, impactee_guid, provider)

    def get_remote_guids(self, methodname):
        """Generate object GUIDs returned by adapted.methodname()."""

        method = getattr(self.adapted, methodname, None)
        if not method or not callable(method):
            return

        r = method()
        if not r:
            return

        try:
            for obj in r:
                yield IGlobalIdentifier(obj).getGUID()

        except TypeError:
            yield IGlobalIdentifier(r).getGUID()


class BaseTriggers(BaseImpactAdapterFactory):

    """Abstract base for INodeTriggers adapter factories."""

    triggers = []

    def get_triggers(self):
        '''
        Return list of triggers defined by subclass' triggers property.
        '''
        # Lazy import without incurring import overhead.
        # http://wiki.python.org/moin/PythonSpeed/PerformanceTips#Import_Statement_Overhead
        global Trigger
        if not Trigger:
            from ZenPacks.zenoss.Impact.impactd import Trigger

        for trigger_args in self.triggers:
            yield Trigger(self.guid(), *trigger_args)


# OVS Impact Providers #################################################

class BridgeTriggers(BaseTriggers):

    """Impact policy triggers for bridge instances."""

    triggers = [
        ('DOWN when 100% device DOWN', PERCENT, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '100',
            'state': DOWN,
            'metaTypes': [OpenvSwitch.meta_type],
            }),
        ]


class InterfaceTriggers(BaseTriggers):

    """Impact policy triggers for interface instances."""

    triggers = [
        ('DOWN when 100% port DOWN', PERCENT, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '100',
            'state': DOWN,
            'metaTypes': [Port.meta_type],
            }),

        ('DOWN when 100% bridge DOWN', PERCENT, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '100',
            'state': DOWN,
            'metaTypes': [Bridge.meta_type],
            }),

        ('DOWN when 100% device DOWN', THRESHOLD, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '100',
            'state': DOWN,
            'metaTypes': [OpenvSwitch.meta_type],
            }),
        ]

class OVSDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

class BridgeDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

class PortDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

class FlowDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

class InterfaceDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

