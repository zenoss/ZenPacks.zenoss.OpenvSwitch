##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
log = logging.getLogger('zen.OpenvSwitch.ML2Integration')

try:
    from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration import get_neutron_components
    OSI_INSTALLED = True
except ImportError:
    OSI_INSTALLED = False

class ML2Integration(object):

    """Mixin for model classes that have OpenStack ML2 integrations."""

    def openstack_core_components(self):
        # openstack infrastructure integration
        if OSI_INSTALLED:
            return get_neutron_components(self)
        else:
            return []
