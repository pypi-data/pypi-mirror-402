# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YServo
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
Yoctopuce library: High-level API for YServo
version: PATCH_WITH_VERSION
requires: yocto_servo_aio
requires: yocto_api
provides: YServo
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

from .yocto_servo_aio import YServo as YServo_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YServo class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YServoValueCallback = Union[Callable[['YServo', str], Any], None]
    except TypeError:
        YServoValueCallback = Union[Callable, Awaitable]
if _IS_MICROPYTHON:
    from collections import namedtuple
    YMove = namedtuple("YMove", ('target', 'ms', 'moving'))
else:
    from typing import NamedTuple
    class YMove(NamedTuple):
        target: int
        ms: int
        moving: int


# noinspection PyProtectedMember
class YServo(YFunction):
    """
    The YServo class is designed to drive remote-control servo motors
    outputs. This class allows you not only to move
    a servo to a given position, but also to specify the time interval
    in which the move should be performed. This makes it possible to
    synchronize two servos involved in a same move.

    """
    _aio: YServo_aio
    # --- (end of YServo class start)
    if not _IS_MICROPYTHON:
        # --- (YServo return codes)
        POSITION_INVALID: Final[int] = YAPI.INVALID_INT
        RANGE_INVALID: Final[int] = YAPI.INVALID_UINT
        NEUTRAL_INVALID: Final[int] = YAPI.INVALID_UINT
        MOVE_INVALID: Final[None] = None
        POSITIONATPOWERON_INVALID: Final[int] = YAPI.INVALID_INT
        ENABLED_FALSE: Final[int] = 0
        ENABLED_TRUE: Final[int] = 1
        ENABLED_INVALID: Final[int] = -1
        ENABLEDATPOWERON_FALSE: Final[int] = 0
        ENABLEDATPOWERON_TRUE: Final[int] = 1
        ENABLEDATPOWERON_INVALID: Final[int] = -1
        # --- (end of YServo return codes)


    # --- (YServo implementation)

    @classmethod
    def FindServo(cls, func: str) -> YServo:
        """
        Retrieves a RC servo motor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the RC servo motor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YServo.isOnline() to test if the RC servo motor is
        indeed online at a given time. In case of ambiguity when looking for
        a RC servo motor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the RC servo motor, for instance
                SERVORC1.servo1.

        @return a YServo object allowing you to drive the RC servo motor.
        """
        return cls._proxy(cls, YServo_aio.FindServoInContext(YAPI_aio, func))

    @classmethod
    def FindServoInContext(cls, yctx: YAPIContext, func: str) -> YServo:
        """
        Retrieves a RC servo motor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the RC servo motor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YServo.isOnline() to test if the RC servo motor is
        indeed online at a given time. In case of ambiguity when looking for
        a RC servo motor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the RC servo motor, for instance
                SERVORC1.servo1.

        @return a YServo object allowing you to drive the RC servo motor.
        """
        return cls._proxy(cls, YServo_aio.FindServoInContext(yctx._aio, func))

    @classmethod
    def FirstServo(cls) -> Union[YServo, None]:
        """
        Starts the enumeration of RC servo motors currently accessible.
        Use the method YServo.nextServo() to iterate on
        next RC servo motors.

        @return a pointer to a YServo object, corresponding to
                the first RC servo motor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YServo_aio.FirstServoInContext(YAPI_aio))

    @classmethod
    def FirstServoInContext(cls, yctx: YAPIContext) -> Union[YServo, None]:
        """
        Starts the enumeration of RC servo motors currently accessible.
        Use the method YServo.nextServo() to iterate on
        next RC servo motors.

        @param yctx : a YAPI context.

        @return a pointer to a YServo object, corresponding to
                the first RC servo motor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YServo_aio.FirstServoInContext(yctx._aio))

    def nextServo(self) -> Union[YServo, None]:
        """
        Continues the enumeration of RC servo motors started using yFirstServo().
        Caution: You can't make any assumption about the returned RC servo motors order.
        If you want to find a specific a RC servo motor, use Servo.findServo()
        and a hardwareID or a logical name.

        @return a pointer to a YServo object, corresponding to
                a RC servo motor currently online, or a None pointer
                if there are no more RC servo motors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextServo())

    if not _DYNAMIC_HELPERS:
        def get_position(self) -> int:
            """
            Returns the current servo position.

            @return an integer corresponding to the current servo position

            On failure, throws an exception or returns YServo.POSITION_INVALID.
            """
            return self._run(self._aio.get_position())

    if not _DYNAMIC_HELPERS:
        def set_position(self, newval: int) -> int:
            """
            Changes immediately the servo driving position.

            @param newval : an integer corresponding to immediately the servo driving position

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_position(newval))

    if not _DYNAMIC_HELPERS:
        def get_enabled(self) -> int:
            """
            Returns the state of the RC servo motors.

            @return either YServo.ENABLED_FALSE or YServo.ENABLED_TRUE, according to the state of the RC servo motors

            On failure, throws an exception or returns YServo.ENABLED_INVALID.
            """
            return self._run(self._aio.get_enabled())

    if not _DYNAMIC_HELPERS:
        def set_enabled(self, newval: int) -> int:
            """
            Stops or starts the RC servo motor.

            @param newval : either YServo.ENABLED_FALSE or YServo.ENABLED_TRUE

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_enabled(newval))

    if not _DYNAMIC_HELPERS:
        def get_range(self) -> int:
            """
            Returns the current range of use of the servo.

            @return an integer corresponding to the current range of use of the servo

            On failure, throws an exception or returns YServo.RANGE_INVALID.
            """
            return self._run(self._aio.get_range())

    if not _DYNAMIC_HELPERS:
        def set_range(self, newval: int) -> int:
            """
            Changes the range of use of the servo, specified in per cents.
            A range of 100% corresponds to a standard control signal, that varies
            from 1 [ms] to 2 [ms], When using a servo that supports a double range,
            from 0.5 [ms] to 2.5 [ms], you can select a range of 200%.
            Be aware that using a range higher than what is supported by the servo
            is likely to damage the servo. Remember to call the matching module
            saveToFlash() method, otherwise this call will have no effect.

            @param newval : an integer corresponding to the range of use of the servo, specified in per cents

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_range(newval))

    if not _DYNAMIC_HELPERS:
        def get_neutral(self) -> int:
            """
            Returns the duration in microseconds of a neutral pulse for the servo.

            @return an integer corresponding to the duration in microseconds of a neutral pulse for the servo

            On failure, throws an exception or returns YServo.NEUTRAL_INVALID.
            """
            return self._run(self._aio.get_neutral())

    if not _DYNAMIC_HELPERS:
        def set_neutral(self, newval: int) -> int:
            """
            Changes the duration of the pulse corresponding to the neutral position of the servo.
            The duration is specified in microseconds, and the standard value is 1500 [us].
            This setting makes it possible to shift the range of use of the servo.
            Be aware that using a range higher than what is supported by the servo is
            likely to damage the servo. Remember to call the matching module
            saveToFlash() method, otherwise this call will have no effect.

            @param newval : an integer corresponding to the duration of the pulse corresponding to the neutral
            position of the servo

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_neutral(newval))

    if not _DYNAMIC_HELPERS:
        def set_move(self, newval: YMove) -> int:
            return self._run(self._aio.set_move(newval))

    if not _DYNAMIC_HELPERS:
        def move(self, target, ms_duration) -> int:
            """
            Performs a smooth move at constant speed toward a given position.

            @param target      : new position at the end of the move
            @param ms_duration : total duration of the move, in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.move(target, ms_duration))

    if not _DYNAMIC_HELPERS:
        def get_positionAtPowerOn(self) -> int:
            """
            Returns the servo position at device power up.

            @return an integer corresponding to the servo position at device power up

            On failure, throws an exception or returns YServo.POSITIONATPOWERON_INVALID.
            """
            return self._run(self._aio.get_positionAtPowerOn())

    if not _DYNAMIC_HELPERS:
        def set_positionAtPowerOn(self, newval: int) -> int:
            """
            Configure the servo position at device power up. Remember to call the matching
            module saveToFlash() method, otherwise this call will have no effect.

            @param newval : an integer

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_positionAtPowerOn(newval))

    if not _DYNAMIC_HELPERS:
        def get_enabledAtPowerOn(self) -> int:
            """
            Returns the servo signal generator state at power up.

            @return either YServo.ENABLEDATPOWERON_FALSE or YServo.ENABLEDATPOWERON_TRUE, according to the
            servo signal generator state at power up

            On failure, throws an exception or returns YServo.ENABLEDATPOWERON_INVALID.
            """
            return self._run(self._aio.get_enabledAtPowerOn())

    if not _DYNAMIC_HELPERS:
        def set_enabledAtPowerOn(self, newval: int) -> int:
            """
            Configure the servo signal generator state at power up. Remember to call the matching module saveToFlash()
            method, otherwise this call will have no effect.

            @param newval : either YServo.ENABLEDATPOWERON_FALSE or YServo.ENABLEDATPOWERON_TRUE

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_enabledAtPowerOn(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YServoValueCallback) -> int:
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

    # --- (end of YServo implementation)

