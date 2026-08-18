# UNRESOLVED — v0 2T0C SPICE sandbox

Items that the v0 sandbox could NOT resolve, or that I had to
paper over with a MODELING_CHOICE.  They are listed so that the
next iteration knows exactly where the v0 leaves off.

## Hard UNRESOLVED (paper does not publish, no sensible surrogate)

1. **CSA Si-MOS transistor sizes / W/L / bias currents.**
   Zhu only publishes the 100 nA CSA current limit (from Fig 14
   caption) and shows a current-mode SA with IREF in Fig 7(b).  No
   transistor parameters.  v0 uses a behavioral current comparator
   stub; reading "1" is decided by RBL dropping below a fixed
   threshold.

2. **2T0C intrinsic storage-node capacitance C_SN.**
   Fig 4(b) reports the *coupling* caps (C_WWL_SN, C_RWL_SN, ...,
   ~25 aF each), but the intrinsic SN cap is not published.  v0
   picks C_SN = 1 fF (same order of magnitude as the 1T1C C_s = 3 fF).

3. **Distributed RC network along WWL/WBL/RWL/RBL for 512x512.**
   v0 only models a single cell + lumped unit-cell R and C.  The
   512x512 distributed pi-network is OUT OF SCOPE.

4. **Sub-threshold slope, DIBL, mobility degradation, gate leakage.**
   The surrogate uses a single (K, Vth, a, alpha, k, n) tuple.  No
   DIBL term.  No gate leakage.  No SS.

5. **Zhu's full compact model equations (Fig 5 surface-potential model).**
   I extracted only the qualitative form (Ids = f(Vgs, Vds, Vth,
   Vov, Vdsat)) and built a single behavioral surrogate.  The
   surface-potential / DIBL / NBTI sub-circuits are NOT reproduced.

6. **WBL swing for 2T0C write.**  Fig 7(b) only labels WBL as a
   write bit line; the paper's text states 0/1.2 V for the 1T1C but
   not explicitly for the 2T0C.  v0 uses 0/1.2 V (MODELING_CHOICE).

7. **Pre-charge RBL voltage for 2T0C read.**  Paper shows a CSA
   with IREF.  v0 sets RBL = V_DD = 1.2 V before the read.

8. **Read-window timing / sense-amp decision time.**
   Paper Fig 7(b) shows ~5 ns read windows; v0 uses 5 ns.  Exact
   numbers not specified in text.

## Soft UNRESOLVED (paper does not constrain, v0 makes an explicit choice)

9. **Operation window bounds (T_WRITE_START, T_WRITE_END, T_READ_START,
   T_READ_END).**  v0 picks WWL pulse 1-11 ns, RWL pulse 15-20 ns.

10. **Sense comparator threshold.**  v0 uses V(RBL) < 1.15 V
    -> SA = LOW.  The actual paper CSA has 100 nA current-limit
    threshold, but mapping that to a single-cell voltage threshold
    requires choosing an R_SENSE.

11. **V_RBL,RD bias (read bit-line bias during read).**
    Paper says "active-high RWL" but does not publish V_RBL during
    read.  v0 keeps RBL = V_DD throughout.

12. **Surrogate "Vds_eff" smoothing parameter k_smooth.**
    v0 picks k_smooth = 1.1 from the optimizer, but the
    paper does not publish a smoothing factor.

13. **Surrogate "Vdsat_scale" alpha_vdsat.**
    v0 picks alpha_vdsat = 0.6 (Vdsat ~ 60% of Vov).  Paper does
    not publish a Vdsat factor directly.

14. **Surrogate exponent a_exp on Vov.**
    v0 picks a_exp = 3.05 (closer to cubic than to classic square-law)
    because that gave the best fit to the digitized Fig 5(d,e) data.
    Real IGZO TFTs usually follow ~2; the difference is the
    surrogate's compensation for un-modelled bulk conduction.

15. **Write0/Write1 specific energy in fJ/bit.**
    v0 surrogate gives ~144 fJ per write, vs paper 0.24-0.58 fJ/bit.
    The difference is because v0 includes the read transistor's
    always-on current (Tr is in depletion mode, Vth < 0) which the
    paper's full-row simulation apparently does NOT count
    (presumably because the read BL is floated during write, so Tr
    is gated off).  v0 does not model the array-level RBL float.

## Numerical / simulator issues that consumed iteration time

16. **B-source expression evaluator: small Vds at large Vov was
    producing huge currents.**  Root cause: the original
    `Vds_eff = Vds * Vdsat / (Vdsat^k + |Vds|^k + eps)^(1/k)`
    formula is NOT smooth at the Vds -> 0 limit (the denominator
    has a 0/0 structure at Vdsat^k + 1e-30).  Fix: replace with
    `Vds_eff = sign(Vds) * 0.5 * (|Vds| + Vdsat - sqrt((|Vds|-Vdsat)^2 + eps^2))`,
    a soft clipped MIN with sign.  This is the v0 Vds_eff.

17. **R_RBL = 2 ohm (per Fig 4(b)) with V_RBL_drv = 0 V (write case)
    or = V_DD (read case) holds RBL pinned and masks the read
    signal.**  v0 read netlist replaces R_RBL with 1 GOhm so the
    cell's read current can actually discharge RBL.  This is
    documented in netlists/read0.sp and read1.sp as a v0
    simplification.

18. **B-source sub-threshold exponent without MIN clamping caused
    a 12 A current at Vov > 0.**  Fix: use MIN(Vov, 0) in the
    exponent argument.

19. **PowerShell I/O pipe into ngspice hangs the .exe.**  Fix: use
    `cmd /c ngspice_con -b -o log cir` (or a .bat wrapper) to run
    ngspice from Python.

20. **ngspice (non-console) GUI version raises a "Fatal error in
    SPICE" popup on transient errors.**  Fix: use ngspice_con
    (D:\Spice64\bin\ngspice_con.exe) which is console-only.

## Things that are NOT UNRESOLVED but worth knowing

* The v0 model is **NOT** the Zhu surface-potential compact model.
  It is a behavioral B-source surrogate.  The library file
  `models/igzo_2t0c_v0.lib` is clearly labeled.
* The v0 cell uses **lumped** parasitics, not distributed.
* The v0 sense stub is **functional**, not a calibrated FEOL SA.
* The v0 energies will be **orders of magnitude off** from
  Zhu Table I.  This is expected and called out in the report.
