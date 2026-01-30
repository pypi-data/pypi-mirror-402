import array
import sys

from yoctolib.yocto_api import YAPI, YRefParam
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

# retrieve the display size

w: int = disp.get_displayWidth()
h: int = disp.get_displayHeight()

# retrieve the first layer
l0: YDisplayLayer = disp.get_displayLayer(0)
count = 8
coord = array.array('b')
for i in range(1, 2 * count):
    coord.append(0)

# precompute the "leds" position
ledwidth:int = int(w / count)

for i in range(0, count):
    coord[i] = i * ledwidth
    coord[2 * count - i - 2] = coord[i]

framesCount :int = 2 * count - 2

# start recording
disp.newSequence()

# build one loop for recording
for i in range(0, framesCount):
    l0.selectColorPen(0)
    l0.drawBar(coord[(i + framesCount - 1) % framesCount], h - 1, coord[(i + framesCount - 1) % framesCount] + ledwidth, h - 4)
    l0.selectColorPen(0xffffff)
    l0.drawBar(coord[i], h - 1, coord[i] + ledwidth, h - 4)
    disp.pauseSequence(50)  # records a 50ms pause.

# self-call : causes an endless looop
disp.playSequence("K2000.seq")
# stop recording and save to device filesystem
disp.saveSequence("K2000.seq")

# play the sequence
disp.playSequence("K2000.seq")

YAPI.FreeAPI()
print("This animation is running in background.")
