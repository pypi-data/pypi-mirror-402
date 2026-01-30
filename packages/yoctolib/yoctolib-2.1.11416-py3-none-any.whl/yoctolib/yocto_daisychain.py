# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YDaisyChain
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
Yoctopuce library: High-level API for YDaisyChain
version: PATCH_WITH_VERSION
requires: yocto_daisychain_aio
requires: yocto_api
provides: YDaisyChain
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

from .yocto_daisychain_aio import YDaisyChain as YDaisyChain_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YDaisyChain class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YDaisyChainValueCallback = Union[Callable[['YDaisyChain', str], Any], None]
    except TypeError:
        YDaisyChainValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YDaisyChain(YFunction):
    """
    The YDaisyChain class can be used to verify that devices that
    are daisy-chained directly from device to device, without a hub,
    are detected properly.

    """
    _aio: YDaisyChain_aio
    # --- (end of YDaisyChain class start)
    if not _IS_MICROPYTHON:
        # --- (YDaisyChain return codes)
        CHILDCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        REQUIREDCHILDCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        DAISYSTATE_READY: Final[int] = 0
        DAISYSTATE_IS_CHILD: Final[int] = 1
        DAISYSTATE_FIRMWARE_MISMATCH: Final[int] = 2
        DAISYSTATE_CHILD_MISSING: Final[int] = 3
        DAISYSTATE_CHILD_LOST: Final[int] = 4
        DAISYSTATE_INVALID: Final[int] = -1
        # --- (end of YDaisyChain return codes)


    # --- (YDaisyChain implementation)

    @classmethod
    def FindDaisyChain(cls, func: str) -> YDaisyChain:
        """
        Retrieves a module chain for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the module chain is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDaisyChain.isOnline() to test if the module chain is
        indeed online at a given time. In case of ambiguity when looking for
        a module chain by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the module chain, for instance
                MyDevice.daisyChain.

        @return a YDaisyChain object allowing you to drive the module chain.
        """
        return cls._proxy(cls, YDaisyChain_aio.FindDaisyChainInContext(YAPI_aio, func))

    @classmethod
    def FindDaisyChainInContext(cls, yctx: YAPIContext, func: str) -> YDaisyChain:
        """
        Retrieves a module chain for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the module chain is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDaisyChain.isOnline() to test if the module chain is
        indeed online at a given time. In case of ambiguity when looking for
        a module chain by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the module chain, for instance
                MyDevice.daisyChain.

        @return a YDaisyChain object allowing you to drive the module chain.
        """
        return cls._proxy(cls, YDaisyChain_aio.FindDaisyChainInContext(yctx._aio, func))

    @classmethod
    def FirstDaisyChain(cls) -> Union[YDaisyChain, None]:
        """
        Starts the enumeration of module chains currently accessible.
        Use the method YDaisyChain.nextDaisyChain() to iterate on
        next module chains.

        @return a pointer to a YDaisyChain object, corresponding to
                the first module chain currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDaisyChain_aio.FirstDaisyChainInContext(YAPI_aio))

    @classmethod
    def FirstDaisyChainInContext(cls, yctx: YAPIContext) -> Union[YDaisyChain, None]:
        """
        Starts the enumeration of module chains currently accessible.
        Use the method YDaisyChain.nextDaisyChain() to iterate on
        next module chains.

        @param yctx : a YAPI context.

        @return a pointer to a YDaisyChain object, corresponding to
                the first module chain currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDaisyChain_aio.FirstDaisyChainInContext(yctx._aio))

    def nextDaisyChain(self) -> Union[YDaisyChain, None]:
        """
        Continues the enumeration of module chains started using yFirstDaisyChain().
        Caution: You can't make any assumption about the returned module chains order.
        If you want to find a specific a module chain, use DaisyChain.findDaisyChain()
        and a hardwareID or a logical name.

        @return a pointer to a YDaisyChain object, corresponding to
                a module chain currently online, or a None pointer
                if there are no more module chains to enumerate.
        """
        return self._proxy(type(self), self._aio.nextDaisyChain())

    if not _DYNAMIC_HELPERS:
        def get_daisyState(self) -> int:
            """
            Returns the state of the daisy-link between modules.

            @return a value among YDaisyChain.DAISYSTATE_READY, YDaisyChain.DAISYSTATE_IS_CHILD,
            YDaisyChain.DAISYSTATE_FIRMWARE_MISMATCH, YDaisyChain.DAISYSTATE_CHILD_MISSING and
            YDaisyChain.DAISYSTATE_CHILD_LOST corresponding to the state of the daisy-link between modules

            On failure, throws an exception or returns YDaisyChain.DAISYSTATE_INVALID.
            """
            return self._run(self._aio.get_daisyState())

    if not _DYNAMIC_HELPERS:
        def get_childCount(self) -> int:
            """
            Returns the number of child nodes currently detected.

            @return an integer corresponding to the number of child nodes currently detected

            On failure, throws an exception or returns YDaisyChain.CHILDCOUNT_INVALID.
            """
            return self._run(self._aio.get_childCount())

    if not _DYNAMIC_HELPERS:
        def get_requiredChildCount(self) -> int:
            """
            Returns the number of child nodes expected in normal conditions.

            @return an integer corresponding to the number of child nodes expected in normal conditions

            On failure, throws an exception or returns YDaisyChain.REQUIREDCHILDCOUNT_INVALID.
            """
            return self._run(self._aio.get_requiredChildCount())

    if not _DYNAMIC_HELPERS:
        def set_requiredChildCount(self, newval: int) -> int:
            """
            Changes the number of child nodes expected in normal conditions.
            If the value is zero, no check is performed. If it is non-zero, the number
            child nodes is checked on startup and the status will change to error if
            the count does not match. Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the number of child nodes expected in normal conditions

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_requiredChildCount(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YDaisyChainValueCallback) -> int:
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

    # --- (end of YDaisyChain implementation)

