# ==============================================================================
#  This is the main process() function that is called by the Events Transform
#  subsystem. See objects.xml for further detail.
# ==============================================================================

from Products.DataCollector.plugins.DataMaps import ObjectMap
from Products.DataCollector.ApplyDataMap import ApplyDataMap
from Products.ZenUtils.Utils import prepId

import logging
log = logging.getLogger('zen.OpenvSwitch.events')

def getObject(device, dmd, componentId):
    # given interface component ID, return the corresponding object
    # for use by apply datamap
    components = device.getDeviceComponents(type='OpenvSwitchInterface')
    for component in components:
        if componentId in component.getPrimaryParent().objectIds():
            return component.getPrimaryParent()._getOb(componentId)
    return None

def updateIface(evt, device, dmd, txnCommit):
    """
        incremental modeling based on events sent
    """
    if 'interface' not in evt.component:
        # for interface only
        return 0

    log.info("event: %s", str(evt))
    datamaps = []
    astate = 'UP'
    lstate = 'UP'
    if 'admin state: DOWN' in evt.summary:
        astate = 'DOWN'
    if 'link state: DOWN' in evt.summary:
        lstate = 'DOWN'

    obj = getObject(device, dmd, evt.component)
    if not obj:
        return 0

    datamaps.append(ObjectMap(
        modname='ZenPacks.zenoss.OpenvSwitch.Interface',
        compname='',
        data={
            'id':      evt.component,
            'lstate':  lstate,
            'astate':  astate,
        },
    ))
    adm = ApplyDataMap(device)
    adm.applyDataMap(obj, datamaps[0])

    return len(datamaps)
