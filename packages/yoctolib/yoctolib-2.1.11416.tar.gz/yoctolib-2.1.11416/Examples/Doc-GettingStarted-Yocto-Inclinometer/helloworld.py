# ********************************************************************
#
#  $Id: helloworld.py 66454 2025-05-09 10:28:28Z seb $
#
#  An example that shows how to use a  Yocto-Inclinometer
#
#  You can find more information on our web site:
#   Yocto-Inclinometer documentation:
#      https://www.yoctopuce.com/EN/products/yocto-inclinometer/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_tilt import YTilt


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
    # retreive any tilt sensor
    sensor: YTilt = YTilt.FirstTilt()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
tilt1: YTilt = YTilt.FindTilt(target + ".tilt1")
tilt2: YTilt = YTilt.FindTilt(target + ".tilt2")
tilt3: YTilt = YTilt.FindTilt(target + ".tilt3")

if not (tilt1.isOnline()):
    die("Module not connected (check identification and USB cable)")

count: int = 0
while tilt1.isOnline():
    if count % 10 == 0:
        print("tilt1   tilt2   tilt3")
    print("%-7.1f " % tilt1.get_currentValue() + \
          "%-7.1f " % tilt2.get_currentValue() + \
          "%-7.1f " % tilt3.get_currentValue())
    count += 1
    YAPI.Sleep(250)
YAPI.FreeAPI()
