# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YTilt
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
Yoctopuce library: Asyncio implementation of YTilt
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YTilt
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

# --- (YTilt class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YTiltValueCallback = Union[Callable[['YTilt', str], Any], None]
        YTiltTimedReportCallback = Union[Callable[['YTilt', YMeasure], Any], None]
    except TypeError:
        YTiltValueCallback = Union[Callable, Awaitable]
        YTiltTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YTilt(YSensor):
    """
    The YSensor class is the parent class for all Yoctopuce sensor types. It can be
    used to read the current value and unit of any sensor, read the min/max
    value, configure autonomous recording frequency and access recorded data.
    It also provides a function to register a callback invoked each time the
    observed value changes, or at a predefined interval. Using this class rather
    than a specific subclass makes it possible to create generic applications
    that work with any Yoctopuce sensor, even those that do not yet exist.
    Note: The YAnButton class is the only analog input which does not inherit
    from YSensor.

    """
    # --- (end of YTilt class start)
    if not _IS_MICROPYTHON:
        # --- (YTilt return codes)
        BANDWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        AXIS_X: Final[int] = 0
        AXIS_Y: Final[int] = 1
        AXIS_Z: Final[int] = 2
        AXIS_INVALID: Final[int] = -1
        # --- (end of YTilt return codes)

    # --- (YTilt attributes declaration)
    _valueCallback: YTiltValueCallback
    _timedReportCallback: YTiltTimedReportCallback
    # --- (end of YTilt attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Tilt', func)
        # --- (YTilt constructor)
        # --- (end of YTilt constructor)

    # --- (YTilt implementation)
    @classmethod
    def FindTilt(cls, func: str) -> YTilt:
        """
        Retrieves a tilt sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the tilt sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YTilt.isOnline() to test if the tilt sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a tilt sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the tilt sensor, for instance
                Y3DMK002.tilt1.

        @return a YTilt object allowing you to drive the tilt sensor.
        """
        return cls.FindTiltInContext(YAPI, func)

    @classmethod
    def FindTiltInContext(cls, yctx: YAPIContext, func: str) -> YTilt:
        """
        Retrieves a tilt sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the tilt sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YTilt.isOnline() to test if the tilt sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a tilt sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the tilt sensor, for instance
                Y3DMK002.tilt1.

        @return a YTilt object allowing you to drive the tilt sensor.
        """
        obj: Union[YTilt, None] = yctx._findInCache('Tilt', func)
        if obj:
            return obj
        return YTilt(yctx, func)

    @classmethod
    def FirstTilt(cls) -> Union[YTilt, None]:
        """
        Starts the enumeration of tilt sensors currently accessible.
        Use the method YTilt.nextTilt() to iterate on
        next tilt sensors.

        @return a pointer to a YTilt object, corresponding to
                the first tilt sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstTiltInContext(YAPI)

    @classmethod
    def FirstTiltInContext(cls, yctx: YAPIContext) -> Union[YTilt, None]:
        """
        Starts the enumeration of tilt sensors currently accessible.
        Use the method YTilt.nextTilt() to iterate on
        next tilt sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YTilt object, corresponding to
                the first tilt sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Tilt')
        if hwid:
            return cls.FindTiltInContext(yctx, hwid2str(hwid))
        return None

    def nextTilt(self) -> Union[YTilt, None]:
        """
        Continues the enumeration of tilt sensors started using yFirstTilt().
        Caution: You can't make any assumption about the returned tilt sensors order.
        If you want to find a specific a tilt sensor, use Tilt.findTilt()
        and a hardwareID or a logical name.

        @return a pointer to a YTilt object, corresponding to
                a tilt sensor currently online, or a None pointer
                if there are no more tilt sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Tilt', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindTiltInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_bandwidth(self) -> int:
        """
        Returns the measure update frequency, measured in Hz.

        @return an integer corresponding to the measure update frequency, measured in Hz

        On failure, throws an exception or returns YTilt.BANDWIDTH_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("bandwidth")
        if json_val is None:
            return YTilt.BANDWIDTH_INVALID
        return json_val

    async def set_bandwidth(self, newval: int) -> int:
        """
        Changes the measure update frequency, measured in Hz. When the
        frequency is lower, the device performs averaging.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the measure update frequency, measured in Hz

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("bandwidth", rest_val)

    async def get_axis(self) -> int:
        json_val: Union[int, None] = await self._fromCache("axis")
        if json_val is None:
            return YTilt.AXIS_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YTiltValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YTiltTimedReportCallback) -> int:
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

    async def calibrateToZero(self) -> int:
        """
        Performs a zero calibration for the tilt measurement (Yocto-Inclinometer only).
        When this method is invoked, a simple shift (translation)
        is applied so that the current position is reported as a zero angle.
        Be aware that this shift will also affect the measurement boundaries.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        currentRawVal: float
        rawVals: list[float] = []
        refVals: list[float] = []
        currentRawVal = await self.get_currentRawValue()
        del rawVals[:]
        del refVals[:]
        rawVals.append(currentRawVal)
        refVals.append(0.0)


        return await self.calibrateFromPoints(rawVals, refVals)

    async def restoreZeroCalibration(self) -> int:
        """
        Cancels any previous zero calibration for the tilt measurement (Yocto-Inclinometer only).
        This function restores the factory zero calibration.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._setAttr("calibrationParam", "0")

    # --- (end of YTilt implementation)

