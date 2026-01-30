# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YQuadratureDecoder
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
Yoctopuce library: High-level API for YQuadratureDecoder
version: PATCH_WITH_VERSION
requires: yocto_quadraturedecoder_aio
requires: yocto_api
provides: YQuadratureDecoder
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

from .yocto_quadraturedecoder_aio import YQuadratureDecoder as YQuadratureDecoder_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YSensor, YMeasure
)

# --- (YQuadratureDecoder class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YQuadratureDecoderValueCallback = Union[Callable[['YQuadratureDecoder', str], Any], None]
        YQuadratureDecoderTimedReportCallback = Union[Callable[['YQuadratureDecoder', YMeasure], Any], None]
    except TypeError:
        YQuadratureDecoderValueCallback = Union[Callable, Awaitable]
        YQuadratureDecoderTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YQuadratureDecoder(YSensor):
    """
    The YQuadratureDecoder class allows you to read and configure Yoctopuce quadrature decoders.
    It inherits from YSensor class the core functions to read measurements,
    to register callback functions, and to access the autonomous datalogger.

    """
    _aio: YQuadratureDecoder_aio
    # --- (end of YQuadratureDecoder class start)
    if not _IS_MICROPYTHON:
        # --- (YQuadratureDecoder return codes)
        SPEED_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        EDGESPERCYCLE_INVALID: Final[int] = YAPI.INVALID_UINT
        DECODING_OFF: Final[int] = 0
        DECODING_ON: Final[int] = 1
        DECODING_INVALID: Final[int] = -1
        # --- (end of YQuadratureDecoder return codes)


    # --- (YQuadratureDecoder implementation)

    @classmethod
    def FindQuadratureDecoder(cls, func: str) -> YQuadratureDecoder:
        """
        Retrieves a quadrature decoder for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the quadrature decoder is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YQuadratureDecoder.isOnline() to test if the quadrature decoder is
        indeed online at a given time. In case of ambiguity when looking for
        a quadrature decoder by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the quadrature decoder, for instance
                YMXBTN01.quadratureDecoder1.

        @return a YQuadratureDecoder object allowing you to drive the quadrature decoder.
        """
        return cls._proxy(cls, YQuadratureDecoder_aio.FindQuadratureDecoderInContext(YAPI_aio, func))

    @classmethod
    def FindQuadratureDecoderInContext(cls, yctx: YAPIContext, func: str) -> YQuadratureDecoder:
        """
        Retrieves a quadrature decoder for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the quadrature decoder is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YQuadratureDecoder.isOnline() to test if the quadrature decoder is
        indeed online at a given time. In case of ambiguity when looking for
        a quadrature decoder by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the quadrature decoder, for instance
                YMXBTN01.quadratureDecoder1.

        @return a YQuadratureDecoder object allowing you to drive the quadrature decoder.
        """
        return cls._proxy(cls, YQuadratureDecoder_aio.FindQuadratureDecoderInContext(yctx._aio, func))

    @classmethod
    def FirstQuadratureDecoder(cls) -> Union[YQuadratureDecoder, None]:
        """
        Starts the enumeration of quadrature decoders currently accessible.
        Use the method YQuadratureDecoder.nextQuadratureDecoder() to iterate on
        next quadrature decoders.

        @return a pointer to a YQuadratureDecoder object, corresponding to
                the first quadrature decoder currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YQuadratureDecoder_aio.FirstQuadratureDecoderInContext(YAPI_aio))

    @classmethod
    def FirstQuadratureDecoderInContext(cls, yctx: YAPIContext) -> Union[YQuadratureDecoder, None]:
        """
        Starts the enumeration of quadrature decoders currently accessible.
        Use the method YQuadratureDecoder.nextQuadratureDecoder() to iterate on
        next quadrature decoders.

        @param yctx : a YAPI context.

        @return a pointer to a YQuadratureDecoder object, corresponding to
                the first quadrature decoder currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YQuadratureDecoder_aio.FirstQuadratureDecoderInContext(yctx._aio))

    def nextQuadratureDecoder(self) -> Union[YQuadratureDecoder, None]:
        """
        Continues the enumeration of quadrature decoders started using yFirstQuadratureDecoder().
        Caution: You can't make any assumption about the returned quadrature decoders order.
        If you want to find a specific a quadrature decoder, use QuadratureDecoder.findQuadratureDecoder()
        and a hardwareID or a logical name.

        @return a pointer to a YQuadratureDecoder object, corresponding to
                a quadrature decoder currently online, or a None pointer
                if there are no more quadrature decoders to enumerate.
        """
        return self._proxy(type(self), self._aio.nextQuadratureDecoder())

    if not _DYNAMIC_HELPERS:
        def set_currentValue(self, newval: float) -> int:
            """
            Changes the current expected position of the quadrature decoder.
            Invoking this function implicitly activates the quadrature decoder.

            @param newval : a floating point number corresponding to the current expected position of the quadrature decoder

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_currentValue(newval))

    if not _DYNAMIC_HELPERS:
        def get_speed(self) -> float:
            """
            Returns the cycle frequency, in Hz.

            @return a floating point number corresponding to the cycle frequency, in Hz

            On failure, throws an exception or returns YQuadratureDecoder.SPEED_INVALID.
            """
            return self._run(self._aio.get_speed())

    if not _DYNAMIC_HELPERS:
        def get_decoding(self) -> int:
            """
            Returns the current activation state of the quadrature decoder.

            @return either YQuadratureDecoder.DECODING_OFF or YQuadratureDecoder.DECODING_ON, according to the
            current activation state of the quadrature decoder

            On failure, throws an exception or returns YQuadratureDecoder.DECODING_INVALID.
            """
            return self._run(self._aio.get_decoding())

    if not _DYNAMIC_HELPERS:
        def set_decoding(self, newval: int) -> int:
            """
            Changes the activation state of the quadrature decoder.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : either YQuadratureDecoder.DECODING_OFF or YQuadratureDecoder.DECODING_ON, according
            to the activation state of the quadrature decoder

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_decoding(newval))

    if not _DYNAMIC_HELPERS:
        def get_edgesPerCycle(self) -> int:
            """
            Returns the edge count per full cycle configuration setting.

            @return an integer corresponding to the edge count per full cycle configuration setting

            On failure, throws an exception or returns YQuadratureDecoder.EDGESPERCYCLE_INVALID.
            """
            return self._run(self._aio.get_edgesPerCycle())

    if not _DYNAMIC_HELPERS:
        def set_edgesPerCycle(self, newval: int) -> int:
            """
            Changes the edge count per full cycle configuration setting.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the edge count per full cycle configuration setting

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_edgesPerCycle(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YQuadratureDecoderValueCallback) -> int:
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
        def registerTimedReportCallback(self, callback: YQuadratureDecoderTimedReportCallback) -> int:
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

    # --- (end of YQuadratureDecoder implementation)

