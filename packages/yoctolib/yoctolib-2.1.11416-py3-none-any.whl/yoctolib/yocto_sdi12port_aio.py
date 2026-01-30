# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_sdi12port_aio.py 70736 2025-12-12 07:53:30Z mvuilleu $
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
Yoctopuce library: Asyncio implementation of YSdi12Port
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True  # noqa

from .yocto_api_aio import (
    YAPIContext, YAPI, YAPI_Exception, YFunction, HwId, hwid2str,
    xarray, xbytearray, xStringIO
)

# --- (generated code: YSdi12SnoopingRecord class start)
# noinspection PyProtectedMember
class YSdi12SnoopingRecord:
    # --- (end of generated code: YSdi12SnoopingRecord class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSdi12SnoopingRecord return codes)
        pass
        # --- (end of generated code: YSdi12SnoopingRecord return codes)

    # --- (generated code: YSdi12SnoopingRecord attributes declaration)
    _tim: int
    _pos: int
    _dir: int
    _msg: str
    # --- (end of generated code: YSdi12SnoopingRecord attributes declaration)

    def __init__(self, json_data: xStringIO):
        # --- (generated code: YSdi12SnoopingRecord constructor)
        self._tim = 0
        self._pos = 0
        self._dir = 0
        self._msg = ''
        # --- (end of generated code: YSdi12SnoopingRecord constructor)
        json_val: Any = json.load(json_data)
        if 't' in json_val:
            self._tim = json_val["t"]
        if 'p' in json_val:
            self._pos = json_val["p"]
        if 'm' in json_val:
            m: str = json_val["m"]
            if m[0] == '<':
                self._dir = 1
            else:
                self._dir = 0
            self._msg = m[1:]

    # --- (generated code: YSdi12SnoopingRecord implementation)
    def get_time(self) -> int:
        """
        Returns the elapsed time, in ms, since the beginning of the preceding message.

        @return the elapsed time, in ms, since the beginning of the preceding message.
        """
        return self._tim

    def get_pos(self) -> int:
        """
        Returns the absolute position of the message end.

        @return the absolute position of the message end.
        """
        return self._pos

    def get_direction(self) -> int:
        """
        Returns the message direction (RX=0, TX=1).

        @return the message direction (RX=0, TX=1).
        """
        return self._dir

    def get_message(self) -> str:
        """
        Returns the message content.

        @return the message content.
        """
        return self._msg

    # --- (end of generated code: YSdi12SnoopingRecord implementation)


