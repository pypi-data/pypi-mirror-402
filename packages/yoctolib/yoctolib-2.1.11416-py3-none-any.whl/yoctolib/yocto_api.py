# -*- coding: utf-8 -*-
# *********************************************************************
# *
# * $Id: yocto_api.py 70499 2025-11-25 10:43:01Z mvuilleu $
# *
# * Typed python programming interface; code common to all modules
# *
# * - - - - - - - - - License information: - - - - - - - - -
# *
# *  Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.
# *
# *  Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
# *  non-exclusive license to use, modify, copy and integrate this
# *  file into your software for the sole purpose of interfacing
# *  with Yoctopuce products.
# *
# *  You may reproduce and distribute copies of this file in
# *  source or object form, as long as the sole purpose of this
# *  code is to interface with Yoctopuce products. You must retain
# *  this notice in the distributed source file.
# *
# *  You should refer to Yoctopuce General Terms and Conditions
# *  for additional information regarding your rights and
# *  obligations.
# *
# *  THE SOFTWARE AND DOCUMENTATION ARE PROVIDED 'AS IS' WITHOUT
# *  WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
# *  WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
# *  FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
# *  EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
# *  INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
# *  COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR
# *  SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT
# *  LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
# *  CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
# *  BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
# *  WARRANTY, OR OTHERWISE.
# *
# *********************************************************************/
"""
Yoctopuce library: high-level API for common code used by all devices
version: 2.1.11416
requires: yocto_api_aio
provides: YAPI YModule YFunction YSensor YAPIContext
"""
# Enable forward references
from __future__ import annotations

__all__ = (
    'xarray', 'xbytearray', 'xmemoryview', 'xlist', 'xdict', 'xStringIO', 'xBytesIO',
    'ticks_ms', 'ticks_add', 'ticks_diff', 'ticks_past', 'print_exception',
    'YAPIContext', 'YAPI', 'YRefParam', 'YAPI_Exception', 'YAPI_aio', 'YSyncProxy',
    'YHub', 'YFunction', 'YModule', 'YFirmwareUpdate', 'YSensor', 'YMeasure',  # noqa
    'YDataLogger', 'YDataStream', 'YDataSet', 'YConsolidatedDataSet'  # noqa
)

# IMPORTANT: This file must stay compatible with
# - CPython 3.8 (for backward-compatibility with Windows 7)
# - micropython (for inclusion in VirtualHub/YoctoHub)

import sys, time, math, asyncio

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union, Final
    from collections.abc import Callable, Awaitable, Coroutine

    const = lambda obj: obj
    _IS_MICROPYTHON = False
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is converted into const() expression just before compiling
    _IS_MICROPYTHON: Final[bool] = True  # noqa
    _DYNAMIC_HELPERS: Final[bool] = True  # noqa

from .yocto_api_aio import (
    xarray, xbytearray, xmemoryview, xlist, xdict, xStringIO, xBytesIO,
    ticks_ms, ticks_add, ticks_diff, ticks_past, print_exception,
    YRefParam, YMeasure, YAPI_Exception, YPlugEv,
    YAPIContext as YAPIContext_aio,
    YAPI as YAPI_aio,
    YFunction as YFunction_aio,
    YModule as YModule_aio,
    YHub as YHub_aio,
    YFirmwareUpdate as YFirmwareUpdate_aio,
    YSensor as YSensor_aio,
    YDataStream as YDataStream_aio,
    YDataSet as YDataSet_aio,
    YDataLogger as YDataLogger_aio,
    YConsolidatedDataSet as YConsolidatedDataSet_aio,
)

# Magic parent class to create a synchronous version of an async object
#
# Synchronous methods are created when used for the first time,
# and cached into the sync proxy object
class YSyncProxy:
    # class attributes:
    _proxies = dict()  # dictionary of reusable instances
    _eventloop = None

    # the only attribute is a reference to the async object
    _aio: any

    @staticmethod
    def _run(coroutine: Coroutine):
        eventloop = YSyncProxy._eventloop
        if not eventloop:
            if _IS_MICROPYTHON:
                eventloop = asyncio.get_event_loop()
            else:
                try:
                    eventloop = asyncio.get_running_loop()
                except RuntimeError:
                    eventloop = asyncio.new_event_loop()
            YSyncProxy._eventloop = eventloop
        return eventloop.run_until_complete(coroutine)

    @staticmethod
    def _proxy(subclass, aio_obj):
        if not aio_obj:
            return None
        sync_obj = YSyncProxy._proxies.get(aio_obj)
        if sync_obj is None:
            sync_obj = subclass(aio_obj)
            YSyncProxy._proxies[aio_obj] = sync_obj
        return sync_obj

    @staticmethod
    def _proxyCb(subclass, cb_fun: any):
        if not cb_fun:
            return None
        if _IS_MICROPYTHON:
            return lambda *args: cb_fun(YSyncProxy._proxy(subclass, args[0]), *args[1:])
        else:
            res = lambda *args: cb_fun(YSyncProxy._proxy(subclass, args[0]), *args[1:])
            res.__name__ = cb_fun.__name__
            return res

    def __init__(self, aio_obj):
        self._aio = aio_obj

    if _DYNAMIC_HELPERS:
        def __getattr__(self, attr: str):
            aio_method = getattr(self._aio, attr)
            sync_fun = lambda *args: self._run(aio_method(*args))
            setattr(self, attr, sync_fun)
            return sync_fun


#### Another way to save on RAM by defining methods "on demand":
#
#    def __getattr__(self, attr: str):
#        func = None
#        if attr == "inc":
#            def inc(self):
#                self.x += 1
#            func = inc
#        elif attr == "dec":
#            def dec(self):
#                self.x -= 1
#            func = dec
#        if func:
#            setattr(type(self), attr, func)
#            return lambda *args: func(self, *args)
#        raise AttributeError(attr)
#
####

#################################################################################
#                                                                               #
#                         YAPIContext, YAPI, YHub                               #
#                                                                               #
#################################################################################

