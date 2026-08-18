"""Find the plot-box axes for Fig 5(d) and 5(e) and extract the data points.

We use the 3x upscaled PNGs. For each, find:
  - left axis (vertical line at x = x_left)
  - right axis (vertical line at x = x_right)
  - top axis (horizontal line at y = y_top)
  - bottom axis (horizontal line at y = y_bot)
Then we have a pixel grid that maps to data coordinates.

Fig 5(d) — Id-Vg 2T0C:
  x: Vg from -1 to 2 V
  y: log Id from 10^-14 to 10^-4 A  (10 decades)
  Curves: Vd=0.1 V, Vd=1 V
Fig 5(e) — Id-Vd 2T0C:
  x: Vd from 0 to 3 V
  y: Id from 0 to 60 uA (linear)
  Curves: Vg=0.4, 1.2, 2.0 V
"""
from PIL import Image
import numpy as np
import os

d = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'

def find_plot_box(img, expected_gray=50, tol=30):
    """Find the dark rectangle (axes) by scanning for solid dark lines."""
    arr = np.array(img.convert('RGB'))
    gray = arr.mean(axis=2)
    H, W = gray.shape
    # Top edge: scan each column for the topmost very-dark pixel
    dark = gray < (expected_gray + tol)
    # Sum per row
    row_density = dark.sum(axis=1)
    col_density = dark.sum(axis=0)
    # Find the longest horizontal line
    thresh_r = max(100, W * 0.5)
    thresh_c = max(100, H * 0.5)
    # Use the highest-density rows
    top_rows = np.where(row_density > thresh_r)[0]
    bot_rows = np.where(row_density > thresh_r)[0]
    left_cols = np.where(col_density > thresh_c)[0]
    right_cols = np.where(col_density > thresh_c)[0]
    return top_rows, bot_rows, left_cols, right_cols

for name in ['fig5d_final_3x.png', 'fig5e_final_3x.png']:
    p = os.path.join(d, name)
    im = Image.open(p)
    print('===', name, im.size)
    arr = np.array(im.convert('RGB'))
    gray = arr.mean(axis=2)
    H, W = gray.shape
    # threshold for "dark"
    dark = gray < 60
    rd = dark.sum(axis=1)
    cd = dark.sum(axis=0)
    # find rows that have a long dark horizontal line (axes)
    # top axis: near top of plot, full width dark line
    # We'll find local maxima
    # Plot borders are typically 3-5 pixels wide.
    # Find a column where the dark count is high: this corresponds to the left axis
    # and the right axis.
    # In a 1350x960 image with plot spanning maybe 200..1100 in x and 100..800 in y:
    thresh_row = W * 0.5
    thresh_col = H * 0.5
    horiz_lines = np.where(rd > thresh_row)[0]
    vert_lines = np.where(cd > thresh_col)[0]
    # cluster consecutive rows
    def cluster(idx):
        if len(idx) == 0:
            return []
        groups = [[idx[0]]]
        for v in idx[1:]:
            if v - groups[-1][-1] <= 2:
                groups[-1].append(v)
            else:
                groups.append([v])
        return [(g[0], g[-1]) for g in groups]
    hr = cluster(horiz_lines)
    vc = cluster(vert_lines)
    print('horiz line candidates (top,bot):', hr[:10])
    print('vert line candidates (left,right):', vc[:10])