# --- (generated code: YSdi12SensorInfo class start)
# noinspection PyProtectedMember
class YSdi12SensorInfo:
    # --- (end of generated code: YSdi12SensorInfo class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSdi12SensorInfo return codes)
        pass
        # --- (end of generated code: YSdi12SensorInfo return codes)

    # --- (generated code: YSdi12SensorInfo attributes declaration)
    _sdi12Port: YSdi12Port
    _isValid: bool
    _addr: str
    _proto: str
    _mfg: str
    _model: str
    _ver: str
    _sn: str
    _valuesDesc: list[list[str]]
    # --- (end of generated code: YSdi12SensorInfo attributes declaration)

    def __init__(self, sdi12port: YSdi12Port, json: str):
        # --- (generated code: YSdi12SensorInfo constructor)
        self._isValid = False
        self._addr = ''
        self._proto = ''
        self._mfg = ''
        self._model = ''
        self._ver = ''
        self._sn = ''
        self._valuesDesc = []
        # --- (end of generated code: YSdi12SensorInfo constructor)
        self._sdi12Port = sdi12port
        self._parseInfoStr(json)

    @staticmethod
    def _throw(errType: int, errMsg: str):
        if not YAPI.ExceptionsDisabled:
            raise YAPI_Exception(errType, errMsg)

    # --- (generated code: YSdi12SensorInfo implementation)
    async def isValid(self) -> bool:
        """
        Returns the sensor state.

        @return the sensor state.
        """
        return self._isValid

    async def get_sensorAddress(self) -> str:
        """
        Returns the sensor address.

        @return the sensor address.
        """
        return self._addr

    async def get_sensorProtocol(self) -> str:
        """
        Returns the compatible SDI-12 version of the sensor.

        @return the compatible SDI-12 version of the sensor.
        """
        return self._proto

    async def get_sensorVendor(self) -> str:
        """
        Returns the sensor vendor identification.

        @return the sensor vendor identification.
        """
        return self._mfg

    async def get_sensorModel(self) -> str:
        """
        Returns the sensor model number.

        @return the sensor model number.
        """
        return self._model

    async def get_sensorVersion(self) -> str:
        """
        Returns the sensor version.

        @return the sensor version.
        """
        return self._ver

    async def get_sensorSerial(self) -> str:
        """
        Returns the sensor serial number.

        @return the sensor serial number.
        """
        return self._sn

    async def get_measureCount(self) -> int:
        """
        Returns the number of sensor measurements.
        This function only works if the sensor is in version 1.4 SDI-12
        and supports metadata commands.

        @return the number of sensor measurements.
        """
        return len(self._valuesDesc)

    async def get_measureCommand(self, measureIndex: int) -> str:
        """
        Returns the sensor measurement command.
        This function only works if the sensor is in version 1.4 SDI-12
        and supports metadata commands.

        @param measureIndex : measurement index

        @return the sensor measurement command.
                On failure, throws an exception or returns an empty string.
        """
        if not (measureIndex < len(self._valuesDesc)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid measure index")
            return ""
        return self._valuesDesc[measureIndex][0]

    async def get_measurePosition(self, measureIndex: int) -> int:
        """
        Returns sensor measurement position.
        This function only works if the sensor is in version 1.4 SDI-12
        and supports metadata commands.

        @param measureIndex : measurement index

        @return the sensor measurement command.
                On failure, throws an exception or returns 0.
        """
        if not (measureIndex < len(self._valuesDesc)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid measure index")
            return 0
        return YAPI._atoi(self._valuesDesc[measureIndex][2])

    async def get_measureSymbol(self, measureIndex: int) -> str:
        """
        Returns the measured value symbol.
        This function only works if the sensor is in version 1.4 SDI-12
        and supports metadata commands.

        @param measureIndex : measurement index

        @return the sensor measurement command.
                On failure, throws an exception or returns an empty string.
        """
        if not (measureIndex < len(self._valuesDesc)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid measure index")
            return ""
        return self._valuesDesc[measureIndex][3]

    async def get_measureUnit(self, measureIndex: int) -> str:
        """
        Returns the unit of the measured value.
        This function only works if the sensor is in version 1.4 SDI-12
        and supports metadata commands.

        @param measureIndex : measurement index

        @return the sensor measurement command.
                On failure, throws an exception or returns an empty string.
        """
        if not (measureIndex < len(self._valuesDesc)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid measure index")
            return ""
        return self._valuesDesc[measureIndex][4]

    async def get_measureDescription(self, measureIndex: int) -> str:
        """
        Returns the description of the measured value.
        This function only works if the sensor is in version 1.4 SDI-12
        and supports metadata commands.

        @param measureIndex : measurement index

        @return the sensor measurement command.
                On failure, throws an exception or returns an empty string.
        """
        if not (measureIndex < len(self._valuesDesc)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid measure index")
            return ""
        return self._valuesDesc[measureIndex][5]

    async def get_typeMeasure(self) -> list[list[str]]:
        return self._valuesDesc

    def _parseInfoStr(self, infoStr: str) -> None:
        errmsg: str

        if len(infoStr) > 1:
            if infoStr[0: 0 + 2] == "ER":
                errmsg = infoStr[2: 2 + len(infoStr)-2]
                self._addr = errmsg
                self._proto = errmsg
                self._mfg = errmsg
                self._model = errmsg
                self._ver = errmsg
                self._sn = errmsg
                self._isValid = False
            else:
                self._addr = infoStr[0: 0 + 1]
                self._proto = infoStr[1: 1 + 2]
                self._mfg = infoStr[3: 3 + 8]
                self._model = infoStr[11: 11 + 6]
                self._ver = infoStr[17: 17 + 3]
                self._sn = infoStr[20: 20 + len(infoStr)-20]
                self._isValid = True

    async def _queryValueInfo(self) -> None:
        val: list[list[str]] = []
        data: list[str] = []
        infoNbVal: str
        cmd: str
        infoVal: str
        value: str
        nbVal: int
        k: int
        i: int
        j: int
        listVal: list[str] = []
        size: int

        k = 0
        size = 4
        while k < 10:
            infoNbVal = await self._sdi12Port.querySdi12(self._addr, "IM%d" % k, 5000)
            if len(infoNbVal) > 1:
                value = infoNbVal[4: 4 + len(infoNbVal)-4]
                nbVal = YAPI._atoi(value)
                if nbVal != 0:
                    del val[:]
                    i = 0
                    while i < nbVal:
                        cmd = "IM%d_00%d" % (k, i+1)
                        infoVal = await self._sdi12Port.querySdi12(self._addr, cmd, 5000)
                        data = (infoVal).split(';')
                        data = (data[0]).split(',')
                        del listVal[:]
                        listVal.append("M%d" % k)
                        listVal.append(str(i+1))
                        j = 0
                        while len(data) < size:
                            data.append("")
                        while j < len(data):
                            listVal.append(data[j])
                            j = j + 1
                        val.append(listVal[:])
                        i = i + 1
            k = k + 1
        self._valuesDesc = val

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
    _valueCallback: YSdi12PortValueCallback
    _rxptr: int
    _rxbuff: xarray
    _rxbuffptr: int
    _eventPos: int
    # --- (end of generated code: YSdi12Port attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Sdi12Port', func)
        # --- (generated code: YSdi12Port constructor)
        self._rxptr = 0
        self._rxbuff = xbytearray(0)
        self._rxbuffptr = 0
        self._eventPos = 0
        # --- (end of generated code: YSdi12Port constructor)

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
        return cls.FindSdi12PortInContext(YAPI, func)

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
        obj: Union[YSdi12Port, None] = yctx._findInCache('Sdi12Port', func)
        if obj:
            return obj
        return YSdi12Port(yctx, func)

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
        return cls.FirstSdi12PortInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('Sdi12Port')
        if hwid:
            return cls.FindSdi12PortInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Sdi12Port', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindSdi12PortInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_rxCount(self) -> int:
        """
        Returns the total number of bytes received since last reset.

        @return an integer corresponding to the total number of bytes received since last reset

        On failure, throws an exception or returns YSdi12Port.RXCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("rxCount")
        if json_val is None:
            return YSdi12Port.RXCOUNT_INVALID
        return json_val

    async def get_txCount(self) -> int:
        """
        Returns the total number of bytes transmitted since last reset.

        @return an integer corresponding to the total number of bytes transmitted since last reset

        On failure, throws an exception or returns YSdi12Port.TXCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("txCount")
        if json_val is None:
            return YSdi12Port.TXCOUNT_INVALID
        return json_val

    async def get_errCount(self) -> int:
        """
        Returns the total number of communication errors detected since last reset.

        @return an integer corresponding to the total number of communication errors detected since last reset

        On failure, throws an exception or returns YSdi12Port.ERRCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("errCount")
        if json_val is None:
            return YSdi12Port.ERRCOUNT_INVALID
        return json_val

    async def get_rxMsgCount(self) -> int:
        """
        Returns the total number of messages received since last reset.

        @return an integer corresponding to the total number of messages received since last reset

        On failure, throws an exception or returns YSdi12Port.RXMSGCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("rxMsgCount")
        if json_val is None:
            return YSdi12Port.RXMSGCOUNT_INVALID
        return json_val

    async def get_txMsgCount(self) -> int:
        """
        Returns the total number of messages send since last reset.

        @return an integer corresponding to the total number of messages send since last reset

        On failure, throws an exception or returns YSdi12Port.TXMSGCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("txMsgCount")
        if json_val is None:
            return YSdi12Port.TXMSGCOUNT_INVALID
        return json_val

    async def get_lastMsg(self) -> str:
        """
        Returns the latest message fully received.

        @return a string corresponding to the latest message fully received

        On failure, throws an exception or returns YSdi12Port.LASTMSG_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("lastMsg")
        if json_val is None:
            return YSdi12Port.LASTMSG_INVALID
        return json_val

    async def get_currentJob(self) -> str:
        """
        Returns the name of the job file currently in use.

        @return a string corresponding to the name of the job file currently in use

        On failure, throws an exception or returns YSdi12Port.CURRENTJOB_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("currentJob")
        if json_val is None:
            return YSdi12Port.CURRENTJOB_INVALID
        return json_val

    async def set_currentJob(self, newval: str) -> int:
        """
        Selects a job file to run immediately. If an empty string is
        given as argument, stops running current job file.

        @param newval : a string

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("currentJob", rest_val)

    async def get_startupJob(self) -> str:
        """
        Returns the job file to use when the device is powered on.

        @return a string corresponding to the job file to use when the device is powered on

        On failure, throws an exception or returns YSdi12Port.STARTUPJOB_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("startupJob")
        if json_val is None:
            return YSdi12Port.STARTUPJOB_INVALID
        return json_val

    async def set_startupJob(self, newval: str) -> int:
        """
        Changes the job to use when the device is powered on.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the job to use when the device is powered on

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("startupJob", rest_val)

    async def get_jobMaxTask(self) -> int:
        """
        Returns the maximum number of tasks in a job that the device can handle.

        @return an integer corresponding to the maximum number of tasks in a job that the device can handle

        On failure, throws an exception or returns YSdi12Port.JOBMAXTASK_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("jobMaxTask")
        if json_val is None:
            return YSdi12Port.JOBMAXTASK_INVALID
        return json_val

    async def get_jobMaxSize(self) -> int:
        """
        Returns maximum size allowed for job files.

        @return an integer corresponding to maximum size allowed for job files

        On failure, throws an exception or returns YSdi12Port.JOBMAXSIZE_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("jobMaxSize")
        if json_val is None:
            return YSdi12Port.JOBMAXSIZE_INVALID
        return json_val

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YSdi12Port.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    async def get_protocol(self) -> str:
        """
        Returns the type of protocol used over the serial line, as a string.
        Possible values are "Line" for ASCII messages separated by CR and/or LF,
        "Frame:[timeout]ms" for binary messages separated by a delay time,
        "Char" for a continuous ASCII stream or
        "Byte" for a continuous binary stream.

        @return a string corresponding to the type of protocol used over the serial line, as a string

        On failure, throws an exception or returns YSdi12Port.PROTOCOL_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("protocol")
        if json_val is None:
            return YSdi12Port.PROTOCOL_INVALID
        return json_val

    async def set_protocol(self, newval: str) -> int:
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
        rest_val = newval
        return await self._setAttr("protocol", rest_val)

    async def get_voltageLevel(self) -> int:
        """
        Returns the voltage level used on the serial line.

        @return a value among YSdi12Port.VOLTAGELEVEL_OFF, YSdi12Port.VOLTAGELEVEL_TTL3V,
        YSdi12Port.VOLTAGELEVEL_TTL3VR, YSdi12Port.VOLTAGELEVEL_TTL5V, YSdi12Port.VOLTAGELEVEL_TTL5VR,
        YSdi12Port.VOLTAGELEVEL_RS232, YSdi12Port.VOLTAGELEVEL_RS485, YSdi12Port.VOLTAGELEVEL_TTL1V8 and
        YSdi12Port.VOLTAGELEVEL_SDI12 corresponding to the voltage level used on the serial line

        On failure, throws an exception or returns YSdi12Port.VOLTAGELEVEL_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("voltageLevel")
        if json_val is None:
            return YSdi12Port.VOLTAGELEVEL_INVALID
        return json_val

    async def set_voltageLevel(self, newval: int) -> int:
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
        rest_val = str(newval)
        return await self._setAttr("voltageLevel", rest_val)

    async def get_serialMode(self) -> str:
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
        json_val: Union[str, None] = await self._fromCache("serialMode")
        if json_val is None:
            return YSdi12Port.SERIALMODE_INVALID
        return json_val

    async def set_serialMode(self, newval: str) -> int:
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
        rest_val = newval
        return await self._setAttr("serialMode", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YSdi12PortValueCallback) -> int:
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

    async def sendCommand(self, text: str) -> int:
        return await self.set_command(text)

    async def readLine(self) -> str:
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
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        res: str

        url = "rxmsg.json?pos=%d&len=1&maxw=1" % self._rxptr
        msgbin = await self._download(url)
        msgarr = self._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return ""
        # last element of array is the new position
        msglen = msglen - 1
        self._rxptr = self._decode_json_int(msgarr[msglen])
        if msglen == 0:
            return ""
        res = self._json_get_string(msgarr[0])
        return res

    async def readMessages(self, pattern: str, maxWait: int) -> list[str]:
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
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        res: list[str] = []
        idx: int

        url = "rxmsg.json?pos=%d&maxw=%d&pat=%s" % (self._rxptr, maxWait, pattern)
        msgbin = await self._download(url)
        msgarr = self._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return res
        # last element of array is the new position
        msglen = msglen - 1
        self._rxptr = self._decode_json_int(msgarr[msglen])
        idx = 0

        while idx < msglen:
            res.append(self._json_get_string(msgarr[idx]))
            idx = idx + 1

        return res

    async def read_seek(self, absPos: int) -> int:
        """
        Changes the current internal stream position to the specified value. This function
        does not affect the device, it only changes the value stored in the API object
        for the next read operations.

        @param absPos : the absolute position index for next read operations.

        @return nothing.
        """
        self._rxptr = absPos
        return YAPI.SUCCESS

    async def read_tell(self) -> int:
        """
        Returns the current absolute stream position pointer of the API object.

        @return the absolute position index for next read operations.
        """
        return self._rxptr

    async def read_avail(self) -> int:
        """
        Returns the number of bytes available to read in the input buffer starting from the
        current absolute stream position pointer of the API object.

        @return the number of bytes available to read
        """
        availPosStr: str
        atPos: int
        res: int
        databin: xarray

        databin = await self._download("rxcnt.bin?pos=%d" % self._rxptr)
        availPosStr = databin.decode('latin-1')
        atPos = availPosStr.find("@")
        res = YAPI._atoi(availPosStr[0: 0 + atPos])
        return res

    async def end_tell(self) -> int:
        availPosStr: str
        atPos: int
        res: int
        databin: xarray

        databin = await self._download("rxcnt.bin?pos=%d" % self._rxptr)
        availPosStr = databin.decode('latin-1')
        atPos = availPosStr.find("@")
        res = YAPI._atoi(availPosStr[atPos+1: atPos+1 + len(availPosStr)-atPos-1])
        return res

    async def queryLine(self, query: str, maxWait: int) -> str:
        """
        Sends a text line query to the serial port, and reads the reply, if any.
        This function is intended to be used when the serial port is configured for 'Line' protocol.

        @param query : the line query to send (without CR/LF)
        @param maxWait : the maximum number of milliseconds to wait for a reply.

        @return the next text line received after sending the text query, as a string.
                Additional lines can be obtained by calling readLine or readMessages.

        On failure, throws an exception or returns an empty string.
        """
        prevpos: int
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        res: str
        if len(query) <= 80:
            # fast query
            url = "rxmsg.json?len=1&maxw=%d&cmd=!%s" % (maxWait, self._escapeAttr(query))
        else:
            # long query
            prevpos = await self.end_tell()
            await self._upload("txdata", xbytearray(query + "\r\n", 'latin-1'))
            url = "rxmsg.json?len=1&maxw=%d&pos=%d" % (maxWait, prevpos)

        msgbin = await self._download(url)
        msgarr = self._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return ""
        # last element of array is the new position
        msglen = msglen - 1
        self._rxptr = self._decode_json_int(msgarr[msglen])
        if msglen == 0:
            return ""
        res = self._json_get_string(msgarr[0])
        return res

    async def queryHex(self, hexString: str, maxWait: int) -> str:
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
        prevpos: int
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        res: str
        if len(hexString) <= 80:
            # fast query
            url = "rxmsg.json?len=1&maxw=%d&cmd=$%s" % (maxWait, hexString)
        else:
            # long query
            prevpos = await self.end_tell()
            await self._upload("txdata", YAPI._hexStrToBin(hexString))
            url = "rxmsg.json?len=1&maxw=%d&pos=%d" % (maxWait, prevpos)

        msgbin = await self._download(url)
        msgarr = self._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return ""
        # last element of array is the new position
        msglen = msglen - 1
        self._rxptr = self._decode_json_int(msgarr[msglen])
        if msglen == 0:
            return ""
        res = self._json_get_string(msgarr[0])
        return res

    async def uploadJob(self, jobfile: str, jsonDef: str) -> int:
        """
        Saves the job definition string (JSON data) into a job file.
        The job file can be later enabled using selectJob().

        @param jobfile : name of the job file to save on the device filesystem
        @param jsonDef : a string containing a JSON definition of the job

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        await self._upload(jobfile, xbytearray(jsonDef, 'latin-1'))
        return YAPI.SUCCESS

    async def selectJob(self, jobfile: str) -> int:
        """
        Load and start processing the specified job file. The file must have
        been previously created using the user interface or uploaded on the
        device filesystem using the uploadJob() function.

        @param jobfile : name of the job file (on the device filesystem)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_currentJob(jobfile)

    async def reset(self) -> int:
        """
        Clears the serial port buffer and resets counters to zero.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        self._eventPos = 0
        self._rxptr = 0
        self._rxbuffptr = 0
        self._rxbuff = xbytearray(0)

        return await self.sendCommand("Z")

    async def writeByte(self, code: int) -> int:
        """
        Sends a single byte to the serial port.

        @param code : the byte to send

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.sendCommand("$%02X" % code)

    async def writeStr(self, text: str) -> int:
        """
        Sends an ASCII string to the serial port, as is.

        @param text : the text string to send

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        idx: int
        ch: int
        buff = xbytearray(text, 'latin-1')
        bufflen = len(buff)
        if bufflen < 100:
            # if string is pure text, we can send it as a simple command (faster)
            ch = 0x20
            idx = 0
            while (idx < bufflen) and(ch != 0):
                ch = buff[idx]
                if (ch >= 0x20) and (ch < 0x7f):
                    idx = idx + 1
                else:
                    ch = 0
            if idx >= bufflen:
                return await self.sendCommand("+%s" % text)
        # send string using file upload
        return await self._upload("txdata", buff)

    async def writeBin(self, buff: xarray) -> int:
        """
        Sends a binary buffer to the serial port, as is.

        @param buff : the binary buffer to send

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._upload("txdata", buff)

    async def writeArray(self, byteList: list[int]) -> int:
        """
        Sends a byte sequence (provided as a list of bytes) to the serial port.

        @param byteList : a list of byte codes

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        idx: int
        hexb: int
        res: int
        bufflen = len(byteList)
        buff = xbytearray(bufflen)
        idx = 0
        while idx < bufflen:
            hexb = byteList[idx]
            buff[idx] = hexb
            idx = idx + 1

        res = await self._upload("txdata", buff)
        return res

    async def writeHex(self, hexString: str) -> int:
        """
        Sends a byte sequence (provided as a hexadecimal string) to the serial port.

        @param hexString : a string of hexadecimal byte codes

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        idx: int
        hexb: int
        res: int
        bufflen = len(hexString)
        if bufflen < 100:
            return await self.sendCommand("$%s" % hexString)
        bufflen = (bufflen >> 1)
        buff = xbytearray(bufflen)
        idx = 0
        while idx < bufflen:
            hexb = int(hexString[2 * idx: 2 * idx + 2], 16)
            buff[idx] = hexb
            idx = idx + 1

        res = await self._upload("txdata", buff)
        return res

    async def writeLine(self, text: str) -> int:
        """
        Sends an ASCII string to the serial port, followed by a line break (CR LF).

        @param text : the text string to send

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        idx: int
        ch: int
        buff = xbytearray("%s\r\n" % text, 'latin-1')
        bufflen = len(buff)-2
        if bufflen < 100:
            # if string is pure text, we can send it as a simple command (faster)
            ch = 0x20
            idx = 0
            while (idx < bufflen) and(ch != 0):
                ch = buff[idx]
                if (ch >= 0x20) and (ch < 0x7f):
                    idx = idx + 1
                else:
                    ch = 0
            if idx >= bufflen:
                return await self.sendCommand("!%s" % text)
        # send string using file upload
        return await self._upload("txdata", buff)

    async def readByte(self) -> int:
        """
        Reads one byte from the receive buffer, starting at current stream position.
        If data at current stream position is not available anymore in the receive buffer,
        or if there is no data available yet, the function returns YAPI.NO_MORE_DATA.

        @return the next byte

        On failure, throws an exception or returns a negative error code.
        """
        currpos: int
        reqlen: int
        buff: xarray
        bufflen: int
        mult: int
        endpos: int
        res: int
        # first check if we have the requested character in the look-ahead buffer
        bufflen = len(self._rxbuff)
        if (self._rxptr >= self._rxbuffptr) and (self._rxptr < self._rxbuffptr+bufflen):
            res = self._rxbuff[self._rxptr-self._rxbuffptr]
            self._rxptr = self._rxptr + 1
            return res
        # try to preload more than one byte to speed-up byte-per-byte access
        currpos = self._rxptr
        reqlen = 1024
        buff = await self.readBin(reqlen)
        bufflen = len(buff)
        if (bufflen > 0) and (self._rxptr == currpos+bufflen):
            # up to 1024 bytes in buffer, all in direction Rx
            res = buff[0]
            self._rxptr = currpos+1
            self._rxbuffptr = currpos
            self._rxbuff = buff
            return res
        # mixed bidirectional data, retry with a smaller block
        self._rxptr = currpos
        reqlen = 16
        buff = await self.readBin(reqlen)
        bufflen = len(buff)
        if (bufflen > 0) and (self._rxptr == currpos+bufflen):
            # up to 16 bytes in buffer, all in direction Rx
            res = buff[0]
            self._rxptr = currpos+1
            self._rxbuffptr = currpos
            self._rxbuff = buff
            return res
        # still mixed, need to process character by character
        self._rxptr = currpos

        buff = await self._download("rxdata.bin?pos=%d&len=1" % self._rxptr)
        bufflen = len(buff) - 1
        endpos = 0
        mult = 1
        while (bufflen > 0) and(buff[bufflen] != 64):
            endpos = endpos + mult * (buff[bufflen] - 48)
            mult = mult * 10
            bufflen = bufflen - 1
        self._rxptr = endpos
        if bufflen == 0:
            return YAPI.NO_MORE_DATA
        res = buff[0]
        return res

    async def readStr(self, nChars: int) -> str:
        """
        Reads data from the receive buffer as a string, starting at current stream position.
        If data at current stream position is not available anymore in the receive buffer, the
        function performs a short read.

        @param nChars : the maximum number of characters to read

        @return a string with receive buffer contents

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        mult: int
        endpos: int
        res: str
        if nChars > 65535:
            nChars = 65535

        buff = await self._download("rxdata.bin?pos=%d&len=%d" % (self._rxptr, nChars))
        bufflen = len(buff) - 1
        endpos = 0
        mult = 1
        while (bufflen > 0) and(buff[bufflen] != 64):
            endpos = endpos + mult * (buff[bufflen] - 48)
            mult = mult * 10
            bufflen = bufflen - 1
        self._rxptr = endpos
        res = (buff.decode('latin-1'))[0: 0 + bufflen]
        return res

    async def readBin(self, nChars: int) -> xarray:
        """
        Reads data from the receive buffer as a binary buffer, starting at current stream position.
        If data at current stream position is not available anymore in the receive buffer, the
        function performs a short read.

        @param nChars : the maximum number of bytes to read

        @return a binary object with receive buffer contents

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        mult: int
        endpos: int
        idx: int
        res: xarray
        if nChars > 65535:
            nChars = 65535

        buff = await self._download("rxdata.bin?pos=%d&len=%d" % (self._rxptr, nChars))
        bufflen = len(buff) - 1
        endpos = 0
        mult = 1
        while (bufflen > 0) and(buff[bufflen] != 64):
            endpos = endpos + mult * (buff[bufflen] - 48)
            mult = mult * 10
            bufflen = bufflen - 1
        self._rxptr = endpos
        res = xbytearray(bufflen)
        idx = 0
        while idx < bufflen:
            res[idx] = buff[idx]
            idx = idx + 1
        return res

    async def readArray(self, nChars: int) -> list[int]:
        """
        Reads data from the receive buffer as a list of bytes, starting at current stream position.
        If data at current stream position is not available anymore in the receive buffer, the
        function performs a short read.

        @param nChars : the maximum number of bytes to read

        @return a sequence of bytes with receive buffer contents

        On failure, throws an exception or returns an empty array.
        """
        buff: xarray
        bufflen: int
        mult: int
        endpos: int
        idx: int
        b: int
        res: list[int] = []
        if nChars > 65535:
            nChars = 65535

        buff = await self._download("rxdata.bin?pos=%d&len=%d" % (self._rxptr, nChars))
        bufflen = len(buff) - 1
        endpos = 0
        mult = 1
        while (bufflen > 0) and(buff[bufflen] != 64):
            endpos = endpos + mult * (buff[bufflen] - 48)
            mult = mult * 10
            bufflen = bufflen - 1
        self._rxptr = endpos
        del res[:]
        idx = 0
        while idx < bufflen:
            b = buff[idx]
            res.append(b)
            idx = idx + 1

        return res

    async def readHex(self, nBytes: int) -> str:
        """
        Reads data from the receive buffer as a hexadecimal string, starting at current stream position.
        If data at current stream position is not available anymore in the receive buffer, the
        function performs a short read.

        @param nBytes : the maximum number of bytes to read

        @return a string with receive buffer contents, encoded in hexadecimal

        On failure, throws an exception or returns a negative error code.
        """
        buff: xarray
        bufflen: int
        mult: int
        endpos: int
        ofs: int
        res: str
        if nBytes > 65535:
            nBytes = 65535

        buff = await self._download("rxdata.bin?pos=%d&len=%d" % (self._rxptr, nBytes))
        bufflen = len(buff) - 1
        endpos = 0
        mult = 1
        while (bufflen > 0) and(buff[bufflen] != 64):
            endpos = endpos + mult * (buff[bufflen] - 48)
            mult = mult * 10
            bufflen = bufflen - 1
        self._rxptr = endpos
        res = ""
        ofs = 0
        while ofs + 3 < bufflen:
            res = "%s%02X%02X%02X%02X" % (res, buff[ofs], buff[ofs + 1], buff[ofs + 2], buff[ofs + 3])
            ofs = ofs + 4
        while ofs < bufflen:
            res = "%s%02X" % (res, buff[ofs])
            ofs = ofs + 1
        return res

    async def querySdi12(self, sensorAddr: str, cmd: str, maxWait: int) -> str:
        """
        Sends a SDI-12 query to the bus, and reads the sensor immediate reply.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param sensorAddr : the sensor address, as a string
        @param cmd : the SDI12 query to send (without address and exclamation point)
        @param maxWait : the maximum timeout to wait for a reply from sensor, in millisecond

        @return the reply returned by the sensor, without newline, as a string.

        On failure, throws an exception or returns an empty string.
        """
        fullCmd: str
        cmdChar: str
        pattern: str
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        res: str
        cmdChar  = ""

        pattern = sensorAddr
        if len(cmd) > 0:
            cmdChar = cmd[0: 0 + 1]
        if sensorAddr == "?":
            pattern = ".*"
        else:
            if cmdChar == "M" or cmdChar == "D":
                pattern = "%s:.*" % sensorAddr
            else:
                pattern = "%s.*" % sensorAddr
        pattern = self._escapeAttr(pattern)
        fullCmd = self._escapeAttr("+%s%s!" % (sensorAddr, cmd))
        url = "rxmsg.json?len=1&maxw=%d&cmd=%s&pat=%s" % (maxWait, fullCmd, pattern)

        msgbin = await self._download(url)
        if len(msgbin)<2:
            return ""
        msgarr = self._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return ""
        # last element of array is the new position
        msglen = msglen - 1
        self._rxptr = self._decode_json_int(msgarr[msglen])
        if msglen == 0:
            return ""
        res = self._json_get_string(msgarr[0])
        return res

    async def discoverSingleSensor(self) -> YSdi12SensorInfo:
        """
        Sends a discovery command to the bus, and reads the sensor information reply.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.
        This function work when only one sensor is connected.

        @return the reply returned by the sensor, as a YSdi12SensorInfo object.

        On failure, throws an exception or returns an empty string.
        """
        resStr: str

        resStr = await self.querySdi12("?", "", 5000)
        if resStr == "":
            return YSdi12SensorInfo(self, "ERSensor Not Found")

        return await self.getSensorInformation(resStr)

    async def discoverAllSensors(self) -> list[YSdi12SensorInfo]:
        """
        Sends a discovery command to the bus, and reads all sensors information reply.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @return all the information from every connected sensor, as an array of YSdi12SensorInfo object.

        On failure, throws an exception or returns an empty string.
        """
        sensors: Union[list[YSdi12SensorInfo], None] = []
        idSens: list[str] = []
        res: str
        i: int
        lettreMin: str
        lettreMaj: str

        # 1. Search for sensors present
        del idSens[:]
        i = 0
        while i < 10:
            res = await self.querySdi12(str(i), "!", 500)
            if len(res) >= 1:
                idSens.append(res)
            i = i+1
        lettreMin = "abcdefghijklmnopqrstuvwxyz"
        lettreMaj = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        i = 0
        while i<26:
            res = await self.querySdi12(lettreMin[i: i + 1], "!", 500)
            if len(res) >= 1:
                idSens.append(res)
            i = i +1
        while i<26:
            res = await self.querySdi12(lettreMaj[i: i + 1], "!", 500)
            if len(res) >= 1:
                idSens.append(res)
            i = i +1

        # 2. Query existing sensors information
        i = 0
        del sensors[:]
        while i < len(idSens):
            sensors.append(await self.getSensorInformation(idSens[i]))
            i = i + 1

        return sensors

    async def readSensor(self, sensorAddr: str, measCmd: str, maxWait: int) -> list[float]:
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
        resStr: str
        res: list[float] = []
        tab: list[str] = []
        split: list[str] = []
        i: int
        valdouble: float

        resStr = await self.querySdi12(sensorAddr, measCmd, maxWait)
        tab = (resStr).split(',')
        split = (tab[0]).split(':')
        if len(split) < 2:
            return res

        valdouble = YAPI._atof(split[1])
        res.append(valdouble)
        i = 1
        while i < len(tab):
            valdouble = YAPI._atof(tab[i])
            res.append(valdouble)
            i = i + 1

        return res

    async def changeAddress(self, oldAddress: str, newAddress: str) -> YSdi12SensorInfo:
        """
        Changes the address of the selected sensor, and returns the sensor information with the new address.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param oldAddress : Actual sensor address, as a string
        @param newAddress : New sensor address, as a string

        @return the sensor address and information , as a YSdi12SensorInfo object.

        On failure, throws an exception or returns an empty string.
        """
        addr: Union[YSdi12SensorInfo, None]

        await self.querySdi12(oldAddress, "A" + newAddress, 1000)
        addr = await self.getSensorInformation(newAddress)
        return addr

    async def getSensorInformation(self, sensorAddr: str) -> YSdi12SensorInfo:
        """
        Sends a information command to the bus, and reads sensors information selected.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param sensorAddr : Sensor address, as a string

        @return the reply returned by the sensor, as a YSdi12Port object.

        On failure, throws an exception or returns an empty string.
        """
        res: str
        sensor: Union[YSdi12SensorInfo, None]

        res = await self.querySdi12(sensorAddr, "I", 1000)
        if res == "":
            return YSdi12SensorInfo(self, "ERSensor Not Found")
        sensor = YSdi12SensorInfo(self, res)
        await sensor._queryValueInfo()
        return sensor

    async def readConcurrentMeasurements(self, sensorAddr: str) -> list[float]:
        """
        Sends a information command to the bus, and reads sensors information selected.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param sensorAddr : Sensor address, as a string

        @return the reply returned by the sensor, as a YSdi12Port object.

        On failure, throws an exception or returns an empty string.
        """
        res: list[float] = []

        res= await self.readSensor(sensorAddr, "D", 1000)
        return res

    async def requestConcurrentMeasurements(self, sensorAddr: str) -> int:
        """
        Sends a information command to the bus, and reads sensors information selected.
        This function is intended to be used when the serial port is configured for 'SDI-12' protocol.

        @param sensorAddr : Sensor address, as a string

        @return the reply returned by the sensor, as a YSdi12Port object.

        On failure, throws an exception or returns an empty string.
        """
        timewait: int
        wait: str

        wait = await self.querySdi12(sensorAddr, "C", 1000)
        wait = wait[1: 1 + 3]
        timewait = YAPI._atoi(wait) * 1000
        return timewait

    async def snoopMessagesEx(self, maxWait: int, maxMsg: int) -> list[YSdi12SnoopingRecord]:
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
        url: str
        msgbin: xarray
        msgarr: list[xarray] = []
        msglen: int
        res: Union[list[YSdi12SnoopingRecord], None] = []
        idx: int

        url = "rxmsg.json?pos=%d&maxw=%d&t=0&len=%d" % (self._rxptr, maxWait, maxMsg)
        msgbin = await self._download(url)
        msgarr = self._json_get_array(msgbin)
        msglen = len(msgarr)
        if msglen == 0:
            return res
        # last element of array is the new position
        msglen = msglen - 1
        self._rxptr = self._decode_json_int(msgarr[msglen])
        idx = 0

        while idx < msglen:
            res.append(YSdi12SnoopingRecord(msgarr[idx].decode('latin-1')))
            idx = idx + 1

        return res

    async def snoopMessages(self, maxWait: int) -> list[YSdi12SnoopingRecord]:
        """
        Retrieves messages (both direction) in the SDI12 port buffer, starting at current position.

        If no message is found, the search waits for one up to the specified maximum timeout
        (in milliseconds).

        @param maxWait : the maximum number of milliseconds to wait for a message if none is found
                in the receive buffer.

        @return an array of YSdi12SnoopingRecord objects containing the messages found, if any.

        On failure, throws an exception or returns an empty array.
        """
        return await self.snoopMessagesEx(maxWait, 255)

    # --- (end of generated code: YSdi12Port implementation)
