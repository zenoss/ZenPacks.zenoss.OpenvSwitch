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

from Products.ZenRRD.CommandParser import ParsedResults
from Products.ZenRRD.zencommand import Cmd, DataPointConfig
from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ..parsers.BridgeStatistics import BridgeStatistics as BridgeStatisticsParser
from ..parsers.InterfaceStatistics import InterfaceStatistics as InterfaceStatisticsParser
from ..parsers.OVSStatus import OVSStatus as OVSStatusParser
from ..parsers.BridgePortStatus import BridgePortStatus as BPStatusParser
from ..parsers.InterfaceStatus import InterfaceStatus as IFStatusParser

from .util import loadData


class FakeCmdResult(object):
    exitCode = None
    output = None
    stderr = None

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
        # Since we only consider the OVS records within cycleTime for event
        # processing, we need to do something so that records for unittests
        # will always be processed. This is achieved by
        # setting a huge value for cycleTime
        cmd.cycleTime = 1430000000

        return cmd

    def _getDumpAggregateCmd(self, exitCode, filename):
        points = []
        for dp_id in ('packet_count', 'byte_count', 'flow_count',):
            dpc = DataPointConfig()
            dpc.id = dp_id
            dpc.component = 'bridges'
            points.append(dpc)

        cmd = self._getCmd(
            'bridge-3fe10504-e059-4398-8b12-b7627e7b5b95',
            '/usr/bin/ovs-ofctl dump-aggregate br-int',
            exitCode, filename, points)

        return cmd

    def testDumpAggregate(self):
        parser = BridgeStatisticsParser()
        results = ParsedResults()
        parser.processResults(
            self._getDumpAggregateCmd(0, 'cmd_dump_aggregate.txt'),
            results)

        self.assertEquals(len(results.values), 3)
        self.assertEquals(len(results.events), 0)

    def testDumpAggregate_none(self):
        parser = InterfaceStatisticsParser()
        results = ParsedResults()
        parser.processResults(
            self._getDumpAggregateCmd(0, 'cmd_dump_aggregate_none.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 0)


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

    def _getCentOSOVSRunningCmd(self, exitCode, filename):
        points = []

        cmd = self._getCmd(
            '',
            '/bin/echo "BEGIN" ; /sbin/service openvswitch status 2> /dev/null ; echo "SPLIT" ; /usr/bin/systemctl status openvswitch-nonetwork.service 2> /dev/null ; echo "SPLIT" ; /usr/bin/sudo service openvswitch-switch status 2> /dev/null ; echo "END"',
            exitCode, filename, points)

        return cmd

    def testCentOS6NotRunning(self):
        parser = OVSStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getCentOSOVSRunningCmd(0, 'centos_6_ovs_not_running.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)

    def testCentOS6Running(self):
        parser = OVSStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getCentOSOVSRunningCmd(0, 'centos_6_ovs_running.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)

    def testCentOS7NotRunning(self):
        parser = OVSStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getCentOSOVSRunningCmd(0, 'centos_7_ovs_not_running.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)

    def testCentOS7Running(self):
        parser = OVSStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getCentOSOVSRunningCmd(0, 'centos_7_ovs_running.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)

    def _getBridgePortStatusCmd(self, exitCode, filename):
        points = []

        cmd = self._getCmd(
            '',
            '/usr/bin/sudo /usr/bin/ovsdb-tool show-log',
            exitCode, filename, points)

        return cmd

    def testBridgePortStatus(self):
        parser = BPStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getBridgePortStatusCmd(0, 'bridge_port_status.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 5)

    def _getInterfaceStatusCmd(self, id, exitCode, filename):
        points = []

        cmd = self._getCmd(
            id,
            '/usr/bin/sudo /usr/bin/ovs-vsctl --columns=_uuid,admin_state,link_state list interface',
            exitCode, filename, points)

        return cmd

    def testInterfaceStatusAUPIUP(self):
        parser = IFStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getInterfaceStatusCmd('interface-35da03b8-1f47-4e82-b89a-d06a866d522f',
                                        0, 'iface_status.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)

    def testInterfaceStatusAUPIDOWN(self):
        parser = IFStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getInterfaceStatusCmd('interface-23128125-cc93-492e-9afd-b75334ad1cc8',
                                        0, 'iface_status.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)

    def testInterfaceStatusADOWNIDOWN(self):
        parser = IFStatusParser()
        results = ParsedResults()
        parser.processResults(
            self._getInterfaceStatusCmd('interface-fb498511-3c18-4483-85d3-c4b3103719ca',
                                        0, 'iface_status.txt'),
            results)

        self.assertEquals(len(results.values), 0)
        self.assertEquals(len(results.events), 1)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestParser))
    return suite
