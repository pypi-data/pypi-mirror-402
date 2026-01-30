# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_messagebox.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YMessageBox API for MessageBox functions
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
Yoctopuce library: High-level API for YMessageBox and YSMS
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_messagebox_aio
provides: YMessageBox YSms
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

from .yocto_messagebox_aio import  (
    YMessageBox as YMessageBox_aio,
    YSms as YSms_aio
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction, YSyncProxy
)

# --- (generated code: YSms class start)
# noinspection PyProtectedMember
class YSms(YSyncProxy):
    """
    YSms objects are used to describe an SMS message, received or to be sent.
    These objects are used in particular in conjunction with the YMessageBox class.

    """
    _aio: YSms_aio
    # --- (end of generated code: YSms class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSms return codes)
        pass
        # --- (end of generated code: YSms return codes)

    # --- (generated code: YSms implementation)
    if not _DYNAMIC_HELPERS:
        def get_textData(self) -> str:
            """
            Returns the content of the message.

            @return  a string with the content of the message.
            """
            return self._run(self._aio.get_textData())

    if not _DYNAMIC_HELPERS:
        def addText(self, val: str) -> int:
            """
            Add a regular text to the SMS. This function support messages
            of more than 160 characters. ISO-latin accented characters
            are supported. For messages with special unicode characters such as asian
            characters and emoticons, use the  addUnicodeData method.

            @param val : the text to be sent in the message

            @return YAPI.SUCCESS when the call succeeds.
            """
            return self._run(self._aio.addText(val))

    if not _DYNAMIC_HELPERS:
        def addUnicodeData(self, val: list[int]) -> int:
            """
            Add a unicode text to the SMS. This function support messages
            of more than 160 characters, using SMS concatenation.

            @param val : an array of special unicode characters

            @return YAPI.SUCCESS when the call succeeds.
            """
            return self._run(self._aio.addUnicodeData(val))

    if not _DYNAMIC_HELPERS:
        def send(self) -> int:
            """
            Sends the SMS to the recipient. Messages of more than 160 characters are supported
            using SMS concatenation.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.send())

    # --- (end of generated code: YSms implementation)


# --- (generated code: YMessageBox class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YMessageBoxValueCallback = Union[Callable[['YMessageBox', str], Any], None]
    except TypeError:
        YMessageBoxValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YMessageBox(YFunction):
    """
    The YMessageBox class provides SMS sending and receiving capability for
    GSM-enabled Yoctopuce devices.

    """
    _aio: YMessageBox_aio
    # --- (end of generated code: YMessageBox class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YMessageBox return codes)
        SLOTSINUSE_INVALID: Final[int] = YAPI.INVALID_UINT
        SLOTSCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        SLOTSBITMAP_INVALID: Final[str] = YAPI.INVALID_STRING
        PDUSENT_INVALID: Final[int] = YAPI.INVALID_UINT
        PDURECEIVED_INVALID: Final[int] = YAPI.INVALID_UINT
        OBEY_INVALID: Final[str] = YAPI.INVALID_STRING
        COMMAND_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of generated code: YMessageBox return codes)

    # --- (generated code: YMessageBox implementation)

    @classmethod
    def FindMessageBox(cls, func: str) -> YMessageBox:
        """
        Retrieves a SMS message box interface for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the SMS message box interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMessageBox.isOnline() to test if the SMS message box interface is
        indeed online at a given time. In case of ambiguity when looking for
        a SMS message box interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the SMS message box interface, for instance
                YHUBGSM1.messageBox.

        @return a YMessageBox object allowing you to drive the SMS message box interface.
        """
        return cls._proxy(cls, YMessageBox_aio.FindMessageBoxInContext(YAPI_aio, func))

    @classmethod
    def FindMessageBoxInContext(cls, yctx: YAPIContext, func: str) -> YMessageBox:
        """
        Retrieves a SMS message box interface for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the SMS message box interface is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YMessageBox.isOnline() to test if the SMS message box interface is
        indeed online at a given time. In case of ambiguity when looking for
        a SMS message box interface by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the SMS message box interface, for instance
                YHUBGSM1.messageBox.

        @return a YMessageBox object allowing you to drive the SMS message box interface.
        """
        return cls._proxy(cls, YMessageBox_aio.FindMessageBoxInContext(yctx._aio, func))

    @classmethod
    def FirstMessageBox(cls) -> Union[YMessageBox, None]:
        """
        Starts the enumeration of SMS message box interfaces currently accessible.
        Use the method YMessageBox.nextMessageBox() to iterate on
        next SMS message box interfaces.

        @return a pointer to a YMessageBox object, corresponding to
                the first SMS message box interface currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YMessageBox_aio.FirstMessageBoxInContext(YAPI_aio))

    @classmethod
    def FirstMessageBoxInContext(cls, yctx: YAPIContext) -> Union[YMessageBox, None]:
        """
        Starts the enumeration of SMS message box interfaces currently accessible.
        Use the method YMessageBox.nextMessageBox() to iterate on
        next SMS message box interfaces.

        @param yctx : a YAPI context.

        @return a pointer to a YMessageBox object, corresponding to
                the first SMS message box interface currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YMessageBox_aio.FirstMessageBoxInContext(yctx._aio))

    def nextMessageBox(self) -> Union[YMessageBox, None]:
        """
        Continues the enumeration of SMS message box interfaces started using yFirstMessageBox().
        Caution: You can't make any assumption about the returned SMS message box interfaces order.
        If you want to find a specific a SMS message box interface, use MessageBox.findMessageBox()
        and a hardwareID or a logical name.

        @return a pointer to a YMessageBox object, corresponding to
                a SMS message box interface currently online, or a None pointer
                if there are no more SMS message box interfaces to enumerate.
        """
        return self._proxy(type(self), self._aio.nextMessageBox())

    if not _DYNAMIC_HELPERS:
        def get_slotsInUse(self) -> int:
            """
            Returns the number of message storage slots currently in use.

            @return an integer corresponding to the number of message storage slots currently in use

            On failure, throws an exception or returns YMessageBox.SLOTSINUSE_INVALID.
            """
            return self._run(self._aio.get_slotsInUse())

    if not _DYNAMIC_HELPERS:
        def get_slotsCount(self) -> int:
            """
            Returns the total number of message storage slots on the SIM card.

            @return an integer corresponding to the total number of message storage slots on the SIM card

            On failure, throws an exception or returns YMessageBox.SLOTSCOUNT_INVALID.
            """
            return self._run(self._aio.get_slotsCount())

    if not _DYNAMIC_HELPERS:
        def get_pduSent(self) -> int:
            """
            Returns the number of SMS units sent so far.

            @return an integer corresponding to the number of SMS units sent so far

            On failure, throws an exception or returns YMessageBox.PDUSENT_INVALID.
            """
            return self._run(self._aio.get_pduSent())

    if not _DYNAMIC_HELPERS:
        def set_pduSent(self, newval: int) -> int:
            """
            Changes the value of the outgoing SMS units counter.

            @param newval : an integer corresponding to the value of the outgoing SMS units counter

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_pduSent(newval))

    if not _DYNAMIC_HELPERS:
        def get_pduReceived(self) -> int:
            """
            Returns the number of SMS units received so far.

            @return an integer corresponding to the number of SMS units received so far

            On failure, throws an exception or returns YMessageBox.PDURECEIVED_INVALID.
            """
            return self._run(self._aio.get_pduReceived())

    if not _DYNAMIC_HELPERS:
        def set_pduReceived(self, newval: int) -> int:
            """
            Changes the value of the incoming SMS units counter.

            @param newval : an integer corresponding to the value of the incoming SMS units counter

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_pduReceived(newval))

    if not _DYNAMIC_HELPERS:
        def get_obey(self) -> str:
            """
            Returns the phone number authorized to send remote management commands.
            When a phone number is specified, the hub will take contre of all incoming
            SMS messages: it will execute commands coming from the authorized number,
            and delete all messages once received (whether authorized or not).
            If you need to receive SMS messages using your own software, leave this
            attribute empty.

            @return a string corresponding to the phone number authorized to send remote management commands

            On failure, throws an exception or returns YMessageBox.OBEY_INVALID.
            """
            return self._run(self._aio.get_obey())

    if not _DYNAMIC_HELPERS:
        def set_obey(self, newval: str) -> int:
            """
            Changes the phone number authorized to send remote management commands.
            The phone number usually starts with a '+' and does not include spacers.
            When a phone number is specified, the hub will take contre of all incoming
            SMS messages: it will execute commands coming from the authorized number,
            and delete all messages once received (whether authorized or not).
            If you need to receive SMS messages using your own software, leave this
            attribute empty. Remember to call the saveToFlash() method of the
            module if the modification must be kept.

            This feature is only available since YoctoHub-GSM-4G.

            @param newval : a string corresponding to the phone number authorized to send remote management commands

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.set_obey(newval))

    if not _DYNAMIC_HELPERS:
        def set_command(self, newval: str) -> int:
            return self._run(self._aio.set_command(newval))

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YMessageBoxValueCallback) -> int:
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
        def clearPduCounters(self) -> int:
            """
            Clear the SMS units counters.

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.clearPduCounters())

    if not _DYNAMIC_HELPERS:
        def sendTextMessage(self, recipient: str, message: str) -> int:
            """
            Sends a regular text SMS, with standard parameters. This function can send messages
            of more than 160 characters, using SMS concatenation. ISO-latin accented characters
            are supported. For sending messages with special unicode characters such as asian
            characters and emoticons, use newMessage to create a new message and define
            the content of using methods addText and addUnicodeData.

            @param recipient : a text string with the recipient phone number, either as a
                    national number, or in international format starting with a plus sign
            @param message : the text to be sent in the message

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.sendTextMessage(recipient, message))

    if not _DYNAMIC_HELPERS:
        def sendFlashMessage(self, recipient: str, message: str) -> int:
            """
            Sends a Flash SMS (class 0 message). Flash messages are displayed on the handset
            immediately and are usually not saved on the SIM card. This function can send messages
            of more than 160 characters, using SMS concatenation. ISO-latin accented characters
            are supported. For sending messages with special unicode characters such as asian
            characters and emoticons, use newMessage to create a new message and define
            the content of using methods addText et addUnicodeData.

            @param recipient : a text string with the recipient phone number, either as a
                    national number, or in international format starting with a plus sign
            @param message : the text to be sent in the message

            @return YAPI.SUCCESS when the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.sendFlashMessage(recipient, message))

    def newMessage(self, recipient: str) -> YSms:
        """
        Creates a new empty SMS message, to be configured and sent later on.

        @param recipient : a text string with the recipient phone number, either as a
                national number, or in international format starting with a plus sign

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return self._proxy(YSms, self._run(self._aio.newMessage(recipient)))

    if not _DYNAMIC_HELPERS:
        def get_messages(self) -> list[YSms]:
            """
            Returns the list of messages received and not deleted. This function
            will automatically decode concatenated SMS.

            @return an YSms object list.

            On failure, throws an exception or returns an empty list.
            """
            return self._run(self._aio.get_messages())

    # --- (end of generated code: YMessageBox implementation)

