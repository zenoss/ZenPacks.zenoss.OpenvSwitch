##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""ZenPacks.zenoss.OpenvSwitch.- OpenvSwitch monitoring for Zenoss.

This module contains initialization code for the ZenPack. Everything in
the module scope will be executed at startup by all Zenoss Python
processes.

The initialization order for ZenPacks is defined by
$ZENHOME/ZenPacks/easy-install.pth.

"""

from . import zenpacklib


# Useful to avoid making literal string references to module and class names
# throughout the rest of the ZenPack.
MODULE_NAME = {}
CLASS_NAME = {}

RELATIONSHIPS_YUML = """
// containing
[OpenvSwitchDevice]++components-ovsdevice1[OpenvSwitchComponent]
[Database]++-[Bridge]
[Bridge]++-[Port]
// non-containing 1:M
[Port]1-.-*[Interface]
// non-containing 1:1
"""

CFG = zenpacklib.ZenPackSpec(
    name=__name__,     # evaluated to 'ZenPacks.zenoss.OpenvSwitch'

    zProperties={
        'DEFAULTS': {'category': 'OpenvSwitch',
                     'type': 'string'},
        },

    classes={
        # Device Types #######################################  ########

        'OpenvSwitchDevice': {
            'base': zenpacklib.Device,
            'meta_type': 'OpenvSwitchDevice',
            'filter_display': False,
        },

        # Component Base Types #######################################
        'OpenvSwitchComponent': {
            'base': zenpacklib.Component,
            'filter_display': False,
        },

        'Database': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchDatabase',
            'label': 'Database',
            'order': 3,
            'properties': {
                'databaseId':  {'grid_display': False,
                                'label': 'Database ID'},                 # 1
                'DB_version':  {'label': 'DB Version'},
                'OVS_version': {'label': 'OVS Version'},
            },
        },

        'Bridge': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchBridge',
            'label': 'Bridge',
            'order': 4,
            'properties': {
                'bridgeId':    {'grid_display': False,
                                'label': 'Bridge ID'},
            },
        },

        'Port': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchPort',
            'label': 'Port',
            'order': 5,
            'properties': {
                'portId':      {'grid_display': False,
                                'label': 'Port ID'},
                'tag_':        {'label': 'Tag'},
            },
        },

        'Interface': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchInterface',
            'label': 'Interface',
            'order': 6,
            'properties': {
                'interfaceId': {'grid_display': False,
                                'label': 'Interface ID'},
                'type_':       {'label': 'Type',
                                'order': 6.1,
                                'label_width': 50,
                                'content_width': 50},
                'mac':         {'label': 'MAC',
                                'order': 6.2,
                                'label_width': 100,
                                'content_width': 100},
                'lspeed':      {'label': 'Link Speed',
                                'order': 6.3,
                                'label_width': 50,
                                'content_width': 50},
                'lstate':      {'label': 'Link State',
                                'order': 6.4,
                                'label_width': 50,
                                'content_width': 50},
                'astate':      {'label': 'Admin State',
                                'order': 6.5,
                                'label_width': 60,
                                'content_width': 60},
                'mtu':         {'label': 'MTU',
                                'order': 6.6,
                                'label_width': 40,
                                'content_width': 40},
                'amac':         {'label': 'Attached MAC',
                                 'order': 6.7,
                                 'label_width': 100,
                                 'content_width': 100},
                'duplex':      {'label': 'Duplex',
                                'order': 6.8,
                                'label_width': 40,
                                'content_width': 40},
            },
        },


    },

    class_relationships=zenpacklib.relationships_from_yuml(RELATIONSHIPS_YUML),
    )

CFG.create()
