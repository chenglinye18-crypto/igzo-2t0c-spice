"""
fit_device.py
=============

Fit a simple, paper-anchored surrogate I(Vg, Vd) model to the
digitized Fig 5(d,e) data, and emit an SPICE library that can be
included by the DC validation netlists.

Surrogate model
---------------
A simple, **non-physical** power-law surrogate that captures the
required trends without enforcing physical C_ox or mobility:

    Vov      = Vgs - Vth
    Vov_pos  = max(Vov, 0)
    Vov_neg  = min(Vov, 0)
    Vds_eff  = Vds * Vdsat / ( Vdsat**k + |Vds|**k + 1e-30 )**(1/k)
              with  Vdsat = alpha * Vov_pos
    I_on     = K * Vov_pos**a * Vds_eff
    I_sub    = K * (|Vov_neg| + Vth_off)^a  *  exp( Vov / (n * Vt) )
              with Vth_off a small offset so the exp doesn't blow up
    Id       = I_on + I_sub

The single fitting constant K absorbs W/L, C_ox, mu, and any bulk
conduction effects.  This is a BEHAVIORAL surrogate, not a physics
model.

Fit procedure
-------------
scipy.optimize.least_squares on (K, Vth, a, alpha, k_smooth) using
mixed log10 (Id-Vg) and relative (Id-Vd) residuals. Weights chosen
so the fit cares about both orders of magnitude (Id-Vg) and absolute
shape (Id-Vd).

Outputs
-------
- models/igzo_2t0c_v0.lib  (SPICE subckt with B-source)
- results/fit_report.json  (params and error metrics)
- results/idvg_idvd_fit.png  (overlay plot)
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import scipy.optimize as opt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
RESULTS = ROOT / "results"
MODELS.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

VT = 0.02585   # thermal voltage at 300 K


# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------
def load_csv(path: Path, ncols: int):
    rows = []
    with path.open() as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split(",")
            if len(parts) < ncols:
                continue
            try:
                vals = [float(x) for x in parts[:ncols]]
            except ValueError:
                continue
            rows.append(vals)
    return np.array(rows)


idvg = load_csv(DATA / "idvg.csv", 3)
idvd = load_csv(DATA / "idvd.csv", 4)
Vg_axis, Id_vd0p1, Id_vd1 = idvg[:, 0], idvg[:, 1], idvg[:, 2]
Vd_axis, Id_vg0p4, Id_vg1p2, Id_vg2 = idvd[:, 0], idvd[:, 1], idvd[:, 2], idvd[:, 3]


# ---------------------------------------------------------------
# Surrogate model in Python
# ---------------------------------------------------------------
def id_pred(vgs, vds, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub):
    """Surrogate I_d(Vgs, Vds) in Amps.

    log_K     = log10(K), K in A/V^a
    Vth       = threshold voltage (V)
    a_exp     = exponent on Vov (typically ~2)
    alpha_vdsat = Vdsat = alpha_vdsat * Vov
    k_smooth  = smoothness of triode/sat blend
    n_sub     = sub-threshold ideality factor

    v0 Vds_eff: smooth MIN(Vds, Vdsat) using a tanh-like soft clamp.
        Vds_eff = 0.5 * (Vds + Vdsat - sqrt((Vds-Vdsat)^2 + eps^2))
        => at Vds << Vdsat: Vds_eff ~ Vds
        => at Vds >> Vdsat: Vds_eff ~ Vdsat
    """
    vgs = np.asarray(vgs, dtype=float)
    vds = np.asarray(vds, dtype=float)
    K = 10.0 ** log_K
    Vov = vgs - Vth
    Vov_pos = np.maximum(Vov, 0.0)
    Vov_neg = np.minimum(Vov, 0.0)
    Vdsat = alpha_vdsat * Vov_pos
    # Soft MIN with SIGNED Vds so reverse Vds gives negative current
    # Vds_eff is the smooth clipped value (always between 0 and Vdsat in magnitude)
    # The sign of Vds_eff is the sign of Vds
    eps = 1e-6
    Vds_eff_mag = 0.5 * (np.abs(vds) + Vdsat - np.sqrt((np.abs(vds) - Vdsat) ** 2 + eps ** 2))
    Vds_eff = np.sign(vds) * Vds_eff_mag
    I_on = K * np.power(Vov_pos + 1e-12, a_exp) * Vds_eff
    # Sub-threshold floor
    I_sub = K * 1e-6 * np.exp(np.minimum(Vov_neg, 0.0) / (n_sub * VT))
    return I_on + I_sub


def residuals(params):
    log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub = params
    # Id-Vg (Vg varies, Vd fixed at 0.1 V and 1 V)
    p_0p1 = id_pred(Vg_axis, np.full_like(Vg_axis, 0.1), log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub)
    p_1 = id_pred(Vg_axis, np.full_like(Vg_axis, 1.0), log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub)
    # log10 RMSE
    def safe_log(x):
        return np.log10(np.maximum(x, 1e-30))
    res_idvg_0p1 = safe_log(p_0p1) - safe_log(np.maximum(Id_vd0p1, 1e-30))
    res_idvg_1 = safe_log(p_1) - safe_log(np.maximum(Id_vd1, 1e-30))
    # Id-Vd (Vg fixed, Vd varies)
    p_0p4 = id_pred(np.full_like(Vd_axis, 0.4), Vd_axis, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub) * 1e6
    p_1p2 = id_pred(np.full_like(Vd_axis, 1.2), Vd_axis, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub) * 1e6
    p_2 = id_pred(np.full_like(Vd_axis, 2.0), Vd_axis, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub) * 1e6
    def rel(y, t):
        return (y - t) / np.maximum(np.abs(t), 0.5)
    res_idvd_0p4 = rel(p_0p4, Id_vg0p4)
    res_idvd_1p2 = rel(p_1p2, Id_vg1p2)
    res_idvd_2 = rel(p_2, Id_vg2)
    return np.concatenate([res_idvg_0p1, res_idvg_1, res_idvd_0p4, res_idvd_1p2, res_idvd_2])


# Initial guess and bounds
#   log_K      : log10 K in A/V^a. We need ~1e-4 A at Vov~1V, so K ~ 1e-4.
#   Vth        : -0.5 to 0
#   a_exp      : 1.5 to 2.5
#   alpha_vdsat: 0.5 to 1.5
#   k_smooth   : 1.5 to 4
#   n_sub      : 1.0 to 3.0
x0 = [math.log10(2e-4), -0.3, 2.0, 0.7, 2.5, 1.5]
lb = [math.log10(1e-6), -1.5, 1.0, 0.3, 1.1, 1.0]
ub = [math.log10(1e-1),  0.5, 3.5, 2.0, 5.0, 3.0]

print("Fitting surrogate model ...")
res = opt.least_squares(
    residuals, x0, bounds=(lb, ub),
    method="trf", xtol=1e-14, ftol=1e-14, max_nfev=200000, verbose=1,
)
log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub = res.x
K = 10.0 ** log_K
print(f"\nFitted parameters:")
print(f"  K           = {K:.4e} A/V^{a_exp:.2f}")
print(f"  Vth         = {Vth:.4f} V")
print(f"  a_exp       = {a_exp:.4f}")
print(f"  alpha_vdsat = {alpha_vdsat:.4f}")
print(f"  k_smooth    = {k_smooth:.4f}")
print(f"  n_sub       = {n_sub:.4f}")


def log_rmse(y, t):
    return float(np.sqrt(np.mean((np.log10(np.maximum(y, 1e-30)) - np.log10(np.maximum(t, 1e-30))) ** 2)))


def rel_rmse(y, t):
    return float(np.sqrt(np.mean(((y - t) / np.maximum(np.abs(t), 0.5)) ** 2)))


# Recompute predictions for metrics
p_0p1 = id_pred(Vg_axis, np.full_like(Vg_axis, 0.1), log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub)
p_1 = id_pred(Vg_axis, np.full_like(Vg_axis, 1.0), log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub)
p_0p4 = id_pred(np.full_like(Vd_axis, 0.4), Vd_axis, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub) * 1e6
p_1p2 = id_pred(np.full_like(Vd_axis, 1.2), Vd_axis, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub) * 1e6
p_2 = id_pred(np.full_like(Vd_axis, 2.0), Vd_axis, log_K, Vth, a_exp, alpha_vdsat, k_smooth, n_sub) * 1e6

metrics = {
    "model_type": "BEHAVIORAL_SURROGATE",
    "idvg": {
        "log10_RMSE_Vd0p1": log_rmse(p_0p1, Id_vd0p1),
        "log10_RMSE_Vd1": log_rmse(p_1, Id_vd1),
    },
    "idvd": {
        "rel_RMSE_Vg0p4": rel_rmse(p_0p4, Id_vg0p4),
        "rel_RMSE_Vg1p2": rel_rmse(p_1p2, Id_vg1p2),
        "rel_RMSE_Vg2p0": rel_rmse(p_2, Id_vg2),
    },
    "params": {
        "K_A_per_VpowA": K,
        "log10_K": log_K,
        "Vth_V": Vth,
        "a_exp": a_exp,
        "alpha_vdsat": alpha_vdsat,
        "k_smooth": k_smooth,
        "n_sub": n_sub,
    },
    "cost": float(res.cost),
    "status": int(res.status),
    "message": res.message,
    "success": bool(res.success),
}
print("\nMetrics:")
print(json.dumps(metrics, indent=2))

with (RESULTS / "fit_report.json").open("w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print(f"  -> {RESULTS / 'fit_report.json'}")

# Plot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
ax = axs[0]
ax.semilogy(Vg_axis, np.maximum(Id_vd0p1, 1e-30), "o", color="orange", label="paper Vd=0.1V", markersize=4)
ax.semilogy(Vg_axis, np.maximum(Id_vd1, 1e-30), "s", color="darkorange", label="paper Vd=1V", markersize=4)
ax.semilogy(Vg_axis, np.maximum(p_0p1, 1e-30), "-", color="orange", alpha=0.7, label="fit Vd=0.1V")
ax.semilogy(Vg_axis, np.maximum(p_1, 1e-30), "-", color="darkorange", alpha=0.7, label="fit Vd=1V")
ax.set_xlabel("Vg (V)")
ax.set_ylabel("Id (A)")
ax.set_title("Id-Vg (Fig 5d)")
ax.grid(True, which="both", alpha=0.3)
ax.legend(fontsize=8)

ax = axs[1]
ax.plot(Vd_axis, Id_vg0p4, "o", color="lightblue", label="paper Vg=0.4V", markersize=4)
ax.plot(Vd_axis, Id_vg1p2, "s", color="steelblue", label="paper Vg=1.2V", markersize=4)
ax.plot(Vd_axis, Id_vg2, "^", color="navy", label="paper Vg=2.0V", markersize=4)
ax.plot(Vd_axis, p_0p4, "-", color="lightblue", alpha=0.7, label="fit Vg=0.4V")
ax.plot(Vd_axis, p_1p2, "-", color="steelblue", alpha=0.7, label="fit Vg=1.2V")
ax.plot(Vd_axis, p_2, "-", color="navy", alpha=0.7, label="fit Vg=2.0V")
ax.set_xlabel("Vd (V)")
ax.set_ylabel("Id (uA)")
ax.set_title("Id-Vd (Fig 5e)")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(RESULTS / "idvg_idvd_fit.png", dpi=120)
print(f"  -> {RESULTS / 'idvg_idvd_fit.png'}")


# ---------------------------------------------------------------
# Emit SPICE library
# ---------------------------------------------------------------
lib_path = MODELS / "igzo_2t0c_v0.lib"
with lib_path.open("w", encoding="utf-8") as f:
    f.write(f"""* =====================================================================
