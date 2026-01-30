# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YRealTimeClock
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
Yoctopuce library: Asyncio implementation of YRealTimeClock
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction
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

    # --- (YRealTimeClock attributes declaration)
    _valueCallback: YRealTimeClockValueCallback
    # --- (end of YRealTimeClock attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'RealTimeClock', func)
        # --- (YRealTimeClock constructor)
        # --- (end of YRealTimeClock constructor)

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
        return cls.FindRealTimeClockInContext(YAPI, func)

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
        obj: Union[YRealTimeClock, None] = yctx._findInCache('RealTimeClock', func)
        if obj:
            return obj
        return YRealTimeClock(yctx, func)

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
        return cls.FirstRealTimeClockInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('RealTimeClock')
        if hwid:
            return cls.FindRealTimeClockInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('RealTimeClock', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindRealTimeClockInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_unixTime(self) -> int:
        """
        Returns the current time in Unix format (number of elapsed seconds since Jan 1st, 1970).

        @return an integer corresponding to the current time in Unix format (number of elapsed seconds
        since Jan 1st, 1970)

        On failure, throws an exception or returns YRealTimeClock.UNIXTIME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("unixTime")
        if json_val is None:
            return YRealTimeClock.UNIXTIME_INVALID
        return json_val

    async def set_unixTime(self, newval: int) -> int:
        """
        Changes the current time. Time is specifid in Unix format (number of elapsed seconds since Jan 1st, 1970).

        @param newval : an integer corresponding to the current time

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("unixTime", rest_val)

    async def get_dateTime(self) -> str:
        """
        Returns the current time in the form "YYYY/MM/DD hh:mm:ss".

        @return a string corresponding to the current time in the form "YYYY/MM/DD hh:mm:ss"

        On failure, throws an exception or returns YRealTimeClock.DATETIME_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("dateTime")
        if json_val is None:
            return YRealTimeClock.DATETIME_INVALID
        return json_val

    async def get_utcOffset(self) -> int:
        """
        Returns the number of seconds between current time and UTC time (time zone).

        @return an integer corresponding to the number of seconds between current time and UTC time (time zone)

        On failure, throws an exception or returns YRealTimeClock.UTCOFFSET_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("utcOffset")
        if json_val is None:
            return YRealTimeClock.UTCOFFSET_INVALID
        return json_val

    async def set_utcOffset(self, newval: int) -> int:
        """
        Changes the number of seconds between current time and UTC time (time zone).
        The timezone is automatically rounded to the nearest multiple of 15 minutes.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : an integer corresponding to the number of seconds between current time and UTC time (time zone)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("utcOffset", rest_val)

    async def get_timeSet(self) -> int:
        """
        Returns true if the clock has been set, and false otherwise.

        @return either YRealTimeClock.TIMESET_FALSE or YRealTimeClock.TIMESET_TRUE, according to true if
        the clock has been set, and false otherwise

        On failure, throws an exception or returns YRealTimeClock.TIMESET_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("timeSet")
        if json_val is None:
            return YRealTimeClock.TIMESET_INVALID
        return json_val

    async def get_disableHostSync(self) -> int:
        """
        Returns true if the automatic clock synchronization with host has been disabled,
        and false otherwise.

        @return either YRealTimeClock.DISABLEHOSTSYNC_FALSE or YRealTimeClock.DISABLEHOSTSYNC_TRUE,
        according to true if the automatic clock synchronization with host has been disabled,
                and false otherwise

        On failure, throws an exception or returns YRealTimeClock.DISABLEHOSTSYNC_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("disableHostSync")
        if json_val is None:
            return YRealTimeClock.DISABLEHOSTSYNC_INVALID
        return json_val

    async def set_disableHostSync(self, newval: int) -> int:
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
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("disableHostSync", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YRealTimeClockValueCallback) -> int:
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

    # --- (end of YRealTimeClock implementation)

