# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Pressure
#
#  You can find more information on our web site:
#   Yocto-Pressure documentation:
#      https://www.yoctopuce.com/EN/products/yocto-pressure/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_pressure import YPressure


def die(msg):
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
    # retreive any pressure sensor
    sensor: YPressure = YPressure.FirstPressure()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
sensor: YPressure = YPressure.FindPressure(target + '.pressure')
if not sensor.isOnline():
    die("Yocto-Meteo '%s' not connected" % target)

print("Use device %s" % sensor.get_serialNumber())
while sensor.isOnline():
    print("Pressure :  " + "%2.1f" % sensor.get_currentValue() + "mbar (Ctrl-C to stop)")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
