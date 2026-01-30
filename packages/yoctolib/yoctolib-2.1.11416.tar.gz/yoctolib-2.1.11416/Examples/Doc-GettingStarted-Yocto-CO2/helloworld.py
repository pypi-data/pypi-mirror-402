# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that show how to use a  Yocto-CO2
#
#  You can find more information on our web site:
#   Yocto-CO2 documentation:
#      https://www.yoctopuce.com/EN/products/yocto-co2/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_carbondioxide import YCarbonDioxide


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
    # retrieve any CO2 sensor
    sensor = YCarbonDioxide.FirstCarbonDioxide()
    if sensor is None:
        die('No Yocto-C02 connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
sensor = YCarbonDioxide.FindCarbonDioxide(target + '.carbonDioxide')
if not (sensor.isOnline()):
    die('device not connected')

print("Use device %s" % sensor.get_serialNumber())
while sensor.isOnline():
    print("CO2 :  " + "%2.1f" % sensor.get_currentValue() + "ppm (Ctrl-C to stop)")
    YAPI.Sleep(1000)

YAPI.FreeAPI()
