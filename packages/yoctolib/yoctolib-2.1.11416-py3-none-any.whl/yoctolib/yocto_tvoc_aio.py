# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YTvoc
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
Yoctopuce library: Asyncio implementation of YTvoc
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YTvoc
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

# --- (YTvoc class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YTvocValueCallback = Union[Callable[['YTvoc', str], Any], None]
        YTvocTimedReportCallback = Union[Callable[['YTvoc', YMeasure], Any], None]
    except TypeError:
        YTvocValueCallback = Union[Callable, Awaitable]
        YTvocTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YTvoc(YSensor):
    """
    The YTvoc class allows you to read and configure Yoctopuce Total Volatile Organic Compound sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    # --- (end of YTvoc class start)
    if not _IS_MICROPYTHON:
        # --- (YTvoc return codes)
        pass
        # --- (end of YTvoc return codes)

    # --- (YTvoc attributes declaration)
    _valueCallback: YTvocValueCallback
    _timedReportCallback: YTvocTimedReportCallback
    # --- (end of YTvoc attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Tvoc', func)
        # --- (YTvoc constructor)
        # --- (end of YTvoc constructor)

    # --- (YTvoc implementation)
    @classmethod
    def FindTvoc(cls, func: str) -> YTvoc:
        """
        Retrieves a Total  Volatile Organic Compound sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the Total  Volatile Organic Compound sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YTvoc.isOnline() to test if the Total  Volatile Organic Compound sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a Total  Volatile Organic Compound sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the Total  Volatile Organic Compound sensor, for instance
                YVOCMK03.tvoc.

        @return a YTvoc object allowing you to drive the Total  Volatile Organic Compound sensor.
        """
        return cls.FindTvocInContext(YAPI, func)

    @classmethod
    def FindTvocInContext(cls, yctx: YAPIContext, func: str) -> YTvoc:
        """
        Retrieves a Total  Volatile Organic Compound sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the Total  Volatile Organic Compound sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YTvoc.isOnline() to test if the Total  Volatile Organic Compound sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a Total  Volatile Organic Compound sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the Total  Volatile Organic Compound sensor, for instance
                YVOCMK03.tvoc.

        @return a YTvoc object allowing you to drive the Total  Volatile Organic Compound sensor.
        """
        obj: Union[YTvoc, None] = yctx._findInCache('Tvoc', func)
        if obj:
            return obj
        return YTvoc(yctx, func)

    @classmethod
    def FirstTvoc(cls) -> Union[YTvoc, None]:
        """
        Starts the enumeration of Total Volatile Organic Compound sensors currently accessible.
        Use the method YTvoc.nextTvoc() to iterate on
        next Total Volatile Organic Compound sensors.

        @return a pointer to a YTvoc object, corresponding to
                the first Total Volatile Organic Compound sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstTvocInContext(YAPI)

    @classmethod
    def FirstTvocInContext(cls, yctx: YAPIContext) -> Union[YTvoc, None]:
        """
        Starts the enumeration of Total Volatile Organic Compound sensors currently accessible.
        Use the method YTvoc.nextTvoc() to iterate on
        next Total Volatile Organic Compound sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YTvoc object, corresponding to
                the first Total Volatile Organic Compound sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Tvoc')
        if hwid:
            return cls.FindTvocInContext(yctx, hwid2str(hwid))
        return None

    def nextTvoc(self) -> Union[YTvoc, None]:
        """
        Continues the enumeration of Total Volatile Organic Compound sensors started using yFirstTvoc().
        Caution: You can't make any assumption about the returned Total Volatile Organic Compound sensors order.
        If you want to find a specific a Total  Volatile Organic Compound sensor, use Tvoc.findTvoc()
        and a hardwareID or a logical name.

        @return a pointer to a YTvoc object, corresponding to
                a Total  Volatile Organic Compound sensor currently online, or a None pointer
                if there are no more Total Volatile Organic Compound sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Tvoc', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindTvocInContext(self._yapi, hwid2str(next_hwid))
        return None

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YTvocValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YTvocTimedReportCallback) -> int:
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

    # --- (end of YTvoc implementation)

