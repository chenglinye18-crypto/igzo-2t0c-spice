# Model Equations Audit — Zhu 2T0C IEDM 2026 + SCE EDTM 2026

This file is the **paper-physics reference** for the v1 compact model.
Every equation, parameter, and geometry is annotated with one of:

* `PAPER_REPORTED`       — directly stated in either paper.
* `DERIVED_FROM_PAPER`   — derived from paper equations but not literally quoted.
* `CALIBRATION_PARAMETER` — required by the model equations, but not published;
                            fitted to the Zhu I-V data in §3.
* `CALIBRATION_EXTENSION` — NOT in either paper; added because the I-V requires it.
* `UNRESOLVED`           — paper does not give enough information to fix.

The v1 model is **PAPER-ANCHORED, PHYSICS-BASED, CAA-ADAPTED**, not
the original Zhu surface-potential compact model. See §2.5 for the
specific things we had to adapt for the CAA geometry.

---

## 1. Zhu 2T0C paper (IEDM 2026, V5)

### 1.1 Geometry and structure (Fig. 5 caption) — `PAPER_REPORTED`

| Parameter        | Value           | Use in v1 model                |
|------------------|-----------------|--------------------------------|
| Gate length `L`  | 55 nm           | fixed, geometric               |
| Channel diameter `CD` | 50 nm      | fixed, geometric               |
| IGZO thickness `t_IGZO = t_ch` | 3 nm | fixed, geometric           |
| Gate-oxide thickness `t_HfOx = t_ox` | 8 nm | fixed, geometric      |
| Effective width `W_eff` | `π·CD` ≈ 157 nm | fixed, geometric         |
| Cell layout      | vertically stacked CAA-CAA | see §2.5 for geometry adaptation |

These are the **calibrated geometries** the paper uses for the
2T0C compact model. They are NOT to be re-tuned for I-V fit.

### 1.2 I-V axis convention (Fig. 5(d,e) labels)

* **1T1C**: `I_d (A/μm)` — normalized per unit width.
* **2T0C**: `I_d (A)` — **total device current** (not per μm).
  The 2T0C axis is 10× higher because the absolute device size is
  smaller; the comparison between 1T1C and 2T0C requires multiplying
  the 1T1C value by `W_1T1C = 500 nm` and the 2T0C value stays as-is.

`PAPER_REPORTED`. `DERIVED_FROM_PAPER`: the absolute-A convention
means the v1 model should output total current, not per-μm.

### 1.3 Fig. 5(d) — 2T0C Id-Vg data — `PAPER_REPORTED`

* x-axis: `V_g` ∈ [-1, 2] V
* y-axis: `I_d` ∈ [10⁻¹⁴, 10⁻⁴] A (10 decades, log scale)
* Two curves: `V_d = 0.1 V` (linear) and `V_d = 1 V` (near saturation)

### 1.4 Fig. 5(e) — 2T0C Id-Vd data — `PAPER_REPORTED`

* x-axis: `V_d` ∈ [0, 3] V
* y-axis: `I_d` ∈ [0, 60] μA
* Three curves: `V_g = 0.4 V`, `V_g = 1.2 V`, `V_g = 2.0 V` (Vstep = 0.8 V)

### 1.5 Surface potential model (Fig. 5 caption, top equation) — `PAPER_REPORTED`

The Zhu surface potential equation, transcribed:

```
C_ox / ε_ox · (V_ov_ox − ψ_s)
  = (2 q / ε_s) · Σ_j N_{V,j} · ( exp(V_ψ,j − V_ψ,s) − exp(−V_ψ,j) )
  − N_D · (1 − κ · ψ_s)
```

with auxiliary definitions:

```
V_ov_ox = V_g − V_fb          (effective gate overdrive referenced to flat-band)
V_ψ,j  = q · N_{V,j} · t_ch / (C_ox · ε_ox) − κ_j · ψ_s
κ      = exp(−t_ch / ε_ox) · 2 ε_s / L_D
L_D    = sqrt(ε_s · V_T / (q · N_D))
```

Notation:
* `C_ox = ε_ox / t_ox` — gate oxide capacitance per unit area.
* `V_T = k_B T / q` — thermal voltage (~0.02585 V at 300 K).
* `ψ_s` — surface potential at the gate-oxide / IGZO interface
  (implicit unknown; this equation defines it).

`DERIVED_FROM_PAPER`: the j-sum Σ over sub-bands is the paper's full
form. For v1 we **simplify to a single term** (j=1, single N_V) and
explicitly note the simplification. See §2.5.

### 1.6 Drain current model (Fig. 5 caption, middle equation) — `PAPER_REPORTED`

