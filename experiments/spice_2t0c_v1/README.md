# Zhu 2T0C IEDM 2026 — physics-based compact model v1

**Scope (frozen):** Id–Vg / Id–Vd DC validation only. NO transient, write/read,
operation energy, parasitic RC, sense amp, array, or thermal.

**What this is:** A paper-anchored physics-based compact model for the 2T0C
OSFET described in Zhu IEDM 2026. The equations come from two sources:

1. **Zhu IEDM 2026** (`ref/IEDM2026_HaotongZhu_V5.pdf`) — surface potential
   (Eq. 5), drain current (Eq. 6), mobility (Eq. 7).
2. **SCE EDTM 2026** (`ref/Physical_Model_of_Intrinsic_Short-channel_Effects_for_Oxide_Thin-film_Transistors.pdf`) —
   off-state current (Eq. 9), DIBL functional form (Eq. 11).

The model is **paper-anchored, physics-based, CAA-adapted**, not the original
author's parameter deck. See `model_equations.md` for the full equation
audit and the explicit per-term provenance labels.

**Caveat:** the Zhu paper does **not** publish the calibrated parameter
values (N_D, N_V,j, μ_0, USR, E_USC, V_fb, ...). We use SCE paper Table I
values as the initial guess and **calibrate** the rest to match Fig. 5(d/e)
digitization. With one effective calibration parameter `K_pre` and one
calibration extension `n_power` (V_ov^n power law), the model is structurally
simpler than the original Zhu model but anchored to its equation forms.

## Layout

```
experiments/spice_2t0c_v1/
├── README.md               this file
├── model_equations.md      paper-anchored equation audit (v1 model definition)
├── UNRESOLVED.md           known issues / not-fully-resolved questions
├── data/
│   ├── idvg.csv            v1 digitization of Fig 5(d)  (25 points x 2 Vd)
│   ├── idvd.csv            v1 digitization of Fig 5(e)  (14 points x 3 Vg)
│   ├── DIGITIZATION_NOTES.md
│   ├── page3-3.png         Zhu paper p.3, 300 DPI
│   ├── fig5d_final.png     clean crop of Fig 5(d)
│   ├── fig5d_final_3x.png  3x upscale (for pixel-level digitization)
│   ├── fig5e_final.png     clean crop of Fig 5(e)
│   ├── fig5e_final_3x.png  3x upscale
├── models/
│   └── igzo_2t0c_v1.lib    ngspice B-source subcircuit
├── netlists/
│   ├── dc_idvg_v1.sp       Id-Vg DC sweep
│   └── dc_idvd_v1.sp       Id-Vd DC sweep
├── scripts/
│   ├── device_model_v1.py  Python reference model
│   ├── fit_device_v1.py    11-step staged calibration
│   └── run_spice_v1.py     ngspice DC sweep + Python/SPICE cross-check
└── results/
    ├── fit_report_v1.json        parameter values + residuals
    ├── iv_crosscheck.csv         cross-bias comparison
    ├── key_bias_validation.csv   key-bias errors
    ├── idvg_idvd_fit_v1.png      paper vs model overlay
    ├── spice_idvg.csv            SPICE Id-Vg (DC sweep)
    ├── spice_idvd.csv            SPICE Id-Vd (DC sweep)
    └── spice_python_crosscheck.csv  Python vs SPICE consistency
```

## Reproduce

```powershell
cd E:\BaiduSyncdisk\study\PAPER\DAC 2026\MATspice\experiments\spice_2t0c_v1
# 1. Calibrate
& 'C:\Users\Leslie\Miniconda3\python.exe' scripts\fit_device_v1.py
# 2. Run SPICE DC sweeps + cross-check
& 'C:\Users\Leslie\Miniconda3\python.exe' scripts\run_spice_v1.py
# 3. View results
explorer results\idvg_idvd_fit_v1.png
```

## Geometry (frozen, PAPER_REPORTED)

| parameter | value  | source                  |
|-----------|--------|-------------------------|
| L         | 55 nm  | Zhu Fig 5 caption       |
| CD        | 50 nm  | Zhu Fig 5 caption       |
| t_ch      | 3 nm   | t_IGZO, Zhu Fig 5 caption |
| t_ox      | 8 nm   | t_HfOx, Zhu Fig 5 caption |
| W_eff     | π·CD ≈ 157 nm | Zhu Fig 5 caption       |

## Status

* **I-V model**: implemented in Python + ngspice B-source. Self-consistent
  to < 1 % median (max 29 % at one subthreshold point).
* **I-V vs paper**: see `results/fit_report_v1.json` for residuals.
  Off-state and on-state roughly match; saturation knee and Id-Vd at low
  Vg have known issues documented in `UNRESOLVED.md`.
* **Cross-bias**: the paper's own Fig 5(d) and Fig 5(e) disagree at the
  shared bias point (Vg=2, Vd=1) by 2–3× — recorded in
  `data/DIGITIZATION_NOTES.md`; the model uses the Fig 5(d) saturated value
  in this region.
* **STOP**: per task scope, this v1 is frozen. No transient, write/read,
  operation energy, array, BTI, or thermal work follows.
