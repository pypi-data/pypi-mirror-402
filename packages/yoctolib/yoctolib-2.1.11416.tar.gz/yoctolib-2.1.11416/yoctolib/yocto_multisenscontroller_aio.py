# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: svn_id $
#
#  Asyncio implementation of YMultiSensController
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
Yoctopuce library: Asyncio implementation of YMultiSensController
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YMultiSensController
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

# --- (YMultiSensController class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YMultiSensControllerValueCallback = Union[Callable[['YMultiSensController', str], Any], None]
    except TypeError:
        YMultiSensControllerValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YMultiSensController(YFunction):
    """
    The YMultiSensController class allows you to set up a customized
    sensor chain on devices featuring that functionality.

    """
    # --- (end of YMultiSensController class start)
    if not _IS_MICROPYTHON:
        # --- (YMultiSensController return codes)
        NSENSORS_INVALID: Final[int] = YAPI.INVALID_UINT
        MAXSENSORS_INVALID: Final[int] = YAPI.INVALID_UINT
        LASTADDRESSDETECTED_INVALID: Final[int] = YAPI.INVALID_UINT
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        MAINTENANCEMODE_FALSE: Final[int] = 0
        MAINTENANCEMODE_TRUE: Final[int] = 1
        MAINTENANCEMODE_INVALID: Final[int] = -1
        # --- (end of YMultiSensController return codes)

    # --- (YMultiSensController attributes declaration)
    _valueCallback: YMultiSensControllerValueCallback
    # --- (end of YMultiSensController attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'MultiSensController', func)
        # --- (YMultiSensController constructor)
        # --- (end of YMultiSensController constructor)

    # --- (YMultiSensController implementation)
    @classmethod
    def FindMultiSensController(cls, func: str) -> YMultiSensController:
        """
        Retrieves a multi-sensor controller for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the multi-sensor controller is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMultiSensController.isOnline() to test if the multi-sensor controller is
        indeed online at a given time. In case of ambiguity when looking for
        a multi-sensor controller by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the multi-sensor controller, for instance
                YTEMPIR1.multiSensController.

        @return a YMultiSensController object allowing you to drive the multi-sensor controller.
        """
        return cls.FindMultiSensControllerInContext(YAPI, func)

    @classmethod
    def FindMultiSensControllerInContext(cls, yctx: YAPIContext, func: str) -> YMultiSensController:
        """
        Retrieves a multi-sensor controller for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the multi-sensor controller is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMultiSensController.isOnline() to test if the multi-sensor controller is
        indeed online at a given time. In case of ambiguity when looking for
        a multi-sensor controller by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the multi-sensor controller, for instance
                YTEMPIR1.multiSensController.

        @return a YMultiSensController object allowing you to drive the multi-sensor controller.
        """
        obj: Union[YMultiSensController, None] = yctx._findInCache('MultiSensController', func)
        if obj:
            return obj
        return YMultiSensController(yctx, func)

    @classmethod
    def FirstMultiSensController(cls) -> Union[YMultiSensController, None]:
        """
        Starts the enumeration of multi-sensor controllers currently accessible.
        Use the method YMultiSensController.nextMultiSensController() to iterate on
        next multi-sensor controllers.

        @return a pointer to a YMultiSensController object, corresponding to
                the first multi-sensor controller currently online, or a None pointer
                if there are none.
        """
        return cls.FirstMultiSensControllerInContext(YAPI)

    @classmethod
    def FirstMultiSensControllerInContext(cls, yctx: YAPIContext) -> Union[YMultiSensController, None]:
        """
        Starts the enumeration of multi-sensor controllers currently accessible.
        Use the method YMultiSensController.nextMultiSensController() to iterate on
        next multi-sensor controllers.

        @param yctx : a YAPI context.

        @return a pointer to a YMultiSensController object, corresponding to
                the first multi-sensor controller currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('MultiSensController')
        if hwid:
            return cls.FindMultiSensControllerInContext(yctx, hwid2str(hwid))
        return None

    def nextMultiSensController(self) -> Union[YMultiSensController, None]:
        """
        Continues the enumeration of multi-sensor controllers started using yFirstMultiSensController().
        Caution: You can't make any assumption about the returned multi-sensor controllers order.
        If you want to find a specific a multi-sensor controller, use MultiSensController.findMultiSensController()
        and a hardwareID or a logical name.

        @return a pointer to a YMultiSensController object, corresponding to
                a multi-sensor controller currently online, or a None pointer
                if there are no more multi-sensor controllers to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('MultiSensController', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindMultiSensControllerInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_nSensors(self) -> int:
        """
        Returns the number of sensors to poll.

        @return an integer corresponding to the number of sensors to poll

        On failure, throws an exception or returns YMultiSensController.NSENSORS_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("nSensors")
        if json_val is None:
            return YMultiSensController.NSENSORS_INVALID
        return json_val

    async def set_nSensors(self, newval: int) -> int:
        """
        Changes the number of sensors to poll. Remember to call the
        saveToFlash() method of the module if the
        modification must be kept. It is recommended to restart the
        device with  module->reboot() after modifying
        (and saving) this settings.

        @param newval : an integer corresponding to the number of sensors to poll

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("nSensors", rest_val)

    async def get_maxSensors(self) -> int:
        """
        Returns the maximum configurable sensor count allowed on this device.

        @return an integer corresponding to the maximum configurable sensor count allowed on this device

        On failure, throws an exception or returns YMultiSensController.MAXSENSORS_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("maxSensors")
        if json_val is None:
            return YMultiSensController.MAXSENSORS_INVALID
        return json_val

    async def get_maintenanceMode(self) -> int:
        """
        Returns true when the device is in maintenance mode.

        @return either YMultiSensController.MAINTENANCEMODE_FALSE or
        YMultiSensController.MAINTENANCEMODE_TRUE, according to true when the device is in maintenance mode

        On failure, throws an exception or returns YMultiSensController.MAINTENANCEMODE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("maintenanceMode")
        if json_val is None:
            return YMultiSensController.MAINTENANCEMODE_INVALID
        return json_val

    async def set_maintenanceMode(self, newval: int) -> int:
        """
        Changes the device mode to enable maintenance and to stop sensor polling.
        This way, the device does not automatically restart when it cannot
        communicate with one of the sensors.

        @param newval : either YMultiSensController.MAINTENANCEMODE_FALSE or
        YMultiSensController.MAINTENANCEMODE_TRUE, according to the device mode to enable maintenance and
        to stop sensor polling

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("maintenanceMode", rest_val)

    async def get_lastAddressDetected(self) -> int:
        """
        Returns the I2C address of the most recently detected sensor. This method can
        be used to in case of I2C communication error to determine what is the
        last sensor that can be reached, or after a call to setupAddress
        to make sure that the address change was properly processed.

        @return an integer corresponding to the I2C address of the most recently detected sensor

        On failure, throws an exception or returns YMultiSensController.LASTADDRESSDETECTED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("lastAddressDetected")
        if json_val is None:
            return YMultiSensController.LASTADDRESSDETECTED_INVALID
        return json_val

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YMultiSensController.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YMultiSensControllerValueCallback) -> int:
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

    async def setupAddress(self, addr: int) -> int:
        """
        Configures the I2C address of the only sensor connected to the device.
        It is recommended to put the the device in maintenance mode before
        changing sensor addresses.  This method is only intended to work with a single
        sensor connected to the device. If several sensors are connected, the result
        is unpredictable.

        Note that the device is expecting to find a sensor or a string of sensors with specific
        addresses. Check the device documentation to find out which addresses should be used.

        @param addr : new address of the connected sensor

        @return YAPI.SUCCESS if the call succeeds.
                On failure, throws an exception or returns a negative error code.
        """
        cmd: str
        res: int
        cmd = "A%d" % addr
        res = await self.set_command(cmd)
        if not (res == YAPI.SUCCESS):
            self._throw(YAPI.IO_ERROR, "unable to trigger address change")
            return YAPI.IO_ERROR
        await YAPI.Sleep(1500)
        res = await self.get_lastAddressDetected()
        if not (res > 0):
            self._throw(YAPI.IO_ERROR, "IR sensor not found")
            return YAPI.IO_ERROR
        if not (res == addr):
            self._throw(YAPI.IO_ERROR, "address change failed")
            return YAPI.IO_ERROR
        return YAPI.SUCCESS

    async def get_sensorAddress(self) -> int:
        """
        Triggers the I2C address detection procedure for the only sensor connected to the device.
        This method is only intended to work with a single sensor connected to the device.
        If several sensors are connected, the result is unpredictable.

        @return the I2C address of the detected sensor, or 0 if none is found

        On failure, throws an exception or returns a negative error code.
        """
        res: int
        res = await self.set_command("a")
        if not (res == YAPI.SUCCESS):
            self._throw(YAPI.IO_ERROR, "unable to trigger address detection")
            return res
        await YAPI.Sleep(1000)
        res = await self.get_lastAddressDetected()
        return res

    # --- (end of YMultiSensController implementation)

