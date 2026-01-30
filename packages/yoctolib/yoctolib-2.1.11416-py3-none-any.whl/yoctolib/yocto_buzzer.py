# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YBuzzer
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
Yoctopuce library: High-level API for YBuzzer
version: PATCH_WITH_VERSION
requires: yocto_buzzer_aio
requires: yocto_api
provides: YBuzzer
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

from .yocto_buzzer_aio import YBuzzer as YBuzzer_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YBuzzer class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YBuzzerValueCallback = Union[Callable[['YBuzzer', str], Any], None]
    except TypeError:
        YBuzzerValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YBuzzer(YFunction):
    """
    The YBuzzer class allows you to drive a buzzer. You can
    choose the frequency and the volume at which the buzzer must sound.
    You can also pre-program a play sequence.

    """
    _aio: YBuzzer_aio
    # --- (end of YBuzzer class start)
    if not _IS_MICROPYTHON:
        # --- (YBuzzer return codes)
        FREQUENCY_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        VOLUME_INVALID: Final[int] = YAPI.INVALID_UINT
        PLAYSEQSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        PLAYSEQMAXSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        PLAYSEQSIGNATURE_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of YBuzzer return codes)


    # --- (YBuzzer implementation)

    @classmethod
    def FindBuzzer(cls, func: str) -> YBuzzer:
        """
        Retrieves a buzzer for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the buzzer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YBuzzer.isOnline() to test if the buzzer is
        indeed online at a given time. In case of ambiguity when looking for
        a buzzer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the buzzer, for instance
                YBUZZER2.buzzer.

        @return a YBuzzer object allowing you to drive the buzzer.
        """
        return cls._proxy(cls, YBuzzer_aio.FindBuzzerInContext(YAPI_aio, func))

    @classmethod
    def FindBuzzerInContext(cls, yctx: YAPIContext, func: str) -> YBuzzer:
        """
        Retrieves a buzzer for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the buzzer is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YBuzzer.isOnline() to test if the buzzer is
        indeed online at a given time. In case of ambiguity when looking for
        a buzzer by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the buzzer, for instance
                YBUZZER2.buzzer.

        @return a YBuzzer object allowing you to drive the buzzer.
        """
        return cls._proxy(cls, YBuzzer_aio.FindBuzzerInContext(yctx._aio, func))

    @classmethod
    def FirstBuzzer(cls) -> Union[YBuzzer, None]:
        """
        Starts the enumeration of buzzers currently accessible.
        Use the method YBuzzer.nextBuzzer() to iterate on
        next buzzers.

        @return a pointer to a YBuzzer object, corresponding to
                the first buzzer currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YBuzzer_aio.FirstBuzzerInContext(YAPI_aio))

    @classmethod
    def FirstBuzzerInContext(cls, yctx: YAPIContext) -> Union[YBuzzer, None]:
        """
        Starts the enumeration of buzzers currently accessible.
        Use the method YBuzzer.nextBuzzer() to iterate on
        next buzzers.

        @param yctx : a YAPI context.

        @return a pointer to a YBuzzer object, corresponding to
                the first buzzer currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YBuzzer_aio.FirstBuzzerInContext(yctx._aio))

    def nextBuzzer(self) -> Union[YBuzzer, None]:
        """
        Continues the enumeration of buzzers started using yFirstBuzzer().
        Caution: You can't make any assumption about the returned buzzers order.
        If you want to find a specific a buzzer, use Buzzer.findBuzzer()
        and a hardwareID or a logical name.

        @return a pointer to a YBuzzer object, corresponding to
                a buzzer currently online, or a None pointer
                if there are no more buzzers to enumerate.
        """
        return self._proxy(type(self), self._aio.nextBuzzer())

    if not _DYNAMIC_HELPERS:
        def set_frequency(self, newval: float) -> int:
            """
            Changes the frequency of the signal sent to the buzzer. A zero value stops the buzzer.

            @param newval : a floating point number corresponding to the frequency of the signal sent to the buzzer

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_frequency(newval))

    if not _DYNAMIC_HELPERS:
        def get_frequency(self) -> float:
            """
            Returns the  frequency of the signal sent to the buzzer/speaker.

            @return a floating point number corresponding to the  frequency of the signal sent to the buzzer/speaker

            On failure, throws an exception or returns YBuzzer.FREQUENCY_INVALID.
            """
            return self._run(self._aio.get_frequency())

    if not _DYNAMIC_HELPERS:
        def get_volume(self) -> int:
            """
            Returns the volume of the signal sent to the buzzer/speaker.

            @return an integer corresponding to the volume of the signal sent to the buzzer/speaker

            On failure, throws an exception or returns YBuzzer.VOLUME_INVALID.
            """
            return self._run(self._aio.get_volume())

    if not _DYNAMIC_HELPERS:
        def set_volume(self, newval: int) -> int:
            """
            Changes the volume of the signal sent to the buzzer/speaker. Remember to call the
            saveToFlash() method of the module if the modification must be kept.

            @param newval : an integer corresponding to the volume of the signal sent to the buzzer/speaker

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_volume(newval))

    if not _DYNAMIC_HELPERS:
        def get_playSeqSize(self) -> int:
            """
            Returns the current length of the playing sequence.

            @return an integer corresponding to the current length of the playing sequence

            On failure, throws an exception or returns YBuzzer.PLAYSEQSIZE_INVALID.
            """
            return self._run(self._aio.get_playSeqSize())

    if not _DYNAMIC_HELPERS:
        def get_playSeqMaxSize(self) -> int:
            """
            Returns the maximum length of the playing sequence.

            @return an integer corresponding to the maximum length of the playing sequence

            On failure, throws an exception or returns YBuzzer.PLAYSEQMAXSIZE_INVALID.
            """
            return self._run(self._aio.get_playSeqMaxSize())

    if not _DYNAMIC_HELPERS:
        def get_playSeqSignature(self) -> int:
            """
            Returns the playing sequence signature. As playing
            sequences cannot be read from the device, this can be used
            to detect if a specific playing sequence is already
            programmed.

            @return an integer corresponding to the playing sequence signature

            On failure, throws an exception or returns YBuzzer.PLAYSEQSIGNATURE_INVALID.
            """
            return self._run(self._aio.get_playSeqSignature())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YBuzzerValueCallback) -> int:
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
        def addFreqMoveToPlaySeq(self, freq: int, msDelay: int) -> int:
            """
            Adds a new frequency transition to the playing sequence.

            @param freq    : desired frequency when the transition is completed, in Hz
            @param msDelay : duration of the frequency transition, in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.addFreqMoveToPlaySeq(freq, msDelay))

    if not _DYNAMIC_HELPERS:
        def addPulseToPlaySeq(self, freq: int, msDuration: int) -> int:
            """
            Adds a pulse to the playing sequence.

            @param freq : pulse frequency, in Hz
            @param msDuration : pulse duration, in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.addPulseToPlaySeq(freq, msDuration))

    if not _DYNAMIC_HELPERS:
        def addVolMoveToPlaySeq(self, volume: int, msDuration: int) -> int:
            """
            Adds a new volume transition to the playing sequence. Frequency stays untouched:
            if frequency is at zero, the transition has no effect.

            @param volume    : desired volume when the transition is completed, as a percentage.
            @param msDuration : duration of the volume transition, in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.addVolMoveToPlaySeq(volume, msDuration))

    if not _DYNAMIC_HELPERS:
        def addNotesToPlaySeq(self, notes: str) -> int:
            """
            Adds notes to the playing sequence. Notes are provided as text words, separated by
            spaces. The pitch is specified using the usual letter from A to G. The duration is
            specified as the divisor of a whole note: 4 for a fourth, 8 for an eight note, etc.
            Some modifiers are supported: # and b to alter a note pitch,
            ' and , to move to the upper/lower octave, . to enlarge
            the note duration.

            @param notes : notes to be played, as a text string.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.addNotesToPlaySeq(notes))

    if not _DYNAMIC_HELPERS:
        def startPlaySeq(self) -> int:
            """
            Starts the preprogrammed playing sequence. The sequence
            runs in loop until it is stopped by stopPlaySeq or an explicit
            change. To play the sequence only once, use oncePlaySeq().

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.startPlaySeq())

    if not _DYNAMIC_HELPERS:
        def stopPlaySeq(self) -> int:
            """
            Stops the preprogrammed playing sequence and sets the frequency to zero.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.stopPlaySeq())

    if not _DYNAMIC_HELPERS:
        def resetPlaySeq(self) -> int:
            """
            Resets the preprogrammed playing sequence and sets the frequency to zero.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.resetPlaySeq())

    if not _DYNAMIC_HELPERS:
        def oncePlaySeq(self) -> int:
            """
            Starts the preprogrammed playing sequence and run it once only.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.oncePlaySeq())

    if not _DYNAMIC_HELPERS:
        def savePlaySeq(self) -> int:
            """
            Saves the preprogrammed playing sequence to flash memory.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.savePlaySeq())

    if not _DYNAMIC_HELPERS:
        def reloadPlaySeq(self) -> int:
            """
            Reloads the preprogrammed playing sequence from the flash memory.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reloadPlaySeq())

    if not _DYNAMIC_HELPERS:
        def pulse(self, frequency: int, duration: int) -> int:
            """
            Activates the buzzer for a short duration.

            @param frequency : pulse frequency, in hertz
            @param duration : pulse duration in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.pulse(frequency, duration))

    if not _DYNAMIC_HELPERS:
        def freqMove(self, frequency: int, duration: int) -> int:
            """
            Makes the buzzer frequency change over a period of time.

            @param frequency : frequency to reach, in hertz. A frequency under 25Hz stops the buzzer.
            @param duration :  pulse duration in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.freqMove(frequency, duration))

    if not _DYNAMIC_HELPERS:
        def volumeMove(self, volume: int, duration: int) -> int:
            """
            Makes the buzzer volume change over a period of time, frequency  stays untouched.

            @param volume : volume to reach in %
            @param duration : change duration in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.volumeMove(volume, duration))

    if not _DYNAMIC_HELPERS:
        def playNotes(self, notes: str) -> int:
            """
            Immediately play a note sequence. Notes are provided as text words, separated by
            spaces. The pitch is specified using the usual letter from A to G. The duration is
            specified as the divisor of a whole note: 4 for a fourth, 8 for an eight note, etc.
            Some modifiers are supported: # and b to alter a note pitch,
            ' and , to move to the upper/lower octave, . to enlarge
            the note duration.

            @param notes : notes to be played, as a text string.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.playNotes(notes))

    # --- (end of YBuzzer implementation)

