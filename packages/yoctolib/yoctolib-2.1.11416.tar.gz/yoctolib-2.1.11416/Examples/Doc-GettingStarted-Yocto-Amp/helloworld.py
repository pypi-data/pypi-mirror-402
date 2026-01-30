# ********************************************************************
#
#  $Id: helloworld.py 66454 2025-05-09 10:28:28Z seb $
#
#  An example that shows how to use a  Yocto-Amp
#
#  You can find more information on our web site:
#   Yocto-Amp documentation:
#      https://www.yoctopuce.com/EN/products/yocto-amp/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_current import YCurrent


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
    # retreive any voltage sensor (can be AC or DC)
    func: YCurrent = YCurrent.FirstCurrent()
    if func is None:
        die('No Yocto-Amp connected')
    target = func.get_serialNumber()

# we need to retrieve both DC and AC voltage from the device.
sensorDC: YCurrent = YCurrent.FindCurrent(target + '.current1')
sensorAC: YCurrent = YCurrent.FindCurrent(target + '.current2')

if not sensorAC.isOnline():
    die('Module not connected')

while sensorAC.isOnline():
    print('DC: ' + str(sensorDC.get_currentValue()) + ' mA ' + \
          'AC: ' + str(sensorAC.get_currentValue()) + ' mA ')
    print('  (press Ctrl-C to exit)')
    YAPI.Sleep(1000, errmsg)
YAPI.FreeAPI()
