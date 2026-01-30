# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YPowerOutput
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
Yoctopuce library: Asyncio implementation of YPowerOutput
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YPowerOutput
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

# --- (YPowerOutput class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPowerOutputValueCallback = Union[Callable[['YPowerOutput', str], Any], None]
    except TypeError:
        YPowerOutputValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPowerOutput(YFunction):
    """
    The YPowerOutput class allows you to control
    the power output featured on some Yoctopuce devices.

    """
    # --- (end of YPowerOutput class start)
    if not _IS_MICROPYTHON:
        # --- (YPowerOutput return codes)
        VOLTAGE_OFF: Final[int] = 0
        VOLTAGE_OUT3V3: Final[int] = 1
        VOLTAGE_OUT5V: Final[int] = 2
        VOLTAGE_OUT4V7: Final[int] = 3
        VOLTAGE_OUT1V8: Final[int] = 4
        VOLTAGE_INVALID: Final[int] = -1
        # --- (end of YPowerOutput return codes)

    # --- (YPowerOutput attributes declaration)
    _valueCallback: YPowerOutputValueCallback
    # --- (end of YPowerOutput attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'PowerOutput', func)
        # --- (YPowerOutput constructor)
        # --- (end of YPowerOutput constructor)

    # --- (YPowerOutput implementation)
    @classmethod
    def FindPowerOutput(cls, func: str) -> YPowerOutput:
        """
        Retrieves a power output for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the power output is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPowerOutput.isOnline() to test if the power output is
        indeed online at a given time. In case of ambiguity when looking for
        a power output by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the power output, for instance
                YI2CMK01.powerOutput.

        @return a YPowerOutput object allowing you to drive the power output.
        """
        return cls.FindPowerOutputInContext(YAPI, func)

    @classmethod
    def FindPowerOutputInContext(cls, yctx: YAPIContext, func: str) -> YPowerOutput:
        """
        Retrieves a power output for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the power output is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPowerOutput.isOnline() to test if the power output is
        indeed online at a given time. In case of ambiguity when looking for
        a power output by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the power output, for instance
                YI2CMK01.powerOutput.

        @return a YPowerOutput object allowing you to drive the power output.
        """
        obj: Union[YPowerOutput, None] = yctx._findInCache('PowerOutput', func)
        if obj:
            return obj
        return YPowerOutput(yctx, func)

    @classmethod
    def FirstPowerOutput(cls) -> Union[YPowerOutput, None]:
        """
        Starts the enumeration of power output currently accessible.
        Use the method YPowerOutput.nextPowerOutput() to iterate on
        next power output.

        @return a pointer to a YPowerOutput object, corresponding to
                the first power output currently online, or a None pointer
                if there are none.
        """
        return cls.FirstPowerOutputInContext(YAPI)

    @classmethod
    def FirstPowerOutputInContext(cls, yctx: YAPIContext) -> Union[YPowerOutput, None]:
        """
        Starts the enumeration of power output currently accessible.
        Use the method YPowerOutput.nextPowerOutput() to iterate on
        next power output.

        @param yctx : a YAPI context.

        @return a pointer to a YPowerOutput object, corresponding to
                the first power output currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('PowerOutput')
        if hwid:
            return cls.FindPowerOutputInContext(yctx, hwid2str(hwid))
        return None

    def nextPowerOutput(self) -> Union[YPowerOutput, None]:
        """
        Continues the enumeration of power output started using yFirstPowerOutput().
        Caution: You can't make any assumption about the returned power output order.
        If you want to find a specific a power output, use PowerOutput.findPowerOutput()
        and a hardwareID or a logical name.

        @return a pointer to a YPowerOutput object, corresponding to
                a power output currently online, or a None pointer
                if there are no more power output to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('PowerOutput', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindPowerOutputInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_voltage(self) -> int:
        """
        Returns the voltage on the power output featured by the module.

        @return a value among YPowerOutput.VOLTAGE_OFF, YPowerOutput.VOLTAGE_OUT3V3,
        YPowerOutput.VOLTAGE_OUT5V, YPowerOutput.VOLTAGE_OUT4V7 and YPowerOutput.VOLTAGE_OUT1V8
        corresponding to the voltage on the power output featured by the module

        On failure, throws an exception or returns YPowerOutput.VOLTAGE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("voltage")
        if json_val is None:
            return YPowerOutput.VOLTAGE_INVALID
        return json_val

    async def set_voltage(self, newval: int) -> int:
        """
        Changes the voltage on the power output provided by the
        module. Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YPowerOutput.VOLTAGE_OFF, YPowerOutput.VOLTAGE_OUT3V3,
        YPowerOutput.VOLTAGE_OUT5V, YPowerOutput.VOLTAGE_OUT4V7 and YPowerOutput.VOLTAGE_OUT1V8
        corresponding to the voltage on the power output provided by the
                module

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("voltage", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YPowerOutputValueCallback) -> int:
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

    # --- (end of YPowerOutput implementation)

