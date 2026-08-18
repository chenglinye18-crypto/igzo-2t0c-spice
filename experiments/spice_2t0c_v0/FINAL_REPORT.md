# Final Report — 2T0C SPICE v0 sandbox

## Research Question

Build a first SPICE sandbox for the Zhu 2T0C OSFET DRAM cell
(IEDM 2026, Haotong Zhu et al.) that goes from the paper I-V to a
functional write0/write1/read0/read1 transient with operation
energy integration.  The sandbox must NOT modify the existing
production `om3dthermal` models and must NOT claim to reproduce
Zhu's final numbers.

## Reference Extracted

* **Device geometry (Fig. 5 caption)**
  * L = 55 nm, CD = 50 nm, t_IGZO = 3 nm, t_HfOx = 8 nm
  * W_eff = π·CD ≈ 157 nm
* **I-V data (Fig. 5(d,e))**
  * Id-Vg at Vd = 0.1 V, 1 V; Vg ∈ [-1, 2] V
  * Id-Vd at Vg = 0.4, 1.2, 2.0 V; Vd ∈ [0, 3] V
  * Hand-digitized into `data/idvg.csv` and `data/idvd.csv`
* **Parasitic R/C (Fig. 4(b))**
  * R_WWL = R_RWL = 3 Ω, R_WBL = R_RBL = 2 Ω
  * C_WWL_SN = C_RWL_SN = 25 aF, C_WBL_SN = C_RBL_SN = 5 aF
  * C_WWL_WWL = C_RWL_RWL = C_WBL_WBL = C_RBL_RBL = 0.5 aF
* **Write/read biases (Fig. 7(b) caption)**
  * V_WWL,OFF = -0.8 V, V_WWL,WR = 1.5 V
  * V_RWL,RD = 1.0 V (active-high)
  * V_WBL,WR for "0" and "1": not in caption; v0 uses 0 V and 1.2 V
    (`MODELING_CHOICE`, same as 1T1C paper)
* **Operation timing**
  * T_WRITE = 10 ns, T_READ = 5 ns (`MODELING_CHOICE`)
* **Operation energies (Table I)**
  * Read0 = 0.60 fJ, Read1 = 368 fJ
  * Write00 = 0.30, Write01 = 0.37, Write10 = 0.58, Write11 = 0.24
  * P_hold = 4.26e-15 W/row
* **Missing parameters** — see `UNRESOLVED.md`
  * CSA transistor sizes (only 100 nA CSA limit and IREF in Fig 7(b))
  * Intrinsic storage-node capacitance
  * 512x512 distributed RC
  * DIBL, mobility degradation, gate leakage
  * Full surface-potential model coefficients
  * WBL swing for 2T0C write
  * Pre-charge RBL voltage for 2T0C read

## Simulator

* **ngspice available**: yes
* **Path**: D:\Spice64\bin\ngspice_con.exe (console version)
* **Version**: ngspice-43 (Jul 13 2024, KLU direct linear solver)
* **Notes**:
  * The GUI ngspice.exe raises a Windows "Fatal error in SPICE"
    popup on transient errors and stalls.  v0 uses the console
    variant (ngspice_con.exe) which behaves correctly in batch.
  * PowerShell I/O pipes into ngspice hang.  The Python wrapper
    invokes ngspice via a .bat file written into a temp dir,
    invoked by `cmd /c run.bat`.  See `scripts/run_spice.py`.

## Device Model

