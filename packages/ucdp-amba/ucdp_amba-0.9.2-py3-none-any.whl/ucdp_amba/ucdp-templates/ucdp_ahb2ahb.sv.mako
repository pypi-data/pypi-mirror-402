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
from icdutil import num
from ucdp_amba import types as t
%>

<%inherit file="sv.mako"/>

<%def name="logic(indent=0, skip=None)">\

${parent.logic(indent=indent, skip=skip)}

<%
  rslvr = usv.get_resolver(mod)
  conv_spec = mod._conv_spec

  rslvr = usv.get_resolver(mod)
%>
  // TODO: handle async


  // === standard forwarding ============
  assign ahb_tgt_htrans_o = ahb_src_htrans_i;
  assign ahb_tgt_hwrite_o = ahb_src_hwrite_i;
  assign ahb_tgt_hsize_o = ahb_src_hsize_i;
  assign ahb_src_hresp_o = ahb_tgt_hresp_i;

${self.haddr_hdl(rslvr, conv_spec)}
${self.hburst_hdl(rslvr, conv_spec)}
${self.hsel_hdl(rslvr, conv_spec)}
${self.hdata_hdl(rslvr, conv_spec)}
${self.hwstrb_hdl(rslvr, conv_spec)}
${self.hready_hdl(rslvr, conv_spec)}
${self.hprot_hdl(rslvr, conv_spec)}
${self.hnonsec_hdl(rslvr, conv_spec)}
${self.hmastlock_hdl(rslvr, conv_spec)}
${self.hexcl_hdl(rslvr, conv_spec)}
${self.hexokay_hdl(rslvr, conv_spec)}
${self.hmaster_hdl(rslvr, conv_spec)}
${self.usertp_hdl("hauser", rslvr, conv_spec)}
${self.usertp_hdl("hwuser", rslvr, conv_spec)}
${self.usertp_hdl("hruser", rslvr, conv_spec)}
${self.usertp_hdl("hbuser", rslvr, conv_spec)}
</%def>


<%def name="haddr_hdl(rslvr, conv_spec)">\
<%
  cspec = conv_spec["haddr"]
  conv = cspec["descr"].conv
%>\
  // === haddr handling =================
% if conv == "forward":
  assign ahb_tgt_haddr_o = ahb_src_haddr_i;
% elif conv == "reduce":
  // ignoring MSBs of source
  assign ahb_tgt_haddr_o = ahb_src_haddr_i[${u.Slice(width=cspec["red"])}];
% else:  ## "expand"
  // extend target address MSBs
%   if isinstance(cspec["exp"], u.Port):
  assign ahb_tgt_haddr_o = {${cspec["exp"].name}, ahb_src_haddr_i};
%   else:
  assign ahb_tgt_haddr_o = {${rslvr.get_default(cspec["exp"])}, ahb_src_haddr_i};
%   endif
% endif
</%def>


<%def name="hsel_hdl(rslvr, conv_spec)">\
<%
  convdir = conv_spec["dir"]
%>\
% if convdir == "s2s" or convdir == "m2s":
  // === hsel handling ==================
% endif
% if convdir == "s2s":
  assign ahb_tgt_hsel_o = ahb_src_hsel_i;
% elif convdir == "m2s":
  assign ahb_tgt_hsel_o = 1'b1;
% endif
</%def>


<%def name="hburst_hdl(rslvr, conv_spec)">\
<%
  conv = conv_spec["hburst"]["descr"].conv
%>\
% if conv in ["forward", "tie-off"]:
  // === hburst handling ================
% endif
% if conv == "forward":
  assign ahb_tgt_hburst_o = ahb_src_hburst_i;
% elif conv == "tie-off":
  assign ahb_tgt_hburst_o = ahb_burst_incr_e;
% endif
</%def>


<%def name="hnonsec_hdl(rslvr, conv_spec)">\
<%
  conv = conv_spec["hnonsec"]["descr"].conv
%>\
% if conv in ["forward", "tie-off"]:
  // === hnonsec handling ================
