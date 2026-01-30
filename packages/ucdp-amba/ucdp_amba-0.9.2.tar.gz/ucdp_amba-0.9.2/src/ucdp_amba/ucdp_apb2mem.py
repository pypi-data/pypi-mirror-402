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
Unified Chip Design Platform - AMBA - APB2MEM.
"""

import math
from typing import ClassVar

import ucdp as u
from icdutil.num import is_power_of2
from ucdp_addr.addrspace import Addrspace
from ucdp_glbl.mem import Addressing, MemIoType

from . import types as t


class UcdpApb2memMod(u.ATailoredMod):
    """APB to MEMio Converter."""

    datawidth: int = 32
    """Data Width in Bits."""
    addrwidth: int = 32
    """Address Width in Bits."""
    mem_addrwidth: int | None = None
    """Memory Address Width, if different from `addrwidth`"""
    addressing: Addressing = "data"
    """Addressing-Width."""
    proto: t.AmbaProto = t.AMBA3
    """AMBA Protocol Specifier."""

    filelists: ClassVar[u.ModFileLists] = (
        u.ModFileList(
            name="hdl",
            gen="full",
            filepaths=("$PRJROOT/{mod.topmodname}/{mod.modname}.sv"),
            template_filepaths=("ucdp_apb2mem.sv.mako", "sv.mako"),
        ),
    )

    def _build(self):
        self.add_port(self.apbslvtype, "apb_slv_i", title="APB Slave Input")
        self.add_port(self.memiotype, "mem_o", title="Memory Interface")

    @property
    def apbslvtype(self) -> t.ApbSlvType:
        """APB Slave Type."""
        return t.ApbSlvType(proto=self.proto, addrwidth=self.addrwidth, datawidth=self.datawidth)

    @property
    def memiotype(self) -> MemIoType:
        """Memory IO-Type."""
        mem_addrwidth = self.mem_addrwidth or self.addrwidth
        return MemIoType(
            addrwidth=mem_addrwidth, datawidth=self.datawidth, writable=True, err=True, addressing=self.addressing
        )

    @property
    def addrslice(self) -> u.Slice:
        """Address Slice To Extract Memory Address From Bus Address."""
        if self.addressing == "data":
            if not is_power_of2(self.datawidth):
                raise ValueError("addressing='data' requires datawidth power of 2")
            right = int(math.log2(self.datawidth / 8))
        else:
            right = 0

        return u.Slice(width=self.memiotype.addrwidth, right=right)

    @staticmethod
    def build_top(**kwargs):
        """Build example top module and return it."""
        return UcdpApb2MemExampleMod()

    @classmethod
    def from_memiotype(cls, parent: u.BaseMod, name: str, memiotype: MemIoType, **kwargs) -> "UcdpApb2memMod":
        """Create for `memiotype`."""
        inst = cls(
            parent,
            name,
            mem_addrwidth=memiotype.addrwidth,
            datawidth=memiotype.datawidth,
            addressing=memiotype.addressing,
            **kwargs,
        )
        if memiotype != inst.memiotype:
            raise ValueError(f"Cannot construct module for memiotype ({memiotype} != {inst.memiotype})")
        return inst

    def get_overview(self) -> str:
        """Overview."""
        mem_addrwidth = self.mem_addrwidth or self.addrwidth
        addressing = f"Addressing-Width: {self.addressing}"
        if self.addressing == "data":
            addrspace = Addrspace(depth=2**mem_addrwidth, width=self.datawidth)
        else:
            addrspace = Addrspace(size=2**mem_addrwidth, width=self.datawidth)
        size = f"Size:             {addrspace.depth}x{addrspace.width} ({addrspace.size})"
        return f"{addressing}\n{size}"


class UcdpApb2MemExampleMod(u.AMod):
    """Example Converter."""

    def _build(self):
        for datawidth in (8, 16, 32):
            for addrwidth in (16, 24, 32):
                for mem_addrwidth in ("", 8, addrwidth):
                    for addressing in ("byte", "data"):
                        name = f"u_d{datawidth}_a{addrwidth}_m{mem_addrwidth}_{addressing}"
                        UcdpApb2memMod(
                            self,
                            name,
                            datawidth=datawidth,
                            addrwidth=addrwidth,
                            mem_addrwidth=mem_addrwidth or None,
                            addressing=addressing,
                        )

                        name = f"u_d{datawidth}_a{addrwidth}_m{mem_addrwidth}_{addressing}_io"
                        memiotype = MemIoType(
                            datawidth=datawidth,
                            addrwidth=mem_addrwidth or addrwidth,
                            addressing=addressing,
                            writable=True,
                            err=True,
                        )
                        UcdpApb2memMod.from_memiotype(self, name, memiotype, addrwidth=addrwidth)