*  igzo_2t0c_v0.lib
*  --------------------------------------------------------------------
*  Paper-anchored BEHAVIORAL SURROGATE model for the Zhu 2T0C OSFET
*  device.  NOT a re-implementation of Zhu's surface-potential compact
*  model.  See reference_notes.md and scripts/fit_device.py.
*
*  The model captures:
*    - sub-threshold leakage
*    - smooth triode-to-saturation transition
*    - on-current in the same order of magnitude as paper Fig 5
*
*  It does NOT capture:
*    - DIBL, channel-length modulation
*    - BTI, self-heating, gate leakage
*    - body effect
*    - separate mobility model; K is a lumped behavioral constant
*
*  Geometry (from Fig. 5 caption, paper):
*    L         = 55 nm
*    CD        = 50 nm
*    t_IGZO    = 3 nm
*    t_HfOx    = 8 nm
*    W_eff     = pi * CD  (used in the paper's compact model; not used
*                          in this surrogate; K absorbs geometry)
*
*  PAPER_ANCHORED_SURROGATE
*  NOT_ZHU_ORIGINAL_COMPACT_MODEL
* =====================================================================

.SUBCKT XOSFET_2T0C D G S B
*   D -- drain
*   G -- gate
*   S -- source
*   B -- body (tied to S internally; no separate body model in v0)

