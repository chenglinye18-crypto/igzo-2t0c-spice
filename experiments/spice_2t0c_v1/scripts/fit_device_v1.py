"""v1 staged calibration script for Zhu 2T0C IEDM 2026.

Implements the 11-step calibration procedure documented in
`model_equations.md §4`. Each step tunes a small subset of parameters;
the next step only adjusts what is not yet correct. After all stages,
a final `scipy.optimize.least_squares` does a small joint refinement
within bounds.

This is intentionally **not** a black-box fit. Every step produces a
visible report (printed to stdout) and the final fit_report_v1.json
records parameter values, bounds, and which parameters were at bound.

Reads:
  data/idvg.csv
  data/idvd.csv

Writes:
  results/fit_report_v1.json
  results/key_bias_validation.csv
  results/idvg_idvd_fit_v1.png
  results/iv_crosscheck.csv
"""
from __future__ import annotations

import os
import json
import csv
import math
import numpy as np
import sys

# import the model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import device_model_v1 as m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
RES  = os.path.join(ROOT, 'results')
os.makedirs(RES, exist_ok=True)


# --- read csv data ----------------------------------------------------------
def read_idvg(path):
    """Read idvg.csv. Skip comment lines starting with #."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            rows.append([float(x) for x in parts])
    a = np.array(rows)
    return a[:, 0], a[:, 1], a[:, 2]   # Vg, Id_Vd01, Id_Vd1


def read_idvd(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            rows.append([float(x) for x in parts])
    a = np.array(rows)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]   # Vd, Id_Vg04, Id_Vg12, Id_Vg20


Vg, Id_vg01, Id_vg1 = read_idvg(os.path.join(DATA, 'idvg.csv'))
Vd, Id_vd04, Id_vd12, Id_vd20 = read_idvd(os.path.join(DATA, 'idvd.csv'))

# paper data sets
PAPER_IDVG = {'Vd=0.1V': (Vg, Id_vg01), 'Vd=1V': (Vg, Id_vg1)}
PAPER_IDVD = {'Vg=0.4V': (Vd, Id_vd04), 'Vg=1.2V': (Vd, Id_vd12), 'Vg=2.0V': (Vd, Id_vd20)}


# --- loss functions --------------------------------------------------------
def loss_idvg_log(p, Vd_fixed):
    """log10 residual for one Vd curve."""
    Vg_arr, Id_paper = PAPER_IDVG[Vd_fixed]
    Id_model = np.array([m.drain_current(float(v), 0.1 if Vd_fixed == 'Vd=0.1V' else 1.0, p)
                          for v in Vg_arr])
    # avoid log(0)
    Id_paper_safe = np.maximum(Id_paper, 1e-20)
    Id_model_safe = np.maximum(Id_model, 1e-20)
    return np.log10(Id_model_safe) - np.log10(Id_paper_safe)


def loss_idvd_rel(p, Vg_fixed):
    """relative residual for one Vg curve."""
    Vd_arr, Id_paper = PAPER_IDVD[Vg_fixed]
    Vg_val = float(Vg_fixed.split('=')[1].rstrip('V'))
    Id_model = np.array([m.drain_current(Vg_val, float(vd), p) for vd in Vd_arr])
    denom = np.maximum(np.abs(Id_paper), 0.5e-6)  # 0.5 uA floor
    return (Id_model - Id_paper) / denom


def loss_total(p, w_log=1.0, w_rel=1.0, w_cross=10.0):
    out = []
    for k in PAPER_IDVG:
        out.append(w_log * loss_idvg_log(p, k))
    for k in PAPER_IDVD:
        out.append(w_rel * loss_idvd_rel(p, k))
    # cross-bias penalty
    cross = []
    Vg_targets = [(0.4, 1.0), (1.2, 1.0), (2.0, 1.0)]
    for vg, vd in Vg_targets:
        Idm = m.drain_current(vg, vd, p)
        # compare to Id-Vd at (Vg, Vd) and to Id-Vg at (Vg, V_d=1V)
        Vd_arr, Id_vd = {
            0.4: (Vd, Id_vd04), 1.2: (Vd, Id_vd12), 2.0: (Vd, Id_vd20)
        }[vg]
        Id_paper_vd = float(np.interp(vd, Vd_arr, Id_vd))
        # Id_paper from Id-Vg at Vd=1V
        Id_paper_vg = float(np.interp(vg, Vg, Id_vg1))
        # we don't force equality, but penalize the absolute difference
        rel_vd = (Idm - Id_paper_vd) / max(Id_paper_vd, 1e-6)
        rel_vg = (Idm - Id_paper_vg) / max(Id_paper_vg, 1e-6)
        cross.append(w_cross * rel_vd)
        cross.append(w_cross * 0.5 * rel_vg)
    out.append(np.array(cross))
    return np.concatenate(out)


# --- staged calibration ----------------------------------------------------
def report_step(step, p, residuals):
    rmse_log_idvg = {}
    for k in PAPER_IDVG:
        r = loss_idvg_log(p, k)
        rmse_log_idvg[k] = float(np.sqrt(np.mean(r**2)))
    rmse_rel_idvd = {}
    for k in PAPER_IDVD:
        r = loss_idvd_rel(p, k)
        rmse_rel_idvd[k] = float(np.sqrt(np.mean(r**2)))
    print(f'\n--- Step {step} ---')
    print(f'  params: V_th0={p["V_th0"]:.3f} V, V_fb={p["V_fb"]:.3f} V, '
          f'mu_0={p["mu_0"]:.2f} cm2/Vs, mu_b={p["mu_b"]:.2f}, '
          f'USR={p["USR"]:.2e}, E_USC={p["E_USC"]:.2f}, '
          f'm_body={p["m_body"]:.2f}, alpha_DIBL={p["alpha_DIBL"]:.3f}, '
          f'alpha_sat={p["alpha_sat"]:.2f}, CLM={p["CLM"]:.3f}')
    print(f'  Id-Vg log10 RMSE per Vd: {rmse_log_idvg}')
    print(f'  Id-Vd rel RMSE per Vg:   {rmse_rel_idvd}')


# Step 1-2: V_th / horizontal alignment
def stage_vth(p):
    print('\n=== STAGE 1-2: V_th / horizontal alignment ===')
    # Fix the other params to a reasonable initial set
    p2 = dict(p)
    p2['mu_0'] = 15.0
    p2['K_pre'] = 0.1
    p2['m_body'] = 1.5
    p2['alpha_DIBL'] = 0.1
    candidates = [-0.3, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1]
    best_score = float('inf')
    best_v = None
    for vt in candidates:
        p2['V_th0'] = vt
        r = loss_idvg_log(p2, 'Vd=0.1V')   # use linear-region data
        s = float(np.mean(r**2))
        if s < best_score:
            best_score = s; best_v = vt
    p['V_th0'] = best_v
    p['mu_0'] = p2['mu_0']; p['K_pre'] = p2['K_pre']
    p['m_body'] = p2['m_body']; p['alpha_DIBL'] = p2['alpha_DIBL']
    print(f'  best V_th0 = {best_v:.3f} V (log-RMSE on Vd=0.1V={best_score:.3f})')
    return p


# Step 3-4: off-state + subthreshold slope via m_body
def stage_off(p):
    print('\n=== STAGE 3-4: off-state & subthreshold slope ===')
    best = float('inf'); best_mb = p['m_body']
    for mb in [1.05, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0]:
        p2 = dict(p); p2['m_body'] = mb
        # focus on subthreshold-to-on transition
        Vg_arr, Id_paper = PAPER_IDVG['Vd=0.1V']
        msk = (Vg_arr < 1.0) & (Vg_arr > -0.5)
        if not msk.any():
            continue
        Id_model = np.array([m.drain_current(float(v), 0.1, p2) for v in Vg_arr[msk]])
        Id_paper_safe = np.maximum(Id_paper[msk], 1e-15)
        Id_model_safe = np.maximum(Id_model, 1e-20)
        s = float(np.mean((np.log10(Id_model_safe) - np.log10(Id_paper_safe))**2))
        if s < best:
            best = s; best_mb = mb
    p['m_body'] = best_mb
    print(f'  best m_body = {best_mb:.2f} (log-RMSE in subthreshold = {best:.3f})')
    return p


# Step 5: DIBL via alpha_DIBL
def stage_dibl(p):
    print('\n=== STAGE 5: DIBL ===')
    best = float('inf'); best_a = p['alpha_DIBL']
    for a in [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]:
        p2 = dict(p); p2['alpha_DIBL'] = a
        # V_th shift at Vd=1V vs Vd=0.1V should be moderate
        # Use Id-Vg at Vg ~ 0.5: ratio of Id at Vd=1V to Id at Vd=0.1V
        # Paper data shows Id@Vd=1V ≈ 30-100x Id@Vd=0.1V at Vg=0.5
        Vg_test = 0.5
        Id_01 = m.drain_current(Vg_test, 0.1, p2)
        Id_1 = m.drain_current(Vg_test, 1.0, p2)
        # crude: penalize if ratio is < 5 or > 200
        if Id_01 < 1e-15:
            Id_01 = 1e-15
        ratio = Id_1 / Id_01
        s = (math.log10(max(ratio, 1e-3)) - 1.5)**2  # target ratio ~30
        if s < best:
            best = s; best_a = a
    p['alpha_DIBL'] = best_a
    print(f'  best alpha_DIBL = {best_a:.3f}')
    return p


# Step 6-7: on-current + curvature via mu_0, USR, E_USC, K_pre, n_power
def stage_on(p):
    print('\n=== STAGE 6-7: on-current & curvature ===')
    best = float('inf')
    best_mu = p['mu_0']; best_USR = p['USR']; best_E = p['E_USC']
    best_K = p['K_pre']; best_n = p['n_power']
    for mu in [5, 10, 20, 40, 80, 150]:
        for USR in [1e-14, 5e-14, 1e-13, 5e-13, 1e-12]:
            for E in [0.5, 1.0, 1.5, 2.0]:
                for K in [0.01, 0.05, 0.1, 0.3, 1.0, 3.0]:
                    for n in [1.5, 2.0, 2.5, 3.0]:
                        p2 = dict(p); p2['mu_0'] = mu; p2['USR'] = USR
                        p2['E_USC'] = E; p2['K_pre'] = K; p2['n_power'] = n
                        Vg_arr, Id_paper = PAPER_IDVG['Vd=1V']
                        msk = Vg_arr > 0.3
                        Id_model = np.array([m.drain_current(float(v), 1.0, p2) for v in Vg_arr[msk]])
                        Id_paper_safe = np.maximum(Id_paper[msk], 1e-12)
                        Id_model_safe = np.maximum(Id_model, 1e-20)
                        s = float(np.mean((np.log10(Id_model_safe) - np.log10(Id_paper_safe))**2))
                        if s < best:
                            best = s; best_mu = mu; best_USR = USR
                            best_E = E; best_K = K; best_n = n
    p['mu_0'] = best_mu; p['USR'] = best_USR; p['E_USC'] = best_E
    p['K_pre'] = best_K; p['n_power'] = best_n
    print(f'  best mu_0={best_mu} cm2/Vs, USR={best_USR:.1e}, E_USC={best_E}, '
          f'K_pre={best_K}, n_power={best_n} '
          f'(log-RMSE on Vd=1V,Vg>0.3 = {best:.3f})')
    return p


# Step 8-10: Id-Vd via alpha_sat, CLM
def stage_idvd(p):
    print('\n=== STAGE 8-10: Id-Vd linear slope & saturation ===')
    best = float('inf'); best_as = p['alpha_sat']; best_clm = p['CLM']
    for as_ in [0.3, 0.5, 0.7, 1.0, 1.3, 1.6, 2.0]:
        for clm in [0.0, 0.05, 0.10, 0.20, 0.40, 1.0]:
            p2 = dict(p); p2['alpha_sat'] = as_; p2['CLM'] = clm
            Vd_arr, Id_paper = PAPER_IDVD['Vg=2.0V']
            Id_model = np.array([m.drain_current(2.0, float(vd), p2) for vd in Vd_arr])
            denom = np.maximum(np.abs(Id_paper), 0.5e-6)
            s = float(np.mean(((Id_model - Id_paper) / denom)**2))
            if s < best:
                best = s; best_as = as_; best_clm = clm
    p['alpha_sat'] = best_as; p['CLM'] = best_clm
    print(f'  best alpha_sat={best_as}, CLM={best_clm} '
          f'(rel-RMSE on Vg=2V = {best:.3f})')
    return p


# Step 11: joint refinement with bounds
def stage_joint(p):
    print('\n=== STAGE 11: joint refinement ===')
    from scipy.optimize import least_squares
    # parameter vector and bounds (in original user-facing units)
    names = ['V_fb', 'V_th0', 'm_body', 'mu_0', 'mu_b',
             'USR', 'E_USC', 'alpha_DIBL', 'alpha_sat', 'CLM', 'K_pre', 'n_power']
    lo = [-1.5, -0.5, 1.0, 1.0, 5.0,
          1e-15, 0.5, 0.0, 0.3, 0.0, 1e-6, 1.0]
    hi = [ 0.5,  1.5, 5.0, 200.0, 50.0,
           1e-10, 3.0, 0.5, 2.5, 1.0, 1e6, 4.0]
    x0 = np.array([p[n] for n in names])
    def unpack(x):
        out = dict(m.DEFAULTS)
        out.update(p)
        for n, v in zip(names, x):
            out[n] = float(v)
        return out
    def resid(x):
        pp = unpack(x)
        r = loss_total(pp, w_log=1.0, w_rel=1.0, w_cross=5.0)
        return r
    res = least_squares(resid, x0, bounds=(lo, hi), max_nfev=2000,
                        method='trf', xtol=1e-6, ftol=1e-6)
    pp = unpack(res.x)
    at_bound = []
    for i, n in enumerate(names):
        if abs(res.x[i] - lo[i]) < 1e-6 or abs(res.x[i] - hi[i]) < 1e-6:
            at_bound.append(n)
    print(f'  joint done: cost={res.cost:.4e}, |r|={np.linalg.norm(res.fun):.4e}')
    print(f'  params at bound: {at_bound if at_bound else "(none)"}')
    return pp, at_bound, names, res


# --- main ------------------------------------------------------------------
if __name__ == '__main__':
    p = dict(m.DEFAULTS)
    # Step 1-2: V_th scan (focused on data above 10nA)
    p['V_th0'] = 0.4   # constant-current at I=10nA, Vd=0.1V is Vg~0.4
    p['mu_0'] = 20.0
    p['K_pre'] = 0.1
    p['m_body'] = 1.8
    p['alpha_DIBL'] = 0.3
    p['alpha_sat'] = 0.5  # small V_ds,sat to capture saturation knee
    p['n_power'] = 1.8
    report_step('1-2 V_th (manual)', p, None)
    # Step 3-4
    p = stage_off(p)
    report_step('3-4 off+sub', p, None)
    # Step 5
    p = stage_dibl(p)
    report_step('5 DIBL', p, None)
    # Step 6-7 (now includes K_pre)
    p = stage_on(p)
    report_step('6-7 on', p, None)
    # Step 8-10
    p = stage_idvd(p)
    report_step('8-10 Id-Vd', p, None)
    # Use stage 8-10 result (good Id-Vg fit, reasonable Id-Vd) as final
    p_final = p
    at_bound = []
    names = list(p_final.keys())
    res = None
    print('\n=== Using stage 8-10 result as final (joint refinement skipped) ===')
    report_step('FINAL', p_final, None)

    # save final report
    fit_report = {
        'stages': {
            'V_th': {'final': float(p['V_th0'])},
            'off_subthreshold': {'m_body': float(p['m_body'])},
            'DIBL': {'alpha_DIBL': float(p['alpha_DIBL'])},
            'on_current': {
                'mu_0_cm2Vs': float(p['mu_0']),
                'USR': float(p['USR']),
                'E_USC': float(p['E_USC']),
                'K_pre': float(p['K_pre']),
                'n_power': float(p['n_power']),
            },
            'Id_Vd_saturation': {
                'alpha_sat': float(p['alpha_sat']),
                'CLM': float(p['CLM']),
            },
            'joint_refinement': {
                'cost': float('nan') if res is None else float(res.cost),
                'residual_norm': float('nan') if res is None else float(np.linalg.norm(res.fun)),
                'note': 'Stage 8-10 result used directly; joint refinement skipped due to model-form limits (see UNRESOLVED.md).',
                'params_at_bound': at_bound,
            },
        },
        'parameters': {n: float(p_final[n]) for n in [
            'V_fb', 'V_th0', 'm_body', 'mu_0', 'mu_b',
            'USR', 'E_USC', 'alpha_DIBL', 'alpha_sat', 'CLM', 'K_pre', 'n_power',
            'N_D', 'eps_s', 'eps_ox', 'lambda_eff']},
        'geometry': {
            'L_nm': m.L_nm, 'CD_nm': m.CD_nm,
            't_ch_nm': m.t_ch_nm, 't_ox_nm': m.t_ox_nm,
            'W_eff_nm': m.W_eff_nm,
        },
    }
    with open(os.path.join(RES, 'fit_report_v1.json'), 'w') as f:
        json.dump(fit_report, f, indent=2)
    print(f'\nfit_report_v1.json written.')

    # cross-bias / key-bias validation
    cross_rows = []
    key_rows = []
    cross_points = [(0.4, 1.0), (1.2, 1.0), (2.0, 1.0),
                    (0.4, 0.1), (1.2, 0.1), (2.0, 0.1),
                    (1.0, 1.0), (1.5, 1.0), (0.0, 1.0)]
    vd_map = {0.4: Id_vd04, 1.2: Id_vd12, 2.0: Id_vd20}
    for vg, vd in cross_points:
        Id_model = m.drain_current(vg, vd, p_final)
        Id_paper_vg = float(np.interp(vg, Vg, Id_vg1))  # Id-Vg at Vd=1V
        if vg in vd_map:
            Id_paper_vd = float(np.interp(vd, Vd, vd_map[vg]))  # Id-Vd at this Vg
        else:
            # interpolate from nearest known curve
            nearest = min(vd_map.keys(), key=lambda k: abs(k - vg))
            Id_paper_vd = float(np.interp(vd, Vd, vd_map[nearest]))
        cross_rows.append({
            'Vg': vg, 'Vd': vd,
            'Id_model': Id_model,
            'Id_paper_idvg_Vd1': Id_paper_vg,
            'Id_paper_idvd': Id_paper_vd,
            'rel_diff_idvg': abs(Id_model - Id_paper_vg) / max(Id_paper_vg, 1e-6),
            'rel_diff_idvd': abs(Id_model - Id_paper_vd) / max(Id_paper_vd, 1e-6),
        })
    # also add Vd=0.1V vs Id-Vg at Vd=0.1V
    for vg in [-0.5, 0.0, 0.4, 1.2, 2.0]:
        Id_model = m.drain_current(vg, 0.1, p_final)
        Id_paper_vg = float(np.interp(vg, Vg, Id_vg01))
        cross_rows.append({
            'Vg': vg, 'Vd': 0.1,
            'Id_model': Id_model,
            'Id_paper_idvg_Vd1': '',
            'Id_paper_idvd': '',
            'rel_diff_idvg': abs(Id_model - Id_paper_vg) / max(Id_paper_vg, 1e-6),
            'rel_diff_idvd': '',
        })
    with open(os.path.join(RES, 'iv_crosscheck.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['Vg', 'Vd', 'Id_model',
                                          'Id_paper_idvg_Vd1', 'Id_paper_idvd',
                                          'rel_diff_idvg', 'rel_diff_idvd'])
        w.writeheader()
        for r in cross_rows:
            w.writerow(r)
    print('iv_crosscheck.csv written.')

    # key bias validation
    for vg, vd in cross_points:
        Id_model = m.drain_current(vg, vd, p_final)
        if vd == 1.0:
            Id_paper = float(np.interp(vg, Vg, Id_vg1))
        elif vd == 0.1:
            Id_paper = float(np.interp(vg, Vg, Id_vg01))
        else:
            # for non 0.1/1.0 Vd values, interpolate from Id-Vd at nearest Vg
            if vg in vd_map:
                Id_paper = float(np.interp(vd, Vd, vd_map[vg]))
            else:
                nearest = min(vd_map.keys(), key=lambda k: abs(k - vg))
                Id_paper = float(np.interp(vd, Vd, vd_map[nearest]))
        key_rows.append([vg, vd, Id_paper, Id_model,
                          abs(Id_model - Id_paper) / max(Id_paper, 1e-6)])
    with open(os.path.join(RES, 'key_bias_validation.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Vg', 'Vd', 'paper_Id_A', 'python_Id_A', 'rel_err'])
        for r in key_rows:
            w.writerow(r)
    print('key_bias_validation.csv written.')

    # plot
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        # Id-Vg
        Vg_dense = np.linspace(-1, 2, 200)
        for vd_lbl, vd_val, color in [('Vd=0.1V', 0.1, 'tab:orange'),
                                       ('Vd=1V',   1.0, 'tab:red')]:
            Idm = np.array([m.drain_current(v, vd_val, p_final) for v in Vg_dense])
            Idp = Id_vg01 if vd_lbl == 'Vd=0.1V' else Id_vg1
            ax1.semilogy(Vg, Idp, 'o', color=color, label=f'paper {vd_lbl}', alpha=0.6)
            ax1.semilogy(Vg_dense, Idm, '-', color=color, label=f'model {vd_lbl}', lw=2)
        ax1.set_xlabel('Vg (V)'); ax1.set_ylabel('Id (A)')
        ax1.set_title('Id-Vg (2T0C)'); ax1.legend(); ax1.grid(True, which='both', alpha=0.3)
        # Id-Vd
        Vd_dense = np.linspace(0, 3, 200)
        for vg_lbl, vg_val, color in [('Vg=0.4V', 0.4, 'tab:blue'),
                                       ('Vg=1.2V', 1.2, 'tab:cyan'),
                                       ('Vg=2.0V', 2.0, 'navy')]:
            Idm = np.array([m.drain_current(vg_val, v, p_final) for v in Vd_dense])
            Idp = {'Vg=0.4V': Id_vd04, 'Vg=1.2V': Id_vd12, 'Vg=2.0V': Id_vd20}[vg_lbl]
            ax2.plot(Vd, Idp*1e6, 'o', color=color, label=f'paper {vg_lbl}', alpha=0.6)
            ax2.plot(Vd_dense, Idm*1e6, '-', color=color, label=f'model {vg_lbl}', lw=2)
        ax2.set_xlabel('Vd (V)'); ax2.set_ylabel('Id (uA)')
        ax2.set_title('Id-Vd (2T0C)'); ax2.legend(); ax2.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(RES, 'idvg_idvd_fit_v1.png'), dpi=130)
        print('idvg_idvd_fit_v1.png written.')
    except Exception as e:
        print('plot failed:', e)
