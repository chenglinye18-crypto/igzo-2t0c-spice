"""Run ngspice DC sweeps for v1.1 model and compare to Python.

Uses the v1.1 final parameters: n=1.7, K=0.7, alpha_sat=0.03, CLM=0, DIBL=0.08.
"""
import os, sys, subprocess, numpy as np, csv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import device_model_v1 as m

NGSPICE = r'D:\Spice64\bin\ngspice_con.exe'
NETLIST_DIR = os.path.join(ROOT, 'netlists')
RES_DIR = os.path.join(ROOT, 'results')
TMP_DIR = os.path.join(RES_DIR, '_spice_tmp_v11')
os.makedirs(TMP_DIR, exist_ok=True)

# v1.1 final parameters
P_FINAL = dict(
    N_D=1.0e18, eps_s=10.0, eps_ox=22.0, mu_0=80.0, mu_b=15.0,
    USR=1.0e-14, E_USC=1.5, V_fb=-0.5, V_th0=0.4, m_body=1.8,
    lambda_eff=1.5e-8, alpha_DIBL=0.08, alpha_sat=0.03, CLM=0.0,
    K_pre=0.7, n_power=1.7,
)

def run_one(netlist_str, name):
    tmp = os.path.join(TMP_DIR, name + '.sp')
    with open(tmp, 'w') as f:
        f.write(netlist_str)
    p = subprocess.run([NGSPICE, '-b', tmp], capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        print('ngspice failed for', name); print(p.stderr[:500])
        return None
    rows = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith('*') or line.startswith('Note') or line.startswith('Doing') \
                or line.startswith('No.') or line.startswith('Index') or line.startswith('----') \
                or line.startswith('Circuit') or line.startswith('Warning') \
                or line.startswith('Total') or line.startswith('Current') or line.startswith('Maximum') \
                or line.startswith('DRAM'):
            continue
        parts = line.split()
        if len(parts) >= 5:
            try:
                idx = int(parts[0])
                vg = float(parts[2])
                vd = float(parts[3])
                ivd = float(parts[4])
                rows.append((vg, vd, ivd))
            except ValueError:
                pass
    return rows

def main():
    os.chdir(NETLIST_DIR)
    with open(os.path.join(NETLIST_DIR, 'dc_idvg_v1.sp')) as f:
        idvg_template = f.read()
    with open(os.path.join(NETLIST_DIR, 'dc_idvd_v1.sp')) as f:
        idvd_template = f.read()

    def make(tmpl, **kwargs):
        s = tmpl
        for k, v in kwargs.items():
            s = s.replace(f'{k} g 0 DC 0', f'{k} g 0 DC {v}').replace(f'{k} d 0 DC 0', f'{k} d 0 DC {v}')
        return s

    print('SPICE Id-Vg Vd=0.1V...')
    idvg_01 = run_one(make(idvg_template, VD=0.1), 'idvg_01')
    print('SPICE Id-Vg Vd=1.0V...')
    idvg_1 = run_one(make(idvg_template, VD=1.0), 'idvg_1')
    print('SPICE Id-Vd Vg=0.4V...')
    idvd_04 = run_one(make(idvd_template, VG=0.4), 'idvd_04')
    print('SPICE Id-Vd Vg=1.2V...')
    idvd_12 = run_one(make(idvd_template, VG=1.2), 'idvd_12')
    print('SPICE Id-Vd Vg=2.0V...')
    idvd_20 = run_one(make(idvd_template, VG=2.0), 'idvd_20')

    # write SPICE CSV
    with open(os.path.join(RES_DIR, 'spice_idvg_v11.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Vg_V', 'Id_Vd01_A_spice', 'Id_Vd1_A_spice'])
        if idvg_01 and idvg_1:
            for i in range(min(len(idvg_01), len(idvg_1))):
                w.writerow([idvg_01[i][0], idvg_01[i][2], idvg_1[i][2]])
    with open(os.path.join(RES_DIR, 'spice_idvd_v11.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Vd_V', 'Id_Vg04_A_spice', 'Id_Vg12_A_spice', 'Id_Vg20_A_spice'])
        if idvd_04 and idvd_12 and idvd_20:
            for i in range(min(len(idvd_04), len(idvd_12), len(idvd_20))):
                w.writerow([idvd_04[i][1], idvd_04[i][2], idvd_12[i][2], idvd_20[i][2]])

    # cross-check Python vs SPICE
    rows = []
    if idvg_01:
        for vg_v, _, _ in idvg_01[::5]:
            Id_sp = abs(float(np.interp(vg_v, [r[0] for r in idvg_01], [r[2] for r in idvg_01])))
            Id_py = m.drain_current(vg_v, 0.1, P_FINAL)
            rows.append({'bias': 'Id-Vg', 'Vg': vg_v, 'Vd': 0.1,
                          'spice_Id': Id_sp, 'python_Id': Id_py,
                          'rel_diff': abs(Id_sp - Id_py) / max(Id_py, 1e-20)})
    if idvg_1:
        for vg_v, _, _ in idvg_1[::5]:
            Id_sp = abs(float(np.interp(vg_v, [r[0] for r in idvg_1], [r[2] for r in idvg_1])))
            Id_py = m.drain_current(vg_v, 1.0, P_FINAL)
            rows.append({'bias': 'Id-Vg', 'Vg': vg_v, 'Vd': 1.0,
                          'spice_Id': Id_sp, 'python_Id': Id_py,
                          'rel_diff': abs(Id_sp - Id_py) / max(Id_py, 1e-20)})
    if idvd_20:
        for _, vd_v, _ in idvd_20[::5]:
            Id_sp = abs(float(np.interp(vd_v, [r[1] for r in idvd_20], [r[2] for r in idvd_20])))
            Id_py = m.drain_current(2.0, vd_v, P_FINAL)
            rows.append({'bias': 'Id-Vd', 'Vg': 2.0, 'Vd': vd_v,
                          'spice_Id': Id_sp, 'python_Id': Id_py,
                          'rel_diff': abs(Id_sp - Id_py) / max(Id_py, 1e-20)})
    with open(os.path.join(RES_DIR, 'spice_python_crosscheck_v11.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['bias', 'Vg', 'Vd', 'spice_Id', 'python_Id', 'rel_diff'])
        w.writeheader()
        for r in rows: w.writerow(r)

    if rows:
        max_diff = max(r['rel_diff'] for r in rows)
        med_diff = float(np.median([r['rel_diff'] for r in rows]))
        print(f'\nSPICE vs Python v1.1: max rel_diff = {max_diff:.3e}, median = {med_diff:.3e}')
        print('  (target < 1%)')

    print('spice_idvg_v11.csv, spice_idvd_v11.csv, spice_python_crosscheck_v11.csv written.')

if __name__ == '__main__':
    main()
