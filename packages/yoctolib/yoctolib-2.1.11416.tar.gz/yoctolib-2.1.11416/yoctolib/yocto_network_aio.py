# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YNetwork
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
Yoctopuce library: Asyncio implementation of YNetwork
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YNetwork
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction, xarray
)

# --- (YNetwork class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YNetworkValueCallback = Union[Callable[['YNetwork', str], Any], None]
    except TypeError:
        YNetworkValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YNetwork(YFunction):
    """
    YNetwork objects provide access to TCP/IP parameters of Yoctopuce
    devices that include a built-in network interface.

    """
    # --- (end of YNetwork class start)
    if not _IS_MICROPYTHON:
        # --- (YNetwork return codes)
        MACADDRESS_INVALID: Final[str] = YAPI.INVALID_STRING
        IPADDRESS_INVALID: Final[str] = YAPI.INVALID_STRING
        SUBNETMASK_INVALID: Final[str] = YAPI.INVALID_STRING
        ROUTER_INVALID: Final[str] = YAPI.INVALID_STRING
        CURRENTDNS_INVALID: Final[str] = YAPI.INVALID_STRING
        IPCONFIG_INVALID: Final[str] = YAPI.INVALID_STRING
        PRIMARYDNS_INVALID: Final[str] = YAPI.INVALID_STRING
        SECONDARYDNS_INVALID: Final[str] = YAPI.INVALID_STRING
        NTPSERVER_INVALID: Final[str] = YAPI.INVALID_STRING
        USERPASSWORD_INVALID: Final[str] = YAPI.INVALID_STRING
        ADMINPASSWORD_INVALID: Final[str] = YAPI.INVALID_STRING
        HTTPPORT_INVALID: Final[int] = YAPI.INVALID_UINT
        HTTPSPORT_INVALID: Final[int] = YAPI.INVALID_UINT
        DEFAULTPAGE_INVALID: Final[str] = YAPI.INVALID_STRING
        WWWWATCHDOGDELAY_INVALID: Final[int] = YAPI.INVALID_UINT
        CALLBACKURL_INVALID: Final[str] = YAPI.INVALID_STRING
        CALLBACKCREDENTIALS_INVALID: Final[str] = YAPI.INVALID_STRING
        CALLBACKINITIALDELAY_INVALID: Final[int] = YAPI.INVALID_UINT
        CALLBACKSCHEDULE_INVALID: Final[str] = YAPI.INVALID_STRING
        CALLBACKMINDELAY_INVALID: Final[int] = YAPI.INVALID_UINT
        CALLBACKMAXDELAY_INVALID: Final[int] = YAPI.INVALID_UINT
        POECURRENT_INVALID: Final[int] = YAPI.INVALID_UINT
        READINESS_DOWN: Final[int] = 0
        READINESS_EXISTS: Final[int] = 1
        READINESS_LINKED: Final[int] = 2
        READINESS_LAN_OK: Final[int] = 3
        READINESS_WWW_OK: Final[int] = 4
        READINESS_INVALID: Final[int] = -1
        SECURITYMODE_UNDEFINED: Final[int] = 0
        SECURITYMODE_LEGACY: Final[int] = 1
        SECURITYMODE_MIXED: Final[int] = 2
        SECURITYMODE_SECURE: Final[int] = 3
        SECURITYMODE_INVALID: Final[int] = -1
        DISCOVERABLE_FALSE: Final[int] = 0
        DISCOVERABLE_TRUE: Final[int] = 1
        DISCOVERABLE_INVALID: Final[int] = -1
        CALLBACKMETHOD_POST: Final[int] = 0
        CALLBACKMETHOD_GET: Final[int] = 1
        CALLBACKMETHOD_PUT: Final[int] = 2
        CALLBACKMETHOD_INVALID: Final[int] = -1
        CALLBACKENCODING_FORM: Final[int] = 0
        CALLBACKENCODING_JSON: Final[int] = 1
        CALLBACKENCODING_JSON_ARRAY: Final[int] = 2
        CALLBACKENCODING_CSV: Final[int] = 3
        CALLBACKENCODING_YOCTO_API: Final[int] = 4
        CALLBACKENCODING_JSON_NUM: Final[int] = 5
        CALLBACKENCODING_EMONCMS: Final[int] = 6
        CALLBACKENCODING_AZURE: Final[int] = 7
        CALLBACKENCODING_INFLUXDB: Final[int] = 8
        CALLBACKENCODING_MQTT: Final[int] = 9
        CALLBACKENCODING_YOCTO_API_JZON: Final[int] = 10
        CALLBACKENCODING_PRTG: Final[int] = 11
        CALLBACKENCODING_INFLUXDB_V2: Final[int] = 12
        CALLBACKENCODING_INVALID: Final[int] = -1
        CALLBACKTEMPLATE_OFF: Final[int] = 0
        CALLBACKTEMPLATE_ON: Final[int] = 1
        CALLBACKTEMPLATE_INVALID: Final[int] = -1
        # --- (end of YNetwork return codes)

    # --- (YNetwork attributes declaration)
    _valueCallback: YNetworkValueCallback
    # --- (end of YNetwork attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Network', func)
        # --- (YNetwork constructor)
        # --- (end of YNetwork constructor)

    # --- (YNetwork implementation)
    @classmethod
    def FindNetwork(cls, func: str) -> YNetwork:
        """
        Retrieves a network interface for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the network interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YNetwork.isOnline() to test if the network interface is
        indeed online at a given time. In case of ambiguity when looking for
        a network interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the network interface, for instance
                YHUBETH1.network.

        @return a YNetwork object allowing you to drive the network interface.
        """
        return cls.FindNetworkInContext(YAPI, func)

    @classmethod
    def FindNetworkInContext(cls, yctx: YAPIContext, func: str) -> YNetwork:
        """
        Retrieves a network interface for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the network interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YNetwork.isOnline() to test if the network interface is
        indeed online at a given time. In case of ambiguity when looking for
        a network interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the network interface, for instance
                YHUBETH1.network.

        @return a YNetwork object allowing you to drive the network interface.
        """
        obj: Union[YNetwork, None] = yctx._findInCache('Network', func)
        if obj:
            return obj
        return YNetwork(yctx, func)

    @classmethod
    def FirstNetwork(cls) -> Union[YNetwork, None]:
        """
        Starts the enumeration of network interfaces currently accessible.
        Use the method YNetwork.nextNetwork() to iterate on
        next network interfaces.

        @return a pointer to a YNetwork object, corresponding to
                the first network interface currently online, or a None pointer
                if there are none.
        """
        return cls.FirstNetworkInContext(YAPI)

    @classmethod
    def FirstNetworkInContext(cls, yctx: YAPIContext) -> Union[YNetwork, None]:
        """
        Starts the enumeration of network interfaces currently accessible.
        Use the method YNetwork.nextNetwork() to iterate on
        next network interfaces.

        @param yctx : a YAPI context.

        @return a pointer to a YNetwork object, corresponding to
                the first network interface currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Network')
        if hwid:
            return cls.FindNetworkInContext(yctx, hwid2str(hwid))
        return None

    def nextNetwork(self) -> Union[YNetwork, None]:
        """
        Continues the enumeration of network interfaces started using yFirstNetwork().
        Caution: You can't make any assumption about the returned network interfaces order.
        If you want to find a specific a network interface, use Network.findNetwork()
        and a hardwareID or a logical name.

        @return a pointer to a YNetwork object, corresponding to
                a network interface currently online, or a None pointer
                if there are no more network interfaces to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Network', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindNetworkInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_readiness(self) -> int:
        """
        Returns the current established working mode of the network interface.
        Level zero (DOWN_0) means that no hardware link has been detected. Either there is no signal
        on the network cable, or the selected wireless access point cannot be detected.
        Level 1 (LIVE_1) is reached when the network is detected, but is not yet connected.
        For a wireless network, this shows that the requested SSID is present.
        Level 2 (LINK_2) is reached when the hardware connection is established.
        For a wired network connection, level 2 means that the cable is attached at both ends.
        For a connection to a wireless access point, it shows that the security parameters
        are properly configured. For an ad-hoc wireless connection, it means that there is
        at least one other device connected on the ad-hoc network.
        Level 3 (DHCP_3) is reached when an IP address has been obtained using DHCP.
        Level 4 (DNS_4) is reached when the DNS server is reachable on the network.
        Level 5 (WWW_5) is reached when global connectivity is demonstrated by properly loading the
        current time from an NTP server.

        @return a value among YNetwork.READINESS_DOWN, YNetwork.READINESS_EXISTS,
        YNetwork.READINESS_LINKED, YNetwork.READINESS_LAN_OK and YNetwork.READINESS_WWW_OK corresponding to
        the current established working mode of the network interface

        On failure, throws an exception or returns YNetwork.READINESS_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("readiness")
        if json_val is None:
            return YNetwork.READINESS_INVALID
        return json_val

    async def get_macAddress(self) -> str:
        """
        Returns the MAC address of the network interface. The MAC address is also available on a sticker
        on the module, in both numeric and barcode forms.

        @return a string corresponding to the MAC address of the network interface

        On failure, throws an exception or returns YNetwork.MACADDRESS_INVALID.
        """
        json_val: Union[str, None] = await self._lazyCache("macAddress")
        if json_val is None:
            return YNetwork.MACADDRESS_INVALID
        return json_val

    async def get_ipAddress(self) -> str:
        """
        Returns the IP address currently in use by the device. The address may have been configured
        statically, or provided by a DHCP server.

        @return a string corresponding to the IP address currently in use by the device

        On failure, throws an exception or returns YNetwork.IPADDRESS_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("ipAddress")
        if json_val is None:
            return YNetwork.IPADDRESS_INVALID
        return json_val

    async def get_subnetMask(self) -> str:
        """
        Returns the subnet mask currently used by the device.

        @return a string corresponding to the subnet mask currently used by the device

        On failure, throws an exception or returns YNetwork.SUBNETMASK_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("subnetMask")
        if json_val is None:
            return YNetwork.SUBNETMASK_INVALID
        return json_val

    async def get_router(self) -> str:
        """
        Returns the IP address of the router on the device subnet (default gateway).

        @return a string corresponding to the IP address of the router on the device subnet (default gateway)

        On failure, throws an exception or returns YNetwork.ROUTER_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("router")
        if json_val is None:
            return YNetwork.ROUTER_INVALID
        return json_val

    async def get_currentDNS(self) -> str:
        """
        Returns the IP address of the DNS server currently used by the device.

        @return a string corresponding to the IP address of the DNS server currently used by the device

        On failure, throws an exception or returns YNetwork.CURRENTDNS_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("currentDNS")
        if json_val is None:
            return YNetwork.CURRENTDNS_INVALID
        return json_val

    async def get_ipConfig(self) -> str:
        """
        Returns the IP configuration of the network interface.

        If the network interface is set up to use a static IP address, the string starts with "STATIC:" and
        is followed by three
        parameters, separated by "/". The first is the device IP address, followed by the subnet mask
        length, and finally the
        router IP address (default gateway). For instance: "STATIC:192.168.1.14/16/192.168.1.1"

        If the network interface is configured to receive its IP from a DHCP server, the string start with
        "DHCP:" and is followed by
        three parameters separated by "/". The first is the fallback IP address, then the fallback subnet
        mask length and finally the
        fallback router IP address. These three parameters are used when no DHCP reply is received.

        @return a string corresponding to the IP configuration of the network interface

        On failure, throws an exception or returns YNetwork.IPCONFIG_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("ipConfig")
        if json_val is None:
            return YNetwork.IPCONFIG_INVALID
        return json_val

    async def set_ipConfig(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("ipConfig", rest_val)

    async def get_primaryDNS(self) -> str:
        """
        Returns the IP address of the primary name server to be used by the module.

        @return a string corresponding to the IP address of the primary name server to be used by the module

        On failure, throws an exception or returns YNetwork.PRIMARYDNS_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("primaryDNS")
        if json_val is None:
            return YNetwork.PRIMARYDNS_INVALID
        return json_val

    async def set_primaryDNS(self, newval: str) -> int:
        """
        Changes the IP address of the primary name server to be used by the module.
        When using DHCP, if a value is specified, it overrides the value received from the DHCP server.
        Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

        @param newval : a string corresponding to the IP address of the primary name server to be used by the module

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("primaryDNS", rest_val)

    async def get_secondaryDNS(self) -> str:
        """
        Returns the IP address of the secondary name server to be used by the module.

        @return a string corresponding to the IP address of the secondary name server to be used by the module

        On failure, throws an exception or returns YNetwork.SECONDARYDNS_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("secondaryDNS")
        if json_val is None:
            return YNetwork.SECONDARYDNS_INVALID
        return json_val

    async def set_secondaryDNS(self, newval: str) -> int:
        """
        Changes the IP address of the secondary name server to be used by the module.
        When using DHCP, if a value is specified, it overrides the value received from the DHCP server.
        Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

        @param newval : a string corresponding to the IP address of the secondary name server to be used by the module

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("secondaryDNS", rest_val)

    async def get_ntpServer(self) -> str:
        """
        Returns the IP address of the NTP server to be used by the device.

        @return a string corresponding to the IP address of the NTP server to be used by the device

        On failure, throws an exception or returns YNetwork.NTPSERVER_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("ntpServer")
        if json_val is None:
            return YNetwork.NTPSERVER_INVALID
        return json_val

    async def set_ntpServer(self, newval: str) -> int:
        """
        Changes the IP address of the NTP server to be used by the module. Use an empty
        string to restore the factory set  address.
        Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

        @param newval : a string corresponding to the IP address of the NTP server to be used by the module

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("ntpServer", rest_val)

    async def get_userPassword(self) -> str:
        """
        Returns a hash string if a password has been set for "user" user,
        or an empty string otherwise.

        @return a string corresponding to a hash string if a password has been set for "user" user,
                or an empty string otherwise

        On failure, throws an exception or returns YNetwork.USERPASSWORD_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("userPassword")
        if json_val is None:
            return YNetwork.USERPASSWORD_INVALID
        return json_val

    async def set_userPassword(self, newval: str) -> int:
        """
        Changes the password for the "user" user. This password becomes instantly required
        to perform any use of the module. If the specified value is an
        empty string, a password is not required anymore.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the password for the "user" user

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not self._is_valid_pass(newval):
            return YAPI.INVALID_ARGUMENT
        rest_val = newval
        return await self._setAttr("userPassword", rest_val)

    async def get_adminPassword(self) -> str:
        """
        Returns a hash string if a password has been set for user "admin",
        or an empty string otherwise.

        @return a string corresponding to a hash string if a password has been set for user "admin",
                or an empty string otherwise

        On failure, throws an exception or returns YNetwork.ADMINPASSWORD_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("adminPassword")
        if json_val is None:
            return YNetwork.ADMINPASSWORD_INVALID
        return json_val

    async def set_adminPassword(self, newval: str) -> int:
        """
        Changes the password for the "admin" user. This password becomes instantly required
        to perform any change of the module state. If the specified value is an
        empty string, a password is not required anymore.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the password for the "admin" user

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not self._is_valid_pass(newval):
            return YAPI.INVALID_ARGUMENT
        rest_val = newval
        return await self._setAttr("adminPassword", rest_val)

    async def get_httpPort(self) -> int:
        """
        Returns the TCP port used to serve the hub web UI.

        @return an integer corresponding to the TCP port used to serve the hub web UI

        On failure, throws an exception or returns YNetwork.HTTPPORT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("httpPort")
        if json_val is None:
            return YNetwork.HTTPPORT_INVALID
        return json_val

    async def set_httpPort(self, newval: int) -> int:
        """
        Changes the the TCP port used to serve the hub web UI. The default value is port 80,
        which is the default for all Web servers. Regardless of the value set here,
        the hub will always reply on port 4444, which is used by default by Yoctopuce
        API library. When you change this parameter, remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the the TCP port used to serve the hub web UI

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("httpPort", rest_val)

    async def get_httpsPort(self) -> int:
        """
        Returns the secure TCP port used to serve the hub web UI.

        @return an integer corresponding to the secure TCP port used to serve the hub web UI

        On failure, throws an exception or returns YNetwork.HTTPSPORT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("httpsPort")
        if json_val is None:
            return YNetwork.HTTPSPORT_INVALID
        return json_val

    async def set_httpsPort(self, newval: int) -> int:
        """
        Changes the secure TCP port used to serve the hub web UI. The default value is port 4443,
        which is the default for all Web servers. When you change this parameter, remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the secure TCP port used to serve the hub web UI

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("httpsPort", rest_val)

    async def get_securityMode(self) -> int:
        """
        Returns the security level chosen to prevent unauthorized access to the server.

        @return a value among YNetwork.SECURITYMODE_UNDEFINED, YNetwork.SECURITYMODE_LEGACY,
        YNetwork.SECURITYMODE_MIXED and YNetwork.SECURITYMODE_SECURE corresponding to the security level
        chosen to prevent unauthorized access to the server

        On failure, throws an exception or returns YNetwork.SECURITYMODE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("securityMode")
        if json_val is None:
            return YNetwork.SECURITYMODE_INVALID
        return json_val

    async def set_securityMode(self, newval: int) -> int:
        """
        Changes the security level used to prevent unauthorized access to the server.
        The value UNDEFINED causes the security configuration wizard to be
        displayed the next time you log on to the Web console.
        The value LEGACY offers unencrypted HTTP access by default, and
        is designed to provide compatibility with legacy applications that do not
        handle password or do not support HTTPS. But it should
        only be used when system security is guaranteed by other means, such as the
        use of a firewall.
        The value MIXED requires the configuration of passwords, and allows
        access via both HTTP (unencrypted) and HTTPS (encrypted), while requiring
        the Yoctopuce API to be tolerant of certificate characteristics.
        The value SECURE requires the configuration of passwords and the
        use of secure communications in all cases.
        When you change this parameter, remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a value among YNetwork.SECURITYMODE_UNDEFINED, YNetwork.SECURITYMODE_LEGACY,
        YNetwork.SECURITYMODE_MIXED and YNetwork.SECURITYMODE_SECURE corresponding to the security level
        used to prevent unauthorized access to the server

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("securityMode", rest_val)

    async def get_defaultPage(self) -> str:
        """
        Returns the HTML page to serve for the URL "/"" of the hub.

        @return a string corresponding to the HTML page to serve for the URL "/"" of the hub

        On failure, throws an exception or returns YNetwork.DEFAULTPAGE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("defaultPage")
        if json_val is None:
            return YNetwork.DEFAULTPAGE_INVALID
        return json_val

    async def set_defaultPage(self, newval: str) -> int:
        """
        Changes the default HTML page returned by the hub. If not value are set the hub return
        "index.html" which is the web interface of the hub. It is possible to change this page
        for file that has been uploaded on the hub. The maximum filename size is 15 characters.
        When you change this parameter, remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a string corresponding to the default HTML page returned by the hub

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("defaultPage", rest_val)

    async def get_discoverable(self) -> int:
        """
        Returns the activation state of the multicast announce protocols to allow easy
        discovery of the module in the network neighborhood (uPnP/Bonjour protocol).

        @return either YNetwork.DISCOVERABLE_FALSE or YNetwork.DISCOVERABLE_TRUE, according to the
        activation state of the multicast announce protocols to allow easy
                discovery of the module in the network neighborhood (uPnP/Bonjour protocol)

        On failure, throws an exception or returns YNetwork.DISCOVERABLE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("discoverable")
        if json_val is None:
            return YNetwork.DISCOVERABLE_INVALID
        return json_val

    async def set_discoverable(self, newval: int) -> int:
        """
        Changes the activation state of the multicast announce protocols to allow easy
        discovery of the module in the network neighborhood (uPnP/Bonjour protocol).
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : either YNetwork.DISCOVERABLE_FALSE or YNetwork.DISCOVERABLE_TRUE, according to the
        activation state of the multicast announce protocols to allow easy
                discovery of the module in the network neighborhood (uPnP/Bonjour protocol)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("discoverable", rest_val)

    async def get_wwwWatchdogDelay(self) -> int:
        """
        Returns the allowed downtime of the WWW link (in seconds) before triggering an automated
        reboot to try to recover Internet connectivity. A zero value disables automated reboot
        in case of Internet connectivity loss.

        @return an integer corresponding to the allowed downtime of the WWW link (in seconds) before
        triggering an automated
                reboot to try to recover Internet connectivity

        On failure, throws an exception or returns YNetwork.WWWWATCHDOGDELAY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("wwwWatchdogDelay")
        if json_val is None:
            return YNetwork.WWWWATCHDOGDELAY_INVALID
        return json_val

    async def set_wwwWatchdogDelay(self, newval: int) -> int:
        """
        Changes the allowed downtime of the WWW link (in seconds) before triggering an automated
        reboot to try to recover Internet connectivity. A zero value disables automated reboot
        in case of Internet connectivity loss. The smallest valid non-zero timeout is
        90 seconds. Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : an integer corresponding to the allowed downtime of the WWW link (in seconds)
        before triggering an automated
                reboot to try to recover Internet connectivity

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("wwwWatchdogDelay", rest_val)

    async def get_callbackUrl(self) -> str:
        """
        Returns the callback URL to notify of significant state changes.

        @return a string corresponding to the callback URL to notify of significant state changes

        On failure, throws an exception or returns YNetwork.CALLBACKURL_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("callbackUrl")
        if json_val is None:
            return YNetwork.CALLBACKURL_INVALID
        return json_val

    async def set_callbackUrl(self, newval: str) -> int:
        """
        Changes the callback URL to notify significant state changes. Remember to call the
        saveToFlash() method of the module if the modification must be kept.

        @param newval : a string corresponding to the callback URL to notify significant state changes

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("callbackUrl", rest_val)

    async def get_callbackMethod(self) -> int:
        """
        Returns the HTTP method used to notify callbacks for significant state changes.

        @return a value among YNetwork.CALLBACKMETHOD_POST, YNetwork.CALLBACKMETHOD_GET and
        YNetwork.CALLBACKMETHOD_PUT corresponding to the HTTP method used to notify callbacks for
        significant state changes

        On failure, throws an exception or returns YNetwork.CALLBACKMETHOD_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("callbackMethod")
        if json_val is None:
            return YNetwork.CALLBACKMETHOD_INVALID
        return json_val

    async def set_callbackMethod(self, newval: int) -> int:
        """
        Changes the HTTP method used to notify callbacks for significant state changes.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YNetwork.CALLBACKMETHOD_POST, YNetwork.CALLBACKMETHOD_GET and
        YNetwork.CALLBACKMETHOD_PUT corresponding to the HTTP method used to notify callbacks for
        significant state changes

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("callbackMethod", rest_val)

    async def get_callbackEncoding(self) -> int:
        """
        Returns the encoding standard to use for representing notification values.

        @return a value among YNetwork.CALLBACKENCODING_FORM, YNetwork.CALLBACKENCODING_JSON,
        YNetwork.CALLBACKENCODING_JSON_ARRAY, YNetwork.CALLBACKENCODING_CSV,
        YNetwork.CALLBACKENCODING_YOCTO_API, YNetwork.CALLBACKENCODING_JSON_NUM,
        YNetwork.CALLBACKENCODING_EMONCMS, YNetwork.CALLBACKENCODING_AZURE,
        YNetwork.CALLBACKENCODING_INFLUXDB, YNetwork.CALLBACKENCODING_MQTT,
        YNetwork.CALLBACKENCODING_YOCTO_API_JZON, YNetwork.CALLBACKENCODING_PRTG and
        YNetwork.CALLBACKENCODING_INFLUXDB_V2 corresponding to the encoding standard to use for
        representing notification values

        On failure, throws an exception or returns YNetwork.CALLBACKENCODING_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("callbackEncoding")
        if json_val is None:
            return YNetwork.CALLBACKENCODING_INVALID
        return json_val

    async def set_callbackEncoding(self, newval: int) -> int:
        """
        Changes the encoding standard to use for representing notification values.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YNetwork.CALLBACKENCODING_FORM, YNetwork.CALLBACKENCODING_JSON,
        YNetwork.CALLBACKENCODING_JSON_ARRAY, YNetwork.CALLBACKENCODING_CSV,
        YNetwork.CALLBACKENCODING_YOCTO_API, YNetwork.CALLBACKENCODING_JSON_NUM,
        YNetwork.CALLBACKENCODING_EMONCMS, YNetwork.CALLBACKENCODING_AZURE,
        YNetwork.CALLBACKENCODING_INFLUXDB, YNetwork.CALLBACKENCODING_MQTT,
        YNetwork.CALLBACKENCODING_YOCTO_API_JZON, YNetwork.CALLBACKENCODING_PRTG and
        YNetwork.CALLBACKENCODING_INFLUXDB_V2 corresponding to the encoding standard to use for
        representing notification values

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("callbackEncoding", rest_val)

    async def get_callbackTemplate(self) -> int:
        """
        Returns the activation state of the custom template file to customize callback
        format. If the custom callback template is disabled, it will be ignored even
        if present on the YoctoHub.

        @return either YNetwork.CALLBACKTEMPLATE_OFF or YNetwork.CALLBACKTEMPLATE_ON, according to the
        activation state of the custom template file to customize callback
                format

        On failure, throws an exception or returns YNetwork.CALLBACKTEMPLATE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("callbackTemplate")
        if json_val is None:
            return YNetwork.CALLBACKTEMPLATE_INVALID
        return json_val

    async def set_callbackTemplate(self, newval: int) -> int:
        """
        Enable the use of a template file to customize callbacks format.
        When the custom callback template file is enabled, the template file
        will be loaded for each callback in order to build the data to post to the
        server. If template file does not exist on the YoctoHub, the callback will
        fail with an error message indicating the name of the expected template file.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : either YNetwork.CALLBACKTEMPLATE_OFF or YNetwork.CALLBACKTEMPLATE_ON

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("callbackTemplate", rest_val)

    async def get_callbackCredentials(self) -> str:
        """
        Returns a hashed version of the notification callback credentials if set,
        or an empty string otherwise.

        @return a string corresponding to a hashed version of the notification callback credentials if set,
                or an empty string otherwise

        On failure, throws an exception or returns YNetwork.CALLBACKCREDENTIALS_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("callbackCredentials")
        if json_val is None:
            return YNetwork.CALLBACKCREDENTIALS_INVALID
        return json_val

    async def set_callbackCredentials(self, newval: str) -> int:
        """
        Changes the credentials required to connect to the callback address. The credentials
        must be provided as returned by function get_callbackCredentials,
        in the form username:hash. The method used to compute the hash varies according
        to the the authentication scheme implemented by the callback, For Basic authentication,
        the hash is the MD5 of the string username:password. For Digest authentication,
        the hash is the MD5 of the string username:realm:password. For a simpler
        way to configure callback credentials, use function callbackLogin instead.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the credentials required to connect to the callback address

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("callbackCredentials", rest_val)

    async def callbackLogin(self, username, password) -> int:
        """
        Connects to the notification callback and saves the credentials required to
        log into it. The password is not stored into the module, only a hashed
        copy of the credentials are saved. Remember to call the
        saveToFlash() method of the module if the modification must be kept.

        @param username : username required to log to the callback
        @param password : password required to log to the callback

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = username + ":" + password
        return await self._setAttr("callbackCredentials", rest_val)

    async def get_callbackInitialDelay(self) -> int:
        """
        Returns the initial waiting time before first callback notifications, in seconds.

        @return an integer corresponding to the initial waiting time before first callback notifications, in seconds

        On failure, throws an exception or returns YNetwork.CALLBACKINITIALDELAY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("callbackInitialDelay")
        if json_val is None:
            return YNetwork.CALLBACKINITIALDELAY_INVALID
        return json_val

    async def set_callbackInitialDelay(self, newval: int) -> int:
        """
        Changes the initial waiting time before first callback notifications, in seconds.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : an integer corresponding to the initial waiting time before first callback
        notifications, in seconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("callbackInitialDelay", rest_val)

    async def get_callbackSchedule(self) -> str:
        """
        Returns the HTTP callback schedule strategy, as a text string.

        @return a string corresponding to the HTTP callback schedule strategy, as a text string

        On failure, throws an exception or returns YNetwork.CALLBACKSCHEDULE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("callbackSchedule")
        if json_val is None:
            return YNetwork.CALLBACKSCHEDULE_INVALID
        return json_val

    async def set_callbackSchedule(self, newval: str) -> int:
        """
        Changes the HTTP callback schedule strategy, as a text string.
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.

        @param newval : a string corresponding to the HTTP callback schedule strategy, as a text string

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("callbackSchedule", rest_val)

    async def get_callbackMinDelay(self) -> int:
        """
        Returns the minimum waiting time between two HTTP callbacks, in seconds.

        @return an integer corresponding to the minimum waiting time between two HTTP callbacks, in seconds

        On failure, throws an exception or returns YNetwork.CALLBACKMINDELAY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("callbackMinDelay")
        if json_val is None:
            return YNetwork.CALLBACKMINDELAY_INVALID
        return json_val

    async def set_callbackMinDelay(self, newval: int) -> int:
        """
        Changes the minimum waiting time between two HTTP callbacks, in seconds.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : an integer corresponding to the minimum waiting time between two HTTP callbacks, in seconds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("callbackMinDelay", rest_val)

    async def get_callbackMaxDelay(self) -> int:
        """
        Returns the waiting time between two HTTP callbacks when there is nothing new.

        @return an integer corresponding to the waiting time between two HTTP callbacks when there is nothing new

        On failure, throws an exception or returns YNetwork.CALLBACKMAXDELAY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("callbackMaxDelay")
        if json_val is None:
            return YNetwork.CALLBACKMAXDELAY_INVALID
        return json_val

    async def set_callbackMaxDelay(self, newval: int) -> int:
        """
        Changes the waiting time between two HTTP callbacks when there is nothing new.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : an integer corresponding to the waiting time between two HTTP callbacks when there
        is nothing new

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("callbackMaxDelay", rest_val)

    async def get_poeCurrent(self) -> int:
        """
        Returns the current consumed by the module from Power-over-Ethernet (PoE), in milliamps.
        The current consumption is measured after converting PoE source to 5 Volt, and should
        never exceed 1800 mA.

        @return an integer corresponding to the current consumed by the module from Power-over-Ethernet
        (PoE), in milliamps

        On failure, throws an exception or returns YNetwork.POECURRENT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("poeCurrent")
        if json_val is None:
            return YNetwork.POECURRENT_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YNetworkValueCallback) -> int:
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

    async def useDHCP(self, fallbackIpAddr: str, fallbackSubnetMaskLen: int, fallbackRouter: str) -> int:
        """
        Changes the configuration of the network interface to enable the use of an
        IP address received from a DHCP server. Until an address is received from a DHCP
        server, the module uses the IP parameters specified to this function.
        Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

        @param fallbackIpAddr : fallback IP address, to be used when no DHCP reply is received
        @param fallbackSubnetMaskLen : fallback subnet mask length when no DHCP reply is received, as an
                integer (e.g. 24 means 255.255.255.0)
        @param fallbackRouter : fallback router IP address, to be used when no DHCP reply is received

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_ipConfig("DHCP:%s/%d/%s" % (fallbackIpAddr, fallbackSubnetMaskLen, fallbackRouter))

    async def useDHCPauto(self) -> int:
        """
        Changes the configuration of the network interface to enable the use of an
        IP address received from a DHCP server. Until an address is received from a DHCP
        server, the module uses an IP of the network 169.254.0.0/16 (APIPA).
        Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_ipConfig("DHCP:")

    async def useStaticIP(self, ipAddress: str, subnetMaskLen: int, router: str) -> int:
        """
        Changes the configuration of the network interface to use a static IP address.
        Remember to call the saveToFlash() method and then to reboot the module to apply this setting.

        @param ipAddress : device IP address
        @param subnetMaskLen : subnet mask length, as an integer (e.g. 24 means 255.255.255.0)
        @param router : router IP address (default gateway)

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_ipConfig("STATIC:%s/%d/%s" % (ipAddress, subnetMaskLen, router))

    async def ping(self, host: str) -> str:
        """
        Pings host to test the network connectivity. Sends four ICMP ECHO_REQUEST requests from the
        module to the target host. This method returns a string with the result of the
        4 ICMP ECHO_REQUEST requests.

        @param host : the hostname or the IP address of the target

        @return a string with the result of the ping.
        """
        content: xarray

        content = await self._download("ping.txt?host=%s" % host)
        return content.decode('latin-1')

    async def triggerCallback(self) -> int:
        """
        Trigger an HTTP callback quickly. This function can even be called within
        an HTTP callback, in which case the next callback will be triggered 5 seconds
        after the end of the current callback, regardless if the minimum time between
        callbacks configured in the device.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_callbackMethod(await self.get_callbackMethod())

    async def set_periodicCallbackSchedule(self, interval: str, offset: int) -> int:
        """
        Set up periodic HTTP callbacks (simplified function).

        @param interval : a string representing the callback periodicity, expressed in
                seconds, minutes or hours, eg. "60s", "5m", "1h", "48h".
        @param offset : an integer representing the time offset relative to the period
                when the callback should occur. For instance, if the periodicity is
                24h, an offset of 7 will make the callback occur each day at 7AM.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_callbackSchedule("every %s+%d" % (interval, offset))

    # --- (end of YNetwork implementation)

