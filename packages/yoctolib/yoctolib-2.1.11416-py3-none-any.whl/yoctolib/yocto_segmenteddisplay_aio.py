# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YSegmentedDisplay
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
Yoctopuce library: Asyncio implementation of YSegmentedDisplay
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YSegmentedDisplay
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

# --- (YSegmentedDisplay class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSegmentedDisplayValueCallback = Union[Callable[['YSegmentedDisplay', str], Any], None]
    except TypeError:
        YSegmentedDisplayValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSegmentedDisplay(YFunction):
    """
    The SegmentedDisplay class allows you to drive segmented displays.

    """
    # --- (end of YSegmentedDisplay class start)
    if not _IS_MICROPYTHON:
        # --- (YSegmentedDisplay return codes)
        DISPLAYEDTEXT_INVALID: Final[str] = YAPI.INVALID_STRING
        DISPLAYMODE_DISCONNECTED: Final[int] = 0
        DISPLAYMODE_MANUAL: Final[int] = 1
        DISPLAYMODE_AUTO1: Final[int] = 2
        DISPLAYMODE_AUTO60: Final[int] = 3
        DISPLAYMODE_INVALID: Final[int] = -1
        # --- (end of YSegmentedDisplay return codes)

    # --- (YSegmentedDisplay attributes declaration)
    _valueCallback: YSegmentedDisplayValueCallback
    # --- (end of YSegmentedDisplay attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'SegmentedDisplay', func)
        # --- (YSegmentedDisplay constructor)
        # --- (end of YSegmentedDisplay constructor)

    # --- (YSegmentedDisplay implementation)
    @classmethod
    def FindSegmentedDisplay(cls, func: str) -> YSegmentedDisplay:
        """
        Retrieves a segmented display for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the segmented display is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSegmentedDisplay.isOnline() to test if the segmented display is
        indeed online at a given time. In case of ambiguity when looking for
        a segmented display by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the segmented display, for instance
                MyDevice.segmentedDisplay.

        @return a YSegmentedDisplay object allowing you to drive the segmented display.
        """
        return cls.FindSegmentedDisplayInContext(YAPI, func)

    @classmethod
    def FindSegmentedDisplayInContext(cls, yctx: YAPIContext, func: str) -> YSegmentedDisplay:
        """
        Retrieves a segmented display for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the segmented display is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSegmentedDisplay.isOnline() to test if the segmented display is
        indeed online at a given time. In case of ambiguity when looking for
        a segmented display by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the segmented display, for instance
                MyDevice.segmentedDisplay.

        @return a YSegmentedDisplay object allowing you to drive the segmented display.
        """
        obj: Union[YSegmentedDisplay, None] = yctx._findInCache('SegmentedDisplay', func)
        if obj:
            return obj
        return YSegmentedDisplay(yctx, func)

    @classmethod
    def FirstSegmentedDisplay(cls) -> Union[YSegmentedDisplay, None]:
        """
        Starts the enumeration of segmented displays currently accessible.
        Use the method YSegmentedDisplay.nextSegmentedDisplay() to iterate on
        next segmented displays.

        @return a pointer to a YSegmentedDisplay object, corresponding to
                the first segmented display currently online, or a None pointer
                if there are none.
        """
        return cls.FirstSegmentedDisplayInContext(YAPI)

    @classmethod
    def FirstSegmentedDisplayInContext(cls, yctx: YAPIContext) -> Union[YSegmentedDisplay, None]:
        """
        Starts the enumeration of segmented displays currently accessible.
        Use the method YSegmentedDisplay.nextSegmentedDisplay() to iterate on
        next segmented displays.

        @param yctx : a YAPI context.

        @return a pointer to a YSegmentedDisplay object, corresponding to
                the first segmented display currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('SegmentedDisplay')
        if hwid:
            return cls.FindSegmentedDisplayInContext(yctx, hwid2str(hwid))
        return None

    def nextSegmentedDisplay(self) -> Union[YSegmentedDisplay, None]:
        """
        Continues the enumeration of segmented displays started using yFirstSegmentedDisplay().
        Caution: You can't make any assumption about the returned segmented displays order.
        If you want to find a specific a segmented display, use SegmentedDisplay.findSegmentedDisplay()
        and a hardwareID or a logical name.

        @return a pointer to a YSegmentedDisplay object, corresponding to
                a segmented display currently online, or a None pointer
                if there are no more segmented displays to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('SegmentedDisplay', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindSegmentedDisplayInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_displayedText(self) -> str:
        """
        Returns the text currently displayed on the screen.

        @return a string corresponding to the text currently displayed on the screen

        On failure, throws an exception or returns YSegmentedDisplay.DISPLAYEDTEXT_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("displayedText")
        if json_val is None:
            return YSegmentedDisplay.DISPLAYEDTEXT_INVALID
        return json_val

    async def set_displayedText(self, newval: str) -> int:
        """
        Changes the text currently displayed on the screen.

        @param newval : a string corresponding to the text currently displayed on the screen

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("displayedText", rest_val)

    async def get_displayMode(self) -> int:
        json_val: Union[int, None] = await self._fromCache("displayMode")
        if json_val is None:
            return YSegmentedDisplay.DISPLAYMODE_INVALID
        return json_val

    async def set_displayMode(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("displayMode", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YSegmentedDisplayValueCallback) -> int:
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

    # --- (end of YSegmentedDisplay implementation)

