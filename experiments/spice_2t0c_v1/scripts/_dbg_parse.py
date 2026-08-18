import subprocess
import os
ROOT = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1'
os.chdir(ROOT)
# Run the netlist and capture
p = subprocess.run([r'D:\Spice64\bin\ngspice_con.exe', '-b', 'netlists/dc_idvg_v1.sp'],
                   capture_output=True, text=True, timeout=60)
print('STDOUT:')
print(p.stdout[:3000])
print('STDERR:')
print(p.stderr[:500])
print('returncode', p.returncode)
