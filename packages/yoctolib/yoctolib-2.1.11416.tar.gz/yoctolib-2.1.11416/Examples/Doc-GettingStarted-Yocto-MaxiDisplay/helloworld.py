# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-MaxiDisplay
#
#  You can find more information on our web site:
#   Yocto-MaxiDisplay documentation:
#      https://www.yoctopuce.com/EN/products/yocto-maxidisplay/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_display import YDisplay, YDisplayLayer


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
    # retrieve any humidity sensor
    tmp: YDisplay = YDisplay.FirstDisplay()
    if tmp is None:
        die('No module connected')
    target = tmp.get_serialNumber()

# retrieve specified functions
disp = YDisplay.FindDisplay(target + ".display")
if not disp.isOnline():
    die("Yocto-MaxiDisplay '%s' not connected" % target)

print("Use device %s" % disp.get_serialNumber())

# display clean up
disp.resetAll()

# retrieve the display size
w: int = disp.get_displayWidth()
h: int = disp.get_displayHeight()

# retrieve the first layer
l0: YDisplayLayer = disp.get_displayLayer(0)
l0.clear()

# display a text in the middle of the screen
l0.drawText(w // 2, h // 2, YDisplayLayer.ALIGN.CENTER, "Hello world!")

# visualize each corner
l0.moveTo(0, 5)
l0.lineTo(0, 0)
l0.lineTo(5, 0)
l0.moveTo(0, h - 6)
l0.lineTo(0, h - 1)
l0.lineTo(5, h - 1)
l0.moveTo(w - 1, h - 6)
l0.lineTo(w - 1, h - 1)
l0.lineTo(w - 6, h - 1)
l0.moveTo(w - 1, 5)
l0.lineTo(w - 1, 0)
l0.lineTo(w - 6, 0)

# draw a circle in the top left corner of layer 1
l1: YDisplayLayer = disp.get_displayLayer(1)
l1.clear()
l1.drawCircle(h // 8, h // 8, h // 8)

# and animate the layer
print("Use Ctrl-C to stop")
x: int = 0
y: int = 0
vx: int = 1
vy: int = 1
while disp.isOnline():
    x += vx
    y += vy
    if x < 0 or x > w - (h / 4):
        vx = -vx
    if y < 0 or y > h - (h / 4):
        vy = -vy
    l1.setLayerPosition(x, y, 0)
    YAPI.Sleep(5, errmsg)
YAPI.FreeAPI()
