"""v1.1 calibration: small parameter refinement after V_d_eff formula change.

Strategy:
  * Geometry frozen (PAPER_REPORTED)
  * V_th0, V_fb, eps_s, eps_ox, N_D, mu_b, lambda_eff: FROZEN from v1
  * 3-4 params tuned: n_power, K_pre, alpha_sat, CLM, alpha_DIBL
  * Search: targeted grid + small joint refinement with scipy.least_squares
"""
import os
import sys
import json
import math
import numpy as np
import csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import device_model_v1 as m

DATA = os.path.join(ROOT, 'data')
RES  = os.path.join(ROOT, 'results')
os.makedirs(RES, exist_ok=True)

# Paper data
def read_csv(path, skip=3):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            rows.append([float(x) for x in parts])
    return np.array(rows)

idvg = read_csv(os.path.join(DATA, 'idvg.csv'))
idvd = read_csv(os.path.join(DATA, 'idvd.csv'))
Vg_idvg, Id_vg01, Id_vg1 = idvg[:, 0], idvg[:, 1], idvg[:, 2]
Vd_idvd, Id_vd04, Id_vd12, Id_vd20 = idvd[:, 0], idvd[:, 1], idvd[:, 2], idvd[:, 3]

# Frozen params from v1
FROZEN = dict(
    N_D=1.0e18, eps_s=10.0, eps_ox=22.0, mu_0=80.0, mu_b=15.0,
    USR=1.0e-14, E_USC=1.5, V_fb=-0.5, V_th0=0.4, m_body=1.8,
    lambda_eff=1.5e-8,
)

def loss(p, w_idvg_log=1.0, w_idvd_rel=1.0, w_cross=5.0):
    """Combined log-RMSE on Id-Vg + rel-RMSE on Id-Vd + cross-bias penalty."""
    r_idvg = []
    for vd in (0.1, 1.0):
        Id_paper = Id_vg01 if vd == 0.1 else Id_vg1
        for vg, Id_p in zip(Vg_idvg, Id_paper):
            Id_m = m.drain_current(float(vg), float(vd), p)
            if Id_p > 1e-12:
                r_idvg.append(w_idvg_log * (math.log10(max(Id_m, 1e-20)) - math.log10(Id_p)))
    r_idvd = []
    for vg, Id_p_vd in [(0.4, Id_vd04), (1.2, Id_vd12), (2.0, Id_vd20)]:
        for vd, Id_p in zip(Vd_idvd, Id_p_vd):
            Id_m = m.drain_current(vg, float(vd), p)
            denom = max(abs(Id_p), 0.5e-6)
            r_idvd.append(w_idvd_rel * (Id_m - Id_p) / denom)
    # cross-bias: at (Vg, Vd) in {(0.4, 1.0), (1.2, 1.0), (2.0, 1.0)}
    r_cross = []
    for vg in (0.4, 1.2, 2.0):
        vd = 1.0
        Id_m = m.drain_current(vg, vd, p)
        # paper: from idvg (Vd=1V column) at this Vg
        Id_p_idvg = float(np.interp(vg, Vg_idvg, Id_vg1))
        if Id_p_idvg > 1e-9:
            r_cross.append(w_cross * abs(Id_m - Id_p_idvg) / Id_p_idvg)
        # paper: from idvd (Vg=2 column) at this Vd
        if abs(vg - 2.0) < 0.01:
            Id_p_idvd = float(np.interp(vd, Vd_idvd, Id_vd20))
            if Id_p_idvd > 1e-9:
                r_cross.append(w_cross * 0.5 * abs(Id_m - Id_p_idvd) / Id_p_idvd)
    return np.array(r_idvg + r_idvd + r_cross)


