# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YRefFrame
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
Yoctopuce library: High-level API for YRefFrame
version: PATCH_WITH_VERSION
requires: yocto_refframe_aio
requires: yocto_api
provides: YRefFrame
"""
from __future__ import annotations

import sys

# On MicroPython, code below will be wiped out at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union, Final
    from enum import IntEnum
    from collections.abc import Callable, Awaitable
    const = lambda obj: obj
    _IS_MICROPYTHON = False
    _DYNAMIC_HELPERS = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython,
    # as they produce overhead in runtime code
    # Final is translated into const() expressions before compilation
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_refframe_aio import YRefFrame as YRefFrame_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YRefFrame class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YRefFrameValueCallback = Union[Callable[['YRefFrame', str], Any], None]
    except TypeError:
        YRefFrameValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YRefFrame(YFunction):
    """
    The YRefFrame class is used to set up the base orientation of the Yoctopuce inertial
    sensors. Thanks to this, orientation functions relative to the earth surface plane
    can use the proper reference frame. For some devices, the class also implements a
    tridimensional sensor calibration process, which can compensate for local variations
    of standard gravity and improve the precision of the tilt sensors.

    """
    _aio: YRefFrame_aio
    # --- (end of YRefFrame class start)
    if not _IS_MICROPYTHON:
        # --- (YRefFrame return codes)
        MOUNTPOS_INVALID: Final[int] = YAPI.INVALID_UINT
        BEARING_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CALIBRATIONPARAM_INVALID: Final[str] = YAPI.INVALID_STRING
        FUSIONMODE_NDOF: Final[int] = 0
        FUSIONMODE_NDOF_FMC_OFF: Final[int] = 1
        FUSIONMODE_M4G: Final[int] = 2
        FUSIONMODE_COMPASS: Final[int] = 3
        FUSIONMODE_IMU: Final[int] = 4
        FUSIONMODE_INCLIN_90DEG_1G8: Final[int] = 5
        FUSIONMODE_INCLIN_90DEG_3G6: Final[int] = 6
        FUSIONMODE_INCLIN_10DEG: Final[int] = 7
        FUSIONMODE_INVALID: Final[int] = -1
        class MOUNTPOSITION(IntEnum):
            BOTTOM = 0
            TOP = 1
            FRONT = 2
            REAR = 3
            RIGHT = 4
            LEFT = 5
            INVALID = 6

        class MOUNTORIENTATION(IntEnum):
            TWELVE = 0
            THREE = 1
            SIX = 2
            NINE = 3
            INVALID = 4

        # --- (end of YRefFrame return codes)


    # --- (YRefFrame implementation)

    @classmethod
    def FindRefFrame(cls, func: str) -> YRefFrame:
        """
        Retrieves a reference frame for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the reference frame is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRefFrame.isOnline() to test if the reference frame is
        indeed online at a given time. In case of ambiguity when looking for
        a reference frame by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the reference frame, for instance
                Y3DMK002.refFrame.

        @return a YRefFrame object allowing you to drive the reference frame.
        """
        return cls._proxy(cls, YRefFrame_aio.FindRefFrameInContext(YAPI_aio, func))

    @classmethod
    def FindRefFrameInContext(cls, yctx: YAPIContext, func: str) -> YRefFrame:
        """
        Retrieves a reference frame for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the reference frame is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRefFrame.isOnline() to test if the reference frame is
        indeed online at a given time. In case of ambiguity when looking for
        a reference frame by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the reference frame, for instance
                Y3DMK002.refFrame.

        @return a YRefFrame object allowing you to drive the reference frame.
        """
        return cls._proxy(cls, YRefFrame_aio.FindRefFrameInContext(yctx._aio, func))

    @classmethod
    def FirstRefFrame(cls) -> Union[YRefFrame, None]:
        """
        Starts the enumeration of reference frames currently accessible.
        Use the method YRefFrame.nextRefFrame() to iterate on
        next reference frames.

        @return a pointer to a YRefFrame object, corresponding to
                the first reference frame currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YRefFrame_aio.FirstRefFrameInContext(YAPI_aio))

    @classmethod
    def FirstRefFrameInContext(cls, yctx: YAPIContext) -> Union[YRefFrame, None]:
        """
        Starts the enumeration of reference frames currently accessible.
        Use the method YRefFrame.nextRefFrame() to iterate on
        next reference frames.

        @param yctx : a YAPI context.

        @return a pointer to a YRefFrame object, corresponding to
                the first reference frame currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YRefFrame_aio.FirstRefFrameInContext(yctx._aio))

    def nextRefFrame(self) -> Union[YRefFrame, None]:
        """
        Continues the enumeration of reference frames started using yFirstRefFrame().
        Caution: You can't make any assumption about the returned reference frames order.
        If you want to find a specific a reference frame, use RefFrame.findRefFrame()
        and a hardwareID or a logical name.

        @return a pointer to a YRefFrame object, corresponding to
                a reference frame currently online, or a None pointer
                if there are no more reference frames to enumerate.
        """
        return self._proxy(type(self), self._aio.nextRefFrame())

    if not _DYNAMIC_HELPERS:
        def set_mountPos(self, newval: int) -> int:
            return self._run(self._aio.set_mountPos(newval))

    if not _DYNAMIC_HELPERS:
        def set_bearing(self, newval: float) -> int:
            """
            Changes the reference bearing used by the compass. The relative bearing
            indicated by the compass is the difference between the measured magnetic
            heading and the reference bearing indicated here.

            For instance, if you set up as reference bearing the value of the earth
            magnetic declination, the compass will provide the orientation relative
            to the geographic North.

            Similarly, when the sensor is not mounted along the standard directions
            because it has an additional yaw angle, you can set this angle in the reference
            bearing so that the compass provides the expected natural direction.

            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : a floating point number corresponding to the reference bearing used by the compass

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_bearing(newval))

    if not _DYNAMIC_HELPERS:
        def get_bearing(self) -> float:
            """
            Returns the reference bearing used by the compass. The relative bearing
            indicated by the compass is the difference between the measured magnetic
            heading and the reference bearing indicated here.

            @return a floating point number corresponding to the reference bearing used by the compass

            On failure, throws an exception or returns YRefFrame.BEARING_INVALID.
            """
            return self._run(self._aio.get_bearing())

    if not _DYNAMIC_HELPERS:
        def set_calibrationParam(self, newval: str) -> int:
            return self._run(self._aio.set_calibrationParam(newval))

    if not _DYNAMIC_HELPERS:
        def get_fusionMode(self) -> int:
            """
            Returns the sensor fusion mode. Note that available sensor fusion modes depend on the sensor type.

            @return a value among YRefFrame.FUSIONMODE_NDOF, YRefFrame.FUSIONMODE_NDOF_FMC_OFF,
            YRefFrame.FUSIONMODE_M4G, YRefFrame.FUSIONMODE_COMPASS, YRefFrame.FUSIONMODE_IMU,
            YRefFrame.FUSIONMODE_INCLIN_90DEG_1G8, YRefFrame.FUSIONMODE_INCLIN_90DEG_3G6 and
            YRefFrame.FUSIONMODE_INCLIN_10DEG corresponding to the sensor fusion mode

            On failure, throws an exception or returns YRefFrame.FUSIONMODE_INVALID.
            """
            return self._run(self._aio.get_fusionMode())

    if not _DYNAMIC_HELPERS:
        def set_fusionMode(self, newval: int) -> int:
            """
            Change the sensor fusion mode. Note that available sensor fusion modes depend on the sensor type.
            Remember to call the matching module saveToFlash() method to save the setting permanently.

            @param newval : a value among YRefFrame.FUSIONMODE_NDOF, YRefFrame.FUSIONMODE_NDOF_FMC_OFF,
            YRefFrame.FUSIONMODE_M4G, YRefFrame.FUSIONMODE_COMPASS, YRefFrame.FUSIONMODE_IMU,
            YRefFrame.FUSIONMODE_INCLIN_90DEG_1G8, YRefFrame.FUSIONMODE_INCLIN_90DEG_3G6 and
            YRefFrame.FUSIONMODE_INCLIN_10DEG

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_fusionMode(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YRefFrameValueCallback) -> int:
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
        def get_mountPosition(self) -> YRefFrame.MOUNTPOSITION:
            """
            Returns the installation position of the device, as configured
            in order to define the reference frame for the compass and the
            pitch/roll tilt sensors.

            @return a value among the YRefFrame.MOUNTPOSITION enumeration
                    (YRefFrame.MOUNTPOSITION.BOTTOM,  YRefFrame.MOUNTPOSITION.TOP,
                    YRefFrame.MOUNTPOSITION.FRONT,    YRefFrame.MOUNTPOSITION.RIGHT,
                    YRefFrame.MOUNTPOSITION.REAR,     YRefFrame.MOUNTPOSITION.LEFT),
                    corresponding to the installation in a box, on one of the six faces.

            On failure, throws an exception or returns YRefFrame.MOUNTPOSITION_INVALID.
            """
            return self._run(self._aio.get_mountPosition())

    if not _DYNAMIC_HELPERS:
        def get_mountOrientation(self) -> YRefFrame.MOUNTORIENTATION:
            """
            Returns the installation orientation of the device, as configured
            in order to define the reference frame for the compass and the
            pitch/roll tilt sensors.

            @return a value among the enumeration YRefFrame.MOUNTORIENTATION
                    (YRefFrame.MOUNTORIENTATION.TWELVE, YRefFrame.MOUNTORIENTATION.THREE,
                    YRefFrame.MOUNTORIENTATION.SIX,     YRefFrame.MOUNTORIENTATION.NINE)
                    corresponding to the orientation of the "X" arrow on the device,
                    as on a clock dial seen from an observer in the center of the box.
                    On the bottom face, the 12H orientation points to the front, while
                    on the top face, the 12H orientation points to the rear.

            On failure, throws an exception or returns YRefFrame.MOUNTORIENTATION_INVALID.
            """
            return self._run(self._aio.get_mountOrientation())

    if not _DYNAMIC_HELPERS:
        def set_mountPosition(self, position: MOUNTPOSITION, orientation: MOUNTORIENTATION) -> int:
            """
            Changes the compass and tilt sensor frame of reference. The magnetic compass
            and the tilt sensors (pitch and roll) naturally work in the plane
            parallel to the earth surface. In case the device is not installed upright
            and horizontally, you must select its reference orientation (parallel to
            the earth surface) so that the measures are made relative to this position.

            @param position : a value among the YRefFrame.MOUNTPOSITION enumeration
                    (YRefFrame.MOUNTPOSITION.BOTTOM,  YRefFrame.MOUNTPOSITION.TOP,
                    YRefFrame.MOUNTPOSITION.FRONT,    YRefFrame.MOUNTPOSITION.RIGHT,
                    YRefFrame.MOUNTPOSITION.REAR,     YRefFrame.MOUNTPOSITION.LEFT),
                    corresponding to the installation in a box, on one of the six faces.
            @param orientation : a value among the enumeration YRefFrame.MOUNTORIENTATION
                    (YRefFrame.MOUNTORIENTATION.TWELVE, YRefFrame.MOUNTORIENTATION.THREE,
                    YRefFrame.MOUNTORIENTATION.SIX,     YRefFrame.MOUNTORIENTATION.NINE)
                    corresponding to the orientation of the "X" arrow on the device,
                    as on a clock dial seen from an observer in the center of the box.
                    On the bottom face, the 12H orientation points to the front, while
                    on the top face, the 12H orientation points to the rear.

            Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_mountPosition(position, orientation))

    if not _DYNAMIC_HELPERS:
        def get_calibrationState(self) -> int:
            """
            Returns the 3D sensor calibration state (Yocto-3D-V2 only). This function returns
            an integer representing the calibration state of the 3 inertial sensors of
            the BNO055 chip, found in the Yocto-3D-V2. Hundredths show the calibration state
            of the accelerometer, tenths show the calibration state of the magnetometer while
            units show the calibration state of the gyroscope. For each sensor, the value 0
            means no calibration and the value 3 means full calibration.

            @return an integer representing the calibration state of Yocto-3D-V2:
                    333 when fully calibrated, 0 when not calibrated at all.

            On failure, throws an exception or returns a negative error code.
            For the Yocto-3D (V1), this function always return -3 (unsupported function).
            """
            return self._run(self._aio.get_calibrationState())

    if not _DYNAMIC_HELPERS:
        def get_measureQuality(self) -> int:
            """
            Returns estimated quality of the orientation (Yocto-3D-V2 only). This function returns
            an integer between 0 and 3 representing the degree of confidence of the position
            estimate. When the value is 3, the estimation is reliable. Below 3, one should
            expect sudden corrections, in particular for heading (compass function).
            The most frequent causes for values below 3 are magnetic interferences, and
            accelerations or rotations beyond the sensor range.

            @return an integer between 0 and 3 (3 when the measure is reliable)

            On failure, throws an exception or returns a negative error code.
            For the Yocto-3D (V1), this function always return -3 (unsupported function).
            """
            return self._run(self._aio.get_measureQuality())

    if not _DYNAMIC_HELPERS:
        def start3DCalibration(self) -> int:
            """
            Initiates the sensors tridimensional calibration process.
            This calibration is used at low level for inertial position estimation
            and to enhance the precision of the tilt sensors.

            After calling this method, the device should be moved according to the
            instructions provided by method get_3DCalibrationHint,
            and more3DCalibration should be invoked about 5 times per second.
            The calibration procedure is completed when the method
            get_3DCalibrationProgress returns 100. At this point,
            the computed calibration parameters can be applied using method
            save3DCalibration. The calibration process can be cancelled
            at any time using method cancel3DCalibration.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.start3DCalibration())

    if not _DYNAMIC_HELPERS:
        def more3DCalibration(self) -> int:
            """
            Continues the sensors tridimensional calibration process previously
            initiated using method start3DCalibration.
            This method should be called approximately 5 times per second, while
            positioning the device according to the instructions provided by method
            get_3DCalibrationHint. Note that the instructions change during
            the calibration process.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.more3DCalibration())

    if not _DYNAMIC_HELPERS:
        def get_3DCalibrationHint(self) -> str:
            """
            Returns instructions to proceed to the tridimensional calibration initiated with
            method start3DCalibration.

            @return a character string.
            """
            return self._run(self._aio.get_3DCalibrationHint())

    if not _DYNAMIC_HELPERS:
        def get_3DCalibrationProgress(self) -> int:
            """
            Returns the global process indicator for the tridimensional calibration
            initiated with method start3DCalibration.

            @return an integer between 0 (not started) and 100 (stage completed).
            """
            return self._run(self._aio.get_3DCalibrationProgress())

    if not _DYNAMIC_HELPERS:
        def get_3DCalibrationStage(self) -> int:
            """
            Returns index of the current stage of the calibration
            initiated with method start3DCalibration.

            @return an integer, growing each time a calibration stage is completed.
            """
            return self._run(self._aio.get_3DCalibrationStage())

    if not _DYNAMIC_HELPERS:
        def get_3DCalibrationStageProgress(self) -> int:
            """
            Returns the process indicator for the current stage of the calibration
            initiated with method start3DCalibration.

            @return an integer between 0 (not started) and 100 (stage completed).
            """
            return self._run(self._aio.get_3DCalibrationStageProgress())

    if not _DYNAMIC_HELPERS:
        def get_3DCalibrationLogMsg(self) -> str:
            """
            Returns the latest log message from the calibration process.
            When no new message is available, returns an empty string.

            @return a character string.
            """
            return self._run(self._aio.get_3DCalibrationLogMsg())

    if not _DYNAMIC_HELPERS:
        def save3DCalibration(self) -> int:
            """
            Applies the sensors tridimensional calibration parameters that have just been computed.
            Remember to call the saveToFlash()  method of the module if the changes
            must be kept when the device is restarted.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.save3DCalibration())

    if not _DYNAMIC_HELPERS:
        def cancel3DCalibration(self) -> int:
            """
            Aborts the sensors tridimensional calibration process et restores normal settings.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.cancel3DCalibration())

    # --- (end of YRefFrame implementation)

