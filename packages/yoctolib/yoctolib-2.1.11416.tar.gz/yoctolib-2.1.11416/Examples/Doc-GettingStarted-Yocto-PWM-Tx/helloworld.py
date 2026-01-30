# ********************************************************************
#
#  $Id: helloworld.py 66588 2025-05-13 07:59:08Z seb $
#
#  An example that shows how to use a  Yocto-PWM-Tx
#
#  You can find more information on our web site:
#   Yocto-PWM-Tx documentation:
#      https://www.yoctopuce.com/EN/products/yocto-pwm-tx/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_pwmoutput import YPwmOutput


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
    # retreive any pwmoutput then find its serial #
    tmp: YPwmOutput = YPwmOutput.FirstPwmOutput()
    if tmp is None:
        die('No module connected')
    target = tmp.get_serialNumber()

pwmoutput1: YPwmOutput = YPwmOutput.FindPwmOutput(target + '.pwmOutput1')
pwmoutput2: YPwmOutput = YPwmOutput.FindPwmOutput(target + '.pwmOutput2')

if not pwmoutput1.isOnline():
    die('device not connected')

frequency: int = 450
duty_cycle: float = 50.0

# output 1: immediate change
pwmoutput1.set_frequency(frequency)
pwmoutput1.set_enabled(YPwmOutput.ENABLED_TRUE)
pwmoutput1.set_dutyCycle(duty_cycle)
# output 2: smooth change
pwmoutput2.set_frequency(frequency)
pwmoutput2.set_enabled(YPwmOutput.ENABLED_TRUE)
pwmoutput2.dutyCycleMove(duty_cycle, 3000)
YAPI.FreeAPI()
