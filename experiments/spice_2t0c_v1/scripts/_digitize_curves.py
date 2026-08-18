"""Digitize Fig 5(d) Id-Vg and Fig 5(e) Id-Vd using the precise plot boxes we found.

Fig 5(d) 3x PNG: 1350 x 960
  Plot box (axes): x in [95, 1129] (px), y in [86, 855]  (top, bot horizontal axis lines)
  data: x: Vg -1..2  (3 V span), y: log Id 10^-4..10^-14 (10 decades, log scale, axis inverted)

Fig 5(e) 3x PNG: 1410 x 960
  Plot box: x in [749, 1018] (left, right axis), y in [84, 855]
  data: x: Vd 0..3 (3 V span), y: Id 0..60 uA (linear, axis inverted)
"""
from PIL import Image
import numpy as np
import os, csv

d = r'E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1\data'

# Plot box parameters
# (left_px, right_px, top_px, bot_px)
box_d = (95, 1129, 86, 855)   # fig5d
box_e = (749, 1018, 84, 855)  # fig5e

# Color targets for the two curves in each plot
# Fig 5(d): dark orange (#E37222) for Vd=1V, light yellow (#E5C575) for Vd=0.1V
# Fig 5(e): three shades of blue. The top curve (Vg=2V) is the darkest.

def load_rgb(name):
    p = os.path.join(d, name)
    im = Image.open(p)
    return np.array(im.convert('RGB')).astype(int)

def find_color_curve(arr, box, target_rgb, tol=40, min_pixels=2):
    """Return (x_px, y_px) per column along the curve, finding the densest
    cluster of pixels whose color is close to target_rgb."""
    L, R, T, B = box
    region = arr[T:B+1, L:R+1]   # shape (h, w, 3)
    H, W, _ = region.shape
    diff = np.abs(region - np.array(target_rgb)).sum(axis=2)
    mask = diff < tol
    # for each column, find the mean y of matching pixels
    out_x, out_y = [], []
    for x in range(W):
        ys = np.where(mask[:, x])[0]
        if len(ys) >= min_pixels:
            # take median y
            out_x.append(x)
            out_y.append(int(np.median(ys)))
    return np.array(out_x), np.array(out_y)

# ---- Fig 5(d) ----
arr_d = load_rgb('fig5d_final_3x.png')
print('arr_d shape', arr_d.shape)

# Try to identify the orange (Vd=1V) and tan (Vd=0.1V) curve colors.
# Sample from a known data region.
def sample(arr, box, x_in, y_in, k=5):
    L, R, T, B = box
    px = arr[T + y_in - k:T + y_in + k + 1, L + x_in - k:L + x_in + k + 1]
    return px.reshape(-1, 3).mean(axis=0)

# We will sweep the plot for both colors. Inspect a few sample points first.
print('sample at Id-Vg dark orange, near top right (curve, Vd=1V, Vg~1.8):',
      sample(arr_d, box_d, 950, 110))
print('sample at Id-Vg tan (Vd=0.1V, Vg~1.8):', sample(arr_d, box_d, 950, 230))
print('sample at empty area (background):', sample(arr_d, box_d, 200, 500))

# The dark orange of the Vd=1V curve. Estimated rgb ~ (220, 110, 35).
# The tan/light yellow of the Vd=0.1V curve. Estimated rgb ~ (220, 190, 120).
TARGETS_D = {
    'Vd=1V':  (220, 110, 35),
    'Vd=0.1V':(220, 190, 120),
}

results_d = {}
for label, tgt in TARGETS_D.items():
    x_px, y_px = find_color_curve(arr_d, box_d, tgt, tol=60, min_pixels=1)
    print(f'  {label}: {len(x_px)} cols, x_px range {x_px.min() if len(x_px) else "-"}..{x_px.max() if len(x_px) else "-"}')
    results_d[label] = (x_px, y_px)

# Map to data: x_data = -1 + (x_px / (R-L)) * 3
# y_data (log10 Id): top axis (T) = -4, bot (B) = -14
# Id = 10^(-4 + (y_px / (B-T)) * (-10)) = 10^(-4 - 10*y_px/(B-T))
def px_to_vg(x_px, box):
    L, R, T, B = box
    return -1.0 + (x_px / (R - L)) * 3.0
def px_to_logId(y_px, box):
    L, R, T, B = box
    return -4.0 + (y_px / (B - T)) * (-10.0)

print()
print('=== Fig 5(d) Id-Vg digitized ===')
for label, (xp, yp) in results_d.items():
    vg = px_to_vg(xp, box_d)
    logId = px_to_logId(yp, box_d)
    Id = 10**logId
    print(f'  {label}: n={len(vg)}, Vg in [{vg.min():.2f},{vg.max():.2f}], Id in [{Id.min():.2e},{Id.max():.2e}]')
    # print every 5th point
    for k in range(0, len(vg), 5):
        print(f'    {vg[k]:6.3f}  {Id[k]:11.3e}')

