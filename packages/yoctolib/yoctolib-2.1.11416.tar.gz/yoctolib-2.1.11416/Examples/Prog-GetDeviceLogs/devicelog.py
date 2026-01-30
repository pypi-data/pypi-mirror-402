import sys

from yoctolib.yocto_api import YRefParam, YAPI, YModule


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


def logfun(m: YModule, s: str) -> None:
    print(m.get_serialNumber() + ' : ' + s)


def deviceArrival(m: YModule) -> None:
    serial = m.get_serialNumber()
    print('Device arrival : ' + serial)
    m.registerLogCallback(logfun)


def deviceRemoval(m: YModule) -> None:
    print('Device removal : ' + m.get_serialNumber())


# the API use local USB devices through VirtualHub
errmsg: YRefParam = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub failed: " + errmsg.value)

YAPI.RegisterDeviceArrivalCallback(deviceArrival)
YAPI.RegisterDeviceRemovalCallback(deviceRemoval)

print('Hit Ctrl-C to Stop ')
while True:
    YAPI.UpdateDeviceList(errmsg)  # traps plug/unplug events
    YAPI.Sleep(500, errmsg)  # traps others events
