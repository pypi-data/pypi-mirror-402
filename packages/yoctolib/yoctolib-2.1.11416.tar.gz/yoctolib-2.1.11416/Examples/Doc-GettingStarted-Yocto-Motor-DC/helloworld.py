# ********************************************************************
#
#  $Id: helloworld.py 66453 2025-05-09 10:25:49Z seb $
#
#  An example that show how to use a  Yocto-Thermocouple
#
#  You can find more information on our web site:
#   Yocto-Motor-DC documentation:
#      https://www.yoctopuce.com/EN/products/yocto-motor-dc/doc.html
#   Python API Reference:
#      https://www.yoctopuce.com/EN/doc/reference/yoctolib-typedpython-EN.html
#
# *********************************************************************

import sys

from yoctolib.yocto_api import YRefParam, YAPI
from yoctolib.yocto_current import YCurrent
from yoctolib.yocto_motor import YMotor
from yoctolib.yocto_temperature import YTemperature
from yoctolib.yocto_voltage import YVoltage


def die(msg):
    YAPI.FreeAPI()
    sys.exit(msg + ' (check USB cable)')


# the API use local USB devices through VirtualHub
errmsg = YRefParam()
if YAPI.RegisterHub("localhost", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub failed: " + errmsg.value)

# To use a specific device, invoke the script as
#   python helloworld.py [serial_number]
# or
#   python helloworld.py [logical_name]
target = 'any'
if len(sys.argv) > 1:
    target = sys.argv[1]

if target == 'any':
    # find any motor then retreive its serial #
    motor = YTemperature.FirstTemperature()
    if motor is None:
        die('No module connected')
    target = motor.get_serialNumber()

# retrieve specified functions
motor = YMotor.FindMotor(target + '.motor')
current = YCurrent.FindCurrent(target + '.current')
voltage = YVoltage.FindVoltage(target + '.voltage')
temperature = YTemperature.FindTemperature(target + '.temperature')

power: int = 100
if motor.isOnline():
    # if the motor is in error state, reset it.
    if motor.get_motorStatus() >= YMotor.MOTORSTATUS_LOVOLT:
        motor.resetStatus()
    motor.drivingForceMove(power, 2000)  # ramp up to power in 2 seconds
    while motor.isOnline():
        print("Status :  " + motor.get_advertisedValue() +
              " Current : " + "%2.1f" % (current.get_currentValue() / 1000) + "A  " + \
              "Voltage : " + "%2.1f" % (voltage.get_currentValue()) + "V  " + \
              "Temperature : " + "%2.1f" % (temperature.get_currentValue()) + "deg C")
        YAPI.Sleep(1000, errmsg)
else:
    die('device not connected')
YAPI.FreeAPI()
