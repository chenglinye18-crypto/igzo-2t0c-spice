"""Low-Vd diagnostic: check Vd_eff/Vd, blending, and Id formula step-by-step."""
import sys, os
sys.path.insert(0, r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\scripts')
import device_model_v1 as m
import math

# v1 calibrated params
p = {
    'N_D': 1e18, 'eps_s': 10.0, 'eps_ox': 22.0,
    'mu_0': 10.0, 'mu_b': 15.0,
    'USR': 1e-14, 'E_USC': 2.0,
    'V_fb': -0.5, 'V_th0': 0.4, 'm_body': 1.8,
    'lambda_eff': 1.5e-8, 'alpha_DIBL': 0.3,
    'alpha_sat': 0.7, 'CLM': 1.0,
    'K_pre': 0.3, 'n_power': 1.5,
}

print(f'{"Vg":>5} {"Vd":>7} {"Vth":>6} {"V_ov":>6} {"Vdsat":>6} {"Vdeff":>7} {"Vdeff/Vd":>9} {"mu":>7} {"I_on":>10} {"I_off":>10} {"w_on":>5} {"I_d":>10}')

# helper: replicate drain_current but expose intermediates
def diag(Vg, Vd, p):
    P = m.si_units(p)
    _, C_ox = m.body_factor(p)
    m_eff = P['m_body']
    psi_s = m.surface_potential(Vg, Vd, p)
    V_th = m.V_th_effective(Vd, p)
    V_ov = Vg - V_th
    mu = m.mobility(Vg, Vd, p, psi_s)
    Vdsat = max(P['alpha_sat'] * V_ov, 0.0)
    Vdeff = min(Vd, Vdsat) if Vdsat > 0 else Vd
    if Vd > Vdsat and Vdsat > 0:
        Vdeff = Vdsat * (1.0 + P['CLM'] * (Vd - Vdsat))
    if V_ov > 0 and Vdeff > 0:
        I_on = P['K_pre'] * (m.W_eff / m.L) * mu * C_ox * (V_ov ** P['n_power']) * Vdeff
    else:
        I_on = 0.0
    mV_T = m_eff * m.V_T
    x_sub = (Vg - V_th) / mV_T
    if x_sub > 10:
        I_off = (m.W_eff / m.L) * P['mu_b'] * C_ox * (mV_T ** 2) * math.exp(10) * (1.0 - math.exp(-Vd / m.V_T))
    elif x_sub < -50:
        I_off = 0.0
    else:
        I_off = (m.W_eff / m.L) * P['mu_b'] * C_ox * (mV_T ** 2) * math.exp(x_sub) * (1.0 - math.exp(-Vd / m.V_T))
    w_on = 1.0 / (1.0 + math.exp(-V_ov / mV_T))
    I = w_on * I_on + (1 - w_on) * I_off
    return V_th, V_ov, Vdsat, Vdeff, mu, I_on, I_off, w_on, I

Vg_list = [0.4, 1.2, 2.0]
Vd_list = [1e-4, 1e-3, 1e-2, 0.05, 0.1, 0.5, 1.0, 2.0, 3.0]
for Vg in Vg_list:
    for Vd in Vd_list:
        Vth, Vov, Vdsat, Vdeff, mu, I_on, I_off, w_on, I = diag(Vg, Vd, p)
        print(f'{Vg:5.2f} {Vd:7.4f} {Vth:6.3f} {Vov:6.3f} {Vdsat:6.3f} {Vdeff:7.4f} {Vdeff/max(Vd,1e-9):9.4f} {mu*1e4:7.2f} {I_on*1e6:10.3f} {I_off*1e6:10.3f} {w_on:5.3f} {I*1e6:10.3f}')
    print()

# Also show paper data for comparison
print('=== paper data ===')
print(f'{"Vg":>5} {"Vd=0.1":>9} {"Vd=1":>9} {"Vd=3":>9}')
paper_idvg = {0.4: 1e-8, 1.2: 6e-6, 2.0: 3.5e-5}
paper_idvd_2 = {0.05: 2, 0.1: 3.5, 0.5: 13, 1.0: 22, 2.0: 38, 3.0: 55}
for Vg in Vg_list:
    print(f'{Vg:5.2f} {paper_idvg.get(Vg, 0)*1e6:9.3f}', end='')
    if Vg == 2.0:
        for Vd in [0.1, 1.0, 3.0]:
            print(f' {paper_idvd_2.get(Vd, 0):9.3f}', end='')
    print()
