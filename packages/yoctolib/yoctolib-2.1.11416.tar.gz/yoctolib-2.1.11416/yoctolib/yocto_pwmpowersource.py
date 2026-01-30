# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YPwmPowerSource
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
Yoctopuce library: High-level API for YPwmPowerSource
version: PATCH_WITH_VERSION
requires: yocto_pwmpowersource_aio
requires: yocto_api
provides: YPwmPowerSource
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

from .yocto_pwmpowersource_aio import YPwmPowerSource as YPwmPowerSource_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YPwmPowerSource class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPwmPowerSourceValueCallback = Union[Callable[['YPwmPowerSource', str], Any], None]
    except TypeError:
        YPwmPowerSourceValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPwmPowerSource(YFunction):
    """
    The YPwmPowerSource class allows you to configure
    the voltage source used by all PWM outputs on the same device.

    """
    _aio: YPwmPowerSource_aio
    # --- (end of YPwmPowerSource class start)
    if not _IS_MICROPYTHON:
        # --- (YPwmPowerSource return codes)
        POWERMODE_USB_5V: Final[int] = 0
        POWERMODE_USB_3V: Final[int] = 1
        POWERMODE_EXT_V: Final[int] = 2
        POWERMODE_OPNDRN: Final[int] = 3
        POWERMODE_INVALID: Final[int] = -1
        # --- (end of YPwmPowerSource return codes)


    # --- (YPwmPowerSource implementation)

    @classmethod
    def FindPwmPowerSource(cls, func: str) -> YPwmPowerSource:
        """
        Retrieves a PWM generator power source for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the PWM generator power source is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPwmPowerSource.isOnline() to test if the PWM generator power source is
        indeed online at a given time. In case of ambiguity when looking for
        a PWM generator power source by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the PWM generator power source, for instance
                YPWMTX01.pwmPowerSource.

        @return a YPwmPowerSource object allowing you to drive the PWM generator power source.
        """
        return cls._proxy(cls, YPwmPowerSource_aio.FindPwmPowerSourceInContext(YAPI_aio, func))

    @classmethod
    def FindPwmPowerSourceInContext(cls, yctx: YAPIContext, func: str) -> YPwmPowerSource:
        """
        Retrieves a PWM generator power source for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the PWM generator power source is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPwmPowerSource.isOnline() to test if the PWM generator power source is
        indeed online at a given time. In case of ambiguity when looking for
        a PWM generator power source by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the PWM generator power source, for instance
                YPWMTX01.pwmPowerSource.

        @return a YPwmPowerSource object allowing you to drive the PWM generator power source.
        """
        return cls._proxy(cls, YPwmPowerSource_aio.FindPwmPowerSourceInContext(yctx._aio, func))

    @classmethod
    def FirstPwmPowerSource(cls) -> Union[YPwmPowerSource, None]:
        """
        Starts the enumeration of PWM generator power sources currently accessible.
        Use the method YPwmPowerSource.nextPwmPowerSource() to iterate on
        next PWM generator power sources.

        @return a pointer to a YPwmPowerSource object, corresponding to
                the first PWM generator power source currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YPwmPowerSource_aio.FirstPwmPowerSourceInContext(YAPI_aio))

    @classmethod
    def FirstPwmPowerSourceInContext(cls, yctx: YAPIContext) -> Union[YPwmPowerSource, None]:
        """
        Starts the enumeration of PWM generator power sources currently accessible.
        Use the method YPwmPowerSource.nextPwmPowerSource() to iterate on
        next PWM generator power sources.

        @param yctx : a YAPI context.

        @return a pointer to a YPwmPowerSource object, corresponding to
                the first PWM generator power source currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YPwmPowerSource_aio.FirstPwmPowerSourceInContext(yctx._aio))

    def nextPwmPowerSource(self) -> Union[YPwmPowerSource, None]:
        """
        Continues the enumeration of PWM generator power sources started using yFirstPwmPowerSource().
        Caution: You can't make any assumption about the returned PWM generator power sources order.
        If you want to find a specific a PWM generator power source, use PwmPowerSource.findPwmPowerSource()
        and a hardwareID or a logical name.

        @return a pointer to a YPwmPowerSource object, corresponding to
                a PWM generator power source currently online, or a None pointer
                if there are no more PWM generator power sources to enumerate.
        """
        return self._proxy(type(self), self._aio.nextPwmPowerSource())

    if not _DYNAMIC_HELPERS:
        def get_powerMode(self) -> int:
            """
            Returns the selected power source for the PWM on the same device.

            @return a value among YPwmPowerSource.POWERMODE_USB_5V, YPwmPowerSource.POWERMODE_USB_3V,
            YPwmPowerSource.POWERMODE_EXT_V and YPwmPowerSource.POWERMODE_OPNDRN corresponding to the selected
            power source for the PWM on the same device

            On failure, throws an exception or returns YPwmPowerSource.POWERMODE_INVALID.
            """
            return self._run(self._aio.get_powerMode())

    if not _DYNAMIC_HELPERS:
        def set_powerMode(self, newval: int) -> int:
            """
            Changes  the PWM power source. PWM can use isolated 5V from USB, isolated 3V from USB or
            voltage from an external power source. The PWM can also work in open drain  mode. In that
            mode, the PWM actively pulls the line down.
            Warning: this setting is common to all PWM on the same device. If you change that parameter,
            all PWM located on the same device are  affected.
            If you want the change to be kept after a device reboot, make sure  to call the matching
            module saveToFlash().

            @param newval : a value among YPwmPowerSource.POWERMODE_USB_5V, YPwmPowerSource.POWERMODE_USB_3V,
            YPwmPowerSource.POWERMODE_EXT_V and YPwmPowerSource.POWERMODE_OPNDRN corresponding to  the PWM power source

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_powerMode(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YPwmPowerSourceValueCallback) -> int:
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

    # --- (end of YPwmPowerSource implementation)

