# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Temperature-IR
#
#  You can find more information on our web site:
#   Yocto-Temperature-IR documentation:
#      https://www.yoctopuce.com/EN/products/yocto-temperature-ir/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_temperature import YTemperature


def die(msg: str) -> None:
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
    # retrieve any humidity sensor
    sensor = YTemperature.FirstTemperature()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
channel1 = YTemperature.FindTemperature(target + '.temperature1')
channel2 = YTemperature.FindTemperature(target + '.temperature2')

while channel1.isOnline():
    print("Ambiant: " + "%2.1f / Infrared: " % channel1.get_currentValue() + \
          "%2.1f" % channel2.get_currentValue() + \
          " deg C (Ctrl-C to stop)")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
