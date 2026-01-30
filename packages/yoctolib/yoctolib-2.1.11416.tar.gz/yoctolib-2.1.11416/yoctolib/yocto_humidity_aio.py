# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YHumidity
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
Yoctopuce library: Asyncio implementation of YHumidity
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YHumidity
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

# --- (YHumidity class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YHumidityValueCallback = Union[Callable[['YHumidity', str], Any], None]
        YHumidityTimedReportCallback = Union[Callable[['YHumidity', YMeasure], Any], None]
    except TypeError:
        YHumidityValueCallback = Union[Callable, Awaitable]
        YHumidityTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YHumidity(YSensor):
    """
    The YHumidity class allows you to read and configure Yoctopuce humidity sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YHumidity class start)
    if not _IS_MICROPYTHON:
        # --- (YHumidity return codes)
        RELHUM_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ABSHUM_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        # --- (end of YHumidity return codes)

    # --- (YHumidity attributes declaration)
    _valueCallback: YHumidityValueCallback
    _timedReportCallback: YHumidityTimedReportCallback
    # --- (end of YHumidity attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Humidity', func)
        # --- (YHumidity constructor)
        # --- (end of YHumidity constructor)

    # --- (YHumidity implementation)
    @classmethod
    def FindHumidity(cls, func: str) -> YHumidity:
        """
        Retrieves a humidity sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the humidity sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YHumidity.isOnline() to test if the humidity sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a humidity sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the humidity sensor, for instance
                YCO2MK02.humidity.

        @return a YHumidity object allowing you to drive the humidity sensor.
        """
        return cls.FindHumidityInContext(YAPI, func)

    @classmethod
    def FindHumidityInContext(cls, yctx: YAPIContext, func: str) -> YHumidity:
        """
        Retrieves a humidity sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the humidity sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YHumidity.isOnline() to test if the humidity sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a humidity sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the humidity sensor, for instance
                YCO2MK02.humidity.

        @return a YHumidity object allowing you to drive the humidity sensor.
        """
        obj: Union[YHumidity, None] = yctx._findInCache('Humidity', func)
        if obj:
            return obj
        return YHumidity(yctx, func)

    @classmethod
    def FirstHumidity(cls) -> Union[YHumidity, None]:
        """
        Starts the enumeration of humidity sensors currently accessible.
        Use the method YHumidity.nextHumidity() to iterate on
        next humidity sensors.

        @return a pointer to a YHumidity object, corresponding to
                the first humidity sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstHumidityInContext(YAPI)

    @classmethod
    def FirstHumidityInContext(cls, yctx: YAPIContext) -> Union[YHumidity, None]:
        """
        Starts the enumeration of humidity sensors currently accessible.
        Use the method YHumidity.nextHumidity() to iterate on
        next humidity sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YHumidity object, corresponding to
                the first humidity sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Humidity')
        if hwid:
            return cls.FindHumidityInContext(yctx, hwid2str(hwid))
        return None

    def nextHumidity(self) -> Union[YHumidity, None]:
        """
        Continues the enumeration of humidity sensors started using yFirstHumidity().
        Caution: You can't make any assumption about the returned humidity sensors order.
        If you want to find a specific a humidity sensor, use Humidity.findHumidity()
        and a hardwareID or a logical name.

        @return a pointer to a YHumidity object, corresponding to
                a humidity sensor currently online, or a None pointer
                if there are no more humidity sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Humidity', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindHumidityInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_unit(self, newval: str) -> int:
        """
        Changes the primary unit for measuring humidity. That unit is a string.
        If that strings starts with the letter 'g', the primary measured value is the absolute
        humidity, in g/m3. Otherwise, the primary measured value will be the relative humidity
        (RH), in per cents.

        Remember to call the saveToFlash() method of the module if the modification
        must be kept.

        @param newval : a string corresponding to the primary unit for measuring humidity

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("unit", rest_val)

    async def get_relHum(self) -> float:
        """
        Returns the current relative humidity, in per cents.

        @return a floating point number corresponding to the current relative humidity, in per cents

        On failure, throws an exception or returns YHumidity.RELHUM_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("relHum")
        if json_val is None:
            return YHumidity.RELHUM_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_absHum(self) -> float:
        """
        Returns the current absolute humidity, in grams per cubic meter of air.

        @return a floating point number corresponding to the current absolute humidity, in grams per cubic meter of air

        On failure, throws an exception or returns YHumidity.ABSHUM_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("absHum")
        if json_val is None:
            return YHumidity.ABSHUM_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YHumidityValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YHumidityTimedReportCallback) -> int:
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

    # --- (end of YHumidity implementation)

