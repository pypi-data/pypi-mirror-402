# -*- coding: utf-8 -*-
# ********************************************************************
#
#  $Id: yocto_messagebox_aio.py 69442 2025-10-16 08:53:14Z mvuilleu $
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
Yoctopuce library: Asyncio implementation of YMessageBox
version: PATCH_WITH_VERSION
requires: yocto_api_aio
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

# --- (generated code: YSms class start)
# noinspection PyProtectedMember
class YSms:
    """
    YSms objects are used to describe an SMS message, received or to be sent.
    These objects are used in particular in conjunction with the YMessageBox class.

    """
    # --- (end of generated code: YSms class start)
    if not _IS_MICROPYTHON:
        # --- (generated code: YSms return codes)
        pass
        # --- (end of generated code: YSms return codes)
        pass


    # --- (generated code: YSms attributes declaration)
    _mbox: YMessageBox
    _slot: int
    _deliv: bool
    _smsc: str
    _mref: int
    _orig: str
    _dest: str
    _pid: int
    _alphab: int
    _mclass: int
    _stamp: str
    _udh: xarray
    _udata: xarray
    _npdu: int
    _pdu: xarray
    _parts: list[YSms]
    _aggSig: str
    _aggIdx: int
    _aggCnt: int
    # --- (end of generated code: YSms attributes declaration)


    def __init__(self, obj_mbox: YMessageBox):
        # --- (generated code: YSms constructor)
        self._slot = 0
        self._deliv = False
        self._smsc = ""
        self._mref = 0
        self._orig = ""
        self._dest = ""
        self._pid = 0
        self._alphab = 0
        self._mclass = 0
        self._stamp = ""
        self._udh = xbytearray(0)
        self._udata = xbytearray(0)
        self._npdu = 0
        self._pdu = xbytearray(0)
        self._parts = []
        self._aggSig = ""
        self._aggIdx = 0
        self._aggCnt = 0
        # --- (end of generated code: YSms constructor)
        self._mbox = obj_mbox

    # --- (generated code: YSms implementation)
    async def get_slot(self) -> int:
        return self._slot

    async def get_smsc(self) -> str:
        return self._smsc

    async def get_msgRef(self) -> int:
        return self._mref

    async def get_sender(self) -> str:
        return self._orig

    async def get_recipient(self) -> str:
        return self._dest

    async def get_protocolId(self) -> int:
        return self._pid

    async def isReceived(self) -> bool:
        return self._deliv

    async def get_alphabet(self) -> int:
        return self._alphab

    async def get_msgClass(self) -> int:
        if (self._mclass & 16) == 0:
            return -1
        return (self._mclass & 3)

    async def get_dcs(self) -> int:
        return (self._mclass | ((self._alphab << 2)))

    async def get_timestamp(self) -> str:
        return self._stamp

    async def get_userDataHeader(self) -> xarray:
        return self._udh

    def get_userData(self) -> xarray:
        return self._udata

    async def get_textData(self) -> str:
        """
        Returns the content of the message.

        @return  a string with the content of the message.
        """
        isolatin: xarray
        isosize: int
        i: int
        if self._alphab == 0:
            # using GSM standard 7-bit alphabet
            return await self._mbox.gsm2str(self._udata)
        if self._alphab == 2:
            # using UCS-2 alphabet
            isosize = (len(self._udata) >> 1)
            isolatin = xbytearray(isosize)
            i = 0
            while i < isosize:
                isolatin[i] = self._udata[2*i+1]
                i = i + 1
            return isolatin.decode('latin-1')
        # default: convert 8 bit to string as-is
        return self._udata.decode('latin-1')

    async def get_unicodeData(self) -> list[int]:
        res: list[int] = []
        unisize: int
        unival: int
        i: int
        if self._alphab == 0:
            # using GSM standard 7-bit alphabet
            return await self._mbox.gsm2unicode(self._udata)
        if self._alphab == 2:
            # using UCS-2 alphabet
            unisize = (len(self._udata) >> 1)
            del res[:]
            i = 0
            while i < unisize:
                unival = 256*self._udata[2*i]+self._udata[2*i+1]
                res.append(unival)
                i = i + 1
        else:
            # return straight 8-bit values
            unisize = len(self._udata)
            del res[:]
            i = 0
            while i < unisize:
                res.append(self._udata[i]+0)
                i = i + 1

        return res

    async def get_partCount(self) -> int:
        if self._npdu == 0:
            await self.generatePdu()
        return self._npdu

    async def get_pdu(self) -> xarray:
        if self._npdu == 0:
            await self.generatePdu()
        return self._pdu

    async def get_parts(self) -> list[YSms]:
        if self._npdu == 0:
            await self.generatePdu()
        return self._parts

    async def get_concatSignature(self) -> str:
        if self._npdu == 0:
            await self.generatePdu()
        return self._aggSig

    async def get_concatIndex(self) -> int:
        if self._npdu == 0:
            await self.generatePdu()
        return self._aggIdx

    async def get_concatCount(self) -> int:
        if self._npdu == 0:
            await self.generatePdu()
        return self._aggCnt

    async def set_slot(self, val: int) -> int:
        self._slot = val
        return YAPI.SUCCESS

    async def set_received(self, val: bool) -> int:
        self._deliv = val
        return YAPI.SUCCESS

    async def set_smsc(self, val: str) -> int:
        self._smsc = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_msgRef(self, val: int) -> int:
        self._mref = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_sender(self, val: str) -> int:
        self._orig = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_recipient(self, val: str) -> int:
        self._dest = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_protocolId(self, val: int) -> int:
        self._pid = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_alphabet(self, val: int) -> int:
        self._alphab = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_msgClass(self, val: int) -> int:
        if val == -1:
            self._mclass = 0
        else:
            self._mclass = 16+val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_dcs(self, val: int) -> int:
        self._alphab = (((val >> 2)) & 3)
        self._mclass = (val & (16+3))
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_timestamp(self, val: str) -> int:
        self._stamp = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def set_userDataHeader(self, val: xarray) -> int:
        self._udh = val
        self._npdu = 0
        await self.parseUserDataHeader()
        return YAPI.SUCCESS

    def set_userData(self, val: xarray) -> int:
        self._udata = val
        self._npdu = 0
        return YAPI.SUCCESS

    async def convertToUnicode(self) -> int:
        ucs2: list[int] = []
        udatalen: int
        i: int
        uni: int
        if self._alphab == 2:
            return YAPI.SUCCESS
        if self._alphab == 0:
            ucs2 = await self._mbox.gsm2unicode(self._udata)
        else:
            udatalen = len(self._udata)
            del ucs2[:]
            i = 0
            while i < udatalen:
                uni = self._udata[i]
                ucs2.append(uni)
                i = i + 1
        self._alphab = 2
        self._udata = xbytearray(0)
        await self.addUnicodeData(ucs2)
        return YAPI.SUCCESS

    async def addText(self, val: str) -> int:
        """
        Add a regular text to the SMS. This function support messages
        of more than 160 characters. ISO-latin accented characters
        are supported. For messages with special unicode characters such as asian
        characters and emoticons, use the  addUnicodeData method.

        @param val : the text to be sent in the message

        @return YAPI.SUCCESS when the call succeeds.
        """
        udata: xarray
        udatalen: int
        newdata: xarray
        newdatalen: int
        i: int
        if len(val) == 0:
            return YAPI.SUCCESS
        if self._alphab == 0:
            # Try to append using GSM 7-bit alphabet
            newdata = await self._mbox.str2gsm(val)
            newdatalen = len(newdata)
            if newdatalen == 0:
                # 7-bit not possible, switch to unicode
                await self.convertToUnicode()
                newdata = xbytearray(val, 'latin-1')
                newdatalen = len(newdata)
        else:
            newdata = xbytearray(val, 'latin-1')
            newdatalen = len(newdata)
        udatalen = len(self._udata)
        if self._alphab == 2:
            # Append in unicode directly
            udata = xbytearray(udatalen + 2*newdatalen)
            i = 0
            while i < udatalen:
                udata[i] = self._udata[i]
                i = i + 1
            i = 0
            while i < newdatalen:
                udata[udatalen+1] = newdata[i]
                udatalen = udatalen + 2
                i = i + 1
        else:
            # Append binary buffers
            udata = xbytearray(udatalen+newdatalen)
            i = 0
            while i < udatalen:
                udata[i] = self._udata[i]
                i = i + 1
            i = 0
            while i < newdatalen:
                udata[udatalen] = newdata[i]
                udatalen = udatalen + 1
                i = i + 1
        return self.set_userData(udata)

    async def addUnicodeData(self, val: list[int]) -> int:
        """
        Add a unicode text to the SMS. This function support messages
        of more than 160 characters, using SMS concatenation.

        @param val : an array of special unicode characters

        @return YAPI.SUCCESS when the call succeeds.
        """
        arrlen: int
        newdatalen: int
        i: int
        uni: int
        udata: xarray
        udatalen: int
        surrogate: int
        if self._alphab != 2:
            await self.convertToUnicode()
        # compute number of 16-bit code units
        arrlen = len(val)
        newdatalen = arrlen
        i = 0
        while i < arrlen:
            uni = val[i]
            if uni > 65535:
                newdatalen = newdatalen + 1
            i = i + 1
        # now build utf-16 buffer
        udatalen = len(self._udata)
        udata = xbytearray(udatalen+2*newdatalen)
        i = 0
        while i < udatalen:
            udata[i] = self._udata[i]
            i = i + 1
        i = 0
        while i < arrlen:
            uni = val[i]
            if uni >= 65536:
                surrogate = uni - 65536
                uni = (((surrogate >> 10) & 1023)) + 55296
                udata[udatalen] = (uni >> 8)
                udata[udatalen+1] = (uni & 255)
                udatalen = udatalen + 2
                uni = ((surrogate & 1023)) + 56320
            udata[udatalen] = (uni >> 8)
            udata[udatalen+1] = (uni & 255)
            udatalen = udatalen + 2
            i = i + 1
        return self.set_userData(udata)

    async def set_pdu(self, pdu: xarray) -> int:
        self._pdu = pdu
        self._npdu = 1
        return await self.parsePdu(pdu)

    async def set_parts(self, parts: list[YSms]) -> int:
        sorted: Union[list[YSms], None] = []
        partno: int
        initpartno: int
        i: int
        retcode: int
        totsize: int
        subsms: Union[YSms, None]
        subdata: xarray
        res: xarray
        self._npdu = len(parts)
        if self._npdu == 0:
            return YAPI.INVALID_ARGUMENT
        del sorted[:]
        partno = 0
        while partno < self._npdu:
            initpartno = partno
            i = 0
            while i < self._npdu:
                subsms = parts[i]
                if await subsms.get_concatIndex() == partno:
                    sorted.append(subsms)
                    partno = partno + 1
                i = i + 1
            if initpartno == partno:
                partno = partno + 1

        self._parts = sorted
        # inherit header fields from first part
        subsms = self._parts[0]
        retcode = await self.parsePdu(await subsms.get_pdu())
        if retcode != YAPI.SUCCESS:
            return retcode
        self._npdu = len(sorted)
        # concatenate user data from all parts
        totsize = 0
        partno = 0
        while partno < len(self._parts):
            subsms = self._parts[partno]
            subdata = subsms.get_userData()
            totsize = totsize + len(subdata)
            partno = partno + 1
        res = xbytearray(totsize)
        totsize = 0
        partno = 0
        while partno < len(self._parts):
            subsms = self._parts[partno]
            subdata = subsms.get_userData()
            i = 0
            while i < len(subdata):
                res[totsize] = subdata[i]
                totsize = totsize + 1
                i = i + 1
            partno = partno + 1
        self._udata = res
        return YAPI.SUCCESS

    async def encodeAddress(self, addr: str) -> xarray:
        bytes: xarray
        srclen: int
        numlen: int
        i: int
        val: int
        digit: int
        res: xarray
        bytes = xbytearray(addr, 'latin-1')
        srclen = len(bytes)
        numlen = 0
        i = 0
        while i < srclen:
            val = bytes[i]
            if (val >= 48) and (val < 58):
                numlen = numlen + 1
            i = i + 1
        if numlen == 0:
            res = xbytearray(1)
            res[0] = 0
            return res
        res = xbytearray(2+((numlen+1) >> 1))
        res[0] = numlen
        if bytes[0] == 43:
            res[1] = 145
        else:
            res[1] = 129
        numlen = 4
        digit = 0
        i = 0
        while i < srclen:
            val = bytes[i]
            if (val >= 48) and (val < 58):
                if (numlen & 1) == 0:
                    digit = val - 48
                else:
                    res[(numlen >> 1)] = digit + 16*(val-48)
                numlen = numlen + 1
            i = i + 1
        # pad with F if needed
        if (numlen & 1) != 0:
            res[(numlen >> 1)] = digit + 240
        return res

    async def decodeAddress(self, addr: xarray, ofs: int, siz: int) -> str:
        addrType: int
        gsm7: xarray
        res: str
        i: int
        rpos: int
        carry: int
        nbits: int
        byt: int
        if siz == 0:
            return ""
        res = ""
        addrType = (addr[ofs] & 112)
        if addrType == 80:
            # alphanumeric number
            siz = (4*siz) // 7
            gsm7 = xbytearray(siz)
            rpos = 1
            carry = 0
            nbits = 0
            i = 0
            while i < siz:
                if nbits == 7:
                    gsm7[i] = carry
                    carry = 0
                    nbits = 0
                else:
                    byt = addr[ofs+rpos]
                    rpos = rpos + 1
                    gsm7[i] = (carry | (((byt << nbits)) & 127))
                    carry = (byt >> (7 - nbits))
                    nbits = nbits + 1
                i = i + 1
            return await self._mbox.gsm2str(gsm7)
        else:
            # standard phone number
            if addrType == 16:
                res = "+"
            siz = ((siz+1) >> 1)
            i = 0
            while i < siz:
                byt = addr[ofs+i+1]
                res = "%s%x%x" % (res, (byt & 15), (byt >> 4))
                i = i + 1
            # remove padding digit if needed
            if ((addr[ofs+siz]) >> 4) == 15:
                res = res[0: 0 + len(res)-1]
            return res

    async def encodeTimeStamp(self, exp: str) -> xarray:
        explen: int
        i: int
        res: xarray
        n: int
        expasc: xarray
        v1: int
        v2: int
        explen = len(exp)
        if explen == 0:
            res = xbytearray(0)
            return res
        if exp[0: 0 + 1] == "+":
            n = YAPI._atoi(exp[1: 1 + explen-1])
            res = xbytearray(1)
            if n > 30*86400:
                n = 192+(n+6*86400) // (7*86400)
            else:
                if n > 86400:
                    n = 166+(n+86399) // 86400
                else:
                    if n > 43200:
                        n = 143+(n-43200+1799) // 1800
                    else:
                        n = -1+(n+299) // 300
            if n < 0:
                n = 0
            res[0] = n
            return res
        if exp[4: 4 + 1] == "-" or exp[4: 4 + 1] == "/":
            # ignore century
            exp = exp[2: 2 + explen-2]
            explen = len(exp)
        expasc = xbytearray(exp, 'latin-1')
        res = xbytearray(7)
        n = 0
        i = 0
        while (i+1 < explen) and(n < 7):
            v1 = expasc[i]
            if (v1 >= 48) and (v1 < 58):
                v2 = expasc[i+1]
                if (v2 >= 48) and (v2 < 58):
                    v1 = v1 - 48
                    v2 = v2 - 48
                    res[n] = ((v2 << 4)) + v1
                    n = n + 1
                    i = i + 1
            i = i + 1
        while n < 7:
            res[n] = 0
            n = n + 1
        if i+2 < explen:
            # convert for timezone in cleartext ISO format +/-nn:nn
            v1 = expasc[i-3]
            v2 = expasc[i]
            if ((v1 == 43) or (v1 == 45)) and (v2 == 58):
                v1 = expasc[i+1]
                v2 = expasc[i+2]
                if (v1 >= 48) and (v1 < 58) and (v1 >= 48) and (v1 < 58):
                    v1 = (10*(v1 - 48)+(v2 - 48)) // 15
                    n = n - 1
                    v2 = 4 * res[n] + v1
                    if expasc[i-3] == 45:
                        v2 = v2 + 128
                    res[n] = v2
        return res

    async def decodeTimeStamp(self, exp: xarray, ofs: int, siz: int) -> str:
        n: int
        res: str
        i: int
        byt: int
        sign: str
        hh: str
        ss: str
        if siz < 1:
            return ""
        if siz == 1:
            n = exp[ofs]
            if n < 144:
                n = n * 300
            else:
                if n < 168:
                    n = (n-143) * 1800
                else:
                    if n < 197:
                        n = (n-166) * 86400
                    else:
                        n = (n-192) * 7 * 86400
            return "+%d" % n
        res = "20"
        i = 0
        while (i < siz) and(i < 6):
            byt = exp[ofs+i]
            res = "%s%x%x" % (res, (byt & 15), (byt >> 4))
            if i < 3:
                if i < 2:
                    res = "%s-" % res
                else:
                    res = "%s " % res
            else:
                if i < 5:
                    res = "%s:" % res
            i = i + 1
        if siz == 7:
            byt = exp[ofs+i]
            sign = "+"
            if (byt & 8) != 0:
                byt = byt - 8
                sign = "-"
            byt = (10*((byt & 15))) + ((byt >> 4))
            hh = "%d" % (byt >> 2)
            ss = "%d" % (15*((byt & 3)))
            if len(hh)<2:
                hh = "0%s" % hh
            if len(ss)<2:
                ss = "0%s" % ss
            res = "%s%s%s:%s" % (res, sign, hh, ss)
        return res

    async def udataSize(self) -> int:
        res: int
        udhsize: int
        udhsize = len(self._udh)
        res = len(self._udata)
        if self._alphab == 0:
            if udhsize > 0:
                res = res + (8 + 8*udhsize + 6) // 7
            res = (res * 7 + 7) // 8
        else:
            if udhsize > 0:
                res = res + 1 + udhsize
        return res

    async def encodeUserData(self) -> xarray:
        udsize: int
        udlen: int
        udhsize: int
        udhlen: int
        res: xarray
        i: int
        wpos: int
        carry: int
        nbits: int
        thi_b: int
        # nbits = number of bits in carry
        udsize = await self.udataSize()
        udhsize = len(self._udh)
        udlen = len(self._udata)
        res = xbytearray(1+udsize)
        udhlen = 0
        nbits = 0
        carry = 0
        # 1. Encode UDL
        if self._alphab == 0:
            # 7-bit encoding
            if udhsize > 0:
                udhlen = (8 + 8*udhsize + 6) // 7
                nbits = 7*udhlen - 8 - 8*udhsize
            res[0] = udhlen+udlen
        else:
            # 8-bit encoding
            res[0] = udsize
        # 2. Encode UDHL and UDL
        wpos = 1
        if udhsize > 0:
            res[wpos] = udhsize
            wpos = wpos + 1
            i = 0
            while i < udhsize:
                res[wpos] = self._udh[i]
                wpos = wpos + 1
                i = i + 1
        # 3. Encode UD
        if self._alphab == 0:
            # 7-bit encoding
            i = 0
            while i < udlen:
                if nbits == 0:
                    carry = self._udata[i]
                    nbits = 7
                else:
                    thi_b = self._udata[i]
                    res[wpos] = (carry | (((thi_b << nbits)) & 255))
                    wpos = wpos + 1
                    nbits = nbits - 1
                    carry = (thi_b >> (7 - nbits))
                i = i + 1
            if nbits > 0:
                res[wpos] = carry
        else:
            # 8-bit encoding
            i = 0
            while i < udlen:
                res[wpos] = self._udata[i]
                wpos = wpos + 1
                i = i + 1
        return res

    async def generateParts(self) -> int:
        udhsize: int
        udlen: int
        mss: int
        partno: int
        partlen: int
        newud: xarray
        newudh: xarray
        newpdu: Union[YSms, None]
        i: int
        wpos: int
        udhsize = len(self._udh)
        udlen = len(self._udata)
        mss = 140 - 1 - 5 - udhsize
        if self._alphab == 0:
            mss = (mss * 8 - 6) // 7
        self._npdu = (udlen+mss-1) // mss
        del self._parts[:]
        partno = 0
        wpos = 0
        while wpos < udlen:
            partno = partno + 1
            newudh = xbytearray(5+udhsize)
            newudh[0] = 0
            # IEI: concatenated message
            newudh[1] = 3
            # IEDL: 3 bytes
            newudh[2] = self._mref
            newudh[3] = self._npdu
            newudh[4] = partno
            i = 0
            while i < udhsize:
                newudh[5+i] = self._udh[i]
                i = i + 1
            if wpos+mss < udlen:
                partlen = mss
            else:
                partlen = udlen-wpos
            newud = xbytearray(partlen)
            i = 0
            while i < partlen:
                newud[i] = self._udata[wpos]
                wpos = wpos + 1
                i = i + 1
            newpdu = YSms(self._mbox)
            await newpdu.set_received(await self.isReceived())
            await newpdu.set_smsc(await self.get_smsc())
            await newpdu.set_msgRef(await self.get_msgRef())
            await newpdu.set_sender(await self.get_sender())
            await newpdu.set_recipient(await self.get_recipient())
            await newpdu.set_protocolId(await self.get_protocolId())
            await newpdu.set_dcs(await self.get_dcs())
            await newpdu.set_timestamp(await self.get_timestamp())
            await newpdu.set_userDataHeader(newudh)
            newpdu.set_userData(newud)
            self._parts.append(newpdu)
        return YAPI.SUCCESS

    async def generatePdu(self) -> int:
        sca: xarray
        hdr: xarray
        addr: xarray
        stamp: xarray
        udata: xarray
        pdutyp: int
        pdulen: int
        i: int
        # Determine if the message can fit within a single PDU
        del self._parts[:]
        if await self.udataSize() > 140:
            # multiple PDU are needed
            self._pdu = xbytearray(0)
            return await self.generateParts()
        sca = await self.encodeAddress(self._smsc)
        if len(sca) > 0:
            sca[0] = len(sca)-1
        stamp = await self.encodeTimeStamp(self._stamp)
        udata = await self.encodeUserData()
        if self._deliv:
            addr = await self.encodeAddress(self._orig)
            hdr = xbytearray(1)
            pdutyp = 0
        else:
            addr = await self.encodeAddress(self._dest)
            self._mref = await self._mbox.nextMsgRef()
            hdr = xbytearray(2)
            hdr[1] = self._mref
            pdutyp = 1
            if len(stamp) > 0:
                pdutyp = pdutyp + 16
            if len(stamp) == 7:
                pdutyp = pdutyp + 8
        if len(self._udh) > 0:
            pdutyp = pdutyp + 64
        hdr[0] = pdutyp
        pdulen = len(sca)+len(hdr)+len(addr)+2+len(stamp)+len(udata)
        self._pdu = xbytearray(pdulen)
        pdulen = 0
        i = 0
        while i < len(sca):
            self._pdu[pdulen] = sca[i]
            pdulen = pdulen + 1
            i = i + 1
        i = 0
        while i < len(hdr):
            self._pdu[pdulen] = hdr[i]
            pdulen = pdulen + 1
            i = i + 1
        i = 0
        while i < len(addr):
            self._pdu[pdulen] = addr[i]
            pdulen = pdulen + 1
            i = i + 1
        self._pdu[pdulen] = self._pid
        pdulen = pdulen + 1
        self._pdu[pdulen] = await self.get_dcs()
        pdulen = pdulen + 1
        i = 0
        while i < len(stamp):
            self._pdu[pdulen] = stamp[i]
            pdulen = pdulen + 1
            i = i + 1
        i = 0
        while i < len(udata):
            self._pdu[pdulen] = udata[i]
            pdulen = pdulen + 1
            i = i + 1
        self._npdu = 1
        return YAPI.SUCCESS

    async def parseUserDataHeader(self) -> int:
        udhlen: int
        i: int
        iei: int
        ielen: int
        sig: str
        self._aggSig = ""
        self._aggIdx = 0
        self._aggCnt = 0
        udhlen = len(self._udh)
        i = 0
        while i+1 < udhlen:
            iei = self._udh[i]
            ielen = self._udh[i+1]
            i = i + 2
            if i + ielen <= udhlen:
                if (iei == 0) and (ielen == 3):
                    # concatenated SMS, 8-bit ref
                    sig = "%s-%s-%02x-%02x" % (self._orig, self._dest, self._mref, self._udh[i])
                    self._aggSig = sig
                    self._aggCnt = self._udh[i+1]
                    self._aggIdx = self._udh[i+2]
                if (iei == 8) and (ielen == 4):
                    # concatenated SMS, 16-bit ref
                    sig = "%s-%s-%02x-%02x%02x" % (self._orig, self._dest, self._mref, self._udh[i], self._udh[i+1])
                    self._aggSig = sig
                    self._aggCnt = self._udh[i+2]
                    self._aggIdx = self._udh[i+3]
            i = i + ielen
        return YAPI.SUCCESS

    async def parsePdu(self, pdu: xarray) -> int:
        rpos: int
        addrlen: int
        pdutyp: int
        tslen: int
        dcs: int
        udlen: int
        udhsize: int
        udhlen: int
        i: int
        carry: int
        nbits: int
        thi_b: int
        self._pdu = pdu
        self._npdu = 1
        # parse meta-data
        self._smsc = await self.decodeAddress(pdu, 1, 2*(pdu[0]-1))
        rpos = 1+pdu[0]
        pdutyp = pdu[rpos]
        rpos = rpos + 1
        self._deliv = ((pdutyp & 3) == 0)
        if self._deliv:
            addrlen = pdu[rpos]
            rpos = rpos + 1
            self._orig = await self.decodeAddress(pdu, rpos, addrlen)
            self._dest = ""
            tslen = 7
        else:
            self._mref = pdu[rpos]
            rpos = rpos + 1
            addrlen = pdu[rpos]
            rpos = rpos + 1
            self._dest = await self.decodeAddress(pdu, rpos, addrlen)
            self._orig = ""
            if ((pdutyp & 16)) != 0:
                if ((pdutyp & 8)) != 0:
                    tslen = 7
                else:
                    tslen= 1
            else:
                tslen = 0
        rpos = rpos + (((addrlen+3) >> 1))
        self._pid = pdu[rpos]
        rpos = rpos + 1
        dcs = pdu[rpos]
        rpos = rpos + 1
        self._alphab = (((dcs >> 2)) & 3)
        self._mclass = (dcs & (16+3))
        self._stamp = await self.decodeTimeStamp(pdu, rpos, tslen)
        rpos = rpos + tslen
        # parse user data (including udh)
        nbits = 0
        carry = 0
        udlen = pdu[rpos]
        rpos = rpos + 1
        if (pdutyp & 64) != 0:
            udhsize = pdu[rpos]
            rpos = rpos + 1
            self._udh = xbytearray(udhsize)
            i = 0
            while i < udhsize:
                self._udh[i] = pdu[rpos]
                rpos = rpos + 1
                i = i + 1
            if self._alphab == 0:
                # 7-bit encoding
                udhlen = (8 + 8*udhsize + 6) // 7
                nbits = 7*udhlen - 8 - 8*udhsize
                if nbits > 0:
                    thi_b = pdu[rpos]
                    rpos = rpos + 1
                    carry = (thi_b >> nbits)
                    nbits = 8 - nbits
            else:
                # byte encoding
                udhlen = 1+udhsize
            udlen = udlen - udhlen
        else:
            udhsize = 0
            self._udh = xbytearray(0)
        self._udata = xbytearray(udlen)
        if self._alphab == 0:
            # 7-bit encoding
            i = 0
            while i < udlen:
                if nbits == 7:
                    self._udata[i] = carry
                    carry = 0
                    nbits = 0
                else:
                    thi_b = pdu[rpos]
                    rpos = rpos + 1
                    self._udata[i] = (carry | (((thi_b << nbits)) & 127))
                    carry = (thi_b >> (7 - nbits))
                    nbits = nbits + 1
                i = i + 1
        else:
            # 8-bit encoding
            i = 0
            while i < udlen:
                self._udata[i] = pdu[rpos]
                rpos = rpos + 1
                i = i + 1
        await self.parseUserDataHeader()
        return YAPI.SUCCESS

    async def send(self) -> int:
        """
        Sends the SMS to the recipient. Messages of more than 160 characters are supported
        using SMS concatenation.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        i: int
        retcode: int
        pdu: Union[YSms, None]

        if self._npdu == 0:
            await self.generatePdu()
        if self._npdu == 1:
            return await self._mbox._upload("sendSMS", self._pdu)
        retcode = YAPI.SUCCESS
        i = 0
        while (i < self._npdu) and(retcode == YAPI.SUCCESS):
            pdu = self._parts[i]
            retcode= await pdu.send()
            i = i + 1
        return retcode

    async def deleteFromSIM(self) -> int:
        i: int
        retcode: int
        pdu: Union[YSms, None]

        if self._npdu < 2:
            return await self._mbox.clearSIMSlot(self._slot)
        retcode = YAPI.SUCCESS
        i = 0
        while (i < self._npdu) and(retcode == YAPI.SUCCESS):
            pdu = self._parts[i]
            retcode= await pdu.deleteFromSIM()
            i = i + 1
        return retcode

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

    # --- (generated code: YMessageBox attributes declaration)
    _valueCallback: YMessageBoxValueCallback
    _nextMsgRef: int
    _prevBitmapStr: str
    _pdus: list[YSms]
    _messages: list[YSms]
    _gsm2unicodeReady: bool
    _gsm2unicode: list[int]
    _iso2gsm: xarray
    # --- (end of generated code: YMessageBox attributes declaration)


    def __init__(self, yctx: YAPIContext, func: str):
        super().__init__(yctx, 'MessageBox', func)
        # --- (generated code: YMessageBox constructor)
        self._nextMsgRef = 0
        self._prevBitmapStr = ""
        self._pdus = []
        self._messages = []
        self._gsm2unicodeReady = False
        self._gsm2unicode = []
        self._iso2gsm = xbytearray(0)
        # --- (end of generated code: YMessageBox constructor)

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
        return cls.FindMessageBoxInContext(YAPI, func)

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
        obj: Union[YMessageBox, None] = yctx._findInCache('MessageBox', func)
        if obj:
            return obj
        return YMessageBox(yctx, func)

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
        return cls.FirstMessageBoxInContext(YAPI)

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
        hwid: Union[HwId, None] = yctx._firstHwId('MessageBox')
        if hwid:
            return cls.FindMessageBoxInContext(yctx, hwid2str(hwid))
        return None

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
        next_hwid: Union[HwId, None] = None
        try:
            next_hwid = self._yapi._nextHwId('MessageBox', self.get_hwId())
        except YAPI_Exception:
            pass
        if next_hwid:
            return self.FindMessageBoxInContext(self._yapi, hwid2str(next_hwid))
        return None

    async def get_slotsInUse(self) -> int:
        """
        Returns the number of message storage slots currently in use.

        @return an integer corresponding to the number of message storage slots currently in use

        On failure, throws an exception or returns YMessageBox.SLOTSINUSE_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("slotsInUse")
        if json_val is None:
            return YMessageBox.SLOTSINUSE_INVALID
        return json_val

    async def get_slotsCount(self) -> int:
        """
        Returns the total number of message storage slots on the SIM card.

        @return an integer corresponding to the total number of message storage slots on the SIM card

        On failure, throws an exception or returns YMessageBox.SLOTSCOUNT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("slotsCount")
        if json_val is None:
            return YMessageBox.SLOTSCOUNT_INVALID
        return json_val

    async def get_slotsBitmap(self) -> str:
        json_val: Union[str, None] = await self._fromCache("slotsBitmap")
        if json_val is None:
            return YMessageBox.SLOTSBITMAP_INVALID
        return json_val

    async def get_pduSent(self) -> int:
        """
        Returns the number of SMS units sent so far.

        @return an integer corresponding to the number of SMS units sent so far

        On failure, throws an exception or returns YMessageBox.PDUSENT_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pduSent")
        if json_val is None:
            return YMessageBox.PDUSENT_INVALID
        return json_val

    async def set_pduSent(self, newval: int) -> int:
        """
        Changes the value of the outgoing SMS units counter.

        @param newval : an integer corresponding to the value of the outgoing SMS units counter

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("pduSent", rest_val)

    async def get_pduReceived(self) -> int:
        """
        Returns the number of SMS units received so far.

        @return an integer corresponding to the number of SMS units received so far

        On failure, throws an exception or returns YMessageBox.PDURECEIVED_INVALID.
        """
        json_val: Union[int, None] = await self._fromCache("pduReceived")
        if json_val is None:
            return YMessageBox.PDURECEIVED_INVALID
        return json_val

    async def set_pduReceived(self, newval: int) -> int:
        """
        Changes the value of the incoming SMS units counter.

        @param newval : an integer corresponding to the value of the incoming SMS units counter

        @return YAPI.SUCCESS if the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(newval)
        return await self._setAttr("pduReceived", rest_val)

    async def get_obey(self) -> str:
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
        json_val: Union[str, None] = await self._fromCache("obey")
        if json_val is None:
            return YMessageBox.OBEY_INVALID
        return json_val

    async def set_obey(self, newval: str) -> int:
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
        rest_val = newval
        return await self._setAttr("obey", rest_val)

    async def get_command(self) -> str:
        json_val: Union[str, None] = await self._fromCache("command")
        if json_val is None:
            return YMessageBox.COMMAND_INVALID
        return json_val

    async def set_command(self, newval: str) -> int:
        rest_val = newval
        return await self._setAttr("command", rest_val)

    if not _IS_MICROPYTHON:
        async def registerValueCallback(self, callback: YMessageBoxValueCallback) -> int:
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

    async def nextMsgRef(self) -> int:
        self._nextMsgRef = self._nextMsgRef + 1
        return self._nextMsgRef

    async def clearSIMSlot(self, slot: int) -> int:
        retry: int
        idx: int
        res: str
        bitmapStr: str
        int_res: int
        newBitmap: xarray
        bitVal: int

        retry = 5
        while retry > 0:
            await self.clearCache()
            bitmapStr = await self.get_slotsBitmap()
            newBitmap = YAPI._hexStrToBin(bitmapStr)
            idx = (slot >> 3)
            if idx < len(newBitmap):
                bitVal = (1 << ((slot & 7)))
                if ((newBitmap[idx] & bitVal)) != 0:
                    self._prevBitmapStr = ""
                    int_res = await self.set_command("DS%d" % slot)
                    if int_res < 0:
                        return int_res
                else:
                    return YAPI.SUCCESS
            else:
                return YAPI.INVALID_ARGUMENT
            res = await self._AT("")
            retry = retry - 1
        return YAPI.IO_ERROR

    async def _AT(self, cmd: str) -> str:
        chrPos: int
        cmdLen: int
        waitMore: int
        res: str
        buff: xarray
        bufflen: int
        buffstr: str
        buffstrlen: int
        idx: int
        suffixlen: int
        # copied form the YCellular class
        # quote dangerous characters used in AT commands
        cmdLen = len(cmd)
        chrPos = cmd.find("#")
        while chrPos >= 0:
            cmd = "%s%c23%s" % (cmd[0: 0 + chrPos], 37, cmd[chrPos+1: chrPos+1 + cmdLen-chrPos-1])
            cmdLen = cmdLen + 2
            chrPos = cmd.find("#")
        chrPos = cmd.find("+")
        while chrPos >= 0:
            cmd = "%s%c2B%s" % (cmd[0: 0 + chrPos], 37, cmd[chrPos+1: chrPos+1 + cmdLen-chrPos-1])
            cmdLen = cmdLen + 2
            chrPos = cmd.find("+")
        chrPos = cmd.find("=")
        while chrPos >= 0:
            cmd = "%s%c3D%s" % (cmd[0: 0 + chrPos], 37, cmd[chrPos+1: chrPos+1 + cmdLen-chrPos-1])
            cmdLen = cmdLen + 2
            chrPos = cmd.find("=")
        cmd = "at.txt?cmd=%s" % cmd
        res = ""
        # max 2 minutes (each iteration may take up to 5 seconds if waiting)
        waitMore = 24
        while waitMore > 0:
            buff = await self._download(cmd)
            bufflen = len(buff)
            buffstr = buff.decode('latin-1')
            buffstrlen = len(buffstr)
            idx = bufflen - 1
            while (idx > 0) and(buff[idx] != 64) and(buff[idx] != 10) and(buff[idx] != 13):
                idx = idx - 1
            if buff[idx] == 64:
                # continuation detected
                suffixlen = bufflen - idx
                cmd = "at.txt?cmd=%s" % (buffstr[buffstrlen - suffixlen: buffstrlen - suffixlen + suffixlen])
                buffstr = buffstr[0: 0 + buffstrlen - suffixlen]
                waitMore = waitMore - 1
            else:
                # request complete
                waitMore = 0
            res = "%s%s" % (res, buffstr)
        return res

    async def fetchPdu(self, slot: int) -> YSms:
        binPdu: xarray
        arrPdu: list[xarray] = []
        hexPdu: str
        sms: Union[YSms, None]

        binPdu = await self._download("sms.json?pos=%d&len=1" % slot)
        arrPdu = self._json_get_array(binPdu)
        hexPdu = self._decode_json_string(arrPdu[0])
        sms = YSms(self)
        await sms.set_slot(slot)
        await sms.parsePdu(YAPI._hexStrToBin(hexPdu))
        return sms

    async def initGsm2Unicode(self) -> int:
        i: int
        uni: int
        del self._gsm2unicode[:]
        # 00-07
        self._gsm2unicode.append(64)
        self._gsm2unicode.append(163)
        self._gsm2unicode.append(36)
        self._gsm2unicode.append(165)
        self._gsm2unicode.append(232)
        self._gsm2unicode.append(233)
        self._gsm2unicode.append(249)
        self._gsm2unicode.append(236)
        # 08-0F
        self._gsm2unicode.append(242)
        self._gsm2unicode.append(199)
        self._gsm2unicode.append(10)
        self._gsm2unicode.append(216)
        self._gsm2unicode.append(248)
        self._gsm2unicode.append(13)
        self._gsm2unicode.append(197)
        self._gsm2unicode.append(229)
        # 10-17
        self._gsm2unicode.append(916)
        self._gsm2unicode.append(95)
        self._gsm2unicode.append(934)
        self._gsm2unicode.append(915)
        self._gsm2unicode.append(923)
        self._gsm2unicode.append(937)
        self._gsm2unicode.append(928)
        self._gsm2unicode.append(936)
        # 18-1F
        self._gsm2unicode.append(931)
        self._gsm2unicode.append(920)
        self._gsm2unicode.append(926)
        self._gsm2unicode.append(27)
        self._gsm2unicode.append(198)
        self._gsm2unicode.append(230)
        self._gsm2unicode.append(223)
        self._gsm2unicode.append(201)
        # 20-7A
        i = 32
        while i <= 122:
            self._gsm2unicode.append(i)
            i = i + 1
        # exceptions in range 20-7A
        self._gsm2unicode[36] = 164
        self._gsm2unicode[64] = 161
        self._gsm2unicode[91] = 196
        self._gsm2unicode[92] = 214
        self._gsm2unicode[93] = 209
        self._gsm2unicode[94] = 220
        self._gsm2unicode[95] = 167
        self._gsm2unicode[96] = 191
        # 7B-7F
        self._gsm2unicode.append(228)
        self._gsm2unicode.append(246)
        self._gsm2unicode.append(241)
        self._gsm2unicode.append(252)
        self._gsm2unicode.append(224)

        # Invert table as well wherever possible
        self._iso2gsm = xbytearray(256)
        i = 0
        while i <= 127:
            uni = self._gsm2unicode[i]
            if uni <= 255:
                self._iso2gsm[uni] = i
            i = i + 1
        i = 0
        while i < 4:
            # mark escape sequences
            self._iso2gsm[91+i] = 27
            self._iso2gsm[123+i] = 27
            i = i + 1
        # Done
        self._gsm2unicodeReady = True
        return YAPI.SUCCESS

    async def gsm2unicode(self, gsm: xarray) -> list[int]:
        i: int
        gsmlen: int
        reslen: int
        res: list[int] = []
        uni: int
        if not self._gsm2unicodeReady:
            await self.initGsm2Unicode()
        gsmlen = len(gsm)
        reslen = gsmlen
        i = 0
        while i < gsmlen:
            if gsm[i] == 27:
                reslen = reslen - 1
            i = i + 1
        del res[:]
        i = 0
        while i < gsmlen:
            uni = self._gsm2unicode[gsm[i]]
            if (uni == 27) and (i+1 < gsmlen):
                i = i + 1
                uni = gsm[i]
                if uni < 60:
                    if uni < 41:
                        if uni==20:
                            uni=94
                        else:
                            if uni==40:
                                uni=123
                            else:
                                uni=0
                    else:
                        if uni==41:
                            uni=125
                        else:
                            if uni==47:
                                uni=92
                            else:
                                uni=0
                else:
                    if uni < 62:
                        if uni==60:
                            uni=91
                        else:
                            if uni==61:
                                uni=126
                            else:
                                uni=0
                    else:
                        if uni==62:
                            uni=93
                        else:
                            if uni==64:
                                uni=124
                            else:
                                if uni==101:
                                    uni=164
                                else:
                                    uni=0
            if uni > 0:
                res.append(uni)
            i = i + 1

        return res

    async def gsm2str(self, gsm: xarray) -> str:
        i: int
        gsmlen: int
        reslen: int
        resbin: xarray
        resstr: str
        uni: int
        if not self._gsm2unicodeReady:
            await self.initGsm2Unicode()
        gsmlen = len(gsm)
        reslen = gsmlen
        i = 0
        while i < gsmlen:
            if gsm[i] == 27:
                reslen = reslen - 1
            i = i + 1
        resbin = xbytearray(reslen)
        i = 0
        reslen = 0
        while i < gsmlen:
            uni = self._gsm2unicode[gsm[i]]
            if (uni == 27) and (i+1 < gsmlen):
                i = i + 1
                uni = gsm[i]
                if uni < 60:
                    if uni < 41:
                        if uni==20:
                            uni=94
                        else:
                            if uni==40:
                                uni=123
                            else:
                                uni=0
                    else:
                        if uni==41:
                            uni=125
                        else:
                            if uni==47:
                                uni=92
                            else:
                                uni=0
                else:
                    if uni < 62:
                        if uni==60:
                            uni=91
                        else:
                            if uni==61:
                                uni=126
                            else:
                                uni=0
                    else:
                        if uni==62:
                            uni=93
                        else:
                            if uni==64:
                                uni=124
                            else:
                                if uni==101:
                                    uni=164
                                else:
                                    uni=0
            if (uni > 0) and (uni < 256):
                resbin[reslen] = uni
                reslen = reslen + 1
            i = i + 1
        resstr = resbin.decode('latin-1')
        if len(resstr) > reslen:
            resstr = resstr[0: 0 + reslen]
        return resstr

    async def str2gsm(self, msg: str) -> xarray:
        asc: xarray
        asclen: int
        i: int
        ch: int
        gsm7: int
        extra: int
        res: xarray
        wpos: int
        if not self._gsm2unicodeReady:
            await self.initGsm2Unicode()
        asc = xbytearray(msg, 'latin-1')
        asclen = len(asc)
        extra = 0
        i = 0
        while i < asclen:
            ch = asc[i]
            gsm7 = self._iso2gsm[ch]
            if gsm7 == 27:
                extra = extra + 1
            if gsm7 == 0:
                # cannot use standard GSM encoding
                res = xbytearray(0)
                return res
            i = i + 1
        res = xbytearray(asclen+extra)
        wpos = 0
        i = 0
        while i < asclen:
            ch = asc[i]
            gsm7 = self._iso2gsm[ch]
            res[wpos] = gsm7
            wpos = wpos + 1
            if gsm7 == 27:
                if ch < 100:
                    if ch<93:
                        if ch<92:
                            gsm7=60
                        else:
                            gsm7=47
                    else:
                        if ch<94:
                            gsm7=62
                        else:
                            gsm7=20
                else:
                    if ch<125:
                        if ch<124:
                            gsm7=40
                        else:
                            gsm7=64
                    else:
                        if ch<126:
                            gsm7=41
                        else:
                            gsm7=61
                res[wpos] = gsm7
                wpos = wpos + 1
            i = i + 1
        return res

    async def checkNewMessages(self) -> int:
        bitmapStr: str
        prevBitmap: xarray
        newBitmap: xarray
        slot: int
        nslots: int
        pduIdx: int
        idx: int
        bitVal: int
        prevBit: int
        i: int
        nsig: int
        cnt: int
        sig: str
        newArr: Union[list[YSms], None] = []
        newMsg: Union[list[YSms], None] = []
        newAgg: Union[list[YSms], None] = []
        signatures: list[str] = []
        sms: Union[YSms, None]

        bitmapStr = await self.get_slotsBitmap()
        if bitmapStr == self._prevBitmapStr:
            return YAPI.SUCCESS
        prevBitmap = YAPI._hexStrToBin(self._prevBitmapStr)
        newBitmap = YAPI._hexStrToBin(bitmapStr)
        self._prevBitmapStr = bitmapStr
        nslots = 8*len(newBitmap)
        del newArr[:]
        del newMsg[:]
        del signatures[:]
        nsig = 0
        # copy known messages
        pduIdx = 0
        while pduIdx < len(self._pdus):
            sms = self._pdus[pduIdx]
            slot = await sms.get_slot()
            idx = (slot >> 3)
            if idx < len(newBitmap):
                bitVal = (1 << ((slot & 7)))
                if ((newBitmap[idx] & bitVal)) != 0:
                    newArr.append(sms)
                    if await sms.get_concatCount() == 0:
                        newMsg.append(sms)
                    else:
                        sig = await sms.get_concatSignature()
                        i = 0
                        while (i < nsig) and(len(sig) > 0):
                            if signatures[i] == sig:
                                sig = ""
                            i = i + 1
                        if len(sig) > 0:
                            signatures.append(sig)
                            nsig = nsig + 1
            pduIdx = pduIdx + 1
        # receive new messages
        slot = 0
        while slot < nslots:
            idx = (slot >> 3)
            bitVal = (1 << ((slot & 7)))
            prevBit = 0
            if idx < len(prevBitmap):
                prevBit = (prevBitmap[idx] & bitVal)
            if ((newBitmap[idx] & bitVal)) != 0:
                if prevBit == 0:
                    sms = await self.fetchPdu(slot)
                    newArr.append(sms)
                    if await sms.get_concatCount() == 0:
                        newMsg.append(sms)
                    else:
                        sig = await sms.get_concatSignature()
                        i = 0
                        while (i < nsig) and(len(sig) > 0):
                            if signatures[i] == sig:
                                sig = ""
                            i = i + 1
                        if len(sig) > 0:
                            signatures.append(sig)
                            nsig = nsig + 1
            slot = slot + 1

        self._pdus = newArr
        # append complete concatenated messages
        del newAgg[:]
        i = 0
        while i < nsig:
            sig = signatures[i]
            cnt = 0
            pduIdx = 0
            while pduIdx < len(self._pdus):
                sms = self._pdus[pduIdx]
                if await sms.get_concatCount() > 0:
                    if await sms.get_concatSignature() == sig:
                        if cnt == 0:
                            cnt = await sms.get_concatCount()
                            del newAgg[:]
                        newAgg.append(sms)
                pduIdx = pduIdx + 1
            if (cnt > 0) and (len(newAgg) == cnt):
                sms = YSms(self)
                await sms.set_parts(newAgg)
                newMsg.append(sms)
            i = i + 1

        self._messages = newMsg
        return YAPI.SUCCESS

    async def get_pdus(self) -> list[YSms]:
        await self.checkNewMessages()
        return self._pdus

    async def clearPduCounters(self) -> int:
        """
        Clear the SMS units counters.

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        retcode: int

        retcode = await self.set_pduReceived(0)
        if retcode != YAPI.SUCCESS:
            return retcode
        retcode = await self.set_pduSent(0)
        return retcode

    async def sendTextMessage(self, recipient: str, message: str) -> int:
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
        sms: Union[YSms, None]

        sms = YSms(self)
        await sms.set_recipient(recipient)
        await sms.addText(message)
        return await sms.send()

    async def sendFlashMessage(self, recipient: str, message: str) -> int:
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
        sms: Union[YSms, None]

        sms = YSms(self)
        await sms.set_recipient(recipient)
        await sms.set_msgClass(0)
        await sms.addText(message)
        return await sms.send()

    async def newMessage(self, recipient: str) -> YSms:
        """
        Creates a new empty SMS message, to be configured and sent later on.

        @param recipient : a text string with the recipient phone number, either as a
                national number, or in international format starting with a plus sign

        @return YAPI.SUCCESS when the call succeeds.

        On failure, throws an exception or returns a negative error code.
        """
        sms: Union[YSms, None]
        sms = YSms(self)
        await sms.set_recipient(recipient)
        return sms

    async def get_messages(self) -> list[YSms]:
        """
        Returns the list of messages received and not deleted. This function
        will automatically decode concatenated SMS.

        @return an YSms object list.

        On failure, throws an exception or returns an empty list.
        """
        await self.checkNewMessages()
        return self._messages

    # --- (end of generated code: YMessageBox implementation)

