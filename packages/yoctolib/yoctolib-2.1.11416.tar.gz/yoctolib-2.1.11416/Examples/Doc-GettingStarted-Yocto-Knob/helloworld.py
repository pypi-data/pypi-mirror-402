# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that show how to use a  Yocto-Knob
#
#  You can find more information on our web site:
#   Yocto-Knob documentation:
#      https://www.yoctopuce.com/EN/products/yocto-knob/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_anbutton import YAnButton


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
    # retrieve any compatible module
    func: YAnButton = YAnButton.FirstAnButton()
    if func is None:
        die('No Yocto-Knob connected')
    target = func.get_serialNumber()

# retrieve specified functions
channel1: YAnButton = YAnButton.FindAnButton(target + '.anButton1')
channel5: YAnButton = YAnButton.FindAnButton(target + '.anButton5')
if not channel1.isOnline():
    die("Yocto-Knob '%s' not connected" % target)

done: bool = False
while not done:
    line: str = ""
    if channel1.get_isPressed() == YAnButton.ISPRESSED_TRUE:
        line = "Button 1 pressed     "
    else:
        line = "Button 1 not pressed "
    line += ' - analog value: ' + str(channel1.get_calibratedValue())
    print(line)

    if channel5.get_isPressed() == YAnButton.ISPRESSED_TRUE:
        line = "Button 5 pressed     "
    else:
        line = "Button 5 not pressed "
    line += ' - analog value: ' + str(channel5.get_calibratedValue())
    print(line)

    print('(press both buttons simultaneously to exit)')
    done = (channel1.get_isPressed() == YAnButton.ISPRESSED_TRUE) and \
           (channel5.get_isPressed() == YAnButton.ISPRESSED_TRUE)
    YAPI.Sleep(1000)
YAPI.FreeAPI()
