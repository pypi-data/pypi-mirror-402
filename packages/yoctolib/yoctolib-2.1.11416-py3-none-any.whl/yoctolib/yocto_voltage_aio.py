# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YVoltage
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
Yoctopuce library: Asyncio implementation of YVoltage
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YSensor, YMeasure
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
    # --- (end of YVoltage class start)
    if not _IS_MICROPYTHON:
        # --- (YVoltage return codes)
        SIGNALBIAS_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ENABLED_FALSE: Final[int] = 0
        ENABLED_TRUE: Final[int] = 1
        ENABLED_INVALID: Final[int] = -1
        # --- (end of YVoltage return codes)

    # --- (YVoltage attributes declaration)
    _valueCallback: YVoltageValueCallback
    _timedReportCallback: YVoltageTimedReportCallback
    # --- (end of YVoltage attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Voltage', func)
        # --- (YVoltage constructor)
        # --- (end of YVoltage constructor)

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
        return cls.FindVoltageInContext(YAPI, func)

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
        obj: Union[YVoltage, None] = yctx._findInCache('Voltage', func)
        if obj:
            return obj
        return YVoltage(yctx, func)

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
        return cls.FirstVoltageInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('Voltage')
        if hwid:
            return cls.FindVoltageInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Voltage', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindVoltageInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_enabled(self) -> int:
        """
        Returns the activation state of this input.

        @return either YVoltage.ENABLED_FALSE or YVoltage.ENABLED_TRUE, according to the activation state of this input

        On failure, throws an exception or returns YVoltage.ENABLED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("enabled")
        if json_val is None:
            return YVoltage.ENABLED_INVALID
        return json_val

    async def set_enabled(self, newval: int) -> int:
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
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("enabled", rest_val)

    async def set_signalBias(self, newval: float) -> int:
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
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("signalBias", rest_val)

    async def get_signalBias(self) -> float:
        """
        Returns the DC bias configured for zero shift adjustment.
        A positive bias value is used to correct a positive DC bias,
        while a negative bias value is used to correct a negative DC bias.

        @return a floating point number corresponding to the DC bias configured for zero shift adjustment

        On failure, throws an exception or returns YVoltage.SIGNALBIAS_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("signalBias")
        if json_val is None:
            return YVoltage.SIGNALBIAS_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YVoltageValueCallback) -> int:
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
            return await super().registerValueCallback(callback)

    if not _IS_MICROPYTHON:
        async def registerTimedReportCallback(self, callback: YVoltageTimedReportCallback) -> int:
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
            return await super().registerTimedReportCallback(callback)

    async def zeroAdjust(self) -> int:
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
        currSignal: float
        bias: float
        currSignal = await self.get_currentRawValue()
        bias = await self.get_signalBias() + currSignal
        if not ((bias > -0.5) and(bias < 0.5)):
            self._throw(YAPI.INVALID_ARGUMENT, "suspicious zeroAdjust, please ensure that the power source inputs are shorted")
            return YAPI.INVALID_ARGUMENT
        return await self.set_signalBias(bias)

    # --- (end of YVoltage implementation)

