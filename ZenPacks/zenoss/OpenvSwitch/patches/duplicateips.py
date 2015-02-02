##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import itertools

from Products.ZenModel.Exceptions import DeviceExistsError
from Products.ZenUtils.Utils import monkeypatch
from Products.Zuul.facades.devicefacade import DeviceFacade

ALLOW_DUPLICATES_IN = [
    '/Network/OpenvSwitch'
    ]


def alike_devclasses(devclass_a, devclass_b):
    """Return True if a and b are the same, or subclasses of each other."""
    return any(
        map(
            lambda x: x[0].getOrganizerName().startswith(x[1].getOrganizerName()),
            itertools.permutations([devclass_a, devclass_b])))


def allow_duplicate_for(deviceclass):
    """Return True if duplicate manageIp is allowed in deviceclass."""
    for dcname in ALLOW_DUPLICATES_IN:
        if deviceclass.getOrganizerName().startswith(dcname):
            return True

    return False


def allow_duplicate_between(devclass_a, devclass_b):
    """Return True if duplicate manageIp should be allowed."""
    if alike_devclasses(devclass_a, devclass_b):
        return False

    return sorted(
        map(
            allow_duplicate_for,
            [devclass_a, devclass_b])) == [False, True]


@monkeypatch('Products.ZenModel.DeviceClass.DeviceClass')
def _checkDeviceExists(self, deviceName, performanceMonitor, ip):
    """Return (deviceName, ip) if device doesn't exist.

    Raises DeviceExistsError if device already exists.

    Overridden by ZenPack to allow for duplicate IPs in some cases.

    """
    try:
        return original(self, deviceName, performanceMonitor, ip)
    except DeviceExistsError as e:
        if allow_duplicate_between(self, e.dev.deviceClass()):
            return deviceName, ip

        raise


@monkeypatch('Products.ZenModel.Device.Device')
def _isDuplicateIp(self, ip):
    """Return True if ip exists on another device. False otherwise.

    Overridden by ZenPack to allow for duplicate IPs in some cases.

    """
    ipMatch = self.getNetworkRoot().findIp(ip)
    if not ipMatch:
        return False

    device = ipMatch.device()
    if not device:
        return False

    if device.id == self.id:
        return False

    if allow_duplicate_between(self.deviceClass(), device.deviceClass()):
        return False

    return True


def noop(*args, **kwargs):
    """Take any arguments and return None."""
    return


@monkeypatch('Products.Zuul.routers.device.DeviceRouter')
def addDevice(self, *args, **kwargs):
    """
    Add a device.

    @type  deviceName: string
    @param deviceName: Name or IP of the new device
    @type  deviceClass: string
    @param deviceClass: The device class to add new device to
    @type  title: string
    @param title: (optional) The title of the new device (default: '')
    @type  snmpCommunity: string
    @param snmpCommunity: (optional) A specific community string to use for
                          this device. (default: '')
    @type  snmpPort: integer
    @param snmpPort: (optional) SNMP port on new device (default: 161)
    @type  manageIp: string
    @param manageIp: (optional) Management IP address on new device (default:
                     empty/derive from DNS)
    @type  locationPath: string
    @param locationPath: (optional) Organizer path of the location for this device
    @type  systemPaths: List (strings)
    @param systemPaths: (optional) List of organizer paths for the device
    @type  groupPaths: List (strings)
    @param groupPaths: (optional) List of organizer paths for the device
    @type  model: boolean
    @param model: (optional) True to model device at add time (default: False)
    @type  collector: string
    @param collector: (optional) Collector to use for new device (default:
                      localhost)
    @type  rackSlot: string
    @param rackSlot: (optional) Rack slot description (default: '')
    @type  productionState: integer
    @param productionState: (optional) Production state of the new device
                            (default: 1000)
    @type  comments: string
    @param comments: (optional) Comments on this device (default: '')
    @type  hwManufacturer: string
    @param hwManufacturer: (optional) Hardware manufacturer name (default: '')
    @type  hwProductName: string
    @param hwProductName: (optional) Hardware product name (default: '')
    @type  osManufacturer: string
    @param osManufacturer: (optional) OS manufacturer name (default: '')
    @type  osProductName: string
    @param osProductName: (optional) OS product name (default: '')
    @type  priority: integer
    @param priority: (optional) Priority of this device (default: 3)
    @type  tag: string
    @param tag: (optional) Tag number of this device (default: '')
    @type  serialNumber: string
    @param serialNumber: (optional) Serial number of this device (default: '')
    @rtype:   DirectResponse
    @return:  B{Properties}:
         - jobId: (string) ID of the add device job
    """
    facade = self._getFacade()
    organizerUid = '/zport/dmd/Devices' + kwargs['deviceClass']
    organizer = facade._getObject(organizerUid)

    try:
        organizer._checkDeviceExists(
            kwargs['deviceName'],
            kwargs['collector'],
            None)
    except DeviceExistsError:
        patch = False
    else:
        patch = True

    if patch:
        # We've already determined the device isn't already in Zenoss,
        # so make getDeviceByIpAddress temporarily not do anything.
        original_getDeviceByIpAddress = DeviceFacade.getDeviceByIpAddress
        DeviceFacade.getDeviceByIpAddress = noop

    r = original(self, *args, **kwargs)

    if patch:
        # Undo the patch so getDeviceByIpAddress works normally again.
        DeviceFacade.getDeviceByIpAddress = original_getDeviceByIpAddress

    return r


