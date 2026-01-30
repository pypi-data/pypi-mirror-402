import sys

from yoctolib.yocto_api import YRefParam, YAPI, YFunction, YMeasure, YSensor, YModule
from yoctolib.yocto_anbutton import YAnButton


def functionValueChangeCallback(fct: YFunction, value: str) -> None:
    info = fct.get_userData()
    print(info['hwId'] + ": " + value + " " + info['unit'] + " (new value)")


def sensorTimedReportCallback(fct: YSensor, measure: YMeasure):
    info = fct.get_userData()
    print(info['hwId'] + ": " + str(measure.get_averageValue()) + " " + info['unit'] + " (timed report)")


def configChangeCallback(mod: YModule) -> None:
    print(mod.get_serialNumber() + ": configuration change")


def beaconCallback(mod: YModule, beacon: int) -> None:
    print("%s: beacon changed to %d" % (mod.get_serialNumber(), beacon))


def deviceArrival(m: YModule) -> None:
    serial = m.get_serialNumber()
    print('Device arrival : ' + serial)
    m.registerConfigChangeCallback(configChangeCallback)
    m.registerBeaconCallback(beaconCallback)

    # First solution: look for a specific type of function (eg. anButton)
    fctcount: int = m.functionCount()
    for i in range(fctcount):
        hardwareId: str = serial + '.' + m.functionId(i)
        if hardwareId.find('.anButton') >= 0:
            print('- ' + hardwareId)
            bt: YAnButton = YAnButton.FindAnButton(hardwareId)
            bt.set_userData({'hwId': hardwareId, 'unit': ''})
            bt.registerValueCallback(functionValueChangeCallback)

    # Alternate solution: register any kind of sensor on the device
    sensor: YSensor = YSensor.FirstSensor()
    while sensor:
        if sensor.get_module().get_serialNumber() == serial:
            hardwareId: str = sensor.get_hardwareId()
            print('- ' + hardwareId)
            sensor.set_userData({'hwId': hardwareId, 'unit': sensor.get_unit()})
            sensor.registerValueCallback(functionValueChangeCallback)
            sensor.registerTimedReportCallback(sensorTimedReportCallback)
        sensor = sensor.nextSensor()


def deviceRemoval(m: YModule) -> None:
    print('Device removal : ' + m.get_serialNumber())


def logfun(line: str) -> None:
    print('LOG : ' + line.rstrip())


YAPI.RegisterLogFunction(logfun)
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
