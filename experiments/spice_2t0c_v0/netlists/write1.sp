********************************************************************************
*  write1.sp
*  Write 1 transient for a single 2T0C cell.
*  Zhu paper Fig. 7(b) bias conditions.
*
*  Differences from write0.sp:
*    WBL held at V_WBL_WR_1 = 1.2 V during the write window.
*
*  Expected: SN charges to ~V_WBL_WR_1 = 1.2 V during the write
*  pulse, with a small coupling-induced transient.
********************************************************************************

.include igzo_2t0c_v0.lib
.include zhu_2t0c_parasitics.inc
.include cell_2t0c.inc

* ---- DC paths for floating nodes ----
R_SN_GND  SN   0  1e12

* ---- Bias sources (pulse) ----
*  WWL pulse: -0.8 V -> 1.5 V at t=1ns, fall at t=11ns
V_WWL  WWL_drv  0  PWL(0 -0.8  1n -0.8  1.0001n 1.5  11n 1.5  11.0001n -0.8  20n -0.8)
*  WBL held at 1.2 V (write data 1) -- MODELING_CHOICE
V_WBL  WBL_drv  0  1.2
*  RWL held at 0 V (read disabled)
V_RWL  RWL_drv  0  0
*  RBL held at 0 V
V_RBL  RBL_drv  0  0
*  V_DD for sense stub
V_DD   VDD      0  1.2

* ---- Line resistances (lumped unit-cell) ----
R_WWL  WWL_drv  WWL  {R_WWL}
R_WBL  WBL_drv  WBL  {R_WBL}
R_RWL  RWL_drv  RWL  {R_RWL}
R_RBL  RBL_drv  RBL  {R_RBL}

* ---- 2T0C cell ----
X_CELL  WWL  WBL  RWL  RBL  SN  X2T0C

* ---- Sense stub ----
R_RBL_PU  RBL  VDD  100k

* ---- Transient ----
.tran 0.1n 20n
.print tran v(wwl) v(wbl) v(rwl) v(rbl) v(sn) v(vdd) i(v_WWL) i(v_WBL) i(v_RBL) i(v_DD)
.end
