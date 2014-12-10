###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2014, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

from Products.ZenRRD.CommandParser import ParsedResults
from Products.ZenRRD.zencommand import Cmd, DataPointConfig
from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ..parsers.InterfaceStatistics import InterfaceStatistics as InterfaceStatisticsParser

from .util import loadData


class FakeCmdResult(object):
    exitCode = None
    output = None

    def __init__(self, exitCode, output):
        self.exitCode = exitCode
        self.output = output


class TestParser(BaseTestCase):
    def _getCmd(self, component, command, exitCode, filename, points):
        cmd = Cmd()

        # DeviceConfig no longer exists as of Zenoss 4.
        try:
            from Products.ZenRRD.zencommand import DeviceConfig
            cmd.deviceConfig = DeviceConfig()
        except ImportError:
            from Products.ZenCollector.services.config import DeviceProxy
            cmd.deviceConfig = DeviceProxy()

        cmd.deviceConfig.device = 'testDevice'
        cmd.component = component
        cmd.command = command
        cmd.eventClass = '/Cmd/Fail'
        cmd.eventKey = 'interfaceIncomingBytes'
        cmd.result = FakeCmdResult(exitCode, loadData(filename))
        cmd.points = points

        return cmd

    def _getListInterfacesCmd(self, exitCode, filename):
        points = []
        for dp_id in ('rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets'
                      'collisions', 'rx_dropped', 'tx_dropped',
                      'rx_crc_err', 'rx_frame_err', 'rx_errors', 'tx_errors',
                     ):
            dpc = DataPointConfig()
            dpc.id = dp_id
            dpc.component = 'interfaces'
            points.append(dpc)

        cmd = self._getCmd(
            'interface-6898492f-2d2e-439e-9370-a0073a0669f8',
            '/usr/bin/ovs-vsctl --columns=_uuid,statistics,external_ids,mac_in_use,name list interface',
            exitCode, filename, points)

        return cmd

    def testListInterfaces(self):
        parser = InterfaceStatisticsParser()
        results = ParsedResults()
        parser.processResults(
            self._getListInterfacesCmd(0, 'cmd_list_interfaces.txt'),
            results)

        self.assertEquals(len(results.values), 9)
        self.assertEquals(len(results.events), 0)

    def testListInterfaces_none(self):
        parser = InterfaceStatisticsParser()
        results = ParsedResults()
        parser.processResults(
            self._getListInterfacesCmd(0, 'cmd_list_interfaces_none.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 0)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestParser))
    return suite