The Zhu drain current equation, transcribed:

```
              W_eff             q N_D t_ch,eff                2 k_B T
I_d  =  ────────── · μ_eff · C_ox · (V_g − V_th) · ──────────── + ────────── · (V_ov_ox − V_fb)
                L                   C_ox                       q
                                                          · ln( exp((V_ov_ox − V_fb) / V_T) − 1 )
                                                                              [percolation correction term]
```

In the original paper the term is more complex; for the v1 we use:

```
I_d = (W_eff / L) · μ_eff · C_ox ·
      [ (V_g − V_th) · (q N_D t_ch,eff / C_ox)
        + (k_B T / q) · ln( exp((V_g − V_fb) / V_T) − 1 )
      ]                                                       — drift + diffusion
   − (percolation term)                                       — `DERIVED_FROM_PAPER`
```

`DERIVED_FROM_PAPER`: the percolation term is small at the bias
points we fit, so v1 omits it. See §2.5.

### 1.7 Mobility model (Fig. 5 caption, bottom equation) — `PAPER_REPORTED`

```
μ_eff = μ_0 / ( 1 + (USR · E_⊥)^E_USC ) · ( M_TLC + M_USC · [percolation] )
```

v1 simplification: ignore the percolation term, use

```
μ_eff = μ_0 / ( 1 + (USR · E_⊥)^E_USC )                      — `DERIVED_FROM_PAPER`
```

with the percolation correction `< 1` lumped into `μ_0`.

`E_⊥` — perpendicular (vertical) field at the IGZO / gate-oxide
interface. For a 2T0C CAA structure, this is `E_⊥ = C_ox · (V_g − V_fb − ψ_s) / ε_s`
`DERIVED_FROM_PAPER`.

### 1.8 BTI model — out of v1 scope

The Zhu paper includes a state-based BTI compact model (PBTI/NBTI,
relaxation, stress-history dependence). v1 is a DC I-V model only.
`UNRESOLVED` for v1.

### 1.9 Parameter deck — `UNRESOLVED`

The Zhu paper does NOT publish the calibrated parameter values
(N_D, N_{V,j}, μ_0, USR, E_USC, V_fb, ...). They are obtained by
calibrating the compact model to the I-V data, with TCAD as an
intermediate constraint. v1 calibrates the free parameters to the
Id-Vg / Id-Vd data in §3.

---

## 2. SCE paper (EDTM 2026) — Physical Model of Intrinsic SCE for OS-TFTs

### 2.1 Geometry of the SCE paper (Figs. 1(c), 5)

The SCE paper is calibrated and validated for:

* **Back-gate (BG) OS-TFT** — primary target.
* **Symmetric dual-gate (DG) OS-TFT** — extension in §III of the paper.
* The planar BG channel: rectangle of length L and channel thickness t_ch.

**It is NOT calibrated for the vertically stacked CAA structure that
Zhu uses for 2T0C.** See §2.5 for the explicit non-migration.

### 2.2 TCAD parameters (Table I) — `PAPER_REPORTED`

These are the OS-TFT physical parameters the SCE paper uses (and
validates with TCAD). They are the **same material system as Zhu's
2T0C** (IGZO, same group, same authors), so we use them as the
initial guess for v1 Zhu 2T0C parameters with the explicit caveat
that they are NOT paper-reported FOR the 2T0C device — they are
initial guesses from a related SCE paper.

| Symbol  | Value           | Meaning                         | v1 use        |
|---------|-----------------|---------------------------------|---------------|
| N_d     | 1 × 10¹⁸ cm⁻³    | donor concentration             | `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| W_TA    | 0.043 eV        | tail-state characteristic energy| `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| g_TA    | 8.8 × 10¹⁹ cm⁻³ eV⁻¹ | tail-state density | `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| μ_b     | 15 cm² V⁻¹ s⁻¹  | band mobility (off-state)       | `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| Φ_s     | 4.26 eV         | channel work function           | `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| E_g     | 3.05 eV         | bandgap (not directly used in I-V at 300 K) | reference only |
| ε_s     | 10              | relative permittivity of channel | `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| ε_ox    | 22              | relative permittivity of gate oxide | `CALIBRATION_PARAMETER` (initial_guess_from_SCE_paper) |
| W       | 80 nm           | channel width in the SCE paper  | not applicable (geometry differs) |

These are not calibrated to Zhu's 2T0C; they are the published SCE
values. The v1 model **starts from these** and adjusts the ones that
are not well-constrained (N_D, μ, ...).

### 2.3 2D potential equation (Eq. 1) — `PAPER_REPORTED`

