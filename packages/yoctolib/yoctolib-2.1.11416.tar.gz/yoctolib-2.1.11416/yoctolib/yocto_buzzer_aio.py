# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YBuzzer
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
Yoctopuce library: Asyncio implementation of YBuzzer
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

import math
from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, xarray, xbytearray
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

    # --- (YBuzzer attributes declaration)
    _valueCallback: YBuzzerValueCallback
    # --- (end of YBuzzer attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Buzzer', func)
        # --- (YBuzzer constructor)
        # --- (end of YBuzzer constructor)

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
        return cls.FindBuzzerInContext(YAPI, func)

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
        obj: Union[YBuzzer, None] = yctx._findInCache('Buzzer', func)
        if obj:
            return obj
        return YBuzzer(yctx, func)

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
        return cls.FirstBuzzerInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('Buzzer')
        if hwid:
            return cls.FindBuzzerInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Buzzer', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindBuzzerInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_frequency(self, newval: float) -> int:
        """
        Changes the frequency of the signal sent to the buzzer. A zero value stops the buzzer.

        @param newval : a floating point number corresponding to the frequency of the signal sent to the buzzer

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("frequency", rest_val)

    async def get_frequency(self) -> float:
        """
        Returns the  frequency of the signal sent to the buzzer/speaker.

        @return a floating point number corresponding to the  frequency of the signal sent to the buzzer/speaker

        On failure, throws an exception or returns YBuzzer.FREQUENCY_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("frequency")
        if json_val is None:
            return YBuzzer.FREQUENCY_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_volume(self) -> int:
        """
        Returns the volume of the signal sent to the buzzer/speaker.

        @return an integer corresponding to the volume of the signal sent to the buzzer/speaker

        On failure, throws an exception or returns YBuzzer.VOLUME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("volume")
        if json_val is None:
            return YBuzzer.VOLUME_INVALID
        return json_val

    async def set_volume(self, newval: int) -> int:
        """
        Changes the volume of the signal sent to the buzzer/speaker. Remember to call the
        saveToFlash() method of the module if the modification must be kept.

        @param newval : an integer corresponding to the volume of the signal sent to the buzzer/speaker

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("volume", rest_val)

    async def get_playSeqSize(self) -> int:
        """
        Returns the current length of the playing sequence.

        @return an integer corresponding to the current length of the playing sequence

        On failure, throws an exception or returns YBuzzer.PLAYSEQSIZE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("playSeqSize")
        if json_val is None:
            return YBuzzer.PLAYSEQSIZE_INVALID
        return json_val

    async def get_playSeqMaxSize(self) -> int:
        """
        Returns the maximum length of the playing sequence.

        @return an integer corresponding to the maximum length of the playing sequence

        On failure, throws an exception or returns YBuzzer.PLAYSEQMAXSIZE_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("playSeqMaxSize")
        if json_val is None:
            return YBuzzer.PLAYSEQMAXSIZE_INVALID
        return json_val

    async def get_playSeqSignature(self) -> int:
        """
        Returns the playing sequence signature. As playing
        sequences cannot be read from the device, this can be used
        to detect if a specific playing sequence is already
        programmed.

        @return an integer corresponding to the playing sequence signature

        On failure, throws an exception or returns YBuzzer.PLAYSEQSIGNATURE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("playSeqSignature")
        if json_val is None:
            return YBuzzer.PLAYSEQSIGNATURE_INVALID
        return json_val

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YBuzzer.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YBuzzerValueCallback) -> int:
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

    async def sendCommand(self, command: str) -> int:
        return await self.set_command(command)

    async def addFreqMoveToPlaySeq(self, freq: int, msDelay: int) -> int:
        """
        Adds a new frequency transition to the playing sequence.

        @param freq    : desired frequency when the transition is completed, in Hz
        @param msDelay : duration of the frequency transition, in milliseconds.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("A%d,%d" % (freq, msDelay))

    async def addPulseToPlaySeq(self, freq: int, msDuration: int) -> int:
        """
        Adds a pulse to the playing sequence.

        @param freq : pulse frequency, in Hz
        @param msDuration : pulse duration, in milliseconds.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("B%d,%d" % (freq, msDuration))

    async def addVolMoveToPlaySeq(self, volume: int, msDuration: int) -> int:
        """
        Adds a new volume transition to the playing sequence. Frequency stays untouched:
        if frequency is at zero, the transition has no effect.

        @param volume    : desired volume when the transition is completed, as a percentage.
        @param msDuration : duration of the volume transition, in milliseconds.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("C%d,%d" % (volume, msDuration))

    async def addNotesToPlaySeq(self, notes: str) -> int:
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
        tempo: int
        prevPitch: int
        prevDuration: int
        prevFreq: int
        note: int
        num: int
        typ: int
        ascNotes: xarray
        notesLen: int
        i: int
        ch: int
        dNote: int
        pitch: int
        freq: int
        ms: int
        ms16: int
        rest: int
        tempo = 100
        prevPitch = 3
        prevDuration = 4
        prevFreq = 110
        note = -99
        num = 0
        typ = 3
        ascNotes = xbytearray(notes, 'latin-1')
        notesLen = len(ascNotes)
        i = 0
        while i < notesLen:
            ch = ascNotes[i]
            # A (note))
            if ch == 65:
                note = 0
            # B (note)
            if ch == 66:
                note = 2
            # C (note)
            if ch == 67:
                note = 3
            # D (note)
            if ch == 68:
                note = 5
            # E (note)
            if ch == 69:
                note = 7
            # F (note)
            if ch == 70:
                note = 8
            # G (note)
            if ch == 71:
                note = 10
            # '#' (sharp modifier)
            if ch == 35:
                note = note + 1
            # 'b' (flat modifier)
            if ch == 98:
                note = note - 1
            # ' (octave up)
            if ch == 39:
                prevPitch = prevPitch + 12
            # , (octave down)
            if ch == 44:
                prevPitch = prevPitch - 12
            # R (rest)
            if ch == 82:
                typ = 0
            # ! (staccato modifier)
            if ch == 33:
                typ = 1
            # ^ (short modifier)
            if ch == 94:
                typ = 2
            # _ (legato modifier)
            if ch == 95:
                typ = 4
            # - (glissando modifier)
            if ch == 45:
                typ = 5
            # % (tempo change)
            if (ch == 37) and (num > 0):
                tempo = num
                num = 0
            if (ch >= 48) and (ch <= 57):
                # 0-9 (number)
                num = (num * 10) + (ch - 48)
            if ch == 46:
                # . (duration modifier)
                num = (num * 2) // 3
            if ((ch == 32) or (i+1 == notesLen)) and ((note > -99) or (typ != 3)):
                if num == 0:
                    num = prevDuration
                else:
                    prevDuration = num
                ms = int(round(320000.0 / (tempo * num)))
                if typ == 0:
                    await self.addPulseToPlaySeq(0, ms)
                else:
                    dNote = note - (((prevPitch) % (12)))
                    if dNote > 6:
                        dNote = dNote - 12
                    if dNote <= -6:
                        dNote = dNote + 12
                    pitch = prevPitch + dNote
                    freq = int(round(440 * math.exp(pitch * 0.05776226504666)))
                    ms16 = (ms >> 4)
                    rest = 0
                    if typ == 3:
                        rest = 2 * ms16
                    if typ == 2:
                        rest = 8 * ms16
                    if typ == 1:
                        rest = 12 * ms16
                    if typ == 5:
                        await self.addPulseToPlaySeq(prevFreq, ms16)
                        await self.addFreqMoveToPlaySeq(freq, 8 * ms16)
                        await self.addPulseToPlaySeq(freq, ms - 9 * ms16)
                    else:
                        await self.addPulseToPlaySeq(freq, ms - rest)
                        if rest > 0:
                            await self.addPulseToPlaySeq(0, rest)
                    prevFreq = freq
                    prevPitch = pitch
                note = -99
                num = 0
                typ = 3
            i = i + 1
        return YAPI.SUCCESS

    async def startPlaySeq(self) -> int:
        """
        Starts the preprogrammed playing sequence. The sequence
        runs in loop until it is stopped by stopPlaySeq or an explicit
        change. To play the sequence only once, use oncePlaySeq().

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("S")

    async def stopPlaySeq(self) -> int:
        """
        Stops the preprogrammed playing sequence and sets the frequency to zero.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("X")

    async def resetPlaySeq(self) -> int:
        """
        Resets the preprogrammed playing sequence and sets the frequency to zero.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("Z")

    async def oncePlaySeq(self) -> int:
        """
        Starts the preprogrammed playing sequence and run it once only.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("s")

    async def savePlaySeq(self) -> int:
        """
        Saves the preprogrammed playing sequence to flash memory.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("W")

    async def reloadPlaySeq(self) -> int:
        """
        Reloads the preprogrammed playing sequence from the flash memory.

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("R")

    async def pulse(self, frequency: int, duration: int) -> int:
        """
        Activates the buzzer for a short duration.

        @param frequency : pulse frequency, in hertz
        @param duration : pulse duration in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("P%d,%d" % (frequency, duration))

    async def freqMove(self, frequency: int, duration: int) -> int:
        """
        Makes the buzzer frequency change over a period of time.

        @param frequency : frequency to reach, in hertz. A frequency under 25Hz stops the buzzer.
        @param duration :  pulse duration in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("F%d,%d" % (frequency, duration))

    async def volumeMove(self, volume: int, duration: int) -> int:
        """
        Makes the buzzer volume change over a period of time, frequency  stays untouched.

        @param volume : volume to reach in %
        @param duration : change duration in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("V%d,%d" % (volume, duration))

    async def playNotes(self, notes: str) -> int:
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
        await self.resetPlaySeq()
        await self.addNotesToPlaySeq(notes)
        return await self.oncePlaySeq()

    # --- (end of YBuzzer implementation)

