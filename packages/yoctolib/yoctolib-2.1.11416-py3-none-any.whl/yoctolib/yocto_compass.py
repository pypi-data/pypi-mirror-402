# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YCompass
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
Yoctopuce library: High-level API for YCompass
version: PATCH_WITH_VERSION
requires: yocto_compass_aio
requires: yocto_api
provides: YCompass
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

from .yocto_compass_aio import YCompass as YCompass_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YCompass class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YCompassValueCallback = Union[Callable[['YCompass', str], Any], None]
        YCompassTimedReportCallback = Union[Callable[['YCompass', YMeasure], Any], None]
    except TypeError:
        YCompassValueCallback = Union[Callable, Awaitable]
        YCompassTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YCompass(YSensor):
    """
    The YCompass class allows you to read and configure Yoctopuce compass functions.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    _aio: YCompass_aio
    # --- (end of YCompass class start)
    if not _IS_MICROPYTHON:
        # --- (YCompass return codes)
        BANDWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        MAGNETICHEADING_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        AXIS_X: Final[int] = 0
        AXIS_Y: Final[int] = 1
        AXIS_Z: Final[int] = 2
        AXIS_INVALID: Final[int] = -1
        # --- (end of YCompass return codes)


    # --- (YCompass implementation)

    @classmethod
    def FindCompass(cls, func: str) -> YCompass:
        """
        Retrieves a compass function for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the compass function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YCompass.isOnline() to test if the compass function is
        indeed online at a given time. In case of ambiguity when looking for
        a compass function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the compass function, for instance
                Y3DMK002.compass.

        @return a YCompass object allowing you to drive the compass function.
        """
        return cls._proxy(cls, YCompass_aio.FindCompassInContext(YAPI_aio, func))

    @classmethod
    def FindCompassInContext(cls, yctx: YAPIContext, func: str) -> YCompass:
        """
        Retrieves a compass function for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the compass function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YCompass.isOnline() to test if the compass function is
        indeed online at a given time. In case of ambiguity when looking for
        a compass function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the compass function, for instance
                Y3DMK002.compass.

        @return a YCompass object allowing you to drive the compass function.
        """
        return cls._proxy(cls, YCompass_aio.FindCompassInContext(yctx._aio, func))

    @classmethod
    def FirstCompass(cls) -> Union[YCompass, None]:
        """
        Starts the enumeration of compass functions currently accessible.
        Use the method YCompass.nextCompass() to iterate on
        next compass functions.

        @return a pointer to a YCompass object, corresponding to
                the first compass function currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YCompass_aio.FirstCompassInContext(YAPI_aio))

    @classmethod
    def FirstCompassInContext(cls, yctx: YAPIContext) -> Union[YCompass, None]:
        """
        Starts the enumeration of compass functions currently accessible.
        Use the method YCompass.nextCompass() to iterate on
        next compass functions.

        @param yctx : a YAPI context.

        @return a pointer to a YCompass object, corresponding to
                the first compass function currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YCompass_aio.FirstCompassInContext(yctx._aio))

    def nextCompass(self) -> Union[YCompass, None]:
        """
        Continues the enumeration of compass functions started using yFirstCompass().
        Caution: You can't make any assumption about the returned compass functions order.
        If you want to find a specific a compass function, use Compass.findCompass()
        and a hardwareID or a logical name.

        @return a pointer to a YCompass object, corresponding to
                a compass function currently online, or a None pointer
                if there are no more compass functions to enumerate.
        """
        return self._proxy(type(self), self._aio.nextCompass())

    if not _DYNAMIC_HELPERS:
        def get_bandwidth(self) -> int:
            """
            Returns the measure update frequency, measured in Hz.

            @return an integer corresponding to the measure update frequency, measured in Hz

            On failure, throws an exception or returns YCompass.BANDWIDTH_INVALID.
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
        def get_magneticHeading(self) -> float:
            """
            Returns the magnetic heading, regardless of the configured bearing.

            @return a floating point number corresponding to the magnetic heading, regardless of the configured bearing

            On failure, throws an exception or returns YCompass.MAGNETICHEADING_INVALID.
            """
            return self._run(self._aio.get_magneticHeading())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YCompassValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YCompassTimedReportCallback) -> int:
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

    # --- (end of YCompass implementation)

