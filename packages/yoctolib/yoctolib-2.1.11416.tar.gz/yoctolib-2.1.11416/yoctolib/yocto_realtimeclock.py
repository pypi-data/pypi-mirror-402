# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YRealTimeClock
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
Yoctopuce library: High-level API for YRealTimeClock
version: PATCH_WITH_VERSION
requires: yocto_realtimeclock_aio
requires: yocto_api
provides: YRealTimeClock
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

from .yocto_realtimeclock_aio import YRealTimeClock as YRealTimeClock_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YRealTimeClock class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YRealTimeClockValueCallback = Union[Callable[['YRealTimeClock', str], Any], None]
    except TypeError:
        YRealTimeClockValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YRealTimeClock(YFunction):
    """
    The YRealTimeClock class provide access to the embedded real-time clock available on some Yoctopuce
    devices. It can provide current date and time, even after a power outage
    lasting several days. It is the base for automated wake-up functions provided by the WakeUpScheduler.
    The current time may represent a local time as well as an UTC time, but no automatic time change
    will occur to account for daylight saving time.

    """
    _aio: YRealTimeClock_aio
    # --- (end of YRealTimeClock class start)
    if not _IS_MICROPYTHON:
        # --- (YRealTimeClock return codes)
        UNIXTIME_INVALID: Final[int] = YAPI.INVALID_LONG
        DATETIME_INVALID: Final[str] = YAPI.INVALID_STRING
        UTCOFFSET_INVALID: Final[int] = YAPI.INVALID_INT
        TIMESET_FALSE: Final[int] = 0
        TIMESET_TRUE: Final[int] = 1
        TIMESET_INVALID: Final[int] = -1
        DISABLEHOSTSYNC_FALSE: Final[int] = 0
        DISABLEHOSTSYNC_TRUE: Final[int] = 1
        DISABLEHOSTSYNC_INVALID: Final[int] = -1
        # --- (end of YRealTimeClock return codes)


    # --- (YRealTimeClock implementation)

    @classmethod
    def FindRealTimeClock(cls, func: str) -> YRealTimeClock:
        """
        Retrieves a real-time clock for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the real-time clock is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRealTimeClock.isOnline() to test if the real-time clock is
        indeed online at a given time. In case of ambiguity when looking for
        a real-time clock by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the real-time clock, for instance
                YHUBGSM5.realTimeClock.

        @return a YRealTimeClock object allowing you to drive the real-time clock.
        """
        return cls._proxy(cls, YRealTimeClock_aio.FindRealTimeClockInContext(YAPI_aio, func))

    @classmethod
    def FindRealTimeClockInContext(cls, yctx: YAPIContext, func: str) -> YRealTimeClock:
        """
        Retrieves a real-time clock for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the real-time clock is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRealTimeClock.isOnline() to test if the real-time clock is
        indeed online at a given time. In case of ambiguity when looking for
        a real-time clock by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the real-time clock, for instance
                YHUBGSM5.realTimeClock.

        @return a YRealTimeClock object allowing you to drive the real-time clock.
        """
        return cls._proxy(cls, YRealTimeClock_aio.FindRealTimeClockInContext(yctx._aio, func))

    @classmethod
    def FirstRealTimeClock(cls) -> Union[YRealTimeClock, None]:
        """
        Starts the enumeration of real-time clocks currently accessible.
        Use the method YRealTimeClock.nextRealTimeClock() to iterate on
        next real-time clocks.

        @return a pointer to a YRealTimeClock object, corresponding to
                the first real-time clock currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YRealTimeClock_aio.FirstRealTimeClockInContext(YAPI_aio))

    @classmethod
    def FirstRealTimeClockInContext(cls, yctx: YAPIContext) -> Union[YRealTimeClock, None]:
        """
        Starts the enumeration of real-time clocks currently accessible.
        Use the method YRealTimeClock.nextRealTimeClock() to iterate on
        next real-time clocks.

        @param yctx : a YAPI context.

        @return a pointer to a YRealTimeClock object, corresponding to
                the first real-time clock currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YRealTimeClock_aio.FirstRealTimeClockInContext(yctx._aio))

    def nextRealTimeClock(self) -> Union[YRealTimeClock, None]:
        """
        Continues the enumeration of real-time clocks started using yFirstRealTimeClock().
        Caution: You can't make any assumption about the returned real-time clocks order.
        If you want to find a specific a real-time clock, use RealTimeClock.findRealTimeClock()
        and a hardwareID or a logical name.

        @return a pointer to a YRealTimeClock object, corresponding to
                a real-time clock currently online, or a None pointer
                if there are no more real-time clocks to enumerate.
        """
        return self._proxy(type(self), self._aio.nextRealTimeClock())

    if not _DYNAMIC_HELPERS:
        def get_unixTime(self) -> int:
            """
            Returns the current time in Unix format (number of elapsed seconds since Jan 1st, 1970).

            @return an integer corresponding to the current time in Unix format (number of elapsed seconds
            since Jan 1st, 1970)

            On failure, throws an exception or returns YRealTimeClock.UNIXTIME_INVALID.
            """
            return self._run(self._aio.get_unixTime())

    if not _DYNAMIC_HELPERS:
        def set_unixTime(self, newval: int) -> int:
            """
            Changes the current time. Time is specifid in Unix format (number of elapsed seconds since Jan 1st, 1970).

            @param newval : an integer corresponding to the current time

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_unixTime(newval))

    if not _DYNAMIC_HELPERS:
        def get_dateTime(self) -> str:
            """
            Returns the current time in the form "YYYY/MM/DD hh:mm:ss".

            @return a string corresponding to the current time in the form "YYYY/MM/DD hh:mm:ss"

            On failure, throws an exception or returns YRealTimeClock.DATETIME_INVALID.
            """
            return self._run(self._aio.get_dateTime())

    if not _DYNAMIC_HELPERS:
        def get_utcOffset(self) -> int:
            """
            Returns the number of seconds between current time and UTC time (time zone).

            @return an integer corresponding to the number of seconds between current time and UTC time (time zone)

            On failure, throws an exception or returns YRealTimeClock.UTCOFFSET_INVALID.
            """
            return self._run(self._aio.get_utcOffset())

    if not _DYNAMIC_HELPERS:
        def set_utcOffset(self, newval: int) -> int:
            """
            Changes the number of seconds between current time and UTC time (time zone).
            The timezone is automatically rounded to the nearest multiple of 15 minutes.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the number of seconds between current time and UTC time (time zone)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_utcOffset(newval))

    if not _DYNAMIC_HELPERS:
        def get_timeSet(self) -> int:
            """
            Returns true if the clock has been set, and false otherwise.

            @return either YRealTimeClock.TIMESET_FALSE or YRealTimeClock.TIMESET_TRUE, according to true if
            the clock has been set, and false otherwise

            On failure, throws an exception or returns YRealTimeClock.TIMESET_INVALID.
            """
            return self._run(self._aio.get_timeSet())

    if not _DYNAMIC_HELPERS:
        def get_disableHostSync(self) -> int:
            """
            Returns true if the automatic clock synchronization with host has been disabled,
            and false otherwise.

            @return either YRealTimeClock.DISABLEHOSTSYNC_FALSE or YRealTimeClock.DISABLEHOSTSYNC_TRUE,
            according to true if the automatic clock synchronization with host has been disabled,
                    and false otherwise

            On failure, throws an exception or returns YRealTimeClock.DISABLEHOSTSYNC_INVALID.
            """
            return self._run(self._aio.get_disableHostSync())

    if not _DYNAMIC_HELPERS:
        def set_disableHostSync(self, newval: int) -> int:
            """
            Changes the automatic clock synchronization with host working state.
            To disable automatic synchronization, set the value to true.
            To enable automatic synchronization (default), set the value to false.

            If you want the change to be kept after a device reboot,
            make sure  to call the matching module saveToFlash().

            @param newval : either YRealTimeClock.DISABLEHOSTSYNC_FALSE or YRealTimeClock.DISABLEHOSTSYNC_TRUE,
            according to the automatic clock synchronization with host working state

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_disableHostSync(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YRealTimeClockValueCallback) -> int:
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

    # --- (end of YRealTimeClock implementation)

