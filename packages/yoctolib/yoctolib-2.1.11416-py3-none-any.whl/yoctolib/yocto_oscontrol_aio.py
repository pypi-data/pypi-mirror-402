# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YOsControl
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
Yoctopuce library: Asyncio implementation of YOsControl
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YOsControl
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction
)

# --- (YOsControl class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YOsControlValueCallback = Union[Callable[['YOsControl', str], Any], None]
    except TypeError:
        YOsControlValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YOsControl(YFunction):
    """
    The YOScontrol class provides some control over the operating system running a VirtualHub.
    YOsControl is available on VirtualHub software only. This feature must be activated at the VirtualHub
    start up with -o option.

    """
    # --- (end of YOsControl class start)
    if not _IS_MICROPYTHON:
        # --- (YOsControl return codes)
        SHUTDOWNCOUNTDOWN_INVALID: Final[int] = YAPI.INVALID_INT
        # --- (end of YOsControl return codes)

    # --- (YOsControl attributes declaration)
    _valueCallback: YOsControlValueCallback
    # --- (end of YOsControl attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'OsControl', func)
        # --- (YOsControl constructor)
        # --- (end of YOsControl constructor)

    # --- (YOsControl implementation)
    @classmethod
    def FindOsControl(cls, func: str) -> YOsControl:
        """
        Retrieves OS control for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the OS control is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YOsControl.isOnline() to test if the OS control is
        indeed online at a given time. In case of ambiguity when looking for
        OS control by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the OS control, for instance
                MyDevice.osControl.

        @return a YOsControl object allowing you to drive the OS control.
        """
        return cls.FindOsControlInContext(YAPI, func)

    @classmethod
    def FindOsControlInContext(cls, yctx: YAPIContext, func: str) -> YOsControl:
        """
        Retrieves OS control for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the OS control is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YOsControl.isOnline() to test if the OS control is
        indeed online at a given time. In case of ambiguity when looking for
        OS control by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the OS control, for instance
                MyDevice.osControl.

        @return a YOsControl object allowing you to drive the OS control.
        """
        obj: Union[YOsControl, None] = yctx._findInCache('OsControl', func)
        if obj:
            return obj
        return YOsControl(yctx, func)

    @classmethod
    def FirstOsControl(cls) -> Union[YOsControl, None]:
        """
        Starts the enumeration of OS control currently accessible.
        Use the method YOsControl.nextOsControl() to iterate on
        next OS control.

        @return a pointer to a YOsControl object, corresponding to
                the first OS control currently online, or a None pointer
                if there are none.
        """
        return cls.FirstOsControlInContext(YAPI)

    @classmethod
    def FirstOsControlInContext(cls, yctx: YAPIContext) -> Union[YOsControl, None]:
        """
        Starts the enumeration of OS control currently accessible.
        Use the method YOsControl.nextOsControl() to iterate on
        next OS control.

        @param yctx : a YAPI context.

        @return a pointer to a YOsControl object, corresponding to
                the first OS control currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('OsControl')
        if hwid:
            return cls.FindOsControlInContext(yctx, hwid2str(hwid))
        return None

    def nextOsControl(self) -> Union[YOsControl, None]:
        """
        Continues the enumeration of OS control started using yFirstOsControl().
        Caution: You can't make any assumption about the returned OS control order.
        If you want to find a specific OS control, use OsControl.findOsControl()
        and a hardwareID or a logical name.

        @return a pointer to a YOsControl object, corresponding to
                OS control currently online, or a None pointer
                if there are no more OS control to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('OsControl', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindOsControlInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_shutdownCountdown(self) -> int:
        """
        Returns the remaining number of seconds before the OS shutdown, or zero when no
        shutdown has been scheduled.

        @return an integer corresponding to the remaining number of seconds before the OS shutdown, or zero when no
                shutdown has been scheduled

        On failure, throws an exception or returns YOsControl.SHUTDOWNCOUNTDOWN_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("shutdownCountdown")
        if json_val is None:
            return YOsControl.SHUTDOWNCOUNTDOWN_INVALID
        return json_val

    async def set_shutdownCountdown(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("shutdownCountdown", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YOsControlValueCallback) -> int:
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

    async def shutdown(self, secBeforeShutDown: int) -> int:
        """
        Schedules an OS shutdown after a given number of seconds.

        @param secBeforeShutDown : number of seconds before shutdown

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_shutdownCountdown(secBeforeShutDown)

    async def reboot(self, secBeforeReboot: int) -> int:
        """
        Schedules an OS reboot after a given number of seconds.

        @param secBeforeReboot : number of seconds before reboot

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_shutdownCountdown(0 - secBeforeReboot)

    # --- (end of YOsControl implementation)