# --- (generated code: YAPIContext class start)
# noinspection PyProtectedMember
class YAPIContext(YSyncProxy):
    _aio: YAPIContext_aio
    # --- (end of generated code: YAPIContext class start)
    if not _IS_MICROPYTHON:
        INVALID_STRING: Final[str] = "!INVALID!"
        INVALID_DOUBLE: Final[float] = -math.inf
        MIN_DOUBLE: Final[float] = -math.inf
        MAX_DOUBLE: Final[float] = math.inf
        INVALID_INT: Final[int] = -9999999999
        INVALID_UINT: Final[int] = 9999999999
        INVALID_LONG: Final[int] = -999999999999999999

        # InitAPI constants
        DETECT_NONE: Final[int] = 0
        DETECT_USB: Final[int] = 1
        DETECT_NET: Final[int] = 2
        DETECT_ALL: Final[int] = 3

        # --- (generated code: YAPI definitions)
        # Yoctopuce error codes, used by default as function return value
        SUCCESS: Final[int] = 0                 # everything worked all right
        NOT_INITIALIZED: Final[int] = -1        # call yInitAPI() first !
        INVALID_ARGUMENT: Final[int] = -2       # one of the arguments passed to the function is invalid
        NOT_SUPPORTED: Final[int] = -3          # the operation attempted is (currently) not supported
        DEVICE_NOT_FOUND: Final[int] = -4       # the requested device is not reachable
        VERSION_MISMATCH: Final[int] = -5       # the device firmware is incompatible with this API version
        DEVICE_BUSY: Final[int] = -6            # the device is busy with another task and cannot answer
        TIMEOUT: Final[int] = -7                # the device took too long to provide an answer
        IO_ERROR: Final[int] = -8               # there was an I/O problem while talking to the device
        NO_MORE_DATA: Final[int] = -9           # there is no more data to read from
        EXHAUSTED: Final[int] = -10             # you have run out of a limited resource, check the documentation
        DOUBLE_ACCES: Final[int] = -11          # you have two process that try to access to the same device
        UNAUTHORIZED: Final[int] = -12          # unauthorized access to password-protected device
        RTC_NOT_READY: Final[int] = -13         # real-time clock has not been initialized (or time was lost)
        FILE_NOT_FOUND: Final[int] = -14        # the file is not found
        SSL_ERROR: Final[int] = -15             # Error reported by mbedSSL
        RFID_SOFT_ERROR: Final[int] = -16       # Recoverable error with RFID tag (eg. tag out of reach), check YRfidStatus for details
        RFID_HARD_ERROR: Final[int] = -17       # Serious RFID error (eg. write-protected, out-of-boundary), check YRfidStatus for details
        BUFFER_TOO_SMALL: Final[int] = -18      # The buffer provided is too small
        DNS_ERROR: Final[int] = -19             # Error during name resolutions (invalid hostname or dns communication error)
        SSL_UNK_CERT: Final[int] = -20          # The certificate is not correctly signed by the trusted CA
        UNCONFIGURED: Final[int] = -21          # Remote hub is not yet configured

        # TLS / SSL definitions
        NO_TRUSTED_CA_CHECK: Final[int] = 1     # Disables certificate checking
        NO_EXPIRATION_CHECK: Final[int] = 2     # Disables certificate expiration date checking
        NO_HOSTNAME_CHECK: Final[int] = 4       # Disable hostname checking
        LEGACY: Final[int] = 8                  # Allow non-secure connection (similar to v1.10)
        # --- (end of generated code: YAPI definitions)

    def __init__(self, from_aio: Union[YAPIContext_aio, None] = None):
        if from_aio:
            super().__init__(from_aio)
        else:
            super().__init__(YAPIContext_aio())



    # --- (generated code: YAPIContext implementation)
    def SetDeviceListValidity(self, deviceListValidity: int) -> None:
        """
        Modifies the delay between each forced enumeration of the used YoctoHubs.
        By default, the library performs a full enumeration every 10 seconds.
        To reduce network traffic, you can increase this delay.
        It's particularly useful when a YoctoHub is connected to the GSM network
        where traffic is billed. This parameter doesn't impact modules connected by USB,
        nor the working of module arrival/removal callbacks.
        Note: you must call this function after yInitAPI.

        @param deviceListValidity : nubmer of seconds between each enumeration.
        @noreturn
        """
        return self._aio.SetDeviceListValidity(deviceListValidity)

    def GetDeviceListValidity(self) -> int:
        """
        Returns the delay between each forced enumeration of the used YoctoHubs.
        Note: you must call this function after yInitAPI.

        @return the number of seconds between each enumeration.
        """
        return self._aio.GetDeviceListValidity()

    if not _IS_MICROPYTHON and not _DYNAMIC_HELPERS:
        def DownloadHostCertificate(self, url: str, mstimeout: int) -> str:
            """
            Download the TLS/SSL certificate from the hub. This function allows to download a TLS/SSL certificate to add it
            to the list of trusted certificates using the AddTrustedCertificates method.

            @param url : the root URL of the VirtualHub V2 or HTTP server.
            @param mstimeout : the number of milliseconds available to download the certificate.

            @return a string containing the certificate. In case of error, returns a string starting with "error:".
            """
            return self._run(self._aio.DownloadHostCertificate(url, mstimeout))

    if not _IS_MICROPYTHON:
        def AddTrustedCertificates(self, certificate: str) -> str:
            """
            Adds a TLS/SSL certificate to the list of trusted certificates. By default, the library
            library will reject TLS/SSL connections to servers whose certificate is not known. This function
            function allows to add a list of known certificates. It is also possible to disable the verification
            using the SetNetworkSecurityOptions method.

            @param certificate : a string containing one or more certificates.

            @return an empty string if the certificate has been added correctly.
                    In case of error, returns a string starting with "error:".
            """
            return self._aio.AddTrustedCertificates(certificate)

    if not _IS_MICROPYTHON:
        def SetTrustedCertificatesList(self, certificatePath: str) -> str:
            """
            Set the path of Certificate Authority file on local filesystem. This method takes as a parameter
            the path of a file containing all certificates in PEM format.
            For technical reasons, only one file can be specified. So if you need to connect to several Hubs
            instances with self-signed certificates, you'll need to use
            a single file containing all the certificates end-to-end. Passing a empty string will restore the
            default settings. This option is only supported by PHP library.

            @param certificatePath : the path of the file containing all certificates in PEM format.

            @return an empty string if the certificate has been added correctly.
                    In case of error, returns a string starting with "error:".
            """
            return self._aio.SetTrustedCertificatesList(certificatePath)

    def SetNetworkSecurityOptions(self, opts: int) -> str:
        """
        Enables or disables certain TLS/SSL certificate checks.

        @param opts : The options are YAPI.NO_TRUSTED_CA_CHECK,
                YAPI.NO_EXPIRATION_CHECK, YAPI.NO_HOSTNAME_CHECK.

        @return an empty string if the options are taken into account.
                On error, returns a string beginning with "error:".
        """
        return self._aio.SetNetworkSecurityOptions(opts)

    def SetNetworkTimeout(self, networkMsTimeout: int) -> None:
        """
        Modifies the network connection delay for yRegisterHub() and yUpdateDeviceList().
        This delay impacts only the YoctoHubs and VirtualHub
        which are accessible through the network. By default, this delay is of 20000 milliseconds,
        but depending on your network you may want to change this delay,
        gor example if your network infrastructure is based on a GSM connection.

        @param networkMsTimeout : the network connection delay in milliseconds.
        @noreturn
        """
        return self._aio.SetNetworkTimeout(networkMsTimeout)

    def GetNetworkTimeout(self) -> int:
        """
        Returns the network connection delay for yRegisterHub() and yUpdateDeviceList().
        This delay impacts only the YoctoHubs and VirtualHub
        which are accessible through the network. By default, this delay is of 20000 milliseconds,
        but depending on your network you may want to change this delay,
        for example if your network infrastructure is based on a GSM connection.

        @return the network connection delay in milliseconds.
        """
        return self._aio.GetNetworkTimeout()

    def SetCacheValidity(self, cacheValidityMs: int) -> None:
        """
        Change the validity period of the data loaded by the library.
        By default, when accessing a module, all the attributes of the
        module functions are automatically kept in cache for the standard
        duration (5 ms). This method can be used to change this standard duration,
        for example in order to reduce network or USB traffic. This parameter
        does not affect value change callbacks
        Note: This function must be called after yInitAPI.

        @param cacheValidityMs : an integer corresponding to the validity attributed to the
                loaded function parameters, in milliseconds.
        @noreturn
        """
        return self._aio.SetCacheValidity(cacheValidityMs)

    def GetCacheValidity(self) -> int:
        """
        Returns the validity period of the data loaded by the library.
        This method returns the cache validity of all attributes
        module functions.
        Note: This function must be called after yInitAPI .

        @return an integer corresponding to the validity attributed to the
                loaded function parameters, in milliseconds
        """
        return self._aio.GetCacheValidity()

    # --- (end of generated code: YAPIContext implementation)

    def DisableExceptions(self) -> None:
        """
        Disables the use of exceptions to report runtime errors.
        When exceptions are disabled, every function returns a specific
        error value which depends on its type and which is documented in
        this reference manual.
        """
        return self._aio.DisableExceptions()

    def EnableExceptions(self) -> None:
        """
        Re-enables the use of exceptions for runtime error handling.
        Be aware than when exceptions are enabled, every function that fails
        triggers an exception. If the exception is not caught by the user code,
        it either fires the debugger or aborts (i.e. crash) the program.
        """
        return self._aio.EnableExceptions()

    @staticmethod
    def GetAPIVersion() -> str:
        """
        Returns the version identifier for the Yoctopuce library in use.
        The version is a string in the form "Major.Minor.Build",
        for instance "1.01.5535". For languages using an external
        DLL (for instance C#, VisualBasic or Delphi), the character string
        includes as well the DLL version, for instance
        "1.01.5535 (1.01.5439)".

        If you want to verify in your code that the library version is
        compatible with the version that you have used during development,
        verify that the major number is strictly equal and that the minor
        number is greater or equal. The build number is not relevant
        with respect to the library compatibility.

        @return a character string describing the library version.
        """
        return YAPIContext_aio.GetAPIVersion()

    if not _DYNAMIC_HELPERS:
        def InitAPI(self, mode: int, errmsg: YRefParam = None) -> int:
            """
            Initializes the Yoctopuce programming library explicitly.
            It is not strictly needed to call yInitAPI(), as the library is
            automatically  initialized when calling yRegisterHub() for the
            first time.

            When YAPI.DETECT_NONE is used as detection mode,
            you must explicitly use yRegisterHub() to point the API to the
            VirtualHub on which your devices are connected before trying to access them.

            @param mode : an integer corresponding to the type of automatic
                    device detection to use. Possible values are
                    YAPI.DETECT_NONE, YAPI.DETECT_USB, YAPI.DETECT_NET,
                    and YAPI.DETECT_ALL.
            @param errmsg : a string passed by reference to receive any error message.

            @return YAPI.SUCCESS when the call succeeds.

            On failure returns a negative error code.
            """
            return self._run(self._aio.InitAPI(mode, errmsg))

        def FreeAPI(self) -> None:
            """
            Waits for all pending communications with Yoctopuce devices to be
            completed then frees dynamically allocated resources used by
            the Yoctopuce library.

            From an operating system standpoint, it is generally not required to call
            this function since the OS will automatically free allocated resources
            once your program is completed. However, there are two situations when
            you may really want to use that function:

            - Free all dynamically allocated memory blocks in order to
            track a memory leak.

            - Send commands to devices right before the end
            of the program. Since commands are sent in an asynchronous way
            the program could exit before all commands are effectively sent.

            You should not call any other library function after calling
            yFreeAPI(), or your program will crash.
            """
            return self._run(self._aio.FreeAPI())

        def RegisterHub(self, url: str, errmsg: YRefParam = None) -> int:
            """
            Set up the Yoctopuce library to use modules connected on a given machine. Idealy this
            call will be made once at the begining of your application.  The
            parameter will determine how the API will work. Use the following values:

            <b>usb</b>: When the usb keyword is used, the API will work with
            devices connected directly to the USB bus. Some programming languages such a JavaScript,
            PHP, and Java don't provide direct access to USB hardware, so usb will
            not work with these. In this case, use a VirtualHub or a networked YoctoHub (see below).

            <b><i>x.x.x.x</i></b> or <b><i>hostname</i></b>: The API will use the devices connected to the
            host with the given IP address or hostname. That host can be a regular computer
            running a <i>native VirtualHub</i>, a <i>VirtualHub for web</i> hosted on a server,
            or a networked YoctoHub such as YoctoHub-Ethernet or
            YoctoHub-Wireless. If you want to use the VirtualHub running on you local
            computer, use the IP address 127.0.0.1. If the given IP is unresponsive, yRegisterHub
            will not return until a time-out defined by ySetNetworkTimeout has elapsed.
            However, it is possible to preventively test a connection  with yTestHub.
            If you cannot afford a network time-out, you can use the non-blocking yPregisterHub
            function that will establish the connection as soon as it is available.


            <b>callback</b>: that keyword make the API run in "<i>HTTP Callback</i>" mode.
            This a special mode allowing to take control of Yoctopuce devices
            through a NAT filter when using a VirtualHub or a networked YoctoHub. You only
            need to configure your hub to call your server script on a regular basis.
            This mode is currently available for PHP and Node.JS only.

            Be aware that only one application can use direct USB access at a
            given time on a machine. Multiple access would cause conflicts
            while trying to access the USB modules. In particular, this means
            that you must stop the VirtualHub software before starting
            an application that uses direct USB access. The workaround
            for this limitation is to set up the library to use the VirtualHub
            rather than direct USB access.

            If access control has been activated on the hub, virtual or not, you want to
            reach, the URL parameter should look like:

            http://username:password@address:port

            You can call <i>RegisterHub</i> several times to connect to several machines. On
            the other hand, it is useless and even counterproductive to call <i>RegisterHub</i>
            with to same address multiple times during the life of the application.

            @param url : a string containing either "usb","callback" or the
                    root URL of the hub to monitor
            @param errmsg : a string passed by reference to receive any error message.

            @return YAPI.SUCCESS when the call succeeds.

            On failure returns a negative error code.
            """
            return self._run(self._aio.RegisterHub(url, errmsg))

        def PreregisterHub(self, url: str, errmsg: YRefParam = None) -> int:
            """
            Fault-tolerant alternative to yRegisterHub(). This function has the same
            purpose and same arguments as yRegisterHub(), but does not trigger
            an error when the selected hub is not available at the time of the function call.
            If the connexion cannot be established immediately, a background task will automatically
            perform periodic retries. This makes it possible to register a network hub independently of the current
            connectivity, and to try to contact it only when a device is actively needed.

            @param url : a string containing either "usb","callback" or the
                    root URL of the hub to monitor
            @param errmsg : a string passed by reference to receive any error message.

            @return YAPI.SUCCESS when the call succeeds.

            On failure returns a negative error code.
            """
            return self._run(self._aio.PreregisterHub(url, errmsg))

        def UnregisterHub(self, url: str):
            """
            Set up the Yoctopuce library to no more use modules connected on a previously
            registered machine with RegisterHub.

            @param url : a string containing either "usb" or the
                    root URL of the hub to monitor
            """
            return self._run(self._aio.UnregisterHub(url))

        def TestHub(self, url: str, mstimeout: int, errmsg: YRefParam = None) -> int:
            """
            Test if the hub is reachable. This method do not register the hub, it only test if the
            hub is usable. The url parameter follow the same convention as the yRegisterHub
            method. This method is useful to verify the authentication parameters for a hub. It
            is possible to force this method to return after mstimeout milliseconds.

            @param url : a string containing either "usb","callback" or the
                    root URL of the hub to monitor
            @param mstimeout : the number of millisecond available to test the connection.
            @param errmsg : a string passed by reference to receive any error message.

            @return YAPI.SUCCESS when the call succeeds.

            On failure returns a negative error code.
            """
            return self._run(self._aio.TestHub(url, mstimeout, errmsg))

        def TriggerHubDiscovery(self, errmsg: YRefParam = None) -> int:
            """
            Force a hub discovery, if a callback as been registered with yRegisterHubDiscoveryCallback it
            will be called for each net work hub that will respond to the discovery.

            @param errmsg : a string passed by reference to receive any error message.

            @return YAPI.SUCCESS when the call succeeds.
                    On failure returns a negative error code.
            """
            return self._run(self._aio.TriggerHubDiscovery(errmsg))

    def UpdateDeviceList(self, errmsg: YRefParam = None) -> int:
        """
        Triggers a (re)detection of connected Yoctopuce modules.
        The library searches the machines or USB ports previously registered using
        yRegisterHub(), and invokes any user-defined callback function
        in case a change in the list of connected devices is detected.

        This function can be called as frequently as desired to refresh the device list
        and to make the application aware of hot-plug events. However, since device
        detection is quite a heavy process, UpdateDeviceList shouldn't be called more
        than once every two seconds.

        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        # Note: this function cannot simply delegate globally to the async object,
        #       as callbacks could cause reentrant calls to the async scheduler
        res: int = self._run(self._aio._updateDeviceList_internal(False, errmsg))
        if res != YAPI.SUCCESS:
            return res
        # after processing all hubs, invoke pending callbacks if required
        nbEvents = len(self._aio._pendingCallbacks)
        for i in range(nbEvents):
            evt: YPlugEv = self._aio._pendingCallbacks[i]
            try:
                retval: Union[Coroutine, None] = self._aio._handlePlugEvent(evt)
                if asyncio.iscoroutine(retval):
                    self._run(retval)
            # noinspection PyBroadException
            except Exception as exc:
                self._aio._logCbError(evt.eventType, self, exc)
        del self._aio._pendingCallbacks[0:nbEvents]
        return YAPI.SUCCESS

    def HandleEvents(self, errmsg: YRefParam = None) -> int:
        """
        Maintains the device-to-library communication channel.
        If your program includes significant loops, you may want to include
        a call to this function to make sure that the library takes care of
        the information pushed by the modules on the communication channels.
        This is not strictly necessary, but it may improve the reactivity
        of the library for the following commands.

        This function may signal an error in case there is a communication problem
        while contacting a module.

        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        # Note: this function cannot simply delegate globally to the async object,
        #       as callbacks could cause reentrant calls to the async scheduler
        try:
            self._run(self._aio._updateDeviceList_internal(False, errmsg))
            evb: Union[bytearray, None] = self._aio._nextDataEvent()
            # Handle ALL pending events
            while evb:
                recipient = None
                try:
                    recipient, retval = self._aio._handleEvent(evb)
                    if asyncio.iscoroutine(retval):
                        self._run(retval)
                # noinspection PyBroadException
                except Exception as exc:
                    self._aio._logCbError(evb[0], recipient, exc)
                evb = self._aio._nextDataEvent()
        except YAPI_Exception as e:
            errmsg.value = e.errorMessage
            return e.errorType
        return YAPI.SUCCESS

    def Sleep(self, ms_duration: int, errmsg: YRefParam = None) -> int:
        """
        Pauses the execution flow for a specified duration.
        This function implements a passive waiting loop, meaning that it does not
        consume CPU cycles significantly. The processor is left available for
        other threads and processes. During the pause, the library nevertheless
        reads from time to time information from the Yoctopuce modules by
        calling yHandleEvents(), in order to stay up-to-date.

        This function may signal an error in case there is a communication problem
        while contacting a module.

        @param ms_duration : an integer corresponding to the duration of the pause,
                in milliseconds.
        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        # Note: this function cannot simply delegate globally to the async object,
        #       as callbacks could cause reentrant calls to the async scheduler
        try:
            evb: Union[bytearray, None] = self._aio._nextDataEvent()
            endTicks: int = ticks_add(ticks_ms(), ms_duration)
            remaining: int = 1
            # Handle as many pending events as possible in given time (at least one)
            while remaining > 0:
                if evb:
                    # handle one event
                    self._run(self._aio._updateDeviceList_internal(False, errmsg))
                    recipient = None
                    try:
                        recipient, retval = self._aio._handleEvent(evb)
                        if asyncio.iscoroutine(retval):
                            self._run(retval)
                    # noinspection PyBroadException
                    except Exception as exc:
                        self._aio._logCbError(evb[0], recipient, exc)
                remaining = ticks_diff(endTicks, ticks_ms())
                if remaining <= 0:
                    # time expired during event processing
                    return YAPI.SUCCESS
                # get next event
                evb = self._aio._nextDataEvent()
                if not evb:
                    if _IS_MICROPYTHON:
                        self._run(asyncio.sleep_ms(min(remaining, 10)))  # noqa
                    else:
                        self._run(asyncio.sleep(min(remaining, 10) / 1000.0))
                    remaining = ticks_diff(endTicks, ticks_ms())
        except YAPI_Exception as e:
            errmsg.value = e.errorMessage
            return e.errorType
        return YAPI.SUCCESS

    @staticmethod
    def GetTickCount() -> int:
        """
        Returns the current value of a monotone millisecond-based time counter.
        This counter can be used to compute delays in relation with
        Yoctopuce devices, which also uses the millisecond as timebase.

        @return a long integer corresponding to the millisecond counter.
        """
        if _IS_MICROPYTHON:
            return time.time_ms()  # noqa
        else:
            return round(time.time() * 1000)

    @staticmethod
    def CheckLogicalName(name: str) -> bool:
        """
        Checks if a given string is valid as logical name for a module or a function.
        A valid logical name has a maximum of 19 characters, all among
        A...Z, a...z, 0...9, _, and -.
        If you try to configure a logical name with an incorrect string,
        the invalid characters are ignored.

        @param name : a string containing the name to check.

        @return true if the name is valid, false otherwise.
        """
        return YAPIContext_aio.CheckLogicalName(name)

    def RegisterDeviceArrivalCallback(self, arrivalCallback: YDeviceUpdateCallback):
        """
        Register a callback function, to be called each time
        a device is plugged. This callback will be invoked while yUpdateDeviceList
        is running. You will have to call this function on a regular basis.

        @param arrivalCallback : a procedure taking a YModule parameter, or None
                to unregister a previously registered  callback.
        """
        return  self._run(self._aio.RegisterDeviceArrivalCallback(self._proxyCb(YModule, arrivalCallback)))

    def RegisterDeviceChangeCallback(self, changeCallback: YDeviceUpdateCallback):
        return self._run(self._aio.RegisterDeviceChangeCallback(self._proxyCb(YModule, changeCallback)))

    def RegisterDeviceRemovalCallback(self, removalCallback: YDeviceUpdateCallback):
        """
        Register a callback function, to be called each time
        a device is unplugged. This callback will be invoked while yUpdateDeviceList
        is running. You will have to call this function on a regular basis.

        @param removalCallback : a procedure taking a YModule parameter, or None
                to unregister a previously registered  callback.
        """
        return  self._run(self._aio.RegisterDeviceRemovalCallback(self._proxyCb(YModule, removalCallback)))

    def RegisterHubDiscoveryCallback(self, hubDiscoveryCallback):
        """
        Register a callback function, to be called each time an Network Hub send
        an SSDP message. The callback has two string parameter, the first one
        contain the serial number of the hub and the second contain the URL of the
        network hub (this URL can be passed to RegisterHub). This callback will be invoked
        while yUpdateDeviceList is running. You will have to call this function on a regular basis.

        @param hubDiscoveryCallback : a procedure taking two string parameter, the serial
                number and the hub URL. Use None to unregister a previously registered  callback.
        """
        return  self._run(self._aio.RegisterHubDiscoveryCallback(hubDiscoveryCallback))

    def RegisterLogFunction(self, logfun: YLogCallback):
        """
        Registers a log callback function. This callback will be called each time
        the API have something to say. Quite useful to debug the API.

        @param logfun : a procedure taking a string parameter, or None
                to unregister a previously registered  callback.
        """
        return self._aio.RegisterLogFunction(logfun)


YAPI: YAPIContext = YAPIContext(YAPI_aio)

# --- (generated code: YHub class start)
# noinspection PyProtectedMember
class YHub(YSyncProxy):
    _aio: YHub_aio
    # --- (end of generated code: YHub class start)

        # --- (generated code: YHub implementation)
    def get_registeredUrl(self) -> str:
        """
        Returns the URL that has been used first to register this hub.
        """
        return self._aio.get_registeredUrl()

    def get_knownUrls(self) -> list[str]:
        """
        Returns all known URLs that have been used to register this hub.
        URLs are pointing to the same hub when the devices connected
        are sharing the same serial number.
        """
        return self._aio.get_knownUrls()

    def get_connectionUrl(self) -> str:
        """
        Returns the URL currently in use to communicate with this hub.
        """
        return self._aio.get_connectionUrl()

    def get_connectionState(self) -> int:
        """
        Returns the state of the connection with this hub. (TRYING, CONNECTED, RECONNECTING, ABORTED, UNREGISTERED)
        """
        return self._aio.get_connectionState()

    def get_serialNumber(self) -> str:
        """
        Returns the hub serial number, if the hub was already connected once.
        """
        return self._aio.get_serialNumber()

    if not _DYNAMIC_HELPERS:
        def isInUse(self) -> bool:
            """
            Tells if this hub is still registered within the API.

            @return true if the hub has not been unregistered.
            """
            return self._run(self._aio.isInUse())

    if not _DYNAMIC_HELPERS:
        def isOnline(self) -> bool:
            """
            Tells if there is an active communication channel with this hub.

            @return true if the hub is currently connected.
            """
            return self._run(self._aio.isOnline())

    if not _DYNAMIC_HELPERS:
        def isReadOnly(self) -> bool:
            """
            Tells if write access on this hub is blocked. Return true if it
            is not possible to change attributes on this hub

            @return true if it is not possible to change attributes on this hub.
            """
            return self._run(self._aio.isReadOnly())

    def set_networkTimeout(self, networkMsTimeout: int) -> None:
        """
        Modifies tthe network connection delay for this hub.
        The default value is inherited from ySetNetworkTimeout
        at the time when the hub is registered, but it can be updated
        afterward for each specific hub if necessary.

        @param networkMsTimeout : the network connection delay in milliseconds.
        @noreturn
        """
        return self._aio.set_networkTimeout(networkMsTimeout)

    def get_networkTimeout(self) -> int:
        """
        Returns the network connection delay for this hub.
        The default value is inherited from ySetNetworkTimeout
        at the time when the hub is registered, but it can be updated
        afterward for each specific hub if necessary.

        @return the network connection delay in milliseconds.
        """
        return self._aio.get_networkTimeout()

    def get_errorType(self) -> int:
        """
        Returns the numerical error code of the latest error with the hub.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a number corresponding to the code of the latest error that occurred while
                using the hub object
        """
        return self._aio.get_errorType()

    def get_errorMessage(self) -> str:
        """
        Returns the error message of the latest error with the hub.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a string corresponding to the latest error message that occured while
                using the hub object
        """
        return self._aio.get_errorMessage()

    def get_userData(self) -> Any:
        """
        Returns the value of the userData attribute, as previously stored
        using method set_userData.
        This attribute is never touched directly by the API, and is at
        disposal of the caller to store a context.

        @return the object stored previously by the caller.
        """
        return self._aio.get_userData()

    def set_userData(self, data: Any) -> None:
        """
        Stores a user context provided as argument in the userData
        attribute of the function.
        This attribute is never touched by the API, and is at
        disposal of the caller to store a context.

        @param data : any kind of object to be stored
        @noreturn
        """
        return self._aio.set_userData(data)

    @classmethod
    def FirstHubInUse(cls, ) -> Union[YHub, None]:
        """
        Starts the enumeration of hubs currently in use by the API.
        Use the method YHub.nextHubInUse() to iterate on the
        next hubs.

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return cls._proxy(cls, YHub_aio.FirstHubInUse())

    @classmethod
    def FirstHubInUseInContext(cls, yctx: YAPIContext) -> Union[YHub, None]:
        """
        Starts the enumeration of hubs currently in use by the API
        in a given YAPI context.
        Use the method YHub.nextHubInUse() to iterate on the
        next hubs.

        @param yctx : a YAPI context

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return cls._proxy(cls, YHub_aio.FirstHubInUseInContext(yctx))

    @classmethod
    def FindHubInUse(cls, url: str) -> Union[YHub, None]:
        """
        Retrieves hub for a given identifier. The identifier can be the URL or the
        serial of the hub.

        @param url : The url or serial of the hub.

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return cls._proxy(cls, cls._run(YHub_aio.FindHubInUse(url)))

    @classmethod
    def FindHubInUseInContext(cls, yctx: YAPIContext, url: str) -> Union[YHub, None]:
        """
        Retrieves hub for a given identifier in a given YAPI context. The identifier can be the URL or the
        serial of the hub.

        @param yctx : a YAPI context
        @param url : The url or serial of the hub.

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return cls._proxy(cls, cls._run(YHub_aio.FindHubInUseInContext(yctx, url)))

    def nextHubInUse(self) -> Union[YHub, None]:
        """
        Continues the module enumeration started using YHub.FirstHubInUse().
        Caution: You can't make any assumption about the order of returned hubs.

        @return a pointer to a YHub object, corresponding to
                the next hub currently in use, or a None pointer
                if there are no more hubs to enumerate.
        """
        return self._proxy(type(self), self._aio.nextHubInUse())

    # --- (end of generated code: YHub implementation)


#################################################################################
#                                                                               #
#                                YFunction                                      #
#                                                                               #
#################################################################################

# --- (generated code: YFunction class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YFunctionValueCallback = Union[Callable[['YFunction', str], Any], None]
    except TypeError:
        YFunctionValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YFunction(YSyncProxy):
    """
    This is the parent class for all public objects representing device functions documented in
    the high-level programming API. This abstract class does all the real job, but without
    knowledge of the specific function attributes.

    Instantiating a child class of YFunction does not cause any communication.
    The instance simply keeps track of its function identifier, and will dynamically bind
    to a matching device at the time it is really being used to read or set an attribute.
    In order to allow true hot-plug replacement of one device by another, the binding stay
    dynamic through the life of the object.

    The YFunction class implements a generic high-level cache for the attribute values of
    the specified function, pre-parsed from the REST API string.

    """
    _aio: YFunction_aio
    # --- (end of generated code: YFunction class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YFunction return codes)
        LOGICALNAME_INVALID: Final[str] = YAPI.INVALID_STRING
        ADVERTISEDVALUE_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of generated code: YFunction return codes)

    def __repr__(self) -> str:
        return "Y%s('%s')" % (self._className, self._func)

    def get_userData(self) -> Any:
        """
        Returns the value of the userData attribute, as previously stored using method
        set_userData.
        This attribute is never touched directly by the API, and is at disposal of the caller to
        store a context.

        @return the object stored previously by the caller.
        """
        return self._aio.get_userData()

    def set_userData(self, data: Any) -> None:
        """
        Stores a user context provided as argument in the userData attribute of the function.
        This attribute is never touched by the API, and is at disposal of the caller to store a context.

        @param data : any kind of object to be stored
        @noreturn
        """
        self._aio.set_userData(data)

    def get_friendlyName(self) -> str:
        """
        Returns a global identifier of the function in the format MODULE_NAME&#46;FUNCTION_NAME.
        The returned string uses the logical names of the module and of the function if they are defined,
        otherwise the serial number of the module and the hardware identifier of the function
        (for example: MyCustomName.relay1)

        @return a string that uniquely identifies the function using logical names
                (ex: MyCustomName.relay1)

        On failure, throws an exception or returns  YFunction.FRIENDLYNAME_INVALID.
        """
        return self._aio.get_friendlyName()

    # --- (generated code: YFunction implementation)

    @classmethod
    def FindFunction(cls, func: str) -> YFunction:
        """
        Retrieves a function for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YFunction.isOnline() to test if the function is
        indeed online at a given time. In case of ambiguity when looking for
        a function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the function, for instance
                MyDevice..

        @return a YFunction object allowing you to drive the function.
        """
        return cls._proxy(cls, YFunction_aio.FindFunctionInContext(YAPI_aio, func))

    @classmethod
    def FindFunctionInContext(cls, yctx: YAPIContext, func: str) -> YFunction:
        """
        Retrieves a function for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YFunction.isOnline() to test if the function is
        indeed online at a given time. In case of ambiguity when looking for
        a function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the function, for instance
                MyDevice..

        @return a YFunction object allowing you to drive the function.
        """
        return cls._proxy(cls, YFunction_aio.FindFunctionInContext(yctx._aio, func))

    @classmethod
    def FirstFunction(cls) -> Union[YFunction, None]:
        """
        comment from .yc definition
        """
        return cls._proxy(cls, YFunction_aio.FirstFunctionInContext(YAPI_aio))

    @classmethod
    def FirstFunctionInContext(cls, yctx: YAPIContext) -> Union[YFunction, None]:
        """
        comment from .yc definition
        """
        return cls._proxy(cls, YFunction_aio.FirstFunctionInContext(yctx._aio))

    def nextFunction(self) -> Union[YFunction, None]:
        """
        comment from .yc definition
        """
        return self._proxy(type(self), self._aio.nextFunction())

    if not _DYNAMIC_HELPERS:
        def get_logicalName(self) -> str:
            """
            Returns the logical name of the function.

            @return a string corresponding to the logical name of the function

            On failure, throws an exception or returns YFunction.LOGICALNAME_INVALID.
            """
            return self._run(self._aio.get_logicalName())

    if not _DYNAMIC_HELPERS:
        def set_logicalName(self, newval: str) -> int:
            """
            Changes the logical name of the function. You can use yCheckLogicalName()
            prior to this call to make sure that your parameter is valid.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : a string corresponding to the logical name of the function

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_logicalName(newval))

    if not _DYNAMIC_HELPERS:
        def get_advertisedValue(self) -> str:
            """
            Returns a short string representing the current state of the function.

            @return a string corresponding to a short string representing the current state of the function

            On failure, throws an exception or returns YFunction.ADVERTISEDVALUE_INVALID.
            """
            return self._run(self._aio.get_advertisedValue())

    if not _DYNAMIC_HELPERS:
        def set_advertisedValue(self, newval: str) -> int:
            return self._run(self._aio.set_advertisedValue(newval))

    if not _DYNAMIC_HELPERS:
        def muteValueCallbacks(self) -> int:
            """
            Disables the propagation of every new advertised value to the parent hub.
            You can use this function to save bandwidth and CPU on computers with limited
            resources, or to prevent unwanted invocations of the HTTP callback.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.muteValueCallbacks())

    if not _DYNAMIC_HELPERS:
        def unmuteValueCallbacks(self) -> int:
            """
            Re-enables the propagation of every new advertised value to the parent hub.
            This function reverts the effect of a previous call to muteValueCallbacks().
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.unmuteValueCallbacks())

    if not _DYNAMIC_HELPERS:
        def loadAttribute(self, attrName: str) -> str:
            """
            Returns the current value of a single function attribute, as a text string, as quickly as
            possible but without using the cached value.

            @param attrName : the name of the requested attribute

            @return a string with the value of the the attribute

            On failure, throws an exception or returns an empty string.
            """
            return self._run(self._aio.loadAttribute(attrName))

    if not _DYNAMIC_HELPERS:
        def isReadOnly(self) -> bool:
            """
            Indicates whether changes to the function are prohibited or allowed.
            Returns true if the function is blocked by an admin password
            or if the function is not available.

            @return true if the function is write-protected or not online.
            """
            return self._run(self._aio.isReadOnly())

    if not _DYNAMIC_HELPERS:
        def get_serialNumber(self) -> str:
            """
            Returns the serial number of the module, as set by the factory.

            @return a string corresponding to the serial number of the module, as set by the factory.

            On failure, throws an exception or returns YFunction.SERIALNUMBER_INVALID.
            """
            return self._run(self._aio.get_serialNumber())

    # --- (end of generated code: YFunction implementation)

    if not _DYNAMIC_HELPERS:
        def get_hardwareId(self) -> str:
            """
            Returns the unique hardware identifier of the function in the form SERIAL.FUNCTIONID.
            The unique hardware identifier is composed of the device serial
            number and of the hardware identifier of the function (for example RELAYLO1-123456.relay1).

            @return a string that uniquely identifies the function (ex: RELAYLO1-123456.relay1)

            On failure, throws an exception or returns  YFunction.HARDWAREID_INVALID.
            """
            return self._run(self._aio.get_hardwareId())

    if not _DYNAMIC_HELPERS:
        def get_functionId(self) -> str:
            """
            Returns the hardware identifier of the function, without reference to the module. For example
            relay1

            @return a string that identifies the function (ex: relay1)

            On failure, throws an exception or returns  YFunction.FUNCTIONID_INVALID.
            """
            return self._run(self._aio.get_functionId())

    if not _DYNAMIC_HELPERS:
        def isOnline(self) -> bool:
            """
            Checks if the function is currently reachable, without raising any error.
            If there is a cached value for the function in cache, that has not yet
            expired, the device is considered reachable.
            No exception is raised if there is an error while trying to contact the
            device hosting the function.

            @return true if the function can be reached, and false otherwise
            """
            return self._run(self._aio.isOnline())

    def get_errorType(self) -> int:
        """
        Returns the numerical error code of the latest error with the function.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a number corresponding to the code of the latest error that occurred while
                using the function object
        """
        return self._aio.get_errorType()

    def get_errorMessage(self) -> str:
        """
        Returns the error message of the latest error with the function.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a string corresponding to the latest error message that occured while
                using the function object
        """
        return self._aio.get_errorMessage()

    if not _DYNAMIC_HELPERS:
        def clearCache(self):
            """
            Invalidates the cache. Invalidates the cache of the function attributes. Forces the
            next call to get_xxx() or loadxxx() to use values that come from the device.

            @noreturn
            """
            return self._run(self._aio.clearCache())

    if not _DYNAMIC_HELPERS:
        def load(self, msValidity: int) -> int:
            """
            Preloads the function cache with a specified validity duration.
            By default, whenever accessing a device, all function attributes
            are kept in cache for the standard duration (5 ms). This method can be
            used to temporarily mark the cache as valid for a longer period, in order
            to reduce network traffic for instance.

            @param msValidity : an integer corresponding to the validity attributed to the
                    loaded function parameters, in milliseconds

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.load(msValidity))

    def get_module(self) -> YModule:
        """
        Gets the YModule object for the device on which the function is located.
        If the function cannot be located on any module, the returned instance of
        YModule is not shown as on-line.

        @return an instance of YModule
        """
        return YModule._proxy(YModule, self._run(self._aio.get_module()))

    def registerValueCallback(self, callback: YFunctionValueCallback) -> int:
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
        # Note: this function cannot simply delegate globally to the async object,
        #       as callbacks could cause reentrant calls to the async scheduler
        val: str = self._run(self._aio._updateValueCallback(self._proxyCb(type(self), callback)))
        if val:
            # Immediately invoke value callback with current value
            retval = self._aio._valueCallback(self._aio, val)
            if asyncio.iscoroutine(retval):
                self._run(retval)
        return YAPI.SUCCESS

    def _download(self, pathname: str) -> xarray:
        return self._run(self._aio._download(pathname))


#################################################################################
#                                                                               #
#                      YModule, YFirmwareUpdate                                 #
#                                                                               #
#################################################################################

# Callback function types
if not _IS_MICROPYTHON:
    try:
        YProgressCallback = Union[Callable[[int, str], None], None]
        YCalibrationCallback = Union[Callable[[float, int, list[float], list[float], list[float]], float], None]
        YLogCallback = Union[Callable[[str], Awaitable[None]], None]
        YHubDiscoveryCallback = Union[Callable[[str, Union[str, None]], Awaitable[None]], None]
        YDeviceUpdateCallback = Union[Callable[["YModule"], Awaitable[None]], None]
        YDeviceLogCallback = Union[Callable[["YModule", str], Awaitable[None]], None]
        YModuleBeaconCallback = Union[Callable[["YModule", int], Awaitable[None]], None]
    except TypeError:
        YProgressCallback = Union[Callable, None]
        YCalibrationCallback = Union[Callable, None]
        YLogCallback = Union[Callable, None]
        YHubDiscoveryCallback = Union[Callable, None]
        YDeviceUpdateCallback = Union[Callable, None]
        YDeviceLogCallback = Union[Callable, None]
        YModuleBeaconCallback = Union[Callable, None]
    YModuleLogCallback = YDeviceLogCallback
    YModuleConfigChangeCallback = YDeviceUpdateCallback


# --- (generated code: YModule class start)
# noinspection PyRedundantParentheses
# noinspection PyUnusedLocal
# noinspection PyProtectedMember
class YModule(YFunction):
    """
    The YModule class can be used with all Yoctopuce USB devices.
    It can be used to control the module global parameters, and
    to enumerate the functions provided by each module.

    """
    _aio: YModule_aio
    # --- (end of generated code: YModule class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YModule return codes)
        PRODUCTNAME_INVALID: Final[str] = YAPI.INVALID_STRING
        SERIALNUMBER_INVALID: Final[str] = YAPI.INVALID_STRING
        PRODUCTID_INVALID: Final[int] = YAPI.INVALID_UINT
        PRODUCTRELEASE_INVALID: Final[int] = YAPI.INVALID_UINT
        FIRMWARERELEASE_INVALID: Final[str] = YAPI.INVALID_STRING
        LUMINOSITY_INVALID: Final[int] = YAPI.INVALID_UINT
        UPTIME_INVALID: Final[int] = YAPI.INVALID_LONG
        USBCURRENT_INVALID: Final[int] = YAPI.INVALID_UINT
        REBOOTCOUNTDOWN_INVALID: Final[int] = YAPI.INVALID_INT
        USERVAR_INVALID: Final[int] = YAPI.INVALID_INT
        PERSISTENTSETTINGS_LOADED: Final[int] = 0
        PERSISTENTSETTINGS_SAVED: Final[int] = 1
        PERSISTENTSETTINGS_MODIFIED: Final[int] = 2
        PERSISTENTSETTINGS_INVALID: Final[int] = -1
        BEACON_OFF: Final[int] = 0
        BEACON_ON: Final[int] = 1
        BEACON_INVALID: Final[int] = -1
        # --- (end of generated code: YModule return codes)

    # --- (generated code: YModule implementation)

    @classmethod
    def FindModule(cls, func: str) -> YModule:
        """
        Allows you to find a module from its serial number or from its logical name.

        This function does not require that the module is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YModule.isOnline() to test if the module is
        indeed online at a given time. In case of ambiguity when looking for
        a module by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.


        If a call to this object's is_online() method returns FALSE although
        you are certain that the device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string containing either the serial number or
                the logical name of the desired module

        @return a YModule object allowing you to drive the module
                or get additional information on the module.
        """
        return cls._proxy(cls, YModule_aio.FindModuleInContext(YAPI_aio, func))

    @classmethod
    def FindModuleInContext(cls, yctx: YAPIContext, func: str) -> YModule:
        """
        Retrieves a module for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the module is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YModule.isOnline() to test if the module is
        indeed online at a given time. In case of ambiguity when looking for
        a module by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the module, for instance
                MyDevice.module.

        @return a YModule object allowing you to drive the module.
        """
        return cls._proxy(cls, YModule_aio.FindModuleInContext(yctx._aio, func))

    @classmethod
    def FirstModule(cls) -> Union[YModule, None]:
        """
        Starts the enumeration of modules currently accessible.
        Use the method YModule.nextModule() to iterate on the
        next modules.

        @return a pointer to a YModule object, corresponding to
                the first module currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YModule_aio.FirstModuleInContext(YAPI_aio))

    @classmethod
    def FirstModuleInContext(cls, yctx: YAPIContext) -> Union[YModule, None]:
        """
        comment from .yc definition
        """
        return cls._proxy(cls, YModule_aio.FirstModuleInContext(yctx._aio))

    def nextModule(self) -> Union[YModule, None]:
        """
        Continues the module enumeration started using yFirstModule().
        Caution: You can't make any assumption about the returned modules order.
        If you want to find a specific module, use Module.findModule()
        and a hardwareID or a logical name.

        @return a pointer to a YModule object, corresponding to
                the next module found, or a None pointer
                if there are no more modules to enumerate.
        """
        return self._proxy(type(self), self._aio.nextModule())

    if not _DYNAMIC_HELPERS:
        def get_productName(self) -> str:
            """
            Returns the commercial name of the module, as set by the factory.

            @return a string corresponding to the commercial name of the module, as set by the factory

            On failure, throws an exception or returns YModule.PRODUCTNAME_INVALID.
            """
            return self._run(self._aio.get_productName())

    if not _DYNAMIC_HELPERS:
        def get_serialNumber(self) -> str:
            """
            Returns the serial number of the module, as set by the factory.

            @return a string corresponding to the serial number of the module, as set by the factory

            On failure, throws an exception or returns YModule.SERIALNUMBER_INVALID.
            """
            return self._run(self._aio.get_serialNumber())

    if not _DYNAMIC_HELPERS:
        def get_productId(self) -> int:
            """
            Returns the USB device identifier of the module.

            @return an integer corresponding to the USB device identifier of the module

            On failure, throws an exception or returns YModule.PRODUCTID_INVALID.
            """
            return self._run(self._aio.get_productId())

    if not _DYNAMIC_HELPERS:
        def get_productRelease(self) -> int:
            """
            Returns the release number of the module hardware, preprogrammed at the factory.
            The original hardware release returns value 1, revision B returns value 2, etc.

            @return an integer corresponding to the release number of the module hardware, preprogrammed at the factory

            On failure, throws an exception or returns YModule.PRODUCTRELEASE_INVALID.
            """
            return self._run(self._aio.get_productRelease())

    if not _DYNAMIC_HELPERS:
        def get_firmwareRelease(self) -> str:
            """
            Returns the version of the firmware embedded in the module.

            @return a string corresponding to the version of the firmware embedded in the module

            On failure, throws an exception or returns YModule.FIRMWARERELEASE_INVALID.
            """
            return self._run(self._aio.get_firmwareRelease())

    if not _DYNAMIC_HELPERS:
        def get_persistentSettings(self) -> int:
            """
            Returns the current state of persistent module settings.

            @return a value among YModule.PERSISTENTSETTINGS_LOADED, YModule.PERSISTENTSETTINGS_SAVED and
            YModule.PERSISTENTSETTINGS_MODIFIED corresponding to the current state of persistent module settings

            On failure, throws an exception or returns YModule.PERSISTENTSETTINGS_INVALID.
            """
            return self._run(self._aio.get_persistentSettings())

    if not _DYNAMIC_HELPERS:
        def set_persistentSettings(self, newval: int) -> int:
            return self._run(self._aio.set_persistentSettings(newval))

    if not _DYNAMIC_HELPERS:
        def get_luminosity(self) -> int:
            """
            Returns the luminosity of the  module informative LEDs (from 0 to 100).

            @return an integer corresponding to the luminosity of the  module informative LEDs (from 0 to 100)

            On failure, throws an exception or returns YModule.LUMINOSITY_INVALID.
            """
            return self._run(self._aio.get_luminosity())

    if not _DYNAMIC_HELPERS:
        def set_luminosity(self, newval: int) -> int:
            """
            Changes the luminosity of the module informative leds. The parameter is a
            value between 0 and 100.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : an integer corresponding to the luminosity of the module informative leds

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_luminosity(newval))

    if not _DYNAMIC_HELPERS:
        def get_beacon(self) -> int:
            """
            Returns the state of the localization beacon.

            @return either YModule.BEACON_OFF or YModule.BEACON_ON, according to the state of the localization beacon

            On failure, throws an exception or returns YModule.BEACON_INVALID.
            """
            return self._run(self._aio.get_beacon())

    if not _DYNAMIC_HELPERS:
        def set_beacon(self, newval: int) -> int:
            """
            Turns on or off the module localization beacon.

            @param newval : either YModule.BEACON_OFF or YModule.BEACON_ON

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_beacon(newval))

    if not _DYNAMIC_HELPERS:
        def get_upTime(self) -> int:
            """
            Returns the number of milliseconds spent since the module was powered on.

            @return an integer corresponding to the number of milliseconds spent since the module was powered on

            On failure, throws an exception or returns YModule.UPTIME_INVALID.
            """
            return self._run(self._aio.get_upTime())

    if not _DYNAMIC_HELPERS:
        def get_usbCurrent(self) -> int:
            """
            Returns the current consumed by the module on the USB bus, in milli-amps.

            @return an integer corresponding to the current consumed by the module on the USB bus, in milli-amps

            On failure, throws an exception or returns YModule.USBCURRENT_INVALID.
            """
            return self._run(self._aio.get_usbCurrent())

    if not _DYNAMIC_HELPERS:
        def get_rebootCountdown(self) -> int:
            """
            Returns the remaining number of seconds before the module restarts, or zero when no
            reboot has been scheduled.

            @return an integer corresponding to the remaining number of seconds before the module restarts, or zero when no
                    reboot has been scheduled

            On failure, throws an exception or returns YModule.REBOOTCOUNTDOWN_INVALID.
            """
            return self._run(self._aio.get_rebootCountdown())

    if not _DYNAMIC_HELPERS:
        def set_rebootCountdown(self, newval: int) -> int:
            return self._run(self._aio.set_rebootCountdown(newval))

    if not _DYNAMIC_HELPERS:
        def get_userVar(self) -> int:
            """
            Returns the value previously stored in this attribute.
            On startup and after a device reboot, the value is always reset to zero.

            @return an integer corresponding to the value previously stored in this attribute

            On failure, throws an exception or returns YModule.USERVAR_INVALID.
            """
            return self._run(self._aio.get_userVar())

    if not _DYNAMIC_HELPERS:
        def set_userVar(self, newval: int) -> int:
            """
            Stores a 32 bit value in the device RAM. This attribute is at programmer disposal,
            should he need to store a state variable.
            On startup and after a device reboot, the value is always reset to zero.

            @param newval : an integer

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_userVar(newval))

    if not _DYNAMIC_HELPERS:
        def saveToFlash(self) -> int:
            """
            Saves current settings in the nonvolatile memory of the module.
            Warning: the number of allowed save operations during a module life is
            limited (about 100000 cycles). Do not call this function within a loop.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.saveToFlash())

    if not _DYNAMIC_HELPERS:
        def revertFromFlash(self) -> int:
            """
            Reloads the settings stored in the nonvolatile memory, as
            when the module is powered on.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.revertFromFlash())

    if not _DYNAMIC_HELPERS:
        def reboot(self, secBeforeReboot: int) -> int:
            """
            Schedules a simple module reboot after the given number of seconds.

            @param secBeforeReboot : number of seconds before rebooting

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reboot(secBeforeReboot))

    if not _DYNAMIC_HELPERS:
        def triggerFirmwareUpdate(self, secBeforeReboot: int) -> int:
            """
            Schedules a module reboot into special firmware update mode.

            @param secBeforeReboot : number of seconds before rebooting

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.triggerFirmwareUpdate(secBeforeReboot))

    def registerLogCallback(self, callback: YModuleLogCallback) -> int:
        """
        Registers a device log callback function. This callback will be called each time
        that a module sends a new log message. Mostly useful to debug a Yoctopuce module.

        @param callback : the callback function to call, or a None pointer.
                The callback function should take two
                arguments: the module object that emitted the log message,
                and the character string containing the log.
                On failure, throws an exception or returns a negative error code.
        """
        serial: str

        serial = self.get_serialNumber()
        if serial == YAPI.INVALID_STRING:
            return YAPI.DEVICE_NOT_FOUND
        self._aio._logCallback = callback
        self._startStopDevLog(serial, callback)
        return 0

    def registerConfigChangeCallback(self, callback: YModuleConfigChangeCallback) -> int:
        """
        Register a callback function, to be called when a persistent settings in
        a device configuration has been changed (e.g. change of unit, etc).

        @param callback : a procedure taking a YModule parameter, or None
                to unregister a previously registered  callback.
        """
        return self._run(self._aio.registerConfigChangeCallback(self._proxyCb(type(self), callback)))

    def registerBeaconCallback(self, callback: YModuleBeaconCallback) -> int:
        """
        Register a callback function, to be called when the localization beacon of the module
        has been changed. The callback function should take two arguments: the YModule object of
        which the beacon has changed, and an integer describing the new beacon state.

        @param callback : The callback function to call, or None to unregister a
                previously registered callback.
        """
        return self._run(self._aio.registerBeaconCallback(self._proxyCb(type(self), callback)))

    if not _DYNAMIC_HELPERS:
        def triggerConfigChangeCallback(self) -> int:
            """
            Triggers a configuration change callback, to check if they are supported or not.
            """
            return self._run(self._aio.triggerConfigChangeCallback())

    if not _DYNAMIC_HELPERS:
        def checkFirmware(self, path: str, onlynew: bool) -> str:
            """
            Tests whether the byn file is valid for this module. This method is useful to test if the module
            needs to be updated.
            It is possible to pass a directory as argument instead of a file. In this case, this method returns
            the path of the most recent
            appropriate .byn file. If the parameter onlynew is true, the function discards firmwares that are older or
            equal to the installed firmware.

            @param path : the path of a byn file or a directory that contains byn files
            @param onlynew : returns only files that are strictly newer

            @return the path of the byn file to use or a empty string if no byn files matches the requirement

            On failure, throws an exception or returns a string that start with "error:".
            """
            return self._run(self._aio.checkFirmware(path, onlynew))

    def updateFirmwareEx(self, path: str, force: bool) -> YFirmwareUpdate:
        """
        Prepares a firmware update of the module. This method returns a YFirmwareUpdate object which
        handles the firmware update process.

        @param path : the path of the .byn file to use.
        @param force : true to force the firmware update even if some prerequisites appear not to be met

        @return a YFirmwareUpdate object or None on error.
        """
        return self._proxy(YFirmwareUpdate, self._run(self._aio.updateFirmwareEx(path, force)))

    def updateFirmware(self, path: str) -> YFirmwareUpdate:
        """
        Prepares a firmware update of the module. This method returns a YFirmwareUpdate object which
        handles the firmware update process.

        @param path : the path of the .byn file to use.

        @return a YFirmwareUpdate object or None on error.
        """
        return self._proxy(YFirmwareUpdate, self._run(self._aio.updateFirmware(path)))

    if not _DYNAMIC_HELPERS:
        def get_allSettings(self) -> xarray:
            """
            Returns all the settings and uploaded files of the module. Useful to backup all the
            logical names, calibrations parameters, and uploaded files of a device.

            @return a binary buffer with all the settings.

            On failure, throws an exception or returns an binary object of size 0.
            """
            return self._run(self._aio.get_allSettings())

    if not _DYNAMIC_HELPERS:
        def set_allSettingsAndFiles(self, settings: xarray) -> int:
            """
            Restores all the settings and uploaded files to the module.
            This method is useful to restore all the logical names and calibrations parameters,
            uploaded files etc. of a device from a backup.
            Remember to call the saveToFlash() method of the module if the
            modifications must be kept.

            @param settings : a binary buffer with all the settings.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_allSettingsAndFiles(settings))

    def hasFunction(self, funcId: str) -> bool:
        """
        Tests if the device includes a specific function. This method takes a function identifier
        and returns a boolean.

        @param funcId : the requested function identifier

        @return true if the device has the function identifier
        """
        return self._aio.hasFunction(funcId)

    def get_functionIds(self, funType: str) -> list[str]:
        """
        Retrieve all hardware identifier that match the type passed in argument.

        @param funType : The type of function (Relay, LightSensor, Voltage,...)

        @return an array of strings.
        """
        return self._aio.get_functionIds(funType)

    if not _DYNAMIC_HELPERS:
        def set_allSettings(self, settings: xarray) -> int:
            """
            Restores all the settings of the device. Useful to restore all the logical names and calibrations parameters
            of a module from a backup.Remember to call the saveToFlash() method of the module if the
            modifications must be kept.

            @param settings : a binary buffer with all the settings.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_allSettings(settings))

    if not _DYNAMIC_HELPERS:
        def get_hardwareId(self) -> str:
            """
            Returns the unique hardware identifier of the module.
            The unique hardware identifier is made of the device serial
            number followed by string ".module".

            @return a string that uniquely identifies the module
            """
            return self._run(self._aio.get_hardwareId())

    if not _DYNAMIC_HELPERS:
        def download(self, pathname: str) -> xarray:
            """
            Downloads the specified built-in file and returns a binary buffer with its content.

            @param pathname : name of the new file to load

            @return a binary buffer with the file content

            On failure, throws an exception or returns an empty content.
            """
            return self._run(self._aio.download(pathname))

    if not _DYNAMIC_HELPERS:
        def get_icon2d(self) -> xarray:
            """
            Returns the icon of the module. The icon is a PNG image and does not
            exceeds 1536 bytes.

            @return a binary buffer with module icon, in png format.
                    On failure, throws an exception or returns an empty content.
            """
            return self._run(self._aio.get_icon2d())

    if not _DYNAMIC_HELPERS:
        def get_lastLogs(self) -> str:
            """
            Returns a string with last logs of the module. This method return only
            logs that are still in the module.

            @return a string with last logs of the module.
                    On failure, throws an exception or returns  YAPI.INVALID_STRING.
            """
            return self._run(self._aio.get_lastLogs())

    if not _DYNAMIC_HELPERS:
        def log(self, text: str) -> int:
            """
            Adds a text message to the device logs. This function is useful in
            particular to trace the execution of HTTP callbacks. If a newline
            is desired after the message, it must be included in the string.

            @param text : the string to append to the logs.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.log(text))

    if not _DYNAMIC_HELPERS:
        def get_subDevices(self) -> list[str]:
            """
            Returns a list of all the modules that are plugged into the current module.
            This method only makes sense when called for a YoctoHub/VirtualHub.
            Otherwise, an empty array will be returned.

            @return an array of strings containing the sub modules.
            """
            return self._run(self._aio.get_subDevices())

    if not _DYNAMIC_HELPERS:
        def get_parentHub(self) -> str:
            """
            Returns the serial number of the YoctoHub on which this module is connected.
            If the module is connected by USB, or if the module is the root YoctoHub, an
            empty string is returned.

            @return a string with the serial number of the YoctoHub or an empty string
            """
            return self._run(self._aio.get_parentHub())

    if not _DYNAMIC_HELPERS:
        def get_url(self) -> str:
            """
            Returns the URL used to access the module. If the module is connected by USB, the
            string 'usb' is returned.

            @return a string with the URL of the module.
            """
            return self._run(self._aio.get_url())

    # --- (end of generated code: YModule implementation)

    def functionCount(self) -> int:
        """
        Returns the number of functions (beside the "module" interface) available on the module.

        @return the number of functions on the module

        On failure, throws an exception or returns a negative error code.
        """
        return self._aio.functionCount()

    def functionId(self, functionIndex: int) -> str:
        """
        Retrieves the hardware identifier of the <i>n</i>th function on the module.

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the unambiguous hardware identifier of the requested module function

        On failure, throws an exception or returns an empty string.
        """
        return self._aio.functionId(functionIndex)

    def functionType(self, functionIndex: int) -> str:
        """
        Retrieves the type of the <i>n</i>th function on the module. Yoctopuce functions type names match
        their class names without the <i>Y</i> prefix, for instance <i>Relay</i>, <i>Temperature</i> etc..

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the type of the function.

        On failure, throws an exception or returns an empty string.
        """
        return self._aio.functionType(functionIndex)

    def functionBaseType(self, functionIndex: int) -> str:
        """
        Retrieves the base type of the <i>n</i>th function on the module.
        For instance, the base type of all measuring functions is "Sensor".

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the base type of the function

        On failure, throws an exception or returns an empty string.
        """
        return self._aio.functionBaseType(functionIndex)

    def functionName(self, functionIndex: int) -> str:
        """
        Retrieves the logical name of the <i>n</i>th function on the module.

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the logical name of the requested module function

        On failure, throws an exception or returns an empty string.
        """
        return self._aio.functionName(functionIndex)

    def functionValue(self, functionIndex: int) -> str:
        """
        Retrieves the advertised value of the <i>n</i>th function on the module.

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a short string (up to 6 characters) corresponding to the advertised value of the requested
        module function

        On failure, throws an exception or returns an empty string.
        """
        return self._aio.functionValue(functionIndex)


