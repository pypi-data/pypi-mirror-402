import asyncio
import sys

from yoctolib.yocto_api_aio import YRefParam, YAPI, YSensor, YDataSet, YMeasure, YDataStream


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


async def dumpSensor(sensor: YSensor) -> None:
    print("Using DataLogger of " +  sensor.get_friendlyName())
    dataset: YDataSet = await sensor.get_recordedData(0, 0)
    print("loading summary... ")
    await dataset.loadMore()
    summary: YMeasure = dataset.get_summary()
    print("from %f to %f : min=%.3f%s avg=%.3f%s  max=%.3f%s" % (
        summary.get_startTimeUTC(),
        summary.get_endTimeUTC(),
        summary.get_minValue(), await sensor.get_unit(),
        summary.get_averageValue(), await sensor.get_unit(),
        summary.get_maxValue(), await sensor.get_unit()))
    print("loading details :   0%")
    progress: int = 0
    while progress < 100:
        progress = await dataset.loadMore()
        print("\b\b\b\b%3d%%" % progress)
    details: list[YMeasure] = dataset.get_measures()
    for measure in details:
        print("from %f to %f : min=%.3f%s avg=%.3f%s  max=%.3f%s" % (
            measure.get_startTimeUTC(),
            measure.get_endTimeUTC(),
            measure.get_minValue(), await sensor.get_unit(),
            measure.get_averageValue(), await sensor.get_unit(),
            measure.get_maxValue(), await sensor.get_unit()))


async def main() -> None:
    errmsg: YRefParam = YRefParam()
    # Setup the API to use local USB devices
    if await YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        sys.exit("init error" + errmsg.value)

    if len(sys.argv) == 1 or sys.argv[1] == 'any':
        sensor = YSensor.FirstSensor()
        if sensor is None:
            die("No module connected (check USB cable)")
    else:
        sensor = YSensor.FindSensor(sys.argv[1])
        if not await sensor.isOnline():
            die("Sensor " + await sensor.get_hardwareId() + " is not connected (check USB cable)")
    await dumpSensor(sensor)
    await YAPI.FreeAPI()


if __name__ == '__main__':
    asyncio.run(main(), debug=False)
