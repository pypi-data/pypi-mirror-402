# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-0-10V-Tx
#
#  You can find more information on our web site:
#   Yocto-0-10V-Tx documentation:
#      https://www.yoctopuce.com/EN/products/yocto-0-10v-tx/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_voltageoutput import YVoltageOutput


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
    # retrieve any VoltageOutput function
    tmp: YVoltageOutput = YVoltageOutput.FirstVoltageOutput()
    if tmp is None:
        die('No module connected')
    target = tmp.get_serialNumber()

# retrieve both channels
vout1: YVoltageOutput = YVoltageOutput.FindVoltageOutput(target + '.voltageOutput1')
vout2: YVoltageOutput = YVoltageOutput.FindVoltageOutput(target + '.voltageOutput2')

if not (vout1.isOnline()):
    die('device not connected')
voltages = [5.0, 10.0, 0.0]
for v in voltages:
    print("Change position to %f" % v)
    # output 1: immediate change
    vout1.set_currentVoltage(v)
    # output 2: smooth change
    vout2.voltageMove(v, 1000)
    YAPI.Sleep(1000)
YAPI.FreeAPI()

YAPI.FreeAPI()
