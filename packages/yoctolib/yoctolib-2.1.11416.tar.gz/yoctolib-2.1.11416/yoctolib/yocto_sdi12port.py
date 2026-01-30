# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_sdi12port.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YSdi12Port API for Sdi12Port functions
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
Yoctopuce library: High-level API for YSdi12Port
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_sdi12port_aio
provides: YSdi12Port YSdi12SensorInfo YSdi12SnoopingRecord
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

from .yocto_sdi12port_aio import (
    YSdi12Port as YSdi12Port_aio,
    YSdi12SensorInfo as YSdi12SensorInfo_aio,
    YSdi12SnoopingRecord
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction, YSyncProxy, xarray
)

# --- (generated code: YSdi12SensorInfo class start)
# noinspection PyProtectedMember
class YSdi12SensorInfo(YSyncProxy):
    _aio: YSdi12SensorInfo_aio
    # --- (end of generated code: YSdi12SensorInfo class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSdi12SensorInfo return codes)
        pass
        # --- (end of generated code: YSdi12SensorInfo return codes)


    # --- (generated code: YSdi12SensorInfo implementation)
    if not _DYNAMIC_HELPERS:
        def isValid(self) -> bool:
            """
            Returns the sensor state.

            @return the sensor state.
            """
            return self._run(self._aio.isValid())

    if not _DYNAMIC_HELPERS:
        def get_sensorAddress(self) -> str:
            """
            Returns the sensor address.

            @return the sensor address.
            """
            return self._run(self._aio.get_sensorAddress())

    if not _DYNAMIC_HELPERS:
        def get_sensorProtocol(self) -> str:
            """
            Returns the compatible SDI-12 version of the sensor.

            @return the compatible SDI-12 version of the sensor.
            """
            return self._run(self._aio.get_sensorProtocol())

    if not _DYNAMIC_HELPERS:
        def get_sensorVendor(self) -> str:
            """
            Returns the sensor vendor identification.

            @return the sensor vendor identification.
            """
            return self._run(self._aio.get_sensorVendor())

    if not _DYNAMIC_HELPERS:
        def get_sensorModel(self) -> str:
            """
            Returns the sensor model number.

            @return the sensor model number.
            """
            return self._run(self._aio.get_sensorModel())

    if not _DYNAMIC_HELPERS:
        def get_sensorVersion(self) -> str:
            """
            Returns the sensor version.

            @return the sensor version.
            """
            return self._run(self._aio.get_sensorVersion())

    if not _DYNAMIC_HELPERS:
        def get_sensorSerial(self) -> str:
            """
            Returns the sensor serial number.

            @return the sensor serial number.
            """
            return self._run(self._aio.get_sensorSerial())

    if not _DYNAMIC_HELPERS:
        def get_measureCount(self) -> int:
            """
            Returns the number of sensor measurements.
            This function only works if the sensor is in version 1.4 SDI-12
            and supports metadata commands.

            @return the number of sensor measurements.
            """
            return self._run(self._aio.get_measureCount())

    if not _DYNAMIC_HELPERS:
        def get_measureCommand(self, measureIndex: int) -> str:
            """
            Returns the sensor measurement command.
            This function only works if the sensor is in version 1.4 SDI-12
            and supports metadata commands.

            @param measureIndex : measurement index

            @return the sensor measurement command.
                    On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.get_measureCommand(measureIndex))

    if not _DYNAMIC_HELPERS:
        def get_measurePosition(self, measureIndex: int) -> int:
            """
            Returns sensor measurement position.
            This function only works if the sensor is in version 1.4 SDI-12
            and supports metadata commands.

            @param measureIndex : measurement index

            @return the sensor measurement command.
                    On failure, throws an exception or returns 0.
            """
            return self._run(self._aio.get_measurePosition(measureIndex))

    if not _DYNAMIC_HELPERS:
        def get_measureSymbol(self, measureIndex: int) -> str:
            """
            Returns the measured value symbol.
            This function only works if the sensor is in version 1.4 SDI-12
            and supports metadata commands.

            @param measureIndex : measurement index

            @return the sensor measurement command.
                    On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.get_measureSymbol(measureIndex))

    if not _DYNAMIC_HELPERS:
        def get_measureUnit(self, measureIndex: int) -> str:
            """
            Returns the unit of the measured value.
            This function only works if the sensor is in version 1.4 SDI-12
            and supports metadata commands.

            @param measureIndex : measurement index

            @return the sensor measurement command.
                    On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.get_measureUnit(measureIndex))

    if not _DYNAMIC_HELPERS:
        def get_measureDescription(self, measureIndex: int) -> str:
            """
            Returns the description of the measured value.
            This function only works if the sensor is in version 1.4 SDI-12
            and supports metadata commands.

            @param measureIndex : measurement index

            @return the sensor measurement command.
                    On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.get_measureDescription(measureIndex))

    # --- (end of generated code: YSdi12SensorInfo implementation)


