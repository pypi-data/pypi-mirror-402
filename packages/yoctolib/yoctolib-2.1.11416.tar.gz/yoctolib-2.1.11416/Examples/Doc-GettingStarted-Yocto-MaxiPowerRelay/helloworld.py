# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-MaxiPowerRelay
#
#  You can find more information on our web site:
#   Yocto-MaxiPowerRelay documentation:
#      https://www.yoctopuce.com/EN/products/yocto-maxipowerrelay/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_relay import YRelay


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
    # retrieve any Relay sensor
    sensor: YRelay = YRelay.FirstRelay()
    if sensor is None:
        die('No Yocto-Relay connected')
    target = sensor.get_serialNumber()

print("Switch on all output")
for channel in range(1, 9):
    relay: YRelay = YRelay.FindRelay("%s.relay%d" % (target, channel))
    relay.set_output(YRelay.OUTPUT_ON)
    YAPI.Sleep(100)
YAPI.Sleep(500)
print("Switch off all output")
for channel in range(1, 9):
    relay: YRelay = YRelay.FindRelay("%s.relay%d" % (target, channel))
    relay.set_output(YRelay.OUTPUT_OFF)
    YAPI.Sleep(100)
YAPI.FreeAPI()
