# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  High-level API for YMultiAxisController
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
Yoctopuce library: High-level API for YMultiAxisController
version: PATCH_WITH_VERSION
requires: yocto_multiaxiscontroller_aio
requires: yocto_api
provides: YMultiAxisController
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

from .yocto_multiaxiscontroller_aio import YMultiAxisController as YMultiAxisController_aio
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction
)

# --- (YMultiAxisController class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YMultiAxisControllerValueCallback = Union[Callable[['YMultiAxisController', str], Any], None]
    except TypeError:
        YMultiAxisControllerValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YMultiAxisController(YFunction):
    """
    The YMultiAxisController class allows you to drive multiple stepper motors
    synchronously.

    """
    _aio: YMultiAxisController_aio
    # --- (end of YMultiAxisController class start)
    if not _IS_MICROPYTHON:
        # --- (YMultiAxisController return codes)
        NAXIS_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        GLOBALSTATE_ABSENT: Final[int] = 0
        GLOBALSTATE_ALERT: Final[int] = 1
        GLOBALSTATE_HI_Z: Final[int] = 2
        GLOBALSTATE_STOP: Final[int] = 3
        GLOBALSTATE_RUN: Final[int] = 4
        GLOBALSTATE_BATCH: Final[int] = 5
        GLOBALSTATE_INVALID: Final[int] = -1
        # --- (end of YMultiAxisController return codes)


    # --- (YMultiAxisController implementation)

    @classmethod
    def FindMultiAxisController(cls, func: str) -> YMultiAxisController:
        """
        Retrieves a multi-axis controller for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the multi-axis controller is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMultiAxisController.isOnline() to test if the multi-axis controller is
        indeed online at a given time. In case of ambiguity when looking for
        a multi-axis controller by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the multi-axis controller, for instance
                MyDevice.multiAxisController.

        @return a YMultiAxisController object allowing you to drive the multi-axis controller.
        """
        return cls._proxy(cls, YMultiAxisController_aio.FindMultiAxisControllerInContext(YAPI_aio, func))

    @classmethod
    def FindMultiAxisControllerInContext(cls, yctx: YAPIContext, func: str) -> YMultiAxisController:
        """
        Retrieves a multi-axis controller for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the multi-axis controller is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMultiAxisController.isOnline() to test if the multi-axis controller is
        indeed online at a given time. In case of ambiguity when looking for
        a multi-axis controller by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the multi-axis controller, for instance
                MyDevice.multiAxisController.

        @return a YMultiAxisController object allowing you to drive the multi-axis controller.
        """
        return cls._proxy(cls, YMultiAxisController_aio.FindMultiAxisControllerInContext(yctx._aio, func))

    @classmethod
    def FirstMultiAxisController(cls) -> Union[YMultiAxisController, None]:
        """
        Starts the enumeration of multi-axis controllers currently accessible.
        Use the method YMultiAxisController.nextMultiAxisController() to iterate on
        next multi-axis controllers.

        @return a pointer to a YMultiAxisController object, corresponding to
                the first multi-axis controller currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YMultiAxisController_aio.FirstMultiAxisControllerInContext(YAPI_aio))

    @classmethod
    def FirstMultiAxisControllerInContext(cls, yctx: YAPIContext) -> Union[YMultiAxisController, None]:
        """
        Starts the enumeration of multi-axis controllers currently accessible.
        Use the method YMultiAxisController.nextMultiAxisController() to iterate on
        next multi-axis controllers.

        @param yctx : a YAPI context.

        @return a pointer to a YMultiAxisController object, corresponding to
                the first multi-axis controller currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YMultiAxisController_aio.FirstMultiAxisControllerInContext(yctx._aio))

    def nextMultiAxisController(self) -> Union[YMultiAxisController, None]:
        """
        Continues the enumeration of multi-axis controllers started using yFirstMultiAxisController().
        Caution: You can't make any assumption about the returned multi-axis controllers order.
        If you want to find a specific a multi-axis controller, use MultiAxisController.findMultiAxisController()
        and a hardwareID or a logical name.

        @return a pointer to a YMultiAxisController object, corresponding to
                a multi-axis controller currently online, or a None pointer
                if there are no more multi-axis controllers to enumerate.
        """
        return self._proxy(type(self), self._aio.nextMultiAxisController())

    if not _DYNAMIC_HELPERS:
        def get_nAxis(self) -> int:
            """
            Returns the number of synchronized controllers.

            @return an integer corresponding to the number of synchronized controllers

            On failure, throws an exception or returns YMultiAxisController.NAXIS_INVALID.
            """
            return self._run(self._aio.get_nAxis())

    if not _DYNAMIC_HELPERS:
        def set_nAxis(self, newval: int) -> int:
            """
            Changes the number of synchronized controllers.

            @param newval : an integer corresponding to the number of synchronized controllers

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_nAxis(newval))

    if not _DYNAMIC_HELPERS:
        def get_globalState(self) -> int:
            """
            Returns the stepper motor set overall state.

            @return a value among YMultiAxisController.GLOBALSTATE_ABSENT,
            YMultiAxisController.GLOBALSTATE_ALERT, YMultiAxisController.GLOBALSTATE_HI_Z,
            YMultiAxisController.GLOBALSTATE_STOP, YMultiAxisController.GLOBALSTATE_RUN and
            YMultiAxisController.GLOBALSTATE_BATCH corresponding to the stepper motor set overall state

            On failure, throws an exception or returns YMultiAxisController.GLOBALSTATE_INVALID.
            """
            return self._run(self._aio.get_globalState())

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YMultiAxisControllerValueCallback) -> int:
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
        def reset(self) -> int:
            """
            Reinitialize all controllers and clear all alert flags.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.reset())

    if not _DYNAMIC_HELPERS:
        def findHomePosition(self, speed: list[float]) -> int:
            """
            Starts all motors backward at the specified speeds, to search for the motor home position.

            @param speed : desired speed for all axis, in steps per second.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.findHomePosition(speed))

    if not _DYNAMIC_HELPERS:
        def moveTo(self, absPos: list[float]) -> int:
            """
            Starts all motors synchronously to reach a given absolute position.
            The time needed to reach the requested position will depend on the lowest
            acceleration and max speed parameters configured for all motors.
            The final position will be reached on all axis at the same time.

            @param absPos : absolute position, measured in steps from each origin.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.moveTo(absPos))

    if not _DYNAMIC_HELPERS:
        def moveRel(self, relPos: list[float]) -> int:
            """
            Starts all motors synchronously to reach a given relative position.
            The time needed to reach the requested position will depend on the lowest
            acceleration and max speed parameters configured for all motors.
            The final position will be reached on all axis at the same time.

            @param relPos : relative position, measured in steps from the current position.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.moveRel(relPos))

    if not _DYNAMIC_HELPERS:
        def pause(self, waitMs: int) -> int:
            """
            Keep the motor in the same state for the specified amount of time, before processing next command.

            @param waitMs : wait time, specified in milliseconds.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.pause(waitMs))

    if not _DYNAMIC_HELPERS:
        def emergencyStop(self) -> int:
            """
            Stops the motor with an emergency alert, without taking any additional precaution.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.emergencyStop())

    if not _DYNAMIC_HELPERS:
        def abortAndBrake(self) -> int:
            """
            Stops the motor smoothly as soon as possible, without waiting for ongoing move completion.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.abortAndBrake())

    if not _DYNAMIC_HELPERS:
        def abortAndHiZ(self) -> int:
            """
            Turn the controller into Hi-Z mode immediately, without waiting for ongoing move completion.

            @return YAPI.SUCCESS if the call succeeds.
                    On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.abortAndHiZ())

    # --- (end of YMultiAxisController implementation)

