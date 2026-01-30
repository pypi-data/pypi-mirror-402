# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YPressure
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
Yoctopuce library: Asyncio implementation of YPressure
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YPressure
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union
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

# --- (YPressure class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPressureValueCallback = Union[Callable[['YPressure', str], Any], None]
        YPressureTimedReportCallback = Union[Callable[['YPressure', YMeasure], Any], None]
    except TypeError:
        YPressureValueCallback = Union[Callable, Awaitable]
        YPressureTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPressure(YSensor):
    """
    The YPressure class allows you to read and configure Yoctopuce pressure sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YPressure class start)
    if not _IS_MICROPYTHON:
        # --- (YPressure return codes)
        pass
        # --- (end of YPressure return codes)

    # --- (YPressure attributes declaration)
    _valueCallback: YPressureValueCallback
    _timedReportCallback: YPressureTimedReportCallback
    # --- (end of YPressure attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Pressure', func)
        # --- (YPressure constructor)
        # --- (end of YPressure constructor)

    # --- (YPressure implementation)
    @classmethod
    def FindPressure(cls, func: str) -> YPressure:
        """
        Retrieves a pressure sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the pressure sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPressure.isOnline() to test if the pressure sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a pressure sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the pressure sensor, for instance
                YALTIMK2.pressure.

        @return a YPressure object allowing you to drive the pressure sensor.
        """
        return cls.FindPressureInContext(YAPI, func)

    @classmethod
    def FindPressureInContext(cls, yctx: YAPIContext, func: str) -> YPressure:
        """
        Retrieves a pressure sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the pressure sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPressure.isOnline() to test if the pressure sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a pressure sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the pressure sensor, for instance
                YALTIMK2.pressure.

        @return a YPressure object allowing you to drive the pressure sensor.
        """
        obj: Union[YPressure, None] = yctx._findInCache('Pressure', func)
        if obj:
            return obj
        return YPressure(yctx, func)

    @classmethod
    def FirstPressure(cls) -> Union[YPressure, None]:
        """
        Starts the enumeration of pressure sensors currently accessible.
        Use the method YPressure.nextPressure() to iterate on
        next pressure sensors.

        @return a pointer to a YPressure object, corresponding to
                the first pressure sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstPressureInContext(YAPI)

    @classmethod
    def FirstPressureInContext(cls, yctx: YAPIContext) -> Union[YPressure, None]:
        """
        Starts the enumeration of pressure sensors currently accessible.
        Use the method YPressure.nextPressure() to iterate on
        next pressure sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YPressure object, corresponding to
                the first pressure sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Pressure')
        if hwid:
            return cls.FindPressureInContext(yctx, hwid2str(hwid))
        return None

    def nextPressure(self) -> Union[YPressure, None]:
        """
        Continues the enumeration of pressure sensors started using yFirstPressure().
        Caution: You can't make any assumption about the returned pressure sensors order.
        If you want to find a specific a pressure sensor, use Pressure.findPressure()
        and a hardwareID or a logical name.

        @return a pointer to a YPressure object, corresponding to
                a pressure sensor currently online, or a None pointer
                if there are no more pressure sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Pressure', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindPressureInContext(self._yapi, hwid2str(next_hwid))
        return None

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YPressureValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YPressureTimedReportCallback) -> int:
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

    # --- (end of YPressure implementation)

