# Reference Notes — Zhu 2T0C (IEDM 2026, V5)

> Source: `ref/IEDM2026_HaotongZhu_V5.pdf` (Haotong Zhu et al., Peking University, IEDM 2026).
>
> "From Cell Metrics to Memory-Array-Tile Operability: DTCO of OSFET-Based 3D DRAM"
>
> Scope: This file captures **only the parameters needed for the v0 SPICE sandbox**.
> Anything not stated in the paper is flagged `UNRESOLVED` or `MODELING_CHOICE`.

---

## 1. Device / Cell Geometry (2T0C, Fig. 3(b) + Fig. 5 caption)

The 2T0C evaluated in Zhu is a **vertically stacked CAA-CAA** OSFET structure
(reference [5], K. Huang et al., VLSI 2022):

| Parameter         | Value           | Source                |
|-------------------|-----------------|-----------------------|
| Gate length `L`   | 55 nm           | Fig. 5 caption        |
| Channel diameter `CD` | 50 nm       | Fig. 5 caption        |
| IGZO thickness `t_IGZO` | 3 nm    | Fig. 5 caption        |
| Gate-oxide thickness `t_HfOx` | 8 nm | Fig. 5 caption        |
| Effective width `W_eff` | `π·CD` ≈ 157 nm | Fig. 5 caption    |

Two stacked n-type OSFETs (write transistor `Tw` and read transistor `Tr`),
sharing the storage node `SN` as a common internal electrode. The 2T0C has
**no explicit capacitor** — the SN capacitance is provided by the gate oxide,
source/drain junctions, and the metal stack of the two transistors.

Per Fig. 7(b) the 2T0C cell has 5 electrical ports:

* `WWL` — write word line
* `WBL` — write bit line
* `RWL` — read word line
* `RBL` — read bit line
* `SN`  — storage node (also accessible to the cell)

(For the full cell the source of `Tw` is `WBL` and the source of `Tr` is `RBL`;
`Tw` drain and `Tr` drain are tied to `SN`.)

---

## 2. Bias Conditions (Fig. 7(b) caption)

| Bias                    | Value          | Notes                                     |
|-------------------------|----------------|-------------------------------------------|
| `V_WWL,OFF`             | **−0.8 V**     | WWL off voltage                           |
| `V_WWL,WR`              | **1.5 V**      | WWL write-selection voltage               |
| `V_RWL,RD`              | **1.0 V**      | RWL read-selection voltage (active-high)  |
| `V_RBL,RD`              | `UNRESOLVED`   | not in caption; we will use a pre-charge / read-bias assumption |
| `V_WBL,WR` (data 0)     | `UNRESOLVED`   | Zhu writes 2T0C with WBL = 0 V or 1.2 V is *not* stated for 2T0C. For 1T1C the paper uses 0/1.2 V; for 2T0C we **assume** the same WBL swing of 0–1.2 V. `MODELING_CHOICE` |
| `V_WBL,WR` (data 1)     | 1.2 V (assumed) | `MODELING_CHOICE`                       |
| `V_RBL,RD` (pre-charge) | `UNRESOLVED`   | The CSA topology has an `IREF` reference, so the RBL is biased against `IREF`; for v0 we use a simple pulled-up RBL. `MODELING_CHOICE` |

Operation timing: Zhu Fig. 7(b) shows write/read windows on the order of
**5–25 ns**. We choose `T_WRITE = 10 ns` and `T_READ = 5 ns` for v0
(`MODELING_CHOICE`, consistent with the figure but not numerically exact).

---

## 3. I–V Data Available (Fig. 5(d,e))

The 2T0C subplot in Fig. 5(d) shows `Id` (A) vs `Vg` (V) at:

* `Vd = 0.1 V` (linear) and `Vd = 1 V` (near-saturation)
* `Vg` sweep ≈ −1 V → 2 V
* `Id` range ≈ `1e-14` → `1e-4` A (10 decades)

Fig. 5(e) shows `Id` (μA) vs `Vd` (V) at:

* `Vg = 0.4 V, 1.2 V, 2.0 V` (Vstep = 0.8 V, three curves)
* `Vd` sweep 0 → 3 V
* `Id` range 0 → 60 μA

**Digitization approach:** since the PDF is text-extractable but the figures
are images, we use representative data points anchored on the figure
axis-tick values (subplot captions in the paper) and the on/off extremes. Each
point is **manually placed** at the visible curve. See `data/idvg.csv` and
`data/idvd.csv`.

> Paper explicitly says: "the reported I–V data do not uniquely constrain
> all compact-model parameters" → the v0 surrogate is **anchored**, not a
> re-extraction of the paper's compact model.

---

## 4. Unit-Cell Parasitic R/C (Fig. 4(b))

Zhu's Fig. 4(b) reports the following 2T0C unit-cell parasitic values.
**Numbers below are read off the axis ticks of Fig. 4(b) and are
approximate (±20 %). They are not numerically tabulated in the paper text.**

