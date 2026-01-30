# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YAnButton
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
Yoctopuce library: High-level API for YAnButton
version: PATCH_WITH_VERSION
requires: yocto_anbutton_aio
requires: yocto_api
provides: YAnButton
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
    _IS_MICROPYTHON: Final[bool] = True # noqa
    _DYNAMIC_HELPERS: Final[bool] = True # noqa

from .yocto_anbutton_aio import YAnButton as YAnButton_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YAnButton class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YAnButtonValueCallback = Union[Callable[['YAnButton', str], Any], None]
    except TypeError:
        YAnButtonValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YAnButton(YFunction):
    """
    The YAnButton class provide access to basic resistive inputs.
    Such inputs can be used to measure the state
    of a simple button as well as to read an analog potentiometer (variable resistance).
    This can be use for instance with a continuous rotating knob, a throttle grip
    or a joystick. The module is capable to calibrate itself on min and max values,
    in order to compute a calibrated value that varies proportionally with the
    potentiometer position, regardless of its total resistance.

    """
    _aio: YAnButton_aio
    # --- (end of YAnButton class start)
    if not _IS_MICROPYTHON:
        # --- (YAnButton return codes)
        CALIBRATEDVALUE_INVALID: Final[int] = YAPI.INVALID_UINT
        RAWVALUE_INVALID: Final[int] = YAPI.INVALID_UINT
        CALIBRATIONMAX_INVALID: Final[int] = YAPI.INVALID_UINT
        CALIBRATIONMIN_INVALID: Final[int] = YAPI.INVALID_UINT
        SENSITIVITY_INVALID: Final[int] = YAPI.INVALID_UINT
        LASTTIMEPRESSED_INVALID: Final[int] = YAPI.INVALID_LONG
        LASTTIMERELEASED_INVALID: Final[int] = YAPI.INVALID_LONG
        PULSECOUNTER_INVALID: Final[int] = YAPI.INVALID_LONG
        PULSETIMER_INVALID: Final[int] = YAPI.INVALID_LONG
        ANALOGCALIBRATION_OFF: Final[int] = 0
        ANALOGCALIBRATION_ON: Final[int] = 1
        ANALOGCALIBRATION_INVALID: Final[int] = -1
        ISPRESSED_FALSE: Final[int] = 0
        ISPRESSED_TRUE: Final[int] = 1
        ISPRESSED_INVALID: Final[int] = -1
        INPUTTYPE_ANALOG_FAST: Final[int] = 0
        INPUTTYPE_DIGITAL4: Final[int] = 1
        INPUTTYPE_ANALOG_SMOOTH: Final[int] = 2
        INPUTTYPE_DIGITAL_FAST: Final[int] = 3
        INPUTTYPE_INVALID: Final[int] = -1
        # --- (end of YAnButton return codes)


    # --- (YAnButton implementation)

    @classmethod
    def FindAnButton(cls, func: str) -> YAnButton:
        """
        Retrieves an analog input for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the analog input is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAnButton.isOnline() to test if the analog input is
        indeed online at a given time. In case of ambiguity when looking for
        an analog input by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the analog input, for instance
                YBUZZER2.anButton1.

        @return a YAnButton object allowing you to drive the analog input.
        """
        return cls._proxy(cls, YAnButton_aio.FindAnButtonInContext(YAPI_aio, func))

    @classmethod
    def FindAnButtonInContext(cls, yctx: YAPIContext, func: str) -> YAnButton:
        """
        Retrieves an analog input for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the analog input is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAnButton.isOnline() to test if the analog input is
        indeed online at a given time. In case of ambiguity when looking for
        an analog input by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the analog input, for instance
                YBUZZER2.anButton1.

        @return a YAnButton object allowing you to drive the analog input.
        """
        return cls._proxy(cls, YAnButton_aio.FindAnButtonInContext(yctx._aio, func))

    @classmethod
    def FirstAnButton(cls) -> Union[YAnButton, None]:
        """
        Starts the enumeration of analog inputs currently accessible.
        Use the method YAnButton.nextAnButton() to iterate on
        next analog inputs.

        @return a pointer to a YAnButton object, corresponding to
                the first analog input currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YAnButton_aio.FirstAnButtonInContext(YAPI_aio))

    @classmethod
    def FirstAnButtonInContext(cls, yctx: YAPIContext) -> Union[YAnButton, None]:
        """
        Starts the enumeration of analog inputs currently accessible.
        Use the method YAnButton.nextAnButton() to iterate on
        next analog inputs.

        @param yctx : a YAPI context.

        @return a pointer to a YAnButton object, corresponding to
                the first analog input currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YAnButton_aio.FirstAnButtonInContext(yctx._aio))

    def nextAnButton(self) -> Union[YAnButton, None]:
        """
        Continues the enumeration of analog inputs started using yFirstAnButton().
        Caution: You can't make any assumption about the returned analog inputs order.
        If you want to find a specific an analog input, use AnButton.findAnButton()
        and a hardwareID or a logical name.

        @return a pointer to a YAnButton object, corresponding to
                an analog input currently online, or a None pointer
                if there are no more analog inputs to enumerate.
        """
        return self._proxy(type(self), self._aio.nextAnButton())

    if not _DYNAMIC_HELPERS:
        def get_calibratedValue(self) -> int:
            """
            Returns the current calibrated input value (between 0 and 1000, included).

            @return an integer corresponding to the current calibrated input value (between 0 and 1000, included)

            On failure, throws an exception or returns YAnButton.CALIBRATEDVALUE_INVALID.
            """
            return self._run(self._aio.get_calibratedValue())

    if not _DYNAMIC_HELPERS:
        def get_rawValue(self) -> int:
            """
            Returns the current measured input value as-is (between 0 and 4095, included).

            @return an integer corresponding to the current measured input value as-is (between 0 and 4095, included)

            On failure, throws an exception or returns YAnButton.RAWVALUE_INVALID.
            """
            return self._run(self._aio.get_rawValue())

    if not _DYNAMIC_HELPERS:
        def get_analogCalibration(self) -> int:
            """
            Tells if a calibration process is currently ongoing.

            @return either YAnButton.ANALOGCALIBRATION_OFF or YAnButton.ANALOGCALIBRATION_ON

            On failure, throws an exception or returns YAnButton.ANALOGCALIBRATION_INVALID.
            """
            return self._run(self._aio.get_analogCalibration())

    if not _DYNAMIC_HELPERS:
        def set_analogCalibration(self, newval: int) -> int:
            """
            Starts or stops the calibration process. Remember to call the saveToFlash()
            method of the module at the end of the calibration if the modification must be kept.

            @param newval : either YAnButton.ANALOGCALIBRATION_OFF or YAnButton.ANALOGCALIBRATION_ON

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_analogCalibration(newval))

    if not _DYNAMIC_HELPERS:
        def get_calibrationMax(self) -> int:
            """
            Returns the maximal value measured during the calibration (between 0 and 4095, included).

            @return an integer corresponding to the maximal value measured during the calibration (between 0
            and 4095, included)

            On failure, throws an exception or returns YAnButton.CALIBRATIONMAX_INVALID.
            """
            return self._run(self._aio.get_calibrationMax())

    if not _DYNAMIC_HELPERS:
        def set_calibrationMax(self, newval: int) -> int:
            """
            Changes the maximal calibration value for the input (between 0 and 4095, included), without actually
            starting the automated calibration.  Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the maximal calibration value for the input (between 0
            and 4095, included), without actually
                    starting the automated calibration

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_calibrationMax(newval))

    if not _DYNAMIC_HELPERS:
        def get_calibrationMin(self) -> int:
            """
            Returns the minimal value measured during the calibration (between 0 and 4095, included).

            @return an integer corresponding to the minimal value measured during the calibration (between 0
            and 4095, included)

            On failure, throws an exception or returns YAnButton.CALIBRATIONMIN_INVALID.
            """
            return self._run(self._aio.get_calibrationMin())

    if not _DYNAMIC_HELPERS:
        def set_calibrationMin(self, newval: int) -> int:
            """
            Changes the minimal calibration value for the input (between 0 and 4095, included), without actually
            starting the automated calibration.  Remember to call the saveToFlash()
            method of the module if the modification must be kept.

            @param newval : an integer corresponding to the minimal calibration value for the input (between 0
            and 4095, included), without actually
                    starting the automated calibration

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_calibrationMin(newval))

    if not _DYNAMIC_HELPERS:
        def get_sensitivity(self) -> int:
            """
            Returns the sensibility for the input (between 1 and 1000) for triggering user callbacks.

            @return an integer corresponding to the sensibility for the input (between 1 and 1000) for
            triggering user callbacks

            On failure, throws an exception or returns YAnButton.SENSITIVITY_INVALID.
            """
            return self._run(self._aio.get_sensitivity())

    if not _DYNAMIC_HELPERS:
        def set_sensitivity(self, newval: int) -> int:
            """
            Changes the sensibility for the input (between 1 and 1000) for triggering user callbacks.
            The sensibility is used to filter variations around a fixed value, but does not preclude the
            transmission of events when the input value evolves constantly in the same direction.
            Special case: when the value 1000 is used, the callback will only be thrown when the logical state
            of the input switches from pressed to released and back.
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : an integer corresponding to the sensibility for the input (between 1 and 1000) for
            triggering user callbacks

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_sensitivity(newval))

    if not _DYNAMIC_HELPERS:
        def get_isPressed(self) -> int:
            """
            Returns true if the input (considered as binary) is active (closed contact), and false otherwise.

            @return either YAnButton.ISPRESSED_FALSE or YAnButton.ISPRESSED_TRUE, according to true if the
            input (considered as binary) is active (closed contact), and false otherwise

            On failure, throws an exception or returns YAnButton.ISPRESSED_INVALID.
            """
            return self._run(self._aio.get_isPressed())

    if not _DYNAMIC_HELPERS:
        def get_lastTimePressed(self) -> int:
            """
            Returns the number of elapsed milliseconds between the module power on and the last time
            the input button was pressed (the input contact transitioned from open to closed).

            @return an integer corresponding to the number of elapsed milliseconds between the module power on
            and the last time
                    the input button was pressed (the input contact transitioned from open to closed)

            On failure, throws an exception or returns YAnButton.LASTTIMEPRESSED_INVALID.
            """
            return self._run(self._aio.get_lastTimePressed())

    if not _DYNAMIC_HELPERS:
        def get_lastTimeReleased(self) -> int:
            """
            Returns the number of elapsed milliseconds between the module power on and the last time
            the input button was released (the input contact transitioned from closed to open).

            @return an integer corresponding to the number of elapsed milliseconds between the module power on
            and the last time
                    the input button was released (the input contact transitioned from closed to open)

            On failure, throws an exception or returns YAnButton.LASTTIMERELEASED_INVALID.
            """
            return self._run(self._aio.get_lastTimeReleased())

    if not _DYNAMIC_HELPERS:
        def get_pulseCounter(self) -> int:
            """
            Returns the pulse counter value. The value is a 32 bit integer. In case
            of overflow (>=2^32), the counter will wrap. To reset the counter, just
            call the resetCounter() method.

            @return an integer corresponding to the pulse counter value

            On failure, throws an exception or returns YAnButton.PULSECOUNTER_INVALID.
            """
            return self._run(self._aio.get_pulseCounter())

    if not _DYNAMIC_HELPERS:
        def set_pulseCounter(self, newval: int) -> int:
            return self._run(self._aio.set_pulseCounter(newval))

    if not _DYNAMIC_HELPERS:
        def get_pulseTimer(self) -> int:
            """
            Returns the timer of the pulses counter (ms).

            @return an integer corresponding to the timer of the pulses counter (ms)

            On failure, throws an exception or returns YAnButton.PULSETIMER_INVALID.
            """
            return self._run(self._aio.get_pulseTimer())

    if not _DYNAMIC_HELPERS:
        def get_inputType(self) -> int:
            """
            Returns the decoding method applied to the input (analog or multiplexed binary switches).

            @return a value among YAnButton.INPUTTYPE_ANALOG_FAST, YAnButton.INPUTTYPE_DIGITAL4,
            YAnButton.INPUTTYPE_ANALOG_SMOOTH and YAnButton.INPUTTYPE_DIGITAL_FAST corresponding to the
            decoding method applied to the input (analog or multiplexed binary switches)

            On failure, throws an exception or returns YAnButton.INPUTTYPE_INVALID.
            """
            return self._run(self._aio.get_inputType())

    if not _DYNAMIC_HELPERS:
        def set_inputType(self, newval: int) -> int:
            """
            Changes the decoding method applied to the input (analog or multiplexed binary switches).
            Remember to call the saveToFlash() method of the module if the modification must be kept.

            @param newval : a value among YAnButton.INPUTTYPE_ANALOG_FAST, YAnButton.INPUTTYPE_DIGITAL4,
            YAnButton.INPUTTYPE_ANALOG_SMOOTH and YAnButton.INPUTTYPE_DIGITAL_FAST corresponding to the
            decoding method applied to the input (analog or multiplexed binary switches)

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_inputType(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YAnButtonValueCallback) -> int:
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
        def resetCounter(self) -> int:
            """
            Returns the pulse counter value as well as its timer.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.resetCounter())

    # --- (end of YAnButton implementation)

