"""Find the precise bounding box of Fig 5(d) and Fig 5(e) in the full page."""
from PIL import Image
import numpy as np
import os
p3 = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data\page3-3.png'
out = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'
im = Image.open(p3).convert('RGB')
W, H = im.size
arr = np.array(im)
print('image', arr.shape)

# Right column on IEDM 2-col paper. Page is 8.5" x 11" = 2550 x 3300 at 300 DPI.
# Right column starts around x ~ 1330 (with 60-70 px margin from gutter at x=1280).
# Let's find dark pixels in the right column to localize the figure frames.
gray = arr.mean(axis=2)
# Look for very dark pixels (axes/ticks/text)
dark = gray < 80
# restrict to right column
right = dark[:, 1300:2500]
# per-row sum
row_sums = right.sum(axis=1)
# show structure
import sys
for y in range(0, H, 50):
    bar = '#' * min(60, int(row_sums[y]/200))
    print(f'{y:4d} {row_sums[y]:6d} {bar}')
