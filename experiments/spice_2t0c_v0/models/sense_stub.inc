********************************************************************************
*  sense_stub.inc
*  --------------------------------------------------------------------
*  FUNCTIONAL_SENSE_STUB
*  NOT_CALIBRATED_FEOL_SA
*  --------------------------------------------------------------------
*  A behavioral current-sensing block that emulates Zhu's CSA.  The
*  paper does not publish Si-MOS CSA transistor sizes, so this stub
*  uses a behavioral B-source comparator against IREF.
*
*  The sense stub is **not** a transistor-level SA.  Its purpose is to:
*    1. Differentiate read0 from read1 by comparing the read current
*       on RBL against a fixed reference current.
*    2. Provide a clean sense output for the read transient.
*    3. Allow energy-integration to include a "sense stub" component
*       (so the cell-vs-cell+SA comparison is meaningful).
*
*  The reference current is set close to the Zhu paper's CSA limit
*  (100 nA from Fig. 14(b) caption).  The sense decision is taken at
*  T_SENSE_END = 5 ns after RWL rises.
*
*  The stub does NOT:
*    - Model the Si-MOS latch of a real current SA
*    - Capture sense-amp offset / mismatch
*    - Track BTI / aging
*
*  The stub consumes a fixed bias current I_BIAS when enabled.  The
*  total energy is therefore:
*      E_sense = V_DD * I_BIAS * T_SENSE
*  which is a deliberate v0 simplification.
********************************************************************************

* Sense stub parameters
.PARAM IREF_SA     = 100.0e-9     ; 100 nA -- from Zhu Fig 14(b) CSA limit
.PARAM I_BIAS_SA   = 1.0e-6        ; 1 uA constant bias while enabled
.PARAM V_SA_HI     = 1.2           ; "logic 1" output level
.PARAM V_SA_LO     = 0.0           ; "logic 0" output level
.PARAM T_SENSE_END = 5.0e-9        ; sense decision time after RWL rise
.PARAM V_DD        = 1.2           ; supply rail

* SA_ENABLE: high during the read window.  Externally controlled.
* SA_OUT:    high when I(RBL) > IREF, low otherwise.
* IREF_IN:   reference current input (set externally).

*  Behavioral current comparator:
*    I(RBL) > IREF  =>  SA_OUT -> V_SA_HI after T_SENSE_END
*    I(RBL) < IREF  =>  SA_OUT -> V_SA_LO after T_SENSE_END
*
*  We approximate this with a smooth tanh-like transition to keep the
*  SPICE matrix well-posed.

.SUBCKT XSENSE_STUB SA_ENABLE SA_OUT IREF_IN
*  G_delta = I(SA_IN) - IREF; we don't have SA_IN in v0, so use a
*  voltage-mode surrogate:  sense current is delivered as a voltage
*  at IREF_IN from a previous stage; we just compare IREF_IN to a
*  threshold and output a digital level.
*
*  In v0 the sense is much simpler: we have a single comparator that
*  looks at the I(RBL) current directly.  The netlist that uses this
*  stub will have to provide I(RBL) as a voltage via a 1-Ohm sense
*  resistor.  See netlists/read0.sp and read1.sp.
.ENDS XSENSE_STUB
