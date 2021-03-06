###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2015, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

import logging
logger = logging.getLogger('zen.OpenvSwitch.Parser')

from Products.ZenRRD.CommandParser import CommandParser
from ZenPacks.zenoss.OpenvSwitch.utils import str_to_dict

class InterfaceStatus(CommandParser):

    createDefaultEventUsingExitCode = False

    eventKey = eventClassKey = 'OpenvSwitch_interface_status'

    def processResults(self, cmd, result):
        # send an event if state is 'down'
        if '/usr/bin/ovs-vsctl' not in cmd.command:
            return

        if len(cmd.result.output) == 0:
            return

        iface_stats = str_to_dict(cmd.result.output)
        uuids = [stat['_uuid'] for stat in iface_stats]

        # cmd.component looks like: 'interface-35da03b8-1f47-4e82-b89a-d06a866d522f'
        iface_id = cmd.component[len('interface-'):]
        if iface_id not in uuids:
            return

        # interface admin_state: UP or DOWN
        # interface link_state: UP or DOWN
        severity = 0
        summary = ''
        iface_stat = [stat for stat in iface_stats if stat['_uuid'] == iface_id]
        if len(iface_stat) == 0:
            return

        if iface_stat[0]['admin_state'] == 'up' and iface_stat[0]['link_state'] == 'up':
            summary = 'Interface admin state: UP; Interface link state: UP'
            severity = 0           # send clear event
        elif iface_stat[0]['admin_state'] == 'down' and iface_stat[0]['link_state'] == 'down':
            summary = 'Interface admin state: DOWN; Interface link state: DOWN'
            severity = 3
        elif iface_stat[0]['link_state'] == 'down' and iface_stat[0]['admin_state'] == 'up':
            summary = 'Interface link state: DOWN'
            severity = 4

        # do not use eventClass, so that we can dedup based on summary
        event = dict(
            summary=summary,
            device= cmd.deviceConfig.device,
            component=cmd.component,
            eventClassKey=self.eventClassKey,
            severity=severity
            )

        result.events.append(event)


