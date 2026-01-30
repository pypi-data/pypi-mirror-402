# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YPowerSupply
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
Yoctopuce library: High-level API for YPowerSupply
version: PATCH_WITH_VERSION
requires: yocto_powersupply_aio
requires: yocto_api
provides: YPowerSupply
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

from .yocto_powersupply_aio import YPowerSupply as YPowerSupply_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YPowerSupply class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPowerSupplyValueCallback = Union[Callable[['YPowerSupply', str], Any], None]
    except TypeError:
        YPowerSupplyValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPowerSupply(YFunction):
    """
    The YPowerSupply class allows you to drive a Yoctopuce power supply.
    It can be use to change the voltage and current limits, and to enable/disable
    the output.

    """
    _aio: YPowerSupply_aio
    # --- (end of YPowerSupply class start)
    if not _IS_MICROPYTHON:
        # --- (YPowerSupply return codes)
        VOLTAGELIMIT_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CURRENTLIMIT_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        MEASUREDVOLTAGE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        MEASUREDCURRENT_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        INPUTVOLTAGE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        VOLTAGETRANSITION_INVALID: Final[str] = YAPI.INVALID_STRING
        VOLTAGELIMITATSTARTUP_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CURRENTLIMITATSTARTUP_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        POWEROUTPUT_OFF: Final[int] = 0
        POWEROUTPUT_ON: Final[int] = 1
        POWEROUTPUT_INVALID: Final[int] = -1
        POWEROUTPUTATSTARTUP_OFF: Final[int] = 0
        POWEROUTPUTATSTARTUP_ON: Final[int] = 1
        POWEROUTPUTATSTARTUP_INVALID: Final[int] = -1
        # --- (end of YPowerSupply return codes)


    # --- (YPowerSupply implementation)

    @classmethod
    def FindPowerSupply(cls, func: str) -> YPowerSupply:
        """
        Retrieves a regulated power supply for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the regulated power supply is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPowerSupply.isOnline() to test if the regulated power supply is
        indeed online at a given time. In case of ambiguity when looking for
        a regulated power supply by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the regulated power supply, for instance
                MyDevice.powerSupply.

        @return a YPowerSupply object allowing you to drive the regulated power supply.
        """
        return cls._proxy(cls, YPowerSupply_aio.FindPowerSupplyInContext(YAPI_aio, func))

    @classmethod
    def FindPowerSupplyInContext(cls, yctx: YAPIContext, func: str) -> YPowerSupply:
        """
        Retrieves a regulated power supply for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the regulated power supply is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPowerSupply.isOnline() to test if the regulated power supply is
        indeed online at a given time. In case of ambiguity when looking for
        a regulated power supply by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the regulated power supply, for instance
                MyDevice.powerSupply.

        @return a YPowerSupply object allowing you to drive the regulated power supply.
        """
        return cls._proxy(cls, YPowerSupply_aio.FindPowerSupplyInContext(yctx._aio, func))

    @classmethod
    def FirstPowerSupply(cls) -> Union[YPowerSupply, None]:
        """
        Starts the enumeration of regulated power supplies currently accessible.
        Use the method YPowerSupply.nextPowerSupply() to iterate on
        next regulated power supplies.

        @return a pointer to a YPowerSupply object, corresponding to
                the first regulated power supply currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YPowerSupply_aio.FirstPowerSupplyInContext(YAPI_aio))

    @classmethod
    def FirstPowerSupplyInContext(cls, yctx: YAPIContext) -> Union[YPowerSupply, None]:
        """
        Starts the enumeration of regulated power supplies currently accessible.
        Use the method YPowerSupply.nextPowerSupply() to iterate on
        next regulated power supplies.

        @param yctx : a YAPI context.

        @return a pointer to a YPowerSupply object, corresponding to
                the first regulated power supply currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YPowerSupply_aio.FirstPowerSupplyInContext(yctx._aio))

    def nextPowerSupply(self) -> Union[YPowerSupply, None]:
        """
        Continues the enumeration of regulated power supplies started using yFirstPowerSupply().
        Caution: You can't make any assumption about the returned regulated power supplies order.
        If you want to find a specific a regulated power supply, use PowerSupply.findPowerSupply()
        and a hardwareID or a logical name.

        @return a pointer to a YPowerSupply object, corresponding to
                a regulated power supply currently online, or a None pointer
                if there are no more regulated power supplies to enumerate.
        """
        return self._proxy(type(self), self._aio.nextPowerSupply())

    if not _DYNAMIC_HELPERS:
        def set_voltageLimit(self, newval: float) -> int:
            """
            Changes the voltage limit, in V.

            @param newval : a floating point number corresponding to the voltage limit, in V

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_voltageLimit(newval))

    if not _DYNAMIC_HELPERS:
        def get_voltageLimit(self) -> float:
            """
            Returns the voltage limit, in V.

            @return a floating point number corresponding to the voltage limit, in V

            On failure, throws an exception or returns YPowerSupply.VOLTAGELIMIT_INVALID.
            """
            return self._run(self._aio.get_voltageLimit())

    if not _DYNAMIC_HELPERS:
        def set_currentLimit(self, newval: float) -> int:
            """
            Changes the current limit, in mA.

            @param newval : a floating point number corresponding to the current limit, in mA

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_currentLimit(newval))

    if not _DYNAMIC_HELPERS:
        def get_currentLimit(self) -> float:
            """
            Returns the current limit, in mA.

            @return a floating point number corresponding to the current limit, in mA

            On failure, throws an exception or returns YPowerSupply.CURRENTLIMIT_INVALID.
            """
            return self._run(self._aio.get_currentLimit())

    if not _DYNAMIC_HELPERS:
        def get_powerOutput(self) -> int:
            """
            Returns the power supply output switch state.

            @return either YPowerSupply.POWEROUTPUT_OFF or YPowerSupply.POWEROUTPUT_ON, according to the power
            supply output switch state

            On failure, throws an exception or returns YPowerSupply.POWEROUTPUT_INVALID.
            """
            return self._run(self._aio.get_powerOutput())

    if not _DYNAMIC_HELPERS:
        def set_powerOutput(self, newval: int) -> int:
            """
            Changes the power supply output switch state.

            @param newval : either YPowerSupply.POWEROUTPUT_OFF or YPowerSupply.POWEROUTPUT_ON, according to
            the power supply output switch state

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_powerOutput(newval))

    if not _DYNAMIC_HELPERS:
        def get_measuredVoltage(self) -> float:
            """
            Returns the measured output voltage, in V.

            @return a floating point number corresponding to the measured output voltage, in V

            On failure, throws an exception or returns YPowerSupply.MEASUREDVOLTAGE_INVALID.
            """
            return self._run(self._aio.get_measuredVoltage())

    if not _DYNAMIC_HELPERS:
        def get_measuredCurrent(self) -> float:
            """
            Returns the measured output current, in mA.

            @return a floating point number corresponding to the measured output current, in mA

            On failure, throws an exception or returns YPowerSupply.MEASUREDCURRENT_INVALID.
            """
            return self._run(self._aio.get_measuredCurrent())

    if not _DYNAMIC_HELPERS:
        def get_inputVoltage(self) -> float:
            """
            Returns the measured input voltage, in V.

            @return a floating point number corresponding to the measured input voltage, in V

            On failure, throws an exception or returns YPowerSupply.INPUTVOLTAGE_INVALID.
            """
            return self._run(self._aio.get_inputVoltage())

    if not _DYNAMIC_HELPERS:
        def set_voltageTransition(self, newval: str) -> int:
            return self._run(self._aio.set_voltageTransition(newval))

    if not _DYNAMIC_HELPERS:
        def set_voltageLimitAtStartUp(self, newval: float) -> int:
            """
            Changes the voltage set point at device start up. Remember to call the matching
            module saveToFlash() method, otherwise this call has no effect.

            @param newval : a floating point number corresponding to the voltage set point at device start up

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_voltageLimitAtStartUp(newval))

    if not _DYNAMIC_HELPERS:
        def get_voltageLimitAtStartUp(self) -> float:
            """
            Returns the selected voltage limit at device startup, in V.

            @return a floating point number corresponding to the selected voltage limit at device startup, in V

            On failure, throws an exception or returns YPowerSupply.VOLTAGELIMITATSTARTUP_INVALID.
            """
            return self._run(self._aio.get_voltageLimitAtStartUp())

    if not _DYNAMIC_HELPERS:
        def set_currentLimitAtStartUp(self, newval: float) -> int:
            """
            Changes the current limit at device start up. Remember to call the matching
            module saveToFlash() method, otherwise this call has no effect.

            @param newval : a floating point number corresponding to the current limit at device start up

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_currentLimitAtStartUp(newval))

    if not _DYNAMIC_HELPERS:
        def get_currentLimitAtStartUp(self) -> float:
            """
            Returns the selected current limit at device startup, in mA.

            @return a floating point number corresponding to the selected current limit at device startup, in mA

            On failure, throws an exception or returns YPowerSupply.CURRENTLIMITATSTARTUP_INVALID.
            """
            return self._run(self._aio.get_currentLimitAtStartUp())

    if not _DYNAMIC_HELPERS:
        def get_powerOutputAtStartUp(self) -> int:
            """
            Returns the power supply output switch state.

            @return either YPowerSupply.POWEROUTPUTATSTARTUP_OFF or YPowerSupply.POWEROUTPUTATSTARTUP_ON,
            according to the power supply output switch state

            On failure, throws an exception or returns YPowerSupply.POWEROUTPUTATSTARTUP_INVALID.
            """
            return self._run(self._aio.get_powerOutputAtStartUp())

    if not _DYNAMIC_HELPERS:
        def set_powerOutputAtStartUp(self, newval: int) -> int:
            """
            Changes the power supply output switch state at device start up. Remember to call the matching
            module saveToFlash() method, otherwise this call has no effect.

            @param newval : either YPowerSupply.POWEROUTPUTATSTARTUP_OFF or
            YPowerSupply.POWEROUTPUTATSTARTUP_ON, according to the power supply output switch state at device start up

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_powerOutputAtStartUp(newval))

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YPowerSupplyValueCallback) -> int:
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

    if not _DYNAMIC_HELPERS:
        def voltageMove(self, V_target: float, ms_duration: int) -> int:
            """
            Performs a smooth transition of output voltage. Any explicit voltage
            change cancels any ongoing transition process.

            @param V_target   : new output voltage value at the end of the transition
                    (floating-point number, representing the end voltage in V)
            @param ms_duration : total duration of the transition, in milliseconds

            @return YAPI.SUCCESS when the call succeeds.
            """
            return self._run(self._aio.voltageMove(V_target, ms_duration))

    # --- (end of YPowerSupply implementation)

