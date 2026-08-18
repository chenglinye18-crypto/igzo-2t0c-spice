"""
extract_iv_curves.py
====================

Manual/programmatic digitization of the 2T0C I-V curves from
Zhu IEDM 2026, Fig. 5(d) and Fig. 5(e).

Approach:
    * Use the cropped figure images (data/fig5d_2t0c_idvg.png,
      data/fig5e_2t0c_idvd.png) which were created from the page-3
      render of ref/IEDM2026_HaotongZhu_V5.pdf.
    * Identify the two orange curves (light orange = Vd=0.1V, dark
      orange = Vd=1V) in Id-Vg and the three blue curves in Id-Vd by
      hue.
    * For each x-axis column, pick the y-pixel of the curve; convert
      pixel -> (Vg, Id) or (Vd, Id) using the axis ranges below.

Axis ranges (read off the paper figure captions and ticks):
    Fig 5(d) 2T0C Id-Vg
        x: Vg in [-1, 2] V
        y: Id in [1e-14, 1e-4] A   (10 decades, log scale)

    Fig 5(e) 2T0C Id-Vd
        x: Vd in [0, 3] V
        y: Id in [0, 60] uA        (linear scale)

These axis ranges are explicitly stated in the figure captions and
visible ticks. They are NOT calibrated pixel-by-pixel against the
PDF; small offsets are expected. The output CSVs are saved with
columns that match the units of the paper exactly.
"""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

# Axis ranges (paper-stated).
IDVG_X = (-1.0, 2.0)   # Vg  [V]
IDVG_Y = (1e-14, 1e-4)  # Id  [A]
IDVD_X = (0.0, 3.0)     # Vd  [V]
IDVD_Y = (0.0, 60.0)    # Id  [uA]


