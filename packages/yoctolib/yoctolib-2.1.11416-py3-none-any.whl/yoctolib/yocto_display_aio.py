# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_display_aio.py 71207 2026-01-07 18:17:59Z mvuilleu $
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
Yoctopuce library: Asyncio implementation of YDisplay and YDisplayLayer
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YDisplay YDisplayLayer
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Union, Final, Any
    from collections.abc import Callable, Awaitable
    from enum import IntEnum
    from .yocto_api_aio import _IS_MICROPYTHON
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, YFunction, HwId, hwid2str,
    xarray, xbytearray, xStringIO
)


# noinspection PyProtectedMember
class YDisplayLayer:
    """
    Each DisplayLayer represents an image layer containing objects
    to display (bitmaps, text, etc.). The content is displayed only when
    the layer is active on the screen (and not masked by other
    overlapping layers).

    """

    # --- (end of generated code: YDisplayLayer class start)

    # --- (generated code: YDisplayLayer attributes declaration)
    # --- (end of generated code: YDisplayLayer attributes declaration)

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

    def __init__(self, parent, layerId):
        self._display = parent
        self._id = int(layerId)
        self._cmdbuff = ""
        self._hidden = False
        # --- (generated code: YDisplayLayer constructor)
        # --- (end of generated code: YDisplayLayer constructor)

    async def flush_now(self) -> int:
        res = YAPI.SUCCESS
        if self._cmdbuff != "":
            res = await self._display.sendCommand(self._cmdbuff)
            self._cmdbuff = ""
        return res

    async def command_push(self, cmd) -> int:
        res = YAPI.SUCCESS
        if len(self._cmdbuff) + len(cmd) >= 100:
            res = await self.flush_now()
        if self._cmdbuff == "":
            self._cmdbuff = str(self._id)
        self._cmdbuff = self._cmdbuff + cmd
        return res

    async def command_flush(self, cmd) -> int:
        res = await self.command_push(cmd)
        if not self._hidden:
            res = await self.flush_now()
        return res

    # --- (generated code: YDisplayLayer implementation)
    async def reset(self) -> int:
        """
        Reverts the layer to its initial state (fully transparent, default settings).
        Reinitializes the drawing pointer to the upper left position,
        and selects the most visible pen color. If you only want to erase the layer
        content, use the method clear() instead.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        self._hidden = False
        return await self.command_flush("X")

    async def clear(self) -> int:
        """
        Erases the whole content of the layer (makes it fully transparent).
        This method does not change any other attribute of the layer.
        To reinitialize the layer attributes to defaults settings, use the method
        reset() instead.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("x")

    async def selectColorPen(self, color: int) -> int:
        """
        Selects the pen color for all subsequent drawing functions,
        including text drawing. The pen color is provided as an RGB value.
        For grayscale or monochrome displays, the value is
        automatically converted to the proper range.

        @param color : the desired pen color, as a 24-bit RGB value

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_push("c%06x" % color)

    async def selectGrayPen(self, graylevel: int) -> int:
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
        return await self.command_push("g%d" % graylevel)

    async def selectEraser(self) -> int:
        """
        Selects an eraser instead of a pen for all subsequent drawing functions,
        except for bitmap copy functions. Any point drawn using the eraser
        becomes transparent (as when the layer is empty), showing the other
        layers beneath it.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_push("e")

    async def setAntialiasingMode(self, mode: bool) -> int:
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
        return await self.command_push("a%d" % mode)

    async def drawPixel(self, x: int, y: int) -> int:
        """
        Draws a single pixel at the specified position.

        @param x : the distance from left of layer, in pixels
        @param y : the distance from top of layer, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("P%d,%d" % (x, y))

    async def drawRect(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """
        Draws an empty rectangle at a specified position.

        @param x1 : the distance from left of layer to the left border of the rectangle, in pixels
        @param y1 : the distance from top of layer to the top border of the rectangle, in pixels
        @param x2 : the distance from left of layer to the right border of the rectangle, in pixels
        @param y2 : the distance from top of layer to the bottom border of the rectangle, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("R%d,%d,%d,%d" % (x1, y1, x2, y2))

    async def drawBar(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """
        Draws a filled rectangular bar at a specified position.

        @param x1 : the distance from left of layer to the left border of the rectangle, in pixels
        @param y1 : the distance from top of layer to the top border of the rectangle, in pixels
        @param x2 : the distance from left of layer to the right border of the rectangle, in pixels
        @param y2 : the distance from top of layer to the bottom border of the rectangle, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("B%d,%d,%d,%d" % (x1, y1, x2, y2))

    async def drawCircle(self, x: int, y: int, r: int) -> int:
        """
        Draws an empty circle at a specified position.

        @param x : the distance from left of layer to the center of the circle, in pixels
        @param y : the distance from top of layer to the center of the circle, in pixels
        @param r : the radius of the circle, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("C%d,%d,%d" % (x, y, r))

    async def drawDisc(self, x: int, y: int, r: int) -> int:
        """
        Draws a filled disc at a given position.

        @param x : the distance from left of layer to the center of the disc, in pixels
        @param y : the distance from top of layer to the center of the disc, in pixels
        @param r : the radius of the disc, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("D%d,%d,%d" % (x, y, r))

    async def selectFont(self, fontname: str) -> int:
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
        return await self.command_push("&%s%c" % (fontname, 27))

    async def drawText(self, x: int, y: int, anchor: ALIGN, text: str) -> int:
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
        return await self.command_flush("T%d,%d,%d,%s%c" % (x, y, anchor, text, 27))

    async def drawImage(self, x: int, y: int, imagename: str) -> int:
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
        return await self.command_flush("*%d,%d,%s%c" % (x, y, imagename, 27))

    async def drawBitmap(self, x: int, y: int, w: int, bitmap: xarray, bgcol: int) -> int:
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
        destname: str
        destname = "layer%d:%d,%d@%d,%d" % (self._id, w, bgcol, x, y)
        return await self._display.upload(destname, bitmap)

    async def moveTo(self, x: int, y: int) -> int:
        """
        Moves the drawing pointer of this layer to the specified position.

        @param x : the distance from left of layer, in pixels
        @param y : the distance from top of layer, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_push("@%d,%d" % (x, y))

    async def lineTo(self, x: int, y: int) -> int:
        """
        Draws a line from current drawing pointer position to the specified position.
        The specified destination pixel is included in the line. The pointer position
        is then moved to the end point of the line.

        @param x : the distance from left of layer to the end point of the line, in pixels
        @param y : the distance from top of layer to the end point of the line, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("-%d,%d" % (x, y))

    async def consoleOut(self, text: str) -> int:
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
        return await self.command_flush("!%s%c" % (text, 27))

    async def setConsoleMargins(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """
        Sets up display margins for the consoleOut function.

        @param x1 : the distance from left of layer to the left margin, in pixels
        @param y1 : the distance from top of layer to the top margin, in pixels
        @param x2 : the distance from left of layer to the right margin, in pixels
        @param y2 : the distance from top of layer to the bottom margin, in pixels

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_push("m%d,%d,%d,%d" % (x1, y1, x2, y2))

    async def setConsoleBackground(self, bgcol: int) -> int:
        """
        Sets up the background color used by the clearConsole function and by
        the console scrolling feature.

        @param bgcol : the background gray level to use when scrolling (0 = black,
                255 = white), or -1 for transparent

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_push("b%d" % bgcol)

    async def setConsoleWordWrap(self, wordwrap: bool) -> int:
        """
        Sets up the wrapping behavior used by the consoleOut function.

        @param wordwrap : true to wrap only between words,
                false to wrap on the last column anyway.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_push("w%d" % wordwrap)

    async def clearConsole(self) -> int:
        """
        Blanks the console area within console margins, and resets the console pointer
        to the upper left corner of the console.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.command_flush("^")

    async def setLayerPosition(self, x: int, y: int, scrollTime: int) -> int:
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
        return await self.command_flush("#%d,%d,%d" % (x, y, scrollTime))

    async def hide(self) -> int:
        """
        Hides the layer. The state of the layer is preserved but the layer is not displayed
        on the screen until the next call to unhide(). Hiding the layer can positively
        affect the drawing speed, since it postpones the rendering until all operations are
        completed (double-buffering).

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.command_push("h")
        self._hidden = True
        return await self.flush_now()

    async def unhide(self) -> int:
        """
        Shows the layer. Shows the layer again after a hide command.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        self._hidden = False
        return await self.command_flush("s")

    async def get_display(self) -> YDisplay:
        """
        Gets parent YDisplay. Returns the parent YDisplay object of the current YDisplayLayer.

        @return an YDisplay object
        """
        return self._display

    async def get_displayWidth(self) -> int:
        """
        Returns the display width, in pixels.

        @return an integer corresponding to the display width, in pixels

        On failure, throws an exception or returns YDisplayLayer.DISPLAYWIDTH_INVALID.
        """
        return await self._display.get_displayWidth()

    async def get_displayHeight(self) -> int:
        """
        Returns the display height, in pixels.

        @return an integer corresponding to the display height, in pixels

        On failure, throws an exception or returns YDisplayLayer.DISPLAYHEIGHT_INVALID.
        """
        return await self._display.get_displayHeight()

    async def get_layerWidth(self) -> int:
        """
        Returns the width of the layers to draw on, in pixels.

        @return an integer corresponding to the width of the layers to draw on, in pixels

        On failure, throws an exception or returns YDisplayLayer.LAYERWIDTH_INVALID.
        """
        return await self._display.get_layerWidth()

    async def get_layerHeight(self) -> int:
        """
        Returns the height of the layers to draw on, in pixels.

        @return an integer corresponding to the height of the layers to draw on, in pixels

        On failure, throws an exception or returns YDisplayLayer.LAYERHEIGHT_INVALID.
        """
        return await self._display.get_layerHeight()

    async def resetHiddenFlag(self) -> int:
        self._hidden = False
        return YAPI.SUCCESS

    # --- (end of generated code: YDisplayLayer implementation)


# --- (generated code: YDisplayLayer functions)
# --- (end of generated code: YDisplayLayer functions)


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
    _sequence: str
    _recording: bool
    # --- (generated code: YDisplay attributes declaration)
    _valueCallback: YDisplayValueCallback
    _allDisplayLayers: list[YDisplayLayer]
    # --- (end of generated code: YDisplay attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Display', func)
        # --- (generated code: YDisplay constructor)
        self._allDisplayLayers = []
        # --- (end of generated code: YDisplay constructor)
        self._sequence = ""
        self._recording = False

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
        return cls.FindDisplayInContext(YAPI, func)

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
        obj: Union[YDisplay, None] = yctx._findInCache('Display', func)
        if obj:
            return obj
        return YDisplay(yctx, func)

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
        return cls.FirstDisplayInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('Display')
        if hwid:
            return cls.FindDisplayInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Display', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindDisplayInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_enabled(self) -> int:
        """
        Returns true if the screen is powered, false otherwise.

        @return either YDisplay.ENABLED_FALSE or YDisplay.ENABLED_TRUE, according to true if the screen is
        powered, false otherwise

        On failure, throws an exception or returns YDisplay.ENABLED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("enabled")
        if json_val is None:
            return YDisplay.ENABLED_INVALID
        return json_val

    async def set_enabled(self, newval: int) -> int:
        """
        Changes the power state of the display.

        @param newval : either YDisplay.ENABLED_FALSE or YDisplay.ENABLED_TRUE, according to the power
        state of the display

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("enabled", rest_val)

    async def get_startupSeq(self) -> str:
        """
        Returns the name of the sequence to play when the displayed is powered on.

        @return a string corresponding to the name of the sequence to play when the displayed is powered on

        On failure, throws an exception or returns YDisplay.STARTUPSEQ_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("startupSeq")
        if json_val is None:
            return YDisplay.STARTUPSEQ_INVALID
        return json_val

    async def set_startupSeq(self, newval: str) -> int:
        """
        Changes the name of the sequence to play when the displayed is powered on.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the name of the sequence to play when the displayed is powered on

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("startupSeq", rest_val)

    async def get_brightness(self) -> int:
        """
        Returns the luminosity of the  module informative LEDs (from 0 to 100).

        @return an integer corresponding to the luminosity of the  module informative LEDs (from 0 to 100)

        On failure, throws an exception or returns YDisplay.BRIGHTNESS_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("brightness")
        if json_val is None:
            return YDisplay.BRIGHTNESS_INVALID
        return json_val

    async def set_brightness(self, newval: int) -> int:
        """
        Changes the brightness of the display. The parameter is a value between 0 and
        100. Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : an integer corresponding to the brightness of the display

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("brightness", rest_val)

    async def get_autoInvertDelay(self) -> int:
        """
        Returns the interval between automatic display inversions, or 0 if automatic
        inversion is disabled. Using the automatic inversion mechanism reduces the
        burn-in that occurs on OLED screens over long periods when the same content
        remains displayed on the screen.

        @return an integer corresponding to the interval between automatic display inversions, or 0 if automatic
                inversion is disabled

        On failure, throws an exception or returns YDisplay.AUTOINVERTDELAY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("autoInvertDelay")
        if json_val is None:
            return YDisplay.AUTOINVERTDELAY_INVALID
        return json_val

    async def set_autoInvertDelay(self, newval: int) -> int:
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
        rest_val = str(newval)
        return await self._setAttr("autoInvertDelay", rest_val)

    async def get_orientation(self) -> int:
        """
        Returns the currently selected display orientation.

        @return a value among YDisplay.ORIENTATION_LEFT, YDisplay.ORIENTATION_UP,
        YDisplay.ORIENTATION_RIGHT and YDisplay.ORIENTATION_DOWN corresponding to the currently selected
        display orientation

        On failure, throws an exception or returns YDisplay.ORIENTATION_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("orientation")
        if json_val is None:
            return YDisplay.ORIENTATION_INVALID
        return json_val

    async def set_orientation(self, newval: int) -> int:
        """
        Changes the display orientation. Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a value among YDisplay.ORIENTATION_LEFT, YDisplay.ORIENTATION_UP,
        YDisplay.ORIENTATION_RIGHT and YDisplay.ORIENTATION_DOWN corresponding to the display orientation

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("orientation", rest_val)

    async def get_displayPanel(self) -> str:
        """
        Returns the exact model of the display panel.

        @return a string corresponding to the exact model of the display panel

        On failure, throws an exception or returns YDisplay.DISPLAYPANEL_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("displayPanel")
        if json_val is None:
            return YDisplay.DISPLAYPANEL_INVALID
        return json_val

    async def set_displayPanel(self, newval: str) -> int:
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
        rest_val = newval
        return await self._setAttr("displayPanel", rest_val)

    async def get_displayWidth(self) -> int:
        """
        Returns the display width, in pixels.

        @return an integer corresponding to the display width, in pixels

        On failure, throws an exception or returns YDisplay.DISPLAYWIDTH_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("displayWidth")
        if json_val is None:
            return YDisplay.DISPLAYWIDTH_INVALID
        return json_val

    async def get_displayHeight(self) -> int:
        """
        Returns the display height, in pixels.

        @return an integer corresponding to the display height, in pixels

        On failure, throws an exception or returns YDisplay.DISPLAYHEIGHT_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("displayHeight")
        if json_val is None:
            return YDisplay.DISPLAYHEIGHT_INVALID
        return json_val

    async def get_displayType(self) -> int:
        """
        Returns the display type: monochrome, gray levels or full color.

        @return a value among YDisplay.DISPLAYTYPE_MONO, YDisplay.DISPLAYTYPE_GRAY,
        YDisplay.DISPLAYTYPE_RGB and YDisplay.DISPLAYTYPE_EPAPER corresponding to the display type:
        monochrome, gray levels or full color

        On failure, throws an exception or returns YDisplay.DISPLAYTYPE_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("displayType")
        if json_val is None:
            return YDisplay.DISPLAYTYPE_INVALID
        return json_val

    async def get_layerWidth(self) -> int:
        """
        Returns the width of the layers to draw on, in pixels.

        @return an integer corresponding to the width of the layers to draw on, in pixels

        On failure, throws an exception or returns YDisplay.LAYERWIDTH_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("layerWidth")
        if json_val is None:
            return YDisplay.LAYERWIDTH_INVALID
        return json_val

    async def get_layerHeight(self) -> int:
        """
        Returns the height of the layers to draw on, in pixels.

        @return an integer corresponding to the height of the layers to draw on, in pixels

        On failure, throws an exception or returns YDisplay.LAYERHEIGHT_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("layerHeight")
        if json_val is None:
            return YDisplay.LAYERHEIGHT_INVALID
        return json_val

    async def get_layerCount(self) -> int:
        """
        Returns the number of available layers to draw on.

        @return an integer corresponding to the number of available layers to draw on

        On failure, throws an exception or returns YDisplay.LAYERCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("layerCount")
        if json_val is None:
            return YDisplay.LAYERCOUNT_INVALID
        return json_val

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YDisplay.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YDisplayValueCallback) -> int:
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

    async def resetAll(self) -> int:
        """
        Clears the display screen and resets all display layers to their default state.
        Using this function in a sequence will kill the sequence play-back. Don't use that
        function to reset the display at sequence start-up.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.flushLayers()
        await self.resetHiddenLayerFlags()
        return await self.sendCommand("Z")

    async def regenerateDisplay(self) -> int:
        """
        Forces an ePaper screen to perform a regenerative update using the slow
        update method. Periodic use of the slow method (total panel update with
        multiple inversions) prevents ghosting effects and improves contrast.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("z")

    async def postponeRefresh(self, duration: int) -> int:
        """
        Disables screen refresh for a short period of time. The combination of
        postponeRefresh and triggerRefresh can be used as an
        alternative to double-buffering to avoid flickering during display updates.

        @param duration : duration of deactivation in milliseconds (max. 30 seconds)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("t%d" % duration)

    async def triggerRefresh(self) -> int:
        """
        Trigger an immediate screen refresh. The combination of
        postponeRefresh and triggerRefresh can be used as an
        alternative to double-buffering to avoid flickering during display updates.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("t0")

    async def fade(self, brightness: int, duration: int) -> int:
        """
        Smoothly changes the brightness of the screen to produce a fade-in or fade-out
        effect.

        @param brightness : the new screen brightness
        @param duration : duration of the brightness transition, in milliseconds.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.flushLayers()
        return await self.sendCommand("+%d,%d" % (brightness, duration))

    async def newSequence(self) -> int:
        """
        Starts to record all display commands into a sequence, for later replay.
        The name used to store the sequence is specified when calling
        saveSequence(), once the recording is complete.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.flushLayers()
        self._sequence = ""
        self._recording = True
        return YAPI.SUCCESS

    async def saveSequence(self, sequenceName: str) -> int:
        """
        Stops recording display commands and saves the sequence into the specified
        file on the display internal memory. The sequence can be later replayed
        using playSequence().

        @param sequenceName : the name of the newly created sequence

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.flushLayers()
        self._recording = False
        await self._upload(sequenceName, xbytearray(self._sequence, 'latin-1'))
        # //We need to use YPRINTF("") for Objective-C
        self._sequence = ""
        return YAPI.SUCCESS

    async def playSequence(self, sequenceName: str) -> int:
        """
        Replays a display sequence previously recorded using
        newSequence() and saveSequence().

        @param sequenceName : the name of the newly created sequence

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.flushLayers()
        return await self.sendCommand("S%s" % sequenceName)

    async def pauseSequence(self, delay_ms: int) -> int:
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
        await self.flushLayers()
        return await self.sendCommand("W%d" % delay_ms)

    async def stopSequence(self) -> int:
        """
        Stops immediately any ongoing sequence replay.
        The display is left as is.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self.flushLayers()
        return await self.sendCommand("S")

    async def upload(self, pathname: str, content: xarray) -> int:
        """
        Uploads an arbitrary file (for instance a GIF file) to the display, to the
        specified full path name. If a file already exists with the same path name,
        its content is overwritten.

        @param pathname : path and name of the new file to create
        @param content : binary buffer with the content to set

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._upload(pathname, content)

    async def copyLayerContent(self, srcLayerId: int, dstLayerId: int) -> int:
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
        await self.flushLayers()
        return await self.sendCommand("o%d,%d" % (srcLayerId, dstLayerId))

    async def swapLayerContent(self, layerIdA: int, layerIdB: int) -> int:
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
        await self.flushLayers()
        return await self.sendCommand("E%d,%d" % (layerIdA, layerIdB))

    async def get_displayLayer(self, layerId: int) -> Union[YDisplayLayer, None]:
        """
        Returns a YDisplayLayer object that can be used to draw on the specified
        layer. The content is displayed only when the layer is active on the
        screen (and not masked by other overlapping layers).

        @param layerId : the identifier of the layer (a number in range 0..layerCount-1)

        @return an YDisplayLayer object

        On failure, throws an exception or returns None.
        """
        layercount: int
        idx: int
        layercount = await self.get_layerCount()
        if not ((layerId >= 0) and(layerId < layercount)):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid DisplayLayer index")
            return None
        if len(self._allDisplayLayers) == 0:
            idx = 0
            while idx < layercount:
                self._allDisplayLayers.append(YDisplayLayer(self, idx))
                idx = idx + 1
        return self._allDisplayLayers[layerId]

    async def readDisplay(self, palette: list[int]) -> xarray:
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
        zipmap: xarray
        zipsize: int
        zipwidth: int
        zipheight: int
        ziprotate: int
        zipcolors: int
        zipcol: int
        zipbits: int
        zipmask: int
        srcpos: int
        endrun: int
        srcpat: int
        srcbit: int
        srcval: int
        srcx: int
        srcy: int
        srci: int
        incx: int
        pixmap: xarray
        pixcount: int
        pixval: int
        pixpos: int
        rotmap: xarray
        pixmap = xbytearray(0)
        # Check if the display firmware has autoInvertDelay and pixels.bin support

        if await self.get_autoInvertDelay() < 0:
            # Old firmware, use uncompressed GIF output to rebuild pixmap
            zipmap = await self._download("display.gif")
            zipsize = len(zipmap)
            if zipsize == 0:
                return pixmap
            if not (zipsize >= 32):
                self._throw(YAPI.IO_ERROR, "not a GIF image")
                return pixmap
            if not ((zipmap[0] == 71) and(zipmap[2] == 70)):
                self._throw(YAPI.INVALID_ARGUMENT, "not a GIF image")
                return pixmap
            zipwidth = zipmap[6] + 256 * zipmap[7]
            zipheight = zipmap[8] + 256 * zipmap[9]
            del palette[:]
            zipcol = zipmap[13] * 65536 + zipmap[14] * 256 + zipmap[15]
            palette.append(zipcol)
            zipcol = zipmap[16] * 65536 + zipmap[17] * 256 + zipmap[18]
            palette.append(zipcol)
            pixcount = zipwidth * zipheight
            pixmap = xbytearray(pixcount)
            pixpos = 0
            srcpos = 30
            zipsize = zipsize - 2
            while srcpos < zipsize:
                # load next run size
                endrun = srcpos + 1 + zipmap[srcpos]
                srcpos = srcpos + 1
                while srcpos < endrun:
                    srcval = zipmap[srcpos]
                    srcpos = srcpos + 1
                    srcbit = 8
                    while srcbit != 0:
                        if srcbit < 3:
                            srcval = srcval + (zipmap[srcpos] << srcbit)
                            srcpos = srcpos + 1
                        pixval = (srcval & 7)
                        srcval = (srcval >> 3)
                        if not ((pixval > 1) and(pixval != 4)):
                            self._throw(YAPI.INVALID_ARGUMENT, "unexpected encoding")
                            return pixmap
                        pixmap[pixpos] = pixval
                        pixpos = pixpos + 1
                        srcbit = srcbit - 3
            return pixmap
        # New firmware, use compressed pixels.bin
        zipmap = await self._download("pixels.bin")
        zipsize = len(zipmap)
        if zipsize == 0:
            return pixmap
        if not (zipsize >= 16):
            self._throw(YAPI.IO_ERROR, "not a pixmap")
            return pixmap
        if not ((zipmap[0] == 80) and(zipmap[2] == 88)):
            self._throw(YAPI.INVALID_ARGUMENT, "not a pixmap")
            return pixmap
        zipwidth = zipmap[4] + 256 * zipmap[5]
        zipheight = zipmap[6] + 256 * zipmap[7]
        ziprotate = zipmap[8]
        zipcolors = zipmap[9]
        del palette[:]
        srcpos = 10
        srci = 0
        while srci < zipcolors:
            zipcol = zipmap[srcpos] * 65536 + zipmap[srcpos+1] * 256 + zipmap[srcpos+2]
            palette.append(zipcol)
            srcpos = srcpos + 3
            srci = srci + 1
        zipbits = 1
        while (1 << zipbits) < zipcolors:
            zipbits = zipbits + 1
        zipmask = (1 << zipbits) - 1

        pixcount = zipwidth * zipheight
        pixmap = xbytearray(pixcount)
        srcx = 0
        srcy = 0
        incx = 8 // zipbits
        srcval = 0
        while srcpos < zipsize:
            # load next compression pattern byte
            srcpat = zipmap[srcpos]
            srcpos = srcpos + 1
            srcbit = 7
            while srcbit >= 0:
                # get next bitmap byte
                if (srcpat & 128) != 0:
                    srcval = zipmap[srcpos]
                    srcpos = srcpos + 1
                srcpat = (srcpat << 1)
                pixpos = srcy * zipwidth + srcx
                # produce 8 pixels (or 4, if bitmap uses 2 bits per pixel)
                srci = 8 - zipbits
                while srci >= 0:
                    pixval = ((srcval >> srci) & zipmask)
                    pixmap[pixpos] = pixval
                    pixpos = pixpos + 1
                    srci = srci - zipbits
                srcy = srcy + 1
                if srcy >= zipheight:
                    srcy = 0
                    srcx = srcx + incx
                    # drop last bytes if image is not a multiple of 8
                    if srcx >= zipwidth:
                        srcbit = 0
                srcbit = srcbit - 1
        # rotate pixmap to match display orientation
        if ziprotate == 0:
            return pixmap
        if (ziprotate & 2) != 0:
            # rotate buffer 180 degrees by swapping pixels
            srcpos = 0
            pixpos = pixcount - 1
            while srcpos < pixpos:
                pixval = pixmap[srcpos]
                pixmap[srcpos] = pixmap[pixpos]
                pixmap[pixpos] = pixval
                srcpos = srcpos + 1
                pixpos = pixpos - 1
        if (ziprotate & 1) == 0:
            return pixmap
        # rotate 90 ccw: first pixel is bottom left
        rotmap = xbytearray(pixcount)
        srcx = 0
        srcy = zipwidth - 1
        srcpos = 0
        while srcpos < pixcount:
            pixval = pixmap[srcpos]
            pixpos = srcy * zipheight + srcx
            rotmap[pixpos] = pixval
            srcy = srcy - 1
            if srcy < 0:
                srcx = srcx + 1
                srcy = zipwidth - 1
            srcpos = srcpos + 1
        return rotmap

    # --- (end of generated code: YDisplay implementation)

    async def flushLayers(self) -> int:
        for it in self._allDisplayLayers:
            await it.flush_now()
        return YAPI.SUCCESS

    async def resetHiddenLayerFlags(self) -> None:
        for it in self._allDisplayLayers:
            await it.resetHiddenFlag()

    async def sendCommand(self, cmd) -> int:
        if not self._recording:
            return await self.set_command(cmd)
        self._sequence = self._sequence + cmd + '\n'
        return YAPI.SUCCESS
