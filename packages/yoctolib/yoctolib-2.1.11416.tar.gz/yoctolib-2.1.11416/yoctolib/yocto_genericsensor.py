# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YGenericSensor
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
Yoctopuce library: High-level API for YGenericSensor
version: PATCH_WITH_VERSION
requires: yocto_genericsensor_aio
requires: yocto_api
provides: YGenericSensor
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

from .yocto_genericsensor_aio import YGenericSensor as YGenericSensor_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YGenericSensor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YGenericSensorValueCallback = Union[Callable[['YGenericSensor', str], Any], None]
        YGenericSensorTimedReportCallback = Union[Callable[['YGenericSensor', YMeasure], Any], None]
    except TypeError:
        YGenericSensorValueCallback = Union[Callable, Awaitable]
        YGenericSensorTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YGenericSensor(YSensor):
    """
    The YGenericSensor class allows you to read and configure Yoctopuce signal
    transducers. It inherits from YSensor class the core functions to read measurements,
    to register callback functions, to access the autonomous datalogger.
    This class adds the ability to configure the automatic conversion between the
    measured signal and the corresponding engineering unit.

    """
    _aio: YGenericSensor_aio
    # --- (end of YGenericSensor class start)
    if not _IS_MICROPYTHON:
        # --- (YGenericSensor return codes)
        SIGNALVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SIGNALUNIT_INVALID: Final[str] = YAPI.INVALID_STRING
        SIGNALRANGE_INVALID: Final[str] = YAPI.INVALID_STRING
        VALUERANGE_INVALID: Final[str] = YAPI.INVALID_STRING
        SIGNALBIAS_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SIGNALSAMPLING_HIGH_RATE: Final[int] = 0
        SIGNALSAMPLING_HIGH_RATE_FILTERED: Final[int] = 1
        SIGNALSAMPLING_LOW_NOISE: Final[int] = 2
        SIGNALSAMPLING_LOW_NOISE_FILTERED: Final[int] = 3
        SIGNALSAMPLING_HIGHEST_RATE: Final[int] = 4
        SIGNALSAMPLING_AC: Final[int] = 5
        SIGNALSAMPLING_INVALID: Final[int] = -1
        ENABLED_FALSE: Final[int] = 0
        ENABLED_TRUE: Final[int] = 1
        ENABLED_INVALID: Final[int] = -1
        # --- (end of YGenericSensor return codes)


    # --- (YGenericSensor implementation)

    @classmethod
    def FindGenericSensor(cls, func: str) -> YGenericSensor:
        """
        Retrieves a generic sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the generic sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGenericSensor.isOnline() to test if the generic sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a generic sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the generic sensor, for instance
                RX010V01.genericSensor1.

        @return a YGenericSensor object allowing you to drive the generic sensor.
        """
        return cls._proxy(cls, YGenericSensor_aio.FindGenericSensorInContext(YAPI_aio, func))

    @classmethod
    def FindGenericSensorInContext(cls, yctx: YAPIContext, func: str) -> YGenericSensor:
        """
        Retrieves a generic sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the generic sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGenericSensor.isOnline() to test if the generic sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a generic sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the generic sensor, for instance
                RX010V01.genericSensor1.

        @return a YGenericSensor object allowing you to drive the generic sensor.
        """
        return cls._proxy(cls, YGenericSensor_aio.FindGenericSensorInContext(yctx._aio, func))

    @classmethod
    def FirstGenericSensor(cls) -> Union[YGenericSensor, None]:
        """
        Starts the enumeration of generic sensors currently accessible.
        Use the method YGenericSensor.nextGenericSensor() to iterate on
        next generic sensors.

        @return a pointer to a YGenericSensor object, corresponding to
                the first generic sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YGenericSensor_aio.FirstGenericSensorInContext(YAPI_aio))

    @classmethod
    def FirstGenericSensorInContext(cls, yctx: YAPIContext) -> Union[YGenericSensor, None]:
        """
        Starts the enumeration of generic sensors currently accessible.
        Use the method YGenericSensor.nextGenericSensor() to iterate on
        next generic sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YGenericSensor object, corresponding to
                the first generic sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YGenericSensor_aio.FirstGenericSensorInContext(yctx._aio))

    def nextGenericSensor(self) -> Union[YGenericSensor, None]:
        """
        Continues the enumeration of generic sensors started using yFirstGenericSensor().
        Caution: You can't make any assumption about the returned generic sensors order.
        If you want to find a specific a generic sensor, use GenericSensor.findGenericSensor()
        and a hardwareID or a logical name.

        @return a pointer to a YGenericSensor object, corresponding to
                a generic sensor currently online, or a None pointer
                if there are no more generic sensors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextGenericSensor())

    if not _DYNAMIC_HELPERS:
        def set_unit(self, newval: str) -> int:
            """
            Changes the measuring unit for the measured value.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the measuring unit for the measured value

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_unit(newval))

    if not _DYNAMIC_HELPERS:
        def get_signalValue(self) -> float:
            """
            Returns the current value of the electrical signal measured by the sensor.

            @return a floating point number corresponding to the current value of the electrical signal
            measured by the sensor

            On failure, throws an exception or returns YGenericSensor.SIGNALVALUE_INVALID.
            """
            return self._run(self._aio.get_signalValue())

    if not _DYNAMIC_HELPERS:
        def get_signalUnit(self) -> str:
            """
            Returns the measuring unit of the electrical signal used by the sensor.

            @return a string corresponding to the measuring unit of the electrical signal used by the sensor

            On failure, throws an exception or returns YGenericSensor.SIGNALUNIT_INVALID.
            """
            return self._run(self._aio.get_signalUnit())

    if not _DYNAMIC_HELPERS:
        def get_signalRange(self) -> str:
            """
            Returns the input signal range used by the sensor.

            @return a string corresponding to the input signal range used by the sensor

            On failure, throws an exception or returns YGenericSensor.SIGNALRANGE_INVALID.
            """
            return self._run(self._aio.get_signalRange())

    if not _DYNAMIC_HELPERS:
        def set_signalRange(self, newval: str) -> int:
            """
            Changes the input signal range used by the sensor.
            When the input signal gets out of the planned range, the output value
            will be set to an arbitrary large value, whose sign indicates the direction
            of the range overrun.

            For a 4-20mA sensor, the default input signal range is "4...20".
            For a 0-10V sensor, the default input signal range is "0.1...10".
            For numeric communication interfaces, the default input signal range is
            "-999999.999...999999.999".

            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a string corresponding to the input signal range used by the sensor

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_signalRange(newval))

    if not _DYNAMIC_HELPERS:
        def get_valueRange(self) -> str:
            """
            Returns the physical value range measured by the sensor.

            @return a string corresponding to the physical value range measured by the sensor

            On failure, throws an exception or returns YGenericSensor.VALUERANGE_INVALID.
            """
            return self._run(self._aio.get_valueRange())

    if not _DYNAMIC_HELPERS:
        def set_valueRange(self, newval: str) -> int:
            """
            Changes the output value range, corresponding to the physical value measured
            by the sensor. The default output value range is the same as the input signal
            range (1:1 mapping), but you can change it so that the function automatically
            computes the physical value encoded by the input signal. Be aware that, as a
            side effect, the range modification may automatically modify the display resolution.

            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a string corresponding to the output value range, corresponding to the physical value measured
                    by the sensor

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_valueRange(newval))

    if not _DYNAMIC_HELPERS:
        def set_signalBias(self, newval: float) -> int:
            """
            Changes the electric signal bias for zero shift adjustment.
            If your electric signal reads positive when it should be zero, set up
            a positive signalBias of the same value to fix the zero shift.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the electric signal bias for zero shift adjustment

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_signalBias(newval))

    if not _DYNAMIC_HELPERS:
        def get_signalBias(self) -> float:
            """
            Returns the electric signal bias for zero shift adjustment.
            A positive bias means that the signal is over-reporting the measure,
            while a negative bias means that the signal is under-reporting the measure.

            @return a floating point number corresponding to the electric signal bias for zero shift adjustment

            On failure, throws an exception or returns YGenericSensor.SIGNALBIAS_INVALID.
            """
            return self._run(self._aio.get_signalBias())

    if not _DYNAMIC_HELPERS:
        def get_signalSampling(self) -> int:
            """
            Returns the electric signal sampling method to use.
            The HIGH_RATE method uses the highest sampling frequency, without any filtering.
            The HIGH_RATE_FILTERED method adds a windowed 7-sample median filter.
            The LOW_NOISE method uses a reduced acquisition frequency to reduce noise.
            The LOW_NOISE_FILTERED method combines a reduced frequency with the median filter
            to get measures as stable as possible when working on a noisy signal.

            @return a value among YGenericSensor.SIGNALSAMPLING_HIGH_RATE,
            YGenericSensor.SIGNALSAMPLING_HIGH_RATE_FILTERED, YGenericSensor.SIGNALSAMPLING_LOW_NOISE,
            YGenericSensor.SIGNALSAMPLING_LOW_NOISE_FILTERED, YGenericSensor.SIGNALSAMPLING_HIGHEST_RATE and
            YGenericSensor.SIGNALSAMPLING_AC corresponding to the electric signal sampling method to use

            On failure, throws an exception or returns YGenericSensor.SIGNALSAMPLING_INVALID.
            """
            return self._run(self._aio.get_signalSampling())

    if not _DYNAMIC_HELPERS:
        def set_signalSampling(self, newval: int) -> int:
            """
            Changes the electric signal sampling method to use.
            The HIGH_RATE method uses the highest sampling frequency, without any filtering.
            The HIGH_RATE_FILTERED method adds a windowed 7-sample median filter.
            The LOW_NOISE method uses a reduced acquisition frequency to reduce noise.
            The LOW_NOISE_FILTERED method combines a reduced frequency with the median filter
            to get measures as stable as possible when working on a noisy signal.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a value among YGenericSensor.SIGNALSAMPLING_HIGH_RATE,
            YGenericSensor.SIGNALSAMPLING_HIGH_RATE_FILTERED, YGenericSensor.SIGNALSAMPLING_LOW_NOISE,
            YGenericSensor.SIGNALSAMPLING_LOW_NOISE_FILTERED, YGenericSensor.SIGNALSAMPLING_HIGHEST_RATE and
            YGenericSensor.SIGNALSAMPLING_AC corresponding to the electric signal sampling method to use

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_signalSampling(newval))

    if not _DYNAMIC_HELPERS:
        def get_enabled(self) -> int:
            """
            Returns the activation state of this input.

            @return either YGenericSensor.ENABLED_FALSE or YGenericSensor.ENABLED_TRUE, according to the
            activation state of this input

            On failure, throws an exception or returns YGenericSensor.ENABLED_INVALID.
            """
            return self._run(self._aio.get_enabled())

    if not _DYNAMIC_HELPERS:
        def set_enabled(self, newval: int) -> int:
            """
            Changes the activation state of this input. When an input is disabled,
            its value is no more updated. On some devices, disabling an input can
            improve the refresh rate of the other active inputs.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : either YGenericSensor.ENABLED_FALSE or YGenericSensor.ENABLED_TRUE, according to
            the activation state of this input

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_enabled(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YGenericSensorValueCallback) -> int:
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

    if not _IS_MICROPYTHON:
        def registerTimedReportCallback(self, callback: YGenericSensorTimedReportCallback) -> int:
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
            return super().registerTimedReportCallback(callback)

    if not _DYNAMIC_HELPERS:
        def zeroAdjust(self) -> int:
            """
            Adjusts the signal bias so that the current signal value is need
            precisely as zero. Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.zeroAdjust())

    # --- (end of YGenericSensor implementation)

