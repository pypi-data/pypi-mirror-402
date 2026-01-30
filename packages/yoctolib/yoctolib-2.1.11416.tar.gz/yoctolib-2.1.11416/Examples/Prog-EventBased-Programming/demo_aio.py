import asyncio
import sys

from yoctolib.yocto_api_aio import YRefParam, YAPI, YFunction, YMeasure, YSensor, YModule
from yoctolib.yocto_anbutton_aio import YAnButton


async def functionValueChangeCallback(fct: YFunction, value: str) -> None:
    info = fct.get_userData()
    print(info['hwId'] + ": " + value + " " + info['unit'] + " (new value)")


async def sensorTimedReportCallback(fct: YSensor, measure: YMeasure):
    info = fct.get_userData()
    print(info['hwId'] + ": " + str(measure.get_averageValue()) + " " + info['unit'] + " (timed report)")


async def configChangeCallback(mod: YModule) -> None:
    print(await mod.get_serialNumber() + ": configuration change")


async def beaconCallback(mod: YModule, beacon: int) -> None:
    print("%s: beacon changed to %d" % (await mod.get_serialNumber(), beacon))


async def deviceArrival(m: YModule) -> None:
    serial = await m.get_serialNumber()
    print('Device arrival : ' + serial)
    await m.registerConfigChangeCallback(configChangeCallback)
    await m.registerBeaconCallback(beaconCallback)

    # First solution: look for a specific type of function (eg. anButton)
    fctcount: int = m.functionCount()
    for i in range(fctcount):
        hardwareId: str = serial + '.' + m.functionId(i)
        if hardwareId.find('.anButton') >= 0:
            print('- ' + hardwareId)
            bt: YAnButton = YAnButton.FindAnButton(hardwareId)
            bt.set_userData({'hwId': hardwareId, 'unit': ''})
            await bt.registerValueCallback(functionValueChangeCallback)

    # Alternate solution: register any kind of sensor on the device
    sensor: YSensor = YSensor.FirstSensor()
    while sensor:
        if await (await sensor.get_module()).get_serialNumber() == serial:
            hardwareId: str = await sensor.get_hardwareId()
            print('- ' + hardwareId)
            sensor.set_userData({'hwId': hardwareId, 'unit': await sensor.get_unit()})
            await sensor.registerValueCallback(functionValueChangeCallback)
            await sensor.registerTimedReportCallback(sensorTimedReportCallback)
        sensor = sensor.nextSensor()


async def deviceRemoval(m: YModule) -> None:
    print('Device removal : ' + await m.get_serialNumber())


def logfun(line: str) -> None:
    print('LOG : ' + line.rstrip())


async def main() -> None:
    YAPI.RegisterLogFunction(logfun)
    # the API use local USB devices through VirtualHub
    errmsg: YRefParam = YRefParam()
    if await YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        sys.exit("RegisterHub failed: " + errmsg.value)

    await YAPI.RegisterDeviceArrivalCallback(deviceArrival)
    await YAPI.RegisterDeviceRemovalCallback(deviceRemoval)

    print('Hit Ctrl-C to Stop ')

    while True:
        await YAPI.UpdateDeviceList(errmsg)  # traps plug/unplug events
        await YAPI.Sleep(500, errmsg)  # traps others events


if __name__ == '__main__':
    asyncio.run(main(), debug=False)
