# ********************************************************************
#
#  $Id: helloworld.py 66454 2025-05-09 10:28:28Z seb $
#
#  An example that shows how to use a  Yocto-PWM-Rx
#
#  You can find more information on our web site:
#   Yocto-PWM-Rx documentation:
#      https://www.yoctopuce.com/EN/products/yocto-pwm-rx/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_pwminput import YPwmInput


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
    # retreive any pwm input channel
    sensor: YPwmInput = YPwmInput.FirstPwmInput()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

pwm1: YPwmInput = YPwmInput.FindPwmInput(target + '.pwmInput1')
pwm2: YPwmInput = YPwmInput.FindPwmInput(target + '.pwmInput2')

if not pwm1.isOnline():
    die('device not connected')

while pwm1.isOnline():
    print("PWM1 : %.1fHz  %.1f%% %d   " % \
          (pwm1.get_frequency(), pwm1.get_dutyCycle(), pwm1.get_pulseCounter()))
    print("PWM2 : %.1fHz  %.1f%% %d   " % \
          (pwm2.get_frequency(), pwm2.get_dutyCycle(), pwm2.get_pulseCounter()))
    YAPI.Sleep(1000)
YAPI.FreeAPI()
