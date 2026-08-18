"""Try crops lower on the page where Fig 5(d)/(e)/(f) for 2T0C live."""
from PIL import Image
import os
p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3)
W, H = im.size
crops = {
    'fig5d_v2.png':  (1300, 1700, 2480, 2300),
    'fig5e_v2.png':  (1300, 2200, 2480, 2800),
    'fig5d_v3.png':  (1300, 1900, 2480, 2400),
    'fig5e_v3.png':  (1300, 2400, 2480, 2900),
}
for name, box in crops.items():
    im.crop(box).save(os.path.join(out, name))
    print('saved', name, box, (box[2]-box[0], box[3]-box[1]))
