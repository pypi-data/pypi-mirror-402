# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YTvoc
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
Yoctopuce library: High-level API for YTvoc
version: PATCH_WITH_VERSION
requires: yocto_tvoc_aio
requires: yocto_api
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_tvoc_aio import YTvoc as YTvoc_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
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
    _aio: YTvoc_aio
    # --- (end of YTvoc class start)
    if not _IS_MICROPYTHON:
        # --- (YTvoc return codes)
        pass
        # --- (end of YTvoc return codes)


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
        return cls._proxy(cls, YTvoc_aio.FindTvocInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YTvoc_aio.FindTvocInContext(yctx._aio, func))

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
        return cls._proxy(cls, YTvoc_aio.FirstTvocInContext(YAPI_aio))

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
        return cls._proxy(cls, YTvoc_aio.FirstTvocInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextTvoc())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YTvocValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YTvocTimedReportCallback) -> int:
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

    # --- (end of YTvoc implementation)

