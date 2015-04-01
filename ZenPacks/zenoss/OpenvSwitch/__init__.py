##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
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
[OpenvSwitch]++-[Bridge]
[Bridge]++-[Port]
[Bridge]++-[Flow]
[Port]++-[Interface]
// non-containing 1:M
// non-containing 1:1
"""

CFG = zenpacklib.ZenPackSpec(
    name=__name__,     # evaluated to 'ZenPacks.zenoss.OpenvSwitch'

    device_classes={
        '/Network/OpenvSwitch': {
            'create': True,
            'remove': False,
            'zProperties': {
                'zCollectorPlugins': [
                    'zenoss.ssh.OpenvSwitch',
                ]
            }
        }
    },

    classes={
        'DEFAULTS': {'base': 'ManagedObject'},

        # Device Types ###############################################
        'OpenvSwitch': {
            'base': zenpacklib.Device,
            'meta_type': 'OpenvSwitch',
            'filter_display': False,
            'properties': {
                'ovsTitle':          {'grid_display': False},
                'ovsId':             {'grid_display': False},
                'ovsDBVersion':      {'grid_display': False},
                'ovsVersion':        {'grid_display': False},
                'numberBridges':     {'grid_display': False},
                'numberPorts':       {'grid_display': False},
                'numberFlows':       {'grid_display': False},
                'numberInterfaces':  {'grid_display': False},
            },
            'impacts': ['bridges'],
        },

        # Component Base Types #######################################
        'ManagedObject': {
            'base': zenpacklib.Component,
            'filter_display': False,
        },

        'Bridge': {
            'meta_type': 'OpenvSwitchBridge',
            'label': 'Bridge',
            'plural_label': 'Bridges',
            'order': 1,
            'properties': {
                'bridgeId':    {'grid_display': False,
                                'label': 'Bridge ID'},
            },
            'impacts': ['ports',
                        'flows',
                       ],
            'impacted_by': ['openvSwitch'],
        },

        'Port': {
            'meta_type': 'OpenvSwitchPort',
            'label': 'Port',
            'plural_label': 'Ports',
            'order': 2,
            'properties': {
                'portId':      {'grid_display': False,
                                'label': 'Port ID'},
                'tag_':        {'label': 'VLAN Tag'},
            },
            'impacts': ['interfaces'],
            'impacted_by': ['bridge'],
        },

        'Flow': {
            'meta_type': 'OpenvSwitchFlow',
            'label': 'Flow',
            'plural_label': 'Flows',
            'order': 3,
            'properties': {
                'flowId':       {'grid_display': False,
                                'label': 'Flow ID'},
                'table':        {'label': 'Table',
                                 'order': 3.1,
                                 'label_width': 50,
                                 'content_width': 50},
                'priority':     {'label': 'Priority',
                                 'order': 3.2,
                                 'label_width': 50,
                                 'content_width': 50},
                'protocol':     {'label': 'Protocol',
                                 'order': 3.3,
                                 'label_width': 50,
                                 'content_width': 50},
                'inport':       {'label': 'In Port',
                                 'order': 3.4,
                                 'label_width': 50,
                                 'content_width': 50},
                'nwsrc':        {'label': 'Source',
                                 'order': 3.5},
                'nwdst':        {'label': 'Destination',
                                 'order': 3.6},
                'action':       {'label': 'Action',
                                 'order': 3.7},
            },
            'impacted_by': ['bridge'],
        },

        'Interface': {
            'meta_type': 'OpenvSwitchInterface',
            'label': 'Interface',
            'plural_label': 'Interfaces',
            'order': 4,
            'properties': {
                'interfaceId': {'grid_display': False,
                                'label': 'Interface ID'},
                'type_':       {'label': 'Type',
                                'order': 4.1,
                                'label_width': 40,
                                'content_width': 40},
                'mac':         {'label': 'MAC in use',
                                'order': 4.2,
                                'label_width': 100,
                                'content_width': 100},
                'amac':        {'label': 'Attached MAC',
                                'order': 4.3,
                                'label_width': 100,
                                'content_width': 100},
                'ofport':      {'label': 'OF Port',
                                'order': 4.4,
                                'label_width': 40,
                                'content_width': 40},
                'astate':      {'label': 'Admin State',
                                'order': 4.5,
                                'label_width': 60,
                                'content_width': 60},
                'lstate':      {'label': 'Link State',
                                'order': 4.6,
                                'label_width': 60,
                                'content_width': 60},
                'lspeed':      {'grid_display': False,
                                'label': 'Link Speed',
                                'order': 4.7},
                'mtu':         {'grid_display': False,
                                'label': 'MTU',
                                'order': 4.8},
                'duplex':      {'grid_display': False,
                                'label': 'Duplex',
                                'order': 4.9},
            },
            'impacted_by': ['port'],
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
