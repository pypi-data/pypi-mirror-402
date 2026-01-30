# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YWakeUpSchedule
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
Yoctopuce library: High-level API for YWakeUpSchedule
version: PATCH_WITH_VERSION
requires: yocto_wakeupschedule_aio
requires: yocto_api
provides: YWakeUpSchedule
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

from .yocto_wakeupschedule_aio import YWakeUpSchedule as YWakeUpSchedule_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YWakeUpSchedule class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YWakeUpScheduleValueCallback = Union[Callable[['YWakeUpSchedule', str], Any], None]
    except TypeError:
        YWakeUpScheduleValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YWakeUpSchedule(YFunction):
    """
    The YWakeUpSchedule class implements a wake up condition. The wake up time is
    specified as a set of months and/or days and/or hours and/or minutes when the
    wake up should happen.

    """
    _aio: YWakeUpSchedule_aio
    # --- (end of YWakeUpSchedule class start)
    if not _IS_MICROPYTHON:
        # --- (YWakeUpSchedule return codes)
        MINUTESA_INVALID: Final[int] = YAPI.INVALID_UINT
        MINUTESB_INVALID: Final[int] = YAPI.INVALID_UINT
        HOURS_INVALID: Final[int] = YAPI.INVALID_UINT
        WEEKDAYS_INVALID: Final[int] = YAPI.INVALID_UINT
        MONTHDAYS_INVALID: Final[int] = YAPI.INVALID_UINT
        MONTHS_INVALID: Final[int] = YAPI.INVALID_UINT
        SECONDSBEFORE_INVALID: Final[int] = YAPI.INVALID_UINT
        NEXTOCCURENCE_INVALID: Final[int] = YAPI.INVALID_LONG
        # --- (end of YWakeUpSchedule return codes)


    # --- (YWakeUpSchedule implementation)

    @classmethod
    def FindWakeUpSchedule(cls, func: str) -> YWakeUpSchedule:
        """
        Retrieves a wake up schedule for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the wake up schedule is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWakeUpSchedule.isOnline() to test if the wake up schedule is
        indeed online at a given time. In case of ambiguity when looking for
        a wake up schedule by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the wake up schedule, for instance
                YHUBGSM5.wakeUpSchedule1.

        @return a YWakeUpSchedule object allowing you to drive the wake up schedule.
        """
        return cls._proxy(cls, YWakeUpSchedule_aio.FindWakeUpScheduleInContext(YAPI_aio, func))

    @classmethod
    def FindWakeUpScheduleInContext(cls, yctx: YAPIContext, func: str) -> YWakeUpSchedule:
        """
        Retrieves a wake up schedule for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the wake up schedule is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWakeUpSchedule.isOnline() to test if the wake up schedule is
        indeed online at a given time. In case of ambiguity when looking for
        a wake up schedule by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the wake up schedule, for instance
                YHUBGSM5.wakeUpSchedule1.

        @return a YWakeUpSchedule object allowing you to drive the wake up schedule.
        """
        return cls._proxy(cls, YWakeUpSchedule_aio.FindWakeUpScheduleInContext(yctx._aio, func))

    @classmethod
    def FirstWakeUpSchedule(cls) -> Union[YWakeUpSchedule, None]:
        """
        Starts the enumeration of wake up schedules currently accessible.
        Use the method YWakeUpSchedule.nextWakeUpSchedule() to iterate on
        next wake up schedules.

        @return a pointer to a YWakeUpSchedule object, corresponding to
                the first wake up schedule currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YWakeUpSchedule_aio.FirstWakeUpScheduleInContext(YAPI_aio))

    @classmethod
    def FirstWakeUpScheduleInContext(cls, yctx: YAPIContext) -> Union[YWakeUpSchedule, None]:
        """
        Starts the enumeration of wake up schedules currently accessible.
        Use the method YWakeUpSchedule.nextWakeUpSchedule() to iterate on
        next wake up schedules.

        @param yctx : a YAPI context.

        @return a pointer to a YWakeUpSchedule object, corresponding to
                the first wake up schedule currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YWakeUpSchedule_aio.FirstWakeUpScheduleInContext(yctx._aio))

    def nextWakeUpSchedule(self) -> Union[YWakeUpSchedule, None]:
        """
        Continues the enumeration of wake up schedules started using yFirstWakeUpSchedule().
        Caution: You can't make any assumption about the returned wake up schedules order.
        If you want to find a specific a wake up schedule, use WakeUpSchedule.findWakeUpSchedule()
        and a hardwareID or a logical name.

        @return a pointer to a YWakeUpSchedule object, corresponding to
                a wake up schedule currently online, or a None pointer
                if there are no more wake up schedules to enumerate.
        """
        return self._proxy(type(self), self._aio.nextWakeUpSchedule())

    if not _DYNAMIC_HELPERS:
        def get_minutesA(self) -> int:
            """
            Returns the minutes in the 00-29 interval of each hour scheduled for wake up.

            @return an integer corresponding to the minutes in the 00-29 interval of each hour scheduled for wake up

            On failure, throws an exception or returns YWakeUpSchedule.MINUTESA_INVALID.
            """
            return self._run(self._aio.get_minutesA())

    if not _DYNAMIC_HELPERS:
        def set_minutesA(self, newval: int) -> int:
            """
            Changes the minutes in the 00-29 interval when a wake up must take place.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the minutes in the 00-29 interval when a wake up must take place

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_minutesA(newval))

    if not _DYNAMIC_HELPERS:
        def get_minutesB(self) -> int:
            """
            Returns the minutes in the 30-59 interval of each hour scheduled for wake up.

            @return an integer corresponding to the minutes in the 30-59 interval of each hour scheduled for wake up

            On failure, throws an exception or returns YWakeUpSchedule.MINUTESB_INVALID.
            """
            return self._run(self._aio.get_minutesB())

    if not _DYNAMIC_HELPERS:
        def set_minutesB(self, newval: int) -> int:
            """
            Changes the minutes in the 30-59 interval when a wake up must take place.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the minutes in the 30-59 interval when a wake up must take place

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_minutesB(newval))

    if not _DYNAMIC_HELPERS:
        def get_hours(self) -> int:
            """
            Returns the hours scheduled for wake up.

            @return an integer corresponding to the hours scheduled for wake up

            On failure, throws an exception or returns YWakeUpSchedule.HOURS_INVALID.
            """
            return self._run(self._aio.get_hours())

    if not _DYNAMIC_HELPERS:
        def set_hours(self, newval: int) -> int:
            """
            Changes the hours when a wake up must take place.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the hours when a wake up must take place

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_hours(newval))

    if not _DYNAMIC_HELPERS:
        def get_weekDays(self) -> int:
            """
            Returns the days of the week scheduled for wake up.

            @return an integer corresponding to the days of the week scheduled for wake up

            On failure, throws an exception or returns YWakeUpSchedule.WEEKDAYS_INVALID.
            """
            return self._run(self._aio.get_weekDays())

    if not _DYNAMIC_HELPERS:
        def set_weekDays(self, newval: int) -> int:
            """
            Changes the days of the week when a wake up must take place.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the days of the week when a wake up must take place

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_weekDays(newval))

    if not _DYNAMIC_HELPERS:
        def get_monthDays(self) -> int:
            """
            Returns the days of the month scheduled for wake up.

            @return an integer corresponding to the days of the month scheduled for wake up

            On failure, throws an exception or returns YWakeUpSchedule.MONTHDAYS_INVALID.
            """
            return self._run(self._aio.get_monthDays())

    if not _DYNAMIC_HELPERS:
        def set_monthDays(self, newval: int) -> int:
            """
            Changes the days of the month when a wake up must take place.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the days of the month when a wake up must take place

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_monthDays(newval))

    if not _DYNAMIC_HELPERS:
        def get_months(self) -> int:
            """
            Returns the months scheduled for wake up.

            @return an integer corresponding to the months scheduled for wake up

            On failure, throws an exception or returns YWakeUpSchedule.MONTHS_INVALID.
            """
            return self._run(self._aio.get_months())

    if not _DYNAMIC_HELPERS:
        def set_months(self, newval: int) -> int:
            """
            Changes the months when a wake up must take place.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the months when a wake up must take place

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_months(newval))

    if not _DYNAMIC_HELPERS:
        def get_secondsBefore(self) -> int:
            """
            Returns the number of seconds to anticipate wake-up time to allow
            the system to power-up.

            @return an integer corresponding to the number of seconds to anticipate wake-up time to allow
                    the system to power-up

            On failure, throws an exception or returns YWakeUpSchedule.SECONDSBEFORE_INVALID.
            """
            return self._run(self._aio.get_secondsBefore())

    if not _DYNAMIC_HELPERS:
        def set_secondsBefore(self, newval: int) -> int:
            """
            Changes the number of seconds to anticipate wake-up time to allow
            the system to power-up.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the number of seconds to anticipate wake-up time to allow
                    the system to power-up

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_secondsBefore(newval))

    if not _DYNAMIC_HELPERS:
        def get_nextOccurence(self) -> int:
            """
            Returns the date/time (seconds) of the next wake up occurrence.

            @return an integer corresponding to the date/time (seconds) of the next wake up occurrence

            On failure, throws an exception or returns YWakeUpSchedule.NEXTOCCURENCE_INVALID.
            """
            return self._run(self._aio.get_nextOccurence())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YWakeUpScheduleValueCallback) -> int:
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

    if not _DYNAMIC_HELPERS:
        def get_minutes(self) -> int:
            """
            Returns all the minutes of each hour that are scheduled for wake up.
            """
            return self._run(self._aio.get_minutes())

    if not _DYNAMIC_HELPERS:
        def set_minutes(self, bitmap: int) -> int:
            """
            Changes all the minutes where a wake up must take place.

            @param bitmap : Minutes 00-59 of each hour scheduled for wake up.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_minutes(bitmap))

    # --- (end of YWakeUpSchedule implementation)

