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

import re
import logging
logger = logging.getLogger('zen.OpenvSwitch.Parser')

from Products.ZenRRD.CommandParser import CommandParser

class OVSStatus(CommandParser):

    eventKey = eventClassKey = 'OpenvSwitch_OVS_status'

    def processResults(self, cmd, result):
        # Since during 1.1.0, we only use
        # Red Hat versions of OpenStack testing targets
        # we are not ready to test Ubuntu hosts for OpenvSwitch yet
        if '/sbin/service openvswitch status' not in cmd.command or \
           '/usr/bin/systemctl status openvswitch.service' not in cmd.command :
            return

        if len(cmd.result.output) == 0:
            return

        summary = ''
        stats = cmd.result.output.split('\n')
        for word in ('BEGIN', 'SPLIT', 'END', ''):
            while word in stats:
                stats.remove(word)

        # centos 6
        if len(stats) < 2:
            # should not happen
            return

        match_centos_6_1 = re.search(r'ovsdb-server is running', stats[0])
        match_centos_6_2 = re.search(r'ovs-vswitchd is running', stats[1])
        if match_centos_6_1 and match_centos_6_2:
            return

        match_centos_6_3 = re.search(r'ovsdb-server is not running', stats[0])
        match_centos_6_4 = re.search(r'ovs-vswitchd is not running', stats[1])
        if match_centos_6_3 or match_centos_6_4:
            summary = stats[0] + '; ' + stats[1]

        if len(summary) == 0:
            # centos 7
            if len(stats) < 4:
                # should not happen
                return

            match_centos_7_1 = re.search(r'Active: active', stats[2])
            if match_centos_7_1:
                return

            match_centos_7_2 = re.search(r'Active: inactive', stats[2])
            if match_centos_7_2:
                summary = 'openvswitch.service: ' + stats[2]

        event = dict(
            summary=summary,
            device= cmd.deviceConfig.device,
            eventClass=cmd.eventClass,
            eventKey=self.eventKey,
            severity=cmd.severity
        )

        result.events.append(event)


