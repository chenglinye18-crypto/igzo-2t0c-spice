"""Tight, clean crop of Fig 5(d), 5(e), and 5(f) without caption."""
from PIL import Image
import os
p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3)
# Based on the v2 crop (1300, 1700, 2480, 2300), Fig 5(d) is approx
# at x_in_crop [50..450], y_in_crop [10..330] -> page [1350..1750, 1710..2030]
# Fig 5(e) at x_in_crop [50..450], y_in_crop [10..330] shifted by ~330 vertically? No, the
# 1T1C row used ~250 vertical; the 2T0C row uses similar ~250 vertical, but the
# legend/f labels are larger.
# Let's just crop the whole 2T0C row strip tightly.
crops = {
    'fig5d_clean.png':  (1340, 1700, 1750, 2030),    # just the (d) panel
    'fig5e_clean.png':  (1740, 1700, 2160, 2030),    # just the (e) panel
    'fig5f_clean.png':  (2160, 1700, 2500, 2030),    # just the (f) panel
    'fig5d_2x.png':     None,                          # placeholder for the 2x upscale
}
for name, box in list(crops.items())[:3]:
    im.crop(box).save(os.path.join(out, name))
    print('saved', name, box, (box[2]-box[0], box[3]-box[1]))
# 2x upscales for higher-precision digitizing
for n in ['fig5d_clean.png', 'fig5e_clean.png']:
    src = Image.open(os.path.join(out, n))
    src.resize((src.size[0]*2, src.size[1]*2), Image.LANCZOS).save(os.path.join(out, n.replace('.png', '_2x.png')))
    print('upscaled', n, '->', n.replace('.png', '_2x.png'))
