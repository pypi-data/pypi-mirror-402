# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-WatchdogDC
#
#  You can find more information on our web site:
#   Yocto-WatchdogDC documentation:
#      https://www.yoctopuce.com/EN/products/yocto-watchdogdc/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_watchdog import YWatchdog


def die(msg: str) -> None:
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
    # retreive any Watchdog
    tmp: YWatchdog = YWatchdog.FirstWatchdog()
    if tmp is None:
        die('No module connected')
    target = tmp.get_serialNumber()

watchdog: YWatchdog = YWatchdog.FindWatchdog(target + ".watchdog1")

if not watchdog.isOnline():
    die('device not connected')

print("Starting watching dog")
watchdog.set_state(YWatchdog.RUNNING_ON)
print("waiting")
for i in range(12):
    YAPI.Sleep(10000)
    print("Resetting watching dog")
    watchdog.resetWatchdog()
    print("waiting")
print("Stopping watching dog")
watchdog.set_state(YWatchdog.RUNNING_OFF)
