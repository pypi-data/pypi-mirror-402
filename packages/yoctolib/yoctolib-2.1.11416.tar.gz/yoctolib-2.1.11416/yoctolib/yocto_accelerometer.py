# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YAccelerometer
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
Yoctopuce library: High-level API for YAccelerometer
version: PATCH_WITH_VERSION
requires: yocto_accelerometer_aio
requires: yocto_api
provides: YAccelerometer
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

from .yocto_accelerometer_aio import YAccelerometer as YAccelerometer_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YAccelerometer class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YAccelerometerValueCallback = Union[Callable[['YAccelerometer', str], Any], None]
        YAccelerometerTimedReportCallback = Union[Callable[['YAccelerometer', YMeasure], Any], None]
    except TypeError:
        YAccelerometerValueCallback = Union[Callable, Awaitable]
        YAccelerometerTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YAccelerometer(YSensor):
    """
    The YAccelerometer class allows you to read and configure Yoctopuce accelerometers.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the possibility to access x, y and z components of the acceleration
    vector separately.

    """
    _aio: YAccelerometer_aio
    # --- (end of YAccelerometer class start)
    if not _IS_MICROPYTHON:
        # --- (YAccelerometer return codes)
        BANDWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        XVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        YVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ZVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        GRAVITYCANCELLATION_OFF: Final[int] = 0
        GRAVITYCANCELLATION_ON: Final[int] = 1
        GRAVITYCANCELLATION_INVALID: Final[int] = -1
        # --- (end of YAccelerometer return codes)


    # --- (YAccelerometer implementation)

    @classmethod
    def FindAccelerometer(cls, func: str) -> YAccelerometer:
        """
        Retrieves an accelerometer for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the accelerometer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAccelerometer.isOnline() to test if the accelerometer is
        indeed online at a given time. In case of ambiguity when looking for
        an accelerometer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the accelerometer, for instance
                Y3DMK002.accelerometer.

        @return a YAccelerometer object allowing you to drive the accelerometer.
        """
        return cls._proxy(cls, YAccelerometer_aio.FindAccelerometerInContext(YAPI_aio, func))

    @classmethod
    def FindAccelerometerInContext(cls, yctx: YAPIContext, func: str) -> YAccelerometer:
        """
        Retrieves an accelerometer for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the accelerometer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAccelerometer.isOnline() to test if the accelerometer is
        indeed online at a given time. In case of ambiguity when looking for
        an accelerometer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the accelerometer, for instance
                Y3DMK002.accelerometer.

        @return a YAccelerometer object allowing you to drive the accelerometer.
        """
        return cls._proxy(cls, YAccelerometer_aio.FindAccelerometerInContext(yctx._aio, func))

    @classmethod
    def FirstAccelerometer(cls) -> Union[YAccelerometer, None]:
        """
        Starts the enumeration of accelerometers currently accessible.
        Use the method YAccelerometer.nextAccelerometer() to iterate on
        next accelerometers.

        @return a pointer to a YAccelerometer object, corresponding to
                the first accelerometer currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YAccelerometer_aio.FirstAccelerometerInContext(YAPI_aio))

    @classmethod
    def FirstAccelerometerInContext(cls, yctx: YAPIContext) -> Union[YAccelerometer, None]:
        """
        Starts the enumeration of accelerometers currently accessible.
        Use the method YAccelerometer.nextAccelerometer() to iterate on
        next accelerometers.

        @param yctx : a YAPI context.

        @return a pointer to a YAccelerometer object, corresponding to
                the first accelerometer currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YAccelerometer_aio.FirstAccelerometerInContext(yctx._aio))

    def nextAccelerometer(self) -> Union[YAccelerometer, None]:
        """
        Continues the enumeration of accelerometers started using yFirstAccelerometer().
        Caution: You can't make any assumption about the returned accelerometers order.
        If you want to find a specific an accelerometer, use Accelerometer.findAccelerometer()
        and a hardwareID or a logical name.

        @return a pointer to a YAccelerometer object, corresponding to
                an accelerometer currently online, or a None pointer
                if there are no more accelerometers to enumerate.
        """
        return self._proxy(type(self), self._aio.nextAccelerometer())

    if not _DYNAMIC_HELPERS:
        def get_bandwidth(self) -> int:
            """
            Returns the measure update frequency, measured in Hz.

            @return an integer corresponding to the measure update frequency, measured in Hz

            On failure, throws an exception or returns YAccelerometer.BANDWIDTH_INVALID.
            """
            return self._run(self._aio.get_bandwidth())

    if not _DYNAMIC_HELPERS:
        def set_bandwidth(self, newval: int) -> int:
            """
            Changes the measure update frequency, measured in Hz. When the
            frequency is lower, the device performs averaging.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the measure update frequency, measured in Hz

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_bandwidth(newval))

    if not _DYNAMIC_HELPERS:
        def get_xValue(self) -> float:
            """
            Returns the X component of the acceleration, as a floating point number.

            @return a floating point number corresponding to the X component of the acceleration, as a floating point number

            On failure, throws an exception or returns YAccelerometer.XVALUE_INVALID.
            """
            return self._run(self._aio.get_xValue())

    if not _DYNAMIC_HELPERS:
        def get_yValue(self) -> float:
            """
            Returns the Y component of the acceleration, as a floating point number.

            @return a floating point number corresponding to the Y component of the acceleration, as a floating point number

            On failure, throws an exception or returns YAccelerometer.YVALUE_INVALID.
            """
            return self._run(self._aio.get_yValue())

    if not _DYNAMIC_HELPERS:
        def get_zValue(self) -> float:
            """
            Returns the Z component of the acceleration, as a floating point number.

            @return a floating point number corresponding to the Z component of the acceleration, as a floating point number

            On failure, throws an exception or returns YAccelerometer.ZVALUE_INVALID.
            """
            return self._run(self._aio.get_zValue())

    if not _DYNAMIC_HELPERS:
        def set_gravityCancellation(self, newval: int) -> int:
            return self._run(self._aio.set_gravityCancellation(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YAccelerometerValueCallback) -> int:
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

    if not _IS_MICROPYTHON:
        def registerTimedReportCallback(self, callback: YAccelerometerTimedReportCallback) -> int:
            """
            Registers the callback function that is invoked on every periodic timed notification.
            The callback is invoked only during the execution of ySleep or yHandleEvents.
            This provides control over the time when the callback is triggered. For good responsiveness, remember to call
            one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

            @param callback : the callback function to call, or a None pointer. The callback function should take two
                    arguments: the function object of which the value has changed, and an YMeasure object describing
                    the new advertised value.
            @noreturn
            """
            return super().registerTimedReportCallback(callback)

    # --- (end of YAccelerometer implementation)

