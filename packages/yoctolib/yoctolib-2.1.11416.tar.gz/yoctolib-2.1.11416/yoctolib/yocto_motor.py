# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YMotor
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
Yoctopuce library: High-level API for YMotor
version: PATCH_WITH_VERSION
requires: yocto_motor_aio
requires: yocto_api
provides: YMotor
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

from .yocto_motor_aio import YMotor as YMotor_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YMotor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YMotorValueCallback = Union[Callable[['YMotor', str], Any], None]
    except TypeError:
        YMotorValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YMotor(YFunction):
    """
    The YMotor class allows you to drive a DC motor. It can be used to configure the
    power sent to the motor to make it turn both ways, but also to drive accelerations
    and decelerations. The motor will then accelerate automatically: you will not
    have to monitor it. The API also allows to slow down the motor by shortening
    its terminals: the motor will then act as an electromagnetic brake.

    """
    _aio: YMotor_aio
    # --- (end of YMotor class start)
    if not _IS_MICROPYTHON:
        # --- (YMotor return codes)
        DRIVINGFORCE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        BRAKINGFORCE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CUTOFFVOLTAGE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        OVERCURRENTLIMIT_INVALID: Final[int] = YAPI.INVALID_UINT
        FREQUENCY_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        STARTERTIME_INVALID: Final[int] = YAPI.INVALID_UINT
        FAILSAFETIMEOUT_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        MOTORSTATUS_IDLE: Final[int] = 0
        MOTORSTATUS_BRAKE: Final[int] = 1
        MOTORSTATUS_FORWD: Final[int] = 2
        MOTORSTATUS_BACKWD: Final[int] = 3
        MOTORSTATUS_LOVOLT: Final[int] = 4
        MOTORSTATUS_HICURR: Final[int] = 5
        MOTORSTATUS_HIHEAT: Final[int] = 6
        MOTORSTATUS_FAILSF: Final[int] = 7
        MOTORSTATUS_INVALID: Final[int] = -1
        # --- (end of YMotor return codes)


    # --- (YMotor implementation)

    @classmethod
    def FindMotor(cls, func: str) -> YMotor:
        """
        Retrieves a motor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the motor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMotor.isOnline() to test if the motor is
        indeed online at a given time. In case of ambiguity when looking for
        a motor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the motor, for instance
                MOTORCTL.motor.

        @return a YMotor object allowing you to drive the motor.
        """
        return cls._proxy(cls, YMotor_aio.FindMotorInContext(YAPI_aio, func))

    @classmethod
    def FindMotorInContext(cls, yctx: YAPIContext, func: str) -> YMotor:
        """
        Retrieves a motor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the motor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMotor.isOnline() to test if the motor is
        indeed online at a given time. In case of ambiguity when looking for
        a motor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the motor, for instance
                MOTORCTL.motor.

        @return a YMotor object allowing you to drive the motor.
        """
        return cls._proxy(cls, YMotor_aio.FindMotorInContext(yctx._aio, func))

    @classmethod
    def FirstMotor(cls) -> Union[YMotor, None]:
        """
        Starts the enumeration of motors currently accessible.
        Use the method YMotor.nextMotor() to iterate on
        next motors.

        @return a pointer to a YMotor object, corresponding to
                the first motor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YMotor_aio.FirstMotorInContext(YAPI_aio))

    @classmethod
    def FirstMotorInContext(cls, yctx: YAPIContext) -> Union[YMotor, None]:
        """
        Starts the enumeration of motors currently accessible.
        Use the method YMotor.nextMotor() to iterate on
        next motors.

        @param yctx : a YAPI context.

        @return a pointer to a YMotor object, corresponding to
                the first motor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YMotor_aio.FirstMotorInContext(yctx._aio))

    def nextMotor(self) -> Union[YMotor, None]:
        """
        Continues the enumeration of motors started using yFirstMotor().
        Caution: You can't make any assumption about the returned motors order.
        If you want to find a specific a motor, use Motor.findMotor()
        and a hardwareID or a logical name.

        @return a pointer to a YMotor object, corresponding to
                a motor currently online, or a None pointer
                if there are no more motors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextMotor())

    if not _DYNAMIC_HELPERS:
        def get_motorStatus(self) -> int:
            """
            Return the controller state. Possible states are:
            IDLE   when the motor is stopped/in free wheel, ready to start;
            FORWD  when the controller is driving the motor forward;
            BACKWD when the controller is driving the motor backward;
            BRAKE  when the controller is braking;
            LOVOLT when the controller has detected a low voltage condition;
            HICURR when the controller has detected an over current condition;
            HIHEAT when the controller has detected an overheat condition;
            FAILSF when the controller switched on the failsafe security.

            When an error condition occurred (LOVOLT, HICURR, HIHEAT, FAILSF), the controller
            status must be explicitly reset using the resetStatus function.

            @return a value among YMotor.MOTORSTATUS_IDLE, YMotor.MOTORSTATUS_BRAKE, YMotor.MOTORSTATUS_FORWD,
            YMotor.MOTORSTATUS_BACKWD, YMotor.MOTORSTATUS_LOVOLT, YMotor.MOTORSTATUS_HICURR,
            YMotor.MOTORSTATUS_HIHEAT and YMotor.MOTORSTATUS_FAILSF

            On failure, throws an exception or returns YMotor.MOTORSTATUS_INVALID.
            """
            return self._run(self._aio.get_motorStatus())

    if not _DYNAMIC_HELPERS:
        def set_motorStatus(self, newval: int) -> int:
            return self._run(self._aio.set_motorStatus(newval))

    if not _DYNAMIC_HELPERS:
        def set_drivingForce(self, newval: float) -> int:
            """
            Changes immediately the power sent to the motor. The value is a percentage between -100%
            to 100%. If you want go easy on your mechanics and avoid excessive current consumption,
            try to avoid brutal power changes. For example, immediate transition from forward full power
            to reverse full power is a very bad idea. Each time the driving power is modified, the
            braking power is set to zero.

            @param newval : a floating point number corresponding to immediately the power sent to the motor

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_drivingForce(newval))

    if not _DYNAMIC_HELPERS:
        def get_drivingForce(self) -> float:
            """
            Returns the power sent to the motor, as a percentage between -100% and +100%.

            @return a floating point number corresponding to the power sent to the motor, as a percentage
            between -100% and +100%

            On failure, throws an exception or returns YMotor.DRIVINGFORCE_INVALID.
            """
            return self._run(self._aio.get_drivingForce())

    if not _DYNAMIC_HELPERS:
        def set_brakingForce(self, newval: float) -> int:
            """
            Changes immediately the braking force applied to the motor (in percents).
            The value 0 corresponds to no braking (free wheel). When the braking force
            is changed, the driving power is set to zero. The value is a percentage.

            @param newval : a floating point number corresponding to immediately the braking force applied to
            the motor (in percents)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_brakingForce(newval))

    if not _DYNAMIC_HELPERS:
        def get_brakingForce(self) -> float:
            """
            Returns the braking force applied to the motor, as a percentage.
            The value 0 corresponds to no braking (free wheel).

            @return a floating point number corresponding to the braking force applied to the motor, as a percentage

            On failure, throws an exception or returns YMotor.BRAKINGFORCE_INVALID.
            """
            return self._run(self._aio.get_brakingForce())

    if not _DYNAMIC_HELPERS:
        def set_cutOffVoltage(self, newval: float) -> int:
            """
            Changes the threshold voltage under which the controller automatically switches to error state
            and prevents further current draw. This setting prevent damage to a battery that can
            occur when drawing current from an "empty" battery.
            Note that whatever the cutoff threshold, the controller switches to undervoltage
            error state if the power supply goes under 3V, even for a very brief time.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the threshold voltage under which the
            controller automatically switches to error state
                    and prevents further current draw

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_cutOffVoltage(newval))

    if not _DYNAMIC_HELPERS:
        def get_cutOffVoltage(self) -> float:
            """
            Returns the threshold voltage under which the controller automatically switches to error state
            and prevents further current draw. This setting prevents damage to a battery that can
            occur when drawing current from an "empty" battery.

            @return a floating point number corresponding to the threshold voltage under which the controller
            automatically switches to error state
                    and prevents further current draw

            On failure, throws an exception or returns YMotor.CUTOFFVOLTAGE_INVALID.
            """
            return self._run(self._aio.get_cutOffVoltage())

    if not _DYNAMIC_HELPERS:
        def get_overCurrentLimit(self) -> int:
            """
            Returns the current threshold (in mA) above which the controller automatically
            switches to error state. A zero value means that there is no limit.

            @return an integer corresponding to the current threshold (in mA) above which the controller automatically
                    switches to error state

            On failure, throws an exception or returns YMotor.OVERCURRENTLIMIT_INVALID.
            """
            return self._run(self._aio.get_overCurrentLimit())

    if not _DYNAMIC_HELPERS:
        def set_overCurrentLimit(self, newval: int) -> int:
            """
            Changes the current threshold (in mA) above which the controller automatically
            switches to error state. A zero value means that there is no limit. Note that whatever the
            current limit is, the controller switches to OVERCURRENT status if the current
            goes above 32A, even for a very brief time. Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the current threshold (in mA) above which the
            controller automatically
                    switches to error state

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_overCurrentLimit(newval))

    if not _DYNAMIC_HELPERS:
        def set_frequency(self, newval: float) -> int:
            """
            Changes the PWM frequency used to control the motor. Low frequency is usually
            more efficient and may help the motor to start, but an audible noise might be
            generated. A higher frequency reduces the noise, but more energy is converted
            into heat. Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the PWM frequency used to control the motor

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_frequency(newval))

    if not _DYNAMIC_HELPERS:
        def get_frequency(self) -> float:
            """
            Returns the PWM frequency used to control the motor.

            @return a floating point number corresponding to the PWM frequency used to control the motor

            On failure, throws an exception or returns YMotor.FREQUENCY_INVALID.
            """
            return self._run(self._aio.get_frequency())

    if not _DYNAMIC_HELPERS:
        def get_starterTime(self) -> int:
            """
            Returns the duration (in ms) during which the motor is driven at low frequency to help
            it start up.

            @return an integer corresponding to the duration (in ms) during which the motor is driven at low
            frequency to help
                    it start up

            On failure, throws an exception or returns YMotor.STARTERTIME_INVALID.
            """
            return self._run(self._aio.get_starterTime())

    if not _DYNAMIC_HELPERS:
        def set_starterTime(self, newval: int) -> int:
            """
            Changes the duration (in ms) during which the motor is driven at low frequency to help
            it start up. Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the duration (in ms) during which the motor is driven
            at low frequency to help
                    it start up

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_starterTime(newval))

    if not _DYNAMIC_HELPERS:
        def get_failSafeTimeout(self) -> int:
            """
            Returns the delay in milliseconds allowed for the controller to run autonomously without
            receiving any instruction from the control process. When this delay has elapsed,
            the controller automatically stops the motor and switches to FAILSAFE error.
            Failsafe security is disabled when the value is zero.

            @return an integer corresponding to the delay in milliseconds allowed for the controller to run
            autonomously without
                    receiving any instruction from the control process

            On failure, throws an exception or returns YMotor.FAILSAFETIMEOUT_INVALID.
            """
            return self._run(self._aio.get_failSafeTimeout())

    if not _DYNAMIC_HELPERS:
        def set_failSafeTimeout(self, newval: int) -> int:
            """
            Changes the delay in milliseconds allowed for the controller to run autonomously without
            receiving any instruction from the control process. When this delay has elapsed,
            the controller automatically stops the motor and switches to FAILSAFE error.
            Failsafe security is disabled when the value is zero.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the delay in milliseconds allowed for the controller to
            run autonomously without
                    receiving any instruction from the control process

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_failSafeTimeout(newval))

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YMotorValueCallback) -> int:
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
        def keepALive(self) -> int:
            """
            Rearms the controller failsafe timer. When the motor is running and the failsafe feature
            is active, this function should be called periodically to prove that the control process
            is running properly. Otherwise, the motor is automatically stopped after the specified
            timeout. Calling a motor <i>set</i> function implicitly rearms the failsafe timer.
            """
            return self._run(self._aio.keepALive())

    if not _DYNAMIC_HELPERS:
        def resetStatus(self) -> int:
            """
            Reset the controller state to IDLE. This function must be invoked explicitly
            after any error condition is signaled.
            """
            return self._run(self._aio.resetStatus())

    if not _DYNAMIC_HELPERS:
        def drivingForceMove(self, targetPower: float, delay: int) -> int:
            """
            Changes progressively the power sent to the motor for a specific duration.

            @param targetPower : desired motor power, in percents (between -100% and +100%)
            @param delay : duration (in ms) of the transition

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drivingForceMove(targetPower, delay))

    if not _DYNAMIC_HELPERS:
        def brakingForceMove(self, targetPower: float, delay: int) -> int:
            """
            Changes progressively the braking force applied to the motor for a specific duration.

            @param targetPower : desired braking force, in percents
            @param delay : duration (in ms) of the transition

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.brakingForceMove(targetPower, delay))

    # --- (end of YMotor implementation)

