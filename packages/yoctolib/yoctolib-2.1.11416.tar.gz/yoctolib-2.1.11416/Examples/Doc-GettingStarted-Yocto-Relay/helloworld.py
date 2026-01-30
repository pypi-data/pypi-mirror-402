# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Relay
#
#  You can find more information on our web site:
#   Yocto-Relay documentation:
#      https://www.yoctopuce.com/EN/products/yocto-relay/doc.html
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
    # retrieve any Relay 
    sensor: YRelay = YRelay.FirstRelay()
    if sensor is None:
        die('No Yocto-Relay connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
relay1: YRelay = YRelay.FindRelay(target + ".relay1")
relay2: YRelay = YRelay.FindRelay(target + ".relay2")
if not (relay1.isOnline()):
    die('device not connected')

print("Use device %s" % relay1.get_serialNumber())

relay1.set_state(YRelay.STATE_B)
relay2.set_state(YRelay.STATE_B)
YAPI.Sleep(500)
relay1.set_state(YRelay.STATE_A)
relay2.set_state(YRelay.STATE_A)
YAPI.FreeAPI()
