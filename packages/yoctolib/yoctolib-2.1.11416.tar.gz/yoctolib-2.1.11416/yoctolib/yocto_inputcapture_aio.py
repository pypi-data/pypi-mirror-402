# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_inputcapture_aio.py 69442 2025-10-16 08:53:14Z mvuilleu $
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
Yoctopuce library: Asyncio implementation of YInputCapture
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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

# --- (generated code: YInputCaptureData class start)
# noinspection PyProtectedMember
class YInputCaptureData:
    """
    InputCaptureData objects represent raw data
    sampled by the analog/digital converter present in
    a Yoctopuce electrical sensor. When several inputs
    are samples simultaneously, their data are provided
    as distinct series.

    """
    # --- (end of generated code: YInputCaptureData class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YInputCaptureData return codes)
        pass
        # --- (end of generated code: YInputCaptureData return codes)
        pass

    # --- (generated code: YInputCaptureData attributes declaration)
    _fmt: int
    _var1size: int
    _var2size: int
    _var3size: int
    _nVars: int
    _recOfs: int
    _nRecs: int
    _samplesPerSec: int
    _trigType: int
    _trigVal: float
    _trigPos: int
    _trigUTC: float
    _var1unit: str
    _var2unit: str
    _var3unit: str
    _var1samples: list[float]
    _var2samples: list[float]
    _var3samples: list[float]
    # --- (end of generated code: YInputCaptureData attributes declaration)

    def __init__(self, yfun: YFunction, json_data: xarray):
        # --- (generated code: YInputCaptureData constructor)
        self._fmt = 0
        self._var1size = 0
        self._var2size = 0
        self._var3size = 0
        self._nVars = 0
        self._recOfs = 0
        self._nRecs = 0
        self._samplesPerSec = 0
        self._trigType = 0
        self._trigVal = 0.0
        self._trigPos = 0
        self._trigUTC = 0.0
        self._var1unit = ''
        self._var2unit = ''
        self._var3unit = ''
        self._var1samples = []
        self._var2samples = []
        self._var3samples = []
        # --- (end of generated code: YInputCaptureData constructor)
        self._decodeSnapBin(json_data)

    @staticmethod
    def _throw(errType: int, errMsg: str):
        if not YAPI._ExceptionsDisabled:
            raise YAPI_Exception(errType, errMsg)

    # --- (generated code: YInputCaptureData implementation)
    def _decodeU16(self, sdata: xarray, ofs: int) -> int:
        v: int
        v = sdata[ofs]
        v = v + 256 * sdata[ofs+1]
        return v

    def _decodeU32(self, sdata: xarray, ofs: int) -> float:
        v: float
        v = self._decodeU16(sdata, ofs)
        v = v + 65536.0 * self._decodeU16(sdata, ofs+2)
        return v

    def _decodeVal(self, sdata: xarray, ofs: int, len: int) -> float:
        v: float
        b: float
        v = self._decodeU16(sdata, ofs)
        b = 65536.0
        ofs = ofs + 2
        len = len - 2
        while len > 0:
            v = v + b * sdata[ofs]
            b = b * 256
            ofs = ofs + 1
            len = len - 1
        if v > (b/2):
            # negative number
            v = v - b
        return v

    def _decodeSnapBin(self, sdata: xarray) -> int:
        buffSize: int
        recOfs: int
        ms: int
        recSize: int
        count: int
        mult1: int
        mult2: int
        mult3: int
        v: float

        buffSize = len(sdata)
        if not (buffSize >= 24):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid snapshot data (too short)")
            return YAPI.INVALID_ARGUMENT
        self._fmt = sdata[0]
        self._var1size = sdata[1] - 48
        self._var2size = sdata[2] - 48
        self._var3size = sdata[3] - 48
        if not (self._fmt == 83):
            self._throw(YAPI.INVALID_ARGUMENT, "Unsupported snapshot format")
            return YAPI.INVALID_ARGUMENT
        if not ((self._var1size >= 2) and(self._var1size <= 4)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid sample size")
            return YAPI.INVALID_ARGUMENT
        if not ((self._var2size >= 0) and(self._var1size <= 4)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid sample size")
            return YAPI.INVALID_ARGUMENT
        if not ((self._var3size >= 0) and(self._var1size <= 4)):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid sample size")
            return YAPI.INVALID_ARGUMENT
        if self._var2size == 0:
            self._nVars = 1
        else:
            if self._var3size == 0:
                self._nVars = 2
            else:
                self._nVars = 3
        recSize = self._var1size + self._var2size + self._var3size
        self._recOfs = self._decodeU16(sdata, 4)
        self._nRecs = self._decodeU16(sdata, 6)
        self._samplesPerSec = self._decodeU16(sdata, 8)
        self._trigType = self._decodeU16(sdata, 10)
        self._trigVal = self._decodeVal(sdata, 12, 4) / 1000
        self._trigPos = self._decodeU16(sdata, 16)
        ms = self._decodeU16(sdata, 18)
        self._trigUTC = self._decodeVal(sdata, 20, 4)
        self._trigUTC = self._trigUTC + (ms / 1000.0)
        recOfs = 24
        while sdata[recOfs] >= 32:
            self._var1unit = "%s%c" % (self._var1unit, sdata[recOfs])
            recOfs = recOfs + 1
        if self._var2size > 0:
            recOfs = recOfs + 1
            while sdata[recOfs] >= 32:
                self._var2unit = "%s%c" % (self._var2unit, sdata[recOfs])
                recOfs = recOfs + 1
        if self._var3size > 0:
            recOfs = recOfs + 1
            while sdata[recOfs] >= 32:
                self._var3unit = "%s%c" % (self._var3unit, sdata[recOfs])
                recOfs = recOfs + 1
        if (recOfs & 1) == 1:
            # align to next word
            recOfs = recOfs + 1
        mult1 = 1
        mult2 = 1
        mult3 = 1
        if recOfs < self._recOfs:
            # load optional value multiplier
            mult1 = self._decodeU16(sdata, recOfs)
            recOfs = recOfs + 2
            if self._var2size > 0:
                mult2 = self._decodeU16(sdata, recOfs)
                recOfs = recOfs + 2
            if self._var3size > 0:
                mult3 = self._decodeU16(sdata, recOfs)
                recOfs = recOfs + 2

        recOfs = self._recOfs
        count = self._nRecs
        while (count > 0) and(recOfs + self._var1size <= buffSize):
            v = self._decodeVal(sdata, recOfs, self._var1size) / 1000.0
            self._var1samples.append(v*mult1)
            recOfs = recOfs + recSize

        if self._var2size > 0:
            recOfs = self._recOfs + self._var1size
            count = self._nRecs
            while (count > 0) and(recOfs + self._var2size <= buffSize):
                v = self._decodeVal(sdata, recOfs, self._var2size) / 1000.0
                self._var2samples.append(v*mult2)
                recOfs = recOfs + recSize
        if self._var3size > 0:
            recOfs = self._recOfs + self._var1size + self._var2size
            count = self._nRecs
            while (count > 0) and(recOfs + self._var3size <= buffSize):
                v = self._decodeVal(sdata, recOfs, self._var3size) / 1000.0
                self._var3samples.append(v*mult3)
                recOfs = recOfs + recSize
        return YAPI.SUCCESS

    def get_serieCount(self) -> int:
        """
        Returns the number of series available in the capture.

        @return an integer corresponding to the number of
                simultaneous data series available.
        """
        return self._nVars

    def get_recordCount(self) -> int:
        """
        Returns the number of records captured (in a serie).
        In the exceptional case where it was not possible
        to transfer all data in time, the number of records
        actually present in the series might be lower than
        the number of records captured

        @return an integer corresponding to the number of
                records expected in each serie.
        """
        return self._nRecs

    def get_samplingRate(self) -> int:
        """
        Returns the effective sampling rate of the device.

        @return an integer corresponding to the number of
                samples taken each second.
        """
        return self._samplesPerSec

    def get_captureType(self) -> int:
        """
        Returns the type of automatic conditional capture
        that triggered the capture of this data sequence.

        @return the type of conditional capture.
        """
        return int(self._trigType)

    def get_triggerValue(self) -> float:
        """
        Returns the threshold value that triggered
        this automatic conditional capture, if it was
        not an instant captured triggered manually.

        @return the conditional threshold value
                at the time of capture.
        """
        return self._trigVal

    def get_triggerPosition(self) -> int:
        """
        Returns the index in the series of the sample
        corresponding to the exact time when the capture
        was triggered. In case of trigger based on average
        or RMS value, the trigger index corresponds to
        the end of the averaging period.

        @return an integer corresponding to a position
                in the data serie.
        """
        return self._trigPos

    def get_triggerRealTimeUTC(self) -> float:
        """
        Returns the absolute time when the capture was
        triggered, as a Unix timestamp. Milliseconds are
        included in this timestamp (floating-point number).

        @return a floating-point number corresponding to
                the number of seconds between the Jan 1,
                1970 and the moment where the capture
                was triggered.
        """
        return self._trigUTC

    def get_serie1Unit(self) -> str:
        """
        Returns the unit of measurement for data points in
        the first serie.

        @return a string containing to a physical unit of
                measurement.
        """
        return self._var1unit

    def get_serie2Unit(self) -> str:
        """
        Returns the unit of measurement for data points in
        the second serie.

        @return a string containing to a physical unit of
                measurement.
        """
        if not (self._nVars >= 2):
            self._throw(YAPI.INVALID_ARGUMENT, "There is no serie 2 in this capture data")
            return ""
        return self._var2unit

    def get_serie3Unit(self) -> str:
        """
        Returns the unit of measurement for data points in
        the third serie.

        @return a string containing to a physical unit of
                measurement.
        """
        if not (self._nVars >= 3):
            self._throw(YAPI.INVALID_ARGUMENT, "There is no serie 3 in this capture data")
            return ""
        return self._var3unit

    def get_serie1Values(self) -> list[float]:
        """
        Returns the sampled data corresponding to the first serie.
        The corresponding physical unit can be obtained
        using the method get_serie1Unit().

        @return a list of real numbers corresponding to all
                samples received for serie 1.

        On failure, throws an exception or returns an empty array.
        """
        return self._var1samples

    def get_serie2Values(self) -> list[float]:
        """
        Returns the sampled data corresponding to the second serie.
        The corresponding physical unit can be obtained
        using the method get_serie2Unit().

        @return a list of real numbers corresponding to all
                samples received for serie 2.

        On failure, throws an exception or returns an empty array.
        """
        if not (self._nVars >= 2):
            self._throw(YAPI.INVALID_ARGUMENT, "There is no serie 2 in this capture data")
            return self._var2samples
        return self._var2samples

    def get_serie3Values(self) -> list[float]:
        """
        Returns the sampled data corresponding to the third serie.
        The corresponding physical unit can be obtained
        using the method get_serie3Unit().

        @return a list of real numbers corresponding to all
                samples received for serie 3.

        On failure, throws an exception or returns an empty array.
        """
        if not (self._nVars >= 3):
            self._throw(YAPI.INVALID_ARGUMENT, "There is no serie 3 in this capture data")
            return self._var3samples
        return self._var3samples

    # --- (end of generated code: YInputCaptureData implementation)


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

    # --- (generated code: YInputCapture attributes declaration)
    _valueCallback: YInputCaptureValueCallback
    # --- (end of generated code: YInputCapture attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'InputCapture', func)
        # --- (generated code: YInputCapture constructor)
        # --- (end of generated code: YInputCapture constructor)

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
        return cls.FindInputCaptureInContext(YAPI, func)

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
        obj: Union[YInputCapture, None] = yctx._findInCache('InputCapture', func)
        if obj:
            return obj
        return YInputCapture(yctx, func)

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
        return cls.FirstInputCaptureInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('InputCapture')
        if hwid:
            return cls.FindInputCaptureInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('InputCapture', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindInputCaptureInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_lastCaptureTime(self) -> int:
        """
        Returns the number of elapsed milliseconds between the module power on
        and the last capture (time of trigger), or zero if no capture has been done.

        @return an integer corresponding to the number of elapsed milliseconds between the module power on
                and the last capture (time of trigger), or zero if no capture has been done

        On failure, throws an exception or returns YInputCapture.LASTCAPTURETIME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("lastCaptureTime")
        if json_val is None:
            return YInputCapture.LASTCAPTURETIME_INVALID
        return json_val

    async def get_nSamples(self) -> int:
        """
        Returns the number of samples that will be captured.

        @return an integer corresponding to the number of samples that will be captured

        On failure, throws an exception or returns YInputCapture.NSAMPLES_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("nSamples")
        if json_val is None:
            return YInputCapture.NSAMPLES_INVALID
        return json_val

    async def set_nSamples(self, newval: int) -> int:
        """
        Changes the type of automatic conditional capture.
        The maximum number of samples depends on the device memory.

        If you want the change to be kept after a device reboot,
        make sure  to call the matching module saveToFlash().

        @param newval : an integer corresponding to the type of automatic conditional capture

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("nSamples", rest_val)

    async def get_samplingRate(self) -> int:
        """
        Returns the sampling frequency, in Hz.

        @return an integer corresponding to the sampling frequency, in Hz

        On failure, throws an exception or returns YInputCapture.SAMPLINGRATE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("samplingRate")
        if json_val is None:
            return YInputCapture.SAMPLINGRATE_INVALID
        return json_val

    async def get_captureType(self) -> int:
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
        json_val: Union[int, None] = await self._fromCache("captureType")
        if json_val is None:
            return YInputCapture.CAPTURETYPE_INVALID
        return json_val

    async def set_captureType(self, newval: int) -> int:
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
        rest_val = str(newval)
        return await self._setAttr("captureType", rest_val)

    async def set_condValue(self, newval: float) -> int:
        """
        Changes current threshold value for automatic conditional capture.

        @param newval : a floating point number corresponding to current threshold value for automatic
        conditional capture

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("condValue", rest_val)

    async def get_condValue(self) -> float:
        """
        Returns current threshold value for automatic conditional capture.

        @return a floating point number corresponding to current threshold value for automatic conditional capture

        On failure, throws an exception or returns YInputCapture.CONDVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("condValue")
        if json_val is None:
            return YInputCapture.CONDVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_condAlign(self) -> int:
        """
        Returns the relative position of the trigger event within the capture window.
        When the value is 50%, the capture is centered on the event.

        @return an integer corresponding to the relative position of the trigger event within the capture window

        On failure, throws an exception or returns YInputCapture.CONDALIGN_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("condAlign")
        if json_val is None:
            return YInputCapture.CONDALIGN_INVALID
        return json_val

    async def set_condAlign(self, newval: int) -> int:
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
        rest_val = str(newval)
        return await self._setAttr("condAlign", rest_val)

    async def get_captureTypeAtStartup(self) -> int:
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
        json_val: Union[int, None] = await self._fromCache("captureTypeAtStartup")
        if json_val is None:
            return YInputCapture.CAPTURETYPEATSTARTUP_INVALID
        return json_val

    async def set_captureTypeAtStartup(self, newval: int) -> int:
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
        rest_val = str(newval)
        return await self._setAttr("captureTypeAtStartup", rest_val)

    async def set_condValueAtStartup(self, newval: float) -> int:
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
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("condValueAtStartup", rest_val)

    async def get_condValueAtStartup(self) -> float:
        """
        Returns the threshold value for automatic conditional
        capture applied at device power on.

        @return a floating point number corresponding to the threshold value for automatic conditional
                capture applied at device power on

        On failure, throws an exception or returns YInputCapture.CONDVALUEATSTARTUP_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("condValueAtStartup")
        if json_val is None:
            return YInputCapture.CONDVALUEATSTARTUP_INVALID
        return round(json_val / 65.536) / 1000.0

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YInputCaptureValueCallback) -> int:
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

    async def get_lastCapture(self) -> YInputCaptureData:
        """
        Returns all details about the last automatic input capture.

        @return an YInputCaptureData object including
                data series and all related meta-information.
                On failure, throws an exception or returns an capture object.
        """
        snapData: xarray

        snapData = await self._download("snap.bin")
        return YInputCaptureData(self, snapData)

    async def get_immediateCapture(self, msDuration: int) -> YInputCaptureData:
        """
        Returns a new immediate capture of the device inputs.

        @param msDuration : duration of the capture window,
                in milliseconds (eg. between 20 and 1000).

        @return an YInputCaptureData object including
                data series for the specified duration.
                On failure, throws an exception or returns an capture object.
        """
        snapUrl: str
        snapData: xarray
        snapStart: int
        if msDuration < 1:
            msDuration = 20
        if msDuration > 1000:
            msDuration = 1000
        snapStart = -msDuration // 2
        snapUrl = "snap.bin?t=%d&d=%d" % (snapStart, msDuration)

        snapData = await self._download(snapUrl)
        return YInputCaptureData(self, snapData)

    # --- (end of generated code: YInputCapture implementation)
