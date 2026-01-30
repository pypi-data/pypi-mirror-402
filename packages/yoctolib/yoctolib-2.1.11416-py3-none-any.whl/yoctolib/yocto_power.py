# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YPower
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
Yoctopuce library: High-level API for YPower
version: PATCH_WITH_VERSION
requires: yocto_power_aio
requires: yocto_api
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_power_aio import YPower as YPower_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
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
    _aio: YPower_aio
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
        return cls._proxy(cls, YPower_aio.FindPowerInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YPower_aio.FindPowerInContext(yctx._aio, func))

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
        return cls._proxy(cls, YPower_aio.FirstPowerInContext(YAPI_aio))

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
        return cls._proxy(cls, YPower_aio.FirstPowerInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextPower())

    if not _DYNAMIC_HELPERS:
        def get_powerFactor(self) -> float:
            """
            Returns the power factor (PF), i.e. ratio between the active power consumed (in W)
            and the apparent power provided (VA).

            @return a floating point number corresponding to the power factor (PF), i.e

            On failure, throws an exception or returns YPower.POWERFACTOR_INVALID.
            """
            return self._run(self._aio.get_powerFactor())

    if not _DYNAMIC_HELPERS:
        def get_cosPhi(self) -> float:
            """
            Returns the Displacement Power factor (DPF), i.e. cosine of the phase shift between
            the voltage and current fundamentals.
            On the Yocto-Watt (V1), the value returned by this method correponds to the
            power factor as this device is cannot estimate the true DPF.

            @return a floating point number corresponding to the Displacement Power factor (DPF), i.e

            On failure, throws an exception or returns YPower.COSPHI_INVALID.
            """
            return self._run(self._aio.get_cosPhi())

    if not _DYNAMIC_HELPERS:
        def set_meter(self, newval: float) -> int:
            return self._run(self._aio.set_meter(newval))

    if not _DYNAMIC_HELPERS:
        def get_meter(self) -> float:
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
            return self._run(self._aio.get_meter())

    if not _DYNAMIC_HELPERS:
        def get_deliveredEnergyMeter(self) -> float:
            """
            Returns the energy counter, maintained by the wattmeter by integrating the power consumption over time,
            but only when positive. Note that this counter is reset at each start of the device.

            @return a floating point number corresponding to the energy counter, maintained by the wattmeter by
            integrating the power consumption over time,
                    but only when positive

            On failure, throws an exception or returns YPower.DELIVEREDENERGYMETER_INVALID.
            """
            return self._run(self._aio.get_deliveredEnergyMeter())

    if not _DYNAMIC_HELPERS:
        def get_receivedEnergyMeter(self) -> float:
            """
            Returns the energy counter, maintained by the wattmeter by integrating the power consumption over time,
            but only when negative. Note that this counter is reset at each start of the device.

            @return a floating point number corresponding to the energy counter, maintained by the wattmeter by
            integrating the power consumption over time,
                    but only when negative

            On failure, throws an exception or returns YPower.RECEIVEDENERGYMETER_INVALID.
            """
            return self._run(self._aio.get_receivedEnergyMeter())

    if not _DYNAMIC_HELPERS:
        def get_meterTimer(self) -> int:
            """
            Returns the elapsed time since last energy counter reset, in seconds.

            @return an integer corresponding to the elapsed time since last energy counter reset, in seconds

            On failure, throws an exception or returns YPower.METERTIMER_INVALID.
            """
            return self._run(self._aio.get_meterTimer())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YPowerValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YPowerTimedReportCallback) -> int:
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

    if not _DYNAMIC_HELPERS:
        def reset(self) -> int:
            """
            Resets the energy counters.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reset())

    # --- (end of YPower implementation)

