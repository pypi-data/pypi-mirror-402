# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YRelay
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
Yoctopuce library: High-level API for YRelay
version: PATCH_WITH_VERSION
requires: yocto_relay_aio
requires: yocto_api
provides: YRelay
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

from .yocto_relay_aio import YRelay as YRelay_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction, YModule
)

# --- (YRelay class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YRelayValueCallback = Union[Callable[['YRelay', str], Any], None]
    except TypeError:
        YRelayValueCallback = Union[Callable, Awaitable]
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
class YRelay(YFunction):
    """
    The YRelay class allows you to drive a Yoctopuce relay or optocoupled output.
    It can be used to simply switch the output on or off, but also to automatically generate short
    pulses of determined duration.
    On devices with two output for each relay (double throw), the two outputs are named A and B,
    with output A corresponding to the idle position (normally closed) and the output B corresponding to the
    active state (normally open).

    """
    _aio: YRelay_aio
    # --- (end of YRelay class start)
    if not _IS_MICROPYTHON:
        # --- (YRelay return codes)
        MAXTIMEONSTATEA_INVALID: Final[int] = YAPI.INVALID_LONG
        MAXTIMEONSTATEB_INVALID: Final[int] = YAPI.INVALID_LONG
        PULSETIMER_INVALID: Final[int] = YAPI.INVALID_LONG
        DELAYEDPULSETIMER_INVALID: Final[None] = None
        COUNTDOWN_INVALID: Final[int] = YAPI.INVALID_LONG
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
        # --- (end of YRelay return codes)


    # --- (YRelay implementation)

    @classmethod
    def FindRelay(cls, func: str) -> YRelay:
        """
        Retrieves a relay for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the relay is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRelay.isOnline() to test if the relay is
        indeed online at a given time. In case of ambiguity when looking for
        a relay by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the relay, for instance
                YLTCHRL1.relay1.

        @return a YRelay object allowing you to drive the relay.
        """
        return cls._proxy(cls, YRelay_aio.FindRelayInContext(YAPI_aio, func))

    @classmethod
    def FindRelayInContext(cls, yctx: YAPIContext, func: str) -> YRelay:
        """
        Retrieves a relay for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the relay is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRelay.isOnline() to test if the relay is
        indeed online at a given time. In case of ambiguity when looking for
        a relay by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the relay, for instance
                YLTCHRL1.relay1.

        @return a YRelay object allowing you to drive the relay.
        """
        return cls._proxy(cls, YRelay_aio.FindRelayInContext(yctx._aio, func))

    @classmethod
    def FirstRelay(cls) -> Union[YRelay, None]:
        """
        Starts the enumeration of relays currently accessible.
        Use the method YRelay.nextRelay() to iterate on
        next relays.

        @return a pointer to a YRelay object, corresponding to
                the first relay currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YRelay_aio.FirstRelayInContext(YAPI_aio))

    @classmethod
    def FirstRelayInContext(cls, yctx: YAPIContext) -> Union[YRelay, None]:
        """
        Starts the enumeration of relays currently accessible.
        Use the method YRelay.nextRelay() to iterate on
        next relays.

        @param yctx : a YAPI context.

        @return a pointer to a YRelay object, corresponding to
                the first relay currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YRelay_aio.FirstRelayInContext(yctx._aio))

    def nextRelay(self) -> Union[YRelay, None]:
        """
        Continues the enumeration of relays started using yFirstRelay().
        Caution: You can't make any assumption about the returned relays order.
        If you want to find a specific a relay, use Relay.findRelay()
        and a hardwareID or a logical name.

        @return a pointer to a YRelay object, corresponding to
                a relay currently online, or a None pointer
                if there are no more relays to enumerate.
        """
        return self._proxy(type(self), self._aio.nextRelay())

    if not _DYNAMIC_HELPERS:
        def get_state(self) -> int:
            """
            Returns the state of the relays (A for the idle position, B for the active position).

            @return either YRelay.STATE_A or YRelay.STATE_B, according to the state of the relays (A for the
            idle position, B for the active position)

            On failure, throws an exception or returns YRelay.STATE_INVALID.
            """
            return self._run(self._aio.get_state())

    if not _DYNAMIC_HELPERS:
        def set_state(self, newval: int) -> int:
            """
            Changes the state of the relays (A for the idle position, B for the active position).

            @param newval : either YRelay.STATE_A or YRelay.STATE_B, according to the state of the relays (A
            for the idle position, B for the active position)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_state(newval))

    if not _DYNAMIC_HELPERS:
        def get_stateAtPowerOn(self) -> int:
            """
            Returns the state of the relays at device startup (A for the idle position,
            B for the active position, UNCHANGED to leave the relay state as is).

            @return a value among YRelay.STATEATPOWERON_UNCHANGED, YRelay.STATEATPOWERON_A and
            YRelay.STATEATPOWERON_B corresponding to the state of the relays at device startup (A for the idle position,
                    B for the active position, UNCHANGED to leave the relay state as is)

            On failure, throws an exception or returns YRelay.STATEATPOWERON_INVALID.
            """
            return self._run(self._aio.get_stateAtPowerOn())

    if not _DYNAMIC_HELPERS:
        def set_stateAtPowerOn(self, newval: int) -> int:
            """
            Changes the state of the relays at device startup (A for the idle position,
            B for the active position, UNCHANGED to leave the relay state as is).
            Remember to call the matching module saveToFlash()
            method, otherwise this call will have no effect.

            @param newval : a value among YRelay.STATEATPOWERON_UNCHANGED, YRelay.STATEATPOWERON_A and
            YRelay.STATEATPOWERON_B corresponding to the state of the relays at device startup (A for the idle position,
                    B for the active position, UNCHANGED to leave the relay state as is)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_stateAtPowerOn(newval))

    if not _DYNAMIC_HELPERS:
        def get_maxTimeOnStateA(self) -> int:
            """
            Returns the maximum time (ms) allowed for the relay to stay in state
            A before automatically switching back in to B state. Zero means no time limit.

            @return an integer corresponding to the maximum time (ms) allowed for the relay to stay in state
                    A before automatically switching back in to B state

            On failure, throws an exception or returns YRelay.MAXTIMEONSTATEA_INVALID.
            """
            return self._run(self._aio.get_maxTimeOnStateA())

    if not _DYNAMIC_HELPERS:
        def set_maxTimeOnStateA(self, newval: int) -> int:
            """
            Changes the maximum time (ms) allowed for the relay to stay in state A
            before automatically switching back in to B state. Use zero for no time limit.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the maximum time (ms) allowed for the relay to stay in state A
                    before automatically switching back in to B state

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_maxTimeOnStateA(newval))

    if not _DYNAMIC_HELPERS:
        def get_maxTimeOnStateB(self) -> int:
            """
            Retourne the maximum time (ms) allowed for the relay to stay in state B
            before automatically switching back in to A state. Zero means no time limit.

            @return an integer

            On failure, throws an exception or returns YRelay.MAXTIMEONSTATEB_INVALID.
            """
            return self._run(self._aio.get_maxTimeOnStateB())

    if not _DYNAMIC_HELPERS:
        def set_maxTimeOnStateB(self, newval: int) -> int:
            """
            Changes the maximum time (ms) allowed for the relay to stay in state B before
            automatically switching back in to A state. Use zero for no time limit.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the maximum time (ms) allowed for the relay to stay in
            state B before
                    automatically switching back in to A state

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_maxTimeOnStateB(newval))

    if not _DYNAMIC_HELPERS:
        def get_output(self) -> int:
            """
            Returns the output state of the relays, when used as a simple switch (single throw).

            @return either YRelay.OUTPUT_OFF or YRelay.OUTPUT_ON, according to the output state of the relays,
            when used as a simple switch (single throw)

            On failure, throws an exception or returns YRelay.OUTPUT_INVALID.
            """
            return self._run(self._aio.get_output())

    if not _DYNAMIC_HELPERS:
        def set_output(self, newval: int) -> int:
            """
            Changes the output state of the relays, when used as a simple switch (single throw).

            @param newval : either YRelay.OUTPUT_OFF or YRelay.OUTPUT_ON, according to the output state of the
            relays, when used as a simple switch (single throw)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_output(newval))

    if not _DYNAMIC_HELPERS:
        def get_pulseTimer(self) -> int:
            """
            Returns the number of milliseconds remaining before the relays is returned to idle position
            (state A), during a measured pulse generation. When there is no ongoing pulse, returns zero.

            @return an integer corresponding to the number of milliseconds remaining before the relays is
            returned to idle position
                    (state A), during a measured pulse generation

            On failure, throws an exception or returns YRelay.PULSETIMER_INVALID.
            """
            return self._run(self._aio.get_pulseTimer())

    if not _DYNAMIC_HELPERS:
        def set_pulseTimer(self, newval: int) -> int:
            return self._run(self._aio.set_pulseTimer(newval))

    if not _DYNAMIC_HELPERS:
        def pulse(self, ms_duration) -> int:
            """
            Sets the relay to output B (active) for a specified duration, then brings it
            automatically back to output A (idle state).

            @param ms_duration : pulse duration, in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.pulse(ms_duration))

    if not _DYNAMIC_HELPERS:
        def set_delayedPulseTimer(self, newval: YDelayedPulse) -> int:
            return self._run(self._aio.set_delayedPulseTimer(newval))

    if not _DYNAMIC_HELPERS:
        def delayedPulse(self, ms_delay, ms_duration) -> int:
            """
            Schedules a pulse.

            @param ms_delay : waiting time before the pulse, in milliseconds
            @param ms_duration : pulse duration, in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.delayedPulse(ms_delay, ms_duration))

    if not _DYNAMIC_HELPERS:
        def get_countdown(self) -> int:
            """
            Returns the number of milliseconds remaining before a pulse (delayedPulse() call)
            When there is no scheduled pulse, returns zero.

            @return an integer corresponding to the number of milliseconds remaining before a pulse (delayedPulse() call)
                    When there is no scheduled pulse, returns zero

            On failure, throws an exception or returns YRelay.COUNTDOWN_INVALID.
            """
            return self._run(self._aio.get_countdown())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YRelayValueCallback) -> int:
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
        def toggle(self) -> int:
            """
            Switch the relay to the opposite state.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.toggle())

    # --- (end of YRelay implementation)

