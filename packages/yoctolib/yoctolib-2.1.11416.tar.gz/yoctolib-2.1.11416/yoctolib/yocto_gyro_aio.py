# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_gyro_aio.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YGyro API for Gyro functions
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
Yoctopuce library: Asyncio implementation of YGyro
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YGyro YQt
"""
from __future__ import annotations

import sys, math

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
    YAPIContext, YAPI, YAPI_Exception, YSensor, YFunction, YMeasure, HwId, hwid2str
)

# --- (generated code: YQt class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YQtValueCallback = Union[Callable[['YQt', str], Any], None]
        YQtTimedReportCallback = Union[Callable[['YQt', YMeasure], Any], None]
    except TypeError:
        YQtValueCallback = Union[Callable, Awaitable]
        YQtTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YQt(YSensor):
    """
    The YQt class provides direct access to the 3D attitude estimation
    provided by Yoctopuce inertial sensors. The four instances of YQt
    provide direct access to the individual quaternion components representing the
    orientation. It is usually not needed to use the YQt class
    directly, as the YGyro class provides a more convenient higher-level
    interface.

    """
    # --- (end of generated code: YQt class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YQt return codes)
        pass
        # --- (end of generated code: YQt return codes)

    # --- (generated code: YQt attributes declaration)
    _valueCallback: YQtValueCallback
    _timedReportCallback: YQtTimedReportCallback
    # --- (end of generated code: YQt attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Qt', func)
        # --- (generated code: YQt constructor)
        # --- (end of generated code: YQt constructor)

    # --- (generated code: YQt implementation)
    @classmethod
    def FindQt(cls, func: str) -> YQt:
        """
        Retrieves a quaternion component for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the quaternion component is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YQt.isOnline() to test if the quaternion component is
        indeed online at a given time. In case of ambiguity when looking for
        a quaternion component by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the quaternion component, for instance
                Y3DMK002.qt1.

        @return a YQt object allowing you to drive the quaternion component.
        """
        return cls.FindQtInContext(YAPI, func)

    @classmethod
    def FindQtInContext(cls, yctx: YAPIContext, func: str) -> YQt:
        """
        Retrieves a quaternion component for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the quaternion component is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YQt.isOnline() to test if the quaternion component is
        indeed online at a given time. In case of ambiguity when looking for
        a quaternion component by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the quaternion component, for instance
                Y3DMK002.qt1.

        @return a YQt object allowing you to drive the quaternion component.
        """
        obj: Union[YQt, None] = yctx._findInCache('Qt', func)
        if obj:
            return obj
        return YQt(yctx, func)

    @classmethod
    def FirstQt(cls) -> Union[YQt, None]:
        """
        Starts the enumeration of quaternion components currently accessible.
        Use the method YQt.nextQt() to iterate on
        next quaternion components.

        @return a pointer to a YQt object, corresponding to
                the first quaternion component currently online, or a None pointer
                if there are none.
        """
        return cls.FirstQtInContext(YAPI)

    @classmethod
    def FirstQtInContext(cls, yctx: YAPIContext) -> Union[YQt, None]:
        """
        Starts the enumeration of quaternion components currently accessible.
        Use the method YQt.nextQt() to iterate on
        next quaternion components.

        @param yctx : a YAPI context.

        @return a pointer to a YQt object, corresponding to
                the first quaternion component currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Qt')
        if hwid:
            return cls.FindQtInContext(yctx, hwid2str(hwid))
        return None

    def nextQt(self) -> Union[YQt, None]:
        """
        Continues the enumeration of quaternion components started using yFirstQt().
        Caution: You can't make any assumption about the returned quaternion components order.
        If you want to find a specific a quaternion component, use Qt.findQt()
        and a hardwareID or a logical name.

        @return a pointer to a YQt object, corresponding to
                a quaternion component currently online, or a None pointer
                if there are no more quaternion components to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Qt', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindQtInContext(self._yapi, hwid2str(next_hwid))
        return None

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YQtValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YQtTimedReportCallback) -> int:
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

    # --- (end of generated code: YQt implementation)


if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YQuatCallback = Union[Callable[['YGyro', float, float, float, float], Awaitable[None]], None]
        YAnglesCallback = Union[Callable[['YGyro', float, float, float], Awaitable[None]], None]
    except TypeError:
        YQuatCallback = Union[Callable, Awaitable]
        YAnglesCallback = Union[Callable, Awaitable]


async def yInternalGyroCallback(obj: YQt, str_value: str) -> None:
    gyro: YGyro = await obj.get_userData()
    if gyro is None:
        return
    tmp = await obj.get_functionId()[2:]
    idx = int(tmp)
    dbl_value = float(str_value)
    # noinspection PyProtectedMember
    await gyro._invokeGyroCallbacks(idx, dbl_value)


# --- (generated code: YGyro class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YGyroValueCallback = Union[Callable[['YGyro', str], Any], None]
        YGyroTimedReportCallback = Union[Callable[['YGyro', YMeasure], Any], None]
    except TypeError:
        YGyroValueCallback = Union[Callable, Awaitable]
        YGyroTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YGyro(YSensor):
    """
    The YGyro class allows you to read and configure Yoctopuce gyroscopes.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the possibility to access x, y and z components of the rotation
    vector separately, as well as the possibility to deal with quaternion-based
    orientation estimates.

    """
    # --- (end of generated code: YGyro class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YGyro return codes)
        BANDWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        XVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        YVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ZVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        # --- (end of generated code: YGyro return codes)

    # --- (generated code: YGyro attributes declaration)
    _valueCallback: YGyroValueCallback
    _timedReportCallback: YGyroTimedReportCallback
    _qt_stamp: int
    _qt_w: YQt
    _qt_x: YQt
    _qt_y: YQt
    _qt_z: YQt
    _w: float
    _x: float
    _y: float
    _z: float
    _angles_stamp: int
    _head: float
    _pitch: float
    _roll: float
    _quatCallback: YQuatCallback
    _anglesCallback: YAnglesCallback
    # --- (end of generated code: YGyro attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Gyro', func)
        # --- (generated code: YGyro constructor)
        self._qt_stamp = 0
        self._w = 0.0
        self._x = 0.0
        self._y = 0.0
        self._z = 0.0
        self._angles_stamp = 0
        self._head = 0.0
        self._pitch = 0.0
        self._roll = 0.0
        # --- (end of generated code: YGyro constructor)

    # --- (generated code: YGyro implementation)
    @classmethod
    def FindGyro(cls, func: str) -> YGyro:
        """
        Retrieves a gyroscope for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the gyroscope is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGyro.isOnline() to test if the gyroscope is
        indeed online at a given time. In case of ambiguity when looking for
        a gyroscope by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the gyroscope, for instance
                Y3DMK002.gyro.

        @return a YGyro object allowing you to drive the gyroscope.
        """
        return cls.FindGyroInContext(YAPI, func)

    @classmethod
    def FindGyroInContext(cls, yctx: YAPIContext, func: str) -> YGyro:
        """
        Retrieves a gyroscope for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the gyroscope is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGyro.isOnline() to test if the gyroscope is
        indeed online at a given time. In case of ambiguity when looking for
        a gyroscope by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the gyroscope, for instance
                Y3DMK002.gyro.

        @return a YGyro object allowing you to drive the gyroscope.
        """
        obj: Union[YGyro, None] = yctx._findInCache('Gyro', func)
        if obj:
            return obj
        return YGyro(yctx, func)

    @classmethod
    def FirstGyro(cls) -> Union[YGyro, None]:
        """
        Starts the enumeration of gyroscopes currently accessible.
        Use the method YGyro.nextGyro() to iterate on
        next gyroscopes.

        @return a pointer to a YGyro object, corresponding to
                the first gyro currently online, or a None pointer
                if there are none.
        """
        return cls.FirstGyroInContext(YAPI)

    @classmethod
    def FirstGyroInContext(cls, yctx: YAPIContext) -> Union[YGyro, None]:
        """
        Starts the enumeration of gyroscopes currently accessible.
        Use the method YGyro.nextGyro() to iterate on
        next gyroscopes.

        @param yctx : a YAPI context.

        @return a pointer to a YGyro object, corresponding to
                the first gyro currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Gyro')
        if hwid:
            return cls.FindGyroInContext(yctx, hwid2str(hwid))
        return None

    def nextGyro(self) -> Union[YGyro, None]:
        """
        Continues the enumeration of gyroscopes started using yFirstGyro().
        Caution: You can't make any assumption about the returned gyroscopes order.
        If you want to find a specific a gyroscope, use Gyro.findGyro()
        and a hardwareID or a logical name.

        @return a pointer to a YGyro object, corresponding to
                a gyroscope currently online, or a None pointer
                if there are no more gyroscopes to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Gyro', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindGyroInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_bandwidth(self) -> int:
        """
        Returns the measure update frequency, measured in Hz.

        @return an integer corresponding to the measure update frequency, measured in Hz

        On failure, throws an exception or returns YGyro.BANDWIDTH_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("bandwidth")
        if json_val is None:
            return YGyro.BANDWIDTH_INVALID
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

    async def get_xValue(self) -> float:
        """
        Returns the angular velocity around the X axis of the device, as a floating point number.

        @return a floating point number corresponding to the angular velocity around the X axis of the
        device, as a floating point number

        On failure, throws an exception or returns YGyro.XVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("xValue")
        if json_val is None:
            return YGyro.XVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_yValue(self) -> float:
        """
        Returns the angular velocity around the Y axis of the device, as a floating point number.

        @return a floating point number corresponding to the angular velocity around the Y axis of the
        device, as a floating point number

        On failure, throws an exception or returns YGyro.YVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("yValue")
        if json_val is None:
            return YGyro.YVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_zValue(self) -> float:
        """
        Returns the angular velocity around the Z axis of the device, as a floating point number.

        @return a floating point number corresponding to the angular velocity around the Z axis of the
        device, as a floating point number

        On failure, throws an exception or returns YGyro.ZVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("zValue")
        if json_val is None:
            return YGyro.ZVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YGyroValueCallback) -> int:
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
        async def registerTimedReportCallback(self, callback: YGyroTimedReportCallback) -> int:
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

    async def _loadQuaternion(self) -> int:
        now_stamp: int
        age_ms: int
        now_stamp = int((YAPI.GetTickCount() & 0x7FFFFFFF))
        age_ms = ((now_stamp - self._qt_stamp) & 0x7FFFFFFF)
        if (age_ms >= 10) or (self._qt_stamp == 0):
            if await self.load(10) != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            if self._qt_stamp == 0:
                self._qt_w = YQt.FindQtInContext(self._yapi, "%s.qt1" % self._serial)
                self._qt_x = YQt.FindQtInContext(self._yapi, "%s.qt2" % self._serial)
                self._qt_y = YQt.FindQtInContext(self._yapi, "%s.qt3" % self._serial)
                self._qt_z = YQt.FindQtInContext(self._yapi, "%s.qt4" % self._serial)
            if await self._qt_w.load(9) != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            if await self._qt_x.load(9) != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            if await self._qt_y.load(9) != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            if await self._qt_z.load(9) != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            self._w = await self._qt_w.get_currentValue()
            self._x = await self._qt_x.get_currentValue()
            self._y = await self._qt_y.get_currentValue()
            self._z = await self._qt_z.get_currentValue()
            self._qt_stamp = now_stamp
        return YAPI.SUCCESS

    async def _loadAngles(self) -> int:
        sqw: float
        sqx: float
        sqy: float
        sqz: float
        norm: float
        delta: float

        if await self._loadQuaternion() != YAPI.SUCCESS:
            return YAPI.DEVICE_NOT_FOUND
        if self._angles_stamp != self._qt_stamp:
            sqw = self._w * self._w
            sqx = self._x * self._x
            sqy = self._y * self._y
            sqz = self._z * self._z
            norm = sqx + sqy + sqz + sqw
            delta = self._y * self._w - self._x * self._z
            if delta > 0.499 * norm:
                # singularity at north pole
                self._pitch = 90.0
                self._head  = round(2.0 * 1800.0/math.pi * math.atan2(self._x,-self._w)) / 10.0
            else:
                if delta < -0.499 * norm:
                    # singularity at south pole
                    self._pitch = -90.0
                    self._head  = round(-2.0 * 1800.0/math.pi * math.atan2(self._x,-self._w)) / 10.0
                else:
                    self._roll  = round(1800.0/math.pi * math.atan2(2.0 * (self._w * self._x + self._y * self._z),sqw - sqx - sqy + sqz)) / 10.0
                    self._pitch = round(1800.0/math.pi * math.asin(2.0 * delta / norm)) / 10.0
                    self._head  = round(1800.0/math.pi * math.atan2(2.0 * (self._x * self._y + self._z * self._w),sqw + sqx - sqy - sqz)) / 10.0
            self._angles_stamp = self._qt_stamp
        return YAPI.SUCCESS

    async def get_roll(self) -> float:
        """
        Returns the estimated roll angle, based on the integration of
        gyroscopic measures combined with acceleration and
        magnetic field measurements.
        The axis corresponding to the roll angle can be mapped to any
        of the device X, Y or Z physical directions using methods of
        the class YRefFrame.

        @return a floating-point number corresponding to roll angle
                in degrees, between -180 and +180.
        """
        await self._loadAngles()
        return self._roll

    async def get_pitch(self) -> float:
        """
        Returns the estimated pitch angle, based on the integration of
        gyroscopic measures combined with acceleration and
        magnetic field measurements.
        The axis corresponding to the pitch angle can be mapped to any
        of the device X, Y or Z physical directions using methods of
        the class YRefFrame.

        @return a floating-point number corresponding to pitch angle
                in degrees, between -90 and +90.
        """
        await self._loadAngles()
        return self._pitch

    async def get_heading(self) -> float:
        """
        Returns the estimated heading angle, based on the integration of
        gyroscopic measures combined with acceleration and
        magnetic field measurements.
        The axis corresponding to the heading can be mapped to any
        of the device X, Y or Z physical directions using methods of
        the class YRefFrame.

        @return a floating-point number corresponding to heading
                in degrees, between 0 and 360.
        """
        await self._loadAngles()
        return self._head

    async def get_quaternionW(self) -> float:
        """
        Returns the w component (real part) of the quaternion
        describing the device estimated orientation, based on the
        integration of gyroscopic measures combined with acceleration and
        magnetic field measurements.

        @return a floating-point number corresponding to the w
                component of the quaternion.
        """
        await self._loadQuaternion()
        return self._w

    async def get_quaternionX(self) -> float:
        """
        Returns the x component of the quaternion
        describing the device estimated orientation, based on the
        integration of gyroscopic measures combined with acceleration and
        magnetic field measurements. The x component is
        mostly correlated with rotations on the roll axis.

        @return a floating-point number corresponding to the x
                component of the quaternion.
        """
        await self._loadQuaternion()
        return self._x

    async def get_quaternionY(self) -> float:
        """
        Returns the y component of the quaternion
        describing the device estimated orientation, based on the
        integration of gyroscopic measures combined with acceleration and
        magnetic field measurements. The y component is
        mostly correlated with rotations on the pitch axis.

        @return a floating-point number corresponding to the y
                component of the quaternion.
        """
        await self._loadQuaternion()
        return self._y

    async def get_quaternionZ(self) -> float:
        """
        Returns the x component of the quaternion
        describing the device estimated orientation, based on the
        integration of gyroscopic measures combined with acceleration and
        magnetic field measurements. The x component is
        mostly correlated with changes of heading.

        @return a floating-point number corresponding to the z
                component of the quaternion.
        """
        await self._loadQuaternion()
        return self._z

    async def registerQuaternionCallback(self, callback: YQuatCallback) -> int:
        """
        Registers a callback function that will be invoked each time that the estimated
        device orientation has changed. The call frequency is typically around 95Hz during a move.
        The callback is invoked only during the execution of ySleep or yHandleEvents.
        This provides control over the time when the callback is triggered.
        For good responsiveness, remember to call one of these two functions periodically.
        To unregister a callback, pass a None pointer as argument.

        @param callback : the callback function to invoke, or a None pointer.
                The callback function should take five arguments:
                the YGyro object of the turning device, and the floating
                point values of the four components w, x, y and z
                (as floating-point numbers).
        @noreturn
        """
        self._quatCallback = callback
        if callback:
            if await self._loadQuaternion() != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            self._qt_w.set_userData(self)
            self._qt_x.set_userData(self)
            self._qt_y.set_userData(self)
            self._qt_z.set_userData(self)
            await self._qt_w.registerValueCallback(yInternalGyroCallback)
            await self._qt_x.registerValueCallback(yInternalGyroCallback)
            await self._qt_y.registerValueCallback(yInternalGyroCallback)
            await self._qt_z.registerValueCallback(yInternalGyroCallback)
        else:
            if not self._anglesCallback:
                await self._qt_w.registerValueCallback(None)
                await self._qt_x.registerValueCallback(None)
                await self._qt_y.registerValueCallback(None)
                await self._qt_z.registerValueCallback(None)
        return 0

    async def registerAnglesCallback(self, callback: YAnglesCallback) -> int:
        """
        Registers a callback function that will be invoked each time that the estimated
        device orientation has changed. The call frequency is typically around 95Hz during a move.
        The callback is invoked only during the execution of ySleep or yHandleEvents.
        This provides control over the time when the callback is triggered.
        For good responsiveness, remember to call one of these two functions periodically.
        To unregister a callback, pass a None pointer as argument.

        @param callback : the callback function to invoke, or a None pointer.
                The callback function should take four arguments:
                the YGyro object of the turning device, and the floating
                point values of the three angles roll, pitch and heading
                in degrees (as floating-point numbers).
        @noreturn
        """
        self._anglesCallback = callback
        if callback:
            if await self._loadQuaternion() != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
            self._qt_w.set_userData(self)
            self._qt_x.set_userData(self)
            self._qt_y.set_userData(self)
            self._qt_z.set_userData(self)
            await self._qt_w.registerValueCallback(yInternalGyroCallback)
            await self._qt_x.registerValueCallback(yInternalGyroCallback)
            await self._qt_y.registerValueCallback(yInternalGyroCallback)
            await self._qt_z.registerValueCallback(yInternalGyroCallback)
        else:
            if not self._quatCallback:
                await self._qt_w.registerValueCallback(None)
                await self._qt_x.registerValueCallback(None)
                await self._qt_y.registerValueCallback(None)
                await self._qt_z.registerValueCallback(None)
        return 0

    async def _invokeGyroCallbacks(self, qtIndex: int, qtValue: float) -> int:
        if qtIndex - 1 == 0:
            self._w = qtValue
        elif qtIndex - 1 == 1:
            self._x = qtValue
        elif qtIndex - 1 == 2:
            self._y = qtValue
        elif qtIndex - 1 == 3:
            self._z = qtValue
        if qtIndex < 4:
            return 0
        self._qt_stamp = int((YAPI.GetTickCount() & 0x7FFFFFFF))
        if self._quatCallback:
            try:
                retval = self._quatCallback(self, self._w, self._x, self._y, self._z)
                if retval is not None: await retval
            # noinspection PyBroadException
            except Exception as e:
                print('Exception in %s.yQuaternionCallback:' % type(self).__name__, type(e).__name__, e)
        if self._anglesCallback:
            await self._loadAngles()
            try:
                retval = self._anglesCallback(self, self._roll, self._pitch, self._head)
                if retval is not None: await retval
            # noinspection PyBroadException
            except Exception as e:
                print('Exception in %s.yAnglesCallback:' % type(self).__name__, type(e).__name__, e)
        return 0

    # --- (end of generated code: YGyro implementation)
