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
log = logging.getLogger('zen.OpenvSwitch')

from Products.Five import zcml

from Products.DataCollector.ApplyDataMap import ApplyDataMap
from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ..modeler.plugins.zenoss.ssh.OpenvSwitch import OpenvSwitch as OpenvSwitchModeler

from .util import loadData


class TestModeler(BaseTestCase):
    def afterSetUp(self):
        super(TestModeler, self).afterSetUp()

        self.d = self.dmd.Devices.createInstance('zenoss.OpenvSwitch.testDevice')
        self.applyDataMap = ApplyDataMap()._applyDataMap

        # Required to prevent erroring out when trying to define viewlets in
        # ../browser/configure.zcml.original.
        import zope.viewlet
        zcml.load_config('meta.zcml', zope.viewlet)

        import ZenPacks.zenoss.OpenvSwitch
        zcml.load_config('configure.zcml', ZenPacks.zenoss.OpenvSwitch)

    def testOvsVsctlNotFound(self):
        modeler = OpenvSwitchModeler()
        modeler_results = loadData('model_no_ovs-vsctl.txt')
        data_maps = modeler.process(self.d, modeler_results, log)

        self.assertEquals(data_maps, None)

    def testOvsOfctlNotFound(self):
        modeler = OpenvSwitchModeler()
        modeler_results = loadData('model_no_ovs-ofctl.txt')
        data_maps = modeler.process(self.d, modeler_results, log)

        self.assertEquals(data_maps, None)

    def testOpenvSwitchNotRunning(self):
        modeler = OpenvSwitchModeler()
        modeler_results = loadData('model_no_openvswitch.txt')
        data_maps = modeler.process(self.d, modeler_results, log)

        self.assertEquals(data_maps, None)

    def testMeaningless(self):
        # if openvswitch service on target Open vSwitch host is down
        # the results look like what is in model_meaningless.txt
        modeler = OpenvSwitchModeler()
        modeler_results = loadData('model_meaningless.txt')
        data_maps = modeler.process(self.d, modeler_results, log)

        self.assertEquals(data_maps, None)

    def testRunningZenoss(self):
        modeler = OpenvSwitchModeler()
        modeler_results = loadData('model_running_zenoss.txt')
        data_maps = modeler.process(self.d, modeler_results, log)

        self.assertEquals(len(data_maps), 6)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestModeler))
    return suite