% endif
% if conv == "forward":
  assign ahb_tgt_hnonsec_o = ahb_src_hnonsec_i;
% elif conv == "tie-off":
  assign ahb_tgt_hnonsec_o = ${rslvr.get_default(t.AhbNonsecType())};
% endif
</%def>


<%def name="hmastlock_hdl(rslvr, conv_spec)">\
<%
  conv = conv_spec["hmastlock"]["descr"].conv
%>\
% if conv in ["forward", "tie-off"]:
  // === hmastlock handling ================
% endif
% if conv == "forward":
  assign ahb_tgt_hmastlock_o = ahb_src_hmastlock_i;
% elif conv == "tie-off":
  assign ahb_tgt_hmastlock_o = ${rslvr.get_default(t.AhbMastlockType())};
% endif
</%def>


<%def name="hexcl_hdl(rslvr, conv_spec)">\
<%
  conv = conv_spec["hexcl"]["descr"].conv
%>\
% if conv in ["forward", "tie-off"]:
  // === hexcl handling ================
% endif
% if conv == "forward":
  assign ahb_tgt_hexcl_o = ahb_src_hexcl_i;
% elif conv == "tie-off":
  assign ahb_tgt_hexcl_o = ${rslvr.get_default(t.AhbExclType())};
% endif
</%def>


<%def name="hexokay_hdl(rslvr, conv_spec)">\
<%
  conv = conv_spec["hexokay"]["descr"].conv
%>\
% if conv in ["forward", "tie-off"]:
  // === hexokay handling ================
% endif
% if conv == "forward":
  assign ahb_src_hexokay_o = ahb_tgt_hexokay_i;
% elif conv == "tie-off":
  assign ahb_src_hexokay_o = ${rslvr.get_default(t.AhbHexokType())};
% endif
</%def>


<%def name="hready_hdl(rslvr, conv_spec)">\
<%
  convdir = conv_spec["dir"]
%>\
  // === hready handling ================
% if convdir == "m2m":
  assign ahb_src_hready_o = ahb_tgt_hready_i;
% elif convdir == "s2s":
  assign ahb_tgt_hready_o = ahb_src_hready_i;
  assign ahb_src_hreadyout_o = ahb_tgt_hreadyout_i;
% elif convdir == "m2s":
  assign ahb_src_hready_o = ahb_tgt_hreadyout_i;
  assign ahb_tgt_hready_o = ahb_tgt_hreadyout_i;
% elif convdir == "s2m":
  assign ahb_src_hreadyout_o = ahb_tgt_hready_i & ahb_src_hready_i;
% endif
</%def>


<%def name="hdata_hdl(rslvr, conv_spec)">\
<%
  ff_dly = f"#{rslvr.ff_dly} " if rslvr.ff_dly else ""
  cspec = conv_spec["hwdata"]
  conv = cspec["descr"].conv
%>\
  // === hxdata handling ================
% if conv == "forward":
  // just forward read/write data
  assign ahb_tgt_hwdata_o = ahb_src_hwdata_i;
  assign ahb_src_hrdata_o = ahb_tgt_hrdata_i;
% else:
<%
    ratio = cspec["ratio"]
    narr = cspec["narr"]
    if cspec["n2w"]:
      mxin = "tgt_hrdata"
      mxout = "src_hrdata"
      asgnin = "src_hwdata"
      asgnout = "tgt_hwdata"
    else:
      mxin = "src_hwdata"
      mxout = "tgt_hwdata"
      asgnin = "tgt_hrdata"
      asgnout = "src_hrdata"

    slclsb = num.calc_unsigned_width(narr-1) - 3
    slcw = num.calc_unsigned_width(ratio-1)
    decslc = u.Slice(right=slclsb, width=slcw)
    varslc = f"[{slcw-1}:0]" if slcw else ""
