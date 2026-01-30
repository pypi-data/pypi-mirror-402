# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YPower
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
Yoctopuce library: Asyncio implementation of YPower
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YPower
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, YSensor, YMeasure
)

# --- (YPower class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YPowerValueCallback = Union[Callable[['YPower', str], Any], None]
        YPowerTimedReportCallback = Union[Callable[['YPower', YMeasure], Any], None]
    except TypeError:
        YPowerValueCallback = Union[Callable, Awaitable]
        YPowerTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YPower(YSensor):
    """
    The YPower class allows you to read and configure Yoctopuce electrical power sensors.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.
    This class adds the ability to access the energy counter and the power factor.

    """
    # --- (end of YPower class start)
    if not _IS_MICROPYTHON:
        # --- (YPower return codes)
        POWERFACTOR_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        COSPHI_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        METER_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        DELIVEREDENERGYMETER_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        RECEIVEDENERGYMETER_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        METERTIMER_INVALID: Final[int] = YAPI.INVALID_UINT
        # --- (end of YPower return codes)

    # --- (YPower attributes declaration)
    _valueCallback: YPowerValueCallback
    _timedReportCallback: YPowerTimedReportCallback
    # --- (end of YPower attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Power', func)
        # --- (YPower constructor)
        # --- (end of YPower constructor)

    # --- (YPower implementation)
    @classmethod
    def FindPower(cls, func: str) -> YPower:
        """
        Retrieves a electrical power sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the electrical power sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPower.isOnline() to test if the electrical power sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a electrical power sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the electrical power sensor, for instance
                YWATTMK1.power.

        @return a YPower object allowing you to drive the electrical power sensor.
        """
        return cls.FindPowerInContext(YAPI, func)

    @classmethod
    def FindPowerInContext(cls, yctx: YAPIContext, func: str) -> YPower:
        """
        Retrieves a electrical power sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the electrical power sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YPower.isOnline() to test if the electrical power sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a electrical power sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the electrical power sensor, for instance
                YWATTMK1.power.

        @return a YPower object allowing you to drive the electrical power sensor.
        """
        obj: Union[YPower, None] = yctx._findInCache('Power', func)
        if obj:
            return obj
        return YPower(yctx, func)

    @classmethod
    def FirstPower(cls) -> Union[YPower, None]:
        """
        Starts the enumeration of electrical power sensors currently accessible.
        Use the method YPower.nextPower() to iterate on
        next electrical power sensors.

        @return a pointer to a YPower object, corresponding to
                the first electrical power sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstPowerInContext(YAPI)

    @classmethod
    def FirstPowerInContext(cls, yctx: YAPIContext) -> Union[YPower, None]:
        """
        Starts the enumeration of electrical power sensors currently accessible.
        Use the method YPower.nextPower() to iterate on
        next electrical power sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YPower object, corresponding to
                the first electrical power sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Power')
        if hwid:
            return cls.FindPowerInContext(yctx, hwid2str(hwid))
        return None

    def nextPower(self) -> Union[YPower, None]:
        """
        Continues the enumeration of electrical power sensors started using yFirstPower().
        Caution: You can't make any assumption about the returned electrical power sensors order.
        If you want to find a specific a electrical power sensor, use Power.findPower()
        and a hardwareID or a logical name.

        @return a pointer to a YPower object, corresponding to
                a electrical power sensor currently online, or a None pointer
                if there are no more electrical power sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Power', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindPowerInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_powerFactor(self) -> float:
        """
        Returns the power factor (PF), i.e. ratio between the active power consumed (in W)
        and the apparent power provided (VA).

        @return a floating point number corresponding to the power factor (PF), i.e

        On failure, throws an exception or returns YPower.POWERFACTOR_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("powerFactor")
        if json_val is None:
            return YPower.POWERFACTOR_INVALID
        res: float
        res = round(json_val / 65.536) / 1000.0
        if res == YPower.POWERFACTOR_INVALID:
            res = self._cosPhi
        return round(res * 1000) / 1000

    async def get_cosPhi(self) -> float:
        """
        Returns the Displacement Power factor (DPF), i.e. cosine of the phase shift between
        the voltage and current fundamentals.
        On the Yocto-Watt (V1), the value returned by this method correponds to the
        power factor as this device is cannot estimate the true DPF.

        @return a floating point number corresponding to the Displacement Power factor (DPF), i.e

        On failure, throws an exception or returns YPower.COSPHI_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("cosPhi")
        if json_val is None:
            return YPower.COSPHI_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_meter(self, newval: float) -> int:
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("meter", rest_val)

    async def get_meter(self) -> float:
        """
        Returns the energy counter, maintained by the wattmeter by integrating the
        power consumption over time. This is the sum of forward and backwad energy transfers,
        if you are insterested in only one direction, use  get_receivedEnergyMeter() or
        get_deliveredEnergyMeter(). Note that this counter is reset at each start of the device.

        @return a floating point number corresponding to the energy counter, maintained by the wattmeter by
        integrating the
                power consumption over time

        On failure, throws an exception or returns YPower.METER_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("meter")
        if json_val is None:
            return YPower.METER_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_deliveredEnergyMeter(self) -> float:
        """
        Returns the energy counter, maintained by the wattmeter by integrating the power consumption over time,
        but only when positive. Note that this counter is reset at each start of the device.

        @return a floating point number corresponding to the energy counter, maintained by the wattmeter by
        integrating the power consumption over time,
                but only when positive

        On failure, throws an exception or returns YPower.DELIVEREDENERGYMETER_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("deliveredEnergyMeter")
        if json_val is None:
            return YPower.DELIVEREDENERGYMETER_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_receivedEnergyMeter(self) -> float:
        """
        Returns the energy counter, maintained by the wattmeter by integrating the power consumption over time,
        but only when negative. Note that this counter is reset at each start of the device.

        @return a floating point number corresponding to the energy counter, maintained by the wattmeter by
        integrating the power consumption over time,
                but only when negative

        On failure, throws an exception or returns YPower.RECEIVEDENERGYMETER_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("receivedEnergyMeter")
        if json_val is None:
            return YPower.RECEIVEDENERGYMETER_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_meterTimer(self) -> int:
        """
        Returns the elapsed time since last energy counter reset, in seconds.

        @return an integer corresponding to the elapsed time since last energy counter reset, in seconds

        On failure, throws an exception or returns YPower.METERTIMER_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("meterTimer")
        if json_val is None:
            return YPower.METERTIMER_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YPowerValueCallback) -> int:
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

    if not _IS_MICROPYTHON:
        async def registerTimedReportCallback(self, callback: YPowerTimedReportCallback) -> int:
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
            return await super().registerTimedReportCallback(callback)

    async def reset(self) -> int:
        """
        Resets the energy counters.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_meter(0)

    # --- (end of YPower implementation)

