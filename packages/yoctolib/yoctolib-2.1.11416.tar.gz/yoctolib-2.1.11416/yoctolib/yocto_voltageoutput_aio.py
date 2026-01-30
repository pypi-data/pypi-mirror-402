# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YVoltageOutput
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
Yoctopuce library: Asyncio implementation of YVoltageOutput
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YVoltageOutput
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

# --- (YVoltageOutput class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YVoltageOutputValueCallback = Union[Callable[['YVoltageOutput', str], Any], None]
    except TypeError:
        YVoltageOutputValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YVoltageOutput(YFunction):
    """
    The YVoltageOutput class allows you to drive a voltage output.

    """
    # --- (end of YVoltageOutput class start)
    if not _IS_MICROPYTHON:
        # --- (YVoltageOutput return codes)
        CURRENTVOLTAGE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        VOLTAGETRANSITION_INVALID: Final[str] = YAPI.INVALID_STRING
        VOLTAGEATSTARTUP_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        # --- (end of YVoltageOutput return codes)

    # --- (YVoltageOutput attributes declaration)
    _valueCallback: YVoltageOutputValueCallback
    # --- (end of YVoltageOutput attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'VoltageOutput', func)
        # --- (YVoltageOutput constructor)
        # --- (end of YVoltageOutput constructor)

    # --- (YVoltageOutput implementation)
    @classmethod
    def FindVoltageOutput(cls, func: str) -> YVoltageOutput:
        """
        Retrieves a voltage output for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the voltage output is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YVoltageOutput.isOnline() to test if the voltage output is
        indeed online at a given time. In case of ambiguity when looking for
        a voltage output by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the voltage output, for instance
                TX010V01.voltageOutput1.

        @return a YVoltageOutput object allowing you to drive the voltage output.
        """
        return cls.FindVoltageOutputInContext(YAPI, func)

    @classmethod
    def FindVoltageOutputInContext(cls, yctx: YAPIContext, func: str) -> YVoltageOutput:
        """
        Retrieves a voltage output for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the voltage output is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YVoltageOutput.isOnline() to test if the voltage output is
        indeed online at a given time. In case of ambiguity when looking for
        a voltage output by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the voltage output, for instance
                TX010V01.voltageOutput1.

        @return a YVoltageOutput object allowing you to drive the voltage output.
        """
        obj: Union[YVoltageOutput, None] = yctx._findInCache('VoltageOutput', func)
        if obj:
            return obj
        return YVoltageOutput(yctx, func)

    @classmethod
    def FirstVoltageOutput(cls) -> Union[YVoltageOutput, None]:
        """
        Starts the enumeration of voltage outputs currently accessible.
        Use the method YVoltageOutput.nextVoltageOutput() to iterate on
        next voltage outputs.

        @return a pointer to a YVoltageOutput object, corresponding to
                the first voltage output currently online, or a None pointer
                if there are none.
        """
        return cls.FirstVoltageOutputInContext(YAPI)

    @classmethod
    def FirstVoltageOutputInContext(cls, yctx: YAPIContext) -> Union[YVoltageOutput, None]:
        """
        Starts the enumeration of voltage outputs currently accessible.
        Use the method YVoltageOutput.nextVoltageOutput() to iterate on
        next voltage outputs.

        @param yctx : a YAPI context.

        @return a pointer to a YVoltageOutput object, corresponding to
                the first voltage output currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('VoltageOutput')
        if hwid:
            return cls.FindVoltageOutputInContext(yctx, hwid2str(hwid))
        return None

    def nextVoltageOutput(self) -> Union[YVoltageOutput, None]:
        """
        Continues the enumeration of voltage outputs started using yFirstVoltageOutput().
        Caution: You can't make any assumption about the returned voltage outputs order.
        If you want to find a specific a voltage output, use VoltageOutput.findVoltageOutput()
        and a hardwareID or a logical name.

        @return a pointer to a YVoltageOutput object, corresponding to
                a voltage output currently online, or a None pointer
                if there are no more voltage outputs to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('VoltageOutput', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindVoltageOutputInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def set_currentVoltage(self, newval: float) -> int:
        """
        Changes the output voltage, in V. Valid range is from 0 to 10V.

        @param newval : a floating point number corresponding to the output voltage, in V

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("currentVoltage", rest_val)

    async def get_currentVoltage(self) -> float:
        """
        Returns the output voltage set point, in V.

        @return a floating point number corresponding to the output voltage set point, in V

        On failure, throws an exception or returns YVoltageOutput.CURRENTVOLTAGE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("currentVoltage")
        if json_val is None:
            return YVoltageOutput.CURRENTVOLTAGE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_voltageTransition(self) -> str:
        json_val: Union[str, None] = await self._fromCache("voltageTransition")
        if json_val is None:
            return YVoltageOutput.VOLTAGETRANSITION_INVALID
        return json_val

    async def set_voltageTransition(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("voltageTransition", rest_val)

    async def set_voltageAtStartUp(self, newval: float) -> int:
        """
        Changes the output voltage at device start up. Remember to call the matching
        module saveToFlash() method, otherwise this call has no effect.

        @param newval : a floating point number corresponding to the output voltage at device start up

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("voltageAtStartUp", rest_val)

    async def get_voltageAtStartUp(self) -> float:
        """
        Returns the selected voltage output at device startup, in V.

        @return a floating point number corresponding to the selected voltage output at device startup, in V

        On failure, throws an exception or returns YVoltageOutput.VOLTAGEATSTARTUP_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("voltageAtStartUp")
        if json_val is None:
            return YVoltageOutput.VOLTAGEATSTARTUP_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YVoltageOutputValueCallback) -> int:
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
        if V_target > 10.0:
            V_target = 10.0
        newval = "%d:%d" % (int(round(V_target*65536)), ms_duration)

        return await self.set_voltageTransition(newval)

    # --- (end of YVoltageOutput implementation)