@monkeypatch('Products.Zuul.facades.devicefacade.DeviceFacade')
def addDevice(self, deviceName, deviceClass, title=None, snmpCommunity="",
              snmpPort=161, manageIp="", model=False, collector='localhost',
              rackSlot=0, productionState=1000, comments="",
              hwManufacturer="", hwProductName="", osManufacturer="",
              osProductName="", priority = 3, tag="", serialNumber="",
              locationPath="", systemPaths=[], groupPaths=[],
              zProperties={}, cProperties={},
              ):
    from Products.ZenUtils.IpUtil import isip

    zProps = dict(zSnmpCommunity=snmpCommunity,
                  zSnmpPort=snmpPort)
    zProps.update(zProperties)
    model = model and "Auto" or "none"
    perfConf = self._dmd.Monitors.getPerformanceMonitor(collector)

    # Make sure this patch only applies to OpenvSwitch device
    if title and isip(deviceName) and deviceClass == '/Network/OpenvSwitch':
        manageIp = deviceName
        deviceName = title

    jobStatus = perfConf.addDeviceCreationJob(deviceName=deviceName,
                                              devicePath=deviceClass,
                                              performanceMonitor=collector,
                                              discoverProto=model,
                                              manageIp=manageIp,
                                              zProperties=zProps,
                                              cProperties=cProperties,
                                              rackSlot=rackSlot,
                                              productionState=productionState,
                                              comments=comments,
                                              hwManufacturer=hwManufacturer,
                                              hwProductName=hwProductName,
                                              osManufacturer=osManufacturer,
                                              osProductName=osProductName,
                                              priority=priority,
                                              tag=tag,
                                              serialNumber=serialNumber,
                                              locationPath=locationPath,
                                              systemPaths=systemPaths,
                                              groupPaths=groupPaths,
                                              title=title)
    return jobStatus

@monkeypatch('Products.ZenHub.services.ModelerService.ModelerService')
def remote_getDeviceConfig(self, names, checkStatus=False):
    import logging
    log = logging.getLogger('zen.ModelerService')

    result = []
    for name in names:
        device = self.dmd.Devices.findDeviceByIdExact(name)
        if not device:
            continue
        device = device.primaryAq()
        skipModelMsg = ''

        if device.isLockedFromUpdates():
            skipModelMsg = "device %s is locked, skipping modeling" % device.id
        if checkStatus and (device.getPingStatus() > 0
                            or device.getSnmpStatus() > 0):
            skipModelMsg = "device %s is down skipping modeling" % device.id
        if (device.productionState <
                device.getProperty('zProdStateThreshold', 0)):
            skipModelMsg = "device %s is below zProdStateThreshold" % device.id
        if skipModelMsg:
            log.info(skipModelMsg)

        result.append(self.createDeviceProxy(device, skipModelMsg))
    return result


