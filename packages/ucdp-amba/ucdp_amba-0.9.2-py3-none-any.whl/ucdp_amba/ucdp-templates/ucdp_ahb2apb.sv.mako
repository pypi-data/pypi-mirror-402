##
## MIT License
##
## Copyright (c) 2024 nbiotcloud
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.
##

<%!
import ucdp as u
import ucdpsv as usv
from aligntext import Align
from ucdp_addr.addrslave import SlaveAddrspace
from icdutil import num


def decode_casez(decoding_slice: u.Slice, addrspace: SlaveAddrspace):
  size = addrspace.size >> decoding_slice.right
  base = addrspace.baseaddr >> decoding_slice.right
  masks = [f"{decoding_slice.width}'b{mask}" for mask in num.calc_addrwinmasks(base, size, decoding_slice.width, '?')]
  return ", ".join(masks)

%>
<%inherit file="sv.mako"/>

<%def name="logic(indent=0, skip=None)">\
<%
  rslvr = usv.get_resolver(mod)
  nr_slv = len(mod.slaves)
  dec_bits = [num.calc_lowest_bit_set(aspc.size) for aspc in mod.addrmap]
  dec_slice = u.Slice(left=mod.ahb_addrwidth-1, right=min(dec_bits))
  rng_bits = [num.calc_unsigned_width(aspc.size - 1) for aspc in mod.addrmap]
  paddr_slice = u.Slice(width=max(rng_bits))

  ff_dly = f"#{rslvr.ff_dly} " if rslvr.ff_dly else ""

  use_hstrb = mod.proto.has_wstrb
  use_pstrb = False
  for slv in mod.slaves:
    if slv.proto.has_wstrb:
      use_pstrb = True
      break
