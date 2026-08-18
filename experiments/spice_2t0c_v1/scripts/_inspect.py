import sys
sys.path.insert(0, r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\scripts')
import device_model_v1 as m
p = m.DEFAULTS
print('V_T =', m.V_T, 'V')
print('C_ox =', (p['eps_ox']*m.EPS0)/m.t_ox, 'F/m^2')
print('W_eff/L =', m.W_eff/m.L)
print()
for Vg in [-0.5, 0, 0.4, 1.2, 2.0]:
    for Vd in [0.1, 1.0]:
        psi = m.surface_potential(Vg, Vd, p)
        Q_s = m.charge_sheet(Vg, Vd, psi, p)
        mu = m.mobility(Vg, Vd, psi, p)
        Vth = p['V_fb'] + psi
        Vov = Vg - Vth
        print(f'Vg={Vg:5.2f} Vd={Vd:4.2f}  psi={psi:7.4f}  V_th={Vth:6.3f}  V_ov={Vov:6.3f}  Q_s={Q_s:9.4f} C/m^2  mu={mu*1e4:7.3f} cm^2/Vs')
