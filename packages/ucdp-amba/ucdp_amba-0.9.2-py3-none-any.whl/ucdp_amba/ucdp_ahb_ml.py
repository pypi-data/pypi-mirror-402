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
Unified Chip Design Platform - AMBA - AHB Multilayer.
"""

from logging import getLogger
from typing import ClassVar

import ucdp as u
from ucdp_addr import AddrMaster, AddrMatrix, AddrRef, AddrSlave

from . import types as t

LOGGER = getLogger(__name__)


class Master(AddrMaster):
    """
    Master.
    """

    proto: t.AmbaProto
    """Protocol Version."""


class Slave(AddrSlave):
    """
    Slave.
    """

    proto: t.AmbaProto
    """Protocol Version."""


class AhbFsmMlType(u.AEnumType):
    """
    FSM Type for AHB Multilayer.
    """

    keytype: u.UintType = u.UintType(3)
    title: str = "AHB ML FSM Type"
    comment: str = "AHB ML FSM Type"

    def _build(self):
        self._add(0, "idle", "No transfer")
        self._add(1, "transfer", "Transfer")
        self._add(2, "transfer_finish", "Transfer Finish (wait for HREADY)")
        self._add(3, "transfer_wait", "Transfer Wait for Grant")
        self._add(4, "error0", "Pre-Error (wait for HREADY)")
        self._add(5, "error1", "1st Error Cycle")
        self._add(6, "error2", "2nd Error Cycle")


class UcdpAhbMlMod(u.ATailoredMod, AddrMatrix):
    """
    AHB Multilayer.

    Multilayer.
    """

    filelists: ClassVar[u.ModFileLists] = (
        u.ModFileList(
            name="hdl",
            gen="full",
            filepaths=("$PRJROOT/{mod.topmodname}/{mod.modname}.sv"),
            template_filepaths=("ucdp_ahb_ml.sv.mako", "sv.mako"),
        ),
    )
    proto: t.AmbaProto = t.AMBA3
    """Default Protocol."""
    is_sub: bool = False
    """Full Address Decoding By Default."""
    addrwidth: int = 32
    datawidth: int = 32

    def _build(self):
        self.add_port(u.ClkRstAnType(), "main_i")

    def add_master(
        self,
        name: str,
        slavenames: u.Names | None = None,
        proto: t.AmbaProto | None = None,
        route: u.Routeable | None = None,
    ) -> Master:
        """
        Add master port named `name` connected to `route`.

        Args:
            name: Name or Pattern ('*' is supported)

        Keyword Args:
            slavenames: Names of slaves to be accessed by this master.
            proto: Protocol.
            route: port to connect this master to.
        """
        self.check_lock()
        proto = proto or self.proto
        master = Master(name=name, proto=proto)
        self._add_master(master, slavenames=slavenames)

        portname = f"ahb_mst_{name}_i"
        title = f"AHB Input {name!r}"
        self.add_port(
            t.AhbMstType(addrwidth=self.addrwidth, datawidth=self.datawidth, proto=proto),
            portname,
            title=title,
            comment=title,
        )
        if route:
            self.con(portname, route)

        return master

    def add_slave(
        self,
        name: str,
        baseaddr: int | str = u.AUTO,
        size: u.Bytes | None = None,
        proto: t.AmbaProto | None = None,
        masternames: u.Names | None = None,
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
            masternames: Names of masters to be accessed by this slave.
            route: APB Slave Port to connect.
            ref: Logical Module connected.
        """
        self.check_lock()
        proto = proto or self.proto
        slave = Slave(name=name, addrdecoder=self, proto=proto, ref=ref)
        self._add_slave(slave, masternames=masternames, baseaddr=baseaddr, size=size)

        portname = f"ahb_slv_{name}_o"
        title = f"AHB Output {name!r}"
        self.add_port(
            t.AhbSlvType(addrwidth=self.addrwidth, datawidth=self.datawidth, proto=proto),
            portname,
            title=title,
            comment=title,
        )
        if route:
            self.con(portname, route)

        return slave

    def _check_proto_comp(self) -> int:
        """Check for Protocol Compatibility."""
        verdict = 0
        for master in self.masters:
            mstname = master.name
            mstproto = master.proto
            for slave in self._master_slaves[master.name]:
                chk = t.check_ahb_proto_pair(mstname, mstproto, slave, self.slaves[slave].proto)
                verdict = max(verdict, chk)
        return verdict

    def _build_dep(self):  # noqa: C901, PLR0912
        self._check_masters_slaves()  # TODO: check for problems and assert
        if self._check_proto_comp() > 1:
            raise AssertionError("Fatal protocol incompatibility detected.")
        self.add_type_consts(t.AhbTransType())
        self.add_type_consts(t.AhbRespType())
        self.add_type_consts(t.AhbSizeType())
        self.add_type_consts(t.AhbBurstType())
        self.add_type_consts(t.AhbWriteType())
        self.add_type_consts(AhbFsmMlType(), name="fsm", item_suffix="st")
        has_exclxfers = max([mst.proto.has_exclxfers for mst in self.masters]) or max(
            [slv.proto.has_exclxfers for slv in self.slaves]
        )
        if has_exclxfers:
            self.add_type_consts(t.AhbHexokType())

        for master in self.masters:
            master_slaves = self._master_slaves[master.name]
            self.add_signal(AhbFsmMlType(), f"fsm_{master.name}_r", comment=f"Master {master.name!r} FSM")
            self.add_signal(u.BitType(), f"mst_{master.name}_new_xfer_s")
            self.add_signal(u.BitType(), f"mst_{master.name}_cont_xfer_s")
            self.add_signal(u.BitType(), f"mst_{master.name}_hready_s")
            self.add_signal(u.BitType(), f"mst_{master.name}_rqstate_s")
            self.add_signal(u.BitType(), f"mst_{master.name}_addr_err_s")
            slv_hprotwidth = 0
            slv_hmasterwidth = 0
            slv_hburst = False
            slv_hmastlock = False
            slv_hnonsec = False
            slv_hauser = False
            for slave in master_slaves:
                slvproto = self.slaves[slave].proto
                slv_hprotwidth = max(slv_hprotwidth, slvproto.hprotwidth)
                slv_hmasterwidth = max(slv_hmasterwidth, slvproto.hmaster_width)
                slv_hburst = slv_hburst or slvproto.has_hburst
                slv_hmastlock = slv_hmastlock or slvproto.has_hmastlock
                slv_hnonsec = slv_hnonsec or slvproto.has_hnonsec
                slv_hauser = slv_hauser or slvproto.ausertype is not None

                self.add_signal(u.BitType(), f"mst_{master.name}_{slave}_sel_s")
                self.add_signal(u.BitType(), f"mst_{master.name}_{slave}_req_r")
                self.add_signal(u.BitType(), f"mst_{master.name}_{slave}_gnt_r")
            self.add_signal(u.BitType(), f"mst_{master.name}_gnt_s")

            mst_hprotwidth = min(master.proto.hprotwidth, slv_hprotwidth)
            mst_hmasterwidth = min(master.proto.hmaster_width, slv_hmasterwidth)
            mstp_type = self.ports[f"ahb_mst_{master.name}_i"].type_
            for subt in mstp_type.values():
                if (subt.orientation == u.BWD) or (subt.name in ["hwdata", "hwstrb", "hwuser"]):
                    continue
                type_ = subt.type_
                if subt.name == "hprot":
                    if slv_hprotwidth == 0:
                        continue
                    type_ = t.AhbProtType(mst_hprotwidth)
                if subt.name == "hmastlock" and not slv_hmastlock:
                    continue
                if subt.name == "hmaster":
                    if slv_hmasterwidth == 0:
                        continue
                    type_ = t.AhbHMastType(mst_hmasterwidth)
                if subt.name == "hburst" and not slv_hburst:
                    continue
                if subt.name == "hnonsec" and not slv_hnonsec:
                    continue
                if subt.name == "hburst" and not slv_hburst:
                    continue
                if subt.name == "hauser" and not slv_hauser:
                    continue
                self.add_signal(type_, f"mst_{master.name}_{subt.name}_s")
                self.add_signal(type_, f"mst_{master.name}_{subt.name}_r")
            self.add_signal(t.AhbWriteType(), f"mst_{master.name}_hwrite_dph_r", comment="data-phase write indicator")

        for slave in self.slaves:
            slave_masters = self._slave_masters[slave.name]
            num_mst = len(slave_masters)
            for master in slave_masters:
                self.add_signal(u.BitType(), f"mst_{master}_{slave.name}_req_s")
                if num_mst > 1:
                    self.add_signal(u.BitType(), f"mst_{master}_{slave.name}_keep_s")
                    self.add_signal(u.BitType(), f"slv_{slave.name}_{master}_gnt_r")
                    self.add_signal(u.BitType(), f"slv_{slave.name}_{master}_sel_s")
                self.add_signal(u.BitType(), f"slv_{slave.name}_{master}_gnt_s")

    @staticmethod
    def build_top(**kwargs):
        """Build example top module and return it."""
        return UcdpAhbMlExampleMod()

    def _resolve_ref(self, ref: AddrRef) -> AddrRef:
        return self.parent.parser(ref)

    def get_overview(self) -> str:
        """Matrix Overview."""
        return AddrMatrix.get_overview(self)


