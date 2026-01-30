# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Color-V2
#
#  You can find more information on our web site:
#   Yocto-Color-V2 documentation:
#      https://www.yoctopuce.com/EN/products/yocto-color-v2/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_colorledcluster import YColorLedCluster


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
    func: YColorLedCluster = YColorLedCluster.FirstColorLedCluster()
    if func is None:
        die('No Yocto-Color-V2 connected')
    target = func.get_serialNumber()

ledCluster: YColorLedCluster = YColorLedCluster.FindColorLedCluster(target + '.colorLedCluster')

nb_leds: int = 2
ledCluster.set_activeLedCount(nb_leds)
ledCluster.set_ledType(YColorLedCluster.LEDTYPE_RGB)

all_colors = [0xff0000, 0x00ff00, 0x0000ff]
for color in all_colors:
    print("Change color to 0x%06x" % color)
    # immediate transition for fist half of leds
    ledCluster.set_rgbColor(0, nb_leds // 2, color)
    # immediate transition for second half of leds
    ledCluster.rgb_move(nb_leds // 2, nb_leds // 2, color, 1000)
    YAPI.Sleep(1000)

YAPI.FreeAPI()
