# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YLongitude
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
Yoctopuce library: Asyncio implementation of YLongitude
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YLongitude
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

# --- (YLongitude class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YLongitudeValueCallback = Union[Callable[['YLongitude', str], Any], None]
        YLongitudeTimedReportCallback = Union[Callable[['YLongitude', YMeasure], Any], None]
    except TypeError:
        YLongitudeValueCallback = Union[Callable, Awaitable]
        YLongitudeTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YLongitude(YSensor):
    """
    The YLongitude class allows you to read and configure Yoctopuce longitude sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YLongitude class start)
    if not _IS_MICROPYTHON:
        # --- (YLongitude return codes)
        pass
        # --- (end of YLongitude return codes)

    # --- (YLongitude attributes declaration)
    _valueCallback: YLongitudeValueCallback
    _timedReportCallback: YLongitudeTimedReportCallback
    # --- (end of YLongitude attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Longitude', func)
        # --- (YLongitude constructor)
        # --- (end of YLongitude constructor)

    # --- (YLongitude implementation)
    @classmethod
    def FindLongitude(cls, func: str) -> YLongitude:
        """
        Retrieves a longitude sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the longitude sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLongitude.isOnline() to test if the longitude sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a longitude sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the longitude sensor, for instance
                YGNSSMK2.longitude.

        @return a YLongitude object allowing you to drive the longitude sensor.
        """
        return cls.FindLongitudeInContext(YAPI, func)

    @classmethod
    def FindLongitudeInContext(cls, yctx: YAPIContext, func: str) -> YLongitude:
        """
        Retrieves a longitude sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the longitude sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLongitude.isOnline() to test if the longitude sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a longitude sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the longitude sensor, for instance
                YGNSSMK2.longitude.

        @return a YLongitude object allowing you to drive the longitude sensor.
        """
        obj: Union[YLongitude, None] = yctx._findInCache('Longitude', func)
        if obj:
            return obj
        return YLongitude(yctx, func)

    @classmethod
    def FirstLongitude(cls) -> Union[YLongitude, None]:
        """
        Starts the enumeration of longitude sensors currently accessible.
        Use the method YLongitude.nextLongitude() to iterate on
        next longitude sensors.

        @return a pointer to a YLongitude object, corresponding to
                the first longitude sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstLongitudeInContext(YAPI)

    @classmethod
    def FirstLongitudeInContext(cls, yctx: YAPIContext) -> Union[YLongitude, None]:
        """
        Starts the enumeration of longitude sensors currently accessible.
        Use the method YLongitude.nextLongitude() to iterate on
        next longitude sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YLongitude object, corresponding to
                the first longitude sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Longitude')
        if hwid:
            return cls.FindLongitudeInContext(yctx, hwid2str(hwid))
        return None

    def nextLongitude(self) -> Union[YLongitude, None]:
        """
        Continues the enumeration of longitude sensors started using yFirstLongitude().
        Caution: You can't make any assumption about the returned longitude sensors order.
        If you want to find a specific a longitude sensor, use Longitude.findLongitude()
        and a hardwareID or a logical name.

        @return a pointer to a YLongitude object, corresponding to
                a longitude sensor currently online, or a None pointer
                if there are no more longitude sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Longitude', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindLongitudeInContext(self._yapi, hwid2str(next_hwid))
        return None

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YLongitudeValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YLongitudeTimedReportCallback) -> int:
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

    # --- (end of YLongitude implementation)

