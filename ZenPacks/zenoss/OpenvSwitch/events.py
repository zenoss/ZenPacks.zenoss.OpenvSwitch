# ==============================================================================
#  This is the main process() function that is called by the Events Transform
#  subsystem. See objects.xml for further detail.
# ==============================================================================

from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.DataCollector.ApplyDataMap import ApplyDataMap

import logging
log = logging.getLogger('zen.OpenvSwitch.events')

def updateBridgePort(evt, device, component):
    """
        incremental bridge modeling based on events sent
        here we only consider delete event

        We can only incrementally model for delete events,
        but not for add event.
        The reason being that for deleting, we only need to know the
        component name. But for adding, we need to know much more
        ovsdb-tool show-log would not give us all info needed for adding
    """
    existingBridgeObjects = device.getDeviceComponents(type='OpenvSwitchBridge')
    bridgeTitleOrIds = [bridge.titleOrId() for bridge in existingBridgeObjects]
    bridgeIDs = [bridge.id for bridge in existingBridgeObjects]

    if evt.component not in bridgeTitleOrIds and \
            evt.component not in bridgeIDs:
        # for existing bridge only
        return 0

    log.info("event: %s", str(evt))
    bridges = []
    compname = ''
    relname = ''
    modname = ''
    if 'del bridge' in evt.summary:
        relname = 'bridges'
        modname = 'ZenPacks.zenoss.OpenvSwitch.Bridge'
        for brdg in existingBridgeObjects:
            if brdg and evt.component in (brdg.id, brdg.titleOrId()):
                continue

            bridges.append(ObjectMap(
                data={
                    'id':       brdg.id,
                    'title':    brdg.titleOrId(),
                    'bridgeId': brdg.uuid,
                    }))
        relmap = RelationshipMap(
            objmaps=bridges)

    if len(bridges) > 0:
        adm = ApplyDataMap(device)
        adm.applyDataMap(device, relmap, relname=relname, compname=compname, modname=modname)

        return 1
    else:
        return 0

def updateIface(evt, device, component):
    """
        incremental interface modeling based on events sent
        here we only consider interface UP or DOWN
    """
    if 'interface' not in evt.component:
        # for interface only
        return 0

    log.info("event: %s", str(evt))
    astate = 'UP'
    lstate = 'UP'
    if 'admin state: DOWN' in evt.summary:
        astate = 'DOWN'
    if 'link state: DOWN' in evt.summary:
        lstate = 'DOWN'

    objmap = ObjectMap(
        modname='ZenPacks.zenoss.OpenvSwitch.Interface',
        compname='',
        data={
            'id':      evt.component,
            'lstate':  lstate,
            'astate':  astate,
        },
    )
    adm = ApplyDataMap(device)
    adm.applyDataMap(component, objmap)

    return 1
