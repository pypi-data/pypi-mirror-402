# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Altimeter
#
#  You can find more information on our web site:
#   Yocto-Altimeter documentation:
#      https://www.yoctopuce.com/EN/products/yocto-altimeter/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_altitude import YAltitude
from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_pressure import YPressure
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
    # retrieve any altitude sensor
    sensor: YAltitude = YAltitude.FirstAltitude()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
altSensor: YAltitude = YAltitude.FindAltitude(target + '.altitude')
pressSensor: YPressure = YPressure.FindPressure(target + '.pressure')
tempSensor: YTemperature = YTemperature.FindTemperature(target + '.temperature')

if not tempSensor.isOnline():
    die("Yocto-Altitude '%s' not connected" % target)

print("Use device %s" % altSensor.get_serialNumber())

while altSensor.isOnline():
    print("%4.1f" % altSensor.get_currentValue() + "m (QNH=" \
          + "%4.1f" % altSensor.get_qnh() + "hPa) " \
          + "%4.1f" % pressSensor.get_currentValue() + "hPa  " \
          + "%2.0f" % tempSensor.get_currentValue() + "deg C " \
          + "(Ctrl-c to stop)  ")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
