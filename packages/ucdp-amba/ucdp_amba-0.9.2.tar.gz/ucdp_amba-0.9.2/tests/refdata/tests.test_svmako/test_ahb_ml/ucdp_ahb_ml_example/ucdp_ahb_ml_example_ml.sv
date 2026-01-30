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
// Module:     ucdp_amba.ucdp_ahb_ml_example_ml
// Data Model: ucdp_amba.ucdp_ahb_ml.UcdpAhbMlMod
//
//
// | Master > Slave | ram | periph | misc |
// | -------------- | --- | ------ | ---- |
// | ext            | X   |        | X    |
// | dsp            | X   | X      |      |
//
//
//
// * Top:     `None`
// * Defines: `None`
// * Size:    `3932320 KB`
//
// | Addrspace | Type     | Base         | Size                        | Infos | Attributes |
// | --------- | -------- | ------------ | --------------------------- | ----- | ---------- |
// | reserved0 | Reserved | `0x0`        | `536870912x32 (2 GB)`       |       |            |
// | misc      | Slave    | `0x80000000` | `5888x32 (23 KB)`           |       |            |
// | reserved1 | Reserved | `0x80005C00` | `469756160x32 (1834985 KB)` |       |            |
// | ram       | Slave    | `0xF0000000` | `16384x32 (64 KB)`          |       |            |
// | periph    | Slave    | `0xF0010000` | `16384x32 (64 KB)`          |       |            |
// | misc      | Slave    | `0xF0020000` | `8192x32 (32 KB)`           |       |            |
// | reserved2 | Reserved | `0xF0028000` | `67067904x32 (261984 KB)`   |       |            |
//
// =============================================================================

`begin_keywords "1800-2009"
`default_nettype none  // implicit wires are forbidden

