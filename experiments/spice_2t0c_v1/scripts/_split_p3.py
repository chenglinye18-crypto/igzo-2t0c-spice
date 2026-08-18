"""Split page 3 into upper and lower halves to find Fig 5."""
from PIL import Image
import os
p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3)
W, H = im.size
# split into 3 vertical bands
for i, (y0, y1) in enumerate([(0, H//3), (H//3, 2*H//3), (2*H//3, H)]):
    im.crop((0, y0, W, y1)).save(os.path.join(out, f'_p3_band{i}.png'))
    print('band', i, y0, y1, '->', y1-y0)
