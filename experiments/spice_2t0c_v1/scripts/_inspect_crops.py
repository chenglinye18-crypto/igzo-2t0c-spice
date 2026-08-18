import os
from PIL import Image
d = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
for f in sorted(os.listdir(d)):
    if f.endswith('.png'):
        im = Image.open(os.path.join(d, f))
        print(f'{f:35s} {im.size[0]:5d} x {im.size[1]:5d}')