def report(p, label):
    rmse_idvg = {0.1: 0.0, 1.0: 0.0}
    counts = {0.1: 0, 1.0: 0}
    for vd in (0.1, 1.0):
        Id_paper = Id_vg01 if vd == 0.1 else Id_vg1
        s = 0
        for vg, Id_p in zip(Vg_idvg, Id_paper):
            Id_m = m.drain_current(float(vg), float(vd), p)
            if Id_p > 1e-12:
                s += (math.log10(max(Id_m, 1e-20)) - math.log10(Id_p))**2
                counts[vd] += 1
        rmse_idvg[vd] = math.sqrt(s / max(counts[vd], 1))
    rmse_idvd = {0.4: 0.0, 1.2: 0.0, 2.0: 0.0}
    counts = {0.4: 0, 1.2: 0, 2.0: 0}
    for vg, Id_p_vd in [(0.4, Id_vd04), (1.2, Id_vd12), (2.0, Id_vd20)]:
        s = 0
        for vd, Id_p in zip(Vd_idvd, Id_p_vd):
            Id_m = m.drain_current(vg, float(vd), p)
            denom = max(abs(Id_p), 0.5e-6)
            s += ((Id_m - Id_p) / denom)**2
            counts[vg] += 1
        rmse_idvd[vg] = math.sqrt(s / max(counts[vg], 1))
    key = [
        (0.4, 1.0, float(np.interp(0.4, Vg_idvg, Id_vg1))),
        (1.2, 1.0, float(np.interp(1.2, Vg_idvg, Id_vg1))),
        (2.0, 1.0, float(np.interp(2.0, Vg_idvg, Id_vg1))),
        (0.4, 0.1, float(np.interp(0.4, Vg_idvg, Id_vg01))),
        (1.2, 0.1, float(np.interp(1.2, Vg_idvg, Id_vg01))),
        (2.0, 0.1, float(np.interp(2.0, Vg_idvg, Id_vg01))),
    ]
    print(f'\n[{label}]')
    print(f'  Id-Vg log-RMSE: Vd=0.1={rmse_idvg[0.1]:.3f}, Vd=1={rmse_idvg[1.0]:.3f}')
    print(f'  Id-Vd rel-RMSE: Vg=0.4={rmse_idvd[0.4]:.3f}, Vg=1.2={rmse_idvd[1.2]:.3f}, Vg=2.0={rmse_idvd[2.0]:.3f}')
    print(f'  Key bias:')
    for vg, vd, Id_p in key:
        Id_m = m.drain_current(vg, vd, p)
        err = (Id_m - Id_p) / max(Id_p, 1e-12) * 100
        print(f'    Vg={vg}, Vd={vd}: paper={Id_p*1e6:.2f} uA, model={Id_m*1e6:.2f} uA, err={err:+.1f}%')


