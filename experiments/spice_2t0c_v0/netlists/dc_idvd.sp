********************************************************************************
*  dc_idvd.sp
*  Id-Vd sweep for the Zhu 2T0C surrogate device, at Vg = 0.4 V, 1.2 V, 2.0 V.
*  Matches the conditions of Zhu paper Fig. 5(e).
*
*  Outputs (ASCII, in the .log file):
*    index  vd-sweep  v(d)  i(vd)
********************************************************************************
* Path: experiments/spice_2t0c_v0/netlists/dc_idvd.sp

.include ../models/igzo_2t0c_v0.lib

*  Vg = 0.4 V
Vd_0p4  D_0p4  0  0
Vg_0p4  G_0p4  0  0.4
X1_0p4  D_0p4  G_0p4  0  XOSFET_DC
.dc Vd_0p4 0 3 0.1
.print dc v(d_0p4) i(vd_0p4)
.end

*  Vg = 1.2 V, 2.0 V via run_spice.py separate runs
