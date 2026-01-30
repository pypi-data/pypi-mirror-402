# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Proximity
#
#  You can find more information on our web site:
#   Yocto-Proximity documentation:
#      https://www.yoctopuce.com/EN/products/yocto-proximity/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************

import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_lightsensor import YLightSensor
from yoctolib.yocto_proximity import YProximity


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
    # retreive any proximity sensor
    sensor: YProximity = YProximity.FirstProximity()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
p: YProximity = YProximity.FindProximity(target + '.proximity1')

if not p.isOnline():
    die('device not connected')

al: YLightSensor = YLightSensor.FindLightSensor(target + '.lightSensor1')
ir: YLightSensor = YLightSensor.FindLightSensor(target + '.lightSensor2')

while p.isOnline():
    print("proximity :  " + str(int(p.get_currentValue())))
    print("ambient :  " + str(int(al.get_currentValue())))
    print("IR :  " + str(int(ir.get_currentValue())))
    YAPI.Sleep(1000)
YAPI.FreeAPI()
