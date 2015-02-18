##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# stdlib Imports
import copy

# ZenPack Imports
from . import schema


class OpenvSwitch(schema.OpenvSwitch):
    """OpenvSwitch model class."""

    # Copy from parent class to avoid changing parent class.
    factory_type_information = copy.deepcopy(
        schema.OpenvSwitch.factory_type_information)

    # Remove "Software" from actions.
    factory_type_information[0]['actions'] = filter(
        lambda a: a['id'] != 'swdetail',
        factory_type_information[0]['actions'])
