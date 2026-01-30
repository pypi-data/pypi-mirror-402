# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_gyro.py 69442 2025-10-16 08:53:14Z mvuilleu $
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
Yoctopuce library: High-level API for YGyro
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_display_aio
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True  # noqa
    _DYNAMIC_HELPERS: Final[bool] = True  # noqa

from .yocto_gyro_aio import (
    YGyro as YGyro_aio,
    YQt as YQt_aio
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
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
    _aio: YQt_aio
    # --- (end of generated code: YQt class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YQt return codes)
        pass
        # --- (end of generated code: YQt return codes)

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
        return cls._proxy(cls, YQt_aio.FindQtInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YQt_aio.FindQtInContext(yctx._aio, func))

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
        return cls._proxy(cls, YQt_aio.FirstQtInContext(YAPI_aio))

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
        return cls._proxy(cls, YQt_aio.FirstQtInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextQt())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YQtValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YQtTimedReportCallback) -> int:
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

    # --- (end of generated code: YQt implementation)

if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YQuatCallback = Union[Callable[['YGyro', float, float, float, float], Awaitable[None]], None]
        YAnglesCallback = Union[Callable[['YGyro', float, float, float], Awaitable[None]], None]
    except TypeError:
        YQuatCallback = Union[Callable, Awaitable]
        YAnglesCallback = Union[Callable, Awaitable]

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
    _aio: YGyro_aio
    # --- (end of generated code: YGyro class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YGyro return codes)
        BANDWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        XVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        YVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ZVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        # --- (end of generated code: YGyro return codes)

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
        return cls._proxy(cls, YGyro_aio.FindGyroInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YGyro_aio.FindGyroInContext(yctx._aio, func))

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
        return cls._proxy(cls, YGyro_aio.FirstGyroInContext(YAPI_aio))

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
        return cls._proxy(cls, YGyro_aio.FirstGyroInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextGyro())

    if not _DYNAMIC_HELPERS:
        def get_bandwidth(self) -> int:
            """
            Returns the measure update frequency, measured in Hz.

            @return an integer corresponding to the measure update frequency, measured in Hz

            On failure, throws an exception or returns YGyro.BANDWIDTH_INVALID.
            """
            return self._run(self._aio.get_bandwidth())

    if not _DYNAMIC_HELPERS:
        def set_bandwidth(self, newval: int) -> int:
            """
            Changes the measure update frequency, measured in Hz. When the
            frequency is lower, the device performs averaging.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the measure update frequency, measured in Hz

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_bandwidth(newval))

    if not _DYNAMIC_HELPERS:
        def get_xValue(self) -> float:
            """
            Returns the angular velocity around the X axis of the device, as a floating point number.

            @return a floating point number corresponding to the angular velocity around the X axis of the
            device, as a floating point number

            On failure, throws an exception or returns YGyro.XVALUE_INVALID.
            """
            return self._run(self._aio.get_xValue())

    if not _DYNAMIC_HELPERS:
        def get_yValue(self) -> float:
            """
            Returns the angular velocity around the Y axis of the device, as a floating point number.

            @return a floating point number corresponding to the angular velocity around the Y axis of the
            device, as a floating point number

            On failure, throws an exception or returns YGyro.YVALUE_INVALID.
            """
            return self._run(self._aio.get_yValue())

    if not _DYNAMIC_HELPERS:
        def get_zValue(self) -> float:
            """
            Returns the angular velocity around the Z axis of the device, as a floating point number.

            @return a floating point number corresponding to the angular velocity around the Z axis of the
            device, as a floating point number

            On failure, throws an exception or returns YGyro.ZVALUE_INVALID.
            """
            return self._run(self._aio.get_zValue())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YGyroValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YGyroTimedReportCallback) -> int:
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
        def get_roll(self) -> float:
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
            return self._run(self._aio.get_roll())

    if not _DYNAMIC_HELPERS:
        def get_pitch(self) -> float:
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
            return self._run(self._aio.get_pitch())

    if not _DYNAMIC_HELPERS:
        def get_heading(self) -> float:
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
            return self._run(self._aio.get_heading())

    if not _DYNAMIC_HELPERS:
        def get_quaternionW(self) -> float:
            """
            Returns the w component (real part) of the quaternion
            describing the device estimated orientation, based on the
            integration of gyroscopic measures combined with acceleration and
            magnetic field measurements.

            @return a floating-point number corresponding to the w
                    component of the quaternion.
            """
            return self._run(self._aio.get_quaternionW())

    if not _DYNAMIC_HELPERS:
        def get_quaternionX(self) -> float:
            """
            Returns the x component of the quaternion
            describing the device estimated orientation, based on the
            integration of gyroscopic measures combined with acceleration and
            magnetic field measurements. The x component is
            mostly correlated with rotations on the roll axis.

            @return a floating-point number corresponding to the x
                    component of the quaternion.
            """
            return self._run(self._aio.get_quaternionX())

    if not _DYNAMIC_HELPERS:
        def get_quaternionY(self) -> float:
            """
            Returns the y component of the quaternion
            describing the device estimated orientation, based on the
            integration of gyroscopic measures combined with acceleration and
            magnetic field measurements. The y component is
            mostly correlated with rotations on the pitch axis.

            @return a floating-point number corresponding to the y
                    component of the quaternion.
            """
            return self._run(self._aio.get_quaternionY())

    if not _DYNAMIC_HELPERS:
        def get_quaternionZ(self) -> float:
            """
            Returns the x component of the quaternion
            describing the device estimated orientation, based on the
            integration of gyroscopic measures combined with acceleration and
            magnetic field measurements. The x component is
            mostly correlated with changes of heading.

            @return a floating-point number corresponding to the z
                    component of the quaternion.
            """
            return self._run(self._aio.get_quaternionZ())

    def registerQuaternionCallback(self, callback: YQuatCallback) -> int:
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
        return self._run(self._aio.registerQuaternionCallback(self._proxyCb(type(self), callback)))

    def registerAnglesCallback(self, callback: YAnglesCallback) -> int:
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
        return self._run(self._aio.registerAnglesCallback(self._proxyCb(type(self), callback)))

    # --- (end of generated code: YGyro implementation)

