# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_cellular.py 69442 2025-10-16 08:53:14Z mvuilleu $
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
Yoctopuce library: High-level API for YCellular
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_cellular_aio
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
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True  # noqa
    _DYNAMIC_HELPERS: Final[bool] = True  # noqa

from .yocto_cellular_aio import (
    YCellular as YCellular_aio,
    YCellRecord
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

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
    _aio: YCellular_aio
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
        return cls._proxy(cls, YCellular_aio.FindCellularInContext(YAPI_aio, func))

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
        return cls._proxy(cls, YCellular_aio.FindCellularInContext(yctx._aio, func))

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
        return cls._proxy(cls, YCellular_aio.FirstCellularInContext(YAPI_aio))

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
        return cls._proxy(cls, YCellular_aio.FirstCellularInContext(yctx._aio))

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
        return self._proxy(type(self), self._aio.nextCellular())

    if not _DYNAMIC_HELPERS:
        def get_linkQuality(self) -> int:
            """
            Returns the link quality, expressed in percent.

            @return an integer corresponding to the link quality, expressed in percent

            On failure, throws an exception or returns YCellular.LINKQUALITY_INVALID.
            """
            return self._run(self._aio.get_linkQuality())

    if not _DYNAMIC_HELPERS:
        def get_cellOperator(self) -> str:
            """
            Returns the name of the cell operator currently in use.

            @return a string corresponding to the name of the cell operator currently in use

            On failure, throws an exception or returns YCellular.CELLOPERATOR_INVALID.
            """
            return self._run(self._aio.get_cellOperator())

    if not _DYNAMIC_HELPERS:
        def get_cellIdentifier(self) -> str:
            """
            Returns the unique identifier of the cellular antenna in use: MCC, MNC, LAC and Cell ID.

            @return a string corresponding to the unique identifier of the cellular antenna in use: MCC, MNC,
            LAC and Cell ID

            On failure, throws an exception or returns YCellular.CELLIDENTIFIER_INVALID.
            """
            return self._run(self._aio.get_cellIdentifier())

    if not _DYNAMIC_HELPERS:
        def get_cellType(self) -> int:
            """
            Active cellular connection type.

            @return a value among YCellular.CELLTYPE_GPRS, YCellular.CELLTYPE_EGPRS, YCellular.CELLTYPE_WCDMA,
            YCellular.CELLTYPE_HSDPA, YCellular.CELLTYPE_NONE, YCellular.CELLTYPE_CDMA,
            YCellular.CELLTYPE_LTE_M, YCellular.CELLTYPE_NB_IOT and YCellular.CELLTYPE_EC_GSM_IOT

            On failure, throws an exception or returns YCellular.CELLTYPE_INVALID.
            """
            return self._run(self._aio.get_cellType())

    if not _DYNAMIC_HELPERS:
        def get_imsi(self) -> str:
            """
            Returns the International Mobile Subscriber Identity (MSI) that uniquely identifies
            the SIM card. The first 3 digits represent the mobile country code (MCC), which
            is followed by the mobile network code (MNC), either 2-digit (European standard)
            or 3-digit (North American standard)

            @return a string corresponding to the International Mobile Subscriber Identity (MSI) that uniquely identifies
                    the SIM card

            On failure, throws an exception or returns YCellular.IMSI_INVALID.
            """
            return self._run(self._aio.get_imsi())

    if not _DYNAMIC_HELPERS:
        def get_message(self) -> str:
            """
            Returns the latest status message from the wireless interface.

            @return a string corresponding to the latest status message from the wireless interface

            On failure, throws an exception or returns YCellular.MESSAGE_INVALID.
            """
            return self._run(self._aio.get_message())

    if not _DYNAMIC_HELPERS:
        def get_pin(self) -> str:
            """
            Returns an opaque string if a PIN code has been configured in the device to access
            the SIM card, or an empty string if none has been configured or if the code provided
            was rejected by the SIM card.

            @return a string corresponding to an opaque string if a PIN code has been configured in the device to access
                    the SIM card, or an empty string if none has been configured or if the code provided
                    was rejected by the SIM card

            On failure, throws an exception or returns YCellular.PIN_INVALID.
            """
            return self._run(self._aio.get_pin())

    if not _DYNAMIC_HELPERS:
        def set_pin(self, newval: str) -> int:
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
            return self._run(self._aio.set_pin(newval))

    if not _DYNAMIC_HELPERS:
        def get_radioConfig(self) -> str:
            """
            Returns the type of protocol used over the serial line, as a string.
            Possible values are "Line" for ASCII messages separated by CR and/or LF,
            "Frame:[timeout]ms" for binary messages separated by a delay time,
            "Char" for a continuous ASCII stream or
            "Byte" for a continuous binary stream.

            @return a string corresponding to the type of protocol used over the serial line, as a string

            On failure, throws an exception or returns YCellular.RADIOCONFIG_INVALID.
            """
            return self._run(self._aio.get_radioConfig())

    if not _DYNAMIC_HELPERS:
        def set_radioConfig(self, newval: str) -> int:
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
            return self._run(self._aio.set_radioConfig(newval))

    if not _DYNAMIC_HELPERS:
        def get_lockedOperator(self) -> str:
            """
            Returns the name of the only cell operator to use if automatic choice is disabled,
            or an empty string if the SIM card will automatically choose among available
            cell operators.

            @return a string corresponding to the name of the only cell operator to use if automatic choice is disabled,
                    or an empty string if the SIM card will automatically choose among available
                    cell operators

            On failure, throws an exception or returns YCellular.LOCKEDOPERATOR_INVALID.
            """
            return self._run(self._aio.get_lockedOperator())

    if not _DYNAMIC_HELPERS:
        def set_lockedOperator(self, newval: str) -> int:
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
            return self._run(self._aio.set_lockedOperator(newval))

    if not _DYNAMIC_HELPERS:
        def get_airplaneMode(self) -> int:
            """
            Returns true if the airplane mode is active (radio turned off).

            @return either YCellular.AIRPLANEMODE_OFF or YCellular.AIRPLANEMODE_ON, according to true if the
            airplane mode is active (radio turned off)

            On failure, throws an exception or returns YCellular.AIRPLANEMODE_INVALID.
            """
            return self._run(self._aio.get_airplaneMode())

    if not _DYNAMIC_HELPERS:
        def set_airplaneMode(self, newval: int) -> int:
            """
            Changes the activation state of airplane mode (radio turned off).

            @param newval : either YCellular.AIRPLANEMODE_OFF or YCellular.AIRPLANEMODE_ON, according to the
            activation state of airplane mode (radio turned off)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_airplaneMode(newval))

    if not _DYNAMIC_HELPERS:
        def get_enableData(self) -> int:
            """
            Returns the condition for enabling IP data services (GPRS).
            When data services are disabled, SMS are the only mean of communication.

            @return a value among YCellular.ENABLEDATA_HOMENETWORK, YCellular.ENABLEDATA_ROAMING,
            YCellular.ENABLEDATA_NEVER and YCellular.ENABLEDATA_NEUTRALITY corresponding to the condition for
            enabling IP data services (GPRS)

            On failure, throws an exception or returns YCellular.ENABLEDATA_INVALID.
            """
            return self._run(self._aio.get_enableData())

    if not _DYNAMIC_HELPERS:
        def set_enableData(self, newval: int) -> int:
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
            return self._run(self._aio.set_enableData(newval))

    if not _DYNAMIC_HELPERS:
        def get_apn(self) -> str:
            """
            Returns the Access Point Name (APN) to be used, if needed.
            When left blank, the APN suggested by the cell operator will be used.

            @return a string corresponding to the Access Point Name (APN) to be used, if needed

            On failure, throws an exception or returns YCellular.APN_INVALID.
            """
            return self._run(self._aio.get_apn())

    if not _DYNAMIC_HELPERS:
        def set_apn(self, newval: str) -> int:
            """
            Returns the Access Point Name (APN) to be used, if needed.
            When left blank, the APN suggested by the cell operator will be used.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a string

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_apn(newval))

    if not _DYNAMIC_HELPERS:
        def get_apnSecret(self) -> str:
            """
            Returns an opaque string if APN authentication parameters have been configured
            in the device, or an empty string otherwise.
            To configure these parameters, use set_apnAuth().

            @return a string corresponding to an opaque string if APN authentication parameters have been configured
                    in the device, or an empty string otherwise

            On failure, throws an exception or returns YCellular.APNSECRET_INVALID.
            """
            return self._run(self._aio.get_apnSecret())

    if not _DYNAMIC_HELPERS:
        def set_apnSecret(self, newval: str) -> int:
            return self._run(self._aio.set_apnSecret(newval))

    if not _DYNAMIC_HELPERS:
        def get_pingInterval(self) -> int:
            """
            Returns the automated connectivity check interval, in seconds.

            @return an integer corresponding to the automated connectivity check interval, in seconds

            On failure, throws an exception or returns YCellular.PINGINTERVAL_INVALID.
            """
            return self._run(self._aio.get_pingInterval())

    if not _DYNAMIC_HELPERS:
        def set_pingInterval(self, newval: int) -> int:
            """
            Changes the automated connectivity check interval, in seconds.
            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the automated connectivity check interval, in seconds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_pingInterval(newval))

    if not _DYNAMIC_HELPERS:
        def get_dataSent(self) -> int:
            """
            Returns the number of bytes sent so far.

            @return an integer corresponding to the number of bytes sent so far

            On failure, throws an exception or returns YCellular.DATASENT_INVALID.
            """
            return self._run(self._aio.get_dataSent())

    if not _DYNAMIC_HELPERS:
        def set_dataSent(self, newval: int) -> int:
            """
            Changes the value of the outgoing data counter.

            @param newval : an integer corresponding to the value of the outgoing data counter

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_dataSent(newval))

    if not _DYNAMIC_HELPERS:
        def get_dataReceived(self) -> int:
            """
            Returns the number of bytes received so far.

            @return an integer corresponding to the number of bytes received so far

            On failure, throws an exception or returns YCellular.DATARECEIVED_INVALID.
            """
            return self._run(self._aio.get_dataReceived())

    if not _DYNAMIC_HELPERS:
        def set_dataReceived(self, newval: int) -> int:
            """
            Changes the value of the incoming data counter.

            @param newval : an integer corresponding to the value of the incoming data counter

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_dataReceived(newval))

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YCellularValueCallback) -> int:
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
        def sendPUK(self, puk: str, newPin: str) -> int:
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
            return self._run(self._aio.sendPUK(puk, newPin))

    if not _DYNAMIC_HELPERS:
        def set_apnAuth(self, username: str, password: str) -> int:
            """
            Configure authentication parameters to connect to the APN. Both
            PAP and CHAP authentication are supported.

            @param username : APN username
            @param password : APN password

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_apnAuth(username, password))

    if not _DYNAMIC_HELPERS:
        def clearDataCounters(self) -> int:
            """
            Clear the transmitted data counters.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.clearDataCounters())

    if not _DYNAMIC_HELPERS:
        def _AT(self, cmd: str) -> str:
            """
            Sends an AT command to the GSM module and returns the command output.
            The command will only execute when the GSM module is in standard
            command state, and should leave it in the exact same state.
            Use this function with great care !

            @param cmd : the AT command to execute, like for instance: "+CCLK?".

            @return a string with the result of the commands. Empty lines are
                    automatically removed from the output.
            """
            return self._run(self._aio._AT(cmd))

    if not _DYNAMIC_HELPERS:
        def get_availableOperators(self) -> list[str]:
            """
            Returns the list detected cell operators in the neighborhood.
            This function will typically take between 30 seconds to 1 minute to
            return. Note that any SIM card can usually only connect to specific
            operators. All networks returned by this function might therefore
            not be available for connection.

            @return a list of string (cell operator names).
            """
            return self._run(self._aio.get_availableOperators())

    if not _DYNAMIC_HELPERS:
        def quickCellSurvey(self) -> list[YCellRecord]:
            """
            Returns a list of nearby cellular antennas, as required for quick
            geolocation of the device. The first cell listed is the serving
            cell, and the next ones are the neighbor cells reported by the
            serving cell.

            @return a list of YCellRecords.
            """
            return self._run(self._aio.quickCellSurvey())

    if not _DYNAMIC_HELPERS:
        def decodePLMN(self, mccmnc: str) -> str:
            """
            Returns the cell operator brand for a given MCC/MNC pair (DEPRECATED).

            @param mccmnc : a string starting with a MCC code followed by a MNC code,

            @return a string containing the corresponding cell operator brand name.
            """
            return self._run(self._aio.decodePLMN(mccmnc))

    if not _DYNAMIC_HELPERS:
        def get_communicationProfiles(self) -> list[str]:
            """
            Returns the list available radio communication profiles, as a string array
            (YoctoHub-GSM-4G only).
            Each string is a made of a numerical ID, followed by a colon,
            followed by the profile description.

            @return a list of string describing available radio communication profiles.
            """
            return self._run(self._aio.get_communicationProfiles())

    # --- (end of generated code: YCellular implementation)

