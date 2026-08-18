# Digitization Notes — idvg.csv / idvd.csv

## Why two CSV files, not the auto-extracted image pixels

The initial `extract_iv_curves.py` script does a hue-based extraction
from the page-3 PNG of the paper. The result was noisy because:

1. The 2T0C subplot shares its crop with axis labels and the "2T0C"
   header text, which the orange-detector picks up as curve pixels.
2. Three blue curves in Id-Vd have similar hue; distinguishing them
   robustly from anti-aliased line segments requires a fit/cluster
   step, not a simple threshold.

Instead, the CSVs in this directory are **manually digitized** by reading
the axis ticks and curve positions of the paper figure. The pixel
extraction script remains in `scripts/extract_iv_curves.py` as a
reproducible starting point if a future revision wants to refine the
extraction.

## How the values were picked

* `data/idvg.csv` — Fig. 5(d):
  - x-axis: Vg from -1 V to 2 V (paper-stated)
  - y-axis: Id from 1e-14 A to 1e-4 A (paper-stated, 10 decades log)
  - 19 points hand-picked at smooth intervals, ~0.1 V
  - Two columns: Vd=0.1 V (linear/triode regime) and Vd=1 V
    (near-saturation)

* `data/idvd.csv` — Fig. 5(e):
  - x-axis: Vd from 0 to 3 V
  - y-axis: Id from 0 to 60 uA
  - 13 points, 0.1 V to 0.3 V steps
  - Three columns: Vg = 0.4, 1.2, 2.0 V (the three Vstep=0.8 V curves)

The values are **representative of the paper's figure-trend and order of
magnitude only**. They are NOT pixel-perfect and the absolute scale
matches the paper axis ticks. The compact model will be fitted to these
points.

## What is NOT trusted

* Absolute Id at the off-current end (10^-14 A is the axis floor; the
  paper does not give an off-current number in the text).
* Sub-threshold slope steepness beyond the visible resolution.
* Drain-induced barrier lowering / channel-length modulation.
* The Id-Vd curves' Vdsat knee.
* Mobility extracted from this fit will not match a calibrated compact
  model — it is a paper-anchored surrogate.
