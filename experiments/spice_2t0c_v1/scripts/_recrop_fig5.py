"""Recrop Fig 5(d) and Fig 5(e) cleanly from page3-3.png at full resolution.
Saves a debug overlay so we can verify axis ranges match the caption."""
from PIL import Image, ImageDraw
import os

p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3)
W, H = im.size
print('page3 size:', W, H)

# We need to find the bounding box of Fig 5(d) and Fig 5(e).
# The page is a 2-column IEDM paper; Fig 5 is described in the caption as
# "(d) Id-Vg and (e) Id-Vd". They are on the right column of page 3.
# Empirically, Fig 5(d) is top-right of the right column, Fig 5(e) is
# middle-right (below the legend block).

# Try: Fig 5d sits approximately at x in [1300, 2500], y in [120, 800]
# Try: Fig 5e sits approximately at x in [1300, 2500], y in [900, 1700]
# Will refine.

# Step 1: produce a few candidate crops for visual inspection
candidates = {
    'fig5d_test1.png': (1280, 100, 2520, 950),
    'fig5d_test2.png': (1300, 130, 2500, 900),
    'fig5d_test3.png': (1330, 80, 2500, 880),
    'fig5e_test1.png': (1280, 950, 2520, 1750),
    'fig5e_test2.png': (1300, 970, 2500, 1700),
    'fig5e_test3.png': (1330, 950, 2500, 1750),
}
for name, box in candidates.items():
    im.crop(box).save(os.path.join(out, name))
    print('saved', name, 'size', (box[2]-box[0], box[3]-box[1]))
