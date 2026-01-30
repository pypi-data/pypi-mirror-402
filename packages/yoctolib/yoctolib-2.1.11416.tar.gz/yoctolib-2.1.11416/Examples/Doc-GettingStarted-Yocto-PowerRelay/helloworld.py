# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-PowerRelay
#
#  You can find more information on our web site:
#   Yocto-PowerRelay documentation:
#      https://www.yoctopuce.com/EN/products/yocto-powerrelay/doc.html
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
    # retrieve any Relay
    sensor = YRelay.FirstRelay()
    if sensor is None:
        die('No Yocto-PowerRelay connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
relay = YRelay.FindRelay(target + ".relay1")
if not (relay.isOnline()):
    die('device not connected')

print("Use device %s" % relay.get_serialNumber())

relay.set_state(YRelay.STATE_B)
YAPI.Sleep(500)
relay.set_state(YRelay.STATE_A)
YAPI.FreeAPI()
