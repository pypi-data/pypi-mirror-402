# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_cellular_aio.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YCellular API for Cellular functions
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
Yoctopuce library: Asyncio implementation of YCellular
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YCellular YCellRecord
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
    YAPIContext, YAPI, YAPI_Exception, YFunction, HwId, hwid2str, YModule
)

# --- (generated code: YCellRecord class start)
# noinspection PyProtectedMember
class YCellRecord:
    """
    YCellRecord objects are used to describe a wireless network.
    These objects are used in particular in conjunction with the
    YCellular class.

    """
    # --- (end of generated code: YCellRecord class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YCellRecord return codes)
        pass
        # --- (end of generated code: YCellRecord return codes)
        pass

    # --- (generated code: YCellRecord attributes declaration)
    _oper: str
    _mcc: int
    _mnc: int
    _lac: int
    _cid: int
    _dbm: int
    _tad: int
    # --- (end of generated code: YCellRecord attributes declaration)

    def __init__(self, mcc: int, mnc: int, lac: int, cellId: int, dbm: int, tad: int, oper: str):
        # --- (generated code: YCellRecord constructor)
        self._oper = ''
        self._mcc = 0
        self._mnc = 0
        self._lac = 0
        self._cid = 0
        self._dbm = 0
        self._tad = 0
        # --- (end of generated code: YCellRecord constructor)
        self._oper = oper
        self._mcc = mcc
        self._mnc = mnc
        self._lac = lac
        self._cid = cellId
        self._dbm = dbm
        self._tad = tad

    # --- (generated code: YCellRecord implementation)
    def get_cellOperator(self) -> str:
        """
        Returns the name of the the cell operator, as received from the network.

        @return a string with the name of the the cell operator.
        """
        return self._oper

    def get_mobileCountryCode(self) -> int:
        """
        Returns the Mobile Country Code (MCC). The MCC is a unique identifier for each country.

        @return an integer corresponding to the Mobile Country Code (MCC).
        """
        return self._mcc

    def get_mobileNetworkCode(self) -> int:
        """
        Returns the Mobile Network Code (MNC). The MNC is a unique identifier for each phone
        operator within a country.

        @return an integer corresponding to the Mobile Network Code (MNC).
        """
        return self._mnc

    def get_locationAreaCode(self) -> int:
        """
        Returns the Location Area Code (LAC). The LAC is a unique identifier for each
        place within a country.

        @return an integer corresponding to the Location Area Code (LAC).
        """
        return self._lac

    def get_cellId(self) -> int:
        """
        Returns the Cell ID. The Cell ID is a unique identifier for each
        base transmission station within a LAC.

        @return an integer corresponding to the Cell Id.
        """
        return self._cid

    def get_signalStrength(self) -> int:
        """
        Returns the signal strength, measured in dBm.

        @return an integer corresponding to the signal strength.
        """
        return self._dbm

    def get_timingAdvance(self) -> int:
        """
        Returns the Timing Advance (TA). The TA corresponds to the time necessary
        for the signal to reach the base station from the device.
        Each increment corresponds about to 550m of distance.

        @return an integer corresponding to the Timing Advance (TA).
        """
        return self._tad

    # --- (end of generated code: YCellRecord implementation)


