"""Final clean crop of Fig 5(d) and 5(e) with full plot box + axes + labels."""
from PIL import Image
import os
p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3)
# Estimate plot box by looking at v2 crop. v2 crop was (1300, 1700, 2480, 2300).
# The Fig 5(d) plot box is approximately at relative (in v2):
#   x: 70..420 (page: 1370..1720)
#   y: 25..285 (page: 1725..1985)
# Fig 5(e) plot box:
#   x: 470..830 (page: 1770..2130)
#   y: 25..285 (page: 1725..1985)
crops = {
    'fig5d_final.png':  (1320, 1690, 1770, 2010),
    'fig5e_final.png':  (1730, 1690, 2200, 2010),
}
for name, box in crops.items():
    im.crop(box).save(os.path.join(out, name))
    print('saved', name, box, (box[2]-box[0], box[3]-box[1]))
# Make 3x upscaled versions for pixel-level digitization
for n in ['fig5d_final.png', 'fig5e_final.png']:
    src = Image.open(os.path.join(out, n))
    sw, sh = src.size
    src.resize((sw*3, sh*3), Image.LANCZOS).save(os.path.join(out, n.replace('.png', '_3x.png')))
    print('3x of', n, '-> size', (sw*3, sh*3))
