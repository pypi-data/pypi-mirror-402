# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YDualPower
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
Yoctopuce library: High-level API for YDualPower
version: PATCH_WITH_VERSION
requires: yocto_dualpower_aio
requires: yocto_api
provides: YDualPower
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

from .yocto_dualpower_aio import YDualPower as YDualPower_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YDualPower class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YDualPowerValueCallback = Union[Callable[['YDualPower', str], Any], None]
    except TypeError:
        YDualPowerValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YDualPower(YFunction):
    """
    The YDualPower class allows you to control
    the power source to use for module functions that require high current.
    The module can also automatically disconnect the external power
    when a voltage drop is observed on the external power source
    (external battery running out of power).

    """
    _aio: YDualPower_aio
    # --- (end of YDualPower class start)
    if not _IS_MICROPYTHON:
        # --- (YDualPower return codes)
        EXTVOLTAGE_INVALID: Final[int] = YAPI.INVALID_UINT
        POWERSTATE_OFF: Final[int] = 0
        POWERSTATE_FROM_USB: Final[int] = 1
        POWERSTATE_FROM_EXT: Final[int] = 2
        POWERSTATE_INVALID: Final[int] = -1
        POWERCONTROL_AUTO: Final[int] = 0
        POWERCONTROL_FROM_USB: Final[int] = 1
        POWERCONTROL_FROM_EXT: Final[int] = 2
        POWERCONTROL_OFF: Final[int] = 3
        POWERCONTROL_INVALID: Final[int] = -1
        # --- (end of YDualPower return codes)


    # --- (YDualPower implementation)

    @classmethod
    def FindDualPower(cls, func: str) -> YDualPower:
        """
        Retrieves a dual power switch for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the dual power switch is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDualPower.isOnline() to test if the dual power switch is
        indeed online at a given time. In case of ambiguity when looking for
        a dual power switch by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the dual power switch, for instance
                SERVORC1.dualPower.

        @return a YDualPower object allowing you to drive the dual power switch.
        """
        return cls._proxy(cls, YDualPower_aio.FindDualPowerInContext(YAPI_aio, func))

    @classmethod
    def FindDualPowerInContext(cls, yctx: YAPIContext, func: str) -> YDualPower:
        """
        Retrieves a dual power switch for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the dual power switch is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDualPower.isOnline() to test if the dual power switch is
        indeed online at a given time. In case of ambiguity when looking for
        a dual power switch by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the dual power switch, for instance
                SERVORC1.dualPower.

        @return a YDualPower object allowing you to drive the dual power switch.
        """
        return cls._proxy(cls, YDualPower_aio.FindDualPowerInContext(yctx._aio, func))

    @classmethod
    def FirstDualPower(cls) -> Union[YDualPower, None]:
        """
        Starts the enumeration of dual power switches currently accessible.
        Use the method YDualPower.nextDualPower() to iterate on
        next dual power switches.

        @return a pointer to a YDualPower object, corresponding to
                the first dual power switch currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDualPower_aio.FirstDualPowerInContext(YAPI_aio))

    @classmethod
    def FirstDualPowerInContext(cls, yctx: YAPIContext) -> Union[YDualPower, None]:
        """
        Starts the enumeration of dual power switches currently accessible.
        Use the method YDualPower.nextDualPower() to iterate on
        next dual power switches.

        @param yctx : a YAPI context.

        @return a pointer to a YDualPower object, corresponding to
                the first dual power switch currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDualPower_aio.FirstDualPowerInContext(yctx._aio))

    def nextDualPower(self) -> Union[YDualPower, None]:
        """
        Continues the enumeration of dual power switches started using yFirstDualPower().
        Caution: You can't make any assumption about the returned dual power switches order.
        If you want to find a specific a dual power switch, use DualPower.findDualPower()
        and a hardwareID or a logical name.

        @return a pointer to a YDualPower object, corresponding to
                a dual power switch currently online, or a None pointer
                if there are no more dual power switches to enumerate.
        """
        return self._proxy(type(self), self._aio.nextDualPower())

    if not _DYNAMIC_HELPERS:
        def get_powerState(self) -> int:
            """
            Returns the current power source for module functions that require lots of current.

            @return a value among YDualPower.POWERSTATE_OFF, YDualPower.POWERSTATE_FROM_USB and
            YDualPower.POWERSTATE_FROM_EXT corresponding to the current power source for module functions that
            require lots of current

            On failure, throws an exception or returns YDualPower.POWERSTATE_INVALID.
            """
            return self._run(self._aio.get_powerState())

    if not _DYNAMIC_HELPERS:
        def get_powerControl(self) -> int:
            """
            Returns the selected power source for module functions that require lots of current.

            @return a value among YDualPower.POWERCONTROL_AUTO, YDualPower.POWERCONTROL_FROM_USB,
            YDualPower.POWERCONTROL_FROM_EXT and YDualPower.POWERCONTROL_OFF corresponding to the selected
            power source for module functions that require lots of current

            On failure, throws an exception or returns YDualPower.POWERCONTROL_INVALID.
            """
            return self._run(self._aio.get_powerControl())

    if not _DYNAMIC_HELPERS:
        def set_powerControl(self, newval: int) -> int:
            """
            Changes the selected power source for module functions that require lots of current.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : a value among YDualPower.POWERCONTROL_AUTO, YDualPower.POWERCONTROL_FROM_USB,
            YDualPower.POWERCONTROL_FROM_EXT and YDualPower.POWERCONTROL_OFF corresponding to the selected
            power source for module functions that require lots of current

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_powerControl(newval))

    if not _DYNAMIC_HELPERS:
        def get_extVoltage(self) -> int:
            """
            Returns the measured voltage on the external power source, in millivolts.

            @return an integer corresponding to the measured voltage on the external power source, in millivolts

            On failure, throws an exception or returns YDualPower.EXTVOLTAGE_INVALID.
            """
            return self._run(self._aio.get_extVoltage())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YDualPowerValueCallback) -> int:
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

    # --- (end of YDualPower implementation)