# --- (generated code: YFirmwareUpdate class start)
# noinspection PyProtectedMember
class YFirmwareUpdate(YSyncProxy):
    """
    The YFirmwareUpdate class let you control the firmware update of a Yoctopuce
    module. This class should not be instantiate directly, but instances should be retrieved
    using the YModule method module.updateFirmware.

    """
    _aio: YFirmwareUpdate_aio
    # --- (end of generated code: YFirmwareUpdate class start)

        # --- (generated code: YFirmwareUpdate implementation)
    @classmethod
    def GetAllBootLoaders(cls, ) -> list[str]:
        """
        Returns a list of all the modules in "firmware update" mode.

        @return an array of strings containing the serial numbers of devices in "firmware update" mode.
        """
        return cls._run(YFirmwareUpdate_aio.GetAllBootLoaders())

    @classmethod
    def GetAllBootLoadersInContext(cls, yctx: YAPIContext) -> list[str]:
        """
        Returns a list of all the modules in "firmware update" mode.

        @param yctx : a YAPI context.

        @return an array of strings containing the serial numbers of devices in "firmware update" mode.
        """
        return cls._run(YFirmwareUpdate_aio.GetAllBootLoadersInContext(yctx))

    @classmethod
    def CheckFirmware(cls, serial: str, path: str, minrelease: int) -> str:
        """
        Test if the byn file is valid for this module. It is possible to pass a directory instead of a file.
        In that case, this method returns the path of the most recent appropriate byn file. This method will
        ignore any firmware older than minrelease.

        @param serial : the serial number of the module to update
        @param path : the path of a byn file or a directory that contains byn files
        @param minrelease : a positive integer

        @return : the path of the byn file to use, or an empty string if no byn files matches the requirement

        On failure, returns a string that starts with "error:".
        """
        return cls._run(YFirmwareUpdate_aio.CheckFirmware(serial, path, minrelease))

    if not _DYNAMIC_HELPERS:
        def get_progress(self) -> int:
            """
            Returns the progress of the firmware update, on a scale from 0 to 100. When the object is
            instantiated, the progress is zero. The value is updated during the firmware update process until
            the value of 100 is reached. The 100 value means that the firmware update was completed
            successfully. If an error occurs during the firmware update, a negative value is returned, and the
            error message can be retrieved with get_progressMessage.

            @return an integer in the range 0 to 100 (percentage of completion)
                    or a negative error code in case of failure.
            """
            return self._run(self._aio.get_progress())

    if not _DYNAMIC_HELPERS:
        def get_progressMessage(self) -> str:
            """
            Returns the last progress message of the firmware update process. If an error occurs during the
            firmware update process, the error message is returned

            @return a string  with the latest progress message, or the error message.
            """
            return self._run(self._aio.get_progressMessage())

    if not _DYNAMIC_HELPERS:
        def startUpdate(self) -> int:
            """
            Starts the firmware update process. This method starts the firmware update process in background. This method
            returns immediately. You can monitor the progress of the firmware update with the get_progress()
            and get_progressMessage() methods.

            @return an integer in the range 0 to 100 (percentage of completion),
                    or a negative error code in case of failure.

            On failure returns a negative error code.
            """
            return self._run(self._aio.startUpdate())

    # --- (end of generated code: YFirmwareUpdate implementation)


