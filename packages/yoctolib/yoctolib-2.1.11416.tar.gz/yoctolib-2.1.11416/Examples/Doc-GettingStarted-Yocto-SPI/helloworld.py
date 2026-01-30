# ********************************************************************
#
#  $Id: helloworld.py 66590 2025-05-13 08:29:43Z seb $
#
#  An example that shows how to use a  Yocto-SPI
#
#  You can find more information on our web site:
#   Yocto-SPI documentation:
#      https://www.yoctopuce.com/EN/products/yocto-spi/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_spiport import YSpiPort


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
    sensor: YSpiPort = YSpiPort.FirstSpiPort()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

spiPort: YSpiPort = YSpiPort.FindSpiPort(target + ".spiPort")
if spiPort is None:
    die('No module connected (check cable)')

# sample code driving MAX7219 7-segment display driver
# such as SPI7SEGDISP8.56 from www.embedded-lab.com
spiPort.set_spiMode("250000,3,msb")
spiPort.set_ssPolarity(YSpiPort.SSPOLARITY_ACTIVE_LOW)
spiPort.set_protocol("Frame:5ms")
spiPort.reset()

# do not forget to onfigure the powerOutput of the Yocto - SPI
# (for SPI7SEGDISP8.56 powerOutput need to be set at 5v)
print("****************************")
print("* make sure voltage levels *")
print("* are properly configured  *")
print("****************************")
value: int = 12345678
# initialize MAX7219
spiPort.writeHex('0c01')  # Exit from shutdown state
spiPort.writeHex('09ff')  # Enable BCD for all digits
spiPort.writeHex('0b07')  # Enable digits 0-7 (=8 in total)
spiPort.writeHex('0a0a')  # Set medium brightness
for i in range(1, 9):
    digit:int = value % 10
    spiPort.writeArray([i, digit])
    value = int(value / 10)

YAPI.FreeAPI()
