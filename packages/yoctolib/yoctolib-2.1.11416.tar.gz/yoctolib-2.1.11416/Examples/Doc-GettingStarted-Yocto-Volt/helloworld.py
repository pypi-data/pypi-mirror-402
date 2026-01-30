# ********************************************************************
#
#  $Id: helloworld.py 66454 2025-05-09 10:28:28Z seb $
#
#  An example that shows how to use a  Yocto-Volt
#
#  You can find more information on our web site:
#   Yocto-Volt documentation:
#      https://www.yoctopuce.com/EN/products/yocto-volt/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_voltage import YVoltage


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
    # retreive any voltage sensor
    func: YVoltage = YVoltage.FirstVoltage()
    if func is None:
        die('No Yocto-Volt connected')
    target = func.get_serialNumber()


sensorDC = YVoltage.FindVoltage(target + '.voltage1')
sensorAC = YVoltage.FindVoltage(target + '.voltage2')

if not (sensorDC.isOnline()):
    die('device not connected')

while sensorDC.isOnline():
    print("Voltage : %3.2fV DC / %3.2fV AC (Ctrl-C to stop) " % \
          (sensorDC.get_currentValue(), sensorAC.get_currentValue()))
    YAPI.Sleep(1000)
YAPI.FreeAPI()
