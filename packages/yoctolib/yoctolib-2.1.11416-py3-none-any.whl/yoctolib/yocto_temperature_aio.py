# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YTemperature
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
Yoctopuce library: Asyncio implementation of YTemperature
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YTemperature
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YSensor, YMeasure, xarray
)

# --- (YTemperature class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YTemperatureValueCallback = Union[Callable[['YTemperature', str], Any], None]
        YTemperatureTimedReportCallback = Union[Callable[['YTemperature', YMeasure], Any], None]
    except TypeError:
        YTemperatureValueCallback = Union[Callable, Awaitable]
        YTemperatureTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YTemperature(YSensor):
    """
    The YTemperature class allows you to read and configure Yoctopuce temperature sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the ability to configure some specific parameters
    for some sensors (connection type, temperature mapping table).

    """
    # --- (end of YTemperature class start)
    if not _IS_MICROPYTHON:
        # --- (YTemperature return codes)
        SIGNALVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SIGNALUNIT_INVALID: Final[str] = YAPI.INVALID_STRING
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        SENSORTYPE_DIGITAL: Final[int] = 0
        SENSORTYPE_TYPE_K: Final[int] = 1
        SENSORTYPE_TYPE_E: Final[int] = 2
        SENSORTYPE_TYPE_J: Final[int] = 3
        SENSORTYPE_TYPE_N: Final[int] = 4
        SENSORTYPE_TYPE_R: Final[int] = 5
        SENSORTYPE_TYPE_S: Final[int] = 6
        SENSORTYPE_TYPE_T: Final[int] = 7
        SENSORTYPE_PT100_4WIRES: Final[int] = 8
        SENSORTYPE_PT100_3WIRES: Final[int] = 9
        SENSORTYPE_PT100_2WIRES: Final[int] = 10
        SENSORTYPE_RES_OHM: Final[int] = 11
        SENSORTYPE_RES_NTC: Final[int] = 12
        SENSORTYPE_RES_LINEAR: Final[int] = 13
        SENSORTYPE_RES_INTERNAL: Final[int] = 14
        SENSORTYPE_IR: Final[int] = 15
        SENSORTYPE_RES_PT1000: Final[int] = 16
        SENSORTYPE_CHANNEL_OFF: Final[int] = 17
        SENSORTYPE_INVALID: Final[int] = -1
        # --- (end of YTemperature return codes)

    # --- (YTemperature attributes declaration)
    _valueCallback: YTemperatureValueCallback
    _timedReportCallback: YTemperatureTimedReportCallback
    # --- (end of YTemperature attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Temperature', func)
        # --- (YTemperature constructor)
        # --- (end of YTemperature constructor)

    # --- (YTemperature implementation)
    @classmethod
    def FindTemperature(cls, func: str) -> YTemperature:
        """
        Retrieves a temperature sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the temperature sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YTemperature.isOnline() to test if the temperature sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a temperature sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the temperature sensor, for instance
                METEOMK2.temperature.

        @return a YTemperature object allowing you to drive the temperature sensor.
        """
        return cls.FindTemperatureInContext(YAPI, func)

    @classmethod
    def FindTemperatureInContext(cls, yctx: YAPIContext, func: str) -> YTemperature:
        """
        Retrieves a temperature sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the temperature sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YTemperature.isOnline() to test if the temperature sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a temperature sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the temperature sensor, for instance
                METEOMK2.temperature.

        @return a YTemperature object allowing you to drive the temperature sensor.
        """
        obj: Union[YTemperature, None] = yctx._findInCache('Temperature', func)
        if obj:
            return obj
        return YTemperature(yctx, func)

    @classmethod
    def FirstTemperature(cls) -> Union[YTemperature, None]:
        """
        Starts the enumeration of temperature sensors currently accessible.
        Use the method YTemperature.nextTemperature() to iterate on
        next temperature sensors.

        @return a pointer to a YTemperature object, corresponding to
                the first temperature sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstTemperatureInContext(YAPI)

    @classmethod
    def FirstTemperatureInContext(cls, yctx: YAPIContext) -> Union[YTemperature, None]:
        """
        Starts the enumeration of temperature sensors currently accessible.
        Use the method YTemperature.nextTemperature() to iterate on
        next temperature sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YTemperature object, corresponding to
                the first temperature sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Temperature')
        if hwid:
            return cls.FindTemperatureInContext(yctx, hwid2str(hwid))
        return None

    def nextTemperature(self) -> Union[YTemperature, None]:
        """
        Continues the enumeration of temperature sensors started using yFirstTemperature().
        Caution: You can't make any assumption about the returned temperature sensors order.
        If you want to find a specific a temperature sensor, use Temperature.findTemperature()
        and a hardwareID or a logical name.

        @return a pointer to a YTemperature object, corresponding to
                a temperature sensor currently online, or a None pointer
                if there are no more temperature sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Temperature', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindTemperatureInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_unit(self, newval: str) -> int:
        """
        Changes the measuring unit for the measured temperature. That unit is a string.
        If that strings end with the letter F all temperatures values will returned in
        Fahrenheit degrees. If that String ends with the letter K all values will be
        returned in Kelvin degrees. If that string ends with the letter C all values will be
        returned in Celsius degrees.  If the string ends with any other character the
        change will be ignored. Remember to call the
        saveToFlash() method of the module if the modification must be kept.
        WARNING: if a specific calibration is defined for the temperature function, a
        unit system change will probably break it.

        @param newval : a string corresponding to the measuring unit for the measured temperature

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("unit", rest_val)

    async def get_sensorType(self) -> int:
        """
        Returns the temperature sensor type.

        @return a value among YTemperature.SENSORTYPE_DIGITAL, YTemperature.SENSORTYPE_TYPE_K,
        YTemperature.SENSORTYPE_TYPE_E, YTemperature.SENSORTYPE_TYPE_J, YTemperature.SENSORTYPE_TYPE_N,
        YTemperature.SENSORTYPE_TYPE_R, YTemperature.SENSORTYPE_TYPE_S, YTemperature.SENSORTYPE_TYPE_T,
        YTemperature.SENSORTYPE_PT100_4WIRES, YTemperature.SENSORTYPE_PT100_3WIRES,
        YTemperature.SENSORTYPE_PT100_2WIRES, YTemperature.SENSORTYPE_RES_OHM,
        YTemperature.SENSORTYPE_RES_NTC, YTemperature.SENSORTYPE_RES_LINEAR,
        YTemperature.SENSORTYPE_RES_INTERNAL, YTemperature.SENSORTYPE_IR,
        YTemperature.SENSORTYPE_RES_PT1000 and YTemperature.SENSORTYPE_CHANNEL_OFF corresponding to the
        temperature sensor type

        On failure, throws an exception or returns YTemperature.SENSORTYPE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("sensorType")
        if json_val is None:
            return YTemperature.SENSORTYPE_INVALID
        return json_val

    async def set_sensorType(self, newval: int) -> int:
        """
        Changes the temperature sensor type.  This function is used
        to define the type of thermocouple (K,E...) used with the device.
        It has no effect if module is using a digital sensor or a thermistor.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YTemperature.SENSORTYPE_DIGITAL, YTemperature.SENSORTYPE_TYPE_K,
        YTemperature.SENSORTYPE_TYPE_E, YTemperature.SENSORTYPE_TYPE_J, YTemperature.SENSORTYPE_TYPE_N,
        YTemperature.SENSORTYPE_TYPE_R, YTemperature.SENSORTYPE_TYPE_S, YTemperature.SENSORTYPE_TYPE_T,
        YTemperature.SENSORTYPE_PT100_4WIRES, YTemperature.SENSORTYPE_PT100_3WIRES,
        YTemperature.SENSORTYPE_PT100_2WIRES, YTemperature.SENSORTYPE_RES_OHM,
        YTemperature.SENSORTYPE_RES_NTC, YTemperature.SENSORTYPE_RES_LINEAR,
        YTemperature.SENSORTYPE_RES_INTERNAL, YTemperature.SENSORTYPE_IR,
        YTemperature.SENSORTYPE_RES_PT1000 and YTemperature.SENSORTYPE_CHANNEL_OFF corresponding to the
        temperature sensor type

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("sensorType", rest_val)

    async def get_signalValue(self) -> float:
        """
        Returns the current value of the electrical signal measured by the sensor.

        @return a floating point number corresponding to the current value of the electrical signal
        measured by the sensor

        On failure, throws an exception or returns YTemperature.SIGNALVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("signalValue")
        if json_val is None:
            return YTemperature.SIGNALVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_signalUnit(self) -> str:
        """
        Returns the measuring unit of the electrical signal used by the sensor.

        @return a string corresponding to the measuring unit of the electrical signal used by the sensor

        On failure, throws an exception or returns YTemperature.SIGNALUNIT_INVALID.
        """
        json_val: Union[str, None] = await self._lazyCache("signalUnit")
        if json_val is None:
            return YTemperature.SIGNALUNIT_INVALID
        return json_val

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YTemperature.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YTemperatureValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YTemperatureTimedReportCallback) -> int:
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

    async def set_ntcParameters(self, res25: float, beta: float) -> int:
        """
        Configures NTC thermistor parameters in order to properly compute the temperature from
        the measured resistance. For increased precision, you can enter a complete mapping
        table using set_thermistorResponseTable. This function can only be used with a
        temperature sensor based on thermistors.

        @param res25 : thermistor resistance at 25 degrees Celsius
        @param beta : Beta value

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        t0: float
        t1: float
        res100: float
        tempValues: list[float] = []
        resValues: list[float] = []
        t0 = 25.0+273.15
        t1 = 100.0+273.15
        res100 = res25 * math.exp(beta*(1.0/t1 - 1.0/t0))
        del tempValues[:]
        del resValues[:]
        tempValues.append(25.0)
        resValues.append(res25)
        tempValues.append(100.0)
        resValues.append(res100)


        return await self.set_thermistorResponseTable(tempValues, resValues)

    async def set_thermistorResponseTable(self, tempValues: list[float], resValues: list[float]) -> int:
        """
        Records a thermistor response table, in order to interpolate the temperature from
        the measured resistance. This function can only be used with a temperature
        sensor based on thermistors.

        @param tempValues : array of floating point numbers, corresponding to all
                temperatures (in degrees Celsius) for which the resistance of the
                thermistor is specified.
        @param resValues : array of floating point numbers, corresponding to the resistance
                values (in Ohms) for each of the temperature included in the first
                argument, index by index.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        siz: int
        res: int
        idx: int
        found: int
        prev: float
        curr: float
        currTemp: float
        idxres: float
        siz = len(tempValues)
        if not (siz >= 2):
            self._throw(YAPI.INVALID_ARGUMENT, "thermistor response table must have at least two points")
            return YAPI.INVALID_ARGUMENT
        if not (siz == len(resValues)):
            self._throw(YAPI.INVALID_ARGUMENT, "table sizes mismatch")
            return YAPI.INVALID_ARGUMENT

        res = await self.set_command("Z")
        if not (res==YAPI.SUCCESS):
            self._throw(YAPI.IO_ERROR, "unable to reset thermistor parameters")
            return YAPI.IO_ERROR
        # add records in growing resistance value
        found = 1
        prev = 0.0
        while found > 0:
            found = 0
            curr = 99999999.0
            currTemp = -999999.0
            idx = 0
            while idx < siz:
                idxres = resValues[idx]
                if (idxres > prev) and (idxres < curr):
                    curr = idxres
                    currTemp = tempValues[idx]
                    found = 1
                idx = idx + 1
            if found > 0:
                res = await self.set_command("m%d:%d" % (int(round(1000*curr)), int(round(1000*currTemp))))
                if not (res==YAPI.SUCCESS):
                    self._throw(YAPI.IO_ERROR, "unable to reset thermistor parameters")
                    return YAPI.IO_ERROR
                prev = curr
        return YAPI.SUCCESS

    async def loadThermistorResponseTable(self, tempValues: list[float], resValues: list[float]) -> int:
        """
        Retrieves the thermistor response table previously configured using the
        set_thermistorResponseTable function. This function can only be used with a
        temperature sensor based on thermistors.

        @param tempValues : array of floating point numbers, that is filled by the function
                with all temperatures (in degrees Celsius) for which the resistance
                of the thermistor is specified.
        @param resValues : array of floating point numbers, that is filled by the function
                with the value (in Ohms) for each of the temperature included in the
                first argument, index by index.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        id: str
        bin_json: xarray
        paramlist: list[xarray] = []
        templist: list[float] = []
        siz: int
        idx: int
        temp: float
        found: int
        prev: float
        curr: float
        currRes: float
        del tempValues[:]
        del resValues[:]

        id = await self.get_functionId()
        id = id[11: 11 + len(id) - 11]
        if id == "":
            id = "1"
        bin_json = await self._download("extra.json?page=%s" % id)
        paramlist = self._json_get_array(bin_json)
        # first convert all temperatures to float
        siz = (len(paramlist) >> 1)
        del templist[:]
        idx = 0
        while idx < siz:
            temp = YAPI._atof((paramlist[2*idx+1]).decode('latin-1'))/1000.0
            templist.append(temp)
            idx = idx + 1
        # then add records in growing temperature value
        del tempValues[:]
        del resValues[:]
        found = 1
        prev = -999999.0
        while found > 0:
            found = 0
            curr = 999999.0
            currRes = -999999.0
            idx = 0
            while idx < siz:
                temp = templist[idx]
                if (temp > prev) and (temp < curr):
                    curr = temp
                    currRes = YAPI._atof((paramlist[2*idx]).decode('latin-1'))/1000.0
                    found = 1
                idx = idx + 1
            if found > 0:
                tempValues.append(curr)
                resValues.append(currRes)
                prev = curr


        return YAPI.SUCCESS

    # --- (end of YTemperature implementation)

