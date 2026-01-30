# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YAltitude
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
Yoctopuce library: High-level API for YAltitude
version: PATCH_WITH_VERSION
requires: yocto_altitude_aio
requires: yocto_api
provides: YAltitude
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

from .yocto_altitude_aio import YAltitude as YAltitude_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YAltitude class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YAltitudeValueCallback = Union[Callable[['YAltitude', str], Any], None]
        YAltitudeTimedReportCallback = Union[Callable[['YAltitude', YMeasure], Any], None]
    except TypeError:
        YAltitudeValueCallback = Union[Callable, Awaitable]
        YAltitudeTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YAltitude(YSensor):
    """
    The YAltitude class allows you to read and configure Yoctopuce altimeters.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the ability to configure the barometric pressure adjusted to
    sea level (QNH) for barometric sensors.

    """
    _aio: YAltitude_aio
    # --- (end of YAltitude class start)
    if not _IS_MICROPYTHON:
        # --- (YAltitude return codes)
        QNH_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        TECHNOLOGY_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of YAltitude return codes)


    # --- (YAltitude implementation)

    @classmethod
    def FindAltitude(cls, func: str) -> YAltitude:
        """
        Retrieves an altimeter for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the altimeter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAltitude.isOnline() to test if the altimeter is
        indeed online at a given time. In case of ambiguity when looking for
        an altimeter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the altimeter, for instance
                YALTIMK2.altitude.

        @return a YAltitude object allowing you to drive the altimeter.
        """
        return cls._proxy(cls, YAltitude_aio.FindAltitudeInContext(YAPI_aio, func))

    @classmethod
    def FindAltitudeInContext(cls, yctx: YAPIContext, func: str) -> YAltitude:
        """
        Retrieves an altimeter for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the altimeter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAltitude.isOnline() to test if the altimeter is
        indeed online at a given time. In case of ambiguity when looking for
        an altimeter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the altimeter, for instance
                YALTIMK2.altitude.

        @return a YAltitude object allowing you to drive the altimeter.
        """
        return cls._proxy(cls, YAltitude_aio.FindAltitudeInContext(yctx._aio, func))

    @classmethod
    def FirstAltitude(cls) -> Union[YAltitude, None]:
        """
        Starts the enumeration of altimeters currently accessible.
        Use the method YAltitude.nextAltitude() to iterate on
        next altimeters.

        @return a pointer to a YAltitude object, corresponding to
                the first altimeter currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YAltitude_aio.FirstAltitudeInContext(YAPI_aio))

    @classmethod
    def FirstAltitudeInContext(cls, yctx: YAPIContext) -> Union[YAltitude, None]:
        """
        Starts the enumeration of altimeters currently accessible.
        Use the method YAltitude.nextAltitude() to iterate on
        next altimeters.

        @param yctx : a YAPI context.

        @return a pointer to a YAltitude object, corresponding to
                the first altimeter currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YAltitude_aio.FirstAltitudeInContext(yctx._aio))

    def nextAltitude(self) -> Union[YAltitude, None]:
        """
        Continues the enumeration of altimeters started using yFirstAltitude().
        Caution: You can't make any assumption about the returned altimeters order.
        If you want to find a specific an altimeter, use Altitude.findAltitude()
        and a hardwareID or a logical name.

        @return a pointer to a YAltitude object, corresponding to
                an altimeter currently online, or a None pointer
                if there are no more altimeters to enumerate.
        """
        return self._proxy(type(self), self._aio.nextAltitude())

    if not _DYNAMIC_HELPERS:
        def set_currentValue(self, newval: float) -> int:
            """
            Changes the current estimated altitude. This allows one to compensate for
            ambient pressure variations and to work in relative mode.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the current estimated altitude

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_currentValue(newval))

    if not _DYNAMIC_HELPERS:
        def set_qnh(self, newval: float) -> int:
            """
            Changes the barometric pressure adjusted to sea level used to compute
            the altitude (QNH). This enables you to compensate for atmospheric pressure
            changes due to weather conditions. Applicable to barometric altimeters only.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the barometric pressure adjusted to sea
            level used to compute
                    the altitude (QNH)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_qnh(newval))

    if not _DYNAMIC_HELPERS:
        def get_qnh(self) -> float:
            """
            Returns the barometric pressure adjusted to sea level used to compute
            the altitude (QNH). Applicable to barometric altimeters only.

            @return a floating point number corresponding to the barometric pressure adjusted to sea level used to compute
                    the altitude (QNH)

            On failure, throws an exception or returns YAltitude.QNH_INVALID.
            """
            return self._run(self._aio.get_qnh())

    if not _DYNAMIC_HELPERS:
        def get_technology(self) -> str:
            """
            Returns the technology used by the sesnor to compute
            altitude. Possibles values are  "barometric" and "gps"

            @return a string corresponding to the technology used by the sesnor to compute
                    altitude

            On failure, throws an exception or returns YAltitude.TECHNOLOGY_INVALID.
            """
            return self._run(self._aio.get_technology())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YAltitudeValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YAltitudeTimedReportCallback) -> int:
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

    # --- (end of YAltitude implementation)

