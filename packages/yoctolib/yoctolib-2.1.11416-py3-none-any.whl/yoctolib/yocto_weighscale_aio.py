# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YWeighScale
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
Yoctopuce library: Asyncio implementation of YWeighScale
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YSensor, YMeasure, xarray
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

    # --- (YWeighScale attributes declaration)
    _valueCallback: YWeighScaleValueCallback
    _timedReportCallback: YWeighScaleTimedReportCallback
    # --- (end of YWeighScale attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'WeighScale', func)
        # --- (YWeighScale constructor)
        # --- (end of YWeighScale constructor)

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
        return cls.FindWeighScaleInContext(YAPI, func)

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
        obj: Union[YWeighScale, None] = yctx._findInCache('WeighScale', func)
        if obj:
            return obj
        return YWeighScale(yctx, func)

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
        return cls.FirstWeighScaleInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('WeighScale')
        if hwid:
            return cls.FindWeighScaleInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('WeighScale', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindWeighScaleInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_unit(self, newval: str) -> int:
        """
        Changes the measuring unit for the weight.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the measuring unit for the weight

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("unit", rest_val)

    async def get_excitation(self) -> int:
        """
        Returns the current load cell bridge excitation method.

        @return a value among YWeighScale.EXCITATION_OFF, YWeighScale.EXCITATION_DC and
        YWeighScale.EXCITATION_AC corresponding to the current load cell bridge excitation method

        On failure, throws an exception or returns YWeighScale.EXCITATION_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("excitation")
        if json_val is None:
            return YWeighScale.EXCITATION_INVALID
        return json_val

    async def set_excitation(self, newval: int) -> int:
        """
        Changes the current load cell bridge excitation method.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YWeighScale.EXCITATION_OFF, YWeighScale.EXCITATION_DC and
        YWeighScale.EXCITATION_AC corresponding to the current load cell bridge excitation method

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("excitation", rest_val)

    async def set_tempAvgAdaptRatio(self, newval: float) -> int:
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
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("tempAvgAdaptRatio", rest_val)

    async def get_tempAvgAdaptRatio(self) -> float:
        """
        Returns the averaged temperature update rate, in per mille.
        The purpose of this adaptation ratio is to model the thermal inertia of the load cell.
        The averaged temperature is updated every 10 seconds, by applying this adaptation rate
        to the difference between the measures ambient temperature and the current compensation
        temperature. The standard rate is 0.2 per mille, and the maximal rate is 65 per mille.

        @return a floating point number corresponding to the averaged temperature update rate, in per mille

        On failure, throws an exception or returns YWeighScale.TEMPAVGADAPTRATIO_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("tempAvgAdaptRatio")
        if json_val is None:
            return YWeighScale.TEMPAVGADAPTRATIO_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_tempChgAdaptRatio(self, newval: float) -> int:
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
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("tempChgAdaptRatio", rest_val)

    async def get_tempChgAdaptRatio(self) -> float:
        """
        Returns the temperature change update rate, in per mille.
        The temperature change is updated every 10 seconds, by applying this adaptation rate
        to the difference between the measures ambient temperature and the current temperature used for
        change compensation. The standard rate is 0.6 per mille, and the maximal rate is 65 per mille.

        @return a floating point number corresponding to the temperature change update rate, in per mille

        On failure, throws an exception or returns YWeighScale.TEMPCHGADAPTRATIO_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("tempChgAdaptRatio")
        if json_val is None:
            return YWeighScale.TEMPCHGADAPTRATIO_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_compTempAvg(self) -> float:
        """
        Returns the current averaged temperature, used for thermal compensation.

        @return a floating point number corresponding to the current averaged temperature, used for thermal compensation

        On failure, throws an exception or returns YWeighScale.COMPTEMPAVG_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("compTempAvg")
        if json_val is None:
            return YWeighScale.COMPTEMPAVG_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_compTempChg(self) -> float:
        """
        Returns the current temperature variation, used for thermal compensation.

        @return a floating point number corresponding to the current temperature variation, used for
        thermal compensation

        On failure, throws an exception or returns YWeighScale.COMPTEMPCHG_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("compTempChg")
        if json_val is None:
            return YWeighScale.COMPTEMPCHG_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_compensation(self) -> float:
        """
        Returns the current current thermal compensation value.

        @return a floating point number corresponding to the current current thermal compensation value

        On failure, throws an exception or returns YWeighScale.COMPENSATION_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("compensation")
        if json_val is None:
            return YWeighScale.COMPENSATION_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_zeroTracking(self, newval: float) -> int:
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
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("zeroTracking", rest_val)

    async def get_zeroTracking(self) -> float:
        """
        Returns the zero tracking threshold value. When this threshold is larger than
        zero, any measure under the threshold will automatically be ignored and the
        zero compensation will be updated.

        @return a floating point number corresponding to the zero tracking threshold value

        On failure, throws an exception or returns YWeighScale.ZEROTRACKING_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("zeroTracking")
        if json_val is None:
            return YWeighScale.ZEROTRACKING_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YWeighScale.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YWeighScaleValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YWeighScaleTimedReportCallback) -> int:
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

    async def tare(self) -> int:
        """
        Adapts the load cell signal bias (stored in the corresponding genericSensor)
        so that the current signal corresponds to a zero weight. Remember to call the
        saveToFlash() method of the module if the modification must be kept.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("T")

    async def setupSpan(self, currWeight: float, maxWeight: float) -> int:
        """
        Configures the load cell span parameters (stored in the corresponding genericSensor)
        so that the current signal corresponds to the specified reference weight.

        @param currWeight : reference weight presently on the load cell.
        @param maxWeight : maximum weight to be expected on the load cell.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("S%d:%d" % (int(round(1000*currWeight)), int(round(1000*maxWeight))))

    async def setCompensationTable(self, tableIndex: int, tempValues: list[float], compValues: list[float]) -> int:
        siz: int
        res: int
        idx: int
        found: int
        prev: float
        curr: float
        currComp: float
        idxTemp: float
        siz = len(tempValues)
        if not (siz != 1):
            self._throw(YAPI.INVALID_ARGUMENT, "thermal compensation table must have at least two points")
            return YAPI.INVALID_ARGUMENT
        if not (siz == len(compValues)):
            self._throw(YAPI.INVALID_ARGUMENT, "table sizes mismatch")
            return YAPI.INVALID_ARGUMENT

        res = await self.set_command("%dZ" % tableIndex)
        if not (res==YAPI.SUCCESS):
            self._throw(YAPI.IO_ERROR, "unable to reset thermal compensation table")
            return YAPI.IO_ERROR
        # add records in growing temperature value
        found = 1
        prev = -999999.0
        while found > 0:
            found = 0
            curr = 99999999.0
            currComp = -999999.0
            idx = 0
            while idx < siz:
                idxTemp = tempValues[idx]
                if (idxTemp > prev) and (idxTemp < curr):
                    curr = idxTemp
                    currComp = compValues[idx]
                    found = 1
                idx = idx + 1
            if found > 0:
                res = await self.set_command("%dm%d:%d" % (tableIndex, int(round(1000*curr)), int(round(1000*currComp))))
                if not (res==YAPI.SUCCESS):
                    self._throw(YAPI.IO_ERROR, "unable to set thermal compensation table")
                    return YAPI.IO_ERROR
                prev = curr
        return YAPI.SUCCESS

    async def loadCompensationTable(self, tableIndex: int, tempValues: list[float], compValues: list[float]) -> int:
        id: str
        bin_json: xarray
        paramlist: list[xarray] = []
        siz: int
        idx: int
        temp: float
        comp: float

        id = await self.get_functionId()
        id = id[10: 10 + len(id) - 10]
        bin_json = await self._download("extra.json?page=%d" % ((4*YAPI._atoi(id))+tableIndex))
        paramlist = self._json_get_array(bin_json)
        # convert all values to float and append records
        siz = (len(paramlist) >> 1)
        del tempValues[:]
        del compValues[:]
        idx = 0
        while idx < siz:
            temp = YAPI._atof((paramlist[2*idx]).decode('latin-1'))/1000.0
            comp = YAPI._atof((paramlist[2*idx+1]).decode('latin-1'))/1000.0
            tempValues.append(temp)
            compValues.append(comp)
            idx = idx + 1


        return YAPI.SUCCESS

    async def set_offsetAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.setCompensationTable(0, tempValues, compValues)

    async def loadOffsetAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.loadCompensationTable(0, tempValues, compValues)

    async def set_offsetChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.setCompensationTable(1, tempValues, compValues)

    async def loadOffsetChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.loadCompensationTable(1, tempValues, compValues)

    async def set_spanAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.setCompensationTable(2, tempValues, compValues)

    async def loadSpanAvgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.loadCompensationTable(2, tempValues, compValues)

    async def set_spanChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.setCompensationTable(3, tempValues, compValues)

    async def loadSpanChgCompensationTable(self, tempValues: list[float], compValues: list[float]) -> int:
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
        return await self.loadCompensationTable(3, tempValues, compValues)

    # --- (end of YWeighScale implementation)

