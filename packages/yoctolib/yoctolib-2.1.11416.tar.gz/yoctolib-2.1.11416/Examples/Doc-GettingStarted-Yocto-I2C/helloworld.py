# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-I2C
#
#  You can find more information on our web site:
#   Yocto-I2C documentation:
#      https://www.yoctopuce.com/EN/products/yocto-i2c/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_i2cport import YI2cPort


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
    # retrieve any I2c port
    tmp: YI2cPort = YI2cPort.FirstI2cPort()
    if tmp is None:
        die('No module connected')
    target = tmp.get_serialNumber()

# retrieve specified functions
i2cPort: YI2cPort = YI2cPort.FindI2cPort(target + ".i2cPort")

# sample code reading MCP9804 temperature sensor
i2cPort.set_i2cMode("100kbps")
i2cPort.set_i2cVoltageLevel(YI2cPort.I2CVOLTAGELEVEL_3V3)
i2cPort.reset()
# do not forget to configure the powerOutput and
# of the Yocto-I2C as well if used
print("****************************")
print("* make sure voltage levels *")
print("* are properly configured  *")
print("****************************")

toSend: list[int] = [0x05]
received: list[int] = i2cPort.i2cSendAndReceiveArray(0x1f, toSend, 2)
tempReg:int = (received[0] << 8) + received[1]
if tempReg & 0x1000:
    tempReg -= 0x2000  # perform sign extension
else:
    tempReg &= 0x0fff  # clear status bits
print("Ambient temperature: " + str(tempReg / 16.0))

YAPI.FreeAPI()
