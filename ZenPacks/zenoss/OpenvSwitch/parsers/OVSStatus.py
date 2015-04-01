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

class OVSStatus(CommandParser):

    createDefaultEventUsingExitCode = False

    eventKey = eventClassKey = 'OpenvSwitch_OVS_status'

    def processResults(self, cmd, result):
        # Since during 1.1.0, we only use
        # Red Hat versions of OpenStack testing targets
        # we are not ready to test Ubuntu hosts for OpenvSwitch yet

        if '/sbin/service openvswitch status' not in cmd.command or \
                '/usr/bin/systemctl status openvswitch-nonetwork.service' not in cmd.command :
            return

        if len(cmd.result.output) == 0:
            return

        stats = cmd.result.output.split('\n')
        for word in ('BEGIN', 'SPLIT', 'END', ''):
            while word in stats:
                stats.remove(word)

        # centos 6
        if len(stats) < 2:
            # should not happen
            return

        summary = ''
        severity = cmd.severity
        if len(stats) == 2:
            # for centos 6.x hosts
            ovsdb_server_is_running = len([stat for stat in stats \
                                           if 'ovsdb-server is running' in stat]) > 0
            ovs_vswitchd_is_running = len([stat for stat in stats \
                                           if 'ovs-vswitchd is running' in stat]) > 0
            if ovsdb_server_is_running and ovs_vswitchd_is_running:
                summary = 'ovsdb-server is running; ovs-vswitchd is running.'
                severity = 0
            elif ovsdb_server_is_running and not ovs_vswitchd_is_running:
                summary = 'ovs-vswitchd is not running.'
            elif not ovsdb_server_is_running and ovs_vswitchd_is_running:
                summary = 'ovsdb-server is not running.'
            else:
                summary = 'ovsdb-server is not running; ovs-vswitchd is not running.'

        # for centos 7 host, we are looking for something like:
        # 22842 ovsdb-server: monitoring pid 22843 (healthy)
        # 22853 ovs-vswitchd: monitoring pid 22854 (healthy)
        # and there should be two healthy daemons: ovsdb-server and ovs-vswitchd
        if len(summary) == 0 and len(stats) > 2:
            stats = [stat.strip() for stat in stats if '(healthy)' in stat]
            if len(stats) == 2:          # all healthy
                summary = 'ovsdb-server is running; ovs-vswitchd is running.'
                severity = 0
            elif len(stats) == 1:
                if 'ovsdb-server' in stats[0]:
                    summary = 'ovs-vswitchd is not running.'
                else:
                    summary = 'ovsdb-server is not running.'
            elif len(stats) == 0:
                summary = 'ovsdb-server is not running; ovs-vswitchd is not running.'

        # if we ever reach here, then summary != ''
        # some daemon is not running
        event = dict(
            summary=summary,
            device= cmd.deviceConfig.device,
            eventClass=cmd.eventClass,
            eventKey=self.eventKey,
            severity=severity
        )

        result.events.append(event)