class UcdpAhbMlExampleMod(u.AMod):
    """
    Just an Example Multilayer.

        >>> print(UcdpAhbMlExampleMod().get_inst('u_ml').get_overview())
        | Master > Slave | ram | periph | misc |
        | -------------- | --- | ------ | ---- |
        | ext            | X   |        | X    |
        | dsp            | X   | X      |      |
        <BLANKLINE>
        <BLANKLINE>
        <BLANKLINE>
        * Top:     `None`
        * Defines: `None`
        * Size:    `3932320 KB`
        <BLANKLINE>
        | Addrspace | Type     | Base         | Size                        | Infos | Attributes |
        | --------- | -------- | ------------ | --------------------------- | ----- | ---------- |
        | reserved0 | Reserved | `0x0`        | `536870912x32 (2 GB)`       |       |            |
        | misc      | Slave    | `0x80000000` | `5888x32 (23 KB)`           |       |            |
        | reserved1 | Reserved | `0x80005C00` | `469756160x32 (1834985 KB)` |       |            |
        | ram       | Slave    | `0xF0000000` | `16384x32 (64 KB)`          |       |            |
        | periph    | Slave    | `0xF0010000` | `16384x32 (64 KB)`          |       |            |
        | misc      | Slave    | `0xF0020000` | `8192x32 (32 KB)`           |       |            |
        | reserved2 | Reserved | `0xF0028000` | `67067904x32 (261984 KB)`   |       |            |
        <BLANKLINE>
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

        ahb5f = t.AmbaProto(
            "ahb5f",
            hmaster_width=4,
            hprotwidth=4,
            has_hmastlock=True,
            has_hnonsec=True,
            has_exclxfers=False,
            has_wstrb=True,
            ausertype=MyUserType(default=2),
            wusertype=MyUserType(default=5),
            rusertype=MyUserType(default=0),
            busertype=MyUserType(default=2),
        )
        ahb5v = ahb5f.new(
            name="ahb5v",
            hprotwidth=7,
            hmaster_width=6,
            enh_hmaster=True,
            has_hmastlock=True,
            has_hnonsec=True,
            has_exclxfers=True,
            ausertype=MyUserType(default=2),
            wusertype=MyUserType(default=5),
            rusertype=MyUserType(default=0),
            busertype=MyUserType(default=2),
        )

        ml = UcdpAhbMlMod(self, "u_ml", addrwidth=36, proto=ahb5f)
        ml.add_master("ext")
        ml.add_master("dsp")

        slv = ml.add_slave("ram", masternames=["ext", "dsp"], proto=ahb5v)
        slv.add_addrrange(0xF0000000, size=2**16)

        slv = ml.add_slave("periph", proto=ahb5v)
        slv.add_addrrange(0xF0010000, size="64kb")

        slv = ml.add_slave("misc", proto=ahb5v)
        slv.add_addrrange(size="32k")
        slv.add_addrrange(0x80000000, size="23k")

        # slv = ml.add_slave("ext", masternames=["ext", "dsp"])
        # slv.add_addrrange(0x0, size=2**32)
        # slv.add_exclude_addrrange(0xF0000000, size=2**18)

        ml.add_interconnects("dsp", "periph")
        ml.add_interconnects("ext", "misc")
