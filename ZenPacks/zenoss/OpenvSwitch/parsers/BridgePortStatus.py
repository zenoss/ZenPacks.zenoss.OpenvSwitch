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

import time
import datetime
from dateutil import parser

import logging
logger = logging.getLogger('zen.OpenvSwitch.Parser')

from Products.ZenRRD.CommandParser import CommandParser
from ZenPacks.zenoss.OpenvSwitch.utils import str_to_dict

class BridgePortStatus(CommandParser):

    eventKey = eventClassKey = 'OpenvSwitch_bridge_port_status'

    def processResults(self, cmd, result):
        # we consider records occurred within cmd.cycleTime
        # we assume the Zenoss host and target OpenvSwitch server
        # are within the same time zone, and time synced
        # we try not to flood Zenoss with old records
        if cmd.command.find('/usr/bin/ovsdb-tool') == -1:
            return

        if len(cmd.result.output) == 0:
            return

        logs = str_to_dict(cmd.result.output)
        rcrd_index = 0
        # logs[0] looks like:
        # {'record 0': 'Open_vSwitch" schema, version="7.4.0", cksum="951746691 20389'}
        # a record looks like this:
        # record 56: 2015-02-02 05:50:58.332 "ovs-vsctl: ovs-vsctl add-br mybridge"
        # We assume the time string looks like: 2015-01-29 05:20:30.199
        while (rcrd_index < len(logs[1].keys())):
            rcrd_index += 1

            rcrd_title = 'record ' + str(rcrd_index)
            rcrd = logs[1][rcrd_title]
            # rcrd_time = rcrd[:len('yyyy-mm-dd hh:mm:ss:xxx')]
            # rcrd_time = parser.parse(rcrd_time)
            # now = rcrd_time.now()
            # time_diff = now - rcrd_time
            # time_diff_seconds = int(time_diff.total_seconds())
            # if time_diff_seconds > cmd.cycleTime:
            #     continue

            summary = ''
            if rcrd.find('add-') > -1:
                if rcrd.find('add-br') > -1:
                    name = rcrd[rcrd.index('add-') + len('add-br '):]
                    summary = 'add bridge: ' + name
                elif rcrd.find('add-port') > -1:
                    marker = rcrd.index('add-') + len('add-port ')
                    name = rcrd[marker:rcrd.index(' --', marker)]
                    summary = 'add port: ' + name

                event = dict(
                    summary=summary,
                    component=cmd.component,
                    eventClass=cmd.eventClass,
                    eventKey=self.eventKey,
                    eventClassKey=self.eventClassKey,
                    severity=cmd.severity
                )

                result.events.append(event)
            elif rcrd.find('del-') > -1:
                if rcrd.find('del-br') > -1:
                    name = rcrd[rcrd.index('del-') + len('del-br '):]
                    summary = 'delete bridge: ' + name
                elif rcrd.find('del-port') > -1:
                    name = rcrd[rcrd.index('del-port ') + len('del-port '):]
                    summary = 'delete port: ' + name

                event = dict(
                    summary=summary,
                    component=cmd.component,
                    eventClass=cmd.eventClass,
                    eventKey=self.eventKey,
                    eventClassKey=self.eventClassKey,
                    severity=cmd.severity
                )

                result.events.append(event)



