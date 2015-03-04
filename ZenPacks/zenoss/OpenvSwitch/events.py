# ==============================================================================
#  This is the main process() function that is called by the Events Transform
#  subsystem. See objects.xml for further detail.
# ==============================================================================

from Products.DataCollector.plugins.DataMaps import ObjectMap
from Products.DataCollector.ApplyDataMap import ApplyDataMap

import logging
log = logging.getLogger('zen.OpenvSwitch.events')

def updateIface(evt, device, component):
    """
        incremental modeling based on events sent
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
