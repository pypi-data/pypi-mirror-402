# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YWatchdog
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
Yoctopuce library: Asyncio implementation of YWatchdog
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YWatchdog
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YModule
)

# --- (YWatchdog class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YWatchdogValueCallback = Union[Callable[['YWatchdog', str], Any], None]
    except TypeError:
        YWatchdogValueCallback = Union[Callable, Awaitable]
if _IS_MICROPYTHON:
    from collections import namedtuple
    YDelayedPulse = namedtuple("YDelayedPulse", ('target', 'ms', 'moving'))
else:
    from typing import NamedTuple
    class YDelayedPulse(NamedTuple):
        target: int
        ms: int
        moving: int


# noinspection PyProtectedMember
class YWatchdog(YFunction):
    """
    The YWatchdog class allows you to drive a Yoctopuce watchdog.
    A watchdog works like a relay, with an extra timer that can automatically
    trigger a brief power cycle to an appliance after a preset delay, to force this
    appliance to reset if a problem occurs. During normal use, the watchdog timer
    is reset periodically by the application to prevent the automated power cycle.
    Whenever the application dies, the watchdog will automatically trigger the power cycle.
    The watchdog can also be driven directly with pulse and delayedPulse
    methods to switch off an appliance for a given duration.

    """
    # --- (end of YWatchdog class start)
    if not _IS_MICROPYTHON:
        # --- (YWatchdog return codes)
        MAXTIMEONSTATEA_INVALID: Final[int] = YAPI.INVALID_LONG
        MAXTIMEONSTATEB_INVALID: Final[int] = YAPI.INVALID_LONG
        PULSETIMER_INVALID: Final[int] = YAPI.INVALID_LONG
        DELAYEDPULSETIMER_INVALID: Final[None] = None
        COUNTDOWN_INVALID: Final[int] = YAPI.INVALID_LONG
        TRIGGERDELAY_INVALID: Final[int] = YAPI.INVALID_LONG
        TRIGGERDURATION_INVALID: Final[int] = YAPI.INVALID_LONG
        LASTTRIGGER_INVALID: Final[int] = YAPI.INVALID_UINT
        STATE_A: Final[int] = 0
        STATE_B: Final[int] = 1
        STATE_INVALID: Final[int] = -1
        STATEATPOWERON_UNCHANGED: Final[int] = 0
        STATEATPOWERON_A: Final[int] = 1
        STATEATPOWERON_B: Final[int] = 2
        STATEATPOWERON_INVALID: Final[int] = -1
        OUTPUT_OFF: Final[int] = 0
        OUTPUT_ON: Final[int] = 1
        OUTPUT_INVALID: Final[int] = -1
        AUTOSTART_OFF: Final[int] = 0
        AUTOSTART_ON: Final[int] = 1
        AUTOSTART_INVALID: Final[int] = -1
        RUNNING_OFF: Final[int] = 0
        RUNNING_ON: Final[int] = 1
        RUNNING_INVALID: Final[int] = -1
        # --- (end of YWatchdog return codes)

    # --- (YWatchdog attributes declaration)
    _valueCallback: YWatchdogValueCallback
    _firm: int
    # --- (end of YWatchdog attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Watchdog', func)
        # --- (YWatchdog constructor)
        self._firm = 0
        # --- (end of YWatchdog constructor)

    # --- (YWatchdog implementation)
    @classmethod
    def FindWatchdog(cls, func: str) -> YWatchdog:
        """
        Retrieves a watchdog for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the watchdog is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWatchdog.isOnline() to test if the watchdog is
        indeed online at a given time. In case of ambiguity when looking for
        a watchdog by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the watchdog, for instance
                WDOGDC01.watchdog1.

        @return a YWatchdog object allowing you to drive the watchdog.
        """
        return cls.FindWatchdogInContext(YAPI, func)

    @classmethod
    def FindWatchdogInContext(cls, yctx: YAPIContext, func: str) -> YWatchdog:
        """
        Retrieves a watchdog for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the watchdog is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWatchdog.isOnline() to test if the watchdog is
        indeed online at a given time. In case of ambiguity when looking for
        a watchdog by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the watchdog, for instance
                WDOGDC01.watchdog1.

        @return a YWatchdog object allowing you to drive the watchdog.
        """
        obj: Union[YWatchdog, None] = yctx._findInCache('Watchdog', func)
        if obj:
            return obj
        return YWatchdog(yctx, func)

    @classmethod
    def FirstWatchdog(cls) -> Union[YWatchdog, None]:
        """
        Starts the enumeration of watchdog currently accessible.
        Use the method YWatchdog.nextWatchdog() to iterate on
        next watchdog.

        @return a pointer to a YWatchdog object, corresponding to
                the first watchdog currently online, or a None pointer
                if there are none.
        """
        return cls.FirstWatchdogInContext(YAPI)

    @classmethod
    def FirstWatchdogInContext(cls, yctx: YAPIContext) -> Union[YWatchdog, None]:
        """
        Starts the enumeration of watchdog currently accessible.
        Use the method YWatchdog.nextWatchdog() to iterate on
        next watchdog.

        @param yctx : a YAPI context.

        @return a pointer to a YWatchdog object, corresponding to
                the first watchdog currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Watchdog')
        if hwid:
            return cls.FindWatchdogInContext(yctx, hwid2str(hwid))
        return None

    def nextWatchdog(self) -> Union[YWatchdog, None]:
        """
        Continues the enumeration of watchdog started using yFirstWatchdog().
        Caution: You can't make any assumption about the returned watchdog order.
        If you want to find a specific a watchdog, use Watchdog.findWatchdog()
        and a hardwareID or a logical name.

        @return a pointer to a YWatchdog object, corresponding to
                a watchdog currently online, or a None pointer
                if there are no more watchdog to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Watchdog', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindWatchdogInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_state(self) -> int:
        """
        Returns the state of the watchdog (A for the idle position, B for the active position).

        @return either YWatchdog.STATE_A or YWatchdog.STATE_B, according to the state of the watchdog (A
        for the idle position, B for the active position)

        On failure, throws an exception or returns YWatchdog.STATE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("state")
        if json_val is None:
            return YWatchdog.STATE_INVALID
        return json_val

    async def set_state(self, newval: int) -> int:
        """
        Changes the state of the watchdog (A for the idle position, B for the active position).

        @param newval : either YWatchdog.STATE_A or YWatchdog.STATE_B, according to the state of the
        watchdog (A for the idle position, B for the active position)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("state", rest_val)

    async def get_stateAtPowerOn(self) -> int:
        """
        Returns the state of the watchdog at device startup (A for the idle position,
        B for the active position, UNCHANGED to leave the relay state as is).

        @return a value among YWatchdog.STATEATPOWERON_UNCHANGED, YWatchdog.STATEATPOWERON_A and
        YWatchdog.STATEATPOWERON_B corresponding to the state of the watchdog at device startup (A for the
        idle position,
                B for the active position, UNCHANGED to leave the relay state as is)

        On failure, throws an exception or returns YWatchdog.STATEATPOWERON_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("stateAtPowerOn")
        if json_val is None:
            return YWatchdog.STATEATPOWERON_INVALID
        return json_val

    async def set_stateAtPowerOn(self, newval: int) -> int:
        """
        Changes the state of the watchdog at device startup (A for the idle position,
        B for the active position, UNCHANGED to leave the relay state as is).
        Remember to call the matching module saveToFlash()
        method, otherwise this call will have no effect.

        @param newval : a value among YWatchdog.STATEATPOWERON_UNCHANGED, YWatchdog.STATEATPOWERON_A and
        YWatchdog.STATEATPOWERON_B corresponding to the state of the watchdog at device startup (A for the
        idle position,
                B for the active position, UNCHANGED to leave the relay state as is)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("stateAtPowerOn", rest_val)

    async def get_maxTimeOnStateA(self) -> int:
        """
        Returns the maximum time (ms) allowed for the watchdog to stay in state
        A before automatically switching back in to B state. Zero means no time limit.

        @return an integer corresponding to the maximum time (ms) allowed for the watchdog to stay in state
                A before automatically switching back in to B state

        On failure, throws an exception or returns YWatchdog.MAXTIMEONSTATEA_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("maxTimeOnStateA")
        if json_val is None:
            return YWatchdog.MAXTIMEONSTATEA_INVALID
        return json_val

    async def set_maxTimeOnStateA(self, newval: int) -> int:
        """
        Changes the maximum time (ms) allowed for the watchdog to stay in state A
        before automatically switching back in to B state. Use zero for no time limit.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the maximum time (ms) allowed for the watchdog to stay in state A
                before automatically switching back in to B state

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("maxTimeOnStateA", rest_val)

    async def get_maxTimeOnStateB(self) -> int:
        """
        Retourne the maximum time (ms) allowed for the watchdog to stay in state B
        before automatically switching back in to A state. Zero means no time limit.

        @return an integer

        On failure, throws an exception or returns YWatchdog.MAXTIMEONSTATEB_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("maxTimeOnStateB")
        if json_val is None:
            return YWatchdog.MAXTIMEONSTATEB_INVALID
        return json_val

    async def set_maxTimeOnStateB(self, newval: int) -> int:
        """
        Changes the maximum time (ms) allowed for the watchdog to stay in state B before
        automatically switching back in to A state. Use zero for no time limit.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the maximum time (ms) allowed for the watchdog to stay
        in state B before
                automatically switching back in to A state

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("maxTimeOnStateB", rest_val)

    async def get_output(self) -> int:
        """
        Returns the output state of the watchdog, when used as a simple switch (single throw).

        @return either YWatchdog.OUTPUT_OFF or YWatchdog.OUTPUT_ON, according to the output state of the
        watchdog, when used as a simple switch (single throw)

        On failure, throws an exception or returns YWatchdog.OUTPUT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("output")
        if json_val is None:
            return YWatchdog.OUTPUT_INVALID
        return json_val

    async def set_output(self, newval: int) -> int:
        """
        Changes the output state of the watchdog, when used as a simple switch (single throw).

        @param newval : either YWatchdog.OUTPUT_OFF or YWatchdog.OUTPUT_ON, according to the output state
        of the watchdog, when used as a simple switch (single throw)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("output", rest_val)

    async def get_pulseTimer(self) -> int:
        """
        Returns the number of milliseconds remaining before the watchdog is returned to idle position
        (state A), during a measured pulse generation. When there is no ongoing pulse, returns zero.

        @return an integer corresponding to the number of milliseconds remaining before the watchdog is
        returned to idle position
                (state A), during a measured pulse generation

        On failure, throws an exception or returns YWatchdog.PULSETIMER_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pulseTimer")
        if json_val is None:
            return YWatchdog.PULSETIMER_INVALID
        return json_val

    async def set_pulseTimer(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("pulseTimer", rest_val)

    async def pulse(self, ms_duration) -> int:
        """
        Sets the relay to output B (active) for a specified duration, then brings it
        automatically back to output A (idle state).

        @param ms_duration : pulse duration, in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(ms_duration)
        return await self._setAttr("pulseTimer", rest_val)

    async def get_delayedPulseTimer(self) -> YDelayedPulse:
        json_val: Union[YDelayedPulse, None] = await self._fromCache("delayedPulseTimer")
        if json_val is None:
            return YWatchdog.DELAYEDPULSETIMER_INVALID
        return json_val

    async def set_delayedPulseTimer(self, newval: YDelayedPulse) -> int:
        rest_val = str(newval.target) + ":" + str(newval.ms)
        return await self._setAttr("delayedPulseTimer", rest_val)

    async def delayedPulse(self, ms_delay, ms_duration) -> int:
        """
        Schedules a pulse.

        @param ms_delay : waiting time before the pulse, in milliseconds
        @param ms_duration : pulse duration, in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(ms_delay) + ":" + str(ms_duration)
        return await self._setAttr("delayedPulseTimer", rest_val)

    async def get_countdown(self) -> int:
        """
        Returns the number of milliseconds remaining before a pulse (delayedPulse() call)
        When there is no scheduled pulse, returns zero.

        @return an integer corresponding to the number of milliseconds remaining before a pulse (delayedPulse() call)
                When there is no scheduled pulse, returns zero

        On failure, throws an exception or returns YWatchdog.COUNTDOWN_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("countdown")
        if json_val is None:
            return YWatchdog.COUNTDOWN_INVALID
        return json_val

    async def get_autoStart(self) -> int:
        """
        Returns the watchdog running state at module power on.

        @return either YWatchdog.AUTOSTART_OFF or YWatchdog.AUTOSTART_ON, according to the watchdog running
        state at module power on

        On failure, throws an exception or returns YWatchdog.AUTOSTART_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("autoStart")
        if json_val is None:
            return YWatchdog.AUTOSTART_INVALID
        return json_val

    async def set_autoStart(self, newval: int) -> int:
        """
        Changes the watchdog running state at module power on. Remember to call the
        saveToFlash() method and then to reboot the module to apply this setting.

        @param newval : either YWatchdog.AUTOSTART_OFF or YWatchdog.AUTOSTART_ON, according to the watchdog
        running state at module power on

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("autoStart", rest_val)

    async def get_running(self) -> int:
        """
        Returns the watchdog running state.

        @return either YWatchdog.RUNNING_OFF or YWatchdog.RUNNING_ON, according to the watchdog running state

        On failure, throws an exception or returns YWatchdog.RUNNING_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("running")
        if json_val is None:
            return YWatchdog.RUNNING_INVALID
        return json_val

    async def set_running(self, newval: int) -> int:
        """
        Changes the running state of the watchdog.

        @param newval : either YWatchdog.RUNNING_OFF or YWatchdog.RUNNING_ON, according to the running
        state of the watchdog

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("running", rest_val)

    async def resetWatchdog(self) -> int:
        """
        Resets the watchdog. When the watchdog is running, this function
        must be called on a regular basis to prevent the watchdog to
        trigger

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1"
        return await self._setAttr("running", rest_val)

    async def get_triggerDelay(self) -> int:
        """
        Returns  the waiting duration before a reset is automatically triggered by the watchdog, in milliseconds.

        @return an integer corresponding to  the waiting duration before a reset is automatically triggered
        by the watchdog, in milliseconds

        On failure, throws an exception or returns YWatchdog.TRIGGERDELAY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("triggerDelay")
        if json_val is None:
            return YWatchdog.TRIGGERDELAY_INVALID
        return json_val

    async def set_triggerDelay(self, newval: int) -> int:
        """
        Changes the waiting delay before a reset is triggered by the watchdog,
        in milliseconds. Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the waiting delay before a reset is triggered by the watchdog,
                in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("triggerDelay", rest_val)

    async def get_triggerDuration(self) -> int:
        """
        Returns the duration of resets caused by the watchdog, in milliseconds.

        @return an integer corresponding to the duration of resets caused by the watchdog, in milliseconds

        On failure, throws an exception or returns YWatchdog.TRIGGERDURATION_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("triggerDuration")
        if json_val is None:
            return YWatchdog.TRIGGERDURATION_INVALID
        return json_val

    async def set_triggerDuration(self, newval: int) -> int:
        """
        Changes the duration of resets caused by the watchdog, in milliseconds.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the duration of resets caused by the watchdog, in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("triggerDuration", rest_val)

    async def get_lastTrigger(self) -> int:
        """
        Returns the number of seconds spent since the last output power-up event.

        @return an integer corresponding to the number of seconds spent since the last output power-up event

        On failure, throws an exception or returns YWatchdog.LASTTRIGGER_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("lastTrigger")
        if json_val is None:
            return YWatchdog.LASTTRIGGER_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YWatchdogValueCallback) -> int:
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

    async def toggle(self) -> int:
        """
        Switch the relay to the opposite state.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        sta: int
        fw: str
        mo: Union[YModule, None]
        if self._firm == 0:
            mo = await self.get_module()
            fw = await mo.get_firmwareRelease()
            if fw == YModule.FIRMWARERELEASE_INVALID:
                return YWatchdog.STATE_INVALID
            self._firm = YAPI._atoi(fw)
        if self._firm < 34921:
            sta = await self.get_state()
            if sta == YWatchdog.STATE_INVALID:
                return YWatchdog.STATE_INVALID
            if sta == YWatchdog.STATE_B:
                await self.set_state(YWatchdog.STATE_A)
            else:
                await self.set_state(YWatchdog.STATE_B)
            return YAPI.SUCCESS
        else:
            return await self._setAttr("state", "X")

    # --- (end of YWatchdog implementation)

