# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YLightSensor
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
Yoctopuce library: Asyncio implementation of YLightSensor
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YLightSensor
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

# --- (YLightSensor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YLightSensorValueCallback = Union[Callable[['YLightSensor', str], Any], None]
        YLightSensorTimedReportCallback = Union[Callable[['YLightSensor', YMeasure], Any], None]
    except TypeError:
        YLightSensorValueCallback = Union[Callable, Awaitable]
        YLightSensorTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YLightSensor(YSensor):
    """
    The YLightSensor class allows you to read and configure Yoctopuce light sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the ability to easily perform a one-point linear calibration
    to compensate the effect of a glass or filter placed in front of the sensor.
    For some light sensors with several working modes, this class can select the
    desired working mode.

    """
    # --- (end of YLightSensor class start)
    if not _IS_MICROPYTHON:
        # --- (YLightSensor return codes)
        MEASURETYPE_HUMAN_EYE: Final[int] = 0
        MEASURETYPE_WIDE_SPECTRUM: Final[int] = 1
        MEASURETYPE_INFRARED: Final[int] = 2
        MEASURETYPE_HIGH_RATE: Final[int] = 3
        MEASURETYPE_HIGH_ENERGY: Final[int] = 4
        MEASURETYPE_HIGH_RESOLUTION: Final[int] = 5
        MEASURETYPE_INVALID: Final[int] = -1
        # --- (end of YLightSensor return codes)

    # --- (YLightSensor attributes declaration)
    _valueCallback: YLightSensorValueCallback
    _timedReportCallback: YLightSensorTimedReportCallback
    # --- (end of YLightSensor attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'LightSensor', func)
        # --- (YLightSensor constructor)
        # --- (end of YLightSensor constructor)

    # --- (YLightSensor implementation)
    @classmethod
    def FindLightSensor(cls, func: str) -> YLightSensor:
        """
        Retrieves a light sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the light sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLightSensor.isOnline() to test if the light sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a light sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the light sensor, for instance
                LIGHTMK4.lightSensor.

        @return a YLightSensor object allowing you to drive the light sensor.
        """
        return cls.FindLightSensorInContext(YAPI, func)

    @classmethod
    def FindLightSensorInContext(cls, yctx: YAPIContext, func: str) -> YLightSensor:
        """
        Retrieves a light sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the light sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YLightSensor.isOnline() to test if the light sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a light sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the light sensor, for instance
                LIGHTMK4.lightSensor.

        @return a YLightSensor object allowing you to drive the light sensor.
        """
        obj: Union[YLightSensor, None] = yctx._findInCache('LightSensor', func)
        if obj:
            return obj
        return YLightSensor(yctx, func)

    @classmethod
    def FirstLightSensor(cls) -> Union[YLightSensor, None]:
        """
        Starts the enumeration of light sensors currently accessible.
        Use the method YLightSensor.nextLightSensor() to iterate on
        next light sensors.

        @return a pointer to a YLightSensor object, corresponding to
                the first light sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstLightSensorInContext(YAPI)

    @classmethod
    def FirstLightSensorInContext(cls, yctx: YAPIContext) -> Union[YLightSensor, None]:
        """
        Starts the enumeration of light sensors currently accessible.
        Use the method YLightSensor.nextLightSensor() to iterate on
        next light sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YLightSensor object, corresponding to
                the first light sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('LightSensor')
        if hwid:
            return cls.FindLightSensorInContext(yctx, hwid2str(hwid))
        return None

    def nextLightSensor(self) -> Union[YLightSensor, None]:
        """
        Continues the enumeration of light sensors started using yFirstLightSensor().
        Caution: You can't make any assumption about the returned light sensors order.
        If you want to find a specific a light sensor, use LightSensor.findLightSensor()
        and a hardwareID or a logical name.

        @return a pointer to a YLightSensor object, corresponding to
                a light sensor currently online, or a None pointer
                if there are no more light sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('LightSensor', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindLightSensorInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_currentValue(self, newval: float) -> int:
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("currentValue", rest_val)

    async def calibrate(self, calibratedVal) -> int:
        """
        Changes the sensor-specific calibration parameter so that the current value
        matches a desired target (linear scaling).

        @param calibratedVal : the desired target value.

        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(calibratedVal * 65536.0, 1)))
        return await self._setAttr("currentValue", rest_val)

    async def get_measureType(self) -> int:
        """
        Returns the type of light measure.

        @return a value among YLightSensor.MEASURETYPE_HUMAN_EYE, YLightSensor.MEASURETYPE_WIDE_SPECTRUM,
        YLightSensor.MEASURETYPE_INFRARED, YLightSensor.MEASURETYPE_HIGH_RATE,
        YLightSensor.MEASURETYPE_HIGH_ENERGY and YLightSensor.MEASURETYPE_HIGH_RESOLUTION corresponding to
        the type of light measure

        On failure, throws an exception or returns YLightSensor.MEASURETYPE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("measureType")
        if json_val is None:
            return YLightSensor.MEASURETYPE_INVALID
        return json_val

    async def set_measureType(self, newval: int) -> int:
        """
        Changes the light sensor type used in the device. The measure can either
        approximate the response of the human eye, focus on a specific light
        spectrum, depending on the capabilities of the light-sensitive cell.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YLightSensor.MEASURETYPE_HUMAN_EYE,
        YLightSensor.MEASURETYPE_WIDE_SPECTRUM, YLightSensor.MEASURETYPE_INFRARED,
        YLightSensor.MEASURETYPE_HIGH_RATE, YLightSensor.MEASURETYPE_HIGH_ENERGY and
        YLightSensor.MEASURETYPE_HIGH_RESOLUTION corresponding to the light sensor type used in the device

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("measureType", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YLightSensorValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YLightSensorTimedReportCallback) -> int:
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

    # --- (end of YLightSensor implementation)