# --- (generated code: YSdi12Port class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSdi12PortValueCallback = Union[Callable[['YSdi12Port', str], Any], None]
    except TypeError:
        YSdi12PortValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSdi12Port(YFunction):
    """
    The YSdi12Port class allows you to fully drive a Yoctopuce SDI12 port.
    It can be used to send and receive data, and to configure communication
    parameters (baud rate, bit count, parity, flow control and protocol).
    Note that Yoctopuce SDI12 ports are not exposed as virtual COM ports.
    They are meant to be used in the same way as all Yoctopuce devices.

    """
    _aio: YSdi12Port_aio
    # --- (end of generated code: YSdi12Port class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSdi12Port return codes)
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
        # --- (end of generated code: YSdi12Port return codes)

    # --- (generated code: YSdi12Port attributes declaration)
    _rxCount: int
    _txCount: int
    _errCount: int
    _rxMsgCount: int
    _txMsgCount: int
    _lastMsg: str
    _currentJob: str
    _startupJob: str
    _jobMaxTask: int
    _jobMaxSize: int
    _command: str
    _protocol: str
    _voltageLevel: int
    _serialMode: str
    _valueCallbackSdi12Port: YSdi12PortValueCallback
    _rxptr: int
    _rxbuff: xarray
    _rxbuffptr: int
    _eventPos: int
    # --- (end of generated code: YSdi12Port attributes declaration)

    # --- (generated code: YSdi12Port implementation)

    @classmethod
    def FindSdi12Port(cls, func: str) -> YSdi12Port:
        """
        Retrieves an SDI12 port for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the SDI12 port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSdi12Port.isOnline() to test if the SDI12 port is
        indeed online at a given time. In case of ambiguity when looking for
        an SDI12 port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the SDI12 port, for instance
                MyDevice.sdi12Port.

        @return a YSdi12Port object allowing you to drive the SDI12 port.
        """
        return cls._proxy(cls, YSdi12Port_aio.FindSdi12PortInContext(YAPI_aio, func))

    @classmethod
    def FindSdi12PortInContext(cls, yctx: YAPIContext, func: str) -> YSdi12Port:
        """
        Retrieves an SDI12 port for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the SDI12 port is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSdi12Port.isOnline() to test if the SDI12 port is
        indeed online at a given time. In case of ambiguity when looking for
        an SDI12 port by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the SDI12 port, for instance
                MyDevice.sdi12Port.

        @return a YSdi12Port object allowing you to drive the SDI12 port.
        """
        return cls._proxy(cls, YSdi12Port_aio.FindSdi12PortInContext(yctx._aio, func))

    @classmethod
    def FirstSdi12Port(cls) -> Union[YSdi12Port, None]:
        """
        Starts the enumeration of SDI12 ports currently accessible.
        Use the method YSdi12Port.nextSdi12Port() to iterate on
        next SDI12 ports.

        @return a pointer to a YSdi12Port object, corresponding to
                the first SDI12 port currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YSdi12Port_aio.FirstSdi12PortInContext(YAPI_aio))

    @classmethod
    def FirstSdi12PortInContext(cls, yctx: YAPIContext) -> Union[YSdi12Port, None]:
        """
        Starts the enumeration of SDI12 ports currently accessible.
        Use the method YSdi12Port.nextSdi12Port() to iterate on
        next SDI12 ports.

        @param yctx : a YAPI context.

        @return a pointer to a YSdi12Port object, corresponding to
                the first SDI12 port currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YSdi12Port_aio.FirstSdi12PortInContext(yctx._aio))

    def nextSdi12Port(self) -> Union[YSdi12Port, None]:
        """
        Continues the enumeration of SDI12 ports started using yFirstSdi12Port().
        Caution: You can't make any assumption about the returned SDI12 ports order.
        If you want to find a specific an SDI12 port, use Sdi12Port.findSdi12Port()
        and a hardwareID or a logical name.

        @return a pointer to a YSdi12Port object, corresponding to
                an SDI12 port currently online, or a None pointer
                if there are no more SDI12 ports to enumerate.
        """
        return self._proxy(type(self), self._aio.nextSdi12Port())

    if not _DYNAMIC_HELPERS:
        def get_rxCount(self) -> int:
            """
            Returns the total number of bytes received since last reset.

            @return an integer corresponding to the total number of bytes received since last reset

            On failure, throws an exception or returns YSdi12Port.RXCOUNT_INVALID.
            """
            return self._run(self._aio.get_rxCount())

    if not _DYNAMIC_HELPERS:
        def get_txCount(self) -> int:
            """
            Returns the total number of bytes transmitted since last reset.

            @return an integer corresponding to the total number of bytes transmitted since last reset

            On failure, throws an exception or returns YSdi12Port.TXCOUNT_INVALID.
            """
            return self._run(self._aio.get_txCount())

    if not _DYNAMIC_HELPERS:
        def get_errCount(self) -> int:
            """
            Returns the total number of communication errors detected since last reset.

            @return an integer corresponding to the total number of communication errors detected since last reset

            On failure, throws an exception or returns YSdi12Port.ERRCOUNT_INVALID.
            """
            return self._run(self._aio.get_errCount())

    if not _DYNAMIC_HELPERS:
        def get_rxMsgCount(self) -> int:
            """
            Returns the total number of messages received since last reset.

            @return an integer corresponding to the total number of messages received since last reset

            On failure, throws an exception or returns YSdi12Port.RXMSGCOUNT_INVALID.
            """
            return self._run(self._aio.get_rxMsgCount())

    if not _DYNAMIC_HELPERS:
        def get_txMsgCount(self) -> int:
            """
            Returns the total number of messages send since last reset.

            @return an integer corresponding to the total number of messages send since last reset

            On failure, throws an exception or returns YSdi12Port.TXMSGCOUNT_INVALID.
            """
            return self._run(self._aio.get_txMsgCount())

    if not _DYNAMIC_HELPERS:
        def get_lastMsg(self) -> str:
            """
            Returns the latest message fully received.

            @return a string corresponding to the latest message fully received

            On failure, throws an exception or returns YSdi12Port.LASTMSG_INVALID.
            """
            return self._run(self._aio.get_lastMsg())

    if not _DYNAMIC_HELPERS:
        def get_currentJob(self) -> str:
            """
            Returns the name of the job file currently in use.

            @return a string corresponding to the name of the job file currently in use

            On failure, throws an exception or returns YSdi12Port.CURRENTJOB_INVALID.
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

            On failure, throws an exception or returns YSdi12Port.STARTUPJOB_INVALID.
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

            On failure, throws an exception or returns YSdi12Port.JOBMAXTASK_INVALID.
            """
            return self._run(self._aio.get_jobMaxTask())

    if not _DYNAMIC_HELPERS:
        def get_jobMaxSize(self) -> int:
            """
            Returns maximum size allowed for job files.

            @return an integer corresponding to maximum size allowed for job files

            On failure, throws an exception or returns YSdi12Port.JOBMAXSIZE_INVALID.
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
            "Frame:[timeout]ms" for binary messages separated by a delay time,
            "Char" for a continuous ASCII stream or
            "Byte" for a continuous binary stream.

            @return a string corresponding to the type of protocol used over the serial line, as a string

            On failure, throws an exception or returns YSdi12Port.PROTOCOL_INVALID.
            """
            return self._run(self._aio.get_protocol())

    if not _DYNAMIC_HELPERS:
        def set_protocol(self, newval: str) -> int:
            """
            Changes the type of protocol used over the serial line.
            Possible values are "Line" for ASCII messages separated by CR and/or LF,
            "Frame:[timeout]ms" for binary messages separated by a delay time,
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

            @return a value among YSdi12Port.VOLTAGELEVEL_OFF, YSdi12Port.VOLTAGELEVEL_TTL3V,
            YSdi12Port.VOLTAGELEVEL_TTL3VR, YSdi12Port.VOLTAGELEVEL_TTL5V, YSdi12Port.VOLTAGELEVEL_TTL5VR,
            YSdi12Port.VOLTAGELEVEL_RS232, YSdi12Port.VOLTAGELEVEL_RS485, YSdi12Port.VOLTAGELEVEL_TTL1V8 and
            YSdi12Port.VOLTAGELEVEL_SDI12 corresponding to the voltage level used on the serial line

            On failure, throws an exception or returns YSdi12Port.VOLTAGELEVEL_INVALID.
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

            @param newval : a value among YSdi12Port.VOLTAGELEVEL_OFF, YSdi12Port.VOLTAGELEVEL_TTL3V,
            YSdi12Port.VOLTAGELEVEL_TTL3VR, YSdi12Port.VOLTAGELEVEL_TTL5V, YSdi12Port.VOLTAGELEVEL_TTL5VR,
            YSdi12Port.VOLTAGELEVEL_RS232, YSdi12Port.VOLTAGELEVEL_RS485, YSdi12Port.VOLTAGELEVEL_TTL1V8 and
            YSdi12Port.VOLTAGELEVEL_SDI12 corresponding to the voltage type used on the serial line

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_voltageLevel(newval))

    if not _DYNAMIC_HELPERS:
        def get_serialMode(self) -> str:
            """
            Returns the serial port communication parameters, as a string such as
            "1200,7E1,Simplex". The string includes the baud rate, the number of data bits,
            the parity, and the number of stop bits. The suffix "Simplex" denotes
            the fact that transmission in both directions is multiplexed on the
            same transmission line.

            @return a string corresponding to the serial port communication parameters, as a string such as
                    "1200,7E1,Simplex"

            On failure, throws an exception or returns YSdi12Port.SERIALMODE_INVALID.
            """
            return self._run(self._aio.get_serialMode())

    if not _DYNAMIC_HELPERS:
        def set_serialMode(self, newval: str) -> int:
            """
            Changes the serial port communication parameters, with a string such as
            "1200,7E1,Simplex". The string includes the baud rate, the number of data bits,
            the parity, and the number of stop bits. The suffix "Simplex" denotes
            the fact that transmission in both directions is multiplexed on the
            same transmission line.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the serial port communication parameters, with a string such as
                    "1200,7E1,Simplex"

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_serialMode(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YSdi12PortValueCallback) -> int:
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
        def querySdi12(self, sensorAddr: str, cmd: str, maxWait: int) -> str:
            """
            Sends a SDI-12 query to the bus, and reads the sensor immediate reply.
            This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

            @param sensorAddr : the sensor address, as a string
            @param cmd : the SDI12 query to send (without address and exclamation point)
            @param maxWait : the maximum timeout to wait for a reply from sensor, in millisecond

            @return the reply returned by the sensor, without newline, as a string.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.querySdi12(sensorAddr, cmd, maxWait))

    def discoverSingleSensor(self) -> YSdi12SensorInfo:
        """
        Sends a discovery command to the bus, and reads the sensor information reply.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.
        This function work when only one sensor is connected.

        @return the reply returned by the sensor, as a YSdi12SensorInfo object.

        On failure, throws an exception or returns an empty string.
        """
        return self._proxy(YSdi12SensorInfo, self._run(self._aio.discoverSingleSensor()))

    if not _DYNAMIC_HELPERS:
        def discoverAllSensors(self) -> list[YSdi12SensorInfo]:
            """
            Sends a discovery command to the bus, and reads all sensors information reply.
            This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

            @return all the information from every connected sensor, as an array of YSdi12SensorInfo object.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.discoverAllSensors())

    if not _DYNAMIC_HELPERS:
        def readSensor(self, sensorAddr: str, measCmd: str, maxWait: int) -> list[float]:
            """
            Sends a mesurement command to the SDI-12 bus, and reads the sensor immediate reply.
            The supported commands are:
            M: Measurement start control
            M1...M9: Additional measurement start command
            D: Measurement reading control
            This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

            @param sensorAddr : the sensor address, as a string
            @param measCmd : the SDI12 query to send (without address and exclamation point)
            @param maxWait : the maximum timeout to wait for a reply from sensor, in millisecond

            @return the reply returned by the sensor, without newline, as a list of float.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.readSensor(sensorAddr, measCmd, maxWait))

    def changeAddress(self, oldAddress: str, newAddress: str) -> YSdi12SensorInfo:
        """
        Changes the address of the selected sensor, and returns the sensor information with the new address.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param oldAddress : Actual sensor address, as a string
        @param newAddress : New sensor address, as a string

        @return the sensor address and information , as a YSdi12SensorInfo object.

        On failure, throws an exception or returns an empty string.
        """
        return self._proxy(YSdi12SensorInfo, self._run(self._aio.changeAddress(oldAddress, newAddress)))

    def getSensorInformation(self, sensorAddr: str) -> YSdi12SensorInfo:
        """
        Sends a information command to the bus, and reads sensors information selected.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param sensorAddr : Sensor address, as a string

        @return the reply returned by the sensor, as a YSdi12Port object.

        On failure, throws an exception or returns an empty string.
        """
        return self._proxy(YSdi12SensorInfo, self._run(self._aio.getSensorInformation(sensorAddr)))

    if not _DYNAMIC_HELPERS:
        def readConcurrentMeasurements(self, sensorAddr: str) -> list[float]:
            """
            Sends a information command to the bus, and reads sensors information selected.
            This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

            @param sensorAddr : Sensor address, as a string

            @return the reply returned by the sensor, as a YSdi12Port object.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.readConcurrentMeasurements(sensorAddr))

    if not _DYNAMIC_HELPERS:
        def requestConcurrentMeasurements(self, sensorAddr: str) -> int:
            """
            Sends a information command to the bus, and reads sensors information selected.
            This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

            @param sensorAddr : Sensor address, as a string

            @return the reply returned by the sensor, as a YSdi12Port object.

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.requestConcurrentMeasurements(sensorAddr))

    if not _DYNAMIC_HELPERS:
        def snoopMessagesEx(self, maxWait: int, maxMsg: int) -> list[YSdi12SnoopingRecord]:
            """
            Retrieves messages (both direction) in the SDI12 port buffer, starting at current position.

            If no message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.
            @param maxMsg : the maximum number of messages to be returned by the function; up to 254.

            @return an array of YSdi12SnoopingRecord objects containing the messages found, if any.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.snoopMessagesEx(maxWait, maxMsg))

    if not _DYNAMIC_HELPERS:
        def snoopMessages(self, maxWait: int) -> list[YSdi12SnoopingRecord]:
            """
            Retrieves messages (both direction) in the SDI12 port buffer, starting at current position.

            If no message is found, the search waits for one up to the specified maximum timeout
            (in milliseconds).

            @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                    in the receive buffer.

            @return an array of YSdi12SnoopingRecord objects containing the messages found, if any.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.snoopMessages(maxWait))

    # --- (end of generated code: YSdi12Port implementation)

