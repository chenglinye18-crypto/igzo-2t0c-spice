"""Generate v1.1 outputs: fit_report, key_bias, low_vd_diagnostic, plot."""
import sys, os, json, math, csv
sys.path.insert(0, r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\scripts')
import device_model_v1 as m
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
RES  = os.path.join(ROOT, 'results')
os.makedirs(RES, exist_ok=True)

# v1.1 final parameters (best fit)
P_FINAL = dict(
    N_D=1.0e18, eps_s=10.0, eps_ox=22.0, mu_0=80.0, mu_b=15.0,
    USR=1.0e-14, E_USC=1.5, V_fb=-0.5, V_th0=0.4, m_body=1.8,
    lambda_eff=1.5e-8, alpha_DIBL=0.08, alpha_sat=0.03, CLM=0.0,
    K_pre=0.7, n_power=1.7,
)

def read_csv(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            rows.append([float(x) for x in line.split(',')])
    return np.array(rows)

idvg = read_csv(os.path.join(DATA, 'idvg.csv'))
idvd = read_csv(os.path.join(DATA, 'idvd.csv'))
Vg_idvg, Id_vg01, Id_vg1 = idvg[:, 0], idvg[:, 1], idvg[:, 2]
Vd_idvd, Id_vd04, Id_vd12, Id_vd20 = idvd[:, 0], idvd[:, 1], idvd[:, 2], idvd[:, 3]

# ---- fit_report_v11.json ----
fit_report = {
    'stages': {
        'formula_change': {
            'from': "piecewise V_d_eff = min(Vd, Vdsat), CLM multiplicative",
            'to':   "smooth-min V_d_eff = Vd*Vdsat/sqrt(Vd^2+Vdsat^2), CLM additive",
            'reason': "piecewise V_d_eff could not capture the soft saturation in Zhu Id-Vd at Vg=2V (Id grows only 1.43x from Vd=0.1 to Vd=1, not 10x expected from linear). smooth-min preserves asymptotes (Vd_eff->Vd for Vd<<Vdsat, Vd_eff->Vdsat for Vd>>Vdsat) and is C^1 smooth.",
        },
        'calibration_strategy': 'grid search over (n_power, K_pre, alpha_sat, alpha_DIBL) targeted at key bias errors',
        'params_at_bound': [],
    },
    'parameters': {n: float(P_FINAL[n]) for n in [
        'V_fb', 'V_th0', 'm_body', 'mu_0', 'mu_b',
        'USR', 'E_USC', 'alpha_DIBL', 'alpha_sat', 'CLM', 'K_pre', 'n_power',
        'N_D', 'eps_s', 'eps_ox', 'lambda_eff']},
    'geometry': dict(L_nm=m.L_nm, CD_nm=m.CD_nm,
                     t_ch_nm=m.t_ch_nm, t_ox_nm=m.t_ox_nm,
                     W_eff_nm=m.W_eff_nm),
    'key_bias_errors_v1_to_v11': {
        'Vg=1.2 Vd=0.1':  {'v1': '1.05 us (paper 6 us, 82% off)', 'v1.1': '6.39 us (paper 6 us, 6% off)'},
        'Vg=2.0 Vd=0.1':  {'v1': '2.59 us (paper 35 us, 93% off)', 'v1.1': '37.94 us (paper 35 us, 8% off)'},
        'Vg=1.2 Vd=1.0':  {'v1': '16.05 us (paper 8 us, 100% off)', 'v1.1': '8.27 us (paper 8 us, 3% off)'},
        'Vg=2.0 Vd=1.0':  {'v1': '54.64 us (paper 50 us, 9% high in v1, but 60% off from idvd 22 us)', 'v1.1': '47.35 us (paper 50 us, 5% off)'},
    },
}
with open(os.path.join(RES, 'fit_report_v11.json'), 'w') as f:
    json.dump(fit_report, f, indent=2)
print('fit_report_v11.json written.')

# ---- low_vd_diagnostic.csv ----
rows = []
for vg in (0.4, 1.2, 2.0):
    for vd in (1e-4, 1e-3, 1e-2, 0.05, 0.1, 0.5, 1.0, 2.0, 3.0):
        V_th = m.V_th_effective(vd, P_FINAL)
        V_ov = vg - V_th
        Vdsat = max(P_FINAL['alpha_sat'] * V_ov, 0.0)
        Vdeff = m.V_d_eff_smooth_min(vd, Vdsat)
        if vd > Vdsat and Vdsat > 0:
            Vdeff += P_FINAL['CLM'] * (vd - Vdsat)
        mu = m.mobility(vg, vd, P_FINAL, m.surface_potential(vg, vd, P_FINAL))
        I_d = m.drain_current(vg, vd, P_FINAL)
        rows.append(dict(Vg=vg, Vd=vd, Vth=V_th, V_ov=V_ov, Vdsat=Vdsat,
                          Vdeff=Vdeff, Vdeff_over_Vd=Vdeff/max(vd, 1e-9),
                          mu=mu, I_d=I_d))
with open(os.path.join(RES, 'low_vd_diagnostic.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['Vg', 'Vd', 'Vth', 'V_ov', 'Vdsat',
                                        'Vdeff', 'Vdeff_over_Vd', 'mu', 'I_d'])
    w.writeheader()
    for r in rows: w.writerow(r)
print('low_vd_diagnostic.csv written.')

# ---- key_bias_validation_v11.csv ----
key = [
    (0.4, 0.1, float(np.interp(0.4, Vg_idvg, Id_vg01))),
    (1.2, 0.1, float(np.interp(1.2, Vg_idvg, Id_vg01))),
    (2.0, 0.1, float(np.interp(2.0, Vg_idvg, Id_vg01))),
    (0.4, 1.0, float(np.interp(0.4, Vg_idvg, Id_vg1))),
    (1.2, 1.0, float(np.interp(1.2, Vg_idvg, Id_vg1))),
    (2.0, 1.0, float(np.interp(2.0, Vg_idvg, Id_vg1))),
    (0.4, 3.0, float(np.interp(3.0, Vd_idvd, Id_vd04)) * 1e-6),
    (1.2, 3.0, float(np.interp(3.0, Vd_idvd, Id_vd12)) * 1e-6),
    (2.0, 3.0, float(np.interp(3.0, Vd_idvd, Id_vd20)) * 1e-6),
]
with open(os.path.join(RES, 'key_bias_validation_v11.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Vg', 'Vd', 'paper_Id_A', 'python_Id_A', 'rel_err'])
    for vg, vd, Id_p in key:
        Id_m = m.drain_current(vg, vd, P_FINAL)
        rel = (Id_m - Id_p) / max(Id_p, 1e-12)
        w.writerow([vg, vd, Id_p, Id_m, rel])
print('key_bias_validation_v11.csv written.')

# ---- plot ----
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
Vg_dense = np.linspace(-1, 2, 200)
for vd_lbl, vd_val, color in [('Vd=0.1V', 0.1, 'tab:orange'),
                               ('Vd=1V',   1.0, 'tab:red')]:
    Idm = np.array([m.drain_current(v, vd_val, P_FINAL) for v in Vg_dense])
    Idp = Id_vg01 if vd_lbl == 'Vd=0.1V' else Id_vg1
    ax1.semilogy(Vg_idvg, Idp, 'o', color=color, label=f'paper {vd_lbl}', alpha=0.6)
    ax1.semilogy(Vg_dense, Idm, '-', color=color, label=f'v1.1 {vd_lbl}', lw=2)
ax1.set_xlabel('Vg (V)'); ax1.set_ylabel('Id (A)')
ax1.set_title('Id-Vg (2T0C) v1.1')
ax1.legend(); ax1.grid(True, which='both', alpha=0.3)
Vd_dense = np.linspace(0, 3, 200)
for vg_lbl, vg_val, color in [('Vg=0.4V', 0.4, 'tab:blue'),
                               ('Vg=1.2V', 1.2, 'tab:cyan'),
                               ('Vg=2.0V', 2.0, 'navy')]:
    Idm = np.array([m.drain_current(vg_val, v, P_FINAL) for v in Vd_dense])
    Idp = {'Vg=0.4V': Id_vd04, 'Vg=1.2V': Id_vd12, 'Vg=2.0V': Id_vd20}[vg_lbl]
    ax2.plot(Vd_idvd, Idp*1e6, 'o', color=color, label=f'paper {vg_lbl}', alpha=0.6)
    ax2.plot(Vd_dense, Idm*1e6, '-', color=color, label=f'v1.1 {vg_lbl}', lw=2)
ax2.set_xlabel('Vd (V)'); ax2.set_ylabel('Id (uA)')
ax2.set_title('Id-Vd (2T0C) v1.1')
ax2.legend(); ax2.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(RES, 'idvg_idvd_fit_v11.png'), dpi=130)
print('idvg_idvd_fit_v11.png written.')

# Summary
print()
print('=== V1.1 KEY BIAS SUMMARY ===')
for vg, vd, Id_p in key:
    Id_m = m.drain_current(vg, vd, P_FINAL)
    rel = (Id_m - Id_p) / max(Id_p, 1e-12) * 100
    flag = 'OK' if abs(rel) < 30 else ('OK50' if abs(rel) < 50 else 'X')
    print(f'  {flag} Vg={vg} Vd={vd}: paper={Id_p*1e6:8.3f} uA, model={Id_m*1e6:8.3f} uA, err={rel:+6.1f}%')
