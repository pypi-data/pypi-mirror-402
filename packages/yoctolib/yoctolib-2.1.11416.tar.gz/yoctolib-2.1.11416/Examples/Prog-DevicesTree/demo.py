import sys
from typing import Union

from yoctolib.yocto_api import YRefParam, YAPI, YModule
from yoctolib.yocto_hubport import YHubPort


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg)


class YoctoShield(object):
    _serial: str
    _subDevices: list[str]

    def __init__(self, serial: str) -> None:
        self._serial = serial
        self._subDevices = []

    def getSerial(self) -> str:
        return self._serial

    def addSubdevice(self, serial: str) -> bool:
        for i in range(1, 5):
            p: YHubPort = YHubPort.FindHubPort("%s.hubPort%d" % (self._serial, i))
            if p.get_logicalName() == serial:
                self._subDevices.append(serial)
                return True
        return False

    def removeSubDevice(self, serial: str) -> None:
        if serial in self._subDevices:
            self._subDevices.remove(serial)

    def describe(self) -> None:
        print("  " + self._serial)
        for subdevice in self._subDevices:
            print("    " + subdevice)


class RootDevice(object):
    _serial: str
    _url: str
    _shields: list[YoctoShield]
    _subDevices: list[str]

    def __init__(self, serial: str, url: str) -> None:
        self._serial = serial
        self._url = url
        self._shields = []
        self._subDevices = []

    def getSerial(self) -> str:
        return self._serial

    def addSubDevice(self, serial: str) -> None:
        if serial[:7] == "YHUBSHL":
            self._shields.append(YoctoShield(serial))
        else:
            # Device to plug look if the device is plugged on a shield
            for shield in self._shields:
                if shield.addSubdevice(serial):
                    return
            self._subDevices.append(serial)

    def removeSubDevice(self, serial: str) -> None:
        if serial in self._subDevices:
            self._subDevices.remove(serial)
        for yoctoShield in reversed(list(self._shields)):
            if yoctoShield.getSerial() == serial:
                self._shields.remove(yoctoShield)
                break
            else:
                yoctoShield.removeSubDevice(serial)

    def describe(self) -> None:
        print(self._serial + " (" + self._url + ")")
        for subdevice in self._subDevices:
            print("  " + subdevice)
        for shield in self._shields:
            shield.describe()


__rootDevices: list[RootDevice] = []


def getYoctoHub(serial: str) -> Union[RootDevice, None]:
    for rootDevice in __rootDevices:
        if rootDevice.getSerial() == serial:
            return rootDevice
    return None


def addRootDevice(serial: str, url: str) -> RootDevice:
    for rootDevice in __rootDevices:
        if rootDevice.getSerial() == serial:
            return rootDevice
    rootDevice = RootDevice(serial, url)
    __rootDevices.append(rootDevice)
    return rootDevice


def showNetwork() -> None:
    print("**** device inventory *****")
    for hub in __rootDevices:
        hub.describe()


def deviceArrival(module: YModule) -> None:
    serial: str = module.get_serialNumber()
    parentHub: str = module.get_parentHub()
    if parentHub == "":
        # root device
        url: str = module.get_url()
        addRootDevice(serial, url)
    else:
        hub: Union[RootDevice, None] = getYoctoHub(parentHub)
        if hub is not None:
            hub.addSubDevice(serial)


def deviceRemoval(module: YModule) -> None:
    serial: str = module.get_serialNumber()
    for rootDevice in reversed(list(__rootDevices)):
        rootDevice.removeSubDevice(serial)
        if rootDevice.getSerial() == serial:
            __rootDevices.remove(rootDevice)


# the API use local USB devices through VirtualHub
errmsg: YRefParam = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    die("RegisterHub failed: " + errmsg.value)

if YAPI.RegisterHub("net", errmsg) != YAPI.SUCCESS:
    die("RegisterHub error: " + errmsg.value)

YAPI.RegisterDeviceArrivalCallback(deviceArrival)
YAPI.RegisterDeviceRemovalCallback(deviceRemoval)

print("Waiting for hubs to signal themselves...")
# wait for 5 seconds, doing nothing.
# noinspection InfiniteLoopStatement
while True:
    YAPI.UpdateDeviceList(errmsg)  # traps plug/unplug events
    YAPI.Sleep(1000, errmsg)  # traps others events
    showNetwork()
