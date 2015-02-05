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

    eventKey = eventClassKey = 'OpenvSwitch_OVS_status'

    def processResults(self, cmd, result):
        if cmd.command.find('/etc/system-release') == -1:
            return

        if len(cmd.result.output) == 0:
            return

        stats = cmd.result.output.split('\n')
        for stat in stats:
            if stat and len(stat) > 0 and stat.find('not running') > -1:
                event = dict(
                    summary=stat,
                    eventClass=cmd.eventClass,
                    eventKey=self.eventKey,
                    eventClassKey=self.eventClassKey,
                    severity=cmd.severity
                )

                result.events.append(event)


