# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YStepperMotor
#
#  - - - - - - - - - License information: - - - - - - - - -
#
#  Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.
#
#  Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
#  non-exclusive license to use, modify, copy and integrate this
#  file into your software for the sole purpose of interfacing
#  with Yoctopuce products.
#
#  You may reproduce and distribute copies of this file in
#  source or object form, as long as the sole purpose of this
#  code is to interface with Yoctopuce products. You must retain
#  this notice in the distributed source file.
#
#  You should refer to Yoctopuce General Terms and Conditions
#  for additional information regarding your rights and
#  obligations.
#
#  THE SOFTWARE AND DOCUMENTATION ARE PROVIDED 'AS IS' WITHOUT
#  WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
#  WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
#  EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
#  INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
#  COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR
#  SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT
#  LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
#  CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
#  BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
#  WARRANTY, OR OTHERWISE.
#
# *********************************************************************
"""
Yoctopuce library: High-level API for YStepperMotor
version: PATCH_WITH_VERSION
requires: yocto_steppermotor_aio
requires: yocto_api
provides: YStepperMotor
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union, Final
    from collections.abc import Callable, Awaitable
    const = lambda obj: obj
    _IS_MICROPYTHON = False
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_steppermotor_aio import YStepperMotor as YStepperMotor_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YStepperMotor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YStepperMotorValueCallback = Union[Callable[['YStepperMotor', str], Any], None]
    except TypeError:
        YStepperMotorValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YStepperMotor(YFunction):
    """
    The YStepperMotor class allows you to drive a stepper motor.

    """
    _aio: YStepperMotor_aio
    # --- (end of YStepperMotor class start)
    if not _IS_MICROPYTHON:
        # --- (YStepperMotor return codes)
        DIAGS_INVALID: Final[int] = YAPI.INVALID_UINT
        STEPPOS_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SPEED_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PULLINSPEED_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        MAXACCEL_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        MAXSPEED_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        OVERCURRENT_INVALID: Final[int] = YAPI.INVALID_UINT
        TCURRSTOP_INVALID: Final[int] = YAPI.INVALID_UINT
        TCURRRUN_INVALID: Final[int] = YAPI.INVALID_UINT
        ALERTMODE_INVALID: Final[str] = YAPI.INVALID_STRING
        AUXMODE_INVALID: Final[str] = YAPI.INVALID_STRING
        AUXSIGNAL_INVALID: Final[int] = YAPI.INVALID_INT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        MOTORSTATE_ABSENT: Final[int] = 0
        MOTORSTATE_ALERT: Final[int] = 1
        MOTORSTATE_HI_Z: Final[int] = 2
        MOTORSTATE_STOP: Final[int] = 3
        MOTORSTATE_RUN: Final[int] = 4
        MOTORSTATE_BATCH: Final[int] = 5
        MOTORSTATE_INVALID: Final[int] = -1
        STEPPING_MICROSTEP16: Final[int] = 0
        STEPPING_MICROSTEP8: Final[int] = 1
        STEPPING_MICROSTEP4: Final[int] = 2
        STEPPING_HALFSTEP: Final[int] = 3
        STEPPING_FULLSTEP: Final[int] = 4
        STEPPING_INVALID: Final[int] = -1
        # --- (end of YStepperMotor return codes)


    # --- (YStepperMotor implementation)

    @classmethod
    def FindStepperMotor(cls, func: str) -> YStepperMotor:
        """
        Retrieves a stepper motor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the stepper motor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YStepperMotor.isOnline() to test if the stepper motor is
        indeed online at a given time. In case of ambiguity when looking for
        a stepper motor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the stepper motor, for instance
                MyDevice.stepperMotor1.

        @return a YStepperMotor object allowing you to drive the stepper motor.
        """
        return cls._proxy(cls, YStepperMotor_aio.FindStepperMotorInContext(YAPI_aio, func))

    @classmethod
    def FindStepperMotorInContext(cls, yctx: YAPIContext, func: str) -> YStepperMotor:
        """
        Retrieves a stepper motor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the stepper motor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YStepperMotor.isOnline() to test if the stepper motor is
        indeed online at a given time. In case of ambiguity when looking for
        a stepper motor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the stepper motor, for instance
                MyDevice.stepperMotor1.

        @return a YStepperMotor object allowing you to drive the stepper motor.
        """
        return cls._proxy(cls, YStepperMotor_aio.FindStepperMotorInContext(yctx._aio, func))

    @classmethod
    def FirstStepperMotor(cls) -> Union[YStepperMotor, None]:
        """
        Starts the enumeration of stepper motors currently accessible.
        Use the method YStepperMotor.nextStepperMotor() to iterate on
        next stepper motors.

        @return a pointer to a YStepperMotor object, corresponding to
                the first stepper motor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YStepperMotor_aio.FirstStepperMotorInContext(YAPI_aio))

    @classmethod
    def FirstStepperMotorInContext(cls, yctx: YAPIContext) -> Union[YStepperMotor, None]:
        """
        Starts the enumeration of stepper motors currently accessible.
        Use the method YStepperMotor.nextStepperMotor() to iterate on
        next stepper motors.

        @param yctx : a YAPI context.

        @return a pointer to a YStepperMotor object, corresponding to
                the first stepper motor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YStepperMotor_aio.FirstStepperMotorInContext(yctx._aio))

    def nextStepperMotor(self) -> Union[YStepperMotor, None]:
        """
        Continues the enumeration of stepper motors started using yFirstStepperMotor().
        Caution: You can't make any assumption about the returned stepper motors order.
        If you want to find a specific a stepper motor, use StepperMotor.findStepperMotor()
        and a hardwareID or a logical name.

        @return a pointer to a YStepperMotor object, corresponding to
                a stepper motor currently online, or a None pointer
                if there are no more stepper motors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextStepperMotor())

    if not _DYNAMIC_HELPERS:
        def get_motorState(self) -> int:
            """
            Returns the motor working state.

            @return a value among YStepperMotor.MOTORSTATE_ABSENT, YStepperMotor.MOTORSTATE_ALERT,
            YStepperMotor.MOTORSTATE_HI_Z, YStepperMotor.MOTORSTATE_STOP, YStepperMotor.MOTORSTATE_RUN and
            YStepperMotor.MOTORSTATE_BATCH corresponding to the motor working state

            On failure, throws an exception or returns YStepperMotor.MOTORSTATE_INVALID.
            """
            return self._run(self._aio.get_motorState())

    if not _DYNAMIC_HELPERS:
        def get_diags(self) -> int:
            """
            Returns the stepper motor controller diagnostics, as a bitmap.

            @return an integer corresponding to the stepper motor controller diagnostics, as a bitmap

            On failure, throws an exception or returns YStepperMotor.DIAGS_INVALID.
            """
            return self._run(self._aio.get_diags())

    if not _DYNAMIC_HELPERS:
        def set_stepPos(self, newval: float) -> int:
            """
            Changes the current logical motor position, measured in steps.
            This command does not cause any motor move, as its purpose is only to set up
            the origin of the position counter. The fractional part of the position,
            that corresponds to the physical position of the rotor, is not changed.
            To trigger a motor move, use methods moveTo() or moveRel()
            instead.

            @param newval : a floating point number corresponding to the current logical motor position, measured in steps

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_stepPos(newval))

    if not _DYNAMIC_HELPERS:
        def get_stepPos(self) -> float:
            """
            Returns the current logical motor position, measured in steps.
            The value may include a fractional part when micro-stepping is in use.

            @return a floating point number corresponding to the current logical motor position, measured in steps

            On failure, throws an exception or returns YStepperMotor.STEPPOS_INVALID.
            """
            return self._run(self._aio.get_stepPos())

    if not _DYNAMIC_HELPERS:
        def get_speed(self) -> float:
            """
            Returns current motor speed, measured in steps per second.
            To change speed, use method changeSpeed().

            @return a floating point number corresponding to current motor speed, measured in steps per second

            On failure, throws an exception or returns YStepperMotor.SPEED_INVALID.
            """
            return self._run(self._aio.get_speed())

    if not _DYNAMIC_HELPERS:
        def set_pullinSpeed(self, newval: float) -> int:
            """
            Changes the motor speed immediately reachable from stop state, measured in steps per second.

            @param newval : a floating point number corresponding to the motor speed immediately reachable from
            stop state, measured in steps per second

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_pullinSpeed(newval))

    if not _DYNAMIC_HELPERS:
        def get_pullinSpeed(self) -> float:
            """
            Returns the motor speed immediately reachable from stop state, measured in steps per second.

            @return a floating point number corresponding to the motor speed immediately reachable from stop
            state, measured in steps per second

            On failure, throws an exception or returns YStepperMotor.PULLINSPEED_INVALID.
            """
            return self._run(self._aio.get_pullinSpeed())

    if not _DYNAMIC_HELPERS:
        def set_maxAccel(self, newval: float) -> int:
            """
            Changes the maximal motor acceleration, measured in steps per second^2.

            @param newval : a floating point number corresponding to the maximal motor acceleration, measured
            in steps per second^2

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_maxAccel(newval))

    if not _DYNAMIC_HELPERS:
        def get_maxAccel(self) -> float:
            """
            Returns the maximal motor acceleration, measured in steps per second^2.

            @return a floating point number corresponding to the maximal motor acceleration, measured in steps per second^2

            On failure, throws an exception or returns YStepperMotor.MAXACCEL_INVALID.
            """
            return self._run(self._aio.get_maxAccel())

    if not _DYNAMIC_HELPERS:
        def set_maxSpeed(self, newval: float) -> int:
            """
            Changes the maximal motor speed, measured in steps per second.

            @param newval : a floating point number corresponding to the maximal motor speed, measured in steps per second

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_maxSpeed(newval))

    if not _DYNAMIC_HELPERS:
        def get_maxSpeed(self) -> float:
            """
            Returns the maximal motor speed, measured in steps per second.

            @return a floating point number corresponding to the maximal motor speed, measured in steps per second

            On failure, throws an exception or returns YStepperMotor.MAXSPEED_INVALID.
            """
            return self._run(self._aio.get_maxSpeed())

    if not _DYNAMIC_HELPERS:
        def get_stepping(self) -> int:
            """
            Returns the stepping mode used to drive the motor.

            @return a value among YStepperMotor.STEPPING_MICROSTEP16, YStepperMotor.STEPPING_MICROSTEP8,
            YStepperMotor.STEPPING_MICROSTEP4, YStepperMotor.STEPPING_HALFSTEP and
            YStepperMotor.STEPPING_FULLSTEP corresponding to the stepping mode used to drive the motor

            On failure, throws an exception or returns YStepperMotor.STEPPING_INVALID.
            """
            return self._run(self._aio.get_stepping())

    if not _DYNAMIC_HELPERS:
        def set_stepping(self, newval: int) -> int:
            """
            Changes the stepping mode used to drive the motor.

            @param newval : a value among YStepperMotor.STEPPING_MICROSTEP16,
            YStepperMotor.STEPPING_MICROSTEP8, YStepperMotor.STEPPING_MICROSTEP4,
            YStepperMotor.STEPPING_HALFSTEP and YStepperMotor.STEPPING_FULLSTEP corresponding to the stepping
            mode used to drive the motor

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_stepping(newval))

    if not _DYNAMIC_HELPERS:
        def get_overcurrent(self) -> int:
            """
            Returns the overcurrent alert and emergency stop threshold, measured in mA.

            @return an integer corresponding to the overcurrent alert and emergency stop threshold, measured in mA

            On failure, throws an exception or returns YStepperMotor.OVERCURRENT_INVALID.
            """
            return self._run(self._aio.get_overcurrent())

    if not _DYNAMIC_HELPERS:
        def set_overcurrent(self, newval: int) -> int:
            """
            Changes the overcurrent alert and emergency stop threshold, measured in mA.

            @param newval : an integer corresponding to the overcurrent alert and emergency stop threshold, measured in mA

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_overcurrent(newval))

    if not _DYNAMIC_HELPERS:
        def get_tCurrStop(self) -> int:
            """
            Returns the torque regulation current when the motor is stopped, measured in mA.

            @return an integer corresponding to the torque regulation current when the motor is stopped, measured in mA

            On failure, throws an exception or returns YStepperMotor.TCURRSTOP_INVALID.
            """
            return self._run(self._aio.get_tCurrStop())

    if not _DYNAMIC_HELPERS:
        def set_tCurrStop(self, newval: int) -> int:
            """
            Changes the torque regulation current when the motor is stopped, measured in mA.

            @param newval : an integer corresponding to the torque regulation current when the motor is
            stopped, measured in mA

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_tCurrStop(newval))

    if not _DYNAMIC_HELPERS:
        def get_tCurrRun(self) -> int:
            """
            Returns the torque regulation current when the motor is running, measured in mA.

            @return an integer corresponding to the torque regulation current when the motor is running, measured in mA

            On failure, throws an exception or returns YStepperMotor.TCURRRUN_INVALID.
            """
            return self._run(self._aio.get_tCurrRun())

    if not _DYNAMIC_HELPERS:
        def set_tCurrRun(self, newval: int) -> int:
            """
            Changes the torque regulation current when the motor is running, measured in mA.

            @param newval : an integer corresponding to the torque regulation current when the motor is
            running, measured in mA

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_tCurrRun(newval))

    if not _DYNAMIC_HELPERS:
        def set_alertMode(self, newval: str) -> int:
            return self._run(self._aio.set_alertMode(newval))

    if not _DYNAMIC_HELPERS:
        def set_auxMode(self, newval: str) -> int:
            return self._run(self._aio.set_auxMode(newval))

    if not _DYNAMIC_HELPERS:
        def get_auxSignal(self) -> int:
            """
            Returns the current value of the signal generated on the auxiliary output.

            @return an integer corresponding to the current value of the signal generated on the auxiliary output

            On failure, throws an exception or returns YStepperMotor.AUXSIGNAL_INVALID.
            """
            return self._run(self._aio.get_auxSignal())

    if not _DYNAMIC_HELPERS:
        def set_auxSignal(self, newval: int) -> int:
            """
            Changes the value of the signal generated on the auxiliary output.
            Acceptable values depend on the auxiliary output signal type configured.

            @param newval : an integer corresponding to the value of the signal generated on the auxiliary output

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_auxSignal(newval))

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YStepperMotorValueCallback) -> int:
            """
            Registers the callback function that is invoked on every change of advertised value.
            The callback is invoked only during the execution of ySleep or yHandleEvents.
            This provides control over the time when the callback is triggered. For good responsiveness, remember to call
            one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

            @param callback : the callback function to call, or a None pointer. The callback function should take two
                    arguments: the function object of which the value has changed, and the character string describing
                    the new advertised value.
            @noreturn
            """
            return super().registerValueCallback(callback)

    if not _DYNAMIC_HELPERS:
        def reset(self) -> int:
            """
            Reinitialize the controller and clear all alert flags.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reset())

    if not _DYNAMIC_HELPERS:
        def findHomePosition(self, speed: float) -> int:
            """
            Starts the motor backward at the specified speed, to search for the motor home position.

            @param speed : desired speed, in steps per second.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.findHomePosition(speed))

    if not _DYNAMIC_HELPERS:
        def changeSpeed(self, speed: float) -> int:
            """
            Starts the motor at a given speed. The time needed to reach the requested speed
            will depend on the acceleration parameters configured for the motor.

            @param speed : desired speed, in steps per second. The minimal non-zero speed
                    is 0.001 pulse per second.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.changeSpeed(speed))

    if not _DYNAMIC_HELPERS:
        def moveTo(self, absPos: float) -> int:
            """
            Starts the motor to reach a given absolute position. The time needed to reach the requested
            position will depend on the acceleration and max speed parameters configured for
            the motor.

            @param absPos : absolute position, measured in steps from the origin.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.moveTo(absPos))

    if not _DYNAMIC_HELPERS:
        def moveRel(self, relPos: float) -> int:
            """
            Starts the motor to reach a given relative position. The time needed to reach the requested
            position will depend on the acceleration and max speed parameters configured for
            the motor.

            @param relPos : relative position, measured in steps from the current position.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.moveRel(relPos))

    if not _DYNAMIC_HELPERS:
        def moveRelSlow(self, relPos: float, maxSpeed: float) -> int:
            """
            Starts the motor to reach a given relative position, keeping the speed under the
            specified limit. The time needed to reach the requested position will depend on
            the acceleration parameters configured for the motor.

            @param relPos : relative position, measured in steps from the current position.
            @param maxSpeed : limit speed, in steps per second.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.moveRelSlow(relPos, maxSpeed))

    if not _DYNAMIC_HELPERS:
        def pause(self, waitMs: int) -> int:
            """
            Keep the motor in the same state for the specified amount of time, before processing next command.

            @param waitMs : wait time, specified in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.pause(waitMs))

    if not _DYNAMIC_HELPERS:
        def emergencyStop(self) -> int:
            """
            Stops the motor with an emergency alert, without taking any additional precaution.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.emergencyStop())

    if not _DYNAMIC_HELPERS:
        def alertStepOut(self) -> int:
            """
            Move one step in the direction opposite the direction set when the most recent alert was raised.
            The move occurs even if the system is still in alert mode (end switch depressed). Caution.
            use this function with great care as it may cause mechanical damages !

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.alertStepOut())

    if not _DYNAMIC_HELPERS:
        def alertStepDir(self, dir: int) -> int:
            """
            Move one single step in the selected direction without regards to end switches.
            The move occurs even if the system is still in alert mode (end switch depressed). Caution.
            use this function with great care as it may cause mechanical damages !

            @param dir : Value +1 or -1, according to the desired direction of the move

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.alertStepDir(dir))

    if not _DYNAMIC_HELPERS:
        def abortAndBrake(self) -> int:
            """
            Stops the motor smoothly as soon as possible, without waiting for ongoing move completion.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.abortAndBrake())

    if not _DYNAMIC_HELPERS:
        def abortAndHiZ(self) -> int:
            """
            Turn the controller into Hi-Z mode immediately, without waiting for ongoing move completion.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.abortAndHiZ())

    # --- (end of YStepperMotor implementation)

