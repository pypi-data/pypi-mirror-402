import sys

from yoctolib.yocto_api import YRefParam, YAPI, YSensor, YDataSet, YMeasure


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


def dumpSensor(sensor: YSensor) -> None:
    print("Using DataLogger of " + sensor.get_friendlyName())
    dataset: YDataSet = sensor.get_recordedData(0, 0)
    print("loading summary... ")
    dataset.loadMore()
    summary: YMeasure = dataset.get_summary()
    print("from %f to %f : min=%.3f%s avg=%.3f%s  max=%.3f%s" % (
        summary.get_startTimeUTC(),
        summary.get_endTimeUTC(),
        summary.get_minValue(), sensor.get_unit(),
        summary.get_averageValue(), sensor.get_unit(),
        summary.get_maxValue(), sensor.get_unit()))
    print("loading details :   0%")
    progress: int = 0
    while progress < 100:
        progress = dataset.loadMore()
        print("\b\b\b\b%3d%%" % progress)
    details: list[YMeasure] = dataset.get_measures()
    for measure in details:
        print("from %f to %f : min=%.3f%s avg=%.3f%s  max=%.3f%s" % (
            measure.get_startTimeUTC(),
            measure.get_endTimeUTC(),
            measure.get_minValue(), sensor.get_unit(),
            measure.get_averageValue(), sensor.get_unit(),
            measure.get_maxValue(), sensor.get_unit()))


def main() -> None:
    errmsg: YRefParam = YRefParam()
    # Setup the API to use local USB devices
    if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        sys.exit("init error" + errmsg.value)

    if len(sys.argv) == 1 or sys.argv[1] == 'any':
        sensor = YSensor.FirstSensor()
        if sensor is None:
            die("No module connected (check USB cable)")
    else:
        sensor = YSensor.FindSensor(sys.argv[1])
        if not sensor.isOnline():
            die("Sensor " + sensor.get_hardwareId() + " is not connected (check USB cable)")
    dumpSensor(sensor)
    YAPI.FreeAPI()


if __name__ == '__main__':
    main()
