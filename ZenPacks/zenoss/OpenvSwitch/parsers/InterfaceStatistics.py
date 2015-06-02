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


class InterfaceStatistics(CommandParser):

    createDefaultEventUsingExitCode = False

    def processResults(self, cmd, result):
        if len(cmd.result.output) == 0:
            return

        resps = str_to_dict(cmd.result.output)

        for resp in resps:
            # is this resp relevant to cmd.component?
            if cmd.component.find(resp['_uuid']) == -1:
                continue

            dp_map = dict([(dp.id, dp) for dp in cmd.points])
            for name, dp in dp_map.items():
                if name in resp['statistics']:
                    if 'bytes' in name:
                        # for throughput, convert to bits from bytes
                        val = resp['statistics'][name] * 8
                    else:
                        val = resp['statistics'][name]
                    result.values.append((dp, val))

