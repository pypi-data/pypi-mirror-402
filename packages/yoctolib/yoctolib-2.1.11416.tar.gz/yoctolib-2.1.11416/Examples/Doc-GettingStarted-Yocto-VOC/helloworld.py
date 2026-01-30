# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-VOC
#
#  You can find more information on our web site:
#   Yocto-VOC documentation:
#      https://www.yoctopuce.com/EN/products/yocto-voc/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_voc import YVoc


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
    # retrieve any voc sensor
    sensor = YVoc.FirstVoc()
    if sensor is None:
        die('No Yocto-VOC connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
sensor = YVoc.FindVoc(target + '.voc')
if not (sensor.isOnline()):
    die('device not connected')

print("Use device %s" % sensor.get_serialNumber())
while sensor.isOnline():
    print("VOC :  " + "%2.1f" % sensor.get_currentValue() + "ppm (Ctrl-C to stop)")
    YAPI.Sleep(1000)

YAPI.FreeAPI()
