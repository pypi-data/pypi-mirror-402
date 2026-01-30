# ********************************************************************
#
#  $Id: helloworld.py 66589 2025-05-13 08:27:37Z seb $
#
#  An example that shows how to use a  Yocto-MaxiBuzzer
#
#  You can find more information on our web site:
#   Yocto-MaxiBuzzer documentation:
#      https://www.yoctopuce.com/EN/products/yocto-maxibuzzer/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_anbutton import YAnButton
from yoctolib.yocto_buzzer import YBuzzer
from yoctolib.yocto_colorled import YColorLed


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
    # retrieve any compatible module
    func: YBuzzer = YBuzzer.FirstBuzzer()
    if func is None:
        die('No Yocto-MaxiBuzzer connected')
    target = func.get_serialNumber()

buz: YBuzzer = YBuzzer.FindBuzzer(target + ".buzzer")
led: YColorLed = YColorLed.FindColorLed(target + ".colorLed")
button1: YAnButton = YAnButton.FindAnButton(target + ".anButton1")
button2: YAnButton = YAnButton.FindAnButton(target + ".anButton2")
print("press any of the test buttons")
while button1.isOnline():
    b1: int = button1.get_isPressed()
    b2: int = button2.get_isPressed()
    if b1 or b2:
        if b1:
            volume: int = 60
            freq: int = 1500
            color: int = 0xff0000
        else:
            volume = 30
            color = 0x00ff00
            freq = 750
        led.resetBlinkSeq()
        led.addRgbMoveToBlinkSeq(color, 100)
        led.addRgbMoveToBlinkSeq(0, 100)
        led.startBlinkSeq()
        buz.set_volume(volume)
        for i in range(5):  # this can be done using sequence as well
            buz.set_frequency(freq)
            buz.freqMove(2 * freq, 250)
            YAPI.Sleep(250)
        buz.set_frequency(0)
        led.stopBlinkSeq()
        led.set_rgbColor(0)
YAPI.FreeAPI()