# --- (generated code: YConsolidatedDataSet class start)
# noinspection PyProtectedMember
class YConsolidatedDataSet(YSyncProxy):
    """
    YConsolidatedDataSet objects make it possible to retrieve a set of
    recorded measures from multiple sensors, for a specified time interval.
    They can be used to load data points progressively, and to receive
    data records by timestamp, one by one..

    """
    _aio: YConsolidatedDataSet_aio
    # --- (end of generated code: YConsolidatedDataSet class start)

    # --- (generated code: YConsolidatedDataSet implementation)
    @classmethod
    def Init(cls, sensorNames: list[str], startTime: float, endTime: float) -> YConsolidatedDataSet:
        """
        Returns an object holding historical data for multiple
        sensors, for a specified time interval.
        The measures will be retrieved from the data logger, which must have been turned
        on at the desired time. The resulting object makes it possible to load progressively
        a large set of measures from multiple sensors, consolidating data on the fly
        to align records based on measurement timestamps.

        @param sensorNames : array of logical names or hardware identifiers of the sensors
                for which data must be loaded from their data logger.
        @param startTime : the start of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without initial limit.
        @param endTime : the end of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without ending limit.

        @return an instance of YConsolidatedDataSet, providing access to
                consolidated historical data. Records can be loaded progressively
                using the YConsolidatedDataSet.nextRecord() method.
        """
        return cls._proxy(cls, YConsolidatedDataSet_aio.Init(sensorNames, startTime, endTime))

    if not _DYNAMIC_HELPERS:
        def nextRecord(self, datarec: list[float]) -> int:
            """
            Extracts the next data record from the data logger of all sensors linked to this
            object.

            @param datarec : array of floating point numbers, that will be filled by the
                    function with the timestamp of the measure in first position,
                    followed by the measured value in next positions.

            @return an integer in the range 0 to 100 (percentage of completion),
                    or a negative error code in case of failure.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.nextRecord(datarec))

    # --- (end of generated code: YConsolidatedDataSet implementation)


#################################################################################
#                                                                               #
#                            YSensor                                            #
#                                                                               #
#################################################################################

# --- (generated code: YSensor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSensorValueCallback = Union[Callable[['YSensor', str], Any], None]
        YSensorTimedReportCallback = Union[Callable[['YSensor', YMeasure], Any], None]
    except TypeError:
        YSensorValueCallback = Union[Callable, Awaitable]
        YSensorTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSensor(YFunction):
    """
    The YSensor class is the parent class for all Yoctopuce sensor types. It can be
    used to read the current value and unit of any sensor, read the min/max
    value, configure autonomous recording frequency and access recorded data.
    It also provides a function to register a callback invoked each time the
    observed value changes, or at a predefined interval. Using this class rather
    than a specific subclass makes it possible to create generic applications
    that work with any Yoctopuce sensor, even those that do not yet exist.
    Note: The YAnButton class is the only analog input which does not inherit
    from YSensor.

    """
    _aio: YSensor_aio
    # --- (end of generated code: YSensor class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSensor return codes)
        UNIT_INVALID: Final[str] = YAPI.INVALID_STRING
        CURRENTVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        LOWESTVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        HIGHESTVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CURRENTRAWVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        LOGFREQUENCY_INVALID: Final[str] = YAPI.INVALID_STRING
        REPORTFREQUENCY_INVALID: Final[str] = YAPI.INVALID_STRING
        CALIBRATIONPARAM_INVALID: Final[str] = YAPI.INVALID_STRING
        RESOLUTION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SENSORSTATE_INVALID: Final[int] = YAPI.INVALID_INT
        ADVMODE_IMMEDIATE: Final[int] = 0
        ADVMODE_PERIOD_AVG: Final[int] = 1
        ADVMODE_PERIOD_MIN: Final[int] = 2
        ADVMODE_PERIOD_MAX: Final[int] = 3
        ADVMODE_INVALID: Final[int] = -1
        # --- (end of generated code: YSensor return codes)

        # --- (generated code: YSensor implementation)

    @classmethod
    def FindSensor(cls, func: str) -> YSensor:
        """
        Retrieves a sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSensor.isOnline() to test if the sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the sensor, for instance
                MyDevice..

        @return a YSensor object allowing you to drive the sensor.
        """
        return cls._proxy(cls, YSensor_aio.FindSensorInContext(YAPI_aio, func))

    @classmethod
    def FindSensorInContext(cls, yctx: YAPIContext, func: str) -> YSensor:
        """
        Retrieves a sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSensor.isOnline() to test if the sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the sensor, for instance
                MyDevice..

        @return a YSensor object allowing you to drive the sensor.
        """
        return cls._proxy(cls, YSensor_aio.FindSensorInContext(yctx._aio, func))

    @classmethod
    def FirstSensor(cls) -> Union[YSensor, None]:
        """
        Starts the enumeration of sensors currently accessible.
        Use the method YSensor.nextSensor() to iterate on
        next sensors.

        @return a pointer to a YSensor object, corresponding to
                the first sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YSensor_aio.FirstSensorInContext(YAPI_aio))

    @classmethod
    def FirstSensorInContext(cls, yctx: YAPIContext) -> Union[YSensor, None]:
        """
        Starts the enumeration of sensors currently accessible.
        Use the method YSensor.nextSensor() to iterate on
        next sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YSensor object, corresponding to
                the first sensor currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YSensor_aio.FirstSensorInContext(yctx._aio))

    def nextSensor(self) -> Union[YSensor, None]:
        """
        Continues the enumeration of sensors started using yFirstSensor().
        Caution: You can't make any assumption about the returned sensors order.
        If you want to find a specific a sensor, use Sensor.findSensor()
        and a hardwareID or a logical name.

        @return a pointer to a YSensor object, corresponding to
                a sensor currently online, or a None pointer
                if there are no more sensors to enumerate.
        """
        return self._proxy(type(self), self._aio.nextSensor())

    if not _DYNAMIC_HELPERS:
        def get_unit(self) -> str:
            """
            Returns the measuring unit for the measure.

            @return a string corresponding to the measuring unit for the measure

            On failure, throws an exception or returns YSensor.UNIT_INVALID.
            """
            return self._run(self._aio.get_unit())

    if not _DYNAMIC_HELPERS:
        def get_currentValue(self) -> float:
            """
            Returns the current value of the measure, in the specified unit, as a floating point number.
            Note that a get_currentValue() call will *not* start a measure in the device, it
            will just return the last measure that occurred in the device. Indeed, internally, each Yoctopuce
            devices is continuously making measurements at a hardware specific frequency.

            If continuously calling  get_currentValue() leads you to performances issues, then
            you might consider to switch to callback programming model. Check the "advanced
            programming" chapter in in your device user manual for more information.

            @return a floating point number corresponding to the current value of the measure, in the specified
            unit, as a floating point number

            On failure, throws an exception or returns YSensor.CURRENTVALUE_INVALID.
            """
            return self._run(self._aio.get_currentValue())

    if not _DYNAMIC_HELPERS:
        def set_lowestValue(self, newval: float) -> int:
            """
            Changes the recorded minimal value observed. Can be used to reset the value returned
            by get_lowestValue().

            @param newval : a floating point number corresponding to the recorded minimal value observed

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_lowestValue(newval))

    if not _DYNAMIC_HELPERS:
        def get_lowestValue(self) -> float:
            """
            Returns the minimal value observed for the measure since the device was started.
            Can be reset to an arbitrary value thanks to set_lowestValue().

            @return a floating point number corresponding to the minimal value observed for the measure since
            the device was started

            On failure, throws an exception or returns YSensor.LOWESTVALUE_INVALID.
            """
            return self._run(self._aio.get_lowestValue())

    if not _DYNAMIC_HELPERS:
        def set_highestValue(self, newval: float) -> int:
            """
            Changes the recorded maximal value observed. Can be used to reset the value returned
            by get_lowestValue().

            @param newval : a floating point number corresponding to the recorded maximal value observed

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_highestValue(newval))

    if not _DYNAMIC_HELPERS:
        def get_highestValue(self) -> float:
            """
            Returns the maximal value observed for the measure since the device was started.
            Can be reset to an arbitrary value thanks to set_highestValue().

            @return a floating point number corresponding to the maximal value observed for the measure since
            the device was started

            On failure, throws an exception or returns YSensor.HIGHESTVALUE_INVALID.
            """
            return self._run(self._aio.get_highestValue())

    if not _DYNAMIC_HELPERS:
        def get_currentRawValue(self) -> float:
            """
            Returns the uncalibrated, unrounded raw value returned by the
            sensor, in the specified unit, as a floating point number.

            @return a floating point number corresponding to the uncalibrated, unrounded raw value returned by the
                    sensor, in the specified unit, as a floating point number

            On failure, throws an exception or returns YSensor.CURRENTRAWVALUE_INVALID.
            """
            return self._run(self._aio.get_currentRawValue())

    if not _DYNAMIC_HELPERS:
        def get_logFrequency(self) -> str:
            """
            Returns the datalogger recording frequency for this function, or "OFF"
            when measures are not stored in the data logger flash memory.

            @return a string corresponding to the datalogger recording frequency for this function, or "OFF"
                    when measures are not stored in the data logger flash memory

            On failure, throws an exception or returns YSensor.LOGFREQUENCY_INVALID.
            """
            return self._run(self._aio.get_logFrequency())

    if not _DYNAMIC_HELPERS:
        def set_logFrequency(self, newval: str) -> int:
            """
            Changes the datalogger recording frequency for this function.
            The frequency can be specified as samples per second,
            as sample per minute (for instance "15/m") or in samples per
            hour (eg. "4/h"). To disable recording for this function, use
            the value "OFF". Note that setting the  datalogger recording frequency
            to a greater value than the sensor native sampling frequency is useless,
            and even counterproductive: those two frequencies are not related.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : a string corresponding to the datalogger recording frequency for this function

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_logFrequency(newval))

    if not _DYNAMIC_HELPERS:
        def get_reportFrequency(self) -> str:
            """
            Returns the timed value notification frequency, or "OFF" if timed
            value notifications are disabled for this function.

            @return a string corresponding to the timed value notification frequency, or "OFF" if timed
                    value notifications are disabled for this function

            On failure, throws an exception or returns YSensor.REPORTFREQUENCY_INVALID.
            """
            return self._run(self._aio.get_reportFrequency())

    if not _DYNAMIC_HELPERS:
        def set_reportFrequency(self, newval: str) -> int:
            """
            Changes the timed value notification frequency for this function.
            The frequency can be specified as samples per second,
            as sample per minute (for instance "15/m") or in samples per
            hour (e.g. "4/h"). To disable timed value notifications for this
            function, use the value "OFF". Note that setting the  timed value
            notification frequency to a greater value than the sensor native
            sampling frequency is unless, and even counterproductive: those two
            frequencies are not related.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : a string corresponding to the timed value notification frequency for this function

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_reportFrequency(newval))

    if not _DYNAMIC_HELPERS:
        def get_advMode(self) -> int:
            """
            Returns the measuring mode used for the advertised value pushed to the parent hub.

            @return a value among YSensor.ADVMODE_IMMEDIATE, YSensor.ADVMODE_PERIOD_AVG,
            YSensor.ADVMODE_PERIOD_MIN and YSensor.ADVMODE_PERIOD_MAX corresponding to the measuring mode used
            for the advertised value pushed to the parent hub

            On failure, throws an exception or returns YSensor.ADVMODE_INVALID.
            """
            return self._run(self._aio.get_advMode())

    if not _DYNAMIC_HELPERS:
        def set_advMode(self, newval: int) -> int:
            """
            Changes the measuring mode used for the advertised value pushed to the parent hub.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : a value among YSensor.ADVMODE_IMMEDIATE, YSensor.ADVMODE_PERIOD_AVG,
            YSensor.ADVMODE_PERIOD_MIN and YSensor.ADVMODE_PERIOD_MAX corresponding to the measuring mode used
            for the advertised value pushed to the parent hub

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_advMode(newval))

    if not _DYNAMIC_HELPERS:
        def set_calibrationParam(self, newval: str) -> int:
            return self._run(self._aio.set_calibrationParam(newval))

    if not _DYNAMIC_HELPERS:
        def set_resolution(self, newval: float) -> int:
            """
            Changes the resolution of the measured physical values. The resolution corresponds to the numerical precision
            when displaying value. It does not change the precision of the measure itself.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the resolution of the measured physical values

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_resolution(newval))

    if not _DYNAMIC_HELPERS:
        def get_resolution(self) -> float:
            """
            Returns the resolution of the measured values. The resolution corresponds to the numerical precision
            of the measures, which is not always the same as the actual precision of the sensor.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @return a floating point number corresponding to the resolution of the measured values

            On failure, throws an exception or returns YSensor.RESOLUTION_INVALID.
            """
            return self._run(self._aio.get_resolution())

    if not _DYNAMIC_HELPERS:
        def get_sensorState(self) -> int:
            """
            Returns the sensor state code, which is zero when there is an up-to-date measure
            available or a positive code if the sensor is not able to provide a measure right now.

            @return an integer corresponding to the sensor state code, which is zero when there is an up-to-date measure
                    available or a positive code if the sensor is not able to provide a measure right now

            On failure, throws an exception or returns YSensor.SENSORSTATE_INVALID.
            """
            return self._run(self._aio.get_sensorState())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YSensorValueCallback) -> int:
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
        def isSensorReady(self) -> bool:
            """
            Checks if the sensor is currently able to provide an up-to-date measure.
            Returns false if the device is unreachable, or if the sensor does not have
            a current measure to transmit. No exception is raised if there is an error
            while trying to contact the device hosting $THEFUNCTION$.

            @return true if the sensor can provide an up-to-date measure, and false otherwise
            """
            return self._run(self._aio.isSensorReady())

    def get_dataLogger(self) -> Union[YDataLogger, None]:
        """
        Returns the YDatalogger object of the device hosting the sensor. This method returns an object
        that can control global parameters of the data logger. The returned object
        should not be freed.

        @return an YDatalogger object, or None on error.
        """
        return self._proxy(YDataLogger, self._run(self._aio.get_dataLogger()))

    if not _DYNAMIC_HELPERS:
        def startDataLogger(self) -> int:
            """
            Starts the data logger on the device. Note that the data logger
            will only save the measures on this sensor if the logFrequency
            is not set to "OFF".

            @return YAPI.SUCCESS if the call succeeds.
            """
            return self._run(self._aio.startDataLogger())

    if not _DYNAMIC_HELPERS:
        def stopDataLogger(self) -> int:
            """
            Stops the datalogger on the device.

            @return YAPI.SUCCESS if the call succeeds.
            """
            return self._run(self._aio.stopDataLogger())

    def get_recordedData(self, startTime: float, endTime: float) -> YDataSet:
        """
        Retrieves a YDataSet object holding historical data for this
        sensor, for a specified time interval. The measures will be
        retrieved from the data logger, which must have been turned
        on at the desired time. See the documentation of the YDataSet
        class for information on how to get an overview of the
        recorded data, and how to load progressively a large set
        of measures from the data logger.

        This function only works if the device uses a recent firmware,
        as YDataSet objects are not supported by firmwares older than
        version 13000.

        @param startTime : the start of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without initial limit.
        @param endTime : the end of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without ending limit.

        @return an instance of YDataSet, providing access to historical
                data. Past measures can be loaded progressively
                using methods from the YDataSet object.
        """
        return self._proxy(YDataSet, self._run(self._aio.get_recordedData(startTime, endTime)))

    def registerTimedReportCallback(self, callback: YSensorTimedReportCallback) -> int:
        """
        Registers the callback function that is invoked on every periodic timed notification.
        The callback is invoked only during the execution of ySleep or yHandleEvents.
        This provides control over the time when the callback is triggered. For good responsiveness, remember to call
        one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

        @param callback : the callback function to call, or a None pointer. The callback function should take two
                arguments: the function object of which the value has changed, and an YMeasure object describing
                the new advertised value.
        @noreturn
        """
        return self._run(self._aio.registerTimedReportCallback(self._proxyCb(type(self), callback)))

    if not _DYNAMIC_HELPERS:
        def calibrateFromPoints(self, rawValues: list[float], refValues: list[float]) -> int:
            """
            Configures error correction data points, in particular to compensate for
            a possible perturbation of the measure caused by an enclosure. It is possible
            to configure up to five correction points. Correction points must be provided
            in ascending order, and be in the range of the sensor. The device will automatically
            perform a linear interpolation of the error correction between specified
            points. Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            For more information on advanced capabilities to refine the calibration of
            sensors, please contact support@yoctopuce.com.

            @param rawValues : array of floating point numbers, corresponding to the raw
                    values returned by the sensor for the correction points.
            @param refValues : array of floating point numbers, corresponding to the corrected
                    values for the correction points.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.calibrateFromPoints(rawValues, refValues))

    if not _DYNAMIC_HELPERS:
        def loadCalibrationPoints(self, rawValues: list[float], refValues: list[float]) -> int:
            """
            Retrieves error correction data points previously entered using the method
            calibrateFromPoints.

            @param rawValues : array of floating point numbers, that will be filled by the
                    function with the raw sensor values for the correction points.
            @param refValues : array of floating point numbers, that will be filled by the
                    function with the desired values for the correction points.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadCalibrationPoints(rawValues, refValues))

    # --- (end of generated code: YSensor implementation)


#################################################################################
#                                                                               #
#                         Datalogger support                                    #
#                                                                               #
#################################################################################

# --- (generated code: YDataStream class start)
# noinspection PyRedundantParentheses
# noinspection PyUnusedLocal
# noinspection PyProtectedMember
class YDataStream(YSyncProxy):
    """
    DataStream objects represent bare recorded measure sequences,
    exactly as found within the data logger present on Yoctopuce
    sensors.

    In most cases, it is not necessary to use DataStream objects
    directly, as the DataSet objects (returned by the
    get_recordedData() method from sensors and the
    get_dataSets() method from the data logger) provide
    a more convenient interface.

    """
    _aio: YDataStream_aio
    # --- (end of generated code: YDataStream class start)
    if not _IS_MICROPYTHON:
        DATA_INVALID: float = YAPI.INVALID_DOUBLE
        DURATION_INVALID: float = YAPI.INVALID_DOUBLE
        # --- (generated code: YDataStream return codes)
        pass
        # --- (end of generated code: YDataStream return codes)

        # --- (generated code: YDataStream implementation)
    def get_runIndex(self) -> int:
        """
        Returns the run index of the data stream. A run can be made of
        multiple datastreams, for different time intervals.

        @return an unsigned number corresponding to the run index.
        """
        return self._aio.get_runIndex()

    if not _DYNAMIC_HELPERS:
        def get_startTime(self) -> int:
            """
            Returns the relative start time of the data stream, measured in seconds.
            For recent firmwares, the value is relative to the present time,
            which means the value is always negative.
            If the device uses a firmware older than version 13000, value is
            relative to the start of the time the device was powered on, and
            is always positive.
            If you need an absolute UTC timestamp, use get_realStartTimeUTC().

            <b>DEPRECATED</b>: This method has been replaced by get_realStartTimeUTC().

            @return an unsigned number corresponding to the number of seconds
                    between the start of the run and the beginning of this data
                    stream.
            """
            return self._run(self._aio.get_startTime())

    def get_startTimeUTC(self) -> int:
        """
        Returns the start time of the data stream, relative to the Jan 1, 1970.
        If the UTC time was not set in the datalogger at the time of the recording
        of this data stream, this method returns 0.

        <b>DEPRECATED</b>: This method has been replaced by get_realStartTimeUTC().

        @return an unsigned number corresponding to the number of seconds
                between the Jan 1, 1970 and the beginning of this data
                stream (i.e. Unix time representation of the absolute time).
        """
        return self._aio.get_startTimeUTC()

    def get_realStartTimeUTC(self) -> float:
        """
        Returns the start time of the data stream, relative to the Jan 1, 1970.
        If the UTC time was not set in the datalogger at the time of the recording
        of this data stream, this method returns 0.

        @return a floating-point number  corresponding to the number of seconds
                between the Jan 1, 1970 and the beginning of this data
                stream (i.e. Unix time representation of the absolute time).
        """
        return self._aio.get_realStartTimeUTC()

    def get_dataSamplesIntervalMs(self) -> int:
        """
        Returns the number of milliseconds between two consecutive
        rows of this data stream. By default, the data logger records one row
        per second, but the recording frequency can be changed for
        each device function

        @return an unsigned number corresponding to a number of milliseconds.
        """
        return self._aio.get_dataSamplesIntervalMs()

    if not _DYNAMIC_HELPERS:
        def get_rowCount(self) -> int:
            """
            Returns the number of data rows present in this stream.

            If the device uses a firmware older than version 13000,
            this method fetches the whole data stream from the device
            if not yet done, which can cause a little delay.

            @return an unsigned number corresponding to the number of rows.

            On failure, throws an exception or returns zero.
            """
            return self._run(self._aio.get_rowCount())

    if not _DYNAMIC_HELPERS:
        def get_columnCount(self) -> int:
            """
            Returns the number of data columns present in this stream.
            The meaning of the values present in each column can be obtained
            using the method get_columnNames().

            If the device uses a firmware older than version 13000,
            this method fetches the whole data stream from the device
            if not yet done, which can cause a little delay.

            @return an unsigned number corresponding to the number of columns.

            On failure, throws an exception or returns zero.
            """
            return self._run(self._aio.get_columnCount())

    if not _DYNAMIC_HELPERS:
        def get_columnNames(self) -> list[str]:
            """
            Returns the title (or meaning) of each data column present in this stream.
            In most case, the title of the data column is the hardware identifier
            of the sensor that produced the data. For streams recorded at a lower
            recording rate, the dataLogger stores the min, average and max value
            during each measure interval into three columns with suffixes _min,
            _avg and _max respectively.

            If the device uses a firmware older than version 13000,
            this method fetches the whole data stream from the device
            if not yet done, which can cause a little delay.

            @return a list containing as many strings as there are columns in the
                    data stream.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.get_columnNames())

    def get_minValue(self) -> float:
        """
        Returns the smallest measure observed within this stream.
        If the device uses a firmware older than version 13000,
        this method will always return YDataStream.DATA_INVALID.

        @return a floating-point number corresponding to the smallest value,
                or YDataStream.DATA_INVALID if the stream is not yet complete (still recording).

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        return self._aio.get_minValue()

    def get_averageValue(self) -> float:
        """
        Returns the average of all measures observed within this stream.
        If the device uses a firmware older than version 13000,
        this method will always return YDataStream.DATA_INVALID.

        @return a floating-point number corresponding to the average value,
                or YDataStream.DATA_INVALID if the stream is not yet complete (still recording).

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        return self._aio.get_averageValue()

    def get_maxValue(self) -> float:
        """
        Returns the largest measure observed within this stream.
        If the device uses a firmware older than version 13000,
        this method will always return YDataStream.DATA_INVALID.

        @return a floating-point number corresponding to the largest value,
                or YDataStream.DATA_INVALID if the stream is not yet complete (still recording).

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        return self._aio.get_maxValue()

    if not _DYNAMIC_HELPERS:
        def get_dataRows(self) -> list[list[float]]:
            """
            Returns the whole data set contained in the stream, as a bidimensional
            table of numbers.
            The meaning of the values present in each column can be obtained
            using the method get_columnNames().

            This method fetches the whole data stream from the device,
            if not yet done.

            @return a list containing as many elements as there are rows in the
                    data stream. Each row itself is a list of floating-point
                    numbers.

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.get_dataRows())

    if not _DYNAMIC_HELPERS:
        def get_data(self, row: int, col: int) -> float:
            """
            Returns a single measure from the data stream, specified by its
            row and column index.
            The meaning of the values present in each column can be obtained
            using the method get_columnNames().

            This method fetches the whole data stream from the device,
            if not yet done.

            @param row : row index
            @param col : column index

            @return a floating-point number

            On failure, throws an exception or returns YDataStream.DATA_INVALID.
            """
            return self._run(self._aio.get_data(row, col))

    # --- (end of generated code: YDataStream implementation)

