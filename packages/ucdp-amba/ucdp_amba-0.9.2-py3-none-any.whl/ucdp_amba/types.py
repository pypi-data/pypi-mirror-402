# MIT License
#
# Copyright (c) 2025-2026 nbiotcloud
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

AMBA Type Definitions.

Mainly these types are needed:

* :any:`AhbMstType`
* :any:`AhbSlvType`
* :any:`ApbSlvType`
"""

from logging import getLogger

import ucdp as u

LOGGER = getLogger(__name__)

LEGAL_AHB_ADDR_WIDTH = range(10, 65)
LEGAL_AHB_DATA_WIDTH = [8, 16, 32, 64, 128, 256, 512, 1024]
LEGAL_AHB_PROT_WIDTH = [0, 4, 7]
LEGAL_APB_ADDR_WIDTH = range(33)
LEGAL_APB_DATA_WIDTH = [8, 16, 32]


class ASecIdType(u.AEnumType):
    """
    Base of all Security ID Types.
    """

    keytype: u.UintType = u.UintType(4)

    def get_subset_type(self, excludes: u.Names | None = None):
        """Return variant with element excluded."""
        excludes = u.split(excludes)
        return self.new(filter_=lambda item: item.value not in excludes)


class AhbProtType(u.UintType):
    """
    AHB Protection.

    >>> AhbProtType().width
    4
    >>> AhbProtType(width=7).width
    7

    Width is checked for legal values:

    >>> t = AhbProtType(width=5)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for AHB hprotwidth: 5. Legal values are [0, 4, 7]
    """

    title: str = "AHB Transfer Protection"
    comment: str = "AHB Transfer Protection"

    def __init__(self, width=4, **kwargs):
        if width not in LEGAL_AHB_PROT_WIDTH:
            raise ValueError(f"Illegal value for AHB hprotwidth: {width}. Legal values are {LEGAL_AHB_PROT_WIDTH}")
        super().__init__(width=width, default=3, **kwargs)


class AhbHMastType(u.UintType):
    """
    AHB Master ID for Exclusive Transfers.
    """

    title: str = "AHB Master ID"
    comment: str = "AHB Master ID"

    def __init__(self, width=4, **kwargs):
        super().__init__(width=width, **kwargs)


class AmbaProto(u.AConfig):
    """
    Amba Protocol Version.

    Specification of optional/conditional Protocol Features.
    Used for both, AHB and APB. However, features not defined for APB are simply ignored.

    hprotwidth (int): Bitwidth for AHB hprot signal
    has_hburst(bool): Determines whether AHB hburst signal exists (otherwise INCR only)
    has_hmastlock (bool): Determines whether AHB hmastlock exists
    has_hnonsec (bool): Determines whether AHB hnonsec signal exists
    has_exclxfers (bool): Determines whether AHB signals for exclusive transfers exist (hexcl, hmaster, hexokay)
    hmaster_width (int): Bitwidth for AHB hmaster signal
    enh_hmaster )bool): Determines whether hmaster signal is enhanced with master index on an interconnect
    has_wstrb (bool): Determines whether AHB hwstrb or APB pstrb write strobe signals exist
    has_pprot (bool): Determines whether APB pprot signal exists
    has_pnse (bool):  Determines whether APB uses Realm Management Extensions
    ausertype (AEnumType|UintType): Type used for AHB hauser or APB pauser
    wusertype (AEnumType|UintType): Type used for AHB hwuser or APB pwuser signal
    rusertype (AEnumType|UintType): Type used for AHB hruser or APB pruser signal
    busertype (AEnumType|UintType): Type used for AHB hbuser or APB pbuser signal
    """

    hprotwidth: int = 4
    hmaster_width: int = 0
    enh_hmaster: bool = False
    has_hburst: bool = True
    has_hmastlock: bool = False
    has_hnonsec: bool = False
    has_exclxfers: bool = False
    has_wstrb: bool = False
    has_pprot: bool = False
    has_pnse: bool = False
    ausertype: u.AEnumType | u.UintType | None = None
    wusertype: u.AEnumType | u.UintType | None = None
    rusertype: u.AEnumType | u.UintType | None = None
    busertype: u.AEnumType | u.UintType | None = None

    @property
    def hprottype(self) -> AhbProtType | None:
        """Protocol has HPROT signal."""
        if self.hprotwidth:
            return AhbProtType(width=self.hprotwidth)
        return None

    @property
    def hmaster_type(self) -> AhbHMastType | None:
        """Protocol has HMASTER signal."""
        if self.hmaster_width:
            return AhbHMastType(width=self.hmaster_width)
        return None


AMBA3 = AmbaProto(name="amba3")


class AhbMstType(u.AStructType):
    """
    From AHB Master.

    Keyword Args:
        proto (Protocol): Protocol feature set selection.

    The default type:

    >>> for item in AhbMstType().values(): item
    StructItem('htrans', AhbTransType(), doc=Doc(title='AHB Transfer Type', ...))
    StructItem('haddr', AhbAddrType(32), doc=Doc(title='AHB Bus Address', ...))
    StructItem('hwrite', AhbWriteType(), doc=Doc(title='AHB Write Enable', ...))
    StructItem('hsize', AhbSizeType(), doc=Doc(title='AHB Size', ...))
    StructItem('hburst', AhbBurstType(), doc=Doc(title='AHB Burst Type', ...))
    StructItem('hprot', AhbProtType(4, default=3), doc=Doc(title='AHB Transfer Protection', ...))
    StructItem('hwdata', AhbDataType(32), doc=Doc(title='AHB Data', ...))
    StructItem('hready', AhbReadyType(), orientation=BWD, doc=Doc(title='AHB Transfer Done', ...))
    StructItem('hresp', AhbRespType(), orientation=BWD, doc=Doc(title='AHB Response Error', ...))
    StructItem('hrdata', AhbDataType(32), orientation=BWD, doc=Doc(title='AHB Data', ...))

    With all extras:

    >>> class AuserType(ASecIdType):
    ...     def _build(self):
    ...         self._add(0, "apps")
    ...         self._add(2, "comm")
    ...         self._add(5, "audio")
    >>> ahb5 = AmbaProto("AHB5", ausertype=AuserType(default=2), hmaster_width=3,\
    has_hmastlock=True, has_hnonsec=True, has_exclxfers=True, has_wstrb=True)

    >>> for item in AhbMstType(proto=ahb5).values(): item
    StructItem('htrans', AhbTransType(), doc=Doc(title='AHB Transfer Type', ...))
    StructItem('haddr', AhbAddrType(32), doc=Doc(title='AHB Bus Address', ...))
    StructItem('hauser', AuserType(default=2), doc=Doc(title='AHB Address User Channel', ...))
    StructItem('hwrite', AhbWriteType(), doc=Doc(title='AHB Write Enable', ...))
    StructItem('hsize', AhbSizeType(), doc=Doc(title='AHB Size', ...))
    StructItem('hburst', AhbBurstType(), doc=Doc(title='AHB Burst Type', ...))
    StructItem('hprot', AhbProtType(4, default=3), doc=Doc(title='AHB Transfer Protection', ...))
    StructItem('hnonsec', AhbNonsecType(), doc=Doc(title='AHB Secure Transfer', ...))
    StructItem('hmastlock', AhbMastlockType(), doc=Doc(title='AHB Locked Sequence Enable', ...))
    StructItem('hwdata', AhbDataType(32), doc=Doc(title='AHB Data', ...))
    StructItem('hwstrb', AhbWstrbType(4), doc=Doc(title='AHB Write Strobe', ...))
    StructItem('hexcl', AhbExclType(), doc=Doc(title='AHB Exclusive Transfer', ...))
    StructItem('hmaster', AhbHMastType(3), doc=Doc(title='AHB Master ID', ...))
    StructItem('hready', AhbReadyType(), orientation=BWD, doc=Doc(title='AHB Transfer Done', ...))
    StructItem('hresp', AhbRespType(), orientation=BWD, doc=Doc(title='AHB Response Error', ...))
    StructItem('hexokay', AhbHexokType(), orientation=BWD, doc=Doc(title='AHB Exclusive Response', ...))
    StructItem('hrdata', AhbDataType(32), orientation=BWD, doc=Doc(title='AHB Data', ...))

    Both protocol versions are not connectable:

    >>> AhbMstType().is_connectable(AhbMstType(proto=ahb5))
    False

    But casting is allowed:

    >>> for item in AhbMstType().cast(AhbMstType(proto=ahb5)): item
    ('', '')
    ('htrans', 'htrans')
    ('haddr', 'haddr')
    ('hwrite', 'hwrite')
    ('hsize', 'hsize')
    ('hburst', 'hburst')
    ('hprot', 'hprot')
    ('hwdata', 'hwdata')
    ('hready', 'hready')
    ('hresp', 'hresp')
    ('hrdata', 'hrdata')

    It is also not allowed to connect Master and Slave:

    >>> AhbMstType().is_connectable(AhbSlvType())
    False

    But casting is allowed in all ways.

    >>> len(tuple(AhbMstType().cast(AhbSlvType())))
    12
    >>> len(tuple(AhbMstType(proto=ahb5).cast(AhbSlvType())))
    11
    >>> len(tuple(AhbMstType(proto=ahb5).cast(AhbSlvType(proto=ahb5))))
    12

    Without HPROT:

    >>> ahbp = AmbaProto("AHB3", hprotwidth=0)

    >>> for item in AhbMstType(proto=ahbp).values(): item
    StructItem('htrans', AhbTransType(), doc=Doc(title='AHB Transfer Type', ...))
    StructItem('haddr', AhbAddrType(32), doc=Doc(title='AHB Bus Address', ...))
    StructItem('hwrite', AhbWriteType(), doc=Doc(title='AHB Write Enable', ...))
    StructItem('hsize', AhbSizeType(), doc=Doc(title='AHB Size', ...))
    StructItem('hburst', AhbBurstType(), doc=Doc(title='AHB Burst Type', ...))
    StructItem('hwdata', AhbDataType(32), doc=Doc(title='AHB Data', ...))
    StructItem('hready', AhbReadyType(), orientation=BWD, doc=Doc(title='AHB Transfer Done', ...))
    StructItem('hresp', AhbRespType(), orientation=BWD, doc=Doc(title='AHB Response Error', ...))
    StructItem('hrdata', AhbDataType(32), orientation=BWD, doc=Doc(title='AHB Data', ...))
    """

    title: str = "AHB Master"
    comment: str = "AHB Master"
    proto: AmbaProto = AMBA3
    addrwidth: int = 32
    datawidth: int = 32

    def _build(self):  # noqa: C901
        # FWD
        self._add("htrans", AhbTransType())
        self._add("haddr", AhbAddrType(self.addrwidth))
        if ausertype := self.proto.ausertype:
            auserdoc = "AHB Address User Channel"
            self._add("hauser", ausertype, title=auserdoc, comment=auserdoc)
        if wusertype := self.proto.wusertype:
            wuserdoc = "AHB Write Data User Channel"
            self._add("hwuser", wusertype, title=wuserdoc, comment=wuserdoc)
        self._add("hwrite", AhbWriteType())
        self._add("hsize", AhbSizeType())
        if self.proto.has_hburst:
            self._add("hburst", AhbBurstType())
        if hprottype := self.proto.hprottype:
            self._add("hprot", hprottype)
        if self.proto.has_hnonsec:
            self._add("hnonsec", AhbNonsecType())
        if self.proto.has_hmastlock:
            self._add("hmastlock", AhbMastlockType())
        self._add("hwdata", AhbDataType(self.datawidth))
        if self.proto.has_wstrb:
            self._add("hwstrb", AhbWstrbType(self.datawidth))
        if self.proto.has_exclxfers:
            self._add("hexcl", AhbExclType())
        if hmasttype := self.proto.hmaster_type:
            self._add("hmaster", hmasttype)
        # BWD
        self._add("hready", AhbReadyType(), u.BWD)
        self._add("hresp", AhbRespType(), u.BWD)
        if self.proto.has_exclxfers:
            self._add("hexokay", AhbHexokType(), u.BWD)
        self._add("hrdata", AhbDataType(self.datawidth), u.BWD)
        if rusertype := self.proto.rusertype:
            ruserdoc = "AHB Read Data User Channel"
            self._add("hruser", rusertype, title=ruserdoc, comment=ruserdoc, orientation=u.BWD)
        if busertype := self.proto.busertype:
            buserdoc = "AHB Read Response User Channel"
            self._add("hbuser", busertype, title=buserdoc, comment=buserdoc, orientation=u.BWD)

    def cast(self, other):
        """
        How to cast an assign of type `self` from a value of type `other`.

        `self = cast(other)`
        """
        if isinstance(other, AhbMstType) and self.proto != other.proto:
            # Drive a Mst with Mst signals
            yield "", ""
            yield "htrans", "htrans"
            yield "haddr", "haddr"
            # never use hauser
            yield "hwrite", "hwrite"
            yield "hsize", "hsize"
            yield "hburst", "hburst"
            yield "hprot", "hprot"
            yield "hwdata", "hwdata"
            # BWD
            yield "hready", "hready"
            yield "hresp", "hresp"
            yield "hrdata", "hrdata"
        elif isinstance(other, AhbSlvType):
            # Drive a Mst with Slv signals
            yield "", ""
            yield "htrans", "htrans"
            yield "haddr", "haddr"
            if self.proto.ausertype == other.proto.ausertype:
                yield "hauser", "hauser"
            yield "hwrite", "hwrite"
            yield "hsize", "hsize"
            yield "hburst", "hburst"
            yield "hprot", "hprot"
            yield "hwdata", "hwdata"
            # BWD
            yield "hready", "hreadyout"
            # yield "hready", "hready" TODO: @djakschik, extend cast support
            yield "hresp", "hresp"
            yield "hrdata", "hrdata"
        else:
            return None


class AhbSlvType(u.AStructType):
    """
    To AHB Slave.

    Keyword Args:
        proto (Protocol): Protocol feature set selection.

    The default type:

    >>> for item in AhbSlvType().values(): item
    StructItem('hsel', AhbSelType(), doc=Doc(title='AHB Slave Select', ...))
    StructItem('haddr', AhbAddrType(32), doc=Doc(title='AHB Bus Address', ...))
    StructItem('hwrite', AhbWriteType(), doc=Doc(title='AHB Write Enable', ...))
    StructItem('htrans', AhbTransType(), doc=Doc(title='AHB Transfer Type', ...))
    StructItem('hsize', AhbSizeType(), doc=Doc(title='AHB Size', ...))
    StructItem('hburst', AhbBurstType(), doc=Doc(title='AHB Burst Type', ...))
    StructItem('hprot', AhbProtType(4, default=3), doc=Doc(title='AHB Transfer Protection', ...))
    StructItem('hwdata', AhbDataType(32), doc=Doc(title='AHB Data', ...))
    StructItem('hready', AhbReadyType(), doc=Doc(title='AHB Transfer Done to Slave', ...))
    StructItem('hreadyout', AhbReadyType(), orientation=BWD, doc=Doc(title='AHB Transfer Done from Slave', ...))
    StructItem('hresp', AhbRespType(), orientation=BWD, doc=Doc(title='AHB Response Error', ...))
    StructItem('hrdata', AhbDataType(32), orientation=BWD, doc=Doc(title='AHB Data', ...))

    With `hauser`:

    >>> class AuserType(ASecIdType):
    ...     def _build(self):
    ...         self._add(0, "apps")
    ...         self._add(2, "comm")
    ...         self._add(5, "audio")
    >>> ahb5 = AmbaProto("AHB5", ausertype=AuserType(default=2))

    >>> for item in AhbSlvType(proto=ahb5).values(): item
    StructItem('hsel', AhbSelType(), doc=Doc(title='AHB Slave Select', ...))
    StructItem('haddr', AhbAddrType(32), doc=Doc(title='AHB Bus Address', ...))
    StructItem('hauser', AuserType(default=2), doc=Doc(title='AHB Address User Channel', ...))
    StructItem('hwrite', AhbWriteType(), doc=Doc(title='AHB Write Enable', ...))
    StructItem('htrans', AhbTransType(), doc=Doc(title='AHB Transfer Type', ...))
    StructItem('hsize', AhbSizeType(), doc=Doc(title='AHB Size', ...))
    StructItem('hburst', AhbBurstType(), doc=Doc(title='AHB Burst Type', ...))
    StructItem('hprot', AhbProtType(4, default=3), doc=Doc(title='AHB Transfer Protection', ...))
    StructItem('hwdata', AhbDataType(32), doc=Doc(title='AHB Data', ...))
    StructItem('hready', AhbReadyType(), doc=Doc(title='AHB Transfer Done to Slave', ...))
    StructItem('hreadyout', AhbReadyType(), orientation=BWD, doc=Doc(title='AHB Transfer Done from Slave', ...))
    StructItem('hresp', AhbRespType(), orientation=BWD, doc=Doc(title='AHB Response Error', ...))
    StructItem('hrdata', AhbDataType(32), orientation=BWD, doc=Doc(title='AHB Data', ...))

    Both protocol versions are not connectable:

    >>> AhbSlvType().is_connectable(AhbSlvType(proto=ahb5))
    False

    But casting is allowed:

    >>> for item in AhbSlvType().cast(AhbSlvType(proto=ahb5)): item
    ('', '')
    ('hsel', 'hsel')
    ('haddr', 'haddr')
    ('hwrite', 'hwrite')
    ('htrans', 'htrans')
    ('hsize', 'hsize')
    ('hburst', 'hburst')
    ('hprot', 'hprot')
    ('hwdata', 'hwdata')
    ('hready', 'hready')
    ('hreadyout', 'hreadyout')
    ('hresp', 'hresp')
    ('hrdata', 'hrdata')

    It is also not allowed to connect Master and Slave:

    >>> AhbSlvType().is_connectable(AhbMstType())
    False

    But casting is allowed in all ways.

    >>> len(tuple(AhbSlvType().cast(AhbMstType())))
    14
    >>> len(tuple(AhbSlvType(proto=ahb5).cast(AhbMstType())))
    13
    >>> len(tuple(AhbSlvType(proto=ahb5).cast(AhbMstType(proto=ahb5))))
    14

    With wider HPROT:

    >>> ahbp = AmbaProto("AHB5", hprotwidth=7)

    >>> for item in AhbSlvType(proto=ahbp).values(): item
    StructItem('hsel', AhbSelType(), doc=Doc(title='AHB Slave Select', ...))
    StructItem('haddr', AhbAddrType(32), doc=Doc(title='AHB Bus Address', ...))
    StructItem('hwrite', AhbWriteType(), doc=Doc(title='AHB Write Enable', ...))
    StructItem('htrans', AhbTransType(), doc=Doc(title='AHB Transfer Type', ...))
    StructItem('hsize', AhbSizeType(), doc=Doc(title='AHB Size', ...))
    StructItem('hburst', AhbBurstType(), doc=Doc(title='AHB Burst Type', ...))
    StructItem('hprot', AhbProtType(7, default=3), doc=Doc(title='AHB Transfer Protection', ...))
    StructItem('hwdata', AhbDataType(32), doc=Doc(title='AHB Data', ...))
    StructItem('hready', AhbReadyType(), doc=Doc(title='AHB Transfer Done to Slave', ...))
    StructItem('hreadyout', AhbReadyType(), orientation=BWD, doc=Doc(title='AHB Transfer Done from Slave', ...))
    StructItem('hresp', AhbRespType(), orientation=BWD, doc=Doc(title='AHB Response Error', ...))
    StructItem('hrdata', AhbDataType(32), orientation=BWD, doc=Doc(title='AHB Data', ...))

    """

    title: str = "AHB Slave"
    comment: str = "AHB Slave"
    proto: AmbaProto = AMBA3
    addrwidth: int = 32
    datawidth: int = 32

    def _build(self):  # noqa: C901
        # FWD
        self._add("hsel", AhbSelType())
        self._add("haddr", AhbAddrType(self.addrwidth))
        if ausertype := self.proto.ausertype:
            auserdoc = "AHB Address User Channel"
            self._add("hauser", ausertype, title=auserdoc, comment=auserdoc)
        if wusertype := self.proto.wusertype:
            wuserdoc = "AHB Write Data User Channel"
            self._add("hwuser", wusertype, title=wuserdoc, comment=wuserdoc)
        self._add("hwrite", AhbWriteType())
        self._add("htrans", AhbTransType())
        self._add("hsize", AhbSizeType())
        if self.proto.has_hburst:
            self._add("hburst", AhbBurstType())
        if self.proto.hprottype:
            self._add("hprot", self.proto.hprottype)
        if self.proto.has_hnonsec:
            self._add("hnonsec", AhbNonsecType())
        if self.proto.has_hmastlock:
            self._add("hmastlock", AhbMastlockType())
        self._add("hwdata", AhbDataType(self.datawidth))
        if self.proto.has_wstrb:
            self._add("hwstrb", AhbWstrbType(self.datawidth))
        title: str = "AHB Transfer Done to Slave"
        self._add("hready", AhbReadyType(), title=title, comment=title)
        if self.proto.has_exclxfers:
            self._add("hexcl", AhbExclType())
        if hmasttype := self.proto.hmaster_type:
            self._add("hmaster", hmasttype)
        # BWD
        title: str = "AHB Transfer Done from Slave"
        self._add("hreadyout", AhbReadyType(), u.BWD, title=title, comment=title)
        self._add("hresp", AhbRespType(), u.BWD)
        if self.proto.has_exclxfers:
            self._add("hexokay", AhbHexokType(), u.BWD)
        self._add("hrdata", AhbDataType(self.datawidth), u.BWD)
        if rusertype := self.proto.rusertype:
            ruserdoc = "AHB Read Data User Channel"
            self._add("hruser", rusertype, title=ruserdoc, comment=ruserdoc, orientation=u.BWD)
        if busertype := self.proto.busertype:
            buserdoc = "AHB Read Response User Channel"
            self._add("hbuser", busertype, title=buserdoc, comment=buserdoc, orientation=u.BWD)

    def cast(self, other):
        """
        How to cast an assign of type `self` from a value of type `other`.

        `self = cast(other)`
        """
        if isinstance(other, AhbSlvType) and self.proto != other.proto:
            # Drive a Slv with Slv signals
            yield "", ""
            yield "hsel", "hsel"
            yield "haddr", "haddr"
            # never use hauser
            yield "hwrite", "hwrite"
            yield "htrans", "htrans"
            yield "hsize", "hsize"
            yield "hburst", "hburst"
            yield "hprot", "hprot"
            yield "hwdata", "hwdata"
            yield "hready", "hready"
            # BWD
            yield "hreadyout", "hreadyout"
            yield "hresp", "hresp"
            yield "hrdata", "hrdata"
        elif isinstance(other, AhbMstType):
            # Drive a Slv with Mst signals
            yield "", ""
            yield "hsel", "ternary(htrans > '1b0', '1b1', '1b0')"
            yield "haddr", "haddr"
            if self.proto.ausertype == other.proto.ausertype:
                yield "hauser", "hauser"
            yield "hwrite", "hwrite"
            yield "htrans", "htrans"
            yield "hsize", "hsize"
            yield "hburst", "hburst"
            yield "hprot", "hprot"
            yield "hwdata", "hwdata"
            yield "hready", u.const("1'b1")
            # BWD
            yield "hreadyout", "hready"
            yield "hresp", "hresp"
            yield "hrdata", "hrdata"
        else:
            return None


class AhbSelType(u.BitType):
    """AHB Select."""

    title: str = "AHB Slave Select"
    comment: str = "AHB Slave Select"


class AhbAddrType(u.UintType):
    """
    Address.

    >>> AhbAddrType().width
    32
    >>> AhbAddrType(width=16).width
    16

    Checked for valid width:
    >>> t = AhbAddrType(width=9)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for AHB addrwidth: 9.Legal values are between 10 and 64.
    """

    title: str = "AHB Bus Address"
    comment: str = "AHB Bus Address"

    def __init__(self, width=32, **kwargs):
        if width not in LEGAL_AHB_ADDR_WIDTH:
            raise ValueError(
                f"Illegal value for AHB addrwidth: {width}."
                f"Legal values are between {LEGAL_AHB_ADDR_WIDTH[0]} and {LEGAL_AHB_ADDR_WIDTH[-1]}."
            )
        super().__init__(width=width, **kwargs)


class AhbDataType(u.UintType):
    """
    AHB Data.

    >>> AhbDataType().width
    32
    >>> AhbDataType(width=64).width
    64

    Data width is checked for legal values:

    >>> t = AhbDataType(width=57)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for AHB datawidth: 57. Legal values are [8, 16, 32, 64, 128, 256, 512, 1024]
    """

    title: str = "AHB Data"
    comment: str = "AHB Data"

    def __init__(self, width=32, **kwargs):
        if width not in LEGAL_AHB_DATA_WIDTH:
            raise ValueError(f"Illegal value for AHB datawidth: {width}. Legal values are {LEGAL_AHB_DATA_WIDTH}")
        super().__init__(width=width, **kwargs)


class AhbTransType(u.AEnumType):
    """
    AHB Transfer Type.

    >>> for item in AhbTransType().values(): item
    EnumItem(0, 'idle', doc=Doc(title='No transfer'))
    EnumItem(1, 'busy', doc=Doc(title='Idle cycle within transfer'))
    EnumItem(2, 'nonseq', doc=Doc(title='Single transfer or first transfer of a burst'))
    EnumItem(3, 'seq', doc=Doc(title='Consecutive transfers of a burst'))
    """

    keytype: u.UintType = u.UintType(2)
    title: str = "AHB Transfer Type"
    comment: str = "AHB Transfer Type"

    def _build(self):
        self._add(0, "idle", "No transfer")
        self._add(1, "busy", "Idle cycle within transfer")
        self._add(2, "nonseq", "Single transfer or first transfer of a burst")
        self._add(3, "seq", "Consecutive transfers of a burst")


class AhbSizeType(u.AEnumType):
    """
    AHB Size Type.

    >>> for item in AhbSizeType().values(): item
    EnumItem(0, 'byte', doc=Doc(title='Byte', descr='8 bits'))
    EnumItem(1, 'halfword', doc=Doc(title='Halfword', descr='16 bits'))
    EnumItem(2, 'word', doc=Doc(title='Word', descr='32 bits'))
    EnumItem(3, 'doubleword', doc=Doc(title='Doubleword', descr='64 bits'))
    ...
    """

    keytype: u.UintType = u.UintType(3)
    title: str = "AHB Size"
    comment: str = "AHB Size"

    def _build(self):
        self._add(0, "byte", "Byte", descr="8 bits")
        self._add(1, "halfword", "Halfword", descr="16 bits")
        self._add(2, "word", "Word", descr="32 bits")
        self._add(3, "doubleword", "Doubleword", descr="64 bits")
        self._add(4, "fourword", "4-word", descr="128 bits")
        self._add(5, "eightword", "8-word", descr="256 bits")
        self._add(6, "sixteenword", "16-word", descr="512 bits")
        self._add(7, "kilobit", "32-word", descr="1024 bits")


class AhbBurstType(u.AEnumType):
    """
    AHB Burst Type.

    >>> for item in AhbBurstType().values(): item
    EnumItem(0, 'single', doc=Doc(title='Single transfer'))
    EnumItem(1, 'incr', doc=Doc(title='Incrementing burst of unspecified length'))
    EnumItem(2, 'wrap4', doc=Doc(title='4-beat wrapping burst'))
    EnumItem(3, 'incr4', doc=Doc(title='4-beat incrementing burst'))
    EnumItem(4, 'wrap8', doc=Doc(title='8-beat wrapping burst'))
    EnumItem(5, 'incr8', doc=Doc(title='8-beat incrementing burst'))
    EnumItem(6, 'wrap16', doc=Doc(title='16-beat wrapping burst'))
    EnumItem(7, 'incr16', doc=Doc(title='16-beat incrementing burst'))
    """

    keytype: u.UintType = u.UintType(3)
    title: str = "AHB Burst Type"
    comment: str = "AHB Burst Type"

    def _build(self):
        self._add(0, "single", "Single transfer")
        self._add(1, "incr", "Incrementing burst of unspecified length")
        self._add(2, "wrap4", "4-beat wrapping burst")
        self._add(3, "incr4", "4-beat incrementing burst")
        self._add(4, "wrap8", "8-beat wrapping burst")
        self._add(5, "incr8", "8-beat incrementing burst")
        self._add(6, "wrap16", "16-beat wrapping burst")
        self._add(7, "incr16", "16-beat incrementing burst")


class AhbWriteType(u.AEnumType):
    """
    AHB Write Type.

    >>> for item in AhbWriteType().values(): item
    EnumItem(0, 'read', doc=Doc(title='Read operation'))
    EnumItem(1, 'write', doc=Doc(title='Write operation'))
    """

    keytype: u.BitType = u.BitType()
    title: str = "AHB Write Enable"
    comment: str = "AHB Write Enable"

    def _build(self):
        self._add(0, "read", "Read operation")
        self._add(1, "write", "Write operation")


class AhbWstrbType(u.UintType):
    """
    AHB Write Strobe.

    Write strobe width is derived directly from data width.
    >>> AhbWstrbType().width
    4

    Data width is checked for legal values:
    >>> t = AhbWstrbType(42)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for AHB datawidth: 42. Legal values are [8, 16, 32, 64, 128, 256, 512, 1024]
    """

    title: str = "AHB Write Strobe"
    comment: str = "AHB Write Strobe"

    def __init__(self, datawidth=32, **kwargs):
        if datawidth not in LEGAL_AHB_DATA_WIDTH:
            raise ValueError(f"Illegal value for AHB datawidth: {datawidth}. Legal values are {LEGAL_AHB_DATA_WIDTH}")
        super().__init__(width=datawidth // 8, **kwargs)


class AhbNonsecType(u.AEnumType):
    """
    AHB Secure Transfer Type.
    """

    keytype: u.BitType = u.BitType()
    title: str = "AHB Secure Transfer"
    comment: str = "AHB Secure Transfer"

    def _build(self):
        self._add(0, "sec", "Secure Transfer")
        self._add(1, "nonsec", "Nonsecure Transfer")


class AhbMastlockType(u.AEnumType):
    """
    AHB Master Lock Type.
    """

    keytype: u.BitType = u.BitType()
    title: str = "AHB Locked Sequence Enable"
    comment: str = "AHB Locked Sequence Enable"

    def _build(self):
        self._add(0, "norm", "Normal sequence")
        self._add(1, "locked", "Locked sequence")


class AhbRespType(u.AEnumType):
    """
    AHB Response Type.

    >>> for item in AhbRespType().values(): item
    EnumItem(0, 'okay', doc=Doc(title='OK'))
    EnumItem(1, 'error', doc=Doc(title='Error'))
    """

    keytype: u.BitType = u.BitType()
    title: str = "AHB Response Error"
    comment: str = "AHB Response Error"

    def _build(self):
        self._add(0, "okay", "OK")
        self._add(1, "error", "Error")


class AhbHexokType(u.AEnumType):
    """AHB Hexokay Type."""

    keytype: u.BitType = u.BitType()
    title: str = "AHB Exclusive Response"
    comment: str = "AHB Exclusive Response"

    def _build(self):
        self._add(0, "error", "Error")
        self._add(1, "okay", "OK")


class AhbReadyType(u.AEnumType):
    """
    AHB Ready Type.

    >>> for item in AhbReadyType().values(): item
    EnumItem(0, 'busy', doc=Doc(title='Ongoing'))
    EnumItem(1, 'done', doc=Doc(title='Done'))
    """

    keytype: u.BitType = u.BitType(default=1)
    title: str = "AHB Transfer Done"
    comment: str = "AHB Transfer Done"

    def _build(self):
        self._add(0, "busy", "Ongoing")
        self._add(1, "done", "Done")


class AhbExclType(u.AEnumType):
    """
    AHB Exclusive Transfer Type.
    """

    keytype: u.BitType = u.BitType(default=1)
    title: str = "AHB Exclusive Transfer"
    comment: str = "AHB Exclusive Transfer"

    def _build(self):
        self._add(0, "norm", "Normal")
        self._add(1, "excl", "Exclusive")


################################################################################################
##   APB PRotocol Related
################################################################################################


class ApbSlvType(u.AStructType):
    """
    To APB Slave.

    Keyword Args:
        proto (Protocol): Protocol feature set selection.

    The default type:

    >>> for item in ApbSlvType().values(): item
    StructItem('paddr', ApbAddrType(12), doc=Doc(title='APB Bus Address', ...))
    StructItem('pwrite', ApbWriteType(), doc=Doc(title='APB Write Enable', ...))
    StructItem('pwdata', ApbDataType(32), doc=Doc(title='APB Data', ...))
    StructItem('penable', ApbEnaType(), doc=Doc(title='APB Transfer Enable', ...))
    StructItem('psel', ApbSelType(), doc=Doc(title='APB Slave Select', ...))
    StructItem('prdata', ApbDataType(32), orientation=BWD, doc=Doc(title='APB Data', ...))
    StructItem('pslverr', ApbRespType(), orientation=BWD, doc=Doc(title='APB Response Error', ...))
    StructItem('pready', ApbReadyType(), orientation=BWD, doc=Doc(title='APB Transfer Done', ...))

    With `pauser`:

    >>> class AuserType(ASecIdType):
    ...     def _build(self):
    ...         self._add(0, "apps")
    ...         self._add(2, "comm")
    ...         self._add(5, "audio")
    >>> apb5 = AmbaProto("APB5", ausertype=AuserType(default=2))

    >>> for item in ApbSlvType(proto=apb5).values(): item
    StructItem('paddr', ApbAddrType(12), doc=Doc(title='APB Bus Address', ...))
    StructItem('pauser', AuserType(default=2), doc=Doc(title='APB Address User Channel', ...))
    StructItem('pwrite', ApbWriteType(), doc=Doc(title='APB Write Enable', ...))
    StructItem('pwdata', ApbDataType(32), doc=Doc(title='APB Data', ...))
    StructItem('penable', ApbEnaType(), doc=Doc(title='APB Transfer Enable', ...))
    StructItem('psel', ApbSelType(), doc=Doc(title='APB Slave Select', ...))
    StructItem('prdata', ApbDataType(32), orientation=BWD, doc=Doc(title='APB Data', ...))
    StructItem('pslverr', ApbRespType(), orientation=BWD, doc=Doc(title='APB Response Error', ...))
    StructItem('pready', ApbReadyType(), orientation=BWD, doc=Doc(title='APB Transfer Done', ...))

    Both protocol versions are not connectable:

    >>> ApbSlvType().is_connectable(ApbSlvType(proto=apb5))
    False

    But casting is allowed:

    >>> for item in ApbSlvType().cast(ApbSlvType(proto=apb5)): item
    ('', '')
    ('paddr', 'paddr')
    ('pwrite', 'pwrite')
    ('pwdata', 'pwdata')
    ('penable', 'penable')
    ('psel', 'psel')
    ('prdata', 'prdata')
    ('pslverr', 'pslverr')
    ('pready', 'pready')
    """

    title: str = "APB Slave"
    comment: str = "APB Slave"
    proto: AmbaProto = AMBA3
    addrwidth: int = 12
    datawidth: int = 32

    def _build(self):
        # FWD
        self._add("paddr", ApbAddrType(self.addrwidth))
        if self.proto.ausertype:
            auserdoc = "APB Address User Channel"
            self._add("pauser", self.proto.ausertype, title=auserdoc, comment=auserdoc)
        if self.proto.wusertype:
            wuserdoc = "APB Write Data User Channel"
            self._add("pwuser", self.proto.wusertype, title=wuserdoc, comment=wuserdoc)
        self._add("pwrite", ApbWriteType())
        self._add("pwdata", ApbDataType(self.datawidth))
        if self.proto.has_wstrb:
            self._add("pstrb", ApbPstrbType(self.datawidth))
        self._add("penable", ApbEnaType())
        self._add("psel", ApbSelType())
        # BWD
        self._add("prdata", ApbDataType(self.datawidth), u.BWD)
        if rusertype := self.proto.rusertype:
            ruserdoc = "APB Read Data User Channel"
            self._add("pruser", rusertype, title=ruserdoc, comment=ruserdoc, dir=u.BWD)
        if busertype := self.proto.busertype:
            buserdoc = "APB Read Response User Channel"
            self._add("pbuser", busertype, title=buserdoc, comment=buserdoc, dir=u.BWD)
        self._add("pslverr", ApbRespType(), u.BWD)
        self._add("pready", ApbReadyType(), u.BWD)

    def cast(self, other):
        """
        How to cast an assign of type `self` from a value of type `other`.

        `self = cast(other)`
        """
        if isinstance(other, ApbSlvType) and self.proto != other.proto:
            # Drive a Slv with Slv signals
            yield "", ""
            yield "paddr", "paddr"
            # never use pauser
            yield "pwrite", "pwrite"
            yield "pwdata", "pwdata"
            yield "penable", "penable"
            yield "psel", "psel"
            # BWD
            yield "prdata", "prdata"
            yield "pslverr", "pslverr"
            yield "pready", "pready"
        else:
            return None


class ApbSelType(u.BitType):
    """APB Select."""

    title: str = "APB Slave Select"
    comment: str = "APB Slave Select"


class ApbEnaType(u.EnaType):
    """APB Enable."""

    title: str = "APB Transfer Enable"
    comment: str = "APB Transfer Enable"


class ApbAddrType(u.UintType):
    """
    APB Address.

    >>> ApbAddrType().width
    32
    >>> ApbAddrType(width=16).width
    16

    Checked for valid width:
    >>> t = ApbAddrType(width=34)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for APB addrwidth: 34.Legal values are between 0 and 32.
    """

    title: str = "APB Bus Address"
    comment: str = "APB Bus Address"

    def __init__(self, width=32, **kwargs):
        if width not in LEGAL_APB_ADDR_WIDTH:
            raise ValueError(
                f"Illegal value for APB addrwidth: {width}."
                f"Legal values are between {LEGAL_APB_ADDR_WIDTH[0]} and {LEGAL_APB_ADDR_WIDTH[-1]}."
            )
        super().__init__(width=width, **kwargs)


class ApbDataType(u.UintType):
    """
    APB Data.

    >>> ApbDataType().width
    32
    >>> ApbDataType(width=16).width
    16

    Data width is checked for legal values:

    >>> t = ApbDataType(width=18)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for APB datawidth: 18. Legal values are [8, 16, 32]
    """

    title: str = "APB Data"
    comment: str = "APB Data"

    def __init__(self, width=32, **kwargs):
        if width not in LEGAL_APB_DATA_WIDTH:
            raise ValueError(f"Illegal value for APB datawidth: {width}. Legal values are {LEGAL_APB_DATA_WIDTH}")
        super().__init__(width=width, **kwargs)


class ApbPstrbType(u.UintType):
    """
    APB Write Strobe.

    Write strobe width is derived directly from data width.
    >>> ApbPstrbType().width
    4

    Data width is checked for legal values:
    >>> t = ApbPstrbType(29)
    Traceback (most recent call last):
    ...
    ValueError: Illegal value for APB datawidth: 29. Legal values are [8, 16, 32]
    """

    title: str = "APB Write Strobe"
    comment: str = "APB Write Strobe"

    def __init__(self, datawidth=32, **kwargs):
        if datawidth not in LEGAL_APB_DATA_WIDTH:
            raise ValueError(f"Illegal value for APB datawidth: {datawidth}. Legal values are {LEGAL_APB_DATA_WIDTH}")
        super().__init__(width=datawidth // 8, **kwargs)


class ApbProtType(u.UintType):
    """
    APB Protection Type.

    >>> ApbProtType().width
    3

    >>> ApbProtType().default
    0
    """

    title: str = "APB Protection Type"
    comment: str = "APB Protection Type"

    def __init__(self):
        super().__init__(width=3, default=0)


class ApbWriteType(u.AEnumType):
    """
    AHB Write Type.

    >>> for item in ApbWriteType().values(): item
    EnumItem(0, 'read', doc=Doc(title='Read operation'))
    EnumItem(1, 'write', doc=Doc(title='Write operation'))
    """

    keytype: u.BitType = u.BitType()
    title: str = "APB Write Enable"
    comment: str = "APB Write Enable"

    def _build(self):
        self._add(0, "read", "Read operation")
        self._add(1, "write", "Write operation")


class ApbRespType(u.AEnumType):
    """
    APB Response Type.

    >>> for item in ApbRespType().values(): item
    EnumItem(0, 'okay', doc=Doc(title='OK'))
    EnumItem(1, 'error', doc=Doc(title='Error'))
    """

    keytype: u.BitType = u.BitType()
    title: str = "APB Response Error"
    comment: str = "APB Response Error"

    def _build(self):
        self._add(0, "okay", "OK")
        self._add(1, "error", "Error")


class ApbReadyType(u.AEnumType):
    """
    APB Ready Type.

    >>> for item in ApbReadyType().values(): item
    EnumItem(0, 'busy', doc=Doc(title='Ongoing'))
    EnumItem(1, 'done', doc=Doc(title='Done'))
    """

    keytype: u.BitType = u.BitType(default=1)
    title: str = "APB Transfer Done"
    comment: str = "APB Transfer Done"

    def _build(self):
        self._add(0, "busy", "Ongoing")
        self._add(1, "done", "Done")


# class IdleType(u.AEnumType):
#     """
#     Bus Idle Type.

