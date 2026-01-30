import math
import sys

from yoctolib.yocto_api import YAPI, YRefParam
from yoctolib.yocto_display import YDisplay, YDisplayLayer


def die(msg: str) -> None:
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


# this is the recusive function to draw 1/3nd of the Von Koch flake
def recursiveLine(layer: YDisplayLayer, x0: float, y0: float, x1: float, y1: float, deep: int):
    if deep <= 0:
        layer.moveTo(int(x0 + 0.5), int(y0 + 0.5))
        layer.lineTo(int(x1 + 0.5), int(y1 + 0.5))
    else:
        dx = (x1 - x0) / 3
        dy = (y1 - y0) / 3
        mx = ((x0 + x1) / 2) + (0.87 * (y1 - y0) / 3)
        my = ((y0 + y1) / 2) - (0.87 * (x1 - x0) / 3)
        recursiveLine(layer, x0, y0, x0 + dx, y0 + dy, deep - 1)
        recursiveLine(layer, x0 + dx, y0 + dy, mx, my, deep - 1)
        recursiveLine(layer, mx, my, x1 - dx, y1 - dy, deep - 1)
        recursiveLine(layer, x1 - dx, y1 - dy, x1, y1, deep - 1)


# setup the API to use local USB devices
errmsg: YRefParam = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub failed: " + errmsg.value)

# In order to use a specific device, invoke the script as
#   python doubleBuffering.py [serial_number]
# or
#   python doubleBuffering.py [logical_name]
target: str = 'any'
if len(sys.argv) > 1:
    target = sys.argv[1]

if target == 'any':
    # retrieve any compatible module
    disp: YDisplay = YDisplay.FirstDisplay()
    if disp is None:
        die('No display module connected')
    target = disp.get_serialNumber()

# retrieve specified module
disp = YDisplay.FindDisplay(target + ".display")
if not disp.isOnline():
    die("Display '%s' not connected" % target)

# display clean up
disp.resetAll()

l1: YDisplayLayer = disp.get_displayLayer(1)
l2: YDisplayLayer = disp.get_displayLayer(2)
l1.hide()  # L1 is hidden, l2 stays visible
centerX: int = disp.get_displayWidth() // 2
centerY: int = disp.get_displayHeight() // 2
radius: float = disp.get_displayHeight() / 2
a: int = 0

while True:
    # we draw in the hidden layer
    l1.clear()
    for i in range(0, 3):
        recursiveLine(l1, centerX + radius * math.cos(a + i * 2.094),
                      centerY + radius * math.sin(a + i * 2.094),
                      centerX + radius * math.cos(a + (i + 1) * 2.094),
                      centerY + radius * math.sin(a + (i + 1) * 2.094), 2)
    # then we swap contents with the visible layer

    disp.swapLayerContent(1, 2)
    # change the flake angle
    a += 0.1257
