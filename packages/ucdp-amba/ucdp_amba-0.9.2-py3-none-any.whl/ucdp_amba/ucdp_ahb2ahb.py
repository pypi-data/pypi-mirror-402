#
# MIT License
#
# Copyright (c) 2024-2026 nbiotcloud
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
Unified Chip Design Platform - AMBA - AHB Bus Converter.
"""

import enum
from logging import getLogger
from typing import Any, ClassVar, NamedTuple

import ucdp as u
from aligntext import Align, center, left
from icdutil import num

from . import types as t

LOGGER = getLogger(__name__)


class ExtSpec(enum.Enum):
    """Extension Specifier."""

    PORT = 1
    AUTO = 2


PORT = ExtSpec.PORT
AUTO = ExtSpec.AUTO


class ConvDescr(NamedTuple):
    """Conversion Specifier."""

    src_pres: bool = True
    tgt_pres: bool = True
    conv: str = "forward"


OPTMAP = [["n/a", "tie-off"], ["ignore", "forward"]]
DIRMAP = [["m2m", "m2s"], ["s2m", "s2s"]]
VECMAP = [["wide to narrow", "narrow to wide"], ["narrow to wide", "wide to narrow"]]
UTPMAP = [["u2u", "u2e"], ["e2u", "e2e"]]


class UcdpAhb2ahbMod(u.ATailoredMod):
    """
    AHB-to-AHB Converter.

    Universal AHB Bus Converter:
        Master to Slave,
        Slave to Master,
        Optional Protocol Conversion,
        Data and Address Width Conversion,
        Clock Domain Crossing
    """

    filelists: ClassVar[u.ModFileLists] = (
        u.ModFileList(
            name="hdl",
            gen="full",
            filepaths=("$PRJROOT/{mod.topmodname}/{mod.modname}.sv"),
            template_filepaths=("ucdp_ahb2ahb.sv.mako", "sv.mako"),
        ),
    )

    source_type: t.AhbMstType | t.AhbSlvType
    target_type: t.AhbMstType | t.AhbSlvType
    async_conv: bool = False
    _conv_spec: dict[str, Any] = u.PrivateField(default_factory=dict)
    __ext_param: dict[str, Any] = u.PrivateField(default_factory=dict)

    def _get_usertype_width(self, usertpye) -> int:
        if usertpye is None:
            return 0
        if isinstance(usertpye, u.UintType):
            return usertpye.width
        if isinstance(usertpye, u.AEnumType):
            return usertpye.bits
        LOGGER.error(f"Dealing with unknown user type: {usertpye}")
        return 0

    def _determine_haddr_conv(self) -> None:
        src_type = self.source_type
        tgt_type = self.target_type
        awdiff = tgt_type.addrwidth - src_type.addrwidth
        self._conv_spec["haddr"] = {}
        conv = "forward" if awdiff == 0 else "reduce" if awdiff < 0 else "expand"
        if self.__ext_param.get("haddr", None) is None:
            if conv == "reduce":
                self._conv_spec["haddr"]["red"] = tgt_type.addrwidth
            elif conv == "expand":
                self._conv_spec["haddr"]["exp"] = u.UintType(awdiff, default=0)
                conv += " by constant"
        elif conv == "expand":
            self._conv_spec["haddr"]["exp"] = self.__ext_param["haddr"]
            if isinstance(self.__ext_param["haddr"], u.Port):
                conv += " by port"
            else:
                conv += " by constant"
        self._conv_spec["haddr"]["descr"] = ConvDescr(conv=conv)

    def _determine_hdata_hstrb_conv(self) -> None:
        src_type = self.source_type
        tgt_type = self.target_type
        # hwdata/hrdata
        self._conv_spec["hwdata"] = {}
        self._conv_spec["hrdata"] = {}
        dwdiff = tgt_type.datawidth - src_type.datawidth
        if dwdiff == 0:
            conv = "forward"
        else:
            conv = "convert"
            if dwdiff > 0:
                wide, narr = tgt_type.datawidth, src_type.datawidth
            else:
                wide, narr = src_type.datawidth, tgt_type.datawidth
            self._conv_spec["hwdata"]["narr"] = narr
            self._conv_spec["hwdata"]["ratio"] = wide // narr
            self._conv_spec["hwdata"]["n2w"] = dwdiff > 0
        self._conv_spec["hwdata"]["descr"] = ConvDescr(conv=conv + (f" {VECMAP[0][dwdiff > 0]}" if dwdiff != 0 else ""))
        self._conv_spec["hrdata"]["descr"] = ConvDescr(conv=conv + (f" {VECMAP[1][dwdiff > 0]}" if dwdiff != 0 else ""))
        # hwstrb
        self._conv_spec["hwstrb"] = {}
        strbw = tgt_type.datawidth >> 3
        conv = OPTMAP[src_type.proto.has_wstrb][tgt_type.proto.has_wstrb]
        if conv == "tie-off":
            self._conv_spec["hwstrb"]["tie"] = u.UintType(strbw, default=(1 << strbw) - 1)
        elif (conv == "forward") and (dwdiff != 0):
            conv = "convert" + (f" {VECMAP[0][dwdiff > 0]}" if dwdiff != 0 else "")
            self._conv_spec["hwstrb"]["narr"] = narr >> 3
            self._conv_spec["hwstrb"]["ratio"] = wide // narr
            self._conv_spec["hwstrb"]["n2w"] = dwdiff > 0
        self._conv_spec["hwstrb"]["descr"] = ConvDescr(
            src_pres=src_type.proto.has_wstrb, tgt_pres=tgt_type.proto.has_wstrb, conv=conv
        )

    def _determine_usertp_conv(self, usrsig: str) -> None:  # noqa: C901, PLR0912
        self._conv_spec[usrsig] = {}
        tname = usrsig[1:] + "type"  # drop the 'h'
        src_usertp = self.source_type.proto.__dict__[tname]
        tgt_usertp = self.target_type.proto.__dict__[tname]
        if usrsig in ["hruser", "hbuser"]:
            src_usertp, tgt_usertp = tgt_usertp, src_usertp  # swap direction
        conv = OPTMAP[src_usertp is not None][tgt_usertp is not None]
        utp = UTPMAP[isinstance(src_usertp, u.AEnumType)][isinstance(tgt_usertp, u.AEnumType)]
        self._conv_spec[usrsig]["utp"] = utp
        usertp_ext = self.__ext_param.get(usrsig, None)
        if conv == "tie-off":
            if usertp_ext is None or usertp_ext == AUTO:
                if isinstance(tgt_usertp, u.AEnumType):
                    self._conv_spec[usrsig]["tie"] = tgt_usertp.decode(tgt_usertp.default)
                else:
                    self._conv_spec[usrsig]["tie"] = tgt_usertp
            else:
                self._conv_spec[usrsig]["tie"] = self.__ext_param[usrsig]
        elif conv == "forward":
            if usertp_ext is None:
                if src_usertp != tgt_usertp:
                    LOGGER.error(f"Mismatching '{usrsig}' types without explicit conversion given.")
                    conv = "tie-off"
                    self._conv_spec[usrsig]["tie"] = tgt_usertp
            else:
                src_hw = self._get_usertype_width(src_usertp)
                tgt_hw = self._get_usertype_width(tgt_usertp)
                if isinstance(usertp_ext, dict):
                    conv = "convert"
                    self._conv_spec[usrsig]["map"] = usertp_ext
                elif tgt_hw < src_hw:
                    conv = "reduce"
                    self._conv_spec[usrsig]["red"] = tgt_hw
                elif tgt_hw > src_hw:
                    if isinstance(usertp_ext, u.Port):
                        conv = "expand by port"
                        self._conv_spec[usrsig]["exp"] = usertp_ext
                    else:
                        conv = "expand by constant"
                        if usertp_ext == AUTO:
                            self._conv_spec[usrsig]["exp"] = u.UintType(tgt_hw - src_hw, default=0)
                        else:
                            self._conv_spec[usrsig]["exp"] = usertp_ext
        self._conv_spec[usrsig]["descr"] = ConvDescr(
            src_pres=src_usertp is not None, tgt_pres=tgt_usertp is not None, conv=conv
        )

    def _determine_hmaster_conv(self) -> None:
        src_type = self.source_type
        tgt_type = self.target_type
        self._conv_spec["hmaster"] = {}
        src_hmw = src_type.proto.hmaster_width
        tgt_hmw = tgt_type.proto.hmaster_width
        hmwdiff = tgt_hmw - src_hmw
        conv = OPTMAP[src_hmw > 0][tgt_hmw > 0]
        if self.__ext_param.get("hmaster", None) is None:
            if conv == "tie-off":
                self._conv_spec["hmaster"]["tie"] = u.UintType(tgt_hmw, default=0)
            elif conv == "forward" and hmwdiff < 0:
                conv = "reduce"
                self._conv_spec["hmaster"]["red"] = tgt_hmw
            elif conv == "forward" and hmwdiff > 0:
                conv = "expand by constant"
                self._conv_spec["hmaster"]["exp"] = u.UintType(hmwdiff, default=0)
        elif hmwdiff > 0:
            if conv == "tie-off":
                self._conv_spec["hmaster"]["tie"] = self.__ext_param["hmaster"]
            else:
                conv = "expand by port" if isinstance(self.__ext_param["hmaster"], u.Port) else "expand by constant"
                self._conv_spec["hmaster"]["exp"] = self.__ext_param["hmaster"]
        self._conv_spec["hmaster"]["descr"] = ConvDescr(src_pres=src_hmw > 0, tgt_pres=tgt_hmw > 0, conv=conv)

    def _determine_hprot_conv(self) -> None:
        src_type = self.source_type
        tgt_type = self.target_type
        self._conv_spec["hprot"] = {}
        src_hpw = src_type.proto.hprotwidth
        tgt_hpw = tgt_type.proto.hprotwidth
        hpwdiff = tgt_hpw - src_hpw
        conv = OPTMAP[src_hpw > 0][tgt_hpw > 0]
        hprot_ext = self.__ext_param.get("hprot", None)
        if conv == "forward":
            if hpwdiff > 0:
                conv = "expand"
                self._conv_spec["hprot"]["exp"] = hprot_ext
                if hprot_ext is None:
                    conv += " by logic"
                elif isinstance(hprot_ext, u.Port):
                    conv += " by port"
                else:
                    conv += " by constant"
            elif hpwdiff < 0:
                conv = "reduce"
        elif conv == "tie-off":
            self._conv_spec["hprot"]["tie"] = hprot_ext
            if hprot_ext is None:
                self._conv_spec["hprot"]["tie"] = tgt_type.proto.hprottype
                conv += " to default"
            elif isinstance(hprot_ext, u.Port):
                conv += " to port"
            else:
                conv += " to constant"
        self._conv_spec["hprot"]["descr"] = ConvDescr(src_pres=src_hpw > 0, tgt_pres=tgt_hpw > 0, conv=conv)

    def _determine_conv(self):
        if self._conv_spec != {}:
            return
        src_type = self.source_type
        tgt_type = self.target_type
        src_slv = isinstance(src_type, t.AhbSlvType)
        tgt_slv = isinstance(tgt_type, t.AhbSlvType)
        self._conv_spec["dir"] = convdir = DIRMAP[src_slv][tgt_slv]
        # simple forwarding:
        self._conv_spec["hwrite"] = {"descr": ConvDescr()}
        self._conv_spec["htrans"] = {"descr": ConvDescr()}
        self._conv_spec["hsize"] = {"descr": ConvDescr()}
        self._conv_spec["hresp"] = {"descr": ConvDescr()}
        # hsel
        self._conv_spec["hsel"] = {
            "descr": ConvDescr(src_pres=src_slv, tgt_pres=tgt_slv, conv=OPTMAP[src_slv][tgt_slv])
        }
        # haddr
        self._determine_haddr_conv()
        # hwdata/hrdata/hwstrb
        self._determine_hdata_hstrb_conv()
        # hburst/hnonsec/hmastlock
        for opt in ["hburst", "hnonsec", "hmastlock"]:
            src_pres = src_type.proto.__dict__[f"has_{opt}"]
            tgt_pres = tgt_type.proto.__dict__[f"has_{opt}"]
            self._conv_spec[opt] = {
                "descr": ConvDescr(src_pres=src_pres, tgt_pres=tgt_pres, conv=OPTMAP[src_pres][tgt_pres])
            }
        # hauser/hwuser/hruser/hbuser
        self._determine_usertp_conv("hauser")
        self._determine_usertp_conv("hwuser")
        self._determine_usertp_conv("hruser")
        self._determine_usertp_conv("hbuser")
        # hmaster
        self._determine_hmaster_conv()
        # hexcl/hexokay
        src_excl = src_type.proto.has_exclxfers
        tgt_excl = tgt_type.proto.has_exclxfers
        self._conv_spec["hexcl"] = {
            "descr": ConvDescr(src_pres=src_excl, tgt_pres=tgt_excl, conv=OPTMAP[src_excl][tgt_excl])
        }
        # deliberately swapped optmap
        self._conv_spec["hexokay"] = {
            "descr": ConvDescr(src_pres=src_excl, tgt_pres=tgt_excl, conv=OPTMAP[tgt_excl][src_excl])
        }
        # hready/hreadyout
        conv = "forward" if convdir in ["m2m", "s2s"] else "convert"
        self._conv_spec["hready"] = {"descr": ConvDescr(conv=conv)}
        conv = "forward" if convdir == "s2s" else "n/a" if convdir == "m2m" else "convert"
        self._conv_spec["hreadyout"] = {"descr": ConvDescr(src_pres=src_slv, tgt_pres=tgt_slv, conv=conv)}
        # hprot
        self._determine_hprot_conv()

    def _add_usertp_const(self) -> None:
        for usrsig in ["hauser", "hwuser", "hruser", "hbuser"]:
            if self._conv_spec[usrsig]["descr"].conv in ["tie-off", "convert"]:
                tname = usrsig[1:] + "type"  # drop the 'h'
                utp = self._conv_spec[usrsig]["utp"]
                # hruser & hbuser are BWD signals
                srcd = ["e2u", "e2e"] if usrsig in ["hauser", "hwuser"] else ["u2e", "e2e"]
                tgtd = ["u2e", "e2e"] if usrsig in ["hauser", "hwuser"] else ["e2u", "e2e"]
                if utp in srcd:
                    src_usertp = self.source_type.proto.__dict__[tname]
                    self.add_type_consts(src_usertp, name=f"src_{usrsig}")
                if utp in tgtd:
                    tgt_usertp = self.target_type.proto.__dict__[tname]
                    self.add_type_consts(tgt_usertp, name=f"tgt_{usrsig}")

    def _build(self):
        if self.async_conv:
            self.add_port(u.ClkRstAnType(), "src_i")
            self.add_port(u.ClkRstAnType(), "tgt_i")
        elif self.source_type.datawidth != self.target_type.datawidth:
            self.add_port(u.ClkRstAnType(), "main_i")
        self.add_port(self.source_type, "ahb_src_i", title="AHB Source Input", comment="AHB Source")
        self.add_port(self.target_type, "ahb_tgt_o", title="AHB Target Output", comment="AHB Target")

    def _build_dep(self):
        # TODO: async
        if self.source_type != self.target_type:
            self.add_type_consts(t.AhbTransType())
            self.add_type_consts(t.AhbBurstType())
        self._determine_conv()
        self._add_usertp_const()

    def define_haddr_ext(self, ext: int | ExtSpec = 0) -> None:
        """Define extension for haddr when src_addrwith < tgt_addrwidth."""
        if self.__ext_param.get("haddr", None) is not None:
            LOGGER.warning("Redefining HADDR extension")
        awdiff = self.target_type.addrwidth - self.source_type.addrwidth
        if awdiff <= 0:
            LOGGER.warning(f"Source addrwidth equal or greater than target addrwidth, no extension for {self.name}.")
            return
        if isinstance(ext, int):
            if num.calc_unsigned_width(ext) > awdiff:
                LOGGER.error(f"Extension value of {ext} too wide for haddr extension.")
                ext = 0
            self.__ext_param["haddr"] = u.UintType(awdiff, default=ext)
        elif ext == PORT:
            port = self.add_port(
                u.UintType(awdiff), "haddr_ext_i", title="Target HADDR Extension", comment="Target HADDR Extension"
            )
            self.__ext_param["haddr"] = port

    def define_hmaster_ext(self, ext: int | ExtSpec = 0) -> None:
        """Define extension of hmaster when width of src.hmaster_width < tgt.hmaster_width (including tie-off)."""
        if self.__ext_param.get("hmaster", None) is not None:
            LOGGER.warning("Redefining HMASTER extension")
        hmwdiff = self.target_type.proto.hmaster_width - self.source_type.proto.hmaster_width
        if hmwdiff <= 0:
            LOGGER.warning(
                f"Source hmaster_width equal or greater than target hmaster_width, no extension for {self.name}."
            )
            return
        if isinstance(ext, int):
            if num.calc_unsigned_width(ext) > hmwdiff:
                LOGGER.error(f"Extension value of {ext} too wide for hmaster extension.")
                ext = 0
            self.__ext_param["hmaster"] = u.UintType(hmwdiff, default=ext)
        elif ext == PORT:
            port = self.add_port(
                u.UintType(hmwdiff),
                "hmaster_ext_i",
                title="Target HMASTER Extension",
                comment="Target HMASTER Extension",
            )
            self.__ext_param["hmaster"] = port

    def define_hprot_ext(self, ext: int | ExtSpec = 0) -> None:
        """Define extension of hprot when width of src.hprotwidth < tgt.hprotwidth (including tie-off)."""
        if self.__ext_param.get("hprot", None) is not None:
            LOGGER.warning("Redefining HPROT extension")
        hpwdiff = self.target_type.proto.hprotwidth - self.source_type.proto.hprotwidth
        if hpwdiff <= 0:
            LOGGER.warning(f"Source hprotwidth equal or greater than target hprotwidth, no extension for {self.name}.")
            return
        if isinstance(ext, int):
            if num.calc_unsigned_width(ext) > hpwdiff:
                LOGGER.error(f"Extension value of {ext} too wide for hprot extension.")
                ext = 0
            self.__ext_param["hprot"] = u.UintType(hpwdiff, default=ext)
        elif ext == PORT:
            port = self.add_port(
                u.UintType(hpwdiff),
                "hprot_ext_i",
                title="Target HPROT Extension",
                comment="Target HPROT Extension",
            )
            self.__ext_param["hprot"] = port

    def _user_conversion(self, usrsig: str, conv: int | str | dict | ExtSpec = 0) -> None:  # noqa: C901, PLR0912
        """Prepare conversion for user-types."""
        uname = usrsig.upper()
        if self.__ext_param.get(usrsig, None) is not None:
            LOGGER.warning(f"Redefining {uname} conversion")
        tname = usrsig[1:] + "type"  # drop the 'h'
        src_usertp = self.source_type.proto.__dict__[tname]
        tgt_usertp = self.target_type.proto.__dict__[tname]
        if usrsig in ["hruser", "hbuser"]:
            src_usertp, tgt_usertp = tgt_usertp, src_usertp  # swap direction
            snd, rcv = "tgt", "src"
        else:
            snd, rcv = "src", "tgt"
        if (src_usertp is None or tgt_usertp is None) and isinstance(conv, dict):
            LOGGER.error(f"Conversion map given, but not both interfaces have {uname}.")
            return
        if src_usertp is not None and src_usertp == tgt_usertp and not isinstance(conv, dict):
            LOGGER.warning("{uname} types are identical, no conversion necessary.")
            return
        if conv == AUTO:
            self.__ext_param[usrsig] = AUTO
            return
        src_uw = self._get_usertype_width(src_usertp)
        tgt_uw = self._get_usertype_width(tgt_usertp)
        uwdiff = tgt_uw - src_uw
        if isinstance(conv, int):
            if uwdiff <= 0:
                LOGGER.warning(
                    f"Source {uname} width equal or greater than {rcv}_{uname} width, no extension for {self.name}."
                )
                return
            if num.calc_unsigned_width(conv) > uwdiff:
                LOGGER.error(f"Extension value of {conv} too wide for {uname} extension.")
                conv = 0
            if uwdiff == tgt_uw and isinstance(tgt_usertp, u.AEnumType):  # tie-off for enum
                if conv not in tgt_usertp.keys():
                    raise ValueError(f"Value '{conv}' can not be used to index tgt_{usrsig}")
                self.__ext_param[usrsig] = tgt_usertp.decode(conv)
            else:
                self.__ext_param[usrsig] = u.UintType(uwdiff, default=conv)
        elif isinstance(conv, str):
            if not isinstance(tgt_usertp, u.AEnumType):
                raise ValueError(f"Value '{conv}' does not match {uname} type.")
            if uwdiff != tgt_uw:
                raise ValueError(f"Value '{conv}' can only be used for tie-off, not for extension.")
            if conv not in [item.value for item in tgt_usertp.values()]:
                raise ValueError(f"Value '{conv}' is not in {uname} enumeration.")
            self.__ext_param[usrsig] = conv
        elif conv == PORT:
            if uwdiff <= 0:
                LOGGER.warning(
                    f"Source {uname} width equal or greater than {rcv}_{uname} width, no extension for {self.name}."
                )
                return
            port = self.add_port(
                u.UintType(uwdiff),
                f"{usrsig}_ext_i",
                title=f"Target {uname} Extension",
                comment=f"Target {uname} Extension",
            )
            self.__ext_param[usrsig] = port
        elif isinstance(conv, dict):
            if isinstance(src_usertp, u.AEnumType):
                src_values = [item.value for item in src_usertp.values()]
            if isinstance(tgt_usertp, u.AEnumType):
                tgt_values = [item.value for item in tgt_usertp.values()]
            map = {}
            for key, value in conv.items():
                kk, vv = key, value
                if key is None:
                    map[kk] = vv
                    continue
                if isinstance(key, int):
                    if isinstance(src_usertp, u.UintType):
                        if num.calc_unsigned_width(key) > src_uw:
                            raise ValueError(f"Value '{key}' too big for {snd}_{usrsig} vector.")
                        kk = u.UintType(src_uw, default=key)
                    if isinstance(src_usertp, u.AEnumType):
                        if key not in src_usertp.keys():
                            raise ValueError(f"Value '{key}' is not in keys of {snd}_{usrsig}.")
                        kk = src_usertp.decode(key)
                    map[kk] = vv
                    continue
                if isinstance(key, str):
                    if not isinstance(src_usertp, u.AEnumType):
                        raise ValueError(f"Value '{key}' can not be used to index {snd}_{usrsig}.")
                    if key not in src_values:
                        raise ValueError(f"Value '{key}' is not in {snd}_{usrsig} enumeration.")
                    map[kk] = vv
            for key, value in map.items():
                kk, vv = key, value
                if isinstance(value, int):
                    if isinstance(tgt_usertp, u.UintType):
                        if num.calc_unsigned_width(value) > tgt_uw:
                            raise ValueError(f"Value '{value}' too big for {rcv}_{usrsig} vector.")
                        vv = u.UintType(tgt_uw, default=value)
                    if isinstance(tgt_usertp, u.AEnumType):
                        if value not in tgt_usertp.keys():
                            raise ValueError(f"Value '{value}' can not be used to index {rcv}_{usrsig}")
                        vv = tgt_usertp.decode(value)
                    map[kk] = vv
                    continue
                if isinstance(value, str):
                    if not isinstance(tgt_usertp, u.AEnumType):
                        raise ValueError(f"Value '{value}' can not be used to index {rcv}_{usrsig}.")
                    if value not in tgt_values:
                        raise ValueError(f"Value '{value}' is not in {rcv}_{usrsig} enumeration.")
                    map[kk] = vv
                    continue
                raise ValueError(f"Value '{value}' can not be mapped to {rcv}_{usrsig}")
            if isinstance(tgt_usertp, u.AEnumType):
                map.setdefault(None, tgt_usertp.decode(tgt_usertp.default))
            else:
                map.setdefault(None, u.UintType(tgt_uw, default=tgt_usertp.default))
            self.__ext_param[usrsig] = map

    def define_hauser_conversion(self, conv: int | str | dict | ExtSpec = 0) -> None:
        """Define conversion for 'hauser' types."""
        self._user_conversion("hauser", conv)

    def define_hwuser_conversion(self, conv: int | str | dict | ExtSpec = 0) -> None:
        """Define conversion for 'hwuser' types."""
        self._user_conversion("hwuser", conv)

    def define_hruser_conversion(self, conv: int | str | dict | ExtSpec = 0) -> None:
        """Define conversion for 'hruser' types."""
        self._user_conversion("hruser", conv)

    def define_hbuser_conversion(self, conv: int | str | dict | ExtSpec = 0) -> None:
        """Define conversion for 'hbuser' types."""
        self._user_conversion("hbuser", conv)

    def get_overview(self) -> str:
        """Converter Overview."""
        if self.source_type == self.target_type:
            return "No conversion, just feed-through."
        self._determine_conv()
        cdir = self._conv_spec["dir"].replace("s", "Slave")
        cdir = cdir.replace("m", "Master")
        cdir = cdir.replace("2", " to ")
        ovr = Align(rtrim=True)
        ovr.set_alignments(left, center, center, left)
        ovr.add_spacer("Converting " + cdir)
        ovr.add_spacer()
        ovr.add_row("Signal", "Src", "Tgt", "Conv")
        for signal, item in self._conv_spec.items():
            if not isinstance(item, dict) or (conv := item.get("descr", None)) is None:
                continue
            src_pres = "x" if conv.src_pres else "-"
            tgt_pres = "x" if conv.tgt_pres else "-"
            ovr.add_row(signal, src_pres, tgt_pres, conv.conv)
        return "\n".join(ovr)

    @staticmethod
    def build_top(**kwargs):
        """Build example top module and return it."""
        return UcdpAhb2ahbExampleMod()


class UcdpAhb2ahbExampleMod(u.AMod):
    """
    Just an Example Converter.
    """

    def _build(self):  # noqa: C901, PLR0912
        class MyUserType(t.ASecIdType):
            """My AUser Type."""

            title: str = "AHB User Type"
            comment: str = "AHB User Type"

            def _build(self):
                self._add(0, "apps")
                self._add(2, "comm")
                self._add(5, "audio")

        class MyOtherUserType(t.ASecIdType):
            """My Other AUser Type."""

            title: str = "Another AHB User Type"
            comment: str = "Another AHB User Type"
            keytype: u.UintType = u.UintType(6)

            def _build(self):
                self._add(0, "audio")
                self._add(2, "apps")
                self._add(5, "comm")

        minp = t.AmbaProto(
            name="minp",
            hprotwidth=0,
            has_hburst=False,
            has_wstrb=False,
            hmaster_width=0,
            has_hmastlock=False,
            has_hnonsec=False,
            has_exclxfers=False,
        )

        smlp = t.AmbaProto(
            name="smlp",
            has_hburst=True,
            has_wstrb=True,
            hmaster_width=4,
            has_hmastlock=True,
            has_hnonsec=True,
            has_exclxfers=True,
        )

        lrgp = t.AmbaProto(
            name="lrgp",
            hprotwidth=7,
            has_wstrb=True,
            hmaster_width=6,
            has_hmastlock=True,
            has_hnonsec=True,
            has_exclxfers=True,
        )

        hsp = minp.new(
            name="hsp",
            ausertype=u.UintType(5, default=1),
            wusertype=u.UintType(5, default=1),
            rusertype=u.UintType(5, default=1),
            busertype=u.UintType(5, default=1),
        )
        hep = minp.new(
            name="hep",
            ausertype=MyUserType(default=2),
            wusertype=MyUserType(default=2),
            rusertype=MyUserType(default=2),
            busertype=MyUserType(default=2),
        )
        hop = minp.new(
            name="hop",
            ausertype=MyOtherUserType(default=5),
            wusertype=MyOtherUserType(default=5),
            rusertype=MyOtherUserType(default=5),
            busertype=MyOtherUserType(default=5),
        )

        for srctp, srctt in [(t.AhbMstType, "mst"), (t.AhbSlvType, "slv")]:
            for tgttp, tgttt in [(t.AhbMstType, "mst"), (t.AhbSlvType, "slv")]:
                for srcp in [minp, smlp, lrgp]:
                    srcaw = 36 if srcp == lrgp else 32
                    srcdw = 128 if srcp == lrgp else 32
                    for tgtp in [minp, smlp, lrgp]:
                        tgtaw = 36 if tgtp == lrgp else 32
                        tgtdw = 128 if tgtp == lrgp else 32
                        source_type = srctp(addrwidth=srcaw, datawidth=srcdw, proto=srcp)
                        target_type = tgttp(addrwidth=tgtaw, datawidth=tgtdw, proto=tgtp)
                        for ext, extn in [(None, "n"), (PORT, "p"), (1, "s")]:
                            mname = f"u_{srctt}2{tgttt}_{srcp.name}_{tgtp.name}_{extn}"
                            m = UcdpAhb2ahbMod(
                                self,
                                mname,
                                source_type=source_type,
                                target_type=target_type,
                            )
                            if ext is None:
                                continue
                            m.define_haddr_ext(ext)
                            m.define_hmaster_ext(ext)
                            m.define_hprot_ext(ext)

        for srcp in [minp, hsp, hep, hop]:
            for tgtp in [minp, hsp, hep, hop]:
                if (srcp == minp) and (tgtp == minp):
                    continue  # combination already covered above
                for trsl, tname in [(None, "n"), (AUTO, "a"), (PORT, "p"), (2, "s"), ("apps", "e")]:
                    if tname == "n" and srcp in [hsp, hep, hop] and tgtp in [hsp, hep, hop] and srcp != tgtp:
                        continue  # different hauser types need explicit conversion
                    mname = f"u_usertp_{srcp.name}_{tgtp.name}_{tname}"
                    m = UcdpAhb2ahbMod(
                        self,
                        mname,
                        source_type=t.AhbMstType(proto=srcp),
                        target_type=t.AhbMstType(proto=tgtp),
                    )
                    if trsl is None:
                        continue
                    # when using enum value, it must be for tie-off and signal to be tied must be an enum
                    if tname != "e" or ((srcp == minp) and (tgtp in [hep, hop])):
                        m.define_hauser_conversion(trsl)
                        m.define_hwuser_conversion(trsl)
                    if tname != "e" or ((tgtp == minp) and (srcp in [hep, hop])):
                        m.define_hruser_conversion(trsl)
                        m.define_hbuser_conversion(trsl)

        hmap_u2u = {0: 5, 2: 0, 5: 2, None: 2}
        hmap_u2e = {0: "comm", 2: 0, 5: 2}
        hmap_e2u = {0: 5, "apps": 0, 5: 2}
        hmap_e2e = {0: "comm", "apps": 0, 5: 2, None: "audio"}

        for srcp in [hsp, hep, hop]:
            for tgtp in [hsp, hep, hop]:
                if srcp in [hep, hop] and srcp == tgtp:
                    continue  # no need to map identical enum, it's just forwarding
                for trsl, trbk, tname in [
                    (hmap_u2u, hmap_u2u, "u2u"),
                    (hmap_u2e, hmap_e2u, "u2e"),
                    (hmap_e2u, hmap_u2e, "e2u"),
                    (hmap_e2e, hmap_e2e, "e2e"),
                ]:
                    if (srcp == hsp and tname[0] == "e") or (tgtp == hsp and tname[2] == "e"):
                        continue  # can't use enum values for non-enum hauser
                    mname = f"u_usertp_{srcp.name}_{tgtp.name}_{tname}"
                    m = UcdpAhb2ahbMod(
                        self,
                        mname,
                        source_type=t.AhbMstType(proto=srcp),
                        target_type=t.AhbMstType(proto=tgtp),
                    )
                    m.define_hauser_conversion(trsl)
                    m.define_hwuser_conversion(trsl)
                    m.define_hruser_conversion(trbk)
                    m.define_hbuser_conversion(trbk)
