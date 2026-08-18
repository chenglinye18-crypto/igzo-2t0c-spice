********************************************************************************
*  zhu_2t0c_parasitics.inc
*  --------------------------------------------------------------------
*  2T0C unit-cell parasitic R/C values, paper-anchored to Zhu IEDM 2026
*  Fig. 4(b).  Values are read off the axis ticks of Fig. 4(b) and are
*  approximate (+/- 20 %).  They are NOT numerically tabulated in the
*  paper text.
*
*  These values define the v0 LUMPED unit-cell parasitic network.  The
*  full 512x512 distributed RC network is OUT OF SCOPE for v0.
*
*  Reference: experiments/spice_2t0c_v0/reference_notes.md (Section 4)
*
*  Sign convention for the supply-monitor resistors (R_WWL_S, etc.):
*  they sit on the *driver* side of the line resistance and are 0 ohm
*  in v0; the LUMPED unit-cell line resistance R_WWL accounts for the
*  full cell-to-driver drop.  This is a v0 simplification.
********************************************************************************

* ---- Line resistances (unit-cell) ----
*  Read from Fig 4(b) axis: 0..5 ohm; 4 bars.
.PARAM R_WWL  = 3.0
.PARAM R_RWL  = 3.0
.PARAM R_WBL  = 2.0
.PARAM R_RBL  = 2.0

* ---- Line-to-line coupling caps (unit-cell) ----
*  Read from Fig 4(b) axis: 0..5 aF; 4 bars.
.PARAM C_WWL_WWL  = 0.5e-18
.PARAM C_RWL_RWL  = 0.5e-18
.PARAM C_WBL_WBL  = 0.5e-18
.PARAM C_RBL_RBL  = 0.5e-18

* ---- Node coupling caps (unit-cell, Fig 4(b) axis 0..35 aF) ----
.PARAM C_WWL_SN  = 25.0e-18
.PARAM C_RWL_SN  = 25.0e-18
.PARAM C_WBL_SN  = 5.0e-18
.PARAM C_RBL_SN  = 5.0e-18

* ---- v0 SIMPLIFICATION: ground-referenced cap to close the network ----
*  Without a ground, the coupling caps carry no DC displacement current
*  in transient.  Add a small GND-referenced cap to each line so the
*  SPICE matrix is well-posed for a single cell.
*  This is a v0 lumped approximation of the array's line-to-substrate
*  capacitance.  Value picked to be small (0.1 fF) so it does NOT
*  dominate the coupling-cap behavior.
.PARAM C_WWL_GND = 0.1e-15
.PARAM C_RWL_GND = 0.1e-15
.PARAM C_WBL_GND = 0.1e-15
.PARAM C_RBL_GND = 0.1e-15