module ucdp_ahb_ml_example_ml ( // ucdp_amba.ucdp_ahb_ml.UcdpAhbMlMod
  // main_i: Clock and Reset
  input  wire         main_clk_i,                 // Clock
  input  wire         main_rst_an_i,              // Async Reset (Low-Active)
  // ahb_mst_ext_i: AHB Input 'ext'
  input  wire  [1:0]  ahb_mst_ext_htrans_i,       // AHB Transfer Type
  input  wire  [35:0] ahb_mst_ext_haddr_i,        // AHB Bus Address
  input  wire  [3:0]  ahb_mst_ext_hauser_i,       // AHB Address User Channel
  input  wire  [3:0]  ahb_mst_ext_hwuser_i,       // AHB Write Data User Channel
  input  wire         ahb_mst_ext_hwrite_i,       // AHB Write Enable
  input  wire  [2:0]  ahb_mst_ext_hsize_i,        // AHB Size
  input  wire  [2:0]  ahb_mst_ext_hburst_i,       // AHB Burst Type
  input  wire  [3:0]  ahb_mst_ext_hprot_i,        // AHB Transfer Protection
  input  wire         ahb_mst_ext_hnonsec_i,      // AHB Secure Transfer
  input  wire         ahb_mst_ext_hmastlock_i,    // AHB Locked Sequence Enable
  input  wire  [31:0] ahb_mst_ext_hwdata_i,       // AHB Data
  input  wire  [3:0]  ahb_mst_ext_hwstrb_i,       // AHB Write Strobe
  input  wire  [3:0]  ahb_mst_ext_hmaster_i,      // AHB Master ID
  output logic        ahb_mst_ext_hready_o,       // AHB Transfer Done
  output logic        ahb_mst_ext_hresp_o,        // AHB Response Error
  output logic [31:0] ahb_mst_ext_hrdata_o,       // AHB Data
  output logic [3:0]  ahb_mst_ext_hruser_o,       // AHB Read Data User Channel
  output logic [3:0]  ahb_mst_ext_hbuser_o,       // AHB Read Response User Channel
  // ahb_mst_dsp_i: AHB Input 'dsp'
  input  wire  [1:0]  ahb_mst_dsp_htrans_i,       // AHB Transfer Type
  input  wire  [35:0] ahb_mst_dsp_haddr_i,        // AHB Bus Address
  input  wire  [3:0]  ahb_mst_dsp_hauser_i,       // AHB Address User Channel
  input  wire  [3:0]  ahb_mst_dsp_hwuser_i,       // AHB Write Data User Channel
  input  wire         ahb_mst_dsp_hwrite_i,       // AHB Write Enable
  input  wire  [2:0]  ahb_mst_dsp_hsize_i,        // AHB Size
  input  wire  [2:0]  ahb_mst_dsp_hburst_i,       // AHB Burst Type
  input  wire  [3:0]  ahb_mst_dsp_hprot_i,        // AHB Transfer Protection
  input  wire         ahb_mst_dsp_hnonsec_i,      // AHB Secure Transfer
  input  wire         ahb_mst_dsp_hmastlock_i,    // AHB Locked Sequence Enable
  input  wire  [31:0] ahb_mst_dsp_hwdata_i,       // AHB Data
  input  wire  [3:0]  ahb_mst_dsp_hwstrb_i,       // AHB Write Strobe
  input  wire  [3:0]  ahb_mst_dsp_hmaster_i,      // AHB Master ID
  output logic        ahb_mst_dsp_hready_o,       // AHB Transfer Done
  output logic        ahb_mst_dsp_hresp_o,        // AHB Response Error
  output logic [31:0] ahb_mst_dsp_hrdata_o,       // AHB Data
  output logic [3:0]  ahb_mst_dsp_hruser_o,       // AHB Read Data User Channel
  output logic [3:0]  ahb_mst_dsp_hbuser_o,       // AHB Read Response User Channel
  // ahb_slv_ram_o: AHB Output 'ram'
  output logic        ahb_slv_ram_hsel_o,         // AHB Slave Select
  output logic [35:0] ahb_slv_ram_haddr_o,        // AHB Bus Address
  output logic [3:0]  ahb_slv_ram_hauser_o,       // AHB Address User Channel
  output logic [3:0]  ahb_slv_ram_hwuser_o,       // AHB Write Data User Channel
  output logic        ahb_slv_ram_hwrite_o,       // AHB Write Enable
  output logic [1:0]  ahb_slv_ram_htrans_o,       // AHB Transfer Type
  output logic [2:0]  ahb_slv_ram_hsize_o,        // AHB Size
  output logic [2:0]  ahb_slv_ram_hburst_o,       // AHB Burst Type
  output logic [6:0]  ahb_slv_ram_hprot_o,        // AHB Transfer Protection
  output logic        ahb_slv_ram_hnonsec_o,      // AHB Secure Transfer
  output logic        ahb_slv_ram_hmastlock_o,    // AHB Locked Sequence Enable
  output logic [31:0] ahb_slv_ram_hwdata_o,       // AHB Data
  output logic [3:0]  ahb_slv_ram_hwstrb_o,       // AHB Write Strobe
  output logic        ahb_slv_ram_hready_o,       // AHB Transfer Done to Slave
  output logic        ahb_slv_ram_hexcl_o,        // AHB Exclusive Transfer
  output logic [5:0]  ahb_slv_ram_hmaster_o,      // AHB Master ID
  input  wire         ahb_slv_ram_hreadyout_i,    // AHB Transfer Done from Slave
  input  wire         ahb_slv_ram_hresp_i,        // AHB Response Error
  input  wire         ahb_slv_ram_hexokay_i,      // AHB Exclusive Response
  input  wire  [31:0] ahb_slv_ram_hrdata_i,       // AHB Data
  input  wire  [3:0]  ahb_slv_ram_hruser_i,       // AHB Read Data User Channel
  input  wire  [3:0]  ahb_slv_ram_hbuser_i,       // AHB Read Response User Channel
  // ahb_slv_periph_o: AHB Output 'periph'
  output logic        ahb_slv_periph_hsel_o,      // AHB Slave Select
  output logic [35:0] ahb_slv_periph_haddr_o,     // AHB Bus Address
  output logic [3:0]  ahb_slv_periph_hauser_o,    // AHB Address User Channel
  output logic [3:0]  ahb_slv_periph_hwuser_o,    // AHB Write Data User Channel
  output logic        ahb_slv_periph_hwrite_o,    // AHB Write Enable
  output logic [1:0]  ahb_slv_periph_htrans_o,    // AHB Transfer Type
  output logic [2:0]  ahb_slv_periph_hsize_o,     // AHB Size
  output logic [2:0]  ahb_slv_periph_hburst_o,    // AHB Burst Type
  output logic [6:0]  ahb_slv_periph_hprot_o,     // AHB Transfer Protection
  output logic        ahb_slv_periph_hnonsec_o,   // AHB Secure Transfer
  output logic        ahb_slv_periph_hmastlock_o, // AHB Locked Sequence Enable
  output logic [31:0] ahb_slv_periph_hwdata_o,    // AHB Data
  output logic [3:0]  ahb_slv_periph_hwstrb_o,    // AHB Write Strobe
  output logic        ahb_slv_periph_hready_o,    // AHB Transfer Done to Slave
  output logic        ahb_slv_periph_hexcl_o,     // AHB Exclusive Transfer
  output logic [5:0]  ahb_slv_periph_hmaster_o,   // AHB Master ID
  input  wire         ahb_slv_periph_hreadyout_i, // AHB Transfer Done from Slave
  input  wire         ahb_slv_periph_hresp_i,     // AHB Response Error
  input  wire         ahb_slv_periph_hexokay_i,   // AHB Exclusive Response
  input  wire  [31:0] ahb_slv_periph_hrdata_i,    // AHB Data
  input  wire  [3:0]  ahb_slv_periph_hruser_i,    // AHB Read Data User Channel
  input  wire  [3:0]  ahb_slv_periph_hbuser_i,    // AHB Read Response User Channel
  // ahb_slv_misc_o: AHB Output 'misc'
  output logic        ahb_slv_misc_hsel_o,        // AHB Slave Select
  output logic [35:0] ahb_slv_misc_haddr_o,       // AHB Bus Address
  output logic [3:0]  ahb_slv_misc_hauser_o,      // AHB Address User Channel
  output logic [3:0]  ahb_slv_misc_hwuser_o,      // AHB Write Data User Channel
  output logic        ahb_slv_misc_hwrite_o,      // AHB Write Enable
  output logic [1:0]  ahb_slv_misc_htrans_o,      // AHB Transfer Type
  output logic [2:0]  ahb_slv_misc_hsize_o,       // AHB Size
  output logic [2:0]  ahb_slv_misc_hburst_o,      // AHB Burst Type
  output logic [6:0]  ahb_slv_misc_hprot_o,       // AHB Transfer Protection
  output logic        ahb_slv_misc_hnonsec_o,     // AHB Secure Transfer
  output logic        ahb_slv_misc_hmastlock_o,   // AHB Locked Sequence Enable
  output logic [31:0] ahb_slv_misc_hwdata_o,      // AHB Data
  output logic [3:0]  ahb_slv_misc_hwstrb_o,      // AHB Write Strobe
  output logic        ahb_slv_misc_hready_o,      // AHB Transfer Done to Slave
  output logic        ahb_slv_misc_hexcl_o,       // AHB Exclusive Transfer
  output logic [5:0]  ahb_slv_misc_hmaster_o,     // AHB Master ID
  input  wire         ahb_slv_misc_hreadyout_i,   // AHB Transfer Done from Slave
  input  wire         ahb_slv_misc_hresp_i,       // AHB Response Error
  input  wire         ahb_slv_misc_hexokay_i,     // AHB Exclusive Response
  input  wire  [31:0] ahb_slv_misc_hrdata_i,      // AHB Data
  input  wire  [3:0]  ahb_slv_misc_hruser_i,      // AHB Read Data User Channel
  input  wire  [3:0]  ahb_slv_misc_hbuser_i       // AHB Read Response User Channel
);




  // ------------------------------------------------------
  //  Local Parameter
  // ------------------------------------------------------
  // ahb_trans
  localparam integer       ahb_trans_width_p      = 2;    // Width in Bits
  localparam logic   [1:0] ahb_trans_min_p        = 2'h0; // AHB Transfer Type
  localparam logic   [1:0] ahb_trans_max_p        = 2'h3; // AHB Transfer Type
  localparam logic   [1:0] ahb_trans_idle_e       = 2'h0; // No transfer
  localparam logic   [1:0] ahb_trans_busy_e       = 2'h1; // Idle cycle within transfer
  localparam logic   [1:0] ahb_trans_nonseq_e     = 2'h2; // Single transfer or first transfer of a burst
  localparam logic   [1:0] ahb_trans_seq_e        = 2'h3; // Consecutive transfers of a burst
  localparam logic   [1:0] ahb_trans_default_p    = 2'h0; // AHB Transfer Type
  // ahb_resp
  localparam integer       ahb_resp_width_p       = 1;    // Width in Bits
  localparam logic         ahb_resp_min_p         = 1'b0; // AHB Response Error
  localparam logic         ahb_resp_max_p         = 1'b1; // AHB Response Error
  localparam logic         ahb_resp_okay_e        = 1'b0; // OK
  localparam logic         ahb_resp_error_e       = 1'b1; // Error
  localparam logic         ahb_resp_default_p     = 1'b0; // AHB Response Error
  // ahb_size
  localparam integer       ahb_size_width_p       = 3;    // Width in Bits
  localparam logic   [2:0] ahb_size_min_p         = 3'h0; // AHB Size
  localparam logic   [2:0] ahb_size_max_p         = 3'h7; // AHB Size
  localparam logic   [2:0] ahb_size_byte_e        = 3'h0; // Byte
  localparam logic   [2:0] ahb_size_halfword_e    = 3'h1; // Halfword
  localparam logic   [2:0] ahb_size_word_e        = 3'h2; // Word
  localparam logic   [2:0] ahb_size_doubleword_e  = 3'h3; // Doubleword
  localparam logic   [2:0] ahb_size_fourword_e    = 3'h4; // 4-word
  localparam logic   [2:0] ahb_size_eightword_e   = 3'h5; // 8-word
  localparam logic   [2:0] ahb_size_sixteenword_e = 3'h6; // 16-word
  localparam logic   [2:0] ahb_size_kilobit_e     = 3'h7; // 32-word
  localparam logic   [2:0] ahb_size_default_p     = 3'h0; // AHB Size
  // ahb_burst
  localparam integer       ahb_burst_width_p      = 3;    // Width in Bits
  localparam logic   [2:0] ahb_burst_min_p        = 3'h0; // AHB Burst Type
  localparam logic   [2:0] ahb_burst_max_p        = 3'h7; // AHB Burst Type
  localparam logic   [2:0] ahb_burst_single_e     = 3'h0; // Single transfer
  localparam logic   [2:0] ahb_burst_incr_e       = 3'h1; // Incrementing burst of unspecified length
  localparam logic   [2:0] ahb_burst_wrap4_e      = 3'h2; // 4-beat wrapping burst
  localparam logic   [2:0] ahb_burst_incr4_e      = 3'h3; // 4-beat incrementing burst
  localparam logic   [2:0] ahb_burst_wrap8_e      = 3'h4; // 8-beat wrapping burst
  localparam logic   [2:0] ahb_burst_incr8_e      = 3'h5; // 8-beat incrementing burst
  localparam logic   [2:0] ahb_burst_wrap16_e     = 3'h6; // 16-beat wrapping burst
  localparam logic   [2:0] ahb_burst_incr16_e     = 3'h7; // 16-beat incrementing burst
  localparam logic   [2:0] ahb_burst_default_p    = 3'h0; // AHB Burst Type
  // ahb_write
  localparam integer       ahb_write_width_p      = 1;    // Width in Bits
  localparam logic         ahb_write_min_p        = 1'b0; // AHB Write Enable
  localparam logic         ahb_write_max_p        = 1'b1; // AHB Write Enable
  localparam logic         ahb_write_read_e       = 1'b0; // Read operation
  localparam logic         ahb_write_write_e      = 1'b1; // Write operation
  localparam logic         ahb_write_default_p    = 1'b0; // AHB Write Enable
  // fsm
  localparam integer       fsm_width_p            = 3;    // Width in Bits
  localparam logic   [2:0] fsm_min_p              = 3'h0; // AHB ML FSM Type
  localparam logic   [2:0] fsm_max_p              = 3'h7; // AHB ML FSM Type
  localparam logic   [2:0] fsm_idle_st            = 3'h0; // No transfer
  localparam logic   [2:0] fsm_transfer_st        = 3'h1; // Transfer
  localparam logic   [2:0] fsm_transfer_finish_st = 3'h2; // Transfer Finish (wait for HREADY)
  localparam logic   [2:0] fsm_transfer_wait_st   = 3'h3; // Transfer Wait for Grant
  localparam logic   [2:0] fsm_error0_st          = 3'h4; // Pre-Error (wait for HREADY)
  localparam logic   [2:0] fsm_error1_st          = 3'h5; // 1st Error Cycle
  localparam logic   [2:0] fsm_error2_st          = 3'h6; // 2nd Error Cycle
  localparam logic   [2:0] fsm_default_p          = 3'h0; // AHB ML FSM Type
  // ahb_hexok
  localparam integer       ahb_hexok_width_p      = 1;    // Width in Bits
  localparam logic         ahb_hexok_min_p        = 1'b0; // AHB Exclusive Response
  localparam logic         ahb_hexok_max_p        = 1'b1; // AHB Exclusive Response
  localparam logic         ahb_hexok_error_e      = 1'b0; // Error
  localparam logic         ahb_hexok_okay_e       = 1'b1; // OK
  localparam logic         ahb_hexok_default_p    = 1'b0; // AHB Exclusive Response


  // ------------------------------------------------------
  //  Signals
  // ------------------------------------------------------
  logic [2:0]  fsm_ext_r;            // Master 'ext' FSM
  logic        mst_ext_new_xfer_s;
  logic        mst_ext_cont_xfer_s;
  logic        mst_ext_hready_s;
  logic        mst_ext_rqstate_s;
  logic        mst_ext_addr_err_s;
  logic        mst_ext_ram_sel_s;
  logic        mst_ext_ram_req_r;
  logic        mst_ext_ram_gnt_r;
  logic        mst_ext_misc_sel_s;
  logic        mst_ext_misc_req_r;
  logic        mst_ext_misc_gnt_r;
  logic        mst_ext_gnt_s;
  logic [1:0]  mst_ext_htrans_s;     // AHB Transfer Type
  logic [1:0]  mst_ext_htrans_r;     // AHB Transfer Type
  logic [35:0] mst_ext_haddr_s;      // AHB Bus Address
  logic [35:0] mst_ext_haddr_r;      // AHB Bus Address
  logic [3:0]  mst_ext_hauser_s;     // AHB User Type
  logic [3:0]  mst_ext_hauser_r;     // AHB User Type
  logic        mst_ext_hwrite_s;     // AHB Write Enable
  logic        mst_ext_hwrite_r;     // AHB Write Enable
  logic [2:0]  mst_ext_hsize_s;      // AHB Size
  logic [2:0]  mst_ext_hsize_r;      // AHB Size
  logic [2:0]  mst_ext_hburst_s;     // AHB Burst Type
  logic [2:0]  mst_ext_hburst_r;     // AHB Burst Type
  logic [3:0]  mst_ext_hprot_s;      // AHB Transfer Protection
  logic [3:0]  mst_ext_hprot_r;      // AHB Transfer Protection
  logic        mst_ext_hnonsec_s;    // AHB Secure Transfer
  logic        mst_ext_hnonsec_r;    // AHB Secure Transfer
  logic        mst_ext_hmastlock_s;  // AHB Locked Sequence Enable
  logic        mst_ext_hmastlock_r;  // AHB Locked Sequence Enable
  logic [3:0]  mst_ext_hmaster_s;    // AHB Master ID
  logic [3:0]  mst_ext_hmaster_r;    // AHB Master ID
  logic        mst_ext_hwrite_dph_r; // data-phase write indicator
  logic [2:0]  fsm_dsp_r;            // Master 'dsp' FSM
  logic        mst_dsp_new_xfer_s;
  logic        mst_dsp_cont_xfer_s;
  logic        mst_dsp_hready_s;
  logic        mst_dsp_rqstate_s;
  logic        mst_dsp_addr_err_s;
  logic        mst_dsp_ram_sel_s;
  logic        mst_dsp_ram_req_r;
  logic        mst_dsp_ram_gnt_r;
  logic        mst_dsp_periph_sel_s;
  logic        mst_dsp_periph_req_r;
  logic        mst_dsp_periph_gnt_r;
  logic        mst_dsp_gnt_s;
  logic [1:0]  mst_dsp_htrans_s;     // AHB Transfer Type
  logic [1:0]  mst_dsp_htrans_r;     // AHB Transfer Type
  logic [35:0] mst_dsp_haddr_s;      // AHB Bus Address
  logic [35:0] mst_dsp_haddr_r;      // AHB Bus Address
  logic [3:0]  mst_dsp_hauser_s;     // AHB User Type
  logic [3:0]  mst_dsp_hauser_r;     // AHB User Type
  logic        mst_dsp_hwrite_s;     // AHB Write Enable
  logic        mst_dsp_hwrite_r;     // AHB Write Enable
  logic [2:0]  mst_dsp_hsize_s;      // AHB Size
  logic [2:0]  mst_dsp_hsize_r;      // AHB Size
  logic [2:0]  mst_dsp_hburst_s;     // AHB Burst Type
  logic [2:0]  mst_dsp_hburst_r;     // AHB Burst Type
  logic [3:0]  mst_dsp_hprot_s;      // AHB Transfer Protection
  logic [3:0]  mst_dsp_hprot_r;      // AHB Transfer Protection
  logic        mst_dsp_hnonsec_s;    // AHB Secure Transfer
  logic        mst_dsp_hnonsec_r;    // AHB Secure Transfer
  logic        mst_dsp_hmastlock_s;  // AHB Locked Sequence Enable
  logic        mst_dsp_hmastlock_r;  // AHB Locked Sequence Enable
  logic [3:0]  mst_dsp_hmaster_s;    // AHB Master ID
  logic [3:0]  mst_dsp_hmaster_r;    // AHB Master ID
  logic        mst_dsp_hwrite_dph_r; // data-phase write indicator
  logic        mst_ext_ram_req_s;
  logic        mst_ext_ram_keep_s;
  logic        slv_ram_ext_gnt_r;
  logic        slv_ram_ext_sel_s;
  logic        slv_ram_ext_gnt_s;
  logic        mst_dsp_ram_req_s;
  logic        mst_dsp_ram_keep_s;
  logic        slv_ram_dsp_gnt_r;
  logic        slv_ram_dsp_sel_s;
  logic        slv_ram_dsp_gnt_s;
  logic        mst_dsp_periph_req_s;
  logic        slv_periph_dsp_gnt_s;
  logic        mst_ext_misc_req_s;
  logic        slv_misc_ext_gnt_s;


  // ------------------------------------------------------
  // The Masters:
  // ------------------------------------------------------
  // Master 'ext' Logic
  always_comb begin: proc_ext_logic
    mst_ext_new_xfer_s  = (ahb_mst_ext_htrans_i == ahb_trans_nonseq_e) ? 1'b1 : 1'b0;
    mst_ext_cont_xfer_s = ((ahb_mst_ext_htrans_i == ahb_trans_busy_e) ||
                           (ahb_mst_ext_htrans_i == ahb_trans_seq_e)) ? 1'b1 : 1'b0;
    mst_ext_rqstate_s   = ((fsm_ext_r == fsm_idle_st) ||
                           (fsm_ext_r == fsm_transfer_st) ||
                           (fsm_ext_r == fsm_transfer_finish_st) ||
                           (fsm_ext_r == fsm_error2_st)) ? 1'b1 : 1'b0;

    // Address Decoding
    mst_ext_addr_err_s = 1'b0;
    mst_ext_ram_sel_s = 1'b0;
    mst_ext_misc_sel_s = 1'b0;

    casez (ahb_mst_ext_haddr_i[35:10])
      26'b00001111000000000000??????: begin // ram
        mst_ext_ram_sel_s = 1'b1;
      end

      26'b0000100000000000000000????, 26'b000010000000000000000100??, 26'b0000100000000000000001010?, 26'b00001000000000000000010110, 26'b000011110000000000100?????: begin // misc
        mst_ext_misc_sel_s = 1'b1;
      end

      default: begin
        mst_ext_addr_err_s = mst_ext_new_xfer_s;
      end
    endcase

    mst_ext_ram_req_s  = (mst_ext_ram_sel_s & mst_ext_new_xfer_s & mst_ext_rqstate_s) | mst_ext_ram_req_r;
    mst_ext_ram_keep_s = mst_ext_ram_gnt_r & mst_ext_cont_xfer_s;
    mst_ext_misc_req_s = (mst_ext_misc_sel_s & mst_ext_new_xfer_s & mst_ext_rqstate_s) | mst_ext_misc_req_r;

    // Grant Combination
    mst_ext_gnt_s = slv_ram_ext_gnt_s |
                    slv_misc_ext_gnt_s;
  end

  // FSM for Master 'ext'
  always_ff @(posedge main_clk_i or negedge main_rst_an_i) begin: proc_ext_fsm
    if (main_rst_an_i == 1'b0) begin
      fsm_ext_r <= fsm_idle_st;
      mst_ext_ram_gnt_r <= 1'b0;
      mst_ext_misc_gnt_r <= 1'b0;
    end else begin
      case (fsm_ext_r)
        fsm_idle_st: begin
          if (mst_ext_new_xfer_s == 1'b1) begin
            if (mst_ext_addr_err_s == 1'b1) begin
              fsm_ext_r <= fsm_error1_st;
            end else if (mst_ext_gnt_s == 1'b1) begin
              mst_ext_ram_req_r <= 1'b0;
              mst_ext_misc_req_r <= 1'b0;
              fsm_ext_r <= fsm_transfer_st;
            end else begin
              mst_ext_ram_req_r <= mst_ext_ram_sel_s;
              mst_ext_misc_req_r <= mst_ext_misc_sel_s;
              fsm_ext_r <= fsm_transfer_wait_st;
            end
            mst_ext_ram_gnt_r <= slv_ram_ext_gnt_s;
            mst_ext_misc_gnt_r <= slv_misc_ext_gnt_s;
          end
        end

        fsm_error0_st: begin
          if (mst_ext_hready_s == 1'b1) begin
            fsm_ext_r <= fsm_error1_st;
          end
        end

        fsm_error1_st: begin
          fsm_ext_r <= fsm_error2_st;
        end

        fsm_error2_st: begin
          if (mst_ext_new_xfer_s == 1'b1) begin
            if (mst_ext_addr_err_s == 1'b1) begin
              fsm_ext_r <= fsm_error1_st;
            end else if (mst_ext_gnt_s == 1'b1) begin
              mst_ext_ram_req_r <= 1'b0;
              mst_ext_misc_req_r <= 1'b0;
              fsm_ext_r <= fsm_transfer_st;
            end else begin
              mst_ext_ram_req_r <= mst_ext_ram_sel_s;
              mst_ext_misc_req_r <= mst_ext_misc_sel_s;
              fsm_ext_r <= fsm_transfer_wait_st;
            end
            mst_ext_ram_gnt_r <= slv_ram_ext_gnt_s;
            mst_ext_misc_gnt_r <= slv_misc_ext_gnt_s;
          end else begin
            fsm_ext_r <= fsm_idle_st;
          end
        end

        fsm_transfer_st: begin
          if ((ahb_mst_ext_htrans_i == ahb_trans_seq_e) ||
              (ahb_mst_ext_htrans_i == ahb_trans_busy_e)) begin
            fsm_ext_r <= fsm_transfer_st;
          end else begin
            if (ahb_mst_ext_htrans_i == ahb_trans_idle_e) begin
              if (mst_ext_hready_s == 1'b0) begin
                fsm_ext_r <= fsm_transfer_finish_st;
              end else begin
                mst_ext_ram_gnt_r <= 1'b0;
                mst_ext_misc_gnt_r <= 1'b0;
                fsm_ext_r <= fsm_idle_st;
              end
            end else begin // ((ahb_mst_ext_htrans_i == ahb_trans_nonseq_e)
              if (mst_ext_addr_err_s == 1'b1) begin
                if (mst_ext_hready_s == 1'b0) begin
                  fsm_ext_r <= fsm_error0_st;
                end else begin
                  fsm_ext_r <= fsm_error1_st;
                end
              end else if (mst_ext_gnt_s == 1'b1) begin
                mst_ext_ram_req_r <= 1'b0;
                mst_ext_misc_req_r <= 1'b0;
                fsm_ext_r <= fsm_transfer_st;
              end else begin
                mst_ext_ram_req_r <= mst_ext_ram_sel_s;
                mst_ext_misc_req_r <= mst_ext_misc_sel_s;
                fsm_ext_r <= fsm_transfer_wait_st;
              end
              mst_ext_ram_gnt_r <= slv_ram_ext_gnt_s;
              mst_ext_misc_gnt_r <= slv_misc_ext_gnt_s;
            end
          end
        end

        fsm_transfer_wait_st: begin
          if (mst_ext_gnt_s == 1'b1) begin
            mst_ext_ram_req_r <= 1'b0;
            mst_ext_misc_req_r <= 1'b0;
            mst_ext_ram_gnt_r <= slv_ram_ext_gnt_s;
            mst_ext_misc_gnt_r <= slv_misc_ext_gnt_s;
            fsm_ext_r <= fsm_transfer_st;
          end
        end

        fsm_transfer_finish_st: begin
          if (mst_ext_hready_s == 1'b1) begin
            if (mst_ext_new_xfer_s == 1'b1) begin
              if (mst_ext_addr_err_s == 1'b1) begin
                fsm_ext_r <= fsm_error1_st;
              end else if (mst_ext_gnt_s == 1'b1) begin
                mst_ext_ram_req_r <= 1'b0;
                mst_ext_misc_req_r <= 1'b0;
                fsm_ext_r <= fsm_transfer_st;
              end else begin
                mst_ext_ram_req_r <= mst_ext_ram_sel_s;
                mst_ext_misc_req_r <= mst_ext_misc_sel_s;
                fsm_ext_r <= fsm_transfer_wait_st;
              end
              mst_ext_ram_gnt_r <= slv_ram_ext_gnt_s;
              mst_ext_misc_gnt_r <= slv_misc_ext_gnt_s;
            end else begin
              mst_ext_ram_gnt_r <= 1'b0;
              mst_ext_misc_gnt_r <= 1'b0;
              fsm_ext_r <= fsm_idle_st;
            end
          end
        end

        default: begin
          mst_ext_ram_gnt_r <= 1'b0;
          mst_ext_ram_req_r <= 1'b0;
          mst_ext_misc_gnt_r <= 1'b0;
          mst_ext_misc_req_r <= 1'b0;
          fsm_ext_r <= fsm_idle_st;
        end
      endcase
    end

    if ((mst_ext_new_xfer_s == 1'b1) && (mst_ext_gnt_s == 1'b0) && (mst_ext_rqstate_s == 1'b1)) begin
      mst_ext_haddr_r  <= ahb_mst_ext_haddr_i;
      mst_ext_htrans_r <= ahb_mst_ext_htrans_i;
      mst_ext_hburst_r <= ahb_mst_ext_hburst_i;
      mst_ext_hsize_r  <= ahb_mst_ext_hsize_i;
      mst_ext_hwrite_r <= ahb_mst_ext_hwrite_i;
      mst_ext_hprot_r  <= ahb_mst_ext_hprot_i;
      mst_ext_hmastlock_r  <= ahb_mst_ext_hmastlock_i;
      mst_ext_hmaster_r  <= ahb_mst_ext_hmaster_i;
      mst_ext_hnonsec_r  <= ahb_mst_ext_hnonsec_i;
      mst_ext_hauser_r <= ahb_mst_ext_hauser_i;
    end

    mst_ext_hwrite_dph_r <= mst_ext_hwrite_s;
  end

  // Master 'ext' Mux
  always_comb begin: proc_ext_mux
    if (fsm_ext_r == fsm_transfer_wait_st) begin
      mst_ext_haddr_s  = mst_ext_haddr_r;
      mst_ext_hauser_s = mst_ext_hauser_r;
      mst_ext_hwrite_s = mst_ext_hwrite_r;
      mst_ext_hburst_s = mst_ext_hburst_r;
      mst_ext_hsize_s  = mst_ext_hsize_r;
      mst_ext_htrans_s = mst_ext_htrans_r;
      mst_ext_hprot_s  = mst_ext_hprot_r;
      mst_ext_hmastlock_s  = mst_ext_hmastlock_r;
      mst_ext_hmaster_s  = mst_ext_hmaster_r;
      mst_ext_hnonsec_s = mst_ext_hnonsec_r;
    end else begin
      mst_ext_haddr_s  = ahb_mst_ext_haddr_i;
      mst_ext_hauser_s = ahb_mst_ext_hauser_i;
      mst_ext_hwrite_s = ahb_mst_ext_hwrite_i;
      mst_ext_hburst_s = ahb_mst_ext_hburst_i;
      mst_ext_hsize_s  = ahb_mst_ext_hsize_i;
      mst_ext_htrans_s = ahb_mst_ext_htrans_i;
      mst_ext_hprot_s  = ahb_mst_ext_hprot_i;
      mst_ext_hmastlock_s  = ahb_mst_ext_hmastlock_i;
      mst_ext_hmaster_s  = ahb_mst_ext_hmaster_i;
      mst_ext_hnonsec_s = ahb_mst_ext_hnonsec_i;
    end

    mst_ext_hready_s = (ahb_slv_ram_hreadyout_i & mst_ext_ram_gnt_r) |
                       (ahb_slv_misc_hreadyout_i & mst_ext_misc_gnt_r) |
                       ~(|{mst_ext_ram_gnt_r, mst_ext_misc_gnt_r});

    case (fsm_ext_r)
      fsm_transfer_wait_st: begin
        ahb_mst_ext_hrdata_o = 32'h00000000;
        ahb_mst_ext_hready_o = 1'b0;
        ahb_mst_ext_hresp_o  = ahb_resp_okay_e;
        ahb_mst_ext_hruser_o = 4'h0;
        ahb_mst_ext_hbuser_o = 4'h2;
      end

      fsm_error1_st: begin
        ahb_mst_ext_hrdata_o = 32'h00000000;
        ahb_mst_ext_hready_o = 1'b0;
        ahb_mst_ext_hresp_o  = ahb_resp_error_e;
        ahb_mst_ext_hruser_o = 4'h0;
        ahb_mst_ext_hbuser_o = 4'h2;
      end

      fsm_error2_st: begin
        ahb_mst_ext_hrdata_o = 32'h00000000;
        ahb_mst_ext_hready_o = 1'b1;
        ahb_mst_ext_hresp_o  = ahb_resp_error_e;
        ahb_mst_ext_hruser_o = 4'h0;
        ahb_mst_ext_hbuser_o = 4'h2;
      end

      fsm_error0_st, fsm_transfer_st: begin
        case ({mst_ext_ram_gnt_r, mst_ext_misc_gnt_r})
          2'b01: begin
            ahb_mst_ext_hrdata_o = (mst_ext_hwrite_dph_r == 1'b0) ? ahb_slv_misc_hrdata_i : 32'h00000000;
            ahb_mst_ext_hready_o = ahb_slv_misc_hreadyout_i;
            ahb_mst_ext_hresp_o = ahb_slv_misc_hresp_i;
            ahb_mst_ext_hruser_o = (mst_ext_hwrite_dph_r == 1'b0) ? ahb_slv_misc_hruser_i : 4'h0;
            ahb_mst_ext_hbuser_o = (mst_ext_hwrite_dph_r == 1'b0) ? ahb_slv_misc_hbuser_i : 4'h2;
          end

          2'b10: begin
            ahb_mst_ext_hrdata_o = (mst_ext_hwrite_dph_r == 1'b0) ? ahb_slv_ram_hrdata_i : 32'h00000000;
            ahb_mst_ext_hready_o = ahb_slv_ram_hreadyout_i;
            ahb_mst_ext_hresp_o = ahb_slv_ram_hresp_i;
            ahb_mst_ext_hruser_o = (mst_ext_hwrite_dph_r == 1'b0) ? ahb_slv_ram_hruser_i : 4'h0;
            ahb_mst_ext_hbuser_o = (mst_ext_hwrite_dph_r == 1'b0) ? ahb_slv_ram_hbuser_i : 4'h2;
          end

          default: begin
            ahb_mst_ext_hrdata_o = 32'h00000000;
            ahb_mst_ext_hready_o = 1'b1;
            ahb_mst_ext_hresp_o  = ahb_resp_okay_e;
            ahb_mst_ext_hruser_o = 4'h0;
            ahb_mst_ext_hbuser_o = 4'h2;
          end
        endcase
      end

      fsm_transfer_finish_st: begin
        case ({mst_ext_ram_gnt_r, mst_ext_misc_gnt_r})
          2'b01: begin
            ahb_mst_ext_hrdata_o = ahb_slv_misc_hrdata_i;
            ahb_mst_ext_hready_o = ahb_slv_misc_hreadyout_i;
            ahb_mst_ext_hresp_o = ahb_slv_misc_hresp_i;
            ahb_mst_ext_hruser_o = ahb_slv_misc_hruser_i;
            ahb_mst_ext_hbuser_o = ahb_slv_misc_hbuser_i;
          end

          2'b10: begin
            ahb_mst_ext_hrdata_o = ahb_slv_ram_hrdata_i;
            ahb_mst_ext_hready_o = ahb_slv_ram_hreadyout_i;
            ahb_mst_ext_hresp_o = ahb_slv_ram_hresp_i;
            ahb_mst_ext_hruser_o = ahb_slv_ram_hruser_i;
            ahb_mst_ext_hbuser_o = ahb_slv_ram_hbuser_i;
          end

          default: begin
            ahb_mst_ext_hrdata_o = 32'h00000000;
            ahb_mst_ext_hready_o = 1'b1;
            ahb_mst_ext_hresp_o  = ahb_resp_okay_e;
            ahb_mst_ext_hruser_o = 4'h0;
            ahb_mst_ext_hbuser_o = 4'h2;
          end
        endcase
      end

      default: begin
        ahb_mst_ext_hrdata_o = 32'h00000000;
        ahb_mst_ext_hready_o = 1'b1;
        ahb_mst_ext_hresp_o  = ahb_resp_okay_e;
        ahb_mst_ext_hruser_o = 4'h0;
        ahb_mst_ext_hbuser_o = 4'h2;
      end
    endcase
  end

  // Master 'dsp' Logic
  always_comb begin: proc_dsp_logic
    mst_dsp_new_xfer_s  = (ahb_mst_dsp_htrans_i == ahb_trans_nonseq_e) ? 1'b1 : 1'b0;
    mst_dsp_cont_xfer_s = ((ahb_mst_dsp_htrans_i == ahb_trans_busy_e) ||
                           (ahb_mst_dsp_htrans_i == ahb_trans_seq_e)) ? 1'b1 : 1'b0;
    mst_dsp_rqstate_s   = ((fsm_dsp_r == fsm_idle_st) ||
                           (fsm_dsp_r == fsm_transfer_st) ||
                           (fsm_dsp_r == fsm_transfer_finish_st) ||
                           (fsm_dsp_r == fsm_error2_st)) ? 1'b1 : 1'b0;

    // Address Decoding
    mst_dsp_addr_err_s = 1'b0;
    mst_dsp_ram_sel_s = 1'b0;
    mst_dsp_periph_sel_s = 1'b0;

    casez (ahb_mst_dsp_haddr_i[35:16])
      20'b00001111000000000000: begin // ram
        mst_dsp_ram_sel_s = 1'b1;
      end

      20'b00001111000000000001: begin // periph
        mst_dsp_periph_sel_s = 1'b1;
      end

      default: begin
        mst_dsp_addr_err_s = mst_dsp_new_xfer_s;
      end
    endcase

    mst_dsp_ram_req_s    = (mst_dsp_ram_sel_s & mst_dsp_new_xfer_s & mst_dsp_rqstate_s) | mst_dsp_ram_req_r;
    mst_dsp_ram_keep_s   = mst_dsp_ram_gnt_r & mst_dsp_cont_xfer_s;
    mst_dsp_periph_req_s = (mst_dsp_periph_sel_s & mst_dsp_new_xfer_s & mst_dsp_rqstate_s) | mst_dsp_periph_req_r;

    // Grant Combination
    mst_dsp_gnt_s = slv_ram_dsp_gnt_s |
                    slv_periph_dsp_gnt_s;
  end

  // FSM for Master 'dsp'
  always_ff @(posedge main_clk_i or negedge main_rst_an_i) begin: proc_dsp_fsm
    if (main_rst_an_i == 1'b0) begin
      fsm_dsp_r <= fsm_idle_st;
      mst_dsp_ram_gnt_r <= 1'b0;
      mst_dsp_periph_gnt_r <= 1'b0;
    end else begin
      case (fsm_dsp_r)
        fsm_idle_st: begin
          if (mst_dsp_new_xfer_s == 1'b1) begin
            if (mst_dsp_addr_err_s == 1'b1) begin
              fsm_dsp_r <= fsm_error1_st;
            end else if (mst_dsp_gnt_s == 1'b1) begin
              mst_dsp_ram_req_r <= 1'b0;
              mst_dsp_periph_req_r <= 1'b0;
              fsm_dsp_r <= fsm_transfer_st;
            end else begin
              mst_dsp_ram_req_r <= mst_dsp_ram_sel_s;
              mst_dsp_periph_req_r <= mst_dsp_periph_sel_s;
              fsm_dsp_r <= fsm_transfer_wait_st;
            end
            mst_dsp_ram_gnt_r <= slv_ram_dsp_gnt_s;
            mst_dsp_periph_gnt_r <= slv_periph_dsp_gnt_s;
          end
        end

        fsm_error0_st: begin
          if (mst_dsp_hready_s == 1'b1) begin
            fsm_dsp_r <= fsm_error1_st;
          end
        end

        fsm_error1_st: begin
          fsm_dsp_r <= fsm_error2_st;
        end

        fsm_error2_st: begin
          if (mst_dsp_new_xfer_s == 1'b1) begin
            if (mst_dsp_addr_err_s == 1'b1) begin
              fsm_dsp_r <= fsm_error1_st;
            end else if (mst_dsp_gnt_s == 1'b1) begin
              mst_dsp_ram_req_r <= 1'b0;
              mst_dsp_periph_req_r <= 1'b0;
              fsm_dsp_r <= fsm_transfer_st;
            end else begin
              mst_dsp_ram_req_r <= mst_dsp_ram_sel_s;
              mst_dsp_periph_req_r <= mst_dsp_periph_sel_s;
              fsm_dsp_r <= fsm_transfer_wait_st;
            end
            mst_dsp_ram_gnt_r <= slv_ram_dsp_gnt_s;
            mst_dsp_periph_gnt_r <= slv_periph_dsp_gnt_s;
          end else begin
            fsm_dsp_r <= fsm_idle_st;
          end
        end

        fsm_transfer_st: begin
          if ((ahb_mst_dsp_htrans_i == ahb_trans_seq_e) ||
              (ahb_mst_dsp_htrans_i == ahb_trans_busy_e)) begin
            fsm_dsp_r <= fsm_transfer_st;
          end else begin
            if (ahb_mst_dsp_htrans_i == ahb_trans_idle_e) begin
              if (mst_dsp_hready_s == 1'b0) begin
                fsm_dsp_r <= fsm_transfer_finish_st;
              end else begin
                mst_dsp_ram_gnt_r <= 1'b0;
                mst_dsp_periph_gnt_r <= 1'b0;
                fsm_dsp_r <= fsm_idle_st;
              end
            end else begin // ((ahb_mst_dsp_htrans_i == ahb_trans_nonseq_e)
              if (mst_dsp_addr_err_s == 1'b1) begin
                if (mst_dsp_hready_s == 1'b0) begin
                  fsm_dsp_r <= fsm_error0_st;
                end else begin
                  fsm_dsp_r <= fsm_error1_st;
                end
              end else if (mst_dsp_gnt_s == 1'b1) begin
                mst_dsp_ram_req_r <= 1'b0;
                mst_dsp_periph_req_r <= 1'b0;
                fsm_dsp_r <= fsm_transfer_st;
              end else begin
                mst_dsp_ram_req_r <= mst_dsp_ram_sel_s;
                mst_dsp_periph_req_r <= mst_dsp_periph_sel_s;
                fsm_dsp_r <= fsm_transfer_wait_st;
              end
              mst_dsp_ram_gnt_r <= slv_ram_dsp_gnt_s;
              mst_dsp_periph_gnt_r <= slv_periph_dsp_gnt_s;
            end
          end
        end

        fsm_transfer_wait_st: begin
          if (mst_dsp_gnt_s == 1'b1) begin
            mst_dsp_ram_req_r <= 1'b0;
            mst_dsp_periph_req_r <= 1'b0;
            mst_dsp_ram_gnt_r <= slv_ram_dsp_gnt_s;
            mst_dsp_periph_gnt_r <= slv_periph_dsp_gnt_s;
            fsm_dsp_r <= fsm_transfer_st;
          end
        end

        fsm_transfer_finish_st: begin
          if (mst_dsp_hready_s == 1'b1) begin
            if (mst_dsp_new_xfer_s == 1'b1) begin
              if (mst_dsp_addr_err_s == 1'b1) begin
                fsm_dsp_r <= fsm_error1_st;
              end else if (mst_dsp_gnt_s == 1'b1) begin
                mst_dsp_ram_req_r <= 1'b0;
                mst_dsp_periph_req_r <= 1'b0;
                fsm_dsp_r <= fsm_transfer_st;
              end else begin
                mst_dsp_ram_req_r <= mst_dsp_ram_sel_s;
                mst_dsp_periph_req_r <= mst_dsp_periph_sel_s;
                fsm_dsp_r <= fsm_transfer_wait_st;
              end
              mst_dsp_ram_gnt_r <= slv_ram_dsp_gnt_s;
              mst_dsp_periph_gnt_r <= slv_periph_dsp_gnt_s;
            end else begin
              mst_dsp_ram_gnt_r <= 1'b0;
              mst_dsp_periph_gnt_r <= 1'b0;
              fsm_dsp_r <= fsm_idle_st;
            end
          end
        end

        default: begin
          mst_dsp_ram_gnt_r <= 1'b0;
          mst_dsp_ram_req_r <= 1'b0;
          mst_dsp_periph_gnt_r <= 1'b0;
          mst_dsp_periph_req_r <= 1'b0;
          fsm_dsp_r <= fsm_idle_st;
        end
      endcase
    end

    if ((mst_dsp_new_xfer_s == 1'b1) && (mst_dsp_gnt_s == 1'b0) && (mst_dsp_rqstate_s == 1'b1)) begin
      mst_dsp_haddr_r  <= ahb_mst_dsp_haddr_i;
      mst_dsp_htrans_r <= ahb_mst_dsp_htrans_i;
      mst_dsp_hburst_r <= ahb_mst_dsp_hburst_i;
      mst_dsp_hsize_r  <= ahb_mst_dsp_hsize_i;
      mst_dsp_hwrite_r <= ahb_mst_dsp_hwrite_i;
      mst_dsp_hprot_r  <= ahb_mst_dsp_hprot_i;
      mst_dsp_hmastlock_r  <= ahb_mst_dsp_hmastlock_i;
      mst_dsp_hmaster_r  <= ahb_mst_dsp_hmaster_i;
      mst_dsp_hnonsec_r  <= ahb_mst_dsp_hnonsec_i;
      mst_dsp_hauser_r <= ahb_mst_dsp_hauser_i;
    end

    mst_dsp_hwrite_dph_r <= mst_dsp_hwrite_s;
  end

  // Master 'dsp' Mux
  always_comb begin: proc_dsp_mux
    if (fsm_dsp_r == fsm_transfer_wait_st) begin
      mst_dsp_haddr_s  = mst_dsp_haddr_r;
      mst_dsp_hauser_s = mst_dsp_hauser_r;
      mst_dsp_hwrite_s = mst_dsp_hwrite_r;
      mst_dsp_hburst_s = mst_dsp_hburst_r;
      mst_dsp_hsize_s  = mst_dsp_hsize_r;
      mst_dsp_htrans_s = mst_dsp_htrans_r;
      mst_dsp_hprot_s  = mst_dsp_hprot_r;
      mst_dsp_hmastlock_s  = mst_dsp_hmastlock_r;
      mst_dsp_hmaster_s  = mst_dsp_hmaster_r;
      mst_dsp_hnonsec_s = mst_dsp_hnonsec_r;
    end else begin
      mst_dsp_haddr_s  = ahb_mst_dsp_haddr_i;
      mst_dsp_hauser_s = ahb_mst_dsp_hauser_i;
      mst_dsp_hwrite_s = ahb_mst_dsp_hwrite_i;
      mst_dsp_hburst_s = ahb_mst_dsp_hburst_i;
      mst_dsp_hsize_s  = ahb_mst_dsp_hsize_i;
      mst_dsp_htrans_s = ahb_mst_dsp_htrans_i;
      mst_dsp_hprot_s  = ahb_mst_dsp_hprot_i;
      mst_dsp_hmastlock_s  = ahb_mst_dsp_hmastlock_i;
      mst_dsp_hmaster_s  = ahb_mst_dsp_hmaster_i;
      mst_dsp_hnonsec_s = ahb_mst_dsp_hnonsec_i;
    end

    mst_dsp_hready_s = (ahb_slv_ram_hreadyout_i & mst_dsp_ram_gnt_r) |
                       (ahb_slv_periph_hreadyout_i & mst_dsp_periph_gnt_r) |
                       ~(|{mst_dsp_ram_gnt_r, mst_dsp_periph_gnt_r});

    case (fsm_dsp_r)
      fsm_transfer_wait_st: begin
        ahb_mst_dsp_hrdata_o = 32'h00000000;
        ahb_mst_dsp_hready_o = 1'b0;
        ahb_mst_dsp_hresp_o  = ahb_resp_okay_e;
        ahb_mst_dsp_hruser_o = 4'h0;
        ahb_mst_dsp_hbuser_o = 4'h2;
      end

      fsm_error1_st: begin
        ahb_mst_dsp_hrdata_o = 32'h00000000;
        ahb_mst_dsp_hready_o = 1'b0;
        ahb_mst_dsp_hresp_o  = ahb_resp_error_e;
        ahb_mst_dsp_hruser_o = 4'h0;
        ahb_mst_dsp_hbuser_o = 4'h2;
      end

      fsm_error2_st: begin
        ahb_mst_dsp_hrdata_o = 32'h00000000;
        ahb_mst_dsp_hready_o = 1'b1;
        ahb_mst_dsp_hresp_o  = ahb_resp_error_e;
        ahb_mst_dsp_hruser_o = 4'h0;
        ahb_mst_dsp_hbuser_o = 4'h2;
      end

      fsm_error0_st, fsm_transfer_st: begin
        case ({mst_dsp_ram_gnt_r, mst_dsp_periph_gnt_r})
          2'b01: begin
            ahb_mst_dsp_hrdata_o = (mst_dsp_hwrite_dph_r == 1'b0) ? ahb_slv_periph_hrdata_i : 32'h00000000;
            ahb_mst_dsp_hready_o = ahb_slv_periph_hreadyout_i;
            ahb_mst_dsp_hresp_o = ahb_slv_periph_hresp_i;
            ahb_mst_dsp_hruser_o = (mst_dsp_hwrite_dph_r == 1'b0) ? ahb_slv_periph_hruser_i : 4'h0;
            ahb_mst_dsp_hbuser_o = (mst_dsp_hwrite_dph_r == 1'b0) ? ahb_slv_periph_hbuser_i : 4'h2;
          end

          2'b10: begin
            ahb_mst_dsp_hrdata_o = (mst_dsp_hwrite_dph_r == 1'b0) ? ahb_slv_ram_hrdata_i : 32'h00000000;
            ahb_mst_dsp_hready_o = ahb_slv_ram_hreadyout_i;
            ahb_mst_dsp_hresp_o = ahb_slv_ram_hresp_i;
            ahb_mst_dsp_hruser_o = (mst_dsp_hwrite_dph_r == 1'b0) ? ahb_slv_ram_hruser_i : 4'h0;
            ahb_mst_dsp_hbuser_o = (mst_dsp_hwrite_dph_r == 1'b0) ? ahb_slv_ram_hbuser_i : 4'h2;
          end

          default: begin
            ahb_mst_dsp_hrdata_o = 32'h00000000;
            ahb_mst_dsp_hready_o = 1'b1;
            ahb_mst_dsp_hresp_o  = ahb_resp_okay_e;
            ahb_mst_dsp_hruser_o = 4'h0;
            ahb_mst_dsp_hbuser_o = 4'h2;
          end
        endcase
      end

      fsm_transfer_finish_st: begin
        case ({mst_dsp_ram_gnt_r, mst_dsp_periph_gnt_r})
          2'b01: begin
            ahb_mst_dsp_hrdata_o = ahb_slv_periph_hrdata_i;
            ahb_mst_dsp_hready_o = ahb_slv_periph_hreadyout_i;
            ahb_mst_dsp_hresp_o = ahb_slv_periph_hresp_i;
            ahb_mst_dsp_hruser_o = ahb_slv_periph_hruser_i;
            ahb_mst_dsp_hbuser_o = ahb_slv_periph_hbuser_i;
          end

          2'b10: begin
            ahb_mst_dsp_hrdata_o = ahb_slv_ram_hrdata_i;
            ahb_mst_dsp_hready_o = ahb_slv_ram_hreadyout_i;
            ahb_mst_dsp_hresp_o = ahb_slv_ram_hresp_i;
            ahb_mst_dsp_hruser_o = ahb_slv_ram_hruser_i;
            ahb_mst_dsp_hbuser_o = ahb_slv_ram_hbuser_i;
          end

          default: begin
            ahb_mst_dsp_hrdata_o = 32'h00000000;
            ahb_mst_dsp_hready_o = 1'b1;
            ahb_mst_dsp_hresp_o  = ahb_resp_okay_e;
            ahb_mst_dsp_hruser_o = 4'h0;
            ahb_mst_dsp_hbuser_o = 4'h2;
          end
        endcase
      end

      default: begin
        ahb_mst_dsp_hrdata_o = 32'h00000000;
        ahb_mst_dsp_hready_o = 1'b1;
        ahb_mst_dsp_hresp_o  = ahb_resp_okay_e;
        ahb_mst_dsp_hruser_o = 4'h0;
        ahb_mst_dsp_hbuser_o = 4'h2;
      end
    endcase
  end



  // ------------------------------------------------------
  // The Slaves:
  // ------------------------------------------------------
  // // Slave 'ram' round-robin arbiter
  always_comb begin: proc_ram_rr_arb
    integer i;
    logic found_s;
    logic [1:0] slv_req_s;
    logic [1:0] prev_grant_s;
    logic [1:0] next_grant_s;
    logic arb_en_s;

    slv_req_s = {mst_ext_ram_req_s, mst_dsp_ram_req_s};
    prev_grant_s = {slv_ram_ext_gnt_r, slv_ram_dsp_gnt_r};
    arb_en_s = ~(mst_ext_ram_keep_s | mst_dsp_ram_keep_s);

    next_grant_s = {prev_grant_s[0:0], prev_grant_s[1]}; // 1st candidate is old grant rotated 1 left
    found_s = 1'b0;
    for (i=0; i<2; i=i+1) begin
      if (found_s == 1'b0) begin
        if ((slv_req_s & next_grant_s) != 2'd0) begin
          found_s = 1'b1;
        end else begin
          next_grant_s = {next_grant_s[0:0], next_grant_s[1]}; // rotate 1 left
        end
      end
    end

    {slv_ram_ext_gnt_s, slv_ram_dsp_gnt_s} = slv_req_s & next_grant_s & {2{(ahb_slv_ram_hreadyout_i & arb_en_s)}};
  end


  always_ff @(posedge main_clk_i or negedge main_rst_an_i) begin: proc_ram_gnt
    if (main_rst_an_i == 1'b0) begin
      slv_ram_ext_gnt_r <= 1'b1;  // initial pseudo-grant
      slv_ram_dsp_gnt_r <= 1'b0;
    end else begin
      if ({slv_ram_ext_gnt_s, slv_ram_dsp_gnt_s} != 2'd0) begin
        slv_ram_ext_gnt_r <= slv_ram_ext_gnt_s;
        slv_ram_dsp_gnt_r <= slv_ram_dsp_gnt_s;
      end
    end
  end


  // Slave 'ram' multiplexer
  always_comb begin: proc_ram_mux
      slv_ram_ext_sel_s = slv_ram_ext_gnt_s |
                          (mst_ext_ram_keep_s & mst_ext_ram_gnt_r);
      slv_ram_dsp_sel_s = slv_ram_dsp_gnt_s |
                          (mst_dsp_ram_keep_s & mst_dsp_ram_gnt_r);

    ahb_slv_ram_hsel_o = |{slv_ram_ext_sel_s, slv_ram_dsp_sel_s};

    case ({slv_ram_ext_sel_s, slv_ram_dsp_sel_s})  // address phase signals
      2'b01: begin
        ahb_slv_ram_haddr_o     = mst_dsp_haddr_s;
        ahb_slv_ram_hwrite_o    = mst_dsp_hwrite_s;
        ahb_slv_ram_hburst_o    = mst_dsp_hburst_s;
        ahb_slv_ram_hsize_o     = mst_dsp_hsize_s;
        ahb_slv_ram_htrans_o    = mst_dsp_htrans_s;
        ahb_slv_ram_hprot_o     = {mst_dsp_hprot_s[3], 1'b0, mst_dsp_hprot_s[3], mst_dsp_hprot_s};
        ahb_slv_ram_hmastlock_o = mst_dsp_hmastlock_s;
        ahb_slv_ram_hmaster_o   = {2'h1, mst_dsp_hmaster_s};
        ahb_slv_ram_hnonsec_o   = mst_dsp_hnonsec_s;
        ahb_slv_ram_hauser_o    = mst_dsp_hauser_s;
        ahb_slv_ram_hready_o    = mst_dsp_hready_s;
      end

      2'b10: begin
        ahb_slv_ram_haddr_o     = mst_ext_haddr_s;
        ahb_slv_ram_hwrite_o    = mst_ext_hwrite_s;
        ahb_slv_ram_hburst_o    = mst_ext_hburst_s;
        ahb_slv_ram_hsize_o     = mst_ext_hsize_s;
        ahb_slv_ram_htrans_o    = mst_ext_htrans_s;
        ahb_slv_ram_hprot_o     = {mst_ext_hprot_s[3], 1'b0, mst_ext_hprot_s[3], mst_ext_hprot_s};
        ahb_slv_ram_hmastlock_o = mst_ext_hmastlock_s;
        ahb_slv_ram_hmaster_o   = {2'h0, mst_ext_hmaster_s};
        ahb_slv_ram_hnonsec_o   = mst_ext_hnonsec_s;
        ahb_slv_ram_hauser_o    = mst_ext_hauser_s;
        ahb_slv_ram_hready_o    = mst_ext_hready_s;
      end

      default: begin
        ahb_slv_ram_haddr_o     = 36'h000000000;
        ahb_slv_ram_hwrite_o    = ahb_write_read_e;
        ahb_slv_ram_hburst_o    = ahb_burst_single_e;
        ahb_slv_ram_hsize_o     = ahb_size_word_e;
        ahb_slv_ram_htrans_o    = ahb_trans_idle_e;
        ahb_slv_ram_hprot_o     = 7'h03;
        ahb_slv_ram_hmastlock_o = 1'b0;
        ahb_slv_ram_hmaster_o   = 6'h00;
        ahb_slv_ram_hnonsec_o   = 1'b0;
        ahb_slv_ram_hauser_o    = 4'h2;
        ahb_slv_ram_hready_o    = ahb_slv_ram_hreadyout_i;
      end
    endcase

    ahb_slv_ram_hexcl_o      = 1'b1;

    case ({mst_ext_ram_gnt_r, mst_dsp_ram_gnt_r})  // data phase signals
      2'b01: begin
        ahb_slv_ram_hwdata_o = ahb_mst_dsp_hwdata_i;
        ahb_slv_ram_hwstrb_o = ahb_mst_dsp_hwstrb_i;
        ahb_slv_ram_hwuser_o = ahb_mst_dsp_hwuser_i;
      end

      2'b10: begin
        ahb_slv_ram_hwdata_o = ahb_mst_ext_hwdata_i;
        ahb_slv_ram_hwstrb_o = ahb_mst_ext_hwstrb_i;
        ahb_slv_ram_hwuser_o = ahb_mst_ext_hwuser_i;
      end

      default: begin
        ahb_slv_ram_hwdata_o = 32'h00000000;
        ahb_slv_ram_hwstrb_o = 4'h0;
        ahb_slv_ram_hwuser_o = 4'h5;
      end
    endcase
  end

  // Slave 'periph': no arbitration necessary
  always_comb begin: proc_periph_asgn
    slv_periph_dsp_gnt_s = mst_dsp_periph_req_s;

    ahb_slv_periph_hsel_o        = mst_dsp_periph_req_s;  // address phase signals
    if (mst_dsp_periph_sel_s == 1'b1) begin
      ahb_slv_periph_haddr_o     = ahb_mst_dsp_haddr_i;
      ahb_slv_periph_hauser_o    = ahb_mst_dsp_hauser_i;
      ahb_slv_periph_hwrite_o    = ahb_mst_dsp_hwrite_i;
      ahb_slv_periph_hburst_o    = ahb_mst_dsp_hburst_i;
      ahb_slv_periph_hsize_o     = ahb_mst_dsp_hsize_i;
      ahb_slv_periph_htrans_o    = ahb_mst_dsp_htrans_i;
      ahb_slv_periph_hprot_o     = {ahb_mst_dsp_hprot_i[3], 1'b0, ahb_mst_dsp_hprot_i[3], ahb_mst_dsp_hprot_i};
      ahb_slv_periph_hmastlock_o = ahb_mst_dsp_hmastlock_i;
      ahb_slv_periph_hmaster_o   = {2'h1, ahb_mst_dsp_hmaster_i};
      ahb_slv_periph_hnonsec_o   = ahb_mst_dsp_hnonsec_i;
      ahb_slv_periph_hready_o    = mst_dsp_hready_s;
    end else begin
      ahb_slv_periph_haddr_o     = 36'h000000000;
      ahb_slv_periph_hwrite_o    = ahb_write_read_e;
      ahb_slv_periph_hburst_o    = ahb_burst_single_e;
      ahb_slv_periph_hsize_o     = ahb_size_word_e;
      ahb_slv_periph_htrans_o    = ahb_trans_idle_e;
      ahb_slv_periph_hprot_o     = 7'h03;
      ahb_slv_periph_hmastlock_o = 1'b0;
      ahb_slv_periph_hmaster_o   = 6'h00;
      ahb_slv_periph_hnonsec_o   = 1'b0;
      ahb_slv_periph_hauser_o    = 4'h2;
      ahb_slv_periph_hready_o    = ahb_slv_periph_hreadyout_i;
    end

    ahb_slv_periph_hexcl_o     = 1'b1;

    if (mst_dsp_periph_gnt_r == 1'b1) begin  // data phase signals
      ahb_slv_periph_hwdata_o = ahb_mst_dsp_hwdata_i;
      ahb_slv_periph_hwstrb_o = ahb_mst_dsp_hwstrb_i;
      ahb_slv_periph_hwuser_o = ahb_mst_dsp_hwuser_i;
    end else begin
      ahb_slv_periph_hwdata_o = 32'h00000000;
      ahb_slv_periph_hwstrb_o = 4'h0;
      ahb_slv_periph_hwuser_o = 4'h5;
    end
  end

  // Slave 'misc': no arbitration necessary
  always_comb begin: proc_misc_asgn
    slv_misc_ext_gnt_s = mst_ext_misc_req_s;

    ahb_slv_misc_hsel_o        = mst_ext_misc_req_s;  // address phase signals
    if (mst_ext_misc_sel_s == 1'b1) begin
      ahb_slv_misc_haddr_o     = ahb_mst_ext_haddr_i;
      ahb_slv_misc_hauser_o    = ahb_mst_ext_hauser_i;
      ahb_slv_misc_hwrite_o    = ahb_mst_ext_hwrite_i;
      ahb_slv_misc_hburst_o    = ahb_mst_ext_hburst_i;
      ahb_slv_misc_hsize_o     = ahb_mst_ext_hsize_i;
      ahb_slv_misc_htrans_o    = ahb_mst_ext_htrans_i;
      ahb_slv_misc_hprot_o     = {ahb_mst_ext_hprot_i[3], 1'b0, ahb_mst_ext_hprot_i[3], ahb_mst_ext_hprot_i};
      ahb_slv_misc_hmastlock_o = ahb_mst_ext_hmastlock_i;
      ahb_slv_misc_hmaster_o   = {2'h0, ahb_mst_ext_hmaster_i};
      ahb_slv_misc_hnonsec_o   = ahb_mst_ext_hnonsec_i;
      ahb_slv_misc_hready_o    = mst_ext_hready_s;
    end else begin
      ahb_slv_misc_haddr_o     = 36'h000000000;
      ahb_slv_misc_hwrite_o    = ahb_write_read_e;
      ahb_slv_misc_hburst_o    = ahb_burst_single_e;
      ahb_slv_misc_hsize_o     = ahb_size_word_e;
      ahb_slv_misc_htrans_o    = ahb_trans_idle_e;
      ahb_slv_misc_hprot_o     = 7'h03;
      ahb_slv_misc_hmastlock_o = 1'b0;
      ahb_slv_misc_hmaster_o   = 6'h00;
      ahb_slv_misc_hnonsec_o   = 1'b0;
      ahb_slv_misc_hauser_o    = 4'h2;
      ahb_slv_misc_hready_o    = ahb_slv_misc_hreadyout_i;
    end

    ahb_slv_misc_hexcl_o     = 1'b1;

    if (mst_ext_misc_gnt_r == 1'b1) begin  // data phase signals
      ahb_slv_misc_hwdata_o = ahb_mst_ext_hwdata_i;
      ahb_slv_misc_hwstrb_o = ahb_mst_ext_hwstrb_i;
      ahb_slv_misc_hwuser_o = ahb_mst_ext_hwuser_i;
    end else begin
      ahb_slv_misc_hwdata_o = 32'h00000000;
      ahb_slv_misc_hwstrb_o = 4'h0;
      ahb_slv_misc_hwuser_o = 4'h5;
    end
  end


endmodule // ucdp_ahb_ml_example_ml

`default_nettype wire
`end_keywords

// =============================================================================
//
//   @generated @fully-generated
//
//   THIS FILE IS GENERATED!!! DO NOT EDIT MANUALLY. CHANGES ARE LOST.
//
// =============================================================================
