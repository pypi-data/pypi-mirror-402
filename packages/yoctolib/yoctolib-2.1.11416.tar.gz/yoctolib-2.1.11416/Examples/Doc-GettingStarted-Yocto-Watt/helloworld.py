# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that show how to use a  Yocto-Knob
#
#  You can find more information on our web site:
#   Yocto-Watt documentation:
#      https://www.yoctopuce.com/EN/products/yocto-watt/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_power import YPower


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
    # retreive any Power sensor
    func: YPower = YPower.FirstPower()
    if func is None:
        die('No Yocto-Watt connected')
    target = func.get_serialNumber()

sensor: YPower = YPower.FindPower(target + '.power')

if not sensor.isOnline():
    die('device not connected')
while sensor.isOnline():
    print("Power :  " + "%2.1f" % sensor.get_currentValue() + "W (Ctrl-C to stop)")
    YAPI.Sleep(1000)
YAPI.FreeAPI()