def main():
    # Stage A: coarse search over n_power, K_pre, alpha_sat
    print('=== STAGE A: coarse grid over n_power, K_pre, alpha_sat ===')
    best = None
    best_cost = float('inf')
    best_p = None
    n_list = [2.0, 2.3, 2.5, 2.7, 3.0]
    K_list = [5e5, 1e6, 2e6, 4e6, 8e6, 1.6e7]
    a_list = [0.05, 0.1, 0.2, 0.3, 0.5]
    for n in n_list:
        for K in K_list:
            for a in a_list:
                p = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=0.0, alpha_DIBL=0.05)
                r = loss(p)
                c = float(np.sum(r**2))
                if c < best_cost:
                    best_cost = c; best = (n, K, a)
    n, K, a = best
    print(f'  best coarse: n={n}, K={K:.2e}, alpha_sat={a}, cost={best_cost:.3e}')

    # Stage B: refine CLM and alpha_DIBL around the coarse winner
    print('\n=== STAGE B: refine CLM and alpha_DIBL ===')
    p_base = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=0.0, alpha_DIBL=0.05)
    for clm in [0.0, 0.05, 0.1, 0.2, 0.4]:
        for dibl in [0.0, 0.02, 0.05, 0.1, 0.15]:
            p = dict(p_base, CLM=clm, alpha_DIBL=dibl)
            r = loss(p)
            c = float(np.sum(r**2))
            if c < best_cost:
                best_cost = c; best = (n, K, a, clm, dibl)
    n, K, a, clm, dibl = best[:5]
    p_best = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=clm, alpha_DIBL=dibl)
    report(p_best, f'STAGE B best: n={n}, K={K:.2e}, a_sat={a}, CLM={clm}, DIBL={dibl}')

    # Stage C: small joint refinement with bounds
    print('\n=== STAGE C: small joint refinement (scipy.least_squares) ===')
    from scipy.optimize import least_squares
    names = ['K_pre', 'n_power', 'alpha_sat', 'CLM', 'alpha_DIBL']
    lo = [K * 0.3, n - 0.5, a * 0.3, 0.0, 0.0]
    hi = [K * 3.0, n + 0.5, min(a * 3, 1.0), 0.5, 0.3]
    x0 = np.array([K, n, a, clm, dibl])
    def resid(x):
        p = dict(p_base, K_pre=x[0], n_power=x[1], alpha_sat=x[2], CLM=x[3], alpha_DIBL=x[4])
        return loss(p)
    res = least_squares(resid, x0, bounds=(lo, hi), max_nfev=2000, method='trf',
                       xtol=1e-7, ftol=1e-7)
    p_final = dict(p_base,
                   K_pre=float(res.x[0]), n_power=float(res.x[1]),
                   alpha_sat=float(res.x[2]), CLM=float(res.x[3]),
                   alpha_DIBL=float(res.x[4]))
    at_bound = [names[i] for i in range(5) if abs(res.x[i]-lo[i]) < 1e-6 or abs(res.x[i]-hi[i]) < 1e-6]
    report(p_final, f'JOINT best: cost={res.cost:.3e}, at_bound={at_bound if at_bound else "(none)"}')
    print(f'  final: K_pre={p_final["K_pre"]:.4e}, n_power={p_final["n_power"]:.4f}')
    print(f'         alpha_sat={p_final["alpha_sat"]:.4f}, CLM={p_final["CLM"]:.4f}, alpha_DIBL={p_final["alpha_DIBL"]:.4f}')

    # ---- Write outputs ----
    # fit_report_v11.json
    fit_report = {
        'stages': {
            'A_coarse': dict(n_power=best[0], K_pre=best[1], alpha_sat=best[2]),
            'B_refine': dict(CLM=best[3], alpha_DIBL=best[4]),
            'C_joint': dict(cost=float(res.cost),
                            residual_norm=float(np.linalg.norm(res.fun)),
                            params_at_bound=at_bound),
        },
        'parameters': {n: float(p_final[n]) for n in [
            'V_fb', 'V_th0', 'm_body', 'mu_0', 'mu_b',
            'USR', 'E_USC', 'alpha_DIBL', 'alpha_sat', 'CLM', 'K_pre', 'n_power',
            'N_D', 'eps_s', 'eps_ox', 'lambda_eff']},
        'geometry': dict(L_nm=m.L_nm, CD_nm=m.CD_nm,
                         t_ch_nm=m.t_ch_nm, t_ox_nm=m.t_ox_nm,
                         W_eff_nm=m.W_eff_nm),
        'equation_change_v1_to_v11': {
            'Vd_eff': 'piecewise min(Vd, Vdsat) -> smooth-min Vd*Vdsat/sqrt(Vd^2+Vdsat^2)',
            'CLM_application': 'multiplicative on V_d_eff -> additive linear beyond Vdsat',
            'reason': 'piecewise Vd_eff could not capture the soft saturation observed in Zhu Id-Vd at Vg=2V (Id grows only 1.43x from Vd=0.1 to Vd=1, not 10x expected from linear). The smooth-min preserves the correct asymptotes (Vd_eff -> Vd for Vd<<Vdsat, Vd_eff -> Vdsat for Vd>>Vdsat) and is C^1 smooth.',
        },
    }
    with open(os.path.join(RES, 'fit_report_v11.json'), 'w') as f:
        json.dump(fit_report, f, indent=2)
    print('\nfit_report_v11.json written.')

    # low_vd_diagnostic.csv
    rows = []
    for vg in (0.4, 1.2, 2.0):
        for vd in (1e-4, 1e-3, 1e-2, 0.05, 0.1, 0.5, 1.0, 2.0, 3.0):
            V_th = m.V_th_effective(vd, p_final)
            V_ov = vg - V_th
            psi = m.surface_potential(vg, vd, p_final)
            mu = m.mobility(vg, vd, p_final, psi)
            Vdsat = max(p_final['alpha_sat'] * V_ov, 0.0)
            Vdeff = m.V_d_eff_smooth_min(vd, Vdsat)
            if vd > Vdsat and Vdsat > 0:
                Vdeff += p_final['CLM'] * (vd - Vdsat)
            I_d = m.drain_current(vg, vd, p_final)
            I_on = (p_final['K_pre'] * (m.W_eff/m.L) * mu * (m.eps0*m.eps_ox_r_unused if False else m.EPS0*p_final['eps_ox']/m.t_ox)
                    * (V_ov**p_final['n_power']) * Vdeff) if V_ov > 0 else 0.0
            rows.append(dict(Vg=vg, Vd=vd, Vth=V_th, V_ov=V_ov, Vdsat=Vdsat,
                              Vdeff=Vdeff, Vdeff_over_Vd=Vdeff/max(vd, 1e-9),
                              mu=mu, I_on=I_on, I_d=I_d))
    with open(os.path.join(RES, 'low_vd_diagnostic.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['Vg', 'Vd', 'Vth', 'V_ov', 'Vdsat',
                                            'Vdeff', 'Vdeff_over_Vd', 'mu', 'I_on', 'I_d'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('low_vd_diagnostic.csv written.')

    # key_bias_validation_v11.csv
    key = [
        (0.4, 0.1, float(np.interp(0.4, Vg_idvg, Id_vg01))),
        (1.2, 0.1, float(np.interp(1.2, Vg_idvg, Id_vg01))),
        (2.0, 0.1, float(np.interp(2.0, Vg_idvg, Id_vg01))),
        (0.4, 1.0, float(np.interp(0.4, Vg_idvg, Id_vg1))),
        (1.2, 1.0, float(np.interp(1.2, Vg_idvg, Id_vg1))),
        (2.0, 1.0, float(np.interp(2.0, Vg_idvg, Id_vg1))),
        (0.4, 3.0, float(np.interp(0.4, Vd_idvd, Id_vd04))),
        (1.2, 3.0, float(np.interp(1.2, Vd_idvd, Id_vd12))),
        (2.0, 3.0, float(np.interp(2.0, Vd_idvd, Id_vd20))),
    ]
    with open(os.path.join(RES, 'key_bias_validation_v11.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Vg', 'Vd', 'paper_Id_A', 'python_Id_A', 'rel_err'])
        for vg, vd, Id_p in key:
            Id_m = m.drain_current(vg, vd, p_final)
            rel = (Id_m - Id_p) / max(Id_p, 1e-12)
            w.writerow([vg, vd, Id_p, Id_m, rel])
    print('key_bias_validation_v11.csv written.')

    # plot
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        Vg_dense = np.linspace(-1, 2, 200)
        for vd_lbl, vd_val, color in [('Vd=0.1V', 0.1, 'tab:orange'),
                                       ('Vd=1V',   1.0, 'tab:red')]:
            Idm = np.array([m.drain_current(v, vd_val, p_final) for v in Vg_dense])
            Idp = Id_vg01 if vd_lbl == 'Vd=0.1V' else Id_vg1
            ax1.semilogy(Vg_idvg, Idp, 'o', color=color, label=f'paper {vd_lbl}', alpha=0.6)
            ax1.semilogy(Vg_dense, Idm, '-', color=color, label=f'v1.1 {vd_lbl}', lw=2)
        ax1.set_xlabel('Vg (V)'); ax1.set_ylabel('Id (A)')
        ax1.set_title('Id-Vg (2T0C) v1.1'); ax1.legend(); ax1.grid(True, which='both', alpha=0.3)
        Vd_dense = np.linspace(0, 3, 200)
        for vg_lbl, vg_val, color in [('Vg=0.4V', 0.4, 'tab:blue'),
                                       ('Vg=1.2V', 1.2, 'tab:cyan'),
                                       ('Vg=2.0V', 2.0, 'navy')]:
            Idm = np.array([m.drain_current(vg_val, v, p_final) for v in Vd_dense])
            Idp = {'Vg=0.4V': Id_vd04, 'Vg=1.2V': Id_vd12, 'Vg=2.0V': Id_vd20}[vg_lbl]
            ax2.plot(Vd_idvd, Idp*1e6, 'o', color=color, label=f'paper {vg_lbl}', alpha=0.6)
            ax2.plot(Vd_dense, Idm*1e6, '-', color=color, label=f'v1.1 {vg_lbl}', lw=2)
        ax2.set_xlabel('Vd (V)'); ax2.set_ylabel('Id (uA)')
        ax2.set_title('Id-Vd (2T0C) v1.1'); ax2.legend(); ax2.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(RES, 'idvg_idvd_fit_v11.png'), dpi=130)
        print('idvg_idvd_fit_v11.png written.')
    except Exception as e:
        print('plot failed:', e)

    return p_final


if __name__ == '__main__':
    main()
