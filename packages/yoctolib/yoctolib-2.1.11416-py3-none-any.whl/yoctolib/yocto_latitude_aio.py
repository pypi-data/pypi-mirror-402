# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YLatitude
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
Yoctopuce library: Asyncio implementation of YLatitude
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YLatitude
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

# --- (YLatitude class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YLatitudeValueCallback = Union[Callable[['YLatitude', str], Any], None]
        YLatitudeTimedReportCallback = Union[Callable[['YLatitude', YMeasure], Any], None]
    except TypeError:
        YLatitudeValueCallback = Union[Callable, Awaitable]
        YLatitudeTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YLatitude(YSensor):
    """
    The YLatitude class allows you to read and configure Yoctopuce latitude sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YLatitude class start)
    if not _IS_MICROPYTHON:
        # --- (YLatitude return codes)
        pass
        # --- (end of YLatitude return codes)

    # --- (YLatitude attributes declaration)
    _valueCallback: YLatitudeValueCallback
    _timedReportCallback: YLatitudeTimedReportCallback
    # --- (end of YLatitude attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Latitude', func)
        # --- (YLatitude constructor)
        # --- (end of YLatitude constructor)

    # --- (YLatitude implementation)
    @classmethod
    def FindLatitude(cls, func: str) -> YLatitude:
        """
        Retrieves a latitude sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the latitude sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLatitude.isOnline() to test if the latitude sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a latitude sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the latitude sensor, for instance
                YGNSSMK2.latitude.

        @return a YLatitude object allowing you to drive the latitude sensor.
        """
        return cls.FindLatitudeInContext(YAPI, func)

    @classmethod
    def FindLatitudeInContext(cls, yctx: YAPIContext, func: str) -> YLatitude:
        """
        Retrieves a latitude sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the latitude sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLatitude.isOnline() to test if the latitude sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a latitude sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the latitude sensor, for instance
                YGNSSMK2.latitude.

        @return a YLatitude object allowing you to drive the latitude sensor.
        """
        obj: Union[YLatitude, None] = yctx._findInCache('Latitude', func)
        if obj:
            return obj
        return YLatitude(yctx, func)

    @classmethod
    def FirstLatitude(cls) -> Union[YLatitude, None]:
        """
        Starts the enumeration of latitude sensors currently accessible.
        Use the method YLatitude.nextLatitude() to iterate on
        next latitude sensors.

        @return a pointer to a YLatitude object, corresponding to
                the first latitude sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstLatitudeInContext(YAPI)

    @classmethod
    def FirstLatitudeInContext(cls, yctx: YAPIContext) -> Union[YLatitude, None]:
        """
        Starts the enumeration of latitude sensors currently accessible.
        Use the method YLatitude.nextLatitude() to iterate on
        next latitude sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YLatitude object, corresponding to
                the first latitude sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Latitude')
        if hwid:
            return cls.FindLatitudeInContext(yctx, hwid2str(hwid))
        return None

    def nextLatitude(self) -> Union[YLatitude, None]:
        """
        Continues the enumeration of latitude sensors started using yFirstLatitude().
        Caution: You can't make any assumption about the returned latitude sensors order.
        If you want to find a specific a latitude sensor, use Latitude.findLatitude()
        and a hardwareID or a logical name.

        @return a pointer to a YLatitude object, corresponding to
                a latitude sensor currently online, or a None pointer
                if there are no more latitude sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Latitude', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindLatitudeInContext(self._yapi, hwid2str(next_hwid))
        return None

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YLatitudeValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YLatitudeTimedReportCallback) -> int:
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

    # --- (end of YLatitude implementation)

