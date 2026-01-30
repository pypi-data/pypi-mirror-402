# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YGps
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
Yoctopuce library: Asyncio implementation of YGps
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YGps
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
    YAPIContext, YAPI, YAPI_Exception, HwId, hwid2str, YFunction
)

# --- (YGps class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YGpsValueCallback = Union[Callable[['YGps', str], Any], None]
    except TypeError:
        YGpsValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YGps(YFunction):
    """
    The YGps class allows you to retrieve positioning
    data from a GPS/GNSS sensor. This class can provides
    complete positioning information. However, if you
    wish to define callbacks on position changes or record
    the position in the datalogger, you
    should use the YLatitude et YLongitude classes.

    """
    # --- (end of YGps class start)
    if not _IS_MICROPYTHON:
        # --- (YGps return codes)
        SATCOUNT_INVALID: Final[int] = YAPI.INVALID_LONG
        SATPERCONST_INVALID: Final[int] = YAPI.INVALID_LONG
        GPSREFRESHRATE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        LATITUDE_INVALID: Final[str] = YAPI.INVALID_STRING
        LONGITUDE_INVALID: Final[str] = YAPI.INVALID_STRING
        DILUTION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        ALTITUDE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        GROUNDSPEED_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        DIRECTION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        UNIXTIME_INVALID: Final[int] = YAPI.INVALID_LONG
        DATETIME_INVALID: Final[str] = YAPI.INVALID_STRING
        UTCOFFSET_INVALID: Final[int] = YAPI.INVALID_INT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        ISFIXED_FALSE: Final[int] = 0
        ISFIXED_TRUE: Final[int] = 1
        ISFIXED_INVALID: Final[int] = -1
        COORDSYSTEM_GPS_DMS: Final[int] = 0
        COORDSYSTEM_GPS_DM: Final[int] = 1
        COORDSYSTEM_GPS_D: Final[int] = 2
        COORDSYSTEM_INVALID: Final[int] = -1
        CONSTELLATION_GNSS: Final[int] = 0
        CONSTELLATION_GPS: Final[int] = 1
        CONSTELLATION_GLONASS: Final[int] = 2
        CONSTELLATION_GALILEO: Final[int] = 3
        CONSTELLATION_GPS_GLONASS: Final[int] = 4
        CONSTELLATION_GPS_GALILEO: Final[int] = 5
        CONSTELLATION_GLONASS_GALILEO: Final[int] = 6
        CONSTELLATION_INVALID: Final[int] = -1
        # --- (end of YGps return codes)

    # --- (YGps attributes declaration)
    _valueCallback: YGpsValueCallback
    # --- (end of YGps attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Gps', func)
        # --- (YGps constructor)
        # --- (end of YGps constructor)

    # --- (YGps implementation)
    @classmethod
    def FindGps(cls, func: str) -> YGps:
        """
        Retrieves a geolocalization module for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the geolocalization module is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGps.isOnline() to test if the geolocalization module is
        indeed online at a given time. In case of ambiguity when looking for
        a geolocalization module by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the geolocalization module, for instance
                YGNSSMK2.gps.

        @return a YGps object allowing you to drive the geolocalization module.
        """
        return cls.FindGpsInContext(YAPI, func)

    @classmethod
    def FindGpsInContext(cls, yctx: YAPIContext, func: str) -> YGps:
        """
        Retrieves a geolocalization module for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the geolocalization module is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YGps.isOnline() to test if the geolocalization module is
        indeed online at a given time. In case of ambiguity when looking for
        a geolocalization module by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the geolocalization module, for instance
                YGNSSMK2.gps.

        @return a YGps object allowing you to drive the geolocalization module.
        """
        obj: Union[YGps, None] = yctx._findInCache('Gps', func)
        if obj:
            return obj
        return YGps(yctx, func)

    @classmethod
    def FirstGps(cls) -> Union[YGps, None]:
        """
        Starts the enumeration of geolocalization modules currently accessible.
        Use the method YGps.nextGps() to iterate on
        next geolocalization modules.

        @return a pointer to a YGps object, corresponding to
                the first geolocalization module currently online, or a None pointer
                if there are none.
        """
        return cls.FirstGpsInContext(YAPI)

    @classmethod
    def FirstGpsInContext(cls, yctx: YAPIContext) -> Union[YGps, None]:
        """
        Starts the enumeration of geolocalization modules currently accessible.
        Use the method YGps.nextGps() to iterate on
        next geolocalization modules.

        @param yctx : a YAPI context.

        @return a pointer to a YGps object, corresponding to
                the first geolocalization module currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Gps')
        if hwid:
            return cls.FindGpsInContext(yctx, hwid2str(hwid))
        return None

    def nextGps(self) -> Union[YGps, None]:
        """
        Continues the enumeration of geolocalization modules started using yFirstGps().
        Caution: You can't make any assumption about the returned geolocalization modules order.
        If you want to find a specific a geolocalization module, use Gps.findGps()
        and a hardwareID or a logical name.

        @return a pointer to a YGps object, corresponding to
                a geolocalization module currently online, or a None pointer
                if there are no more geolocalization modules to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Gps', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindGpsInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_isFixed(self) -> int:
        """
        Returns TRUE if the receiver has found enough satellites to work.

        @return either YGps.ISFIXED_FALSE or YGps.ISFIXED_TRUE, according to TRUE if the receiver has found
        enough satellites to work

        On failure, throws an exception or returns YGps.ISFIXED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("isFixed")
        if json_val is None:
            return YGps.ISFIXED_INVALID
        return json_val

    async def get_satCount(self) -> int:
        """
        Returns the total count of satellites used to compute GPS position.

        @return an integer corresponding to the total count of satellites used to compute GPS position

        On failure, throws an exception or returns YGps.SATCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("satCount")
        if json_val is None:
            return YGps.SATCOUNT_INVALID
        return json_val

    async def get_satPerConst(self) -> int:
        """
        Returns the count of visible satellites per constellation encoded
        on a 32 bit integer: bits 0..5: GPS satellites count,  bits 6..11 : Glonass, bits 12..17 : Galileo.
        this value is refreshed every 5 seconds only.

        @return an integer corresponding to the count of visible satellites per constellation encoded
                on a 32 bit integer: bits 0.

        On failure, throws an exception or returns YGps.SATPERCONST_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("satPerConst")
        if json_val is None:
            return YGps.SATPERCONST_INVALID
        return json_val

    async def get_gpsRefreshRate(self) -> float:
        """
        Returns effective GPS data refresh frequency.
        this value is refreshed every 5 seconds only.

        @return a floating point number corresponding to effective GPS data refresh frequency

        On failure, throws an exception or returns YGps.GPSREFRESHRATE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("gpsRefreshRate")
        if json_val is None:
            return YGps.GPSREFRESHRATE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_coordSystem(self) -> int:
        """
        Returns the representation system used for positioning data.

        @return a value among YGps.COORDSYSTEM_GPS_DMS, YGps.COORDSYSTEM_GPS_DM and YGps.COORDSYSTEM_GPS_D
        corresponding to the representation system used for positioning data

        On failure, throws an exception or returns YGps.COORDSYSTEM_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("coordSystem")
        if json_val is None:
            return YGps.COORDSYSTEM_INVALID
        return json_val

    async def set_coordSystem(self, newval: int) -> int:
        """
        Changes the representation system used for positioning data.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a value among YGps.COORDSYSTEM_GPS_DMS, YGps.COORDSYSTEM_GPS_DM and
        YGps.COORDSYSTEM_GPS_D corresponding to the representation system used for positioning data

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("coordSystem", rest_val)

    async def get_constellation(self) -> int:
        """
        Returns the the satellites constellation used to compute
        positioning data.

        @return a value among YGps.CONSTELLATION_GNSS, YGps.CONSTELLATION_GPS, YGps.CONSTELLATION_GLONASS,
        YGps.CONSTELLATION_GALILEO, YGps.CONSTELLATION_GPS_GLONASS, YGps.CONSTELLATION_GPS_GALILEO and
        YGps.CONSTELLATION_GLONASS_GALILEO corresponding to the the satellites constellation used to compute
                positioning data

        On failure, throws an exception or returns YGps.CONSTELLATION_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("constellation")
        if json_val is None:
            return YGps.CONSTELLATION_INVALID
        return json_val

    async def set_constellation(self, newval: int) -> int:
        """
        Changes the satellites constellation used to compute
        positioning data. Possible  constellations are GNSS ( = all supported constellations),
        GPS, Glonass, Galileo , and the 3 possible pairs. This setting has  no effect on Yocto-GPS (V1).

        @param newval : a value among YGps.CONSTELLATION_GNSS, YGps.CONSTELLATION_GPS,
        YGps.CONSTELLATION_GLONASS, YGps.CONSTELLATION_GALILEO, YGps.CONSTELLATION_GPS_GLONASS,
        YGps.CONSTELLATION_GPS_GALILEO and YGps.CONSTELLATION_GLONASS_GALILEO corresponding to the
        satellites constellation used to compute
                positioning data

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("constellation", rest_val)

    async def get_latitude(self) -> str:
        """
        Returns the current latitude.

        @return a string corresponding to the current latitude

        On failure, throws an exception or returns YGps.LATITUDE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("latitude")
        if json_val is None:
            return YGps.LATITUDE_INVALID
        return json_val

    async def get_longitude(self) -> str:
        """
        Returns the current longitude.

        @return a string corresponding to the current longitude

        On failure, throws an exception or returns YGps.LONGITUDE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("longitude")
        if json_val is None:
            return YGps.LONGITUDE_INVALID
        return json_val

    async def get_dilution(self) -> float:
        """
        Returns the current horizontal dilution of precision,
        the smaller that number is, the better .

        @return a floating point number corresponding to the current horizontal dilution of precision,
                the smaller that number is, the better

        On failure, throws an exception or returns YGps.DILUTION_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("dilution")
        if json_val is None:
            return YGps.DILUTION_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_altitude(self) -> float:
        """
        Returns the current altitude. Beware:  GPS technology
        is very inaccurate regarding altitude.

        @return a floating point number corresponding to the current altitude

        On failure, throws an exception or returns YGps.ALTITUDE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("altitude")
        if json_val is None:
            return YGps.ALTITUDE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_groundSpeed(self) -> float:
        """
        Returns the current ground speed in Km/h.

        @return a floating point number corresponding to the current ground speed in Km/h

        On failure, throws an exception or returns YGps.GROUNDSPEED_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("groundSpeed")
        if json_val is None:
            return YGps.GROUNDSPEED_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_direction(self) -> float:
        """
        Returns the current move bearing in degrees, zero
        is the true (geographic) north.

        @return a floating point number corresponding to the current move bearing in degrees, zero
                is the true (geographic) north

        On failure, throws an exception or returns YGps.DIRECTION_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("direction")
        if json_val is None:
            return YGps.DIRECTION_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_unixTime(self) -> int:
        """
        Returns the current time in Unix format (number of
        seconds elapsed since Jan 1st, 1970).

        @return an integer corresponding to the current time in Unix format (number of
                seconds elapsed since Jan 1st, 1970)

        On failure, throws an exception or returns YGps.UNIXTIME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("unixTime")
        if json_val is None:
            return YGps.UNIXTIME_INVALID
        return json_val

    async def get_dateTime(self) -> str:
        """
        Returns the current time in the form "YYYY/MM/DD hh:mm:ss".

        @return a string corresponding to the current time in the form "YYYY/MM/DD hh:mm:ss"

        On failure, throws an exception or returns YGps.DATETIME_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("dateTime")
        if json_val is None:
            return YGps.DATETIME_INVALID
        return json_val

    async def get_utcOffset(self) -> int:
        """
        Returns the number of seconds between current time and UTC time (time zone).

        @return an integer corresponding to the number of seconds between current time and UTC time (time zone)

        On failure, throws an exception or returns YGps.UTCOFFSET_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("utcOffset")
        if json_val is None:
            return YGps.UTCOFFSET_INVALID
        return json_val

    async def set_utcOffset(self, newval: int) -> int:
        """
        Changes the number of seconds between current time and UTC time (time zone).
        The timezone is automatically rounded to the nearest multiple of 15 minutes.
        If current UTC time is known, the current time is automatically be updated according to the selected time zone.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : an integer corresponding to the number of seconds between current time and UTC time (time zone)

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("utcOffset", rest_val)

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YGps.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YGpsValueCallback) -> int:
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

    # --- (end of YGps implementation)

