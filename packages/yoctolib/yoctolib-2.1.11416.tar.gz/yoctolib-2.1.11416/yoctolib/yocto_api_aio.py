# -*- coding: utf-8 -*-
# *********************************************************************
# *
# * $Id: yocto_api_aio.py 71244 2026-01-12 07:18:59Z mvuilleu $
# *
# * Typed python programming interface; code common to all modules
# *
# * - - - - - - - - - License information: - - - - - - - - -
# *
# *  Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.
# *
# *  Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
# *  non-exclusive license to use, modify, copy and integrate this
# *  file into your software for the sole purpose of interfacing
# *  with Yoctopuce products.
# *
# *  You may reproduce and distribute copies of this file in
# *  source or object form, as long as the sole purpose of this
# *  code is to interface with Yoctopuce products. You must retain
# *  this notice in the distributed source file.
# *
# *  You should refer to Yoctopuce General Terms and Conditions
# *  for additional information regarding your rights and
# *  obligations.
# *
# *  THE SOFTWARE AND DOCUMENTATION ARE PROVIDED 'AS IS' WITHOUT
# *  WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING
# *  WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
# *  FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
# *  EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
# *  INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
# *  COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR
# *  SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT
# *  LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
# *  CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
# *  BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
# *  WARRANTY, OR OTHERWISE.
# *
# *********************************************************************/
"""
Yoctopuce library: asyncio implementation of common code used by all devices
version: 2.1.11416
provides: YAPI YModule YFunction YSensor YRefParam
"""
# Enable forward references
from __future__ import annotations

__all__ = (
    'xarray', 'xbytearray', 'xmemoryview', 'xlist', 'xdict', 'xStringIO', 'xBytesIO',
    'ticks_ms', 'ticks_add', 'ticks_diff', 'ticks_past', 'print_exception',
    'YAPIContext', 'YAPI', 'YRefParam', 'YAPI_Exception', 'HwId', 'hwid2str',
    'YHub', 'YFunction', 'YModule', 'YFirmwareUpdate', 'YSensor', 'YMeasure',  # noqa
    'YDataLogger', 'YDataStream', 'YDataSet', 'YConsolidatedDataSet'  # noqa
)

# IMPORTANT: This file must stay compatible with
# - CPython 3.8 (for backward-compatibility with Windows 7)
# - micropython (for inclusion in VirtualHub/YoctoHub)

# Load common libraries
import atexit, sys, time, math, json, re, random, binascii, asyncio, hashlib

# On MicroPython, code below will be optimized at compile time
if sys.implementation.name != "micropython":
    # In CPython, enable edit-time type checking, including Final declaration
    from typing import Any, Union, Type, TypeVar, Final, NamedTuple
    from collections import OrderedDict
    from collections.abc import Callable, Awaitable, Coroutine
    import ssl  # used to import CERT_* constants
    from ssl import SSLContext, SSLCertVerificationError as CertError

    const = lambda obj: obj
    _IS_MICROPYTHON = False
else:
    # In our micropython VM, common generic types are global built-ins
    # Others such as TypeVar should be avoided when using micropython, as they produce overhead in runtime code
    # Final is converted into const() expression just before compiling
    # ssl constants are resolved at compile time by ympy_cross
    from collections import namedtuple, OrderedDict
    from sys import print_exception  # noqa
    from tls import SSLContext, CertError  # noqa

    _IS_MICROPYTHON: Final[bool] = True  # noqa

# Symbols exported as Final will be preprocessed for micropython for optimization (converted to const() notation)
# Those starting with an underline will not be added to the module global dictionary
_YOCTO_API_VERSION_STR: Final[str] = "2.0"
_YOCTO_API_BUILD_VERSION_STR: Final[str] = "2.1.11416"

_YOCTO_DEFAULT_PORT: Final[int] = 4444
_YOCTO_DEFAULT_HTTPS_PORT: Final[int] = 4443
_YOCTO_VENDORID: Final[int] = 0x24e0
_YOCTO_DEVID_FACTORYBOOT: Final[int] = 1

_YOCTO_DEVID_BOOTLOADER: Final[int] = 2
_YOCTO_ERRMSG_LEN: Final[int] = 256
_YOCTO_MANUFACTURER_LEN: Final[int] = 20
_YOCTO_SERIAL_LEN: Final[int] = 20
_YOCTO_BASE_SERIAL_LEN: Final[int] = 8
_YOCTO_PRODUCTNAME_LEN: Final[int] = 28
_YOCTO_FIRMWARE_LEN: Final[int] = 22
_YOCTO_LOGICAL_LEN: Final[int] = 20
_YOCTO_FUNCTION_LEN: Final[int] = 20

_YOCTO_PUBVAL_SIZE: Final[int] = 6  # Size of PUBVAL data (may not be non-null terminated)
_YOCTO_PUBVAL_LEN: Final[int] = 16  # Temporary storage, > _YOCTO_PUBVAL_SIZE
_YOCTO_PASS_LEN: Final[int] = 20
_YOCTO_REALM_LEN: Final[int] = 20

_YOCTO_CALIB_TYPE_OFS: Final[int] = 30
_YOCTO_BASETYPES: Final[tuple[str, str]] = ("Function", "Sensor")

_EVENT_PLUG: Final[int] = 1
_EVENT_UNPLUG: Final[int] = -1
_EVENT_CHANGE: Final[int] = 0
_TIMED_REPORT_SHIFT: Final[int] = 100
_EVENT_SSDP_CB: Final[int] = 200

_NOTIFY_V2_LEGACY: Final[int] = 0  # unused (reserved for compatibility with legacy notifications)
_NOTIFY_V2_6RAWBYTES: Final[int] = 1  # largest type: data is always 6 bytes
_NOTIFY_V2_TYPEDDATA: Final[int] = 2  # other types: first data byte holds the decoding format
_NOTIFY_V2_FLUSHGROUP: Final[int] = 3  # no data associated

# PubVal V2 notification types
_PUBVAL_LEGACY: Final[int] = 0  # 0-6 ASCII characters (normally sent as YSTREAM_NOTICE)
_PUBVAL_1RAWBYTE: Final[int] = 1  # 1 raw byte  (=2 characters)
_PUBVAL_2RAWBYTES: Final[int] = 2  # 2 raw bytes (=4 characters)
_PUBVAL_3RAWBYTES: Final[int] = 3  # 3 raw bytes (=6 characters)
_PUBVAL_4RAWBYTES: Final[int] = 4  # 4 raw bytes (=8 characters)
_PUBVAL_5RAWBYTES: Final[int] = 5  # 5 raw bytes (=10 characters)
_PUBVAL_6RAWBYTES: Final[int] = 6  # 6 hex bytes (=12 characters) (sent as V2_6RAWBYTES)
_PUBVAL_C_LONG: Final[int] = 7  # 32-bit C signed integer
_PUBVAL_C_FLOAT: Final[int] = 8  # 32-bit C float
_PUBVAL_YOCTO_FLOAT_E3: Final[int] = 9  # 32-bit Yocto fixed-point format (e-3)
_PUBVAL_YOCTO_FLOAT_E6: Final[int] = 10  # 32-bit Yocto fixed-point format (e-6)

# Network notification codes
_NOTIFY_NETPKT_NAME: Final[int] = 48  # '0'
_NOTIFY_NETPKT_CHILD: Final[int] = 50  # '2'
_NOTIFY_NETPKT_FUNCNAME: Final[int] = 52  # '4'
_NOTIFY_NETPKT_FUNCVAL: Final[int] = 53  # '5'
_NOTIFY_NETPKT_FUNCNAMEYDX: Final[int] = 56  # '8'
_NOTIFY_NETPKT_CONFCHGYDX: Final[int] = 115  # 's'
_NOTIFY_NETPKT_FLUSHV2YDX: Final[int] = 116  # 't'
_NOTIFY_NETPKT_FUNCV2YDX: Final[int] = 117  # 'u'
_NOTIFY_NETPKT_TIMEV2YDX: Final[int] = 118  # 'v'
_NOTIFY_NETPKT_DEVLOGYDX: Final[int] = 119  # 'w'
_NOTIFY_NETPKT_TIMEVALYDX: Final[int] = 120  # 'x'
_NOTIFY_NETPKT_FUNCVALYDX: Final[int] = 121  # 'y'
_NOTIFY_NETPKT_TIMEAVGYDX: Final[int] = 122  # 'z'
_NOTIFY_NETPKT_NOT_SYNC: Final[int] = 64  # '@'
_NOTIFY_NETPKT_LOG: Final[int] = 55  # '7'
_NOTIFY_NETPKT_STOP: Final[int] = 10

# YGenericHub states
_HUB_UNKNOWN: Final[int] = -6  # hub was never connected in any way
_HUB_DETACHED: Final[int] = -5  # hub has been connected, but is no more trying to reconnect
_HUB_DETACHING: Final[int] = -4  # about to return to detached state
_HUB_DISCONNECTED: Final[int] = -3  # currently disconnected but waiting to reconnect
_HUB_DISCONNECTING: Final[int] = -2  # about to return to disconnected state
_HUB_CONNECTING: Final[int] = -1  # actively reconnecting to hub
_HUB_CONNECTED: Final[int] = 0  # successfully connected (target state for TestHub, before disconnecting again)
_HUB_PREREGISTERED: Final[int] = 1  # preregistered hub
_HUB_REGISTERED: Final[int] = 2  # registered hub (trigger exceptions on failed updates)
_HUB_CALLBACK: Final[int] = 3  # or websocket callback hub, triggers exceptions on failed updates

# network timeouts, in milliseconds
_MAX_REQUEST_MS: Final[int] = 5000
_YIO_IDLE_TCP_TIMEOUT: Final[int] = 5000
_YIO_DEFAULT_TCP_TIMEOUT: Final[int] = 20000
_YIO_1_MINUTE_TCP_TIMEOUT: Final[int] = 60000
_YIO_10_MINUTES_TCP_TIMEOUT: Final[int] = 600000
_NET_HUB_NOT_CONNECTION_TIMEOUT: Final[int] = 6000
_YPROG_BOOTLOADER_TIMEOUT: Final[int] = 20000

_LOG_LEVEL: Final[int] = 0

# typing class
ByteArrayLike = Union["xarray", bytearray, memoryview, bytes]

#################################################################################
#                                                                               #
#          MicroPython-specific definitions, and their CPython equivalent       #
#                                                                               #
#################################################################################

if _IS_MICROPYTHON:
    from time import ticks_ms, ticks_add, ticks_diff, ticks_past  # noqa
    from xmem import xarray, xbytearray, xmemoryview, xlist, xdict, xStringIO, xBytesIO  # noqa
else:
    # -Class-Export-Start: from .micropython_emu import *
    # -Class-Export-Preamble: import time
    # -Class-Export-Preamble: from typing import Union
    import io, array, ssl, traceback


    #################################################################################
    #                                                                               #
    #          Compatibility layer to run MicroPython code in CPython               #
    #                                                                               #
    #################################################################################

    # Equivalents for micropython-specific fast millisecond timing functions
    # Remember that ticks_ms will wrap: always use ticks_add and ticks_diff !
    def ticks_ms() -> int:
        return time.time_ns() // 1_000_000

    def ticks_add(ticks: int, delta: int) -> int:
        return ticks + delta

    def ticks_diff(ticks1: int, ticks2: int) -> int:
        return ticks1 - ticks2

    def ticks_past(timeout: int) -> int:
        return ticks_ms() - timeout >= 0

    # Simple exception-printing function, compatible with Python 3.8+
    # (the signature of traceback.print_exception has changed in Python 3.10...)
    def print_exception(exc):
        tb_exc = traceback.TracebackException.from_exception(exc)
        print(''.join(tb_exc.format()))
        if isinstance(exc, YAPI_Exception):
            print("(errorType=%d, errorMessage=%s)" % (exc.errorType, exc.errorMessage))


    # Equivalents our micropython xarray objects, stored in external RAM
    #
    # This code is not optimized for efficiency in CPython, which
    # runs very fast anyway, but to replicate MicroPython behaviour
    # in order to facilitate debugging

    _BYTEARRAY_TYPECODE = '\001'
    _TRACK_XARRAY_LEAKS = False

    if _TRACK_XARRAY_LEAKS:
        import inspect, weakref

        # noinspection PyProtectedMember
        class InstanceTracker(type):
            def __init__(cls, name, bases, dct):
                super().__init__(name, bases, dct)
                cls._instances = weakref.WeakSet()
                cls._instanceCounter = 0
                def __hash__(self):
                    return hash(self._instance_id)
                cls.__hash__ = __hash__

            def __call__(cls, *args, **kwargs):
                instance = super().__call__(*args, **kwargs)
                frame = inspect.currentframe()
                try:
                    instance._origin = '?'
                    caller_frame = frame.f_back
                    if caller_frame is not None:
                        instance._origin = caller_frame.f_code.co_filename + (":%d" % caller_frame.f_lineno)
                        if cls == xbytearray:
                            print("* new %s(%d) in %s" % (cls.__name__, len(instance._obj), instance._origin))
                finally:
                    del frame
                cls._instanceCounter += 1
                instance._instance_id = cls._instanceCounter
                cls._instances.add(instance)
                return instance

            def total_allocated(cls) -> int:
                total:int = 0
                for instance in cls._instances:
                    total += len(instance._obj)
                return total

            def dump_instances(cls):
                print(f"Instances of {cls.__name__}:")
                for instance in cls._instances:
                    print(f"- {instance._origin} #{instance._instance_id}: {len(instance._obj)} bytes")

        xarrayMetaClass = InstanceTracker
    else:
        xarrayMetaClass = type

    # noinspection PyProtectedMember
    class xarray(metaclass=xarrayMetaClass):
        _obj: Union[array.array, bytearray, memoryview]
        _classname: str
        _typecode: str
        _itemsize: int

        # noinspection PyUnusedLocal
        def __init__(self, typecode: str, initializer=None, alloc=None):
            if initializer is None:
                initializer = []
            elif isinstance(initializer, int):
                initializer = [0] * initializer
            elif isinstance(initializer, xarray):
                initializer = initializer._obj
            self._classname = 'xarray'
            self._obj = array.array(typecode, initializer)
            self._typecode = self._obj.typecode
            self._itemsize = self._obj.itemsize

        def __getattr__(self, attr: str) -> Union[int, str]:
            if attr == 'typecode':
                return self._typecode
            elif attr == 'itemsize':
                return self._itemsize
            raise AttributeError('there is no attribute ' + attr + ' in xarray objects')

        def __setattr__(self, attr: str, value):
            if attr == 'typecode' or attr == 'itemsize':
                raise AttributeError('attribute ' + attr + ' is read-only')
            super().__setattr__(attr, value)

        def __str__(self) -> str:
            plen: int = 64 // self._itemsize
            more: str = ''
            if plen < len(self._obj):
                more = ', ...'
            else:
                plen = len(self._obj)
            if self._typecode == _BYTEARRAY_TYPECODE:
                content = '(' + str(bytes(memoryview(self._obj)[:plen])) + more[2:] + ')'
            elif plen == 0:
                content = '(' + str(array.array(self._typecode))[6:-1] + ')'
            else:
                content = '(' + str(array.array(self._typecode, self._obj[:plen]))[6:-2] + more + '])'
            return self._classname + content

        def __repr__(self) -> str:
            return str(self)

        def __len__(self) -> int:
            return len(self._obj)

        def __contains__(self, buffer: Union[bytearray, bytes, int]) -> bool:
            # 'in' operator is more type-tolerant than 'find' and return False
            # except for strings, where we always want to catch missing encoding
            if isinstance(buffer, str):
                raise TypeError("can't convert 'str' object to bytes implicitly")
            try:
                res: bool = (self.find(buffer) >= 0)
            except TypeError:
                return False
            return res

        def __getitem__(self, key: Union[int, slice]):
            if isinstance(key, slice):
                res = xmemoryview(self)
                res._obj = memoryview(res._obj)[key]
                return res
            else:
                return self._obj[key]

        def __setitem__(self, key: Union[int, slice], value):
            if isinstance(value, xarray):
                self._obj[key] = value._obj
            else:
                if isinstance(value, str):
                    value = value.encode('ascii')
                self._obj[key] = value

        def __add__(self, other: ByteArrayLike) -> xarray:
            if self._typecode == _BYTEARRAY_TYPECODE:
                res = xbytearray(self._obj)
            else:
                res = xarray(self._typecode, self._obj)
            otherbuf = other._obj if isinstance(other, xarray) else other
            res._obj[len(self):] = otherbuf
            return res

        def __iadd__(self, other: ByteArrayLike) -> xarray:
            if self._typecode == _BYTEARRAY_TYPECODE:
                newobj = bytearray(self._obj)
            else:
                newobj = array.array(self._typecode, self._obj)
            otherbuf = other._obj if isinstance(other, xarray) else other
            newobj[len(self):] = otherbuf
            self._obj = newobj
            return self

        def __lt__(self, other: ByteArrayLike) -> bool:
            otherbuf = other._obj if isinstance(other, xarray) else other
            return self._obj < otherbuf

        def __le__(self, other: ByteArrayLike) -> bool:
            otherbuf = other._obj if isinstance(other, xarray) else other
            return self._obj <= otherbuf

        def __eq__(self, other: ByteArrayLike) -> bool:
            otherbuf = other._obj if isinstance(other, xarray) else other
            return self._obj == otherbuf

        def __ne__(self, other: ByteArrayLike) -> bool:
            otherbuf = other._obj if isinstance(other, xarray) else other
            return self._obj != otherbuf

        def __ge__(self, other: ByteArrayLike) -> bool:
            otherbuf = other._obj if isinstance(other, xarray) else other
            return self._obj >= otherbuf

        def __gt__(self, other: ByteArrayLike) -> bool:
            otherbuf = other._obj if isinstance(other, xarray) else other
            return self._obj > otherbuf

        def append(self, element: int) -> None:
            self._obj.append(element)

        def extend(self, elements: ByteArrayLike) -> None:
            self._obj.extend(elements)

        def _find_ex(self, rev: bool, needle: Union[bytearray, bytes, int], start: Union[int, None] = 0, stop: Union[int, None] = None) -> int:
            # find must fail for any object that does not implement buffer protocol,
            # except for plain integers that must be converted to the proper type of int
            needle: bytearray
            barr: bytearray
            typeOK: bool = True
            if isinstance(needle, int) or isinstance(needle, float):
                if self._typecode == _BYTEARRAY_TYPECODE and isinstance(needle, int):
                    needle = bytearray([needle])
                else:
                    needle = bytearray(array.array(self._typecode, [needle]))
            try:
                memoryview(needle)
            except TypeError:
                typeOK = False
            if not typeOK:
                raise TypeError("can't convert '%s' object to bytes implicitly" % type(needle).__name__)
            if isinstance(self._obj, bytearray):
                barr = self._obj
            else:
                # must create a bytearray to search :-(
                barr = bytearray(self._obj)
            bstart: int = start * self._itemsize
            bstop: int = None if stop is None else stop * self._itemsize
            res: int
            if rev:
                res = barr.rfind(needle, bstart, bstop)
            else:
                res = barr.find(needle, bstart, bstop)
            if self._itemsize > 1:
                # skip over unaligned matches
                while res > 0 and res % self._itemsize != 0:
                    if rev:
                        bstop = res - 1
                        res = -1
                        if bstop <= bstart: break
                        res = barr.rfind(needle, bstart, bstop)
                    else:
                        bstart = res + 1
                        res = -1
                        if bstop is not None and bstart >= bstop: break
                        res = barr.find(needle, bstart, bstop)
                if res > 0:
                    res //= self._itemsize
            return res

        def find(self, *args) -> int:
            return self._find_ex(False, *args)

        def rfind(self, *args) -> int:
            return self._find_ex(True, *args)

        def _strip_ex(self, sides: int, *args) -> xmemoryview:
            barr: bytearray
            if isinstance(self._obj, bytearray):
                barr = self._obj
            else:
                # must create a bytearray to search :-(
                barr = bytearray(self._obj)
            start: int = 0
            stop: int = len(barr)
            if sides >= 0 and start < stop:
                start = len(barr) - len(barr.lstrip(*args))
            if sides <= 0 and start < stop:
                stop = len(barr.rstrip(*args))
            if start > stop:
                start = stop = 0
            return self[start:stop]

        def strip(self, *args) -> xmemoryview:
            return self._strip_ex(0, *args)

        def lstrip(self, *args) -> xmemoryview:
            return self._strip_ex(1, *args)

        def rstrip(self, *args) -> xmemoryview:
            return self._strip_ex(-1, *args)

        def split(self, *args) -> list[xmemoryview]:
            if isinstance(self._obj, bytearray):
                barr = self._obj
            else:
                # must create a bytearray to split :-(
                barr = bytearray(self._obj)
            parts: list[bytearray] = barr.split(*args)
            # build xmemoryview corresponding to the splits
            res: list[xmemoryview] = []
            pos: int = 0
            for sub in parts:
                start: int = barr.find(sub, pos)
                stop: int = start + len(sub)
                res.append(self[start:stop])
                pos = stop
            return res

        def startswith(self, prefix: ByteArrayLike, start: int = 0, end: Union[int, None] = None) -> bool:
            if end is None:
                end = len(self)
            if end - start < len(prefix):
                return False
            end = start + len(prefix)
            return self[start:end] == prefix

        def endswith(self, suffix: ByteArrayLike, start: int = 0, end: Union[int, None] = None) -> bool:
            if end is None:
                end = len(self)
            if end - start < len(suffix):
                return False
            start = end - len(suffix)
            return self[start:end] == suffix

        def tobytes(self) -> bytes:
            return memoryview(self._obj).tobytes()

        def decode(self, encoding: Union[str, None] = 'utf-8'):
            return self.tobytes().decode(encoding)

        def crc32(self, crc: int = 0):
            res = binascii.crc32(self.tobytes(), crc)
            if res > 0x7FFFFFFF:
                res -= 0x100000000
            return res

        def json(self, *, reuse=None, mapValues=False, encoding='utf-8'):
            jsonRoot = json.loads(str(self._obj, encoding))
            if isinstance(reuse, xjson):
                return reuse._updateRoot(jsonRoot, mapValues)
            if isinstance(jsonRoot, dict):
                return xdict(jsonRoot)
            if isinstance(jsonRoot, list):
                return xlist(jsonRoot)
            # root is an atom
            return jsonRoot


    class xjson:
        _root: xjson
        _obj: Union[list, dict]
        _age: int

        def __init__(self, content: Union[list, dict], root: Union[xjson,None]=None):
            if root:
                self._root = root
                self._age = root._age
            else:
                self._root = self
                self._age = 1
            self._obj = content

        def __getattr__(self, attr: str) -> Union[int, str]:
            if attr == 'memsize':
                return self._memsize(self._obj)
            raise AttributeError('there is no attribute ' + attr + ' in xjson objects')

        def __setattr__(self, attr: str, value):
            if attr == 'memsize':
                raise AttributeError('attribute ' + attr + ' is read-only')
            super().__setattr__(attr, value)

        def dump(self, fp, separators: Union[tuple,None] = None):
            json.dump(self._obj, fp, separators=separators)

        # Compute a theoretical storage size for the object
        @staticmethod
        def _memsize(obj: Any) -> Any:
            res = 4
            if isinstance(obj, dict):
                for value in obj.values():
                    res += 4 + xjson._memsize(value)
            elif isinstance(obj, list):
                for value in obj:
                    res += xjson._memsize(value)
            elif isinstance(obj, str) and len(str) > 1:
                res += (len(str) + 3) & ~3
            elif isinstance(obj, int) and abs(obj) > 2**31:
                res += 8
            elif isinstance(obj, tuple):
                res += 8
            return res

        # Map an optimized JZON reply to a previously known JSON structure
        @staticmethod
        def _jzon2json(jzon: Any, jsn: dict) -> Any:
            if isinstance(jzon, list):
                sz: int = len(jzon)
                if isinstance(jsn, list):
                    # Array in both sides
                    defval = jsn[0] if len(jsn) > 0 else None
                    res: list = []
                    for idx in range(sz):
                        res.append(xjson._jzon2json(jzon[idx], defval))
                    return res
                elif isinstance(jsn, dict):
                    # Typical optimization case: array in jzon, struct in json
                    res: dict = OrderedDict()
                    idx: int = 0
                    for key, val in jsn.items():
                        res[key] = xjson._jzon2json(jzon[idx], val)
                        idx += 1
                    return res
                else:
                    return jzon
            elif isinstance(jzon, dict):
                if isinstance(jsn, list):
                    return jzon
                elif isinstance(jsn, dict):
                    defval = None
                    for val in jsn.values():
                        defval = val
                        break
                    res: dict = OrderedDict()
                    for key, val in jzon.items():
                        other = jsn.get(key, [])
                        if other != []:
                            res[key] = xjson._jzon2json(val, other)  # noqa
                        else:
                            res[key] = xjson._jzon2json(val, defval)
                    return res
                else:
                    return jzon
            # Keep atomic JZON value as is
            return jzon

        def _updateRoot(self, newRoot: any, mapValues=False):
            if self._root != self:
                raise ValueError("can only update root xjson node")
            if mapValues:
                self._obj = xjson._jzon2json(newRoot, self._obj)
            else:
                self._obj = newRoot
            self._age += 1
            if isinstance(self._obj, dict):
                if isinstance(self, xdict):
                    return self
                return xdict(self._obj)
            if isinstance(self._obj, list):
                if isinstance(self, xlist):
                    return self
                return xlist(self._obj)
            # new root is an atom
            return self._obj

        def _sub(self, subval):
            if isinstance(subval, dict):
                return xdict(subval, self._root)
            if isinstance(subval, list):
                if self._age != self._root._age:
                    raise ValueError("outdated json object")
                return xlist(subval, self._root)
            if subval and isinstance(subval, str):
                hwid = '^[A-Z][A-Z0-9]{7}-(([XT][0-2][0-9](:[0-5][0-9]){2})|([0-9A-Fa-f]{4,12}))\.[a-z][0-9A-Za-z]*$'
                if re.match(hwid, subval):
                    return str2hwid(subval)
            return subval


    class xdict(xjson):
        def __init__(self, content: Union[dict,None]=None, root: Union[xjson,None]=None):
            if content is None:
                content = OrderedDict()
            super().__init__(content, root)

        def __str__(self) -> str:
            plen: int = 8
            more: str = ''
            if plen < len(self._obj):
                more = ', ...'
            else:
                plen = len(self._obj)
            if plen == 0:
                return '{}'
            res = '{'
            for key, val in self._obj.items():
                res += f"'{key}': {repr(self._sub(val))}, "
                plen -= 1
                if plen == 0:
                    break
            return res[:-2] + more + '}'

        def __repr__(self) -> str:
            return str(self)

        def __len__(self) -> int:
            return len(self._obj)

        def __contains__(self, key: str) -> bool:
            return key in self._obj

        def __getitem__(self, key: str):
            if key in self._obj:
                return self._sub(self._obj[key])
            raise KeyError('no key "' + key + '" found in xdict object')

        def __setitem__(self, key: str, value):
            if key in self._obj:
                self._obj[key] = value
                return
            raise KeyError('cannot add key "' + key + '" to xdict object')

        def get(self, key: str, defVal = None):
            if key in self._obj:
                return self._sub(self._obj[key])
            return defVal

        def keys(self):
            return xlist(list(self._obj.keys()), self._root)

        def values(self):
            return xlist(list(self._obj.values()), self._root)

        def items(self):
            # this is only used for short-term enumeration, so we take a shortcut
            # (our micropython implementation has the fully delayed items handling)
            res = []
            for key, val in self._obj.items():
                res.append((key, self._sub(val)))
            return res

    class xlist(xjson):
        def __init__(self, content: Union[list, None]=None, root: Union[xjson,None]=None):
            if content is None:
                content = []
            super().__init__(content, root)

        def __str__(self) -> str:
            plen: int = 8
            more: str = ''
            if plen < len(self._obj):
                more = ', ...'
            else:
                plen = len(self._obj)
            if plen == 0:
                return '[]'
            res = '['
            for i in range(plen):
                res += repr(self._sub(self._obj[i])) + ", "
            return res[:-2] + more + ']'

        def __repr__(self) -> str:
            return str(self)

        def __len__(self) -> int:
            return len(self._obj)

        def __getitem__(self, key: Union[int, slice]):
            if self._age != self._root._age:
                raise ValueError("outdated json object")
            if isinstance(key, slice):
                return xlist(self._obj[key], self._root)
            else:
                return self._sub(self._obj[key])

        def __setitem__(self, key: Union[int, slice], value):
            if self._age != self._root._age:
                raise ValueError("outdated json object")
            if isinstance(key, slice):
                raise TypeError("unsupported slice index")
            self._obj[key] = value

        def append(self, value):
            self._obj.append(value)

        def extend(self, values):
            self._obj.extend(values)


    # noinspection PyProtectedMember
    class xbytearray(xarray):
        # noinspection PyUnusedLocal
        def __init__(self, source: Union[int, ByteArrayLike, str, None] = None, encoding: Union[str, None] = None, _=None, alloc=None):
            if source is None:
                source = 0
            elif isinstance(source, int):
                source = [0] * source
            elif isinstance(source, xarray):
                source = source._obj
            elif isinstance(source, str) and encoding is None:
                raise TypeError('string argument without an encoding')
            super().__init__('B', [])
            self._classname = 'xbytearray'
            if encoding is None:
                self._obj = bytearray(source)
            else:
                self._obj = bytearray(source, encoding)
            self._typecode = _BYTEARRAY_TYPECODE


    # noinspection PyProtectedMember
    class xmemoryview(xarray):
        def __init__(self, source: xarray, start: int = 0, end: Union[int, None] = None):
            if not isinstance(source, xarray):
                raise TypeError('xmemoryview can only map to xbytearray or xarray')
            super().__init__('B', [])
            if end is None:
                end = len(source)
            self._classname = 'xmemoryview'
            self._obj = memoryview(source._obj)[start:end]
            self._typecode = source.typecode
            self._itemsize = source.itemsize

        def cast(self, typecode) -> xmemoryview:
            res: xmemoryview = xmemoryview(self)
            res._obj = res._obj.cast(typecode)
            res._typecode = typecode
            res._itemsize = res._obj.itemsize
            return res

        def tobytes(self) -> bytes:
            return self._obj.tobytes()


    # noinspection PyProtectedMember
    class xStringIO(io.StringIO):
        def __init__(self, base: Union[ByteArrayLike,int,None]=None, encoding:str='utf-8'):
            if base is None or isinstance(base, int):
                decode = None
            elif isinstance(base, xarray):
                decode = str(base._obj, encoding)
            else:
                decode = str(base, encoding)
            super().__init__(decode)


    # noinspection PyProtectedMember
    class xBytesIO(io.BytesIO):
        def __init__(self, base: Union[ByteArrayLike,int,None]=None):
            if base is None or isinstance(base, int):
                super().__init__()
            else:
                super().__init__(base._obj)

    # -Class-Export-End (micropython_emu.xarray)

#################################################################################
#                                                                               #
#                  Yoctopuce-style YUrl and aiohttp support                     #
#                                                                               #
#################################################################################

# noinspection PyUnresolvedReferences
# -Class-Export-Start: from aiohttp import YUrl, BaseSession, ClientResponse, BaseWsResponse, HTTPState
# -Class-Export-Provides: ClientSession ClientResponse ClientWebSocketResponse WSMessage BasicAuth DigestAuth
# -Class-Export-Preamble: import random, json, binascii, hashlib
# -Class-Export-Preamble: from collections import OrderedDict
# -Class-Export-Preamble:
# -Class-Export-Preamble: _LOG_LEVEL = const(0)

# Max length returned by StreamReader readuntil() and readline()
_MAX_STREAM_READUNTIL: Final[int] = 512


class YUrl:
    if not _IS_MICROPYTHON:
        PROTO: Final[int] = 1  # include URL protocol
        AUTH: Final[int] = 2  # include auth parameters
        ENDSLASH: Final[int] = 4  # include trailing slash

    proto: str
    host: str
    port: int
    user: str
    _pass: str
    subDomain: str
    originalURL: str

    def __init__(self, url: str, defaultHttpPort: int = 80, defaultHttpsPort: int = 443):
        self.proto = ""
        self.host = ""
        self.port = -1
        self.user = ""
        self._pass = ""
        self.subDomain = ""
        self.originalURL = url
        defaultPort = defaultHttpPort
        pos = 0
        proto = ""
        if _IS_MICROPYTHON:
            # within MicroPython, local devices are reached via localhost pipe sockets
            if url == "usb":
                self.proto = "ws"
                self.host = "localhost"
                self.port = defaultHttpPort
                return
        if url.startswith("http://"):
            pos = 7
            proto = "http"
        elif url.startswith("ws://"):
            pos = 5
            proto = "ws"
        elif url.startswith("https://"):
            pos = 8
            proto = "https"
            defaultPort = defaultHttpsPort
        elif url.startswith("wss://"):
            pos = 6
            proto = "wss"
            defaultPort = defaultHttpsPort
        elif url.startswith("auto://"):
            pos = 7
            proto = "auto"
        elif url.startswith("secure://"):
            pos = 9
            proto = "secure"
            defaultPort = defaultHttpsPort
        elif defaultHttpPort != 80: # eg. Yoctopuce API
            proto = "auto"
        else:
            proto = "http"
        self.proto = proto
        if url.endswith("/"):
            url = url[:-1]
        end_auth = url.find('@', pos)
        if 0 < end_auth:
            end_user = url.find(':', pos)
            if 0 <= end_user < end_auth:
                self.user = url[pos:end_user]
                self._pass = url[end_user + 1:end_auth]
            else:
                self.user = url[pos:end_auth]
                self._pass = ''
            pos = end_auth + 1
        else:
            self.user = ""
            self._pass = ""

        if len(url) > pos and url[pos] == '@':
            pos += 1

        end_host = url.find('/', pos)
        if end_host < 0:
            end_host = len(url)
            self.subDomain = ""
        else:
            self.subDomain = url[end_host:]
        endv6 = url.find(']', pos)
        portpos = url.find(':', pos)
        if portpos > 0 and endv6 < end_host and portpos < endv6:
            # ipv6 URL
            portpos = url.find(':', endv6)
        if portpos > 0:
            if portpos + 1 < end_host:
                self.host = url[pos:portpos]
                self.port = int(url[portpos + 1:end_host])
            else:
                self.host = url[pos:portpos]
                self.port = defaultPort

        else:
            self.host = url[pos:end_host]
            if len(self.subDomain) > 0:
                # override default port if there is a subdomain (VHub4web)
                if self.proto == "http":
                    defaultPort = 80
                elif self.proto == "https":
                    defaultPort = 443
            self.port = defaultPort

    def updateFromRef(self, http_params_org: YUrl, proto: str, port: int):
        self.originalURL = http_params_org.originalURL
        self.host = http_params_org.host
        self.port = port
        self.user = http_params_org.user
        self._pass = http_params_org._pass
        if http_params_org.proto != "http" and http_params_org.proto != "https":
            self.proto = proto
        else:
            self.proto = http_params_org.proto
        self.subDomain = http_params_org.subDomain

    def getUrl(self, includeOptions: int) -> str:
        if self.originalURL == "usb":
            return "usb"
        if includeOptions & YUrl.PROTO:
            url = "%s://" % self.proto
        else:
            url = ""
        if includeOptions & YUrl.AUTH and self.user != "":
            if self._pass != "":
                url += "%s:%s@" % (self.user, self._pass)
            else:
                url += "%s@" % self.user
        url += "%s:%d%s" % (self.host, self.port, self.subDomain)
        if includeOptions & YUrl.ENDSLASH:
            url += '/'
        return url

    def isWebSocket(self) -> bool:
        return self.proto.startswith("ws")

    def isSecure(self) -> bool:
        return "wss" == self.proto or "https" == self.proto or "secure" == self.proto

    def testInfoJson(self) -> bool:
        return "auto" == self.proto or "secure" == self.proto or "http" == self.proto or "https" == self.proto

    def updateBestProto(self, proto: str, port: int) -> None:
        self.port = port
        if not self.proto.startswith("http"):
            self.proto = proto

    def updatePortInfo(self, proto: str, port: int) -> None:
        self.port = port
        self.proto = proto

    def updateForRedirect(self, host: str, port: int, is_secure: bool) -> None:
        self.host = host
        self.port = port
        if self.isWebSocket():
            self.proto = 'wss' if is_secure else 'ws'
        else:
            self.proto = 'https' if is_secure else 'http'


if _IS_MICROPYTHON:
    Pairs = Union[dict, list]
    ProgressCallback = Union[Callable, None]
else:
    try:
        Pairs = Union[dict[str, str], list[tuple[str, str]]]
        ProgressCallback = Union[Callable[[int, int], None], None]
    except TypeError:
        Pairs = Union[dict, list]
        ProgressCallback = Union[Callable, None]


class HTTPState:
    if not _IS_MICROPYTHON:
        NOT_SENT: Final[int] = -5
        CONNECT: Final[int] = -4
        SEND_HEADERS: Final[int] = -3
        SEND_DATA: Final[int] = -2
        RECV_HEADERS: Final[int] = -1
        ABORT: Final[int] = 0


# noinspection PyProtectedMember
class BaseChan:
    _session: BaseSession
    _base: YUrl
    _ssl: Union[SSLContext, None]
    _pending: list[BaseResponse]
    _current: Union[BaseResponse, None]
    _reader: Union[asyncio.StreamReader, None]
    _writer: Union[asyncio.StreamWriter, None]
    _task: Union[asyncio.Task, None]

    def __init__(self, session: BaseSession, baseurl: YUrl, sslctx: SSLContext):
        self._session = session
        self._base = baseurl
        self._ssl = sslctx
        self._pending = []
        self._current = None
        self._reader = None
        self._writer = None
        self._task = None

    def matchUrl(self, url: YUrl) -> bool:
        if self._base.host != url.host:
            return False
        return self._base.port == url.port

    # Append a pending request to the channel
    def queue(self, request) -> None:
        if self._current is None:
            self._current = request
        else:
            self._pending.append(request)

    # Internal method to receive data from socket for a given request
    async def _recv(self, req: BaseResponse, sz: int) -> bytes:
        if isinstance(req, BaseResponse) and self._current != req:
            raise OSError("HTTP request not active")
        if self._reader is None:
            raise OSError("Connection reset")
        # Ensure we never read more than 256 bytes, to avoid out of memory errors
        # FIXME: try to use read_into to read directly into extmem
        res = await self._reader.read(min(sz, 256))
        if not res:
            raise EOFError()
        return res

    # Internal method to send a small binary buffer to the socket
    async def _send(self, blk: Union[bytes, bytearray, memoryview]) -> None:
        if _IS_MICROPYTHON:
            # Use our write+drain optimized function
            await self._writer.wdrain(blk)  # noqa
        else:
            self._writer.write(blk)
            await self._writer.drain()

    # Internal method to send a large binary buffer (via callback) to the socket
    async def _sendView(self, dataViewer: Callable[[int, int], bytes]) -> None:
        sent: int = 0
        blk: bytes = dataViewer(sent, 128)
        while len(blk) > 0:
            await self._send(blk)
            sent += len(blk)
            blk = dataViewer(sent, 128)

    # Start the background process
    def keepRunning(self) -> None:
        if self._task is None or self._task.done():
            self._task = self._session.create_task(self._process())

    # Process all pending HTTP requests until no more are pending
    async def _process(self) -> None:
        # make sure there is never two instances running in parallel
        retrycount: int = 0
        while self._current:
            req: BaseResponse = self._current
            try:
                try:
                    if req.status == HTTPState.NOT_SENT:
                        req.status = HTTPState.CONNECT
                    if req.status < HTTPState.SEND_HEADERS:
                        req.startWatchdog(self._session)
                    url = self._base
                    reuse_sock: bool = self._writer is not None
                    if not reuse_sock:
                        if url.isSecure():
                            ssl_arg = self._ssl
                            if ssl_arg is None:
                                # if no ssl context is provided use default one
                                ssl_arg = True
                        else:
                            ssl_arg = None
                        self._reader, self._writer = await asyncio.open_connection(url.host, url.port, ssl=ssl_arg)
                    mustRestart = False
                    if req.status < HTTPState.SEND_HEADERS:
                        req.status = HTTPState.SEND_HEADERS
                        has_auth_info = req._prepHeaders(self._base, self._session._auth)
                        await self._sendView(req.getHeaderView)
                        req.prepRecv()
                        if len(req.getDataView(0, 128)) > 0:
                            if req.status < HTTPState.SEND_DATA:
                                req.status = HTTPState.SEND_DATA
                            await self._sendView(req.getDataView)
                        if req._async is not None:
                            # asynchronous requests trigger the _ready Future as soon as fully sent
                            req._ready.set()
                        if req.status < HTTPState.RECV_HEADERS:
                            req.status = HTTPState.RECV_HEADERS
                        # trigger reading until headers are fully received or timeout
                        recvMore: bool = True
                        while recvMore:
                            pkt: bytes = await self._reader.read(128)
                            if len(pkt) == 0:
                                # connection closed by peer
                                # it's a reusable socket ensure remote has not closed the socket since last read
                                if reuse_sock and req._len == 0:
                                    # socket has expired restart silently
                                    mustRestart = True
                                    recvMore = False
                                else:
                                    await self.close()
                                break
                            recvMore = (req.appendBytes(pkt) < 0)
                        if req.status == 401 or req.status == 204:
                            if self._session._auth is not None and self._base.user and not has_auth_info:
                                self._session._auth.login(req)
                                mustRestart = True
                        elif req.status == 301 or req.status == 302 or req.status == 307 or req.status == 308 and retrycount < 3:
                            new_url = YUrl(req.get('Location'))
                            self._base.updateForRedirect(new_url.host, new_url.port, new_url.isSecure())
                            mustRestart = True
                        else:
                            if recvMore:
                                # FIXME: could also be a connection closed by peer
                                raise asyncio.TimeoutError
                    if req._async is None and not mustRestart:
                        await req.waitEndProcesssing()
                    # cancel the watchdog thread when done
                    req.stopWatchdog()
                    if req.requestMustBeClosed() or mustRestart:
                        await self.close()
                    if mustRestart:
                        # reset request and start it again
                        req.reset()
                        retrycount += 1
                        continue
                        # no wait_closed() to speedup next requests
                except asyncio.CancelledError as exc:
                    raise asyncio.TimeoutError from exc
            except BaseException as exc:
                req.status = HTTPState.ABORT
                await self.close()
                req.stopWatchdog()
                if not req._ready.is_set():
                    req._except = exc
                    req._ready.set()
            retrycount = 0
            if len(self._pending) > 0:
                self._current = self._pending.pop(0)
            else:
                self._current = None
        self._task = None

    # Release a request; if request is current and content was not fully read, this will cause
    # a disconnection of the underlying TCP connection (breaking keep-alive)
    async def release(self, req: BaseResponse) -> None:
        if self._current != req:
            return
        if req.status < HTTPState.ABORT:
            # connection released before header was fully read
            req.stopWatchdog()
            req.status = HTTPState.ABORT
            await self.close()

    async def waitForPendingRequests(self) -> None:
        while self._task:
            await self._task

    # Close underlying socket
    async def close(self):
        sock = self._writer
        self._reader = None
        self._writer = None
        if sock:
            try:
                sock.close()
                await sock.wait_closed()
            except OSError as _:
                # ignore errors on close, like ssl.SSLError APPLICATION_DATA_AFTER_CLOSE_NOTIFY
                pass
            except asyncio.CancelledError as _:
                # ignore cancelled task during close
                pass


# To reduce memory footprint, we use a single polymorphic BaseResponse object
# that also work as a Python asynchronous context manager and as "headers" dictionary
#
# noinspection PyProtectedMember
class BaseResponse:
    _chan: Union[BaseChan, None]
    _method: str
    _target: str
    _headers: dict
    _timeout: int  # relative timeout in ms
    _buff: Union[xbytearray, bytes, memoryview, None]  # incoming and outgoing buffer
    _len: int  # size of data in _buff
    _headPos: int  # when header received: start of header in _buff
    _headEnd: int  # when header received: end of header in _buff
    _except: Union[RuntimeError, OSError, BaseException, None]
    _endTicks: int  # absolute timeout end tick, when watchdog is started
    _watchdog: Union[asyncio.Task, None]  # the request timeout task
    _async: Union[int, None]  # if not None, the request does not need to be awaited for completion
    _ready: asyncio.Event  # event set when the header is fully received (or fully sent, for async requests)
    _done: asyncio.Event  # event sset when the request is completed
    status: int
    reason: str
    ok: bool
    headers: BaseResponse  # pseudo-attribute pointing to self

    def __init__(self, method: str, target: str, headers: dict, timeout: int):
        self._chan = None
        self._method = method
        self._target = target
        self._headers = headers
        self._timeout = timeout
        self._buff = None
        self._len = 0
        self._headPos = -1
        self._headEnd = -1
        self._except = None
        self._endTicks = -1
        self._watchdog = None
        self._async = None
        self._ready = asyncio.Event()
        self._done = asyncio.Event()
        self.status = HTTPState.NOT_SENT
        self.reason = 'Not sent'
        self.ok = False
        self.headers = self

    def _appendHeader(self, key: str, value: str):
        assert(isinstance(self._buff, xbytearray))
        buf: xbytearray = self._buff
        pos: int = self._len
        ilen: int = len(key)
        npos: int = pos + ilen
        buf[pos:npos] = key.encode('ascii')
        buf[npos:npos + 2] = b': '
        ilen = len(value)
        pos = npos + 2
        npos = pos + ilen
        buf[pos:npos] = value.encode('ascii')
        buf[npos:npos + 2] = b'\r\n'
        self._len = npos + 2

    def _prepHeaders(self, url: YUrl, auth: Union[BaseAuth | None]) -> bool:
        firstLine: str = "%s %s %s\r\n" % (self._method, self._target, self._chan._session._httpver)
        pos: int = len(firstLine)
        # always allocate 512 bytes to avoid fragmenting memory
        if self._buff is None:
            self._buff = xbytearray(512)
        self._buff[:pos] = firstLine
        self._len = pos
        # Build the headers
        hasAuthInfo = False
        if self._chan._session._httpver:
            self._appendHeader('Host', '%s:%d' % (url.host, url.port))
        if auth is not None:
            key, value = auth.getAuth(self._method, self._target)
            if key:
                hasAuthInfo = True
                self._appendHeader(key, value)
        if self._headers:
            for key, value in self._headers.items():
                self._appendHeader(key, value)
        if not self.hasData():
            pos = self._len
            self._buff[pos:pos + 2] = b'\r\n'
            self._len = pos + 2
        return hasAuthInfo

    def reset(self):
        self._headPos = -1
        self._headEnd = -1
        self._except = None
        self._endTicks = -1
        self._watchdog = None
        self.status = HTTPState.NOT_SENT
        self.reason = 'Not sent'
        self.ok = False

    def queueOn(self, chan: BaseChan):
        self._chan = chan
        chan.queue(self)

    async def __aenter__(self) -> BaseResponse:
        await self.ready()
        return self

    async def __aexit__(self, *args) -> None:
        self.release()
        await self.released()

    async def request_watchdog(self, task: asyncio.Task) -> None:
        remaining = ticks_diff(self._endTicks, ticks_ms())
        while remaining > 0:
            if _IS_MICROPYTHON:
                await asyncio.sleep_ms(min(remaining, 250))  # noqa
            else:
                await asyncio.sleep(min(remaining, 250) / 1000.0)
            remaining = ticks_diff(self._endTicks, ticks_ms())
        task.cancel()

    def startWatchdog(self, session: BaseSession):
        self._endTicks = ticks_add(ticks_ms(), self._timeout)
        self._watchdog = session.create_task(self.request_watchdog(asyncio.current_task()))

    def keepAlive(self, gracetime_ms: int) -> None:
        self._endTicks = ticks_add(ticks_ms(), gracetime_ms)

    def stopWatchdog(self):
        if self._watchdog:
            self._watchdog.cancel()
        self._watchdog = None

    def getHeaderView(self, pos: int, maxLen: int) -> bytes:
        endPos = min(self._len, pos + maxLen)
        return self._buff[pos:endPos].tobytes()

    def getDataView(self, pos: int, maxLen: int) -> bytes:
        return b''

    def hasData(self) -> bool:
        return False

    # When the header has been fully sent, reset object to receive and parse incoming data
    # (using the same buffer)
    def prepRecv(self):
        self._len = 0

    # Append incoming header data
    #
    # If the data appended includes the end of header marker,
    #    return the total length of the headers block
    # Otherwise, return -1
    def appendBytes(self, data: Union[bytes, memoryview]) -> int:
        sz: int = len(data)
        pos: int = self._len
        if self._buff is None:
            # keep the first chunk as low-memory object, to avoid xbytearray allocation until really needed
            if not _IS_MICROPYTHON:
                if isinstance(data, memoryview):
                    data = bytes(data) # in CPython, memoryview is missing find()
            self._buff = data
        elif sz:
            if not isinstance(self._buff, xbytearray):
                # use a xbytearray for growing content, as it may become large
                prvbuff = self._buff
                assert(pos == len(prvbuff))
                self._buff = xbytearray(512)
                self._buff[:pos] = prvbuff
            self._buff[pos:pos + sz] = data
        self._len = pos + sz
        if self.status < 0:
            eoh: int = self._buff.find(b'\r\n\r\n', max(0, pos - 3), self._len)
            if eoh >= 0:
                self._headPos = self._buff.find(b'\r\n', 0, eoh + 2) + 2
                self._headEnd = eoh + 4
                firstline: str = self.headers['status']
                if len(firstline) >= 2 and firstline[1] == 'K':
                    self.status = 200
                    if _IS_MICROPYTHON:
                        self.reason = sys.intern(firstline[:2])
                    else:
                        self.reason = firstline[:2]
                else:
                    status: list[str] = firstline.split(' ', 2)
                    try:
                        self.status = int(status[1])
                        self.reason = "HTTP Error (%s)" % status[-1]
                    except ValueError:
                        self.status = -1
                        self.reason = "HTTP Error (%s)" % firstline
                self.ok = (200 <= self.status <= 299)
                return eoh
        return -1

    def get(self, key: str, default_val:Union[str, None]=None) -> Union[str, None]:
        """
        Retrieves a received header element based on its (case-insensitive) name
        Returns None if the requested header element has not been received.
        """
        key = key.lower()
        pos = self._headPos
        if pos < 0:
            return default_val
        if key == 'status':
            stat = self._buff[:pos - 2]
            if isinstance(stat, memoryview):
                stat = bytes(stat)
            return stat.decode('ascii')
        while 0 <= pos < self._headEnd - 4:
            sep = self._buff.find(b':', pos, self._headEnd)
            endl = self._buff.find(b'\r\n', pos, self._headEnd)
            if sep < 0 or endl < 0:
                return default_val
            if sep < endl:
                hkey = self._buff[pos:sep].strip(b' ').decode('ascii').lower()
                if hkey == key:
                    return self._buff[sep + 1:endl].strip(b' ').decode('ascii')
            pos = endl + 2
        return default_val

    def __getitem__(self, key: str) -> str:
        """
        Retrieves a received header element based on its (case-insensitive) name
        Throws KeyError if the requested header element has not been received.
        """
        res: Union[str, None] = self.get(key)
        if res is None:
            raise KeyError(key)
        return res

    def __contains__(self, key: str) -> bool:
        """
        Tells if a specific header element has ben included in the response.
        Comparison is case-insensitive, as per HTTP protocol.
        """
        find: Union[str, None] = self.get(key)
        return find is not None

    async def ready(self) -> None:
        """
        Wait for the request to be sent and the response header to be fully received.
        This method is equivalent to entering the async context of the request.
        """
        if self.status >= 0:
            return
        if self._chan:
            self._chan.keepRunning()
        await self._ready.wait()
        if self._except:
            raise self._except

    def get_encoding(self) -> str:
        """
        Retrieve request encoding based on HTTP headers.
        This method should only be invoked once the response headers have been fully received.
        """
        contentType = self.headers.get('Content-Type')
        if contentType:
            pos = contentType.find('charset=')
            if pos >= 0:
                return contentType[pos + 8:]
        return 'utf-8'

    # Method overriden by subclasses
    def release(self) -> None:
        """
        Release current request; if content was not fully read, this will cause
        a disconnection of the underlying TCP connection (breaking keep-alive)
        """
        pass

    # Wait for response to be completed
    async def released(self) -> None:
        pass

    async def waitEndProcesssing(self) -> None:
        self._ready.set()
        await self._done.wait()

    def requestMustBeClosed(self) -> bool:
        return True


class BaseAuth:
    _type: str
    _user: str
    _pwd: str

    def __init__(self, scheme: str, user: str, pwd: str):
        self._type = scheme
        self._user = user
        self._pwd = pwd

    def login(self, headers: BaseResponse):
        wwwAuth = headers.get('www-authenticate')
        if wwwAuth is None:
            raise RuntimeError('%s not found' % 'www-authenticate')
        authReq = [item.strip() for item in wwwAuth.split(',')]
        sep = authReq[0].find(' ')
        if sep < 0:
            raise RuntimeError('Invalid %s' % 'www-authenticate')
        scheme = authReq[0][:sep]
        if scheme != self._type:
            raise RuntimeError('%s %s expected, received %s' % (self._type, 'www-authenticate', scheme))
        authReq[0] = authReq[0][sep + 1:].strip()
        self._login(authReq)

    def _login(self, authReq: list[str]) -> None:
        # implemented by subclasses
        pass

    def getAuth(self, method: str, path: str) -> tuple[str, str]:
        pass


class BasicAuth(BaseAuth):
    _hash: str

    def __init__(self, login: str, password: str):
        super().__init__('Basic', login, password)
        self._hash = ""

    def _login(self, authReq: list[str]) -> None:
        pass

    def getAuth(self, method: str, path: str) -> tuple[str, str]:
        if self._hash == "":
            key = ('%s:%s' % (self._user, self._pwd)).encode('utf-8')
            self._hash = '%s %s' % ('Basic', binascii.b2a_base64(key).decode('ascii').strip())
        return 'authorization', self._hash


class DigestAuth(BaseAuth):
    _realm: str
    _nonce: str
    _opaque: str
    _ha1: str
    _nc: int

    def __init__(self, login: str, password: str):
        super().__init__('Digest', login, password)
        self._realm = ''
        self._nonce = ''
        self._opaque = ''
        self._ha1 = ''
        self._nc = -1

    def _login(self, authReq: list[str]) -> None:
        for item in authReq:
            key, val = item.split('=')
            val = val.strip('"')
            if key == 'realm':
                self._realm = val
            elif key == 'nonce':
                self._nonce = val
            elif key == 'opaque':
                self._opaque = val
        ha1_str: str = '%s:%s:%s' % (self._user, self._realm, self._pwd)
        self._ha1 = hashlib.md5(ha1_str.encode('ascii')).hexdigest().lower()

    def getAuth(self, method: str, path: str) -> tuple[str, str]:
        if self._realm != "":
            self._nc += 1
            nc: str = "%08x" % self._nc
            cnonce: str = "%08x" % random.getrandbits(32)
            plaintext: str = "%s:%s" % (method, path)
            md_ = hashlib.md5(plaintext.encode('ascii'))
            ha2 = md_.hexdigest().lower()
            plaintext = self._ha1 + ":" + self._nonce + ":" + nc + ":" + cnonce + ":auth:" + ha2
            md_ = hashlib.md5(plaintext.encode('ascii'))
            response: str = md_.hexdigest().lower()
            return 'authorization', \
                "%s username=\"%s\", realm=\"%s\", nonce=\"%s\", uri=\"%s\", qop=auth, nc=%s, cnonce=\"%s\", response=\"%s\", opaque=\"%s\"" % (
                    'Digest', self._user, self._realm, self._nonce, path, nc, cnonce, response, self._opaque)
        return '', ''


# To reduce memory footprint, we use a single polymorphic ClientResponse object
# that also behaves as "content" StreamReader
#
# noinspection PyProtectedMember
class ClientResponse(BaseResponse):
    _data: Union[xarray, None]
    _dataCb: ProgressCallback  # callback for upload progress tracking
    _dataPos: int  # when header received: start of unread content in _buff
    _dataRem: int  # when header received: remaining bytes of content to be read (-1 if unknown)
    _chunkRem: int  # when header received: remaining bytes in current chunk (-1 if not chunked)
    content: ClientResponse  # pseudo-attribute pointing to self

    def __init__(self, method: str, url: str, headers: dict, timeout: int, payload: Union[xarray, None]):
        super().__init__(method, url, headers, timeout)
        self._data = payload
        self._dataCb = None
        self._dataPos = -1
        self._dataRem = -1
        self._chunkRem = -1
        self.content = self

    def reset(self):
        super().reset()
        self._dataPos = -1
        self._dataRem = -1
        self._chunkRem = -1

    def requestMustBeClosed(self) -> bool:
        # http request can be reused only if the header has
        # content-length or content-encoding informations
        mustClose: bool = self._dataRem < 0 and self._chunkRem < 0
        if not mustClose:
            mustClose = (self.get('connection','').lower() == 'close')
        return mustClose

    def __repr__(self) -> str:
        return "<%s %d %sdone>" % ('ClientResponse', self.status, "" if self._done.is_set() else "not ")

    def hasData(self) -> bool:
        return self._data is not None

    def getDataView(self, pos: int, maxLen: int) -> bytes:
        if self._data is None:
            return b''
        totLen = len(self._data)
        endPos = min(totLen, pos + maxLen)
        if self._dataCb:
            self._dataCb(endPos, totLen)
        return self._data[pos:endPos].tobytes()

    # Append incoming header data
    #
    # If the data appended includes the end of header marker,
    #    return the total length of the headers block
    # Otherwise, return -1
    def appendBytes(self, data: Union[bytes, memoryview]) -> int:
        eoh: int = super().appendBytes(data)
        if eoh >= 0:
            self._dataPos = eoh + 4
            if self._headPos == 4 and self._buff.find(b'0K') == 0:
                self._dataRem = 0
            else:
                encoding = self.get('transfer-encoding')
                if encoding and encoding.lower().find("chunked") >= 0:
                    self._chunkRem = 0
                length = self.get('content-length')
                if length is not None:
                    self._dataRem = int(length)
        return eoh

    # Read more data from TCP channel and store it in the work buffer
    # May raise EOFError in case of EOF, or OSError if work buffer is full
    async def _readMore(self):
        if self._chan is None:
            # pre-filled request content, cannot read more
            raise EOFError()
        sz: int = len(self._buff) - self._len
        if sz == 0:
            raise OSError("input buffer full")
        pkt: bytes = await self._chan._recv(self, sz)
        pktlen: int = len(pkt)
        newlen = self._len + pktlen
        self._buff[self._len:newlen] = pkt
        self._len = newlen

    async def read(self, n: int = -1, readUntil: int = -1) -> ByteArrayLike:
        """
        Read up to n bytes from the content stream, or read the whole content if sz = -1

        For the sake of efficiency, the output of this function might be a xmemoryview
        object within the internal read buffer, so it should be read before the next
        call to read() or readexactly() to prevent being overwritten by next read
        """
        await self.ready()
        if n == 0:
            return self._buff[:0]
        if n < 0:
            if self._chunkRem < 0 and not self._chan:
                # return pre-filled request content directly
                n = self._len - self._dataPos
            else:
                return await self.readexactly(n)
        if self._chunkRem >= 0:
            if self._chunkRem == 2:
                # skip the last \r\n
                self._chunkRem -= 2
            # HTTP encoding is chunked
            if self._chunkRem == 0:
                # we need to start by receiving length of next chunk
                # make sure there is enough space in buffer for this
                if self._dataPos + 10 >= len(self._buff):
                    # about to reach end of buffer, rewind first
                    avail = self._len - self._dataPos
                    if avail > 0:
                        remains: bytes = self._buff[self._dataPos:self._len].tobytes()
                        self._dataPos = self._headEnd
                        self._len = self._dataPos + avail
                        self._buff[self._dataPos:self._len] = remains
                # get enough data to get the next chunk length
                eolPos: int = self._buff.find(b'\r\n', self._dataPos, self._len)
                while eolPos < 0:
                    await self._readMore()
                    eolPos = self._buff.find(b'\r\n', self._dataPos, self._len)
                self._chunkRem = int(self._buff[self._dataPos:eolPos].decode('ascii'), 16)
                self._dataPos = eolPos + 2
                if self._chunkRem == 0:
                    # eof encountered
                    self._done.set()
                    if _LOG_LEVEL >= 5:
                        print("Read exit %u to eof (chunk) (_dataPos=%d _len=%d buffsize=%d _chunkRem=%d readUntil=%d)" %
                              (n, self._dataPos, self._len, len(self._buff), self._chunkRem, readUntil))
                    return self._buff[self._dataPos:self._dataPos]
                else:
                    # add 2 bytes for the last \r\n after the data
                    self._chunkRem += 2

            # will read as much continuous data as available
            if n > self._chunkRem:
                n = self._chunkRem
        else:
            # HTTP encoding is natural
            if self._dataRem >= 0:
                if n > self._dataRem:
                    n = self._dataRem
        if self._dataPos == self._len:
            # no more buffered data, we need to receive more
            # make sure there is space in the buffer
            if self._len == len(self._buff):
                # end of buffer reached, we need to rewind buffer
                startPos: int = self._headEnd
                self._len = startPos
                self._dataPos = startPos
            # read data
            try:
                await self._readMore()
            except EOFError:
                self._done.set()
                return self._buff[:0]
        avail: int = self._len - self._dataPos
        if n > avail:
            n = avail
        prevPos: int = self._dataPos
        if readUntil >= 0:
            # make sure we stop after specified limit character (eg. LF)
            endl = prevPos
            endPos = prevPos + n
            while endl < endPos:
                byte = self._buff[endl]
                endl += 1
                if byte == readUntil:
                    n = endl - prevPos
                    break
        self._dataPos += n
        self._dataRem -= n
        if self._chunkRem >= 0:
            self._chunkRem -= n
        return self._buff[prevPos:self._dataPos]

    async def readuntil(self, separator: bytes) -> bytes:
        """
        Read from content stream until a separator byte is found.
        The separator is included in the returned bytes object
        """
        sepByte: int = separator[0]
        res: bytes = (await self.read(128, sepByte)).tobytes()
        if len(res) == 0:
            return res
        while res[-1] != sepByte:
            more: bytes = (await self.read(128, sepByte)).tobytes()
            if len(more) == 0:
                return res
            res += more
            if len(res) >= _MAX_STREAM_READUNTIL:
                return res
        return res

    async def readline(self, encoding: str = '') -> str:
        """
        Read next line from the content stream (until \n is found)
        and return it as a string (including \n)
        """
        if not encoding:
            encoding = self.get_encoding()
        line: bytes = await self.readuntil(b'\n')
        return line.decode(encoding)

    async def readexactly(self, n: int) -> ByteArrayLike:
        """
        Read exactly n bytes from the content stream, or read the whole file if n = -1

        For the sake of efficiency, the output of this function might be a xmemoryview
        object within the internal read buffer, so it should be read before the next
        call to read() or readexactly() to prevent being overwritten by next read
        """
        await self.ready()
        if n < 0 and self._dataRem >= 0:
            n = self._dataRem
        if n == 0:
            return self._buff[:0]
        if self._chunkRem < 0 and 0 < n < len(self._buff) - self._dataPos:
            # optimal case: we can read and return data from our internal buffer
            startPos: int = self._dataPos
            endPos: int = self._dataPos + n
            while n > 0:
                n -= len(await self.read(n))
            assert self._dataPos >= endPos
            return self._buff[startPos:endPos]
        # general case: we need to allocate a new buffer
        if n > 0:
            res: xbytearray = xbytearray(n)
            pos: int = 0
            while pos < n:
                blk: xarray = await self.read(n - pos)
                rw = len(blk)
                if rw == 0:
                    raise EOFError()
                res[pos:pos + rw] = blk
                pos += rw
        else:
            blk: xarray = await self.read(1024)
            if not len(blk):
                return blk
            res: xbytearray = xbytearray(1024)
            pos: int = 0
            rw = len(blk)
            while rw > 0:
                if _LOG_LEVEL >= 5:
                    print("blk sz=", len(blk), blk[:16], '...', blk[-16:])
                res[pos:pos + rw] = blk
                pos += rw
                blk: xarray = await self.read(1024)
                rw = len(blk)
            if _LOG_LEVEL >= 5:
                print("res sz=", pos, res[:16], '...', res[-16:])
        return res[:pos]

    async def text(self, encoding: str = '') -> str:
        """
        Read the full request content and return it as a string        
        """
        body: xarray = await self.read()
        if not encoding:
            encoding = self.get_encoding()
        return body.decode(encoding)

    async def json(self) -> Any:
        """
        Read the full request content and return it as a JSON object
        """
        return json.load(xStringIO(await self.read()))

    def release(self, exc: Union[OSError, None] = None) -> None:
        """
        Release current request; if content was not fully read, this will cause
        a disconnection of the underlying TCP connection (breaking keep-alive)
        """
        if not self._done.is_set() and exc is None:
            exc = OSError("request closed before end")
        if exc:
            self._except = exc
        self._ready.set()
        self._done.set()

    def close(self) -> None:
        """
        Release current request and close underlying TCP connection forcibly.
        If request was already completed previously, raise an exception.
        """
        if self._done.is_set():
            raise OSError("request already released")
        self._except = OSError("request closed before end")
        self._done.set()

    # Wait for request to be completely received
    async def released(self) -> None:
        await self._done.wait()

    async def waitEndProcesssing(self) -> None:
        self._ready.set()
        if self._dataRem == 0:
            self._done.set()
        # body reading must be handled by application
        await self._done.wait()


class WSMsgType:
    if not _IS_MICROPYTHON:
        TEXT: Final[int] = 1
        BINARY: Final[int] = 2
        CLOSE: Final[int] = 8
        PING: Final[int] = 9
        PONG: Final[int] = 10


if _IS_MICROPYTHON:
    WSMessage = namedtuple("WSMessage", ('type', 'data', 'fin'))
else:
    class WSMessage(NamedTuple):
        type: int
        data: Union[xarray, memoryview, bytes, str]
        fin: bool

# To reduce memory footprint, we use a single polymorphic WebSocketResponse
# object that also behaves as a context and as websocket connection manager
#
# noinspection PyProtectedMember
class BaseWsResponse(BaseResponse):
    _gracetime: int
    _frame: bytearray
    _xframe: Union[xmemoryview, None]

    def __init__(self, method: str, target: str, headers: dict, timeout: int, chan: BaseChan):
        super().__init__(method, target, headers, timeout)
        self._chan = chan
        self._remaining = 0
        self._gracetime = timeout
        self._frame = bytearray(136)
        self._xframe = None

    def __repr__(self) -> str:
        return "<%s %d %sclosed>" % ('BaseWsResponse', self.status, "" if self._done.is_set() else "not ")

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._done.is_set():
            raise StopAsyncIteration
        msg: WSMessage = await self.receive()
        if msg.type == WSMsgType.CLOSE:
            raise StopAsyncIteration
        return msg

    # Append incoming header data
    #
    # If the data appended includes the end of header marker,
    #    make sure the websocket upgrade was successful
    # Otherwise, return -1
    def appendBytes(self, data: Union[bytes, memoryview]) -> int:
        eoh: int = super().appendBytes(data)
        if eoh >= 0:
            # FIXME: handle redirects in a way compatible with aiohttp library
            self.ok = (self.status == 101)
            extraLen: int = self._len - self._headEnd
            if extraLen > 64:
                self._buff[:extraLen] = xbytearray(self._buff[self._headEnd:self._len])
            elif extraLen > 0:
                self._buff[:extraLen] = self._buff[self._headEnd:self._len].tobytes()
            self._len = extraLen
        return eoh

    async def ready(self) -> None:
        """
        Wait for the Websocket request to be sent and the response header to be fully received.
        This method is equivalent to entering the async context of the request.
        """
        if self.status >= 0:
            return
        # make sure we restart a new connection
        await self._chan.close()
        # queue the request
        self._chan.queue(self)
        await super().ready()
        if not self.ok:
            raise RuntimeError('Websocket handshake failed (status=%d)' % self.status)

    def getFrameView(self, pos: int, maxLen: int) -> bytes:
        endPos = min(len(self._xframe), pos + maxLen)
        return self._xframe[pos:endPos].tobytes()

    async def send(self, msg: WSMessage) -> None:
        mask: int = random.getrandbits(32)
        data: Union[xarray, bytes, memoryview]
        data = msg.data.encode('utf-8') if isinstance(msg.data, str) else msg.data
        dataLen: int = len(data)
        firstByte: int = msg.type
        if msg.fin:
            firstByte |= 0x80
        if dataLen < 0x7e:
            # header length = 6 (2 + mask)
            roundedLen = 6 + ((dataLen + 3) & 0xfffc)
            # Always reuse the same short buffer to avoid GC
            # We must ensure that the mask is dword-aligned
            buff: memoryview = memoryview(self._frame)[2:2 + roundedLen]
            dwView: memoryview = buff[2:].cast('I')
            buff[0] = firstByte
            buff[1] = 0x80 + dataLen
            buff[6:6 + dataLen] = data
            dwView[0] = mask
            for i in range(1, roundedLen // 4):
                dwView[i] ^= mask
            await self._chan._send(buff[:6 + dataLen])
        else:
            assert dataLen <= 65535
            # header length = 8 (4 + mask)
            roundedLen = 8 + ((dataLen + 3) & 0xfffc)
            buff: xbytearray = xbytearray(roundedLen)
            buff[0] = firstByte
            buff[1] = 0xfe
            buff[2] = dataLen >> 8
            buff[3] = dataLen & 0xff
            dwView: xmemoryview = buff[4:roundedLen].cast('I')
            dwView[0] = mask
            buff[8:8 + dataLen] = data
            for i in range(1, roundedLen // 4):
                dwView[i] ^= mask
            self._xframe = buff[:8 + dataLen]
            await self._chan._sendView(self.getFrameView)
            self._xframe = None

    async def recv(self, partialFrames: bool = False) -> WSMessage:
        pkt: bytes
        if self._len > 0:
            pkt = self._buff[:self._len].tobytes()
            self._len = 0
        else:
            pkt = await self._chan._recv(self, 128)
        rcvLen: int = len(pkt)
        while rcvLen < 2:
            # receiving the header byte by byte is very unlikely, no need to optimize more
            pkt += await self._chan._recv(self, 128)
            rcvLen = len(pkt)
        msgType: int = pkt[0] & 0x0f
        isFin: bool = (pkt[0] & 0x80) != 0
        isMasked: bool = (pkt[1] & 0x80) != 0
        mask: int = 0
        dataLen: int = pkt[1] & 0x7f
        hdrLen: int = 2
        if dataLen >= 0x7e:
            assert dataLen != 0x7f
            while rcvLen < 4:
                # receiving the header byte by byte is very unlikely, no need to optimize more
                pkt += await self._chan._recv(self, 128)
                rcvLen = len(pkt)
            hdrLen = 4
            dataLen = pkt[2] * 256 + pkt[3]
        if isMasked:
            # note: server is not expected to send masked frames
            mask = (pkt[hdrLen + 3] << 24) + (pkt[hdrLen + 2] << 16) + (pkt[hdrLen + 1] << 8) + pkt[hdrLen]
            hdrLen += 4
        frameLen: int = hdrLen + dataLen
        extraLen: int = 0
        extraData: Union[memoryview, None] = None
        if rcvLen > frameLen:
            extraLen = rcvLen - frameLen
            extraData = memoryview(pkt)[frameLen:rcvLen]
        # 1. Shortcut for the most frequent case: fully received unmasked frames
        if rcvLen >= frameLen and (isFin or partialFrames) and mask == 0:
            self._len = extraLen
            if extraLen > 0:
                if self._buff is None:
                    self._buff = xbytearray(512)
                self._buff[:extraLen] = extraData
            self.keepAlive(self._gracetime)
            return WSMessage(msgType, memoryview(pkt)[hdrLen:frameLen], isFin)
        # 2. General case: accumulate data, unmask if needed
        if self._buff is None:
            self._buff = xbytearray(512)
        roundedLen: int = (dataLen + 3) & 0xfffc
        buff: xarray
        if rcvLen > frameLen:
            self._len = extraLen
            if extraLen > 0:
                self._buff[:extraLen] = extraData
            roundedStart: int = (extraLen + 3) & 0xfffc
            buff = self._buff[roundedStart:roundedStart + roundedLen]
        else:
            if dataLen <= len(self._buff):
                buff = self._buff[:roundedLen]
            else:
                buff = xbytearray(roundedLen)
            rcvLen -= hdrLen
            buff[:rcvLen] = pkt[hdrLen:]
            while rcvLen < dataLen:
                pktLen: int = min(dataLen - rcvLen, 128)
                pkt = await self._chan._recv(self, pktLen)
                pktLen = len(pkt)
                buff[rcvLen:rcvLen + pktLen] = pkt
                rcvLen += pktLen
        # decode mask if needed
        if mask != 0:
            dwView = buff[:roundedLen].cast('I')
            for i in range(0, roundedLen // 4):
                dwView[i] ^= mask
        # return single frame if FIN or if no merge is requested
        data: xarray = buff[:dataLen]
        if isFin or partialFrames:
            self.keepAlive(self._gracetime)
            return WSMessage(msgType, data, isFin)
        # 3. Final case: need to aggregate multiple frames (first frame had no FIN flag)
        frames: list[xarray] = [data]
        totLen: int = len(data)
        while not isFin:
            nextMsg: WSMessage = await self.recv(True)
            frames.append(nextMsg.data)
            totLen += len(nextMsg.data)
            isFin = nextMsg.fin
        data = xbytearray(totLen)
        totLen = 0
        for frame in frames:
            frameLen = len(frame)
            data[totLen:totLen + frameLen] = frame
            totLen += frameLen
        return WSMessage(msgType, data, True)

    async def pong(self, data: Union[bytes, str] = b'') -> None:
        await self.send(WSMessage(WSMsgType.PONG, data, True))

    async def send_bytes(self, data: Union[bytes, bytearray, memoryview]) -> None:
        await self.send(WSMessage(WSMsgType.BINARY, data, True))

    async def receive(self) -> WSMessage:
        msg: WSMessage = await self.recv()
        while msg.type == WSMsgType.PING:
            await self.pong(msg.data)
            msg = await self.recv()
        if msg.type == WSMsgType.CLOSE:
            self._done.set()
            await self._chan.close()
            raise EOFError()
        return msg

    async def receive_bytes(self) -> bytes:
        msg: WSMessage = await self.receive()
        if msg.type != WSMsgType.BINARY:
            raise TypeError(f"Message is not BINARY")
        if isinstance(msg.data, bytes):
            return msg.data
        if isinstance(msg.data, memoryview):
            return bytes(msg.data)
        return msg.data.tobytes()

    async def close(self):
        if self._chan._writer:
            try:
                await self.send(WSMessage(WSMsgType.CLOSE, b'', True))
            except OSError as _:
                pass
            except asyncio.CancelledError as _:
                pass
            await self._chan.close()
        self._done.set()

    def release(self) -> None:
        self._chan._session.create_task(self.close())

    # Wait for response to be completed
    async def released(self) -> None:
        await self._chan.close()


# noinspection PyRedeclaration
class ClientWebSocketResponse(BaseWsResponse):

    async def ping(self, data: Union[bytes, str] = b'') -> None:
        await self.send(WSMessage(WSMsgType.PING, data, True))

    async def send_str(self, data: str) -> None:
        await self.send(WSMessage(WSMsgType.TEXT, data.encode('utf-8'), True))

    async def send_json(self, data) -> None:
        await self.send_str(json.dumps(data))

    async def receive_str(self) -> str:
        msg: WSMessage = await self.receive()
        if msg.type != WSMsgType.TEXT:
            raise TypeError(f"Message is not TEXT")
        return msg.data

    async def receive_json(self):
        data: str = await self.receive_str()
        return json.loads(data)

    if not _IS_MICROPYTHON:
        def __repr__(self) -> str:
            return "<%s %d %sclosed>" % ('ClientWebSocketResponse', self.status, "" if self._done.is_set() else "not ")


if not _IS_MICROPYTHON:
    AkaClientResponse = TypeVar('AkaClientResponse', bound=ClientResponse)
    AkaClientWebSocketResponse = TypeVar('AkaClientWebSocketResponse', bound=ClientWebSocketResponse)
else:
    AkaClientResponse = None
    AkaClientWebSocketResponse = None


# noinspection PyProtectedMember
class BaseSession:
    _base: Union[YUrl, None]
    _ssl: Union[SSLContext, None]
    _headers: Union[Pairs, None]
    _auth: Union[BaseAuth, None]
    _httpver: str
    _channels: list[Union[BaseChan, None]]
    _wschannels: list[BaseChan]

    def __init__(self, base_url: Union[YUrl, str] = "", *,
                 headers: Union[Pairs, None] = None,
                 ssl: Union[SSLContext, None] = None,
                 auth: Union[BaseAuth, None] = None,
                 version: str = "HTTP/1.1"):
        if isinstance(base_url, YUrl):
            self._base = base_url
        elif len(base_url) == 0:
            self._base = None
        else:
            self._base = YUrl(base_url)
        if headers is not None:
            self._headers = headers
        elif version != "":
            self._headers = {"User-Agent": "yaiohttp", "Accept-Encoding": ""}
        else:
            self._headers = None
        self._ssl = ssl
        if auth is not None:
            self._auth = auth
        elif self._base and self._base.user:
            self._auth = DigestAuth(self._base.user, self._base._pass)
        else:
            self._auth = None
        self._httpver = version
        self._channels = []
        self._wschannels = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return await self.close()

    def create_task(self, coro: Coroutine) -> asyncio.Task:
        return asyncio.create_task(coro)

    # Build the request line
    def _buildRequest(self, path: str, params: Union[Pairs, None]) -> str:
        if params is not None and len(params) > 0:
            paramStr: str = '&'.join(['='.join(param) for param in params])
            if '?' in path:
                path += '&' + paramStr
            else:
                path += '?' + paramStr
        return path if path else '/'

    def _sendRequest(self, baseUrl: YUrl, request: ClientResponse, *,
                     ssl: Union[SSLContext, bool, None] = None,
                     channel: int = -1):
        if ssl is None:
            ssl = self._ssl
        chan: int = max(0, channel)
        while chan < len(self._channels) and not self._channels[chan].matchUrl(baseUrl):
            chan += 1
        while chan >= len(self._channels):
            self._channels.append(None)
        if self._channels[chan] is None:
            self._channels[chan] = BaseChan(self, baseUrl, ssl)
        request.queueOn(self._channels[chan])

    def request(self, method: str, url: str = "", *,
                params: Union[Pairs, None] = None,
                data: Union[xarray, bytes, None] = None,
                json: Any = None,
                headers: Union[Pairs, None] = None,
                ssl: Union[SSLContext, bool, None] = None,
                auth: Union[BaseAuth, None] = None,
                version: Union[str, None] = None,
                timeout: float = 300,
                channel: Union[int, None] = -1,
                as_cls: Type[AkaClientResponse] = ClientResponse) -> AkaClientResponse:
        base: YUrl
        relative: str
        if self._base is None:
            base = YUrl(url)
            path = base.subDomain
        else:
            base = self._base
            if len(url) > 0 and url[0] != '/':
                url = '/' + url
            if not base.isWebSocket() and base.subDomain:
                path = base.subDomain + url
            else:
                path = url
        relative = self._buildRequest(path, params)
        proto: str = self._httpver if version is None else version
        if auth is not None:
            self._auth = auth
        if self._auth is None and base.user:
            self._auth = DigestAuth(base.user, base._pass)
        # Build the headers list
        if len(proto) > 3 and proto[-3] == '1.0':
            reqHeaders = OrderedDict({'Connection': 'keep-alive'})
        else:
            reqHeaders = OrderedDict()
        # Build the content as xarray
        if json is not None:
            data = xbytearray.fromJson(json)
            reqHeaders['Content-Type'] = 'application/json'
        if data is not None:
            if not isinstance(data, xarray):
                data = xbytearray(data)
            reqHeaders['Content-Length'] = str(len(data))
        # Apply user-requested headers last
        if self._headers is not None and proto != "":
            reqHeaders.update(self._headers)
        if headers is not None:
            reqHeaders.update(headers)
        # Create request/response object
        res: as_cls = as_cls(method, relative, reqHeaders, int(timeout * 1000), data)
        if channel is not None:
            self._sendRequest(base, res, ssl=ssl, channel=channel)
        return res

    def get(self, url: Union[YUrl, str] = "", *,
            params: Union[Pairs, None] = None,
            ssl: Union[SSLContext, bool, None] = None,
            headers: Union[Pairs, None] = None,
            auth: Union[BaseAuth, None] = None,
            timeout: float = 300,
            channel: Union[int, None] = -1) -> ClientResponse:
        return self.request("GET", url, ssl=ssl, params=params, headers=headers,
                            auth=auth, timeout=timeout, channel=channel)

    def ws_connect(self, url: Union[YUrl, str] = "", *,
                   params: Union[Pairs, None] = None,
                   ssl: Union[SSLContext, None] = None,
                   timeout: float = 300,
                   as_cls: Type[AkaClientWebSocketResponse] = ClientWebSocketResponse) -> "AkaClientWebSocketResponse":
        base: YUrl
        path: str

        if self._base is None:
            base = YUrl(url)
            path = base.subDomain
        else:
            base = self._base
            if url[0] != '/':
                url = '/' + url
            if base.subDomain:
                path = base.subDomain + url
            else:
                path = url
        relative: str = self._buildRequest(path, params)
        nonce: str = "%x%s%x" % (random.getrandbits(32), relative, ticks_ms())
        key: str = binascii.b2a_base64(hashlib.md5(nonce.encode('ascii')).digest()).decode('ascii').strip()
        reqHeaders: dict[str, str] = {
            'User-Agent':            'yaiohttp',
            'Sec-WebSocket-Version': '13',
            'Sec-WebSocket-Key':     key.strip(),
            'Connection':            'keep-alive, Upgrade',
            'Upgrade':               'websocket'
        }
        # Find channel to use (always reuse channel for same host)
        if ssl is None:
            ssl = self._ssl
        chan: int = 0
        while chan < len(self._wschannels) and not self._wschannels[chan].matchUrl(base):
            chan += 1
        if chan >= len(self._wschannels):
            self._wschannels.append(BaseChan(self, base, ssl))
        return as_cls('GET', relative, reqHeaders, int(timeout * 1000), self._wschannels[chan])  # type: ignore

    async def close(self):
        await asyncio.gather(*[chan.close() for chan in (self._channels + self._wschannels) if chan is not None])


# noinspection PyRedeclaration
class ClientSession(BaseSession):
    def post(self, url: str, **kwargs) -> ClientResponse:
        return self.request("POST", url, **kwargs)  # type: ignore

    def put(self, url: str, **kwargs) -> ClientResponse:
        return self.request("PUT", url, **kwargs)  # type: ignore

    def patch(self, url: str, **kwargs) -> ClientResponse:
        return self.request("PATCH", url, **kwargs)  # type: ignore

    def delete(self, url: str, **kwargs) -> ClientResponse:
        return self.request("DELETE", url, **kwargs)  # type: ignore

    def head(self, url: str, **kwargs) -> ClientResponse:
        return self.request("HEAD", url, **kwargs)  # type: ignore

    def options(self, url: str, **kwargs) -> ClientResponse:
        return self.request("OPTIONS", url, **kwargs)  # type: ignore

# -Class-Export-End (aiohttp)

#################################################################################
#                                                                               #
#          Common utility classes used by Yoctopuce library                     #
#                                                                               #
#################################################################################

# Callback function types
if not _IS_MICROPYTHON:
    try:
        YProgressCallback = Union[Callable[[int, str], None], None]
        YCalibrationCallback = Union[Callable[[float, int, list[float], list[float], list[float]], float], None]
        YLogCallback = Union[Callable[[str], Any], None]
        YHubDiscoveryCallback = Union[Callable[[str, Union[str, None]], Any], None]
        YDeviceUpdateCallback = Union[Callable[["YModule"], Any], None]
        YDeviceLogCallback = Union[Callable[["YModule", str], Any], None]
        YModuleBeaconCallback = Union[Callable[["YModule", int], Any], None]
    except TypeError:
        YProgressCallback = Union[Callable, None]
        YCalibrationCallback = Union[Callable, None]
        YLogCallback = Union[Callable, None]
        YHubDiscoveryCallback = Union[Callable, None]
        YDeviceUpdateCallback = Union[Callable, None]
        YDeviceLogCallback = Union[Callable, None]
        YModuleBeaconCallback = Union[Callable, None]
    YModuleLogCallback = YDeviceLogCallback
    YModuleConfigChangeCallback = YDeviceUpdateCallback


# This class is used to mimic "ByReference" parameter in function calls
class YRefParam:
    value: any

    def __init__(self, initialValue=None):
        self.value = initialValue

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return str(self.value)

# Class used for all Yoctopuce exceptions
class YAPI_Exception(Exception):
    errorType: int
    errorMessage: str

    def __init__(self, errType: int, errMsg: str):
        super().__init__(errMsg)
        self.errorType = errType
        self.errorMessage = errMsg

    def __repr__(self) -> str:
        return "%s(%d,'%s')" % ('YAPI_Exception', self.errorType, self.errorMessage)


# Default calibration handler
# noinspection PyUnusedLocal
def _linCalHdl(rawValue: float, calibType: int, calibParams: list[float], calibRawValues: list[float], calibRefValues: list[float]) -> float:
    # calibration types n = 1..10 and 11..20 are meant for linear calibration using n points
    npt: int
    if calibType < _YOCTO_CALIB_TYPE_OFS:
        npt = min(calibType % 10, len(calibRawValues), len(calibRefValues))
    else:
        npt = len(calibRefValues)
    x: float = calibRawValues[0]
    adj: float = calibRefValues[0] - x
    i: int = 1
    while i < npt and rawValue > calibRawValues[i - 1]:
        x2 = x
        adj2 = adj
        x = calibRawValues[i]
        adj = calibRefValues[i] - x
        if rawValue < x and x > x2:
            adj = adj2 + (adj - adj2) * (rawValue - x2) / (x - x2)
        i += 1
    return rawValue + adj


#################################################################################
#                                                                               #
#                  HwId, YPEntry, PlugEvent, CalHdl                             #
#                                                                               #
#   In micropython, an object uses 1 block (16 bytes) more than a namedtuple.   #
#   So for trivial objects that exist in large counts, we use namedtuples-      #
#                                                                               #
#################################################################################

if _IS_MICROPYTHON:
    HwId = namedtuple("HwId", ('module', 'function'))
    YPlugEv = namedtuple("YPlugEv", ('eventType', 'module'))
    YCalibCtx = namedtuple("YCalibCtx", ('src', 'typ', 'par', 'raw', 'cal'))
else:

    class HwId(NamedTuple):
        module: str
        function: str


    class YPlugEv(NamedTuple):
        eventType: int
        module: YModule


    class YCalibCtx(NamedTuple):
        src: str
        typ: int
        par: list[int]
        raw: list[float]
        cal: list[float]


def str2hwid(hwid_str: str) -> HwId:
    words: list[str] = hwid_str.split('.', 1)
    if _IS_MICROPYTHON:
        return HwId(sys.intern(words[0]), sys.intern(words[1]))
    else:
        return HwId(words[0], words[1])


def hwid2str(hwid: HwId) -> str:
    return '%s.%s' % hwid

#################################################################################
#                                                                               #
#                                  YDevice                                      #
#                                                                               #
#################################################################################

# noinspection PyProtectedMember
class YDevice:
    ref: int  # unique identifier for each device created
    hub: YGenericHub
    _serial: str
    _networkUrl: str
    _funcIds: list[Union[str,None]]
    _cacheExpiration: int
    _cache_json: Union[xdict, None]
    _api_buff: Union[xbytearray, None]
    _upload_buff: Union[xbytearray, None]
    lastTimeRef: float
    lastDuration: float
    # Possible key for callbackDict:
    # funydx for value callback
    # (funydx + _TIMED_REPORT_SHIFT) for timed callback
    # 'name' for beacon change and config change callback
    callbackDict: dict[Union[int, str], Union[YFunction, None]]
    _pendingReq: Union[YRequest, None]  # linked list of pending requests
    _logCallback: YDeviceLogCallback
    _logpos: int
    _beacon: int

    def __init__(self, yctx: YAPIContext, ref: int, devrec: xdict, funcIds: list[Union[str,None]]):
        serial: str = devrec['serialNumber']
        hub: Union[YGenericHub,None] = yctx.getGenHub(devrec['hubRef'])
        if not hub:
            raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND, "Device [%s] not online" % serial)
        self.ref = ref
        self.hub = hub
        self._serial = serial
        self._networkUrl = devrec['networkUrl']
        self._funcIds = funcIds
        self._cacheExpiration = 0
        self._cache_json = None
        self._api_buff = None
        self._upload_buff = None
        self.lastTimeRef = 0
        self.lastDuration = 0
        self.callbackDict = {}
        self._beacon = -1
        self._pendingReq = None
        self._logpos = 0

    def getFunYdxByFuncId(self, funcid: str) -> int:
        try:
            return self._funcIds.index(funcid)
        except ValueError: # not present
            return -1

    def _ensureConnected(self):
        if not self.hub:
            raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND, "Device [%s] has been disconnected" % self._serial)

    async def requestAPI(self) -> xdict:
        # This function raises an exception on error !
        self._ensureConnected()
        if ticks_past(self._cacheExpiration) or not self._cacheExpiration:
            reqUrl: str = "/api.json"
            if self._cache_json is not None:
                fwrelease: str = self._cache_json["module"]["firmwareRelease"]
                fwrelease = YFunction._escapeAttr(fwrelease)
                reqUrl += "?fw=" + fwrelease
            if self._api_buff is None:
                self._api_buff = xbytearray(1024)
            try:
                yreq: xarray = await self.requestHTTPSync(reqUrl, None, self._api_buff)
            except YAPI_Exception as ecx:
                if ecx.errorType == YAPI.UNAUTHORIZED:
                    raise
                self._ensureConnected()
                # if _LOG_LEVEL > 3:
                # fixme: log all faulty request for now.
                self.hub._yapi._Log('Request failed (%s), retry after updateDeviceList.' % str(ecx))
                await self.hub.updateDeviceList(True)
                yreq: xarray = await self.requestHTTPSync(reqUrl, None, self._api_buff)
            try:
                remap: bool = (yreq[0] == 91)  # '['
                self._cache_json = yreq.json(reuse=self._cache_json, mapValues=remap, encoding='latin-1')
            except BaseException as exc:
                raise YAPI_Exception(YAPI.IO_ERROR, "Invalid JSON response")
            self._cacheExpiration = ticks_add(ticks_ms(), self.hub._yapi._defaultCacheValidity) | 1
        return self._cache_json

    async def requestHTTPSync(self, reqUrl: str, body: Union[xarray, None], buff: Union[xbytearray, None] = None) -> ByteArrayLike:
        timeout: int = self.hub.networkTimeout
        if ("/testcb.txt" in reqUrl) or ("/logger.json" in reqUrl) or \
                ("/rxmsg.json" in reqUrl) or ("/rxdata.bin" in reqUrl) or \
                ("/at.txt" in reqUrl) or ("/files.json" in reqUrl):
            timeout = _YIO_1_MINUTE_TCP_TIMEOUT
        elif ("/flash.json" in reqUrl) or ("/upload.html" in reqUrl):
            timeout = _YIO_10_MINUTES_TCP_TIMEOUT
        yreq: YRequest = await self.initRequest(reqUrl, body, timeout)
        if buff:
            yreq.setBuff(buff)
        try:
            self._ensureConnected()
            res: ByteArrayLike = await self.hub.devRequestSync(yreq)
        finally:
            if self._pendingReq == yreq:
                # enable garbage collection asap
                self._pendingReq = self._pendingReq.devNext
        return res

    async def requestHTTPAsync(self, reqUrl: str, body: Union[xarray, None]) -> None:
        yreq: YRequest = await self.initRequest(reqUrl, body, self.hub.networkTimeout)
        try:
            self._ensureConnected()
            await self.hub.devRequestAsync(yreq)
        finally:
            if self._pendingReq == yreq:
                # enable garbage collection asap
                self._pendingReq = self._pendingReq.devNext

    async def initRequest(self, reqUrl: str, body: Union[xarray, None], msTimeout: int) -> YRequest:
        self._ensureConnected()
        fmt: str = "%s/%s" if reqUrl[0] != '/' else "%s%s"
        reqUrl = fmt % (self._networkUrl, reqUrl)
        method: str = "GET" if body is None else "POST"
        yreq: YRequest = self.hub.makeRequest(method, reqUrl, body, msTimeout)
        if self._pendingReq:
            prevReq: YRequest = self._pendingReq
            while prevReq.devNext:
                prevReq = prevReq.devNext
            prevReq.devNext = yreq
            await prevReq.released()
        self._pendingReq = yreq
        return yreq

    async def waitForPendingQueries(self) -> None:
        while self._pendingReq:
            lastReq: YRequest = self._pendingReq
            while lastReq.devNext:
                lastReq = lastReq.devNext
            await lastReq.released()

    def clearCache(self):
        self._cacheExpiration = 0

    def setLastTimeRef(self, data: bytearray):
        sec: int = (data[0] & 0xff) + 0x100 * (data[1] & 0xff) + 0x10000 * (data[2] & 0xff) + 0x1000000 * (data[3] & 0xff)
        ms: int = (data[4] & 0xff) * 4
        if len(data) >= 6:
            ms += (data[5] & 0xff) >> 6
            freq: int = data[6]
            freq += (data[5] & 0xf) * 0x100
            if (data[5] & 0x10) != 0:
                self.lastDuration = freq
            else:
                self.lastDuration = freq / 1000.0
        else:
            self.lastDuration = 0
        self.lastTimeRef = sec + ms / 1000.0

    def triggerLogPull(self):
        if self.hub and self not in self.hub._logPullList:
            self.hub._logPullList.append(self)

    def registerLogCallback(self, callback: YDeviceLogCallback):
        self._logCallback = callback
        if callback:
            self.triggerLogPull()

    @staticmethod
    def formatHTTPUpload(path: str, content: ByteArrayLike, buff: Union[xbytearray, None] = None) -> xarray:
        pathbin: bytes = path.encode()
        mimehdr1: bytes = b'Content-Disposition: form-data; name="'
        mimehdr2: bytes = b'"; filename="api"\r\nContent-Type: application/octet-stream\r\nContent-Transfer-Encoding: binary\r\n'
        boundary: bytes = b''
        while not boundary or content.find(boundary) >= 0:
            boundary = ('--Zz%06xzZ' % random.getrandbits(24)).encode()
        # VirtualHub-4web quirk: we have to switch from "multipart/form-data" to "x-upload"
        # to bypass PHP own processing of uploads. The exact value has anyway always be
        # ignored by VirtualHub and YoctoHubs, as long as a boundary is defined.
        bodyparts: list = [boundary, b'\r\n', mimehdr1, pathbin, mimehdr2, b'\r\n', content, b'\r\n', boundary, b'--\r\n']
        bodysize: bytes = str(sum(len(s) for s in bodyparts)).encode()
        allparts: list = [b'Content-Type: x-upload; boundary=', boundary[2:], b'\r\n',
                          b'Content-Length: ', bodysize, b'\r\n', b'\r\n'] + bodyparts
        fullsize: int = sum(len(s) for s in allparts)
        res: xbytearray = buff if (buff and len(buff) >= fullsize) else xbytearray(fullsize)
        pos: int = 0
        endpos: int = 0
        for part in allparts:
            endpos = pos + len(part)
            res[pos:endpos] = part
            pos = endpos
        return res if len(res) == endpos else res[:endpos]

    async def requestHTTPUpload(self, path: str, content: ByteArrayLike) -> int:
        await self.requestHTTPUploadEx(path, content)
        return YAPI.SUCCESS

    async def requestHTTPUploadEx(self, path: str, content: ByteArrayLike) -> ByteArrayLike:
        head_body: xarray = YDevice.formatHTTPUpload(path, content, self._upload_buff)
        res = await self.requestHTTPSync('/upload.html', head_body)
        if isinstance(head_body, xbytearray) and (self._upload_buff is None or len(self._upload_buff) < len(head_body)):
            # save working buffer to reuse it for next upload
            self._upload_buff = head_body
        return res


#################################################################################
#                                                                               #
#                         YAPIContext, YAPI, YHub                               #
#                                                                               #
#################################################################################

if not _IS_MICROPYTHON:
    def _freeAPI(yapi: YAPIContext, eventLoop):
        if eventLoop.is_closed():
            # Oops, original event loop is closed, we must recreate one to close sockets
            asyncio.run(yapi.FreeAPI())
        else:
            eventLoop.run_until_complete(yapi.FreeAPI())


# --- (generated code: YAPIContext class start)
# noinspection PyProtectedMember
class YAPIContext:
    # --- (end of generated code: YAPIContext class start)
    if not _IS_MICROPYTHON:
        INVALID_STRING: Final[str] = "!INVALID!"
        INVALID_DOUBLE: Final[float] = -math.inf
        MIN_DOUBLE: Final[float] = -math.inf
        MAX_DOUBLE: Final[float] = math.inf
        INVALID_INT: Final[int] = -9999999999
        INVALID_UINT: Final[int] = 9999999999
        INVALID_LONG: Final[int] = -999999999999999999
        HASH_BUF_SIZE: Final[int] = 28

        # InitAPI constants
        DETECT_NONE: Final[int] = 0
        DETECT_USB: Final[int] = 1
        DETECT_NET: Final[int] = 2
        DETECT_ALL: Final[int] = 3

        # --- (generated code: YAPI definitions)
        # Yoctopuce error codes, used by default as function return value
        SUCCESS: Final[int] = 0                 # everything worked all right
        NOT_INITIALIZED: Final[int] = -1        # call yInitAPI() first !
        INVALID_ARGUMENT: Final[int] = -2       # one of the arguments passed to the function is invalid
        NOT_SUPPORTED: Final[int] = -3          # the operation attempted is (currently) not supported
        DEVICE_NOT_FOUND: Final[int] = -4       # the requested device is not reachable
        VERSION_MISMATCH: Final[int] = -5       # the device firmware is incompatible with this API version
        DEVICE_BUSY: Final[int] = -6            # the device is busy with another task and cannot answer
        TIMEOUT: Final[int] = -7                # the device took too long to provide an answer
        IO_ERROR: Final[int] = -8               # there was an I/O problem while talking to the device
        NO_MORE_DATA: Final[int] = -9           # there is no more data to read from
        EXHAUSTED: Final[int] = -10             # you have run out of a limited resource, check the documentation
        DOUBLE_ACCES: Final[int] = -11          # you have two process that try to access to the same device
        UNAUTHORIZED: Final[int] = -12          # unauthorized access to password-protected device
        RTC_NOT_READY: Final[int] = -13         # real-time clock has not been initialized (or time was lost)
        FILE_NOT_FOUND: Final[int] = -14        # the file is not found
        SSL_ERROR: Final[int] = -15             # Error reported by mbedSSL
        RFID_SOFT_ERROR: Final[int] = -16       # Recoverable error with RFID tag (eg. tag out of reach), check YRfidStatus for details
        RFID_HARD_ERROR: Final[int] = -17       # Serious RFID error (eg. write-protected, out-of-boundary), check YRfidStatus for details
        BUFFER_TOO_SMALL: Final[int] = -18      # The buffer provided is too small
        DNS_ERROR: Final[int] = -19             # Error during name resolutions (invalid hostname or dns communication error)
        SSL_UNK_CERT: Final[int] = -20          # The certificate is not correctly signed by the trusted CA
        UNCONFIGURED: Final[int] = -21          # Remote hub is not yet configured

        # TLS / SSL definitions
        NO_TRUSTED_CA_CHECK: Final[int] = 1     # Disables certificate checking
        NO_EXPIRATION_CHECK: Final[int] = 2     # Disables certificate expiration date checking
        NO_HOSTNAME_CHECK: Final[int] = 4       # Disable hostname checking
        LEGACY: Final[int] = 8                  # Allow non-secure connection (similar to v1.10)
        # --- (end of generated code: YAPI definitions)
    else:
        # ympy-cross will resolve all references to API constants to their value at compile time
        SUCCESS = 0  # Provide YAPI.SUCCESS nevertheless, just in case it is used in REPL

    _apiMode: int
    _atexit: Union[Callable[[], None], None]
    _lastErrorType: int
    _lastErrorMsg: str
    _hubs: list[YGenericHub]
    _registeredHubs: list[YGenericHub]  # List of hubs currently (Pre)Registered. TestHub should not add hub to this list
    _yhub_cache: dict[int, YHub]
    _pendingCallbacks: list[YPlugEv]
    _eventsBuff: xbytearray
    _eventsHead: int
    _eventsTail: int
    _arrivalCallback: YDeviceUpdateCallback
    _namechgCallback: YDeviceUpdateCallback
    _removalCallback: YDeviceUpdateCallback
    _logCallback: YLogCallback
    _ValueCallbackList: list[YFunction]
    _TimedReportCallbackList: list[YSensor]
    _moduleCallbackList: list[YModule]
    _deviceListValidityMs: int
    _networkTimeoutMs: int
    _defaultCacheValidity: int
    _networkSecurityOptions: int
    _sslContext: Union[SSLContext | None]
    _tasks: list[asyncio.Task]  # List of global asyncio background task objects
    _ExceptionsDisabled: bool
    # Device and functions hash tables
    _lastDevRef: int
    _devRecs: xlist  # white page records with corresponding yp records as sublists
    _devRecBySn: dict[str, xdict]  # hash table of devRec, by serial number, for connected devices
    _devsBySn: dict[str, YDevice]  # hash table of instantiated devices, by serial number (kept on disconnect)
    _devsByRef: dict[int, YDevice]  # hash table of devices, by unique identifier (kept on disconnect)
    _connectedFns: dict[HwId, YFunction]  # functions requested and available, by Hardware Id
    _requestedFns: dict[str, YFunction]  # functions requested but not yet known, by any type of name
    # Attributes below are not used in YoctoHubs (global certificates, no SSDP client for now)
    if not _IS_MICROPYTHON:
        _trustedCertificate: list[str]
        _ssdp: Union[YSSDP, None]
        _HubDiscoveryCallback: YHubDiscoveryCallback

    def __init__(self):
        self._ExceptionsDisabled = False
        self._lastErrorType = 0
        self._lastErrorMsg = ''
        self._eventsBuff = xbytearray(4096)
        self._deviceListValidityMs = 10000
        self._networkTimeoutMs = 20000
        self._defaultCacheValidity = 5
        self._tasks = []
        if not _IS_MICROPYTHON:
            self._trustedCertificate = []
            self._ssdp = None
        self.resetContext()

    def resetContext(self):
        if not _IS_MICROPYTHON:
            self._trustedCertificate = []
            self._HubDiscoveryCallback = None
            if self._ssdp:
                self._ssdp.reset()
        self._apiMode = 0
        self._atexit = None
        self._hubs = []
        self._registeredHubs = []
        self._yhub_cache = OrderedDict()
        self._pendingCallbacks = []
        self._eventsHead = 0
        self._eventsTail = 0
        self._arrivalCallback = None
        self._namechgCallback = None
        self._removalCallback = None
        self._logCallback = None
        self._ValueCallbackList = []
        self._TimedReportCallbackList = []
        self._moduleCallbackList = []
        self._networkSecurityOptions = 0
        # Device and functions hash tables
        self._lastDevRef = 0
        self._devRecs = xlist()
        self._devRecBySn = {}
        self._devsBySn = {}
        self._devsByRef = {}
        self._connectedFns = {}
        self._requestedFns = {}

    def _throw(self, errType: int, errMsg: str) -> int:
        self._lastErrorType = errType
        self._lastErrorMsg = errMsg
        if not self._ExceptionsDisabled:
            raise YAPI_Exception(errType, errMsg)
        return errType

    def _rethrow(self, exc: YAPI_Exception) -> int:
        self._lastErrorType = exc.errorType
        self._lastErrorMsg = exc.errorMessage
        if not self._ExceptionsDisabled:
            raise exc
        return exc.errorType

    def create_task(self, coro: Coroutine) -> asyncio.Task:
        # first purge list from completed tasks
        allTasks = self._tasks
        for pos in range(len(allTasks) - 1, 0, -1):
            if allTasks[pos].done():
                del allTasks[pos]
        task: asyncio.Task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task

    # Default encoding when exchanging data through the Yoctopuce API
    DefaultEncoding: str = "latin-1"

    # Convert Yoctopuce 16-bit decimal floats to standard double-precision floats
    _decExp = [1.0e-6, 1.0e-5, 1.0e-4, 1.0e-3, 1.0e-2, 1.0e-1, 1.0, 1.0e1,
               1.0e2, 1.0e3, 1.0e4, 1.0e5, 1.0e6, 1.0e7, 1.0e8, 1.0e9]

    @staticmethod
    def _decimalToDouble(val: int) -> float:
        negate = False
        mantis = val & 2047
        if mantis == 0:
            return 0.0
        if val > 32767:
            negate = True
            val = 65536 - val
        if val < 0:
            negate = True
            val = -val
        exp = val >> 11
        res = mantis * YAPIContext._decExp[exp]
        if negate:
            return -res
        else:
            return res

    # Convert standard double-precision floats to Yoctopuce 16-bit decimal floats
    @staticmethod
    def _doubleToDecimal(val: float) -> int:
        negate = False
        if val == 0.0:
            return 0
        if val < 0.0:
            negate = True
            val = -val
        comp: float = val / 1999.0
        decpow: int = 0
        while comp > YAPIContext._decExp[decpow] and decpow < 15:
            decpow += 1
        mant: float = val / YAPIContext._decExp[decpow]
        if decpow == 15 and mant > 2047.0:
            # overflow
            res: int = (15 << 11) + 2047
        else:
            res: int = (decpow << 11) + round(mant)
        if negate:
            return -res
        else:
            return res

    # Parse an array of u16 encoded in a base64-like string with memory-based compression
    @staticmethod
    def _decodeWords(dataStr: str) -> list[int]:
        data: bytes = dataStr.encode('ascii')
        udata: list[int] = []
        datalen: int = len(data)
        p: int = 0
        while p < datalen:
            c: int = data[p]
            if c == 42:  # character '*'
                val = 0
            elif c == 88:  # character 'X'
                val = 0xffff
            elif c == 89:  # character 'Y'
                val = 0x7fff
            elif c >= 97:  # character 'a'...
                srcpos: int = len(udata) - 1 - (c - 97)
                if srcpos < 0:
                    val = 0
                else:
                    val = udata[srcpos]
            else:
                if p + 2 > datalen:
                    return udata
                val = c - 48  # character '0'...
                p += 1
                c = data[p]
                val += (c - 48) << 5
                p += 1
                c = data[p]
                if c == 122:  # character 'z'
                    c = 92  # character '\\'
                val += (c - 48) << 10
            udata.append(val)
            p += 1
        return udata

    # Parse an array of floats in a string, as in calibrationParams, and
    # return them in Yoctopuce fixed-decimal style
    @staticmethod
    def _decodeFloats(dataStr: str) -> list[int]:
        data: bytes = dataStr.encode('ascii')
        idata: list[int] = []
        datalen: int = len(data)
        p: int = 0
        while p < datalen:
            val: int = 0
            sign: int = 1
            dec: int = 0
            decInc: int = 0
            c: int = data[p]
            p += 1
            while not ((48 <= c < 58) or c == 45):  # not a digit or '-'
                if p >= datalen:
                    return idata
                c = data[p]
                p += 1
            if c == 45:  # character '-'
                if p >= datalen:
                    return idata
                c = data[p]
                p += 1
                sign = -sign
            while (48 <= c < 58) or c == 46:  # digit or '.'
                if c == 46:  # character '.'
                    decInc = 1
                elif dec < 3:
                    val = val * 10 + (c - 48)
                    dec += decInc
                if p < datalen:
                    c = data[p]
                    p += 1
                else:
                    c = 0
            if dec < 3:
                if dec == 0:
                    val *= 1000
                elif dec == 1:
                    val *= 100
                else:
                    val *= 10
            idata.append(sign * val)
        return idata

    @staticmethod
    def decodePubVal(typeV2: int, funcval: bytes, ofs: int, funcvallen: int) -> str:
        buffer = ""
        if typeV2 == _NOTIFY_V2_6RAWBYTES or typeV2 == _NOTIFY_V2_TYPEDDATA:
            funcValType: int
            if typeV2 == _NOTIFY_V2_6RAWBYTES:
                funcValType = _PUBVAL_6RAWBYTES
            else:
                funcValType = funcval[ofs] & 0xff
                ofs += 1
            if funcValType == _PUBVAL_LEGACY:
                # fallback to legacy handling, just in case
                pass
            elif funcValType in (_PUBVAL_1RAWBYTE,
                                 _PUBVAL_2RAWBYTES,
                                 _PUBVAL_3RAWBYTES,
                                 _PUBVAL_4RAWBYTES,
                                 _PUBVAL_5RAWBYTES,
                                 _PUBVAL_6RAWBYTES):
                # 1..5 hex bytes
                for i in range(funcValType):
                    c: int = funcval[ofs] & 0xff
                    ofs += 1
                    b: int = c >> 4
                    buffer += b + ord('a') if b > 9 else b + ord('0')
                    b = c & 0xf
                    buffer += b + ord('a') if b > 9 else b + ord('0')
            elif funcValType in (_PUBVAL_C_LONG,
                                 _PUBVAL_YOCTO_FLOAT_E3):
                # 32bit integer in little endian format or Yoctopuce 10-3 format
                numVal: int = funcval[ofs] & 0xff
                numVal += (funcval[ofs + 1] & 0xff) << 8
                numVal += (funcval[ofs + 2] & 0xff) << 16
                numVal += (funcval[ofs + 3] & 0xff) << 24
                if numVal & 0x8000000:
                    numVal -= 0x100000000
                if funcValType == _PUBVAL_C_LONG:
                    return "%d" % numVal
                else:
                    buffer = "%.3f" % (numVal / 1000.0)
                    endp: int = len(buffer)
                    while endp > 0 and buffer[endp - 1] == '0':
                        endp -= 1
                    if endp > 0 and buffer[endp - 1] == '.':
                        endp -= 1
                        buffer = buffer[:endp]
                    return buffer
            elif funcValType == _PUBVAL_C_FLOAT:
                # 32bit (short) float
                v = funcval[ofs]
                v += funcval[ofs + 1] << 8
                v += funcval[ofs + 2] << 16
                v += funcval[ofs + 3] << 24
                if v & 0x8000000:
                    v -= 0x100000000
                fraction = (v & ((1 << 23) - 1)) + (1 << 23) * (v >> 31 | 1)
                exp = (v >> 23 & 0xFF) - 127
                floatVal: float = fraction * pow(2, exp - 23)
                buffer = "%.6f" % floatVal
                endp: int = len(buffer)
                while endp > 0 and buffer[endp - 1] == '0':
                    endp -= 1
                if endp > 0 and buffer[endp - 1] == '.':
                    endp -= 1
                    buffer = buffer[:endp]
                return buffer
            else:
                return "?"
        # Legacy handling: just pad with NUL up to 7 chars
        lenvar: int = 0
        while lenvar < _YOCTO_PUBVAL_LEN and lenvar < funcvallen:
            if funcval[lenvar + ofs] == 0:
                break
            lenvar += 1
            return funcval[ofs: lenvar + ofs].decode(YAPI.DefaultEncoding)

    @staticmethod
    def decodeNetFuncValV2(p: bytes) -> Union[bytearray, None]:
        # Network notification format: 7x7bit (mapped to 7 chars in range 32..159)
        #                              used to represent 1 flag (RAW6BYTES) + 6 bytes
        # INPUT:  [R765432][1076543][2107654][3210765][4321076][5432107][6543210]
        # OUTPUT: 7 bytes array (1 byte for the funcTypeV2 and 6 bytes of USB like data
        #                     funcTypeV2 + [R][-byte 0][-byte 1-][-byte 2-][-byte 3-][-byte 4-][-byte 5-]
        #
        # return null on error
        p_ofs: int = 0
        ch: int = p[p_ofs] & 0xff
        len_var: int = 0
        func_val: bytearray = bytearray(7)
        func_val[:6] = b'\x00' * 6
        if ch < 32 or ch > 32 + 127:
            return None
        # get the 7 first bits
        ch -= 32
        func_val[0] = _NOTIFY_V2_6RAWBYTES if (ch & 0x40) != 0 else _NOTIFY_V2_TYPEDDATA
        # clear flag
        ch &= 0x3f
        while len_var < _YOCTO_PUBVAL_SIZE:
            p_ofs += 1
            if p_ofs >= len(p):
                break
            new_ch = p[p_ofs] & 0xff
            if new_ch == _NOTIFY_NETPKT_STOP:
                break
            if new_ch < 32 or new_ch > 32 + 127:
                return None
            new_ch -= 32
            ch = (ch << 7) + new_ch
            func_val[len_var + 1] = (ch >> (5 - len_var)) & 0xFF
            len_var += 1
        return func_val

    @staticmethod
    def functionClass(funcid: str) -> str:
        classlen: int = len(funcid)
        while ord(funcid[classlen - 1]) <= 57:
            classlen -= 1
        return sys.intern(funcid[0].upper() + funcid[1:classlen])

    @staticmethod
    def _atoi(val: str) -> int:
        val = val.strip()
        stop: int = len(val)
        if stop == 0:
            return 0
        start: int = 1 if val[0] in '-+' else 0
        extra: str = val[start:].lstrip('0123456789')
        stop -= len(extra)
        if stop == 0: return 0
        return int(val[:stop])

    @staticmethod
    def _atof(val: str) -> float:
        try:
            res = float(val)
        except ValueError:
            res = 0.0
        return res

    @staticmethod
    def _bytesToHexStr(bindata: xarray) -> str:
        return binascii.hexlify(bindata.tobytes()).decode('ascii').upper().strip()

    @staticmethod
    def _hexStrToBin(hex_str: str) -> xarray:
        return xbytearray(binascii.unhexlify(hex_str))

    def _findDevRecByName(self, logicalName: str) -> Union[xdict,None]:
        for devrec in self._devRecBySn.values():
            if devrec["logicalName"] == logicalName:
                return devrec
        return None

    def _findFunRecByHwId(self, hwid: HwId) -> Union[xdict,None]:
        devrec: Union[xdict, None] = self._devRecBySn.get(hwid.module)
        if devrec:
            for funrec in devrec["yellowPages"]:
                if funrec["functionId"] == hwid.function:
                    return funrec
        return None

    def _resolveFuncName(self, className: str, logicalName: str) -> Union[HwId, None]:
        if className in _YOCTO_BASETYPES:
            for serial, devrec in self._devRecBySn.items():
                for funrec in devrec["yellowPages"]:
                    if funrec["logicalName"] == logicalName:
                        if className == "Function" or funrec["baseType"] == className:
                            return HwId(serial, funrec["functionId"])
        else:
            for serial, devrec in self._devRecBySn.items():
                for funrec in devrec["yellowPages"]:
                    if funrec["logicalName"] == logicalName:
                        if funrec["functionType"] == className:
                            return HwId(serial, funrec["functionId"])
        return None

    def _storeServices(self, hubRef: int, wprec: xdict, isNew: bool, yp: xdict) -> bool:
        serial: str = sys.intern(wprec["serialNumber"])
        lname: str = sys.intern(wprec["logicalName"])
        ischg: bool = False
        # create or update device record
        newrec: Union[dict,None] = None
        devrec: Union[xdict,None] = self._devRecBySn.get(serial)
        if not devrec:
            isNew = True
            # Check if we can reuse an existing (inactive) devrec
            for scan in self._devRecs:
                if scan["serialNumber"] == serial:
                    devrec = scan
                    break
            if not devrec:
                newrec = OrderedDict()
                devrec = newrec
                devrec["serialNumber"] = serial
        if isNew:
            # New arrival, setup or update all key fields
            dev: Union[YDevice,None] = self._devsBySn.get(serial)
            if dev:
                dev.hub = self.getGenHub(hubRef)
            devrec["hubRef"] = hubRef
            devrec["networkUrl"] = wprec["networkUrl"][:-4]
            devrec["logicalName"] = lname
        else:
            # Update information about connected device
            if devrec["logicalName"] != lname:
                devrec["logicalName"] = lname
                ischg = True
        devrec["index"] = wprec["index"]
        if newrec:
            # append yellowPage records, add device to xmem storage
            funrecs: list[dict[str, Union[str, int]]] = []
            for categ, yprecs in yp.items():
                for yprec in yprecs:
                    hwid = yprec["hardwareId"]
                    if hwid.module == serial:
                        funrec = OrderedDict()
                        funrec["functionId"] = hwid.function
                        funrec["functionType"] = categ
                        funrec["baseType"] = _YOCTO_BASETYPES[yprec["baseType"]]
                        funrec["logicalName"] = sys.intern(yprec["logicalName"])
                        advVal = yprec["advertisedValue"]
                        if len(advVal) > 1:
                            # make sure to reserve two dwords to avoid future resizes
                            advVal = advVal.ljust(5,'\0')
                        funrec["advertisedValue"] = advVal
                        funrec["index"] = yprec["index"]
                        funrecs.append(funrec)
            newrec["yellowPages"] = funrecs
            idx: int = len(self._devRecs)
            self._devRecs.append(newrec)
            devrec = self._devRecs[idx]
        else:
            # update existing yellowPage records, traversing both src and dst structure in parallel
            categ: str = ''
            yprecs: Union[xlist,None] = None
            yprec: Union[xdict,None] = None
            idx: int = 0
            for funrec in devrec["yellowPages"]:
                funcid = funrec["functionId"]
                if categ != funrec["functionType"]:
                    categ = funrec["functionType"]
                    yprecs = yp.get(categ)
                    if not yprecs: continue
                    idx = 0
                while idx < len(yprecs):
                    yprec = yprecs[idx]
                    hwid = yprec["hardwareId"]
                    if hwid.module == serial and hwid.function == funcid:
                        break
                    idx += 1
                if idx >= len(yprecs):
                    continue
                funrec["logicalName"] = sys.intern(yprec["logicalName"])
                funrec["advertisedValue"] = yprec["advertisedValue"]
                idx += 1
        if isNew:
            self._devRecBySn[serial] = devrec
            self._Log("HUB: device " + serial + " has been plugged")
            self._pushPlugEvent(serial)
        elif ischg:
            self._pushChangeEvent(serial)
        return isNew

    # Remove a device by serial from all hash tables
    def _forgetDevice(self, serial: str):
        try:
            del self._devRecBySn[serial]
        except KeyError:
            pass

    def _resolve(self, className: str, func: str) -> HwId:
        # Find the HwId for the specified function, if currently connected.
        # If device is not known as connected, return a clean error.
        # This function will not cause any network access.
        parts: list[str] = func.split('.')
        serial: str = parts[0]
        funcid: str
        if className == 'Module':
            # Special case: retrieve a module object
            funcid = 'module'
        elif len(parts) == 1:
            # Typical case: func is the logical name of a function
            hwid = self._resolveFuncName(className, func)
            if hwid:
                return hwid
            # fallback to assuming that func is a logical name or serial number of a module
            # with an implicit function name (like serial.module for instance)
            funcid = className[0].lower() + className[1:]
        else:
            # Second case: func is in the form: device_id.function_id
            funcid = parts[1]
        if serial:
            devrec: Union[xdict, None] = self._devRecBySn.get(serial)
            if not devrec:
                # Might actually be a device name rather than a serial
                devrec = self._findDevRecByName(serial)
                if devrec:
                    serial = devrec['serialNumber']
                else:
                    if self._hubs:
                        errmsg = "Device [%s] not online" % serial
                    else:
                        errmsg = "No hub has been registered"
                    raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND, errmsg)
            if funcid == 'module':
                return HwId(serial, funcid)
            for funrec in devrec["yellowPages"]:
                if funrec["functionId"] == funcid:
                    return HwId(serial, funcid)
                if funrec["logicalName"] == funcid:
                    return HwId(serial, funrec["functionId"])
        else:
            # serial is empty (ie ".temperature")
            for serial, devrec in self._devRecBySn.items():
                for funrec in devrec["yellowPages"]:
                    if funrec["functionId"] == funcid:
                        return HwId(serial, funcid)
        raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND,
                             "No function [%s] found on device [%s]" % (funcid, serial))

    def _addToCache(self, className: str, func: str, yfunc: YFunction):
        try:
            hwid: HwId = self._resolve(className, func)
            self._connectedFns[hwid] = yfunc
        except YAPI_Exception:
            self._requestedFns[func] = yfunc

    def _findInCache(self, className: str, func: str) -> Union[YFunction, None]:
        try:
            hwid: HwId = self._resolve(className, func)
            # the function has been located on a device
            fn: YFunction = self._connectedFns.get(hwid)
            if fn:
                return fn
            fn = self._requestedFns.get(func)
            if fn:
                self._connectedFns[hwid] = fn
                del self._requestedFns[func]
                return fn
        except YAPI_Exception:
            # The function is still abstract. At this point we don't know
            # if func is a true HwId or not, test for removal just in case
            if '.' in func:
                hwid: HwId = str2hwid(func)
                if hwid in self._connectedFns:
                    del self._connectedFns[hwid]
            if func in self._requestedFns:
                del self._requestedFns[func]
        return None

    def _firstHwId(self, className: str) -> Union[HwId, None]:
        if className == "Module":
            for serial in self._devRecBySn.keys():
                return HwId(serial,'module')
        elif className in _YOCTO_BASETYPES:
            for serial, devrec in self._devRecBySn.items():
                for funrec in devrec["yellowPages"]:
                    if className == "Function" or funrec["baseType"] == className:
                        return HwId(serial, funrec["functionId"])
        else:
            for serial, devrec in self._devRecBySn.items():
                for funrec in devrec["yellowPages"]:
                    if funrec["functionType"] == className:
                        return HwId(serial, funrec["functionId"])
        return None

    def _nextHwId(self, className: str, hwid: Union[HwId,None]) -> Union[HwId, None]:
        if not hwid:
            return None
        currSerial: str = hwid.module
        currFunctionId: str = hwid.function
        found: bool = False
        if className == "Module":
            for serial in self._devRecBySn.keys():
                if found:
                    return HwId(serial,'module')
                else:
                    found |= serial == currSerial
        elif className in _YOCTO_BASETYPES:
            for serial, devrec in self._devRecBySn.items():
                if not found and serial != currSerial:
                    continue
                for funrec in devrec["yellowPages"]:
                    if found:
                        if className == "Function" or funrec["baseType"] == className:
                            return HwId(serial, funrec["functionId"])
                    else:
                        found |= funrec["functionId"] == currFunctionId
        else:
            for serial, devrec in self._devRecBySn.items():
                if not found and serial != currSerial:
                    continue
                for funrec in devrec["yellowPages"]:
                    if found:
                        if funrec["functionType"] == className:
                            return HwId(serial, funrec["functionId"])
                    else:
                        found |= funrec["functionId"] == currFunctionId
        return None

    # Return a Device object for a specified serial number or logical device name,
    # if the device is known from past enumerations. Otherwise, return None.
    # This function will not cause any network access
    def _getDevice(self, serialOrName: str) -> Union[YDevice, None]:
        # 1. lookup for an existing YDevice object
        dev: Union[YDevice, None] = self._devsBySn.get(serialOrName)
        if dev:
            return dev
        # 2. scan through white pages for
        # - a known device that has not yet been instantiated
        # - a device by logical name
        found: Union[xdict,None] = self._devRecBySn.get(serialOrName)
        if not found:
            for serial, devrec in self._devRecBySn.items():
                if devrec["logicalName"] == serialOrName:
                    dev = self._devsBySn.get(serial)
                    if dev:
                        return dev
                    found = devrec
                    break
        if not found:
            return None
        # Build the list of function ids by funydx
        funcIds = []
        nfun = 0
        for funrec in found["yellowPages"]:
            funydx: int = funrec["index"]
            if funydx < nfun:
                funcIds[funydx] = funrec["functionId"]
            else:
                while nfun < funydx:
                    funcIds.append(None)
                    nfun += 1
                funcIds.append(funrec["functionId"])
                nfun += 1
        newRef = (self._lastDevRef + 1) & 0xffff
        while self._devsByRef.get(newRef):
            newRef = (newRef + 1) & 0xffff
        dev = YDevice(self, newRef, found, funcIds)
        self._devsByRef[newRef] = dev
        self._devsBySn[dev._serial] = dev
        return dev

    def _plugDevices(self):
        # look if we have previously registered callbacks in the global list
        for func in self._moduleCallbackList:
            hwid = func.get_hwId()
            if hwid:
                dev = self._getDevice(hwid.module)
                dev.callbackDict['name'] = func
                self._moduleCallbackList.remove(func)
                break
        i = len(self._ValueCallbackList) - 1
        while i >= 0:
            func = self._ValueCallbackList[i]
            hwid = func.get_hwId()
            if hwid:
                dev = self._getDevice(hwid.module)
                funydx: int = dev.getFunYdxByFuncId(func._hwId.function)
                if funydx >= 0:
                    dev.callbackDict[funydx] = func
                del self._ValueCallbackList[i]
            i -= 1
        i = len(self._TimedReportCallbackList) - 1
        while i >= 0:
            func = self._TimedReportCallbackList[i]
            hwid = func.get_hwId()
            if hwid:
                dev = self._getDevice(hwid.module)
                funydx: int = dev.getFunYdxByFuncId(func._hwId.function)
                if funydx >= 0:
                    dev.callbackDict[funydx + _TIMED_REPORT_SHIFT] = func
                del self._TimedReportCallbackList[i]
            i -= 1

    def _unplugDevice(self, serial: str) -> None:
        self._Log("HUB: device " + serial + " has been unplugged")
        self._pushUnplugEvent(serial)
        self._forgetDevice(serial)
        # mark device as disconnected
        dev: Union[YDevice,None] = self._devsBySn.get(serial)
        if dev:
            dev.hub = None
        # No need to move callbacks to global list, we keep the YDevice object in case of future reconnection

    # base synchronous handling for YAPI.UpdateDeviceList()
    def _handlePlugEvent(self, evt: YPlugEv) -> Union[Coroutine, None]:
        if evt.eventType == _EVENT_PLUG:
            if self._arrivalCallback:
                return self._arrivalCallback(evt.module)
        elif evt.eventType == _EVENT_UNPLUG:
            if self._removalCallback:
                return self._removalCallback(evt.module)
        elif evt.eventType == _EVENT_CHANGE:
            if self._namechgCallback:
                return self._namechgCallback(evt.module)
        return None

    # base synchronous handling for YAPI.Sleep() and YAPI.HandleEvents()
    def _handleEvent(self, evb: bytearray) -> tuple[Union[YFunction, None], Union[Coroutine, None]]:
        recipient: Union[YFunction, None] = None
        retval: Union[Coroutine, None] = None
        devRef: int = evb[1] * 256 + evb[2]
        ydev: Union[YDevice, None] = self._devsByRef.get(devRef)
        if ydev:
            funydx: int = evb[3]
            if evb[0] == _NOTIFY_NETPKT_FUNCVALYDX:
                # function value ydx (tiny notification)
                recipient: Union[YFunction, None] = ydev.callbackDict.get(funydx)
                if recipient:
                    retval = recipient._valueCallback(recipient, evb[4:].decode('latin-1'))
            elif evb[0] == _NOTIFY_NETPKT_FUNCV2YDX:
                # function value ydx (tiny notification)
                recipient: Union[YFunction, None] = ydev.callbackDict.get(funydx)
                if recipient:
                    rawval: Union[bytearray, None] = self.decodeNetFuncValV2(evb[4:])
                    if rawval:
                        retval = recipient._valueCallback(recipient, self.decodePubVal(rawval[0], rawval, 1, 6))
            elif evb[0] in (_NOTIFY_NETPKT_TIMEVALYDX, _NOTIFY_NETPKT_TIMEAVGYDX, _NOTIFY_NETPKT_TIMEV2YDX):
                if funydx == 0xf:
                    ydev.setLastTimeRef(evb[5:])
                else:
                    recipient: Union[YSensor, None] = ydev.callbackDict.get(funydx + _TIMED_REPORT_SHIFT)
                    if recipient:
                        value: YMeasure = recipient._decodeTimedReport(ydev.lastTimeRef, ydev.lastDuration, evb[4:])
                        retval = recipient._timedReportCallback(recipient, value)
            elif evb[0] == _NOTIFY_NETPKT_CONFCHGYDX:
                recipient: Union[YModule, None] = ydev.callbackDict.get('name')
                if recipient:
                    retval = recipient._confChangeCallback(recipient)
            elif evb[0] == _NOTIFY_NETPKT_NAME:
                # device name change, or arrival
                recipient: Union[YModule, None] = ydev.callbackDict.get('name')
                if recipient:
                    retval = recipient._beaconCallback(recipient, evb[3])
        return recipient, retval

    # common logging code for all callback exceptions
    def _logCbError(self, event: int, recipient, exc: Exception):
        cbname: str = 'callback'
        if event in (_NOTIFY_NETPKT_FUNCVALYDX, _NOTIFY_NETPKT_FUNCV2YDX):
            cbname = '%sCallback "%s"' % ('value', recipient._valueCallback.__name__)
        elif event in (_NOTIFY_NETPKT_TIMEVALYDX, _NOTIFY_NETPKT_TIMEAVGYDX, _NOTIFY_NETPKT_TIMEV2YDX):
            cbname = '%sCallback "%s"' % ('timedReport', recipient._timedReportCallback.__name__)
        elif event == _NOTIFY_NETPKT_CONFCHGYDX:
            cbname = '%sCallback "%s"' % ('configChange', recipient._confChangeCallback.__name__)
        elif event == _NOTIFY_NETPKT_NAME:
            cbname = '%sCallback "%s"' % ('beacon', recipient._beaconCallback.__name__)
        elif event == _EVENT_PLUG:
            cbname = '%sCallback "%s"' % ('arrival', self._arrivalCallback.__name__)
        elif event == _EVENT_UNPLUG:
            cbname = '%sCallback "%s"' % ('removal', self._removalCallback.__name__)
        elif event == _EVENT_CHANGE:
            cbname = '%sCallback "%s"' % ('change', self._namechgCallback.__name__)
        elif event == _EVENT_SSDP_CB:
            cbname = '%sCallback "%s"' % ('SSDP', recipient._callback.__name__)
        rcptname = 'device' if recipient is self else type(recipient).__name__
        self._Log('Error in %s %s' % (rcptname, cbname), True)
        print_exception(exc)

    if not _IS_MICROPYTHON:
        def _ssdpCallback(self, serial: str, urlToRegister: Union[str, None], urlToUnregister: Union[str, None]):
            if urlToRegister is not None:
                if self._HubDiscoveryCallback:
                    self._HubDiscoveryCallback(serial, urlToRegister)
            if (self._apiMode & YAPI.DETECT_NET) != 0:
                if urlToRegister is not None:
                    if urlToUnregister is not None:
                        self.UnregisterHub(urlToUnregister)
                    self.PreregisterHub(urlToRegister)

    def _pushChangeEvent(self, serial) -> Union[YModule, None]:
        if self._namechgCallback:
            module = YModule.FindModuleInContext(self, serial + '.module')
            module.load(self._defaultCacheValidity)
            self._pendingCallbacks.append(YPlugEv(_EVENT_CHANGE, module))
            return module
        return None

    # noinspection PyUnusedLocal
    def _pushPlugEvent(self, serial: str) -> Union[YModule, None]:
        if self._arrivalCallback:
            module = YModule.FindModuleInContext(self, serial + '.module')
            self._pendingCallbacks.append(YPlugEv(_EVENT_PLUG, module))
            return module
        return None

    def _pushUnplugEvent(self, serial: str) -> Union[YModule, None]:
        if self._removalCallback:
            module = YModule.FindModuleInContext(self, serial + '.module')
            self._pendingCallbacks.append(YPlugEv(_EVENT_UNPLUG, module))
            return module
        return None

    def _pushDataEvent(self, decodedEvent: bytearray):
        xbuff: xbytearray = self._eventsBuff
        buflen: int = len(xbuff)
        head: int = self._eventsHead
        tail: int = self._eventsTail
        pending: int = head - tail
        if pending < 0:
            pending += buflen
        # we will prepend event length
        evtlen: int = 1 + len(decodedEvent)
        if evtlen < 3:
            raise ValueError('Invalid decodedEvent buffer')
        while pending + evtlen >= buflen:
            # buffer overflow, drop oldest events
            oldlen: int = self._eventsBuff[tail]
            pending -= oldlen
            tail = (tail + oldlen) % buflen
            self._eventsTail = tail
        # save event length
        self._eventsBuff[head] = evtlen
        head = (head + 1) % buflen
        evtlen -= 1
        # save event itself
        if head + evtlen >= buflen:
            # event is wrapping around buffer
            len1: int = buflen - head
            len2: int = evtlen - len1
            xbuff[head:buflen] = decodedEvent[:len1]
            if len2 > 0:
                xbuff[:len2] = decodedEvent[len1:]
            self._eventsHead = len2
        else:
            # event can be pushed as is
            newhead: int = head + evtlen
            xbuff[head:newhead] = decodedEvent
            self._eventsHead = newhead % buflen

    def _nextDataEvent(self) -> Union[bytearray, None]:
        xbuff: xbytearray = self._eventsBuff
        buflen: int = len(xbuff)
        head: int = self._eventsHead
        tail: int = self._eventsTail
        pending: int = head - tail
        if pending < 0:
            pending += buflen
        if pending == 0:
            return None
        # first byte is the event length
        evtlen = self._eventsBuff[tail]
        self._eventsTail = (tail + evtlen) % buflen
        tail = (tail + 1) % buflen
        evtlen -= 1
        if tail + evtlen > buflen:
            # event is wrapping around buffer
            len1: int = buflen - tail
            len2: int = evtlen - len1
            res = bytearray(len1 + len2)
            res[:len1] = self._eventsBuff[tail:buflen].tobytes()
            res[len1:len1 + len2] = self._eventsBuff[:len2].tobytes()
        else:
            # event can be returned as is
            res = self._eventsBuff[tail:tail + evtlen].tobytes()
        return res

    def _handleNetNotification(self, hub: YGenericHub, evb: memoryview):
        evc: int = evb[0]
        evlen: int = len(evb)
        if evlen >= 3 and _NOTIFY_NETPKT_CONFCHGYDX <= evc <= _NOTIFY_NETPKT_TIMEAVGYDX:
            devydx: int = evb[1] - 65  # from 'A'
            funydx: int = evb[2] - 48  # from '0'
            if (funydx & 64) != 0:
                funydx -= 64
                devydx += 128
            # print("Notification %d for %d:%d" % (evlen, devydx, funydx))
            serial: Union[str, None] = hub.getSerialByYdx(devydx)
            if not serial:
                # print("ignore notification for %d:%d because no serial is found" % (devydx, funydx))
                return
            ydev: Union[YDevice,None] = self._devsBySn.get(serial)
            if not ydev:
                # print("ignore notification for %d:%d ->%s because no device is found" % (devydx, funydx, serial))
                return
            if evc in (_NOTIFY_NETPKT_FUNCVALYDX, _NOTIFY_NETPKT_FUNCV2YDX):
                # print("look notification for %d:%d ->%s " % (devydx, funydx, serial))
                if ydev.callbackDict.get(funydx):
                    devRef: int = ydev.ref
                    decodedEvent = bytearray(len(evb) + 1)
                    decodedEvent[0] = evc
                    decodedEvent[1] = devRef >> 8
                    decodedEvent[2] = devRef & 0xff
                    decodedEvent[3] = funydx
                    decodedEvent[4:] = evb[3:]
                    # print("notification for %d:%d ->%s " % (devydx, funydx, serial))
                    self._pushDataEvent(decodedEvent)
            elif evc in (_NOTIFY_NETPKT_TIMEV2YDX, _NOTIFY_NETPKT_TIMEVALYDX, _NOTIFY_NETPKT_TIMEAVGYDX):
                if ydev.callbackDict.get(funydx + _TIMED_REPORT_SHIFT):
                    devRef: int = ydev.ref
                    tlen: int = (evlen - 3) // 2
                    decodedEvent = bytearray(5 + tlen)
                    decodedEvent[0] = evc
                    decodedEvent[1] = devRef >> 8
                    decodedEvent[2] = devRef & 0xff
                    decodedEvent[3] = funydx
                    if evc == _NOTIFY_NETPKT_TIMEV2YDX:
                        decodedEvent[4] = 2
                    else:
                        decodedEvent[4] = 0 if evc == _NOTIFY_NETPKT_TIMEVALYDX else 1
                    for i in range(tlen):
                        decodedEvent[5 + i] = int(evb[i * 2 + 3:i * 2 + 5].tobytes(), 16)
                    self._pushDataEvent(decodedEvent)
            elif evc == _NOTIFY_NETPKT_DEVLOGYDX:
                ydev.triggerLogPull()
            elif evc == _NOTIFY_NETPKT_CONFCHGYDX:
                if ydev.callbackDict.get("name"):
                    devRef: int = ydev.ref
                    decodedEvent = bytearray(4)
                    decodedEvent[0] = _NOTIFY_NETPKT_CONFCHGYDX
                    decodedEvent[1] = devRef >> 8
                    decodedEvent[2] = devRef & 0xff
                    decodedEvent[3] = 0
                    self._pushDataEvent(decodedEvent)
        elif evlen >= 5 and evb[:4] == b"YN01":
            notype = evb[4]
            if notype in (_NOTIFY_NETPKT_NAME, _NOTIFY_NETPKT_FUNCVAL):
                serial, name, value, *_ = evb[5:].tobytes().decode('latin-1').split(",")
                ydev: Union[YDevice,None] = self._devsBySn.get(serial)
                if not ydev:
                    return
                if notype == _NOTIFY_NETPKT_FUNCVAL:
                    # function value (long notification)
                    funydx: int = ydev.getFunYdxByFuncId(name)
                    if ydev.callbackDict.get(funydx):
                        devRef: int = ydev.ref
                        decodedEvent = bytearray(4 + len(value))
                        decodedEvent[0] = _NOTIFY_NETPKT_FUNCVALYDX
                        decodedEvent[1] = devRef >> 8
                        decodedEvent[2] = devRef & 0xff
                        decodedEvent[3] = funydx
                        if len(value) > 0:
                            decodedEvent[4:] = value.encode('latin-1')
                        self._pushDataEvent(decodedEvent)
                else:
                    # device name change, beacon change (also during arrival)
                    if ydev.callbackDict.get("name"):
                        new_beacon: int = int(value)
                        if ydev._beacon != new_beacon:
                            # no need to save the logical name: name change is handled via updateDeviceList
                            devRef: int = ydev.ref
                            decodedEvent = bytearray(4)
                            decodedEvent[0] = _NOTIFY_NETPKT_NAME
                            decodedEvent[1] = devRef >> 8
                            decodedEvent[2] = devRef & 0xff
                            decodedEvent[3] = new_beacon
                            self._pushDataEvent(decodedEvent)
                            ydev._beacon = new_beacon

    async def _UpdateValueCallbackList(self, func: YFunction, add: bool):
        if func._hwId or await func.isOnline():
            # isOnline always sets _hwId when it succeeds
            ydev: Union[YDevice,None] = self._devsBySn.get(func._hwId.module)
            if ydev is not None:
                funydx: int = ydev.getFunYdxByFuncId(func._hwId.function)
                if funydx >= 0:
                    ydev.callbackDict[funydx] = func if add else None
                return
        if add:
            if not func in self._ValueCallbackList:
                self._ValueCallbackList.append(func)
        else:
            if func in self._ValueCallbackList:
                self._ValueCallbackList.remove(func)

    async def _UpdateTimedReportCallbackList(self, func: YSensor, add: bool):
        if func._hwId or await func.isOnline():
            # isOnline always sets _hwId when it succeeds
            ydev: Union[YDevice,None] = self._devsBySn.get(func._hwId.module)
            if ydev is not None:
                funydx: int = ydev.getFunYdxByFuncId(func._hwId.function)
                if funydx >= 0:
                    if add:
                        ydev.callbackDict[funydx + _TIMED_REPORT_SHIFT] = func
                        ydev.callbackDict[0xf + _TIMED_REPORT_SHIFT] = func
                    else:
                        ydev.callbackDict[funydx + _TIMED_REPORT_SHIFT] = None
                        has_cb: bool = False
                        for f in range(0xf):
                            if ydev.callbackDict[funydx + _TIMED_REPORT_SHIFT] is not None:
                                has_cb = True
                                break
                        if not has_cb:
                            ydev.callbackDict[0xf + _TIMED_REPORT_SHIFT] = None
                return
        if add:
            if not func in self._TimedReportCallbackList:
                self._TimedReportCallbackList.append(func)
        else:
            if func in self._TimedReportCallbackList:
                self._TimedReportCallbackList.remove(func)

    async def _UpdateModuleCallbackList(self, module: YModule, add: bool):
        if module._hwId or await module.isOnline():
            ydev: Union[YDevice,None] = self._devsBySn.get(module._hwId.module)
            if ydev is not None:
                ydev.callbackDict['name'] = module if add else None
                return
        if add:
            if not module in self._moduleCallbackList:
                self._moduleCallbackList.append(module)
        else:
            if module in self._moduleCallbackList:
                self._moduleCallbackList.remove(module)

    async def _addNewHub(self, url: str, desiredState: int, mstimeout: int, errmsg: YRefParam) -> int:
        if errmsg is None:
            errmsg = YRefParam()
        res: int = YAPI.SUCCESS
        if url == "net":
            if _IS_MICROPYTHON:
                return YAPI.NOT_SUPPORTED
            else:
                if self._apiMode & YAPI.DETECT_NET:
                    return YAPI.SUCCESS
                self._apiMode |= YAPI.DETECT_NET
                res = await self.TriggerHubDiscovery(errmsg)
                # preregister localhost anyway
                if desiredState >= _HUB_REGISTERED:
                    desiredState = _HUB_PREREGISTERED
                url = "localhost"
        if url == "usb":
            if not _IS_MICROPYTHON:
                # FIXME: Add native (OS-based) USB support later
                #        For now we use VirtualHub
                self._Log("Warning: USB support not yet available, using VirtualHub on 127.0.0.1", True)
                url = "127.0.0.1"
        parsedUrl = YUrl(url, _YOCTO_DEFAULT_PORT, _YOCTO_DEFAULT_HTTPS_PORT)
        if parsedUrl.host == "callback":
            errmsg.value = "callback mode not supported"
            return YAPI.NOT_SUPPORTED
        # if not yet done, setup an atexit handler to free API if user forget to do it
        if not self._atexit:
            if _IS_MICROPYTHON:
                self._atexit = lambda: asyncio.get_event_loop().run_until_complete(self.FreeAPI())
            else:
                eventloop = asyncio.get_running_loop()
                self._atexit = lambda: _freeAPI(self, eventloop)
            atexit.register(self._atexit)
        # setup requested hub
        hub: Union[YGenericHub, None] = None
        for scanHub in self._hubs:
            if scanHub.isSameHub(url):
                hub = scanHub
                break
        if hub is None:
            if _LOG_LEVEL >= 3:
                self._Log('Registering new hub: ' + parsedUrl.getUrl(YUrl.PROTO))
            hub = YGenericHub(self, parsedUrl)
            if desiredState >= _HUB_PREREGISTERED:
                hub.addKnownURL(parsedUrl)
                self._updateRegisteredHubs(hub, True)
            self._hubs.append(hub)
        else:
            if _LOG_LEVEL >= 3:
                self._Log("Registering existing hub: %s old=%s (%s)" % (parsedUrl.getUrl(YUrl.PROTO), hub._urlInfo.getUrl(YUrl.PROTO), hub._hubSerial))
            if desiredState >= _HUB_PREREGISTERED:
                hub.updateUrl(parsedUrl)
                self._updateRegisteredHubs(hub, True)
        # Trigger hub attachment
        try:
            await hub.attach(desiredState)
            if desiredState == _HUB_REGISTERED:
                res = await hub.waitForConnection(mstimeout, errmsg)
                if res == YAPI.SUCCESS:
                    res = await hub.updateDeviceList(True)
                if res != YAPI.SUCCESS:
                    await hub.detach(res, errmsg.value)
                    self._hubs.remove(hub)
                    self._updateRegisteredHubs(hub, False)
                    hub._release()
            elif desiredState == _HUB_CONNECTED:  # i.e. TestHub
                res = await hub.waitForConnection(mstimeout, errmsg)
        except YAPI_Exception as e:
            errmsg.value = e.errorMessage
            res = e.errorType
            self._updateRegisteredHubs(hub, False)
        if res != YAPI.SUCCESS:
            self._lastErrorType = res
            self._lastErrorMsg = errmsg.value
        return res

    # Check if a given connected YGenericHub should be used as the primary hub object
    # Update the internal list of hubs on the fly if hubs need to be merged
    #
    # This function chooses between equivalent hubs based connection state and precedence.
    # A disconnected hub is NEVER returned in place of a connected hub
    #
    def _getPrimaryHub(self, hub: YGenericHub) -> YGenericHub:
        serial: str = hub.getSerialNumber()
        for otherHub in self._hubs:
            if otherHub == hub:
                continue
            if otherHub.getSerialNumber() == serial:
                if hub._urlInfo.isSecure() or not otherHub._urlInfo.isSecure():
                    if otherHub._currentState >= hub._currentState:
                        # Existing hub is already "better" connected, keep it as primary hub
                        # Remember alias URL and update target state if needed
                        otherHub._inheritFrom(hub)
                        if hub in self._hubs:
                            self._hubs.remove(hub)
                            self._updateRegisteredHubs(hub, False)
                        return otherHub
                # Existing hub is not actively connected, set the new hub as primary
                hub._inheritFrom(otherHub)
                self._hubs.remove(otherHub)
                self._updateRegisteredHubs(otherHub, False)
                return hub
        return hub

    async def _removeHub(self, url: str) -> None:
        for hub in self._hubs:
            if hub.isSameHub(url):
                if hub.isDisconnected():
                    self._hubs.remove(hub)
                    self._updateRegisteredHubs(hub, False)
                    hub._release()
                    return
                # first ensure all set request are done
                await hub.waitForPendingQueries(200)
                if _LOG_LEVEL >= 3:
                    self._Log('Unregistering hub ' + url + ' (' + hub._urlInfo.getUrl(YUrl.PROTO) + ')')
                hub.removeAllDevices()
                if not hub.isDisconnecting():
                    await hub.detach(YAPI.IO_ERROR, 'Hub has been unregistered')
                if _LOG_LEVEL >= 4:
                    before = ticks_ms()
                await hub.waitForDisconnection(500)
                self._hubs.remove(hub)
                self._updateRegisteredHubs(hub, False)
                hub._release()
                if _LOG_LEVEL >= 4:
                    # noinspection PyUnboundLocalVariable
                    self._Log('Disconnected after %d ms' % ticks_diff(ticks_ms(),before))
                return
        if _LOG_LEVEL >= 4:
            self._Log('No hub to Unregister with ' + url)

    async def _updateDeviceList_internal(self, forceupdate: bool, errmsg: YRefParam) -> int:
        try:
            for h in self._hubs:
                await h.updateDeviceList(forceupdate)
            return YAPI.SUCCESS
        except YAPI_Exception as e:
            self._lastErrorType = e.errorType
            self._lastErrorMsg = e.errorMessage
            errmsg.value = e.errorMessage
            return e.errorType

    def _updateRegisteredHubs(self, hub: YGenericHub, add: bool) -> None:
        for h in self._registeredHubs:
            if h == hub:
                if not add:
                    self._registeredHubs.remove(h)
                return
        if add:
            self._registeredHubs.append(hub)

    def _Log(self, message: str, force: bool = False) -> None:
        if self._logCallback:
            self._logCallback(message)
        elif force:
            print(message)

    async def BasicHTTPRequestEx(self, host: str, port: int, usessl: bool, url: str) -> xarray:
        proto: str = "https" if usessl else "http"
        return await self.BasicHTTPRequest("%s://%s:%d/%s" % (proto, host, port, url))

    async def BasicHTTPRequest(self, url: str) -> xarray:
        async with BaseSession(url) as session:
            async with session.get("", timeout=self._networkTimeoutMs / 1000) as response:
                return await response.read()

    def SetDeviceListValidity(self, deviceListValidity: int) -> None:
        """
        Modifies the delay between each forced enumeration of the used YoctoHubs.
        By default, the library performs a full enumeration every 10 seconds.
        To reduce network traffic, you can increase this delay.
        It's particularly useful when a YoctoHub is connected to the GSM network
        where traffic is billed. This parameter doesn't impact modules connected by USB,
        nor the working of module arrival/removal callbacks.
        Note: you must call this function after yInitAPI.

        @param deviceListValidity : nubmer of seconds between each enumeration.
        @noreturn
        """
        self._deviceListValidityMs = deviceListValidity * 1000

    def GetDeviceListValidity(self) -> int:
        """
        Returns the delay between each forced enumeration of the used YoctoHubs.
        Note: you must call this function after yInitAPI.

        @return the number of seconds between each enumeration.
        """
        return self._deviceListValidityMs // 1000

    if not _IS_MICROPYTHON:
        @staticmethod
        def convert_der_to_pem(der_data) -> str:
            base64_data: str = binascii.b2a_base64(der_data, newline=False).decode()
            base64_data_with_newlines: str = "\n".join([base64_data[i:i + 64] for i in range(0, len(base64_data), 64)])
            return "-----BEGIN CERTIFICATE-----\n" + base64_data_with_newlines + "\n-----END CERTIFICATE-----"

    if not _IS_MICROPYTHON:
        async def DownloadHostCertificate(self, url: str, mstimeout: int) -> str:
            """
            Download the TLS/SSL certificate from the hub. This function allows to download a TLS/SSL certificate to add it
            to the list of trusted certificates using the AddTrustedCertificates method.

            @param url : the root URL of the VirtualHub V2 or HTTP server.
            @param mstimeout : the number of milliseconds available to download the certificate.

            @return a string containing the certificate. In case of error, returns a string starting with "error:".
            """
            httpUrl = YUrl(url, _YOCTO_DEFAULT_PORT, _YOCTO_DEFAULT_HTTPS_PORT)
            try:
                if _LOG_LEVEL >= 4:
                    self._Log('Get remote certificate for %s:%d ' % (httpUrl.host, httpUrl.port))
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                reader, writer = await asyncio.open_connection(
                    httpUrl.host,  # use the real host name
                    httpUrl.port,
                    ssl=context
                )
                ssl_info = writer.get_extra_info('ssl_object')
                if sys.version_info[0] == 3 and sys.version_info[1] >= 13:
                    chain = ssl_info.get_unverified_chain()
                    res: str = ""
                    for cert in chain:
                        res += self.convert_der_to_pem(cert) + "\n"
                    return res
                else:
                    cert = ssl_info.getpeercert(binary_form=True)
                    return self.convert_der_to_pem(cert)
            except BaseException as e:
                return "error: " + str(e)

    if not _IS_MICROPYTHON:
        def AddTrustedCertificates(self, certificate: str) -> str:
            """
            Adds a TLS/SSL certificate to the list of trusted certificates. By default, the library
            library will reject TLS/SSL connections to servers whose certificate is not known. This function
            function allows to add a list of known certificates. It is also possible to disable the verification
            using the SetNetworkSecurityOptions method.

            @param certificate : a string containing one or more certificates.

            @return an empty string if the certificate has been added correctly.
                    In case of error, returns a string starting with "error:".
            """
            self._trustedCertificate.append(certificate)
            return ""

    if not _IS_MICROPYTHON:
        def SetTrustedCertificatesList(self, certificatePath: str) -> str:
            """
            Set the path of Certificate Authority file on local filesystem. This method takes as a parameter
            the path of a file containing all certificates in PEM format.
            For technical reasons, only one file can be specified. So if you need to connect to several Hubs
            instances with self-signed certificates, you'll need to use
            a single file containing all the certificates end-to-end. Passing a empty string will restore the
            default settings. This option is only supported by PHP library.

            @param certificatePath : the path of the file containing all certificates in PEM format.

            @return an empty string if the certificate has been added correctly.
                    In case of error, returns a string starting with "error:".
            """
            return "error: not supported"

    def SetNetworkSecurityOptions(self, opts: int) -> str:
        """
        Enables or disables certain TLS/SSL certificate checks.

        @param opts : The options are YAPI.NO_TRUSTED_CA_CHECK,
                YAPI.NO_EXPIRATION_CHECK, YAPI.NO_HOSTNAME_CHECK.

        @return an empty string if the options are taken into account.
                On error, returns a string beginning with "error:".
        """
        self._networkSecurityOptions = opts
        return ""

    def SetNetworkTimeout(self, networkMsTimeout: int) -> None:
        """
        Modifies the network connection delay for yRegisterHub() and yUpdateDeviceList().
        This delay impacts only the YoctoHubs and VirtualHub
        which are accessible through the network. By default, this delay is of 20000 milliseconds,
        but depending on your network you may want to change this delay,
        gor example if your network infrastructure is based on a GSM connection.

        @param networkMsTimeout : the network connection delay in milliseconds.
        @noreturn
        """
        self._networkTimeoutMs = networkMsTimeout

    def GetNetworkTimeout(self) -> int:
        """
        Returns the network connection delay for yRegisterHub() and yUpdateDeviceList().
        This delay impacts only the YoctoHubs and VirtualHub
        which are accessible through the network. By default, this delay is of 20000 milliseconds,
        but depending on your network you may want to change this delay,
        for example if your network infrastructure is based on a GSM connection.

        @return the network connection delay in milliseconds.
        """
        return self._networkTimeoutMs

    # --- (generated code: YAPIContext implementation)
    def SetCacheValidity(self, cacheValidityMs: int) -> None:
        """
        Change the validity period of the data loaded by the library.
        By default, when accessing a module, all the attributes of the
        module functions are automatically kept in cache for the standard
        duration (5 ms). This method can be used to change this standard duration,
        for example in order to reduce network or USB traffic. This parameter
        does not affect value change callbacks
        Note: This function must be called after yInitAPI.

        @param cacheValidityMs : an integer corresponding to the validity attributed to the
                loaded function parameters, in milliseconds.
        @noreturn
        """
        self._defaultCacheValidity = cacheValidityMs

    def GetCacheValidity(self) -> int:
        """
        Returns the validity period of the data loaded by the library.
        This method returns the cache validity of all attributes
        module functions.
        Note: This function must be called after yInitAPI .

        @return an integer corresponding to the validity attributed to the
                loaded function parameters, in milliseconds
        """
        return self._defaultCacheValidity

    def getYHubObj(self, hubref: int) -> YHub:
        obj: Union[YHub, None]
        obj = self._findYHubFromCache(hubref)
        if obj is None:
            obj = YHub(self, hubref)
            self._addYHubToCache(hubref, obj)
        return obj

    async def findYHubFromID(self, id: str) -> Union[YHub, None]:
        rhub: Union[YHub, None]
        rhub = self.nextHubInUseInternal(-1)
        while rhub:
            if rhub.get_serialNumber() == id:
                return rhub
            if rhub.get_registeredUrl() == id:
                return rhub
            rhub = rhub.nextHubInUse()
        return rhub

    # --- (end of generated code: YAPIContext implementation)

    def getGenHub(self, hubref: int) -> Union[YGenericHub, None]:
        for h in self._registeredHubs:
            if h._hubRef == hubref:
                return h
        return None

    async def getAllBootLoaders(self):
        res: list[str] = []
        for hub in self._hubs:
            res += await hub.getBootloaders()
        return res

    async def getHubWithBootloader(self, serial):
        for hub in self._hubs:
            bootloaders: list[str] = await hub.getBootloaders()
            if serial in bootloaders:
                return hub
        return None

    def _addYHubToCache(self, hubref: int, obj: YHub) -> None:
        self._yhub_cache[hubref] = obj

    def _findYHubFromCache(self, hubref: int) -> Union[YHub, None]:
        return self._yhub_cache.get(hubref)

    def nextHubInUseInternal(self, hubref: int) -> Union[YHub, None]:
        nextref: int = max(hubref + 1, 0)
        bestref: int = (1 << 30)
        for h in self._registeredHubs:
            if h._hubRef == nextref:
                return self.getYHubObj(nextref)
            elif nextref < h._hubRef < bestref:
                bestref = h._hubRef
        if bestref < (1 << 30):
            return self.getYHubObj(bestref)
        return None

    def DisableExceptions(self) -> None:
        """
        Disables the use of exceptions to report runtime errors.
        When exceptions are disabled, every function returns a specific
        error value which depends on its type and which is documented in
        this reference manual.
        """
        self._ExceptionsDisabled = True

    def EnableExceptions(self) -> None:
        """
        Re-enables the use of exceptions for runtime error handling.
        Be aware than when exceptions are enabled, every function that fails
        triggers an exception. If the exception is not caught by the user code,
        it either fires the debugger or aborts (i.e. crash) the program.
        """
        self._ExceptionsDisabled = False

    @staticmethod
    def GetAPIVersion() -> str:
        """
        Returns the version identifier for the Yoctopuce library in use.
        The version is a string in the form "Major.Minor.Build",
        for instance "1.01.5535". For languages using an external
        DLL (for instance C#, VisualBasic or Delphi), the character string
        includes as well the DLL version, for instance
        "1.01.5535 (1.01.5439)".

        If you want to verify in your code that the library version is
        compatible with the version that you have used during development,
        verify that the major number is strictly equal and that the minor
        number is greater or equal. The build number is not relevant
        with respect to the library compatibility.

        @return a character string describing the library version.
        """
        return _YOCTO_API_BUILD_VERSION_STR

    async def InitAPI(self, mode: int, errmsg: YRefParam = None) -> int:
        """
        Initializes the Yoctopuce programming library explicitly.
        It is not strictly needed to call yInitAPI(), as the library is
        automatically  initialized when calling yRegisterHub() for the
        first time.

        When YAPI.DETECT_NONE is used as detection mode,
        you must explicitly use yRegisterHub() to point the API to the
        VirtualHub on which your devices are connected before trying to access them.

        @param mode : an integer corresponding to the type of automatic
                device detection to use. Possible values are
                YAPI.DETECT_NONE, YAPI.DETECT_USB, YAPI.DETECT_NET,
                and YAPI.DETECT_ALL.
        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        self._apiMode = mode
        if errmsg is None:
            errmsg = YRefParam()
        if (mode & YAPI.DETECT_NET) != 0:
            if _IS_MICROPYTHON:
                return YAPI.NOT_SUPPORTED
            else:
                res = await self.RegisterHub("net", errmsg)
                if res != YAPI.SUCCESS:
                    return res
        if (mode & YAPI.DETECT_USB) != 0:
            res = await self.RegisterHub("usb", errmsg)
            if res != YAPI.SUCCESS:
                return res
        return YAPI.SUCCESS

    async def FreeAPI(self) -> None:
        """
        Waits for all pending communications with Yoctopuce devices to be
        completed then frees dynamically allocated resources used by
        the Yoctopuce library.

        From an operating system standpoint, it is generally not required to call
        this function since the OS will automatically free allocated resources
        once your program is completed. However, there are two situations when
        you may really want to use that function:

        - Free all dynamically allocated memory blocks in order to
        track a memory leak.

        - Send commands to devices right before the end
        of the program. Since commands are sent in an asynchronous way
        the program could exit before all commands are effectively sent.

        You should not call any other library function after calling
        yFreeAPI(), or your program will crash.
        """
        if self._atexit:
            atexit.unregister(self._atexit)
        if not _IS_MICROPYTHON:
            if (self._apiMode & YAPI.DETECT_NET) != 0:
                await self._ssdp.stop()
        hubs = self._hubs
        self._hubs = []
        completion: list[asyncio.Task] = []
        for hub in hubs:
            if not hub.isDisconnected():
                hub.removeAllDevices()
                if not hub.isDisconnecting():
                    await hub.detach(YAPI.IO_ERROR, 'API shutdown')
                completion.append(hub.create_task(hub.waitForDisconnection(2000)))
        await asyncio.gather(*completion)
        for hub in hubs:
            hub._release()
        for task in self._tasks:
            if not task.done():
                task.cancel()
        self.resetContext()

    async def RegisterHub(self, url: str, errmsg: YRefParam = None) -> int:
        """
        Set up the Yoctopuce library to use modules connected on a given machine. Idealy this
        call will be made once at the begining of your application.  The
        parameter will determine how the API will work. Use the following values:

        <b>usb</b>: When the usb keyword is used, the API will work with
        devices connected directly to the USB bus. Some programming languages such a JavaScript,
        PHP, and Java don't provide direct access to USB hardware, so usb will
        not work with these. In this case, use a VirtualHub or a networked YoctoHub (see below).

        <b><i>x.x.x.x</i></b> or <b><i>hostname</i></b>: The API will use the devices connected to the
        host with the given IP address or hostname. That host can be a regular computer
        running a <i>native VirtualHub</i>, a <i>VirtualHub for web</i> hosted on a server,
        or a networked YoctoHub such as YoctoHub-Ethernet or
        YoctoHub-Wireless. If you want to use the VirtualHub running on you local
        computer, use the IP address 127.0.0.1. If the given IP is unresponsive, yRegisterHub
        will not return until a time-out defined by ySetNetworkTimeout has elapsed.
        However, it is possible to preventively test a connection  with yTestHub.
        If you cannot afford a network time-out, you can use the non-blocking yPregisterHub
        function that will establish the connection as soon as it is available.


        <b>callback</b>: that keyword make the API run in "<i>HTTP Callback</i>" mode.
        This a special mode allowing to take control of Yoctopuce devices
        through a NAT filter when using a VirtualHub or a networked YoctoHub. You only
        need to configure your hub to call your server script on a regular basis.
        This mode is currently available for PHP and Node.JS only.

        Be aware that only one application can use direct USB access at a
        given time on a machine. Multiple access would cause conflicts
        while trying to access the USB modules. In particular, this means
        that you must stop the VirtualHub software before starting
        an application that uses direct USB access. The workaround
        for this limitation is to set up the library to use the VirtualHub
        rather than direct USB access.

        If access control has been activated on the hub, virtual or not, you want to
        reach, the URL parameter should look like:

        http://username:password@address:port

        You can call <i>RegisterHub</i> several times to connect to several machines. On
        the other hand, it is useless and even counterproductive to call <i>RegisterHub</i>
        with to same address multiple times during the life of the application.

        @param url : a string containing either "usb","callback" or the
                root URL of the hub to monitor
        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        if _LOG_LEVEL >= 3:
            self._Log("Registering hub: " + url)
        if errmsg is None:
            errmsg = YRefParam()
        return await self._addNewHub(url, _HUB_REGISTERED, self._networkTimeoutMs, errmsg)

    async def PreregisterHub(self, url: str, errmsg: YRefParam = None) -> int:
        """
        Fault-tolerant alternative to yRegisterHub(). This function has the same
        purpose and same arguments as yRegisterHub(), but does not trigger
        an error when the selected hub is not available at the time of the function call.
        If the connexion cannot be established immediately, a background task will automatically
        perform periodic retries. This makes it possible to register a network hub independently of the current
        connectivity, and to try to contact it only when a device is actively needed.

        @param url : a string containing either "usb","callback" or the
                root URL of the hub to monitor
        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        if _LOG_LEVEL >= 3:
            self._Log("Preregistering hub: " + url)
        if errmsg is None:
            errmsg = YRefParam()
        return await self._addNewHub(url, _HUB_PREREGISTERED, self._networkTimeoutMs, errmsg)

    async def UnregisterHub(self, url: str):
        """
        Set up the Yoctopuce library to no more use modules connected on a previously
        registered machine with RegisterHub.

        @param url : a string containing either "usb" or the
                root URL of the hub to monitor
        """
        if not _IS_MICROPYTHON:
            if url == "net":
                self._apiMode &= ~YAPI.DETECT_NET
                return
        return await self._removeHub(url)

    async def TestHub(self, url: str, mstimeout: int, errmsg: YRefParam = None) -> int:
        """
        Test if the hub is reachable. This method do not register the hub, it only test if the
        hub is usable. The url parameter follow the same convention as the yRegisterHub
        method. This method is useful to verify the authentication parameters for a hub. It
        is possible to force this method to return after mstimeout milliseconds.

        @param url : a string containing either "usb","callback" or the
                root URL of the hub to monitor
        @param mstimeout : the number of millisecond available to test the connection.
        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        if errmsg is None:
            errmsg = YRefParam()
        if not _IS_MICROPYTHON:
            if url == "net":
                res = YAPI.INVALID_ARGUMENT
                errmsg.value = "TestHub requires a specific address"
                self._lastErrorType = res
                self._lastErrorMsg = errmsg.value
                return res
        return await self._addNewHub(url, _HUB_CONNECTED, mstimeout, errmsg)

    async def UpdateDeviceList(self, errmsg: YRefParam = None) -> int:
        """
        Triggers a (re)detection of connected Yoctopuce modules.
        The library searches the machines or USB ports previously registered using
        yRegisterHub(), and invokes any user-defined callback function
        in case a change in the list of connected devices is detected.

        This function can be called as frequently as desired to refresh the device list
        and to make the application aware of hot-plug events. However, since device
        detection is quite a heavy process, UpdateDeviceList shouldn't be called more
        than once every two seconds.

        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        if errmsg is None:
            errmsg = YRefParam()
        res: int = await self._updateDeviceList_internal(False, errmsg)
        if res != YAPI.SUCCESS:
            return res
        # after processing all hubs, invoke pending callbacks if required
        nbEvents = len(self._pendingCallbacks)
        for i in range(nbEvents):
            evt: YPlugEv = self._pendingCallbacks[i]
            try:
                retval: Union[Coroutine, None] = self._handlePlugEvent(evt)
                if asyncio.iscoroutine(retval):
                    await retval
            # noinspection PyBroadException
            except Exception as exc:
                self._logCbError(evt.eventType, self, exc)
        del self._pendingCallbacks[:nbEvents]
        return YAPI.SUCCESS

    async def HandleEvents(self, errmsg: YRefParam = None) -> int:
        """
        Maintains the device-to-library communication channel.
        If your program includes significant loops, you may want to include
        a call to this function to make sure that the library takes care of
        the information pushed by the modules on the communication channels.
        This is not strictly necessary, but it may improve the reactivity
        of the library for the following commands.

        This function may signal an error in case there is a communication problem
        while contacting a module.

        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        if errmsg is None:
            errmsg = YRefParam()
        try:
            evb: Union[bytearray, None] = self._nextDataEvent()
            # Handle ALL pending events
            while evb:
                recipient = None
                try:
                    recipient, retval = self._handleEvent(evb)
                    if asyncio.iscoroutine(retval):
                        await retval
                # noinspection PyBroadException
                except Exception as exc:
                    self._logCbError(evb[0], recipient, exc)
                evb = self._nextDataEvent()
        except YAPI_Exception as e:
            errmsg.value = e.errorMessage
            return e.errorType
        return YAPI.SUCCESS

    async def Sleep(self, ms_duration: int, errmsg: YRefParam = None) -> int:
        """
        Pauses the execution flow for a specified duration.
        This function implements a passive waiting loop, meaning that it does not
        consume CPU cycles significantly. The processor is left available for
        other threads and processes. During the pause, the library nevertheless
        reads from time to time information from the Yoctopuce modules by
        calling yHandleEvents(), in order to stay up-to-date.

        This function may signal an error in case there is a communication problem
        while contacting a module.

        @param ms_duration : an integer corresponding to the duration of the pause,
                in milliseconds.
        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.

        On failure returns a negative error code.
        """
        if errmsg is None:
            errmsg = YRefParam()
        try:
            evb: Union[bytearray, None] = self._nextDataEvent()
            endTicks: int = ticks_add(ticks_ms(), ms_duration)
            remaining: int = 1
            # Handle as many pending events as possible in given time (at least one)
            while remaining > 0:
                if evb:
                    # handle one event
                    recipient = None
                    try:
                        recipient, retval = self._handleEvent(evb)
                        if asyncio.iscoroutine(retval):
                            await retval
                    # noinspection PyBroadException
                    except Exception as exc:
                        self._logCbError(evb[0], recipient, exc)
                remaining = ticks_diff(endTicks, ticks_ms())
                if remaining <= 0:
                    # time expired during event processing
                    return YAPI.SUCCESS
                # get next event
                evb = self._nextDataEvent()
                if not evb:
                    if _IS_MICROPYTHON:
                        await asyncio.sleep_ms(min(remaining, 10))  # noqa
                    else:
                        await asyncio.sleep(min(remaining, 10) / 1000.0)
                    remaining = ticks_diff(endTicks, ticks_ms())
        except YAPI_Exception as e:
            errmsg.value = e.errorMessage
            return e.errorType
        return YAPI.SUCCESS

    async def TriggerHubDiscovery(self, errmsg: YRefParam = None) -> int:
        """
        Force a hub discovery, if a callback as been registered with yRegisterHubDiscoveryCallback it
        will be called for each net work hub that will respond to the discovery.

        @param errmsg : a string passed by reference to receive any error message.

        @return YAPI.SUCCESS when the call succeeds.
                On failure returns a negative error code.
        """
        if errmsg is None:
            errmsg = YRefParam()
        if _IS_MICROPYTHON:
            errmsg.value = "Discovery not supported yet in MicroPython"
            return YAPI.NOT_SUPPORTED
        else:
            try:
                if self._ssdp is None:
                    self._ssdp = YSSDP(self)  # type: ignore
                await self._ssdp.start(self._ssdpCallback)
            except YAPI_Exception as ex:
                errmsg.value = ex.errorMessage
                return ex.errorType
            return YAPI.SUCCESS

    @staticmethod
    def GetTickCount() -> int:
        """
        Returns the current value of a monotone millisecond-based time counter.
        This counter can be used to compute delays in relation with
        Yoctopuce devices, which also uses the millisecond as timebase.

        @return a long integer corresponding to the millisecond counter.
        """
        if _IS_MICROPYTHON:
            return time.time_ms()  # noqa
        else:
            return round(time.time() * 1000)

    @staticmethod
    def CheckLogicalName(name: str) -> bool:
        """
        Checks if a given string is valid as logical name for a module or a function.
        A valid logical name has a maximum of 19 characters, all among
        A...Z, a...z, 0...9, _, and -.
        If you try to configure a logical name with an incorrect string,
        the invalid characters are ignored.

        @param name : a string containing the name to check.

        @return true if the name is valid, false otherwise.
        """
        if not isinstance(name, str):
            return False
        if not name:
            return True
        if len(name) > 19:
            return False
        return re.match('^[A-Za-z0-9_-]*$', name) is not None

    async def RegisterDeviceArrivalCallback(self, arrivalCallback: YDeviceUpdateCallback):
        """
        Register a callback function, to be called each time
        a device is plugged. This callback will be invoked while yUpdateDeviceList
        is running. You will have to call this function on a regular basis.

        @param arrivalCallback : a procedure taking a YModule parameter, or None
                to unregister a previously registered  callback.
        """
        self._arrivalCallback = arrivalCallback
        if arrivalCallback is not None:
            mod: YModule = YModule.FirstModule()
            while mod is not None:
                if await mod.isOnline():
                    self._pendingCallbacks.append(YPlugEv(_EVENT_PLUG, mod))
                mod = mod.nextModule()
        return 0

    def RegisterDeviceChangeCallback(self, changeCallback: YDeviceUpdateCallback):
        self._namechgCallback = changeCallback

    async def RegisterDeviceRemovalCallback(self, removalCallback: YDeviceUpdateCallback):
        """
        Register a callback function, to be called each time
        a device is unplugged. This callback will be invoked while yUpdateDeviceList
        is running. You will have to call this function on a regular basis.

        @param removalCallback : a procedure taking a YModule parameter, or None
                to unregister a previously registered  callback.
        """
        self._removalCallback = removalCallback

    async def RegisterHubDiscoveryCallback(self, hubDiscoveryCallback):
        """
        Register a callback function, to be called each time an Network Hub send
        an SSDP message. The callback has two string parameter, the first one
        contain the serial number of the hub and the second contain the URL of the
        network hub (this URL can be passed to RegisterHub). This callback will be invoked
        while yUpdateDeviceList is running. You will have to call this function on a regular basis.

        @param hubDiscoveryCallback : a procedure taking two string parameter, the serial
                number and the hub URL. Use None to unregister a previously registered  callback.
        """
        if not _IS_MICROPYTHON:
            self._HubDiscoveryCallback = hubDiscoveryCallback
            try:
                await self.TriggerHubDiscovery()
            except YAPI_Exception:
                pass

    def RegisterLogFunction(self, logfun: YLogCallback):
        """
        Registers a log callback function. This callback will be called each time
        the API have something to say. Quite useful to debug the API.

        @param logfun : a procedure taking a string parameter, or None
                to unregister a previously registered  callback.
        """
        self._logCallback = logfun


YAPI: YAPIContext = YAPIContext()


# --- (generated code: YHub class start)
# noinspection PyProtectedMember
class YHub:
    # --- (end of generated code: YHub class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YHub return codes)
        TRYING: Final[int] = 1
        CONNECTED: Final[int] = 2
        RECONNECTING: Final[int] = 3
        ABORTED: Final[int] = 4
        UNREGISTERED: Final[int] = 5
        # --- (end of generated code: YHub return codes)

    # --- (generated code: YHub attributes)
    _ctx: YAPIContext
    _hubref: int
    _userData: Any

    # --- (end of generated code: YHub attributes)

    def __init__(self, yctx: YAPIContext, hubref: int):
        self._ctx = yctx
        self._hubref = hubref

    def _imm_getStrAttr(self, attrName: str) -> str:
        hub: YGenericHub = self._ctx.getGenHub(self._hubref)
        if hub is None:
            return ""
        if attrName == "registeredUrl":
            return hub._urlInfo.originalURL
        if attrName == "connectionUrl":
            if hub._hubEngine:
                return hub._hubEngine._base.getUrl(YUrl.PROTO | YUrl.ENDSLASH)
        if attrName == "serialNumber":
            return hub.getSerialNumber()
        elif attrName == "errorType":
            return hub.lastErrorMsg
        return ""

    def _imm_getIntAttr(self, attrName: str) -> int:
        hub: YGenericHub = self._ctx.getGenHub(self._hubref)
        if attrName == "isInUse":
            return 0 if hub is None else 1
        if attrName == "connectionState":
            if hub is None:
                return YHub.UNREGISTERED
            return hub.get_connectionState()
        if hub is None:
            return -1
        if attrName == "isOnline":
            return 1 if hub.isOnline() else 0
        elif attrName == "networkTimeout":
            return hub.networkTimeout
        elif attrName == "errorType":
            return hub.lastErrorType
        else:
            return -1

    async def _getIntAttr(self, attrName: str) -> int:
        if attrName == "isReadOnly":
            hub: YGenericHub = self._ctx.getGenHub(self._hubref)
            if hub is None:
                return -1
            return 1 if await hub.isReadOnly() else 0
        return self._imm_getIntAttr(attrName)

    def _imm_setIntAttr(self, attrName: str, value: int):
        hub: YGenericHub = self._ctx.getGenHub(self._hubref)
        if hub and attrName == "networkTimeout":
            hub.networkTimeout = value

    def get_knownUrls(self) -> list[str]:
        """
        Returns all known URLs that have been used to register this hub.
        URLs are pointing to the same hub when the devices connected
        are sharing the same serial number.
        """
        hub: YGenericHub = self._ctx.getGenHub(self._hubref)
        if hub:
            return hub._knownUrls
        return []

    # --- (generated code: YHub implementation)
    def get_registeredUrl(self) -> str:
        """
        Returns the URL that has been used first to register this hub.
        """
        return self._imm_getStrAttr("registeredUrl")

    def get_connectionUrl(self) -> str:
        """
        Returns the URL currently in use to communicate with this hub.
        """
        return self._imm_getStrAttr("connectionUrl")

    def get_connectionState(self) -> int:
        """
        Returns the state of the connection with this hub. (TRYING, CONNECTED, RECONNECTING, ABORTED, UNREGISTERED)
        """
        return self._imm_getIntAttr("connectionState")

    def get_serialNumber(self) -> str:
        """
        Returns the hub serial number, if the hub was already connected once.
        """
        return self._imm_getStrAttr("serialNumber")

    async def isInUse(self) -> bool:
        """
        Tells if this hub is still registered within the API.

        @return true if the hub has not been unregistered.
        """
        return await self._getIntAttr("isInUse") > 0

    async def isOnline(self) -> bool:
        """
        Tells if there is an active communication channel with this hub.

        @return true if the hub is currently connected.
        """
        return await self._getIntAttr("isOnline") > 0

    async def isReadOnly(self) -> bool:
        """
        Tells if write access on this hub is blocked. Return true if it
        is not possible to change attributes on this hub

        @return true if it is not possible to change attributes on this hub.
        """
        return await self._getIntAttr("isReadOnly") > 0

    def set_networkTimeout(self, networkMsTimeout: int) -> None:
        """
        Modifies tthe network connection delay for this hub.
        The default value is inherited from ySetNetworkTimeout
        at the time when the hub is registered, but it can be updated
        afterward for each specific hub if necessary.

        @param networkMsTimeout : the network connection delay in milliseconds.
        @noreturn
        """
        self._imm_setIntAttr("networkTimeout", networkMsTimeout)

    def get_networkTimeout(self) -> int:
        """
        Returns the network connection delay for this hub.
        The default value is inherited from ySetNetworkTimeout
        at the time when the hub is registered, but it can be updated
        afterward for each specific hub if necessary.

        @return the network connection delay in milliseconds.
        """
        return self._imm_getIntAttr("networkTimeout")

    def get_errorType(self) -> int:
        """
        Returns the numerical error code of the latest error with the hub.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a number corresponding to the code of the latest error that occurred while
                using the hub object
        """
        return self._imm_getIntAttr("errorType")

    def get_errorMessage(self) -> str:
        """
        Returns the error message of the latest error with the hub.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a string corresponding to the latest error message that occured while
                using the hub object
        """
        return self._imm_getStrAttr("errorMessage")

    def get_userData(self) -> Any:
        """
        Returns the value of the userData attribute, as previously stored
        using method set_userData.
        This attribute is never touched directly by the API, and is at
        disposal of the caller to store a context.

        @return the object stored previously by the caller.
        """
        return self._userData

    def set_userData(self, data: Any) -> None:
        """
        Stores a user context provided as argument in the userData
        attribute of the function.
        This attribute is never touched by the API, and is at
        disposal of the caller to store a context.

        @param data : any kind of object to be stored
        @noreturn
        """
        self._userData = data

    @staticmethod
    def FirstHubInUse() -> Union[YHub, None]:
        """
        Starts the enumeration of hubs currently in use by the API.
        Use the method YHub.nextHubInUse() to iterate on the
        next hubs.

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return YAPI.nextHubInUseInternal(-1)

    @staticmethod
    def FirstHubInUseInContext(yctx: YAPIContext) -> Union[YHub, None]:
        """
        Starts the enumeration of hubs currently in use by the API
        in a given YAPI context.
        Use the method YHub.nextHubInUse() to iterate on the
        next hubs.

        @param yctx : a YAPI context

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return yctx.nextHubInUseInternal(-1)

    @staticmethod
    async def FindHubInUse(url: str) -> Union[YHub, None]:
        """
        Retrieves hub for a given identifier. The identifier can be the URL or the
        serial of the hub.

        @param url : The url or serial of the hub.

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return await YAPI.findYHubFromID(url)

    @staticmethod
    async def FindHubInUseInContext(yctx: YAPIContext, url: str) -> Union[YHub, None]:
        """
        Retrieves hub for a given identifier in a given YAPI context. The identifier can be the URL or the
        serial of the hub.

        @param yctx : a YAPI context
        @param url : The url or serial of the hub.

        @return a pointer to a YHub object, corresponding to
                the first hub currently in use by the API, or a
                None pointer if none has been registered.
        """
        return await yctx.findYHubFromID(url)

    def nextHubInUse(self) -> Union[YHub, None]:
        """
        Continues the module enumeration started using YHub.FirstHubInUse().
        Caution: You can't make any assumption about the order of returned hubs.

        @return a pointer to a YHub object, corresponding to
                the next hub currently in use, or a None pointer
                if there are no more hubs to enumerate.
        """
        return self._ctx.nextHubInUseInternal(self._hubref)

    # --- (end of generated code: YHub implementation)


#################################################################################
#                                                                               #
#             Yoctopuce-style Future-like objects, based on Event               #
#             (Futures are currently not available on micropython)              #
#                                                                               #
#################################################################################

class YFuture:
    errorType: int
    errorMsg: str
    _event: asyncio.Event
    _result: Any

    def __init__(self):
        self.errorType = YAPI.SUCCESS
        self.errorMsg = ''
        self._event = asyncio.Event()
        self._result = None

    def set_result(self, errType: int, errMsg: str, result: any = None) -> None:
        if self._event.is_set():
            raise RuntimeError("Future is already done")
        self.errorType = errType
        self.errorMsg = errMsg
        self._result = result
        self._event.set()

    def set_exception(self, exception: Exception) -> None:
        if self._event.is_set():
            raise RuntimeError("Future is already done")
        self._result = exception
        self._event.set()

    def result(self) -> Any:
        if not self._event.is_set():
            raise RuntimeError("Result is not ready")
        if isinstance(self._result, Exception):
            raise self._result
        return self._result

    def done(self) -> bool:
        return self._event.is_set()

    async def ready(self) -> YFuture:
        await self._event.wait()
        return self


#################################################################################
#                                                                               #
#                    YRequest, YHubEngine, YGenericHub, YHub                    #
#                                                                               #
#################################################################################

YTimer = Union[asyncio.Task, None]


# noinspection PyProtectedMember
class YRequest(ClientResponse):
    devNext: Union[YRequest, None]  # pointer to next request in device-specific linked list
    hubNext: Union[YRequest, None]  # pointer to next request in hub tcp channel-specific list
    _wsHdr: Union[bytes, None]

    def __init__(self, method: str, url: str, headers: dict, timeout: int, payload: Union[xarray, None]):
        if headers and payload:
            # our payload is always form-encoded, with Content-Type and Content-Length
            # headers included at the beginning of the payload buffer
            if headers.get('Content-Length'):
                del headers['Content-Length']
            if headers.get('Content-Type'):
                del headers['Content-Type']
        super().__init__(method, url, headers, timeout, payload)
        self.devNext = None
        self.hubNext = None
        self._wsHdr = None

    def __repr__(self) -> str:
        return "<%s %d %s%sdone>" % ('YRequest', self.status, "" if self._async is None else "async ", "" if self._done.is_set() else "not ")

    async def ready(self) -> None:
        """
        Wait for the request to be sent and the response header to be fully received.
        This method is equivalent to entering the async context of the request.
        """
        if self.status >= 0:
            return
        if self._chan:
            self._chan.keepRunning()
        await self._ready.wait()
        if self._except:
            if isinstance(self._except, YAPI_Exception):
                raise self._except
            raise YAPI_Exception(YAPI.IO_ERROR, repr(self._except))

    # provide a preallocated buffer for this request
    def setBuff(self, buff: xbytearray):
        self._buff = buff

    # mark request for asynchronous completion
    def setAsync(self):
        self._async = -1

    def wsPrepHeaders(self):
        if self.hasData():
            self._wsHdr = ("%s %s\r\n" % (self._method, self._target)).encode()
        else:
            self._wsHdr = ("%s %s\r\n\r\n" % (self._method, self._target)).encode()

    def getWsHeaderView(self, pos: int, maxLen: int) -> bytes:
        if maxLen >= len(self._wsHdr) and not pos:
            return self._wsHdr
        endPos = min(len(self._wsHdr), pos + maxLen)
        return self._wsHdr[pos:endPos]


# noinspection PyProtectedMember
class YHubEngine(BaseSession):
    _hub: YGenericHub

    # Note: _runtime_urlInfo is available as _base

    def __init__(self, hub: YGenericHub, runtimeUrl: YUrl, proto: str):
        super().__init__(runtimeUrl, version=proto)
        self._hub = hub

    def request(self, method: str, url: Union[YUrl, str] = "", *,
                params: Union[Pairs, None] = None,
                data: Union[xarray, bytes, None] = None,
                json: Any = None,
                headers: Union[Pairs, None] = None,
                ssl: Union[SSLContext, bool, None] = None,
                auth: Union[BaseAuth, None] = None,
                version: Union[str, None] = None,
                timeout: float = 300,
                channel: Union[int, None] = -1,
                as_cls: Type[AkaClientResponse] = ClientResponse) -> AkaClientResponse:
        # subdomain is already handled by BaseSession
        if ssl is None:
            ssl_ctx = self._hub._getSslContex()
        else:
            ssl_ctx = ssl
        return super().request(method, url, params=params, data=data, json=json, headers=headers, ssl=ssl_ctx, auth=auth, version=version, timeout=timeout, channel=channel, as_cls=as_cls)

    # Defer all task creation to the hub, for better tracking
    def create_task(self, coro: Coroutine) -> asyncio.Task:
        return self._hub.create_task(coro)

    # Common HTTP status check for engines
    def _checkStatus(self, response: BaseResponse, tryOpenID: str) -> bool:
        # We assume automatic handling by aiohttp for
        # - status 301, 302, 307, 308 (redirect)
        # - status 401/204 (authentication), if provided properly
        status = response.status
        if status != 200 and status != 304 and status != 101:
            if status == 401 or status == 204:
                if self._auth is not None:
                    self._auth.login(response)
                # Authentication failed
                self._hub._commonDisconnect(tryOpenID, YAPI.UNAUTHORIZED, 'Unauthorized access')
            if status == 404:
                # Path not found
                self._hub._commonDisconnect(tryOpenID, YAPI.FILE_NOT_FOUND, 'not.byn not found')
            self._hub._disconnectNow()
            return False
        return True

    async def reconnectEngine(self, tryOpenID: str) -> None:
        """
        Attempt to establish a connection to the hub asynchronously.

        On success, this method should call self.signalHubConnected()
        On temporary failure, this method should call self._signalHubDisconnected()
        On fatal failure, this method should call self._commonDisconnect()
        """
        # This method must be redefined by subclasses
        raise NotImplementedError

    def disconnectEngineNow(self, connID: str = ''):
        """
        Abort communication channel immediately

        If a connectionID is passed as argument, only abort the
        communication channel if the ID matched current connection
        """
        # This method must be redefined by subclasses
        raise NotImplementedError

    def makeRequest(self, method: str, rel_url: str, body: Union[xarray, None], msTimeout: int) -> YRequest:
        """
        Prepare a request to be sent to the hub, but do not send it yet.
        The method will be sent using method sendRequest() below.
        """
        # This method must be redefined by subclasses
        raise NotImplementedError

    def _sendRequest(self, baseUrl: YUrl, request: ClientResponse, *,
                     ssl: Union[SSLContext, bool, None] = None,
                     channel: int = -1):
        if ssl is None:
            ssl_ctx = self._hub._getSslContex()
        else:
            ssl_ctx = ssl
        super()._sendRequest(baseUrl, request, ssl=ssl_ctx, channel=channel)

    async def sendRequest(self, request: YRequest, tcpchan: int) -> ByteArrayLike:
        """
        Attempt to schedule the request passed as argument and to return the result
        If the request is async, the method should return None as soon as
        the async request has been sent to the hub
        """
        # This method must be redefined by subclasses
        raise NotImplementedError

    async def waitForPendingQueries(self) -> None:
        # This method must be redefined by subclasses
        raise NotImplementedError


# hub security modes
_HUBMODE_LEGACY: Final[int] = 0
_HUBMODE_MIXED: Final[int] = 1
_HUBMODE_SECURE: Final[int] = 2
_HUBMODE_UNKNOWN: Final[int] = 3


# noinspection PyProtectedMember
class YGenericHub:
    _GlobalCnt: int = 0
    _hubRef: int  # unique identifier for each hub created
    _hubEngine: Union[YHubEngine, None]  # connection handler
    _yapi: YAPIContext
    lastErrorType: int
    lastErrorMsg: str
    # key hub state variables
    _urlInfo: YUrl  # structure that describe the original URL of the hub
    _portInfo: list[tuple[str, int]]  # recommended protocol/ports
    _isVhub4web: bool  # host is a true web server
    _hubSerial: str  # the hub true serial number, as obtained from the hub itself
    _serialByYdx: dict[int, str]  # serials by hub-specific devYdx
    # state variables to establish connection
    _currentState: int
    _targetState: int
    _currentConnID: str  # ConnID of the current/next connection attempt
    _connResolvers: list[YFuture]  # Futures to notify permanent state changes
    _disconnResolvers: list[YFuture]  # Futures to notify disconnects
    _retryDelay: int  # delay before reconnecting in case of error: initially 15ms
    _reconnTimer: YTimer  # timer for retrying connect
    _rwAccess: Union[bool, None]  # None until hub has been tested for rw-access
    _tasks: list[asyncio.Task]  # List of asyncio background task objects
    # variables for special "Test Hub trying" state
    _keepTryingUntil: int  # tick_ms of end of all TestHub requests and return to detached
    _keepTryingTimer: YTimer  # timer for detaching at end of TestHub
    # state variable to handle connected state
    networkTimeout: int  # hub-specific timeout for detecting stalled connections
    _lastPing: int  # timestamp of last notification received
    _isNotifWorking: bool  # true if we are receiving valid notification
    _updateDevListStarted: int  # time_ms stamp of start of updateDevList when in progress
    _devListExpires: int  # timestamp of next useful updateDeviceList
    notifPos: int  # current absolute position in hub notification stream
    _firstArrivalCallback: bool  # this is the first connection to the hub
    _knownUrls: list[str]  # the list of url that can be used for this hub
    _sslContext: Union[SSLContext | None]
    _hubMode: int
    _logPullList: list[YDevice]

    def __init__(self, yctx: YAPIContext, urlInfo: YUrl):
        YGenericHub._GlobalCnt += 1
        self._hubRef = YGenericHub._GlobalCnt
        self._hubEngine = None
        self._yapi = yctx
        self.lastErrorType = YAPI.IO_ERROR
        self.lastErrorMsg = 'New hub'
        self._urlInfo: YUrl = urlInfo
        self._portInfo = []
        self._isVhub4web = False
        self._hubSerial = ""
        self._serialByYdx = dict()
        self._currentState = _HUB_UNKNOWN
        self._targetState = _HUB_DETACHED
        self._currentConnID = ''
        self._connResolvers = []
        self._disconnResolvers = []
        self._retryDelay = 15
        self._reconnTimer = None
        self._rwAccess = None
        self._tasks = []
        self._keepTryingUntil = 0
        self._keepTryingTimer = None
        self.networkTimeout = yctx.GetNetworkTimeout()
        self._lastPing = 0
        self._isNotifWorking = False
        self._updateDevListStarted = 0
        self._devListExpires = 0
        self.notifPos = -1
        self._firstArrivalCallback = True
        self._knownUrls = []
        self._sslContext = None
        self._hubMode = _HUBMODE_SECURE
        self._logPullList = []

    def _release(self):
        if self._reconnTimer:
            self._reconnTimer.cancel()
        if self._keepTryingTimer:
            self._keepTryingTimer.cancel()
        self._serialByYdx = dict()
        self._knownUrls = []

    # YGenericHub._throw always throw an exception
    def _throw(self, errType: int, errMsg: str):
        self.lastErrorType = errType
        self.lastErrorMsg = errMsg
        raise YAPI_Exception(errType, errMsg)

    def getSerialNumber(self) -> str:
        return self._hubSerial

    def updateUrl(self, urlInfo: YUrl):
        self.addKnownURL(urlInfo)
        self._urlInfo = urlInfo
        if _LOG_LEVEL >= 4:
            if self._currentState < _HUB_CONNECTING:
                self._yapi._Log("Updating auth credentials for " + self._urlInfo.getUrl(YUrl.PROTO))

    def isFirstArrivalCallback(self) -> bool:
        return self._firstArrivalCallback

    def setFirstArrivalCallback(self, isFirst: bool) -> None:
        self._firstArrivalCallback = isFirst

    def _setState(self, newState: int) -> None:
        self._currentState = newState

    def _setTargetState(self, newState: int) -> None:
        self._targetState = newState

    def isDisconnecting(self) -> bool:
        return self._targetState <= _HUB_DETACHED

    def isDisconnected(self) -> bool:
        return self._targetState <= _HUB_DETACHED and self._currentState <= _HUB_DETACHED

    def isPreOrRegistered(self) -> bool:
        return self._targetState >= _HUB_PREREGISTERED

    def get_connectionState(self):
        if self.isOnline():
            return YHub.CONNECTED
        if self.isDisconnecting():
            return YHub.ABORTED
        if self._lastPing > 0:
            return YHub.RECONNECTING
        return YHub.TRYING

    def isOnline(self) -> bool:
        return ticks_diff(ticks_ms(), self._lastPing) < self.networkTimeout

    def getSerialByYdx(self, devydx: int) -> Union[str, None]:
        return self._serialByYdx.get(devydx)

    def addKnownURL(self, urlInfo: YUrl) -> None:
        orgUrl = urlInfo.originalURL
        if not orgUrl in self._knownUrls:
            self._knownUrls.append(orgUrl)

    def isSameHub(self, url: str) -> bool:
        for ku in self._knownUrls:
            if url == ku:
                return True
        stdUrl = YUrl(url, _YOCTO_DEFAULT_PORT, _YOCTO_DEFAULT_HTTPS_PORT).getUrl(0)
        return stdUrl == self._urlInfo.getUrl(0)

    def _inheritFrom(self, otherHub: YGenericHub) -> None:
        if _LOG_LEVEL >= 4:
            self._yapi._Log("---- hub %s(%s) inheritFrom %s(%s)" % (self._hubSerial, self._urlInfo.getUrl(YUrl.PROTO), otherHub._hubSerial, otherHub._urlInfo.getUrl(YUrl.PROTO)))
        # keep the strongest targetState
        if self._targetState < otherHub._targetState:
            self._setTargetState(otherHub._targetState)
        # inherit known devYdx, just in case
        for ydx, serial in otherHub._serialByYdx.items():
            if ydx not in self._serialByYdx:
                self._serialByYdx[ydx] = serial
        # merge pending resolvers (either resolve or transfer)
        if self._currentState >= _HUB_CONNECTED > otherHub._currentState:
            # Forward the result to all pending promises
            for resolver in otherHub._connResolvers:
                if not resolver.done():
                    resolver.set_result(YAPI.SUCCESS, 'Hub %s already connected' % self._hubSerial, None)
        else:
            # inherit connection resolvers
            for resolver in otherHub._connResolvers:
                self._connResolvers.append(resolver)
        otherHub._connResolvers = []
        # shut down otherHub connection
        if _LOG_LEVEL >= 3:
            self._yapi._Log('Hub ' + self._hubSerial + ' is connected as ' + self._urlInfo.getUrl(YUrl.PROTO) + ', dropping connection to ' + otherHub._urlInfo.getUrl(YUrl.PROTO))
        otherHub._commonDisconnect('inherit', YAPI.SUCCESS, 'Hub %s already connected' % self._hubSerial)
        otherHub._disconnectNow()
        for url in otherHub._knownUrls:
            if url not in self._knownUrls:
                self._knownUrls.append(url)

    def _bestUrl(self) -> YUrl:
        cur_proto: str = self._urlInfo.proto
        best: YUrl = YUrl(self._urlInfo.getUrl(YUrl.PROTO + YUrl.AUTH), _YOCTO_DEFAULT_PORT, _YOCTO_DEFAULT_HTTPS_PORT)
        self._hubMode = _HUBMODE_SECURE
        if len(self._portInfo) > 0:
            if self._isVhub4web:
                # For VirtualHub-4web, info.json always has the most accurate value.
                # Note 1 : redirection from http to https was already done during the download of info.json
                # Note 2 : Websocket is not supported by VirtualHub-4web
                if cur_proto.startswith("ws"):
                    raise ValueError('Websocket protocol is not supported by VirtualHub-4web')
                for proto, port in self._portInfo:
                    if proto.startswith("http"):
                        if _LOG_LEVEL >= 3:
                            self._yapi._Log("Hub %s will use %s proto on port %d" % (self._urlInfo.host, proto, port))
                        best.updateBestProto(proto, port)
                        break
            else:
                best_port: int = 0
                best_proto: str = 'ws'
                if self._portInfo[0][0] in ('ws', 'http'):
                    self._hubMode = _HUBMODE_LEGACY
                for proto, port in self._portInfo:
                    if self._hubMode == _HUBMODE_SECURE and proto in ('ws', 'http'):
                        if _LOG_LEVEL >= 3:
                            self._yapi._Log("Hub " + self._urlInfo.host + " use mixed or legacy mode")
                        self._hubMode = _HUBMODE_MIXED
                    if cur_proto == 'auto' and best_port == 0:
                        if proto.startswith('ws') or proto.startswith('http'):
                            best_proto = proto
                            best_port = port
                    elif cur_proto == 'secure' and best_port == 0:
                        if proto == 'wss' or proto == 'https':
                            best_proto = proto
                            best_port = port
                if best_port != 0:
                    if _LOG_LEVEL >= 3:
                        self._yapi._Log("Hub %s will use %s proto on port %d" % (self._urlInfo.host, best_proto, best_port))
                    best.updatePortInfo(best_proto, best_port)
        return best

    async def waitForPendingQueries(self, msTimeout: int) -> None:
        if self._hubEngine:
            pending: list[Coroutine] = list()
            for serial in self._serialByYdx.values():
                dev: Union[YDevice,None] = self._yapi._devsBySn.get(serial)
                if dev:
                    pending.append(dev.waitForPendingQueries())
            waitForDev = asyncio.gather(*pending)
            await asyncio.wait_for(waitForDev, msTimeout / 1000)
            await asyncio.wait_for(self._hubEngine.waitForPendingQueries(), msTimeout / 1000)

    @staticmethod
    def _getNewConnID() -> str:
        ts = time.localtime()
        return '%dh%02dm%d02_0' % (ts.tm_hour, ts.tm_min, ts.tm_sec)

    # Put current task on sleep for a specified duration in milliseconds
    # Sleep by slices of 250ms to ensure  periodic calls to VM hook for
    # debugger access, in case all other running tasks are pending I/O
    @staticmethod
    async def sleep_ms(duration_ms: int) -> None:
        endTicks: int = ticks_add(ticks_ms(), duration_ms)
        remaining = ticks_diff(endTicks, ticks_ms())
        while remaining > 0:
            if _IS_MICROPYTHON:
                await asyncio.sleep_ms(min(remaining, 250))  # noqa
            else:
                await asyncio.sleep(min(remaining, 250) / 1000.0)
            remaining = ticks_diff(endTicks, ticks_ms())

    def create_task(self, coro: Coroutine) -> asyncio.Task:
        # first purge list from completed tasks
        allTasks = self._tasks
        for pos in range(len(allTasks) - 1, 0, -1):
            if allTasks[pos].done():
                del allTasks[pos]
        task: asyncio.Task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task

    def _tryTestConnectFor(self, mstimeout: int) -> None:
        tryUntil: int = ticks_add(ticks_ms(), mstimeout)
        if ticks_diff(self._keepTryingUntil, tryUntil) < 0:
            self._keepTryingUntil = tryUntil
            if self._keepTryingTimer:
                self._keepTryingTimer.cancel()
            self._keepTryingTimer = self.create_task(self._testHubTimeout(mstimeout))

    async def _testHubTimeout(self, mstimeout: int) -> None:
        await self.sleep_ms(mstimeout)
        # Timeout during TestHub connection: detach if no more needed
        self.keepTryingTimeer = None
        if self._targetState == _HUB_CONNECTED:
            await self.detach(YAPI.IO_ERROR, 'TestHub timeout reached')

    # Trigger the setup of a connection to the target hub, and return.
    # This method uses a connection helper that is overridden by each type of hub.
    async def attach(self, targetConnType: int) -> None:
        mustReconnect: bool = False
        # Keep the latest connection settings requested for this hub
        if self._targetState <= _HUB_CONNECTED or targetConnType > _HUB_CONNECTED:
            # Upgrade target state
            self._setTargetState(targetConnType)
            if self._currentState == _HUB_CONNECTED and targetConnType > _HUB_CONNECTED:
                # Hub must be kept attached
                try:
                    self._setState(targetConnType)
                except YAPI_Exception:
                    # Communication failure, must retry connecting
                    self._disconnectNow()

            # Special handling for TestHub
            if targetConnType == _HUB_CONNECTED:
                # This is a TestHub attachment: stay connected at least for 100ms,
                # unless configured for more in next call to waitForConnection
                self._tryTestConnectFor(100)
        if self._currentState <= _HUB_DETACHED:
            # Hub is not yet connecting, trigger connection
            if _LOG_LEVEL >= 4:
                self._yapi._Log('New hub is detached, connecting...')
            self._hubEngine = None  # clean old hub engine to force reload of info.json
            self.networkTimeout = self._yapi.GetNetworkTimeout()
            self._setState(_HUB_CONNECTING)
            mustReconnect = True
        elif self._currentState == _HUB_DISCONNECTED:
            # Currently waiting to reconnect, trigger immediate retry
            if self._reconnTimer:
                if _LOG_LEVEL >= 4:
                    self._yapi._Log('New hub connection requested, retry now (drop [' + self._currentConnID + '])')
                self._reconnTimer.cancel()
                self._reconnTimer = None
                self._currentConnID = ''
            else:
                if _LOG_LEVEL >= 4:
                    self._yapi._Log('New hub connection requested, retry now (no pending reconnection ?!?)')
            mustReconnect = True
        elif self._currentState == _HUB_DETACHING or self._currentState == _HUB_DISCONNECTING:
            if _LOG_LEVEL >= 4:
                self._yapi._Log('Hub is currently disconnecting, reconnection will be triggered soon [' + self._currentConnID + ']')
                self._yapi._Log('Current state: %d' % self._currentState)
                self._yapi._Log('Target state: %d (%d)' % (self._targetState, targetConnType))
        if mustReconnect:
            self.create_task(self.reconnect(self._getNewConnID()))

    @staticmethod
    async def _timeoutResolve(mstimeout: int, future: YFuture, retCode: int, errMsg: str, retVal: Any = None):
        try:
            await YGenericHub.sleep_ms(mstimeout)
        except asyncio.CancelledError as exc:
            pass
        if not future.done():
            future.set_result(retCode, errMsg, retVal)

    # Wait until the connection to the hub is established
    async def waitForConnection(self, mstimeout: int, errmsg: YRefParam) -> int:
        # First handle cases where no waiting is needed
        if self._targetState < _HUB_CONNECTED:
            # Attachment may have already been cancelled (by error or other)
            errmsg.value = self.lastErrorMsg
            return self.lastErrorType
        if self._currentState >= _HUB_CONNECTED:
            # Connection already established
            return YAPI.SUCCESS
        if mstimeout <= 1:
            # Not connected, and immediate reply requested
            errmsg.value = 'Hub not connected'
            return YAPI.TIMEOUT
        if self._targetState == _HUB_CONNECTED:
            # This is a TestHub connection: keep trying for the specified period of time
            self._tryTestConnectFor(mstimeout)

        # We will need to wait, so we need to set up a request-specific future with timeout
        connOpenPromise: YFuture = YFuture()
        connOpenTimeoutObj = self.create_task(YGenericHub._timeoutResolve(mstimeout, connOpenPromise, YAPI.TIMEOUT,
                                                                          "Timeout waiting for hub connection"))

        # connResolvers will be invoked by self.signalHubConnected()
        # and by self._commonDisconnect() in case of fatal failure,
        # then cleared from the list
        self._connResolvers.append(connOpenPromise)

        # Handle race conditions with the connecting flow (connection possibly
        # established before adding the resolver into the list)
        if self._targetState < _HUB_CONNECTED:
            # Attachment has already failed
            connOpenTimeoutObj.cancel()
            errmsg.value = self.lastErrorMsg
            return self.lastErrorType
        if self._currentState >= _HUB_CONNECTED:
            # Connection established
            connOpenTimeoutObj.cancel()
            return YAPI.SUCCESS

        # Wait for the connection to come up, or for the timeout to expire
        openRes = await connOpenPromise.ready()

        # Clear timeout
        if connOpenTimeoutObj:
            connOpenTimeoutObj.cancel()

        # Return result
        if openRes.errorType != YAPI.SUCCESS and errmsg:
            errmsg.value = openRes.errorMsg
        return openRes.errorType

    def _getSslContex(self) -> Union[SSLContext, None]:
        if _IS_MICROPYTHON:
            return None
        ctx = SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_default_certs()
        if self._hubMode == _HUBMODE_MIXED or self._hubMode == _HUBMODE_LEGACY:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx.check_hostname = self._yapi._networkSecurityOptions & YAPI.NO_HOSTNAME_CHECK == 0
            if (self._yapi._networkSecurityOptions & (YAPI.NO_EXPIRATION_CHECK | YAPI.NO_TRUSTED_CA_CHECK)) == 0:
                ctx.verify_mode = ssl.CERT_REQUIRED
            else:
                ctx.verify_mode = ssl.CERT_NONE
        if not _IS_MICROPYTHON:
            for cert in self._yapi._trustedCertificate:
                ctx.load_verify_locations(None, None, cadata=cert)
        if _LOG_LEVEL >= 5:
            stats = ctx.cert_store_stats()
            print('SSL context: crl:%d, x509_ca:%d, x509:%d' % (stats['crl'], stats['x509_ca'], stats['x509']))
        self._sslContext = ctx
        return self._sslContext

    # Attempt to establish a connection to the hub asynchronously.
    #
    # On success, this method should call self.signalHubConnected()
    # On temporary failure, this method should call self._signalHubDisconnected()
    # On fatal failure, this method should call self._commonDisconnect()
    async def reconnect(self, tryOpenID: str) -> None:
        if self._hubEngine is None:
            if _LOG_LEVEL >= 4:
                self._yapi._Log('look for suitable Hub engine [' + tryOpenID + ']')
            self._isVhub4web = False
            if self._urlInfo.testInfoJson():
                https_req: bool = self._urlInfo.isSecure()
                if self._urlInfo.port == _YOCTO_DEFAULT_HTTPS_PORT:
                    https_req = True
                proto: str = "https://" if https_req else "http://"
                httpUrl = YUrl(proto + self._urlInfo.getUrl(0), _YOCTO_DEFAULT_PORT, _YOCTO_DEFAULT_HTTPS_PORT)
                async with BaseSession(httpUrl) as httpSession:
                    try:
                        req: ClientResponse
                        if https_req:
                            arg = self._getSslContex()
                        else:
                            arg = None
                        if _LOG_LEVEL >= 4:
                            self._yapi._Log('look for info.json at ' + httpUrl.getUrl(YUrl.PROTO) + ' [' + tryOpenID + ']')
                        async with httpSession.get("/info.json", timeout=self.networkTimeout / 1000, ssl=arg) as req:
                            info: Any = await req.json()
                            self._hubSerial = info["serialNumber"]
                            if "securityMode" in info and info["securityMode"] == 0:
                                self._commonDisconnect(tryOpenID, YAPI.UNCONFIGURED, "Remote hub is not yet configured")
                                self._disconnectNow()
                                return
                            if "protocol" in info:
                                self._isVhub4web = (info["protocol"] != "")
                            self._portInfo = []
                            portList: list[str] = info["port"]
                            for protoPort in portList:
                                proto, port = protoPort.split(":")
                                self._portInfo.append((proto, int(port)))
                            if _LOG_LEVEL >= 4:
                                self._yapi._Log('info.json successfully parsed ' + httpUrl.getUrl(YUrl.PROTO) + ' [' + tryOpenID + ']')
                    except CertError as e:
                        self._commonDisconnect(tryOpenID, YAPI.SSL_UNK_CERT, e.verify_message)
                        self._disconnectNow()
                        return
                    except asyncio.CancelledError as e:
                        # task cancelled, most probably due to asyncio loop closed before FreeAPI
                        if not self.isDisconnecting():
                            self._yapi._Log('Hub task was killed without notice, consider using FreeAPI()')
                        return
                    except BaseException as e:
                        if self.isDisconnecting():
                            return
                        if _LOG_LEVEL >= 4:
                            print_exception(e)
                            self._yapi._Log('Unable to get info.json from ' + httpUrl.getUrl(YUrl.PROTO) + ' [' + tryOpenID + ']')
                        # Old firmware without support for info.json, get at least the serial number
                        try:
                            req: ClientResponse
                            async with httpSession.get("/api/module/serialNumber", timeout=self.networkTimeout / 1000) as req:
                                serial: str = await req.content.text()
                                self._hubSerial = serial
                        except BaseException as e:
                            self._commonDisconnect(tryOpenID, YAPI.IO_ERROR, str(e))
                            return

            runtimeUrl = self._bestUrl()
            if runtimeUrl.isWebSocket():
                if _LOG_LEVEL >= 4:
                    self._yapi._Log('Use WebSocket hub engine [' + tryOpenID + ']')
                self._hubEngine = YWebSocketEngine(self, runtimeUrl)  # type: ignore
            else:
                if _LOG_LEVEL >= 4:
                    self._yapi._Log('Use HTTP hub engine [' + tryOpenID + ']')
                proto: str = "HTTP/1.1" if self._isVhub4web else ""
                self._hubEngine = YHttpEngine(self, runtimeUrl, proto)  # type: ignore
        await self._hubEngine.reconnectEngine(tryOpenID)

    # Invoked by self.reconnect() to handle successful hub connection
    # noinspection PyUnusedLocal
    async def signalHubConnected(self, tryOpenID: str, hubSerial: str) -> None:
        self._setState(_HUB_CONNECTED)
        self._hubSerial = hubSerial
        if _LOG_LEVEL >= 4:
            self._yapi._Log('Hub ' + hubSerial + ' connected [' + tryOpenID + ']')

        primaryHub: YGenericHub = self._yapi._getPrimaryHub(self)
        # If another hub connection was active for the same hub, they may have been merged.
        # So from that point, we continue the work on "primaryHub" rather than "self"
        if primaryHub._targetState >= _HUB_PREREGISTERED:
            if primaryHub._currentState < primaryHub._targetState:
                primaryHub._setState(primaryHub._targetState)
        else:
            # This is a TestHub connection: keep the connection up for 100ms
            # to allow an immediate RegisterHub to piggy-back on connection,
            # then disconnect.
            primaryHub.keepTryingExpiration = 0
            primaryHub._tryTestConnectFor(100)
        # Forward the result to all pending promises
        resolvers: list[YFuture] = primaryHub._connResolvers
        primaryHub._connResolvers = []
        primaryHub.lastErrorType = YAPI.SUCCESS
        primaryHub.lastErrorMsg = 'Hub %s connected' % hubSerial
        for resolver in resolvers:
            if not resolver.done():
                resolver.set_result(YAPI.SUCCESS, primaryHub.lastErrorMsg)

    # Invoked by the network handler to signal hub disconnection
    #
    # Returns true if a reconnection has been scheduled
    #      or false if the target state is "detached"
    def _signalHubDisconnected(self, tryOpenID: str) -> bool:
        if _LOG_LEVEL >= 4:
            self._yapi._Log('signalHubDisconnected  ' + self._urlInfo.getUrl(YUrl.PROTO))
        if self._currentState > _HUB_DISCONNECTED:
            self._setState(_HUB_DISCONNECTED)
        self.isNotifWorking = False
        self._devListExpires = 0
        self.removeAllDevices()
        # make sure any future reconnection triggers firstArrivalCallback
        self._firstArrivalCallback = True

        # notify any pending task that hub is now fully disconnected
        resolvers: list[YFuture] = self._disconnResolvers
        self._disconnResolvers = []
        for resolver in resolvers:
            if not resolver.done():
                resolver.set_result(YAPI.SUCCESS, 'Hub disconnect completed')

        # test the current target state to determine of a reconnection is desired
        if self.isDisconnecting():
            # no reconnection is desired
            self._setState(_HUB_DETACHED)
            if _LOG_LEVEL >= 4:
                self._yapi._Log('Hub ' + self._urlInfo.getUrl(YUrl.PROTO) + ' detached')
            return False
        if self._reconnTimer:
            if _LOG_LEVEL >= 4:
                self._yapi._Log('Hub disconnected, reconnection is already scheduled [' + self._currentConnID + ']')
            return True

        # need to schedule next retry
        openIDwords = tryOpenID.split('_')
        nextOpenID = '%s_%d' % (openIDwords[0], int(openIDwords[1]) + 1)
        self.retryDelay = min(self._retryDelay * 2, 5000)
        if _LOG_LEVEL >= 4:
            self._yapi._Log('Hub reconnection scheduled in %ds [%s]' % (self._retryDelay / 1000, nextOpenID))

        self._currentConnID = nextOpenID
        self._reconnTimer = self.create_task(self._retryHubConnection(self.retryDelay, nextOpenID))
        return True

    async def _retryHubConnection(self, mstimeout: int, nextOpenID: str) -> None:
        if _LOG_LEVEL >= 4:
            self._yapi._Log('Will retry hub connection in ' + str(mstimeout) + 'ms [' + nextOpenID + ']')
        await self.sleep_ms(mstimeout)
        # Time to retry connection
        self._reconnTimer = None
        self._currentConnID = ''
        if self.isDisconnecting():
            # reconnection cancelled
            return
        if _LOG_LEVEL >= 4:
            self._yapi._Log('Retry hub connection now [' + nextOpenID + ']')
        await self.reconnect(nextOpenID)

    # Cancel current connection and report the fatal connection failure to the initiator.
    # This function may be called with YAPI.SUCCESS in case of desired disconnection
    #
    # This function should be called FIRST by any implementors of async detach()
    # in order to prevent automatic reconnect
    # noinspection PyUnusedLocal
    def _commonDisconnect(self, tryOpenID: str, errType: int, errMsg: str) -> None:
        self.lastErrorType = errType
        self.lastErrorMsg = errMsg
        if self._currentState >= _HUB_DISCONNECTING:
            self._setState(_HUB_DETACHING)
        elif self._currentState == _HUB_DISCONNECTED:
            self._setState(_HUB_DETACHED)
        self._setTargetState(_HUB_DETACHED)
        if self._reconnTimer:
            self._reconnTimer.cancel()
            self._reconnTimer = None
        if _LOG_LEVEL >= 4:
            if errType != YAPI.SUCCESS and tryOpenID != 'detach':
                self._yapi._Log('Hub connection failed: ' + errMsg + ' [' + tryOpenID + ']')
        # make sure any future reconnection triggers firstArrivalCallback
        self._firstArrivalCallback = True

        resolvers: list[YFuture] = self._connResolvers
        self.connResolvers = []
        for resolver in resolvers:
            if not resolver.done():
                resolver.set_result(errType, errMsg)

    # Default implementation of function to abort communication channel immediately
    #
    # If a connectionID is passed as argument, only abort the
    # communication channel if the ID matched current connection
    #
    # Return true if the connection is getting aborted
    #
    # Subclasses are expected to invoke _signalHubDisconnected() after cleaning
    # up current communication, to bring back the link again later
    def _disconnectNow(self, connID: str = '') -> bool:
        if connID and connID != self._currentConnID:
            return False
        if self._currentState > _HUB_DISCONNECTING:
            self._setState(_HUB_DISCONNECTING)
        if self._hubEngine:
            self._hubEngine.disconnectEngineNow(connID)
        else:
            self._signalHubDisconnected(connID)
        return True

    # Invoked by UnregisterHub
    #
    # Free resources allocated by the hub, close requests,
    # call self._commonDisconnect() and bring the link down.
    #
    # This method may be redefined by subclasses to do additional
    # cleanup before invoking self._commonDisconnect() to bring
    # communication down, to prevent automatic reconnect.
    async def detach(self, errType: int = YAPI.IO_ERROR, errMsg: str = 'Hub has been forcibly detached') -> None:
        self._commonDisconnect('detach', errType, errMsg)
        self._disconnectNow()
        self.networkTimeout = self._yapi.GetNetworkTimeout()
        if self._hubEngine:
            await self._hubEngine.close()
            self._hubEngine = None
        for task in self._tasks:
            if not task.done():
                task.cancel()
        # yield to child tasks so that they can terminate
        await self.sleep_ms(10)
        self._tasks = []

    # Wait until the hub is fully disconnected
    async def waitForDisconnection(self, mstimeout: int) -> None:
        if self.isDisconnected():
            # disconnection has already happened in between
            return
        # Add resolver to the disconnResolvers list
        disconnPromise: YFuture = YFuture()
        self._disconnResolvers.append(disconnPromise)
        # Set up the timeout for disconnection
        disconnTimeoutObj = self.create_task(self._timeoutResolve(mstimeout, disconnPromise, YAPI.TIMEOUT,
                                                                  "Timeout waiting for hub disconnection"))
        # wait for the connection to come down, or for the timeout to expire
        await disconnPromise.ready()
        # Clear the timeout
        disconnTimeoutObj.cancel()

    def removeAllDevices(self) -> None:
        for serial in self._serialByYdx.values():
            self._yapi._unplugDevice(serial)
        self._serialByYdx = dict()

    async def _updateFromServices(self, services: xdict):
        newPlugs: bool = False
        newSerialByYdx: dict[int, str] = dict()
        whitePages: xlist = services["whitePages"]
        yellowPages: xdict = services["yellowPages"]
        for wp in whitePages:
            serial: str = sys.intern(wp['serialNumber'])
            devydx: int = wp["index"]
            newSerialByYdx[devydx] = serial
            isNew: bool = (self._serialByYdx.get(devydx) != serial)
            if self._hubSerial is None:
                if wp['networkUrl'] == '/api':
                    self._hubSerial = serial
            newPlugs |= self._yapi._storeServices(self._hubRef, wp, isNew, yellowPages)
        for devydx, serial in self._serialByYdx.items():
            if newSerialByYdx.get(devydx) != serial:
                self._yapi._unplugDevice(serial)
        self._serialByYdx = newSerialByYdx
        if newPlugs:
            self._yapi._plugDevices()

    async def updateDeviceList(self, forceupdate: bool) -> int:
        if forceupdate:
            self._devListExpires = 0
        elif not self.isOnline():
            return YAPI.SUCCESS
        if self._currentState < _HUB_PREREGISTERED:
            return YAPI.SUCCESS
        if self._updateDevListStarted and ticks_diff(ticks_ms(), self._updateDevListStarted) < 30000:
            return YAPI.SUCCESS
        if self._devListExpires and not ticks_past(self._devListExpires):
            return YAPI.SUCCESS

        # Start update process
        try:
            self._updateDevListStarted = ticks_ms() | 1
            ydev: Union[YDevice, None] = None
            if self._hubSerial:
                ydev = self._yapi._devsBySn.get(self._hubSerial)
            try:
                if ydev:
                    if not ydev.hub:
                        ydev.hub = self
                        ydev.clearCache()
                    elif self._devListExpires == 0:
                        ydev.clearCache()
                    loadval: xdict = await ydev.requestAPI()
                else:
                    yreq: xarray = await self.hubRequest("/api.json")
                    loadval: xdict = yreq.json(encoding='latin-1')
            except BaseException as exc:
                print_exception(exc)
                if isinstance(exc, YAPI_Exception):
                    raise
                raise YAPI_Exception(YAPI.IO_ERROR, "Invalid JSON response")

            if self._rwAccess is None:
                network: Union[dict, None] = loadval.get("network")
                if network:
                    adminpass: str = network.get("adminPassword", "")
                    if not adminpass:
                        self._rwAccess = True

            services: Union[xdict, None] = loadval.get("services")
            if not services:
                self.lastErrorMsg = "Device %s is not a hub" % self._urlInfo.host
                self.lastErrorType = YAPI.INVALID_ARGUMENT
                return YAPI.INVALID_ARGUMENT
            await self._updateFromServices(services)

            # reset device list cache timeout for this hub
            self._devListExpires = ticks_add(ticks_ms(), (self._yapi._deviceListValidityMs if self._isNotifWorking else 500)) | 1
            self._updateDevListStarted = 0
        except:
            self._updateDevListStarted = 0
            if self._currentState >= _HUB_PREREGISTERED:
                # generate unplug events
                self.removeAllDevices()
            if self._currentState > _HUB_PREREGISTERED:
                raise
        return YAPI.SUCCESS

    def handleNetNotification(self, evb: memoryview):
        evlen: int = len(evb)
        self._lastPing = ticks_ms()
        if evlen == 0:
            # drop ping notification
            self._isNotifWorking = True
            return
        if evlen >= 3 and _NOTIFY_NETPKT_CONFCHGYDX <= evb[0] <= _NOTIFY_NETPKT_TIMEAVGYDX:
            # function value ydx (tiny notification)
            self._isNotifWorking = True
            if self.notifPos >= 0:
                self.notifPos += evlen + 1
            self._yapi._handleNetNotification(self, evb)
        elif evlen >= 5 and evb[:4] == b'YN01':
            self._isNotifWorking = True
            if self.notifPos >= 0:
                self.notifPos += evlen + 1
            notype = evb[4]
            if notype == _NOTIFY_NETPKT_NOT_SYNC:
                self.notifPos = int(evb[5:])
            else:
                self._yapi._handleNetNotification(self, evb)
                if notype in (_NOTIFY_NETPKT_NAME, _NOTIFY_NETPKT_CHILD, _NOTIFY_NETPKT_FUNCNAME, _NOTIFY_NETPKT_FUNCNAMEYDX):
                    # device name change, plug/unplug or function name change
                    if notype == _NOTIFY_NETPKT_CHILD:
                        parts = evb.tobytes().decode('latin-1').split(",")
                        if len(parts) >= 3 and parts[2] == '0':
                            self._yapi._unplugDevice(parts[1])
                    self._devListExpires = 0
        else:
            # oops, bad notification? be safe until a good one comes
            self._isNotifWorking = False
            self.notifPos = -1

    def isRwAccess(self) -> bool:
        if self._rwAccess is None:
            return False
        return self._rwAccess

    def setRwAccess(self, rwAccess: bool) -> None:
        self._rwAccess = rwAccess

    async def isReadOnly(self) -> bool:
        if self._rwAccess is None:
            try:
                await self.hubRequest('/api/module/serialNumber.json?serialNumber=rwTest')
                self._rwAccess = True
            except YAPI_Exception:
                self._rwAccess = False
        return not self._rwAccess

    async def getBootloaders(self) -> list[str]:
        res: xarray = await self.hubRequest('/flash.json?a=list', None, 1)
        flashState: dict = json.load(xStringIO(res))
        return flashState['list']

    # used to trigger requests directly on the hub itself, without using an YDevice object
    async def hubRequest(self, rel_url: str, body: Union[xarray, None] = None, tcpchan: int = 0) -> ByteArrayLike:
        if self._currentState < _HUB_CONNECTED or self._hubEngine is None:
            return self._throw(YAPI.IO_ERROR, "Hub is currently unavailable")
        method: str = "GET" if body is None else "POST"
        yreq: YRequest = self._hubEngine.makeRequest(method, rel_url, body, self.networkTimeout)
        return await self._hubEngine.sendRequest(yreq, tcpchan)

    # invoked by YDevice to prepare a device-specific request
    def makeRequest(self, method: str, rel_url: str, body: Union[xarray, None], msTimeout: int) -> YRequest:
        return self._hubEngine.makeRequest(method, rel_url, body, msTimeout)

    # invoked by YDevice to trigger a device-specific synchronous request
    async def devRequestSync(self, yreq: YRequest) -> ByteArrayLike:
        if self._currentState < _HUB_CONNECTED or self._hubEngine is None:
            self._throw(YAPI.IO_ERROR, "Hub is currently unavailable")
        return await self._hubEngine.sendRequest(yreq, 0)

    # invoked by YDevice to trigger a device-specific asynchronous request
    async def devRequestAsync(self, yreq: YRequest) -> None:
        if self._currentState < _HUB_CONNECTED or self._hubEngine is None:
            self._throw(YAPI.IO_ERROR, "Hub is currently unavailable")
        if yreq._target.endswith('&.') and await self.isReadOnly():
            self._throw(YAPI.UNAUTHORIZED, 'Access denied: admin credentials required')
        yreq.setAsync()
        await self._hubEngine.sendRequest(yreq, 0)

    def get_urlOf(self, serialNumber: str) -> str:
        dev = self._yapi._getDevice(serialNumber)
        if dev:
            return self._urlInfo.getUrl(YUrl.PROTO) + dev._networkUrl + '/'
        return self._urlInfo.getUrl(YUrl.PROTO | YUrl.ENDSLASH)

    def get_subDeviceOf(self, serialNumber: str) -> list[str]:
        res: list[str] = []
        if serialNumber != self._hubSerial:
            return []
        for serial in self._serialByYdx.values():
            if serial == serialNumber:
                continue
            res.append(serial)
        return res

    def _decode_json(self, data: xarray) -> Any:
        uploadstate = xStringIO(data, 'latin-1')
        try:
            return json.load(uploadstate)
        except BaseException as exc:
            print("JSON error:")
            print(data.tobytes())
            raise YAPI_Exception(YAPI.IO_ERROR, "invalid json response :" + str(exc))

    async def firmwareUpdate(self, serial: str, firmware: xarray, settings: xarray, progress) -> list[str]:
        use_self_flash: bool = False
        baseurl: str = ""
        need_reboot: bool = True
        if self._hubSerial.startswith("VIRTHUB"):
            use_self_flash = False
        elif serial == self._hubSerial:
            use_self_flash = True
        else:
            # check if subdevice support self-flashing
            try:
                await self.hubRequest("/bySerial/" + serial + "/flash.json?a=state")
                baseurl = "/bySerial/" + serial
                use_self_flash = True
            except YAPI_Exception:
                pass
        # 5 % -> 10 %
        progress(5, "Enter in bootloader")
        bootloaders: list[str] = await self.getBootloaders()

        is_shield: bool = serial.startswith("YHUBSHL1")
        for bl in bootloaders:
            if bl == serial:
                need_reboot = False
            elif is_shield:
                if bl.startswith("YHUBSHL1"):
                    raise YAPI_Exception(YAPI.IO_ERROR, "Only one YoctoHub-Shield is allowed in update mode")
        if not use_self_flash and need_reboot and len(bootloaders) >= 4:
            raise YAPI_Exception(YAPI.IO_ERROR, "Too many devices in update mode")
        # ensure flash engine is not busy
        data: xarray = await self.hubRequest(baseurl + "/flash.json?a=state")
        uploadres = self._decode_json(data)
        state: str = uploadres["state"]
        if state == "uploading" or state == "flashing":
            raise YAPI_Exception(YAPI.IO_ERROR, "Cannot start firmware update: busy (" + state + ")")
        # start firmware upload
        # 10% -> 40%
        progress(10, "Send firmware file")
        head_body: xarray = YDevice.formatHTTPUpload("firmware", firmware)
        await self.hubRequest(baseurl + "/upload.html", head_body, 0)
        # check firmware upload result
        data = await self.hubRequest(baseurl + "/flash.json?a=state")
        uploadres = self._decode_json(data)
        if uploadres['state'] != "valid":
            raise YAPI_Exception(YAPI.IO_ERROR, "Upload of firmware failed: invalid firmware(" + uploadres.getString("state") + ")")
        if uploadres["progress"] != 100:
            raise YAPI_Exception(YAPI.IO_ERROR, "Upload of firmware failed: incomplete upload")
        if use_self_flash:
            try:
                jsonObject = self._decode_json(settings)
                settingsOnly = jsonObject['api']
                settingsOnly.pop("services", None)
                startupConf: xarray = xbytearray(json.dumps(settingsOnly), 'latin-1')
            except BaseException:
                startupConf: xarray = xbytearray()
            progress(20, "Upload startupConf.json")
            head_body = YDevice.formatHTTPUpload("startupConf.json", startupConf)
            await self.hubRequest(baseurl + "/upload.html", head_body)
            progress(20, "Upload firmwareConf")
            head_body = YDevice.formatHTTPUpload("firmwareConf", startupConf)
            await self.hubRequest(baseurl + "/upload.html", head_body)

        # 40 %-> 80 %
        if use_self_flash:
            progress(40, "Flash firmware")
            # the hub itself -> reboot in autoflash mode
            await self.hubRequest(baseurl + "/api/module/rebootCountdown?rebootCountdown=-1003")
            await asyncio.sleep(7)
        else:
            if need_reboot:
                await  self.hubRequest("/bySerial/" + serial + "/api/module/rebootCountdown?rebootCountdown=-2")
            # // verify that the device is in bootloader

            # verify that the device is in bootloader
            timeout: int = YAPI.GetTickCount() + _YPROG_BOOTLOADER_TIMEOUT
            found: bool = False
            progress(40, "Wait for device to be in bootloader")
            while not found and YAPI.GetTickCount() < timeout:
                blist: list[str] = await self.getBootloaders()
                for bl in blist:
                    if bl == serial:
                        found = True
                        break

                if not found:
                    if _IS_MICROPYTHON:
                        await asyncio.sleep_ms(100)  # noqa
                    else:
                        await asyncio.sleep(100 / 1000.0)
            # start flash
            progress(45, "Flash firmware")
            res = await self.hubRequest("/flash.json?a=flash&s=" + serial)
            flashres = self._decode_json(res)
            return flashres['logs']


#################################################################################
#                                                                               #
#                               YHttpEngine                                     #
#                                                                               #
#################################################################################

# noinspection PyRedeclaration
# noinspection PyProtectedMember
class YHttpEngine(YHubEngine):
    # Notification stream handling
    _notbynRequest: Union[ClientResponse, None] = None

    def __init__(self, hub: YGenericHub, urlInfo: YUrl, proto: str):
        super().__init__(hub, urlInfo, proto)
        self._notbynRequest = None

    async def reconnectEngine(self, tryOpenID: str) -> None:
        """
        Attempt to establish a connection to the hub asynchronously.

        On success, this method should call self.signalHubConnected()
        On temporary failure, this method should call self._signalHubDisconnected()
        On fatal failure, this method should call self._commonDisconnect()
        """
        # fixme: On Typescript we get info.json after first connection to look if device settings has changed
        self._hub._currentConnID = tryOpenID
        # Check if this hub is a duplicate connection
        primaryHub: Union[YGenericHub, None] = self._hub._yapi._getPrimaryHub(self._hub)
        if primaryHub != self._hub:
            self._hub._commonDisconnect(tryOpenID, YAPI.SUCCESS, 'Hub %s is already connected' % self._hub.getSerialNumber())
            self._hub._currentConnID = ''
            self._hub._signalHubDisconnected(tryOpenID)
            return
        # Then issue an HTTP request to open the notification channel
        args = ''
        notifPos: int = self._hub.notifPos
        if notifPos >= 0:
            args = '?abs=%d' % notifPos
        else:
            self._hub.setFirstArrivalCallback(True)
        if _LOG_LEVEL >= 4:
            self._hub._yapi._Log('Opening http connection to hub (args="' + args + '") [' + tryOpenID + ']')
        try:
            req: ClientResponse = self.request('GET', '/not.byn' + args, timeout=self._hub.networkTimeout / 1000, channel=0)
            self._notbynRequest = req
            await req.ready()
            if not self._checkStatus(req, tryOpenID):
                return
            await self._hub.signalHubConnected(tryOpenID, self._hub.getSerialNumber())
            while not self._hub.isDisconnecting():
                evb: bytes = await req.readuntil(b'\n')
                if len(evb) > 0 and evb[-1] == 10:
                    req.keepAlive(self._hub.networkTimeout)
                    self._hub.handleNetNotification(memoryview(evb)[:-1])
        except EOFError:
            if not self._hub.isDisconnecting():
                self._hub._yapi._Log('%s: %s' % ('reconnectEngine', 'EOFError'))
                if tryOpenID != self._hub._currentConnID:
                    return
                self._hub.create_task(self.reconnectEngine(tryOpenID))
        except OSError as exc:
            errmsg = exc.strerror
            if errmsg is None:
                if len(exc.args) > 0:
                    errmsg = exc.args[0]
                else:
                    errmsg = "OSError"
            if not self._hub.isDisconnecting():
                self._hub._yapi._Log('%s: %s' % ('reconnectEngine', errmsg))
            if tryOpenID != self._hub._currentConnID:
                return
            self._hub.lastErrorType = YAPI.IO_ERROR
            self._hub.lastErrorMsg = errmsg
            # connection error, will retry automatically
            self._hub._disconnectNow(tryOpenID)
        except asyncio.TimeoutError:
            # stalled connection
            if not self._hub.isDisconnecting():
                self._hub._yapi._Log('%s: %s' % ('reconnectEngine', 'TimeoutError'))
            if tryOpenID != self._hub._currentConnID:
                return
            self._hub.lastErrorType = YAPI.IO_ERROR
            self._hub.lastErrorMsg = 'TimeoutError'
            self._hub._disconnectNow()
        except asyncio.CancelledError:
            # task cancelled, most probably due to asyncio loop closed before FreeAPI
            if not self._hub.isDisconnecting():
                self._hub._yapi._Log('Hub task was killed without notice, consider using FreeAPI()')
        except BaseException as exc:
            print_exception(exc)
            self._hub._yapi._Log(str(exc))

    def disconnectEngineNow(self, connID: str = ''):
        """
        Abort communication channel immediately

        If a connectionID is passed as argument, only abort the
        communication channel if the ID matched current connection
        """
        if self._notbynRequest is None:
            return
        closeConnID: str = connID if connID else self._hub._currentConnID
        self._notbynRequest.release()
        self._notbynRequest = None
        self._hub._currentConnID = ''
        self._hub._signalHubDisconnected(closeConnID)

    def makeRequest(self, method: str, rel_url: str, body: Union[xarray, None], msTimeout: int) -> YRequest:
        """
        Prepare a request to be sent to the hub, but do not send it yet.
        The method will be sent using method request() below
        """
        # FIXME: Add VirtualHub for Web x-y-auth support later
        return self.request(method, rel_url, data=body, timeout=msTimeout / 1000, channel=None, as_cls=YRequest)

    async def sendRequest(self, request: YRequest, tcpchan: int) -> ByteArrayLike:
        """
        Attempt to schedule the request passed as argument and to return the result
        If the request is async, the method should return None as soon as
        the async request has been sent to the hub
        """
        self._sendRequest(self._base, request, ssl=self._ssl, channel=tcpchan + 1)
        if request._async is not None:
            await request.ready()
            return b''
        res = await request.read()

        if request.status == 401:
            raise YAPI_Exception(YAPI.UNAUTHORIZED, request.reason)
        if request.status != 200:
            raise YAPI_Exception(YAPI.IO_ERROR, request.reason)
        return res

    async def waitForPendingQueries(self) -> None:
        await asyncio.gather(*[chan.waitForPendingRequests() for chan in self._channels[1:]])


#################################################################################
#                                                                               #
#                             YWebSocketEngine                                  #
#                                                                               #
#################################################################################

_DEFAULT_TCP_ROUND_TRIP_TIME: Final[int] = 30
_DEFAULT_TCP_MAX_WINDOW_SIZE: Final[int] = 4 * 65536

# websocket encoding constants
_YSTREAM_EMPTY: Final[int] = 0
_YSTREAM_TCP: Final[int] = 1
_YSTREAM_TCP_CLOSE: Final[int] = 2
_YSTREAM_NOTICE: Final[int] = 3
_YSTREAM_REPORT: Final[int] = 4
_YSTREAM_META: Final[int] = 5
_YSTREAM_REPORT_V2: Final[int] = 6
_YSTREAM_NOTICE_V2: Final[int] = 7
_YSTREAM_TCP_NOTIF: Final[int] = 8
_YSTREAM_TCP_ASYNCCLOSE: Final[int] = 9

_USB_META_UTCTIME: Final[int] = 1
_USB_META_DLFLUSH: Final[int] = 2
_USB_META_ACK_D2H_PACKET: Final[int] = 3
_USB_META_WS_ANNOUNCE: Final[int] = 4
_USB_META_WS_AUTHENTICATION: Final[int] = 5
_USB_META_WS_ERROR: Final[int] = 6
_USB_META_ACK_UPLOAD: Final[int] = 7

_USB_META_UTCTIME_SIZE: Final[int] = 6
_USB_META_DLFLUSH_SIZE: Final[int] = 1
_USB_META_ACK_D2H_PACKET_SIZE: Final[int] = 2
_USB_META_WS_ANNOUNCE_SIZE: Final[int] = 28  # = 8 + _YOCTO_SERIAL_LEN
_USB_META_WS_AUTHENTICATION_SIZE: Final[int] = 28
_USB_META_WS_ERROR_SIZE: Final[int] = 6
_USB_META_ACK_UPLOAD_SIZE: Final[int] = 6

_USB_META_WS_PROTO_V1: Final[int] = 1  # adding authentication support
_USB_META_WS_PROTO_V2: Final[int] = 2  # adding API packets throttling
_VERSION_SUPPORT_ASYNC_CLOSE: Final[int] = 1

_USB_META_WS_VALID_SHA1: Final[int] = 1
_USB_META_WS_AUTH_FLAGS_RW: Final[int] = 2

_WS_CONNSTATE_DEAD: Final[int] = 0
_WS_CONNSTATE_DISCONNECTED: Final[int] = 1
_WS_CONNSTATE_CONNECTING: Final[int] = 2
_WS_CONNSTATE_AUTHENTICATING: Final[int] = 3
_WS_CONNSTATE_READY: Final[int] = 4
_WS_CONNSTATE_CONNECTED: Final[int] = 5

# noinspection PyProtectedMember
# noinspection PyRedeclaration
class YWebSocketEngine(YHubEngine):
    # Notification stream handling
    websocket: Union[BaseWsResponse, None]
    tcpChan: list[Union[YRequest, None]]
    _frame: bytearray
    _notifCarryOver: bytearray
    _notifCarryOverLen: int
    _nextAsyncId: int
    _connectionTime: int  # from ticks_ms()
    _connectionState: int  # a constant from _WS_CONNSTATE_*
    _remoteVersion: int
    _remoteSerial: str
    _remoteNonce: int
    _nonce: int
    _session_error: Union[str, None]
    _session_errno: Union[int, None]
    _task: Union[asyncio.Task, None]  # sending task
    _tcpRoundTripTime: int
    _tcpMaxWindowSize: int
    # upload field below only apply to tcpchan 0
    _lastUploadAckBytes: int
    _lastUploadAckTime: int
    _lastUploadRateBytes: int
    _lastUploadRateTime: int
    _uploadPos: int
    _uploadRate: int

    def __init__(self, hub: YGenericHub, urlInfo: YUrl):
        super().__init__(hub, urlInfo, "HTTP/1.1")
        self.websocket = None
        self.tcpChan = [None, None]
        self._frame = bytearray(125)
        self._notifCarryOver = bytearray(63)
        self._notifCarryOverLen = 0
        self._nextAsyncId = 48
        self._connectionTime = 0
        self._connectionState = _WS_CONNSTATE_CONNECTING
        self._remoteVersion = 0
        self._remoteSerial = ''
        self._remoteNonce = -1
        self._nonce = -1
        self._session_error = None
        self._session_errno = None
        self._task = None
        self._tcpRoundTripTime = _DEFAULT_TCP_ROUND_TRIP_TIME
        self._tcpMaxWindowSize = _DEFAULT_TCP_MAX_WINDOW_SIZE
        self._lastUploadAckBytes = 0
        self._lastUploadAckTime = 0
        self._lastUploadRateBytes = 0
        self._lastUploadRateTime = 0
        self._uploadPos = 0
        self._uploadRate = 0

    @staticmethod
    def _computeAuth(user: str, pwd: str, serial: str, nonce: int) -> bytes:
        ha1_str: str = '%s:%s:%s' % (user, serial, pwd)
        ha1: str = hashlib.md5(ha1_str.encode('ascii')).hexdigest().lower()
        sha1_raw: str = '%s%02x%02x%02x%02x' % (ha1, nonce & 0xff, (nonce >> 8) & 0xff, (nonce >> 16) & 0xff, (nonce >> 24) & 0xff)
        sha1 = hashlib.sha1(sha1_raw.encode('ascii')).digest()
        sha1_str = "sha1= "
        for b in sha1:
            sha1_str += ("%x" % b)
        return sha1

    def _wsError(self, msg: str) -> None:
        self._hub._yapi._Log('WS: %s' % msg)
        self._session_error = msg
        self._connectionState = _WS_CONNSTATE_DEAD

    async def reconnectEngine(self, tryOpenID: str) -> None:
        """
        Attempt to establish a connection to the hub asynchronously.

        On success, this method should call self.signalHubConnected()
        On temporary failure, this method should call self._signalHubDisconnected()
        On fatal failure, this method should call self._commonDisconnect()
        """
        self._connectionState = _WS_CONNSTATE_CONNECTING
        if _LOG_LEVEL >= 4:
            self._hub._yapi._Log('Opening websocket connection [' + tryOpenID + ']')
        self._hub._currentConnID = tryOpenID
        # Check if this hub is a duplicate connection
        primaryHub: Union[YGenericHub, None] = self._hub._yapi._getPrimaryHub(self._hub)
        if primaryHub != self._hub:
            self._hub._commonDisconnect(tryOpenID, YAPI.SUCCESS, 'Hub %s is already connected' % self._hub.getSerialNumber())
            self._hub._currentConnID = ''
            self._hub._signalHubDisconnected(tryOpenID)
            return
        # Then issue an HTTP request to open the websocket channel
        self._hub.setFirstArrivalCallback(True)
        try:
            if _LOG_LEVEL >= 4:
                self._hub._yapi._Log('About to open websocket connection [' + tryOpenID + ']')
            ssl_arg = self._hub._getSslContex()
            websocket: BaseWsResponse = self.ws_connect('/not.byn', ssl=ssl_arg, timeout=self._hub.networkTimeout / 1000, as_cls=BaseWsResponse)
            self.websocket = websocket
            await websocket.ready()
            if not self._checkStatus(self.websocket, tryOpenID):
                self._wsError('Failed to open websocket')
                return
            if _LOG_LEVEL >= 4:
                self._hub._yapi._Log('Websocket host reached, about to negociate [' + tryOpenID + ']')
            while self._connectionState in (_WS_CONNSTATE_CONNECTING, _WS_CONNSTATE_AUTHENTICATING):
                await self._wsRecvSetup(await websocket.receive_bytes())
            if self._connectionState == _WS_CONNSTATE_READY:
                self._connectionState = _WS_CONNSTATE_CONNECTED
                await self._hub.signalHubConnected(tryOpenID, self._remoteSerial)
                if _LOG_LEVEL >= 4:
                    self._hub._yapi._Log('Websocket connection ready [' + tryOpenID + ']')
            while self._connectionState == _WS_CONNSTATE_CONNECTED:
                await self._wsRecvData(await websocket.receive_bytes())
            errMsg: str = 'Websocket I/O error' if self._session_error is None else 'Websocket error: ' + self._session_error
            if self._session_errno == 401:
                self._hub._commonDisconnect(tryOpenID, YAPI.UNAUTHORIZED, errMsg)
            else:
                self._hub.lastErrorType = YAPI.IO_ERROR
                self._hub.lastErrorMsg = errMsg
            self._hub._disconnectNow(tryOpenID)
        except CertError as exc:
            self._hub._yapi._Log('WS: %s' % 'CertError')
            if tryOpenID != self._hub._currentConnID:
                return
            self._hub._commonDisconnect(tryOpenID, YAPI.SSL_UNK_CERT, exc.strerror)
            self._hub._disconnectNow(tryOpenID)
        except (EOFError, asyncio.TimeoutError) as exc:
            errmsg = str(exc)
            self._hub._yapi._Log('WS: %s' % errmsg)
            if tryOpenID != self._hub._currentConnID:
                return
            self._hub.lastErrorType = YAPI.IO_ERROR
            self._hub.lastErrorMsg = errmsg
            # connection error, will retry automatically
            self._hub._disconnectNow(tryOpenID)
        except OSError as exc:
            errmsg = exc.strerror
            if errmsg is None:
                if len(exc.args) > 0:
                    errmsg = exc.args[0]
                else:
                    errmsg = "OSError"
            if not self._hub.isDisconnecting():
                self._hub._yapi._Log('WS: %s' % errmsg)
            if tryOpenID != self._hub._currentConnID:
                return
            self._hub.lastErrorType = YAPI.IO_ERROR
            self._hub.lastErrorMsg = errmsg
            # connection error, will retry automatically
            self._hub._disconnectNow(tryOpenID)
        except asyncio.CancelledError:
            if not self._hub.isDisconnecting():
                self._hub._yapi._Log('Hub task was killed without notice, consider using FreeAPI()')
        except BaseException as exc:
            print_exception(exc)
            self._wsError(str(exc))

    async def _wsRecvSetup(self, arr_bytes: bytes) -> None:
        data: memoryview = memoryview(arr_bytes)
        ystream: int = arr_bytes[0] >> 3
        if ystream != _YSTREAM_META:
            self._wsError('bad setup stream %d' % ystream)
            return
        metatype: int = arr_bytes[1]
        if metatype == _USB_META_WS_ANNOUNCE:
            if len(arr_bytes) < 1 + _USB_META_WS_ANNOUNCE_SIZE:
                return
            self._remoteVersion = arr_bytes[2]
            if self._remoteVersion < 1:
                return
            maxtcpws: int = (arr_bytes[3] << 4) + (arr_bytes[4] << 12)
            if maxtcpws > 0:
                self._tcpMaxWindowSize = maxtcpws
            self._remoteNonce = arr_bytes[5] + (arr_bytes[6] << 8) + (arr_bytes[7] << 16) + (arr_bytes[8] << 24)
            endSerial: int = arr_bytes.find(b'\0', 9, 9 + 20)
            if endSerial >= 0:
                self._remoteSerial = str(data[9:endSerial], 'ascii')
            self._nonce = random.getrandbits(32)
            self._connectionTime = ticks_ms()
            self._connectionState = _WS_CONNSTATE_AUTHENTICATING
            # send our authentication packet
            frame = bytearray(1 + _USB_META_WS_AUTHENTICATION_SIZE)
            flags = 0
            frame[0] = _YSTREAM_META << 3
            frame[1] = _USB_META_WS_AUTHENTICATION
            frame[2] = min(self._remoteVersion, 2)
            if self._base._pass:
                flags = _USB_META_WS_VALID_SHA1
                sha1: bytes = self._computeAuth(self._base.user, self._base._pass, self._remoteSerial, self._remoteNonce)
                frame[9:9 + len(sha1)] = sha1
            frame[3] = flags & 0xff
            frame[4] = flags >> 8
            frame[5] = self._nonce & 0xff
            frame[6] = (self._nonce >> 8) & 0xff
            frame[7] = (self._nonce >> 16) & 0xff
            frame[8] = (self._nonce >> 24) & 0xff
            await self.websocket.send_bytes(frame)
            return
        if metatype == _USB_META_WS_AUTHENTICATION:
            if len(arr_bytes) < 1 + _USB_META_WS_AUTHENTICATION_SIZE:
                return
            self._tcpRoundTripTime = ticks_diff(ticks_ms(), self._connectionTime) + 1
            if self._tcpMaxWindowSize < 2048 and self._tcpRoundTripTime < 7:
                # Fix overly optimistic round-trip on YoctoHubs
                self._tcpRoundTripTime = 7
            self._uploadRate = round(self._tcpMaxWindowSize * 1000 / self._tcpRoundTripTime)
            if _LOG_LEVEL >= 4:
                self._hub._yapi._Log('RTT=%dms, WS=%d, uploadRate=%f KB/s' % (self._tcpRoundTripTime, self._tcpMaxWindowSize, self._uploadRate / 1000))
            self._remoteVersion = arr_bytes[2]
            if self._remoteVersion < 1:
                return
            inflags: int = arr_bytes[3] + (arr_bytes[4] << 8)
            self._hub.setRwAccess((inflags & _USB_META_WS_AUTH_FLAGS_RW) != 0)
            if (inflags & _USB_META_WS_VALID_SHA1) != 0:
                remote_sha1: bytes = arr_bytes[9:29]
                sha1: bytes = self._computeAuth(self._base.user, self._base._pass, self._remoteSerial, self._nonce)
                if sha1 != remote_sha1:
                    # bad signature
                    self._session_errno = 401
                    self._session_error = 'Authentication failed'
                    self._connectionState = _WS_CONNSTATE_DEAD
                    return
                # password verified OK
                self._connectionState = _WS_CONNSTATE_READY
            else:
                if not self._base._pass:
                    # No password required, connection OK
                    self._connectionState = _WS_CONNSTATE_READY
                else:
                    # Hub did not sign password, unauthorized
                    self._session_errno = 401
                    if self._base.user == 'admin' and not self._hub.isRwAccess():
                        self._session_error = 'Authentication as admin failed'
                    else:
                        self._session_error = 'Password not set on remote hub'
                    self._connectionState = _WS_CONNSTATE_DEAD
            return
        if metatype == _USB_META_WS_ERROR:
            # ignore reserved first byte
            html_error: int = arr_bytes[3] + (arr_bytes[4] << 8)
            if html_error == 401:
                self._session_errno = 401
                self._wsError('Authentication failed')
            else:
                self._wsError("Remote hub closed connection with error %d" % html_error)

    async def _wsRecvData(self, arr_bytes: bytes) -> None:
        data: memoryview = memoryview(arr_bytes)
        ystream: int = arr_bytes[0] >> 3
        if ystream == _YSTREAM_TCP_NOTIF:
            pos: int = 1
            nextPos: int = arr_bytes.find(b'\n', pos)
            if self._notifCarryOverLen > 0 and nextPos >= pos:
                first_notif_end: int = self._notifCarryOverLen + nextPos - pos
                self._notifCarryOver[self._notifCarryOverLen:first_notif_end] = data[pos:nextPos]
                self._hub.handleNetNotification(memoryview(self._notifCarryOver)[:first_notif_end])
                self._notifCarryOverLen = 0
                pos = nextPos + 1
                nextPos: int = arr_bytes.find(b'\n', pos)
            while nextPos >= pos:
                self._hub.handleNetNotification(data[pos:nextPos])
                pos = nextPos + 1
                nextPos: int = arr_bytes.find(b'\n', pos)
            if pos < len(arr_bytes):
                remain = len(arr_bytes) - pos
                self._notifCarryOver[:remain] = data[pos:]
                self._notifCarryOverLen = remain
            return
        if self.websocket is None:
            return
        tcpchan: int = arr_bytes[0] & 7
        if ystream in (_YSTREAM_TCP, _YSTREAM_TCP_CLOSE, _YSTREAM_TCP_ASYNCCLOSE):
            if tcpchan > 3:
                self._wsError('bad tcpChan')
                return
            tcp_end: int = len(arr_bytes)
            yreq: Union[YRequest, None] = self.tcpChan[tcpchan]
            if yreq is None:
                self._wsError('tcpChan %d is closed(%d)' % (tcpchan, ystream))
                return
            if ystream == _YSTREAM_TCP_ASYNCCLOSE:
                # async close packet, check async signature byte
                tcp_end -= 1
                rcvId: int = arr_bytes[tcp_end]
                if yreq._async is None:
                    self._wsError('unexpected async close')
                    return
                if yreq._async != rcvId:
                    self._wsError('incorrect async close %d/%d on tcpChan %d' % (rcvId, yreq._async, tcpchan))
                    return
                # pop request from tcp channel
                self.tcpChan[tcpchan] = yreq.hubNext
                # signal request completion
                yreq._done.set()
                return
            eoh = yreq.appendBytes(data[1:tcp_end])
            if eoh >= 0:
                yreq._ready.set()

            # when the request is closed, proceed to next one and/or post result to caller
            if ystream == _YSTREAM_TCP_CLOSE:
                # synchronous close
                # pop request from tcp channel
                yreq.stopWatchdog()
                self.tcpChan[tcpchan] = yreq.hubNext
                if yreq._async is not None:
                    # no need to ack that close packet, we have sent the ack when aborting
                    # the request if the request was indeed coming from us
                    yreq._done.set()
                    return
                if yreq.status < HTTPState.RECV_HEADERS:
                    # close before completely sent, trigger disconnect
                    self._wsError('tcpclose during send')
                    yreq.status = HTTPState.ABORT
                    yreq._except = OSError('tcpclose during send')
                    yreq._ready.set()
                    yreq._done.set()
                    return
                # ack synchronous close
                frame: bytearray = bytearray(1)
                frame[0] = (_YSTREAM_TCP_CLOSE << 3) + tcpchan
                await self.websocket.send_bytes(frame)
                # signal request completion
                yreq._done.set()
            return
        if ystream == _YSTREAM_META:
            metatype: int = arr_bytes[1]
            if metatype == _USB_META_ACK_UPLOAD:
                tcpchan: int = arr_bytes[2]
                if tcpchan != 0 or self.tcpChan[0] is None:
                    return
                yreq: YRequest = self.tcpChan[tcpchan]
                ackBytes: int = arr_bytes[3] + (arr_bytes[4] << 8) + (arr_bytes[5] << 16) + (arr_bytes[6] << 24)
                ackTime: int = ticks_ms()
                if self._lastUploadAckTime != 0 and ackBytes > self._lastUploadAckBytes:
                    self._lastUploadAckBytes = ackBytes
                    self._lastUploadAckTime = ackTime
                    deltaBytes: int = ackBytes - self._lastUploadRateBytes
                    deltaTime: int = ticks_diff(ackTime, self._lastUploadRateTime)
                    if deltaTime < 500:
                        return  # wait more
                    if deltaTime < 1000 and deltaBytes < 65536:
                        return  # wait more
                    self._lastUploadRateBytes = ackBytes
                    self._lastUploadAckTime = ackTime
                    if yreq._dataCb:
                        yreq._dataCb(ackBytes, len(yreq._data))
                    newRate: float = deltaBytes * 1000 / deltaTime
                    self._uploadRate = round(0.8 * self._uploadRate + 0.3 * newRate)  # +10% intentionally
                else:
                    # First ack received
                    self._lastUploadAckBytes = ackBytes
                    self._lastUploadAckTime = ackTime
                    self._lastUploadRateBytes = ackBytes
                    self._lastUploadRateTime = ackTime
                    if yreq._dataCb:
                        yreq._dataCb(ackBytes, len(yreq._data))
                    # FIXME: Make sure upload resumes as soon as the first packet is confirmed
            return
        self._wsError('Bad message')

    async def waitForPendingQueries(self) -> None:
        for listHead in self.tcpChan:
            yreq: Union[YRequest, None] = listHead
            while yreq:
                await yreq.released()
                yreq = yreq.hubNext

    def dropAllPendingConnection(self):
        for listHead in self.tcpChan:
            yreq: Union[YRequest, None] = listHead
            while yreq:
                if yreq._async is None:
                    yreq.release()
                yreq = yreq.hubNext
        self.tcpChan = [None, None]

    def disconnectEngineNow(self, connID: str = ''):
        """
        Abort communication channel immediately

        If a connectionID is passed as argument, only abort the
        communication channel if the ID matched current connection
        """
        if _LOG_LEVEL >= 4:
            self._hub._yapi._Log("YWebSocketEngine disconnectEngineNow [" + connID + "]")
        if self.websocket is None:
            return
        closeConnID = connID if connID else self._hub._currentConnID
        websocket = self.websocket
        self.websocket = None
        websocket.release()
        self.dropAllPendingConnection()
        self._hub._currentConnID = ''
        self._hub._signalHubDisconnected(closeConnID)

    def makeRequest(self, method: str, rel_url: str, body: Union[xarray, None], msTimeout: int) -> YRequest:
        """
        Prepare a request to be sent to the hub, but do not send it yet.
        The method will be sent using method request() below
        """
        # Create an YRequest (aka ClientResponse) object, although we will not really send it over HTTP
        # but encode it within Websocket frames
        return YRequest(method, rel_url, {}, msTimeout, body)

    async def sendRequest(self, request: YRequest, tcpchan: int) -> ByteArrayLike:
        """
        Attempt to schedule the request passed as argument and to return the result
        If the request is async, the method should return None as soon as
        the async request has been sent to the hub
        """
        if self.websocket is None or self._hub.isDisconnecting() or self._connectionState != _WS_CONNSTATE_CONNECTED:
            raise OSError('WebSocket not connected')
        while len(self.tcpChan) < tcpchan:
            self.tcpChan.append(None)
        prevReq: YRequest = self.tcpChan[tcpchan]
        if request._async is not None:
            request._async = self._nextAsyncId
            self._nextAsyncId = self._nextAsyncId + 1
            if self._nextAsyncId >= 127:
                self._nextAsyncId = 48
        if prevReq is None:
            # no request currently active on this channel
            self.tcpChan[tcpchan] = request
        else:
            # channel is already active, simply queue request
            while prevReq.hubNext:
                prevReq = prevReq.hubNext
            prevReq.hubNext = request
        if self._task is None or self._task.done():
            # need to start a sending task
            self._task = self._hub.create_task(self._wsProcessSend(tcpchan))
        await request.ready()
        if request._async is not None:
            return b''
        if request.status == 401:
            raise YAPI_Exception(YAPI.UNAUTHORIZED, request.reason)
        if request.status != 200:
            raise YAPI_Exception(YAPI.IO_ERROR, request.reason)
        await request.released()
        return await request.read()

    async def _wsProcessSend(self, tcpchan: int) -> None:
        yreq: Union[YRequest, None] = self.tcpChan[tcpchan]
        while yreq:
            try:
                if self.websocket is None or self._hub.isDisconnecting() or self._connectionState != _WS_CONNSTATE_CONNECTED:
                    self.tcpChan[tcpchan] = yreq.hubNext
                    yreq.release()
                    yreq = yreq.hubNext
                    continue
                if yreq.status > HTTPState.SEND_DATA:
                    # request already sent
                    if yreq.hubNext is None:
                        # nothing more to be sent for now, we can leave
                        self._task = None
                        return
                    if yreq._async is None:
                        # synchronous request pending, we must wait for completion
                        await yreq._done.wait()
                    else:
                        # for now, wait until async requests are completed as well
                        await yreq._done.wait()
                    yreq = yreq.hubNext
                    continue

                # Send request
                if yreq.status < HTTPState.SEND_HEADERS:
                    yreq.startWatchdog(self)
                    yreq.status = HTTPState.SEND_HEADERS
                    if yreq.hasData() or not await self._sendShort(yreq, tcpchan):
                        yreq.wsPrepHeaders()
                        if tcpchan == 0:
                            self._uploadPos = 0
                            self._lastUploadAckBytes = 0
                            self._lastUploadAckTime = 0
                        if yreq.hasData():
                            await self._sendView(yreq.getWsHeaderView, tcpchan)
                            yreq.prepRecv()
                            if yreq.status < HTTPState.SEND_DATA:
                                yreq.status = HTTPState.SEND_DATA
                            await self._sendView(yreq.getDataView, tcpchan)
                        else:
                            await self._sendView(yreq.getWsHeaderView, tcpchan, yreq._async)
                            yreq.prepRecv()
                    if yreq._async is not None:
                        # asynchronous request completed
                        # we can stop the watchdog early as nobody will be waiting on the request
                        yreq.stopWatchdog()
                        # asynchronous requests trigger the _ready Future as soon as fully sent
                        yreq._ready.set()
                    if yreq.status < HTTPState.RECV_HEADERS:
                        yreq.status = HTTPState.RECV_HEADERS
            except BaseException as exc:
                print_exception(exc)
                if not yreq._ready.is_set():
                    yreq.stopWatchdog()
                    yreq.status = HTTPState.ABORT
                    yreq._except = exc
                    yreq._ready.set()
                yreq = yreq.hubNext
        self._task = None

    # Internal method to attempt to send a short GET request to a websocket TCP stream
    # Return True iff a short send was possible
    async def _sendShort(self, yreq: YRequest, tcpchan: int) -> bool:
        targetLen: int = len(yreq._target)
        if targetLen > 125 - 10:
            return False
        if yreq._async is None:
            shortframe: memoryview = memoryview(self._frame)[:targetLen + 9]
            shortframe[0] = (_YSTREAM_TCP << 3) + tcpchan
            shortframe[-4:] = b'\r\n\r\n'
        else:
            shortframe: memoryview = memoryview(self._frame)[:targetLen + 10]
            shortframe[0] = (_YSTREAM_TCP_ASYNCCLOSE << 3) + tcpchan
            shortframe[-5:-1] = b'\r\n\r\n'
            shortframe[-1] = yreq._async
        shortframe[1:5] = b'GET '
        shortframe[5:5 + targetLen] = yreq._target.encode('latin-1')
        yreq.prepRecv()
        await self.websocket.send_bytes(shortframe)
        return True

    # Internal method to send a large binary buffer (via callback) to the websocket
    async def _sendView(self, dataViewer: Callable[[int, int], bytes], tcpchan: int, asyncId: Union[int, None] = None) -> None:
        sent: int = 0
        frame: bytearray = self._frame
        frame[0] = (_YSTREAM_TCP << 3) + tcpchan
        # Special handling for first two frames, in case of large content
        # on a YoctoHub, the input FIFO is limited to 192, and we can only
        # accept a frame if it fits entirely in the input FIFO. So make sure
        # the beginning of a request gets delivered entirely
        blk: bytes = dataViewer(sent, 124)
        size: int = len(blk)
        if size == 124:
            frame[1:] = blk
            await self.websocket.send_bytes(frame)
            sent += size
            blk = dataViewer(sent, 67)
            size = len(blk)
            if size == 67:
                shortframe: memoryview = memoryview(frame)[:size + 1]
                shortframe[1:] = blk
                await self.websocket.send_bytes(shortframe)
                sent += size
                # prepare to read 124 bytes again, if possible
                blk = dataViewer(sent, 124)
                size = len(blk)
        # Send remaining data by frames of 124 bytes as long as possible
        # On TCP channel 0, perform throttling on large uploads
        absPos: int = self._uploadPos
        endPos: int = 2108
        while size == 124:
            frame[1:] = blk
            await self.websocket.send_bytes(frame)
            sent += size
            if tcpchan == 0:
                # for large uploads, when we cross a segment boundary, compute next
                # block size and wait if needed for bandwidth throttling
                while absPos + sent > endPos:  # while used as "if ... repeat until ..."
                    bytesOnTheAir: int = absPos - self._lastUploadAckBytes
                    timeOnTheAir: int = ticks_diff(ticks_ms(), self._lastUploadAckTime)
                    uploadRate: float = self._uploadRate
                    toBeSent: int = round(2 * uploadRate + 1024 - bytesOnTheAir + (uploadRate * timeOnTheAir / 1000))
                    if toBeSent + bytesOnTheAir > _DEFAULT_TCP_MAX_WINDOW_SIZE:
                        toBeSent = _DEFAULT_TCP_MAX_WINDOW_SIZE - bytesOnTheAir
                    if toBeSent >= 64:
                        endPos = absPos + toBeSent
                        break
                    waitTime: float = max(0.002, (128 - toBeSent) / uploadRate)
                    await asyncio.sleep(waitTime)
            blk = dataViewer(sent, 124)
            size = len(blk)
        # Complete sending with a short frame
        if asyncId is not None:
            shortframe: memoryview = memoryview(frame)[:size + 2]
            shortframe[0] = (_YSTREAM_TCP_ASYNCCLOSE << 3) + tcpchan
            if size > 0:
                shortframe[1:-1] = blk
            shortframe[-1] = asyncId
            await self.websocket.send_bytes(shortframe)
        elif size > 0:
            shortframe: memoryview = memoryview(frame)[:size + 1]
            shortframe[1:] = blk
            await self.websocket.send_bytes(shortframe)
        if tcpchan == 0:
            self._uploadPos += sent + size


#################################################################################
#                                                                               #
#                                YFunction                                      #
#                                                                               #
#################################################################################

if _IS_MICROPYTHON:
    YFunctionValueCallback = Union[Callable, None]

# --- (generated code: YFunction class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YFunctionValueCallback = Union[Callable[['YFunction', str], Any], None]
    except TypeError:
        YFunctionValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YFunction:
    """
    This is the parent class for all public objects representing device functions documented in
    the high-level programming API. This abstract class does all the real job, but without
    knowledge of the specific function attributes.

    Instantiating a child class of YFunction does not cause any communication.
    The instance simply keeps track of its function identifier, and will dynamically bind
    to a matching device at the time it is really being used to read or set an attribute.
    In order to allow true hot-plug replacement of one device by another, the binding stay
    dynamic through the life of the object.

    The YFunction class implements a generic high-level cache for the attribute values of
    the specified function, pre-parsed from the REST API string.

    """
    # --- (end of generated code: YFunction class start)
    if not _IS_MICROPYTHON:
        FRIENDLYNAME_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (generated code: YFunction return codes)
        LOGICALNAME_INVALID: Final[str] = YAPI.INVALID_STRING
        ADVERTISEDVALUE_INVALID: Final[str] = YAPI.INVALID_STRING
        # --- (end of generated code: YFunction return codes)

    _yapi: YAPIContext
    _className: str
    _func: str
    _hwId: Union[HwId, None]
    _dev: Union[YDevice, None]
    _lastErrorType: int
    _lastErrorMsg: str
    _userData: Any
    _cache: Union[xdict, None]
    # --- (generated code: YFunction attributes declaration)
    _valueCallback: YFunctionValueCallback
    _cacheExpiration: int
    # --- (end of generated code: YFunction attributes declaration)

    def __init__(self, yctx: YAPIContext, classname: str, func: str):
        self._yapi = yctx
        self._className = classname
        self._func = func
        self._hwId = None
        self._dev = None
        self._lastErrorType = YAPI.SUCCESS
        self._lastErrorMsg = ""
        self._userData = None
        self._cache = None
        # --- (generated code: YFunction constructor)
        self._valueCallback = None
        self._cacheExpiration = 0
        # --- (end of generated code: YFunction constructor)
        yctx._addToCache(classname, func, self)

    def __repr__(self) -> str:
        return "Y%s('%s')" % (self._className, self._func)

    def _throw(self, errType: int, errMsg: str) -> int:
        self._lastErrorType = errType
        self._lastErrorMsg = errMsg
        return self._yapi._throw(errType, errMsg)

    def _rethrow(self, ex: YAPI_Exception) -> int:
        self._lastErrorType = ex.errorType
        self._lastErrorMsg = ex.errorMessage
        return self._yapi._rethrow(ex)

    # Retrieve the function HwId from yellow pages if available
    def get_hwId(self) -> HwId:
        if not self._hwId:
            self._hwId = self._yapi._resolve(self._className, self._func)
        return self._hwId

    # Retrieve the YDevice object hosting the function
    # May cause an internal updateDeviceList if the device is currently unknown
    # On failure, raise an exception
    async def _getDev(self) -> YDevice:
        dev: Union[YDevice, None] = self._dev
        if not dev:
            try:
                hwid = self.get_hwId()
                if hwid:
                    dev: Union[YDevice, None] = self._yapi._getDevice(hwid.module)
            except YAPI_Exception as ex:
                if not self._yapi._hubs:
                    raise
        if not dev or not dev.hub:
            # try to force a device list update to check if the device arrived in between
            errmsg: YRefParam = YRefParam()
            await self._yapi._updateDeviceList_internal(True, errmsg)
            hwid = self.get_hwId()
            dev = self._yapi._getDevice(hwid.module)
            if dev is None:
                raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND, "Device [%s] not online" % hwid.module)
        self._dev = dev
        return dev

    def get_userData(self) -> Any:
        """
        Returns the value of the userData attribute, as previously stored using method
        set_userData.
        This attribute is never touched directly by the API, and is at disposal of the caller to
        store a context.

        @return the object stored previously by the caller.
        """
        return self._userData

    def set_userData(self, data: Any) -> None:
        """
        Stores a user context provided as argument in the userData attribute of the function.
        This attribute is never touched by the API, and is at disposal of the caller to store a context.

        @param data : any kind of object to be stored
        @noreturn
        """
        self._userData = data

    def get_friendlyName(self) -> str:
        """
        Returns a global identifier of the function in the format MODULE_NAME&#46;FUNCTION_NAME.
        The returned string uses the logical names of the module and of the function if they are defined,
        otherwise the serial number of the module and the hardware identifier of the function
        (for example: MyCustomName.relay1)

        @return a string that uniquely identifies the function using logical names
                (ex: MyCustomName.relay1)

        On failure, throws an exception or returns  YFunction.FRIENDLYNAME_INVALID.
        """
        devrec: Union[xdict,None] = None
        hwid: Union[HwId,None] = self.get_hwId()
        serial: str = self._func
        if hwid:
            serial = hwid.module
            devrec = self._yapi._devRecBySn[serial]
        if not devrec:
            self._throw(YAPI.DEVICE_NOT_FOUND, "Device [%s] not online" % serial)
            return YFunction.FRIENDLYNAME_INVALID
        devname: str = devrec['logicalName']
        devdesc: str = devname if devname else serial
        if self._className == "Module":
            return devdesc + ".module"
        else:
            fundesc: str = ''
            if self._cache:
                fundesc = self._cache.get('logicalName', '')
            else:
                funrec: Union[xdict,None] = self._yapi._findFunRecByHwId(hwid)
                if funrec:
                    fundesc = funrec.get("logicalName", '')
            return devdesc + "." + (fundesc if fundesc else hwid.function)

    async def _updateValueCallback(self, callback: YFunctionValueCallback) -> str:
        if callback:
            await self._yapi._UpdateValueCallbackList(self, True)
        else:
            await self._yapi._UpdateValueCallbackList(self, False)
        self._valueCallback = callback
        if callback and await self.isOnline():
            return self._cache['advertisedValue']
        else:
            return ""

    async def registerValueCallback(self, callback: YFunctionValueCallback) -> int:
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
        val: str = await self._updateValueCallback(callback)
        if val:
            # Immediately invoke value callback with current value
            retval = self._valueCallback(self, val)
            if asyncio.iscoroutine(retval):
                await retval
        return YAPI.SUCCESS

    # Retrieve an attribute value from cache, with cache auto-refresh
    async def _fromCache(self, attrName: str):
        if ticks_past(self._cacheExpiration) or not self._cacheExpiration:
            if await self.load(self._yapi._defaultCacheValidity) != YAPI.SUCCESS:
                return None
        return self._cache.get(attrName)

    # Retrieve an attribute value from cache, without auto-refresh
    async def _lazyCache(self, attrName: str):
        if not self._cacheExpiration:
            if await self.load(self._yapi._defaultCacheValidity) != YAPI.SUCCESS:
                return None
        return self._cache.get(attrName)

    # --- (generated code: YFunction implementation)
    @classmethod
    def FindFunction(cls, func: str) -> YFunction:
        """
        Retrieves a function for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YFunction.isOnline() to test if the function is
        indeed online at a given time. In case of ambiguity when looking for
        a function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the function, for instance
                MyDevice..

        @return a YFunction object allowing you to drive the function.
        """
        return cls.FindFunctionInContext(YAPI, func)

    @classmethod
    def FindFunctionInContext(cls, yctx: YAPIContext, func: str) -> YFunction:
        """
        Retrieves a function for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the function is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YFunction.isOnline() to test if the function is
        indeed online at a given time. In case of ambiguity when looking for
        a function by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the function, for instance
                MyDevice..

        @return a YFunction object allowing you to drive the function.
        """
        obj: Union[YFunction, None] = yctx._findInCache('Function', func)
        if obj:
            return obj
        return YFunction(yctx, 'Function', func)

    @classmethod
    def FirstFunction(cls) -> Union[YFunction, None]:
        """
        comment from .yc definition
        """
        return cls.FirstFunctionInContext(YAPI)

    @classmethod
    def FirstFunctionInContext(cls, yctx: YAPIContext) -> Union[YFunction, None]:
        """
        comment from .yc definition
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Function')
        if hwid:
            return cls.FindFunctionInContext(yctx, hwid2str(hwid))
        return None

    def nextFunction(self) -> Union[YFunction, None]:
        """
        comment from .yc definition
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Function', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindFunctionInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_logicalName(self) -> str:
        """
        Returns the logical name of the function.

        @return a string corresponding to the logical name of the function

        On failure, throws an exception or returns YFunction.LOGICALNAME_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("logicalName")
        if json_val is None:
            return YFunction.LOGICALNAME_INVALID
        return json_val

    async def set_logicalName(self, newval: str) -> int:
        """
        Changes the logical name of the function. You can use yCheckLogicalName()
        prior to this call to make sure that your parameter is valid.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : a string corresponding to the logical name of the function

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        if not YAPI.CheckLogicalName(newval):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid name :" + newval)
            return YAPI.INVALID_ARGUMENT
        rest_val = newval
        return await self._setAttr("logicalName", rest_val)

    async def get_advertisedValue(self) -> str:
        """
        Returns a short string representing the current state of the function.

        @return a string corresponding to a short string representing the current state of the function

        On failure, throws an exception or returns YFunction.ADVERTISEDVALUE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("advertisedValue")
        if json_val is None:
            return YFunction.ADVERTISEDVALUE_INVALID
        return json_val

    async def set_advertisedValue(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("advertisedValue", rest_val)

    async def muteValueCallbacks(self) -> int:
        """
        Disables the propagation of every new advertised value to the parent hub.
        You can use this function to save bandwidth and CPU on computers with limited
        resources, or to prevent unwanted invocations of the HTTP callback.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_advertisedValue("SILENT")

    async def unmuteValueCallbacks(self) -> int:
        """
        Re-enables the propagation of every new advertised value to the parent hub.
        This function reverts the effect of a previous call to muteValueCallbacks().
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_advertisedValue("")

    async def loadAttribute(self, attrName: str) -> str:
        """
        Returns the current value of a single function attribute, as a text string, as quickly as
        possible but without using the cached value.

        @param attrName : the name of the requested attribute

        @return a string with the value of the the attribute

        On failure, throws an exception or returns an empty string.
        """
        url: str
        attrVal: xarray
        url = "api/%s/%s" % (await self.get_functionId(), attrName)
        attrVal = await self._download(url)
        return attrVal.decode('latin-1')

    async def get_serialNumber(self) -> str:
        """
        Returns the serial number of the module, as set by the factory.

        @return a string corresponding to the serial number of the module, as set by the factory.

        On failure, throws an exception or returns YFunction.SERIALNUMBER_INVALID.
        """
        m: Union[YModule, None]
        m = await self.get_module()
        return await m.get_serialNumber()

    def _parserHelper(self) -> int:
        return 0

    def _is_valid_pass(self, passwd: str) -> bool:
        tmp: str
        if len(passwd) > YAPI.HASH_BUF_SIZE:
            tmp = "Password too long (max %d chars) :%s" % (YAPI.HASH_BUF_SIZE, passwd)
            self._throw(YAPI.INVALID_ARGUMENT, tmp)
            return False
        if passwd.find("@") >=0:
            self._throw(YAPI.INVALID_ARGUMENT, "Character @ is not allowed in password")
            return False
        if passwd.find("/") >=0:
            self._throw(YAPI.INVALID_ARGUMENT, "Character / is not allowed in password")
            return False
        return True

    # --- (end of generated code: YFunction implementation)

    async def isReadOnly(self) -> bool:
        """
        Indicates whether changes to the function are prohibited or allowed.
        Returns true if the function is blocked by an admin password
        or if the function is not available.

        @return true if the function is write-protected or not online.
        """
        try:
            dev: YDevice = await self._getDev()
            hub: YGenericHub = dev.hub
            return await hub.isReadOnly()
        except YAPI_Exception:
            return False

    async def get_hardwareId(self) -> str:
        """
        Returns the unique hardware identifier of the function in the form SERIAL.FUNCTIONID.
        The unique hardware identifier is composed of the device serial
        number and of the hardware identifier of the function (for example RELAYLO1-123456.relay1).

        @return a string that uniquely identifies the function (ex: RELAYLO1-123456.relay1)

        On failure, throws an exception or returns  YFunction.HARDWAREID_INVALID.
        """
        return hwid2str(self.get_hwId())

    async def get_functionId(self) -> str:
        """
        Returns the hardware identifier of the function, without reference to the module. For example
        relay1

        @return a string that identifies the function (ex: relay1)

        On failure, throws an exception or returns  YFunction.FUNCTIONID_INVALID.
        """
        return self.get_hwId().function

    async def isOnline(self) -> bool:
        """
        Checks if the function is currently reachable, without raising any error.
        If there is a cached value for the function in cache, that has not yet
        expired, the device is considered reachable.
        No exception is raised if there is an error while trying to contact the
        device hosting the function.

        @return true if the function can be reached, and false otherwise
        """
        # A valid value in cache means that the device is online
        if ticks_past(self._cacheExpiration) or not self._cacheExpiration:
            try:
                # Check that the function is available without throwing exceptions
                await self.load(self._yapi._defaultCacheValidity)
            except YAPI_Exception:
                return False
        return True

    def get_errorType(self) -> int:
        """
        Returns the numerical error code of the latest error with the function.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a number corresponding to the code of the latest error that occurred while
                using the function object
        """
        return self._lastErrorType

    def get_errorMessage(self) -> str:
        """
        Returns the error message of the latest error with the function.
        This method is mostly useful when using the Yoctopuce library with
        exceptions disabled.

        @return a string corresponding to the latest error message that occured while
                using the function object
        """
        return self._lastErrorMsg

    async def clearCache(self):
        """
        Invalidates the cache. Invalidates the cache of the function attributes. Forces the
        next call to get_xxx() or loadxxx() to use values that come from the device.

        @noreturn
        """
        try:
            dev: YDevice = await self._getDev()
            dev.clearCache()
        except YAPI_Exception:
            pass
        if self._cacheExpiration:
            self._cacheExpiration = ticks_ms()

    async def load(self, msValidity: int) -> int:
        """
        Preloads the function cache with a specified validity duration.
        By default, whenever accessing a device, all function attributes
        are kept in cache for the standard duration (5 ms). This method can be
        used to temporarily mark the cache as valid for a longer period, in order
        to reduce network traffic for instance.

        @param msValidity : an integer corresponding to the validity attributed to the
                loaded function parameters, in milliseconds

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        try:
            self._cache = await self._devRequest("")
            self._cacheExpiration = ticks_add(ticks_ms(), msValidity) | 1
            self._parserHelper()
            return YAPI.SUCCESS
        except YAPI_Exception as e:
            return self._rethrow(e)

    async def get_module(self) -> YModule:
        """
        Gets the YModule object for the device on which the function is located.
        If the function cannot be located on any module, the returned instance of
        YModule is not shown as on-line.

        @return an instance of YModule
        """
        hwid = self.get_hwId()
        if hwid:
            return YModule.FindModuleInContext(self._yapi, hwid.module + '.module')
        dotOfs: int = self._func.find('.')
        if dotOfs >= 0:
            serial: str = self._func[:dotOfs]
            return YModule.FindModuleInContext(self._yapi, serial + '.module')
        try:
            serial: str = self._yapi._resolve('Module', self._func).module
            return YModule.FindModuleInContext(self._yapi, serial + '.module')
        except YAPI_Exception:
            pass
        # device not resolved for now, force a communication for a last chance resolution
        try:
            if await self.load(self._yapi._defaultCacheValidity) == YAPI.SUCCESS:
                hwid = self.get_hwId()
                return YModule.FindModuleInContext(self._yapi, hwid.module + '.module')
        except YAPI_Exception:
            pass
        return YModule.FindModuleInContext(self._yapi, 'module_of_{}_{}'.format(self._className, self._func))

    @staticmethod
    def _escapeAttr(newval: str) -> str:
        encoded: bytes = newval.encode(YAPI.DefaultEncoding)
        vallen: int = len(encoded)
        escount: int = 0
        for b in encoded:
            if b in b'%=&+ ' or b < 32 or b >= 127:
                escount += 1
        if escount == 0:
            return newval
        escaped: bytearray = bytearray(vallen + 2 * escount)
        escount = 0
        for b in encoded:
            if b in b'%=&+ ' or b < 32 or b >= 127:
                hexstr: str = '%%%02X' % b
                escaped[escount:escount + 3] = hexstr.encode('ascii')
                escount += 3
            else:
                escaped[escount] = b
                escount += 1
        return escaped.decode('ascii')

    async def _setAttr(self, attrname: str, newval: str) -> int:
        """
        Change the value of an attribute on a device, and update cache on the fly
        Note: the function cache is a typed (parsed) cache, contrarily to the agnostic device cache
        """
        if newval is None:
            return self._throw(YAPI.INVALID_ARGUMENT, "Undefined value to set for attribute " + attrname)
        extra: str = "/" + attrname + "?" + attrname + "=" + self._escapeAttr(newval) + "&."
        try:
            await self._devRequest(extra)
            if self._cacheExpiration:
                self._cacheExpiration = ticks_ms()
            return YAPI.SUCCESS
        except YAPI_Exception as e:
            return self._rethrow(e)

    async def _request(self, req_first_line: str, body: Union[xarray, None]) -> xarray:
        try:
            dev: YDevice = await self._getDev()
            res = await dev.requestHTTPSync(req_first_line, body)
            if isinstance(res, xarray):
                return res
            return xbytearray(res)
        except YAPI_Exception as e:
            self._rethrow(e)
            return xbytearray(0)

    async def _uploadEx(self, path: str, content: xarray) -> xarray:
        try:
            dev: YDevice = await self._getDev()
            res = await dev.requestHTTPUploadEx(path, content)
            if isinstance(res, xarray):
                return res
            return xbytearray(res)
        except YAPI_Exception as e:
            self._rethrow(e)
            return xbytearray(0)

    async def _upload(self, path: str, content: Union[xarray, bytearray, bytes]) -> int:
        try:
            dev: YDevice = await self._getDev()
            return await dev.requestHTTPUpload(path, content)
        except YAPI_Exception as e:
            return self._rethrow(e)

    async def _download(self, url: str) -> xarray:
        try:
            request: str = url
            return await self._request(request, None)
        except YAPI_Exception as e:
            self._rethrow(e)
            return xbytearray(0)

    @staticmethod
    def _json_get_key(jsonBin: xarray, key: str) -> str:
        obj: dict = json.load(xStringIO(jsonBin, 'latin-1'))
        val = obj.get(key)
        if val is not None:
            return str(val)
        raise YAPI_Exception(YAPI.IO_ERROR, "No key %s in JSON struct" % key)

    @staticmethod
    def _json_get_string(jsonBin: xarray) -> str:
        res: str = json.load(xStringIO(jsonBin, 'latin-1'))
        return res

    @staticmethod
    def _json_get_array(jsonBin: xarray) -> list[xarray]:
        obj: list = json.load(xStringIO(jsonBin, 'latin-1'))
        # type cheat: this function normally returns a list of strings,
        #             but this would eat too much heap space for micropython.
        #             => reduce type checks by declaring an untyped list...
        res: list = []
        for val in obj:
            res.append(xbytearray(json.dumps(val), 'latin-1'))
        return res

    @staticmethod
    def _get_json_path(jsonBin: xarray, path: str) -> xarray:
        xio = xStringIO(jsonBin, 'latin-1')
        obj: dict = json.load(xio)
        paths: list[str] = path.split('|')
        for subpath in paths:
            if isinstance(obj, list):
                ofs: int = YAPI._atoi(subpath)
                if ofs < len(obj):
                    obj = obj[ofs]
                else:
                    return xbytearray()
            else:
                obj = obj.get(subpath)
                if obj is None:
                    return xbytearray()
        json_str = json.dumps(obj, ensure_ascii=False)
        return xbytearray(json_str, 'latin-1')

    @staticmethod
    def _decode_json_string(jsonBin: xarray) -> str:
        if len(jsonBin) == 0:
            return ''
        return json.load(xStringIO(jsonBin, 'latin-1'))

    @staticmethod
    def _decode_json_int(jsonBin: xarray) -> int:
        res: int = json.load(xStringIO(jsonBin, 'latin-1'))
        return res

    async def _devRequest(self, extra: str) -> Union[xdict, None]:
        # Load and parse the REST API for a function given by class name and identifier, possibly applying changes
        # Device cache will be preloaded when loading function Module and  leveraged for other modules
        dev: YDevice = await self._getDev()
        if not dev.hub:
            raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND, "Device [%s] not online" % self._hwId.module)
        funcId: str = self._hwId.function
        loadval: Union[xdict, None] = None
        if extra == "":
            # use a cached API string, without reloading unless module is requested
            jsonval: xdict = await dev.requestAPI()
            loadval = jsonval.get(funcId)
            if not loadval:
                raise YAPI_Exception(YAPI.IO_ERROR,
                                     "Request failed, could not parse API result for " + dev._serial)
        if loadval is None:
            # request specified function only to minimize traffic
            if extra == "":
                httpreq: str = "/api/%s.json" % funcId
                yreq: xarray = await dev.requestHTTPSync(httpreq, None)
                try:
                    loadval: xdict = yreq.json()
                except YAPI_Exception:
                    raise YAPI_Exception(YAPI.IO_ERROR,
                                         "Request failed, could not parse API result for " + httpreq)
            else:
                httpreq = "/api/%s%s" % (funcId, extra)
                await dev.requestHTTPAsync(httpreq, None)
                dev.clearCache()
                return None
        return loadval


#################################################################################
#                                                                               #
#                      YModule, YFirmwareUpdate                                 #
#                                                                               #
#################################################################################

# --- (generated code: YModule class start)
# noinspection PyRedundantParentheses
# noinspection PyUnusedLocal
# noinspection PyProtectedMember
class YModule(YFunction):
    """
    The YModule class can be used with all Yoctopuce USB devices.
    It can be used to control the module global parameters, and
    to enumerate the functions provided by each module.

    """
    # --- (end of generated code: YModule class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YModule return codes)
        PRODUCTNAME_INVALID: Final[str] = YAPI.INVALID_STRING
        SERIALNUMBER_INVALID: Final[str] = YAPI.INVALID_STRING
        PRODUCTID_INVALID: Final[int] = YAPI.INVALID_UINT
        PRODUCTRELEASE_INVALID: Final[int] = YAPI.INVALID_UINT
        FIRMWARERELEASE_INVALID: Final[str] = YAPI.INVALID_STRING
        LUMINOSITY_INVALID: Final[int] = YAPI.INVALID_UINT
        UPTIME_INVALID: Final[int] = YAPI.INVALID_LONG
        USBCURRENT_INVALID: Final[int] = YAPI.INVALID_UINT
        REBOOTCOUNTDOWN_INVALID: Final[int] = YAPI.INVALID_INT
        USERVAR_INVALID: Final[int] = YAPI.INVALID_INT
        PERSISTENTSETTINGS_LOADED: Final[int] = 0
        PERSISTENTSETTINGS_SAVED: Final[int] = 1
        PERSISTENTSETTINGS_MODIFIED: Final[int] = 2
        PERSISTENTSETTINGS_INVALID: Final[int] = -1
        BEACON_OFF: Final[int] = 0
        BEACON_ON: Final[int] = 1
        BEACON_INVALID: Final[int] = -1
        # --- (end of generated code: YModule return codes)

    # --- (generated code: YModule attributes declaration)
    _logCallback: YModuleLogCallback
    _confChangeCallback: YModuleConfigChangeCallback
    _beaconCallback: YModuleBeaconCallback
    # --- (end of generated code: YModule attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, "Module", func)
        # --- (generated code: YModule constructor)
        # --- (end of generated code: YModule constructor)
        self._logCallback = None
        self._confChangeCallback = None
        self._beaconCallback = None

    @staticmethod
    async def _updateModuleCallbackList(func: YModule, add: bool):
        await func._yapi._UpdateModuleCallbackList(func, add)

    @staticmethod
    def _flattenJsonStruct(jsoncomplex: xarray) -> xarray:
        decoded = json.load(xStringIO(jsoncomplex, 'latin-1'))
        res: xbytearray = xbytearray(1024)
        res[:1] = b'['
        isnext: bool = False
        sep: str = ''
        pos: int = 1
        for function_name in decoded:
            if function_name == 'services':
                continue
            function_attrs = decoded[function_name]
            for attr_name in function_attrs:
                attr_value = function_attrs[attr_name]
                if attr_value is None or isinstance(attr_value, dict):
                    continue
                flat: str = function_name + '/' + attr_name + '=' + str(attr_value)
                quoted: bytes = json.dumps(flat).encode('utf-8')
                if isnext:
                    res[pos:pos + 1] = b','
                    pos += 1
                res[pos:pos + len(quoted)] = quoted
                pos += len(quoted)
                isnext = True
        res[pos:pos + 1] = b']'
        return res[:pos + 1]

    async def get_subDevices(self) -> list[str]:
        """
        Returns the serial number of the YoctoHub on which this module is connected.
        If the module is connected by USB, or if the module is the root YoctoHub, an
        empty string is returned.

        @return a string with the serial number of the YoctoHub or an empty string
        """
        dev: YDevice = await self._getDev()
        hub: YGenericHub = dev.hub
        return hub.get_subDeviceOf(await self.get_serialNumber())

    async def get_parentHub(self) -> str:
        """
        Returns the serial number of the YoctoHub on which this module is connected.
        If the module is connected by USB, or if the module is the root YoctoHub, an
        empty string is returned.

        @return a string with the serial number of the YoctoHub or an empty string
        """
        dev: YDevice = await self._getDev()
        hub: YGenericHub = dev.hub
        hubSerial: str = hub.getSerialNumber()
        if hubSerial == await self.get_serialNumber():
            return ''
        return hubSerial

    async def get_url(self) -> str:
        """
        Returns the URL used to access the module. If the module is connected by USB, the
        string 'usb' is returned.

        @return a string with the URL of the module.
        """
        dev: YDevice = await self._getDev()
        hub: YGenericHub = dev.hub
        return hub.get_urlOf(await self.get_serialNumber())

    async def _startStopDevLog(self, serial: str, start: Union[bool,YModuleLogCallback]) -> None:
        ydev: YDevice = await self._getDev()
        ydev.registerLogCallback(self._logCallback if start else None)

    # --- (generated code: YModule implementation)
    @classmethod
    def FindModule(cls, func: str) -> YModule:
        """
        Allows you to find a module from its serial number or from its logical name.

        This function does not require that the module is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YModule.isOnline() to test if the module is
        indeed online at a given time. In case of ambiguity when looking for
        a module by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.


        If a call to this object's is_online() method returns FALSE although
        you are certain that the device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string containing either the serial number or
                the logical name of the desired module

        @return a YModule object allowing you to drive the module
                or get additional information on the module.
        """
        return cls.FindModuleInContext(YAPI, func)

    @classmethod
    def FindModuleInContext(cls, yctx: YAPIContext, func: str) -> YModule:
        """
        Retrieves a module for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the module is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YModule.isOnline() to test if the module is
        indeed online at a given time. In case of ambiguity when looking for
        a module by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the module, for instance
                MyDevice.module.

        @return a YModule object allowing you to drive the module.
        """
        obj: Union[YModule, None] = yctx._findInCache('Module', func)
        if obj:
            return obj
        return YModule(yctx, func)

    @classmethod
    def FirstModule(cls) -> Union[YModule, None]:
        """
        Starts the enumeration of modules currently accessible.
        Use the method YModule.nextModule() to iterate on the
        next modules.

        @return a pointer to a YModule object, corresponding to
                the first module currently online, or a None pointer
                if there are none.
        """
        return cls.FirstModuleInContext(YAPI)

    @classmethod
    def FirstModuleInContext(cls, yctx: YAPIContext) -> Union[YModule, None]:
        """
        comment from .yc definition
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Module')
        if hwid:
            return cls.FindModuleInContext(yctx, hwid2str(hwid))
        return None

    def nextModule(self) -> Union[YModule, None]:
        """
        Continues the module enumeration started using yFirstModule().
        Caution: You can't make any assumption about the returned modules order.
        If you want to find a specific module, use Module.findModule()
        and a hardwareID or a logical name.

        @return a pointer to a YModule object, corresponding to
                the next module found, or a None pointer
                if there are no more modules to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Module', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindModuleInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_productName(self) -> str:
        """
        Returns the commercial name of the module, as set by the factory.

        @return a string corresponding to the commercial name of the module, as set by the factory

        On failure, throws an exception or returns YModule.PRODUCTNAME_INVALID.
        """
        json_val: Union[str, None] = await self._lazyCache("productName")
        if json_val is None:
            return YModule.PRODUCTNAME_INVALID
        return json_val

    async def get_serialNumber(self) -> str:
        """
        Returns the serial number of the module, as set by the factory.

        @return a string corresponding to the serial number of the module, as set by the factory

        On failure, throws an exception or returns YModule.SERIALNUMBER_INVALID.
        """
        json_val: Union[str, None] = await self._lazyCache("serialNumber")
        if json_val is None:
            return YModule.SERIALNUMBER_INVALID
        return json_val

    async def get_productId(self) -> int:
        """
        Returns the USB device identifier of the module.

        @return an integer corresponding to the USB device identifier of the module

        On failure, throws an exception or returns YModule.PRODUCTID_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("productId")
        if json_val is None:
            return YModule.PRODUCTID_INVALID
        return json_val

    async def get_productRelease(self) -> int:
        """
        Returns the release number of the module hardware, preprogrammed at the factory.
        The original hardware release returns value 1, revision B returns value 2, etc.

        @return an integer corresponding to the release number of the module hardware, preprogrammed at the factory

        On failure, throws an exception or returns YModule.PRODUCTRELEASE_INVALID.
        """
        json_val: Union[int, None] = await self._lazyCache("productRelease")
        if json_val is None:
            return YModule.PRODUCTRELEASE_INVALID
        return json_val

    async def get_firmwareRelease(self) -> str:
        """
        Returns the version of the firmware embedded in the module.

        @return a string corresponding to the version of the firmware embedded in the module

        On failure, throws an exception or returns YModule.FIRMWARERELEASE_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("firmwareRelease")
        if json_val is None:
            return YModule.FIRMWARERELEASE_INVALID
        return json_val

    async def get_persistentSettings(self) -> int:
        """
        Returns the current state of persistent module settings.

        @return a value among YModule.PERSISTENTSETTINGS_LOADED, YModule.PERSISTENTSETTINGS_SAVED and
        YModule.PERSISTENTSETTINGS_MODIFIED corresponding to the current state of persistent module settings

        On failure, throws an exception or returns YModule.PERSISTENTSETTINGS_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("persistentSettings")
        if json_val is None:
            return YModule.PERSISTENTSETTINGS_INVALID
        return json_val

    async def set_persistentSettings(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("persistentSettings", rest_val)

    async def get_luminosity(self) -> int:
        """
        Returns the luminosity of the  module informative LEDs (from 0 to 100).

        @return an integer corresponding to the luminosity of the  module informative LEDs (from 0 to 100)

        On failure, throws an exception or returns YModule.LUMINOSITY_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("luminosity")
        if json_val is None:
            return YModule.LUMINOSITY_INVALID
        return json_val

    async def set_luminosity(self, newval: int) -> int:
        """
        Changes the luminosity of the module informative leds. The parameter is a
        value between 0 and 100.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : an integer corresponding to the luminosity of the module informative leds

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("luminosity", rest_val)

    async def get_beacon(self) -> int:
        """
        Returns the state of the localization beacon.

        @return either YModule.BEACON_OFF or YModule.BEACON_ON, according to the state of the localization beacon

        On failure, throws an exception or returns YModule.BEACON_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("beacon")
        if json_val is None:
            return YModule.BEACON_INVALID
        return json_val

    async def set_beacon(self, newval: int) -> int:
        """
        Turns on or off the module localization beacon.

        @param newval : either YModule.BEACON_OFF or YModule.BEACON_ON

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("beacon", rest_val)

    async def get_upTime(self) -> int:
        """
        Returns the number of milliseconds spent since the module was powered on.

        @return an integer corresponding to the number of milliseconds spent since the module was powered on

        On failure, throws an exception or returns YModule.UPTIME_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("upTime")
        if json_val is None:
            return YModule.UPTIME_INVALID
        return json_val

    async def get_usbCurrent(self) -> int:
        """
        Returns the current consumed by the module on the USB bus, in milli-amps.

        @return an integer corresponding to the current consumed by the module on the USB bus, in milli-amps

        On failure, throws an exception or returns YModule.USBCURRENT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("usbCurrent")
        if json_val is None:
            return YModule.USBCURRENT_INVALID
        return json_val

    async def get_rebootCountdown(self) -> int:
        """
        Returns the remaining number of seconds before the module restarts, or zero when no
        reboot has been scheduled.

        @return an integer corresponding to the remaining number of seconds before the module restarts, or zero when no
                reboot has been scheduled

        On failure, throws an exception or returns YModule.REBOOTCOUNTDOWN_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("rebootCountdown")
        if json_val is None:
            return YModule.REBOOTCOUNTDOWN_INVALID
        return json_val

    async def set_rebootCountdown(self, newval: int) -> int:
        rest_val = str(newval)
        return await self._setAttr("rebootCountdown", rest_val)

    async def get_userVar(self) -> int:
        """
        Returns the value previously stored in this attribute.
        On startup and after a device reboot, the value is always reset to zero.

        @return an integer corresponding to the value previously stored in this attribute

        On failure, throws an exception or returns YModule.USERVAR_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("userVar")
        if json_val is None:
            return YModule.USERVAR_INVALID
        return json_val

    async def set_userVar(self, newval: int) -> int:
        """
        Stores a 32 bit value in the device RAM. This attribute is at programmer disposal,
        should he need to store a state variable.
        On startup and after a device reboot, the value is always reset to zero.

        @param newval : an integer

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("userVar", rest_val)

    async def get_productNameAndRevision(self) -> str:
        prodname: str
        prodrel: int
        fullname: str

        prodname = await self.get_productName()
        prodrel = await self.get_productRelease()
        if prodrel > 1:
            fullname = "%s rev. %c" % (prodname, 64 + prodrel)
        else:
            fullname = prodname
        return fullname

    async def saveToFlash(self) -> int:
        """
        Saves current settings in the nonvolatile memory of the module.
        Warning: the number of allowed save operations during a module life is
        limited (about 100000 cycles). Do not call this function within a loop.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_persistentSettings(YModule.PERSISTENTSETTINGS_SAVED)

    async def revertFromFlash(self) -> int:
        """
        Reloads the settings stored in the nonvolatile memory, as
        when the module is powered on.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_persistentSettings(YModule.PERSISTENTSETTINGS_LOADED)

    async def reboot(self, secBeforeReboot: int) -> int:
        """
        Schedules a simple module reboot after the given number of seconds.

        @param secBeforeReboot : number of seconds before rebooting

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_rebootCountdown(secBeforeReboot)

    async def triggerFirmwareUpdate(self, secBeforeReboot: int) -> int:
        """
        Schedules a module reboot into special firmware update mode.

        @param secBeforeReboot : number of seconds before rebooting

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_rebootCountdown(-secBeforeReboot)

    async def registerLogCallback(self, callback: YModuleLogCallback) -> int:
        """
        Registers a device log callback function. This callback will be called each time
        that a module sends a new log message. Mostly useful to debug a Yoctopuce module.

        @param callback : the callback function to call, or a None pointer.
                The callback function should take two
                arguments: the module object that emitted the log message,
                and the character string containing the log.
                On failure, throws an exception or returns a negative error code.
        """
        serial: str

        serial = await self.get_serialNumber()
        if serial == YAPI.INVALID_STRING:
            return YAPI.DEVICE_NOT_FOUND
        self._logCallback = callback
        await self._startStopDevLog(serial, callback)
        return 0

    def get_logCallback(self) -> YModuleLogCallback:
        return self._logCallback

    async def registerConfigChangeCallback(self, callback: YModuleConfigChangeCallback) -> int:
        """
        Register a callback function, to be called when a persistent settings in
        a device configuration has been changed (e.g. change of unit, etc).

        @param callback : a procedure taking a YModule parameter, or None
                to unregister a previously registered  callback.
        """
        if callback:
            await YModule._updateModuleCallbackList(self, True)
        else:
            await YModule._updateModuleCallbackList(self, False)
        self._confChangeCallback = callback
        return 0

    async def registerBeaconCallback(self, callback: YModuleBeaconCallback) -> int:
        """
        Register a callback function, to be called when the localization beacon of the module
        has been changed. The callback function should take two arguments: the YModule object of
        which the beacon has changed, and an integer describing the new beacon state.

        @param callback : The callback function to call, or None to unregister a
                previously registered callback.
        """
        if callback:
            await YModule._updateModuleCallbackList(self, True)
        else:
            await YModule._updateModuleCallbackList(self, False)
        self._beaconCallback = callback
        return 0

    async def triggerConfigChangeCallback(self) -> int:
        """
        Triggers a configuration change callback, to check if they are supported or not.
        """
        await self._setAttr("persistentSettings", "2")
        return 0

    async def checkFirmware(self, path: str, onlynew: bool) -> str:
        """
        Tests whether the byn file is valid for this module. This method is useful to test if the module
        needs to be updated.
        It is possible to pass a directory as argument instead of a file. In this case, this method returns
        the path of the most recent
        appropriate .byn file. If the parameter onlynew is true, the function discards firmwares that are older or
        equal to the installed firmware.

        @param path : the path of a byn file or a directory that contains byn files
        @param onlynew : returns only files that are strictly newer

        @return the path of the byn file to use or a empty string if no byn files matches the requirement

        On failure, throws an exception or returns a string that start with "error:".
        """
        serial: str
        release: int
        tmp_res: str
        if onlynew:
            release = YAPI._atoi(await self.get_firmwareRelease())
        else:
            release = 0
        # //may throw an exception
        serial = await self.get_serialNumber()
        tmp_res = await YFirmwareUpdate.CheckFirmware(serial, path, release)
        if tmp_res.find("error:") == 0:
            self._throw(YAPI.INVALID_ARGUMENT, tmp_res)
        return tmp_res

    async def updateFirmwareEx(self, path: str, force: bool) -> YFirmwareUpdate:
        """
        Prepares a firmware update of the module. This method returns a YFirmwareUpdate object which
        handles the firmware update process.

        @param path : the path of the .byn file to use.
        @param force : true to force the firmware update even if some prerequisites appear not to be met

        @return a YFirmwareUpdate object or None on error.
        """
        serial: str
        settings: xarray

        serial = await self.get_serialNumber()
        settings = await self.get_allSettings()
        if len(settings) == 0:
            self._throw(YAPI.IO_ERROR, "Unable to get device settings")
            settings = xbytearray("error:Unable to get device settings", 'latin-1')
        return YFirmwareUpdate(self._yapi, serial, path, settings, force)

    async def updateFirmware(self, path: str) -> YFirmwareUpdate:
        """
        Prepares a firmware update of the module. This method returns a YFirmwareUpdate object which
        handles the firmware update process.

        @param path : the path of the .byn file to use.

        @return a YFirmwareUpdate object or None on error.
        """
        return await self.updateFirmwareEx(path, False)

    async def get_allSettings(self) -> xarray:
        """
        Returns all the settings and uploaded files of the module. Useful to backup all the
        logical names, calibrations parameters, and uploaded files of a device.

        @return a binary buffer with all the settings.

        On failure, throws an exception or returns an binary object of size 0.
        """
        settings: xarray
        json: xarray
        res: xarray
        sep: str
        name: str
        item: str
        t_type: str
        pageid: str
        url: str
        file_data: str
        file_data_bin: xarray
        temp_data_bin: xarray
        ext_settings: str
        filelist: list[xarray] = []
        templist: list[str] = []

        settings = await self._download("api.json")
        if len(settings) == 0:
            return settings
        ext_settings = ", \"extras\":["
        templist = self.get_functionIds("Temperature")
        sep = ""
        for ii_0 in templist:
            if YAPI._atoi(await self.get_firmwareRelease()) > 9000:
                url = "api/%s/sensorType" % ii_0
                t_type = (await self._download(url)).decode('latin-1')
                if t_type == "RES_NTC" or t_type == "RES_LINEAR":
                    pageid = ii_0[11: 11 + len(ii_0) - 11]
                    if pageid == "":
                        pageid = "1"
                    temp_data_bin = await self._download("extra.json?page=%s" % pageid)
                    if len(temp_data_bin) > 0:
                        item = "%s{\"fid\":\"%s\", \"json\":%s}\n" % (sep, ii_0, temp_data_bin.decode('latin-1'))
                        ext_settings = ext_settings + item
                        sep = ","
        ext_settings = ext_settings + "],\n\"files\":["
        if self.hasFunction("files"):
            json = await self._download("files.json?a=dir&d=1&f=")
            if len(json) == 0:
                return json
            filelist = self._json_get_array(json)
            sep = ""
            for ii_1 in filelist:
                name = self._json_get_key(ii_1, "name")
                if (len(name) > 0) and not (name == "startupConf.json"):
                    if name[len(name)-1: len(name)-1 + 1] == "/":
                        file_data = ""
                    else:
                        file_data_bin = await self._download(self._escapeAttr(name))
                        file_data = YAPI._bytesToHexStr(file_data_bin)
                    item = "%s{\"name\":\"%s\", \"data\":\"%s\"}\n" % (sep, name, file_data)
                    ext_settings = ext_settings + item
                    sep = ","
        res = xbytearray("{ \"api\":" + settings.decode('latin-1') + ext_settings + "]}", 'latin-1')
        return res

    async def loadThermistorExtra(self, funcId: str, jsonExtra: str) -> int:
        values: list[xarray] = []
        url: str
        curr: str
        binCurr: xarray
        currTemp: str
        binCurrTemp: xarray
        ofs: int
        size: int
        url = "api/" + funcId + ".json?command=Z"

        await self._download(url)
        # add records in growing resistance value
        values = self._json_get_array(xbytearray(jsonExtra, 'latin-1'))
        ofs = 0
        size = len(values)
        while ofs + 1 < size:
            binCurr = values[ofs]
            binCurrTemp = values[ofs + 1]
            curr = self._json_get_string(binCurr)
            currTemp = self._json_get_string(binCurrTemp)
            url = "api/%s.json?command=m%s:%s" % (funcId, curr, currTemp)
            await self._download(url)
            ofs = ofs + 2
        return YAPI.SUCCESS

    async def set_extraSettings(self, jsonExtra: str) -> int:
        extras: list[xarray] = []
        tmp: xarray
        functionId: str
        data: xarray
        extras = self._json_get_array(xbytearray(jsonExtra, 'latin-1'))
        for ii_0 in extras:
            tmp = self._get_json_path(ii_0, "fid")
            functionId = self._json_get_string(tmp)
            data = self._get_json_path(ii_0, "json")
            if self.hasFunction(functionId):
                await self.loadThermistorExtra(functionId, data.decode('latin-1'))
        return YAPI.SUCCESS

    async def set_allSettingsAndFiles(self, settings: xarray) -> int:
        """
        Restores all the settings and uploaded files to the module.
        This method is useful to restore all the logical names and calibrations parameters,
        uploaded files etc. of a device from a backup.
        Remember to call the saveToFlash() method of the module if the
        modifications must be kept.

        @param settings : a binary buffer with all the settings.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        down: xarray
        json_api: xarray
        json_files: xarray
        json_extra: xarray
        fuperror: int
        globalres: int
        fuperror = 0
        json_api = self._get_json_path(settings, "api")
        if len(json_api) == 0:
            return await self.set_allSettings(settings)
        json_extra = self._get_json_path(settings, "extras")
        if len(json_extra) > 0:
            await self.set_extraSettings(json_extra.decode('latin-1'))
        await self.set_allSettings(json_api)
        if self.hasFunction("files"):
            files: list[xarray] = []
            res: str
            tmp: xarray
            name: str
            data: str
            down = await self._download("files.json?a=format")
            down = self._get_json_path(down, "res")
            res = self._json_get_string(down)
            if not (res == "ok"):
                self._throw(YAPI.IO_ERROR, "format failed")
                return YAPI.IO_ERROR
            json_files = self._get_json_path(settings, "files")
            files = self._json_get_array(json_files)
            for ii_0 in files:
                tmp = self._get_json_path(ii_0, "name")
                name = self._json_get_string(tmp)
                tmp = self._get_json_path(ii_0, "data")
                data = self._json_get_string(tmp)
                if name == "":
                    fuperror = fuperror + 1
                else:
                    await self._upload(name, YAPI._hexStrToBin(data))
        # Apply settings a second time for file-dependent settings and dynamic sensor nodes
        globalres = await self.set_allSettings(json_api)
        if not (fuperror == 0):
            self._throw(YAPI.IO_ERROR, "Error during file upload")
            return YAPI.IO_ERROR
        return globalres

    def hasFunction(self, funcId: str) -> bool:
        """
        Tests if the device includes a specific function. This method takes a function identifier
        and returns a boolean.

        @param funcId : the requested function identifier

        @return true if the device has the function identifier
        """
        count: int
        i: int
        fid: str

        count = self.functionCount()
        i = 0
        while i < count:
            fid = self.functionId(i)
            if fid == funcId:
                return True
            i = i + 1
        return False

    def get_functionIds(self, funType: str) -> list[str]:
        """
        Retrieve all hardware identifier that match the type passed in argument.

        @param funType : The type of function (Relay, LightSensor, Voltage,...)

        @return an array of strings.
        """
        count: int
        i: int
        ftype: str
        res: list[str] = []

        count = self.functionCount()
        i = 0

        while i < count:
            ftype = self.functionType(i)
            if ftype == funType:
                res.append(self.functionId(i))
            else:
                ftype = self.functionBaseType(i)
                if ftype == funType:
                    res.append(self.functionId(i))
            i = i + 1

        return res

    def calibVersion(self, cparams: str) -> int:
        if cparams == "0,":
            return 3
        if cparams.find(",") >= 0:
            if cparams.find(" ") > 0:
                return 3
            else:
                return 1
        if cparams == "" or cparams == "0":
            return 1
        if (len(cparams) < 2) or (cparams.find(".") >= 0):
            return 0
        else:
            return 2

    def calibScale(self, unit_name: str, sensorType: str) -> int:
        if unit_name == "g" or unit_name == "gauss" or unit_name == "W":
            return 1000
        if unit_name == "C":
            if sensorType == "":
                return 16
            if YAPI._atoi(sensorType) < 8:
                return 16
            else:
                return 100
        if unit_name == "m" or unit_name == "deg":
            return 10
        return 1

    def calibOffset(self, unit_name: str) -> int:
        if unit_name == "% RH" or unit_name == "mbar" or unit_name == "lx":
            return 0
        return 32767

    async def calibConvert(self, param: str, currentFuncValue: str, unit_name: str, sensorType: str) -> str:
        paramVer: int
        funVer: int
        funScale: int
        funOffset: int
        paramScale: int
        paramOffset: int
        words: list[int] = []
        words_str: list[str] = []
        calibData: list[float] = []
        iCalib: list[int]
        calibType: int
        i: int
        maxSize: int
        ratio: float
        nPoints: int
        wordVal: float
        # Initial guess for parameter encoding
        paramVer = self.calibVersion(param)
        funVer = self.calibVersion(currentFuncValue)
        funScale = self.calibScale(unit_name, sensorType)
        funOffset = self.calibOffset(unit_name)
        paramScale = funScale
        paramOffset = funOffset
        if funVer < 3:
            # Read the effective device scale if available
            if funVer == 2:
                words = YAPIContext._decodeWords(currentFuncValue)
                if (words[0] == 1366) and (words[1] == 12500):
                    # Yocto-3D RefFrame used a special encoding
                    funScale = 1
                    funOffset = 0
                else:
                    funScale = words[1]
                    funOffset = words[0]
            else:
                if funVer == 1:
                    if currentFuncValue == "" or (YAPI._atoi(currentFuncValue) > 10):
                        funScale = 0
        del calibData[:]
        calibType = 0
        if paramVer < 3:
            # Handle old 16 bit parameters formats
            if paramVer == 2:
                words = YAPIContext._decodeWords(param)
                if (words[0] == 1366) and (words[1] == 12500):
                    # Yocto-3D RefFrame used a special encoding
                    paramScale = 1
                    paramOffset = 0
                else:
                    paramScale = words[1]
                    paramOffset = words[0]
                if (len(words) >= 3) and (words[2] > 0):
                    maxSize = 3 + 2 * ((words[2]) % (10))
                    if maxSize > len(words):
                        maxSize = len(words)
                    i = 3
                    while i < maxSize:
                        calibData.append(float(words[i]))
                        i = i + 1
            else:
                if paramVer == 1:
                    words_str = (param).split(',')
                    for ii_0 in words_str:
                        words.append(YAPI._atoi(ii_0))
                    if param == "" or (words[0] > 10):
                        paramScale = 0
                    if (len(words) > 0) and (words[0] > 0):
                        maxSize = 1 + 2 * ((words[0]) % (10))
                        if maxSize > len(words):
                            maxSize = len(words)
                        i = 1
                        while i < maxSize:
                            calibData.append(float(words[i]))
                            i = i + 1
                else:
                    if paramVer == 0:
                        ratio = YAPI._atof(param)
                        if ratio > 0:
                            calibData.append(0.0)
                            calibData.append(0.0)
                            calibData.append(round(65535 / ratio))
                            calibData.append(65535.0)
            i = 0
            while i < len(calibData):
                if paramScale > 0:
                    # scalar decoding
                    calibData[i] = (calibData[i] - paramOffset) / paramScale
                else:
                    # floating-point decoding
                    calibData[i] = YAPIContext._decimalToDouble(int(round(calibData[i])))
                i = i + 1
        else:
            # Handle latest 32bit parameter format
            iCalib = YAPIContext._decodeFloats(param)
            calibType = int(round(iCalib[0] / 1000.0))
            if calibType >= 30:
                calibType = calibType - 30
            i = 1
            while i < len(iCalib):
                calibData.append(iCalib[i] / 1000.0)
                i = i + 1
        if funVer >= 3:
            # Encode parameters in new format
            if len(calibData) == 0:
                param = "0,"
            else:
                param = str(30 + calibType)
                i = 0
                while i < len(calibData):
                    if (i & 1) > 0:
                        param = param + ":"
                    else:
                        param = param + " "
                    param = param + str(int(round(calibData[i] * 1000.0 / 1000.0)))
                    i = i + 1
                param = param + ","
        else:
            if funVer >= 1:
                # Encode parameters for older devices
                nPoints = len(calibData) // 2
                param = str(nPoints)
                i = 0
                while i < 2 * nPoints:
                    if funScale == 0:
                        wordVal = YAPIContext._doubleToDecimal(int(round(calibData[i])))
                    else:
                        wordVal = calibData[i] * funScale + funOffset
                    param = param + "," + str(round(wordVal))
                    i = i + 1
            else:
                # Initial V0 encoding used for old Yocto-Light
                if len(calibData) == 4:
                    param = str(round(1000 * (calibData[3] - calibData[1]) / calibData[2] - calibData[0]))
        return param

    async def _tryExec(self, url: str) -> int:
        res: int
        done: int
        res = YAPI.SUCCESS
        done = 1
        try:
            await self._download(url)
        except YAPI_Exception:
            done = 0
        if done == 0:
            # retry silently after a short wait
            try:
                await YAPI.Sleep(500)
                await self._download(url)
            except YAPI_Exception:
                # second failure, return error code
                res = self.get_errorType()
        return res

    async def set_allSettings(self, settings: xarray) -> int:
        """
        Restores all the settings of the device. Useful to restore all the logical names and calibrations parameters
        of a module from a backup.Remember to call the saveToFlash() method of the module if the
        modifications must be kept.

        @param settings : a binary buffer with all the settings.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        restoreLast: list[str] = []
        old_json_flat: xarray
        old_dslist: list[xarray] = []
        old_jpath: list[str] = []
        old_jpath_len: list[int] = []
        old_val_arr: list[str] = []
        actualSettings: xarray
        new_dslist: list[xarray] = []
        new_jpath: list[str] = []
        new_jpath_len: list[int] = []
        new_val_arr: list[str] = []
        cpos: int
        eqpos: int
        leng: int
        i: int
        j: int
        subres: int
        res: int
        njpath: str
        jpath: str
        fun: str
        attr: str
        value: str
        old_serial: str
        new_serial: str
        url: str
        tmp: str
        binTmp: xarray
        sensorType: str
        unit_name: str
        newval: str
        oldval: str
        old_calib: str
        each_str: str
        do_update: bool
        found: bool
        res = YAPI.SUCCESS
        binTmp = self._get_json_path(settings, "api")
        if len(binTmp) > 0:
            settings = binTmp
        old_serial = ""
        oldval = ""
        newval = ""
        old_json_flat = self._flattenJsonStruct(settings)
        old_dslist = self._json_get_array(old_json_flat)



        for ii_0 in old_dslist:
            each_str = self._json_get_string(ii_0)
            # split json path and attr
            leng = len(each_str)
            eqpos = each_str.find("=")
            if (eqpos < 0) or (leng == 0):
                self._throw(YAPI.INVALID_ARGUMENT, "Invalid settings")
                return YAPI.INVALID_ARGUMENT
            jpath = each_str[0: 0 + eqpos]
            eqpos = eqpos + 1
            value = each_str[eqpos: eqpos + leng - eqpos]
            old_jpath.append(jpath)
            old_jpath_len.append(len(jpath))
            old_val_arr.append(value)
            if jpath == "module/serialNumber":
                old_serial = value




        try:
            actualSettings = await self._download("api.json")
        except YAPI_Exception:
            # retry silently after a short wait
            await YAPI.Sleep(500)
            actualSettings = await self._download("api.json")
        new_serial = await self.get_serialNumber()
        if old_serial == new_serial or old_serial == "":
            old_serial = "_NO_SERIAL_FILTER_"
        actualSettings = self._flattenJsonStruct(actualSettings)
        new_dslist = self._json_get_array(actualSettings)



        for ii_1 in new_dslist:
            # remove quotes
            each_str = self._json_get_string(ii_1)
            # split json path and attr
            leng = len(each_str)
            eqpos = each_str.find("=")
            if (eqpos < 0) or (leng == 0):
                self._throw(YAPI.INVALID_ARGUMENT, "Invalid settings")
                return YAPI.INVALID_ARGUMENT
            jpath = each_str[0: 0 + eqpos]
            eqpos = eqpos + 1
            value = each_str[eqpos: eqpos + leng - eqpos]
            new_jpath.append(jpath)
            new_jpath_len.append(len(jpath))
            new_val_arr.append(value)




        i = 0
        while i < len(new_jpath):
            njpath = new_jpath[i]
            leng = len(njpath)
            cpos = njpath.find("/")
            if (cpos < 0) or (leng == 0):
                continue
            fun = njpath[0: 0 + cpos]
            cpos = cpos + 1
            attr = njpath[cpos: cpos + leng - cpos]
            do_update = True
            if fun == "services":
                do_update = False
            if do_update and (attr == "firmwareRelease"):
                do_update = False
            if do_update and (attr == "usbCurrent"):
                do_update = False
            if do_update and (attr == "upTime"):
                do_update = False
            if do_update and (attr == "persistentSettings"):
                do_update = False
            if do_update and (attr == "adminPassword"):
                do_update = False
            if do_update and (attr == "userPassword"):
                do_update = False
            if do_update and (attr == "rebootCountdown"):
                do_update = False
            if do_update and (attr == "advertisedValue"):
                do_update = False
            if do_update and (attr == "poeCurrent"):
                do_update = False
            if do_update and (attr == "readiness"):
                do_update = False
            if do_update and (attr == "ipAddress"):
                do_update = False
            if do_update and (attr == "subnetMask"):
                do_update = False
            if do_update and (attr == "router"):
                do_update = False
            if do_update and (attr == "linkQuality"):
                do_update = False
            if do_update and (attr == "ssid"):
                do_update = False
            if do_update and (attr == "channel"):
                do_update = False
            if do_update and (attr == "security"):
                do_update = False
            if do_update and (attr == "message"):
                do_update = False
            if do_update and (attr == "signalValue"):
                do_update = False
            if do_update and (attr == "currentValue"):
                do_update = False
            if do_update and (attr == "currentRawValue"):
                do_update = False
            if do_update and (attr == "currentRunIndex"):
                do_update = False
            if do_update and (attr == "pulseTimer"):
                do_update = False
            if do_update and (attr == "lastTimePressed"):
                do_update = False
            if do_update and (attr == "lastTimeReleased"):
                do_update = False
            if do_update and (attr == "filesCount"):
                do_update = False
            if do_update and (attr == "freeSpace"):
                do_update = False
            if do_update and (attr == "timeUTC"):
                do_update = False
            if do_update and (attr == "rtcTime"):
                do_update = False
            if do_update and (attr == "unixTime"):
                do_update = False
            if do_update and (attr == "dateTime"):
                do_update = False
            if do_update and (attr == "rawValue"):
                do_update = False
            if do_update and (attr == "lastMsg"):
                do_update = False
            if do_update and (attr == "delayedPulseTimer"):
                do_update = False
            if do_update and (attr == "rxCount"):
                do_update = False
            if do_update and (attr == "txCount"):
                do_update = False
            if do_update and (attr == "msgCount"):
                do_update = False
            if do_update and (attr == "rxMsgCount"):
                do_update = False
            if do_update and (attr == "txMsgCount"):
                do_update = False
            if do_update:
                do_update = False
                j = 0
                found = False
                newval = new_val_arr[i]
                while (j < len(old_jpath)) and not found:
                    if (new_jpath_len[i] == old_jpath_len[j]) and (new_jpath[i] == old_jpath[j]):
                        found = True
                        oldval = old_val_arr[j]
                        if not (newval == oldval) and not (oldval == old_serial):
                            do_update = True
                    j = j + 1
            if do_update:
                if attr == "calibrationParam":
                    old_calib = ""
                    unit_name = ""
                    sensorType = ""
                    j = 0
                    found = False
                    while (j < len(old_jpath)) and not found:
                        if (new_jpath_len[i] == old_jpath_len[j]) and (new_jpath[i] == old_jpath[j]):
                            found = True
                            old_calib = old_val_arr[j]
                        j = j + 1
                    tmp = fun + "/unit"
                    j = 0
                    found = False
                    while (j < len(new_jpath)) and not found:
                        if tmp == new_jpath[j]:
                            found = True
                            unit_name = new_val_arr[j]
                        j = j + 1
                    tmp = fun + "/sensorType"
                    j = 0
                    found = False
                    while (j < len(new_jpath)) and not found:
                        if tmp == new_jpath[j]:
                            found = True
                            sensorType = new_val_arr[j]
                        j = j + 1
                    newval = await self.calibConvert(old_calib, new_val_arr[i], unit_name, sensorType)
                    url = "api/" + fun + ".json?" + attr + "=" + self._escapeAttr(newval)
                    subres = await self._tryExec(url)
                    if (res == YAPI.SUCCESS) and (subres != YAPI.SUCCESS):
                        res = subres
                else:
                    url = "api/" + fun + ".json?" + attr + "=" + self._escapeAttr(oldval)
                    if attr == "resolution":
                        restoreLast.append(url)
                    else:
                        subres = await self._tryExec(url)
                        if (res == YAPI.SUCCESS) and (subres != YAPI.SUCCESS):
                            res = subres
            i = i + 1

        for ii_2 in restoreLast:
            subres = await self._tryExec(ii_2)
            if (res == YAPI.SUCCESS) and (subres != YAPI.SUCCESS):
                res = subres
        await self.clearCache()
        return res

    async def get_hardwareId(self) -> str:
        """
        Returns the unique hardware identifier of the module.
        The unique hardware identifier is made of the device serial
        number followed by string ".module".

        @return a string that uniquely identifies the module
        """
        serial: str

        serial = await self.get_serialNumber()
        return serial + ".module"

    async def download(self, pathname: str) -> xarray:
        """
        Downloads the specified built-in file and returns a binary buffer with its content.

        @param pathname : name of the new file to load

        @return a binary buffer with the file content

        On failure, throws an exception or returns an empty content.
        """
        return await self._download(pathname)

    async def get_icon2d(self) -> xarray:
        """
        Returns the icon of the module. The icon is a PNG image and does not
        exceeds 1536 bytes.

        @return a binary buffer with module icon, in png format.
                On failure, throws an exception or returns an empty content.
        """
        return await self._download("icon2d.png")

    async def get_lastLogs(self) -> str:
        """
        Returns a string with last logs of the module. This method return only
        logs that are still in the module.

        @return a string with last logs of the module.
                On failure, throws an exception or returns  YAPI.INVALID_STRING.
        """
        content: xarray

        content = await self._download("logs.txt")
        if len(content) == 0:
            return YAPI.INVALID_STRING
        return content.decode('latin-1')

    async def log(self, text: str) -> int:
        """
        Adds a text message to the device logs. This function is useful in
        particular to trace the execution of HTTP callbacks. If a newline
        is desired after the message, it must be included in the string.

        @param text : the string to append to the logs.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self._upload("logs.txt", xbytearray(text, 'latin-1'))

    # --- (end of generated code: YModule implementation)

    def functionCount(self) -> int:
        """
        Returns the number of functions (beside the "module" interface) available on the module.

        @return the number of functions on the module

        On failure, throws an exception or returns a negative error code.
        """
        dev: Union[YDevice, None] = self._dev
        if not dev:
            return self._lastErrorType
        funcIds: list[Union[str,None]] = dev._funcIds
        return len(funcIds) - funcIds.count(None)

    def functionId(self, functionIndex: int) -> str:
        """
        Retrieves the hardware identifier of the <i>n</i>th function on the module.

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the unambiguous hardware identifier of the requested module function

        On failure, throws an exception or returns an empty string.
        """
        dev: Union[YDevice, None] = self._dev
        if not dev:
            return ""
        res: Union[str, None] = None
        try:
            res = dev._funcIds[functionIndex]
        except IndexError:
            pass
        if not res:
            self._throw(YAPI.DEVICE_NOT_FOUND, "invalid functionIndex")
            return ""
        return res

    def functionType(self, functionIndex: int) -> str:
        """
        Retrieves the type of the <i>n</i>th function on the module. Yoctopuce functions type names match
        their class names without the <i>Y</i> prefix, for instance <i>Relay</i>, <i>Temperature</i> etc..

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the type of the function.

        On failure, throws an exception or returns an empty string.
        """
        funcId: str = self.functionId(functionIndex)
        if funcId:
            return YAPIContext.functionClass(funcId)
        return ""

    def _getFunRecFromIndex(self, functionIndex: int) -> Union[xdict,None]:
        funcId: str = self.functionId(functionIndex)
        if not funcId:
            return None
        res: Union[xdict, None] = self._yapi._findFunRecByHwId(HwId(self._hwId.module, funcId))
        if res:
            return res
        self._throw(YAPI.DEVICE_NOT_FOUND, "Device [%s] not online" % self._hwId.module)
        return None

    def functionBaseType(self, functionIndex: int) -> str:
        """
        Retrieves the base type of the <i>n</i>th function on the module.
        For instance, the base type of all measuring functions is "Sensor".

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the base type of the function

        On failure, throws an exception or returns an empty string.
        """
        funrec: Union[xdict,None] = self._getFunRecFromIndex(functionIndex)
        if funrec:
            return funrec["baseType"]
        return ""

    def functionName(self, functionIndex: int) -> str:
        """
        Retrieves the logical name of the <i>n</i>th function on the module.

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a string corresponding to the logical name of the requested module function

        On failure, throws an exception or returns an empty string.
        """
        funrec: Union[xdict,None] = self._getFunRecFromIndex(functionIndex)
        if funrec:
            return funrec["logicalName"]
        return ""

    def functionValue(self, functionIndex: int) -> str:
        """
        Retrieves the advertised value of the <i>n</i>th function on the module.

        @param functionIndex : the index of the function for which the information is desired, starting at
        0 for the first function.

        @return a short string (up to 6 characters) corresponding to the advertised value of the requested
        module function

        On failure, throws an exception or returns an empty string.
        """
        funrec: Union[xdict,None] = self._getFunRecFromIndex(functionIndex)
        if funrec:
            return funrec["advertisedValue"].strip("\0")
        return ""


# --- (generated code: YFirmwareUpdate class start)
# noinspection PyProtectedMember
class YFirmwareUpdate:
    """
    The YFirmwareUpdate class let you control the firmware update of a Yoctopuce
    module. This class should not be instantiate directly, but instances should be retrieved
    using the YModule method module.updateFirmware.

    """
    # --- (end of generated code: YFirmwareUpdate class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YFirmwareUpdate return codes)
        pass
        # --- (end of generated code: YFirmwareUpdate return codes)

    _yapi: YAPIContext
    # --- (generated code: YFirmwareUpdate attributes declaration)
    _serial: str
    _settings: xarray
    _firmwarepath: str
    _progress_msg: str
    _progress_c: int
    _progress: int
    _restore_step: int
    _force: bool
    # --- (end of generated code: YFirmwareUpdate attributes declaration)

    def __init__(self, yapi: YAPIContext, serial: str, path: str, settings: xarray, force: bool):
        # --- (generated code: YFirmwareUpdate constructor)
        self._serial = ''
        self._settings = xbytearray(0)
        self._firmwarepath = ''
        self._progress_msg = ''
        self._progress_c = 0
        self._progress = 0
        self._restore_step = 0
        self._force = False
        # --- (end of generated code: YFirmwareUpdate constructor)
        self._yapi = yapi
        self._serial = serial
        self._firmwarepath = path
        self._settings = settings
        self._force = force

    def progress(self, progress: int, msg: str) -> None:
        self._progress = progress
        self._progress_msg = msg

    @staticmethod
    async def CheckFirmware(serial: str, path: str, minrelease: int) -> str:
        if 0 <= path.find("www.yoctopuce.com", 0) < 8:
            try:
                async with BaseSession("http://www.yoctopuce.com") as httpSession:
                    req: ClientResponse
                    async with httpSession.get("/FR/common/getLastFirmwareLink.php?serial=%s" % serial) as req:
                        info: Any = await req.json()
                        link = info["link"]
                        best_rev = info["version"]
                        if minrelease != 0:
                            if minrelease < best_rev:
                                return link
                            else:
                                return ""
                        else:
                            return link
            except BaseException as e:
                return "error:" + str(e)
        else:
            # FIXME: to be implemented
            raise YAPI_Exception(YAPI.NOT_SUPPORTED, 'Not yet supported')

    @staticmethod
    async def GetAllBootLoadersInContext(yctx: YAPIContext) -> list[str]:
        res: list[str] = []
        for hub in yctx._hubs:
            res += await hub.getBootloaders()
        return res

    @staticmethod
    async def GetAllBootLoaders() -> list[str]:
        return await YFirmwareUpdate.GetAllBootLoadersInContext(YAPI)

    def _report_progress(self, progress: int, msg: str) -> None:
        self._progress = progress
        self._progress_msg = msg

    def _checkFirmware(self, data: xarray) -> str:
        if data[0] != ord('B') or data[1] != ord('Y') or data[2] != ord('N') or data[3] != 0:
            raise YAPI_Exception(YAPI.INVALID_ARGUMENT, "Not a firmware file")
        fw_dat: xarray = data[74:74 + _YOCTO_FIRMWARE_LEN]
        ofs: int = fw_dat.find(0)
        fw: str = fw_dat[0:ofs].decode(YAPI.DefaultEncoding)
        return fw

    async def _processMore(self, newupdate: int) -> int:
        if newupdate == 1:
            self._yapi.create_task(self._processMoreWorker(newupdate))
        return YAPI.SUCCESS

    async def _processMoreWorker(self, newupdate: int) -> int:

        try:
            # 1% -> 5%
            self._report_progress(1, "Loading firmware")
            if self._firmwarepath.startswith("www.yoctopuce.com") or self._firmwarepath.startswith("http://www.yoctopuce.com"):
                firmware = await self._yapi.BasicHTTPRequest(self._firmwarepath)
                firmware_rev: str = self._checkFirmware(firmware)
            else:
                # fixme: implement file load
                raise YAPI_Exception(YAPI.NOT_SUPPORTED, 'Not yet supported')

            # 5% -> 10%
            self._report_progress(5, "check if module is already in bootloader")
            module: YModule = YModule.FindModuleInContext(self._yapi, self._serial + ".module")
            if await module.isOnline():
                dev: YDevice = await module._getDev()
                hub: YGenericHub = dev.hub
            else:
                # test if already in bootloader
                hub: YGenericHub = await self._yapi.getHubWithBootloader(self._serial)
            if hub is None:
                raise YAPI_Exception(YAPI.DEVICE_NOT_FOUND, "device " + self._serial + " is not detected")

            await hub.firmwareUpdate(self._serial, firmware, self._settings, self._report_progress)
            # 80%-> 98%
            self._report_progress(80, "wait to the device restart")
            timeout: int = YAPI.GetTickCount() + 60000
            await module.clearCache()
            while (not await module.isOnline()) and timeout > YAPI.GetTickCount():
                if _IS_MICROPYTHON:
                    await asyncio.sleep_ms(500)  # noqa
                else:
                    await asyncio.sleep(500 / 1000.0)
                try:
                    await self._yapi.UpdateDeviceList()
                except YAPI_Exception:
                    pass
            if await module.isOnline():
                if self._settings is not None:
                    await module.set_allSettingsAndFiles(self._settings)
                    await module.saveToFlash()

                realFw: str = await module.get_firmwareRelease()
                if realFw == firmware_rev:
                    self._report_progress(100, "Success")
                else:
                    self._report_progress(YAPI.IO_ERROR, "Unable to update firmware")
            else:
                self._report_progress(YAPI.DEVICE_NOT_FOUND, "Device did not reboot correctly")
            return YAPI.SUCCESS
        except YAPI_Exception as e:
            self._report_progress(e.errorType, e.errorMessage)
            return e.errorType
        except BaseException as e:
            self._report_progress(YAPI.IO_ERROR, str(e))
            return YAPI.IO_ERROR

    # --- (generated code: YFirmwareUpdate implementation)
    async def get_progress(self) -> int:
        """
        Returns the progress of the firmware update, on a scale from 0 to 100. When the object is
        instantiated, the progress is zero. The value is updated during the firmware update process until
        the value of 100 is reached. The 100 value means that the firmware update was completed
        successfully. If an error occurs during the firmware update, a negative value is returned, and the
        error message can be retrieved with get_progressMessage.

        @return an integer in the range 0 to 100 (percentage of completion)
                or a negative error code in case of failure.
        """
        if self._progress >= 0:
            await self._processMore(0)
        return self._progress

    async def get_progressMessage(self) -> str:
        """
        Returns the last progress message of the firmware update process. If an error occurs during the
        firmware update process, the error message is returned

        @return a string  with the latest progress message, or the error message.
        """
        return self._progress_msg

    async def startUpdate(self) -> int:
        """
        Starts the firmware update process. This method starts the firmware update process in background. This method
        returns immediately. You can monitor the progress of the firmware update with the get_progress()
        and get_progressMessage() methods.

        @return an integer in the range 0 to 100 (percentage of completion),
                or a negative error code in case of failure.

        On failure returns a negative error code.
        """
        err: str
        leng: int
        err = self._settings.decode('latin-1')
        leng = len(err)
        if (leng >= 6) and ("error:" == err[0: 0 + 6]):
            self._progress = -1
            self._progress_msg = err[6: 6 + leng - 6]
        else:
            self._progress = 0
            self._progress_c = 0
            await self._processMore(1)
        return self._progress

    # --- (end of generated code: YFirmwareUpdate implementation)


# --- (generated code: YConsolidatedDataSet class start)
# noinspection PyProtectedMember
class YConsolidatedDataSet:
    """
    YConsolidatedDataSet objects make it possible to retrieve a set of
    recorded measures from multiple sensors, for a specified time interval.
    They can be used to load data points progressively, and to receive
    data records by timestamp, one by one..

    """
    # --- (end of generated code: YConsolidatedDataSet class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YConsolidatedDataSet return codes)
        pass
        # --- (end of generated code: YConsolidatedDataSet return codes)

    # --- (generated code: YConsolidatedDataSet attributes declaration)
    _start: float
    _end: float
    _nsensors: int
    _sensors: list[YSensor]
    _datasets: list[YDataSet]
    _progresss: list[int]
    _nextidx: list[int]
    _nexttim: list[float]
    # --- (end of generated code: YConsolidatedDataSet attributes declaration)

    def __init__(self, start: float, end: float, sensorList: list[YSensor]):
        # --- (generated code: YConsolidatedDataSet constructor)
        self._start = 0.0
        self._end = 0.0
        self._nsensors = 0
        self._sensors = []
        self._datasets = []
        self._progresss = []
        self._nextidx = []
        self._nexttim = []
        # --- (end of generated code: YConsolidatedDataSet constructor)
        self.imm_init(start, end, sensorList)

        # --- (generated code: YConsolidatedDataSet implementation)
    def imm_init(self, startt: float, endt: float, sensorList: list[YSensor]) -> int:
        self._start = startt
        self._end = endt
        self._sensors = sensorList
        self._nsensors = -1
        return YAPI.SUCCESS

    @staticmethod
    def Init(sensorNames: list[str], startTime: float, endTime: float) -> YConsolidatedDataSet:
        """
        Returns an object holding historical data for multiple
        sensors, for a specified time interval.
        The measures will be retrieved from the data logger, which must have been turned
        on at the desired time. The resulting object makes it possible to load progressively
        a large set of measures from multiple sensors, consolidating data on the fly
        to align records based on measurement timestamps.

        @param sensorNames : array of logical names or hardware identifiers of the sensors
                for which data must be loaded from their data logger.
        @param startTime : the start of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without initial limit.
        @param endTime : the end of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without ending limit.

        @return an instance of YConsolidatedDataSet, providing access to
                consolidated historical data. Records can be loaded progressively
                using the YConsolidatedDataSet.nextRecord() method.
        """
        nSensors: int
        sensorList: Union[list[YSensor], None] = []
        idx: int
        sensorName: str
        s: Union[YSensor, None]
        obj: Union[YConsolidatedDataSet, None]
        nSensors = len(sensorNames)
        del sensorList[:]
        idx = 0
        while idx < nSensors:
            sensorName = sensorNames[idx]
            s = YSensor.FindSensor(sensorName)
            sensorList.append(s)
            idx = idx + 1

        obj = YConsolidatedDataSet(startTime, endTime, sensorList)
        return obj

    async def nextRecord(self, datarec: list[float]) -> int:
        """
        Extracts the next data record from the data logger of all sensors linked to this
        object.

        @param datarec : array of floating point numbers, that will be filled by the
                function with the timestamp of the measure in first position,
                followed by the measured value in next positions.

        @return an integer in the range 0 to 100 (percentage of completion),
                or a negative error code in case of failure.

        On failure, throws an exception or returns a negative error code.
        """
        s: int
        idx: int
        sensor: Union[YSensor, None]
        newdataset: Union[YDataSet, None]
        globprogress: int
        currprogress: int
        currnexttim: float
        newvalue: float
        measures: Union[list[YMeasure], None] = []
        nexttime: float
        # //
        # Ensure the dataset have been retrieved
        # //
        if self._nsensors == -1:
            self._nsensors = len(self._sensors)
            del self._datasets[:]
            del self._progresss[:]
            del self._nextidx[:]
            del self._nexttim[:]
            s = 0
            while s < self._nsensors:
                sensor = self._sensors[s]
                newdataset = await sensor.get_recordedData(self._start, self._end)
                self._datasets.append(newdataset)
                self._progresss.append(0)
                self._nextidx.append(0)
                self._nexttim.append(0.0)
                s = s + 1
        del datarec[:]
        # //
        # Find next timestamp to process
        # //
        nexttime = 0
        s = 0
        while s < self._nsensors:
            currnexttim = self._nexttim[s]
            if currnexttim == 0:
                idx = self._nextidx[s]
                measures = self._datasets[s].get_measures()
                currprogress = self._progresss[s]
                while (idx >= len(measures)) and(currprogress < 100):
                    currprogress = await self._datasets[s].loadMore()
                    if currprogress < 0:
                        currprogress = 100
                    self._progresss[s] = currprogress
                    measures = self._datasets[s].get_measures()
                if idx < len(measures):
                    currnexttim = measures[idx].get_endTimeUTC()
                    self._nexttim[s] = currnexttim
            if currnexttim > 0:
                if (nexttime == 0) or (nexttime > currnexttim):
                    nexttime = currnexttim
            s = s + 1
        if nexttime == 0:
            return 100
        # //
        # Extract data for this timestamp
        # //
        del datarec[:]
        datarec.append(nexttime)
        globprogress = 0
        s = 0
        while s < self._nsensors:
            if self._nexttim[s] == nexttime:
                idx = self._nextidx[s]
                measures = self._datasets[s].get_measures()
                newvalue = measures[idx].get_averageValue()
                datarec.append(newvalue)
                self._nexttim[s] = 0.0
                self._nextidx[s] = idx + 1
            else:
                datarec.append(math.nan)
            currprogress = self._progresss[s]
            globprogress = globprogress + currprogress
            s = s + 1
        if globprogress > 0:
            globprogress = globprogress // self._nsensors
            if globprogress > 99:
                globprogress = 99

        return globprogress

    # --- (end of generated code: YConsolidatedDataSet implementation)


#################################################################################
#                                                                               #
#                            YMeasure, YSensor                                  #
#                                                                               #
#################################################################################

# --- (generated code: YMeasure class start)
# noinspection PyProtectedMember
class YMeasure:
    """
    YMeasure objects are used within the API to represent
    a value measured at a specified time. These objects are
    used in particular in conjunction with the YDataSet class,
    but also for sensors periodic timed reports
    (see sensor.registerTimedReportCallback).

    """
    # --- (end of generated code: YMeasure class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YMeasure return codes)
        pass
        # --- (end of generated code: YMeasure return codes)

    # --- (generated code: YMeasure attributes declaration)
    _start: float
    _end: float
    _minVal: float
    _avgVal: float
    _maxVal: float
    # --- (end of generated code: YMeasure attributes declaration)

    def __init__(self, start: float, end: float, minVal: float, avgVal: float, maxVal: float):
        # --- (generated code: YMeasure constructor)
        self._start = 0.0
        self._end = 0.0
        self._minVal = 0.0
        self._avgVal = 0.0
        self._maxVal = 0.0
        # --- (end of generated code: YMeasure constructor)
        self._start = start
        self._end = end
        self._minVal = minVal
        self._avgVal = avgVal
        self._maxVal = maxVal

    # --- (generated code: YMeasure implementation)
    def get_startTimeUTC(self) -> float:
        """
        Returns the start time of the measure, relative to the Jan 1, 1970 UTC
        (Unix timestamp). When the recording rate is higher then 1 sample
        per second, the timestamp may have a fractional part.

        @return a floating point number corresponding to the number of seconds
                between the Jan 1, 1970 UTC and the beginning of this measure.
        """
        return self._start

    def get_endTimeUTC(self) -> float:
        """
        Returns the end time of the measure, relative to the Jan 1, 1970 UTC
        (Unix timestamp). When the recording rate is higher than 1 sample
        per second, the timestamp may have a fractional part.

        @return a floating point number corresponding to the number of seconds
                between the Jan 1, 1970 UTC and the end of this measure.
        """
        return self._end

    def get_minValue(self) -> float:
        """
        Returns the smallest value observed during the time interval
        covered by this measure.

        @return a floating-point number corresponding to the smallest value observed.
        """
        return self._minVal

    def get_averageValue(self) -> float:
        """
        Returns the average value observed during the time interval
        covered by this measure.

        @return a floating-point number corresponding to the average value observed.
        """
        return self._avgVal

    def get_maxValue(self) -> float:
        """
        Returns the largest value observed during the time interval
        covered by this measure.

        @return a floating-point number corresponding to the largest value observed.
        """
        return self._maxVal

    # --- (end of generated code: YMeasure implementation)


# --- (generated code: YSensor class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YSensorValueCallback = Union[Callable[['YSensor', str], Any], None]
        YSensorTimedReportCallback = Union[Callable[['YSensor', YMeasure], Any], None]
    except TypeError:
        YSensorValueCallback = Union[Callable, Awaitable]
        YSensorTimedReportCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YSensor(YFunction):
    """
    The YSensor class is the parent class for all Yoctopuce sensor types. It can be
    used to read the current value and unit of any sensor, read the min/max
    value, configure autonomous recording frequency and access recorded data.
    It also provides a function to register a callback invoked each time the
    observed value changes, or at a predefined interval. Using this class rather
    than a specific subclass makes it possible to create generic applications
    that work with any Yoctopuce sensor, even those that do not yet exist.
    Note: The YAnButton class is the only analog input which does not inherit
    from YSensor.

    """
    # --- (end of generated code: YSensor class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSensor return codes)
        UNIT_INVALID: Final[str] = YAPI.INVALID_STRING
        CURRENTVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        LOWESTVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        HIGHESTVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        CURRENTRAWVALUE_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        LOGFREQUENCY_INVALID: Final[str] = YAPI.INVALID_STRING
        REPORTFREQUENCY_INVALID: Final[str] = YAPI.INVALID_STRING
        CALIBRATIONPARAM_INVALID: Final[str] = YAPI.INVALID_STRING
        RESOLUTION_INVALID: Final[float] = YAPI.INVALID_DOUBLE
        SENSORSTATE_INVALID: Final[int] = YAPI.INVALID_INT
        ADVMODE_IMMEDIATE: Final[int] = 0
        ADVMODE_PERIOD_AVG: Final[int] = 1
        ADVMODE_PERIOD_MIN: Final[int] = 2
        ADVMODE_PERIOD_MAX: Final[int] = 3
        ADVMODE_INVALID: Final[int] = -1
        # --- (end of generated code: YSensor return codes)

    # --- (generated code: YSensor attributes declaration)
    _valueCallback: YSensorValueCallback
    _timedReportCallback: YSensorTimedReportCallback
    _prevTR: float
    _iresol: float
    # --- (end of generated code: YSensor attributes declaration)
    _cal: Union[YCalibCtx, None]
    if not _IS_MICROPYTHON:
        _dataStreams: dict[str,YDataStream]

    def __init__(self, yctx: YAPIContext,  classname: str, func: str):
        super().__init__(yctx, classname, func)
        # --- (generated code: YSensor constructor)
        self._timedReportCallback = None
        self._prevTR = 0.0
        self._iresol = 0.0
        # --- (end of generated code: YSensor constructor)
        self._cal = None
        if not _IS_MICROPYTHON:
            self._dataStreams = dict()

    # DataStream objects cache
    async def _findDataStream(self, dataset: YDataSet, definition: str) -> Union[YDataStream | None]:
        if _IS_MICROPYTHON:
            self._throw(YAPI.NOT_SUPPORTED, "not yet supported, sorry")
            return None
        else:
            key: str = await dataset.get_functionId() + ":" + definition
            ds: Union[YDataStream | None] = self._dataStreams.get(key)
            if ds:
                return ds
            words = YAPIContext._decodeWords(definition)
            if len(words) < 14:
                self._throw(YAPI.VERSION_MISMATCH, "device firmware is too old")
                return None
            ds = YDataStream(self, dataset, words)  # type: ignore
            self._dataStreams[key] = ds
            return ds

    # Clear cache of DataStream object (undocumented)
    if not _IS_MICROPYTHON:
        def _clearDataStreamCache(self):
            self._dataStreams.clear()

    # --- (generated code: YSensor implementation)
    @classmethod
    def FindSensor(cls, func: str) -> YSensor:
        """
        Retrieves a sensor for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSensor.isOnline() to test if the sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the sensor, for instance
                MyDevice..

        @return a YSensor object allowing you to drive the sensor.
        """
        return cls.FindSensorInContext(YAPI, func)

    @classmethod
    def FindSensorInContext(cls, yctx: YAPIContext, func: str) -> YSensor:
        """
        Retrieves a sensor for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the sensor is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YSensor.isOnline() to test if the sensor is
        indeed online at a given time. In case of ambiguity when looking for
        a sensor by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the sensor, for instance
                MyDevice..

        @return a YSensor object allowing you to drive the sensor.
        """
        obj: Union[YSensor, None] = yctx._findInCache('Sensor', func)
        if obj:
            return obj
        return YSensor(yctx, 'Sensor', func)

    @classmethod
    def FirstSensor(cls) -> Union[YSensor, None]:
        """
        Starts the enumeration of sensors currently accessible.
        Use the method YSensor.nextSensor() to iterate on
        next sensors.

        @return a pointer to a YSensor object, corresponding to
                the first sensor currently online, or a None pointer
                if there are none.
        """
        return cls.FirstSensorInContext(YAPI)

    @classmethod
    def FirstSensorInContext(cls, yctx: YAPIContext) -> Union[YSensor, None]:
        """
        Starts the enumeration of sensors currently accessible.
        Use the method YSensor.nextSensor() to iterate on
        next sensors.

        @param yctx : a YAPI context.

        @return a pointer to a YSensor object, corresponding to
                the first sensor currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('Sensor')
        if hwid:
            return cls.FindSensorInContext(yctx, hwid2str(hwid))
        return None

    def nextSensor(self) -> Union[YSensor, None]:
        """
        Continues the enumeration of sensors started using yFirstSensor().
        Caution: You can't make any assumption about the returned sensors order.
        If you want to find a specific a sensor, use Sensor.findSensor()
        and a hardwareID or a logical name.

        @return a pointer to a YSensor object, corresponding to
                a sensor currently online, or a None pointer
                if there are no more sensors to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('Sensor', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindSensorInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_unit(self) -> str:
        """
        Returns the measuring unit for the measure.

        @return a string corresponding to the measuring unit for the measure

        On failure, throws an exception or returns YSensor.UNIT_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("unit")
        if json_val is None:
            return YSensor.UNIT_INVALID
        return json_val

    async def get_currentValue(self) -> float:
        """
        Returns the current value of the measure, in the specified unit, as a floating point number.
        Note that a get_currentValue() call will *not* start a measure in the device, it
        will just return the last measure that occurred in the device. Indeed, internally, each Yoctopuce
        devices is continuously making measurements at a hardware specific frequency.

        If continuously calling  get_currentValue() leads you to performances issues, then
        you might consider to switch to callback programming model. Check the "advanced
        programming" chapter in in your device user manual for more information.

        @return a floating point number corresponding to the current value of the measure, in the specified
        unit, as a floating point number

        On failure, throws an exception or returns YSensor.CURRENTVALUE_INVALID.
        """
        res: float
        if self._cal is None:
            res = await self._fromCache("currentValue")
            if res is None:
                return YSensor.CURRENTVALUE_INVALID
            res = res / 65536.0
        else:
            res = await self._fromCache("currentRawValue")
            if res is None:
                return YSensor.CURRENTVALUE_INVALID
            res = self._applyCalibration(round(res / 65.536) / 1000.0)
        return round(res * self._iresol) / self._iresol

    async def set_lowestValue(self, newval: float) -> int:
        """
        Changes the recorded minimal value observed. Can be used to reset the value returned
        by get_lowestValue().

        @param newval : a floating point number corresponding to the recorded minimal value observed

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("lowestValue", rest_val)

    async def get_lowestValue(self) -> float:
        """
        Returns the minimal value observed for the measure since the device was started.
        Can be reset to an arbitrary value thanks to set_lowestValue().

        @return a floating point number corresponding to the minimal value observed for the measure since
        the device was started

        On failure, throws an exception or returns YSensor.LOWESTVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("lowestValue")
        if json_val is None:
            return YSensor.LOWESTVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def set_highestValue(self, newval: float) -> int:
        """
        Changes the recorded maximal value observed. Can be used to reset the value returned
        by get_lowestValue().

        @param newval : a floating point number corresponding to the recorded maximal value observed

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("highestValue", rest_val)

    async def get_highestValue(self) -> float:
        """
        Returns the maximal value observed for the measure since the device was started.
        Can be reset to an arbitrary value thanks to set_highestValue().

        @return a floating point number corresponding to the maximal value observed for the measure since
        the device was started

        On failure, throws an exception or returns YSensor.HIGHESTVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("highestValue")
        if json_val is None:
            return YSensor.HIGHESTVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_currentRawValue(self) -> float:
        """
        Returns the uncalibrated, unrounded raw value returned by the
        sensor, in the specified unit, as a floating point number.

        @return a floating point number corresponding to the uncalibrated, unrounded raw value returned by the
                sensor, in the specified unit, as a floating point number

        On failure, throws an exception or returns YSensor.CURRENTRAWVALUE_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("currentRawValue")
        if json_val is None:
            return YSensor.CURRENTRAWVALUE_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_logFrequency(self) -> str:
        """
        Returns the datalogger recording frequency for this function, or "OFF"
        when measures are not stored in the data logger flash memory.

        @return a string corresponding to the datalogger recording frequency for this function, or "OFF"
                when measures are not stored in the data logger flash memory

        On failure, throws an exception or returns YSensor.LOGFREQUENCY_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("logFrequency")
        if json_val is None:
            return YSensor.LOGFREQUENCY_INVALID
        return json_val

    async def set_logFrequency(self, newval: str) -> int:
        """
        Changes the datalogger recording frequency for this function.
        The frequency can be specified as samples per second,
        as sample per minute (for instance "15/m") or in samples per
        hour (eg. "4/h"). To disable recording for this function, use
        the value "OFF". Note that setting the  datalogger recording frequency
        to a greater value than the sensor native sampling frequency is useless,
        and even counterproductive: those two frequencies are not related.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a string corresponding to the datalogger recording frequency for this function

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("logFrequency", rest_val)

    async def get_reportFrequency(self) -> str:
        """
        Returns the timed value notification frequency, or "OFF" if timed
        value notifications are disabled for this function.

        @return a string corresponding to the timed value notification frequency, or "OFF" if timed
                value notifications are disabled for this function

        On failure, throws an exception or returns YSensor.REPORTFREQUENCY_INVALID.
        """
        json_val: Union[str, None] = await self._fromCache("reportFrequency")
        if json_val is None:
            return YSensor.REPORTFREQUENCY_INVALID
        return json_val

    async def set_reportFrequency(self, newval: str) -> int:
        """
        Changes the timed value notification frequency for this function.
        The frequency can be specified as samples per second,
        as sample per minute (for instance "15/m") or in samples per
        hour (e.g. "4/h"). To disable timed value notifications for this
        function, use the value "OFF". Note that setting the  timed value
        notification frequency to a greater value than the sensor native
        sampling frequency is unless, and even counterproductive: those two
        frequencies are not related.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a string corresponding to the timed value notification frequency for this function

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = newval
        return await self._setAttr("reportFrequency", rest_val)

    async def get_advMode(self) -> int:
        """
        Returns the measuring mode used for the advertised value pushed to the parent hub.

        @return a value among YSensor.ADVMODE_IMMEDIATE, YSensor.ADVMODE_PERIOD_AVG,
        YSensor.ADVMODE_PERIOD_MIN and YSensor.ADVMODE_PERIOD_MAX corresponding to the measuring mode used
        for the advertised value pushed to the parent hub

        On failure, throws an exception or returns YSensor.ADVMODE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("advMode")
        if json_val is None:
            return YSensor.ADVMODE_INVALID
        return json_val

    async def set_advMode(self, newval: int) -> int:
        """
        Changes the measuring mode used for the advertised value pushed to the parent hub.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a value among YSensor.ADVMODE_IMMEDIATE, YSensor.ADVMODE_PERIOD_AVG,
        YSensor.ADVMODE_PERIOD_MIN and YSensor.ADVMODE_PERIOD_MAX corresponding to the measuring mode used
        for the advertised value pushed to the parent hub

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("advMode", rest_val)

    async def get_calibrationParam(self) -> str:
        json_val: Union[str, None] = await self._fromCache("calibrationParam")
        if json_val is None:
            return YSensor.CALIBRATIONPARAM_INVALID
        return json_val

    async def set_calibrationParam(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("calibrationParam", rest_val)

    async def set_resolution(self, newval: float) -> int:
        """
        Changes the resolution of the measured physical values. The resolution corresponds to the numerical precision
        when displaying value. It does not change the precision of the measure itself.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @param newval : a floating point number corresponding to the resolution of the measured physical values

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return await self._setAttr("resolution", rest_val)

    async def get_resolution(self) -> float:
        """
        Returns the resolution of the measured values. The resolution corresponds to the numerical precision
        of the measures, which is not always the same as the actual precision of the sensor.
        Remember to call the saveToFlash() method of the module if the modification must be kept.

        @return a floating point number corresponding to the resolution of the measured values

        On failure, throws an exception or returns YSensor.RESOLUTION_INVALID.
        """
        json_val: Union[float, None] = await self._fromCache("resolution")
        if json_val is None:
            return YSensor.RESOLUTION_INVALID
        return round(json_val / 65.536) / 1000.0

    async def get_sensorState(self) -> int:
        """
        Returns the sensor state code, which is zero when there is an up-to-date measure
        available or a positive code if the sensor is not able to provide a measure right now.

        @return an integer corresponding to the sensor state code, which is zero when there is an up-to-date measure
                available or a positive code if the sensor is not able to provide a measure right now

        On failure, throws an exception or returns YSensor.SENSORSTATE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("sensorState")
        if json_val is None:
            return YSensor.SENSORSTATE_INVALID
        return json_val

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YSensorValueCallback) -> int:
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

    def _parserHelper(self) -> int:
        calibStr: str
        # Store inverted resolution, to provide better rounding
        if self._cache["resolution"] > 0:
            self._iresol = round(65536.0 / self._cache["resolution"])
        else:
            self._iresol = 10000
        # Shortcut when there is no calibration parameter
        calibStr = self._cache["calibrationParam"]
        if calibStr == "0," or calibStr == "" or calibStr == "0":
            self._cal = None
            return 0
        # Parse calibration parameters only if they have changed
        if self._cal is None or not (self._cal.src == calibStr):
            self._parseCalibStr(calibStr)
        return 0

    async def isSensorReady(self) -> bool:
        """
        Checks if the sensor is currently able to provide an up-to-date measure.
        Returns false if the device is unreachable, or if the sensor does not have
        a current measure to transmit. No exception is raised if there is an error
        while trying to contact the device hosting $THEFUNCTION$.

        @return true if the sensor can provide an up-to-date measure, and false otherwise
        """
        try:
            if await self.get_sensorState() != 0:
                return False
        except YAPI_Exception:
            return False
        return True

    async def get_dataLogger(self) -> Union[YDataLogger, None]:
        """
        Returns the YDatalogger object of the device hosting the sensor. This method returns an object
        that can control global parameters of the data logger. The returned object
        should not be freed.

        @return an YDatalogger object, or None on error.
        """
        logger: Union[YDataLogger, None]
        modu: Union[YModule, None]
        serial: str
        hwid: str

        modu = await self.get_module()
        serial = await modu.get_serialNumber()
        if serial == YAPI.INVALID_STRING:
            return None
        hwid = serial + ".dataLogger"
        logger = YDataLogger.FindDataLogger(hwid)
        return logger

    def _parseCalibStr(self, calibStr: str) -> int:
        iCalib: list[int]
        caltyp: int
        calhdl: YCalibrationCallback
        maxpos: int
        position: int
        calpar: list[int] = []
        calraw: list[float] = []
        calref: list[float] = []
        fRaw: float
        fRef: float
        iRaw: int
        iRef: int
        if calibStr.find(",") >= 0:
            # Plain text format
            iCalib = YAPIContext._decodeFloats(calibStr)
            caltyp = iCalib[0] // 1000
            if caltyp < _YOCTO_CALIB_TYPE_OFS:
                # Unknown calibration type: calibrated value will be provided by the device
                self._cal = None
                return YAPI.SUCCESS
            calhdl = _linCalHdl
            if not calhdl:
                # Unknown calibration type: calibrated value will be provided by the device
                self._cal = None
                return YAPI.SUCCESS
            # New 32 bits text format
            maxpos = len(iCalib)
            del calpar[:]
            position = 1
            while position < maxpos:
                calpar.append(iCalib[position])
                position = position + 1
            del calraw[:]
            del calref[:]
            position = 1
            while position + 1 < maxpos:
                fRaw = iCalib[position]
                fRaw = fRaw / 1000.0
                fRef = iCalib[position + 1]
                fRef = fRef / 1000.0
                calraw.append(fRaw)
                calref.append(fRef)
                position = position + 2
        else:
            # Old recorder-encoded format, including encoding
            if _IS_MICROPYTHON:
                return YAPI.SUCCESS
            else:
                iCalib = YAPIContext._decodeWords(calibStr)
                if len(iCalib) <= 2:
                    # Unknown calibration type: calibrated value will be provided by the device
                    self._cal = None
                    return YAPI.SUCCESS
                caltyp = iCalib[2]
                calhdl = _linCalHdl
                if not calhdl:
                    # Unknown calibration type: calibrated value will be provided by the device
                    self._cal = None
                    return YAPI.SUCCESS
                if caltyp <= 10:
                    maxpos = caltyp
                else:
                    if caltyp <= 20:
                        maxpos = caltyp - 10
                    else:
                        maxpos = 5
                maxpos = 3 + 2 * maxpos
                if maxpos > len(iCalib):
                    maxpos = len(iCalib)
                del calpar[:]
                del calraw[:]
                del calref[:]
                position = 3
                while position + 1 < maxpos:
                    iRaw = iCalib[position]
                    iRef = iCalib[position + 1]
                    calpar.append(iRaw)
                    calpar.append(iRef)
                    calraw.append(YAPIContext._decimalToDouble(iRaw))
                    calref.append(YAPIContext._decimalToDouble(iRef))
                    position = position + 2
        self._cal = YCalibCtx(calibStr, caltyp, calpar, calraw, calref)
        return YAPI.SUCCESS

    async def startDataLogger(self) -> int:
        """
        Starts the data logger on the device. Note that the data logger
        will only save the measures on this sensor if the logFrequency
        is not set to "OFF".

        @return YAPI.SUCCESS if the call succeeds.
        """
        res: xarray

        res = await self._download("api/dataLogger/recording?recording=1")
        if not (len(res) > 0):
            self._throw(YAPI.IO_ERROR, "unable to start datalogger")
            return YAPI.IO_ERROR
        return YAPI.SUCCESS

    async def stopDataLogger(self) -> int:
        """
        Stops the datalogger on the device.

        @return YAPI.SUCCESS if the call succeeds.
        """
        res: xarray

        res = await self._download("api/dataLogger/recording?recording=0")
        if not (len(res) > 0):
            self._throw(YAPI.IO_ERROR, "unable to stop datalogger")
            return YAPI.IO_ERROR
        return YAPI.SUCCESS

    async def get_recordedData(self, startTime: float, endTime: float) -> YDataSet:
        """
        Retrieves a YDataSet object holding historical data for this
        sensor, for a specified time interval. The measures will be
        retrieved from the data logger, which must have been turned
        on at the desired time. See the documentation of the YDataSet
        class for information on how to get an overview of the
        recorded data, and how to load progressively a large set
        of measures from the data logger.

        This function only works if the device uses a recent firmware,
        as YDataSet objects are not supported by firmwares older than
        version 13000.

        @param startTime : the start of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without initial limit.
        @param endTime : the end of the desired measure time interval,
                as a Unix timestamp, i.e. the number of seconds since
                January 1, 1970 UTC. The special value 0 can be used
                to include any measure, without ending limit.

        @return an instance of YDataSet, providing access to historical
                data. Past measures can be loaded progressively
                using methods from the YDataSet object.
        """
        funcid: str
        funit: str

        funcid = await self.get_functionId()
        funit = await self.get_unit()
        return YDataSet(self, funcid, funit, startTime, endTime)

    async def calibrateFromPoints(self, rawValues: list[float], refValues: list[float]) -> int:
        """
        Configures error correction data points, in particular to compensate for
        a possible perturbation of the measure caused by an enclosure. It is possible
        to configure up to five correction points. Correction points must be provided
        in ascending order, and be in the range of the sensor. The device will automatically
        perform a linear interpolation of the error correction between specified
        points. Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        For more information on advanced capabilities to refine the calibration of
        sensors, please contact support@yoctopuce.com.

        @param rawValues : array of floating point numbers, corresponding to the raw
                values returned by the sensor for the correction points.
        @param refValues : array of floating point numbers, corresponding to the corrected
                values for the correction points.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val: str
        res: int

        rest_val = await self._encodeCalibrationPoints(rawValues, refValues)
        res = await self._setAttr("calibrationParam", rest_val)
        return res

    async def loadCalibrationPoints(self, rawValues: list[float], refValues: list[float]) -> int:
        """
        Retrieves error correction data points previously entered using the method
        calibrateFromPoints.

        @param rawValues : array of floating point numbers, that will be filled by the
                function with the raw sensor values for the correction points.
        @param refValues : array of floating point numbers, that will be filled by the
                function with the desired values for the correction points.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        del rawValues[:]
        del refValues[:]
        # Load function parameters if not yet loaded
        if ticks_past(self._cacheExpiration) or not self._cacheExpiration:
            if await self.load(self._yapi.GetCacheValidity()) != YAPI.SUCCESS:
                return YAPI.DEVICE_NOT_FOUND
        if self._cal is None:
            return YAPI.SUCCESS
        del rawValues[:]
        del refValues[:]
        for ii_0 in self._cal.raw:
            rawValues.append(ii_0)
        for ii_1 in self._cal.cal:
            refValues.append(ii_1)
        return YAPI.SUCCESS

    async def _encodeCalibrationPoints(self, rawValues: list[float], refValues: list[float]) -> str:
        res: str
        npt: int
        idx: int
        npt = len(rawValues)
        if npt != len(refValues):
            self._throw(YAPI.INVALID_ARGUMENT, "Invalid calibration parameters (size mismatch)")
            return YAPI.INVALID_STRING
        # Shortcut when building empty calibration parameters
        if npt == 0:
            return "0"
        # Encode using newer 32-bit fixed-point method
        res = "%d" % _YOCTO_CALIB_TYPE_OFS
        idx = 0
        while idx < npt:
            res = "%s,%f,%f" % (res, rawValues[idx], refValues[idx])
            idx = idx + 1
        return res

    def _applyCalibration(self, rawValue: float) -> float:
        if self._cal is None:
            return rawValue
        if rawValue == YSensor.CURRENTVALUE_INVALID:
            return YSensor.CURRENTVALUE_INVALID
        return _linCalHdl(rawValue, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)

    def _decodeTimedReport(self, timestamp: float, duration: float, report: ByteArrayLike) -> YMeasure:
        i: int
        byteVal: int
        poww: float
        minRaw: float
        avgRaw: float
        maxRaw: float
        sublen: int
        difRaw: float
        startTime: float
        endTime: float
        minVal: float
        avgVal: float
        maxVal: float
        if duration > 0:
            startTime = timestamp - duration
        else:
            startTime = self._prevTR
        endTime = timestamp
        self._prevTR = endTime
        if startTime == 0:
            startTime = endTime
        # 32 bits timed report format
        if len(report) <= 5:
            # sub-second report, 1-4 bytes
            poww = 1
            avgRaw = 0
            byteVal = 0
            i = 1
            while i < len(report):
                byteVal = report[i]
                avgRaw = avgRaw + poww * byteVal
                poww = poww * 0x100
                i = i + 1
            if (byteVal & 0x80) != 0:
                avgRaw = avgRaw - poww
            avgVal = avgRaw / 1000.0
            if self._cal:
                avgVal = _linCalHdl(avgVal, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
            minVal = avgVal
            maxVal = avgVal
        else:
            # averaged report: avg,avg-min,max-avg
            sublen = 1 + (report[1] & 3)
            poww = 1
            avgRaw = 0
            byteVal = 0
            i = 2
            while (sublen > 0) and(i < len(report)):
                byteVal = report[i]
                avgRaw = avgRaw + poww * byteVal
                poww = poww * 0x100
                i = i + 1
                sublen = sublen - 1
            if (byteVal & 0x80) != 0:
                avgRaw = avgRaw - poww
            sublen = 1 + ((report[1] >> 2) & 3)
            poww = 1
            difRaw = 0
            while (sublen > 0) and(i < len(report)):
                byteVal = report[i]
                difRaw = difRaw + poww * byteVal
                poww = poww * 0x100
                i = i + 1
                sublen = sublen - 1
            minRaw = avgRaw - difRaw
            sublen = 1 + ((report[1] >> 4) & 3)
            poww = 1
            difRaw = 0
            while (sublen > 0) and(i < len(report)):
                byteVal = report[i]
                difRaw = difRaw + poww * byteVal
                poww = poww * 0x100
                i = i + 1
                sublen = sublen - 1
            maxRaw = avgRaw + difRaw
            avgVal = avgRaw / 1000.0
            minVal = minRaw / 1000.0
            maxVal = maxRaw / 1000.0
            if self._cal:
                avgVal = _linCalHdl(avgVal, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
                minVal = _linCalHdl(minVal, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
                maxVal = _linCalHdl(maxVal, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
        return YMeasure(startTime, endTime, minVal, avgVal, maxVal)

    def _decodeVal(self, w: int) -> float:
        val: float
        val = w if w <= 0x7fffffff else -0x100000000 + w
        if self._cal:
            val = _linCalHdl(val, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
        return val

    def _decodeAvg(self, dw: int) -> float:
        val: float
        val = dw if dw <= 0x7fffffff else -0x100000000 + dw
        if self._cal:
            val = _linCalHdl(val, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
        return val

    # --- (end of generated code: YSensor implementation)

    async def registerTimedReportCallback(self, callback: YSensorTimedReportCallback) -> int:
        """
        Registers the callback function that is invoked on every periodic timed notification.
        The callback is invoked only during the execution of ySleep or yHandleEvents.
        This provides control over the time when the callback is triggered. For good responsiveness, remember to call
        one of these two functions periodically. To unregister a callback, pass a None pointer as argument.

        @param callback : the callback function to call, or a None pointer. The callback function should take two
                arguments: the function object of which the value has changed, and an YMeasure object describing
                the new advertised value.
        @noreturn
        """
        if callback:
            await self._yapi._UpdateTimedReportCallbackList(self, True)
        else:
            await self._yapi._UpdateTimedReportCallbackList(self, False)
        self._timedReportCallback = callback
        return YAPI.SUCCESS


#################################################################################
#                                                                               #
#                         Datalogger support                                    #
#                                                                               #
#################################################################################

# --- (generated code: YDataStream class start)
# noinspection PyRedundantParentheses
# noinspection PyUnusedLocal
# noinspection PyProtectedMember
class YDataStream:
    """
    DataStream objects represent bare recorded measure sequences,
    exactly as found within the data logger present on Yoctopuce
    sensors.

    In most cases, it is not necessary to use DataStream objects
    directly, as the DataSet objects (returned by the
    get_recordedData() method from sensors and the
    get_dataSets() method from the data logger) provide
    a more convenient interface.

    """
    # --- (end of generated code: YDataStream class start)
    if not _IS_MICROPYTHON:
        DATA_INVALID: float = YAPI.INVALID_DOUBLE
        DURATION_INVALID: float = YAPI.INVALID_DOUBLE
        # --- (generated code: YDataStream return codes)
        pass
        # --- (end of generated code: YDataStream return codes)

    _yapi: YAPIContext
    _cal: Union[YCalibCtx, None]
    # --- (generated code: YDataStream attributes declaration)
    _parent: YSensor
    _runNo: int
    _utcStamp: int
    _nCols: int
    _nRows: int
    _startTime: float
    _duration: float
    _dataSamplesInterval: float
    _firstMeasureDuration: float
    _columnNames: list[str]
    _functionId: str
    _isClosed: bool
    _isAvg: bool
    _minVal: float
    _avgVal: float
    _maxVal: float
    _values: list[list[float]]
    _isLoaded: bool
    # --- (end of generated code: YDataStream attributes declaration)

    def __init__(self, obj_parent: YSensor, obj_dataset: YDataSet, encoded: list[int]):
        # --- (generated code: YDataStream constructor)
        self._runNo = 0
        self._utcStamp = 0
        self._nCols = 0
        self._nRows = 0
        self._startTime = 0.0
        self._duration = 0.0
        self._dataSamplesInterval = 0.0
        self._firstMeasureDuration = 0.0
        self._columnNames = []
        self._functionId = ''
        self._isClosed = False
        self._isAvg = False
        self._minVal = 0.0
        self._avgVal = 0.0
        self._maxVal = 0.0
        self._values = []
        self._isLoaded = False
        # --- (end of generated code: YDataStream constructor)
        self._parent = obj_parent
        self._yapi = self._parent._yapi
        if obj_dataset is not None:
            self._initFromDataSet(obj_dataset, encoded)

    # --- (generated code: YDataStream implementation)
    def _parseCalibArr(self, iCalib: list[int]) -> int:
        caltyp: int
        calhdl: YCalibrationCallback
        maxpos: int
        position: int
        calpar: list[int] = []
        calraw: list[float] = []
        calref: list[float] = []
        fRaw: float
        fRef: float
        caltyp = iCalib[0] // 1000
        if caltyp < _YOCTO_CALIB_TYPE_OFS:
            # Unknown calibration type: calibrated value will be provided by the device
            self._cal = None
            return YAPI.SUCCESS
        calhdl = _linCalHdl
        if not calhdl:
            # Unknown calibration type: calibrated value will be provided by the device
            self._cal = None
            return YAPI.SUCCESS
        # New 32 bits text format
        maxpos = len(iCalib)
        del calpar[:]
        position = 1
        while position < maxpos:
            calpar.append(iCalib[position])
            position = position + 1

        del calraw[:]
        del calref[:]
        position = 1
        while position + 1 < maxpos:
            fRaw = iCalib[position]
            fRaw = fRaw / 1000.0
            fRef = iCalib[position + 1]
            fRef = fRef / 1000.0
            calraw.append(fRaw)
            calref.append(fRef)
            position = position + 2


        self._cal = YCalibCtx("", caltyp, calpar, calraw, calref)
        return YAPI.SUCCESS

    def _initFromDataSet(self, dataset: YDataSet, encoded: list[int]) -> int:
        val: int
        ms_offset: int
        samplesPerHour: int
        caltyp: int
        iCalib: list[int]
        # decode sequence header to extract data
        self._runNo = encoded[0] + ((encoded[1] << 16))
        self._utcStamp = encoded[2] + ((encoded[3] << 16))
        val = encoded[4]
        self._isAvg = ((val & 0x100) == 0)
        samplesPerHour = (val & 0xff)
        if (val & 0x100) != 0:
            samplesPerHour = samplesPerHour * 3600
        else:
            if (val & 0x200) != 0:
                samplesPerHour = samplesPerHour * 60
        self._dataSamplesInterval = 3600.0 / samplesPerHour
        ms_offset = encoded[6]
        if ms_offset < 1000:
            # new encoding -> add the ms to the UTC timestamp
            self._startTime = self._utcStamp + (ms_offset / 1000.0)
        else:
            # legacy encoding subtract the measure interval form the UTC timestamp
            self._startTime = self._utcStamp - self._dataSamplesInterval
        self._firstMeasureDuration = encoded[5]
        if not self._isAvg:
            self._firstMeasureDuration = self._firstMeasureDuration / 1000.0
        val = encoded[7]
        self._isClosed = (val != 0xffff)
        if val == 0xffff:
            val = 0
        self._nRows = val
        if self._nRows > 0:
            if self._firstMeasureDuration > 0:
                self._duration = self._firstMeasureDuration + (self._nRows - 1) * self._dataSamplesInterval
            else:
                self._duration = self._nRows * self._dataSamplesInterval
        else:
            self._duration = 0
        # precompute decoding parameters
        iCalib = dataset._get_calibration()
        caltyp = iCalib[0]
        if caltyp == 0:
            self._cal = None
        else:
            self._parseCalibArr(iCalib)
        # preload column names for backward-compatibility
        self._functionId = dataset._functionId
        if self._isAvg:
            del self._columnNames[:]
            self._columnNames.append("%s_min" % self._functionId)
            self._columnNames.append("%s_avg" % self._functionId)
            self._columnNames.append("%s_max" % self._functionId)
            self._nCols = 3
        else:
            del self._columnNames[:]
            self._columnNames.append(self._functionId)
            self._nCols = 1
        # decode min/avg/max values for the sequence
        if self._nRows > 0:
            self._avgVal = self._decodeAvg(encoded[8] + (((encoded[9] ^ 0x8000) << 16)), 1)
            self._minVal = self._decodeVal(encoded[10] + ((encoded[11] << 16)))
            self._maxVal = self._decodeVal(encoded[12] + ((encoded[13] << 16)))
        return 0

    def _parseStream(self, sdata: xarray) -> int:
        idx: int
        udat: list[int] = []
        dat: list[float] = []
        if self._isLoaded and not self._isClosed:
            return YAPI.SUCCESS
        if len(sdata) == 0:
            self._nRows = 0
            return YAPI.SUCCESS

        udat = YAPIContext._decodeWords(self._parent._json_get_string(sdata))
        del self._values[:]
        idx = 0
        if self._isAvg:
            while idx + 3 < len(udat):
                del dat[:]
                if (udat[idx] == 65535) and (udat[idx + 1] == 65535):
                    dat.append(math.nan)
                    dat.append(math.nan)
                    dat.append(math.nan)
                else:
                    dat.append(self._decodeVal(udat[idx + 2] + (((udat[idx + 3]) << 16))))
                    dat.append(self._decodeAvg(udat[idx] + ((((udat[idx + 1]) ^ 0x8000) << 16)), 1))
                    dat.append(self._decodeVal(udat[idx + 4] + (((udat[idx + 5]) << 16))))
                idx = idx + 6
                self._values.append(dat[:])
        else:
            while idx + 1 < len(udat):
                del dat[:]
                if (udat[idx] == 65535) and (udat[idx + 1] == 65535):
                    dat.append(math.nan)
                else:
                    dat.append(self._decodeAvg(udat[idx] + ((((udat[idx + 1]) ^ 0x8000) << 16)), 1))
                self._values.append(dat[:])
                idx = idx + 2

        self._nRows = len(self._values)
        self._isLoaded = True
        return YAPI.SUCCESS

    def _wasLoaded(self) -> bool:
        return self._isLoaded

    def _get_url(self) -> str:
        url: str
        url = "logger.json?id=%s&run=%d&utc=%u" % (self._functionId, self._runNo, self._utcStamp)
        return url

    def _get_baseurl(self) -> str:
        url: str
        url = "logger.json?id=%s&run=%d&utc=" % (self._functionId, self._runNo)
        return url

    def _get_urlsuffix(self) -> str:
        url: str
        url = "%u" % self._utcStamp
        return url

    async def loadStream(self) -> int:
        return self._parseStream(await self._parent._download(self._get_url()))

    def _decodeVal(self, w: int) -> float:
        val: float
        val = (w if w <= 0x7fffffff else -0x100000000 + w) / 1000.0
        if self._cal:
            val = _linCalHdl(val, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
        return val

    def _decodeAvg(self, dw: int, count: int) -> float:
        val: float
        val = (dw if dw <= 0x7fffffff else -0x100000000 + dw) / 1000.0
        if self._cal:
            val = _linCalHdl(val, self._cal.typ, self._cal.par, self._cal.raw, self._cal.cal)
        return val

    def isClosed(self) -> bool:
        return self._isClosed

    def get_runIndex(self) -> int:
        """
        Returns the run index of the data stream. A run can be made of
        multiple datastreams, for different time intervals.

        @return an unsigned number corresponding to the run index.
        """
        return self._runNo

    async def get_startTime(self) -> int:
        """
        Returns the relative start time of the data stream, measured in seconds.
        For recent firmwares, the value is relative to the present time,
        which means the value is always negative.
        If the device uses a firmware older than version 13000, value is
        relative to the start of the time the device was powered on, and
        is always positive.
        If you need an absolute UTC timestamp, use get_realStartTimeUTC().

        <b>DEPRECATED</b>: This method has been replaced by get_realStartTimeUTC().

        @return an unsigned number corresponding to the number of seconds
                between the start of the run and the beginning of this data
                stream.
        """
        return self._utcStamp - int(time.time())

    def get_startTimeUTC(self) -> int:
        """
        Returns the start time of the data stream, relative to the Jan 1, 1970.
        If the UTC time was not set in the datalogger at the time of the recording
        of this data stream, this method returns 0.

        <b>DEPRECATED</b>: This method has been replaced by get_realStartTimeUTC().

        @return an unsigned number corresponding to the number of seconds
                between the Jan 1, 1970 and the beginning of this data
                stream (i.e. Unix time representation of the absolute time).
        """
        return int(round(self._startTime))

    def get_realStartTimeUTC(self) -> float:
        """
        Returns the start time of the data stream, relative to the Jan 1, 1970.
        If the UTC time was not set in the datalogger at the time of the recording
        of this data stream, this method returns 0.

        @return a floating-point number  corresponding to the number of seconds
                between the Jan 1, 1970 and the beginning of this data
                stream (i.e. Unix time representation of the absolute time).
        """
        return self._startTime

    def get_dataSamplesIntervalMs(self) -> int:
        """
        Returns the number of milliseconds between two consecutive
        rows of this data stream. By default, the data logger records one row
        per second, but the recording frequency can be changed for
        each device function

        @return an unsigned number corresponding to a number of milliseconds.
        """
        return int(round(self._dataSamplesInterval*1000))

    def get_dataSamplesInterval(self) -> float:
        return self._dataSamplesInterval

    def get_firstDataSamplesInterval(self) -> float:
        return self._firstMeasureDuration

    async def get_rowCount(self) -> int:
        """
        Returns the number of data rows present in this stream.

        If the device uses a firmware older than version 13000,
        this method fetches the whole data stream from the device
        if not yet done, which can cause a little delay.

        @return an unsigned number corresponding to the number of rows.

        On failure, throws an exception or returns zero.
        """
        if (self._nRows != 0) and self._isClosed:
            return self._nRows
        await self.loadStream()
        return self._nRows

    async def get_columnCount(self) -> int:
        """
        Returns the number of data columns present in this stream.
        The meaning of the values present in each column can be obtained
        using the method get_columnNames().

        If the device uses a firmware older than version 13000,
        this method fetches the whole data stream from the device
        if not yet done, which can cause a little delay.

        @return an unsigned number corresponding to the number of columns.

        On failure, throws an exception or returns zero.
        """
        if self._nCols != 0:
            return self._nCols
        await self.loadStream()
        return self._nCols

    async def get_columnNames(self) -> list[str]:
        """
        Returns the title (or meaning) of each data column present in this stream.
        In most case, the title of the data column is the hardware identifier
        of the sensor that produced the data. For streams recorded at a lower
        recording rate, the dataLogger stores the min, average and max value
        during each measure interval into three columns with suffixes _min,
        _avg and _max respectively.

        If the device uses a firmware older than version 13000,
        this method fetches the whole data stream from the device
        if not yet done, which can cause a little delay.

        @return a list containing as many strings as there are columns in the
                data stream.

        On failure, throws an exception or returns an empty array.
        """
        if len(self._columnNames) != 0:
            return self._columnNames
        await self.loadStream()
        return self._columnNames

    def get_minValue(self) -> float:
        """
        Returns the smallest measure observed within this stream.
        If the device uses a firmware older than version 13000,
        this method will always return YDataStream.DATA_INVALID.

        @return a floating-point number corresponding to the smallest value,
                or YDataStream.DATA_INVALID if the stream is not yet complete (still recording).

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        return self._minVal

    def get_averageValue(self) -> float:
        """
        Returns the average of all measures observed within this stream.
        If the device uses a firmware older than version 13000,
        this method will always return YDataStream.DATA_INVALID.

        @return a floating-point number corresponding to the average value,
                or YDataStream.DATA_INVALID if the stream is not yet complete (still recording).

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        return self._avgVal

    def get_maxValue(self) -> float:
        """
        Returns the largest measure observed within this stream.
        If the device uses a firmware older than version 13000,
        this method will always return YDataStream.DATA_INVALID.

        @return a floating-point number corresponding to the largest value,
                or YDataStream.DATA_INVALID if the stream is not yet complete (still recording).

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        return self._maxVal

    def get_realDuration(self) -> float:
        if self._isClosed:
            return self._duration
        return float(int(time.time()) - self._utcStamp)

    async def get_dataRows(self) -> list[list[float]]:
        """
        Returns the whole data set contained in the stream, as a bidimensional
        table of numbers.
        The meaning of the values present in each column can be obtained
        using the method get_columnNames().

        This method fetches the whole data stream from the device,
        if not yet done.

        @return a list containing as many elements as there are rows in the
                data stream. Each row itself is a list of floating-point
                numbers.

        On failure, throws an exception or returns an empty array.
        """
        if (len(self._values) == 0) or not self._isClosed:
            await self.loadStream()
        return self._values

    async def get_data(self, row: int, col: int) -> float:
        """
        Returns a single measure from the data stream, specified by its
        row and column index.
        The meaning of the values present in each column can be obtained
        using the method get_columnNames().

        This method fetches the whole data stream from the device,
        if not yet done.

        @param row : row index
        @param col : column index

        @return a floating-point number

        On failure, throws an exception or returns YDataStream.DATA_INVALID.
        """
        if (len(self._values) == 0) or not self._isClosed:
            await self.loadStream()
        if row >= len(self._values):
            return YDataStream.DATA_INVALID
        if col >= len(self._values[row]):
            return YDataStream.DATA_INVALID
        return self._values[row][col]

    # --- (end of generated code: YDataStream implementation)


# --- (generated code: YDataSet class start)
# noinspection PyRedundantParentheses
# noinspection PyUnusedLocal
# noinspection PyProtectedMember
class YDataSet:
    """
    YDataSet objects make it possible to retrieve a set of recorded measures
    for a given sensor and a specified time interval. They can be used
    to load data points with a progress report. When the YDataSet object is
    instantiated by the sensor.get_recordedData()  function, no data is
    yet loaded from the module. It is only when the loadMore()
    method is called over and over than data will be effectively loaded
    from the dataLogger.

    A preview of available measures is available using the function
    get_preview() as soon as loadMore() has been called
    once. Measures themselves are available using function get_measures()
    when loaded by subsequent calls to loadMore().

    This class can only be used on devices that use a relatively recent firmware,
    as YDataSet objects are not supported by firmwares older than version 13000.

    """
    # --- (end of generated code: YDataSet class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YDataSet return codes)
        pass
        # --- (end of generated code: YDataSet return codes)

    _yapi: YAPIContext
    # --- (generated code: YDataSet attributes declaration)
    _parent: YSensor
    _hardwareId: str
    _functionId: str
    _unit: str
    _bulkLoad: int
    _startTimeMs: float
    _endTimeMs: float
    _progress: int
    _calib: list[int]
    _streams: list[YDataStream]
    _summary: YMeasure
    _preview: list[YMeasure]
    _measures: list[YMeasure]
    _summaryMinVal: float
    _summaryMaxVal: float
    _summaryTotalAvg: float
    _summaryTotalTime: float
    # --- (end of generated code: YDataSet attributes declaration)

    def __init__(self, parent: YSensor, functionId: str = '', unit: str = '', startTime: float = 0.0, endTime: float = 0.0):
        # --- (generated code: YDataSet constructor)
        self._hardwareId = ''
        self._functionId = ''
        self._unit = ''
        self._bulkLoad = 0
        self._startTimeMs = 0.0
        self._endTimeMs = 0.0
        self._progress = 0
        self._calib = []
        self._streams = []
        self._preview = []
        self._measures = []
        self._summaryMinVal = 0.0
        self._summaryMaxVal = 0.0
        self._summaryTotalAvg = 0.0
        self._summaryTotalTime = 0.0
        # --- (end of generated code: YDataSet constructor)
        self._summary = YMeasure(0, 0, 0, 0, 0)
        if not functionId:
            self._initFromJson(parent)
        else:
            self._initFromParams(parent, functionId, unit, startTime, endTime)

    def _initFromParams(self, parent: YSensor, functionId: str, unit: str, startTime: float, endTime: float):
        self._yapi = parent._yapi
        self._parent = parent
        self._functionId = functionId
        self._unit = unit
        self._startTimeMs = startTime * 1000
        self._endTimeMs = endTime * 1000
        self._progress = -1

    def _initFromJson(self, parent: YSensor):
        self._yapi = parent._yapi
        self._parent = parent
        self._startTimeMs = 0
        self._endTimeMs = 0

    # YDataSet parser for stream list
    async def _parse(self, jsonBlob: str) -> int:
        jsonBin: xarray = xbytearray(jsonBlob, 'latin-1')
        loadval: Union[dict, None] = None
        try:
            loadval = json.load(xStringIO(jsonBin))
        except ValueError:
            pass
        if loadval is None:
            # no data available
            self._progress = 0
            return self.get_progress()

        self._functionId = loadval["id"]
        self._unit = loadval["unit"]
        if "bulk" in loadval:
            self._bulkLoad = YAPI._atoi(loadval["bulk"])
        if "calib" in loadval:
            self._calib = YAPIContext._decodeFloats(loadval["calib"])
            self._calib[0] = round(self._calib[0] / 1000)
        else:
            self._calib = YAPIContext._decodeWords(loadval["cal"])
        self._streams = []
        self._preview = []
        self._measures = []
        for i in range(len(loadval["streams"])):
            stream: Union[YDataStream | None] = await self._parent._findDataStream(self, loadval["streams"][i])
            if stream is None:
                return YAPI.IO_ERROR
            streamStartTime: float = stream.get_realStartTimeUTC() * 1000
            streamEndTime: float = streamStartTime + stream.get_realDuration() * 1000
            if self._startTimeMs > 0 and streamEndTime <= self._startTimeMs:
                # this stream is too early, drop it
                pass
            elif streamStartTime >= self._endTimeMs > 0:
                # this stream is too late, drop it
                pass
            else:
                self._streams.append(stream)
        self._progress = 0
        return self.get_progress()

    # --- (generated code: YDataSet implementation)
    def _get_calibration(self) -> list[int]:
        return self._calib

    async def loadSummary(self, data: xarray) -> int:
        dataRows: list[list[float]] = []
        tim: float
        mitv: float
        itv: float
        fitv: float
        end_: float
        nCols: int
        minCol: int
        avgCol: int
        maxCol: int
        res: int
        m_pos: int
        previewTotalTime: float
        previewTotalAvg: float
        previewMinVal: float
        previewMaxVal: float
        previewAvgVal: float
        previewStartMs: float
        previewStopMs: float
        previewDuration: float
        streamStartTimeMs: float
        streamDuration: float
        streamEndTimeMs: float
        minVal: float
        avgVal: float
        maxVal: float
        summaryStartMs: float
        summaryStopMs: float
        summaryTotalTime: float
        summaryTotalAvg: float
        summaryMinVal: float
        summaryMaxVal: float
        url: str
        strdata: str
        measure_data: list[float] = []

        if self._progress < 0:
            strdata = data.decode('latin-1')
            if strdata == "{}":
                self._parent._throw(YAPI.VERSION_MISMATCH, "device firmware is too old")
                return YAPI.VERSION_MISMATCH
            res = await self._parse(strdata)
            if res < 0:
                return res
        summaryTotalTime = 0
        summaryTotalAvg = 0
        summaryMinVal = YAPI.MAX_DOUBLE
        summaryMaxVal = YAPI.MIN_DOUBLE
        summaryStartMs = YAPI.MAX_DOUBLE
        summaryStopMs = YAPI.MIN_DOUBLE

        # Parse complete streams
        for ii_0 in self._streams:
            streamStartTimeMs = round(ii_0.get_realStartTimeUTC() * 1000)
            streamDuration = ii_0.get_realDuration()
            streamEndTimeMs = streamStartTimeMs + round(streamDuration * 1000)
            if (streamStartTimeMs >= self._startTimeMs) and ((self._endTimeMs == 0) or (streamEndTimeMs <= self._endTimeMs)):
                # stream that are completely inside the dataset
                previewMinVal = ii_0.get_minValue()
                previewAvgVal = ii_0.get_averageValue()
                previewMaxVal = ii_0.get_maxValue()
                previewStartMs = streamStartTimeMs
                previewStopMs = streamEndTimeMs
                previewDuration = streamDuration
            else:
                # stream that are partially in the dataset
                # we need to parse data to filter value outside the dataset
                if not ii_0._wasLoaded():
                    url = ii_0._get_url()
                    data = await self._parent._download(url)
                    ii_0._parseStream(data)
                dataRows = await ii_0.get_dataRows()
                if len(dataRows) == 0:
                    return self.get_progress()
                tim = streamStartTimeMs
                fitv = round(ii_0.get_firstDataSamplesInterval() * 1000)
                itv = round(ii_0.get_dataSamplesInterval() * 1000)
                nCols = len(dataRows[0])
                minCol = 0
                if nCols > 2:
                    avgCol = 1
                else:
                    avgCol = 0
                if nCols > 2:
                    maxCol = 2
                else:
                    maxCol = 0
                previewTotalTime = 0
                previewTotalAvg = 0
                previewStartMs = streamEndTimeMs
                previewStopMs = streamStartTimeMs
                previewMinVal = YAPI.MAX_DOUBLE
                previewMaxVal = YAPI.MIN_DOUBLE
                m_pos = 0
                while m_pos < len(dataRows):
                    measure_data = dataRows[m_pos]
                    if m_pos == 0:
                        mitv = fitv
                    else:
                        mitv = itv
                    end_ = tim + mitv
                    if (end_ > self._startTimeMs) and ((self._endTimeMs == 0) or (tim < self._endTimeMs)):
                        minVal = measure_data[minCol]
                        avgVal = measure_data[avgCol]
                        maxVal = measure_data[maxCol]
                        if previewStartMs > tim:
                            previewStartMs = tim
                        if previewStopMs < end_:
                            previewStopMs = end_
                        if previewMinVal > minVal:
                            previewMinVal = minVal
                        if previewMaxVal < maxVal:
                            previewMaxVal = maxVal
                        if not math.isnan(avgVal):
                            previewTotalAvg = previewTotalAvg + (avgVal * mitv)
                            previewTotalTime = previewTotalTime + mitv
                    tim = end_
                    m_pos = m_pos + 1
                if previewTotalTime > 0:
                    previewAvgVal = previewTotalAvg / previewTotalTime
                    previewDuration = (previewStopMs - previewStartMs) / 1000.0
                else:
                    previewAvgVal = 0.0
                    previewDuration = 0.0
            self._preview.append(YMeasure(previewStartMs / 1000.0, previewStopMs / 1000.0, previewMinVal, previewAvgVal, previewMaxVal))
            if summaryMinVal > previewMinVal:
                summaryMinVal = previewMinVal
            if summaryMaxVal < previewMaxVal:
                summaryMaxVal = previewMaxVal
            if summaryStartMs > previewStartMs:
                summaryStartMs = previewStartMs
            if summaryStopMs < previewStopMs:
                summaryStopMs = previewStopMs
            summaryTotalAvg = summaryTotalAvg + (previewAvgVal * previewDuration)
            summaryTotalTime = summaryTotalTime + previewDuration
        if (self._startTimeMs == 0) or (self._startTimeMs > summaryStartMs):
            self._startTimeMs = summaryStartMs
        if (self._endTimeMs == 0) or (self._endTimeMs < summaryStopMs):
            self._endTimeMs = summaryStopMs
        if summaryTotalTime > 0:
            self._summary = YMeasure(summaryStartMs / 1000.0, summaryStopMs / 1000.0, summaryMinVal, summaryTotalAvg / summaryTotalTime, summaryMaxVal)
        else:
            self._summary = YMeasure(0.0, 0.0, YAPI.INVALID_DOUBLE, YAPI.INVALID_DOUBLE, YAPI.INVALID_DOUBLE)
        return self.get_progress()

    async def processMore(self, progress: int, data: xarray) -> int:
        stream: Union[YDataStream, None]
        dataRows: list[list[float]] = []
        tim: float
        itv: float
        fitv: float
        avgv: float
        end_: float
        nCols: int
        minCol: int
        avgCol: int
        maxCol: int
        firstMeasure: bool
        baseurl: str
        url: str
        suffix: str
        suffixes: list[str] = []
        idx: int
        bulkFile: xarray
        urlIdx: int
        streamBin: list[xarray] = []

        if progress != self._progress:
            return self._progress
        if self._progress < 0:
            return await self.loadSummary(data)
        stream = self._streams[self._progress]
        if not stream._wasLoaded():
            stream._parseStream(data)
        dataRows = await stream.get_dataRows()
        self._progress = self._progress + 1
        if len(dataRows) == 0:
            return self.get_progress()
        tim = round(stream.get_realStartTimeUTC() * 1000)
        fitv = round(stream.get_firstDataSamplesInterval() * 1000)
        itv = round(stream.get_dataSamplesInterval() * 1000)
        if fitv == 0:
            fitv = itv
        if tim < itv:
            tim = itv
        nCols = len(dataRows[0])
        minCol = 0
        if nCols > 2:
            avgCol = 1
        else:
            avgCol = 0
        if nCols > 2:
            maxCol = 2
        else:
            maxCol = 0

        firstMeasure = True
        for ii_0 in dataRows:
            if firstMeasure:
                end_ = tim + fitv
                firstMeasure = False
            else:
                end_ = tim + itv
            avgv = ii_0[avgCol]
            if (end_ > self._startTimeMs) and ((self._endTimeMs == 0) or (tim < self._endTimeMs)) and not math.isnan(avgv):
                self._measures.append(YMeasure(tim / 1000, end_ / 1000, ii_0[minCol], avgv, ii_0[maxCol]))
            tim = end_

        # Perform bulk preload to speed-up network transfer
        if (self._bulkLoad > 0) and (self._progress < len(self._streams)):
            stream = self._streams[self._progress]
            if stream._wasLoaded():
                return self.get_progress()
            baseurl = stream._get_baseurl()
            url = stream._get_url()
            suffix = stream._get_urlsuffix()
            suffixes.append(suffix)
            idx = self._progress + 1
            while (idx < len(self._streams)) and(len(suffixes) < self._bulkLoad):
                stream = self._streams[idx]
                if not stream._wasLoaded() and (stream._get_baseurl() == baseurl):
                    suffix = stream._get_urlsuffix()
                    suffixes.append(suffix)
                    url = url + "," + suffix
                idx = idx + 1
            bulkFile = await self._parent._download(url)
            streamBin = self._parent._json_get_array(bulkFile)
            urlIdx = 0
            idx = self._progress
            while (idx < len(self._streams)) and(urlIdx < len(suffixes)) and(urlIdx < len(streamBin)):
                stream = self._streams[idx]
                if (stream._get_baseurl() == baseurl) and (stream._get_urlsuffix() == suffixes[urlIdx]):
                    stream._parseStream(streamBin[urlIdx])
                    urlIdx = urlIdx + 1
                idx = idx + 1
        return self.get_progress()

    def get_privateDataStreams(self) -> list[YDataStream]:
        return self._streams

    async def get_hardwareId(self) -> str:
        """
        Returns the unique hardware identifier of the function who performed the measures,
        in the form SERIAL.FUNCTIONID. The unique hardware identifier is composed of the
        device serial number and of the hardware identifier of the function
        (for example THRMCPL1-123456.temperature1)

        @return a string that uniquely identifies the function (ex: THRMCPL1-123456.temperature1)

        On failure, throws an exception or returns  YDataSet.HARDWAREID_INVALID.
        """
        mo: Union[YModule, None]
        if not (self._hardwareId == ""):
            return self._hardwareId
        mo = await self._parent.get_module()
        self._hardwareId = "%s.%s" % (await mo.get_serialNumber(), await self.get_functionId())
        return self._hardwareId

    async def get_functionId(self) -> str:
        """
        Returns the hardware identifier of the function that performed the measure,
        without reference to the module. For example temperature1.

        @return a string that identifies the function (ex: temperature1)
        """
        return self._functionId

    async def get_unit(self) -> str:
        """
        Returns the measuring unit for the measured value.

        @return a string that represents a physical unit.

        On failure, throws an exception or returns  YDataSet.UNIT_INVALID.
        """
        return self._unit

    def get_startTimeUTC(self) -> int:
        """
        Returns the start time of the dataset, relative to the Jan 1, 1970.
        When the YDataSet object is created, the start time is the value passed
        in parameter to the get_dataSet() function. After the
        very first call to loadMore(), the start time is updated
        to reflect the timestamp of the first measure actually found in the
        dataLogger within the specified range.

        <b>DEPRECATED</b>: This method has been replaced by get_summary()
        which contain more precise informations.

        @return an unsigned number corresponding to the number of seconds
                between the Jan 1, 1970 and the beginning of this data
                set (i.e. Unix time representation of the absolute time).
        """
        return self.imm_get_startTimeUTC()

    def imm_get_startTimeUTC(self) -> int:
        return int((self._startTimeMs / 1000.0))

    def get_endTimeUTC(self) -> int:
        """
        Returns the end time of the dataset, relative to the Jan 1, 1970.
        When the YDataSet object is created, the end time is the value passed
        in parameter to the get_dataSet() function. After the
        very first call to loadMore(), the end time is updated
        to reflect the timestamp of the last measure actually found in the
        dataLogger within the specified range.

        <b>DEPRECATED</b>: This method has been replaced by get_summary()
        which contain more precise informations.

        @return an unsigned number corresponding to the number of seconds
                between the Jan 1, 1970 and the end of this data
                set (i.e. Unix time representation of the absolute time).
        """
        return self.imm_get_endTimeUTC()

    def imm_get_endTimeUTC(self) -> int:
        return int(round(self._endTimeMs / 1000.0))

    def get_progress(self) -> int:
        """
        Returns the progress of the downloads of the measures from the data logger,
        on a scale from 0 to 100. When the object is instantiated by get_dataSet,
        the progress is zero. Each time loadMore() is invoked, the progress
        is updated, to reach the value 100 only once all measures have been loaded.

        @return an integer in the range 0 to 100 (percentage of completion).
        """
        if self._progress < 0:
            return 0
        # index not yet loaded
        if self._progress >= len(self._streams):
            return 100
        return (1 + (1 + self._progress) * 98) // (1 + len(self._streams))

    async def loadMore(self) -> int:
        """
        Loads the next block of measures from the dataLogger, and updates
        the progress indicator.

        @return an integer in the range 0 to 100 (percentage of completion),
                or a negative error code in case of failure.

        On failure, throws an exception or returns a negative error code.
        """
        url: str
        stream: Union[YDataStream, None]
        if self._progress < 0:
            url = "logger.json?id=%s" % self._functionId
            if self._startTimeMs != 0:
                url = "%s&from=%u" % (url, self.imm_get_startTimeUTC())
            if self._endTimeMs != 0:
                url = "%s&to=%u" % (url, self.imm_get_endTimeUTC() + 1)
        else:
            if self._progress >= len(self._streams):
                return 100
            else:
                stream = self._streams[self._progress]
                if stream._wasLoaded():
                    # Do not reload stream if it was already loaded
                    return await self.processMore(self._progress, xbytearray("", 'latin-1'))
                url = stream._get_url()
        try:
            return await self.processMore(self._progress, await self._parent._download(url))
        except YAPI_Exception:
            return await self.processMore(self._progress, await self._parent._download(url))

    def get_summary(self) -> YMeasure:
        """
        Returns an YMeasure object which summarizes the whole
        YDataSet. In includes the following information:
        - the start of a time interval
        - the end of a time interval
        - the minimal value observed during the time interval
        - the average value observed during the time interval
        - the maximal value observed during the time interval

        This summary is available as soon as loadMore() has
        been called for the first time.

        @return an YMeasure object
        """
        return self._summary

    def get_preview(self) -> list[YMeasure]:
        """
        Returns a condensed version of the measures that can
        retrieved in this YDataSet, as a list of YMeasure
        objects. Each item includes:
        - the start of a time interval
        - the end of a time interval
        - the minimal value observed during the time interval
        - the average value observed during the time interval
        - the maximal value observed during the time interval

        This preview is available as soon as loadMore() has
        been called for the first time.

        @return a table of records, where each record depicts the
                measured values during a time interval

        On failure, throws an exception or returns an empty array.
        """
        return self._preview

    async def get_measuresAt(self, measure: YMeasure) -> list[YMeasure]:
        """
        Returns the detailed set of measures for the time interval corresponding
        to a given condensed measures previously returned by get_preview().
        The result is provided as a list of YMeasure objects.

        @param measure : condensed measure from the list previously returned by
                get_preview().

        @return a table of records, where each record depicts the
                measured values during a time interval

        On failure, throws an exception or returns an empty array.
        """
        startUtcMs: float
        stream: Union[YDataStream, None]
        dataRows: list[list[float]] = []
        measures: Union[list[YMeasure], None] = []
        tim: float
        itv: float
        end_: float
        nCols: int
        minCol: int
        avgCol: int
        maxCol: int

        startUtcMs = measure.get_startTimeUTC() * 1000
        stream = None
        for ii_0 in self._streams:
            if round(ii_0.get_realStartTimeUTC() *1000) == startUtcMs:
                stream = ii_0
        if stream is None:
            return measures
        dataRows = await stream.get_dataRows()
        if len(dataRows) == 0:
            return measures
        tim = round(stream.get_realStartTimeUTC() * 1000)
        itv = round(stream.get_dataSamplesInterval() * 1000)
        if tim < itv:
            tim = itv
        nCols = len(dataRows[0])
        minCol = 0
        if nCols > 2:
            avgCol = 1
        else:
            avgCol = 0
        if nCols > 2:
            maxCol = 2
        else:
            maxCol = 0

        for ii_1 in dataRows:
            end_ = tim + itv
            if (end_ > self._startTimeMs) and ((self._endTimeMs == 0) or (tim < self._endTimeMs)):
                measures.append(YMeasure(tim / 1000.0, end_ / 1000.0, ii_1[minCol], ii_1[avgCol], ii_1[maxCol]))
            tim = end_

        return measures

    def get_measures(self) -> list[YMeasure]:
        """
        Returns all measured values currently available for this DataSet,
        as a list of YMeasure objects. Each item includes:
        - the start of the measure time interval
        - the end of the measure time interval
        - the minimal value observed during the time interval
        - the average value observed during the time interval
        - the maximal value observed during the time interval

        Before calling this method, you should call loadMore()
        to load data from the device. You may have to call loadMore()
        several time until all rows are loaded, but you can start
        looking at available data rows before the load is complete.

        The oldest measures are always loaded first, and the most
        recent measures will be loaded last. As a result, timestamps
        are normally sorted in ascending order within the measure table,
        unless there was an unexpected adjustment of the datalogger UTC
        clock.

        @return a table of records, where each record depicts the
                measured value for a given time interval

        On failure, throws an exception or returns an empty array.
        """
        return self._measures

    # --- (end of generated code: YDataSet implementation)

# --- (generated code: YDataLogger class start)
if not _IS_MICROPYTHON:
    # For CPython, use strongly typed callback types
    try:
        YDataLoggerValueCallback = Union[Callable[['YDataLogger', str], Any], None]
    except TypeError:
        YDataLoggerValueCallback = Union[Callable, Awaitable]

# noinspection PyProtectedMember
class YDataLogger(YFunction):
    """
    A non-volatile memory for storing ongoing measured data is available on most Yoctopuce
    sensors. Recording can happen automatically, without requiring a permanent
    connection to a computer.
    The YDataLogger class controls the global parameters of the internal data
    logger. Recording control (start/stop) as well as data retrieval is done at
    sensor objects level.

    """
    # --- (end of generated code: YDataLogger class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YDataLogger return codes)
        CURRENTRUNINDEX_INVALID: Final[int] = YAPI.INVALID_UINT
        TIMEUTC_INVALID: Final[int] = YAPI.INVALID_LONG
        USAGE_INVALID: Final[int] = YAPI.INVALID_UINT
        RECORDING_OFF: Final[int] = 0
        RECORDING_ON: Final[int] = 1
        RECORDING_PENDING: Final[int] = 2
        RECORDING_INVALID: Final[int] = -1
        AUTOSTART_OFF: Final[int] = 0
        AUTOSTART_ON: Final[int] = 1
        AUTOSTART_INVALID: Final[int] = -1
        BEACONDRIVEN_OFF: Final[int] = 0
        BEACONDRIVEN_ON: Final[int] = 1
        BEACONDRIVEN_INVALID: Final[int] = -1
        CLEARHISTORY_FALSE: Final[int] = 0
        CLEARHISTORY_TRUE: Final[int] = 1
        CLEARHISTORY_INVALID: Final[int] = -1
        # --- (end of generated code: YDataLogger return codes)

    # --- (generated code: YDataLogger attributes declaration)
    _valueCallback: YDataLoggerValueCallback
    # --- (end of generated code: YDataLogger attributes declaration)

    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, "DataLogger", func)
        # --- (generated code: YDataLogger constructor)
        # --- (end of generated code: YDataLogger constructor)

    # --- (generated code: YDataLogger implementation)
    @classmethod
    def FindDataLogger(cls, func: str) -> YDataLogger:
        """
        Retrieves a data logger for a given identifier.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the data logger is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDataLogger.isOnline() to test if the data logger is
        indeed online at a given time. In case of ambiguity when looking for
        a data logger by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        If a call to this object's is_online() method returns FALSE although
        you are certain that the matching device is plugged, make sure that you did
        call registerHub() at application initialization time.

        @param func : a string that uniquely characterizes the data logger, for instance
                LIGHTMK4.dataLogger.

        @return a YDataLogger object allowing you to drive the data logger.
        """
        return cls.FindDataLoggerInContext(YAPI, func)

    @classmethod
    def FindDataLoggerInContext(cls, yctx: YAPIContext, func: str) -> YDataLogger:
        """
        Retrieves a data logger for a given identifier in a YAPI context.
        The identifier can be specified using several formats:

        - FunctionLogicalName
        - ModuleSerialNumber.FunctionIdentifier
        - ModuleSerialNumber.FunctionLogicalName
        - ModuleLogicalName.FunctionIdentifier
        - ModuleLogicalName.FunctionLogicalName


        This function does not require that the data logger is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YDataLogger.isOnline() to test if the data logger is
        indeed online at a given time. In case of ambiguity when looking for
        a data logger by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.

        @param yctx : a YAPI context
        @param func : a string that uniquely characterizes the data logger, for instance
                LIGHTMK4.dataLogger.

        @return a YDataLogger object allowing you to drive the data logger.
        """
        obj: Union[YDataLogger, None] = yctx._findInCache('DataLogger', func)
        if obj:
            return obj
        return YDataLogger(yctx, func)

    @classmethod
    def FirstDataLogger(cls) -> Union[YDataLogger, None]:
        """
        Starts the enumeration of data loggers currently accessible.
        Use the method YDataLogger.nextDataLogger() to iterate on
        next data loggers.

        @return a pointer to a YDataLogger object, corresponding to
                the first data logger currently online, or a None pointer
                if there are none.
        """
        return cls.FirstDataLoggerInContext(YAPI)

    @classmethod
    def FirstDataLoggerInContext(cls, yctx: YAPIContext) -> Union[YDataLogger, None]:
        """
        Starts the enumeration of data loggers currently accessible.
        Use the method YDataLogger.nextDataLogger() to iterate on
        next data loggers.

        @param yctx : a YAPI context.

        @return a pointer to a YDataLogger object, corresponding to
                the first data logger currently online, or a None pointer
                if there are none.
        """
        hwid: Union[HwId, None] = yctx._firstHwId('DataLogger')
        if hwid:
            return cls.FindDataLoggerInContext(yctx, hwid2str(hwid))
        return None

    def nextDataLogger(self) -> Union[YDataLogger, None]:
        """
        Continues the enumeration of data loggers started using yFirstDataLogger().
        Caution: You can't make any assumption about the returned data loggers order.
        If you want to find a specific a data logger, use DataLogger.findDataLogger()
        and a hardwareID or a logical name.

        @return a pointer to a YDataLogger object, corresponding to
                a data logger currently online, or a None pointer
                if there are no more data loggers to enumerate.
        """
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('DataLogger', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindDataLoggerInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_currentRunIndex(self) -> int:
        """
        Returns the current run number, corresponding to the number of times the module was
        powered on with the dataLogger enabled at some point.

        @return an integer corresponding to the current run number, corresponding to the number of times the module was
                powered on with the dataLogger enabled at some point

        On failure, throws an exception or returns YDataLogger.CURRENTRUNINDEX_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("currentRunIndex")
        if json_val is None:
            return YDataLogger.CURRENTRUNINDEX_INVALID
        return json_val

    async def get_timeUTC(self) -> int:
        """
        Returns the Unix timestamp for current UTC time, if known.

        @return an integer corresponding to the Unix timestamp for current UTC time, if known

        On failure, throws an exception or returns YDataLogger.TIMEUTC_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("timeUTC")
        if json_val is None:
            return YDataLogger.TIMEUTC_INVALID
        return json_val

    async def set_timeUTC(self, newval: int) -> int:
        """
        Changes the current UTC time reference used for recorded data.

        @param newval : an integer corresponding to the current UTC time reference used for recorded data

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("timeUTC", rest_val)

    async def get_recording(self) -> int:
        """
        Returns the current activation state of the data logger.

        @return a value among YDataLogger.RECORDING_OFF, YDataLogger.RECORDING_ON and
        YDataLogger.RECORDING_PENDING corresponding to the current activation state of the data logger

        On failure, throws an exception or returns YDataLogger.RECORDING_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("recording")
        if json_val is None:
            return YDataLogger.RECORDING_INVALID
        return json_val

    async def set_recording(self, newval: int) -> int:
        """
        Changes the activation state of the data logger to start/stop recording data.

        @param newval : a value among YDataLogger.RECORDING_OFF, YDataLogger.RECORDING_ON and
        YDataLogger.RECORDING_PENDING corresponding to the activation state of the data logger to
        start/stop recording data

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("recording", rest_val)

    async def get_autoStart(self) -> int:
        """
        Returns the default activation state of the data logger on power up.

        @return either YDataLogger.AUTOSTART_OFF or YDataLogger.AUTOSTART_ON, according to the default
        activation state of the data logger on power up

        On failure, throws an exception or returns YDataLogger.AUTOSTART_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("autoStart")
        if json_val is None:
            return YDataLogger.AUTOSTART_INVALID
        return json_val

    async def set_autoStart(self, newval: int) -> int:
        """
        Changes the default activation state of the data logger on power up.
        Do not forget to call the saveToFlash() method of the module to save the
        configuration change.  Note: if the device doesn't have any time source at his disposal when
        starting up, it will wait for ~8 seconds before automatically starting to record  with
        an arbitrary timestamp

        @param newval : either YDataLogger.AUTOSTART_OFF or YDataLogger.AUTOSTART_ON, according to the
        default activation state of the data logger on power up

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("autoStart", rest_val)

    async def get_beaconDriven(self) -> int:
        """
        Returns true if the data logger is synchronised with the localization beacon.

        @return either YDataLogger.BEACONDRIVEN_OFF or YDataLogger.BEACONDRIVEN_ON, according to true if
        the data logger is synchronised with the localization beacon

        On failure, throws an exception or returns YDataLogger.BEACONDRIVEN_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("beaconDriven")
        if json_val is None:
            return YDataLogger.BEACONDRIVEN_INVALID
        return json_val

    async def set_beaconDriven(self, newval: int) -> int:
        """
        Changes the type of synchronisation of the data logger.
        Remember to call the saveToFlash() method of the module if the
        modification must be kept.

        @param newval : either YDataLogger.BEACONDRIVEN_OFF or YDataLogger.BEACONDRIVEN_ON, according to
        the type of synchronisation of the data logger

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("beaconDriven", rest_val)

    async def get_usage(self) -> int:
        """
        Returns the percentage of datalogger memory in use.

        @return an integer corresponding to the percentage of datalogger memory in use

        On failure, throws an exception or returns YDataLogger.USAGE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("usage")
        if json_val is None:
            return YDataLogger.USAGE_INVALID
        return json_val

    async def get_clearHistory(self) -> int:
        json_val: Union[int, None] = await self._fromCache("clearHistory")
        if json_val is None:
            return YDataLogger.CLEARHISTORY_INVALID
        return json_val

    async def set_clearHistory(self, newval: int) -> int:
        rest_val = "1" if newval > 0 else "0"
        return await self._setAttr("clearHistory", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YDataLoggerValueCallback) -> int:
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

    async def forgetAllDataStreams(self) -> int:
        """
        Clears the data logger memory and discards all recorded data streams.
        This method also resets the current run index to zero.

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        return await self.set_clearHistory(YDataLogger.CLEARHISTORY_TRUE)

    # --- (end of generated code: YDataLogger implementation)


if not _IS_MICROPYTHON:
    #################################################################################
    #                                                                               #
    #                            SSDP support                                       #
    #                                                                               #
    #################################################################################
    import socket
    import struct
    YSSDP_MCAST_ADDR: Final[str] = "239.255.255.250"
    YSSDP_PORT: Final[int] = 1900
    YSSDP_URN_YOCTOPUCE: Final[str] = "urn:yoctopuce-com:device:hub:1"
    YSSDP_DISCOVER_MSG: Final[bytes] = b"M-SEARCH * HTTP/1.1\r\nHOST:239.255.255.250:1900\r\nMAN:\"ssdp:discover\"\r\nMX:5\r\nST:urn:yoctopuce-com:device:hub:1\r\n\r\n"

    class YSSDPServerProtocol(asyncio.DatagramProtocol):
        def __init__(self, ssdp: YSSDP):
            self.transport = None
            self.ssdp = ssdp

        def connection_made(self, transport):
            self.transport = transport

        def datagram_received(self, data: bytes, addr):
            self.ssdp.ySSDPParseMessage(data.decode())

    # noinspection PyUnusedLocal
    # noinspection PyRedeclaration
    # noinspection PyProtectedMember
    class YSSDP:
        _yapi: YAPIContext
        _started: bool
        _callback: Union[Callable[[str, Union[str, None], Union[str, None]], None], None]
        _SSDPCache: dict[str, dict]
        _search_transport: Union[any, None]
        _server_transport: Union[any, None]

        def __init__(self, yctx: YAPIContext) -> None:
            self._yapi = yctx
            self._started = False
            self._callback = None
            self._SSDPCache = {}
            self._search_transport = None
            self._server_transport = None

        async def start(self, callback: Union[Callable[[str, Union[str, None], Union[str, None]], None], None]):
            if self._started:
                await self.ySSDPDiscover()
                return YAPI.SUCCESS
            self._callback = callback
            await self.ySSDPOpenSockets()
            self._started = True
            await self.ySSDPDiscover()
            await self.ySSDPCheckExpiration()
            return YAPI.SUCCESS

        async def stop(self) -> None:
            self._started = False
            if self._search_transport is not None:
                self._search_transport.close()
                self._search_transport = None
            if self._server_transport is not None:
                self._server_transport.close()
                self._server_transport = None
            for uuid in self._SSDPCache:
                p: dict = self._SSDPCache[uuid]
                if p is not None:
                    if p.maxAge > 0:
                        await self._yapi.UnregisterHub(p['url'])
                        p.maxAge = 0
                        await self._invokeCallback(p['serial'], None, p['url'])
            self._SSDPCache = {}

        def reset(self) -> None:
            self._started = False
            self._callback = None
            self._SSDPCache = {}
            self._search_transport = None
            self._server_transport = None

        async def _invokeCallback(self, str_serial: str, str_addUrl: Union[str | None], str_removeUrl: Union[str | None]):
            if self._callback is not None:
                try:
                    retval: Union[Coroutine, None] = self._callback(str_serial, str_addUrl, str_removeUrl)
                    if asyncio.iscoroutine(retval):
                        await retval
                except Exception as exc:
                    self._yapi._logCbError(_EVENT_SSDP_CB, self, exc)

        async def ySSDPOpenSockets(self):
            loop = asyncio.get_running_loop()
            local_ip = socket.gethostbyname(socket.gethostname())
            # fixme: check if we need to bind all network interface interfaces
            # open client socket to broadcast search
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
            optval = 1
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, optval)
            if 'SO_REUSEPORT' in vars(socket):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, optval)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setblocking(False)
            sock.bind((local_ip, 0))
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: YSSDPServerProtocol(self),
                sock=sock)
            self._search_transport = transport
            # open sever socket to listen broadcasts
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
            optval = 1
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, optval)
            if 'SO_REUSEPORT' in vars(socket):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, optval)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setblocking(False)
            sock.bind((local_ip, 1900))
            mreq = struct.pack('4s4s', socket.inet_aton(YSSDP_MCAST_ADDR), socket.inet_aton(local_ip))
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            server, protocol = await loop.create_datagram_endpoint(
                lambda: YSSDPServerProtocol(self),
                sock=sock
            )
            self._server_transport = server

        async def ySSDPDiscover(self):
            if self._search_transport is None:
                return
            for rep in range(3):
                duration: int = 10 << rep
                if _IS_MICROPYTHON:
                    await asyncio.sleep_ms(min(duration, 10))  # noqa
                else:
                    await asyncio.sleep(min(duration, 10) / 1000.0)
                self._search_transport.sendto(YSSDP_DISCOVER_MSG, (YSSDP_MCAST_ADDR, YSSDP_PORT))

        async def ySSDPCheckExpiration(self):
            now: int = self._yapi.GetTickCount()
            for uuid in self._SSDPCache:
                entry: dict = self._SSDPCache[uuid]
                if now - entry['detectedTime'] > entry['maxAge']:
                    # has expired
                    if self._callback is not None:
                        self._callback(entry['serial'], None, entry['url'])

        def ySSDPParseMessage(self, msg: str) -> None:

            SSDP_HTTP: str = "HTTP/1.1 200 OK"
            SSDP_NOTIFY: str = "NOTIFY * HTTP/1.1"
            location: str = ''
            usn: str = ''
            cache: str = ''

            lines: list[str] = msg.splitlines(keepends=False)
            # values: _YY_SSDPValues = {}
            if lines[0] != SSDP_HTTP and lines[0] != SSDP_NOTIFY:
                return
            for line in lines:
                parts: list[str] = line.split(': ')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key == 'LOCATION':
                        location = value
                    elif key == 'USN':
                        usn = value
                    elif key == 'CACHE-CONTROL':
                        cache = value
            if location != '' and usn != '' and cache != '':
                # parse USN
                posuuid: int = usn.find(':')
                if posuuid < 0:
                    return
                posuuid += 1
                posurn = usn.find("::", posuuid)
                if posurn < 0:
                    return
                uuid: str = usn[posuuid: posurn].strip()
                urn: str = usn[posurn + 2:].strip()
                if urn != YSSDP_URN_YOCTOPUCE:
                    return
                # parse Location
                if location.startswith("http://"):
                    location = location[7:]

                posslash: int = location.find('/')
                if posslash > 0:
                    location = location[0:posslash]
                poscache: int = cache.find('=')
                if poscache < 0:
                    return
                cache = cache[poscache + 1:].strip()
                self.ySSDPUpdateCache(uuid, location, int(cache))

        @staticmethod
        def convert_uuid_to_serial(uuid: str):
            serial = []
            j = 0
            for i in range(4):
                ch = uuid[j:j + 2]
                serial.append(chr(int(ch, 16)))
                j += 2

            j += 1
            for i in range(4, 6):
                ch = uuid[j:j + 2]
                serial.append(chr(int(ch, 16)))
                j += 2

            j += 1
            for i in range(6, 8):
                ch = uuid[j:j + 2]
                serial.append(chr(int(ch, 16)))
                j += 2

            serial.append('-')
            i = uuid.index("-COFF-EE")
            i += 8
            while uuid[i] == '0':
                i += 1
            num_part = uuid[i:]
            while len(num_part) < 5:
                serial.append('0')
            serial.append(num_part)
            m_serial = ''.join(serial)
            return m_serial

        def ySSDPUpdateCache(self, uuid: str, url: str, cacheValidity: int):
            if cacheValidity <= 0:
                cacheValidity = 1800
            cacheValidity *= 1000
            # print("SSDP: update %s (%s) with %d" % (uuid, url, cacheValidity))
            if uuid in self._SSDPCache:
                entry: dict = self._SSDPCache[uuid]
                if entry['url'] != url:
                    if self._callback is not None:
                        self._callback(entry['serial'], url, entry['url'])
                    entry['url'] = url
                else:
                    now = YAPI.GetTickCount()
                    if now - entry['detectedTime'] > entry['maxAge']:
                        # has expired
                        if self._callback is not None:
                            self._callback(entry['serial'], url, None)
                tick_count = YAPI.GetTickCount()
                entry['detectedTime'] = tick_count
                entry['maxAge'] = cacheValidity
                return
            serial: str = self.convert_uuid_to_serial(uuid)
            entry: dict = {'serial': serial, 'url': url, 'detectedTime': YAPI.GetTickCount(), 'maxAge': cacheValidity}
            self._SSDPCache[uuid] = entry
            if self._callback is not None:
                self._callback(entry['serial'], url, None)
