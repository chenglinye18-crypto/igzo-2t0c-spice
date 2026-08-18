import sys, os
sys.path.insert(0, r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\scripts')
import device_model_v1 as m
FROZEN = dict(
    N_D=1.0e18, eps_s=10.0, eps_ox=22.0, mu_0=80.0, mu_b=15.0,
    USR=1.0e-14, E_USC=1.5, V_fb=-0.5, V_th0=0.4, m_body=1.8,
    lambda_eff=1.5e-8,
)
p_final = dict(FROZEN, n_power=1.5, K_pre=1.5e5, alpha_sat=0.015, CLM=0, alpha_DIBL=0)
print('p_final:', p_final)
print()
for Vg, Vd in [(1.2, 1.0), (2.0, 1.0), (2.0, 0.1), (0.4, 1.0)]:
    I = m.drain_current(Vg, Vd, p_final)
    print(f'Vg={Vg} Vd={Vd}: Id={I*1e6:.3f} uA')
    P = m.si_units(p_final)
    V_th = m.V_th_effective(Vd, p_final)
    V_ov = Vg - V_th
    Vdsat = max(p_final['alpha_sat']*V_ov, 0.0)
    Vdeff = m.V_d_eff_smooth_min(Vd, Vdsat)
    mu = m.mobility(Vg, Vd, p_final, m.surface_potential(Vg, Vd, p_final))
    _, C_ox = m.body_factor(p_final)
    I_on = p_final['K_pre'] * (m.W_eff/m.L) * mu * C_ox * (V_ov**1.5) * Vdeff
    print(f'  V_ov={V_ov:.3f} Vdsat={Vdsat:.4f} Vdeff={Vdeff:.4f} mu={mu:.4f} C_ox={C_ox:.4f} I_on={I_on*1e6:.3f} uA')
