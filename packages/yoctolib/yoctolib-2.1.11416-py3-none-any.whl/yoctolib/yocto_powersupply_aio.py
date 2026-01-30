# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YPowerSupply
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
Yoctopuce library: Asyncio implementation of YPowerSupply
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction
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

    # --- (YPowerSupply attributes declaration)
    _valueCallback: YPowerSupplyValueCallback
    # --- (end of YPowerSupply attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'PowerSupply', func)
        # --- (YPowerSupply constructor)
        # --- (end of YPowerSupply constructor)

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
        return cls.FindPowerSupplyInContext(YAPI, func)

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
        obj: Union[YPowerSupply, None] = yctx._findInCache('PowerSupply', func)
        if obj:
            return obj
        return YPowerSupply(yctx, func)

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
        return cls.FirstPowerSupplyInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('PowerSupply')
        if hwid:
            return cls.FindPowerSupplyInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('PowerSupply', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindPowerSupplyInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_voltageLimit(self, newval: float) -> int:
        """
        Changes the voltage limit, in V.

        @param newval : a floating point number corresponding to the voltage limit, in V

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("voltageLimit", rest_val)

    async def get_voltageLimit(self) -> float:
        """
        Returns the voltage limit, in V.

        @return a floating point number corresponding to the voltage limit, in V

        On failure, throws an exception or returns YPowerSupply.VOLTAGELIMIT_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("voltageLimit")
        if json_val is None:
            return YPowerSupply.VOLTAGELIMIT_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_currentLimit(self, newval: float) -> int:
        """
        Changes the current limit, in mA.

        @param newval : a floating point number corresponding to the current limit, in mA

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("currentLimit", rest_val)

    async def get_currentLimit(self) -> float:
        """
        Returns the current limit, in mA.

        @return a floating point number corresponding to the current limit, in mA

        On failure, throws an exception or returns YPowerSupply.CURRENTLIMIT_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("currentLimit")
        if json_val is None:
            return YPowerSupply.CURRENTLIMIT_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_powerOutput(self) -> int:
        """
        Returns the power supply output switch state.

        @return either YPowerSupply.POWEROUTPUT_OFF or YPowerSupply.POWEROUTPUT_ON, according to the power
        supply output switch state

        On failure, throws an exception or returns YPowerSupply.POWEROUTPUT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("powerOutput")
        if json_val is None:
            return YPowerSupply.POWEROUTPUT_INVALID
        return json_val

    async def set_powerOutput(self, newval: int) -> int:
        """
        Changes the power supply output switch state.

        @param newval : either YPowerSupply.POWEROUTPUT_OFF or YPowerSupply.POWEROUTPUT_ON, according to
        the power supply output switch state

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("powerOutput", rest_val)

    async def get_measuredVoltage(self) -> float:
        """
        Returns the measured output voltage, in V.

        @return a floating point number corresponding to the measured output voltage, in V

        On failure, throws an exception or returns YPowerSupply.MEASUREDVOLTAGE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("measuredVoltage")
        if json_val is None:
            return YPowerSupply.MEASUREDVOLTAGE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_measuredCurrent(self) -> float:
        """
        Returns the measured output current, in mA.

        @return a floating point number corresponding to the measured output current, in mA

        On failure, throws an exception or returns YPowerSupply.MEASUREDCURRENT_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("measuredCurrent")
        if json_val is None:
            return YPowerSupply.MEASUREDCURRENT_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_inputVoltage(self) -> float:
        """
        Returns the measured input voltage, in V.

        @return a floating point number corresponding to the measured input voltage, in V

        On failure, throws an exception or returns YPowerSupply.INPUTVOLTAGE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("inputVoltage")
        if json_val is None:
            return YPowerSupply.INPUTVOLTAGE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_voltageTransition(self) -> str:
        json_val: Union[str, None] = await self._fromCache("voltageTransition")
        if json_val is None:
            return YPowerSupply.VOLTAGETRANSITION_INVALID
        return json_val

    async def set_voltageTransition(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("voltageTransition", rest_val)

    async def set_voltageLimitAtStartUp(self, newval: float) -> int:
        """
        Changes the voltage set point at device start up. Remember to call the matching
        module saveToFlash() method, otherwise this call has no effect.

        @param newval : a floating point number corresponding to the voltage set point at device start up

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("voltageLimitAtStartUp", rest_val)

    async def get_voltageLimitAtStartUp(self) -> float:
        """
        Returns the selected voltage limit at device startup, in V.

        @return a floating point number corresponding to the selected voltage limit at device startup, in V

        On failure, throws an exception or returns YPowerSupply.VOLTAGELIMITATSTARTUP_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("voltageLimitAtStartUp")
        if json_val is None:
            return YPowerSupply.VOLTAGELIMITATSTARTUP_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_currentLimitAtStartUp(self, newval: float) -> int:
        """
        Changes the current limit at device start up. Remember to call the matching
        module saveToFlash() method, otherwise this call has no effect.

        @param newval : a floating point number corresponding to the current limit at device start up

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("currentLimitAtStartUp", rest_val)

    async def get_currentLimitAtStartUp(self) -> float:
        """
        Returns the selected current limit at device startup, in mA.

        @return a floating point number corresponding to the selected current limit at device startup, in mA

        On failure, throws an exception or returns YPowerSupply.CURRENTLIMITATSTARTUP_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("currentLimitAtStartUp")
        if json_val is None:
            return YPowerSupply.CURRENTLIMITATSTARTUP_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_powerOutputAtStartUp(self) -> int:
        """
        Returns the power supply output switch state.

        @return either YPowerSupply.POWEROUTPUTATSTARTUP_OFF or YPowerSupply.POWEROUTPUTATSTARTUP_ON,
        according to the power supply output switch state

        On failure, throws an exception or returns YPowerSupply.POWEROUTPUTATSTARTUP_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("powerOutputAtStartUp")
        if json_val is None:
            return YPowerSupply.POWEROUTPUTATSTARTUP_INVALID
        return json_val

    async def set_powerOutputAtStartUp(self, newval: int) -> int:
        """
        Changes the power supply output switch state at device start up. Remember to call the matching
        module saveToFlash() method, otherwise this call has no effect.

        @param newval : either YPowerSupply.POWEROUTPUTATSTARTUP_OFF or
        YPowerSupply.POWEROUTPUTATSTARTUP_ON, according to the power supply output switch state at device start up

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("powerOutputAtStartUp", rest_val)

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YPowerSupply.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YPowerSupplyValueCallback) -> int:
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

    async def voltageMove(self, V_target: float, ms_duration: int) -> int:
        """
        Performs a smooth transition of output voltage. Any explicit voltage
        change cancels any ongoing transition process.

        @param V_target   : new output voltage value at the end of the transition
                (floating-point number, representing the end voltage in V)
        @param ms_duration : total duration of the transition, in milliseconds

        @return YAPI.SUCCESS when the call succeeds.
        """
        newval: str
        if V_target < 0.0:
            V_target  = 0.0
        newval = "%d:%d" % (int(round(V_target*65536)), ms_duration)

        return await self.set_voltageTransition(newval)

    # --- (end of YPowerSupply implementation)

