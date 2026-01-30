# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-Buzzer
#
#  You can find more information on our web site:
#   Yocto-Buzzer documentation:
#      https://www.yoctopuce.com/EN/products/yocto-buzzer/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_anbutton import YAnButton
from yoctolib.yocto_buzzer import YBuzzer
from yoctolib.yocto_led import YLed


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
    # retrieve any Buzzer
    func: YBuzzer = YBuzzer.FirstBuzzer()
    if func is None:
        die('No Yocto-Knob connected')
    target = func.get_serialNumber()

buz: YBuzzer = YBuzzer.FindBuzzer(target + ".buzzer")
led1: YLed = YLed.FindLed(target + ".led1")
led2: YLed = YLed.FindLed(target + ".led2")
button1: YAnButton = YAnButton.FindAnButton(target + ".anButton1")
button2: YAnButton = YAnButton.FindAnButton(target + ".anButton2")
print("press any of the test buttons")
while button1.isOnline():
    b1: int = button1.get_isPressed()
    b2: int = button2.get_isPressed()
    if b1 or b2:
        if b1:
            led = led1
            freq = 1500
        else:
            led = led2
            freq = 750
        led.set_power(YLed.POWER_ON)
        led.set_luminosity(100)
        led.set_blinking(YLed.BLINKING_PANIC)
        for i in range(5):  # this can be done using sequence as well
            buz.set_frequency(freq)
            buz.freqMove(2 * freq, 250)
            YAPI.Sleep(250)
        buz.set_frequency(0)
        led.set_power(YLed.POWER_OFF)
YAPI.FreeAPI()
