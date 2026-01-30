# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_files_aio.py 70518 2025-11-26 16:18:50Z mvuilleu $
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
Yoctopuce library: Asyncio implementation of YFiles
version: PATCH_WITH_VERSION
requires: yocto_api_aio
provides: YFiles YFileRecord
"""
from __future__ import annotations

import json
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

# --- (generated code: YFileRecord class start)
# noinspection PyProtectedMember
class YFileRecord:
    """
    YFileRecord objects are used to describe a file that is stored on a Yoctopuce device.
    These objects are used in particular in conjunction with the YFiles class.

    """
    # --- (end of generated code: YFileRecord class start)

    # --- (generated code: YFileRecord attributes declaration)
    _name: str
    _size: int
    _crc: int
    # --- (end of generated code: YFileRecord attributes declaration)


    def __init__(self, json_data: str):
        # --- (generated code: YFileRecord constructor)
        self._name = ''
        self._size = 0
        self._crc = 0
        # --- (end of generated code: YFileRecord constructor)
        new_json: Any = json.loads(json_data)
        self._name = new_json["name"]
        self._size = new_json["size"]
        self._crc = new_json["crc"]

    # --- (generated code: YFileRecord implementation)
    def get_name(self) -> str:
        """
        Returns the name of the file.

        @return a string with the name of the file.
        """
        return self._name

    def get_size(self) -> int:
        """
        Returns the size of the file in bytes.

        @return the size of the file.
        """
        return self._size

    def get_crc(self) -> int:
        """
        Returns the 32-bit CRC of the file content.

        @return the 32-bit CRC of the file content.
        """
        return self._crc

    # --- (end of generated code: YFileRecord implementation)


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
    # --- (end of generated code: YFiles class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YFiles return codes)
        FILESCOUNT_INVALID: Final[int] = YAPI.INVALID_UINT
        FREESPACE_INVALID: Final[int] = YAPI.INVALID_UINT
        # --- (end of generated code: YFiles return codes)

    # --- (generated code: YFiles attributes declaration)
    _valueCallback: YFilesValueCallback
    _ver: int
    # --- (end of generated code: YFiles attributes declaration)


    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'Files', func)
        # --- (generated code: YFiles constructor)
        self._ver = 0
        # --- (end of generated code: YFiles constructor)

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
        return cls.FindFilesInContext(YAPI, func)

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
        obj: Union[YFiles, None] = yctx._findInCache('Files', func)
        if obj:
            return obj
        return YFiles(yctx, func)

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
        return cls.FirstFilesInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('Files')
        if hwid:
            return cls.FindFilesInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Files', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindFilesInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_filesCount(self) -> int:
        """
        Returns the number of files currently loaded in the filesystem.

        @return an integer corresponding to the number of files currently loaded in the filesystem

        On failure, throws an exception or returns YFiles.FILESCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("filesCount")
        if json_val is None:
            return YFiles.FILESCOUNT_INVALID
        return json_val

    async def get_freeSpace(self) -> int:
        """
        Returns the free space for uploading new files to the filesystem, in bytes.

        @return an integer corresponding to the free space for uploading new files to the filesystem, in bytes

        On failure, throws an exception or returns YFiles.FREESPACE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("freeSpace")
        if json_val is None:
            return YFiles.FREESPACE_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YFilesValueCallback) -> int:
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

    async def sendCommand(self, command: str) -> xarray:
        url: str
        url = "files.json?a=%s" % command

        return await self._download(url)

    async def _getVersion(self) -> int:
        json: xarray
        if self._ver > 0:
            return self._ver
        # //may throw an exception
        json = await self.sendCommand("info")
        if json[0] != 123:
            # ascii code for '{'
            self._ver = 30
        else:
            self._ver = YAPI._atoi(self._json_get_key(json, "ver"))
        return self._ver

    async def format_fs(self) -> int:
        """
        Reinitialize the filesystem to its clean, unfragmented, empty state.
        All files previously uploaded are permanently lost.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        json: xarray
        res: str
        json = await self.sendCommand("format")
        res = self._json_get_key(json, "res")
        if not (res == "ok"):
            self._throw(YAPI.IO_ERROR, "format failed")
            return YAPI.IO_ERROR
        return YAPI.SUCCESS

    async def get_list(self, pattern: str) -> list[YFileRecord]:
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
        json: xarray
        filelist: list[xarray] = []
        res: Union[list[YFileRecord], None] = []
        json = await self.sendCommand("dir&f=%s" % pattern)
        filelist = self._json_get_array(json)
        del res[:]
        for ii_0 in filelist:
            res.append(YFileRecord(ii_0.decode('latin-1')))
        return res

    async def fileExist(self, filename: str) -> bool:
        """
        Tests if a file exists on the filesystem of the module.

        @param filename : the filename to test.

        @return true if the file exists, false otherwise.

        On failure, throws an exception.
        """
        json: xarray
        filelist: list[xarray] = []
        if len(filename) == 0:
            return False
        json = await self.sendCommand("dir&f=%s" % filename)
        filelist = self._json_get_array(json)
        if len(filelist) > 0:
            return True
        return False

    async def download(self, pathname: str) -> xarray:
        """
        Downloads the requested file and returns a binary buffer with its content.

        @param pathname : path and name of the file to download

        @return a binary buffer with the file content

        On failure, throws an exception or returns an empty content.
        """
        return await self._download(pathname)

    async def upload(self, pathname: str, content: Union[xarray, bytearray, bytes]) -> int:
        """
        Uploads a file to the filesystem, to the specified full path name.
        If a file already exists with the same path name, its content is overwritten.

        @param pathname : path and name of the new file to create
        @param content : binary buffer with the content to set

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._upload(pathname, content)

    async def remove(self, pathname: str) -> int:
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
        json: xarray
        res: str
        json = await self.sendCommand("del&f=%s" % pathname)
        res  = self._json_get_key(json, "res")
        if not (res == "ok"):
            self._throw(YAPI.IO_ERROR, "unable to remove file")
            return YAPI.IO_ERROR
        return YAPI.SUCCESS

    async def get_content_crc(self, content: xarray) -> int:
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
        fsver: int
        sz: int
        blkcnt: int
        meta: xarray
        blkidx: int
        blksz: int
        part: int
        res: int
        sz = len(content)

        fsver = await self._getVersion()
        if fsver < 40:
            res = content[0:0+sz].crc32()
            res = ((res & 0x7fffffff) - 2 * ((res >> 1) & 0x40000000))
            return res
        blkcnt = (sz + 255) // 256
        meta = xbytearray(4 * blkcnt)
        blkidx = 0
        while blkidx < blkcnt:
            blksz = sz - blkidx * 256
            if blksz > 256:
                blksz = 256
            part = ((content[blkidx * 256:blkidx * 256+blksz].crc32()) ^ int(0xffffffff))
            meta[4 * blkidx] = (part & 255)
            meta[4 * blkidx + 1] = ((part >> 8) & 255)
            meta[4 * blkidx + 2] = ((part >> 16) & 255)
            meta[4 * blkidx + 3] = ((part >> 24) & 255)
            blkidx = blkidx + 1
        res = ((meta[0:0+4 * blkcnt].crc32()) ^ int(0xffffffff))
        res = ((res & 0x7fffffff) - 2 * ((res >> 1) & 0x40000000))
        return res

    # --- (end of generated code: YFiles implementation)

