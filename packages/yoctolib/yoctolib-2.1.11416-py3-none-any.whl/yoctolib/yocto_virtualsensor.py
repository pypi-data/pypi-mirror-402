# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YVirtualSensor
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
Yoctopuce library: High-level API for YVirtualSensor
version: PATCH_WITH_VERSION
requires: yocto_virtualsensor_aio
requires: yocto_api
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_virtualsensor_aio import YVirtualSensor as YVirtualSensor_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
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
    _aio: YVirtualSensor_aio
    # --- (end of YVirtualSensor class start)
    if not _IS_MICROPYTHON:
        # --- (YVirtualSensor return codes)
        INVALIDVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        # --- (end of YVirtualSensor return codes)


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
        return cls._proxy(cls, YVirtualSensor_aio.FindVirtualSensorInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YVirtualSensor_aio.FindVirtualSensorInContext(yctx._aio, func))

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
        return cls._proxy(cls, YVirtualSensor_aio.FirstVirtualSensorInContext(YAPI_aio))

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
        return cls._proxy(cls, YVirtualSensor_aio.FirstVirtualSensorInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextVirtualSensor())

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
        def set_currentRawValue(self, newval: float) -> int:
            """
            Changes the current value of the sensor (raw value, before calibration).

            @param newval : a floating point number corresponding to the current value of the sensor (raw
            value, before calibration)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_currentRawValue(newval))

    if not _DYNAMIC_HELPERS:
        def set_sensorState(self, newval: int) -> int:
            return self._run(self._aio.set_sensorState(newval))

    if not _DYNAMIC_HELPERS:
        def set_invalidValue(self, newval: float) -> int:
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
            return self._run(self._aio.set_invalidValue(newval))

    if not _DYNAMIC_HELPERS:
        def get_invalidValue(self) -> float:
            """
            Returns the invalid value of the sensor, returned if the sensor is read when in invalid state
            (for instance before having been set).

            @return a floating point number corresponding to the invalid value of the sensor, returned if the
            sensor is read when in invalid state
                    (for instance before having been set)

            On failure, throws an exception or returns YVirtualSensor.INVALIDVALUE_INVALID.
            """
            return self._run(self._aio.get_invalidValue())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YVirtualSensorValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YVirtualSensorTimedReportCallback) -> int:
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
        def set_sensorAsInvalid(self) -> int:
            """
            Changes the current sensor state to invalid (as if no value would have been ever set).

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_sensorAsInvalid())

    # --- (end of YVirtualSensor implementation)

