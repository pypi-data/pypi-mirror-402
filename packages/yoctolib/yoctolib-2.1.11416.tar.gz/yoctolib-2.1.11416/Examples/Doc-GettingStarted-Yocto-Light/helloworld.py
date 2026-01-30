# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Light
#
#  You can find more information on our web site:
#   Yocto-Light documentation:
#      https://www.yoctopuce.com/EN/products/yocto-light/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_lightsensor import YLightSensor


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
    # retrieve any light sensor
    sensor = YLightSensor.FirstLightSensor()
    if sensor is None:
        die('No Yocto-Light connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
sensor = YLightSensor.FindLightSensor(target + '.lightSensor')
if not (sensor.isOnline()):
    die('device not connected')

print("Use device %s" % sensor.get_serialNumber())
while sensor.isOnline():
    print("Light :  " + str(int(sensor.get_currentValue())) + " lx (Ctrl-C to stop)")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