Line resistances (x-axis 0–5 Ω, four bars):

| Element        | Approx. value | Notes                              |
|----------------|---------------|------------------------------------|
| `R_WWL`        | ~3 Ω          | read off bar height                |
| `R_RWL`        | ~3 Ω          | read off bar height                |
| `R_WBL`        | ~2 Ω          |                                    |
| `R_RBL`        | ~2 Ω          |                                    |

All line-to-line coupling caps (Fig. 4(b), one bar group, aF, axis 0–5 aF):

| Element           | Approx. value |
|-------------------|---------------|
| `C_WWL_WWL`       | ~0.5 aF       |
| `C_RWL_RWL`       | ~0.5 aF       |
| `C_WBL_WBL`       | ~0.5 aF       |
| `C_RBL_RBL`       | ~0.5 aF       |

Node coupling caps (Fig. 4(b), aF, axis 0–35 aF):

| Element        | Approx. value | Notes                          |
|----------------|---------------|--------------------------------|
| `C_WWL_SN`     | ~25 aF        | dominates; reasonable for CAA gate overlap |
| `C_RWL_SN`     | ~25 aF        | same                           |
| `C_WBL_SN`     | ~5 aF         | parasitic overlap              |
| `C_RBL_SN`     | ~5 aF         |                                |

These are written into `models/zhu_2t0c_parasitics.inc`. v0 uses **unit-cell
lumped** values for a single 2T0C; the 512×512 distributed network is out of
scope (see Section 12 of the task spec).

---

## 5. Sense Amplifier (Fig. 7(b))

Zhu uses a **current sense amplifier (CSA)** with `IREF` reference
(`FUNCTIONAL_SENSE_STUB`, not a calibrated FEOL SA). The paper does not give
transistor sizes / currents.

> From the paper text and Fig. 7(b):
> * 2T0C uses CSA + active-high RWL read selection
> * CSA limit: **100 nA** (from Fig. 14 caption)
> * The 2T0C baseline read margin after 10 s hold is `0.23 μA` (from Fig. 14(b)
>   text — "increases from 0.2351 μA")

v0 stub: a simple current comparator surrogate. The RBL is held by a small
pull-up; the read current discharges it; a Schmitt-trigger inverter compares
against a fixed threshold current `IREF`. We do **not** fabricate transistor
sizes; we instead use a behavioral current-to-voltage conversion with the
known CSA limit of 100 nA and the paper read margin (0.23 μA) as a **target
read-current scale**, not a calibration target. See `models/igzo_2t0c_v0.lib`
section `X_SENSE_STUB`.

---

## 6. Operation Energies (Zhu Table I)

Reported 2T0C operation energies per bit (sanity reference only):

| Operation         | Energy (fJ/bit) |
|-------------------|-----------------|
| Read "0"          | 0.60            |
| Read "1"          | 368             |
| Write 00          | 0.30            |
| Write 01          | 0.37            |
| Write 10          | 0.58            |
| Write 11          | 0.24            |
| Refresh "0"       | 0.90            |
| Refresh "1"       | 370             |
| `P_hold` (per row)| `4.26e-15 W/row`|

**These are sanity reference only.** v0 will not match them (single cell +
lumped parasitics + surrogate device + sense stub).

---

## 7. What the Paper Does NOT Publish (`UNRESOLVED`)

The following are **not stated** in Zhu V5 and are marked `UNRESOLVED` or
`MODELING_CHOICE` everywhere they appear:

* Exact Vth of Tw and Tr (only the calibrated TCAD model in the paper has it;
  the I-V is the public anchor).
* Exact mobility μ_eff of the calibrated 2T0C (depends on the surface-potential
  compact model; not a single number).
* Exact WBL swing and RBL pre-charge voltage for the 2T0C (the paper only
  states 1T1C values).
* CSA transistor sizes / device parameters. Only the CSA current limit
  (100 nA) and a representative `IREF` are inferable from Fig. 7(b) / Fig. 14.
* Sub-threshold slope, DIBL, gate leakage, contact resistance.
* BTI model parameters (out of v0 scope).
* Interconnect resistance per unit length / distributed R() / C() values
  (only the unit-cell lumped values are shown).
* Thermal / BTI effects (out of v0 scope; this sandbox is purely electrical).

For each `UNRESOLVED` we use a `MODELING_CHOICE` annotated in the corresponding
file. **No silent padding of values.**

---

## 8. Reference for v0

* v0 surrogate is a **paper-anchored behavioral model** of the 2T0C device,
  fitted to a hand-digitized subset of Fig. 5(d,e).
* v0 cell is **a single 2T0C**, not a 512×512 row.
* v0 sense is a **functional current-sense stub**, not a calibrated FEOL SA.
* v0 energies will likely be **orders of magnitude off** Zhu Table I.
  This is expected and called out in the final report.
