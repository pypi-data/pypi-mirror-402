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
Unified Chip Design Platform - AMBA - AHB2APB Tests.
"""

import logging
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from humannum import Hex

from tests.ahb_driver import AHBMasterDriver, BurstType, SizeType
from tests.apb_driver import APBSlaveDriver


# TODO put this is a generic tb lib
async def wait_clocks(clock, cycles):
    """Helper Function."""
    for _ in range(cycles):
        await RisingEdge(clock)


@cocotb.test()
async def ahb2apb_test(dut):  # noqa: C901, PLR0912
    """Main Test Loop."""
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    hclk = dut.main_clk_i
    rst_an = dut.main_rst_an_i

    ahb_mst = AHBMasterDriver(
        name="ahb_mst",
        log_level=logging.INFO,
        clk=hclk,
        rst_an=rst_an,
        hsel=dut.ahb_slv_hsel_i,
        haddr=dut.ahb_slv_haddr_i,
        hwrite=dut.ahb_slv_hwrite_i,
        hwstrb=dut.ahb_slv_hwstrb_i,
        hwdata=dut.ahb_slv_hwdata_i,
        htrans=dut.ahb_slv_htrans_i,
        hburst=dut.ahb_slv_hburst_i,
        hsize=dut.ahb_slv_hsize_i,
        hprot=dut.ahb_slv_hprot_i,
        hrdata=dut.ahb_slv_hrdata_o,
        hready=dut.ahb_slv_hreadyout_o,  # special hready/hreadyout swap as the master is not on a ML
        hreadyout=dut.ahb_slv_hready_i,
        hresp=dut.ahb_slv_hresp_o,
    )

    foo_slv = APBSlaveDriver(
        name="slv_foo",
        log_level=logging.INFO,
        clk=hclk,
        rst_an=rst_an,
        paddr=dut.apb_slv_foo_paddr_o,
        pwrite=dut.apb_slv_foo_pwrite_o,
        pwdata=dut.apb_slv_foo_pwdata_o,
        penable=dut.apb_slv_foo_penable_o,
        psel=dut.apb_slv_foo_psel_o,
        prdata=dut.apb_slv_foo_prdata_i,
        pready=dut.apb_slv_foo_pready_i,
        pslverr=dut.apb_slv_foo_pslverr_i,
        pready_delay=0,
        size_bytes=4 * 1024,
        err_addr={"w": list(range(0x400, 0x410)), "r": list(range(0x420, 0x430)), "rw": list(range(0x440, 0x450))},
    )

    bar_slv = APBSlaveDriver(
        name="slv_bar",
        log_level=logging.INFO,
        clk=hclk,
        rst_an=rst_an,
        paddr=dut.apb_slv_bar_paddr_o,
        pwrite=dut.apb_slv_bar_pwrite_o,
        pstrb=dut.apb_slv_bar_pstrb_o,
        pwdata=dut.apb_slv_bar_pwdata_o,
        penable=dut.apb_slv_bar_penable_o,
        psel=dut.apb_slv_bar_psel_o,
        prdata=dut.apb_slv_bar_prdata_i,
        pready=dut.apb_slv_bar_pready_i,
        pslverr=dut.apb_slv_bar_pslverr_i,
        pready_delay=0,
        size_bytes=1024,
    )

    baz_slv = APBSlaveDriver(
        name="slv_baz",
        log_level=logging.INFO,
        clk=hclk,
        rst_an=rst_an,
        paddr=dut.apb_slv_baz_paddr_o,
        pwrite=dut.apb_slv_baz_pwrite_o,
        pwdata=dut.apb_slv_baz_pwdata_o,
        penable=dut.apb_slv_baz_penable_o,
        psel=dut.apb_slv_baz_psel_o,
        prdata=dut.apb_slv_baz_prdata_i,
        pready=dut.apb_slv_baz_pready_i,
        pslverr=dut.apb_slv_baz_pslverr_i,
        pready_delay=0,
        size_bytes=13 * 1024,
    )

    mem = [bytearray(4 * 1024), bytearray(1024), bytearray(13 * 1024)]

    baseaddr = [0x0, 0x1000, 0x4000]

    btypes = (
        BurstType.SINGLE,
        BurstType.WRAP4,
        BurstType.INCR4,
        BurstType.WRAP8,
        BurstType.INCR8,
        BurstType.WRAP16,
        BurstType.INCR16,
    )

    sizes = (SizeType.BYTE, SizeType.HALFWORD, SizeType.WORD)

    slaves = [foo_slv, bar_slv, baz_slv]

    cocotb.start_soon(Clock(hclk, period=10).start())

    cocotb.start_soon(foo_slv.run())
    cocotb.start_soon(bar_slv.run())
    cocotb.start_soon(baz_slv.run())

    # initial reset
    rst_an.value = 0
    await wait_clocks(hclk, 10)
    rst_an.value = 1
    await wait_clocks(hclk, 10)

    # randomized accesses
    for _ in range(50):
        tgt = 1  # random.randint(0, 2)
        btype = random.choice(btypes)
        if slaves[tgt].pstrb is not None:
            size = random.choice(sizes)
        else:
            size = SizeType.WORD
        if btype == BurstType.SINGLE:
            blen = 1
            mmask = (1 << size) - 1
        else:
            blen = 2 << (btype >> 1)
            mmask = (4 << (((btype - 2) >> 1) + size)) - 1
        offs = random.randint(0, 100) & (~((1 << size) - 1))  # make it size aligned
        if btype in (BurstType.INCR16, BurstType.INCR8, BurstType.INCR4):
            offs &= ~mmask  # make it burst aligned

        smax = (1 << (1 << (size + 3))) - 1  # max value according to size
        if random.randint(0, 1):
            wdata = [random.randint(1, smax) for i in range(blen)]
            refdata = ahb_mst.calc_wrmem(offs=offs, size=size, blen=blen, mmask=mmask, wdata=wdata, mem=mem[tgt])
            mem[tgt][(offs & ~mmask) : (offs & ~mmask) + (blen << size)] = refdata
            log.info(
                f"=MST WRITE TRANSFER= target: {slaves[tgt].name}; offs:{hex(offs)}; "
                f"burst:{btype.name}; size:{size.name}; "
                f"wdata:{[hex(w) for w in wdata]}\n"
            )
            err_resp = await ahb_mst.write(baseaddr[tgt] + offs, wdata, burst_type=btype, size=size)
            assert not err_resp, "Unexpected error response"
            for ln in range(5):
                log.warning(
                    f"MEM[{ln * 16}:{ln * 16 + 15}] = {[str(Hex(w, 8)) for w in mem[tgt][(ln * 16) : (ln * 16 + 15)]]}"
                )
        else:
            xdata = ahb_mst.calc_expected(offs=offs, size=size, blen=blen, mmask=mmask, mem=mem[tgt])
            err_resp, rdata = await ahb_mst.read(baseaddr[tgt] + offs, burst_type=btype, size=size)
            assert not err_resp, "Unexpected error response"
            if tuple(rdata) == tuple(xdata):
                log.info(
                    f"=MST READ TRANSFER= target: {slaves[tgt].name}; offs:{hex(offs)}; "
                    f"burst:{btype.name}; size:{size.name};\n"
                    f"> rdata: {[hex(w) for w in rdata]};"
                )
            else:
                log.error(
                    f"=MST READ TRANSFER MISMATCH= target: {slaves[tgt].name}; offs:{hex(offs)}; "
                    f"burst:{btype.name}; size:{size.name};\n"
                    f"> expected: {[hex(w) for w in xdata]};\n"
                    f"> got:      {[hex(w) for w in rdata]};"
                )
                raise AssertionError("Read data compare mismatch.")

        await wait_clocks(hclk, random.randint(0, 5))
    await wait_clocks(hclk, 20)

    # directed tests for expected error responses
    # 0x400...0x40F error on write
    # 0x420...0x42F error on read
    # 0x440...0x44F error in read and write

    log.info("=MST WRITE TRANSFER= target: 0; offs:0x408; with expected Error Response")
    err_resp = await ahb_mst.write(0x0000408, 0xDEAD)
    assert err_resp, "Missed expected Error Response"
    await wait_clocks(hclk, 5)

    err_resp, rdata = await ahb_mst.read(0x0000408)
    assert not err_resp, "Unexpected error response"
    if tuple(rdata) == (0,):
        log.info(f"=MST READ TRANSFER= target: 0; offs:0x408;\n> rdata: {[hex(w) for w in rdata]};")
    else:
        log.error(
            "=MST READ TRANSFER MISMATCH= target: 0; offs:0x408;\n"
            "> expected: [0x0];\n"
            f"> got:      {[hex(w) for w in rdata]};"
        )
        raise AssertionError("Read data compare mismatch.")
    await wait_clocks(hclk, 5)

    log.info("=MST WRITE TRANSFER= target: 0; offs:0x424; wdata:[0xAFFE]")
    err_resp = await ahb_mst.write(0x0000424, 0xAFFE)
    assert not err_resp, "Unexpected error response"
    await wait_clocks(hclk, 5)

    log.info("=MST READ TRANSFER= target: 0; offs:0x424; with expected Error Response")
    err_resp, rdata = await ahb_mst.read(0x0000424)
    assert err_resp, "Missed expected Error Response"
    if tuple(rdata) != (0,):
        log.error(
            "=MST READ TRANSFER MISMATCH= target: 0; offs:0x424;\n"
            "> expected: [0x0];\n"
            f"> got:      {[hex(w) for w in rdata]};"
        )
        raise AssertionError("Read data compare mismatch.")
    await wait_clocks(hclk, 5)

    log.info("=MST WRITE TRANSFER= target: 0; offs:0x44C; with expected Error Response")
    err_resp = await ahb_mst.write(0x000044C, 0xDEAD)
    assert err_resp, "Missed expected Error Response"
    await wait_clocks(hclk, 5)

    log.info("=MST READ TRANSFER= target: 0; offs:0x44C; with expected Error Response")
    err_resp, rdata = await ahb_mst.read(0x000044C)
    assert err_resp, "Missed expected Error Response"
    if tuple(rdata) != (0,):
        log.error(
            "=MST READ TRANSFER MISMATCH= target: 0; offs:0x44C;\n"
            "> expected: [0x0];\n"
            f"> got:      {[hex(w) for w in rdata]};"
        )
        raise AssertionError("Read data compare mismatch.")

    await wait_clocks(hclk, 30)
