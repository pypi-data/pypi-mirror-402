# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_serialport.py 70498 2025-11-25 10:19:57Z mvuilleu $
#
#  Implements the asyncio YSerialPort API for SerialPort functions
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
Yoctopuce library: High-level API for YSerialPort
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_serialport_aio
provides: YSerialPort YSnoopingRecord
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
    _IS_MICROPYTHON: Final[bool] = True  # noqa
    _DYNAMIC_HELPERS: Final[bool] = True  # noqa

from .yocto_serialport_aio import (
    YSerialPort as YSerialPort_aio,
    YSnoopingRecord
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction, xarray
)

def yInternalEventCallback(obj: YSerialPort, value: str) -> None:
    obj._internalEventHandler(value)

# --- (generated code: YSerialPort class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSerialPortValueCallback = Union[Callable[['YSerialPort', str], Any], None]
        YSnoopingCallback = Union[Callable[['YSerialPort', YSnoopingRecord], Any], None]
    except TypeError:
        YSerialPortValueCallback = Union[Callable, Awaitable]
        YSnoopingCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSerialPort(YFunction):
    """
    The YSerialPort class allows you to fully drive a Yoctopuce serial port.
    It can be used to send and receive data, and to configure communication
    parameters (baud rate, bit count, parity, flow control and protocol).
    Note that Yoctopuce serial ports are not exposed as virtual COM ports.
    They are meant to be used in the same way as all Yoctopuce devices.

    """
    _aio: YSerialPort_aio
    # --- (end of generated code: YSerialPort class start)

    if not _IS_MICROPYTHON:
        # --- (generated code: YSerialPort return codes)
        RXCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        TXCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        ERRCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        RXMSGCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        TXMSGCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        LASTMSG_INVALID: Final[str] = YAPI.INVALID_STRING
        CURRENTJOB_INVALID: Final[str] = YAPI.INVALID_STRING
        STARTUPJOB_INVALID: Final[str] = YAPI.INVALID_STRING
        JOBMAXTASK_INVALID: Final[int] = YAPI.INVALID_UINT
        JOBMAXSIZE_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        PROTOCOL_INVALID: Final[str] = YAPI.INVALID_STRING
        SERIALMODE_INVALID: Final[str] = YAPI.INVALID_STRING
        VOLTAGELEVEL_OFF: Final[int] = 0
        VOLTAGELEVEL_TTL3V: Final[int] = 1
        VOLTAGELEVEL_TTL3VR: Final[int] = 2
        VOLTAGELEVEL_TTL5V: Final[int] = 3
        VOLTAGELEVEL_TTL5VR: Final[int] = 4
        VOLTAGELEVEL_RS232: Final[int] = 5
        VOLTAGELEVEL_RS485: Final[int] = 6
        VOLTAGELEVEL_TTL1V8: Final[int] = 7
        VOLTAGELEVEL_SDI12: Final[int] = 8
        VOLTAGELEVEL_INVALID: Final[int] = -1
        # --- (end of generated code: YSerialPort return codes)

    # --- (generated code: YSerialPort implementation)

    @classmethod
    def FindSerialPort(cls, func: str) -> YSerialPort:
        """
        Retrieves a serial port for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the serial port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSerialPort.isOnline() to test if the serial port is
        indeed online at a given time. In case of ambiguity when looking for
        a serial port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the serial port, for instance
                RS232MK1.serialPort.

        @return a YSerialPort object allowing you to drive the serial port.
        """
        return cls._proxy(cls, YSerialPort_aio.FindSerialPortInContext(YAPI_aio, func))

    @classmethod
    def FindSerialPortInContext(cls, yctx: YAPIContext, func: str) -> YSerialPort:
        """
        Retrieves a serial port for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the serial port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSerialPort.isOnline() to test if the serial port is
        indeed online at a given time. In case of ambiguity when looking for
        a serial port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the serial port, for instance
                RS232MK1.serialPort.

        @return a YSerialPort object allowing you to drive the serial port.
        """
        return cls._proxy(cls, YSerialPort_aio.FindSerialPortInContext(yctx._aio, func))

    @classmethod
    def FirstSerialPort(cls) -> Union[YSerialPort, None]:
        """
        Starts the enumeration of serial ports currently accessible.
        Use the method YSerialPort.nextSerialPort() to iterate on
        next serial ports.

        @return a pointer to a YSerialPort object, corresponding to
                the first serial port currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YSerialPort_aio.FirstSerialPortInContext(YAPI_aio))

    @classmethod
    def FirstSerialPortInContext(cls, yctx: YAPIContext) -> Union[YSerialPort, None]:
        """
        Starts the enumeration of serial ports currently accessible.
        Use the method YSerialPort.nextSerialPort() to iterate on
        next serial ports.

        @param yctx : a YAPI context.

        @return a pointer to a YSerialPort object, corresponding to
                the first serial port currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YSerialPort_aio.FirstSerialPortInContext(yctx._aio))

    def nextSerialPort(self) -> Union[YSerialPort, None]:
        """
        Continues the enumeration of serial ports started using yFirstSerialPort().
        Caution: You can't make any assumption about the returned serial ports order.
        If you want to find a specific a serial port, use SerialPort.findSerialPort()
        and a hardwareID or a logical name.

        @return a pointer to a YSerialPort object, corresponding to
                a serial port currently online, or a None pointer
                if there are no more serial ports to enumerate.
        """
        return self._proxy(type(self), self._aio.nextSerialPort())

    if not _DYNAMIC_HELPERS:
        def get_rxCount(self) -> int:
            """
            Returns the total number of bytes received since last reset.

            @return an integer corresponding to the total number of bytes received since last reset

            On failure, throws an exception or returns YSerialPort.RXCOUNT_INVALID.
            """
            return self._run(self._aio.get_rxCount())

    if not _DYNAMIC_HELPERS:
        def get_txCount(self) -> int:
            """
            Returns the total number of bytes transmitted since last reset.

            @return an integer corresponding to the total number of bytes transmitted since last reset

            On failure, throws an exception or returns YSerialPort.TXCOUNT_INVALID.
            """
            return self._run(self._aio.get_txCount())

    if not _DYNAMIC_HELPERS:
        def get_errCount(self) -> int:
            """
            Returns the total number of communication errors detected since last reset.

            @return an integer corresponding to the total number of communication errors detected since last reset

            On failure, throws an exception or returns YSerialPort.ERRCOUNT_INVALID.
            """
            return self._run(self._aio.get_errCount())

    if not _DYNAMIC_HELPERS:
        def get_rxMsgCount(self) -> int:
            """
            Returns the total number of messages received since last reset.

            @return an integer corresponding to the total number of messages received since last reset

            On failure, throws an exception or returns YSerialPort.RXMSGCOUNT_INVALID.
            """
            return self._run(self._aio.get_rxMsgCount())

    if not _DYNAMIC_HELPERS:
        def get_txMsgCount(self) -> int:
            """
            Returns the total number of messages send since last reset.

            @return an integer corresponding to the total number of messages send since last reset

            On failure, throws an exception or returns YSerialPort.TXMSGCOUNT_INVALID.
            """
            return self._run(self._aio.get_txMsgCount())

    if not _DYNAMIC_HELPERS:
        def get_lastMsg(self) -> str:
            """
            Returns the latest message fully received (for Line, Frame and Modbus protocols).

            @return a string corresponding to the latest message fully received (for Line, Frame and Modbus protocols)

            On failure, throws an exception or returns YSerialPort.LASTMSG_INVALID.
            """
            return self._run(self._aio.get_lastMsg())

    if not _DYNAMIC_HELPERS:
        def get_currentJob(self) -> str:
            """
            Returns the name of the job file currently in use.

            @return a string corresponding to the name of the job file currently in use

            On failure, throws an exception or returns YSerialPort.CURRENTJOB_INVALID.
            """
            return self._run(self._aio.get_currentJob())

    if not _DYNAMIC_HELPERS:
        def set_currentJob(self, newval: str) -> int:
            """
            Selects a job file to run immediately. If an empty string is
            given as argument, stops running current job file.

            @param newval : a string

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_currentJob(newval))

    if not _DYNAMIC_HELPERS:
        def get_startupJob(self) -> str:
            """
            Returns the job file to use when the device is powered on.

            @return a string corresponding to the job file to use when the device is powered on

            On failure, throws an exception or returns YSerialPort.STARTUPJOB_INVALID.
            """
            return self._run(self._aio.get_startupJob())

    if not _DYNAMIC_HELPERS:
        def set_startupJob(self, newval: str) -> int:
            """
            Changes the job to use when the device is powered on.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the job to use when the device is powered on

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_startupJob(newval))

    if not _DYNAMIC_HELPERS:
        def get_jobMaxTask(self) -> int:
            """
            Returns the maximum number of tasks in a job that the device can handle.

            @return an integer corresponding to the maximum number of tasks in a job that the device can handle

            On failure, throws an exception or returns YSerialPort.JOBMAXTASK_INVALID.
            """
            return self._run(self._aio.get_jobMaxTask())

    if not _DYNAMIC_HELPERS:
        def get_jobMaxSize(self) -> int:
            """
            Returns maximum size allowed for job files.

            @return an integer corresponding to maximum size allowed for job files

            On failure, throws an exception or returns YSerialPort.JOBMAXSIZE_INVALID.
            """
            return self._run(self._aio.get_jobMaxSize())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _DYNAMIC_HELPERS:
        def get_protocol(self) -> str:
            """
            Returns the type of protocol used over the serial line, as a string.
            Possible values are "Line" for ASCII messages separated by CR and/or LF,
            "StxEtx" for ASCII messages delimited by STX/ETX codes,
            "Frame:[timeout]ms" for binary messages separated by a delay time,
            "Modbus-ASCII" for MODBUS messages in ASCII mode,
            "Modbus-RTU" for MODBUS messages in RTU mode,
            "Wiegand-ASCII" for Wiegand messages in ASCII mode,
            "Wiegand-26","Wiegand-34", etc for Wiegand messages in byte mode,
            "Char" for a continuous ASCII stream or
            "Byte" for a continuous binary stream.

            @return a string corresponding to the type of protocol used over the serial line, as a string

            On failure, throws an exception or returns YSerialPort.PROTOCOL_INVALID.
            """
            return self._run(self._aio.get_protocol())

    if not _DYNAMIC_HELPERS:
        def set_protocol(self, newval: str) -> int:
            """
            Changes the type of protocol used over the serial line.
            Possible values are "Line" for ASCII messages separated by CR and/or LF,
            "StxEtx" for ASCII messages delimited by STX/ETX codes,
            "Frame:[timeout]ms" for binary messages separated by a delay time,
            "Modbus-ASCII" for MODBUS messages in ASCII mode,
            "Modbus-RTU" for MODBUS messages in RTU mode,
            "Wiegand-ASCII" for Wiegand messages in ASCII mode,
            "Wiegand-26","Wiegand-34", etc for Wiegand messages in byte mode,
            "Char" for a continuous ASCII stream or
            "Byte" for a continuous binary stream.
            The suffix "/[wait]ms" can be added to reduce the transmit rate so that there
            is always at lest the specified number of milliseconds between each bytes sent.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the type of protocol used over the serial line

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_protocol(newval))

    if not _DYNAMIC_HELPERS:
        def get_voltageLevel(self) -> int:
            """
            Returns the voltage level used on the serial line.

            @return a value among YSerialPort.VOLTAGELEVEL_OFF, YSerialPort.VOLTAGELEVEL_TTL3V,
            YSerialPort.VOLTAGELEVEL_TTL3VR, YSerialPort.VOLTAGELEVEL_TTL5V, YSerialPort.VOLTAGELEVEL_TTL5VR,
            YSerialPort.VOLTAGELEVEL_RS232, YSerialPort.VOLTAGELEVEL_RS485, YSerialPort.VOLTAGELEVEL_TTL1V8 and
            YSerialPort.VOLTAGELEVEL_SDI12 corresponding to the voltage level used on the serial line

            On failure, throws an exception or returns YSerialPort.VOLTAGELEVEL_INVALID.
            """
            return self._run(self._aio.get_voltageLevel())

    if not _DYNAMIC_HELPERS:
        def set_voltageLevel(self, newval: int) -> int:
            """
            Changes the voltage type used on the serial line. Valid
            values  will depend on the Yoctopuce device model featuring
            the serial port feature.  Check your device documentation
            to find out which values are valid for that specific model.
            Trying to set an invalid value will have no effect.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a value among YSerialPort.VOLTAGELEVEL_OFF, YSerialPort.VOLTAGELEVEL_TTL3V,
            YSerialPort.VOLTAGELEVEL_TTL3VR, YSerialPort.VOLTAGELEVEL_TTL5V, YSerialPort.VOLTAGELEVEL_TTL5VR,
            YSerialPort.VOLTAGELEVEL_RS232, YSerialPort.VOLTAGELEVEL_RS485, YSerialPort.VOLTAGELEVEL_TTL1V8 and
            YSerialPort.VOLTAGELEVEL_SDI12 corresponding to the voltage type used on the serial line

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_voltageLevel(newval))

    if not _DYNAMIC_HELPERS:
        def get_serialMode(self) -> str:
            """
            Returns the serial port communication parameters, as a string such as
            "9600,8N1". The string includes the baud rate, the number of data bits,
            the parity, and the number of stop bits. An optional suffix is included
            if flow control is active: "CtsRts" for hardware handshake, "XOnXOff"
            for logical flow control and "Simplex" for acquiring a shared bus using
            the RTS line (as used by some RS485 adapters for instance).

            @return a string corresponding to the serial port communication parameters, as a string such as
                    "9600,8N1"

            On failure, throws an exception or returns YSerialPort.SERIALMODE_INVALID.
            """
            return self._run(self._aio.get_serialMode())

    if not _DYNAMIC_HELPERS:
        def set_serialMode(self, newval: str) -> int:
            """
            Changes the serial port communication parameters, with a string such as
            "9600,8N1". The string includes the baud rate, the number of data bits,
            the parity, and the number of stop bits. An optional suffix can be added
            to enable flow control: "CtsRts" for hardware handshake, "XOnXOff"
            for logical flow control and "Simplex" for acquiring a shared bus using
            the RTS line (as used by some RS485 adapters for instance).
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the serial port communication parameters, with a string such as
                    "9600,8N1"

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_serialMode(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YSerialPortValueCallback) -> int:
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
        def readLine(self) -> str:
            """
            Reads a single line (or message) from the receive buffer, starting at current stream position.
            This function is intended to be used when the serial port is configured for a message protocol,
            such as 'Line' mode or frame protocols.

            If data at current stream position is not available anymore in the receive buffer,
            the function returns the oldest available line and moves the stream position just after.
            If no new full line is received, the function returns an empty line.

            @return a string with a single line of text

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.readLine())

    if not _DYNAMIC_HELPERS:
        def readMessages(self, pattern: str, maxWait: int) -> list[str]:
            """
            Searches for incoming messages in the serial port receive buffer matching a given pattern,
            starting at current position. This function will only compare and return printable characters
            in the message strings. Binary protocols are handled as hexadecimal strings.

            The search returns all messages matching the expression provided as argument in the buffer.
            If no matching message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param pattern : a limited regular expression describing the expected message format,
                    or an empty string if all messages should be returned (no filtering).
                    When using binary protocols, the format applies to the hexadecimal
                    representation of the message.
            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.

            @return an array of strings containing the messages found, if any.
                    Binary messages are converted to hexadecimal representation.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.readMessages(pattern, maxWait))

    if not _DYNAMIC_HELPERS:
        def read_seek(self, absPos: int) -> int:
            """
            Changes the current internal stream position to the specified value. This function
            does not affect the device, it only changes the value stored in the API object
            for the next read operations.

            @param absPos : the absolute position index for next read operations.

            @return nothing.
            """
            return self._run(self._aio.read_seek(absPos))

    if not _DYNAMIC_HELPERS:
        def read_tell(self) -> int:
            """
            Returns the current absolute stream position pointer of the API object.

            @return the absolute position index for next read operations.
            """
            return self._run(self._aio.read_tell())

    if not _DYNAMIC_HELPERS:
        def read_avail(self) -> int:
            """
            Returns the number of bytes available to read in the input buffer starting from the
            current absolute stream position pointer of the API object.

            @return the number of bytes available to read
            """
            return self._run(self._aio.read_avail())

    if not _DYNAMIC_HELPERS:
        def queryLine(self, query: str, maxWait: int) -> str:
            """
            Sends a text line query to the serial port, and reads the reply, if any.
            This function is intended to be used when the serial port is configured for 'Line' protocol.

            @param query : the line query to send (without CR/LF)
            @param maxWait : the maximum number of milliseconds to wait for a reply.

            @return the next text line received after sending the text query, as a string.
                    Additional lines can be obtained by calling readLine or readMessages.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.queryLine(query, maxWait))

    if not _DYNAMIC_HELPERS:
        def queryHex(self, hexString: str, maxWait: int) -> str:
            """
            Sends a binary message to the serial port, and reads the reply, if any.
            This function is intended to be used when the serial port is configured for
            Frame-based protocol.

            @param hexString : the message to send, coded in hexadecimal
            @param maxWait : the maximum number of milliseconds to wait for a reply.

            @return the next frame received after sending the message, as a hex string.
                    Additional frames can be obtained by calling readHex or readMessages.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.queryHex(hexString, maxWait))

    if not _DYNAMIC_HELPERS:
        def uploadJob(self, jobfile: str, jsonDef: str) -> int:
            """
            Saves the job definition string (JSON data) into a job file.
            The job file can be later enabled using selectJob().

            @param jobfile : name of the job file to save on the device filesystem
            @param jsonDef : a string containing a JSON definition of the job

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.uploadJob(jobfile, jsonDef))

    if not _DYNAMIC_HELPERS:
        def selectJob(self, jobfile: str) -> int:
            """
            Load and start processing the specified job file. The file must have
            been previously created using the user interface or uploaded on the
            device filesystem using the uploadJob() function.

            @param jobfile : name of the job file (on the device filesystem)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.selectJob(jobfile))

    if not _DYNAMIC_HELPERS:
        def reset(self) -> int:
            """
            Clears the serial port buffer and resets counters to zero.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reset())

    if not _DYNAMIC_HELPERS:
        def writeByte(self, code: int) -> int:
            """
            Sends a single byte to the serial port.

            @param code : the byte to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeByte(code))

    if not _DYNAMIC_HELPERS:
        def writeStr(self, text: str) -> int:
            """
            Sends an ASCII string to the serial port, as is.

            @param text : the text string to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeStr(text))

    if not _DYNAMIC_HELPERS:
        def writeBin(self, buff: xarray) -> int:
            """
            Sends a binary buffer to the serial port, as is.

            @param buff : the binary buffer to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeBin(buff))

    if not _DYNAMIC_HELPERS:
        def writeArray(self, byteList: list[int]) -> int:
            """
            Sends a byte sequence (provided as a list of bytes) to the serial port.

            @param byteList : a list of byte codes

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeArray(byteList))

    if not _DYNAMIC_HELPERS:
        def writeHex(self, hexString: str) -> int:
            """
            Sends a byte sequence (provided as a hexadecimal string) to the serial port.

            @param hexString : a string of hexadecimal byte codes

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeHex(hexString))

    if not _DYNAMIC_HELPERS:
        def writeLine(self, text: str) -> int:
            """
            Sends an ASCII string to the serial port, followed by a line break (CR LF).

            @param text : the text string to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeLine(text))

    if not _DYNAMIC_HELPERS:
        def readByte(self) -> int:
            """
            Reads one byte from the receive buffer, starting at current stream position.
            If data at current stream position is not available anymore in the receive buffer,
            or if there is no data available yet, the function returns YAPI.NO_MORE_DATA.

            @return the next byte

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.readByte())

    if not _DYNAMIC_HELPERS:
        def readStr(self, nChars: int) -> str:
            """
            Reads data from the receive buffer as a string, starting at current stream position.
            If data at current stream position is not available anymore in the receive buffer, the
            function performs a short read.

            @param nChars : the maximum number of characters to read

            @return a string with receive buffer contents

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.readStr(nChars))

    if not _DYNAMIC_HELPERS:
        def readBin(self, nChars: int) -> xarray:
            """
            Reads data from the receive buffer as a binary buffer, starting at current stream position.
            If data at current stream position is not available anymore in the receive buffer, the
            function performs a short read.

            @param nChars : the maximum number of bytes to read

            @return a binary object with receive buffer contents

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.readBin(nChars))

    if not _DYNAMIC_HELPERS:
        def readArray(self, nChars: int) -> list[int]:
            """
            Reads data from the receive buffer as a list of bytes, starting at current stream position.
            If data at current stream position is not available anymore in the receive buffer, the
            function performs a short read.

            @param nChars : the maximum number of bytes to read

            @return a sequence of bytes with receive buffer contents

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.readArray(nChars))

    if not _DYNAMIC_HELPERS:
        def readHex(self, nBytes: int) -> str:
            """
            Reads data from the receive buffer as a hexadecimal string, starting at current stream position.
            If data at current stream position is not available anymore in the receive buffer, the
            function performs a short read.

            @param nBytes : the maximum number of bytes to read

            @return a string with receive buffer contents, encoded in hexadecimal

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.readHex(nBytes))

    if not _DYNAMIC_HELPERS:
        def sendBreak(self, duration: int) -> int:
            """
            Emits a BREAK condition on the serial interface. When the specified
            duration is 0, the BREAK signal will be exactly one character wide.
            When the duration is between 1 and 100, the BREAK condition will
            be hold for the specified number of milliseconds.

            @param duration : 0 for a standard BREAK, or duration between 1 and 100 ms

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.sendBreak(duration))

    if not _DYNAMIC_HELPERS:
        def set_RTS(self, val: int) -> int:
            """
            Manually sets the state of the RTS line. This function has no effect when
            hardware handshake is enabled, as the RTS line is driven automatically.

            @param val : 1 to turn RTS on, 0 to turn RTS off

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_RTS(val))

    if not _DYNAMIC_HELPERS:
        def get_CTS(self) -> int:
            """
            Reads the level of the CTS line. The CTS line is usually driven by
            the RTS signal of the connected serial device.

            @return 1 if the CTS line is high, 0 if the CTS line is low.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.get_CTS())

    if not _DYNAMIC_HELPERS:
        def snoopMessagesEx(self, maxWait: int, maxMsg: int) -> list[YSnoopingRecord]:
            """
            Retrieves messages (both direction) in the serial port buffer, starting at current position.
            This function will only compare and return printable characters in the message strings.
            Binary protocols are handled as hexadecimal strings.

            If no message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.
            @param maxMsg : the maximum number of messages to be returned by the function; up to 254.

            @return an array of YSnoopingRecord objects containing the messages found, if any.
                    Binary messages are converted to hexadecimal representation.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.snoopMessagesEx(maxWait, maxMsg))

    if not _DYNAMIC_HELPERS:
        def snoopMessages(self, maxWait: int) -> list[YSnoopingRecord]:
            """
            Retrieves messages (both direction) in the serial port buffer, starting at current position.
            This function will only compare and return printable characters in the message strings.
            Binary protocols are handled as hexadecimal strings.

            If no message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.

            @return an array of YSnoopingRecord objects containing the messages found, if any.
                    Binary messages are converted to hexadecimal representation.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.snoopMessages(maxWait))

    def registerSnoopingCallback(self, callback: YSnoopingCallback) -> int:
        """
        Registers a callback function to be called each time that a message is sent or
        received by the serial port. The callback is invoked only during the execution of
        ySleep or yHandleEvents. This provides control over the time when
        the callback is triggered. For good responsiveness, remember to call one of these
        two functions periodically. To unregister a callback, pass a None pointer as argument.

        @param callback : the callback function to call, or a None pointer.
                The callback function should take four arguments:
                the YSerialPort object that emitted the event, and
                the YSnoopingRecord object that describes the message
                sent or received.
                On failure, throws an exception or returns a negative error code.
        """
        if callback:
            self.registerValueCallback(yInternalEventCallback)
        else:
            self.registerValueCallback(None)
        # register user callback AFTER the internal pseudo-event,
        # to make sure we start with future events only
        self._aio._eventCallback = callback
        return 0

    def _internalEventHandler(self, advstr: str) -> int:
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        idx: int
        if not self._aio._eventCallback:
            # first simulated event, use it only to initialize reference values
            self._eventPos = 0

        url = "rxmsg.json?pos=%d&maxw=0&t=0" % self._eventPos
        msgbin = self._download(url)
        msgarr = self._aio._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return YAPI.SUCCESS
        # last element of array is the new position
        msglen = msglen - 1
        if not self._aio._eventCallback:
            # first simulated event, use it only to initialize reference values
            self._eventPos = self._aio._decode_json_int(msgarr[msglen])
            return YAPI.SUCCESS
        self._eventPos = self._aio._decode_json_int(msgarr[msglen])
        idx = 0
        while idx < msglen:
            try:
                retval = self._aio._eventCallback(self, YSnoopingRecord(msgarr[idx].decode('latin-1')))
                if retval is not None: self._run(retval)
            # noinspection PyBroadException
            except Exception as e:
                print('Exception in %s.snoopingCallback:' % type(self).__name__, type(e).__name__, e)
            idx = idx + 1
        return YAPI.SUCCESS

    if not _DYNAMIC_HELPERS:
        def writeStxEtx(self, text: str) -> int:
            """
            Sends an ASCII string to the serial port, preceeded with an STX code and
            followed by an ETX code.

            @param text : the text string to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeStxEtx(text))

    if not _DYNAMIC_HELPERS:
        def writeMODBUS(self, hexString: str) -> int:
            """
            Sends a MODBUS message (provided as a hexadecimal string) to the serial port.
            The message must start with the slave address. The MODBUS CRC/LRC is
            automatically added by the function. This function does not wait for a reply.

            @param hexString : a hexadecimal message string, including device address but no CRC/LRC

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeMODBUS(hexString))

    if not _DYNAMIC_HELPERS:
        def queryMODBUS(self, slaveNo: int, pduBytes: list[int]) -> list[int]:
            """
            Sends a message to a specified MODBUS slave connected to the serial port, and reads the
            reply, if any. The message is the PDU, provided as a vector of bytes.

            @param slaveNo : the address of the slave MODBUS device to query
            @param pduBytes : the message to send (PDU), as a vector of bytes. The first byte of the
                    PDU is the MODBUS function code.

            @return the received reply, as a vector of bytes.

            On failure, throws an exception or returns an empty array (or a MODBUS error reply).
            """
            return self._run(self._aio.queryMODBUS(slaveNo, pduBytes))

    if not _DYNAMIC_HELPERS:
        def modbusReadBits(self, slaveNo: int, pduAddr: int, nBits: int) -> list[int]:
            """
            Reads one or more contiguous internal bits (or coil status) from a MODBUS serial device.
            This method uses the MODBUS function code 0x01 (Read Coils).

            @param slaveNo : the address of the slave MODBUS device to query
            @param pduAddr : the relative address of the first bit/coil to read (zero-based)
            @param nBits : the number of bits/coils to read

            @return a vector of integers, each corresponding to one bit.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.modbusReadBits(slaveNo, pduAddr, nBits))

    if not _DYNAMIC_HELPERS:
        def modbusReadInputBits(self, slaveNo: int, pduAddr: int, nBits: int) -> list[int]:
            """
            Reads one or more contiguous input bits (or discrete inputs) from a MODBUS serial device.
            This method uses the MODBUS function code 0x02 (Read Discrete Inputs).

            @param slaveNo : the address of the slave MODBUS device to query
            @param pduAddr : the relative address of the first bit/input to read (zero-based)
            @param nBits : the number of bits/inputs to read

            @return a vector of integers, each corresponding to one bit.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.modbusReadInputBits(slaveNo, pduAddr, nBits))

    if not _DYNAMIC_HELPERS:
        def modbusReadRegisters(self, slaveNo: int, pduAddr: int, nWords: int) -> list[int]:
            """
            Reads one or more contiguous internal registers (holding registers) from a MODBUS serial device.
            This method uses the MODBUS function code 0x03 (Read Holding Registers).

            @param slaveNo : the address of the slave MODBUS device to query
            @param pduAddr : the relative address of the first holding register to read (zero-based)
            @param nWords : the number of holding registers to read

            @return a vector of integers, each corresponding to one 16-bit register value.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.modbusReadRegisters(slaveNo, pduAddr, nWords))

    if not _DYNAMIC_HELPERS:
        def modbusReadInputRegisters(self, slaveNo: int, pduAddr: int, nWords: int) -> list[int]:
            """
            Reads one or more contiguous input registers (read-only registers) from a MODBUS serial device.
            This method uses the MODBUS function code 0x04 (Read Input Registers).

            @param slaveNo : the address of the slave MODBUS device to query
            @param pduAddr : the relative address of the first input register to read (zero-based)
            @param nWords : the number of input registers to read

            @return a vector of integers, each corresponding to one 16-bit input value.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.modbusReadInputRegisters(slaveNo, pduAddr, nWords))

    if not _DYNAMIC_HELPERS:
        def modbusWriteBit(self, slaveNo: int, pduAddr: int, value: int) -> int:
            """
            Sets a single internal bit (or coil) on a MODBUS serial device.
            This method uses the MODBUS function code 0x05 (Write Single Coil).

            @param slaveNo : the address of the slave MODBUS device to drive
            @param pduAddr : the relative address of the bit/coil to set (zero-based)
            @param value : the value to set (0 for OFF state, non-zero for ON state)

            @return the number of bits/coils affected on the device (1)

            On failure, throws an exception or returns zero.
            """
            return self._run(self._aio.modbusWriteBit(slaveNo, pduAddr, value))

    if not _DYNAMIC_HELPERS:
        def modbusWriteBits(self, slaveNo: int, pduAddr: int, bits: list[int]) -> int:
            """
            Sets several contiguous internal bits (or coils) on a MODBUS serial device.
            This method uses the MODBUS function code 0x0f (Write Multiple Coils).

            @param slaveNo : the address of the slave MODBUS device to drive
            @param pduAddr : the relative address of the first bit/coil to set (zero-based)
            @param bits : the vector of bits to be set (one integer per bit)

            @return the number of bits/coils affected on the device

            On failure, throws an exception or returns zero.
            """
            return self._run(self._aio.modbusWriteBits(slaveNo, pduAddr, bits))

    if not _DYNAMIC_HELPERS:
        def modbusWriteRegister(self, slaveNo: int, pduAddr: int, value: int) -> int:
            """
            Sets a single internal register (or holding register) on a MODBUS serial device.
            This method uses the MODBUS function code 0x06 (Write Single Register).

            @param slaveNo : the address of the slave MODBUS device to drive
            @param pduAddr : the relative address of the register to set (zero-based)
            @param value : the 16 bit value to set

            @return the number of registers affected on the device (1)

            On failure, throws an exception or returns zero.
            """
            return self._run(self._aio.modbusWriteRegister(slaveNo, pduAddr, value))

    if not _DYNAMIC_HELPERS:
        def modbusWriteRegisters(self, slaveNo: int, pduAddr: int, values: list[int]) -> int:
            """
            Sets several contiguous internal registers (or holding registers) on a MODBUS serial device.
            This method uses the MODBUS function code 0x10 (Write Multiple Registers).

            @param slaveNo : the address of the slave MODBUS device to drive
            @param pduAddr : the relative address of the first internal register to set (zero-based)
            @param values : the vector of 16 bit values to set

            @return the number of registers affected on the device

            On failure, throws an exception or returns zero.
            """
            return self._run(self._aio.modbusWriteRegisters(slaveNo, pduAddr, values))

    if not _DYNAMIC_HELPERS:
        def modbusWriteAndReadRegisters(self, slaveNo: int, pduWriteAddr: int, values: list[int], pduReadAddr: int, nReadWords: int) -> list[int]:
            """
            Sets several contiguous internal registers (holding registers) on a MODBUS serial device,
            then performs a contiguous read of a set of (possibly different) internal registers.
            This method uses the MODBUS function code 0x17 (Read/Write Multiple Registers).

            @param slaveNo : the address of the slave MODBUS device to drive
            @param pduWriteAddr : the relative address of the first internal register to set (zero-based)
            @param values : the vector of 16 bit values to set
            @param pduReadAddr : the relative address of the first internal register to read (zero-based)
            @param nReadWords : the number of 16 bit values to read

            @return a vector of integers, each corresponding to one 16-bit register value read.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.modbusWriteAndReadRegisters(slaveNo, pduWriteAddr, values, pduReadAddr, nReadWords))

    # --- (end of generated code: YSerialPort implementation)


