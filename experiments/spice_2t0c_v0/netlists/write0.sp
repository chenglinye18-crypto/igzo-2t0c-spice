********************************************************************************
*  write0.sp
*  Write 0 transient for a single 2T0C cell.
*  Zhu paper Fig. 7(b) bias conditions.
*
*  Timing (v0, MODELING_CHOICE -- paper shows write window ~5 ns):
*      t = 0      : all lines at rest
*      t = 1 ns   : WWL rises from V_WWL_OFF = -0.8 V to V_WWL_WR = 1.5 V
*      t = 11 ns  : WWL falls back to -0.8 V
*      t = 20 ns  : end of transient
*
*  WBL is held at 0 V during write (WBL_WR_0 = 0 V, MODELING_CHOICE).
*  RBL is held at 0 V (RBL quiescent).
*  RWL is held at 0 V (read disabled).
*
*  Outputs:
*      v(wwl), v(wbl), v(rwl), v(rbl), v(sn)
*      i(vwwl_drv), i(vwbl_drv), i(vdd_sa) -- supply currents
*      v(sa_out)   -- sense output (stays low during write)
********************************************************************************

.include igzo_2t0c_v0.lib
.include zhu_2t0c_parasitics.inc
.include cell_2t0c.inc

* ---- DC paths for floating nodes (SN) ----
*  Real DRAM cells have sub-threshold leakage from the OSFETs which
*  provides a DC path.  The B-source model gives 0 DC current at Vgs=0
*  (only a tiny floor of 1e-12 A through the sub-threshold exp), so
*  we add 1 TOhm resistors to provide numerical DC paths.
R_SN_GND  SN   0  1e12

* ---- Bias sources (pulse) ----
*  WWL pulse: -0.8 V -> 1.5 V at t=1ns, fall at t=11ns
V_WWL  WWL_drv  0  PWL(0 -0.8  1n -0.8  1.0001n 1.5  11n 1.5  11.0001n -0.8  20n -0.8)
*  WBL held at 0 V (write data 0)
V_WBL  WBL_drv  0  0
*  RWL held at 0 V (read disabled)
V_RWL  RWL_drv  0  0
*  RBL held at 0 V (read pre-charge to 0 in v0; pull-up via 10k to 1.2V
*  for sense current path)
V_RBL  RBL_drv  0  0
*  V_DD for sense stub (always-on in v0 to keep the SA bias path closed)
V_DD   VDD      0  1.2

* ---- Line resistances (lumped unit-cell) ----
R_WWL  WWL_drv  WWL  {R_WWL}
R_WBL  WBL_drv  WBL  {R_WBL}
R_RWL  RWL_drv  RWL  {R_RWL}
R_RBL  RBL_drv  RBL  {R_RBL}

* ---- 2T0C cell ----
X_CELL  WWL  WBL  RWL  RBL  SN  X2T0C

* ---- Sense stub (disabled during write) ----
*  RBL pull-up to V_DD through 100k (small pre-charge)
R_RBL_PU  RBL  VDD  100k

* ---- Transient ----
.tran 0.1n 20n
.print tran v(wwl) v(wbl) v(rwl) v(rbl) v(sn) v(vdd) i(v_WWL) i(v_WBL) i(v_RBL) i(v_DD)
.end
