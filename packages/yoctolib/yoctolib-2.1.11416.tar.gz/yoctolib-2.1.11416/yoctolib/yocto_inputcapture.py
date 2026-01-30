# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_inputcapture.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YInputCapture API for InputCapture functions
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
Yoctopuce library: High-level API for YInputCapture
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_inputcapture_aio
provides: YInputCapture YInputCaptureData
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

from .yocto_inputcapture_aio import (
    YInputCapture as YInputCapture_aio,
    YInputCaptureData
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (generated code: YInputCapture class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YInputCaptureValueCallback = Union[Callable[['YInputCapture', str], Any], None]
    except TypeError:
        YInputCaptureValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YInputCapture(YFunction):
    """
    The YInputCapture class allows you to access data samples
    measured by a Yoctopuce electrical sensor. The data capture can be
    triggered manually, or be configured to detect specific events.

    """
    _aio: YInputCapture_aio
    # --- (end of generated code: YInputCapture class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YInputCapture return codes)
        LASTCAPTURETIME_INVALID: Final[int] = YAPI.INVALID_LONG
        NSAMPLES_INVALID: Final[int] = YAPI.INVALID_UINT
        SAMPLINGRATE_INVALID: Final[int] = YAPI.INVALID_UINT
        CONDVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CONDALIGN_INVALID: Final[int] = YAPI.INVALID_UINT
        CONDVALUEATSTARTUP_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CAPTURETYPE_NONE: Final[int] = 0
        CAPTURETYPE_TIMED: Final[int] = 1
        CAPTURETYPE_V_MAX: Final[int] = 2
        CAPTURETYPE_V_MIN: Final[int] = 3
        CAPTURETYPE_I_MAX: Final[int] = 4
        CAPTURETYPE_I_MIN: Final[int] = 5
        CAPTURETYPE_P_MAX: Final[int] = 6
        CAPTURETYPE_P_MIN: Final[int] = 7
        CAPTURETYPE_V_AVG_MAX: Final[int] = 8
        CAPTURETYPE_V_AVG_MIN: Final[int] = 9
        CAPTURETYPE_V_RMS_MAX: Final[int] = 10
        CAPTURETYPE_V_RMS_MIN: Final[int] = 11
        CAPTURETYPE_I_AVG_MAX: Final[int] = 12
        CAPTURETYPE_I_AVG_MIN: Final[int] = 13
        CAPTURETYPE_I_RMS_MAX: Final[int] = 14
        CAPTURETYPE_I_RMS_MIN: Final[int] = 15
        CAPTURETYPE_P_AVG_MAX: Final[int] = 16
        CAPTURETYPE_P_AVG_MIN: Final[int] = 17
        CAPTURETYPE_PF_MIN: Final[int] = 18
        CAPTURETYPE_DPF_MIN: Final[int] = 19
        CAPTURETYPE_INVALID: Final[int] = -1
        CAPTURETYPEATSTARTUP_NONE: Final[int] = 0
        CAPTURETYPEATSTARTUP_TIMED: Final[int] = 1
        CAPTURETYPEATSTARTUP_V_MAX: Final[int] = 2
        CAPTURETYPEATSTARTUP_V_MIN: Final[int] = 3
        CAPTURETYPEATSTARTUP_I_MAX: Final[int] = 4
        CAPTURETYPEATSTARTUP_I_MIN: Final[int] = 5
        CAPTURETYPEATSTARTUP_P_MAX: Final[int] = 6
        CAPTURETYPEATSTARTUP_P_MIN: Final[int] = 7
        CAPTURETYPEATSTARTUP_V_AVG_MAX: Final[int] = 8
        CAPTURETYPEATSTARTUP_V_AVG_MIN: Final[int] = 9
        CAPTURETYPEATSTARTUP_V_RMS_MAX: Final[int] = 10
        CAPTURETYPEATSTARTUP_V_RMS_MIN: Final[int] = 11
        CAPTURETYPEATSTARTUP_I_AVG_MAX: Final[int] = 12
        CAPTURETYPEATSTARTUP_I_AVG_MIN: Final[int] = 13
        CAPTURETYPEATSTARTUP_I_RMS_MAX: Final[int] = 14
        CAPTURETYPEATSTARTUP_I_RMS_MIN: Final[int] = 15
        CAPTURETYPEATSTARTUP_P_AVG_MAX: Final[int] = 16
        CAPTURETYPEATSTARTUP_P_AVG_MIN: Final[int] = 17
        CAPTURETYPEATSTARTUP_PF_MIN: Final[int] = 18
        CAPTURETYPEATSTARTUP_DPF_MIN: Final[int] = 19
        CAPTURETYPEATSTARTUP_INVALID: Final[int] = -1
        # --- (end of generated code: YInputCapture return codes)

    # --- (generated code: YInputCapture implementation)

    @classmethod
    def FindInputCapture(cls, func: str) -> YInputCapture:
        """
        Retrieves an instant snapshot trigger for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the instant snapshot trigger is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YInputCapture.isOnline() to test if the instant snapshot trigger is
        indeed online at a given time. In case of ambiguity when looking for
        an instant snapshot trigger by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the instant snapshot trigger, for instance
                MyDevice.inputCapture.

        @return a YInputCapture object allowing you to drive the instant snapshot trigger.
        """
        return cls._proxy(cls, YInputCapture_aio.FindInputCaptureInContext(YAPI_aio, func))

    @classmethod
    def FindInputCaptureInContext(cls, yctx: YAPIContext, func: str) -> YInputCapture:
        """
        Retrieves an instant snapshot trigger for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the instant snapshot trigger is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YInputCapture.isOnline() to test if the instant snapshot trigger is
        indeed online at a given time. In case of ambiguity when looking for
        an instant snapshot trigger by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the instant snapshot trigger, for instance
                MyDevice.inputCapture.

        @return a YInputCapture object allowing you to drive the instant snapshot trigger.
        """
        return cls._proxy(cls, YInputCapture_aio.FindInputCaptureInContext(yctx._aio, func))

    @classmethod
    def FirstInputCapture(cls) -> Union[YInputCapture, None]:
        """
        Starts the enumeration of instant snapshot triggers currently accessible.
        Use the method YInputCapture.nextInputCapture() to iterate on
        next instant snapshot triggers.

        @return a pointer to a YInputCapture object, corresponding to
                the first instant snapshot trigger currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YInputCapture_aio.FirstInputCaptureInContext(YAPI_aio))

    @classmethod
    def FirstInputCaptureInContext(cls, yctx: YAPIContext) -> Union[YInputCapture, None]:
        """
        Starts the enumeration of instant snapshot triggers currently accessible.
        Use the method YInputCapture.nextInputCapture() to iterate on
        next instant snapshot triggers.

        @param yctx : a YAPI context.

        @return a pointer to a YInputCapture object, corresponding to
                the first instant snapshot trigger currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YInputCapture_aio.FirstInputCaptureInContext(yctx._aio))

    def nextInputCapture(self) -> Union[YInputCapture, None]:
        """
        Continues the enumeration of instant snapshot triggers started using yFirstInputCapture().
        Caution: You can't make any assumption about the returned instant snapshot triggers order.
        If you want to find a specific an instant snapshot trigger, use InputCapture.findInputCapture()
        and a hardwareID or a logical name.

        @return a pointer to a YInputCapture object, corresponding to
                an instant snapshot trigger currently online, or a None pointer
                if there are no more instant snapshot triggers to enumerate.
        """
        return self._proxy(type(self), self._aio.nextInputCapture())

    if not _DYNAMIC_HELPERS:
        def get_lastCaptureTime(self) -> int:
            """
            Returns the number of elapsed milliseconds between the module power on
            and the last capture (time of trigger), or zero if no capture has been done.

            @return an integer corresponding to the number of elapsed milliseconds between the module power on
                    and the last capture (time of trigger), or zero if no capture has been done

            On failure, throws an exception or returns YInputCapture.LASTCAPTURETIME_INVALID.
            """
            return self._run(self._aio.get_lastCaptureTime())

    if not _DYNAMIC_HELPERS:
        def get_nSamples(self) -> int:
            """
            Returns the number of samples that will be captured.

            @return an integer corresponding to the number of samples that will be captured

            On failure, throws an exception or returns YInputCapture.NSAMPLES_INVALID.
            """
            return self._run(self._aio.get_nSamples())

    if not _DYNAMIC_HELPERS:
        def set_nSamples(self, newval: int) -> int:
            """
            Changes the type of automatic conditional capture.
            The maximum number of samples depends on the device memory.

            If you want the change to be kept after a device reboot,
            make sure  to call the matching module saveToFlash().

            @param newval : an integer corresponding to the type of automatic conditional capture

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_nSamples(newval))

    if not _DYNAMIC_HELPERS:
        def get_samplingRate(self) -> int:
            """
            Returns the sampling frequency, in Hz.

            @return an integer corresponding to the sampling frequency, in Hz

            On failure, throws an exception or returns YInputCapture.SAMPLINGRATE_INVALID.
            """
            return self._run(self._aio.get_samplingRate())

    if not _DYNAMIC_HELPERS:
        def get_captureType(self) -> int:
            """
            Returns the type of automatic conditional capture.

            @return a value among YInputCapture.CAPTURETYPE_NONE, YInputCapture.CAPTURETYPE_TIMED,
            YInputCapture.CAPTURETYPE_V_MAX, YInputCapture.CAPTURETYPE_V_MIN, YInputCapture.CAPTURETYPE_I_MAX,
            YInputCapture.CAPTURETYPE_I_MIN, YInputCapture.CAPTURETYPE_P_MAX, YInputCapture.CAPTURETYPE_P_MIN,
            YInputCapture.CAPTURETYPE_V_AVG_MAX, YInputCapture.CAPTURETYPE_V_AVG_MIN,
            YInputCapture.CAPTURETYPE_V_RMS_MAX, YInputCapture.CAPTURETYPE_V_RMS_MIN,
            YInputCapture.CAPTURETYPE_I_AVG_MAX, YInputCapture.CAPTURETYPE_I_AVG_MIN,
            YInputCapture.CAPTURETYPE_I_RMS_MAX, YInputCapture.CAPTURETYPE_I_RMS_MIN,
            YInputCapture.CAPTURETYPE_P_AVG_MAX, YInputCapture.CAPTURETYPE_P_AVG_MIN,
            YInputCapture.CAPTURETYPE_PF_MIN and YInputCapture.CAPTURETYPE_DPF_MIN corresponding to the type of
            automatic conditional capture

            On failure, throws an exception or returns YInputCapture.CAPTURETYPE_INVALID.
            """
            return self._run(self._aio.get_captureType())

    if not _DYNAMIC_HELPERS:
        def set_captureType(self, newval: int) -> int:
            """
            Changes the type of automatic conditional capture.

            @param newval : a value among YInputCapture.CAPTURETYPE_NONE, YInputCapture.CAPTURETYPE_TIMED,
            YInputCapture.CAPTURETYPE_V_MAX, YInputCapture.CAPTURETYPE_V_MIN, YInputCapture.CAPTURETYPE_I_MAX,
            YInputCapture.CAPTURETYPE_I_MIN, YInputCapture.CAPTURETYPE_P_MAX, YInputCapture.CAPTURETYPE_P_MIN,
            YInputCapture.CAPTURETYPE_V_AVG_MAX, YInputCapture.CAPTURETYPE_V_AVG_MIN,
            YInputCapture.CAPTURETYPE_V_RMS_MAX, YInputCapture.CAPTURETYPE_V_RMS_MIN,
            YInputCapture.CAPTURETYPE_I_AVG_MAX, YInputCapture.CAPTURETYPE_I_AVG_MIN,
            YInputCapture.CAPTURETYPE_I_RMS_MAX, YInputCapture.CAPTURETYPE_I_RMS_MIN,
            YInputCapture.CAPTURETYPE_P_AVG_MAX, YInputCapture.CAPTURETYPE_P_AVG_MIN,
            YInputCapture.CAPTURETYPE_PF_MIN and YInputCapture.CAPTURETYPE_DPF_MIN corresponding to the type of
            automatic conditional capture

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_captureType(newval))

    if not _DYNAMIC_HELPERS:
        def set_condValue(self, newval: float) -> int:
            """
            Changes current threshold value for automatic conditional capture.

            @param newval : a floating point number corresponding to current threshold value for automatic
            conditional capture

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_condValue(newval))

    if not _DYNAMIC_HELPERS:
        def get_condValue(self) -> float:
            """
            Returns current threshold value for automatic conditional capture.

            @return a floating point number corresponding to current threshold value for automatic conditional capture

            On failure, throws an exception or returns YInputCapture.CONDVALUE_INVALID.
            """
            return self._run(self._aio.get_condValue())

    if not _DYNAMIC_HELPERS:
        def get_condAlign(self) -> int:
            """
            Returns the relative position of the trigger event within the capture window.
            When the value is 50%, the capture is centered on the event.

            @return an integer corresponding to the relative position of the trigger event within the capture window

            On failure, throws an exception or returns YInputCapture.CONDALIGN_INVALID.
            """
            return self._run(self._aio.get_condAlign())

    if not _DYNAMIC_HELPERS:
        def set_condAlign(self, newval: int) -> int:
            """
            Changes the relative position of the trigger event within the capture window.
            The new value must be between 10% (on the left) and 90% (on the right).
            When the value is 50%, the capture is centered on the event.

            If you want the change to be kept after a device reboot,
            make sure  to call the matching module saveToFlash().

            @param newval : an integer corresponding to the relative position of the trigger event within the capture window

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_condAlign(newval))

    if not _DYNAMIC_HELPERS:
        def get_captureTypeAtStartup(self) -> int:
            """
            Returns the type of automatic conditional capture
            applied at device power on.

            @return a value among YInputCapture.CAPTURETYPEATSTARTUP_NONE,
            YInputCapture.CAPTURETYPEATSTARTUP_TIMED, YInputCapture.CAPTURETYPEATSTARTUP_V_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_V_MIN, YInputCapture.CAPTURETYPEATSTARTUP_I_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_I_MIN, YInputCapture.CAPTURETYPEATSTARTUP_P_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_P_MIN, YInputCapture.CAPTURETYPEATSTARTUP_V_AVG_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_V_AVG_MIN, YInputCapture.CAPTURETYPEATSTARTUP_V_RMS_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_V_RMS_MIN, YInputCapture.CAPTURETYPEATSTARTUP_I_AVG_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_I_AVG_MIN, YInputCapture.CAPTURETYPEATSTARTUP_I_RMS_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_I_RMS_MIN, YInputCapture.CAPTURETYPEATSTARTUP_P_AVG_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_P_AVG_MIN, YInputCapture.CAPTURETYPEATSTARTUP_PF_MIN and
            YInputCapture.CAPTURETYPEATSTARTUP_DPF_MIN corresponding to the type of automatic conditional capture
                    applied at device power on

            On failure, throws an exception or returns YInputCapture.CAPTURETYPEATSTARTUP_INVALID.
            """
            return self._run(self._aio.get_captureTypeAtStartup())

    if not _DYNAMIC_HELPERS:
        def set_captureTypeAtStartup(self, newval: int) -> int:
            """
            Changes the type of automatic conditional capture
            applied at device power on.

            If you want the change to be kept after a device reboot,
            make sure  to call the matching module saveToFlash().

            @param newval : a value among YInputCapture.CAPTURETYPEATSTARTUP_NONE,
            YInputCapture.CAPTURETYPEATSTARTUP_TIMED, YInputCapture.CAPTURETYPEATSTARTUP_V_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_V_MIN, YInputCapture.CAPTURETYPEATSTARTUP_I_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_I_MIN, YInputCapture.CAPTURETYPEATSTARTUP_P_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_P_MIN, YInputCapture.CAPTURETYPEATSTARTUP_V_AVG_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_V_AVG_MIN, YInputCapture.CAPTURETYPEATSTARTUP_V_RMS_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_V_RMS_MIN, YInputCapture.CAPTURETYPEATSTARTUP_I_AVG_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_I_AVG_MIN, YInputCapture.CAPTURETYPEATSTARTUP_I_RMS_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_I_RMS_MIN, YInputCapture.CAPTURETYPEATSTARTUP_P_AVG_MAX,
            YInputCapture.CAPTURETYPEATSTARTUP_P_AVG_MIN, YInputCapture.CAPTURETYPEATSTARTUP_PF_MIN and
            YInputCapture.CAPTURETYPEATSTARTUP_DPF_MIN corresponding to the type of automatic conditional capture
                    applied at device power on

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_captureTypeAtStartup(newval))

    if not _DYNAMIC_HELPERS:
        def set_condValueAtStartup(self, newval: float) -> int:
            """
            Changes current threshold value for automatic conditional
            capture applied at device power on.

            If you want the change to be kept after a device reboot,
            make sure  to call the matching module saveToFlash().

            @param newval : a floating point number corresponding to current threshold value for automatic conditional
                    capture applied at device power on

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_condValueAtStartup(newval))

    if not _DYNAMIC_HELPERS:
        def get_condValueAtStartup(self) -> float:
            """
            Returns the threshold value for automatic conditional
            capture applied at device power on.

            @return a floating point number corresponding to the threshold value for automatic conditional
                    capture applied at device power on

            On failure, throws an exception or returns YInputCapture.CONDVALUEATSTARTUP_INVALID.
            """
            return self._run(self._aio.get_condValueAtStartup())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YInputCaptureValueCallback) -> int:
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
        def get_lastCapture(self) -> YInputCaptureData:
            """
            Returns all details about the last automatic input capture.

            @return an YInputCaptureData object including
                    data series and all related meta-information.
                    On failure, throws an exception or returns an capture object.
            """
            return self._run(self._aio.get_lastCapture())

    if not _DYNAMIC_HELPERS:
        def get_immediateCapture(self, msDuration: int) -> YInputCaptureData:
            """
            Returns a new immediate capture of the device inputs.

            @param msDuration : duration of the capture window,
                    in milliseconds (eg. between 20 and 1000).

            @return an YInputCaptureData object including
                    data series for the specified duration.
                    On failure, throws an exception or returns an capture object.
            """
            return self._run(self._aio.get_immediateCapture(msDuration))

    # --- (end of generated code: YInputCapture implementation)

