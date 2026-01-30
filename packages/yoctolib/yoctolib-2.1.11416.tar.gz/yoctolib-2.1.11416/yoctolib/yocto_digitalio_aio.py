# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YDigitalIO
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
Yoctopuce library: Asyncio implementation of YDigitalIO
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YDigitalIO
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

# --- (YDigitalIO class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YDigitalIOValueCallback = Union[Callable[['YDigitalIO', str], Any], None]
    except TypeError:
        YDigitalIOValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YDigitalIO(YFunction):
    """
    The YDigitalIO class allows you drive a Yoctopuce digital input/output port.
    It can be used to set up the direction of each channel, to read the state of each channel
    and to switch the state of each channel configures as an output.
    You can work on all channels at once, or one by one. Most functions
    use a binary representation for channels where bit 0 matches channel #0 , bit 1 matches channel
    #1 and so on. If you are not familiar with numbers binary representation, you will find more
    information here: https://en.wikipedia.org/wiki/Binary_number#Representation. It is also possible
    to automatically generate short pulses of a determined duration. Electrical behavior
    of each I/O can be modified (open drain and reverse polarity).

    """
    # --- (end of YDigitalIO class start)
    if not _IS_MICROPYTHON:
        # --- (YDigitalIO return codes)
        PORTSTATE_INVALID: Final[int] = YAPI.INVALID_UINT
        PORTDIRECTION_INVALID: Final[int] = YAPI.INVALID_UINT
        PORTOPENDRAIN_INVALID: Final[int] = YAPI.INVALID_UINT
        PORTPOLARITY_INVALID: Final[int] = YAPI.INVALID_UINT
        PORTDIAGS_INVALID: Final[int] = YAPI.INVALID_UINT
        PORTSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        OUTPUTVOLTAGE_USB_5V: Final[int] = 0
        OUTPUTVOLTAGE_USB_3V: Final[int] = 1
        OUTPUTVOLTAGE_EXT_V: Final[int] = 2
        OUTPUTVOLTAGE_INVALID: Final[int] = -1
        # --- (end of YDigitalIO return codes)

    # --- (YDigitalIO attributes declaration)
    _valueCallback: YDigitalIOValueCallback
    # --- (end of YDigitalIO attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'DigitalIO', func)
        # --- (YDigitalIO constructor)
        # --- (end of YDigitalIO constructor)

    # --- (YDigitalIO implementation)
    @classmethod
    def FindDigitalIO(cls, func: str) -> YDigitalIO:
        """
        Retrieves a digital IO port for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the digital IO port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDigitalIO.isOnline() to test if the digital IO port is
        indeed online at a given time. In case of ambiguity when looking for
        a digital IO port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the digital IO port, for instance
                YMINIIO0.digitalIO.

        @return a YDigitalIO object allowing you to drive the digital IO port.
        """
        return cls.FindDigitalIOInContext(YAPI, func)

    @classmethod
    def FindDigitalIOInContext(cls, yctx: YAPIContext, func: str) -> YDigitalIO:
        """
        Retrieves a digital IO port for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the digital IO port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDigitalIO.isOnline() to test if the digital IO port is
        indeed online at a given time. In case of ambiguity when looking for
        a digital IO port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the digital IO port, for instance
                YMINIIO0.digitalIO.

        @return a YDigitalIO object allowing you to drive the digital IO port.
        """
        obj: Union[YDigitalIO, None] = yctx._findInCache('DigitalIO', func)
        if obj:
            return obj
        return YDigitalIO(yctx, func)

    @classmethod
    def FirstDigitalIO(cls) -> Union[YDigitalIO, None]:
        """
        Starts the enumeration of digital IO ports currently accessible.
        Use the method YDigitalIO.nextDigitalIO() to iterate on
        next digital IO ports.

        @return a pointer to a YDigitalIO object, corresponding to
                the first digital IO port currently online, or a None pointer
                if there are none.
        """
        return cls.FirstDigitalIOInContext(YAPI)

    @classmethod
    def FirstDigitalIOInContext(cls, yctx: YAPIContext) -> Union[YDigitalIO, None]:
        """
        Starts the enumeration of digital IO ports currently accessible.
        Use the method YDigitalIO.nextDigitalIO() to iterate on
        next digital IO ports.

        @param yctx : a YAPI context.

        @return a pointer to a YDigitalIO object, corresponding to
                the first digital IO port currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('DigitalIO')
        if hwid:
            return cls.FindDigitalIOInContext(yctx, hwid2str(hwid))
        return None

    def nextDigitalIO(self) -> Union[YDigitalIO, None]:
        """
        Continues the enumeration of digital IO ports started using yFirstDigitalIO().
        Caution: You can't make any assumption about the returned digital IO ports order.
        If you want to find a specific a digital IO port, use DigitalIO.findDigitalIO()
        and a hardwareID or a logical name.

        @return a pointer to a YDigitalIO object, corresponding to
                a digital IO port currently online, or a None pointer
                if there are no more digital IO ports to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('DigitalIO', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindDigitalIOInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_portState(self) -> int:
        """
        Returns the digital IO port state as an integer with each bit
        representing a channel.
        value 0 = 0b00000000 -> all channels are OFF
        value 1 = 0b00000001 -> channel #0 is ON
        value 2 = 0b00000010 -> channel #1 is ON
        value 3 = 0b00000011 -> channels #0 and #1 are ON
        value 4 = 0b00000100 -> channel #2 is ON
        and so on...

        @return an integer corresponding to the digital IO port state as an integer with each bit
                representing a channel

        On failure, throws an exception or returns YDigitalIO.PORTSTATE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("portState")
        if json_val is None:
            return YDigitalIO.PORTSTATE_INVALID
        return json_val

    async def set_portState(self, newval: int) -> int:
        """
        Changes the state of all digital IO port's channels at once: the parameter
        is an integer where each bit represents a channel, with bit 0 matching channel #0.
        To set all channels to  0 -> 0b00000000 -> parameter = 0
        To set channel #0 to 1 -> 0b00000001 -> parameter =  1
        To set channel #1 to  1 -> 0b00000010 -> parameter = 2
        To set channel #0 and #1 -> 0b00000011 -> parameter =  3
        To set channel #2 to 1 -> 0b00000100 -> parameter =  4
        an so on....
        Only channels configured as outputs will be affecter, according to the value
        configured using set_portDirection.

        @param newval : an integer corresponding to the state of all digital IO port's channels at once: the parameter
                is an integer where each bit represents a channel, with bit 0 matching channel #0

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("portState", rest_val)

    async def get_portDirection(self) -> int:
        """
        Returns the I/O direction of all channels of the port (bitmap): 0 makes a bit an input, 1 makes it an output.

        @return an integer corresponding to the I/O direction of all channels of the port (bitmap): 0 makes
        a bit an input, 1 makes it an output

        On failure, throws an exception or returns YDigitalIO.PORTDIRECTION_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("portDirection")
        if json_val is None:
            return YDigitalIO.PORTDIRECTION_INVALID
        return json_val

    async def set_portDirection(self, newval: int) -> int:
        """
        Changes the I/O direction of all channels of the port (bitmap): 0 makes a bit an input, 1 makes it an output.
        Remember to call the saveToFlash() method  to make sure the setting is kept after a reboot.

        @param newval : an integer corresponding to the I/O direction of all channels of the port (bitmap):
        0 makes a bit an input, 1 makes it an output

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("portDirection", rest_val)

    async def get_portOpenDrain(self) -> int:
        """
        Returns the electrical interface for each bit of the port. For each bit set to 0  the matching I/O
        works in the regular,
        intuitive way, for each bit set to 1, the I/O works in reverse mode.

        @return an integer corresponding to the electrical interface for each bit of the port

        On failure, throws an exception or returns YDigitalIO.PORTOPENDRAIN_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("portOpenDrain")
        if json_val is None:
            return YDigitalIO.PORTOPENDRAIN_INVALID
        return json_val

    async def set_portOpenDrain(self, newval: int) -> int:
        """
        Changes the electrical interface for each bit of the port. 0 makes a bit a regular input/output, 1 makes
        it an open-drain (open-collector) input/output. Remember to call the
        saveToFlash() method  to make sure the setting is kept after a reboot.

        @param newval : an integer corresponding to the electrical interface for each bit of the port

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("portOpenDrain", rest_val)

    async def get_portPolarity(self) -> int:
        """
        Returns the polarity of all the bits of the port.  For each bit set to 0, the matching I/O works the regular,
        intuitive way; for each bit set to 1, the I/O works in reverse mode.

        @return an integer corresponding to the polarity of all the bits of the port

        On failure, throws an exception or returns YDigitalIO.PORTPOLARITY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("portPolarity")
        if json_val is None:
            return YDigitalIO.PORTPOLARITY_INVALID
        return json_val

    async def set_portPolarity(self, newval: int) -> int:
        """
        Changes the polarity of all the bits of the port: For each bit set to 0, the matching I/O works the regular,
        intuitive way; for each bit set to 1, the I/O works in reverse mode.
        Remember to call the saveToFlash() method  to make sure the setting will be kept after a reboot.

        @param newval : an integer corresponding to the polarity of all the bits of the port: For each bit
        set to 0, the matching I/O works the regular,
                intuitive way; for each bit set to 1, the I/O works in reverse mode

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("portPolarity", rest_val)

    async def get_portDiags(self) -> int:
        """
        Returns the port state diagnostics. Bit 0 indicates a shortcut on output 0, etc.
        Bit 8 indicates a power failure, and bit 9 signals overheating (overcurrent).
        During normal use, all diagnostic bits should stay clear.

        @return an integer corresponding to the port state diagnostics

        On failure, throws an exception or returns YDigitalIO.PORTDIAGS_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("portDiags")
        if json_val is None:
            return YDigitalIO.PORTDIAGS_INVALID
        return json_val

    async def get_portSize(self) -> int:
        """
        Returns the number of bits (i.e. channels)implemented in the I/O port.

        @return an integer corresponding to the number of bits (i.e

        On failure, throws an exception or returns YDigitalIO.PORTSIZE_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("portSize")
        if json_val is None:
            return YDigitalIO.PORTSIZE_INVALID
        return json_val

    async def get_outputVoltage(self) -> int:
        """
        Returns the voltage source used to drive output bits.

        @return a value among YDigitalIO.OUTPUTVOLTAGE_USB_5V, YDigitalIO.OUTPUTVOLTAGE_USB_3V and
        YDigitalIO.OUTPUTVOLTAGE_EXT_V corresponding to the voltage source used to drive output bits

        On failure, throws an exception or returns YDigitalIO.OUTPUTVOLTAGE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("outputVoltage")
        if json_val is None:
            return YDigitalIO.OUTPUTVOLTAGE_INVALID
        return json_val

    async def set_outputVoltage(self, newval: int) -> int:
        """
        Changes the voltage source used to drive output bits.
        Remember to call the saveToFlash() method  to make sure the setting is kept after a reboot.

        @param newval : a value among YDigitalIO.OUTPUTVOLTAGE_USB_5V, YDigitalIO.OUTPUTVOLTAGE_USB_3V and
        YDigitalIO.OUTPUTVOLTAGE_EXT_V corresponding to the voltage source used to drive output bits

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("outputVoltage", rest_val)

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YDigitalIO.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YDigitalIOValueCallback) -> int:
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

    async def set_bitState(self, bitno: int, bitstate: int) -> int:
        """
        Sets a single bit (i.e. channel) of the I/O port.

        @param bitno : the bit number; lowest bit has index 0
        @param bitstate : the state of the bit (1 or 0)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not (bitstate >= 0):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid bit state")
            return YAPI.INVALID_ARGUMENT
        if not (bitstate <= 1):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid bit state")
            return YAPI.INVALID_ARGUMENT
        return await self.set_command("%c%d" % (82+bitstate, bitno))

    async def get_bitState(self, bitno: int) -> int:
        """
        Returns the state of a single bit (i.e. channel)  of the I/O port.

        @param bitno : the bit number; lowest bit has index 0

        @return the bit state (0 or 1)

        On failure, throws an exception or returns a negative error code.
        """
        portVal: int
        portVal = await self.get_portState()
        return ((portVal >> bitno) & 1)

    async def toggle_bitState(self, bitno: int) -> int:
        """
        Reverts a single bit (i.e. channel) of the I/O port.

        @param bitno : the bit number; lowest bit has index 0

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("T%d" % bitno)

    async def set_bitDirection(self, bitno: int, bitdirection: int) -> int:
        """
        Changes  the direction of a single bit (i.e. channel) from the I/O port.

        @param bitno : the bit number; lowest bit has index 0
        @param bitdirection : direction to set, 0 makes the bit an input, 1 makes it an output.
                Remember to call the   saveToFlash() method to make sure the setting is kept after a reboot.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not (bitdirection >= 0):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid direction")
            return YAPI.INVALID_ARGUMENT
        if not (bitdirection <= 1):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid direction")
            return YAPI.INVALID_ARGUMENT
        return await self.set_command("%c%d" % (73+6*bitdirection, bitno))

    async def get_bitDirection(self, bitno: int) -> int:
        """
        Returns the direction of a single bit (i.e. channel) from the I/O port (0 means the bit is an
        input, 1  an output).

        @param bitno : the bit number; lowest bit has index 0

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        portDir: int
        portDir = await self.get_portDirection()
        return ((portDir >> bitno) & 1)

    async def set_bitPolarity(self, bitno: int, bitpolarity: int) -> int:
        """
        Changes the polarity of a single bit from the I/O port.

        @param bitno : the bit number; lowest bit has index 0.
        @param bitpolarity : polarity to set, 0 makes the I/O work in regular mode, 1 makes the I/O  works
        in reverse mode.
                Remember to call the   saveToFlash() method to make sure the setting is kept after a reboot.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not (bitpolarity >= 0):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid bit polarity")
            return YAPI.INVALID_ARGUMENT
        if not (bitpolarity <= 1):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid bit polarity")
            return YAPI.INVALID_ARGUMENT
        return await self.set_command("%c%d" % (110+4*bitpolarity, bitno))

    async def get_bitPolarity(self, bitno: int) -> int:
        """
        Returns the polarity of a single bit from the I/O port (0 means the I/O works in regular mode, 1
        means the I/O  works in reverse mode).

        @param bitno : the bit number; lowest bit has index 0

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        portPol: int
        portPol = await self.get_portPolarity()
        return ((portPol >> bitno) & 1)

    async def set_bitOpenDrain(self, bitno: int, opendrain: int) -> int:
        """
        Changes  the electrical interface of a single bit from the I/O port.

        @param bitno : the bit number; lowest bit has index 0
        @param opendrain : 0 makes a bit a regular input/output, 1 makes
                it an open-drain (open-collector) input/output. Remember to call the
                saveToFlash() method to make sure the setting is kept after a reboot.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not (opendrain >= 0):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid state")
            return YAPI.INVALID_ARGUMENT
        if not (opendrain <= 1):
            self._throw(YAPI.INVALID_ARGUMENT, "invalid state")
            return YAPI.INVALID_ARGUMENT
        return await self.set_command("%c%d" % (100-32*opendrain, bitno))

    async def get_bitOpenDrain(self, bitno: int) -> int:
        """
        Returns the type of electrical interface of a single bit from the I/O port. (0 means the bit is an
        input, 1  an output).

        @param bitno : the bit number; lowest bit has index 0

        @return   0 means the a bit is a regular input/output, 1 means the bit is an open-drain
                (open-collector) input/output.

        On failure, throws an exception or returns a negative error code.
        """
        portOpenDrain: int
        portOpenDrain = await self.get_portOpenDrain()
        return ((portOpenDrain >> bitno) & 1)

    async def pulse(self, bitno: int, ms_duration: int) -> int:
        """
        Triggers a pulse on a single bit for a specified duration. The specified bit
        will be turned to 1, and then back to 0 after the given duration.

        @param bitno : the bit number; lowest bit has index 0
        @param ms_duration : desired pulse duration in milliseconds. Be aware that the device time
                resolution is not guaranteed up to the millisecond.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("Z%d,0,%d" % (bitno, ms_duration))

    async def delayedPulse(self, bitno: int, ms_delay: int, ms_duration: int) -> int:
        """
        Schedules a pulse on a single bit for a specified duration. The specified bit
        will be turned to 1, and then back to 0 after the given duration.

        @param bitno : the bit number; lowest bit has index 0
        @param ms_delay : waiting time before the pulse, in milliseconds
        @param ms_duration : desired pulse duration in milliseconds. Be aware that the device time
                resolution is not guaranteed up to the millisecond.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_command("Z%d,%d,%d" % (bitno, ms_delay, ms_duration))

    # --- (end of YDigitalIO implementation)

