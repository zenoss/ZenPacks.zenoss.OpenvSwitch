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
        if '/usr/bin/ovsdb-tool' not in cmd.command:
            return

        if len(cmd.result.output) == 0:
            return

        logs = str_to_dict(cmd.result.output.split('SPLIT')[1])
        rcrd_index = 0
        # logs[0] looks like:
        # {'record 0': 'Open_vSwitch" schema, version="7.4.0", cksum="951746691 20389'}
        # logs[1] is more interesting. Haven't seen logs[2] yet
        # a record looks like this:
        # record 56: 2015-02-02 05:50:58.332 "ovs-vsctl: ovs-vsctl add-br mybridge"
        # record 11: 2015-01-26 14:50:37.396 "ovs-vsctl: /usr/bin/ovs-vsctl -- --if-exists del-port qr-1046f5f2-02 -- add-port br-int qr-1046f5f2-02
        # We assume the time string looks like: 2015-01-29 05:20:30.199
        while (rcrd_index < len(logs[1])):
            rcrd_index += 1

            rcrd_title = 'record ' + str(rcrd_index)
            rcrd = logs[1][rcrd_title]

            # cmd.component: bridge name
            if cmd.component not in rcrd:
                # this record has nothing to do with this bridge
                continue

            summary = ''
            if 'add-' in rcrd:
                if 'add-br' in rcrd:
                    name = rcrd[rcrd.index('add-') + len('add-br '):]
                    summary = 'add bridge: ' + name
                elif 'add-port' in rcrd:
                    marker = rcrd.index('add-') + len('add-port ')
                    name = rcrd[marker:rcrd.index(' --', marker)]
                    summary = 'add port: ' + name

                event = dict(
                    summary=summary,
                    component=cmd.component,
                    eventClass=cmd.eventClass,
                    eventKey=self.eventKey,
                    severity=cmd.severity
                )

                result.events.append(event)
            # adding is often preceded by deleting.
            # if this is the case, then the record has been taken care of already
            # we only need to consider the case of deleting without adding here
            elif 'del-' in rcrd and 'add-' not in rcrd:
                if 'del-br' in rcrd:
                    name = rcrd[rcrd.index('del-') + len('del-br '):]
                    summary = 'delete bridge: ' + name
                elif 'del-port' in rcrd:
                    name = rcrd[rcrd.index('del-port ') + len('del-port '):]
                    summary = 'delete port: ' + name

                event = dict(
                    summary=summary,
                    component=cmd.component,
                    eventClass=cmd.eventClass,
                    eventKey=self.eventKey,
                    severity=cmd.severity
                )

                result.events.append(event)



