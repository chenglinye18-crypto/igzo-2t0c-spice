# UNRESOLVED — v1 Zhu 2T0C compact model

This file documents known issues and un-resolved questions about v1. Each
item is tagged with severity (BLOCKING / MAJOR / MINOR) and a reference
back to `model_equations.md` or the data files.

---

## U-1 (MAJOR) Zhu's N_V,j sub-band sum not used

The Zhu paper Eq. 5 has an explicit Σ over sub-bands
`Σ_j N_{V,j} (exp(V_ψ,j − V_ψ,s) − exp(−V_ψ,j))`.
Without the author's calibrated N_{V,j} values, we cannot solve Eq. 5
faithfully. v1 replaces the full Eq. 5 with the standard charge-sheet form
`ψ_s = m·V_T·ln(1+exp((V_g−V_fb−V_th0)/m·V_T))`. This is structurally the
same as the gradual-channel limit but loses the N_V-dependent threshold
shift. See `model_equations.md §2.5` and §3.3.

**Action:** if the author's parameter deck becomes available, switch to the
full Eq. 5 and re-fit. The staged calibration in `fit_device_v1.py` is
designed to be re-run with minimal changes.

---

## U-2 (MAJOR) SCE paper's natural length λ not portable to CAA

The SCE paper Eq. 5 gives `λ = (t_ch/ε_ox)·η·√(C_s/C_ox)` for planar
BG/DG OS-TFTs. The Zhu 2T0C is a vertically-stacked CAA-CAA structure
where the channel is a thin IGZO shell wrapped around a vertical pillar
(W_eff = π·CD). The SCE planar formula is **not** valid for CAA.

v1 uses an effective DIBL parameter `alpha_DIBL` (CALIBRATION_PARAMETER)
that captures the threshold shift with V_d, but the underlying physics
(cylindrical field, radial depletion) is not modeled. See
`model_equations.md §2.5` and §3.5.

**Action:** if a cylindrical 2D Poisson solution is needed, a
DD-Mode-Space or similar numerical approach would be required. Out of v1 scope.

---

## U-3 (MAJOR) Id-Vd low-Vd slope and saturation knee are off

The staged calibration gives `Id-Vd rel RMSE per Vg ≈ 0.96` because:

* At very low Vd (0.05–0.1 V), the data shows a finite current that
  does **not** follow `Id ∝ Vd` exactly. Likely cause: contact resistance
  or velocity-saturation at low field. v1 has no `R_contact` parameter.
* At the saturation knee (Vd ~ 1 V for Vg=2V), the data shows Id
  continuing to grow roughly linearly with Vd up to Vd=3V (no clear
  saturation). The v1 model saturates at V_ds,sat = α_sat·V_ov. Either
  α_sat is too small (allowing more linear behavior) or the device has
  no clean saturation region in this data.

The data also shows: at Vg=2V, the Id grows from 13 μA at Vd=0.5V to
55 μA at Vd=3V (a 4× range). For a clean saturation device, the ratio
should be 1–2×. The device is therefore NOT in classic saturation in
the Vd range probed. v1 cannot reproduce this with a single α_sat value.

**Action:** if Zhu paper Fig 5(e) is re-digitized with a smaller Vd
step near 0, a contact-resistance value can be added. This would require
a `CALIBRATION_EXTENSION` (R_series, R_contact) and is not in v1 scope.

---

## U-4 (MAJOR) Off-state subthreshold slope and noise floor

The data shows: at Vg = -0.5 V, Id = 1e-14 A (the noise floor of the
measurement, presumably). The v1 model gives Id = exp(...) which
continues to decrease exponentially below this. The model is therefore
in agreement with the data in this regime, but the **subthreshold slope**
is determined by `m_body` (currently 1.8) which was set by grid search.
The actual subthreshold slope of the data is roughly 250 mV/decade,
corresponding to m_body ≈ 4. The v1 model uses m_body=1.8 because the
fit minimizes an aggregate loss that includes the on-state.

**Action:** if a stricter subthreshold fit is needed, separate the
loss weighting for Vg < 0.3 V from Vg > 0.5 V and re-fit. The staged
calibration already supports this via the `stage_off` function.

---

## U-5 (MINOR) Id-Vg on-state amplitude under-predicts by 2-5x

At Vd=0.1V (linear region), the v1 model gives Id(Vg=2V) ≈ 4.3 μA
where the data says 35 μA. The v1 model gives Id(Vg=1.2V) ≈ 1.7 μA
where the data says 6 μA. The Id-Vd at Vd=1V is closer (within 30%).

The 2–5× under-prediction in the linear region likely indicates that
the effective on-state prefactor in this 2T0C device is higher than
what the simplified Zhu Eq. 6 form gives without the author's N_V,j
calibration. v1 has `K_pre` as a single global calibration
parameter; per-Vg tuning is not done.

**Action:** the staged fit tries multiple K_pre values; the best one
balances over- and under-prediction. A finer grid search or per-Vg K_pre
is possible but would risk overfitting.

---

## U-6 (MINOR) Cross-bias disagreement in source data

At (Vg=2 V, Vd=1 V), Fig 5(d) (Id-Vg at Vd=1V) shows Id ≈ 5×10⁻⁵ A
(50 μA, in saturation plateau), while Fig 5(e) (Id-Vd at Vg=2V)
shows Id ≈ 22 μA (linear region). The two should agree; they don't
by 2.3×. v1 reports both values without forcing them to be equal,
and the loss function penalizes the disagreement via `w_cross` term.

**Action:** if a cross-bias fix is needed, redo one of the
digitizations. The data is in `data/idvg.csv` and `data/idvd.csv`.
See `data/DIGITIZATION_NOTES.md` for the rationale.

---

## U-7 (MINOR) Joint refinement skipped

Stage 11 in `fit_device_v1.py` is the joint refinement with
`scipy.optimize.least_squares`. With the current model form, the joint
fit pushes 7 of 11 parameters to their bounds (most of them at the
physical upper/lower limit), indicating the model is **not identifiable**
in the joint sense. We skip the joint refinement and use the stage 8-10
result as the final v1 parameters.

**Action:** the model is identifiable only if the prior (SCE Table I)
is enforced more strictly. v1 takes a step in this direction by fixing
`eps_s=10, eps_ox=22, N_D=1e18` from SCE. A Bayesian fit with explicit
priors would be more principled, but is out of v1 scope.

---

## U-8 (MINOR) No percolation term

The Zhu paper Eq. 6 has an explicit percolation correction term. v1
omits it (model_equations.md §2.5) and absorbs the < 1 effect into μ_0.
This is acceptable for the bias range we fit (Vg -1 to 2 V, Vd 0 to 3 V),
but may matter at very low Vg or in the deep subthreshold.

**Action:** if percolation is needed, add it as a multiplicative
factor on μ_0: `μ_eff = μ_0·(1 + M_P·(V_ov/V_0)^n) / (1 + (USR·E_⊥)^E_USC)`.
Not in v1.

---

## U-9 (MINOR) No BTI / hysteresis

The Zhu paper has a state-based BTI model (PBTI/NBTI, relaxation,
stress-history dependence). v1 is a DC I-V model only. BTI is **out of
v1 scope** per the user instructions.

**Action:** not applicable to v1.

---

## U-10 (MINOR) No temperature dependence

The v1 model uses T=300K (V_T = 25.85 mV). The Zhu paper includes
temperature dependence explicitly. v1 has no `T` parameter; it would
need to be added for any thermal study (out of v1 scope).

**Action:** not applicable to v1.
