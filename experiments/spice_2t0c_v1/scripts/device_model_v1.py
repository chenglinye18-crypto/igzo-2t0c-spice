"""Zhu 2T0C IEDM 2026 physics-based compact model — v1.1 Python reference.

v1.1 changes (from v1):
  * V_d_eff formula changed from piecewise min(Vd, V_ds,sat) to a
    smooth-min: V_d_eff = Vd·Vdsat / sqrt(Vd^2 + Vdsat^2). This
    preserves the correct asymptotes (Vd_eff -> Vd for Vd<<Vdsat,
    Vd_eff -> Vdsat for Vd>>Vdsat) and is C^1 smooth. The v1 piecewise
    formula could not capture the soft saturation observed in the
    paper's Id-Vd at Vg=2V (Id grows only 1.43x from Vd=0.1 to Vd=1,
    not the 10x expected from linear-region Vd scaling).
  * n_power, K_pre, alpha_sat, CLM, alpha_DIBL retuned to fit the
    smooth-min formula. See fit_report_v11.json for the v1.1 values.
  * Removed dependence on `psi_s` field-dependent mobility: the
    field-dependent μ_eff (Zhu Eq. 7) is retained, but USR is set
    to a small value (1e-14) so the on-state amplitude is dominated
    by K_pre. The 2T0C CAA geometry produces a very high vertical
    field at the gate oxide; without the author's parameter deck the
    field-rolling is not constrained, so we use μ_eff ≈ μ_0 in v1.1.
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

# fixed geometry from Zhu Fig 5 caption (PAPER_REPORTED, FROZEN)
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

# v1.1 default parameters (calibrated for smooth-min V_d_eff)
DEFAULTS = dict(
    # material (initial_guess_from_SCE_paper — Table I)
    N_D=1.0e18,
    eps_s=10.0,
    eps_ox=22.0,
    mu_0=80.0,         # cm^2/Vs — on-state mobility
    mu_b=15.0,         # cm^2/Vs — band mobility (SCE Table I)
    # mobility field-dependence (Zhu Eq. 7)
    USR=1.0e-14,       # m/V — small (effectively off; v1.1 default)
    E_USC=1.5,         # exponent
    # threshold / flat-band (CALIBRATION_PARAMETER)
    V_fb=-0.5,
    V_th0=0.4,
    m_body=1.8,
    # SCE DIBL (CALIBRATION_PARAMETER; effective alpha_DIBL for CAA)
    lambda_eff=15.0e-9,
    alpha_DIBL=0.08,   # v1.1: tuned to match low-Vd Id-Vd at Vg=2
    # saturation knee (v1.1: small alpha_sat with smooth-min V_d_eff)
    alpha_sat=0.03,
    # channel-length modulation (CALIBRATION_EXTENSION; not used in v1.1 best fit)
    CLM=0.0,
    # current prefactor (CALIBRATION_PARAMETER; v1.1 tuned)
    K_pre=0.7,
    # on-state power-law exponent (CALIBRATION_EXTENSION; v1.1 tuned)
    n_power=1.7,
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
    """Approximate ψ_s via the charge-sheet model (gradual-channel limit)."""
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


def V_d_eff_smooth_min(V_d, V_ds_sat):
    """Smooth-min V_d_eff (v1.1 NEW; replaces v1's piecewise min).

    Asymptotes:
        Vd << Vdsat: Vd_eff -> Vd
        Vd >> Vdsat: Vd_eff -> Vdsat
    C^1 smooth, no kink.
    """
    if V_ds_sat <= 0:
        return V_d
    denom = math.sqrt(V_d * V_d + V_ds_sat * V_ds_sat)
    return V_d * V_ds_sat / denom


def drain_current(V_g, V_d, p):
    """Compute I_d at (V_g, V_d) in amperes.

    On-state (anchored to Zhu Eq. 6, with smooth-min V_d_eff):
        I_on = K_pre · (W/L) · μ_eff · C_ox · V_ov^n · V_d_eff
    with V_ov = V_g − V_th_eff, V_ds_sat = α_sat · V_ov,
    and V_d_eff = Vd·Vdsat / sqrt(Vd² + Vdsat²)  (v1.1 NEW; was piecewise min)
    plus an additive CLM term on the saturated value:
        V_d_eff += CLM · (V_d − V_ds_sat)·(V_d > V_ds_sat)
    (i.e. CLM adds a linear Vd term in the saturation regime, not a
    multiplicative factor on V_d_eff like v1 had).

    Off-state (SCE Eq. 9 universal form, clamped above V_th):
        I_off = (W/L)·μ_b·C_ox·(m·V_T)^2·exp(min(x_sub,10))·(1−exp(−V_d/V_T))

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
    V_d_eff = V_d_eff_smooth_min(V_d, V_ds_sat)
    # CLM: additive linear term beyond V_ds_sat
    if V_d > V_ds_sat and V_ds_sat > 0:
        V_d_eff = V_d_eff + P['CLM'] * (V_d - V_ds_sat)
    if V_ov > 0:
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
    if x_sub > 10:
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
            Vdsat = max(p['alpha_sat']*(Vg-Vth), 0)
            Vdeff = V_d_eff_smooth_min(Vd, Vdsat)
            if Vd > Vdsat and Vdsat > 0:
                Vdeff += p['CLM']*(Vd-Vdsat)
            print(f'  Vg={Vg:5.2f} Vd={Vd:4.2f}  psi={psi:7.4f}  Vth={Vth:6.3f}  Vov={Vg-Vth:6.3f}  Vdsat={Vdsat:6.3f}  Vdeff={Vdeff:6.3f}  Vdeff/Vd={Vdeff/Vd:5.3f}  Id={drain_current(Vg, Vd, p)*1e6:8.3f} uA')
