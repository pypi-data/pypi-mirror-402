# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YThreshold
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
Yoctopuce library: High-level API for YThreshold
version: PATCH_WITH_VERSION
requires: yocto_threshold_aio
requires: yocto_api
provides: YThreshold
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

from .yocto_threshold_aio import YThreshold as YThreshold_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YThreshold class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YThresholdValueCallback = Union[Callable[['YThreshold', str], Any], None]
    except TypeError:
        YThresholdValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YThreshold(YFunction):
    """
    The Threshold class allows you define a threshold on a Yoctopuce sensor
    to trigger a predefined action, on specific devices where this is implemented.

    """
    _aio: YThreshold_aio
    # --- (end of YThreshold class start)
    if not _IS_MICROPYTHON:
        # --- (YThreshold return codes)
        TARGETSENSOR_INVALID: Final[str] = YAPI.INVALID_STRING
        ALERTLEVEL_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SAFELEVEL_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        THRESHOLDSTATE_SAFE: Final[int] = 0
        THRESHOLDSTATE_ALERT: Final[int] = 1
        THRESHOLDSTATE_INVALID: Final[int] = -1
        # --- (end of YThreshold return codes)


    # --- (YThreshold implementation)

    @classmethod
    def FindThreshold(cls, func: str) -> YThreshold:
        """
        Retrieves a threshold function for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the threshold function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YThreshold.isOnline() to test if the threshold function is
        indeed online at a given time. In case of ambiguity when looking for
        a threshold function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the threshold function, for instance
                MyDevice.threshold1.

        @return a YThreshold object allowing you to drive the threshold function.
        """
        return cls._proxy(cls, YThreshold_aio.FindThresholdInContext(YAPI_aio, func))

    @classmethod
    def FindThresholdInContext(cls, yctx: YAPIContext, func: str) -> YThreshold:
        """
        Retrieves a threshold function for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the threshold function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YThreshold.isOnline() to test if the threshold function is
        indeed online at a given time. In case of ambiguity when looking for
        a threshold function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the threshold function, for instance
                MyDevice.threshold1.

        @return a YThreshold object allowing you to drive the threshold function.
        """
        return cls._proxy(cls, YThreshold_aio.FindThresholdInContext(yctx._aio, func))

    @classmethod
    def FirstThreshold(cls) -> Union[YThreshold, None]:
        """
        Starts the enumeration of threshold functions currently accessible.
        Use the method YThreshold.nextThreshold() to iterate on
        next threshold functions.

        @return a pointer to a YThreshold object, corresponding to
                the first threshold function currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YThreshold_aio.FirstThresholdInContext(YAPI_aio))

    @classmethod
    def FirstThresholdInContext(cls, yctx: YAPIContext) -> Union[YThreshold, None]:
        """
        Starts the enumeration of threshold functions currently accessible.
        Use the method YThreshold.nextThreshold() to iterate on
        next threshold functions.

        @param yctx : a YAPI context.

        @return a pointer to a YThreshold object, corresponding to
                the first threshold function currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YThreshold_aio.FirstThresholdInContext(yctx._aio))

    def nextThreshold(self) -> Union[YThreshold, None]:
        """
        Continues the enumeration of threshold functions started using yFirstThreshold().
        Caution: You can't make any assumption about the returned threshold functions order.
        If you want to find a specific a threshold function, use Threshold.findThreshold()
        and a hardwareID or a logical name.

        @return a pointer to a YThreshold object, corresponding to
                a threshold function currently online, or a None pointer
                if there are no more threshold functions to enumerate.
        """
        return self._proxy(type(self), self._aio.nextThreshold())

    if not _DYNAMIC_HELPERS:
        def get_thresholdState(self) -> int:
            """
            Returns current state of the threshold function.

            @return either YThreshold.THRESHOLDSTATE_SAFE or YThreshold.THRESHOLDSTATE_ALERT, according to
            current state of the threshold function

            On failure, throws an exception or returns YThreshold.THRESHOLDSTATE_INVALID.
            """
            return self._run(self._aio.get_thresholdState())

    if not _DYNAMIC_HELPERS:
        def get_targetSensor(self) -> str:
            """
            Returns the name of the sensor monitored by the threshold function.

            @return a string corresponding to the name of the sensor monitored by the threshold function

            On failure, throws an exception or returns YThreshold.TARGETSENSOR_INVALID.
            """
            return self._run(self._aio.get_targetSensor())

    if not _DYNAMIC_HELPERS:
        def set_alertLevel(self, newval: float) -> int:
            """
            Changes the sensor alert level triggering the threshold function.
            Remember to call the matching module saveToFlash()
            method if you want to preserve the setting after reboot.

            @param newval : a floating point number corresponding to the sensor alert level triggering the
            threshold function

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_alertLevel(newval))

    if not _DYNAMIC_HELPERS:
        def get_alertLevel(self) -> float:
            """
            Returns the sensor alert level, triggering the threshold function.

            @return a floating point number corresponding to the sensor alert level, triggering the threshold function

            On failure, throws an exception or returns YThreshold.ALERTLEVEL_INVALID.
            """
            return self._run(self._aio.get_alertLevel())

    if not _DYNAMIC_HELPERS:
        def set_safeLevel(self, newval: float) -> int:
            """
            Changes the sensor acceptable level for disabling the threshold function.
            Remember to call the matching module saveToFlash()
            method if you want to preserve the setting after reboot.

            @param newval : a floating point number corresponding to the sensor acceptable level for disabling
            the threshold function

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_safeLevel(newval))

    if not _DYNAMIC_HELPERS:
        def get_safeLevel(self) -> float:
            """
            Returns the sensor acceptable level for disabling the threshold function.

            @return a floating point number corresponding to the sensor acceptable level for disabling the
            threshold function

            On failure, throws an exception or returns YThreshold.SAFELEVEL_INVALID.
            """
            return self._run(self._aio.get_safeLevel())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YThresholdValueCallback) -> int:
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

    # --- (end of YThreshold implementation)