%>\
  // convert data from ${conv[8:]}
  always_ff @(posedge main_clk_i or negedge main_rst_an_i) begin: proc_addr_str
    logic ${varslc} dmux_sel_r;

    if (main_rst_an_i == 1'b0) begin
      dmux_sel_r <= ${ff_dly}${rslvr._get_uint_value(0, slcw)};
    end else begin
      if ((ahb_src_htrans_i == ahb_trans_nonseq_e) || (ahb_src_htrans_i == ahb_trans_seq_e)) begin
        dmux_sel_r <= ${ff_dly}ahb_src_haddr_i[${decslc}];
      end
    end
  end

  always_comb begin: proc_data_mux
    case(dmux_sel_r)
%   for sel in range(ratio-1, 0, -1):
      ${rslvr._get_uint_value(sel, slcw)}: begin
        ahb_${mxout}_o = ahb_${mxin}_i[${u.Slice(right=sel*narr, width=narr)}];
      end

%   endfor
      default: begin
        ahb_${mxout}_o = ahb_${mxin}_i[${u.Slice(width=narr)}];
      end
    endcase
  end

  assign ahb_${asgnout}_o = {${ratio}{ahb_${asgnin}_i}};
% endif
</%def>

<%def name="hwstrb_hdl(rslvr, conv_spec)">\
<%
  cspec = conv_spec["hwstrb"]
  conv = cspec["descr"].conv
%>\
% if conv not in ["n/a", "ignore"]:
  // === hwstrb handling =================
% endif
% if conv == "forward":
  assign ahb_tgt_hwstrb_o = ahb_src_hwstrb_i;
% elif conv.startswith("tie"):
  assign ahb_tgt_hwstrb_o = ${rslvr.get_default(cspec["tie"])};
% elif conv.startswith("convert"):
<%
    ratio = cspec["ratio"]
    narr = cspec["narr"]
    selw = num.calc_unsigned_width(ratio-1)
%>\
  // convert hwstrb from ${conv[8:]}
  always_comb begin: proc_strb_mux
    case(dmux_sel_r)
%   for sel in range(ratio-1, 0, -1):
<%
      pre = f"{rslvr._get_uint_value(0, (ratio-sel-1)*narr)}, " if sel < (ratio-1) else ""
      post =  f", {rslvr._get_uint_value(0, sel*narr)}" if sel > 0 else ""
%>\
      ${rslvr._get_uint_value(sel, selw)}: begin
%     if cspec["n2w"]:
        ahb_tgt_hwstrb_o = {${pre}ahb_src_hwstrb_i${post}};
%     else:
        ahb_tgt_hwstrb_o = ahb_src_hwstrb_i[${u.Slice(right=sel*narr, width=narr)}];
%     endif
      end

%   endfor
      default: begin
%   if cspec["n2w"]:
        ahb_tgt_hwstrb_o = {${rslvr._get_uint_value(0, (ratio-1)*narr)}, ahb_src_hwstrb_i};
%   else:
        ahb_tgt_hwstrb_o = ahb_src_hwstrb_i[${u.Slice(width=narr)}];
%   endif
      end
    endcase
  end
% endif
</%def>


<%def name="hprot_hdl(rslvr, conv_spec)">\
<%
  cspec = conv_spec["hprot"]
  conv = cspec["descr"].conv
%>\
% if conv not in ["n/a", "ignore"]:
  // === hprot handling =================
% endif
% if conv == "forward":
  assign ahb_tgt_hprot_o = ahb_src_hprot_i;
% elif conv.startswith("tie"):
%   if isinstance(cspec["tie"], u.Port):
  assign ahb_tgt_hprot_o =  ${cspec["tie"].name};
%   else:
  assign ahb_tgt_hprot_o = ${rslvr.get_default(cspec["tie"])};
%   endif
% elif conv == "reduce":
  assign ahb_tgt_hprot_o = ahb_src_hprot_i[3:0];
% elif conv.startswith("expand"):
%   if cspec["exp"] is None:
  assign ahb_tgt_hprot_o = {ahb_src_hprot_i[3], 1'b0, ahb_src_hprot_i[3], ahb_src_hprot_i};
%   elif isinstance(cspec["exp"], u.Port):
  assign ahb_tgt_hprot_o = {${cspec["exp"].name}, ahb_src_hprot_i};
%   else:
  assign ahb_tgt_hprot_o = {${rslvr.get_default(cspec["exp"])}, ahb_src_hprot_i};
%   endif
% endif
</%def>


<%def name="hmaster_hdl(rslvr, conv_spec)">\
<%
  cspec = conv_spec["hmaster"]
  conv = cspec["descr"].conv
%>\
% if conv not in ["n/a", "ignore"]:
  // === hmaster handling: ${conv} =================
% endif
% if conv == "forward":
  assign ahb_tgt_hmaster_o = ahb_src_hmaster_i;
% elif conv.startswith("tie"):
%   if isinstance(cspec["tie"], u.Port):
  assign ahb_tgt_hmaster_o = ${cspec["tie"].name};
%   else:
  assign ahb_tgt_hmaster_o = ${rslvr.get_default(cspec["tie"])};
%   endif
% elif conv == "reduce":
  assign ahb_tgt_hmaster_o = ahb_src_hmaster_i[${u.Slice(width=cspec["red"])}];
% elif conv.startswith("expand"):
%   if isinstance(cspec["exp"], u.Port):
  assign ahb_tgt_hmaster_o = {${cspec["exp"].name}, ahb_src_hmaster_i};
%   else:
  assign ahb_tgt_hmaster_o = {${rslvr.get_default(cspec["exp"])}, ahb_src_hmaster_i};
%   endif
% endif
</%def>


<%def name="usertp_hdl(usrsig, rslvr, conv_spec)">\
<%
  cspec = conv_spec[usrsig]
  conv = cspec["descr"].conv
  if usrsig in ["hauser", "hwuser"]:
    snd, rcv = "src", "tgt"
  else:
    snd, rcv = "tgt", "src"
%>\
% if conv not in ["n/a", "ignore"]:
  // === ${usrsig} handling =================
% endif
% if conv == "forward":
  assign ahb_${rcv}_${usrsig}_o = ahb_${snd}_${usrsig}_i;
% elif conv.startswith("tie"):
%   if isinstance(cspec["tie"], u.Port):
  assign ahb_${rcv}_${usrsig}_o = ${cspec["tie"].name};
%   elif isinstance(cspec["tie"], str):
  assign ahb_${rcv}_${usrsig}_o = ${f"{rcv}_{usrsig}_{cspec['tie']}_e"};
%   else:
  assign ahb_${rcv}_${usrsig}_o = ${rslvr.get_default(cspec["tie"])};
%   endif
% elif conv == "reduce":
  assign ahb_${rcv}_${usrsig}_o = ahb_${snd}_${usrsig}_i[${u.Slice(width=cspec["red"])}];
% elif conv.startswith("expand"):
%   if isinstance(cspec["exp"], u.Port):
  assign ahb_${rcv}_${usrsig}_o = {${cspec["exp"].name}, ahb_${snd}_${usrsig}_i};
%   else:
  assign ahb_${rcv}_${usrsig}_o = {${rslvr.get_default(cspec["exp"])}, ahb_${snd}_${usrsig}_i};
%   endif
% elif conv == "convert":
<%
    utp = cspec["utp"]
    casemap = {}
    for key, value in cspec["map"].items():
      if key is None:
        continue
      kk = rslvr.get_default(key) if utp in ["u2u", "u2e"] else f"{snd}_{usrsig}_{key}_e"
      vv = rslvr.get_default(value) if utp in ["u2u", "e2u"] else f"{rcv}_{usrsig}_{value}_e"
      casemap[kk] = vv
    defval = cspec["map"][None]
    dflt = rslvr.get_default(defval) if utp in ["u2u", "e2u"] else f"{rcv}_{usrsig}_{defval}_e"
%>\
  // map ${usrsig} values
  always_comb begin: proc_${usrsig}_mux
    case(ahb_${snd}_${usrsig}_i)
%   for key, value in casemap.items():
      ${key}: begin
        ahb_${rcv}_${usrsig}_o = ${value};
      end

%   endfor
      default: begin
        ahb_${rcv}_${usrsig}_o = ${dflt};
      end
    endcase
  end
% endif
</%def>
