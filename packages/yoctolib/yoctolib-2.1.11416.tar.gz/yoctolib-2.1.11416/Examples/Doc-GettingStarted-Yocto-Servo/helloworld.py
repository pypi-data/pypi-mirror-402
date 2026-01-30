# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Servo
#
#  You can find more information on our web site:
#   Yocto-Servo documentation:
#      https://www.yoctopuce.com/EN/products/yocto-servo/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_servo import YServo


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
    # retreive any servo then find its serial #
    servo: YServo = YServo.FirstServo()
    if servo is None:
        die('No module connected')
    target = servo.get_serialNumber()

# retrieve specified functions
servo1: YServo = YServo.FindServo(target + ".servo1")
servo5: YServo = YServo.FindServo(target + ".servo5")
if not servo1.isOnline():
    die("Yocto-Servo '%s' not connected" % target)

print("Use device %s" % servo1.get_serialNumber())

positions = [-1000, 1000, 0]
for pos in positions:
    print("Change position to %d" % pos)
    servo1.set_position(pos)  # immediate transition
    servo5.move(pos, 1000)  # smooth transition
    YAPI.Sleep(1000)
YAPI.FreeAPI()
