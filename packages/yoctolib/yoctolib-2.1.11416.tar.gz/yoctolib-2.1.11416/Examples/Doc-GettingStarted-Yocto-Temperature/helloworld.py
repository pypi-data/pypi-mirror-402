# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that show how to use a  Yocto-Temperature
#
#  You can find more information on our web site:
#   Yocto-Temperature documentation:
#      https://www.yoctopuce.com/EN/products/yocto-temperature/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_temperature import YTemperature


def die(msg):
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


# the API use local USB devices through VirtualHub
errmsg = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub failed: " + errmsg.value)

# To use a specific device, invoke the script as
#   python helloworld.py [serial_number]
# or
#   python helloworld.py [logical_name]
target = 'any'
if len(sys.argv) > 1:
    target = sys.argv[1]

if target == 'any':
    # retreive any temperature sensor
    sensor = YTemperature.FirstTemperature()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
tempSensor = YTemperature.FindTemperature(target + '.temperature')
if not tempSensor.isOnline():
    die("Yocto-Temperature '%s' not connected" % target)

print("Use device %s" % tempSensor.get_serialNumber())
while tempSensor.isOnline():
    print("Temp :  " + "%2.1f" % tempSensor.get_currentValue() + "°C (Ctrl-C to stop)")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
