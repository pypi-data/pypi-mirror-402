# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YArithmeticSensor
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
Yoctopuce library: High-level API for YArithmeticSensor
version: PATCH_WITH_VERSION
requires: yocto_arithmeticsensor_aio
requires: yocto_api
provides: YArithmeticSensor
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

from .yocto_arithmeticsensor_aio import YArithmeticSensor as YArithmeticSensor_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YArithmeticSensor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YArithmeticSensorValueCallback = Union[Callable[['YArithmeticSensor', str], Any], None]
        YArithmeticSensorTimedReportCallback = Union[Callable[['YArithmeticSensor', YMeasure], Any], None]
    except TypeError:
        YArithmeticSensorValueCallback = Union[Callable, Awaitable]
        YArithmeticSensorTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YArithmeticSensor(YSensor):
    """
    The YArithmeticSensor class allows some Yoctopuce devices to compute in real-time
    values based on an arithmetic formula involving one or more measured signals as
    well as the temperature. As for any physical sensor, the computed values can be
    read by callback and stored in the built-in datalogger.

    """
    _aio: YArithmeticSensor_aio
    # --- (end of YArithmeticSensor class start)
    if not _IS_MICROPYTHON:
        # --- (YArithmeticSensor return codes)
        DESCRIPTION_INVALID: Final[str] = YAPI.INVALID_STRING
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of YArithmeticSensor return codes)


    # --- (YArithmeticSensor implementation)

    @classmethod
    def FindArithmeticSensor(cls, func: str) -> YArithmeticSensor:
        """
        Retrieves an arithmetic sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the arithmetic sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YArithmeticSensor.isOnline() to test if the arithmetic sensor is
        indeed online at a given time. In case of ambiguity when looking for
        an arithmetic sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the arithmetic sensor, for instance
                RXUVOLT1.arithmeticSensor1.

        @return a YArithmeticSensor object allowing you to drive the arithmetic sensor.
        """
        return cls._proxy(cls, YArithmeticSensor_aio.FindArithmeticSensorInContext(YAPI_aio, func))

    @classmethod
    def FindArithmeticSensorInContext(cls, yctx: YAPIContext, func: str) -> YArithmeticSensor:
        """
        Retrieves an arithmetic sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the arithmetic sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YArithmeticSensor.isOnline() to test if the arithmetic sensor is
        indeed online at a given time. In case of ambiguity when looking for
        an arithmetic sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the arithmetic sensor, for instance
                RXUVOLT1.arithmeticSensor1.

        @return a YArithmeticSensor object allowing you to drive the arithmetic sensor.
        """
        return cls._proxy(cls, YArithmeticSensor_aio.FindArithmeticSensorInContext(yctx._aio, func))

    @classmethod
    def FirstArithmeticSensor(cls) -> Union[YArithmeticSensor, None]:
        """
        Starts the enumeration of arithmetic sensors currently accessible.
        Use the method YArithmeticSensor.nextArithmeticSensor() to iterate on
        next arithmetic sensors.

        @return a pointer to a YArithmeticSensor object, corresponding to
                the first arithmetic sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YArithmeticSensor_aio.FirstArithmeticSensorInContext(YAPI_aio))

    @classmethod
    def FirstArithmeticSensorInContext(cls, yctx: YAPIContext) -> Union[YArithmeticSensor, None]:
        """
        Starts the enumeration of arithmetic sensors currently accessible.
        Use the method YArithmeticSensor.nextArithmeticSensor() to iterate on
        next arithmetic sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YArithmeticSensor object, corresponding to
                the first arithmetic sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YArithmeticSensor_aio.FirstArithmeticSensorInContext(yctx._aio))

    def nextArithmeticSensor(self) -> Union[YArithmeticSensor, None]:
        """
        Continues the enumeration of arithmetic sensors started using yFirstArithmeticSensor().
        Caution: You can't make any assumption about the returned arithmetic sensors order.
        If you want to find a specific an arithmetic sensor, use ArithmeticSensor.findArithmeticSensor()
        and a hardwareID or a logical name.

        @return a pointer to a YArithmeticSensor object, corresponding to
                an arithmetic sensor currently online, or a None pointer
                if there are no more arithmetic sensors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextArithmeticSensor())

    if not _DYNAMIC_HELPERS:
        def set_unit(self, newval: str) -> int:
            """
            Changes the measuring unit for the arithmetic sensor.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the measuring unit for the arithmetic sensor

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_unit(newval))

    if not _DYNAMIC_HELPERS:
        def get_description(self) -> str:
            """
            Returns a short informative description of the formula.

            @return a string corresponding to a short informative description of the formula

            On failure, throws an exception or returns YArithmeticSensor.DESCRIPTION_INVALID.
            """
            return self._run(self._aio.get_description())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YArithmeticSensorValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YArithmeticSensorTimedReportCallback) -> int:
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
        def defineExpression(self, expr: str, descr: str) -> float:
            """
            Defines the arithmetic function by means of an algebraic expression. The expression
            may include references to device sensors, by their physical or logical name, to
            usual math functions and to auxiliary functions defined separately.

            @param expr : the algebraic expression defining the function.
            @param descr : short informative description of the expression.

            @return the current expression value if the call succeeds.

            On failure, throws an exception or returns YAPI.INVALID_DOUBLE.
            """
            return self._run(self._aio.defineExpression(expr, descr))

    if not _DYNAMIC_HELPERS:
        def loadExpression(self) -> str:
            """
            Retrieves the algebraic expression defining the arithmetic function, as previously
            configured using the defineExpression function.

            @return a string containing the mathematical expression.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadExpression())

    if not _DYNAMIC_HELPERS:
        def defineAuxiliaryFunction(self, name: str, inputValues: list[float], outputValues: list[float]) -> int:
            """
            Defines a auxiliary function by means of a table of reference points. Intermediate values
            will be interpolated between specified reference points. The reference points are given
            as pairs of floating point numbers.
            The auxiliary function will be available for use by all ArithmeticSensor objects of the
            device. Up to nine auxiliary function can be defined in a device, each containing up to
            96 reference points.

            @param name : auxiliary function name, up to 16 characters.
            @param inputValues : array of floating point numbers, corresponding to the function input value.
            @param outputValues : array of floating point numbers, corresponding to the output value
                    desired for each of the input value, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.defineAuxiliaryFunction(name, inputValues, outputValues))

    if not _DYNAMIC_HELPERS:
        def loadAuxiliaryFunction(self, name: str, inputValues: list[float], outputValues: list[float]) -> int:
            """
            Retrieves the reference points table defining an auxiliary function previously
            configured using the defineAuxiliaryFunction function.

            @param name : auxiliary function name, up to 16 characters.
            @param inputValues : array of floating point numbers, that is filled by the function
                    with all the function reference input value.
            @param outputValues : array of floating point numbers, that is filled by the function
                    output value for each of the input value, index by index.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadAuxiliaryFunction(name, inputValues, outputValues))

    # --- (end of YArithmeticSensor implementation)

