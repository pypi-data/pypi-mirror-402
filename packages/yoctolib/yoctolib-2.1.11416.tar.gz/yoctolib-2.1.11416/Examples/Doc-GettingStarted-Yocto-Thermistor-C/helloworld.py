# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Thermistor-C
#
#  You can find more information on our web site:
#   Yocto-Thermistor-C documentation:
#      https://www.yoctopuce.com/EN/products/yocto-thermistor-c/doc.html
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
    # retrieve any temperature sensor
    sensor = YTemperature.FirstTemperature()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
channel1 = YTemperature.FindTemperature(target + '.temperature1')
channel2 = YTemperature.FindTemperature(target + '.temperature2')
channel3 = YTemperature.FindTemperature(target + '.temperature3')
channel4 = YTemperature.FindTemperature(target + '.temperature4')
channel5 = YTemperature.FindTemperature(target + '.temperature5')
channel6 = YTemperature.FindTemperature(target + '.temperature6')
if not channel1.isOnline():
    die("Yocto-Meteo '%s' not connected" % target)

print("Use device %s" % channel1.get_serialNumber())
while channel1.isOnline():
    print("| 1: " + "%2.1f " % channel1.get_currentValue() + \
          "| 2: " + "%2.1f " % channel2.get_currentValue() + \
          "| 3: " + "%2.1f " % channel3.get_currentValue() + \
          "| 4: " + "%2.1f " % channel4.get_currentValue() + \
          "| 5: " + "%2.1f " % channel5.get_currentValue() + \
          "| 6: " + "%2.1f " % channel6.get_currentValue() + \
          "| deg C |")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
