# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-PowerColor
#
#  You can find more information on our web site:
#   Yocto-PowerColor documentation:
#      https://www.yoctopuce.com/EN/products/yocto-powercolor/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_colorled import YColorLed


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
    # retreive any RGB led
    func: YColorLed = YColorLed.FirstColorLed()
    if func is None:
        die('No Yocto-Color connected')
    target = func.get_serialNumber()

led1: YColorLed = YColorLed.FindColorLed(target + '.colorLed1')

all_colors = [0xff0000, 0x00ff00, 0x0000ff]
for color in all_colors:
    print("Change color to 0x%06x" % color)
    led1.rgbMove(color, 1000)  # smooth transition
    YAPI.Sleep(1000)

YAPI.FreeAPI()
