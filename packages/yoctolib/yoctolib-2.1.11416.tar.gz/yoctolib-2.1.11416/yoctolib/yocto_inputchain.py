# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YInputChain
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
Yoctopuce library: High-level API for YInputChain
version: PATCH_WITH_VERSION
requires: yocto_inputchain_aio
requires: yocto_api
provides: YInputChain
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

from .yocto_inputchain_aio import YInputChain as YInputChain_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, xarray, YFunction
)

def yInternalEventCallback(obj: YInputChain, value: str):
    obj._internalEventHandler(value)

# --- (YInputChain class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YInputChainValueCallback = Union[Callable[['YInputChain', str], Any], None]
        YStateChangeCallback = Union[Callable[['YInputChain',int , str, str, str], Any], None]
    except TypeError:
        YInputChainValueCallback = Union[Callable, Awaitable]
        YStateChangeCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YInputChain(YFunction):
    """
    The YInputChain class provides access to separate
    digital inputs connected in a chain.

    """
    _aio: YInputChain_aio
    # --- (end of YInputChain class start)
    if not _IS_MICROPYTHON:
        # --- (YInputChain return codes)
        EXPECTEDNODES_INVALID: Final[int] = YAPI.INVALID_UINT
        DETECTEDNODES_INVALID: Final[int] = YAPI.INVALID_UINT
        REFRESHRATE_INVALID: Final[int] = YAPI.INVALID_UINT
        BITCHAIN1_INVALID: Final[str] = YAPI.INVALID_STRING
        BITCHAIN2_INVALID: Final[str] = YAPI.INVALID_STRING
        BITCHAIN3_INVALID: Final[str] = YAPI.INVALID_STRING
        BITCHAIN4_INVALID: Final[str] = YAPI.INVALID_STRING
        BITCHAIN5_INVALID: Final[str] = YAPI.INVALID_STRING
        BITCHAIN6_INVALID: Final[str] = YAPI.INVALID_STRING
        BITCHAIN7_INVALID: Final[str] = YAPI.INVALID_STRING
        WATCHDOGPERIOD_INVALID: Final[int] = YAPI.INVALID_UINT
        CHAINDIAGS_INVALID: Final[int] = YAPI.INVALID_UINT
        LOOPBACKTEST_OFF: Final[int] = 0
        LOOPBACKTEST_ON: Final[int] = 1
        LOOPBACKTEST_INVALID: Final[int] = -1
        # --- (end of YInputChain return codes)


    # --- (YInputChain implementation)

    @classmethod
    def FindInputChain(cls, func: str) -> YInputChain:
        """
        Retrieves a digital input chain for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the digital input chain is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YInputChain.isOnline() to test if the digital input chain is
        indeed online at a given time. In case of ambiguity when looking for
        a digital input chain by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the digital input chain, for instance
                MyDevice.inputChain.

        @return a YInputChain object allowing you to drive the digital input chain.
        """
        return cls._proxy(cls, YInputChain_aio.FindInputChainInContext(YAPI_aio, func))

    @classmethod
    def FindInputChainInContext(cls, yctx: YAPIContext, func: str) -> YInputChain:
        """
        Retrieves a digital input chain for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the digital input chain is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YInputChain.isOnline() to test if the digital input chain is
        indeed online at a given time. In case of ambiguity when looking for
        a digital input chain by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the digital input chain, for instance
                MyDevice.inputChain.

        @return a YInputChain object allowing you to drive the digital input chain.
        """
        return cls._proxy(cls, YInputChain_aio.FindInputChainInContext(yctx._aio, func))

    @classmethod
    def FirstInputChain(cls) -> Union[YInputChain, None]:
        """
        Starts the enumeration of digital input chains currently accessible.
        Use the method YInputChain.nextInputChain() to iterate on
        next digital input chains.

        @return a pointer to a YInputChain object, corresponding to
                the first digital input chain currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YInputChain_aio.FirstInputChainInContext(YAPI_aio))

    @classmethod
    def FirstInputChainInContext(cls, yctx: YAPIContext) -> Union[YInputChain, None]:
        """
        Starts the enumeration of digital input chains currently accessible.
        Use the method YInputChain.nextInputChain() to iterate on
        next digital input chains.

        @param yctx : a YAPI context.

        @return a pointer to a YInputChain object, corresponding to
                the first digital input chain currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YInputChain_aio.FirstInputChainInContext(yctx._aio))

    def nextInputChain(self) -> Union[YInputChain, None]:
        """
        Continues the enumeration of digital input chains started using yFirstInputChain().
        Caution: You can't make any assumption about the returned digital input chains order.
        If you want to find a specific a digital input chain, use InputChain.findInputChain()
        and a hardwareID or a logical name.

        @return a pointer to a YInputChain object, corresponding to
                a digital input chain currently online, or a None pointer
                if there are no more digital input chains to enumerate.
        """
        return self._proxy(type(self), self._aio.nextInputChain())

    if not _DYNAMIC_HELPERS:
        def get_expectedNodes(self) -> int:
            """
            Returns the number of nodes expected in the chain.

            @return an integer corresponding to the number of nodes expected in the chain

            On failure, throws an exception or returns YInputChain.EXPECTEDNODES_INVALID.
            """
            return self._run(self._aio.get_expectedNodes())

    if not _DYNAMIC_HELPERS:
        def set_expectedNodes(self, newval: int) -> int:
            """
            Changes the number of nodes expected in the chain.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the number of nodes expected in the chain

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_expectedNodes(newval))

    if not _DYNAMIC_HELPERS:
        def get_detectedNodes(self) -> int:
            """
            Returns the number of nodes detected in the chain.

            @return an integer corresponding to the number of nodes detected in the chain

            On failure, throws an exception or returns YInputChain.DETECTEDNODES_INVALID.
            """
            return self._run(self._aio.get_detectedNodes())

    if not _DYNAMIC_HELPERS:
        def get_loopbackTest(self) -> int:
            """
            Returns the activation state of the exhaustive chain connectivity test.
            The connectivity test requires a cable connecting the end of the chain
            to the loopback test connector.

            @return either YInputChain.LOOPBACKTEST_OFF or YInputChain.LOOPBACKTEST_ON, according to the
            activation state of the exhaustive chain connectivity test

            On failure, throws an exception or returns YInputChain.LOOPBACKTEST_INVALID.
            """
            return self._run(self._aio.get_loopbackTest())

    if not _DYNAMIC_HELPERS:
        def set_loopbackTest(self, newval: int) -> int:
            """
            Changes the activation state of the exhaustive chain connectivity test.
            The connectivity test requires a cable connecting the end of the chain
            to the loopback test connector.

            If you want the change to be kept after a device reboot,
            make sure  to call the matching module saveToFlash().

            @param newval : either YInputChain.LOOPBACKTEST_OFF or YInputChain.LOOPBACKTEST_ON, according to
            the activation state of the exhaustive chain connectivity test

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_loopbackTest(newval))

    if not _DYNAMIC_HELPERS:
        def get_refreshRate(self) -> int:
            """
            Returns the desired refresh rate, measured in Hz.
            The higher the refresh rate is set, the higher the
            communication speed on the chain will be.

            @return an integer corresponding to the desired refresh rate, measured in Hz

            On failure, throws an exception or returns YInputChain.REFRESHRATE_INVALID.
            """
            return self._run(self._aio.get_refreshRate())

    if not _DYNAMIC_HELPERS:
        def set_refreshRate(self, newval: int) -> int:
            """
            Changes the desired refresh rate, measured in Hz.
            The higher the refresh rate is set, the higher the
            communication speed on the chain will be.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the desired refresh rate, measured in Hz

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_refreshRate(newval))

    if not _DYNAMIC_HELPERS:
        def get_bitChain1(self) -> str:
            """
            Returns the state of input 1 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 1 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN1_INVALID.
            """
            return self._run(self._aio.get_bitChain1())

    if not _DYNAMIC_HELPERS:
        def get_bitChain2(self) -> str:
            """
            Returns the state of input 2 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 2 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN2_INVALID.
            """
            return self._run(self._aio.get_bitChain2())

    if not _DYNAMIC_HELPERS:
        def get_bitChain3(self) -> str:
            """
            Returns the state of input 3 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 3 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN3_INVALID.
            """
            return self._run(self._aio.get_bitChain3())

    if not _DYNAMIC_HELPERS:
        def get_bitChain4(self) -> str:
            """
            Returns the state of input 4 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 4 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN4_INVALID.
            """
            return self._run(self._aio.get_bitChain4())

    if not _DYNAMIC_HELPERS:
        def get_bitChain5(self) -> str:
            """
            Returns the state of input 5 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 5 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN5_INVALID.
            """
            return self._run(self._aio.get_bitChain5())

    if not _DYNAMIC_HELPERS:
        def get_bitChain6(self) -> str:
            """
            Returns the state of input 6 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 6 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN6_INVALID.
            """
            return self._run(self._aio.get_bitChain6())

    if not _DYNAMIC_HELPERS:
        def get_bitChain7(self) -> str:
            """
            Returns the state of input 7 for all nodes of the input chain,
            as a hexadecimal string. The node nearest to the controller
            is the lowest bit of the result.

            @return a string corresponding to the state of input 7 for all nodes of the input chain,
                    as a hexadecimal string

            On failure, throws an exception or returns YInputChain.BITCHAIN7_INVALID.
            """
            return self._run(self._aio.get_bitChain7())

    if not _DYNAMIC_HELPERS:
        def get_watchdogPeriod(self) -> int:
            """
            Returns the wait time in seconds before triggering an inactivity
            timeout error.

            @return an integer corresponding to the wait time in seconds before triggering an inactivity
                    timeout error

            On failure, throws an exception or returns YInputChain.WATCHDOGPERIOD_INVALID.
            """
            return self._run(self._aio.get_watchdogPeriod())

    if not _DYNAMIC_HELPERS:
        def set_watchdogPeriod(self, newval: int) -> int:
            """
            Changes the wait time in seconds before triggering an inactivity
            timeout error. Remember to call the saveToFlash() method
            of the module if the modification must be kept.

            @param newval : an integer corresponding to the wait time in seconds before triggering an inactivity
                    timeout error

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_watchdogPeriod(newval))

    if not _DYNAMIC_HELPERS:
        def get_chainDiags(self) -> int:
            """
            Returns the controller state diagnostics. Bit 0 indicates a chain length
            error, bit 1 indicates an inactivity timeout and bit 2 indicates
            a loopback test failure.

            @return an integer corresponding to the controller state diagnostics

            On failure, throws an exception or returns YInputChain.CHAINDIAGS_INVALID.
            """
            return self._run(self._aio.get_chainDiags())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YInputChainValueCallback) -> int:
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
        def resetWatchdog(self) -> int:
            """
            Resets the application watchdog countdown.
            If you have set up a non-zero watchdogPeriod, you should
            call this function on a regular basis to prevent the application
            inactivity error to be triggered.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.resetWatchdog())

    if not _DYNAMIC_HELPERS:
        def get_lastEvents(self) -> str:
            """
            Returns a string with last events observed on the digital input chain.
            This method return only events that are still buffered in the device memory.

            @return a string with last events observed (one per line).

            On failure, throws an exception or returns  YAPI.INVALID_STRING.
            """
            return self._run(self._aio.get_lastEvents())

    def registerStateChangeCallback(self, callback: YStateChangeCallback) -> int:
        """
        Registers a callback function to be called each time that an event is detected on the
        input chain.The callback is invoked only during the execution of
        ySleep or yHandleEvents. This provides control over the time when
        the callback is triggered. For good responsiveness, remember to call one of these
        two functions periodically. To unregister a callback, pass a None pointer as argument.

        @param callback : the callback function to call, or a None pointer.
                The callback function should take four arguments:
                the YInputChain object that emitted the event, the
                UTC timestamp of the event, a character string describing
                the type of event and a character string with the event data.
                On failure, throws an exception or returns a negative error code.
        """
        if callback:
            self.registerValueCallback(yInternalEventCallback)
        else:
            self.registerValueCallback(None)
        # register user callback AFTER the internal pseudo-event,
        # to make sure we start with future events only
        self._aio._stateChangeCallback = callback
        return 0

    def _internalEventHandler(self, cbpos: str) -> int:
        newPos: int
        url: str
        content: xarray
        contentStr: str
        eventArr: list[str] = []
        arrLen: int
        lenStr: str
        arrPos: int
        eventStr: str
        eventLen: int
        hexStamp: str
        typePos: int
        dataPos: int
        evtStamp: int
        evtType: str
        evtData: str
        evtChange: str
        chainIdx: int
        newPos = YAPI._atoi(cbpos)
        if newPos < self._prevPos:
            self._eventPos = 0
        self._prevPos = newPos
        if newPos < self._eventPos:
            return YAPI.SUCCESS
        if not self._aio._stateChangeCallback:
            # first simulated event, use it to initialize reference values
            self._eventPos = newPos
            del self._eventChains[:]
            self._eventChains.append(self.get_bitChain1())
            self._eventChains.append(self.get_bitChain2())
            self._eventChains.append(self.get_bitChain3())
            self._eventChains.append(self.get_bitChain4())
            self._eventChains.append(self.get_bitChain5())
            self._eventChains.append(self.get_bitChain6())
            self._eventChains.append(self.get_bitChain7())
            return YAPI.SUCCESS
        url = "events.txt?pos=%d" % self._eventPos

        content = self._download(url)
        contentStr = content.decode('latin-1')
        eventArr = (contentStr).split('\n')
        arrLen = len(eventArr)
        if not (arrLen > 0):
            self._throw(YAPI.IO_ERROR, "fail to download events")
            return YAPI.IO_ERROR
        # last element of array is the new position preceeded by '@'
        arrLen = arrLen - 1
        lenStr = eventArr[arrLen]
        lenStr = lenStr[1: 1 + len(lenStr)-1]
        # update processed event position pointer
        self._eventPos = YAPI._atoi(lenStr)
        # now generate callbacks for each event received
        arrPos = 0
        while arrPos < arrLen:
            eventStr = eventArr[arrPos]
            eventLen = len(eventStr)
            if eventLen >= 1:
                hexStamp = eventStr[0: 0 + 8]
                evtStamp = int(hexStamp, 16)
                typePos = eventStr.find(":")+1
                if (evtStamp >= self._eventStamp) and (typePos > 8):
                    self._eventStamp = evtStamp
                    dataPos = eventStr.find("=")+1
                    evtType = eventStr[typePos: typePos + 1]
                    evtData = ""
                    evtChange = ""
                    if dataPos > 10:
                        evtData = eventStr[dataPos: dataPos + len(eventStr)-dataPos]
                        if ("1234567").find(evtType) >= 0:
                            chainIdx = YAPI._atoi(evtType) - 1
                            evtChange = self._strXor(evtData, self._eventChains[chainIdx])
                            self._eventChains[chainIdx] = evtData
                    try:
                        retval = self._aio._stateChangeCallback(self, evtStamp, evtType, evtData, evtChange)
                        if retval is not None: self._run(retval)
                    # noinspection PyBroadException
                    except Exception as e:
                        print('Exception in %s.stateChangeCallback:' % type(self).__name__, type(e).__name__, e)
            arrPos = arrPos + 1
        return YAPI.SUCCESS

    # --- (end of YInputChain implementation)

