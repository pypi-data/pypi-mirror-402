# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YLed
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
Yoctopuce library: High-level API for YLed
version: PATCH_WITH_VERSION
requires: yocto_led_aio
requires: yocto_api
provides: YLed
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

from .yocto_led_aio import YLed as YLed_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YLed class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YLedValueCallback = Union[Callable[['YLed', str], Any], None]
    except TypeError:
        YLedValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YLed(YFunction):
    """
    The YLed class allows you to drive a monocolor LED.
    You can not only to drive the intensity of the LED, but also to
    have it blink at various preset frequencies.

    """
    _aio: YLed_aio
    # --- (end of YLed class start)
    if not _IS_MICROPYTHON:
        # --- (YLed return codes)
        LUMINOSITY_INVALID: Final[int] = YAPI.INVALID_UINT
        POWER_OFF: Final[int] = 0
        POWER_ON: Final[int] = 1
        POWER_INVALID: Final[int] = -1
        BLINKING_STILL: Final[int] = 0
        BLINKING_RELAX: Final[int] = 1
        BLINKING_AWARE: Final[int] = 2
        BLINKING_RUN: Final[int] = 3
        BLINKING_CALL: Final[int] = 4
        BLINKING_PANIC: Final[int] = 5
        BLINKING_INVALID: Final[int] = -1
        # --- (end of YLed return codes)


    # --- (YLed implementation)

    @classmethod
    def FindLed(cls, func: str) -> YLed:
        """
        Retrieves a monochrome LED for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the monochrome LED is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLed.isOnline() to test if the monochrome LED is
        indeed online at a given time. In case of ambiguity when looking for
        a monochrome LED by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the monochrome LED, for instance
                YBUZZER2.led1.

        @return a YLed object allowing you to drive the monochrome LED.
        """
        return cls._proxy(cls, YLed_aio.FindLedInContext(YAPI_aio, func))

    @classmethod
    def FindLedInContext(cls, yctx: YAPIContext, func: str) -> YLed:
        """
        Retrieves a monochrome LED for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the monochrome LED is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLed.isOnline() to test if the monochrome LED is
        indeed online at a given time. In case of ambiguity when looking for
        a monochrome LED by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the monochrome LED, for instance
                YBUZZER2.led1.

        @return a YLed object allowing you to drive the monochrome LED.
        """
        return cls._proxy(cls, YLed_aio.FindLedInContext(yctx._aio, func))

    @classmethod
    def FirstLed(cls) -> Union[YLed, None]:
        """
        Starts the enumeration of monochrome LEDs currently accessible.
        Use the method YLed.nextLed() to iterate on
        next monochrome LEDs.

        @return a pointer to a YLed object, corresponding to
                the first monochrome LED currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YLed_aio.FirstLedInContext(YAPI_aio))

    @classmethod
    def FirstLedInContext(cls, yctx: YAPIContext) -> Union[YLed, None]:
        """
        Starts the enumeration of monochrome LEDs currently accessible.
        Use the method YLed.nextLed() to iterate on
        next monochrome LEDs.

        @param yctx : a YAPI context.

        @return a pointer to a YLed object, corresponding to
                the first monochrome LED currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YLed_aio.FirstLedInContext(yctx._aio))

    def nextLed(self) -> Union[YLed, None]:
        """
        Continues the enumeration of monochrome LEDs started using yFirstLed().
        Caution: You can't make any assumption about the returned monochrome LEDs order.
        If you want to find a specific a monochrome LED, use Led.findLed()
        and a hardwareID or a logical name.

        @return a pointer to a YLed object, corresponding to
                a monochrome LED currently online, or a None pointer
                if there are no more monochrome LEDs to enumerate.
        """
        return self._proxy(type(self), self._aio.nextLed())

    if not _DYNAMIC_HELPERS:
        def get_power(self) -> int:
            """
            Returns the current LED state.

            @return either YLed.POWER_OFF or YLed.POWER_ON, according to the current LED state

            On failure, throws an exception or returns YLed.POWER_INVALID.
            """
            return self._run(self._aio.get_power())

    if not _DYNAMIC_HELPERS:
        def set_power(self, newval: int) -> int:
            """
            Changes the state of the LED.

            @param newval : either YLed.POWER_OFF or YLed.POWER_ON, according to the state of the LED

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_power(newval))

    if not _DYNAMIC_HELPERS:
        def get_luminosity(self) -> int:
            """
            Returns the current LED intensity (in per cent).

            @return an integer corresponding to the current LED intensity (in per cent)

            On failure, throws an exception or returns YLed.LUMINOSITY_INVALID.
            """
            return self._run(self._aio.get_luminosity())

    if not _DYNAMIC_HELPERS:
        def set_luminosity(self, newval: int) -> int:
            """
            Changes the current LED intensity (in per cent). Remember to call the
            saveToFlash() method of the module if the modification must be kept.

            @param newval : an integer corresponding to the current LED intensity (in per cent)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_luminosity(newval))

    if not _DYNAMIC_HELPERS:
        def get_blinking(self) -> int:
            """
            Returns the current LED signaling mode.

            @return a value among YLed.BLINKING_STILL, YLed.BLINKING_RELAX, YLed.BLINKING_AWARE,
            YLed.BLINKING_RUN, YLed.BLINKING_CALL and YLed.BLINKING_PANIC corresponding to the current LED signaling mode

            On failure, throws an exception or returns YLed.BLINKING_INVALID.
            """
            return self._run(self._aio.get_blinking())

    if not _DYNAMIC_HELPERS:
        def set_blinking(self, newval: int) -> int:
            """
            Changes the current LED signaling mode.

            @param newval : a value among YLed.BLINKING_STILL, YLed.BLINKING_RELAX, YLed.BLINKING_AWARE,
            YLed.BLINKING_RUN, YLed.BLINKING_CALL and YLed.BLINKING_PANIC corresponding to the current LED signaling mode

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_blinking(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YLedValueCallback) -> int:
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

    # --- (end of YLed implementation)

