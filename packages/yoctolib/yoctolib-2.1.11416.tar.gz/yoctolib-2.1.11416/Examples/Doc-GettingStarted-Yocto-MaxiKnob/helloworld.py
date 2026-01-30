# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-MaxiKnob
#
#  You can find more information on our web site:
#   Yocto-MaxiKnob documentation:
#      https://www.yoctopuce.com/EN/products/yocto-maxiknob/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import math
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_anbutton import YAnButton
from yoctolib.yocto_buzzer import YBuzzer
from yoctolib.yocto_colorledcluster import YColorLedCluster
from yoctolib.yocto_quadraturedecoder import YQuadratureDecoder


def die(msg) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


def notefreq(note: int) -> int:
    return int(220.0 * math.exp(note * math.log(2) / 12))


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
        die('No Yocto-MaxiKnob connected')
    target = func.get_serialNumber()

buz: YBuzzer = YBuzzer.FindBuzzer(target + ".buzzer")
leds: YColorLedCluster = YColorLedCluster.FindColorLedCluster(target + ".colorLedCluster")
button: YAnButton = YAnButton.FindAnButton(target + ".anButton1")
qd: YQuadratureDecoder = YQuadratureDecoder.FindQuadratureDecoder(target + ".quadratureDecoder1")

if not button.isOnline() or not qd.isOnline():
    sys.exit("Make sure the Yocto-MaxiKnob is configured with at least one AnButton and One Quadrature decoder.")

lastPos: int = math.floor(qd.get_currentValue())
buz.set_volume(100)
qd.set_edgesPerCycle(2)

print("press button 1, or turn the encoder")
while button.isOnline():
    if button.get_isPressed() and lastPos != 0:
        lastPos = 0
        qd.set_currentValue(0)
        buz.playNotes("'E32 C8")
        leds.set_rgbColor(0, 1, 0x000000)
    else:
        p:int = math.floor(qd.get_currentValue())
        if lastPos != p:
            lastPos = p
            buz.pulse(notefreq(p), 250)
            leds.set_hslColor(0, 1, 0x00FF7f | (p % 255) << 16)
YAPI.FreeAPI()
