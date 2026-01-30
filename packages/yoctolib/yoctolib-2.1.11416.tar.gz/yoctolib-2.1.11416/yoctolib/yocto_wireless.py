# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_wireless.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YWireless API for Wireless functions
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
Yoctopuce library: High-level API for YWireless
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_wireless_aio
provides: YWireless YWlanRecord
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

from .yocto_wireless_aio import (
    YWireless as YWireless_aio,
    YWlanRecord
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (generated code: YWireless class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YWirelessValueCallback = Union[Callable[['YWireless', str], Any], None]
    except TypeError:
        YWirelessValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YWireless(YFunction):
    """
    The YWireless class provides control over wireless network parameters
    and status for devices that are wireless-enabled.
    Note that TCP/IP parameters are configured separately, using class YNetwork.

    """
    _aio: YWireless_aio
    # --- (end of generated code: YWireless class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YWireless return codes)
        LINKQUALITY_INVALID: Final[int] = YAPI.INVALID_UINT
        SSID_INVALID: Final[str] = YAPI.INVALID_STRING
        CHANNEL_INVALID: Final[int] = YAPI.INVALID_UINT
        MESSAGE_INVALID: Final[str] = YAPI.INVALID_STRING
        WLANCONFIG_INVALID: Final[str] = YAPI.INVALID_STRING
        SECURITY_UNKNOWN: Final[int] = 0
        SECURITY_OPEN: Final[int] = 1
        SECURITY_WEP: Final[int] = 2
        SECURITY_WPA: Final[int] = 3
        SECURITY_WPA2: Final[int] = 4
        SECURITY_INVALID: Final[int] = -1
        WLANSTATE_DOWN: Final[int] = 0
        WLANSTATE_SCANNING: Final[int] = 1
        WLANSTATE_CONNECTED: Final[int] = 2
        WLANSTATE_REJECTED: Final[int] = 3
        WLANSTATE_INVALID: Final[int] = -1
        # --- (end of generated code: YWireless return codes)

    # --- (generated code: YWireless implementation)

    @classmethod
    def FindWireless(cls, func: str) -> YWireless:
        """
        Retrieves a wireless LAN interface for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the wireless LAN interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWireless.isOnline() to test if the wireless LAN interface is
        indeed online at a given time. In case of ambiguity when looking for
        a wireless LAN interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the wireless LAN interface, for instance
                YHUBWLN1.wireless.

        @return a YWireless object allowing you to drive the wireless LAN interface.
        """
        return cls._proxy(cls, YWireless_aio.FindWirelessInContext(YAPI_aio, func))

    @classmethod
    def FindWirelessInContext(cls, yctx: YAPIContext, func: str) -> YWireless:
        """
        Retrieves a wireless LAN interface for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the wireless LAN interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YWireless.isOnline() to test if the wireless LAN interface is
        indeed online at a given time. In case of ambiguity when looking for
        a wireless LAN interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the wireless LAN interface, for instance
                YHUBWLN1.wireless.

        @return a YWireless object allowing you to drive the wireless LAN interface.
        """
        return cls._proxy(cls, YWireless_aio.FindWirelessInContext(yctx._aio, func))

    @classmethod
    def FirstWireless(cls) -> Union[YWireless, None]:
        """
        Starts the enumeration of wireless LAN interfaces currently accessible.
        Use the method YWireless.nextWireless() to iterate on
        next wireless LAN interfaces.

        @return a pointer to a YWireless object, corresponding to
                the first wireless LAN interface currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YWireless_aio.FirstWirelessInContext(YAPI_aio))

    @classmethod
    def FirstWirelessInContext(cls, yctx: YAPIContext) -> Union[YWireless, None]:
        """
        Starts the enumeration of wireless LAN interfaces currently accessible.
        Use the method YWireless.nextWireless() to iterate on
        next wireless LAN interfaces.

        @param yctx : a YAPI context.

        @return a pointer to a YWireless object, corresponding to
                the first wireless LAN interface currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YWireless_aio.FirstWirelessInContext(yctx._aio))

    def nextWireless(self) -> Union[YWireless, None]:
        """
        Continues the enumeration of wireless LAN interfaces started using yFirstWireless().
        Caution: You can't make any assumption about the returned wireless LAN interfaces order.
        If you want to find a specific a wireless LAN interface, use Wireless.findWireless()
        and a hardwareID or a logical name.

        @return a pointer to a YWireless object, corresponding to
                a wireless LAN interface currently online, or a None pointer
                if there are no more wireless LAN interfaces to enumerate.
        """
        return self._proxy(type(self), self._aio.nextWireless())

    if not _DYNAMIC_HELPERS:
        def get_linkQuality(self) -> int:
            """
            Returns the link quality, expressed in percent.

            @return an integer corresponding to the link quality, expressed in percent

            On failure, throws an exception or returns YWireless.LINKQUALITY_INVALID.
            """
            return self._run(self._aio.get_linkQuality())

    if not _DYNAMIC_HELPERS:
        def get_ssid(self) -> str:
            """
            Returns the wireless network name (SSID).

            @return a string corresponding to the wireless network name (SSID)

            On failure, throws an exception or returns YWireless.SSID_INVALID.
            """
            return self._run(self._aio.get_ssid())

    if not _DYNAMIC_HELPERS:
        def get_channel(self) -> int:
            """
            Returns the 802.11 channel currently used, or 0 when the selected network has not been found.

            @return an integer corresponding to the 802.11 channel currently used, or 0 when the selected
            network has not been found

            On failure, throws an exception or returns YWireless.CHANNEL_INVALID.
            """
            return self._run(self._aio.get_channel())

    if not _DYNAMIC_HELPERS:
        def get_security(self) -> int:
            """
            Returns the security algorithm used by the selected wireless network.

            @return a value among YWireless.SECURITY_UNKNOWN, YWireless.SECURITY_OPEN, YWireless.SECURITY_WEP,
            YWireless.SECURITY_WPA and YWireless.SECURITY_WPA2 corresponding to the security algorithm used by
            the selected wireless network

            On failure, throws an exception or returns YWireless.SECURITY_INVALID.
            """
            return self._run(self._aio.get_security())

    if not _DYNAMIC_HELPERS:
        def get_message(self) -> str:
            """
            Returns the latest status message from the wireless interface.

            @return a string corresponding to the latest status message from the wireless interface

            On failure, throws an exception or returns YWireless.MESSAGE_INVALID.
            """
            return self._run(self._aio.get_message())

    if not _DYNAMIC_HELPERS:
        def set_wlanConfig(self, newval: str) -> int:
            return self._run(self._aio.set_wlanConfig(newval))

    if not _DYNAMIC_HELPERS:
        def get_wlanState(self) -> int:
            """
            Returns the current state of the wireless interface. The state YWireless.WLANSTATE_DOWN means that
            the network interface is
            not connected to a network. The state YWireless.WLANSTATE_SCANNING means that the network interface
            is scanning available
            frequencies. During this stage, the device is not reachable, and the network settings are not yet
            applied. The state
            YWireless.WLANSTATE_CONNECTED means that the network settings have been successfully applied ant
            that the device is reachable
            from the wireless network. If the device is configured to use ad-hoc or Soft AP mode, it means that
            the wireless network
            is up and that other devices can join the network. The state YWireless.WLANSTATE_REJECTED means
            that the network interface has
            not been able to join the requested network. The description of the error can be obtain with the
            get_message() method.

            @return a value among YWireless.WLANSTATE_DOWN, YWireless.WLANSTATE_SCANNING,
            YWireless.WLANSTATE_CONNECTED and YWireless.WLANSTATE_REJECTED corresponding to the current state
            of the wireless interface

            On failure, throws an exception or returns YWireless.WLANSTATE_INVALID.
            """
            return self._run(self._aio.get_wlanState())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YWirelessValueCallback) -> int:
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
        def startWlanScan(self) -> int:
            """
            Triggers a scan of the wireless frequency and builds the list of available networks.
            The scan forces a disconnection from the current network. At then end of the process, the
            the network interface attempts to reconnect to the previous network. During the scan, the wlanState
            switches to YWireless.WLANSTATE_DOWN, then to YWireless.WLANSTATE_SCANNING. When the scan is completed,
            get_wlanState() returns either YWireless.WLANSTATE_DOWN or YWireless.WLANSTATE_SCANNING. At this
            point, the list of detected network can be retrieved with the get_detectedWlans() method.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.startWlanScan())

    if not _DYNAMIC_HELPERS:
        def joinNetwork(self, ssid: str, securityKey: str) -> int:
            """
            Changes the configuration of the wireless lan interface to connect to an existing
            access point (infrastructure mode).
            Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

            @param ssid : the name of the network to connect to
            @param securityKey : the network key, as a character string

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.joinNetwork(ssid, securityKey))

    if not _DYNAMIC_HELPERS:
        def adhocNetwork(self, ssid: str, securityKey: str) -> int:
            """
            Changes the configuration of the wireless lan interface to create an ad-hoc
            wireless network, without using an access point. On the YoctoHub-Wireless-g
            and YoctoHub-Wireless-n,
            you should use softAPNetwork() instead, which emulates an access point
            (Soft AP) which is more efficient and more widely supported than ad-hoc networks.

            When a security key is specified for an ad-hoc network, the network is protected
            by a WEP40 key (5 characters or 10 hexadecimal digits) or WEP128 key (13 characters
            or 26 hexadecimal digits). It is recommended to use a well-randomized WEP128 key
            using 26 hexadecimal digits to maximize security.
            Remember to call the saveToFlash() method and then to reboot the module
            to apply this setting.

            @param ssid : the name of the network to connect to
            @param securityKey : the network key, as a character string

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.adhocNetwork(ssid, securityKey))

    if not _DYNAMIC_HELPERS:
        def softAPNetwork(self, ssid: str, securityKey: str) -> int:
            """
            Changes the configuration of the wireless lan interface to create a new wireless
            network by emulating a WiFi access point (Soft AP). This function can only be
            used with the YoctoHub-Wireless-g and the YoctoHub-Wireless-n.

            On the YoctoHub-Wireless-g, when a security key is specified for a SoftAP network,
            the network is protected by a WEP40 key (5 characters or 10 hexadecimal digits) or
            WEP128 key (13 characters or 26 hexadecimal digits). It is recommended to use a
            well-randomized WEP128 key using 26 hexadecimal digits to maximize security.

            On the YoctoHub-Wireless-n, when a security key is specified for a SoftAP network,
            the network will be protected by WPA2.

            Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

            @param ssid : the name of the network to connect to
            @param securityKey : the network key, as a character string

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.softAPNetwork(ssid, securityKey))

    if not _DYNAMIC_HELPERS:
        def get_detectedWlans(self) -> list[YWlanRecord]:
            """
            Returns a list of YWlanRecord objects that describe detected Wireless networks.
            This list is not updated when the module is already connected to an access point (infrastructure mode).
            To force an update of this list, startWlanScan() must be called.
            Note that an languages without garbage collections, the returned list must be freed by the caller.

            @return a list of YWlanRecord objects, containing the SSID, channel,
                    link quality and the type of security of the wireless network.

            On failure, throws an exception or returns an empty list.
            """
            return self._run(self._aio.get_detectedWlans())

    # --- (end of generated code: YWireless implementation)