*  Surrogate parameters
.PARAM K_2T0C={K:.6e}
.PARAM VTH_2T0C={Vth:.6f}
.PARAM A_2T0C={a_exp:.6f}
.PARAM ALPHA_VDSAT_2T0C={alpha_vdsat:.6f}
.PARAM K_SMOOTH_2T0C={k_smooth:.6f}
.PARAM N_SUB_2T0C={n_sub:.6f}

*  I_d(Vgs, Vds):
*    Vov    = V(G,S) - VTH_2T0C
*    Vov_p  = MAX(Vov, 0)
*    Vov_n  = MIN(Vov, 0)
*    Vdsat  = ALPHA_VDSAT_2T0C * Vov_p
*    Vds_eff= V(D,S) * Vdsat / (Vdsat^K_SMOOTH + |V(D,S)|^K_SMOOTH + 1e-30)^(1/K_SMOOTH)
*    I_on   = K_2T0C * (Vov_p + 1e-12)^A_2T0C * Vds_eff
*    I_sub  = K_2T0C * 1e-6 * exp(MIN(Vov_n, 0) / (N_SUB_2T0C * 0.02585))
*    I_d    = I_on + I_sub
*
*  Caveat: at Vov > 0 the sub-threshold term evaluates to a constant
*  K_2T0C * 1e-6 * exp(0) = K_2T0C * 1e-6 A (a small on-region floor,
*  used to keep ngspice numerical at Vgs = VWL_OFF).  At Vov < 0, the
*  exponential decays the sub-threshold current.

B_ID D S I=
+    (K_2T0C *
+     (MAX(V(G,S) - VTH_2T0C, 0) + 1e-12) ** A_2T0C *
+     SGN(V(D,S)) *
+     (0.5 * (ABS(V(D,S)) + ALPHA_VDSAT_2T0C*MAX(V(G,S) - VTH_2T0C, 0) -
+      SQRT((ABS(V(D,S)) - ALPHA_VDSAT_2T0C*MAX(V(G,S) - VTH_2T0C, 0))**2 + 1e-12)
+     ))
+    ) +
+    (K_2T0C * 1.0e-6 *
+     EXP(MIN(V(G,S) - VTH_2T0C, 0) / (N_SUB_2T0C * 0.02585))
+    )

*  No device-internal capacitance (lumped outside in the parasitic RC).
.ENDS XOSFET_2T0C


*  Convenience alias for DC Id-Vg / Id-Vd sweeps (B tied to S).
.SUBCKT XOSFET_DC D G S
X1 D G S S XOSFET_2T0C
.ENDS XOSFET_DC
""")
print(f"  -> {lib_path}")
