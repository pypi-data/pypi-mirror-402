# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YPwmOutput
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
Yoctopuce library: Asyncio implementation of YPwmOutput
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YPwmOutput
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

# --- (YPwmOutput class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPwmOutputValueCallback = Union[Callable[['YPwmOutput', str], Any], None]
    except TypeError:
        YPwmOutputValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPwmOutput(YFunction):
    """
    The YPwmOutput class allows you to drive a pulse-width modulated output (PWM).
    You can configure the frequency as well as the duty cycle, and set up progressive
    transitions.

    """
    # --- (end of YPwmOutput class start)
    if not _IS_MICROPYTHON:
        # --- (YPwmOutput return codes)
        FREQUENCY_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PERIOD_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        DUTYCYCLE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PULSEDURATION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PWMTRANSITION_INVALID: Final[str] = YAPI.INVALID_STRING
        DUTYCYCLEATPOWERON_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ENABLED_FALSE: Final[int] = 0
        ENABLED_TRUE: Final[int] = 1
        ENABLED_INVALID: Final[int] = -1
        INVERTEDOUTPUT_FALSE: Final[int] = 0
        INVERTEDOUTPUT_TRUE: Final[int] = 1
        INVERTEDOUTPUT_INVALID: Final[int] = -1
        ENABLEDATPOWERON_FALSE: Final[int] = 0
        ENABLEDATPOWERON_TRUE: Final[int] = 1
        ENABLEDATPOWERON_INVALID: Final[int] = -1
        # --- (end of YPwmOutput return codes)

    # --- (YPwmOutput attributes declaration)
    _valueCallback: YPwmOutputValueCallback
    # --- (end of YPwmOutput attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'PwmOutput', func)
        # --- (YPwmOutput constructor)
        # --- (end of YPwmOutput constructor)

    # --- (YPwmOutput implementation)
    @classmethod
    def FindPwmOutput(cls, func: str) -> YPwmOutput:
        """
        Retrieves a PWM generator for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the PWM generator is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPwmOutput.isOnline() to test if the PWM generator is
        indeed online at a given time. In case of ambiguity when looking for
        a PWM generator by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the PWM generator, for instance
                YPWMTX01.pwmOutput1.

        @return a YPwmOutput object allowing you to drive the PWM generator.
        """
        return cls.FindPwmOutputInContext(YAPI, func)

    @classmethod
    def FindPwmOutputInContext(cls, yctx: YAPIContext, func: str) -> YPwmOutput:
        """
        Retrieves a PWM generator for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the PWM generator is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPwmOutput.isOnline() to test if the PWM generator is
        indeed online at a given time. In case of ambiguity when looking for
        a PWM generator by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the PWM generator, for instance
                YPWMTX01.pwmOutput1.

        @return a YPwmOutput object allowing you to drive the PWM generator.
        """
        obj: Union[YPwmOutput, None] = yctx._findInCache('PwmOutput', func)
        if obj:
            return obj
        return YPwmOutput(yctx, func)

    @classmethod
    def FirstPwmOutput(cls) -> Union[YPwmOutput, None]:
        """
        Starts the enumeration of PWM generators currently accessible.
        Use the method YPwmOutput.nextPwmOutput() to iterate on
        next PWM generators.

        @return a pointer to a YPwmOutput object, corresponding to
                the first PWM generator currently online, or a None pointer
                if there are none.
        """
        return cls.FirstPwmOutputInContext(YAPI)

    @classmethod
    def FirstPwmOutputInContext(cls, yctx: YAPIContext) -> Union[YPwmOutput, None]:
        """
        Starts the enumeration of PWM generators currently accessible.
        Use the method YPwmOutput.nextPwmOutput() to iterate on
        next PWM generators.

        @param yctx : a YAPI context.

        @return a pointer to a YPwmOutput object, corresponding to
                the first PWM generator currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('PwmOutput')
        if hwid:
            return cls.FindPwmOutputInContext(yctx, hwid2str(hwid))
        return None

    def nextPwmOutput(self) -> Union[YPwmOutput, None]:
        """
        Continues the enumeration of PWM generators started using yFirstPwmOutput().
        Caution: You can't make any assumption about the returned PWM generators order.
        If you want to find a specific a PWM generator, use PwmOutput.findPwmOutput()
        and a hardwareID or a logical name.

        @return a pointer to a YPwmOutput object, corresponding to
                a PWM generator currently online, or a None pointer
                if there are no more PWM generators to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('PwmOutput', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindPwmOutputInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_enabled(self) -> int:
        """
        Returns the state of the PWM generators.

        @return either YPwmOutput.ENABLED_FALSE or YPwmOutput.ENABLED_TRUE, according to the state of the PWM generators

        On failure, throws an exception or returns YPwmOutput.ENABLED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("enabled")
        if json_val is None:
            return YPwmOutput.ENABLED_INVALID
        return json_val

    async def set_enabled(self, newval: int) -> int:
        """
        Stops or starts the PWM.

        @param newval : either YPwmOutput.ENABLED_FALSE or YPwmOutput.ENABLED_TRUE

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("enabled", rest_val)

    async def set_frequency(self, newval: float) -> int:
        """
        Changes the PWM frequency. The duty cycle is kept unchanged thanks to an
        automatic pulse width change, in other words, the change will not be applied
        before the end of the current period. This can significantly affect reaction
        time at low frequencies. If you call the matching module saveToFlash()
        method, the frequency will be kept after a device power cycle.
        To stop the PWM signal, do not set the frequency to zero, use the set_enabled()
        method instead.

        @param newval : a floating point number corresponding to the PWM frequency

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("frequency", rest_val)

    async def get_frequency(self) -> float:
        """
        Returns the PWM frequency in Hz.

        @return a floating point number corresponding to the PWM frequency in Hz

        On failure, throws an exception or returns YPwmOutput.FREQUENCY_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("frequency")
        if json_val is None:
            return YPwmOutput.FREQUENCY_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_period(self, newval: float) -> int:
        """
        Changes the PWM period in milliseconds. Caution: in order to avoid  random truncation of
        the current pulse, the change will not be applied
        before the end of the current period. This can significantly affect reaction
        time at low frequencies. If you call the matching module saveToFlash()
        method, the frequency will be kept after a device power cycle.

        @param newval : a floating point number corresponding to the PWM period in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("period", rest_val)

    async def get_period(self) -> float:
        """
        Returns the PWM period in milliseconds.

        @return a floating point number corresponding to the PWM period in milliseconds

        On failure, throws an exception or returns YPwmOutput.PERIOD_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("period")
        if json_val is None:
            return YPwmOutput.PERIOD_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_dutyCycle(self, newval: float) -> int:
        """
        Changes the PWM duty cycle, in per cents.

        @param newval : a floating point number corresponding to the PWM duty cycle, in per cents

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("dutyCycle", rest_val)

    async def get_dutyCycle(self) -> float:
        """
        Returns the PWM duty cycle, in per cents.

        @return a floating point number corresponding to the PWM duty cycle, in per cents

        On failure, throws an exception or returns YPwmOutput.DUTYCYCLE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("dutyCycle")
        if json_val is None:
            return YPwmOutput.DUTYCYCLE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_pulseDuration(self, newval: float) -> int:
        """
        Changes the PWM pulse length, in milliseconds. A pulse length cannot be longer than period,
        otherwise it is truncated.

        @param newval : a floating point number corresponding to the PWM pulse length, in milliseconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("pulseDuration", rest_val)

    async def get_pulseDuration(self) -> float:
        """
        Returns the PWM pulse length in milliseconds, as a floating point number.

        @return a floating point number corresponding to the PWM pulse length in milliseconds, as a
        floating point number

        On failure, throws an exception or returns YPwmOutput.PULSEDURATION_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("pulseDuration")
        if json_val is None:
            return YPwmOutput.PULSEDURATION_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_pwmTransition(self) -> str:
        json_val: Union[str, None] = await self._fromCache("pwmTransition")
        if json_val is None:
            return YPwmOutput.PWMTRANSITION_INVALID
        return json_val

    async def set_pwmTransition(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("pwmTransition", rest_val)

    async def get_invertedOutput(self) -> int:
        """
        Returns true if the output signal is configured as inverted, and false otherwise.

        @return either YPwmOutput.INVERTEDOUTPUT_FALSE or YPwmOutput.INVERTEDOUTPUT_TRUE, according to true
        if the output signal is configured as inverted, and false otherwise

        On failure, throws an exception or returns YPwmOutput.INVERTEDOUTPUT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("invertedOutput")
        if json_val is None:
            return YPwmOutput.INVERTEDOUTPUT_INVALID
        return json_val

    async def set_invertedOutput(self, newval: int) -> int:
        """
        Changes the inversion mode of the output signal.
        Remember to call the matching module saveToFlash() method if you want
        the change to be kept after power cycle.

        @param newval : either YPwmOutput.INVERTEDOUTPUT_FALSE or YPwmOutput.INVERTEDOUTPUT_TRUE, according
        to the inversion mode of the output signal

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("invertedOutput", rest_val)

    async def get_enabledAtPowerOn(self) -> int:
        """
        Returns the state of the PWM at device power on.

        @return either YPwmOutput.ENABLEDATPOWERON_FALSE or YPwmOutput.ENABLEDATPOWERON_TRUE, according to
        the state of the PWM at device power on

        On failure, throws an exception or returns YPwmOutput.ENABLEDATPOWERON_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("enabledAtPowerOn")
        if json_val is None:
            return YPwmOutput.ENABLEDATPOWERON_INVALID
        return json_val

    async def set_enabledAtPowerOn(self, newval: int) -> int:
        """
        Changes the state of the PWM at device power on. Remember to call the matching module saveToFlash()
        method, otherwise this call will have no effect.

        @param newval : either YPwmOutput.ENABLEDATPOWERON_FALSE or YPwmOutput.ENABLEDATPOWERON_TRUE,
        according to the state of the PWM at device power on

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("enabledAtPowerOn", rest_val)

    async def set_dutyCycleAtPowerOn(self, newval: float) -> int:
        """
        Changes the PWM duty cycle at device power on. Remember to call the matching
        module saveToFlash() method, otherwise this call will have no effect.

        @param newval : a floating point number corresponding to the PWM duty cycle at device power on

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("dutyCycleAtPowerOn", rest_val)

    async def get_dutyCycleAtPowerOn(self) -> float:
        """
        Returns the PWM generators duty cycle at device power on as a floating point number between 0 and 100.

        @return a floating point number corresponding to the PWM generators duty cycle at device power on
        as a floating point number between 0 and 100

        On failure, throws an exception or returns YPwmOutput.DUTYCYCLEATPOWERON_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("dutyCycleAtPowerOn")
        if json_val is None:
            return YPwmOutput.DUTYCYCLEATPOWERON_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YPwmOutputValueCallback) -> int:
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

    async def pulseDurationMove(self, ms_target: float, ms_duration: int) -> int:
        """
        Performs a smooth transition of the pulse duration toward a given value.
        Any period, frequency, duty cycle or pulse width change will cancel any ongoing transition process.

        @param ms_target   : new pulse duration at the end of the transition
                (floating-point number, representing the pulse duration in milliseconds)
        @param ms_duration : total duration of the transition, in milliseconds

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        if ms_target < 0.0:
            ms_target = 0.0
        newval = "%dms:%d" % (int(round(ms_target*65536)), ms_duration)
        return await self.set_pwmTransition(newval)

    async def dutyCycleMove(self, target: float, ms_duration: int) -> int:
        """
        Performs a smooth change of the duty cycle toward a given value.
        Any period, frequency, duty cycle or pulse width change will cancel any ongoing transition process.

        @param target      : new duty cycle at the end of the transition
                (percentage, floating-point number between 0 and 100)
        @param ms_duration : total duration of the transition, in milliseconds

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        if target < 0.0:
            target = 0.0
        if target > 100.0:
            target = 100.0
        newval = "%d:%d" % (int(round(target*65536)), ms_duration)
        return await self.set_pwmTransition(newval)

    async def frequencyMove(self, target: float, ms_duration: int) -> int:
        """
        Performs a smooth frequency change toward a given value.
        Any period, frequency, duty cycle or pulse width change will cancel any ongoing transition process.

        @param target      : new frequency at the end of the transition (floating-point number)
        @param ms_duration : total duration of the transition, in milliseconds

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        if target < 0.001:
            target = 0.001
        newval = "%fHz:%d" % (target, ms_duration)
        return await self.set_pwmTransition(newval)

    async def phaseMove(self, target: float, ms_duration: int) -> int:
        """
        Performs a smooth transition toward a specified value of the phase shift between this channel
        and the other channel. The phase shift is executed by slightly changing the frequency
        temporarily during the specified duration. This function only makes sense when both channels
        are running, either at the same frequency, or at a multiple of the channel frequency.
        Any period, frequency, duty cycle or pulse width change will cancel any ongoing transition process.

        @param target      : phase shift at the end of the transition, in milliseconds (floating-point number)
        @param ms_duration : total duration of the transition, in milliseconds

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        newval = "%fps:%d" % (target, ms_duration)
        return await self.set_pwmTransition(newval)

    async def triggerPulsesByDuration(self, ms_target: float, n_pulses: int) -> int:
        """
        Trigger a given number of pulses of specified duration, at current frequency.
        At the end of the pulse train, revert to the original state of the PWM generator.

        @param ms_target : desired pulse duration
                (floating-point number, representing the pulse duration in milliseconds)
        @param n_pulses  : desired pulse count

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        if ms_target < 0.0:
            ms_target = 0.0
        newval = "%dms*%d" % (int(round(ms_target*65536)), n_pulses)
        return await self.set_pwmTransition(newval)

    async def triggerPulsesByDutyCycle(self, target: float, n_pulses: int) -> int:
        """
        Trigger a given number of pulses of specified duration, at current frequency.
        At the end of the pulse train, revert to the original state of the PWM generator.

        @param target   : desired duty cycle for the generated pulses
                (percentage, floating-point number between 0 and 100)
        @param n_pulses : desired pulse count

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        if target < 0.0:
            target = 0.0
        if target > 100.0:
            target = 100.0
        newval = "%d*%d" % (int(round(target*65536)), n_pulses)
        return await self.set_pwmTransition(newval)

    async def triggerPulsesByFrequency(self, target: float, n_pulses: int) -> int:
        """
        Trigger a given number of pulses at the specified frequency, using current duty cycle.
        At the end of the pulse train, revert to the original state of the PWM generator.

        @param target   : desired frequency for the generated pulses (floating-point number)
        @param n_pulses : desired pulse count

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        newval: str
        if target < 0.001:
            target = 0.001
        newval = "%fHz*%d" % (target, n_pulses)
        return await self.set_pwmTransition(newval)

    async def markForRepeat(self) -> int:
        return await self.set_pwmTransition(":")

    async def repeatFromMark(self) -> int:
        return await self.set_pwmTransition("R")

    # --- (end of YPwmOutput implementation)

