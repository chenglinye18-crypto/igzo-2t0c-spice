********************************************************************************
*  cell_2t0c.inc
*  --------------------------------------------------------------------
*  Single 2T0C cell subcircuit (Zhu IEDM 2026, Fig. 3(d) / Fig. 7(b)).
*  Five external ports:
*      WWL -- write word line
*      WBL -- write bit line
*      RWL -- read  word line
*      RBL -- read  bit line
*      SN  -- storage node (also an external port; tied internally
*             to the drain of Tw and the gate of Tr)
*
*  The cell contains:
*    - Tw (write OSFET): gate=WWL, source=WBL, drain=SN, body=SN
*    - Tr (read OSFET):  gate=SN,  source=RBL, drain=?? (open in v0)
*        v0 simplification: Tr drain is an internal node, brought out
*        only as the cell output to the sense amplifier.  The v0
*        sense-stub model is in sense_stub.inc.
*
*  The 2T0C has NO explicit capacitor.  The SN capacitance is
*  dominated by C_WWL_SN + C_RWL_SN + the Tw gate-drain + Tr gate-source
*  overlap.  v0 uses only the four coupling caps defined in
*  zhu_2t0c_parasitics.inc.
*
*  The line resistors and line-to-line caps (R_WWL, R_RWL, ...) are
*  NOT included inside the cell subcircuit; they are on the line
*  driver side and are included by the transient netlist as external
*  discrete elements.  This keeps the cell subcircuit small and
*  reusable.
********************************************************************************

*  X2T0C -- 2T0C cell
*  Node list (must match .SUBCKT line below):
*      WWL WBL RWL RBL SN TRD
*  TRD = Tr drain, brought out so the netlist can connect a sense
*  stub or a DC path.
.SUBCKT X2T0C WWL WBL RWL RBL SN
*  Write transistor: gate=WWL, drain=SN, source=WBL, body=SN
X_Tw  SN  WWL  WBL  SN  XOSFET_2T0C
*  Read transistor:  gate=SN,  drain=RBL, source=0 (ground), body=0
*  v0 simplification: Tr source tied to ground so the read current
*  flows from RBL (pre-charged) through Tr to ground when SN is high.
*  This deviates from Fig. 3(d) (which shows Tr on a separate SL),
*  but it preserves the read-current-vs-SN relationship without
*  requiring a sixth port.  MODELING_CHOICE.
X_Tr  RBL  SN  0  0  XOSFET_2T0C

* Parasitic coupling caps at the SN node (all unit-cell, lumped)
*  SN -- WWL gate overlap of Tw (C_WWL_SN)
C_WWL_SN  WWL  SN  {C_WWL_SN}
*  SN -- RWL gate overlap of Tr (C_RWL_SN)
C_RWL_SN  RWL  SN  {C_RWL_SN}
*  SN -- WBL overlap
C_WBL_SN  WBL  SN  {C_WBL_SN}
*  SN -- RBL overlap (Tr drain-to-SN, included for symmetry)
C_RBL_SN  RBL  SN  {C_RBL_SN}

* v0 ADDITION: an explicit SN-to-ground capacitance that approximates
*  the total storage-node capacitance (the intrinsic C of the stacked
*  CAA structure, the gate-drain overlap of Tw, the gate-source of Tr,
*  the metal-to-metal fringe capacitance, etc.).  Without this the WWL
*  capacitive coupling completely dominates the SN, and the cell
*  cannot hold a defined state.
*
*  The paper reports C_WWL_SN ~25 aF and C_RWL_SN ~25 aF as the
*  coupling caps; the intrinsic SN cap is NOT reported explicitly.
*  v0 picks C_SN = 1 fF (same order of magnitude as the 1T1C C_s = 3 fF
*  used in Zhu's 1T1C baseline; 2T0C SN is expected to be smaller
*  because the SN sits between two transistors, not a dedicated cap).
*
*  C_SN = 1 fF   (MODELING_CHOICE)
.PARAM C_SN_INTRINSIC = 1.0e-15
C_SN  SN  0  {C_SN_INTRINSIC}

* Line-to-line coupling (small; included for completeness)
C_WWL_WWL  WWL  0  {C_WWL_WWL + C_WWL_GND}
C_RWL_RWL  RWL  0  {C_RWL_RWL + C_RWL_GND}
C_WBL_WBL  WBL  0  {C_WBL_WBL + C_WBL_GND}
C_RBL_RBL  RBL  0  {C_RBL_RBL + C_RBL_GND}

.ENDS X2T0C
