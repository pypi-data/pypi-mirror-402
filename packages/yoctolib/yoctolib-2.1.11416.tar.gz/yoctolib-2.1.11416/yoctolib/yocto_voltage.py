# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YVoltage
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
Yoctopuce library: High-level API for YVoltage
version: PATCH_WITH_VERSION
requires: yocto_voltage_aio
requires: yocto_api
provides: YVoltage
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

from .yocto_voltage_aio import YVoltage as YVoltage_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YVoltage class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YVoltageValueCallback = Union[Callable[['YVoltage', str], Any], None]
        YVoltageTimedReportCallback = Union[Callable[['YVoltage', YMeasure], Any], None]
    except TypeError:
        YVoltageValueCallback = Union[Callable, Awaitable]
        YVoltageTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YVoltage(YSensor):
    """
    The YVoltage class allows you to read and configure Yoctopuce voltage sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    _aio: YVoltage_aio
    # --- (end of YVoltage class start)
    if not _IS_MICROPYTHON:
        # --- (YVoltage return codes)
        SIGNALBIAS_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ENABLED_FALSE: Final[int] = 0
        ENABLED_TRUE: Final[int] = 1
        ENABLED_INVALID: Final[int] = -1
        # --- (end of YVoltage return codes)


    # --- (YVoltage implementation)

    @classmethod
    def FindVoltage(cls, func: str) -> YVoltage:
        """
        Retrieves a voltage sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the voltage sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YVoltage.isOnline() to test if the voltage sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a voltage sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the voltage sensor, for instance
                MOTORCTL.voltage.

        @return a YVoltage object allowing you to drive the voltage sensor.
        """
        return cls._proxy(cls, YVoltage_aio.FindVoltageInContext(YAPI_aio, func))

    @classmethod
    def FindVoltageInContext(cls, yctx: YAPIContext, func: str) -> YVoltage:
        """
        Retrieves a voltage sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the voltage sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YVoltage.isOnline() to test if the voltage sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a voltage sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the voltage sensor, for instance
                MOTORCTL.voltage.

        @return a YVoltage object allowing you to drive the voltage sensor.
        """
        return cls._proxy(cls, YVoltage_aio.FindVoltageInContext(yctx._aio, func))

    @classmethod
    def FirstVoltage(cls) -> Union[YVoltage, None]:
        """
        Starts the enumeration of voltage sensors currently accessible.
        Use the method YVoltage.nextVoltage() to iterate on
        next voltage sensors.

        @return a pointer to a YVoltage object, corresponding to
                the first voltage sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YVoltage_aio.FirstVoltageInContext(YAPI_aio))

    @classmethod
    def FirstVoltageInContext(cls, yctx: YAPIContext) -> Union[YVoltage, None]:
        """
        Starts the enumeration of voltage sensors currently accessible.
        Use the method YVoltage.nextVoltage() to iterate on
        next voltage sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YVoltage object, corresponding to
                the first voltage sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YVoltage_aio.FirstVoltageInContext(yctx._aio))

    def nextVoltage(self) -> Union[YVoltage, None]:
        """
        Continues the enumeration of voltage sensors started using yFirstVoltage().
        Caution: You can't make any assumption about the returned voltage sensors order.
        If you want to find a specific a voltage sensor, use Voltage.findVoltage()
        and a hardwareID or a logical name.

        @return a pointer to a YVoltage object, corresponding to
                a voltage sensor currently online, or a None pointer
                if there are no more voltage sensors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextVoltage())

    if not _DYNAMIC_HELPERS:
        def get_enabled(self) -> int:
            """
            Returns the activation state of this input.

            @return either YVoltage.ENABLED_FALSE or YVoltage.ENABLED_TRUE, according to the activation state of this input

            On failure, throws an exception or returns YVoltage.ENABLED_INVALID.
            """
            return self._run(self._aio.get_enabled())

    if not _DYNAMIC_HELPERS:
        def set_enabled(self, newval: int) -> int:
            """
            Changes the activation state of this voltage input. When AC measurements are disabled,
            the device will always assume a DC signal, and vice-versa. When both AC and DC measurements
            are active, the device switches between AC and DC mode based on the relative amplitude
            of variations compared to the average value.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : either YVoltage.ENABLED_FALSE or YVoltage.ENABLED_TRUE, according to the activation
            state of this voltage input

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_enabled(newval))

    if not _DYNAMIC_HELPERS:
        def set_signalBias(self, newval: float) -> int:
            """
            Changes the DC bias configured for zero shift adjustment.
            If your DC current reads positive when it should be zero, set up
            a positive signalBias of the same value to fix the zero shift.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the DC bias configured for zero shift adjustment

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_signalBias(newval))

    if not _DYNAMIC_HELPERS:
        def get_signalBias(self) -> float:
            """
            Returns the DC bias configured for zero shift adjustment.
            A positive bias value is used to correct a positive DC bias,
            while a negative bias value is used to correct a negative DC bias.

            @return a floating point number corresponding to the DC bias configured for zero shift adjustment

            On failure, throws an exception or returns YVoltage.SIGNALBIAS_INVALID.
            """
            return self._run(self._aio.get_signalBias())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YVoltageValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YVoltageTimedReportCallback) -> int:
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

    if not _DYNAMIC_HELPERS:
        def zeroAdjust(self) -> int:
            """
            Calibrate the device by adjusting signalBias so that the current
            input voltage is precisely seen as zero. Before calling this method, make
            sure to short the power source inputs as close as possible to the connector, and
            to disconnect the load to ensure the wires don't capture radiated noise.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.zeroAdjust())

    # --- (end of YVoltage implementation)