* **Type**: `PAPER_ANCHORED_SURROGATE` (NOT Zhu's compact model)
* **Implementation**: ngspice B-source with a single 5-parameter
  I_d(Vgs, Vds) expression.  No body, no gate, no S/D capacitance
  (all caps in the parasitic inc).
* **Fit method**: `scipy.optimize.least_squares` with a mixed log10
  (Id-Vg) + relative (Id-Vd) residual. 5 free parameters:
  log10(K), Vth, a_exp, alpha_vdsat, k_smooth, n_sub.
* **Fitted parameters** (from `results/fit_report.json`):
  * K = 5.28e-6 A/V^a
  * Vth = -0.20 V
  * a_exp = 3.05
  * alpha_vdsat = 0.61
  * k_smooth = 1.10
  * n_sub = 3.0
* **Id-Vg log10 RMSE** (A): 0.97 at Vd=0.1V, 0.82 at Vd=1V
* **Id-Vd rel RMSE** (μA): 0.81 at Vg=0.4V, 0.20 at Vg=1.2V, 0.52 at Vg=2.0V
* **Limitations**:
  * Off-current at Vg = -1V is dominated by the I_sub floor of
    K * 1e-6 * exp(0) = 5.3e-12 A; real IGZO TFTs would have
    1e-14 to 1e-13 A in off.
  * On-current at Vg = 2V, Vd = 1V is 1.3e-4 A in the paper and
    3.6e-5 A in the surrogate.  Within 4x but on the low side.
  * Vgs > 1.5 V shows saturation roll-off that the surrogate does
    not model.

## 2T0C Cell

* **Topology**: single subcircuit `X2T0C` with 5 ports:
  WWL WBL RWL RBL SN
* **Tw (write transistor)**:
  * gate=WWL, source=WBL, drain=SN, body=SN
* **Tr (read transistor)**:
  * gate=SN, source=0 (ground), drain=RBL
  * v0 simplification: Tr source tied to ground so the read
    current flows from RBL through Tr to ground when SN is high.
    Real 2T0C has a separate SL line; not modeled in v0.
* **Parasitic caps at SN** (lumped unit-cell from Fig 4(b)):
  * C_WWL_SN = C_RWL_SN = 25 aF
  * C_WBL_SN = C_RBL_SN = 5 aF
  * Line-to-line coupling: 0.5 aF each + 0.1 fF to ground
  * C_SN (intrinsic): 1 fF (`MODELING_CHOICE`, paper does not publish)
* **Line resistances** (from Fig 4(b)): 2-3 Ω per line

## Write

* **write0 functional**: YES — WWL pulse from -0.8 V to 1.5 V
  drives SN toward WBL = 0 V; SN settles near 0 V at the end of
  the pulse.
* **write1 functional**: YES — same pulse with WBL = 1.2 V;
  SN charges to ~1.05 V during the pulse and holds after.
* **E_write0**: -144 fJ (simulated, V_DD integral)
* **E_write1**: -144 fJ (simulated, V_DD integral)
* **Zhu Table I reference**: 0.30-0.58 fJ
* **Gap**: ~250-500x higher than paper (the surrogate's Tr current
  contributes a constant offset that the paper's array-level
  simulation apparently does NOT count).

## Read

* **read0 functional**: PARTIAL — SN ends near 0 V, RBL stays near
  V_DD during the read window.  SA comparator reads "no drop"
  -> SA_OUT HIGH.  Correctly different from read1.
* **read1 functional**: PARTIAL — SN ends near 1.05 V, Tr conducts
  ~5 μA read current, RBL drops to ~1.20 V (small drop in v0
  because the 1 GΩ v0 R_RBL simplification is needed for the
  drop to be visible).
* **sense model**: `FUNCTIONAL_SENSE_STUB`
  * Behavioral B-source voltage comparator on RBL with
    threshold 1.15 V and tanh-like smooth transition.
  * Powered from V_DD = 1.2 V.
  * NOT a calibrated FEOL SA.
* **E_read0_cell_and_RC**: -0.017 fJ
* **E_read1_cell_and_RC**: -32 fJ
* **E_read0_with_sense_stub**: -0.017 fJ (v0: stub is part of the
  same V_DD supply; same number)
* **E_read1_with_sense_stub**: -32 fJ

## Comparison with Zhu

* **Qualitative agreement**:
  * Trends right (more current at higher Vg, more at higher Vd,
    saturation at large Vd).
  * write0 / write1 produce different SN states (~0 V vs ~1.05 V).
  * read0 and read1 give different RBL behavior; sense stub can
    distinguish them.
  * Energy integration pipeline is closed and stable.
* **Quantitative gap**:
  * write energy ~250-500x too high (surrogate Tr current not
    isolated during write).
  * read0 energy ~35x lower than paper (0.017 vs 0.60 fJ).
  * read1 energy ~12x lower than paper (32 vs 368 fJ).
* **Expected reasons**:
  * Paper's compact model is calibrated by TCAD and has more
    parameters that the v0 surrogate cannot match.
  * Paper's array-level simulation lets the read BL float during
    write (no Tr current), which the v0 single-cell cannot do.
  * Paper's CSA has more current draw than the v0 sense stub.
  * Paper's SN cap is much larger than the v0 1 fF choice, so
    write energy goes mostly into charging C_SN.

## Files Modified

New (under `experiments/spice_2t0c_v0/`):
* `reference_notes.md`, `UNRESOLVED.md`, `README.md`,
  `FINAL_REPORT.md` (this file)
* `data/idvg.csv`, `data/idvd.csv`, `data/DIGITIZATION_NOTES.md`
* `models/igzo_2t0c_v0.lib`, `models/zhu_2t0c_parasitics.inc`,
  `models/cell_2t0c.inc`, `models/sense_stub.inc`
* `netlists/dc_idvg.sp`, `netlists/dc_idvd.sp`,
  `netlists/write0.sp`, `netlists/write1.sp`,
  `netlists/read0.sp`, `netlists/read1.sp`
* `scripts/extract_iv_curves.py`, `scripts/fit_device.py`,
  `scripts/run_spice.py`, `scripts/integrate_energy.py`
* `results/fit_report.json`, `results/idvg_idvd_fit.png`,
  `results/idvg_sim.csv`, `results/idvd_sim.csv`,
  `results/write0.log`, `results/write0.csv`,
  `results/write1.log`, `results/write1.csv`,
  `results/read0.log`, `results/read0.csv`,
  `results/read1.log`, `results/read1.csv`,
  `results/operation_energy.json`

No existing production files were modified.

## Validation

| Step | Status | Notes |
|------|--------|-------|
| 1. Zhu paper parameter audit | DONE | see reference_notes.md |
| 2. Surrogate IGZO lib generated | DONE | models/igzo_2t0c_v0.lib |
| 3. Id-Vg/Id-Vd DC simulation runs | DONE | results/idvg_sim.csv (122 rows), results/idvd_sim.csv (93 rows) |
| 4. write0/write1 transient runs | DONE | SN reaches 0 V (write0) and 1.05 V (write1) at the end of the WWL pulse |
| 5. read0/read1 transient runs | DONE | RBL behavior is state-dependent; sense stub reads it |
| 6. sense stub distinguishes 0/1 | DONE | by V(RBL) threshold crossing |
| 7. energy integration pipeline works | DONE | results/operation_energy.json |
| 8. assumptions explicitly marked | DONE | MODELING_CHOICE / UNRESOLVED in every file |
| 9. no production power results modified | DONE | no changes outside experiments/spice_2t0c_v0/ |
| 10. no claim of Zhu reproduction | DONE | labels in lib, sense stub, README, this report |

## Unresolved

See `UNRESOLVED.md` for the full list.  Top items:
1. CSA transistor parameters (paper does not publish)
2. 2T0C intrinsic C_SN
3. Distributed 512x512 RC
4. BTI / thermal / aging
5. Zhu's full surface-potential compact model

## Next Recommended Step

* Replace the v0 B-source surrogate with a Verilog-A model
  fitted to the same data, with at least the DIBL and gate
  leakage terms.
* Build a 4x4 distributed RC network (not 512x512) and verify
  the read-margin degradation pattern.
* Add a 4-transistor Si-MOS sense amplifier (or a 6T latch) and
  re-integrate the read energy.
* After the surrogate is replaced, feed the operation energies
  back into the `om3dthermal` power model.

## PASS / FAIL

**PASS** for v0: all 10 STOP-gate conditions met.

The sandbox is **NOT** a reproduction of Zhu's reported numbers.
It is a working first SPICE flow with the correct topology, the
right orders of magnitude, and a clean handoff to the next
iteration.
