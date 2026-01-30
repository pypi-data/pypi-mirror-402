# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YWeighScale
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
Yoctopuce library: High-level API for YWeighScale
version: PATCH_WITH_VERSION
requires: yocto_weighscale_aio
requires: yocto_api
provides: YWeighScale
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

from .yocto_weighscale_aio import YWeighScale as YWeighScale_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YWeighScale class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YWeighScaleValueCallback = Union[Callable[['YWeighScale', str], Any], None]
        YWeighScaleTimedReportCallback = Union[Callable[['YWeighScale', YMeasure], Any], None]
    except TypeError:
        YWeighScaleValueCallback = Union[Callable, Awaitable]
        YWeighScaleTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YWeighScale(YSensor):
    """
    The YWeighScale class provides a weight measurement from a ratiometric sensor.
    It can be used to control the bridge excitation parameters, in order to avoid
    measure shifts caused by temperature variation in the electronics, and can also
    automatically apply an additional correction factor based on temperature to
    compensate for offsets in the load cell itself.

    """
    _aio: YWeighScale_aio
    # --- (end of YWeighScale class start)
    if not _IS_MICROPYTHON:
        # --- (YWeighScale return codes)
        TEMPAVGADAPTRATIO_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        TEMPCHGADAPTRATIO_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        COMPTEMPAVG_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        COMPTEMPCHG_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        COMPENSATION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ZEROTRACKING_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        EXCITATION_OFF: Final[int] = 0
        EXCITATION_DC: Final[int] = 1
        EXCITATION_AC: Final[int] = 2
        EXCITATION_INVALID: Final[int] = -1
        # --- (end of YWeighScale return codes)


    # --- (YWeighScale implementation)

    @classmethod
    def FindWeighScale(cls, func: str) -> YWeighScale:
        """
        Retrieves a weighing scale sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the weighing scale sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWeighScale.isOnline() to test if the weighing scale sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a weighing scale sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the weighing scale sensor, for instance
                YWBRIDG1.weighScale1.

        @return a YWeighScale object allowing you to drive the weighing scale sensor.
        """
        return cls._proxy(cls, YWeighScale_aio.FindWeighScaleInContext(YAPI_aio, func))

    @classmethod
    def FindWeighScaleInContext(cls, yctx: YAPIContext, func: str) -> YWeighScale:
        """
        Retrieves a weighing scale sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the weighing scale sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWeighScale.isOnline() to test if the weighing scale sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a weighing scale sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the weighing scale sensor, for instance
                YWBRIDG1.weighScale1.

        @return a YWeighScale object allowing you to drive the weighing scale sensor.
        """
        return cls._proxy(cls, YWeighScale_aio.FindWeighScaleInContext(yctx._aio, func))

    @classmethod
    def FirstWeighScale(cls) -> Union[YWeighScale, None]:
        """
        Starts the enumeration of weighing scale sensors currently accessible.
        Use the method YWeighScale.nextWeighScale() to iterate on
        next weighing scale sensors.

        @return a pointer to a YWeighScale object, corresponding to
                the first weighing scale sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YWeighScale_aio.FirstWeighScaleInContext(YAPI_aio))

    @classmethod
    def FirstWeighScaleInContext(cls, yctx: YAPIContext) -> Union[YWeighScale, None]:
        """
        Starts the enumeration of weighing scale sensors currently accessible.
        Use the method YWeighScale.nextWeighScale() to iterate on
        next weighing scale sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YWeighScale object, corresponding to
                the first weighing scale sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YWeighScale_aio.FirstWeighScaleInContext(yctx._aio))

    def nextWeighScale(self) -> Union[YWeighScale, None]:
        """
        Continues the enumeration of weighing scale sensors started using yFirstWeighScale().
        Caution: You can't make any assumption about the returned weighing scale sensors order.
        If you want to find a specific a weighing scale sensor, use WeighScale.findWeighScale()
        and a hardwareID or a logical name.

        @return a pointer to a YWeighScale object, corresponding to
                a weighing scale sensor currently online, or a None pointer
                if there are no more weighing scale sensors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextWeighScale())

    if not _DYNAMIC_HELPERS:
        def set_unit(self, newval: str) -> int:
            """
            Changes the measuring unit for the weight.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the measuring unit for the weight

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_unit(newval))

    if not _DYNAMIC_HELPERS:
        def get_excitation(self) -> int:
            """
            Returns the current load cell bridge excitation method.

            @return a value among YWeighScale.EXCITATION_OFF, YWeighScale.EXCITATION_DC and
            YWeighScale.EXCITATION_AC corresponding to the current load cell bridge excitation method

            On failure, throws an exception or returns YWeighScale.EXCITATION_INVALID.
            """
            return self._run(self._aio.get_excitation())

    if not _DYNAMIC_HELPERS:
        def set_excitation(self, newval: int) -> int:
            """
            Changes the current load cell bridge excitation method.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a value among YWeighScale.EXCITATION_OFF, YWeighScale.EXCITATION_DC and
            YWeighScale.EXCITATION_AC corresponding to the current load cell bridge excitation method

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_excitation(newval))

    if not _DYNAMIC_HELPERS:
        def set_tempAvgAdaptRatio(self, newval: float) -> int:
            """
            Changes the averaged temperature update rate, in per mille.
            The purpose of this adaptation ratio is to model the thermal inertia of the load cell.
            The averaged temperature is updated every 10 seconds, by applying this adaptation rate
            to the difference between the measures ambient temperature and the current compensation
            temperature. The standard rate is 0.2 per mille, and the maximal rate is 65 per mille.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a floating point number corresponding to the averaged temperature update rate, in per mille

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_tempAvgAdaptRatio(newval))

    if not _DYNAMIC_HELPERS:
        def get_tempAvgAdaptRatio(self) -> float:
            """
            Returns the averaged temperature update rate, in per mille.
            The purpose of this adaptation ratio is to model the thermal inertia of the load cell.
            The averaged temperature is updated every 10 seconds, by applying this adaptation rate
            to the difference between the measures ambient temperature and the current compensation
            temperature. The standard rate is 0.2 per mille, and the maximal rate is 65 per mille.

            @return a floating point number corresponding to the averaged temperature update rate, in per mille

            On failure, throws an exception or returns YWeighScale.TEMPAVGADAPTRATIO_INVALID.
            """
            return self._run(self._aio.get_tempAvgAdaptRatio())

    if not _DYNAMIC_HELPERS:
        def set_tempChgAdaptRatio(self, newval: float) -> int:
            """
            Changes the temperature change update rate, in per mille.
            The temperature change is updated every 10 seconds, by applying this adaptation rate
            to the difference between the measures ambient temperature and the current temperature used for
            change compensation. The standard rate is 0.6 per mille, and the maximal rate is 65 per mille.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a floating point number corresponding to the temperature change update rate, in per mille

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_tempChgAdaptRatio(newval))

    if not _DYNAMIC_HELPERS:
        def get_tempChgAdaptRatio(self) -> float:
            """
            Returns the temperature change update rate, in per mille.
            The temperature change is updated every 10 seconds, by applying this adaptation rate
            to the difference between the measures ambient temperature and the current temperature used for
            change compensation. The standard rate is 0.6 per mille, and the maximal rate is 65 per mille.

            @return a floating point number corresponding to the temperature change update rate, in per mille

            On failure, throws an exception or returns YWeighScale.TEMPCHGADAPTRATIO_INVALID.
            """
            return self._run(self._aio.get_tempChgAdaptRatio())

    if not _DYNAMIC_HELPERS:
        def get_compTempAvg(self) -> float:
            """
            Returns the current averaged temperature, used for thermal compensation.

            @return a floating point number corresponding to the current averaged temperature, used for thermal compensation

            On failure, throws an exception or returns YWeighScale.COMPTEMPAVG_INVALID.
            """
            return self._run(self._aio.get_compTempAvg())

    if not _DYNAMIC_HELPERS:
        def get_compTempChg(self) -> float:
            """
            Returns the current temperature variation, used for thermal compensation.

            @return a floating point number corresponding to the current temperature variation, used for
            thermal compensation

            On failure, throws an exception or returns YWeighScale.COMPTEMPCHG_INVALID.
            """
            return self._run(self._aio.get_compTempChg())

    if not _DYNAMIC_HELPERS:
        def get_compensation(self) -> float:
            """
            Returns the current current thermal compensation value.

            @return a floating point number corresponding to the current current thermal compensation value

            On failure, throws an exception or returns YWeighScale.COMPENSATION_INVALID.
            """
            return self._run(self._aio.get_compensation())

    if not _DYNAMIC_HELPERS:
        def set_zeroTracking(self, newval: float) -> int:
            """
            Changes the zero tracking threshold value. When this threshold is larger than
            zero, any measure under the threshold will automatically be ignored and the
            zero compensation will be updated.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a floating point number corresponding to the zero tracking threshold value

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_zeroTracking(newval))

    if not _DYNAMIC_HELPERS:
        def get_zeroTracking(self) -> float:
            """
            Returns the zero tracking threshold value. When this threshold is larger than
            zero, any measure under the threshold will automatically be ignored and the
            zero compensation will be updated.

            @return a floating point number corresponding to the zero tracking threshold value

            On failure, throws an exception or returns YWeighScale.ZEROTRACKING_INVALID.
            """
            return self._run(self._aio.get_zeroTracking())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YWeighScaleValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YWeighScaleTimedReportCallback) -> int:
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
        def tare(self) -> int:
            """
            Adapts the load cell signal bias (stored in the corresponding genericSensor)
            so that the current signal corresponds to a zero weight. Remember to call the
            saveToFlash() method of the module if the modification must be kept.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.tare())

    if not _DYNAMIC_HELPERS:
        def setupSpan(self, currWeight: float, maxWeight: float) -> int:
            """
            Configures the load cell span parameters (stored in the corresponding genericSensor)
            so that the current signal corresponds to the specified reference weight.

            @param currWeight : reference weight presently on the load cell.
            @param maxWeight : maximum weight to be expected on the load cell.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.setupSpan(currWeight, maxWeight))

    if not _DYNAMIC_HELPERS:
        def set_offsetAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Records a weight offset thermal compensation table, in order to automatically correct the
            measured weight based on the averaged compensation temperature.
            The weight correction will be applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, corresponding to all averaged
                    temperatures for which an offset correction is specified.
            @param compValues : array of floating point numbers, corresponding to the offset correction
                    to apply for each of the temperature included in the first
                    argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_offsetAvgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def loadOffsetAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Retrieves the weight offset thermal compensation table previously configured using the
            set_offsetAvgCompensationTable function.
            The weight correction is applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, that is filled by the function
                    with all averaged temperatures for which an offset correction is specified.
            @param compValues : array of floating point numbers, that is filled by the function
                    with the offset correction applied for each of the temperature
                    included in the first argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadOffsetAvgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def set_offsetChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Records a weight offset thermal compensation table, in order to automatically correct the
            measured weight based on the variation of temperature.
            The weight correction will be applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, corresponding to temperature
                    variations for which an offset correction is specified.
            @param compValues : array of floating point numbers, corresponding to the offset correction
                    to apply for each of the temperature variation included in the first
                    argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_offsetChgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def loadOffsetChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Retrieves the weight offset thermal compensation table previously configured using the
            set_offsetChgCompensationTable function.
            The weight correction is applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, that is filled by the function
                    with all temperature variations for which an offset correction is specified.
            @param compValues : array of floating point numbers, that is filled by the function
                    with the offset correction applied for each of the temperature
                    variation included in the first argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadOffsetChgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def set_spanAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Records a weight span thermal compensation table, in order to automatically correct the
            measured weight based on the compensation temperature.
            The weight correction will be applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, corresponding to all averaged
                    temperatures for which a span correction is specified.
            @param compValues : array of floating point numbers, corresponding to the span correction
                    (in percents) to apply for each of the temperature included in the first
                    argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_spanAvgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def loadSpanAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Retrieves the weight span thermal compensation table previously configured using the
            set_spanAvgCompensationTable function.
            The weight correction is applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, that is filled by the function
                    with all averaged temperatures for which an span correction is specified.
            @param compValues : array of floating point numbers, that is filled by the function
                    with the span correction applied for each of the temperature
                    included in the first argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadSpanAvgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def set_spanChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Records a weight span thermal compensation table, in order to automatically correct the
            measured weight based on the variation of temperature.
            The weight correction will be applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, corresponding to all variations of
                    temperatures for which a span correction is specified.
            @param compValues : array of floating point numbers, corresponding to the span correction
                    (in percents) to apply for each of the temperature variation included
                    in the first argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_spanChgCompensationTable(tempValues, compValues))

    if not _DYNAMIC_HELPERS:
        def loadSpanChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
            """
            Retrieves the weight span thermal compensation table previously configured using the
            set_spanChgCompensationTable function.
            The weight correction is applied by linear interpolation between specified points.

            @param tempValues : array of floating point numbers, that is filled by the function
                    with all variation of temperature for which an span correction is specified.
            @param compValues : array of floating point numbers, that is filled by the function
                    with the span correction applied for each of variation of temperature
                    included in the first argument, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadSpanChgCompensationTable(tempValues, compValues))

    # --- (end of YWeighScale implementation)