```
ε_ox · (dE(y)/dy) · (C_ox / ε_ox) · (V_g − V_fb − φ_s(y)) − q N_d · x = η · ²
```

In standard notation this is the 2D Poisson equation for a rectangular
Gaussian box at height `x` and lateral extent `Δy`. The first term
is the displacement field; the second is the depletion charge; the
right side is the "non-uniformity correction" with fitting parameter η.

`UNRESOLVED` for v1 Zhu 2T0C: this equation assumes a planar BG
geometry with x as the vertical coordinate. For CAA, the geometry
is **cylindrical** and the field is radial. We do NOT solve the 2D
Poisson equation directly for v1.

### 2.4 2D potential profile (Eq. 2) — `PAPER_REPORTED`

```
                              sinh(y / λ)                              sinh((L − y) / λ)
φ_s(x, y) = φ_long(x) + [φ_s(x, L) − φ_long(x)] · ─────────────── + [φ_s(x, 0) − φ_long(x)] · ───────────────
                              sinh(L / λ)                              sinh(L / λ)
```

with the natural length:

```
                ┌         ┐
       t_ch     │  C_s    │
λ  =  ───── · η │ ──────  │                (Eq. 5)
       ε_ox     │  C_ox   │
                └         ┘
```

`C_s` is the channel (semiconductor) capacitance per unit area,
`C_s = ε_s / t_ch` for a uniform slab.

`PAPER_REPORTED` for planar BG. **NOT directly applicable to CAA**;
see §2.5.

### 2.5 What can and cannot be migrated to Zhu 2T0C CAA

The SCE paper was developed and TCAD-validated on **planar BG
and symmetric DG** OS-TFTs. The Zhu 2T0C is a **vertically stacked
CAA-CAA** structure: the channel is a thin IGZO shell wrapped
around a vertical pillar (W_eff = πCD).

| SCE element             | Direct use in Zhu 2T0C CAA? | Action              |
|-------------------------|------------------------------|---------------------|
| Natural length λ (Eq. 5)| NO — planar formula, not cylindrical | `CALIBRATION_PARAMETER`; use as a structural inspiration, not a literal equation. |
| 2D Poisson (Eq. 1)      | NO — assumes rectangular box | `UNRESOLVED`; v1 uses Zhu's 1D vertical field equation instead. |
| 2D potential profile (Eq. 2) | NO — uses λ from above | `UNRESOLVED`; v1 uses Zhu's surface potential equation. |
| 1D long-channel φ (Eq. 4) | PARTIAL — the 1D limit is structurally the same | use as a sanity check on the Zhu equation in the long-channel limit. |
| Eq. 3 boundary conditions | PARTIAL — physically similar but planar | use only the **physical structure** (V_fb shift, charge sign), not the specific form. |
| Off-state current I_off (Eq. 9) | YES — physical structure is universal | use directly, calibrate `N_f` to Zhu I-V. |
| Q_f expression (Eq. 10) | YES | use directly. |
| V_th roll-off / DIBL (Eq. 11) | PARTIAL — form can be retained, λ must be calibrated as an effective parameter | use Eq. 11 as the **functional form** of ΔV_th, with `λ` as a calibration parameter. |
| μ_b (off-state mobility) | YES — material parameter | use directly from Table I as initial guess. |
| η (fitting)            | NO — physical meaning tied to planar BG | rename to `η_eff` and treat as `CALIBRATION_PARAMETER` for v1. |

The SCE paper provides **physical guidance** for the off-state and
DIBL sub-circuits of v1. The **explicit equations are reused only
for the off-state current, the Q_f expression, and the functional
form of V_th roll-off**. Everything else is implemented using the
Zhu equations from §1, with the **CAA geometry** folded into a small
number of effective calibration parameters (N_D, N_V, V_fb, η_eff).

### 2.6 Off-state current (Eq. 9) — `PAPER_REPORTED` (universal form)

```
                              [ exp(−(V_g − V_fb − V_{φ,s,min}) / V_T) − exp(−(V_g − V_fb − V_{φ,s,d}) / V_T) ]
I_off  =  W · μ_b · (q N_d t_ch / L) · ────────────────────────────────────────────────────────────────────────
                              [                                          1                                            ]
```

with

```
                    q N_d t_ch
V_{φ,s,d}  =  −  ───────────  ±  (something)                     (Eq. 3)
                    2 C_ox
```

and the extended-state density (Eq. 10)

```
                  ┌             q V_{φ,s,d}          ┐
Q_f  =  q N_f  · erf │  V_T · ───────────────      │                (Eq. 10)
                  └                                ┘
```

