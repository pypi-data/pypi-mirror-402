# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that show how to use a  Yocto-Thermocouple
#
#  You can find more information on our web site:
#   Yocto-Thermocouple documentation:
#      https://www.yoctopuce.com/EN/products/yocto-thermocouple/doc.html
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
if not channel1.isOnline():
    die("Yocto-Meteo '%s' not connected" % target)

print("Use device %s" % channel1.get_serialNumber())
while channel1.isOnline():
    print("Channel 1 temperature: %2.1f" % channel1.get_currentValue())
    print("Channel 2 temperature: %2.1f" % channel2.get_currentValue())
    print("  (press Ctrl-C to exit)")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
