# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_display.py 71207 2026-01-07 18:17:59Z mvuilleu $
#
#  Implements the asyncio YDisplay API for Display functions
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
Yoctopuce library: High-level API for YDisplay and YDisplayLayer
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_display_aio
provides: YDisplay YDisplayLayer
"""
from __future__ import annotations
import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union, Final
    from collections.abc import Callable, Awaitable
    from enum import IntEnum
    const = lambda obj: obj
    _IS_MICROPYTHON = False
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True  # noqa
    _DYNAMIC_HELPERS: Final[bool] = True  # noqa

from .yocto_display_aio import (
    YDisplay as YDisplay_aio,
    YDisplayLayer as YDisplayLayer_aio
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction, YSyncProxy, xarray
)

# --- (generated code: YDisplayLayer class start)
# noinspection PyProtectedMember
class YDisplayLayer(YSyncProxy):
    """
    Each DisplayLayer represents an image layer containing objects
    to display (bitmaps, text, etc.). The content is displayed only when
    the layer is active on the screen (and not masked by other
    overlapping layers).

    """
    _aio: YDisplayLayer_aio
    # --- (end of generated code: YDisplayLayer class start)

    if not _IS_MICROPYTHON:
        # --- (generated code: YDisplayLayer return codes)
        class ALIGN(IntEnum):
            TOP_LEFT = 0
            CENTER_LEFT = 1
            BASELINE_LEFT = 2
            BOTTOM_LEFT = 3
            TOP_CENTER = 4
            CENTER = 5
            BASELINE_CENTER = 6
            BOTTOM_CENTER = 7
            TOP_DECIMAL = 8
            CENTER_DECIMAL = 9
            BASELINE_DECIMAL = 10
            BOTTOM_DECIMAL = 11
            TOP_RIGHT = 12
            CENTER_RIGHT = 13
            BASELINE_RIGHT = 14
            BOTTOM_RIGHT = 15

        # --- (end of generated code: YDisplayLayer return codes)

    # --- (generated code: YDisplayLayer implementation)
    if not _DYNAMIC_HELPERS:
        def reset(self) -> int:
            """
            Reverts the layer to its initial state (fully transparent, default settings).
            Reinitializes the drawing pointer to the upper left position,
            and selects the most visible pen color. If you only want to erase the layer
            content, use the method clear() instead.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reset())

    if not _DYNAMIC_HELPERS:
        def clear(self) -> int:
            """
            Erases the whole content of the layer (makes it fully transparent).
            This method does not change any other attribute of the layer.
            To reinitialize the layer attributes to defaults settings, use the method
            reset() instead.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.clear())

    if not _DYNAMIC_HELPERS:
        def selectColorPen(self, color: int) -> int:
            """
            Selects the pen color for all subsequent drawing functions,
            including text drawing. The pen color is provided as an RGB value.
            For grayscale or monochrome displays, the value is
            automatically converted to the proper range.

            @param color : the desired pen color, as a 24-bit RGB value

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.selectColorPen(color))

    if not _DYNAMIC_HELPERS:
        def selectGrayPen(self, graylevel: int) -> int:
            """
            Selects the pen gray level for all subsequent drawing functions,
            including text drawing. The gray level is provided as a number between
            0 (black) and 255 (white, or whichever the lightest color is).
            For monochrome displays (without gray levels), any value
            lower than 128 is rendered as black, and any value equal
            or above to 128 is non-black.

            @param graylevel : the desired gray level, from 0 to 255

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.selectGrayPen(graylevel))

    if not _DYNAMIC_HELPERS:
        def selectEraser(self) -> int:
            """
            Selects an eraser instead of a pen for all subsequent drawing functions,
            except for bitmap copy functions. Any point drawn using the eraser
            becomes transparent (as when the layer is empty), showing the other
            layers beneath it.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.selectEraser())

    if not _DYNAMIC_HELPERS:
        def setAntialiasingMode(self, mode: bool) -> int:
            """
            Enables or disables anti-aliasing for drawing oblique lines and circles.
            Anti-aliasing provides a smoother aspect when looked from far enough,
            but it can add fuzziness when the display is looked from very close.
            At the end of the day, it is your personal choice.
            Anti-aliasing is enabled by default on grayscale and color displays,
            but you can disable it if you prefer. This setting has no effect
            on monochrome displays.

            @param mode : true to enable anti-aliasing, false to
                    disable it.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.setAntialiasingMode(mode))

    if not _DYNAMIC_HELPERS:
        def drawPixel(self, x: int, y: int) -> int:
            """
            Draws a single pixel at the specified position.

            @param x : the distance from left of layer, in pixels
            @param y : the distance from top of layer, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawPixel(x, y))

    if not _DYNAMIC_HELPERS:
        def drawRect(self, x1: int, y1: int, x2: int, y2: int) -> int:
            """
            Draws an empty rectangle at a specified position.

            @param x1 : the distance from left of layer to the left border of the rectangle, in pixels
            @param y1 : the distance from top of layer to the top border of the rectangle, in pixels
            @param x2 : the distance from left of layer to the right border of the rectangle, in pixels
            @param y2 : the distance from top of layer to the bottom border of the rectangle, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawRect(x1, y1, x2, y2))

    if not _DYNAMIC_HELPERS:
        def drawBar(self, x1: int, y1: int, x2: int, y2: int) -> int:
            """
            Draws a filled rectangular bar at a specified position.

            @param x1 : the distance from left of layer to the left border of the rectangle, in pixels
            @param y1 : the distance from top of layer to the top border of the rectangle, in pixels
            @param x2 : the distance from left of layer to the right border of the rectangle, in pixels
            @param y2 : the distance from top of layer to the bottom border of the rectangle, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawBar(x1, y1, x2, y2))

    if not _DYNAMIC_HELPERS:
        def drawCircle(self, x: int, y: int, r: int) -> int:
            """
            Draws an empty circle at a specified position.

            @param x : the distance from left of layer to the center of the circle, in pixels
            @param y : the distance from top of layer to the center of the circle, in pixels
            @param r : the radius of the circle, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawCircle(x, y, r))

    if not _DYNAMIC_HELPERS:
        def drawDisc(self, x: int, y: int, r: int) -> int:
            """
            Draws a filled disc at a given position.

            @param x : the distance from left of layer to the center of the disc, in pixels
            @param y : the distance from top of layer to the center of the disc, in pixels
            @param r : the radius of the disc, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawDisc(x, y, r))

    if not _DYNAMIC_HELPERS:
        def selectFont(self, fontname: str) -> int:
            """
            Selects a font to use for the next text drawing functions, by providing the name of the
            font file. You can use a built-in font as well as a font file that you have previously
            uploaded to the device built-in memory. If you experience problems selecting a font
            file, check the device logs for any error message such as missing font file or bad font
            file format.

            @param fontname : the font file name, embedded fonts are 8x8.yfm, Small.yfm, Medium.yfm, Large.yfm
            (not available on Yocto-MiniDisplay).

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.selectFont(fontname))

    if not _DYNAMIC_HELPERS:
        def drawText(self, x: int, y: int, anchor: ALIGN, text: str) -> int:
            """
            Draws a text string at the specified position. The point of the text that is aligned
            to the specified pixel position is called the anchor point, and can be chosen among
            several options. Text is rendered from left to right, without implicit wrapping.

            @param x : the distance from left of layer to the text anchor point, in pixels
            @param y : the distance from top of layer to the text anchor point, in pixels
            @param anchor : the text anchor point, chosen among the YDisplayLayer.ALIGN enumeration:
                    YDisplayLayer.ALIGN.TOP_LEFT,         YDisplayLayer.ALIGN.CENTER_LEFT,
                    YDisplayLayer.ALIGN.BASELINE_LEFT,    YDisplayLayer.ALIGN.BOTTOM_LEFT,
                    YDisplayLayer.ALIGN.TOP_CENTER,       YDisplayLayer.ALIGN.CENTER,
                    YDisplayLayer.ALIGN.BASELINE_CENTER,  YDisplayLayer.ALIGN.BOTTOM_CENTER,
                    YDisplayLayer.ALIGN.TOP_DECIMAL,      YDisplayLayer.ALIGN.CENTER_DECIMAL,
                    YDisplayLayer.ALIGN.BASELINE_DECIMAL, YDisplayLayer.ALIGN.BOTTOM_DECIMAL,
                    YDisplayLayer.ALIGN.TOP_RIGHT,        YDisplayLayer.ALIGN.CENTER_RIGHT,
                    YDisplayLayer.ALIGN.BASELINE_RIGHT,   YDisplayLayer.ALIGN.BOTTOM_RIGHT.
            @param text : the text string to draw

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawText(x, y, anchor, text))

    if not _DYNAMIC_HELPERS:
        def drawImage(self, x: int, y: int, imagename: str) -> int:
            """
            Draws a GIF image at the specified position. The GIF image must have been previously
            uploaded to the device built-in memory. If you experience problems using an image
            file, check the device logs for any error message such as missing image file or bad
            image file format.

            @param x : the distance from left of layer to the left of the image, in pixels
            @param y : the distance from top of layer to the top of the image, in pixels
            @param imagename : the GIF file name

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawImage(x, y, imagename))

    if not _DYNAMIC_HELPERS:
        def drawBitmap(self, x: int, y: int, w: int, bitmap: xarray, bgcol: int) -> int:
            """
            Draws a bitmap at the specified position. The bitmap is provided as a binary object,
            where each pixel maps to a bit, from left to right and from top to bottom.
            The most significant bit of each byte maps to the leftmost pixel, and the least
            significant bit maps to the rightmost pixel. Bits set to 1 are drawn using the
            layer selected pen color. Bits set to 0 are drawn using the specified background
            gray level, unless -1 is specified, in which case they are not drawn at all
            (as if transparent).

            @param x : the distance from left of layer to the left of the bitmap, in pixels
            @param y : the distance from top of layer to the top of the bitmap, in pixels
            @param w : the width of the bitmap, in pixels
            @param bitmap : a binary object
            @param bgcol : the background gray level to use for zero bits (0 = black,
                    255 = white), or -1 to leave the pixels unchanged

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.drawBitmap(x, y, w, bitmap, bgcol))

    if not _DYNAMIC_HELPERS:
        def moveTo(self, x: int, y: int) -> int:
            """
            Moves the drawing pointer of this layer to the specified position.

            @param x : the distance from left of layer, in pixels
            @param y : the distance from top of layer, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.moveTo(x, y))

    if not _DYNAMIC_HELPERS:
        def lineTo(self, x: int, y: int) -> int:
            """
            Draws a line from current drawing pointer position to the specified position.
            The specified destination pixel is included in the line. The pointer position
            is then moved to the end point of the line.

            @param x : the distance from left of layer to the end point of the line, in pixels
            @param y : the distance from top of layer to the end point of the line, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.lineTo(x, y))

    if not _DYNAMIC_HELPERS:
        def consoleOut(self, text: str) -> int:
            """
            Outputs a message in the console area, and advances the console pointer accordingly.
            The console pointer position is automatically moved to the beginning
            of the next line when a newline character is met, or when the right margin
            is hit. When the new text to display extends below the lower margin, the
            console area is automatically scrolled up.

            @param text : the message to display

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.consoleOut(text))

    if not _DYNAMIC_HELPERS:
        def setConsoleMargins(self, x1: int, y1: int, x2: int, y2: int) -> int:
            """
            Sets up display margins for the consoleOut function.

            @param x1 : the distance from left of layer to the left margin, in pixels
            @param y1 : the distance from top of layer to the top margin, in pixels
            @param x2 : the distance from left of layer to the right margin, in pixels
            @param y2 : the distance from top of layer to the bottom margin, in pixels

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.setConsoleMargins(x1, y1, x2, y2))

    if not _DYNAMIC_HELPERS:
        def setConsoleBackground(self, bgcol: int) -> int:
            """
            Sets up the background color used by the clearConsole function and by
            the console scrolling feature.

            @param bgcol : the background gray level to use when scrolling (0 = black,
                    255 = white), or -1 for transparent

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.setConsoleBackground(bgcol))

    if not _DYNAMIC_HELPERS:
        def setConsoleWordWrap(self, wordwrap: bool) -> int:
            """
            Sets up the wrapping behavior used by the consoleOut function.

            @param wordwrap : true to wrap only between words,
                    false to wrap on the last column anyway.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.setConsoleWordWrap(wordwrap))

    if not _DYNAMIC_HELPERS:
        def clearConsole(self) -> int:
            """
            Blanks the console area within console margins, and resets the console pointer
            to the upper left corner of the console.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.clearConsole())

    if not _DYNAMIC_HELPERS:
        def setLayerPosition(self, x: int, y: int, scrollTime: int) -> int:
            """
            Sets the position of the layer relative to the display upper left corner.
            When smooth scrolling is used, the display offset of the layer is
            automatically updated during the next milliseconds to animate the move of the layer.

            @param x : the distance from left of display to the upper left corner of the layer
            @param y : the distance from top of display to the upper left corner of the layer
            @param scrollTime : number of milliseconds to use for smooth scrolling, or
                    0 if the scrolling should be immediate.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.setLayerPosition(x, y, scrollTime))

    if not _DYNAMIC_HELPERS:
        def hide(self) -> int:
            """
            Hides the layer. The state of the layer is preserved but the layer is not displayed
            on the screen until the next call to unhide(). Hiding the layer can positively
            affect the drawing speed, since it postpones the rendering until all operations are
            completed (double-buffering).

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.hide())

    if not _DYNAMIC_HELPERS:
        def unhide(self) -> int:
            """
            Shows the layer. Shows the layer again after a hide command.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.unhide())

    def get_display(self) -> YDisplay:
        """
        Gets parent YDisplay. Returns the parent YDisplay object of the current YDisplayLayer.

        @return an YDisplay object
        """
        return self._proxy(YDisplay, self._run(self._aio.get_display()))

    if not _DYNAMIC_HELPERS:
        def get_displayWidth(self) -> int:
            """
            Returns the display width, in pixels.

            @return an integer corresponding to the display width, in pixels

            On failure, throws an exception or returns YDisplayLayer.DISPLAYWIDTH_INVALID.
            """
            return self._run(self._aio.get_displayWidth())

    if not _DYNAMIC_HELPERS:
        def get_displayHeight(self) -> int:
            """
            Returns the display height, in pixels.

            @return an integer corresponding to the display height, in pixels

            On failure, throws an exception or returns YDisplayLayer.DISPLAYHEIGHT_INVALID.
            """
            return self._run(self._aio.get_displayHeight())

    if not _DYNAMIC_HELPERS:
        def get_layerWidth(self) -> int:
            """
            Returns the width of the layers to draw on, in pixels.

            @return an integer corresponding to the width of the layers to draw on, in pixels

            On failure, throws an exception or returns YDisplayLayer.LAYERWIDTH_INVALID.
            """
            return self._run(self._aio.get_layerWidth())

    if not _DYNAMIC_HELPERS:
        def get_layerHeight(self) -> int:
            """
            Returns the height of the layers to draw on, in pixels.

            @return an integer corresponding to the height of the layers to draw on, in pixels

            On failure, throws an exception or returns YDisplayLayer.LAYERHEIGHT_INVALID.
            """
            return self._run(self._aio.get_layerHeight())

    # --- (end of generated code: YDisplayLayer implementation)

