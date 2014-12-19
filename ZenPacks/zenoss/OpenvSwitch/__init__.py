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
[OVS]++-[Bridge]
[Bridge]++-[Port]
[Bridge]++-[Flow]
// non-containing 1:M
[Port]1-.-*[Interface]
// non-containing 1:1
"""

CFG = zenpacklib.ZenPackSpec(
    name=__name__,     # evaluated to 'ZenPacks.zenoss.OpenvSwitch'

    classes={
        # Device Types ###############################################
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

        'OVS': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchOVS',
            'label': 'Open vSwitch',
            'order': 1,
            'properties': {
                'ovsId':       {'grid_display': False,
                                'label': 'OpenvSwitch ID'},
                'DB_version':  {'label': 'DB Version'},
                'OVS_version': {'label': 'OVS Version'},
            },
        },

        'Bridge': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchBridge',
            'label': 'Bridge',
            'order': 2,
            'properties': {
                'bridgeId':    {'grid_display': False,
                                'label': 'Bridge ID'},
                # 'flow_count':  {'label': 'Flow Count',
                #                 'order': 2.1},
                # 'byte_count':  {'label': 'Byte Count',
                #                  'order': 2.2},
                # 'packet_count':{'label': 'Packet Count',
                #                  'order': 2.3},
            },
        },

        'Port': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchPort',
            'label': 'Port',
            'order': 3,
            'properties': {
                'portId':      {'grid_display': False,
                                'label': 'Port ID'},
                'tag_':        {'label': 'VLAN Tag'},
            },
        },

        'Flow': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchFlow',
            'label': 'Flow',
            'order': 4,
            'properties': {
                'flowId':       {'grid_display': False,
                                'label': 'Flow ID'},
                'table':        {'label': 'Table',
                                 'order': 4.1},
                'priority':     {'label': 'Priority',
                                 'order': 4.2},
                'protocol':     {'label': 'Protocol',
                                 'order': 4.3},
                'inport':       {'label': 'In Port',
                                 'order': 4.4},
                'nwsrc':        {'label': 'Source',
                                 'order': 4.5},
                'nwdst':        {'label': 'Destination',
                                 'order': 4.6},
                'action':       {'label': 'Action',
                                 'order': 4.7},
                # 'bytes':        {'label': 'Bytes',
                #                  'order': 4.4},
                # 'packets':      {'label': 'Packets',
                #                  'order': 4.5},
            },
        },

        'Interface': {
            'base': 'OpenvSwitchComponent',
            'meta_type': 'OpenvSwitchInterface',
            'label': 'Interface',
            'order': 5,
            'properties': {
                'interfaceId': {'grid_display': False,
                                'label': 'Interface ID'},
                'type_':       {'label': 'Type',
                                'order': 5.1,
                                'label_width': 50,
                                'content_width': 50},
                'mac':         {'label': 'MAC in use',
                                'order': 5.2,
                                'label_width': 100,
                                'content_width': 100},
                'amac':        {'label': 'Attached MAC',
                                'order': 5.3,
                                'label_width': 100,
                                'content_width': 100},
                'ofport':      {'label': 'OF Port',
                                'order': 5.4,
                                'label_width': 50,
                                'content_width': 50},
                'lspeed':      {'label': 'Link Speed',
                                'order': 5.5,
                                'label_width': 50,
                                'content_width': 50},
                'lstate':      {'label': 'Link State',
                                'order': 5.6,
                                'label_width': 50,
                                'content_width': 50},
                'astate':      {'label': 'Admin State',
                                'order': 5.7,
                                'label_width': 60,
                                'content_width': 60},
                'mtu':         {'label': 'MTU',
                                'order': 5.8,
                                'label_width': 40,
                                'content_width': 40},
                'duplex':      {'label': 'Duplex',
                                'order': 5.9,
                                'label_width': 40,
                                'content_width': 40},
            },
        },


    },

    class_relationships=zenpacklib.relationships_from_yuml(RELATIONSHIPS_YUML),
    )

CFG.create()

# patches
from Products.ZenUtils.Utils import unused

# Patch last to avoid import recursion problems.
from ZenPacks.zenoss.OpenvSwitch import patches
unused(patches)
