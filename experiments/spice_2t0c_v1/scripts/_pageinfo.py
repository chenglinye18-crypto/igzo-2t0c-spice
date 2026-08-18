"""Render every page of the Zhu paper and let us identify which has Fig 5(d)/(e)."""
import os, subprocess
pdf = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\ref\IEDM2026_HaotongZhu_V5.pdf'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\_pages'
os.makedirs(out, exist_ok=True)
# Use a fast low-res render to identify pages
cairo = r'C:\Users\Leslie\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftocairo.exe'
subprocess.run([cairo, '-png', '-r', '90', pdf, os.path.join(out, 'p')], check=True)
import glob
for f in sorted(glob.glob(os.path.join(out, 'p-*.png'))):
    print(f, os.path.getsize(f))
