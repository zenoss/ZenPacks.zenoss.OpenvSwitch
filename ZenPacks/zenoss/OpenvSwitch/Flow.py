##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


from . import schema

import logging
LOG = logging.getLogger('zen.OpenvSwitchFlow')

class Flow(schema.Flow):
    def get_bridge(self):
        if self.bridge():
            return self.bridge().id