# --- (generated code: YCellular class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YCellularValueCallback = Union[Callable[['YCellular', str], Any], None]
    except TypeError:
        YCellularValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YCellular(YFunction):
    """
    The YCellular class provides control over cellular network parameters
    and status for devices that are GSM-enabled.
    Note that TCP/IP parameters are configured separately, using class YNetwork.

    """
    # --- (end of generated code: YCellular class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YCellular return codes)
        LINKQUALITY_INVALID: Final[int] = YAPI.INVALID_UINT
        CELLOPERATOR_INVALID: Final[str] = YAPI.INVALID_STRING
        CELLIDENTIFIER_INVALID: Final[str] = YAPI.INVALID_STRING
        IMSI_INVALID: Final[str] = YAPI.INVALID_STRING
        MESSAGE_INVALID: Final[str] = YAPI.INVALID_STRING
        PIN_INVALID: Final[str] = YAPI.INVALID_STRING
        RADIOCONFIG_INVALID: Final[str] = YAPI.INVALID_STRING
        LOCKEDOPERATOR_INVALID: Final[str] = YAPI.INVALID_STRING
        APN_INVALID: Final[str] = YAPI.INVALID_STRING
        APNSECRET_INVALID: Final[str] = YAPI.INVALID_STRING
        PINGINTERVAL_INVALID: Final[int] = YAPI.INVALID_UINT
        DATASENT_INVALID: Final[int] = YAPI.INVALID_UINT
        DATARECEIVED_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        CELLTYPE_GPRS: Final[int] = 0
        CELLTYPE_EGPRS: Final[int] = 1
        CELLTYPE_WCDMA: Final[int] = 2
        CELLTYPE_HSDPA: Final[int] = 3
        CELLTYPE_NONE: Final[int] = 4
        CELLTYPE_CDMA: Final[int] = 5
        CELLTYPE_LTE_M: Final[int] = 6
        CELLTYPE_NB_IOT: Final[int] = 7
        CELLTYPE_EC_GSM_IOT: Final[int] = 8
        CELLTYPE_INVALID: Final[int] = -1
        AIRPLANEMODE_OFF: Final[int] = 0
        AIRPLANEMODE_ON: Final[int] = 1
        AIRPLANEMODE_INVALID: Final[int] = -1
        ENABLEDATA_HOMENETWORK: Final[int] = 0
        ENABLEDATA_ROAMING: Final[int] = 1
        ENABLEDATA_NEVER: Final[int] = 2
        ENABLEDATA_NEUTRALITY: Final[int] = 3
        ENABLEDATA_INVALID: Final[int] = -1
        # --- (end of generated code: YCellular return codes)

    # --- (generated code: YCellular attributes declaration)
    _valueCallback: YCellularValueCallback
    # --- (end of generated code: YCellular attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Cellular', func)
        # --- (generated code: YCellular constructor)
        # --- (end of generated code: YCellular constructor)

    # --- (generated code: YCellular implementation)
    @classmethod
    def FindCellular(cls, func: str) -> YCellular:
        """
        Retrieves a cellular interface for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the cellular interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YCellular.isOnline() to test if the cellular interface is
        indeed online at a given time. In case of ambiguity when looking for
        a cellular interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the cellular interface, for instance
                YHUBGSM1.cellular.

        @return a YCellular object allowing you to drive the cellular interface.
        """
        return cls.FindCellularInContext(YAPI, func)

    @classmethod
    def FindCellularInContext(cls, yctx: YAPIContext, func: str) -> YCellular:
        """
        Retrieves a cellular interface for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the cellular interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YCellular.isOnline() to test if the cellular interface is
        indeed online at a given time. In case of ambiguity when looking for
        a cellular interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the cellular interface, for instance
                YHUBGSM1.cellular.

        @return a YCellular object allowing you to drive the cellular interface.
        """
        obj: Union[YCellular, None] = yctx._findInCache('Cellular', func)
        if obj:
            return obj
        return YCellular(yctx, func)

    @classmethod
    def FirstCellular(cls) -> Union[YCellular, None]:
        """
        Starts the enumeration of cellular interfaces currently accessible.
        Use the method YCellular.nextCellular() to iterate on
        next cellular interfaces.

        @return a pointer to a YCellular object, corresponding to
                the first cellular interface currently online, or a None pointer
                if there are none.
        """
        return cls.FirstCellularInContext(YAPI)

    @classmethod
    def FirstCellularInContext(cls, yctx: YAPIContext) -> Union[YCellular, None]:
        """
        Starts the enumeration of cellular interfaces currently accessible.
        Use the method YCellular.nextCellular() to iterate on
        next cellular interfaces.

        @param yctx : a YAPI context.

        @return a pointer to a YCellular object, corresponding to
                the first cellular interface currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Cellular')
        if hwid:
            return cls.FindCellularInContext(yctx, hwid2str(hwid))
        return None

    def nextCellular(self) -> Union[YCellular, None]:
        """
        Continues the enumeration of cellular interfaces started using yFirstCellular().
        Caution: You can't make any assumption about the returned cellular interfaces order.
        If you want to find a specific a cellular interface, use Cellular.findCellular()
        and a hardwareID or a logical name.

        @return a pointer to a YCellular object, corresponding to
                a cellular interface currently online, or a None pointer
                if there are no more cellular interfaces to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Cellular', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindCellularInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_linkQuality(self) -> int:
        """
        Returns the link quality, expressed in percent.

        @return an integer corresponding to the link quality, expressed in percent

        On failure, throws an exception or returns YCellular.LINKQUALITY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("linkQuality")
        if json_val is None:
            return YCellular.LINKQUALITY_INVALID
        return json_val

    async def get_cellOperator(self) -> str:
        """
        Returns the name of the cell operator currently in use.

        @return a string corresponding to the name of the cell operator currently in use

        On failure, throws an exception or returns YCellular.CELLOPERATOR_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("cellOperator")
        if json_val is None:
            return YCellular.CELLOPERATOR_INVALID
        return json_val

    async def get_cellIdentifier(self) -> str:
        """
        Returns the unique identifier of the cellular antenna in use: MCC, MNC, LAC and Cell ID.

        @return a string corresponding to the unique identifier of the cellular antenna in use: MCC, MNC,
        LAC and Cell ID

        On failure, throws an exception or returns YCellular.CELLIDENTIFIER_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("cellIdentifier")
        if json_val is None:
            return YCellular.CELLIDENTIFIER_INVALID
        return json_val

    async def get_cellType(self) -> int:
        """
        Active cellular connection type.

        @return a value among YCellular.CELLTYPE_GPRS, YCellular.CELLTYPE_EGPRS, YCellular.CELLTYPE_WCDMA,
        YCellular.CELLTYPE_HSDPA, YCellular.CELLTYPE_NONE, YCellular.CELLTYPE_CDMA,
        YCellular.CELLTYPE_LTE_M, YCellular.CELLTYPE_NB_IOT and YCellular.CELLTYPE_EC_GSM_IOT

        On failure, throws an exception or returns YCellular.CELLTYPE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("cellType")
        if json_val is None:
            return YCellular.CELLTYPE_INVALID
        return json_val

    async def get_imsi(self) -> str:
        """
        Returns the International Mobile Subscriber Identity (MSI) that uniquely identifies
        the SIM card. The first 3 digits represent the mobile country code (MCC), which
        is followed by the mobile network code (MNC), either 2-digit (European standard)
        or 3-digit (North American standard)

        @return a string corresponding to the International Mobile Subscriber Identity (MSI) that uniquely identifies
                the SIM card

        On failure, throws an exception or returns YCellular.IMSI_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("imsi")
        if json_val is None:
            return YCellular.IMSI_INVALID
        return json_val

    async def get_message(self) -> str:
        """
        Returns the latest status message from the wireless interface.

        @return a string corresponding to the latest status message from the wireless interface

        On failure, throws an exception or returns YCellular.MESSAGE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("message")
        if json_val is None:
            return YCellular.MESSAGE_INVALID
        return json_val

    async def get_pin(self) -> str:
        """
        Returns an opaque string if a PIN code has been configured in the device to access
        the SIM card, or an empty string if none has been configured or if the code provided
        was rejected by the SIM card.

        @return a string corresponding to an opaque string if a PIN code has been configured in the device to access
                the SIM card, or an empty string if none has been configured or if the code provided
                was rejected by the SIM card

        On failure, throws an exception or returns YCellular.PIN_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("pin")
        if json_val is None:
            return YCellular.PIN_INVALID
        return json_val

    async def set_pin(self, newval: str) -> int:
        """
        Changes the PIN code used by the module to access the SIM card.
        This function does not change the code on the SIM card itself, but only changes
        the parameter used by the device to try to get access to it. If the SIM code
        does not work immediately on first try, it will be automatically forgotten
        and the message will be set to "Enter SIM PIN". The method should then be
        invoked again with right correct PIN code. After three failed attempts in a row,
        the message is changed to "Enter SIM PUK" and the SIM card PUK code must be
        provided using method sendPUK.

        Remember to call the saveToFlash() method of the module to save the
        new value in the device flash.

        @param newval : a string corresponding to the PIN code used by the module to access the SIM card

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("pin", rest_val)

    async def get_radioConfig(self) -> str:
        """
        Returns the type of protocol used over the serial line, as a string.
        Possible values are "Line" for ASCII messages separated by CR and/or LF,
        "Frame:[timeout]ms" for binary messages separated by a delay time,
        "Char" for a continuous ASCII stream or
        "Byte" for a continuous binary stream.

        @return a string corresponding to the type of protocol used over the serial line, as a string

        On failure, throws an exception or returns YCellular.RADIOCONFIG_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("radioConfig")
        if json_val is None:
            return YCellular.RADIOCONFIG_INVALID
        return json_val

    async def set_radioConfig(self, newval: str) -> int:
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
        return await self._setAttr("radioConfig", rest_val)

    async def get_lockedOperator(self) -> str:
        """
        Returns the name of the only cell operator to use if automatic choice is disabled,
        or an empty string if the SIM card will automatically choose among available
        cell operators.

        @return a string corresponding to the name of the only cell operator to use if automatic choice is disabled,
                or an empty string if the SIM card will automatically choose among available
                cell operators

        On failure, throws an exception or returns YCellular.LOCKEDOPERATOR_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("lockedOperator")
        if json_val is None:
            return YCellular.LOCKEDOPERATOR_INVALID
        return json_val

    async def set_lockedOperator(self, newval: str) -> int:
        """
        Changes the name of the cell operator to be used. If the name is an empty
        string, the choice will be made automatically based on the SIM card. Otherwise,
        the selected operator is the only one that will be used.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a string corresponding to the name of the cell operator to be used

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("lockedOperator", rest_val)

    async def get_airplaneMode(self) -> int:
        """
        Returns true if the airplane mode is active (radio turned off).

        @return either YCellular.AIRPLANEMODE_OFF or YCellular.AIRPLANEMODE_ON, according to true if the
        airplane mode is active (radio turned off)

        On failure, throws an exception or returns YCellular.AIRPLANEMODE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("airplaneMode")
        if json_val is None:
            return YCellular.AIRPLANEMODE_INVALID
        return json_val

    async def set_airplaneMode(self, newval: int) -> int:
        """
        Changes the activation state of airplane mode (radio turned off).

        @param newval : either YCellular.AIRPLANEMODE_OFF or YCellular.AIRPLANEMODE_ON, according to the
        activation state of airplane mode (radio turned off)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("airplaneMode", rest_val)

    async def get_enableData(self) -> int:
        """
        Returns the condition for enabling IP data services (GPRS).
        When data services are disabled, SMS are the only mean of communication.

        @return a value among YCellular.ENABLEDATA_HOMENETWORK, YCellular.ENABLEDATA_ROAMING,
        YCellular.ENABLEDATA_NEVER and YCellular.ENABLEDATA_NEUTRALITY corresponding to the condition for
        enabling IP data services (GPRS)

        On failure, throws an exception or returns YCellular.ENABLEDATA_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("enableData")
        if json_val is None:
            return YCellular.ENABLEDATA_INVALID
        return json_val

    async def set_enableData(self, newval: int) -> int:
        """
        Changes the condition for enabling IP data services (GPRS).
        The service can be either fully deactivated, or limited to the SIM home network,
        or enabled for all partner networks (roaming). Caution: enabling data services
        on roaming networks may cause prohibitive communication costs !

        When data services are disabled, SMS are the only mean of communication.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a value among YCellular.ENABLEDATA_HOMENETWORK, YCellular.ENABLEDATA_ROAMING,
        YCellular.ENABLEDATA_NEVER and YCellular.ENABLEDATA_NEUTRALITY corresponding to the condition for
        enabling IP data services (GPRS)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("enableData", rest_val)

    async def get_apn(self) -> str:
        """
        Returns the Access Point Name (APN) to be used, if needed.
        When left blank, the APN suggested by the cell operator will be used.

        @return a string corresponding to the Access Point Name (APN) to be used, if needed

        On failure, throws an exception or returns YCellular.APN_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("apn")
        if json_val is None:
            return YCellular.APN_INVALID
        return json_val

    async def set_apn(self, newval: str) -> int:
        """
        Returns the Access Point Name (APN) to be used, if needed.
        When left blank, the APN suggested by the cell operator will be used.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a string

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("apn", rest_val)

    async def get_apnSecret(self) -> str:
        """
        Returns an opaque string if APN authentication parameters have been configured
        in the device, or an empty string otherwise.
        To configure these parameters, use set_apnAuth().

        @return a string corresponding to an opaque string if APN authentication parameters have been configured
                in the device, or an empty string otherwise

        On failure, throws an exception or returns YCellular.APNSECRET_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("apnSecret")
        if json_val is None:
            return YCellular.APNSECRET_INVALID
        return json_val

    async def set_apnSecret(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("apnSecret", rest_val)

    async def get_pingInterval(self) -> int:
        """
        Returns the automated connectivity check interval, in seconds.

        @return an integer corresponding to the automated connectivity check interval, in seconds

        On failure, throws an exception or returns YCellular.PINGINTERVAL_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pingInterval")
        if json_val is None:
            return YCellular.PINGINTERVAL_INVALID
        return json_val

    async def set_pingInterval(self, newval: int) -> int:
        """
        Changes the automated connectivity check interval, in seconds.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the automated connectivity check interval, in seconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("pingInterval", rest_val)

    async def get_dataSent(self) -> int:
        """
        Returns the number of bytes sent so far.

        @return an integer corresponding to the number of bytes sent so far

        On failure, throws an exception or returns YCellular.DATASENT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("dataSent")
        if json_val is None:
            return YCellular.DATASENT_INVALID
        return json_val

    async def set_dataSent(self, newval: int) -> int:
        """
        Changes the value of the outgoing data counter.

        @param newval : an integer corresponding to the value of the outgoing data counter

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("dataSent", rest_val)

    async def get_dataReceived(self) -> int:
        """
        Returns the number of bytes received so far.

        @return an integer corresponding to the number of bytes received so far

        On failure, throws an exception or returns YCellular.DATARECEIVED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("dataReceived")
        if json_val is None:
            return YCellular.DATARECEIVED_INVALID
        return json_val

    async def set_dataReceived(self, newval: int) -> int:
        """
        Changes the value of the incoming data counter.

        @param newval : an integer corresponding to the value of the incoming data counter

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("dataReceived", rest_val)

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YCellular.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YCellularValueCallback) -> int:
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

    async def sendPUK(self, puk: str, newPin: str) -> int:
        """
        Sends a PUK code to unlock the SIM card after three failed PIN code attempts, and
        set up a new PIN into the SIM card. Only ten consecutive tentatives are permitted:
        after that, the SIM card will be blocked permanently without any mean of recovery
        to use it again. Note that after calling this method, you have usually to invoke
        method set_pin() to tell the YoctoHub which PIN to use in the future.

        @param puk : the SIM PUK code
        @param newPin : new PIN code to configure into the SIM card

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        gsmMsg: str
        gsmMsg = await self.get_message()
        if not (gsmMsg[0: 0 + 13] == "Enter SIM PUK"):
            self._throw(YAPI.INVALID_ARGUMENT, "PUK not expected at this time")
            return YAPI.INVALID_ARGUMENT
        if newPin == "":
            return await self.set_command("AT+CPIN=%s,0000;+CLCK=SC,0,0000" % puk)
        return await self.set_command("AT+CPIN=%s,%s" % (puk, newPin))

    async def set_apnAuth(self, username: str, password: str) -> int:
        """
        Configure authentication parameters to connect to the APN. Both
        PAP and CHAP authentication are supported.

        @param username : APN username
        @param password : APN password

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_apnSecret("%s,%s" % (username, password))

    async def clearDataCounters(self) -> int:
        """
        Clear the transmitted data counters.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        retcode: int

        retcode = await self.set_dataReceived(0)
        if retcode != YAPI.SUCCESS:
            return retcode
        retcode = await self.set_dataSent(0)
        return retcode

    async def _AT(self, cmd: str) -> str:
        """
        Sends an AT command to the GSM module and returns the command output.
        The command will only execute when the GSM module is in standard
        command state, and should leave it in the exact same state.
        Use this function with great care !

        @param cmd : the AT command to execute, like for instance: "+CCLK?".

        @return a string with the result of the commands. Empty lines are
                automatically removed from the output.
        """
        chrPos: int
        cmdLen: int
        waitMore: int
        res: str
        buff: xarray
        bufflen: int
        buffstr: str
        buffstrlen: int
        idx: int
        suffixlen: int
        # quote dangerous characters used in AT commands
        cmdLen = len(cmd)
        chrPos = cmd.find("#")
        while chrPos >= 0:
            cmd = "%s%c23%s" % (cmd[0: 0 + chrPos], 37, cmd[chrPos+1: chrPos+1 + cmdLen-chrPos-1])
            cmdLen = cmdLen + 2
            chrPos = cmd.find("#")
        chrPos = cmd.find("+")
        while chrPos >= 0:
            cmd = "%s%c2B%s" % (cmd[0: 0 + chrPos], 37, cmd[chrPos+1: chrPos+1 + cmdLen-chrPos-1])
            cmdLen = cmdLen + 2
            chrPos = cmd.find("+")
        chrPos = cmd.find("=")
        while chrPos >= 0:
            cmd = "%s%c3D%s" % (cmd[0: 0 + chrPos], 37, cmd[chrPos+1: chrPos+1 + cmdLen-chrPos-1])
            cmdLen = cmdLen + 2
            chrPos = cmd.find("=")
        cmd = "at.txt?cmd=%s" % cmd
        res = ""
        # max 2 minutes (each iteration may take up to 5 seconds if waiting)
        waitMore = 24
        while waitMore > 0:
            buff = await self._download(cmd)
            bufflen = len(buff)
            buffstr = buff.decode('latin-1')
            buffstrlen = len(buffstr)
            idx = bufflen - 1
            while (idx > 0) and(buff[idx] != 64) and(buff[idx] != 10) and(buff[idx] != 13):
                idx = idx - 1
            if buff[idx] == 64:
                # continuation detected
                suffixlen = bufflen - idx
                cmd = "at.txt?cmd=%s" % (buffstr[buffstrlen - suffixlen: buffstrlen - suffixlen + suffixlen])
                buffstr = buffstr[0: 0 + buffstrlen - suffixlen]
                waitMore = waitMore - 1
            else:
                # request complete
                waitMore = 0
            res = "%s%s" % (res, buffstr)
        return res

    async def get_availableOperators(self) -> list[str]:
        """
        Returns the list detected cell operators in the neighborhood.
        This function will typically take between 30 seconds to 1 minute to
        return. Note that any SIM card can usually only connect to specific
        operators. All networks returned by this function might therefore
        not be available for connection.

        @return a list of string (cell operator names).
        """
        cops: str
        idx: int
        slen: int
        res: list[str] = []

        cops = await self._AT("+COPS=?")
        slen = len(cops)
        del res[:]
        idx = cops.find("(")
        while idx >= 0:
            slen = slen - (idx+1)
            cops = cops[idx+1: idx+1 + slen]
            idx = cops.find("\"")
            if idx > 0:
                slen = slen - (idx+1)
                cops = cops[idx+1: idx+1 + slen]
                idx = cops.find("\"")
                if idx > 0:
                    res.append(cops[0: 0 + idx])
            idx = cops.find("(")

        return res

    async def quickCellSurvey(self) -> list[YCellRecord]:
        """
        Returns a list of nearby cellular antennas, as required for quick
        geolocation of the device. The first cell listed is the serving
        cell, and the next ones are the neighbor cells reported by the
        serving cell.

        @return a list of YCellRecords.
        """
        moni: str
        recs: list[str] = []
        llen: int
        mccs: str
        mcc: int
        mncs: str
        mnc: int
        lac: int
        cellId: int
        dbms: str
        dbm: int
        tads: str
        tad: int
        oper: str
        res: Union[list[YCellRecord], None] = []

        moni = await self._AT("+CCED=0;#MONI=7;#MONI")
        mccs = moni[7: 7 + 3]
        if mccs[0: 0 + 1] == "0":
            mccs = mccs[1: 1 + 2]
        if mccs[0: 0 + 1] == "0":
            mccs = mccs[1: 1 + 1]
        mcc = YAPI._atoi(mccs)
        mncs = moni[11: 11 + 3]
        if mncs[2: 2 + 1] == ",":
            mncs = mncs[0: 0 + 2]
        if mncs[0: 0 + 1] == "0":
            mncs = mncs[1: 1 + len(mncs)-1]
        mnc = YAPI._atoi(mncs)
        recs = (moni).split('#')
        # process each line in turn
        del res[:]
        for ii_0 in recs:
            llen = len(ii_0) - 2
            if llen >= 44:
                if ii_0[41: 41 + 3] == "dbm":
                    lac = int(ii_0[16: 16 + 4], 16)
                    cellId = int(ii_0[23: 23 + 4], 16)
                    dbms = ii_0[37: 37 + 4]
                    if dbms[0: 0 + 1] == " ":
                        dbms = dbms[1: 1 + 3]
                    dbm = YAPI._atoi(dbms)
                    if llen > 66:
                        tads = ii_0[54: 54 + 2]
                        if tads[0: 0 + 1] == " ":
                            tads = tads[1: 1 + 3]
                        tad = YAPI._atoi(tads)
                        oper = ii_0[66: 66 + llen-66]
                    else:
                        tad = -1
                        oper = ""
                    if lac < 65535:
                        res.append(YCellRecord(mcc, mnc, lac, cellId, dbm, tad, oper))
        return res

    async def decodePLMN(self, mccmnc: str) -> str:
        """
        Returns the cell operator brand for a given MCC/MNC pair (DEPRECATED).

        @param mccmnc : a string starting with a MCC code followed by a MNC code,

        @return a string containing the corresponding cell operator brand name.
        """
        return mccmnc

    async def get_communicationProfiles(self) -> list[str]:
        """
        Returns the list available radio communication profiles, as a string array
        (YoctoHub-GSM-4G only).
        Each string is a made of a numerical ID, followed by a colon,
        followed by the profile description.

        @return a list of string describing available radio communication profiles.
        """
        profiles: str
        lines: list[str] = []
        nlines: int
        idx: int
        line: str
        cpos: int
        profno: int
        res: list[str] = []

        profiles = await self._AT("+UMNOPROF=?")
        lines = (profiles).split('\n')
        nlines = len(lines)
        if not (nlines > 0):
            self._throw(YAPI.IO_ERROR, "fail to retrieve profile list")
            return res
        del res[:]
        idx = 0
        while idx < nlines:
            line = lines[idx]
            cpos = line.find(":")
            if cpos > 0:
                profno = YAPI._atoi(line[0: 0 + cpos])
                if profno > 1:
                    res.append(line)
            idx = idx + 1

        return res

    # --- (end of generated code: YCellular implementation)
