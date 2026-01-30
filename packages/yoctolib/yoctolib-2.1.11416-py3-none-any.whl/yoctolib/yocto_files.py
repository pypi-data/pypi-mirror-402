# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_files.py 69442 2025-10-16 08:53:14Z mvuilleu $
#
#  Implements the asyncio YFiles API for Files functions
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
Yoctopuce library: High-level API for YFiles
version: PATCH_WITH_VERSION
requires: yocto_api
requires: yocto_files_aio
provides: YFiles YFileRecord
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

from .yocto_files_aio import (
    YFiles as YFiles_aio,
    YFileRecord
)
from .yocto_api import (
    YAPIContext, YAPI, YAPI_aio, YFunction,xarray
)

# --- (generated code: YFiles class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YFilesValueCallback = Union[Callable[['YFiles', str], Any], None]
    except TypeError:
        YFilesValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YFiles(YFunction):
    """
    The YFiles class is used to access the filesystem embedded on
    some Yoctopuce devices. This filesystem makes it
    possible for instance to design a custom web UI
    (for networked devices) or to add fonts (on display devices).

    """
    _aio: YFiles_aio
    # --- (end of generated code: YFiles class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YFiles return codes)
        FILESCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        FREESPACE_INVALID: Final[int] = YAPI.INVALID_UINT
        # --- (end of generated code: YFiles return codes)

    # --- (generated code: YFiles implementation)

    @classmethod
    def FindFiles(cls, func: str) -> YFiles:
        """
        Retrieves a filesystem for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the filesystem is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YFiles.isOnline() to test if the filesystem is
        indeed online at a given time. In case of ambiguity when looking for
        a filesystem by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the filesystem, for instance
                YRGBLED2.files.

        @return a YFiles object allowing you to drive the filesystem.
        """
        return cls._proxy(cls, YFiles_aio.FindFilesInContext(YAPI_aio, func))

    @classmethod
    def FindFilesInContext(cls, yctx: YAPIContext, func: str) -> YFiles:
        """
        Retrieves a filesystem for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the filesystem is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YFiles.isOnline() to test if the filesystem is
        indeed online at a given time. In case of ambiguity when looking for
        a filesystem by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the filesystem, for instance
                YRGBLED2.files.

        @return a YFiles object allowing you to drive the filesystem.
        """
        return cls._proxy(cls, YFiles_aio.FindFilesInContext(yctx._aio, func))

    @classmethod
    def FirstFiles(cls) -> Union[YFiles, None]:
        """
        Starts the enumeration of filesystems currently accessible.
        Use the method YFiles.nextFiles() to iterate on
        next filesystems.

        @return a pointer to a YFiles object, corresponding to
                the first filesystem currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YFiles_aio.FirstFilesInContext(YAPI_aio))

    @classmethod
    def FirstFilesInContext(cls, yctx: YAPIContext) -> Union[YFiles, None]:
        """
        Starts the enumeration of filesystems currently accessible.
        Use the method YFiles.nextFiles() to iterate on
        next filesystems.

        @param yctx : a YAPI context.

        @return a pointer to a YFiles object, corresponding to
                the first filesystem currently online, or a None pointer
                if there are none.
        """
        return cls._proxy(cls, YFiles_aio.FirstFilesInContext(yctx._aio))

    def nextFiles(self) -> Union[YFiles, None]:
        """
        Continues the enumeration of filesystems started using yFirstFiles().
        Caution: You can't make any assumption about the returned filesystems order.
        If you want to find a specific a filesystem, use Files.findFiles()
        and a hardwareID or a logical name.

        @return a pointer to a YFiles object, corresponding to
                a filesystem currently online, or a None pointer
                if there are no more filesystems to enumerate.
        """
        return self._proxy(type(self), self._aio.nextFiles())

    if not _DYNAMIC_HELPERS:
        def get_filesCount(self) -> int:
            """
            Returns the number of files currently loaded in the filesystem.

            @return an integer corresponding to the number of files currently loaded in the filesystem

            On failure, throws an exception or returns YFiles.FILESCOUNT_INVALID.
            """
            return self._run(self._aio.get_filesCount())

    if not _DYNAMIC_HELPERS:
        def get_freeSpace(self) -> int:
            """
            Returns the free space for uploading new files to the filesystem, in bytes.

            @return an integer corresponding to the free space for uploading new files to the filesystem, in bytes

            On failure, throws an exception or returns YFiles.FREESPACE_INVALID.
            """
            return self._run(self._aio.get_freeSpace())

    if not _IS_MICROPYTHON:
        def registerValueCallback(self, callback: YFilesValueCallback) -> int:
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
        def format_fs(self) -> int:
            """
            Reinitialize the filesystem to its clean, unfragmented, empty state.
            All files previously uploaded are permanently lost.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.format_fs())

    if not _DYNAMIC_HELPERS:
        def get_list(self, pattern: str) -> list[YFileRecord]:
            """
            Returns a list of YFileRecord objects that describe files currently loaded
            in the filesystem.

            @param pattern : an optional filter pattern, using star and question marks
                    as wild cards. When an empty pattern is provided, all file records
                    are returned.

            @return a list of YFileRecord objects, containing the file path
                    and name, byte size and 32-bit CRC of the file content.

            On failure, throws an exception or returns an empty list.
            """
            return self._run(self._aio.get_list(pattern))

    if not _DYNAMIC_HELPERS:
        def fileExist(self, filename: str) -> bool:
            """
            Tests if a file exists on the filesystem of the module.

            @param filename : the filename to test.

            @return true if the file exists, false otherwise.

            On failure, throws an exception.
            """
            return self._run(self._aio.fileExist(filename))

    if not _DYNAMIC_HELPERS:
        def download(self, pathname: str) -> xarray:
            """
            Downloads the requested file and returns a binary buffer with its content.

            @param pathname : path and name of the file to download

            @return a binary buffer with the file content

            On failure, throws an exception or returns an empty content.
            """
            return self._run(self._aio.download(pathname))

    if not _DYNAMIC_HELPERS:
        def upload(self, pathname: str, content: Union[xarray, bytearray, bytes]) -> int:
            """
            Uploads a file to the filesystem, to the specified full path name.
            If a file already exists with the same path name, its content is overwritten.

            @param pathname : path and name of the new file to create
            @param content : binary buffer with the content to set

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.upload(pathname, content))

    if not _DYNAMIC_HELPERS:
        def remove(self, pathname: str) -> int:
            """
            Deletes a file, given by its full path name, from the filesystem.
            Because of filesystem fragmentation, deleting a file may not always
            free up the whole space used by the file. However, rewriting a file
            with the same path name will always reuse any space not freed previously.
            If you need to ensure that no space is taken by previously deleted files,
            you can use format_fs to fully reinitialize the filesystem.

            @param pathname : path and name of the file to remove.

            @return YAPI.SUCCESS if the call succeeds.

            On failure, throws an exception or returns a negative error code.
            """
            return self._run(self._aio.remove(pathname))

    if not _DYNAMIC_HELPERS:
        def get_content_crc(self, content: xarray) -> int:
            """
            Returns the expected file CRC for a given content.
            Note that the CRC value may vary depending on the version
            of the filesystem used by the hub, so it is important to
            use this method if a reference value needs to be computed.

            @param content : a buffer representing a file content

            @return the 32-bit CRC summarizing the file content, as it would
                    be returned by the get_crc() method of
                    YFileRecord objects returned by get_list().
            """
            return self._run(self._aio.get_content_crc(content))

    # --- (end of generated code: YFiles implementation)
