// =============================================================================
//
//   @generated @fully-generated
//
//   THIS FILE IS GENERATED!!! DO NOT EDIT MANUALLY. CHANGES ARE LOST.
//
// =============================================================================
//
//  MIT License
//
//  Copyright (c) 2024-2026 nbiotcloud
//
//  Permission is hereby granted, free of charge, to any person obtaining a copy
//  of this software and associated documentation files (the "Software"), to deal
//  in the Software without restriction, including without limitation the rights
//  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//  copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//
//  The above copyright notice and this permission notice shall be included in all
//  copies or substantial portions of the Software.
//
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//  SOFTWARE.
//
// =============================================================================
//
// Module:     ucdp_amba.ucdp_ahb2ahb_example_slv2slv_lrgp_lrgp_n
// Data Model: ucdp_amba.ucdp_ahb2ahb.UcdpAhb2ahbMod
//
//
// No conversion, just feed-through.
//
// =============================================================================

`begin_keywords "1800-2009"
`default_nettype none  // implicit wires are forbidden

module ucdp_ahb2ahb_example_slv2slv_lrgp_lrgp_n ( // ucdp_amba.ucdp_ahb2ahb.UcdpAhb2ahbMod
  // ahb_src_i: AHB Source
  input  wire          ahb_src_hsel_i,      // AHB Slave Select
  input  wire  [35:0]  ahb_src_haddr_i,     // AHB Bus Address
  input  wire          ahb_src_hwrite_i,    // AHB Write Enable
  input  wire  [1:0]   ahb_src_htrans_i,    // AHB Transfer Type
  input  wire  [2:0]   ahb_src_hsize_i,     // AHB Size
  input  wire  [2:0]   ahb_src_hburst_i,    // AHB Burst Type
  input  wire  [6:0]   ahb_src_hprot_i,     // AHB Transfer Protection
  input  wire          ahb_src_hnonsec_i,   // AHB Secure Transfer
  input  wire          ahb_src_hmastlock_i, // AHB Locked Sequence Enable
  input  wire  [127:0] ahb_src_hwdata_i,    // AHB Data
  input  wire  [15:0]  ahb_src_hwstrb_i,    // AHB Write Strobe
  input  wire          ahb_src_hready_i,    // AHB Transfer Done to Slave
  input  wire          ahb_src_hexcl_i,     // AHB Exclusive Transfer
  input  wire  [5:0]   ahb_src_hmaster_i,   // AHB Master ID
  output logic         ahb_src_hreadyout_o, // AHB Transfer Done from Slave
  output logic         ahb_src_hresp_o,     // AHB Response Error
  output logic         ahb_src_hexokay_o,   // AHB Exclusive Response
  output logic [127:0] ahb_src_hrdata_o,    // AHB Data
  // ahb_tgt_o: AHB Target
  output logic         ahb_tgt_hsel_o,      // AHB Slave Select
  output logic [35:0]  ahb_tgt_haddr_o,     // AHB Bus Address
  output logic         ahb_tgt_hwrite_o,    // AHB Write Enable
  output logic [1:0]   ahb_tgt_htrans_o,    // AHB Transfer Type
  output logic [2:0]   ahb_tgt_hsize_o,     // AHB Size
  output logic [2:0]   ahb_tgt_hburst_o,    // AHB Burst Type
  output logic [6:0]   ahb_tgt_hprot_o,     // AHB Transfer Protection
  output logic         ahb_tgt_hnonsec_o,   // AHB Secure Transfer
  output logic         ahb_tgt_hmastlock_o, // AHB Locked Sequence Enable
  output logic [127:0] ahb_tgt_hwdata_o,    // AHB Data
  output logic [15:0]  ahb_tgt_hwstrb_o,    // AHB Write Strobe
  output logic         ahb_tgt_hready_o,    // AHB Transfer Done to Slave
  output logic         ahb_tgt_hexcl_o,     // AHB Exclusive Transfer
  output logic [5:0]   ahb_tgt_hmaster_o,   // AHB Master ID
  input  wire          ahb_tgt_hreadyout_i, // AHB Transfer Done from Slave
  input  wire          ahb_tgt_hresp_i,     // AHB Response Error
  input  wire          ahb_tgt_hexokay_i,   // AHB Exclusive Response
  input  wire  [127:0] ahb_tgt_hrdata_i     // AHB Data
);





  // TODO: handle async


  // === standard forwarding ============
  assign ahb_tgt_htrans_o = ahb_src_htrans_i;
  assign ahb_tgt_hwrite_o = ahb_src_hwrite_i;
  assign ahb_tgt_hsize_o = ahb_src_hsize_i;
  assign ahb_src_hresp_o = ahb_tgt_hresp_i;

  // === haddr handling =================
  assign ahb_tgt_haddr_o = ahb_src_haddr_i;

  // === hburst handling ================
  assign ahb_tgt_hburst_o = ahb_src_hburst_i;

  // === hsel handling ==================
  assign ahb_tgt_hsel_o = ahb_src_hsel_i;

  // === hxdata handling ================
  // just forward read/write data
  assign ahb_tgt_hwdata_o = ahb_src_hwdata_i;
  assign ahb_src_hrdata_o = ahb_tgt_hrdata_i;

  // === hwstrb handling =================
  assign ahb_tgt_hwstrb_o = ahb_src_hwstrb_i;

  // === hready handling ================
  assign ahb_tgt_hready_o = ahb_src_hready_i;
  assign ahb_src_hreadyout_o = ahb_tgt_hreadyout_i;

  // === hprot handling =================
  assign ahb_tgt_hprot_o = ahb_src_hprot_i;

  // === hnonsec handling ================
  assign ahb_tgt_hnonsec_o = ahb_src_hnonsec_i;

  // === hmastlock handling ================
  assign ahb_tgt_hmastlock_o = ahb_src_hmastlock_i;

  // === hexcl handling ================
  assign ahb_tgt_hexcl_o = ahb_src_hexcl_i;

  // === hexokay handling ================
  assign ahb_src_hexokay_o = ahb_tgt_hexokay_i;

  // === hmaster handling: forward =================
  assign ahb_tgt_hmaster_o = ahb_src_hmaster_i;






endmodule // ucdp_ahb2ahb_example_slv2slv_lrgp_lrgp_n

`default_nettype wire
`end_keywords

// =============================================================================
//
//   @generated @fully-generated
//
//   THIS FILE IS GENERATED!!! DO NOT EDIT MANUALLY. CHANGES ARE LOST.
//
// =============================================================================
