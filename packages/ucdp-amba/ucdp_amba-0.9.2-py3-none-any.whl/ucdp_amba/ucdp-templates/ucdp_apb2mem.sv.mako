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
import ucdpsv as usv
%>

<%inherit file="sv.mako"/>

<%def name="logic(indent=0, skip=None)">\
<%
rslvr = usv.get_resolver(mod)
%>\
${parent.logic(indent=indent, skip=skip)}\

assign mem_ena_o = apb_slv_penable_i & apb_slv_psel_i;
assign mem_addr_o = apb_slv_paddr_i${rslvr.resolve_slice(mod.addrslice)};
assign mem_wena_o = apb_slv_pwrite_i;
assign mem_wdata_o = apb_slv_pwdata_i;

assign apb_slv_prdata_o = mem_rdata_i;
assign apb_slv_pslverr_o = mem_err_i;
assign apb_slv_pready_o = 1'b1;
</%def>
