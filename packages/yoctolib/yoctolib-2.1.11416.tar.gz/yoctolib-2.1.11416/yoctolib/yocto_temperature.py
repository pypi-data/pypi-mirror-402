# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YTemperature
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
Yoctopuce library: High-level API for YTemperature
version: PATCH_WITH_VERSION
requires: yocto_temperature_aio
requires: yocto_api
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_temperature_aio import YTemperature as YTemperature_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
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
    _aio: YTemperature_aio
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
        return cls._proxy(cls, YTemperature_aio.FindTemperatureInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YTemperature_aio.FindTemperatureInContext(yctx._aio, func))

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
        return cls._proxy(cls, YTemperature_aio.FirstTemperatureInContext(YAPI_aio))

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
        return cls._proxy(cls, YTemperature_aio.FirstTemperatureInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextTemperature())

    if not _DYNAMIC_HELPERS:
        def set_unit(self, newval: str) -> int:
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
            return self._run(self._aio.set_unit(newval))

    if not _DYNAMIC_HELPERS:
        def get_sensorType(self) -> int:
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
            return self._run(self._aio.get_sensorType())

    if not _DYNAMIC_HELPERS:
        def set_sensorType(self, newval: int) -> int:
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
            return self._run(self._aio.set_sensorType(newval))

    if not _DYNAMIC_HELPERS:
        def get_signalValue(self) -> float:
            """
            Returns the current value of the electrical signal measured by the sensor.

            @return a floating point number corresponding to the current value of the electrical signal
            measured by the sensor

            On failure, throws an exception or returns YTemperature.SIGNALVALUE_INVALID.
            """
            return self._run(self._aio.get_signalValue())

    if not _DYNAMIC_HELPERS:
        def get_signalUnit(self) -> str:
            """
            Returns the measuring unit of the electrical signal used by the sensor.

            @return a string corresponding to the measuring unit of the electrical signal used by the sensor

            On failure, throws an exception or returns YTemperature.SIGNALUNIT_INVALID.
            """
            return self._run(self._aio.get_signalUnit())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YTemperatureValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YTemperatureTimedReportCallback) -> int:
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
        def set_ntcParameters(self, res25: float, beta: float) -> int:
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
            return self._run(self._aio.set_ntcParameters(res25, beta))

    if not _DYNAMIC_HELPERS:
        def set_thermistorResponseTable(self, tempValues: list[float], resValues: list[float]) -> int:
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
            return self._run(self._aio.set_thermistorResponseTable(tempValues, resValues))

    if not _DYNAMIC_HELPERS:
        def loadThermistorResponseTable(self, tempValues: list[float], resValues: list[float]) -> int:
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
            return self._run(self._aio.loadThermistorResponseTable(tempValues, resValues))

    # --- (end of YTemperature implementation)

