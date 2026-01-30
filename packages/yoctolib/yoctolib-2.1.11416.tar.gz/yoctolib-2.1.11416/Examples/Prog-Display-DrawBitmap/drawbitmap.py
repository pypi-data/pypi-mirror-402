import math
import sys

from yoctolib.yocto_api import YAPI, YRefParam, xarray
from yoctolib.yocto_display import YDisplay, YDisplayLayer


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
    # retrieve any humidity sensor
    disp: YDisplay = YDisplay.FirstDisplay()
    if disp is None:
        die('No module connected')
    target = disp.get_serialNumber()

# retrieve specified functions
disp = YDisplay.FindDisplay(target + ".display")
if not disp.isOnline():
    die("Module not connected ")

disp.resetAll()
# retreive the display size
w: int = disp.get_displayWidth()
h: int = disp.get_displayHeight()

# reteive the first layer
l0: YDisplayLayer = disp.get_displayLayer(0)
bytesPerLines = int(w / 8)

data: xarray = xarray('B', [])
for i in range(0, h * bytesPerLines):
    data.append(0)

max_iteration: int = 50
centerX: float = 0.0
centerY: float = 0.0
targetX: float = 0.834555980181972
targetY: float = 0.204552998862566
zoom: float = 1.0
distance: float = 1.0

while True:
    for i in range(0, len(data)):
        data[i] = 0
    distance *= 0.95
    centerX = targetX * (1 - distance)
    centerY = targetY * (1 - distance)
    max_iteration = int(0.5 + max_iteration + math.sqrt(zoom))
    if max_iteration > 1500:
        max_iteration = 1500
    for j in range(0, h):
        for i in range(0, w):
            x0 = (((i - w / 2.0) / (w / 8)) / zoom) - centerX
            y0 = (((j - h / 2.0) / (w / 8)) / zoom) - centerY
            x = 0
            y = 0
            iteration = 0

            while (x * x + y * y < 4) and (iteration < max_iteration):
                xtemp = x * x - y * y + x0
                y = 2 * x * y + y0
                x = xtemp
                iteration += 1

            if iteration >= max_iteration:
                data[j * bytesPerLines + (i >> 3)] |= (128 >> (i & 7))

    l0.drawBitmap(0, 0, w, data, 0)
    zoom /= 0.95
