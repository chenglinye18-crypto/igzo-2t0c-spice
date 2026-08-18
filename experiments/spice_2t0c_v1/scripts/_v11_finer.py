"""Finer grid + CLM/alpha_sat variants around the best v1.1 fit."""
import sys, os, math
sys.path.insert(0, r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\scripts')
import device_model_v1 as m

FROZEN = dict(
    N_D=1.0e18, eps_s=10.0, eps_ox=22.0, mu_0=80.0, mu_b=15.0,
    USR=1.0e-14, E_USC=1.5, V_fb=-0.5, V_th0=0.4, m_body=1.8,
    lambda_eff=1.5e-8,
)

TARGETS = [
    (0.4, 0.1, 1e-8),
    (1.2, 0.1, 6e-6),
    (2.0, 0.1, 35e-6),
    (0.4, 1.0, 2.3e-6),
    (1.2, 1.0, 8e-6),
    (2.0, 1.0, 50e-6),
]

best = None
best_score = float('inf')
candidates = []

# Around the best from grid: n=1.5, K=0.3, alpha_sat=0.05, DIBL=0.05
# Try CLM (additive) and slightly different alpha_sat
n_list = [1.3, 1.5, 1.7]
K_list = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
a_list = [0.02, 0.03, 0.05, 0.07, 0.1, 0.15]
d_list = [0.0, 0.03, 0.05, 0.08, 0.1]
clm_list = [0.0, 0.05, 0.1, 0.2]

for n in n_list:
    for K in K_list:
        for a in a_list:
            for d in d_list:
                for clm in clm_list:
                    p = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=clm, alpha_DIBL=d)
                    errs = []
                    for vg, vd, Id_t in TARGETS:
                        if vg < 0.5: continue
                        Id_m = m.drain_current(vg, vd, p)
                        if Id_t > 0:
                            errs.append(abs(Id_m - Id_t) / Id_t)
                    if not errs: continue
                    log_err = math.log10(max(max(errs), 1e-3))
                    if log_err < best_score:
                        best_score = log_err
                        best = (n, K, a, d, clm, max(errs))
                    candidates.append((log_err, max(errs), n, K, a, d, clm))

candidates.sort()
print('Top 15:')
for c in candidates[:15]:
    log_err, max_err, n, K, a, d, clm = c
    p = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=clm, alpha_DIBL=d)
    print(f'  log={log_err:.2f} max={max_err:.2f}  n={n} K={K} a_sat={a} DIBL={d} CLM={clm}')
    for vg, vd, Id_t in TARGETS:
        if vg < 0.5: continue
        Id_m = m.drain_current(vg, vd, p)
        rel = (Id_m - Id_t) / Id_t * 100
        print(f'    Vg={vg} Vd={vd}: paper={Id_t*1e6:.2f} model={Id_m*1e6:.2f} err={rel:+.1f}%')
