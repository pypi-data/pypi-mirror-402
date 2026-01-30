# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_i2cport.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YI2cPort API for I2cPort functions
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
Yoctopuce library: High-level API for YI2cPort
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_i2cport_aio
provides: YI2cPort YI2cSnoopingRecord
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

from .yocto_i2cport_aio import (
    YI2cPort as YI2cPort_aio,
    YI2cSnoopingRecord
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction, xarray
)


# --- (generated code: YI2cPort class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YI2cPortValueCallback = Union[Callable[['YI2cPort', str], Any], None]
    except TypeError:
        YI2cPortValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YI2cPort(YFunction):
    """
    The YI2cPort classe allows you to fully drive a Yoctopuce I2C port.
    It can be used to send and receive data, and to configure communication
    parameters (baud rate, etc).
    Note that Yoctopuce I2C ports are not exposed as virtual COM ports.
    They are meant to be used in the same way as all Yoctopuce devices.

    """
    _aio: YI2cPort_aio
    # --- (end of generated code: YI2cPort class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YI2cPort return codes)
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
        I2CMODE_INVALID: Final[str] = YAPI.INVALID_STRING
        I2CVOLTAGELEVEL_OFF: Final[int] = 0
        I2CVOLTAGELEVEL_3V3: Final[int] = 1
        I2CVOLTAGELEVEL_1V8: Final[int] = 2
        I2CVOLTAGELEVEL_INVALID: Final[int] = -1
        # --- (end of generated code: YI2cPort return codes)

    # --- (generated code: YI2cPort implementation)

    @classmethod
    def FindI2cPort(cls, func: str) -> YI2cPort:
        """
        Retrieves an I2C port for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the I2C port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YI2cPort.isOnline() to test if the I2C port is
        indeed online at a given time. In case of ambiguity when looking for
        an I2C port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the I2C port, for instance
                YI2CMK01.i2cPort.

        @return a YI2cPort object allowing you to drive the I2C port.
        """
        return cls._proxy(cls, YI2cPort_aio.FindI2cPortInContext(YAPI_aio, func))

    @classmethod
    def FindI2cPortInContext(cls, yctx: YAPIContext, func: str) -> YI2cPort:
        """
        Retrieves an I2C port for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the I2C port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YI2cPort.isOnline() to test if the I2C port is
        indeed online at a given time. In case of ambiguity when looking for
        an I2C port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the I2C port, for instance
                YI2CMK01.i2cPort.

        @return a YI2cPort object allowing you to drive the I2C port.
        """
        return cls._proxy(cls, YI2cPort_aio.FindI2cPortInContext(yctx._aio, func))

    @classmethod
    def FirstI2cPort(cls) -> Union[YI2cPort, None]:
        """
        Starts the enumeration of I2C ports currently accessible.
        Use the method YI2cPort.nextI2cPort() to iterate on
        next I2C ports.

        @return a pointer to a YI2cPort object, corresponding to
                the first I2C port currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YI2cPort_aio.FirstI2cPortInContext(YAPI_aio))

    @classmethod
    def FirstI2cPortInContext(cls, yctx: YAPIContext) -> Union[YI2cPort, None]:
        """
        Starts the enumeration of I2C ports currently accessible.
        Use the method YI2cPort.nextI2cPort() to iterate on
        next I2C ports.

        @param yctx : a YAPI context.

        @return a pointer to a YI2cPort object, corresponding to
                the first I2C port currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YI2cPort_aio.FirstI2cPortInContext(yctx._aio))

    def nextI2cPort(self) -> Union[YI2cPort, None]:
        """
        Continues the enumeration of I2C ports started using yFirstI2cPort().
        Caution: You can't make any assumption about the returned I2C ports order.
        If you want to find a specific an I2C port, use I2cPort.findI2cPort()
        and a hardwareID or a logical name.

        @return a pointer to a YI2cPort object, corresponding to
                an I2C port currently online, or a None pointer
                if there are no more I2C ports to enumerate.
        """
        return self._proxy(type(self), self._aio.nextI2cPort())

    if not _DYNAMIC_HELPERS:
        def get_rxCount(self) -> int:
            """
            Returns the total number of bytes received since last reset.

            @return an integer corresponding to the total number of bytes received since last reset

            On failure, throws an exception or returns YI2cPort.RXCOUNT_INVALID.
            """
            return self._run(self._aio.get_rxCount())

    if not _DYNAMIC_HELPERS:
        def get_txCount(self) -> int:
            """
            Returns the total number of bytes transmitted since last reset.

            @return an integer corresponding to the total number of bytes transmitted since last reset

            On failure, throws an exception or returns YI2cPort.TXCOUNT_INVALID.
            """
            return self._run(self._aio.get_txCount())

    if not _DYNAMIC_HELPERS:
        def get_errCount(self) -> int:
            """
            Returns the total number of communication errors detected since last reset.

            @return an integer corresponding to the total number of communication errors detected since last reset

            On failure, throws an exception or returns YI2cPort.ERRCOUNT_INVALID.
            """
            return self._run(self._aio.get_errCount())

    if not _DYNAMIC_HELPERS:
        def get_rxMsgCount(self) -> int:
            """
            Returns the total number of messages received since last reset.

            @return an integer corresponding to the total number of messages received since last reset

            On failure, throws an exception or returns YI2cPort.RXMSGCOUNT_INVALID.
            """
            return self._run(self._aio.get_rxMsgCount())

    if not _DYNAMIC_HELPERS:
        def get_txMsgCount(self) -> int:
            """
            Returns the total number of messages send since last reset.

            @return an integer corresponding to the total number of messages send since last reset

            On failure, throws an exception or returns YI2cPort.TXMSGCOUNT_INVALID.
            """
            return self._run(self._aio.get_txMsgCount())

    if not _DYNAMIC_HELPERS:
        def get_lastMsg(self) -> str:
            """
            Returns the latest message fully received (for Line and Frame protocols).

            @return a string corresponding to the latest message fully received (for Line and Frame protocols)

            On failure, throws an exception or returns YI2cPort.LASTMSG_INVALID.
            """
            return self._run(self._aio.get_lastMsg())

    if not _DYNAMIC_HELPERS:
        def get_currentJob(self) -> str:
            """
            Returns the name of the job file currently in use.

            @return a string corresponding to the name of the job file currently in use

            On failure, throws an exception or returns YI2cPort.CURRENTJOB_INVALID.
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

            On failure, throws an exception or returns YI2cPort.STARTUPJOB_INVALID.
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

            On failure, throws an exception or returns YI2cPort.JOBMAXTASK_INVALID.
            """
            return self._run(self._aio.get_jobMaxTask())

    if not _DYNAMIC_HELPERS:
        def get_jobMaxSize(self) -> int:
            """
            Returns maximum size allowed for job files.

            @return an integer corresponding to maximum size allowed for job files

            On failure, throws an exception or returns YI2cPort.JOBMAXSIZE_INVALID.
            """
            return self._run(self._aio.get_jobMaxSize())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _DYNAMIC_HELPERS:
        def get_protocol(self) -> str:
            """
            Returns the type of protocol used to send I2C messages, as a string.
            Possible values are
            "Line" for messages separated by LF or
            "Char" for continuous stream of codes.

            @return a string corresponding to the type of protocol used to send I2C messages, as a string

            On failure, throws an exception or returns YI2cPort.PROTOCOL_INVALID.
            """
            return self._run(self._aio.get_protocol())

    if not _DYNAMIC_HELPERS:
        def set_protocol(self, newval: str) -> int:
            """
            Changes the type of protocol used to send I2C messages.
            Possible values are
            "Line" for messages separated by LF or
            "Char" for continuous stream of codes.
            The suffix "/[wait]ms" can be added to reduce the transmit rate so that there
            is always at lest the specified number of milliseconds between each message sent.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the type of protocol used to send I2C messages

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_protocol(newval))

    if not _DYNAMIC_HELPERS:
        def get_i2cVoltageLevel(self) -> int:
            """
            Returns the voltage level used on the I2C bus.

            @return a value among YI2cPort.I2CVOLTAGELEVEL_OFF, YI2cPort.I2CVOLTAGELEVEL_3V3 and
            YI2cPort.I2CVOLTAGELEVEL_1V8 corresponding to the voltage level used on the I2C bus

            On failure, throws an exception or returns YI2cPort.I2CVOLTAGELEVEL_INVALID.
            """
            return self._run(self._aio.get_i2cVoltageLevel())

    if not _DYNAMIC_HELPERS:
        def set_i2cVoltageLevel(self, newval: int) -> int:
            """
            Changes the voltage level used on the I2C bus.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a value among YI2cPort.I2CVOLTAGELEVEL_OFF, YI2cPort.I2CVOLTAGELEVEL_3V3 and
            YI2cPort.I2CVOLTAGELEVEL_1V8 corresponding to the voltage level used on the I2C bus

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_i2cVoltageLevel(newval))

    if not _DYNAMIC_HELPERS:
        def get_i2cMode(self) -> str:
            """
            Returns the I2C port communication parameters, as a string such as
            "400kbps,2000ms,NoRestart". The string includes the baud rate, the
            recovery delay after communications errors, and if needed the option
            NoRestart to use a Stop/Start sequence instead of the
            Restart state when performing read on the I2C bus.

            @return a string corresponding to the I2C port communication parameters, as a string such as
                    "400kbps,2000ms,NoRestart"

            On failure, throws an exception or returns YI2cPort.I2CMODE_INVALID.
            """
            return self._run(self._aio.get_i2cMode())

    if not _DYNAMIC_HELPERS:
        def set_i2cMode(self, newval: str) -> int:
            """
            Changes the I2C port communication parameters, with a string such as
            "400kbps,2000ms". The string includes the baud rate, the
            recovery delay after communications errors, and if needed the option
            NoRestart to use a Stop/Start sequence instead of the
            Restart state when performing read on the I2C bus.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the I2C port communication parameters, with a string such as
                    "400kbps,2000ms"

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_i2cMode(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YI2cPortValueCallback) -> int:
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
        def i2cSendBin(self, slaveAddr: int, buff: xarray) -> int:
            """
            Sends a one-way message (provided as a a binary buffer) to a device on the I2C bus.
            This function checks and reports communication errors on the I2C bus.

            @param slaveAddr : the 7-bit address of the slave device (without the direction bit)
            @param buff : the binary buffer to be sent

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.i2cSendBin(slaveAddr, buff))

    if not _DYNAMIC_HELPERS:
        def i2cSendArray(self, slaveAddr: int, values: list[int]) -> int:
            """
            Sends a one-way message (provided as a list of integer) to a device on the I2C bus.
            This function checks and reports communication errors on the I2C bus.

            @param slaveAddr : the 7-bit address of the slave device (without the direction bit)
            @param values : a list of data bytes to be sent

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.i2cSendArray(slaveAddr, values))

    if not _DYNAMIC_HELPERS:
        def i2cSendAndReceiveBin(self, slaveAddr: int, buff: xarray, rcvCount: int) -> xarray:
            """
            Sends a one-way message (provided as a a binary buffer) to a device on the I2C bus,
            then read back the specified number of bytes from device.
            This function checks and reports communication errors on the I2C bus.

            @param slaveAddr : the 7-bit address of the slave device (without the direction bit)
            @param buff : the binary buffer to be sent
            @param rcvCount : the number of bytes to receive once the data bytes are sent

            @return a list of bytes with the data received from slave device.

            On failure, throws an exception or returns an empty binary buffer.
            """
            return self._run(self._aio.i2cSendAndReceiveBin(slaveAddr, buff, rcvCount))

    if not _DYNAMIC_HELPERS:
        def i2cSendAndReceiveArray(self, slaveAddr: int, values: list[int], rcvCount: int) -> list[int]:
            """
            Sends a one-way message (provided as a list of integer) to a device on the I2C bus,
            then read back the specified number of bytes from device.
            This function checks and reports communication errors on the I2C bus.

            @param slaveAddr : the 7-bit address of the slave device (without the direction bit)
            @param values : a list of data bytes to be sent
            @param rcvCount : the number of bytes to receive once the data bytes are sent

            @return a list of bytes with the data received from slave device.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.i2cSendAndReceiveArray(slaveAddr, values, rcvCount))

    if not _DYNAMIC_HELPERS:
        def writeStr(self, codes: str) -> int:
            """
            Sends a text-encoded I2C code stream to the I2C bus, as is.
            An I2C code stream is a string made of hexadecimal data bytes,
            but that may also include the I2C state transitions code:
            "{S}" to emit a start condition,
            "{R}" for a repeated start condition,
            "{P}" for a stop condition,
            "xx" for receiving a data byte,
            "{A}" to ack a data byte received and
            "{N}" to nack a data byte received.
            If a newline ("\n") is included in the stream, the message
            will be terminated and a newline will also be added to the
            receive stream.

            @param codes : the code stream to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeStr(codes))

    if not _DYNAMIC_HELPERS:
        def writeLine(self, codes: str) -> int:
            """
            Sends a text-encoded I2C code stream to the I2C bus, and release the bus.
            An I2C code stream is a string made of hexadecimal data bytes,
            but that may also include the I2C state transitions code:
            "{S}" to emit a start condition,
            "{R}" for a repeated start condition,
            "{P}" for a stop condition,
            "xx" for receiving a data byte,
            "{A}" to ack a data byte received and
            "{N}" to nack a data byte received.
            At the end of the stream, a stop condition is added if missing
            and a newline is added to the receive buffer as well.

            @param codes : the code stream to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeLine(codes))

    if not _DYNAMIC_HELPERS:
        def writeByte(self, code: int) -> int:
            """
            Sends a single byte to the I2C bus. Depending on the I2C bus state, the byte
            will be interpreted as an address byte or a data byte.

            @param code : the byte to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeByte(code))

    if not _DYNAMIC_HELPERS:
        def writeHex(self, hexString: str) -> int:
            """
            Sends a byte sequence (provided as a hexadecimal string) to the I2C bus.
            Depending on the I2C bus state, the first byte will be interpreted as an
            address byte or a data byte.

            @param hexString : a string of hexadecimal byte codes

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeHex(hexString))

    if not _DYNAMIC_HELPERS:
        def writeBin(self, buff: xarray) -> int:
            """
            Sends a binary buffer to the I2C bus, as is.
            Depending on the I2C bus state, the first byte will be interpreted
            as an address byte or a data byte.

            @param buff : the binary buffer to send

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeBin(buff))

    if not _DYNAMIC_HELPERS:
        def writeArray(self, byteList: list[int]) -> int:
            """
            Sends a byte sequence (provided as a list of bytes) to the I2C bus.
            Depending on the I2C bus state, the first byte will be interpreted as an
            address byte or a data byte.

            @param byteList : a list of byte codes

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.writeArray(byteList))

    if not _DYNAMIC_HELPERS:
        def snoopMessagesEx(self, maxWait: int, maxMsg: int) -> list[YI2cSnoopingRecord]:
            """
            Retrieves messages (both direction) in the I2C port buffer, starting at current position.

            If no message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.
            @param maxMsg : the maximum number of messages to be returned by the function; up to 254.

            @return an array of YI2cSnoopingRecord objects containing the messages found, if any.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.snoopMessagesEx(maxWait, maxMsg))

    if not _DYNAMIC_HELPERS:
        def snoopMessages(self, maxWait: int) -> list[YI2cSnoopingRecord]:
            """
            Retrieves messages (both direction) in the I2C port buffer, starting at current position.

            If no message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.

            @return an array of YI2cSnoopingRecord objects containing the messages found, if any.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.snoopMessages(maxWait))

    # --- (end of generated code: YI2cPort implementation)

