# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YGroundSpeed
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
Yoctopuce library: High-level API for YGroundSpeed
version: PATCH_WITH_VERSION
requires: yocto_groundspeed_aio
requires: yocto_api
provides: YGroundSpeed
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union
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

from .yocto_groundspeed_aio import YGroundSpeed as YGroundSpeed_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YGroundSpeed class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YGroundSpeedValueCallback = Union[Callable[['YGroundSpeed', str], Any], None]
        YGroundSpeedTimedReportCallback = Union[Callable[['YGroundSpeed', YMeasure], Any], None]
    except TypeError:
        YGroundSpeedValueCallback = Union[Callable, Awaitable]
        YGroundSpeedTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YGroundSpeed(YSensor):
    """
    The YGroundSpeed class allows you to read and configure Yoctopuce ground speed sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    _aio: YGroundSpeed_aio
    # --- (end of YGroundSpeed class start)
    if not _IS_MICROPYTHON:
        # --- (YGroundSpeed return codes)
        pass
        # --- (end of YGroundSpeed return codes)


    # --- (YGroundSpeed implementation)

    @classmethod
    def FindGroundSpeed(cls, func: str) -> YGroundSpeed:
        """
        Retrieves a ground speed sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the ground speed sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGroundSpeed.isOnline() to test if the ground speed sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a ground speed sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the ground speed sensor, for instance
                YGNSSMK2.groundSpeed.

        @return a YGroundSpeed object allowing you to drive the ground speed sensor.
        """
        return cls._proxy(cls, YGroundSpeed_aio.FindGroundSpeedInContext(YAPI_aio, func))

    @classmethod
    def FindGroundSpeedInContext(cls, yctx: YAPIContext, func: str) -> YGroundSpeed:
        """
        Retrieves a ground speed sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the ground speed sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGroundSpeed.isOnline() to test if the ground speed sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a ground speed sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the ground speed sensor, for instance
                YGNSSMK2.groundSpeed.

        @return a YGroundSpeed object allowing you to drive the ground speed sensor.
        """
        return cls._proxy(cls, YGroundSpeed_aio.FindGroundSpeedInContext(yctx._aio, func))

    @classmethod
    def FirstGroundSpeed(cls) -> Union[YGroundSpeed, None]:
        """
        Starts the enumeration of ground speed sensors currently accessible.
        Use the method YGroundSpeed.nextGroundSpeed() to iterate on
        next ground speed sensors.

        @return a pointer to a YGroundSpeed object, corresponding to
                the first ground speed sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YGroundSpeed_aio.FirstGroundSpeedInContext(YAPI_aio))

    @classmethod
    def FirstGroundSpeedInContext(cls, yctx: YAPIContext) -> Union[YGroundSpeed, None]:
        """
        Starts the enumeration of ground speed sensors currently accessible.
        Use the method YGroundSpeed.nextGroundSpeed() to iterate on
        next ground speed sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YGroundSpeed object, corresponding to
                the first ground speed sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YGroundSpeed_aio.FirstGroundSpeedInContext(yctx._aio))

    def nextGroundSpeed(self) -> Union[YGroundSpeed, None]:
        """
        Continues the enumeration of ground speed sensors started using yFirstGroundSpeed().
        Caution: You can't make any assumption about the returned ground speed sensors order.
        If you want to find a specific a ground speed sensor, use GroundSpeed.findGroundSpeed()
        and a hardwareID or a logical name.

        @return a pointer to a YGroundSpeed object, corresponding to
                a ground speed sensor currently online, or a None pointer
                if there are no more ground speed sensors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextGroundSpeed())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YGroundSpeedValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YGroundSpeedTimedReportCallback) -> int:
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

    # --- (end of YGroundSpeed implementation)