# ---- Fig 5(e) ----
arr_e = load_rgb('fig5e_final_3x.png')
print()
print('arr_e shape', arr_e.shape)
# Sample colors at top (Vg=2V) and middle (Vg=1.2V) and bottom (Vg=0.4V)
# Top curve ~ Vg=2V is the darkest blue, bottom is lightest
# Try to read the colors at known points
print('sample at Id-Vd Vg=2V (top), Vd~2.0:', sample(arr_e, box_e, 200, 100))
print('sample at Id-Vd Vg=1.2V (mid), Vd~1.0:', sample(arr_e, box_e, 100, 250))
print('sample at Id-Vd Vg=0.4V (low), Vd~1.0:', sample(arr_e, box_e, 100, 500))

# In the 3x crop we see three curves. The top (Vg=2V) curve at Vd=2.0 is around x_px=200, y_px=100
# The mid (Vg=1.2V) is around y_px=300
# The low (Vg=0.4V) is around y_px=550
# All three are blue but with different brightness.

# Try to find each curve. We'll use distinct lightness thresholds.
# First, find "blue" pixels (B channel much larger than R, G).
def find_blue_curve(arr, box, b_min=130, b_minus_r_min=20, min_pixels=2):
    L, R, T, B_ = box
    region = arr[T:B_+1, L:R+1]
    H, W, _ = region.shape
    r, g, b = region[..., 0], region[..., 1], region[..., 2]
    mask = (b > b_min) & ((b - r) > b_minus_r_min) & ((b - g) > b_minus_r_min)
    out_x, out_y = [], []
    for x in range(W):
        ys = np.where(mask[:, x])[0]
        if len(ys) >= min_pixels:
            out_x.append(x)
            out_y.append(int(np.median(ys)))
    return np.array(out_x), np.array(out_y)

# Lightest blue (Vg=0.4V) — typically b channel just above 130
# Darkest blue (Vg=2V) — b channel near 200
xp_l, yp_l = find_blue_curve(arr_e, box_e, b_min=130, b_minus_r_min=10, min_pixels=1)
print('blue total:', len(xp_l), 'y range', yp_l.min() if len(yp_l) else '-', yp_l.max() if len(yp_l) else '-')

# Split into 3 curves by y position: bottom (highest Id), middle, top (lowest Id)
# Id axis: 0 at bottom (y=855), 60 at top (y=84). Larger y => smaller Id.
# So the smallest y corresponds to largest Id (Vg=2V).
# The three curves (Vg=2V, 1.2V, 0.4V) have monotonic y order at any Vd:
#   Vg=2V  -> smallest y  (highest Id)
#   Vg=1.2V -> middle y
#   Vg=0.4V -> largest y  (lowest Id)
# We can separate them by running clustering on y per column.
# Simpler: for each x, we expect at most 3 y values (the 3 curves). Sort them
# and take the smallest (Vg=2V), middle (Vg=1.2V), largest (Vg=0.4V).

def split_three_curves(xp, yp, max_gap=8):
    """At each x where all 3 curves are present, separate."""
    by_x = {}
    for x, y in zip(xp, yp):
        by_x.setdefault(x, []).append(y)
    out = {2.0: ([], []), 1.2: ([], []), 0.4: ([], [])}
    for x, ys in by_x.items():
        ys = sorted(set(ys))
        # cluster y values
        groups = [[ys[0]]]
        for v in ys[1:]:
            if v - groups[-1][-1] <= max_gap:
                groups[-1].append(v)
            else:
                groups.append([v])
        # take median of each group
        med = [int(np.median(g)) for g in groups]
        if len(med) >= 3:
            # assume sorted by y: smallest y = top curve = Vg=2V
            out[2.0][0].append(x); out[2.0][1].append(med[0])
            out[1.2][0].append(x); out[1.2][1].append(med[len(med)//2])
            out[0.4][0].append(x); out[0.4][1].append(med[-1])
    return out

curves_e = split_three_curves(xp_l, yp_l, max_gap=4)
print()
print('=== Fig 5(e) Id-Vd digitized ===')
# Map to Vd / Id
def px_to_Vd(x_px, box):
    L, R, T, B = box
    return (x_px / (R - L)) * 3.0
def px_to_Id_uA(y_px, box):
    L, R, T, B = box
    # 60 at top (y=T), 0 at bottom (y=B)
    return 60.0 * (1 - (y_px - T) / (B - T))
for vg, (xp, yp) in curves_e.items():
    xp = np.array(xp); yp = np.array(yp)
    if len(xp) == 0:
        print(f'  Vg={vg}: empty')
        continue
    vd = px_to_Vd(xp, box_e)
    IuA = px_to_Id_uA(yp, box_e)
    print(f'  Vg={vg}: n={len(vd)}, Vd in [{vd.min():.2f},{vd.max():.2f}], Id in [{IuA.min():.2f},{IuA.max():.2f}] uA')
    for k in range(0, len(vd), 5):
        print(f'    Vd={vd[k]:6.3f}  Id={IuA[k]:8.3f} uA')