For v1 we use the off-state current expression with `N_f` and `N_d`
as **CALIBRATION_PARAMETER**. The erf approximation is in `Abramowitz &
Stegun handbook of mathematical functions, §7.1.26` — the
analytical approximation noted by the SCE paper.

### 2.7 V_th roll-off / DIBL (Eq. 11) — `PAPER_REPORTED` (functional form)

```
                  ┌                                                          ┐
                  │  cosh(L / (2λ)) · [1 − 1]    − 1                            │
ΔV_th  =  − ( 2 V_T / 1 ) · arccosh │  ─────────────────────────  +  ...        │
                  │  cosh(L / (2λ)) · [1 − (V_ψ_es / V_ψ_on)]    − 1            │
                  └                                                          ┘
```

The full Eq. 11 has three terms that all depend on the natural length
λ. The functional form `ΔV_th = f(L, λ, V_d)` is universal; the
specific coefficients in Eq. 11 are SCE-paper-specific.

For v1, we use the **functional form** with an **effective** λ
that is fitted to the Zhu I-V (because the SCE planar formula is
not directly valid for CAA). This is marked as
`CALIBRATION_PARAMETER`.

### 2.8 QFL and current (Eqs. 6–8) — `PAPER_REPORTED`

```
                      dV_ch
I_d  =  W · Q_f · μ_b · ────                                       (Eq. 6)
                       dy

V_ch(y)  =  ...                                                      (Eq. 7)

F(y)  =  exp(−V_ch(y) / V_T) / integral                               (Eq. 8)
```

`DERIVED_FROM_PAPER`: the QFL integral Eq. 8 is the same shape as
the 1D Zhu surface potential equation in the off-state limit.
For v1, the Zhu surface potential equation (Eq. 5 in §1) is used
instead, and the SCE QFL equation is the **cross-check** that the
off-state exponential is correct.

---

## 3. v1 Zhu 2T0C compact model

The v1 model combines the **Zhu I-V equations** (for the on-state
and the surface potential) with the **SCE off-state and DIBL
equations** (for the off-state current and the threshold shift with
drain bias). All other physics is captured by **calibration
parameters** that are fitted to the I-V data in §4.

### 3.1 Geometry (fixed) — `PAPER_REPORTED`

| Symbol         | Value          | Source            |
|----------------|----------------|-------------------|
| `L`            | 55 nm          | Zhu Fig. 5 caption|
| `CD`           | 50 nm          | Zhu Fig. 5 caption|
| `t_ch = t_IGZO`| 3 nm           | Zhu Fig. 5 caption|
| `t_ox = t_HfOx` | 8 nm           | Zhu Fig. 5 caption|
| `W_eff`        | π · CD ≈ 157 nm| Zhu Fig. 5 caption|

### 3.2 Material parameters (initial_guess_from_SCE_paper, then calibrated) — `CALIBRATION_PARAMETER`

| Symbol         | Initial guess (SCE) | v1 calibrated value | Fitted? |
|----------------|---------------------|----------------------|----------|
| `N_D`          | 1 × 10¹⁸ cm⁻³      | TBD in fit           | YES      |
| `N_V`          | (single-j N_V from Zhu) | TBD in fit     | YES      |
| `ε_s`          | 10                 | TBD in fit           | NO (use SCE value) |
| `ε_ox`         | 22                 | TBD in fit           | NO (use SCE value) |
| `μ_0` (sat)    | (from on-current)   | TBD in fit           | YES      |
| `USR`          | (from field dep.)   | TBD in fit           | YES      |
| `E_USC`        | (from field dep.)   | TBD in fit           | YES      |
| `V_fb`         | (from V_th)         | TBD in fit           | YES      |
| `μ_b` (off)    | 15 cm²/Vs          | TBD in fit           | NO (use SCE value as initial) |
| `η_eff`        | (DIBL)              | TBD in fit           | YES      |

### 3.3 Surface potential solver (Zhu Eq. 5)

`scripts/device_model_v1.py` will implement a Newton iteration to
solve the Zhu surface potential equation for each (V_g, V_d) pair.
The solver treats ψ_s as the unknown and iterates:

```
F(ψ_s) = C_ox/ε_ox · (V_g − V_fb − ψ_s)
       − (2 q N_V / ε_s) · ( exp((V_ψ − ψ_s) / V_T) − exp(−V_ψ / V_T) )
       + N_D · (1 − κ · ψ_s)

ψ_s^{new} = ψ_s^{old} − F(ψ_s) / F'(ψ_s)
```

where `V_ψ = q N_V t_ch / (C_ox ε_ox) − κ ψ_s` and `κ = exp(−t_ch/ε_ox) · 2 ε_s / L_D`.

