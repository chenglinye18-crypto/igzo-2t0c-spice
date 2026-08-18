"""Zhu 2T0C IEDM 2026 physics-based compact model — v1 Python reference.

Implements the equations documented in `model_equations.md`:

  * Surface potential ψ_s via the charge-sheet relation that *approximates*
    Zhu Eq. (5) in the single-j simplification limit. The exact Zhu equation
    has an N_V-related exponential that requires the author's parameter deck
    to solve reliably; we use the universal smooth form
        ψ_s = m·V_T · ln( 1 + exp((V_g − V_fb − V_th0)/m·V_T) )
    which is the gradual-channel limit (UNRESOLVED for the original N_V
    form).

  * Drain current: OSFET form anchored to the Zhu paper's drift-diffusion
    structure (Eq. 6 simplified). The on-state current is
        I_d = (W/L) · μ_eff · C_ox · V_ov · V_d_eff · K_pre
    with a field-dependent mobility μ_eff = μ_0/(1 + (USR·E_⊥)^E_USC).
    K_pre is a CALIBRATION_PARAMETER that absorbs the unknown prefactor
    in Zhu's N_V·t_ch,eff term (model_equations.md §3.4).
    The V_ov^n power-law characteristic of OSFETs is captured by the
    field-dependent mobility; the exponent n is effectively n ≈ 1 + δ
    where δ is the roll-off strength from USR.

  * Off-state current (SCE Eq. 9 universal form):
        I_off = (W/L) · μ_b · C_ox · (m·V_T)^2 · exp((V_g − V_th)/m·V_T)
                                         · (1 − exp(−V_d/V_T))

  * DIBL via SCE Eq. (11) functional form with effective α_DIBL
    (CALIBRATION_PARAMETER; the SCE λ formula is for planar BG/DG, not
    for CAA — see model_equations.md §2.5).

Provenance: every parameter is tagged. Geometry is fixed from Zhu Fig.5
caption.
"""
from __future__ import annotations

import math
import numpy as np

# physical constants
Q = 1.602176634e-19      # C
K_B = 1.380649e-23       # J/K
EPS0 = 8.854187817e-12   # F/m
T_DEFAULT = 300.0        # K
V_T = K_B * T_DEFAULT / Q  # ~0.02585 V at 300 K

# fixed geometry from Zhu Fig 5 caption (PAPER_REPORTED)
L_nm = 55.0
CD_nm = 50.0
t_ch_nm = 3.0
t_ox_nm = 8.0
W_eff_nm = math.pi * CD_nm  # ≈ 157 nm

L = L_nm * 1e-9
CD = CD_nm * 1e-9
t_ch = t_ch_nm * 1e-9
t_ox = t_ox_nm * 1e-9
W_eff = W_eff_nm * 1e-9

# default parameters
DEFAULTS = dict(
    # material (initial_guess_from_SCE_paper — Table I)
    N_D=1.0e18,        # cm^-3  donor density
    eps_s=10.0,
    eps_ox=22.0,
    mu_0=80.0,         # cm^2/Vs — on-state mobility (CALIBRATION_PARAMETER)
    mu_b=15.0,         # cm^2/Vs — band mobility, off-state (SCE Table I)
    # mobility field-dependence (Zhu Eq. 7)
    USR=2.0e-9,        # m/V — vertical-field coefficient (calibrated)
    E_USC=1.5,         # exponent
    # threshold / flat-band (CALIBRATION_PARAMETER)
    V_fb=-0.5,         # V — flat-band voltage
    V_th0=0.5,         # V — threshold (constant-current, I_ref=10nA)
    m_body=1.5,        # body factor / ideality
    # SCE DIBL
    lambda_eff=15.0e-9,# m — effective natural length for DIBL
    alpha_DIBL=0.05,   # V/V — DIBL: ΔV_th = -alpha_DIBL · V_d
    # saturation knee
    alpha_sat=1.0,     # V_ds,sat = alpha_sat * V_ov
    # channel-length modulation (CALIBRATION_EXTENSION)
    CLM=0.10,          # dimensionless — dI/dV_d beyond V_ds,sat
    # current prefactor (CALIBRATION_PARAMETER; absorbs unknown N_V factor)
    K_pre=0.5,         # dimensionless scaling on on-state
    # on-state power-law exponent (CALIBRATION_EXTENSION; captures the
    # effective V_ov^n scaling of OSFET I-V not directly in Zhu Eq. 6)
    n_power=2.0,       # Id ∝ V_ov^n_power
)


def si_units(p):
    out = dict(p)
    out['N_D']  = p['N_D']  * 1e6
    out['mu_0'] = p['mu_0'] * 1e-4
    out['mu_b'] = p['mu_b'] * 1e-4
    return out


def body_factor(p):
    P = si_units(p)
    eps_s = P['eps_s'] * EPS0
    eps_ox = P['eps_ox'] * EPS0
    C_ox = eps_ox / t_ox
    C_s = eps_s / t_ch
    return 1.0 + C_s / C_ox, C_ox


def surface_potential(V_g, V_d, p):
    """Approximate ψ_s via the charge-sheet model.

        ψ_s = m·V_T·ln(1 + exp((V_g−V_fb−V_th0)/m·V_T)) − α_DIBL·V_d
    """
    P = si_units(p)
    mV_T = P['m_body'] * V_T
    x = (V_g - P['V_fb'] - P['V_th0']) / mV_T
    if x > 50:
        psi = x * mV_T
    elif x < -50:
        psi = 0.0
    else:
        psi = mV_T * math.log(1.0 + math.exp(x))
    psi = max(psi - P['alpha_DIBL'] * V_d, 0.0)
    return psi


