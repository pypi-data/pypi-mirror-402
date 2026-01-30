# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-RangeFinder
#
#  You can find more information on our web site:
#   Yocto-RangeFinder documentation:
#      https://www.yoctopuce.com/EN/products/yocto-rangefinder/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************

import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_lightsensor import YLightSensor
from yoctolib.yocto_rangefinder import YRangeFinder
from yoctolib.yocto_temperature import YTemperature


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


# the API use local USB devices through VirtualHub
errmsg: YRefParam = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub failed: " + errmsg.value)

# To use a specific device, invoke the script as
#   python helloworld.py [serial_number]
# or
#   python helloworld.py [logical_name]
target: str = 'any'
if len(sys.argv) > 1:
    target = sys.argv[1]

if target == 'any':
    # retrieve any Range finder
    sensor: YRangeFinder = YRangeFinder.FirstRangeFinder()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

rf: YRangeFinder = YRangeFinder.FindRangeFinder(target + '.rangeFinder1')

if not rf.isOnline():
    die('device not connected')

ir: YLightSensor = YLightSensor.FindLightSensor(target + '.lightSensor1')
tmp: YTemperature = YTemperature.FindTemperature(target + '.temperature1')

while rf.isOnline():
    print("Distance    :  " + str(int(rf.get_currentValue())))
    print("Ambiant IR  :  " + str(int(ir.get_currentValue())))
    print("Temperature :  " + str(int(tmp.get_currentValue())))
    YAPI.Sleep(1000)

YAPI.FreeAPI()
