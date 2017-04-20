##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from ZenPacks.zenoss.Layer2.connections_provider import \
    Connection, BaseConnectionsProvider


class DeviceConnectionsProvider(BaseConnectionsProvider):
    """
    Yields OSI layer 2 and 3 connections for OpenvSwitch device
    """

    def get_connections(self):
        device = self.context

        # Connect OpenvSwitch to his network by IP
        net = device.dmd.Networks.getNet(device.manageIp)
        if net and net.netmask != 32:
            yield Connection(device, (net, ), ['layer3', ])
            yield Connection(net, (device, ), ['layer3', ])

        for bridge in device.bridges():
            for port in bridge.ports():
                for interface in port.interfaces():
                    if interface.mac:
                        mac = interface.mac.strip()
                        yield Connection(device, (mac, ), ['layer2', ])
                        yield Connection(mac, (device, ), ['layer2', ])

