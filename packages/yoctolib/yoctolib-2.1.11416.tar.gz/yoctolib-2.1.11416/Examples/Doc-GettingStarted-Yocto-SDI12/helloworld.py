# ********************************************************************
#
#  $Id: helloworld.py 66616 2025-05-13 09:24:35Z seb $
#
#  An example that shows how to use a  Yocto-SDI12
#
#  You can find more information on our web site:
#   Yocto-SDI12 documentation:
#      https://www.yoctopuce.com/EN/products/yocto-sdi12/doc.html
#   Python V2 API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************
import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_sdi12port import YSdi12Port


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
    # retrieve any SDI12 sensor
    sensor: YSdi12Port = YSdi12Port.FirstSdi12Port()
    if sensor is None:
        die('No module connected')
    target = sensor.get_serialNumber()

sdi12Port: YSdi12Port = YSdi12Port.FindSdi12Port(target + ".sdi12Port")
if not sdi12Port.isOnline():
    sys.exit('Module not connected')

singleSensor = sdi12Port.discoverSingleSensor()
print("%-35s %s " % ("Sensor address :", singleSensor.get_sensorAddress()))
print("%-35s %s " % ("Sensor SDI-12 compatibility : ", singleSensor.get_sensorProtocol()))
print("%-35s %s " % ("Sensor company name : ", singleSensor.get_sensorVendor()))
print("%-35s %s " % ("Sensor model number : ", singleSensor.get_sensorModel()))
print("%-35s %s " % ("Sensor version : ", singleSensor.get_sensorVersion()))
print("%-35s %s " % ("Sensor serial number : ", singleSensor.get_sensorSerial()))

valSensor: list[float] = sdi12Port.readSensor(singleSensor.get_sensorAddress(), "M", 5000)
i: int = 0
while i < len(valSensor):
    if singleSensor.get_measureCount() > 1:
        print("{0} : {1:8.2f} {2:8s} ({3})".format(singleSensor.get_measureSymbol(i),
                                                   valSensor[i], singleSensor.get_measureUnit(i),
                                                   singleSensor.get_measureDescription(i)))
    else:
        print(valSensor[i])
    i += 1

YAPI.FreeAPI()
