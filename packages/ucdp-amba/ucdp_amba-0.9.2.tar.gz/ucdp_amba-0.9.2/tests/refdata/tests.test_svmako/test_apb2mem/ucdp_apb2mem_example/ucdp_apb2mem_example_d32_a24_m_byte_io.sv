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
// Module:     ucdp_amba.ucdp_apb2mem_example_d32_a24_m_byte_io
// Data Model: ucdp_amba.ucdp_apb2mem.UcdpApb2memMod
//
//
// Addressing-Width: byte
// Size:             4194304x32 (16 MB)
//
// =============================================================================

`begin_keywords "1800-2009"
`default_nettype none  // implicit wires are forbidden

module ucdp_apb2mem_example_d32_a24_m_byte_io ( // ucdp_amba.ucdp_apb2mem.UcdpApb2memMod
  // apb_slv_i: APB Slave
  input  wire  [23:0] apb_slv_paddr_i,   // APB Bus Address
  input  wire         apb_slv_pwrite_i,  // APB Write Enable
  input  wire  [31:0] apb_slv_pwdata_i,  // APB Data
  input  wire         apb_slv_penable_i, // APB Transfer Enable
  input  wire         apb_slv_psel_i,    // APB Slave Select
  output logic [31:0] apb_slv_prdata_o,  // APB Data
  output logic        apb_slv_pslverr_o, // APB Response Error
  output logic        apb_slv_pready_o,  // APB Transfer Done
  // mem_o: Memory Interface
  output logic        mem_ena_o,         // Memory Access Enable
  output logic [23:0] mem_addr_o,        // Memory Address
  output logic        mem_wena_o,        // Memory Write Enable
  output logic [31:0] mem_wdata_o,       // Memory Write Data
  input  wire  [31:0] mem_rdata_i,       // Memory Read Data
  input  wire         mem_err_i          // Memory Access Failed.
);


assign mem_ena_o = apb_slv_penable_i & apb_slv_psel_i;
assign mem_addr_o = apb_slv_paddr_i[23:0];
assign mem_wena_o = apb_slv_pwrite_i;
assign mem_wdata_o = apb_slv_pwdata_i;

assign apb_slv_prdata_o = mem_rdata_i;
assign apb_slv_pslverr_o = mem_err_i;
assign apb_slv_pready_o = 1'b1;

endmodule // ucdp_apb2mem_example_d32_a24_m_byte_io

`default_nettype wire
`end_keywords

// =============================================================================
//
//   @generated @fully-generated
//
//   THIS FILE IS GENERATED!!! DO NOT EDIT MANUALLY. CHANGES ARE LOST.
//
// =============================================================================
