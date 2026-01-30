# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YColorLed
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
Yoctopuce library: High-level API for YColorLed
version: PATCH_WITH_VERSION
requires: yocto_colorled_aio
requires: yocto_api
provides: YColorLed
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

from .yocto_colorled_aio import YColorLed as YColorLed_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YColorLed class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YColorLedValueCallback = Union[Callable[['YColorLed', str], Any], None]
    except TypeError:
        YColorLedValueCallback = Union[Callable, Awaitable]
if _IS_MICROPYTHON:
    from collections import namedtuple
    YMove = namedtuple("YMove", ('target', 'ms', 'moving'))
else:
    from typing import NamedTuple
    class YMove(NamedTuple):
        target: int
        ms: int
        moving: int


# noinspection PyProtectedMember
class YColorLed(YFunction):
    """
    The ColorLed class allows you to drive a color LED.
    The color can be specified using RGB coordinates as well as HSL coordinates.
    The module performs all conversions form RGB to HSL automatically. It is then
    self-evident to turn on a LED with a given hue and to progressively vary its
    saturation or lightness. If needed, you can find more information on the
    difference between RGB and HSL in the section following this one.

    """
    _aio: YColorLed_aio
    # --- (end of YColorLed class start)
    if not _IS_MICROPYTHON:
        # --- (YColorLed return codes)
        RGBCOLOR_INVALID: Final[int] = YAPI.INVALID_UINT
        HSLCOLOR_INVALID: Final[int] = YAPI.INVALID_UINT
        RGBMOVE_INVALID: Final[None] = None
        HSLMOVE_INVALID: Final[None] = None
        RGBCOLORATPOWERON_INVALID: Final[int] = YAPI.INVALID_UINT
        BLINKSEQSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        BLINKSEQMAXSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        BLINKSEQSIGNATURE_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of YColorLed return codes)


    # --- (YColorLed implementation)

    @classmethod
    def FindColorLed(cls, func: str) -> YColorLed:
        """
        Retrieves an RGB LED for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the RGB LED is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YColorLed.isOnline() to test if the RGB LED is
        indeed online at a given time. In case of ambiguity when looking for
        an RGB LED by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the RGB LED, for instance
                YRGBLED2.colorLed1.

        @return a YColorLed object allowing you to drive the RGB LED.
        """
        return cls._proxy(cls, YColorLed_aio.FindColorLedInContext(YAPI_aio, func))

    @classmethod
    def FindColorLedInContext(cls, yctx: YAPIContext, func: str) -> YColorLed:
        """
        Retrieves an RGB LED for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the RGB LED is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YColorLed.isOnline() to test if the RGB LED is
        indeed online at a given time. In case of ambiguity when looking for
        an RGB LED by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the RGB LED, for instance
                YRGBLED2.colorLed1.

        @return a YColorLed object allowing you to drive the RGB LED.
        """
        return cls._proxy(cls, YColorLed_aio.FindColorLedInContext(yctx._aio, func))

    @classmethod
    def FirstColorLed(cls) -> Union[YColorLed, None]:
        """
        Starts the enumeration of RGB LEDs currently accessible.
        Use the method YColorLed.nextColorLed() to iterate on
        next RGB LEDs.

        @return a pointer to a YColorLed object, corresponding to
                the first RGB LED currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YColorLed_aio.FirstColorLedInContext(YAPI_aio))

    @classmethod
    def FirstColorLedInContext(cls, yctx: YAPIContext) -> Union[YColorLed, None]:
        """
        Starts the enumeration of RGB LEDs currently accessible.
        Use the method YColorLed.nextColorLed() to iterate on
        next RGB LEDs.

        @param yctx : a YAPI context.

        @return a pointer to a YColorLed object, corresponding to
                the first RGB LED currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YColorLed_aio.FirstColorLedInContext(yctx._aio))

    def nextColorLed(self) -> Union[YColorLed, None]:
        """
        Continues the enumeration of RGB LEDs started using yFirstColorLed().
        Caution: You can't make any assumption about the returned RGB LEDs order.
        If you want to find a specific an RGB LED, use ColorLed.findColorLed()
        and a hardwareID or a logical name.

        @return a pointer to a YColorLed object, corresponding to
                an RGB LED currently online, or a None pointer
                if there are no more RGB LEDs to enumerate.
        """
        return self._proxy(type(self), self._aio.nextColorLed())

    if not _DYNAMIC_HELPERS:
        def get_rgbColor(self) -> int:
            """
            Returns the current RGB color of the LED.

            @return an integer corresponding to the current RGB color of the LED

            On failure, throws an exception or returns YColorLed.RGBCOLOR_INVALID.
            """
            return self._run(self._aio.get_rgbColor())

    if not _DYNAMIC_HELPERS:
        def set_rgbColor(self, newval: int) -> int:
            """
            Changes the current color of the LED, using an RGB color. Encoding is done as follows: 0xRRGGBB.

            @param newval : an integer corresponding to the current color of the LED, using an RGB color

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_rgbColor(newval))

    if not _DYNAMIC_HELPERS:
        def get_hslColor(self) -> int:
            """
            Returns the current HSL color of the LED.

            @return an integer corresponding to the current HSL color of the LED

            On failure, throws an exception or returns YColorLed.HSLCOLOR_INVALID.
            """
            return self._run(self._aio.get_hslColor())

    if not _DYNAMIC_HELPERS:
        def set_hslColor(self, newval: int) -> int:
            """
            Changes the current color of the LED, using a specific HSL color. Encoding is done as follows: 0xHHSSLL.

            @param newval : an integer corresponding to the current color of the LED, using a specific HSL color

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_hslColor(newval))

    if not _DYNAMIC_HELPERS:
        def set_rgbMove(self, newval: YMove) -> int:
            return self._run(self._aio.set_rgbMove(newval))

    if not _DYNAMIC_HELPERS:
        def rgbMove(self, rgb_target, ms_duration) -> int:
            """
            Performs a smooth transition in the RGB color space between the current color and a target color.

            @param rgb_target  : desired RGB color at the end of the transition
            @param ms_duration : duration of the transition, in millisecond

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.rgbMove(rgb_target, ms_duration))

    if not _DYNAMIC_HELPERS:
        def set_hslMove(self, newval: YMove) -> int:
            return self._run(self._aio.set_hslMove(newval))

    if not _DYNAMIC_HELPERS:
        def hslMove(self, hsl_target, ms_duration) -> int:
            """
            Performs a smooth transition in the HSL color space between the current color and a target color.

            @param hsl_target  : desired HSL color at the end of the transition
            @param ms_duration : duration of the transition, in millisecond

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.hslMove(hsl_target, ms_duration))

    if not _DYNAMIC_HELPERS:
        def get_rgbColorAtPowerOn(self) -> int:
            """
            Returns the configured color to be displayed when the module is turned on.

            @return an integer corresponding to the configured color to be displayed when the module is turned on

            On failure, throws an exception or returns YColorLed.RGBCOLORATPOWERON_INVALID.
            """
            return self._run(self._aio.get_rgbColorAtPowerOn())

    if not _DYNAMIC_HELPERS:
        def set_rgbColorAtPowerOn(self, newval: int) -> int:
            """
            Changes the color that the LED displays by default when the module is turned on.
            Remember to call the saveLedsConfigAtPowerOn() method of the module if the modification must be kept.
            Note: for the original modules Yocto-Color (version 1) et Yocto-PowerColor, the  saveToFlash()
            method must be used instead.

            @param newval : an integer corresponding to the color that the LED displays by default when the
            module is turned on

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_rgbColorAtPowerOn(newval))

    if not _DYNAMIC_HELPERS:
        def get_blinkSeqSize(self) -> int:
            """
            Returns the current length of the blinking sequence.

            @return an integer corresponding to the current length of the blinking sequence

            On failure, throws an exception or returns YColorLed.BLINKSEQSIZE_INVALID.
            """
            return self._run(self._aio.get_blinkSeqSize())

    if not _DYNAMIC_HELPERS:
        def get_blinkSeqMaxSize(self) -> int:
            """
            Returns the maximum length of the blinking sequence.

            @return an integer corresponding to the maximum length of the blinking sequence

            On failure, throws an exception or returns YColorLed.BLINKSEQMAXSIZE_INVALID.
            """
            return self._run(self._aio.get_blinkSeqMaxSize())

    if not _DYNAMIC_HELPERS:
        def get_blinkSeqSignature(self) -> int:
            """
            Returns the blinking sequence signature. Since blinking
            sequences cannot be read from the device, this can be used
            to detect if a specific blinking sequence is already
            programmed.

            @return an integer corresponding to the blinking sequence signature

            On failure, throws an exception or returns YColorLed.BLINKSEQSIGNATURE_INVALID.
            """
            return self._run(self._aio.get_blinkSeqSignature())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YColorLedValueCallback) -> int:
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
        def addHslMoveToBlinkSeq(self, HSLcolor: int, msDelay: int) -> int:
            """
            Add a new transition to the blinking sequence, the move will
            be performed in the HSL space.

            @param HSLcolor : desired HSL color when the transition is completed
            @param msDelay : duration of the color transition, in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.addHslMoveToBlinkSeq(HSLcolor, msDelay))

    if not _DYNAMIC_HELPERS:
        def addRgbMoveToBlinkSeq(self, RGBcolor: int, msDelay: int) -> int:
            """
            Adds a new transition to the blinking sequence, the move is
            performed in the RGB space.

            @param RGBcolor : desired RGB color when the transition is completed
            @param msDelay : duration of the color transition, in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.addRgbMoveToBlinkSeq(RGBcolor, msDelay))

    if not _DYNAMIC_HELPERS:
        def startBlinkSeq(self) -> int:
            """
            Starts the preprogrammed blinking sequence. The sequence is
            run in a loop until it is stopped by stopBlinkSeq or an explicit
            change.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.startBlinkSeq())

    if not _DYNAMIC_HELPERS:
        def stopBlinkSeq(self) -> int:
            """
            Stops the preprogrammed blinking sequence.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.stopBlinkSeq())

    if not _DYNAMIC_HELPERS:
        def resetBlinkSeq(self) -> int:
            """
            Resets the preprogrammed blinking sequence.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.resetBlinkSeq())

    if not _DYNAMIC_HELPERS:
        def saveLedsConfigAtPowerOn(self) -> int:
            """
            Saves the LEDs power-on configuration.  Warning: this method is not supported by
            Yocto-Color (version 1) and Yocto-PowerColor modules. For these devices, the saveToFlash()
            method of the module must be used instead.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.saveLedsConfigAtPowerOn())

    # --- (end of YColorLed implementation)

