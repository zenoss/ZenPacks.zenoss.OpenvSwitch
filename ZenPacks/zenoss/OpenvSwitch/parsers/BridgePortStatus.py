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
log = logging.getLogger('zen.OpenvSwitch.Parser')

from Products.ZenRRD.CommandParser import CommandParser
from ZenPacks.zenoss.OpenvSwitch.utils import str_to_dict, get_ovsdb_records

class BridgePortStatus(CommandParser):

    eventKey = eventClassKey = 'OpenvSwitch_bridge_port_status'

    def processResults(self, cmd, result):
        if '/usr/bin/ovsdb-tool' not in cmd.command:
            return

        if len(cmd.result.output) == 0:
            return

        logs = str_to_dict(cmd.result.output.split('SPLIT')[1])
        # logs[0] looks like:
        # {'record 0': 'Open_vSwitch" schema, version="7.4.0", cksum="951746691 20389'}
        # logs[1] is more interesting. Haven't seen logs[2] yet
        # a record looks like this:
        # record 56: 2015-02-02 05:50:58.332 "ovs-vsctl: ovs-vsctl add-br mybridge"
        # record 11: 2015-01-26 14:50:37.396 "ovs-vsctl: /usr/bin/ovs-vsctl -- --if-exists del-port qr-1046f5f2-02 -- add-port br-int qr-1046f5f2-02
        # We assume the time string looks like: 2015-01-29 05:20:30.199
        events = get_ovsdb_records(logs[1], cmd.component, cmd.cycleTime)
        for evt in events:
            severity = 2
            if 'del' in evt['summary']:
                severity = 3

            event = dict(
                summary=evt['summary'],
                device= cmd.deviceConfig.device,
                component=cmd.component,
                eventClass=cmd.eventClass,
                eventClassKey=self.eventClassKey,
                severity=severity
            )

            result.events.append(event)