# --- (generated code: YDisplay class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YDisplayValueCallback = Union[Callable[['YDisplay', str], Any], None]
    except TypeError:
        YDisplayValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YDisplay(YFunction):
    """
    The YDisplay class allows to drive Yoctopuce displays.
    Yoctopuce display interface has been designed to easily
    show information and images. The device provides built-in
    multi-layer rendering. Layers can be drawn offline, individually,
    and freely moved on the display. It can also replay recorded
    sequences (animations).

    In order to draw on the screen, you should use the
    display.get_displayLayer method to retrieve the layer(s) on
    which you want to draw, and then use methods defined in
    YDisplayLayer to draw on the layers.

    """
    _aio: YDisplay_aio
    # --- (end of generated code: YDisplay class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YDisplay return codes)
        STARTUPSEQ_INVALID: Final[str] = YAPI.INVALID_STRING
        BRIGHTNESS_INVALID: Final[int] = YAPI.INVALID_UINT
        AUTOINVERTDELAY_INVALID: Final[int] = YAPI.INVALID_UINT
        DISPLAYPANEL_INVALID: Final[str] = YAPI.INVALID_STRING
        DISPLAYWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        DISPLAYHEIGHT_INVALID: Final[int] = YAPI.INVALID_UINT
        LAYERWIDTH_INVALID: Final[int] = YAPI.INVALID_UINT
        LAYERHEIGHT_INVALID: Final[int] = YAPI.INVALID_UINT
        LAYERCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        ENABLED_FALSE: Final[int] = 0
        ENABLED_TRUE: Final[int] = 1
        ENABLED_INVALID: Final[int] = -1
        ORIENTATION_LEFT: Final[int] = 0
        ORIENTATION_UP: Final[int] = 1
        ORIENTATION_RIGHT: Final[int] = 2
        ORIENTATION_DOWN: Final[int] = 3
        ORIENTATION_INVALID: Final[int] = -1
        DISPLAYTYPE_MONO: Final[int] = 0
        DISPLAYTYPE_GRAY: Final[int] = 1
        DISPLAYTYPE_RGB: Final[int] = 2
        DISPLAYTYPE_EPAPER: Final[int] = 3
        DISPLAYTYPE_INVALID: Final[int] = -1
        # --- (end of generated code: YDisplay return codes)

    # --- (generated code: YDisplay implementation)

    @classmethod
    def FindDisplay(cls, func: str) -> YDisplay:
        """
        Retrieves a display for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the display is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDisplay.isOnline() to test if the display is
        indeed online at a given time. In case of ambiguity when looking for
        a display by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the display, for instance
                YD128X32.display.

        @return a YDisplay object allowing you to drive the display.
        """
        return cls._proxy(cls, YDisplay_aio.FindDisplayInContext(YAPI_aio, func))

    @classmethod
    def FindDisplayInContext(cls, yctx: YAPIContext, func: str) -> YDisplay:
        """
        Retrieves a display for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the display is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDisplay.isOnline() to test if the display is
        indeed online at a given time. In case of ambiguity when looking for
        a display by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the display, for instance
                YD128X32.display.

        @return a YDisplay object allowing you to drive the display.
        """
        return cls._proxy(cls, YDisplay_aio.FindDisplayInContext(yctx._aio, func))

    @classmethod
    def FirstDisplay(cls) -> Union[YDisplay, None]:
        """
        Starts the enumeration of displays currently accessible.
        Use the method YDisplay.nextDisplay() to iterate on
        next displays.

        @return a pointer to a YDisplay object, corresponding to
                the first display currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDisplay_aio.FirstDisplayInContext(YAPI_aio))

    @classmethod
    def FirstDisplayInContext(cls, yctx: YAPIContext) -> Union[YDisplay, None]:
        """
        Starts the enumeration of displays currently accessible.
        Use the method YDisplay.nextDisplay() to iterate on
        next displays.

        @param yctx : a YAPI context.

        @return a pointer to a YDisplay object, corresponding to
                the first display currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDisplay_aio.FirstDisplayInContext(yctx._aio))

    def nextDisplay(self) -> Union[YDisplay, None]:
        """
        Continues the enumeration of displays started using yFirstDisplay().
        Caution: You can't make any assumption about the returned displays order.
        If you want to find a specific a display, use Display.findDisplay()
        and a hardwareID or a logical name.

        @return a pointer to a YDisplay object, corresponding to
                a display currently online, or a None pointer
                if there are no more displays to enumerate.
        """
        return self._proxy(type(self), self._aio.nextDisplay())

    if not _DYNAMIC_HELPERS:
        def get_enabled(self) -> int:
            """
            Returns true if the screen is powered, false otherwise.

            @return either YDisplay.ENABLED_FALSE or YDisplay.ENABLED_TRUE, according to true if the screen is
            powered, false otherwise

            On failure, throws an exception or returns YDisplay.ENABLED_INVALID.
            """
            return self._run(self._aio.get_enabled())

    if not _DYNAMIC_HELPERS:
        def set_enabled(self, newval: int) -> int:
            """
            Changes the power state of the display.

            @param newval : either YDisplay.ENABLED_FALSE or YDisplay.ENABLED_TRUE, according to the power
            state of the display

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_enabled(newval))

    if not _DYNAMIC_HELPERS:
        def get_startupSeq(self) -> str:
            """
            Returns the name of the sequence to play when the displayed is powered on.

            @return a string corresponding to the name of the sequence to play when the displayed is powered on

            On failure, throws an exception or returns YDisplay.STARTUPSEQ_INVALID.
            """
            return self._run(self._aio.get_startupSeq())

    if not _DYNAMIC_HELPERS:
        def set_startupSeq(self, newval: str) -> int:
            """
            Changes the name of the sequence to play when the displayed is powered on.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the name of the sequence to play when the displayed is powered on

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_startupSeq(newval))

    if not _DYNAMIC_HELPERS:
        def get_brightness(self) -> int:
            """
            Returns the luminosity of the  module informative LEDs (from 0 to 100).

            @return an integer corresponding to the luminosity of the  module informative LEDs (from 0 to 100)

            On failure, throws an exception or returns YDisplay.BRIGHTNESS_INVALID.
            """
            return self._run(self._aio.get_brightness())

    if not _DYNAMIC_HELPERS:
        def set_brightness(self, newval: int) -> int:
            """
            Changes the brightness of the display. The parameter is a value between 0 and
            100. Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the brightness of the display

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_brightness(newval))

    if not _DYNAMIC_HELPERS:
        def get_autoInvertDelay(self) -> int:
            """
            Returns the interval between automatic display inversions, or 0 if automatic
            inversion is disabled. Using the automatic inversion mechanism reduces the
            burn-in that occurs on OLED screens over long periods when the same content
            remains displayed on the screen.

            @return an integer corresponding to the interval between automatic display inversions, or 0 if automatic
                    inversion is disabled

            On failure, throws an exception or returns YDisplay.AUTOINVERTDELAY_INVALID.
            """
            return self._run(self._aio.get_autoInvertDelay())

    if not _DYNAMIC_HELPERS:
        def set_autoInvertDelay(self, newval: int) -> int:
            """
            Changes the interval between automatic display inversions.
            The parameter is the number of seconds, or 0 to disable automatic inversion.
            Using the automatic inversion mechanism reduces the burn-in that occurs on OLED
            screens over long periods when the same content remains displayed on the screen.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the interval between automatic display inversions

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_autoInvertDelay(newval))

    if not _DYNAMIC_HELPERS:
        def get_orientation(self) -> int:
            """
            Returns the currently selected display orientation.

            @return a value among YDisplay.ORIENTATION_LEFT, YDisplay.ORIENTATION_UP,
            YDisplay.ORIENTATION_RIGHT and YDisplay.ORIENTATION_DOWN corresponding to the currently selected
            display orientation

            On failure, throws an exception or returns YDisplay.ORIENTATION_INVALID.
            """
            return self._run(self._aio.get_orientation())

    if not _DYNAMIC_HELPERS:
        def set_orientation(self, newval: int) -> int:
            """
            Changes the display orientation. Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a value among YDisplay.ORIENTATION_LEFT, YDisplay.ORIENTATION_UP,
            YDisplay.ORIENTATION_RIGHT and YDisplay.ORIENTATION_DOWN corresponding to the display orientation

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_orientation(newval))

    if not _DYNAMIC_HELPERS:
        def get_displayPanel(self) -> str:
            """
            Returns the exact model of the display panel.

            @return a string corresponding to the exact model of the display panel

            On failure, throws an exception or returns YDisplay.DISPLAYPANEL_INVALID.
            """
            return self._run(self._aio.get_displayPanel())

    if not _DYNAMIC_HELPERS:
        def set_displayPanel(self, newval: str) -> int:
            """
            Changes the model of display to match the connected display panel.
            This function has no effect if the module does not support the selected
            display panel.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a string corresponding to the model of display to match the connected display panel

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_displayPanel(newval))

    if not _DYNAMIC_HELPERS:
        def get_displayWidth(self) -> int:
            """
            Returns the display width, in pixels.

            @return an integer corresponding to the display width, in pixels

            On failure, throws an exception or returns YDisplay.DISPLAYWIDTH_INVALID.
            """
            return self._run(self._aio.get_displayWidth())

    if not _DYNAMIC_HELPERS:
        def get_displayHeight(self) -> int:
            """
            Returns the display height, in pixels.

            @return an integer corresponding to the display height, in pixels

            On failure, throws an exception or returns YDisplay.DISPLAYHEIGHT_INVALID.
            """
            return self._run(self._aio.get_displayHeight())

    if not _DYNAMIC_HELPERS:
        def get_displayType(self) -> int:
            """
            Returns the display type: monochrome, gray levels or full color.

            @return a value among YDisplay.DISPLAYTYPE_MONO, YDisplay.DISPLAYTYPE_GRAY,
            YDisplay.DISPLAYTYPE_RGB and YDisplay.DISPLAYTYPE_EPAPER corresponding to the display type:
            monochrome, gray levels or full color

            On failure, throws an exception or returns YDisplay.DISPLAYTYPE_INVALID.
            """
            return self._run(self._aio.get_displayType())

    if not _DYNAMIC_HELPERS:
        def get_layerWidth(self) -> int:
            """
            Returns the width of the layers to draw on, in pixels.

            @return an integer corresponding to the width of the layers to draw on, in pixels

            On failure, throws an exception or returns YDisplay.LAYERWIDTH_INVALID.
            """
            return self._run(self._aio.get_layerWidth())

    if not _DYNAMIC_HELPERS:
        def get_layerHeight(self) -> int:
            """
            Returns the height of the layers to draw on, in pixels.

            @return an integer corresponding to the height of the layers to draw on, in pixels

            On failure, throws an exception or returns YDisplay.LAYERHEIGHT_INVALID.
            """
            return self._run(self._aio.get_layerHeight())

    if not _DYNAMIC_HELPERS:
        def get_layerCount(self) -> int:
            """
            Returns the number of available layers to draw on.

            @return an integer corresponding to the number of available layers to draw on

            On failure, throws an exception or returns YDisplay.LAYERCOUNT_INVALID.
            """
            return self._run(self._aio.get_layerCount())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YDisplayValueCallback) -> int:
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
        def resetAll(self) -> int:
            """
            Clears the display screen and resets all display layers to their default state.
            Using this function in a sequence will kill the sequence play-back. Don't use that
            function to reset the display at sequence start-up.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.resetAll())

    if not _DYNAMIC_HELPERS:
        def regenerateDisplay(self) -> int:
            """
            Forces an ePaper screen to perform a regenerative update using the slow
            update method. Periodic use of the slow method (total panel update with
            multiple inversions) prevents ghosting effects and improves contrast.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.regenerateDisplay())

    if not _DYNAMIC_HELPERS:
        def postponeRefresh(self, duration: int) -> int:
            """
            Disables screen refresh for a short period of time. The combination of
            postponeRefresh and triggerRefresh can be used as an
            alternative to double-buffering to avoid flickering during display updates.

            @param duration : duration of deactivation in milliseconds (max. 30 seconds)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.postponeRefresh(duration))

    if not _DYNAMIC_HELPERS:
        def triggerRefresh(self) -> int:
            """
            Trigger an immediate screen refresh. The combination of
            postponeRefresh and triggerRefresh can be used as an
            alternative to double-buffering to avoid flickering during display updates.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.triggerRefresh())

    if not _DYNAMIC_HELPERS:
        def fade(self, brightness: int, duration: int) -> int:
            """
            Smoothly changes the brightness of the screen to produce a fade-in or fade-out
            effect.

            @param brightness : the new screen brightness
            @param duration : duration of the brightness transition, in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.fade(brightness, duration))

    if not _DYNAMIC_HELPERS:
        def newSequence(self) -> int:
            """
            Starts to record all display commands into a sequence, for later replay.
            The name used to store the sequence is specified when calling
            saveSequence(), once the recording is complete.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.newSequence())

    if not _DYNAMIC_HELPERS:
        def saveSequence(self, sequenceName: str) -> int:
            """
            Stops recording display commands and saves the sequence into the specified
            file on the display internal memory. The sequence can be later replayed
            using playSequence().

            @param sequenceName : the name of the newly created sequence

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.saveSequence(sequenceName))

    if not _DYNAMIC_HELPERS:
        def playSequence(self, sequenceName: str) -> int:
            """
            Replays a display sequence previously recorded using
            newSequence() and saveSequence().

            @param sequenceName : the name of the newly created sequence

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.playSequence(sequenceName))

    if not _DYNAMIC_HELPERS:
        def pauseSequence(self, delay_ms: int) -> int:
            """
            Waits for a specified delay (in milliseconds) before playing next
            commands in current sequence. This method can be used while
            recording a display sequence, to insert a timed wait in the sequence
            (without any immediate effect). It can also be used dynamically while
            playing a pre-recorded sequence, to suspend or resume the execution of
            the sequence. To cancel a delay, call the same method with a zero delay.

            @param delay_ms : the duration to wait, in milliseconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.pauseSequence(delay_ms))

    if not _DYNAMIC_HELPERS:
        def stopSequence(self) -> int:
            """
            Stops immediately any ongoing sequence replay.
            The display is left as is.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.stopSequence())

    if not _DYNAMIC_HELPERS:
        def upload(self, pathname: str, content: xarray) -> int:
            """
            Uploads an arbitrary file (for instance a GIF file) to the display, to the
            specified full path name. If a file already exists with the same path name,
            its content is overwritten.

            @param pathname : path and name of the new file to create
            @param content : binary buffer with the content to set

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.upload(pathname, content))

    if not _DYNAMIC_HELPERS:
        def copyLayerContent(self, srcLayerId: int, dstLayerId: int) -> int:
            """
            Copies the whole content of a layer to another layer. The color and transparency
            of all the pixels from the destination layer are set to match the source pixels.
            This method only affects the displayed content, but does not change any
            property of the layer object.
            Note that layer 0 has no transparency support (it is always completely opaque).

            @param srcLayerId : the identifier of the source layer (a number in range 0..layerCount-1)
            @param dstLayerId : the identifier of the destination layer (a number in range 0..layerCount-1)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.copyLayerContent(srcLayerId, dstLayerId))

    if not _DYNAMIC_HELPERS:
        def swapLayerContent(self, layerIdA: int, layerIdB: int) -> int:
            """
            Swaps the whole content of two layers. The color and transparency of all the pixels from
            the two layers are swapped. This method only affects the displayed content, but does
            not change any property of the layer objects. In particular, the visibility of each
            layer stays unchanged. When used between one hidden layer and a visible layer,
            this method makes it possible to easily implement double-buffering.
            Note that layer 0 has no transparency support (it is always completely opaque).

            @param layerIdA : the first layer (a number in range 0..layerCount-1)
            @param layerIdB : the second layer (a number in range 0..layerCount-1)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.swapLayerContent(layerIdA, layerIdB))

    def get_displayLayer(self, layerId: int) -> Union[YDisplayLayer, None]:
        """
        Returns a YDisplayLayer object that can be used to draw on the specified
        layer. The content is displayed only when the layer is active on the
        screen (and not masked by other overlapping layers).

        @param layerId : the identifier of the layer (a number in range 0..layerCount-1)

        @return an YDisplayLayer object

        On failure, throws an exception or returns None.
        """
        return self._proxy(YDisplayLayer, self._run(self._aio.get_displayLayer(layerId)))

    if not _DYNAMIC_HELPERS:
        def readDisplay(self, palette: list[int]) -> xarray:
            """
            Returns a color image with the current content of the display.
            The image is returned as a binary object, where each byte represents a pixel,
            from left to right and from top to bottom. The palette used to map byte
            values to RGB colors is filled into the list provided as argument.
            In all cases, the first palette entry (value 0) corresponds to the
            screen default background color.
            The image dimensions are given by the display width and height.

            @param palette : a list to be filled with the image palette

            @return a binary object if the call succeeds.

            On failure, throws an exception or returns an empty binary object.
            """
            return self._run(self._aio.readDisplay(palette))

    # --- (end of generated code: YDisplay implementation)