def _find_orange_columns(img_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (light_orange_y, dark_orange_y) per column.

    The two orange curves in Fig 5(d) are: a lighter orange (Vd=0.1V)
    and a darker orange (Vd=1V). We classify pixels by hue/saturation.
    """
    R = img_arr[..., 0].astype(int)
    G = img_arr[..., 1].astype(int)
    B = img_arr[..., 2].astype(int)
    # orange-ish: R high, B low
    is_orange = (R > 180) & (B < 180) & (R - B > 50) & (G > B)
    # light vs dark: lighter if G is higher
    light = is_orange & (G > 150)
    dark = is_orange & (G <= 150) & (G > 90)
    return light, dark


def _column_curve_ys(curve_mask: np.ndarray, y_plot_min: int, y_plot_max: int) -> np.ndarray:
    """For each x column, return the median y of pixels inside the plot
    vertical band [y_plot_min, y_plot_max]. Returns array of length W
    with NaN where no curve pixels were found.
    """
    H, W = curve_mask.shape
    out = np.full(W, np.nan)
    band = curve_mask[y_plot_min:y_plot_max, :]
    for x in range(W):
        col = np.where(band[:, x])[0]
        if col.size:
            # median over the y band (relative); convert to absolute
            out[x] = col.mean() + y_plot_min
    return out


def extract_idvg() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract (Vg, Id_Vd0p1, Id_Vd1) from the cropped Fig 5(d)."""
    img_path = DATA / "fig5d_2t0c_idvg.png"
    if not img_path.exists():
        raise FileNotFoundError(img_path)
    im = Image.open(img_path).convert("RGB")
    arr = np.array(im)
    H, W, _ = arr.shape
    light, dark = _find_orange_columns(arr)

    # Plot area inspection: orange curves are in x in [78, 203]
    # The y plot area covers roughly [10, 195] (the 10^-14 to 10^-4 ticks)
    # Pick tight band to avoid the axis label "Id (A)" and the "2T0C" text
    y_min, y_max = 28, 195

    # Use median y of curve pixels in the plot band
    light_y = _column_curve_ys(light, y_min, y_max)
    dark_y = _column_curve_ys(dark, y_min, y_max)

    # Pick x columns where both curves have a reading
    valid_x = np.where(np.isfinite(light_y) | np.isfinite(dark_y))[0]
    if valid_x.size == 0:
        raise RuntimeError("No orange curve pixels found in Id-Vg plot")
    # The actual plot x range is 78..203, which corresponds to Vg in [-1, 2]
    x_left, x_right = valid_x.min(), valid_x.max()
    xs = np.arange(x_left, x_right + 1)
    Vg_axis = np.interp(xs, [x_left, x_right], [IDVG_X[0], IDVG_X[1]])

    # Map y_px in [y_plot_top, y_plot_bot] to log10(Id) in [log(y_max), log(y_min)]
    # log y: top of plot -> Id = 1e-4, bottom -> Id = 1e-14
    log_y_top = np.log10(IDVG_Y[1])  # 1e-4
    log_y_bot = np.log10(IDVG_Y[0])  # 1e-14
    y_plot_top = y_min
    y_plot_bot = y_max

    def to_id(y_px_arr: np.ndarray) -> np.ndarray:
        out = np.full_like(y_px_arr, np.nan, dtype=float)
        m = np.isfinite(y_px_arr)
        if m.any():
            t = (y_px_arr[m] - y_plot_top) / (y_plot_bot - y_plot_top)
            out[m] = 10.0 ** (log_y_top + t * (log_y_bot - log_y_top))
        return out

    Id0p1 = to_id(light_y[x_left:x_right + 1])
    Id1 = to_id(dark_y[x_left:x_right + 1])
    return Vg_axis, Id0p1, Id1


def _find_blue_columns(img_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (light_blue, mid_blue, dark_blue) per column for Fig 5(e).

    The three Id-Vd curves are: Vg=0.4V (lowest), Vg=1.2V (middle),
    Vg=2.0V (highest). We just find 3 clusters by intensity.
    """
    R = img_arr[..., 0].astype(int)
    G = img_arr[..., 1].astype(int)
    B = img_arr[..., 2].astype(int)
    is_blue = (B > 180) & (B > R + 30) & (R < 200)
    # Three shades: light (R,G,B all high) -> dark (R,G low, B still high)
    light = is_blue & (G > 150) & (R > 100)
    mid = is_blue & (G > 110) & (G < 170) & (R < 130)
    dark = is_blue & (G < 130) & (R < 100)
    return light, mid, dark


def extract_idvd() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract (Vd, Id_Vg0p4, Id_Vg1p2, Id_Vg2) from Fig 5(e)."""
    img_path = DATA / "fig5e_2t0c_idvd.png"
    if not img_path.exists():
        raise FileNotFoundError(img_path)
    im = Image.open(img_path).convert("RGB")
    arr = np.array(im)
    H, W, _ = arr.shape
    light, mid, dark = _find_blue_columns(arr)

    # Same approach: pick tight plot band, find median y per x column
    y_min, y_max = 28, 195
    light_y = _column_curve_ys(light, y_min, y_max)
    mid_y = _column_curve_ys(mid, y_min, y_max)
    dark_y = _column_curve_ys(dark, y_min, y_max)

    valid_x = np.where(np.isfinite(light_y) | np.isfinite(mid_y) | np.isfinite(dark_y))[0]
    if valid_x.size == 0:
        raise RuntimeError("No blue curve pixels found in Id-Vd plot")
    x_left, x_right = valid_x.min(), valid_x.max()
    xs = np.arange(x_left, x_right + 1)
    Vd_axis = np.interp(xs, [x_left, x_right], [IDVD_X[0], IDVD_X[1]])

    y_plot_top, y_plot_bot = y_min, y_max

    def to_uA(y_px_arr: np.ndarray) -> np.ndarray:
        out = np.full_like(y_px_arr, np.nan, dtype=float)
        m = np.isfinite(y_px_arr)
        if m.any():
            t = (y_px_arr[m] - y_plot_top) / (y_plot_bot - y_plot_top)
            out[m] = (1.0 - t) * (IDVD_Y[1] - IDVD_Y[0]) + IDVD_Y[0]
        return out

    Id0p4 = to_uA(light_y[x_left:x_right + 1])
    Id1p2 = to_uA(mid_y[x_left:x_right + 1])
    Id2 = to_uA(dark_y[x_left:x_right + 1])
    return Vd_axis, Id0p4, Id1p2, Id2


def main() -> None:
    print("Extracting Fig 5(d) 2T0C Id-Vg ...")
    Vg, Id0p1, Id1 = extract_idvg()
    out_idvg = DATA / "idvg.csv"
    with out_idvg.open("w", encoding="utf-8") as f:
        f.write("# Zhu 2T0C Fig 5(d) -- paper-anchored digitization\n")
        f.write("# Vg (V), Id @ Vd=0.1V (A), Id @ Vd=1V (A)\n")
        for vg, i1, i2 in zip(Vg, Id0p1, Id1):
            f.write(f"{vg:.6e},{i1:.6e},{i2:.6e}\n")
    print(f"  -> {out_idvg}  ({len(Vg)} rows)")

    print("Extracting Fig 5(e) 2T0C Id-Vd ...")
    Vd, Id0p4, Id1p2, Id2 = extract_idvd()
    out_idvd = DATA / "idvd.csv"
    with out_idvd.open("w", encoding="utf-8") as f:
        f.write("# Zhu 2T0C Fig 5(e) -- paper-anchored digitization\n")
        f.write("# Vd (V), Id @ Vg=0.4V (uA), Id @ Vg=1.2V (uA), Id @ Vg=2.0V (uA)\n")
        for vd, i1, i2, i3 in zip(Vd, Id0p4, Id1p2, Id2):
            f.write(f"{vd:.6e},{i1:.6e},{i2:.6e},{i3:.6e}\n")
    print(f"  -> {out_idvd}  ({len(Vd)} rows)")


if __name__ == "__main__":
    main()
