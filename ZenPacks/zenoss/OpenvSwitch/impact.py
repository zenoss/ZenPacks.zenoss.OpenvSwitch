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

ZENPACK_NAME = 'ZenPacks.zenoss.OpenvSwitch'


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


class OVSDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

#    impacts = ['openvSwitchBridge']


class BridgeDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

#    impacted_by = ['openvSwitchOVS']
#    impacts = ['openvSwitchPort', 'openvSwitchFlow']

class PortDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

#    impacted_by = ['openvSwitchBridge']
#    impacts = ['openvSwitchInterface']

class FlowDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

#    impacted_by = ['openvSwitchBridge']

class InterfaceDeviceRelationsProvider(BaseRelationshipDataProvider):
    adapts(Device)

#    impacted_by = ['openvSwitchPort']

