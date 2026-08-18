"""v1.1 grid search focused on key bias errors < 50%."""
import sys, os, math
sys.path.insert(0, r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\scripts')
import device_model_v1 as m

FROZEN = dict(
    N_D=1.0e18, eps_s=10.0, eps_ox=22.0, mu_0=80.0, mu_b=15.0,
    USR=1.0e-14, E_USC=1.5, V_fb=-0.5, V_th0=0.4, m_body=1.8,
    lambda_eff=1.5e-8,
)

# Key bias targets (using idvg.csv for the Id-Vg side)
TARGETS = [
    (0.4, 0.1, 1e-8),
    (1.2, 0.1, 6e-6),
    (2.0, 0.1, 35e-6),
    (0.4, 1.0, 2.3e-6),
    (1.2, 1.0, 8e-6),
    (2.0, 1.0, 50e-6),   # idvg says 50
    (2.0, 1.0, 22e-6),   # idvd says 22 (alternative target)
]

# We need to match Vg=2 Vd=0.1 (=35) and Vd=1 (=50) simultaneously.
# The data Id(0.1)/Id(1) = 0.7. The smooth-min V_d_eff has ratio:
#   V_d_eff(0.1)/V_d_eff(1) = 0.1·Vdsat/sqrt(0.01+Vdsat²) / (Vdsat/sqrt(1+Vdsat²))
#                            = 0.1·sqrt(1+Vdsat²)/sqrt(0.01+Vdsat²)
# For Vdsat = alpha_sat * V_ov, with V_ov=1.5 (at Vd=0) and DIBL
# Let me just do a 4-D grid.

best = None
best_score = float('inf')
candidates = []
n_list = [1.0, 1.2, 1.5, 1.8, 2.0, 2.3]
K_list = [0.001, 0.003, 0.005, 0.01, 0.02, 0.05, 0.1, 0.3, 1.0]
a_list = [0.05, 0.1, 0.2, 0.3, 0.5]
d_list = [0.0, 0.02, 0.05, 0.1, 0.15]

for n in n_list:
    for K in K_list:
        for a in a_list:
            for d in d_list:
                p = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=0.0, alpha_DIBL=d)
                # max rel err across the on-state key biases
                errs = []
                for vg, vd, Id_t in TARGETS:
                    if vg < 0.5:  # skip off-state
                        continue
                    Id_m = m.drain_current(vg, vd, p)
                    if Id_t > 0:
                        rel = abs(Id_m - Id_t) / Id_t
                        errs.append(rel)
                if not errs:
                    continue
                # log-mean error
                log_err = math.log10(max(max(errs), 1e-3))
                if log_err < best_score:
                    best_score = log_err
                    best = (n, K, a, d, max(errs))
                # also store top-5
                candidates.append((log_err, max(errs), n, K, a, d))
                if len(candidates) > 50:
                    candidates.sort()
                    candidates = candidates[:50]

candidates.sort()
print('Top 10 parameter sets:')
for c in candidates[:10]:
    log_err, max_err, n, K, a, d = c
    p = dict(FROZEN, n_power=n, K_pre=K, alpha_sat=a, CLM=0.0, alpha_DIBL=d)
    print(f'  log_err={log_err:.2f} max_err={max_err:.2f}  n={n} K={K} alpha_sat={a} DIBL={d}')
    for vg, vd, Id_t in TARGETS:
        if vg < 0.5: continue
        Id_m = m.drain_current(vg, vd, p)
        rel = (Id_m - Id_t) / Id_t * 100
        print(f'    Vg={vg} Vd={vd}: paper={Id_t*1e6:.2f} model={Id_m*1e6:.2f} err={rel:+.1f}%')