def body_factor(p):
    """Returns (m_physical, C_ox) where m_physical = 1 + C_s/C_ox.

    Note: m_physical is for documentation; the actual body factor used
    in the off-state is p['m_body'] (calibration parameter)."""
    P = si_units(p)
    eps_s = P['eps_s'] * EPS0
    eps_ox = P['eps_ox'] * EPS0
    C_ox = eps_ox / t_ox
    C_s = eps_s / t_ch
    return 1.0 + C_s / C_ox, C_ox


def V_th_effective(V_d, p):
    return si_units(p)['V_th0'] - si_units(p)['alpha_DIBL'] * V_d


def mobility(V_g, V_d, p, psi_s=None):
    """Field-dependent mobility (Zhu Eq. 7 simplified)."""
    P = si_units(p)
    _, C_ox = body_factor(p)
    if psi_s is None:
        psi_s = surface_potential(V_g, V_d, p)
    E_perp = C_ox * (V_g - P['V_fb'] - psi_s) / (P['eps_s'] * EPS0)
    mu_0 = P['mu_0']
    if abs(P['USR'] * E_perp) < 1e-30:
        return mu_0
    return mu_0 / (1.0 + abs(P['USR'] * E_perp) ** P['E_USC'])


def drain_current(V_g, V_d, p):
    """Compute I_d at (V_g, V_d) in amperes.

    On-state (anchored to Zhu Eq. 6):
        I_on = (W/L) · μ_eff · C_ox · V_ov · V_d_eff · K_pre
    with V_ov = V_g − V_th(V_d), V_d_eff = min(V_d, V_ds_sat) (linear
    region) and V_d_eff = V_ds_sat · (1 + CLM·(V_d−V_ds_sat)) in
    saturation.

    Off-state (SCE Eq. 9 universal form):
        I_off = (W/L) · μ_b · C_ox · (m·V_T)^2 · exp((V_g − V_th)/m·V_T)
                                         · (1 − exp(−V_d/V_T))

    Smooth blend via a logistic on V_ov around 0 with width m·V_T.
    """
    P = si_units(p)
    _, C_ox = body_factor(p)
    m_eff = P['m_body']
    psi_s = surface_potential(V_g, V_d, p)
    V_th = V_th_effective(V_d, p)
    V_ov = V_g - V_th
    mu = mobility(V_g, V_d, p, psi_s)

    # ---- on-state ----
    V_ds_sat = max(P['alpha_sat'] * V_ov, 0.0)
    V_d_eff = min(V_d, V_ds_sat) if V_ds_sat > 0 else V_d
    if V_d > V_ds_sat and V_ds_sat > 0:
        V_d_eff = V_ds_sat * (1.0 + P['CLM'] * (V_d - V_ds_sat))
    if V_ov > 0 and V_d_eff > 0:
        n_p = P['n_power']
        I_on = P['K_pre'] * (W_eff / L) * mu * C_ox * (V_ov ** n_p) * V_d_eff
    else:
        I_on = 0.0
    if I_on < 0 or not math.isfinite(I_on):
        I_on = 0.0

    # ---- off-state (only in subthreshold; clamped above V_th) ----
    mu_b = P['mu_b']
    mV_T = m_eff * V_T
    x_sub = (V_g - V_th) / mV_T
    if x_sub > 10:   # well above threshold: clamp to I_ref-level
        I_off = (W_eff / L) * mu_b * C_ox * (mV_T ** 2) \
                * math.exp(10) * (1.0 - math.exp(-V_d / V_T))
    elif x_sub < -50:
        I_off = 0.0
    else:
        I_off = (W_eff / L) * mu_b * C_ox * (mV_T ** 2) \
                * math.exp(x_sub) * (1.0 - math.exp(-V_d / V_T))
    if not math.isfinite(I_off) or I_off < 0:
        I_off = 0.0

    # smooth blend: width 1·mV_T around V_ov = 0
    if V_ov > 50 * mV_T:
        return I_on
    if V_ov < -50 * mV_T:
        return I_off
    w_on = 1.0 / (1.0 + math.exp(-V_ov / (1.0 * mV_T)))
    return w_on * I_on + (1.0 - w_on) * I_off


def Id_array(V_g_sweep, V_d_sweep, p, mode='idvg', Vg_fixed=None, Vd_fixed=None):
    if mode == 'idvg':
        Vd = Vd_fixed if Vd_fixed is not None else V_d_sweep
        out = np.array([drain_current(float(Vg), float(Vd), p) for Vg in V_g_sweep])
    elif mode == 'idvd':
        Vg = Vg_fixed if Vg_fixed is not None else V_g_sweep
        out = np.array([drain_current(float(Vg), float(Vd), p) for Vd in V_d_sweep])
    else:
        raise ValueError(mode)
    return out


if __name__ == '__main__':
    p = DEFAULTS
    m, C_ox = body_factor(p)
    print('V_T =', V_T, 'V')
    print('C_ox =', C_ox, 'F/m^2')
    print('W_eff =', W_eff*1e9, 'nm  W/L =', W_eff/L)
    print('m =', m)
    for Vd in (0.1, 1.0):
        for Vg in (-0.5, 0, 0.4, 1.2, 2.0):
            psi = surface_potential(Vg, Vd, p)
            mu = mobility(Vg, Vd, p, psi)
            Vth = V_th_effective(Vd, p)
            print(f'  Vg={Vg:5.2f} Vd={Vd:4.2f}  psi={psi:7.4f}  Vth={Vth:6.3f}  Vov={Vg-Vth:6.3f}  mu={mu*1e4:7.3f} cm2/Vs  Id={drain_current(Vg, Vd, p)*1e6:8.3f} uA')
