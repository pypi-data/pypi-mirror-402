# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YPwmInput
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
Yoctopuce library: Asyncio implementation of YPwmInput
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YPwmInput
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YSensor, YMeasure
)

# --- (YPwmInput class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPwmInputValueCallback = Union[Callable[['YPwmInput', str], Any], None]
        YPwmInputTimedReportCallback = Union[Callable[['YPwmInput', YMeasure], Any], None]
    except TypeError:
        YPwmInputValueCallback = Union[Callable, Awaitable]
        YPwmInputTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPwmInput(YSensor):
    """
    The YPwmInput class allows you to read and configure Yoctopuce PWM inputs.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the ability to configure the signal parameter used to transmit
    information: the duty cycle, the frequency or the pulse width.

    """
    # --- (end of YPwmInput class start)
    if not _IS_MICROPYTHON:
        # --- (YPwmInput return codes)
        DUTYCYCLE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PULSEDURATION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        FREQUENCY_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PERIOD_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        PULSECOUNTER_INVALID: Final[int] = YAPI.INVALID_LONG
        PULSETIMER_INVALID: Final[int] = YAPI.INVALID_LONG
        DEBOUNCEPERIOD_INVALID: Final[int] = YAPI.INVALID_UINT
        MINFREQUENCY_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        BANDWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        EDGESPERPERIOD_INVALID: Final[int] = YAPI.INVALID_UINT
        PWMREPORTMODE_PWM_DUTYCYCLE: Final[int] = 0
        PWMREPORTMODE_PWM_FREQUENCY: Final[int] = 1
        PWMREPORTMODE_PWM_PULSEDURATION: Final[int] = 2
        PWMREPORTMODE_PWM_EDGECOUNT: Final[int] = 3
        PWMREPORTMODE_PWM_PULSECOUNT: Final[int] = 4
        PWMREPORTMODE_PWM_CPS: Final[int] = 5
        PWMREPORTMODE_PWM_CPM: Final[int] = 6
        PWMREPORTMODE_PWM_STATE: Final[int] = 7
        PWMREPORTMODE_PWM_FREQ_CPS: Final[int] = 8
        PWMREPORTMODE_PWM_FREQ_CPM: Final[int] = 9
        PWMREPORTMODE_PWM_PERIODCOUNT: Final[int] = 10
        PWMREPORTMODE_INVALID: Final[int] = -1
        # --- (end of YPwmInput return codes)

    # --- (YPwmInput attributes declaration)
    _valueCallback: YPwmInputValueCallback
    _timedReportCallback: YPwmInputTimedReportCallback
    # --- (end of YPwmInput attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'PwmInput', func)
        # --- (YPwmInput constructor)
        # --- (end of YPwmInput constructor)

    # --- (YPwmInput implementation)
    @classmethod
    def FindPwmInput(cls, func: str) -> YPwmInput:
        """
        Retrieves a PWM input for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the PWM input is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPwmInput.isOnline() to test if the PWM input is
        indeed online at a given time. In case of ambiguity when looking for
        a PWM input by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the PWM input, for instance
                YPWMRX01.pwmInput1.

        @return a YPwmInput object allowing you to drive the PWM input.
        """
        return cls.FindPwmInputInContext(YAPI, func)

    @classmethod
    def FindPwmInputInContext(cls, yctx: YAPIContext, func: str) -> YPwmInput:
        """
        Retrieves a PWM input for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the PWM input is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPwmInput.isOnline() to test if the PWM input is
        indeed online at a given time. In case of ambiguity when looking for
        a PWM input by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the PWM input, for instance
                YPWMRX01.pwmInput1.

        @return a YPwmInput object allowing you to drive the PWM input.
        """
        obj: Union[YPwmInput, None] = yctx._findInCache('PwmInput', func)
        if obj:
            return obj
        return YPwmInput(yctx, func)

    @classmethod
    def FirstPwmInput(cls) -> Union[YPwmInput, None]:
        """
        Starts the enumeration of PWM inputs currently accessible.
        Use the method YPwmInput.nextPwmInput() to iterate on
        next PWM inputs.

        @return a pointer to a YPwmInput object, corresponding to
                the first PWM input currently online, or a None pointer
                if there are none.
        """
        return cls.FirstPwmInputInContext(YAPI)

    @classmethod
    def FirstPwmInputInContext(cls, yctx: YAPIContext) -> Union[YPwmInput, None]:
        """
        Starts the enumeration of PWM inputs currently accessible.
        Use the method YPwmInput.nextPwmInput() to iterate on
        next PWM inputs.

        @param yctx : a YAPI context.

        @return a pointer to a YPwmInput object, corresponding to
                the first PWM input currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('PwmInput')
        if hwid:
            return cls.FindPwmInputInContext(yctx, hwid2str(hwid))
        return None

    def nextPwmInput(self) -> Union[YPwmInput, None]:
        """
        Continues the enumeration of PWM inputs started using yFirstPwmInput().
        Caution: You can't make any assumption about the returned PWM inputs order.
        If you want to find a specific a PWM input, use PwmInput.findPwmInput()
        and a hardwareID or a logical name.

        @return a pointer to a YPwmInput object, corresponding to
                a PWM input currently online, or a None pointer
                if there are no more PWM inputs to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('PwmInput', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindPwmInputInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_unit(self, newval: str) -> int:
        """
        Changes the measuring unit for the measured quantity. That unit
        is just a string which is automatically initialized each time
        the measurement mode is changed. But is can be set to an
        arbitrary value.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a string corresponding to the measuring unit for the measured quantity

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("unit", rest_val)

    async def get_dutyCycle(self) -> float:
        """
        Returns the PWM duty cycle, in per cents.

        @return a floating point number corresponding to the PWM duty cycle, in per cents

        On failure, throws an exception or returns YPwmInput.DUTYCYCLE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("dutyCycle")
        if json_val is None:
            return YPwmInput.DUTYCYCLE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_pulseDuration(self) -> float:
        """
        Returns the PWM pulse length in milliseconds, as a floating point number.

        @return a floating point number corresponding to the PWM pulse length in milliseconds, as a
        floating point number

        On failure, throws an exception or returns YPwmInput.PULSEDURATION_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("pulseDuration")
        if json_val is None:
            return YPwmInput.PULSEDURATION_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_frequency(self) -> float:
        """
        Returns the PWM frequency in Hz.

        @return a floating point number corresponding to the PWM frequency in Hz

        On failure, throws an exception or returns YPwmInput.FREQUENCY_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("frequency")
        if json_val is None:
            return YPwmInput.FREQUENCY_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_period(self) -> float:
        """
        Returns the PWM period in milliseconds.

        @return a floating point number corresponding to the PWM period in milliseconds

        On failure, throws an exception or returns YPwmInput.PERIOD_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("period")
        if json_val is None:
            return YPwmInput.PERIOD_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_pulseCounter(self) -> int:
        """
        Returns the pulse counter value. Actually that
        counter is incremented twice per period. That counter is
        limited  to 1 billion.

        @return an integer corresponding to the pulse counter value

        On failure, throws an exception or returns YPwmInput.PULSECOUNTER_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pulseCounter")
        if json_val is None:
            return YPwmInput.PULSECOUNTER_INVALID
        return json_val

    async def set_pulseCounter(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("pulseCounter", rest_val)

    async def get_pulseTimer(self) -> int:
        """
        Returns the timer of the pulses counter (ms).

        @return an integer corresponding to the timer of the pulses counter (ms)

        On failure, throws an exception or returns YPwmInput.PULSETIMER_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pulseTimer")
        if json_val is None:
            return YPwmInput.PULSETIMER_INVALID
        return json_val

    async def get_pwmReportMode(self) -> int:
        """
        Returns the parameter (frequency/duty cycle, pulse width, edges count) returned by the
        get_currentValue function and callbacks. Attention

        @return a value among YPwmInput.PWMREPORTMODE_PWM_DUTYCYCLE, YPwmInput.PWMREPORTMODE_PWM_FREQUENCY,
        YPwmInput.PWMREPORTMODE_PWM_PULSEDURATION, YPwmInput.PWMREPORTMODE_PWM_EDGECOUNT,
        YPwmInput.PWMREPORTMODE_PWM_PULSECOUNT, YPwmInput.PWMREPORTMODE_PWM_CPS,
        YPwmInput.PWMREPORTMODE_PWM_CPM, YPwmInput.PWMREPORTMODE_PWM_STATE,
        YPwmInput.PWMREPORTMODE_PWM_FREQ_CPS, YPwmInput.PWMREPORTMODE_PWM_FREQ_CPM and
        YPwmInput.PWMREPORTMODE_PWM_PERIODCOUNT corresponding to the parameter (frequency/duty cycle, pulse
        width, edges count) returned by the get_currentValue function and callbacks

        On failure, throws an exception or returns YPwmInput.PWMREPORTMODE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pwmReportMode")
        if json_val is None:
            return YPwmInput.PWMREPORTMODE_INVALID
        return json_val

    async def set_pwmReportMode(self, newval: int) -> int:
        """
        Changes the  parameter  type (frequency/duty cycle, pulse width, or edge count) returned by the
        get_currentValue function and callbacks.
        The edge count value is limited to the 6 lowest digits. For values greater than one million, use
        get_pulseCounter().
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a value among YPwmInput.PWMREPORTMODE_PWM_DUTYCYCLE,
        YPwmInput.PWMREPORTMODE_PWM_FREQUENCY, YPwmInput.PWMREPORTMODE_PWM_PULSEDURATION,
        YPwmInput.PWMREPORTMODE_PWM_EDGECOUNT, YPwmInput.PWMREPORTMODE_PWM_PULSECOUNT,
        YPwmInput.PWMREPORTMODE_PWM_CPS, YPwmInput.PWMREPORTMODE_PWM_CPM,
        YPwmInput.PWMREPORTMODE_PWM_STATE, YPwmInput.PWMREPORTMODE_PWM_FREQ_CPS,
        YPwmInput.PWMREPORTMODE_PWM_FREQ_CPM and YPwmInput.PWMREPORTMODE_PWM_PERIODCOUNT corresponding to
        the  parameter  type (frequency/duty cycle, pulse width, or edge count) returned by the
        get_currentValue function and callbacks

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("pwmReportMode", rest_val)

    async def get_debouncePeriod(self) -> int:
        """
        Returns the shortest expected pulse duration, in ms. Any shorter pulse will be automatically ignored (debounce).

        @return an integer corresponding to the shortest expected pulse duration, in ms

        On failure, throws an exception or returns YPwmInput.DEBOUNCEPERIOD_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("debouncePeriod")
        if json_val is None:
            return YPwmInput.DEBOUNCEPERIOD_INVALID
        return json_val

    async def set_debouncePeriod(self, newval: int) -> int:
        """
        Changes the shortest expected pulse duration, in ms. Any shorter pulse will be automatically ignored (debounce).
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : an integer corresponding to the shortest expected pulse duration, in ms

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("debouncePeriod", rest_val)

    async def set_minFrequency(self, newval: float) -> int:
        """
        Changes the minimum detected frequency, in Hz. Slower signals will be consider as zero frequency.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a floating point number corresponding to the minimum detected frequency, in Hz

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("minFrequency", rest_val)

    async def get_minFrequency(self) -> float:
        """
        Returns the minimum detected frequency, in Hz. Slower signals will be consider as zero frequency.

        @return a floating point number corresponding to the minimum detected frequency, in Hz

        On failure, throws an exception or returns YPwmInput.MINFREQUENCY_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("minFrequency")
        if json_val is None:
            return YPwmInput.MINFREQUENCY_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_bandwidth(self) -> int:
        """
        Returns the input signal sampling rate, in kHz.

        @return an integer corresponding to the input signal sampling rate, in kHz

        On failure, throws an exception or returns YPwmInput.BANDWIDTH_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("bandwidth")
        if json_val is None:
            return YPwmInput.BANDWIDTH_INVALID
        return json_val

    async def set_bandwidth(self, newval: int) -> int:
        """
        Changes the input signal sampling rate, measured in kHz.
        A lower sampling frequency can be used to hide hide-frequency bounce effects,
        for instance on electromechanical contacts, but limits the measure resolution.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the input signal sampling rate, measured in kHz

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("bandwidth", rest_val)

    async def get_edgesPerPeriod(self) -> int:
        """
        Returns the number of edges detected per preiod. For a clean PWM signal, this should be exactly two,
        but in cas the signal is created by a mechanical contact with bounces, it can get higher.

        @return an integer corresponding to the number of edges detected per preiod

        On failure, throws an exception or returns YPwmInput.EDGESPERPERIOD_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("edgesPerPeriod")
        if json_val is None:
            return YPwmInput.EDGESPERPERIOD_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YPwmInputValueCallback) -> int:
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

    if not _IS_MICROPYTHON:
        async def registerTimedReportCallback(self, callback: YPwmInputTimedReportCallback) -> int:
            """
            Registers the callback function that is invoked on every periodic timed notification.
            The callback is invoked only during the execution of ySleep or yHandleEvents.
            This provides control over the time when the callback is triggered. For good responsiveness, remember to call
            one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

            @param callback : the callback function to call, or a None pointer. The callback function should take two
                    arguments: the function object of which the value has changed, and an YMeasure object describing
                    the new advertised value.
            @noreturn
            """
            return await super().registerTimedReportCallback(callback)

    async def resetPeriodDetection(self) -> int:
        """
        Resets the periodicity detection algorithm.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_bandwidth(await self.get_bandwidth())

    async def resetCounter(self) -> int:
        """
        Resets the pulse counter value as well as its timer.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_pulseCounter(0)

    # --- (end of YPwmInput implementation)

