# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YColorLedCluster
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
Yoctopuce library: Asyncio implementation of YColorLedCluster
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YColorLedCluster
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, xbytearray, xarray
)

# --- (YColorLedCluster class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YColorLedClusterValueCallback = Union[Callable[['YColorLedCluster', str], Any], None]
    except TypeError:
        YColorLedClusterValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YColorLedCluster(YFunction):
    """
    The YColorLedCluster class allows you to drive a
    color LED cluster. Unlike the ColorLed class, the YColorLedCluster
    class allows to handle several LEDs at once. Color changes can be done using RGB
    coordinates as well as HSL coordinates.
    The module performs all conversions form RGB to HSL automatically. It is then
    self-evident to turn on a LED with a given hue and to progressively vary its
    saturation or lightness. If needed, you can find more information on the
    difference between RGB and HSL in the section following this one.

    """
    # --- (end of YColorLedCluster class start)
    if not _IS_MICROPYTHON:
        # --- (YColorLedCluster return codes)
        ACTIVELEDCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        MAXLEDCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        DYNAMICLEDCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        BLINKSEQMAXCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        BLINKSEQMAXSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        LEDTYPE_RGB: Final[int] = 0
        LEDTYPE_RGBW: Final[int] = 1
        LEDTYPE_WS2811: Final[int] = 2
        LEDTYPE_INVALID: Final[int] = -1
        # --- (end of YColorLedCluster return codes)

    # --- (YColorLedCluster attributes declaration)
    _valueCallback: YColorLedClusterValueCallback
    # --- (end of YColorLedCluster attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'ColorLedCluster', func)
        # --- (YColorLedCluster constructor)
        # --- (end of YColorLedCluster constructor)

    # --- (YColorLedCluster implementation)
    @classmethod
    def FindColorLedCluster(cls, func: str) -> YColorLedCluster:
        """
        Retrieves a RGB LED cluster for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the RGB LED cluster is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YColorLedCluster.isOnline() to test if the RGB LED cluster is
        indeed online at a given time. In case of ambiguity when looking for
        a RGB LED cluster by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the RGB LED cluster, for instance
                YRGBLED2.colorLedCluster.

        @return a YColorLedCluster object allowing you to drive the RGB LED cluster.
        """
        return cls.FindColorLedClusterInContext(YAPI, func)

    @classmethod
    def FindColorLedClusterInContext(cls, yctx: YAPIContext, func: str) -> YColorLedCluster:
        """
        Retrieves a RGB LED cluster for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the RGB LED cluster is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YColorLedCluster.isOnline() to test if the RGB LED cluster is
        indeed online at a given time. In case of ambiguity when looking for
        a RGB LED cluster by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the RGB LED cluster, for instance
                YRGBLED2.colorLedCluster.

        @return a YColorLedCluster object allowing you to drive the RGB LED cluster.
        """
        obj: Union[YColorLedCluster, None] = yctx._findInCache('ColorLedCluster', func)
        if obj:
            return obj
        return YColorLedCluster(yctx, func)

    @classmethod
    def FirstColorLedCluster(cls) -> Union[YColorLedCluster, None]:
        """
        Starts the enumeration of RGB LED clusters currently accessible.
        Use the method YColorLedCluster.nextColorLedCluster() to iterate on
        next RGB LED clusters.

        @return a pointer to a YColorLedCluster object, corresponding to
                the first RGB LED cluster currently online, or a None pointer
                if there are none.
        """
        return cls.FirstColorLedClusterInContext(YAPI)

    @classmethod
    def FirstColorLedClusterInContext(cls, yctx: YAPIContext) -> Union[YColorLedCluster, None]:
        """
        Starts the enumeration of RGB LED clusters currently accessible.
        Use the method YColorLedCluster.nextColorLedCluster() to iterate on
        next RGB LED clusters.

        @param yctx : a YAPI context.

        @return a pointer to a YColorLedCluster object, corresponding to
                the first RGB LED cluster currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('ColorLedCluster')
        if hwid:
            return cls.FindColorLedClusterInContext(yctx, hwid2str(hwid))
        return None

    def nextColorLedCluster(self) -> Union[YColorLedCluster, None]:
        """
        Continues the enumeration of RGB LED clusters started using yFirstColorLedCluster().
        Caution: You can't make any assumption about the returned RGB LED clusters order.
        If you want to find a specific a RGB LED cluster, use ColorLedCluster.findColorLedCluster()
        and a hardwareID or a logical name.

        @return a pointer to a YColorLedCluster object, corresponding to
                a RGB LED cluster currently online, or a None pointer
                if there are no more RGB LED clusters to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('ColorLedCluster', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindColorLedClusterInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_activeLedCount(self) -> int:
        """
        Returns the number of LEDs currently handled by the device.

        @return an integer corresponding to the number of LEDs currently handled by the device

        On failure, throws an exception or returns YColorLedCluster.ACTIVELEDCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("activeLedCount")
        if json_val is None:
            return YColorLedCluster.ACTIVELEDCOUNT_INVALID
        return json_val

    async def set_activeLedCount(self, newval: int) -> int:
        """
        Changes the number of LEDs currently handled by the device.
        Remember to call the matching module
        saveToFlash() method to save the setting permanently.

        @param newval : an integer corresponding to the number of LEDs currently handled by the device

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("activeLedCount", rest_val)

    async def get_ledType(self) -> int:
        """
        Returns the RGB LED type currently handled by the device.

        @return a value among YColorLedCluster.LEDTYPE_RGB, YColorLedCluster.LEDTYPE_RGBW and
        YColorLedCluster.LEDTYPE_WS2811 corresponding to the RGB LED type currently handled by the device

        On failure, throws an exception or returns YColorLedCluster.LEDTYPE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("ledType")
        if json_val is None:
            return YColorLedCluster.LEDTYPE_INVALID
        return json_val

    async def set_ledType(self, newval: int) -> int:
        """
        Changes the RGB LED type currently handled by the device.
        Remember to call the matching module
        saveToFlash() method to save the setting permanently.

        @param newval : a value among YColorLedCluster.LEDTYPE_RGB, YColorLedCluster.LEDTYPE_RGBW and
        YColorLedCluster.LEDTYPE_WS2811 corresponding to the RGB LED type currently handled by the device

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("ledType", rest_val)

    async def get_maxLedCount(self) -> int:
        """
        Returns the maximum number of LEDs that the device can handle.

        @return an integer corresponding to the maximum number of LEDs that the device can handle

        On failure, throws an exception or returns YColorLedCluster.MAXLEDCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("maxLedCount")
        if json_val is None:
            return YColorLedCluster.MAXLEDCOUNT_INVALID
        return json_val

    async def get_dynamicLedCount(self) -> int:
        """
        Returns the maximum number of LEDs that can perform autonomous transitions and sequences.

        @return an integer corresponding to the maximum number of LEDs that can perform autonomous
        transitions and sequences

        On failure, throws an exception or returns YColorLedCluster.DYNAMICLEDCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("dynamicLedCount")
        if json_val is None:
            return YColorLedCluster.DYNAMICLEDCOUNT_INVALID
        return json_val

    async def get_blinkSeqMaxCount(self) -> int:
        """
        Returns the maximum number of sequences that the device can handle.

        @return an integer corresponding to the maximum number of sequences that the device can handle

        On failure, throws an exception or returns YColorLedCluster.BLINKSEQMAXCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("blinkSeqMaxCount")
        if json_val is None:
            return YColorLedCluster.BLINKSEQMAXCOUNT_INVALID
        return json_val

    async def get_blinkSeqMaxSize(self) -> int:
        """
        Returns the maximum length of sequences.

        @return an integer corresponding to the maximum length of sequences

        On failure, throws an exception or returns YColorLedCluster.BLINKSEQMAXSIZE_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("blinkSeqMaxSize")
        if json_val is None:
            return YColorLedCluster.BLINKSEQMAXSIZE_INVALID
        return json_val

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YColorLedCluster.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YColorLedClusterValueCallback) -> int:
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

    async def sendCommand(self, command: str) -> int:
        return await self.set_command(command)

    async def set_rgbColor(self, ledIndex: int, count: int, rgbValue: int) -> int:
        """
        Changes the current color of consecutive LEDs in the cluster, using a RGB color. Encoding is done
        as follows: 0xRRGGBB.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param rgbValue :  new color.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("SR%d,%d,%x" % (ledIndex, count, rgbValue))

    async def set_rgbColorAtPowerOn(self, ledIndex: int, count: int, rgbValue: int) -> int:
        """
        Changes the  color at device startup of consecutive LEDs in the cluster, using a RGB color.
        Encoding is done as follows: 0xRRGGBB. Don't forget to call saveLedsConfigAtPowerOn()
        to make sure the modification is saved in the device flash memory.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param rgbValue :  new color.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("SC%d,%d,%x" % (ledIndex, count, rgbValue))

    async def set_hslColorAtPowerOn(self, ledIndex: int, count: int, hslValue: int) -> int:
        """
        Changes the  color at device startup of consecutive LEDs in the cluster, using a HSL color.
        Encoding is done as follows: 0xHHSSLL. Don't forget to call saveLedsConfigAtPowerOn()
        to make sure the modification is saved in the device flash memory.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param hslValue :  new color.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rgbValue: int
        rgbValue = self.hsl2rgb(hslValue)
        return await self.sendCommand("SC%d,%d,%x" % (ledIndex, count, rgbValue))

    async def set_hslColor(self, ledIndex: int, count: int, hslValue: int) -> int:
        """
        Changes the current color of consecutive LEDs in the cluster, using a HSL color. Encoding is done
        as follows: 0xHHSSLL.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param hslValue :  new color.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("SH%d,%d,%x" % (ledIndex, count, hslValue))

    async def rgb_move(self, ledIndex: int, count: int, rgbValue: int, delay: int) -> int:
        """
        Allows you to modify the current color of a group of adjacent LEDs to another color, in a seamless and
        autonomous manner. The transition is performed in the RGB space.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param rgbValue :  new color (0xRRGGBB).
        @param delay    :  transition duration in ms

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("MR%d,%d,%x,%d" % (ledIndex, count, rgbValue, delay))

    async def hsl_move(self, ledIndex: int, count: int, hslValue: int, delay: int) -> int:
        """
        Allows you to modify the current color of a group of adjacent LEDs  to another color, in a seamless and
        autonomous manner. The transition is performed in the HSL space. In HSL, hue is a circular
        value (0..360 deg). There are always two paths to perform the transition: by increasing
        or by decreasing the hue. The module selects the shortest transition.
        If the difference is exactly 180 deg, the module selects the transition which increases
        the hue.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param hslValue :  new color (0xHHSSLL).
        @param delay    :  transition duration in ms

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("MH%d,%d,%x,%d" % (ledIndex, count, hslValue, delay))

    async def addRgbMoveToBlinkSeq(self, seqIndex: int, rgbValue: int, delay: int) -> int:
        """
        Adds an RGB transition to a sequence. A sequence is a transition list, which can
        be executed in loop by a group of LEDs.  Sequences are persistent and are saved
        in the device flash memory as soon as the saveBlinkSeq() method is called.

        @param seqIndex :  sequence index.
        @param rgbValue :  target color (0xRRGGBB)
        @param delay    :  transition duration in ms

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("AR%d,%x,%d" % (seqIndex, rgbValue, delay))

    async def addHslMoveToBlinkSeq(self, seqIndex: int, hslValue: int, delay: int) -> int:
        """
        Adds an HSL transition to a sequence. A sequence is a transition list, which can
        be executed in loop by an group of LEDs.  Sequences are persistent and are saved
        in the device flash memory as soon as the saveBlinkSeq() method is called.

        @param seqIndex : sequence index.
        @param hslValue : target color (0xHHSSLL)
        @param delay    : transition duration in ms

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("AH%d,%x,%d" % (seqIndex, hslValue, delay))

    async def addMirrorToBlinkSeq(self, seqIndex: int) -> int:
        """
        Adds a mirror ending to a sequence. When the sequence will reach the end of the last
        transition, its running speed will automatically be reversed so that the sequence plays
        in the reverse direction, like in a mirror. After the first transition of the sequence
        is played at the end of the reverse execution, the sequence starts again in
        the initial direction.

        @param seqIndex : sequence index.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("AC%d,0,0" % seqIndex)

    async def addJumpToBlinkSeq(self, seqIndex: int, linkSeqIndex: int) -> int:
        """
        Adds to a sequence a jump to another sequence. When a pixel will reach this jump,
        it will be automatically relinked to the new sequence, and will run it starting
        from the beginning.

        @param seqIndex : sequence index.
        @param linkSeqIndex : index of the sequence to chain.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("AC%d,100,%d,1000" % (seqIndex, linkSeqIndex))

    async def addUnlinkToBlinkSeq(self, seqIndex: int) -> int:
        """
        Adds a to a sequence a hard stop code. When a pixel will reach this stop code,
        instead of restarting the sequence in a loop it will automatically be unlinked
        from the sequence.

        @param seqIndex : sequence index.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("AC%d,100,-1,1000" % seqIndex)

    async def linkLedToBlinkSeq(self, ledIndex: int, count: int, seqIndex: int, offset: int) -> int:
        """
        Links adjacent LEDs to a specific sequence. These LEDs start to execute
        the sequence as soon as  startBlinkSeq is called. It is possible to add an offset
        in the execution: that way we  can have several groups of LED executing the same
        sequence, with a  temporal offset. A LED cannot be linked to more than one sequence.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param seqIndex :  sequence index.
        @param offset   :  execution offset in ms.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("LS%d,%d,%d,%d" % (ledIndex, count, seqIndex, offset))

    async def linkLedToBlinkSeqAtPowerOn(self, ledIndex: int, count: int, seqIndex: int, offset: int) -> int:
        """
        Links adjacent LEDs to a specific sequence at device power-on. Don't forget to configure
        the sequence auto start flag as well and call saveLedsConfigAtPowerOn(). It is possible to add an offset
        in the execution: that way we  can have several groups of LEDs executing the same
        sequence, with a  temporal offset. A LED cannot be linked to more than one sequence.

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param seqIndex :  sequence index.
        @param offset   :  execution offset in ms.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("LO%d,%d,%d,%d" % (ledIndex, count, seqIndex, offset))

    async def linkLedToPeriodicBlinkSeq(self, ledIndex: int, count: int, seqIndex: int, periods: int) -> int:
        """
        Links adjacent LEDs to a specific sequence. These LED start to execute
        the sequence as soon as  startBlinkSeq is called. This function automatically
        introduces a shift between LEDs so that the specified number of sequence periods
        appears on the group of LEDs (wave effect).

        @param ledIndex :  index of the first affected LED.
        @param count    :  affected LED count.
        @param seqIndex :  sequence index.
        @param periods  :  number of periods to show on LEDs.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("LP%d,%d,%d,%d" % (ledIndex, count, seqIndex, periods))

    async def unlinkLedFromBlinkSeq(self, ledIndex: int, count: int) -> int:
        """
        Unlinks adjacent LEDs from a  sequence.

        @param ledIndex  :  index of the first affected LED.
        @param count     :  affected LED count.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("US%d,%d" % (ledIndex, count))

    async def startBlinkSeq(self, seqIndex: int) -> int:
        """
        Starts a sequence execution: every LED linked to that sequence starts to
        run it in a loop. Note that a sequence with a zero duration can't be started.

        @param seqIndex :  index of the sequence to start.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("SS%d" % seqIndex)

    async def stopBlinkSeq(self, seqIndex: int) -> int:
        """
        Stops a sequence execution. If started again, the execution
        restarts from the beginning.

        @param seqIndex :  index of the sequence to stop.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("XS%d" % seqIndex)

    async def resetBlinkSeq(self, seqIndex: int) -> int:
        """
        Stops a sequence execution and resets its contents. LEDs linked to this
        sequence are not automatically updated anymore.

        @param seqIndex :  index of the sequence to reset

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("ZS%d" % seqIndex)

    async def set_blinkSeqStateAtPowerOn(self, seqIndex: int, autostart: int) -> int:
        """
        Configures a sequence to make it start automatically at device
        startup. Note that a sequence with a zero duration can't be started.
        Don't forget to call saveBlinkSeq() to make sure the
        modification is saved in the device flash memory.

        @param seqIndex :  index of the sequence to reset.
        @param autostart : 0 to keep the sequence turned off and 1 to start it automatically.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("AS%d,%d" % (seqIndex, autostart))

    async def set_blinkSeqSpeed(self, seqIndex: int, speed: int) -> int:
        """
        Changes the execution speed of a sequence. The natural execution speed is 1000 per
        thousand. If you configure a slower speed, you can play the sequence in slow-motion.
        If you set a negative speed, you can play the sequence in reverse direction.

        @param seqIndex :  index of the sequence to start.
        @param speed :     sequence running speed (-1000...1000).

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("CS%d,%d" % (seqIndex, speed))

    async def saveLedsConfigAtPowerOn(self) -> int:
        """
        Saves the LEDs power-on configuration. This includes the start-up color or
        sequence binding for all LEDs. Warning: if some LEDs are linked to a sequence, the
        method saveBlinkSeq() must also be called to save the sequence definition.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("WL")

    async def saveLedsState(self) -> int:
        return await self.sendCommand("WL")

    async def saveBlinkSeq(self, seqIndex: int) -> int:
        """
        Saves the definition of a sequence. Warning: only sequence steps and flags are saved.
        to save the LEDs startup bindings, the method saveLedsConfigAtPowerOn()
        must be called.

        @param seqIndex :  index of the sequence to start.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("WS%d" % seqIndex)

    async def set_rgbColorBuffer(self, ledIndex: int, buff: xarray) -> int:
        """
        Sends a binary buffer to the LED RGB buffer, as is.
        First three bytes are RGB components for LED specified as parameter, the
        next three bytes for the next LED, etc.

        @param ledIndex : index of the first LED which should be updated
        @param buff : the binary buffer to send

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._upload("rgb:0:%d" % ledIndex, buff)

    async def set_rgbColorArray(self, ledIndex: int, rgbList: list[int]) -> int:
        """
        Sends 24bit RGB colors (provided as a list of integers) to the LED RGB buffer, as is.
        The first number represents the RGB value of the LED specified as parameter, the second
        number represents the RGB value of the next LED, etc.

        @param ledIndex : index of the first LED which should be updated
        @param rgbList : a list of 24bit RGB codes, in the form 0xRRGGBB

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        listlen: int
        buff: xarray
        idx: int
        rgb: int
        res: int
        listlen = len(rgbList)
        buff = xbytearray(3*listlen)
        idx = 0
        while idx < listlen:
            rgb = rgbList[idx]
            buff[3*idx] = ((rgb >> 16) & 255)
            buff[3*idx+1] = ((rgb >> 8) & 255)
            buff[3*idx+2] = (rgb & 255)
            idx = idx + 1

        res = await self._upload("rgb:0:%d" % ledIndex, buff)
        return res

    async def rgbArrayOfs_move(self, ledIndex: int, rgbList: list[int], delay: int) -> int:
        """
        Sets up a smooth RGB color transition to the specified pixel-by-pixel list of RGB
        color codes. The first color code represents the target RGB value of the first LED,
        the next color code represents the target value of the next LED, etc.

        @param ledIndex : index of the first LED which should be updated
        @param rgbList : a list of target 24bit RGB codes, in the form 0xRRGGBB
        @param delay   : transition duration in ms

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        listlen: int
        buff: xarray
        idx: int
        rgb: int
        res: int
        listlen = len(rgbList)
        buff = xbytearray(3*listlen)
        idx = 0
        while idx < listlen:
            rgb = rgbList[idx]
            buff[3*idx] = ((rgb >> 16) & 255)
            buff[3*idx+1] = ((rgb >> 8) & 255)
            buff[3*idx+2] = (rgb & 255)
            idx = idx + 1

        res = await self._upload("rgb:%d:%d" % (delay, ledIndex), buff)
        return res

    async def rgbArray_move(self, rgbList: list[int], delay: int) -> int:
        """
        Sets up a smooth RGB color transition to the specified pixel-by-pixel list of RGB
        color codes. The first color code represents the target RGB value of the first LED,
        the next color code represents the target value of the next LED, etc.

        @param rgbList : a list of target 24bit RGB codes, in the form 0xRRGGBB
        @param delay   : transition duration in ms

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        res: int

        res = await self.rgbArrayOfs_move(0, rgbList, delay)
        return res

    async def set_hslColorBuffer(self, ledIndex: int, buff: xarray) -> int:
        """
        Sends a binary buffer to the LED HSL buffer, as is.
        First three bytes are HSL components for the LED specified as parameter, the
        next three bytes for the second LED, etc.

        @param ledIndex : index of the first LED which should be updated
        @param buff : the binary buffer to send

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._upload("hsl:0:%d" % ledIndex, buff)

    async def set_hslColorArray(self, ledIndex: int, hslList: list[int]) -> int:
        """
        Sends 24bit HSL colors (provided as a list of integers) to the LED HSL buffer, as is.
        The first number represents the HSL value of the LED specified as parameter, the second number represents
        the HSL value of the second LED, etc.

        @param ledIndex : index of the first LED which should be updated
        @param hslList : a list of 24bit HSL codes, in the form 0xHHSSLL

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        listlen: int
        buff: xarray
        idx: int
        hsl: int
        res: int
        listlen = len(hslList)
        buff = xbytearray(3*listlen)
        idx = 0
        while idx < listlen:
            hsl = hslList[idx]
            buff[3*idx] = ((hsl >> 16) & 255)
            buff[3*idx+1] = ((hsl >> 8) & 255)
            buff[3*idx+2] = (hsl & 255)
            idx = idx + 1

        res = await self._upload("hsl:0:%d" % ledIndex, buff)
        return res

    async def hslArray_move(self, hslList: list[int], delay: int) -> int:
        """
        Sets up a smooth HSL color transition to the specified pixel-by-pixel list of HSL
        color codes. The first color code represents the target HSL value of the first LED,
        the second color code represents the target value of the second LED, etc.

        @param hslList : a list of target 24bit HSL codes, in the form 0xHHSSLL
        @param delay   : transition duration in ms

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        res: int

        res = await self.hslArrayOfs_move(0, hslList, delay)
        return res

    async def hslArrayOfs_move(self, ledIndex: int, hslList: list[int], delay: int) -> int:
        """
        Sets up a smooth HSL color transition to the specified pixel-by-pixel list of HSL
        color codes. The first color code represents the target HSL value of the first LED,
        the second color code represents the target value of the second LED, etc.

        @param ledIndex : index of the first LED which should be updated
        @param hslList : a list of target 24bit HSL codes, in the form 0xHHSSLL
        @param delay   : transition duration in ms

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        listlen: int
        buff: xarray
        idx: int
        hsl: int
        res: int
        listlen = len(hslList)
        buff = xbytearray(3*listlen)
        idx = 0
        while idx < listlen:
            hsl = hslList[idx]
            buff[3*idx] = ((hsl >> 16) & 255)
            buff[3*idx+1] = ((hsl >> 8) & 255)
            buff[3*idx+2] = (hsl & 255)
            idx = idx + 1

        res = await self._upload("hsl:%d:%d" % (delay, ledIndex), buff)
        return res

    async def get_rgbColorBuffer(self, ledIndex: int, count: int) -> xarray:
        """
        Returns a binary buffer with content from the LED RGB buffer, as is.
        First three bytes are RGB components for the first LED in the interval,
        the next three bytes for the second LED in the interval, etc.

        @param ledIndex : index of the first LED which should be returned
        @param count    : number of LEDs which should be returned

        @return a binary buffer with RGB components of selected LEDs.

        On failure, throws an exception or returns an empty binary buffer.
        """
        return await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (0, 3*ledIndex, 3*count))

    async def get_rgbColorArray(self, ledIndex: int, count: int) -> list[int]:
        """
        Returns a list on 24bit RGB color values with the current colors displayed on
        the RGB LEDs. The first number represents the RGB value of the first LED,
        the second number represents the RGB value of the second LED, etc.

        @param ledIndex : index of the first LED which should be returned
        @param count    : number of LEDs which should be returned

        @return a list of 24bit color codes with RGB components of selected LEDs, as 0xRRGGBB.

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        r: int
        g: int
        b: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (0, 3*ledIndex, 3*count))
        del res[:]

        idx = 0
        while idx < count:
            r = buff[3*idx]
            g = buff[3*idx+1]
            b = buff[3*idx+2]
            res.append(r*65536+g*256+b)
            idx = idx + 1

        return res

    async def get_rgbColorArrayAtPowerOn(self, ledIndex: int, count: int) -> list[int]:
        """
        Returns a list on 24bit RGB color values with the RGB LEDs startup colors.
        The first number represents the startup RGB value of the first LED,
        the second number represents the RGB value of the second LED, etc.

        @param ledIndex : index of the first LED  which should be returned
        @param count    : number of LEDs which should be returned

        @return a list of 24bit color codes with RGB components of selected LEDs, as 0xRRGGBB.

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        r: int
        g: int
        b: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (4, 3*ledIndex, 3*count))
        del res[:]

        idx = 0
        while idx < count:
            r = buff[3*idx]
            g = buff[3*idx+1]
            b = buff[3*idx+2]
            res.append(r*65536+g*256+b)
            idx = idx + 1

        return res

    async def get_linkedSeqArray(self, ledIndex: int, count: int) -> list[int]:
        """
        Returns a list on sequence index for each RGB LED. The first number represents the
        sequence index for the the first LED, the second number represents the sequence
        index for the second LED, etc.

        @param ledIndex : index of the first LED which should be returned
        @param count    : number of LEDs which should be returned

        @return a list of integers with sequence index

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        seq: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (1, ledIndex, count))
        del res[:]

        idx = 0
        while idx < count:
            seq = buff[idx]
            res.append(seq)
            idx = idx + 1

        return res

    async def get_blinkSeqSignatures(self, seqIndex: int, count: int) -> list[int]:
        """
        Returns a list on 32 bit signatures for specified blinking sequences.
        Since blinking sequences cannot be read from the device, this can be used
        to detect if a specific blinking sequence is already programmed.

        @param seqIndex : index of the first blinking sequence which should be returned
        @param count    : number of blinking sequences which should be returned

        @return a list of 32 bit integer signatures

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        hh: int
        hl: int
        lh: int
        ll: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (2, 4*seqIndex, 4*count))
        del res[:]

        idx = 0
        while idx < count:
            hh = buff[4*idx]
            hl = buff[4*idx+1]
            lh = buff[4*idx+2]
            ll = buff[4*idx+3]
            res.append((hh << 24)+(hl << 16)+(lh << 8)+ll)
            idx = idx + 1

        return res

    async def get_blinkSeqStateSpeed(self, seqIndex: int, count: int) -> list[int]:
        """
        Returns a list of integers with the current speed for specified blinking sequences.

        @param seqIndex : index of the first sequence speed which should be returned
        @param count    : number of sequence speeds which should be returned

        @return a list of integers, 0 for sequences turned off and 1 for sequences running

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        lh: int
        ll: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (6, seqIndex, count))
        del res[:]

        idx = 0
        while idx < count:
            lh = buff[2*idx]
            ll = buff[2*idx+1]
            res.append((lh << 8)+ll)
            idx = idx + 1

        return res

    async def get_blinkSeqStateAtPowerOn(self, seqIndex: int, count: int) -> list[int]:
        """
        Returns a list of integers with the "auto-start at power on" flag state for specified blinking sequences.

        @param seqIndex : index of the first blinking sequence which should be returned
        @param count    : number of blinking sequences which should be returned

        @return a list of integers, 0 for sequences turned off and 1 for sequences running

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        started: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (5, seqIndex, count))
        del res[:]

        idx = 0
        while idx < count:
            started = buff[idx]
            res.append(started)
            idx = idx + 1

        return res

    async def get_blinkSeqState(self, seqIndex: int, count: int) -> list[int]:
        """
        Returns a list of integers with the started state for specified blinking sequences.

        @param seqIndex : index of the first blinking sequence which should be returned
        @param count    : number of blinking sequences which should be returned

        @return a list of integers, 0 for sequences turned off and 1 for sequences running

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        res: list[int] = []
        idx: int
        started: int

        buff = await self._download("rgb.bin?typ=%d&pos=%d&len=%d" % (3, seqIndex, count))
        del res[:]

        idx = 0
        while idx < count:
            started = buff[idx]
            res.append(started)
            idx = idx + 1

        return res

    def hsl2rgbInt(self, temp1: int, temp2: int, temp3: int) -> int:
        if temp3 >= 170:
            return (temp1 + 127) // 255
        if temp3 > 42:
            if temp3 <= 127:
                return (temp2 + 127) // 255
            temp3 = 170 - temp3
        return (temp1*255 + (temp2-temp1) * (6 * temp3) + 32512) // 65025

    def hsl2rgb(self, hslValue: int) -> int:
        R: int
        G: int
        B: int
        H: int
        S: int
        L: int
        temp1: int
        temp2: int
        temp3: int
        res: int
        L = (hslValue & 0xff)
        S = ((hslValue >> 8) & 0xff)
        H = ((hslValue >> 16) & 0xff)
        if S==0:
            res = (L << 16)+(L << 8)+L
            return res
        if L<=127:
            temp2 = L * (255 + S)
        else:
            temp2 = (L + S) * 255 - L * S
        temp1 = 510 * L - temp2
        # R
        temp3 = ((H + 85) & 0xff)
        R = self.hsl2rgbInt(temp1, temp2, temp3)
        # G
        temp3 = (H & 0xff)
        G = self.hsl2rgbInt(temp1, temp2, temp3)
        # B
        temp3 = ((H + 170) & 0xff)
        B = self.hsl2rgbInt(temp1, temp2, temp3)
        # just in case
        if R > 255:
            R = 255
        if G > 255:
            G = 255
        if B > 255:
            B = 255
        res = (R << 16) + (G << 8) + B
        return res

    # --- (end of YColorLedCluster implementation)