#     >>> for item in IdleType().values(): item
#     EnumItem(0, 'busy', doc=Doc(title='Busy', comment='Transfers Ongoing'))
#     EnumItem(1, 'idle', doc=Doc(title='Idle'))
#     """

#     keytype: u.BitType = u.BitType(default=1)
#     title: str = "Bus Idle"
#     comment: str = "Bus Idle"

#     def _build(self):
#         self._add(0, "busy", "Busy", comment="Transfers Ongoing")
#         self._add(1, "idle", "Idle")


def check_ahb_proto_pair(src_name: str, src_proto: AmbaProto, tgt_name: str, tgt_proto: AmbaProto) -> int:  # noqa: C901, PLR0912
    """
    Check AHB Protocol Compatibility.

    >>> p0 = AmbaProto("p0")
    >>> p1 = AmbaProto("p1",
    ...                 hmaster_width=3,
    ...                 hprotwidth=0,
    ...                 has_hburst=False,
    ...                 has_hmastlock=False,
    ...                 has_hnonsec=False,
    ...                 has_exclxfers=False
    ...               )
    >>> p2 = AmbaProto("p2",
    ...                hmaster_width=4,
    ...                hprotwidth=7,
    ...                has_hburst=True,
    ...                has_hmastlock=True,
    ...                has_hnonsec=True,
    ...                has_exclxfers=True
    ...               )
    >>> p3 = AmbaProto("p3", ausertype=u.UintType(3))
    >>> p4 = AmbaProto("p4", ausertype=u.UintType(4))
    >>> check_ahb_proto_pair("src", p0, "tgt", p0)
    0
    >>> check_ahb_proto_pair("src", p0, "tgt", p1)
    1
    >>> check_ahb_proto_pair("src", p1, "tgt", p2)
    1
    >>> check_ahb_proto_pair("src", p2, "tgt", p1)
    1
    >>> check_ahb_proto_pair("src", p0, "tgt", p3)
    1
    >>> check_ahb_proto_pair("src", p3, "tgt", p0)
    1
    >>> check_ahb_proto_pair("src", p3, "tgt", p4)
    2
    """
    if src_proto == tgt_proto:  # no need to check
        return 0

    opts = {
        "has_hburst": "hburst",
        "has_hmastlock": "hmastlock",
        "has_hnonsec": "hnonsec",
        "has_exclxfers": "hexcl/hexokay",
        "has_wstrb": "hwstrb",
    }
    src_dict = dict(src_proto)
    tgt_dict = dict(tgt_proto)
    verdict = 0
    pre1 = f"Protocol Pair for Source {src_name} with Protocol {src_proto.name} "
    pre2 = f"and Target {tgt_name} with Protocol {tgt_proto.name}"
    preamble = pre1 + pre2
    LOGGER.info(f"Checking {preamble}.")

    for usrtp in ["auser", "wuser", "ruser", "buser"]:
        tname = f"{usrtp}type"
        src_usertp = src_proto.__dict__[tname]
        tgt_usertp = tgt_proto.__dict__[tname]
        if src_usertp is not None and tgt_usertp is not None and src_usertp != tgt_usertp:
            LOGGER.error(f"{preamble}: Incompatible Definitions for 'h{usrtp}'!")
            verdict = 2

    if src_proto.ausertype is not None and tgt_proto.ausertype is None:
        LOGGER.warning(f"{preamble}: Ignoring source 'hauser'.")
        verdict = max(verdict, 1)
    elif src_proto.ausertype is None and tgt_proto.ausertype is not None:
        LOGGER.warning(f"{preamble}: Clamping target 'hauser'.")
        verdict = max(verdict, 1)
    if src_proto.hprotwidth > 0 and tgt_proto.hprotwidth == 0:
        LOGGER.warning(f"{preamble}: Ignoring source 'hprot'.")
        verdict = max(verdict, 1)
    elif src_proto.hprotwidth == 0 and tgt_proto.hprotwidth > 0:
        LOGGER.warning(f"{preamble}: Clamping target 'hprot'.")
        verdict = max(verdict, 1)
    elif src_proto.hprotwidth != tgt_proto.hprotwidth:
        LOGGER.warning(f"{preamble}: Different width for 'hprot' signals.")
        verdict = max(verdict, 1)
    if src_proto.hmaster_width > tgt_proto.hmaster_width:
        slc = "MSBs of " if tgt_proto.hmaster_width else ""
        LOGGER.warning(f"{preamble}: Ignoring {slc}source 'hmaster'.")
        verdict = max(verdict, 1)
    elif src_proto.hmaster_width < tgt_proto.hmaster_width:
        slc = "MSBs of " if src_proto.hmaster_width else ""
        LOGGER.warning(f"{preamble}: Clamping {slc}target 'hmaster'.")
        verdict = max(verdict, 1)

    for opt, sig in opts.items():
        if src_dict[opt] and not tgt_dict[opt]:
            LOGGER.warning(f"{preamble}: Ignoring source '{sig}'.")
            verdict = max(verdict, 1)
        elif not src_dict[opt] and tgt_dict[opt]:
            LOGGER.warning(f"{preamble}: Clamping target '{sig}'.")
            verdict = max(verdict, 1)

    return verdict
