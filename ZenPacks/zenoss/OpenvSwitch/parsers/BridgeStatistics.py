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

from ZenPacks.zenoss.OpenvSwitch.utils import bridge_stats_data_to_dict


class BridgeStatistics(CommandParser):
    def processResults(self, cmd, result):
        if len(cmd.result.output) == 0:
            return

        resps = bridge_stats_data_to_dict(cmd.result.output)

        for k, v in resps.iteritems():
            # is this (k, v) relevant to cmd.component?
            if cmd.component.find(v['uuid']) == -1:
                continue

            dp_map = dict([(dp.id, dp) for dp in cmd.points])
            for name, dp in dp_map.iteritems():
                if name in v:
                    result.values.append((dp, v[name]))

