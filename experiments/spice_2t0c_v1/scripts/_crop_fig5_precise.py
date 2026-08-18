"""Precise crop of Fig 5(d) and 5(e) using the band1 image as reference."""
from PIL import Image
import os
p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3)
W, H = im.size

# Based on the band1 inspection, Fig 5(d) is around y=1200..1900, right column.
# Within band1 image (1100..2200 in page coords), Fig 5(d) is around the
# upper-right subfigure. Let me look at specific crops.
# Try a wider crop covering the full right column of the figure region.
crops = {
    'fig5d_precise.png':  (1370, 1100, 2450, 1660),
    'fig5e_precise.png':  (1370, 1660, 2450, 2200),
    'fig5d_extra.png':    (1330, 1100, 2480, 1680),
    'fig5e_extra.png':    (1330, 1660, 2480, 2200),
}
for name, box in crops.items():
    im.crop(box).save(os.path.join(out, name))
    print('saved', name, box, (box[2]-box[0], box[3]-box[1]))
