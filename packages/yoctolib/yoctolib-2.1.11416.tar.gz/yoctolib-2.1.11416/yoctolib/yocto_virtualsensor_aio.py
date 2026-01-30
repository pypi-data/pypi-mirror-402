# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YVirtualSensor
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
Yoctopuce library: Asyncio implementation of YVirtualSensor
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YVirtualSensor
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

# --- (YVirtualSensor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YVirtualSensorValueCallback = Union[Callable[['YVirtualSensor', str], Any], None]
        YVirtualSensorTimedReportCallback = Union[Callable[['YVirtualSensor', YMeasure], Any], None]
    except TypeError:
        YVirtualSensorValueCallback = Union[Callable, Awaitable]
        YVirtualSensorTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YVirtualSensor(YSensor):
    """
    The YVirtualSensor class allows you to use Yoctopuce virtual sensors.
    These sensors make it possible to show external data collected by the user
    as a Yoctopuce Sensor. This class inherits from YSensor class the core
    functions to read measurements, to register callback functions, and to access
    the autonomous datalogger. It adds the ability to change the sensor value as
    needed, or to mark current value as invalid.

    """
    # --- (end of YVirtualSensor class start)
    if not _IS_MICROPYTHON:
        # --- (YVirtualSensor return codes)
        INVALIDVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        # --- (end of YVirtualSensor return codes)

    # --- (YVirtualSensor attributes declaration)
    _valueCallback: YVirtualSensorValueCallback
    _timedReportCallback: YVirtualSensorTimedReportCallback
    # --- (end of YVirtualSensor attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'VirtualSensor', func)
        # --- (YVirtualSensor constructor)
        # --- (end of YVirtualSensor constructor)

    # --- (YVirtualSensor implementation)
    @classmethod
    def FindVirtualSensor(cls, func: str) -> YVirtualSensor:
        """
        Retrieves a virtual sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the virtual sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YVirtualSensor.isOnline() to test if the virtual sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a virtual sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the virtual sensor, for instance
                MyDevice.virtualSensor1.

        @return a YVirtualSensor object allowing you to drive the virtual sensor.
        """
        return cls.FindVirtualSensorInContext(YAPI, func)

    @classmethod
    def FindVirtualSensorInContext(cls, yctx: YAPIContext, func: str) -> YVirtualSensor:
        """
        Retrieves a virtual sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the virtual sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YVirtualSensor.isOnline() to test if the virtual sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a virtual sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the virtual sensor, for instance
                MyDevice.virtualSensor1.

        @return a YVirtualSensor object allowing you to drive the virtual sensor.
        """
        obj: Union[YVirtualSensor, None] = yctx._findInCache('VirtualSensor', func)
        if obj:
            return obj
        return YVirtualSensor(yctx, func)

    @classmethod
    def FirstVirtualSensor(cls) -> Union[YVirtualSensor, None]:
        """
        Starts the enumeration of virtual sensors currently accessible.
        Use the method YVirtualSensor.nextVirtualSensor() to iterate on
        next virtual sensors.

        @return a pointer to a YVirtualSensor object, corresponding to
                the first virtual sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstVirtualSensorInContext(YAPI)

    @classmethod
    def FirstVirtualSensorInContext(cls, yctx: YAPIContext) -> Union[YVirtualSensor, None]:
        """
        Starts the enumeration of virtual sensors currently accessible.
        Use the method YVirtualSensor.nextVirtualSensor() to iterate on
        next virtual sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YVirtualSensor object, corresponding to
                the first virtual sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('VirtualSensor')
        if hwid:
            return cls.FindVirtualSensorInContext(yctx, hwid2str(hwid))
        return None

    def nextVirtualSensor(self) -> Union[YVirtualSensor, None]:
        """
        Continues the enumeration of virtual sensors started using yFirstVirtualSensor().
        Caution: You can't make any assumption about the returned virtual sensors order.
        If you want to find a specific a virtual sensor, use VirtualSensor.findVirtualSensor()
        and a hardwareID or a logical name.

        @return a pointer to a YVirtualSensor object, corresponding to
                a virtual sensor currently online, or a None pointer
                if there are no more virtual sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('VirtualSensor', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindVirtualSensorInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_unit(self, newval: str) -> int:
        """
        Changes the measuring unit for the measured value.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the measuring unit for the measured value

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("unit", rest_val)

    async def set_currentRawValue(self, newval: float) -> int:
        """
        Changes the current value of the sensor (raw value, before calibration).

        @param newval : a floating point number corresponding to the current value of the sensor (raw
        value, before calibration)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("currentRawValue", rest_val)

    async def set_sensorState(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("sensorState", rest_val)

    async def set_invalidValue(self, newval: float) -> int:
        """
        Changes the invalid value of the sensor, returned if the sensor is read when in invalid state
        (for instance before having been set). Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a floating point number corresponding to the invalid value of the sensor, returned
        if the sensor is read when in invalid state
                (for instance before having been set)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("invalidValue", rest_val)

    async def get_invalidValue(self) -> float:
        """
        Returns the invalid value of the sensor, returned if the sensor is read when in invalid state
        (for instance before having been set).

        @return a floating point number corresponding to the invalid value of the sensor, returned if the
        sensor is read when in invalid state
                (for instance before having been set)

        On failure, throws an exception or returns YVirtualSensor.INVALIDVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("invalidValue")
        if json_val is None:
            return YVirtualSensor.INVALIDVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YVirtualSensorValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YVirtualSensorTimedReportCallback) -> int:
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

    async def set_sensorAsInvalid(self) -> int:
        """
        Changes the current sensor state to invalid (as if no value would have been ever set).

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_sensorState(1)

    # --- (end of YVirtualSensor implementation)

