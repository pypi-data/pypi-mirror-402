import datetime
import sys

from yoctolib.yocto_api import YRefParam, YAPI, YSensor, YConsolidatedDataSet


def die(msg):
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


def main() -> None:
    # the API use local USB devices through VirtualHub
    errmsg: YRefParam = YRefParam()
    if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
        sys.exit("RegisterHub failed: " + errmsg.value)

    # Enumerate all connected sensors
    sensorList: list = []
    sensor: YSensor = YSensor.FirstSensor()
    while sensor is not None:
        sensorList.append(sensor)
        sensor = sensor.nextSensor()
    if len(sensorList) == 0:
        die("No Yoctopuce sensor connected (check USB cable)")

    # Generate consolidated CSV output for all sensors
    data = YConsolidatedDataSet(0, 0, sensorList)
    record = []
    while data.nextRecord(record) < 100:
        line = datetime.datetime.fromtimestamp(record[0]).isoformat()
        for idx in range(1, len(record)):
            line += ";%.3f" % record[idx]
        print(line)
    YAPI.FreeAPI()


if __name__ == '__main__':
    main()
