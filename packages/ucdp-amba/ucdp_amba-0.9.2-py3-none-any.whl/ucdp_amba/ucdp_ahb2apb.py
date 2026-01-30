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
Unified Chip Design Platform - AMBA - AHB2APB.
"""

from logging import getLogger
from typing import ClassVar

import ucdp as u
from humannum import bytes_
from icdutil import num
from ucdp_addr import AddrDecoder, AddrRef, AddrSlave
from ucdp_glbl.irq import LevelIrqType

from . import types as t

LOGGER = getLogger(__name__)


class Slave(AddrSlave):
    """
    Slave.
    """

    proto: t.AmbaProto
    """Protocol Version."""


class Ahb2ApbFsmType(u.AEnumType):
    """
    FSM Type for AHB to APB Bridge.
    """

    keytype: u.UintType = u.UintType(2)
    title: str = "AHB to APB FSM Type"
    comment: str = "AHB to APB FSM Type"

    def _build(self):
        self._add(0, "idle", "No transfer")
        self._add(1, "apb_ctrl", "Control Phase")
        self._add(2, "apb_data", "Data Phase")
        self._add(3, "ahb_err", "Error Phase")


class UcdpAhb2apbMod(u.ATailoredMod, AddrDecoder):
    """
    AHB to APB Bridge.

    Keyword Args:
        proto (AmbaProto): Defines Protocol
        errirq (bool): Use Error Interrupt instead of standard AHB Response Signalling
        optbw (bool): Optimized Bandwidth, faster response but increased logic depth

    Example:

        >>> class Mod(u.AMod):
        ...     def _build(self):
        ...         ahb2apb = UcdpAhb2apbMod(self, "u_ahb2apb")
        ...         ahb2apb.add_slave("uart")
        ...         ahb2apb.add_slave("spi")

        >>> ahb2apb = Mod().get_inst("u_ahb2apb")
        >>> print(ahb2apb.get_overview())
        * Top:     `None`
        * Defines: `None`
        * Size:    `8 KB`
        <BLANKLINE>
        | Addrspace | Type  | Base      | Size             | Infos | Attributes |
        | --------- | ----- | --------- | ---------------- | ----- | ---------- |
        | uart      | Slave | `+0x0`    | `1024x32 (4 KB)` | Sub   |            |
        | spi       | Slave | `+0x1000` | `1024x32 (4 KB)` | Sub   |            |
        <BLANKLINE>
    """

    filelists: ClassVar[u.ModFileLists] = (
        u.ModFileList(
            name="hdl",
            gen="full",
            filepaths=("$PRJROOT/{mod.topmodname}/{mod.modname}.sv"),
            template_filepaths=("ucdp_ahb2apb.sv.mako", "sv.mako"),
        ),
    )

    proto: t.AmbaProto = t.AMBA3
    errirq: bool = False
    optbw: bool = False
    is_sub: bool = True
    default_size: u.Bytes | None = 4096
    ahb_addrwidth: int = 32
    datawidth: int = 32

    def add_slave(
        self,
        name: str,
        baseaddr: int | str = u.AUTO,
        size: u.Bytes | None = None,
        proto: t.AmbaProto | None = None,
        route: u.Routeable | None = None,
        ref: u.BaseMod | str | None = None,
    ):
        """
        Add APB Slave.

        Args:
            name: Slave Name.

        Keyword Args:
            baseaddr: Base address, Next Free address by default. Do not add address space if `None`.
            size: Address Space.
            proto: AMBA Protocol Selection.
            route: APB Slave Port to connect.
            ref: Logical Module connected.
        """
        proto = proto or self.proto
        slave = Slave(name=name, addrdecoder=self, proto=proto, ref=ref)
        self.slaves.add(slave)
        size = bytes_(size or self.default_size)
        if baseaddr is not None and (size is not None or self.default_size):
            slave.add_addrrange(baseaddr, size)

        portname = f"apb_slv_{name}_o"
        title = f"APB Slave {name!r}"
        self.add_port(
            t.ApbSlvType(proto=proto, addrwidth=num.calc_unsigned_width(size - 1), datawidth=self.datawidth),
            portname,
            title=title,
            comment=title,
        )
        if route:
            self.con(portname, route)

        return slave

    def _check_slaves(self):
        if not self.slaves:
            LOGGER.error("%r: has no APB slaves", self)
        slvchk = []
        for aspc in self.addrmap:
            if aspc.name in slvchk:
                raise ValueError(f"Slave {aspc.name!r} has non-contiguous address range.")
            slvchk.append(aspc.name)

    def _check_hauser(self) -> bool:
        use_hauser = False
        ahbproto = self.proto
        for slv in self.slaves:
            apbproto = slv.proto
            if ahbproto == apbproto:
                use_hauser = use_hauser or (ahbproto.ausertype is not None)
            elif (ahbproto.ausertype is not None) and (apbproto.ausertype is None):
                LOGGER.warning(f"Bridge {self.name!r} slave {slv.name!r} has no APB 'pauser', ignoring AHB 'hauser'!")
            elif (ahbproto.ausertype is None) and (apbproto.ausertype is not None):
                LOGGER.warning(
                    f"Bridge {self.name!r} slave {slv.name!r} is clamping APB 'pauser' since there is no AHB 'hauser'!"
                )
            elif ahbproto.ausertype != apbproto.ausertype:
                LOGGER.error(f"Bridge {self.name!r} slave {slv.name!r} has differing AHB 'hauser' and APB 'pauser'!")
            else:
                use_hauser = True
        return use_hauser

    def _check_wstrb(self) -> tuple[bool, bool]:
        use_pstrb = False
        for slv in self.slaves:
            apbproto = slv.proto
            if (self.datawidth > 8) and (not apbproto.has_wstrb):  # noqa: PLR2004
                LOGGER.warning(f"Bridge {self.name!r} slave {slv.name!r} can only support full-datawidth writes.")
            use_pstrb = use_pstrb or apbproto.has_wstrb
        # hstrb only makes sense when there is at least one pstrb...
        use_hstrb = self.proto.has_wstrb and use_pstrb
        return (use_hstrb, use_pstrb)

    def _build(self):
        self.add_port(u.ClkRstAnType(), "main_i")
        if self.errirq:
            title = "APB Error Interrupt"
            self.add_port(LevelIrqType(), "irq_o", title=title, comment=title)
        self.add_port(
            t.AhbSlvType(proto=self.proto, addrwidth=self.ahb_addrwidth, datawidth=self.datawidth), "ahb_slv_i"
        )

    def _build_dep(self):
        self._check_slaves()
        use_hauser = self._check_hauser()
        self.add_type_consts(t.AhbTransType())
        self.add_type_consts(t.AhbSizeType())
        self.add_type_consts(t.AhbWriteType())
        self.add_type_consts(t.ApbReadyType())
        self.add_type_consts(t.ApbRespType())
        self.add_type_consts(Ahb2ApbFsmType(), name="fsm", item_suffix="st")
        self.add_signal(u.BitType(), "new_xfer_s")
        self.add_signal(u.BitType(), "valid_addr_s")
        self.add_signal(u.BitType(), "ahb_slv_sel_s")
        self.add_signal(Ahb2ApbFsmType(), "fsm_r")
        self.add_signal(t.AhbReadyType(), "hready_r")
        use_hstrb, use_pstrb = self._check_wstrb()
        if use_hstrb:
            self.add_signal(t.AhbWstrbType(self.datawidth), "hwstrb_s")
            self.add_signal(t.AhbWstrbType(self.datawidth), "hwstrb_r")
        if use_hauser:
            self.add_signal(self.proto.ausertype, "hauser_r")
        if self.optbw:
            self.add_signal(t.AhbReadyType(), "hready_s")
        if not self.errirq:
            self.add_signal(t.ApbRespType(), "hresp_r")
        rng_bits = [num.calc_unsigned_width(aspc.size - 1) for aspc in self.addrmap]
        self.add_signal(t.ApbAddrType(max(rng_bits)), "paddr_r")
        self.add_signal(t.ApbWriteType(), "pwrite_r")
        if use_pstrb:
            self.add_signal(t.ApbPstrbType(self.datawidth), "size_strb_s")
            self.add_signal(t.ApbPstrbType(self.datawidth), "pstrb_r")
        self.add_signal(t.ApbDataType(self.datawidth), "pwdata_s")
        self.add_signal(t.ApbDataType(self.datawidth), "pwdata_r")
        self.add_signal(t.ApbDataType(self.datawidth), "prdata_s")
        self.add_signal(t.ApbDataType(self.datawidth), "prdata_r")
        self.add_signal(t.ApbEnaType(), "penable_r")
        self.add_signal(t.ApbReadyType(), "pready_s")
        self.add_signal(t.ApbRespType(), "pslverr_s")
        for aspc in self.addrmap:
            self.add_signal(t.ApbSelType(), f"apb_{aspc.name}_sel_s")
            self.add_signal(t.ApbSelType(), f"apb_{aspc.name}_sel_r")
        if self.errirq:
            self.add_signal(LevelIrqType(), "irq_r")

    def get_overview(self):
        """Overview."""
        return self.addrmap.get_overview(minimal=True)

    @staticmethod
    def build_top(**kwargs):
        """Build example top module and return it."""
        return UcdpAhb2apbExampleMod()

    def _resolve_ref(self, ref: AddrRef) -> AddrRef:
        return self.parent.parser(ref)


class UcdpAhb2apbExampleMod(u.AMod):
    """
    Just an Example.
    """

    def _build(self):
        class MyUserType(t.ASecIdType):
            """My AUser Type."""

            title: str = "AHB User Type"
            comment: str = "AHB User Type"

            def _build(self):
                self._add(0, "apps")
                self._add(2, "comm")
                self._add(5, "audio")

        amba5 = t.AmbaProto(name="amba5", ausertype=MyUserType(default=2), has_wstrb=True)
        apb5 = t.AmbaProto(name="ap5", ausertype=MyUserType(default=2), has_wstrb=True)
        apb3 = t.AmbaProto(name="ap3")

        for errirq in (False, True):
            for proto in (t.AMBA3, amba5):
                name = f"u_ahb2apb_{proto.name}_errirq{errirq}".lower()
                ahb2apb = UcdpAhb2apbMod(self, name, proto=proto, errirq=errirq)
                ahb2apb.add_slave("default")
                ahb2apb.add_slave("slv3", proto=t.AMBA3)
                ahb2apb.add_slave("slv5", proto=amba5)

        ahb2apb = UcdpAhb2apbMod(self, "u_odd", proto=amba5, ahb_addrwidth=27, errirq=False, optbw=True)
        ahb2apb.add_slave("foo", proto=apb3)
        ahb2apb.add_slave("bar", size="1KB", proto=apb5)
        ahb2apb.add_slave("baz", size="13kB", proto=apb3)
        # slv.add_addrrange(size="3kB")
