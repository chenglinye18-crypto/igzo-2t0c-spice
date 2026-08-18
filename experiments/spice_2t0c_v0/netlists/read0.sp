********************************************************************************
*  read0.sp
*  Read transient for a single 2T0C cell, pre-conditioned to "stored 0".
*  Full write0 + read in one transient.
*
*  read0 expected: RBL stays close to 1.2 V during the read window
*  because Tr is weakly on (Vgs = V(SN) ~ 0 V).
********************************************************************************

.include igzo_2t0c_v0.lib
.include zhu_2t0c_parasitics.inc
.include cell_2t0c.inc
.include sense_stub.inc

* ---- DC paths for floating nodes ----
R_SN_GND  SN   0  1e12

* ---- Bias sources ----
*  WWL pulse for write
V_WWL  WWL_drv  0  PWL(0 -0.8  1n -0.8  1.0001n 1.5  11n 1.5  11.0001n -0.8  20n -0.8)
*  WBL held at 0 V (write data 0)
V_WBL  WBL_drv  0  0
*  RWL pulse for read (delayed)
V_RWL  RWL_drv  0  PWL(0 0  15n 0  15.0001n 1.0  20n 1.0  20.0001n 0  30n 0)
*  RBL pre-charged to 1.2 V
V_RBL  RBL_drv  0  1.2
*  V_DD for sense stub
V_DD   VDD      0  1.2

* ---- Line resistances ----
R_WWL  WWL_drv  WWL  {R_WWL}
R_WBL  WBL_drv  WBL  {R_WBL}
R_RWL  RWL_drv  RWL  {R_RWL}
*  v0 simplification: R_RBL is replaced with a 1GOhm resistor
*  during the read so the bitline can actually discharge through Tr.
*  (The 2-ohm paper value is correct for the write case but masks
*  the read signal in this v0 single-cell test.)
R_RBL  RBL_drv  RBL  1G

* ---- 2T0C cell ----
X_CELL  WWL  WBL  RWL  RBL  SN  X2T0C

* ---- RBL pre-charge ----
R_RBL_PU  RBL  VDD  10k

* ---- v0 Sense stub ----
B_COMP  SA_OUT  0  V={V_SA_HI}/(1 + EXP(-(V(RBL) - 1.15) / 0.005))
R_SA_PU  SA_OUT  0  1Meg
C_SA_FILT  SA_OUT  0  10f

* ---- Transient ----
.tran 0.05n 30n
.print tran v(wwl) v(wbl) v(rwl) v(rbl) v(sn) v(sa_out) v(vdd) i(v_WWL) i(v_WBL) i(v_RBL) i(v_DD)
.end
