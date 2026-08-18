********************************************************************************
*  dc_idvg.sp
*  Id-Vg sweep for the Zhu 2T0C surrogate device, at Vd = 0.1 V and 1 V.
*  Matches the conditions of Zhu paper Fig. 5(d).
*
*  Outputs (ASCII, in the .log file):
*    index  vg-sweep  v(d)  i(vd)
*
*  The current through the Vd source is the drain current of the OSFET.
*  Sign convention: positive Id = conventional current INTO the drain.
********************************************************************************
* Path: experiments/spice_2t0c_v0/netlists/dc_idvg.sp

* ---- include the surrogate device library ----
.include ../models/igzo_2t0c_v0.lib

* ---- sweep Vg, Vd held at fixed values ----
*  Vd = 0.1 V
Vd_lo   D_lo  0  0.1
Vg_lo   G_lo  0  0
X1_lo   D_lo  G_lo  0  XOSFET_DC
.dc Vg_lo -1 2 0.05
.print dc v(g_lo) i(vd_lo)
.end

*  Vd = 1 V  (separate circuit, run via run_spice.py)