%>
${parent.logic(indent=indent, skip=skip)}\

  // ------------------------------------------------------
  // transfer decoding
  // ------------------------------------------------------
  always_comb begin: proc_xfer_dec_proc
    ahb_slv_sel_s = ahb_slv_hsel_i & ahb_slv_hready_i;
    if ((ahb_slv_sel_s == 1'b1) &&
        ((ahb_slv_htrans_i == ahb_trans_nonseq_e) || (ahb_slv_htrans_i == ahb_trans_seq_e))) begin
      new_xfer_s = 1'b1;
    end else begin
      new_xfer_s = 1'b0;
    end
    valid_addr_s = 1'b0;
% for aspc in mod.addrmap:
    apb_${aspc.name}_sel_s = 1'b0;
% endfor

    casez(ahb_slv_haddr_i[${dec_slice}])
% for aspc in mod.addrmap:
      ${decode_casez(dec_slice, aspc)}: begin // ${aspc.name}
        valid_addr_s = 1'b1;
        apb_${aspc.name}_sel_s = 1'b1;
      end

% endfor
      default: begin
        valid_addr_s = 1'b0;
      end
    endcase
% if use_pstrb:

    if (ahb_slv_hwrite_i == ahb_write_write_e) begin
%   if mod.datawidth == 32:
      case (ahb_slv_hsize_i)
        ahb_size_byte_e: begin
          case (ahb_slv_haddr_i[1:0])
            2'b11: begin
              size_strb_s = 4'b1000;
            end
            2'b10: begin
              size_strb_s = 4'b0100;
            end
            2'b01: begin
              size_strb_s = 4'b0010;
            end
            default: begin
              size_strb_s = 4'b0001;
            end
          endcase
        end

        ahb_size_halfword_e: begin
          size_strb_s = (ahb_slv_haddr_i[1] == 1'b1) ? 4'b1100 : 4'b0011;
        end

        default: begin
          size_strb_s = 4'b1111;
        end
      endcase
%   elif mod.datawidth == 16:
      case (ahb_slv_hsize_i)
        ahb_size_byte_e: begin
          size_strb_s = (ahb_slv_haddr_i[0] == 1'b1) ? 2'b10 : 2'b01;
        end

        default: begin
          size_strb_s = 2'b11;
        end
      endcase
%   endif
    end else begin
      size_strb_s = ${rslvr._get_uint_value(0, mod.datawidth//8)};
    end
% endif
  end

<%
  rdy_terms = []
  err_terms = []
  dta_terms = []
  for aspc in mod.addrmap:
    rdy_terms.append(f"(apb_slv_{aspc.name}_pready_i & apb_{aspc.name}_sel_r)")
    err_terms.append(f"(apb_slv_{aspc.name}_pslverr_i & apb_{aspc.name}_sel_r)")
    dta_terms.append(f"(apb_slv_{aspc.name}_prdata_i & {{{mod.datawidth}{{(~pwrite_r & penable_r & apb_{aspc.name}_sel_r)}}}})")
  rdy_terms = " |\n               ".join(rdy_terms)
  err_terms = " |\n                ".join(err_terms)
  dta_terms = " |\n               ".join(dta_terms)
  sels = [f"apb_{aspc.name}_sel_r" for aspc in mod.addrmap]
  if nr_slv > 1:
    selgrps = [" | ".join(sels[i:i+4]) for i in range(0, nr_slv, 4)]
    selgrps = " |\n                 ".join(selgrps)
    nosels = f"~({selgrps})"
  else:
    nosels = f"~{sels[0]}"

  use_hauser = False
  if mod.proto.ausertype is not None:
    for slv in mod.slaves:
      if mod.proto.ausertype == slv.proto.ausertype:
        use_hauser = True
        break
%>
  // ------------------------------------------------------
  // slave input multiplexing
  // ------------------------------------------------------
  always_comb begin: proc_slave_mux
    pready_s = ${rdy_terms};
    pslverr_s = ${err_terms};
    prdata_s = ${dta_terms};
% if mod.optbw:
    hready_s = hready_r & ((pready_s & ~pslverr_s) |
               ${nosels});
% endif
  end

  // ------------------------------------------------------
  // FSM
  // ------------------------------------------------------
  always_ff @ (posedge main_clk_i or negedge main_rst_an_i) begin: proc_fsm
    if (main_rst_an_i == 1'b0) begin
      fsm_r <= ${ff_dly}fsm_idle_st;
      hready_r <= ${ff_dly}1'b1;
% if not mod.errirq:
      hresp_r <= ${ff_dly}apb_resp_okay_e;
% endif
% if use_hauser:
      hauser_r <= ${ff_dly}${rslvr.get_default(mod.proto.ausertype)};
% endif
      paddr_r <= ${ff_dly}${rslvr._get_uint_value(0, paddr_slice.width)};
      pwrite_r <= ${ff_dly}1'b0;
      pwdata_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth)};
% if use_pstrb:
      pstrb_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth//8)};
% endif
      prdata_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth)};
      penable_r <= ${ff_dly}1'b0;
% for aspc in mod.addrmap:
      apb_${aspc.name}_sel_r <= ${ff_dly}1'b0;
% endfor
% if mod.errirq:
      irq_r <= ${ff_dly}1'b0;
% endif
    end else begin
      case (fsm_r)
        fsm_idle_st: begin
% if mod.errirq:
          irq_r <= ${ff_dly}new_xfer_s & ~valid_addr_s;
% endif
          if (new_xfer_s == 1'b1) begin
            if (valid_addr_s == 1'b1) begin
              hready_r <= ${ff_dly}1'b0;
% if use_hauser:
              hauser_r <= ${ff_dly}ahb_slv_hauser_i;
% endif
% if not mod.errirq:
              hresp_r <= ${ff_dly}apb_resp_okay_e;
% endif
              paddr_r <= ${ff_dly}ahb_slv_haddr_i[${paddr_slice}];
              pwrite_r <= ${ff_dly}ahb_slv_hwrite_i;
% if use_pstrb:
              pstrb_r <= ${ff_dly}size_strb_s;
% endif
% for aspc in mod.addrmap:
              apb_${aspc.name}_sel_r <= ${ff_dly}apb_${aspc.name}_sel_s;
% endfor
              fsm_r <= ${ff_dly}fsm_apb_ctrl_st;
% if mod.errirq:
            end
% else:
            end else begin
              hresp_r <= ${ff_dly}apb_resp_error_e;
              fsm_r <= ${ff_dly}fsm_ahb_err_st;
            end
          end else begin
            hresp_r <= ${ff_dly}apb_resp_okay_e;
% endif
          end
        end

        fsm_apb_ctrl_st: begin
          if (pwrite_r == 1'b1) begin
% if use_hstrb:
            hwstrb_r <= ${ff_dly}ahb_slv_hwstrb_i;
% endif
            pwdata_r <= ${ff_dly}ahb_slv_hwdata_i;
          end
          penable_r <= ${ff_dly}1'b1;
% if mod.optbw:
          hready_r <= ${ff_dly}1'b1;
% endif
          fsm_r <= ${ff_dly}fsm_apb_data_st;
        end

        fsm_apb_data_st: begin
          if (pready_s == 1'b1) begin
            penable_r <= ${ff_dly}1'b0;
% if mod.optbw:
%   if mod.errirq:
            irq_r <= ${ff_dly}pslverr_s | (new_xfer_s & ~valid_addr_s);
            if (new_xfer_s == 1'b1) begin
%   else:
            if (pslverr_s == 1'b1) begin
              hready_r <= ${ff_dly}1'b0;
              hresp_r <= ${ff_dly}apb_resp_error_e;
%   for aspc in mod.addrmap:
              apb_${aspc.name}_sel_r <= ${ff_dly}1'b0;
%   endfor
              fsm_r <= ${ff_dly}fsm_ahb_err_st;
            end else if (new_xfer_s == 1'b1) begin
%   endif
%   if not mod.errirq:
              hready_r <= ${ff_dly}1'b0;
%   endif
              if (valid_addr_s == 1'b1) begin
%   if mod.errirq:
                hready_r <= ${ff_dly}1'b0;
%   endif
%   if use_hauser:
                hauser_r <= ${ff_dly}ahb_slv_hauser_i;
%   endif
                paddr_r <= ${ff_dly}ahb_slv_haddr_i[${paddr_slice}];
                pwrite_r <= ${ff_dly}ahb_slv_hwrite_i;
%   if use_pstrb:
                pstrb_r <= ${ff_dly}size_strb_s;
%   endif
%   for aspc in mod.addrmap:
                apb_${aspc.name}_sel_r <= ${ff_dly}apb_${aspc.name}_sel_s;
%   endfor
                fsm_r <= ${ff_dly}fsm_apb_ctrl_st;
              end else begin
%   if mod.errirq:
                hready_r <= ${ff_dly}1'b1;
                pwrite_r <= ${ff_dly}1'b0;
                fsm_r <= ${ff_dly}fsm_idle_st;
%   else:
%   if use_pstrb:
              pstrb_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth//8)};
%   endif
%   for aspc in mod.addrmap:
                apb_${aspc.name}_sel_r <= ${ff_dly}1'b0;
%   endfor
                hresp_r <= ${ff_dly}apb_resp_error_e;
                fsm_r <= ${ff_dly}fsm_ahb_err_st;
%   endif
              end
            end else begin // no new xfer and no pslverr
              penable_r <= ${ff_dly}1'b0;
              hready_r <= ${ff_dly}1'b1;
              pwrite_r <= ${ff_dly}1'b0;
%   if use_pstrb:
              pstrb_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth//8)};
%   endif
%   for aspc in mod.addrmap:
              apb_${aspc.name}_sel_r <= ${ff_dly}1'b0;
%   endfor
              fsm_r <= ${ff_dly}fsm_idle_st;
            end
% else:  # not optbw
            prdata_r <= ${ff_dly}prdata_s;
%   for aspc in mod.addrmap:
            apb_${aspc.name}_sel_r <= ${ff_dly}1'b0;
%   endfor
            pwrite_r <= ${ff_dly}1'b0;
%   if use_pstrb:
            pstrb_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth//8)};
%   endif
%   if mod.errirq:
            hready_r <= ${ff_dly}1'b1;
            pwrite_r <= ${ff_dly}1'b0;
            irq_r <= ${ff_dly}pslverr_s;
            fsm_r <= ${ff_dly}fsm_idle_st;
%   else:
            if (pslverr_s == 1'b0) begin
              hready_r <= ${ff_dly}1'b1;
              hresp_r <= ${ff_dly}apb_resp_okay_e;
              fsm_r <= ${ff_dly}fsm_idle_st;
            end else begin
              hresp_r <= ${ff_dly}apb_resp_error_e;
              fsm_r <= ${ff_dly}fsm_ahb_err_st;
            end
%   endif
% endif
          end
        end

% if not mod.errirq:
        fsm_ahb_err_st: begin
          hready_r <= ${ff_dly}1'b1;
          fsm_r <= ${ff_dly}fsm_idle_st;
        end
% endif

        default: begin
          hready_r <= ${ff_dly}1'b1;
% if not mod.errirq:
          hresp_r <= ${ff_dly}apb_resp_okay_e;
% endif
          pwrite_r <= ${ff_dly}1'b0;
% if use_pstrb:
          pstrb_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth//8)};
% endif
          pwdata_r <= ${ff_dly}${rslvr._get_uint_value(0, mod.datawidth)};
          penable_r <= ${ff_dly}1'b0;
          paddr_r <= ${ff_dly}${rslvr._get_uint_value(0, paddr_slice.width)};
% for aspc in mod.addrmap:
          apb_${aspc.name}_sel_r <= ${ff_dly}1'b0;
% endfor
          fsm_r <= ${ff_dly}fsm_idle_st;
        end
      endcase
    end
  end

<%
  outp_asgn = Align(rtrim=True)
  outp_asgn.set_separators(" = ", first="  assign ")
  dzero = rslvr._get_uint_value(0, mod.datawidth)
  for aspc in mod.addrmap:
    asz = num.calc_unsigned_width(aspc.size - 1)
    azero = rslvr._get_uint_value(0, asz)
    outp_asgn.add_spacer(f"  // Slave {aspc.name!r}:")
    outp_asgn.add_row(f"apb_slv_{aspc.name}_paddr_o", f"(apb_{aspc.name}_sel_r  == 1'b1) ? paddr_r[{asz-1}:0] : {azero};")
    outp_asgn.add_row(f"apb_slv_{aspc.name}_pwrite_o", f"pwrite_r & apb_{aspc.name}_sel_r;")
    outp_asgn.add_row(f"apb_slv_{aspc.name}_pwdata_o", f"((pwrite_r & apb_{aspc.name}_sel_r)  == 1'b1) ? pwdata_s : {dzero};")
    outp_asgn.add_row(f"apb_slv_{aspc.name}_penable_o", f"penable_r & apb_{aspc.name}_sel_r;")
    outp_asgn.add_row(f"apb_slv_{aspc.name}_psel_o", f"apb_{aspc.name}_sel_r;")
    slvprot = mod.slaves[aspc.name].proto
    if slvprot.has_wstrb:
      if use_hstrb:
        outp_asgn.add_row(f"apb_slv_{aspc.name}_pstrb_o", "pstrb_r & hwstrb_s;")
      else:
        outp_asgn.add_row(f"apb_slv_{aspc.name}_pstrb_o", "pstrb_r;")
    pauser = slvprot.ausertype
    if pauser is not None:
      if use_hauser:
        outp_asgn.add_row(f"apb_slv_{aspc.name}_pauser_o", f"hauser_r;")
      else:
        outp_asgn.add_row(f"apb_slv_{aspc.name}_pauser_o", f"{rslvr.get_default(pauser)};")
%>
  // ------------------------------------------------------
  // output Assignments
  // ------------------------------------------------------
% if mod.optbw:
  assign ahb_slv_hreadyout_o = hready_s;
  assign ahb_slv_hrdata_o = prdata_s;
% else:
  assign ahb_slv_hreadyout_o = hready_r;
  assign ahb_slv_hrdata_o = prdata_r;
% endif
% if mod.errirq:
  assign ahb_slv_hresp_o = apb_resp_okay_e;
% else:
  assign ahb_slv_hresp_o = hresp_r;
% endif

  assign pwdata_s = (penable_r == 1'b1) ? pwdata_r : ahb_slv_hwdata_i;
% if use_hstrb:
  assign hwstrb_s = (penable_r == 1'b1) ? hwstrb_r : ahb_slv_hwstrb_i;
% endif

${outp_asgn.get()}
% if mod.errirq:

  assign irq_o = irq_r;
% endif

</%def>
