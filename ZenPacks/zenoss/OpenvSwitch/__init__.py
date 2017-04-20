##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""ZenPacks.zenoss.OpenvSwitch.- OpenvSwitch monitoring for Zenoss.

This module contains initialization code for the ZenPack. Everything in
the module scope will be executed at startup by all Zenoss Python
processes.

The initialization order for ZenPacks is defined by
$ZENHOME/ZenPacks/easy-install.pth.

"""

from . import zenpacklib

#------------------------------------------------------------------------------
# Load ZPL Yaml here
#------------------------------------------------------------------------------
CFG = zenpacklib.load_yaml()

# patches
from Products.ZenUtils.Utils import unused

from . import schema


class ZenPack(schema.ZenPack):
    def install(self, app):
        super(ZenPack, self).install(app)

        try:
            from ZenPacks.zenoss.OpenStackInfrastructure.neutron_integration \
                import reindex_core_components
            reindex_core_components(self.dmd)
        except ImportError:
            pass

    def remove(self, dmd, leaveObjects=False):
        # since this ZP added addition eventClasses, and zencatalogservice,
        # if is running, indexed them, the event catalog needs to be
        # cleaned up at removal
        super(ZenPack, self).remove(dmd, leaveObjects=leaveObjects)

        from ZODB.transact import transact
        brains = dmd.Events.eventClassSearch()
        for brain in brains:
            try:
                test_reference = brain.getObject()
                test_reference._p_deactivate()
            except Exception:
                object_path_string = brain.getPath()
                try:
                    transact(dmd.Events.eventClassSearch.uncatalog_object)(
                        object_path_string)
                except Exception as e:
                    pass

# Patch last to avoid import recursion problems.
from ZenPacks.zenoss.OpenvSwitch import patches
unused(patches)