### 3.4 Drain current (Zhu Eq. 6 simplified)

```
                          q N_D t_ch,eff              2 k_B T
I_d  =  (W_eff / L) · μ_eff · C_ox · [ (V_g − V_th) · ──────────  +  ────── · ln(exp((V_g − V_fb) / V_T) − 1) ]
                              C_ox                       q
```

The threshold voltage `V_th` is the V_g at which `I_d = I_ref = 10 nA`
(constant-current method, as in SCE paper).

### 3.5 DIBL (SCE functional form with effective λ)

```
V_th(V_d)  =  V_th(V_d → 0)  −  ΔV_th(L, λ_eff, V_d)
ΔV_th     ≈  (some analytical function)  fitted to Zhu Id-Vg(V_d) shift
```

The analytical functional form is the SCE Eq. 11 with `λ` replaced by
`λ_eff`, a calibration parameter. This is the **only** place where
the SCE paper is used in the on-state model.

### 3.6 Mobility

```
μ_eff  =  μ_0 / (1 + (USR · E_⊥)^E_USC)
E_⊥   =  C_ox · (V_g − V_fb − ψ_s) / ε_s
```

### 3.7 Off-state current (SCE Eq. 9, universal form)

```
                              [ exp(−(V_g − V_fb − V_{φ,s,min}) / V_T) − exp(−(V_g − V_fb − V_{φ,s,d}) / V_T) ]
I_off  =  W · μ_b · (q N_d t_ch / L) · ────────────────────────────────────────────────────────────────────────
                              [                                          1                                            ]
```

The Q_f expression (Eq. 10) is implicit; v1 uses the
`Abramowitz & Stegun` analytical approximation for `erf(x)`.

---

## 4. Calibration procedure (staged)

Each step is performed in order. If a step's calibration parameter
hits a bound, that is reported, not silently extended.

1. **Digitization correctness** — verify Fig. 5(d) and 5(e) at the
   cross-bias points `(V_g, V_d) ∈ {(0.4, 1.0), (1.2, 1.0), (2.0, 1.0)}`
   agree.
2. **V_th / horizontal alignment** — fix V_fb, V_ψ, and other
   surface-potential terms; tune until the Id-Vg turn-on is at the
   right V_g.
3. **Off-current** — tune N_d and N_f so the off-state exponential
   matches the low-V_g tail of Id-Vg.
4. **Subthreshold slope** — tune E_⊥ and ε_s so the Id-Vg slope in
   the exponential region matches.
5. **DIBL** — tune λ_eff so the Id-Vg(V_d) shift matches the
   V_d = 0.1 V → V_d = 1 V shift in the subthreshold region.
6. **On-current scale** — tune μ_0 so the strong-on Id-Vg at high V_g
   matches.
7. **Id-Vg curvature** — tune USR, E_USC so the high-V_g roll-off
   matches.
8. **Id-Vd linear slope** — tune W_eff (or μ_0) to match the
   low-V_d slope.
9. **Id-Vd saturation knee** — tune V_dsat definition (implicitly via
   surface potential) to match the knee.
10. **Id-Vd saturation slope** — verify; if the data shows
    non-zero dI/dV_d in saturation, add a minimal
    `CALIBRATION_EXTENSION` for channel-length modulation.
11. **Joint refinement** — `scipy.optimize.least_squares` with bounds
    on every parameter; report any parameter at bound.

---

## 5. Loss function

* **Id-Vg**: `log10(Id_model) − log10(Id_paper)` (log RMSE per V_d).
* **Id-Vd**: relative error `|Id_model − Id_paper| / max(|Id_paper|, 0.5 μA)`
  per V_g.
* **Cross-bias consistency**: high weight on the three shared bias
  points `(V_g, V_d) ∈ {(0.4, 1), (1.2, 1), (2.0, 1)}` — must agree
  between Id-Vg and Id-Vd sweeps.

If Id-Vg and Id-Vd disagree at a shared bias point, **STOP** and
re-check the digitization before fitting.

---

## 6. PASS criteria (summary)

1. Surface potential equation is the Zhu equation, NOT a free fit.
2. DIBL uses the SCE functional form with an effective λ.
3. Off-state current uses the SCE Eq. 9.
4. Geometry is fixed (Zhu paper values).
5. Id-Vg and Id-Vd at cross-bias points agree within ~20 %.
6. Python model and SPICE B-source agree to within ~1 %.
7. No parameter is at a bound without explanation.
8. Memory-relevant bias (V_g ~ 0–2 V, V_d ~ 0–1.5 V) is within
   ~30 % of the paper.
