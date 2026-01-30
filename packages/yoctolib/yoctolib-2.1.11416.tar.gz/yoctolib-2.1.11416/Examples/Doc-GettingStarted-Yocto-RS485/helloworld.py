# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that shows how to use a  Yocto-RS485
#
#  You can find more information on our web site:
#   Yocto-RS485 documentation:
#      https://www.yoctopuce.com/EN/products/yocto-rs485/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_serialport import YSerialPort


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
    # retrieve any serial port
    sensor: YSerialPort = YSerialPort.FirstSerialPort()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

serialPort: YSerialPort = YSerialPort.FindSerialPort(target + ".serialPort")
print("Please enter the MODBUS slave address (1...255)")
slave: int = 0
while (slave < 1) or (slave > 255):
    slave = int(input("slave: "))  # use raw_input in python 2.x

reg: int = 0
while (reg < 1) or (reg >= 50000) or (reg % 10000) == 0:
    print("Please select a Coil No (>=1), Input Bit No (>=10001),")
    print("Input Register No (>=30001) or Register No (>=40001)")
    reg = int(input("No: "))  # use raw_input in python 2.x

while serialPort.isOnline():
    if reg >= 40001:
        val: int = serialPort.modbusReadRegisters(slave, reg - 40001, 1)[0]
    elif reg >= 30001:
        val = serialPort.modbusReadInputRegisters(slave, reg - 30001, 1)[0]
    elif reg >= 10001:
        val = serialPort.modbusReadInputBits(slave, reg - 10001, 1)[0]
    else:
        val = serialPort.modbusReadBits(slave, reg - 1, 1)[0]

    print("Current value: %d " % val)
    print("Press ENTER to read again, Q to quit")
    if (reg % 40000) < 10000:
        print(" or enter a new value")

    cmd: str = input(": ")  # use raw_input in python 2.x
    if (cmd == "q") or (cmd == "Q"):
        die('')

    if cmd != "" and ((reg % 40000) < 10000):
        val = int(cmd)
        if reg >= 40001:
            serialPort.modbusWriteRegister(slave, reg - 40001, val)
        else:
            serialPort.modbusWriteBit(slave, reg - 1, val)
YAPI.FreeAPI()
