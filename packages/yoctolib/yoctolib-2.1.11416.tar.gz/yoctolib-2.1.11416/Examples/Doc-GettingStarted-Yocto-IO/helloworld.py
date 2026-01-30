# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-IO
#
#  You can find more information on our web site:
#   Yocto-IO documentation:
#      https://www.yoctopuce.com/EN/products/yocto-io/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_digitalio import YDigitalIO


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
    # retrieve any DigitalIO function
    sensor: YDigitalIO = YDigitalIO.FirstDigitalIO()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

# retrieve specified functions
io: YDigitalIO = YDigitalIO.FindDigitalIO(target + '.digitalIO')
if not (io.isOnline()):
    die('device not connected')

print('using device ' + io.get_serialNumber())
# lets configure the channels direction
# bits 0..1 as output
# bits 2..3 as input
io.set_portDirection(0x03)
io.set_portPolarity(0)  # polarity set to regular
io.set_portOpenDrain(0)  # No open drain

print("Channels 0..1 are configured as outputs and channels 2..3")
print("are configured as inputs, you can connect some inputs to ")
print("outputs and see what happens")

outputdata: int = 0
while io.isOnline():
    inputdata: int = io.get_portState()  # read port values
    line: str = ""  # display part state value as binary
    for i in range(0, 4):
        if (inputdata & (8 >> i)) > 0:
            line += '1'
        else:
            line += '0'
    print(" port value = " + line)
    outputdata: int = (outputdata + 1) % 4  # cycle output 0..3
    io.set_portState(outputdata)  # We could have used set_bitState as well
    YAPI.Sleep(1000, errmsg)

print("Module disconnected")
YAPI.FreeAPI()