# --- (generated code: YDataSet class start)
# noinspection PyRedundantParentheses
# noinspection PyUnusedLocal
# noinspection PyProtectedMember
class YDataSet(YSyncProxy):
    """
    YDataSet objects make it possible to retrieve a set of recorded measures
    for a given sensor and a specified time interval. They can be used
    to load data points with a progress report. When the YDataSet object is
    instantiated by the sensor.get_recordedData()  function, no data is
    yet loaded from the module. It is only when the loadMore()
    method is called over and over than data will be effectively loaded
    from the dataLogger.

    A preview of available measures is available using the function
    get_preview() as soon as loadMore() has been called
    once. Measures themselves are available using function get_measures()
    when loaded by subsequent calls to loadMore().

    This class can only be used on devices that use a relatively recent firmware,
    as YDataSet objects are not supported by firmwares older than version 13000.

    """
    _aio: YDataSet_aio
    # --- (end of generated code: YDataSet class start)

        # --- (generated code: YDataSet implementation)
    if not _DYNAMIC_HELPERS:
        def get_hardwareId(self) -> str:
            """
            Returns the unique hardware identifier of the function who performed the measures,
            in the form SERIAL.FUNCTIONID. The unique hardware identifier is composed of the
            device serial number and of the hardware identifier of the function
            (for example THRMCPL1-123456.temperature1)

            @return a string that uniquely identifies the function (ex: THRMCPL1-123456.temperature1)

            On failure, throws an exception or returns  YDataSet.HARDWAREID_INVALID.
            """
            return self._run(self._aio.get_hardwareId())

    if not _DYNAMIC_HELPERS:
        def get_functionId(self) -> str:
            """
            Returns the hardware identifier of the function that performed the measure,
            without reference to the module. For example temperature1.

            @return a string that identifies the function (ex: temperature1)
            """
            return self._run(self._aio.get_functionId())

    if not _DYNAMIC_HELPERS:
        def get_unit(self) -> str:
            """
            Returns the measuring unit for the measured value.

            @return a string that represents a physical unit.

            On failure, throws an exception or returns  YDataSet.UNIT_INVALID.
            """
            return self._run(self._aio.get_unit())

    def get_startTimeUTC(self) -> int:
        """
        Returns the start time of the dataset, relative to the Jan 1, 1970.
        When the YDataSet object is created, the start time is the value passed
        in parameter to the get_dataSet() function. After the
        very first call to loadMore(), the start time is updated
        to reflect the timestamp of the first measure actually found in the
        dataLogger within the specified range.

        <b>DEPRECATED</b>: This method has been replaced by get_summary()
        which contain more precise informations.

        @return an unsigned number corresponding to the number of seconds
                between the Jan 1, 1970 and the beginning of this data
                set (i.e. Unix time representation of the absolute time).
        """
        return self._aio.get_startTimeUTC()

    def get_endTimeUTC(self) -> int:
        """
        Returns the end time of the dataset, relative to the Jan 1, 1970.
        When the YDataSet object is created, the end time is the value passed
        in parameter to the get_dataSet() function. After the
        very first call to loadMore(), the end time is updated
        to reflect the timestamp of the last measure actually found in the
        dataLogger within the specified range.

        <b>DEPRECATED</b>: This method has been replaced by get_summary()
        which contain more precise informations.

        @return an unsigned number corresponding to the number of seconds
                between the Jan 1, 1970 and the end of this data
                set (i.e. Unix time representation of the absolute time).
        """
        return self._aio.get_endTimeUTC()

    def get_progress(self) -> int:
        """
        Returns the progress of the downloads of the measures from the data logger,
        on a scale from 0 to 100. When the object is instantiated by get_dataSet,
        the progress is zero. Each time loadMore() is invoked, the progress
        is updated, to reach the value 100 only once all measures have been loaded.

        @return an integer in the range 0 to 100 (percentage of completion).
        """
        return self._aio.get_progress()

    if not _DYNAMIC_HELPERS:
        def loadMore(self) -> int:
            """
            Loads the next block of measures from the dataLogger, and updates
            the progress indicator.

            @return an integer in the range 0 to 100 (percentage of completion),
                    or a negative error code in case of failure.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.loadMore())

    def get_summary(self) -> YMeasure:
        """
        Returns an YMeasure object which summarizes the whole
        YDataSet. In includes the following information:
        - the start of a time interval
        - the end of a time interval
        - the minimal value observed during the time interval
        - the average value observed during the time interval
        - the maximal value observed during the time interval

        This summary is available as soon as loadMore() has
        been called for the first time.

        @return an YMeasure object
        """
        return self._aio.get_summary()

    def get_preview(self) -> list[YMeasure]:
        """
        Returns a condensed version of the measures that can
        retrieved in this YDataSet, as a list of YMeasure
        objects. Each item includes:
        - the start of a time interval
        - the end of a time interval
        - the minimal value observed during the time interval
        - the average value observed during the time interval
        - the maximal value observed during the time interval

        This preview is available as soon as loadMore() has
        been called for the first time.

        @return a table of records, where each record depicts the
                measured values during a time interval

        On failure, throws an exception or returns an empty array.
        """
        return self._aio.get_preview()

    if not _DYNAMIC_HELPERS:
        def get_measuresAt(self, measure: YMeasure) -> list[YMeasure]:
            """
            Returns the detailed set of measures for the time interval corresponding
            to a given condensed measures previously returned by get_preview().
            The result is provided as a list of YMeasure objects.

            @param measure : condensed measure from the list previously returned by
                    get_preview().

            @return a table of records, where each record depicts the
                    measured values during a time interval

            On failure, throws an exception or returns an empty array.
            """
            return self._run(self._aio.get_measuresAt(measure))

    def get_measures(self) -> list[YMeasure]:
        """
        Returns all measured values currently available for this DataSet,
        as a list of YMeasure objects. Each item includes:
        - the start of the measure time interval
        - the end of the measure time interval
        - the minimal value observed during the time interval
        - the average value observed during the time interval
        - the maximal value observed during the time interval

        Before calling this method, you should call loadMore()
        to load data from the device. You may have to call loadMore()
        several time until all rows are loaded, but you can start
        looking at available data rows before the load is complete.

        The oldest measures are always loaded first, and the most
        recent measures will be loaded last. As a result, timestamps
        are normally sorted in ascending order within the measure table,
        unless there was an unexpected adjustment of the datalogger UTC
        clock.

        @return a table of records, where each record depicts the
                measured value for a given time interval

        On failure, throws an exception or returns an empty array.
        """
        return self._aio.get_measures()

    # --- (end of generated code: YDataSet implementation)


# --- (generated code: YDataLogger class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YDataLoggerValueCallback = Union[Callable[['YDataLogger', str], Any], None]
    except TypeError:
        YDataLoggerValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YDataLogger(YFunction):
    """
    A non-volatile memory for storing ongoing measured data is available on most Yoctopuce
    sensors. Recording can happen automatically, without requiring a permanent
    connection to a computer.
    The YDataLogger class controls the global parameters of the internal data
    logger. Recording control (start/stop) as well as data retrieval is done at
    sensor objects level.

    """
    _aio: YDataLogger_aio
    # --- (end of generated code: YDataLogger class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YDataLogger return codes)
        CURRENTRUNINDEX_INVALID: Final[int] = YAPI.INVALID_UINT
        TIMEUTC_INVALID: Final[int] = YAPI.INVALID_LONG
        USAGE_INVALID: Final[int] = YAPI.INVALID_UINT
        RECORDING_OFF: Final[int] = 0
        RECORDING_ON: Final[int] = 1
        RECORDING_PENDING: Final[int] = 2
        RECORDING_INVALID: Final[int] = -1
        AUTOSTART_OFF: Final[int] = 0
        AUTOSTART_ON: Final[int] = 1
        AUTOSTART_INVALID: Final[int] = -1
        BEACONDRIVEN_OFF: Final[int] = 0
        BEACONDRIVEN_ON: Final[int] = 1
        BEACONDRIVEN_INVALID: Final[int] = -1
        CLEARHISTORY_FALSE: Final[int] = 0
        CLEARHISTORY_TRUE: Final[int] = 1
        CLEARHISTORY_INVALID: Final[int] = -1
        # --- (end of generated code: YDataLogger return codes)

        # --- (generated code: YDataLogger implementation)

    @classmethod
    def FindDataLogger(cls, func: str) -> YDataLogger:
        """
        Retrieves a data logger for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the data logger is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDataLogger.isOnline() to test if the data logger is
        indeed online at a given time. In case of ambiguity when looking for
        a data logger by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the data logger, for instance
                LIGHTMK4.dataLogger.

        @return a YDataLogger object allowing you to drive the data logger.
        """
        return cls._proxy(cls, YDataLogger_aio.FindDataLoggerInContext(YAPI_aio, func))

    @classmethod
    def FindDataLoggerInContext(cls, yctx: YAPIContext, func: str) -> YDataLogger:
        """
        Retrieves a data logger for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the data logger is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDataLogger.isOnline() to test if the data logger is
        indeed online at a given time. In case of ambiguity when looking for
        a data logger by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the data logger, for instance
                LIGHTMK4.dataLogger.

        @return a YDataLogger object allowing you to drive the data logger.
        """
        return cls._proxy(cls, YDataLogger_aio.FindDataLoggerInContext(yctx._aio, func))

    @classmethod
    def FirstDataLogger(cls) -> Union[YDataLogger, None]:
        """
        Starts the enumeration of data loggers currently accessible.
        Use the method YDataLogger.nextDataLogger() to iterate on
        next data loggers.

        @return a pointer to a YDataLogger object, corresponding to
                the first data logger currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDataLogger_aio.FirstDataLoggerInContext(YAPI_aio))

    @classmethod
    def FirstDataLoggerInContext(cls, yctx: YAPIContext) -> Union[YDataLogger, None]:
        """
        Starts the enumeration of data loggers currently accessible.
        Use the method YDataLogger.nextDataLogger() to iterate on
        next data loggers.

        @param yctx : a YAPI context.

        @return a pointer to a YDataLogger object, corresponding to
                the first data logger currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YDataLogger_aio.FirstDataLoggerInContext(yctx._aio))

    def nextDataLogger(self) -> Union[YDataLogger, None]:
        """
        Continues the enumeration of data loggers started using yFirstDataLogger().
        Caution: You can't make any assumption about the returned data loggers order.
        If you want to find a specific a data logger, use DataLogger.findDataLogger()
        and a hardwareID or a logical name.

        @return a pointer to a YDataLogger object, corresponding to
                a data logger currently online, or a None pointer
                if there are no more data loggers to enumerate.
        """
        return self._proxy(type(self), self._aio.nextDataLogger())

    if not _DYNAMIC_HELPERS:
        def get_currentRunIndex(self) -> int:
            """
            Returns the current run number, corresponding to the number of times the module was
            powered on with the dataLogger enabled at some point.

            @return an integer corresponding to the current run number, corresponding to the number of times the module was
                    powered on with the dataLogger enabled at some point

            On failure, throws an exception or returns YDataLogger.CURRENTRUNINDEX_INVALID.
            """
            return self._run(self._aio.get_currentRunIndex())

    if not _DYNAMIC_HELPERS:
        def get_timeUTC(self) -> int:
            """
            Returns the Unix timestamp for current UTC time, if known.

            @return an integer corresponding to the Unix timestamp for current UTC time, if known

            On failure, throws an exception or returns YDataLogger.TIMEUTC_INVALID.
            """
            return self._run(self._aio.get_timeUTC())

    if not _DYNAMIC_HELPERS:
        def set_timeUTC(self, newval: int) -> int:
            """
            Changes the current UTC time reference used for recorded data.

            @param newval : an integer corresponding to the current UTC time reference used for recorded data

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_timeUTC(newval))

    if not _DYNAMIC_HELPERS:
        def get_recording(self) -> int:
            """
            Returns the current activation state of the data logger.

            @return a value among YDataLogger.RECORDING_OFF, YDataLogger.RECORDING_ON and
            YDataLogger.RECORDING_PENDING corresponding to the current activation state of the data logger

            On failure, throws an exception or returns YDataLogger.RECORDING_INVALID.
            """
            return self._run(self._aio.get_recording())

    if not _DYNAMIC_HELPERS:
        def set_recording(self, newval: int) -> int:
            """
            Changes the activation state of the data logger to start/stop recording data.

            @param newval : a value among YDataLogger.RECORDING_OFF, YDataLogger.RECORDING_ON and
            YDataLogger.RECORDING_PENDING corresponding to the activation state of the data logger to
            start/stop recording data

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_recording(newval))

    if not _DYNAMIC_HELPERS:
        def get_autoStart(self) -> int:
            """
            Returns the default activation state of the data logger on power up.

            @return either YDataLogger.AUTOSTART_OFF or YDataLogger.AUTOSTART_ON, according to the default
            activation state of the data logger on power up

            On failure, throws an exception or returns YDataLogger.AUTOSTART_INVALID.
            """
            return self._run(self._aio.get_autoStart())

    if not _DYNAMIC_HELPERS:
        def set_autoStart(self, newval: int) -> int:
            """
            Changes the default activation state of the data logger on power up.
            Do not forget to call the saveToFlash() method of the module to save the
            configuration change.  Note: if the device doesn't have any time source at his disposal when
            starting up, it will wait for ~8 seconds before automatically starting to record  with
            an arbitrary timestamp

            @param newval : either YDataLogger.AUTOSTART_OFF or YDataLogger.AUTOSTART_ON, according to the
            default activation state of the data logger on power up

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_autoStart(newval))

    if not _DYNAMIC_HELPERS:
        def get_beaconDriven(self) -> int:
            """
            Returns true if the data logger is synchronised with the localization beacon.

            @return either YDataLogger.BEACONDRIVEN_OFF or YDataLogger.BEACONDRIVEN_ON, according to true if
            the data logger is synchronised with the localization beacon

            On failure, throws an exception or returns YDataLogger.BEACONDRIVEN_INVALID.
            """
            return self._run(self._aio.get_beaconDriven())

    if not _DYNAMIC_HELPERS:
        def set_beaconDriven(self, newval: int) -> int:
            """
            Changes the type of synchronisation of the data logger.
            Remember to call the saveToFlash() method of the module if the
            modification must be kept.

            @param newval : either YDataLogger.BEACONDRIVEN_OFF or YDataLogger.BEACONDRIVEN_ON, according to
            the type of synchronisation of the data logger

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_beaconDriven(newval))

    if not _DYNAMIC_HELPERS:
        def get_usage(self) -> int:
            """
            Returns the percentage of datalogger memory in use.

            @return an integer corresponding to the percentage of datalogger memory in use

            On failure, throws an exception or returns YDataLogger.USAGE_INVALID.
            """
            return self._run(self._aio.get_usage())

    if not _DYNAMIC_HELPERS:
        def set_clearHistory(self, newval: int) -> int:
            return self._run(self._aio.set_clearHistory(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YDataLoggerValueCallback) -> int:
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
        def forgetAllDataStreams(self) -> int:
            """
            Clears the data logger memory and discards all recorded data streams.
            This method also resets the current run index to zero.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.forgetAllDataStreams())

    # --- (end of generated code: YDataLogger implementation)

