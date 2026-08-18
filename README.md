# MATspice — OSFET 2T0C SPICE Sandbox

A first-pass SPICE sandbox for the OSFET 2T0C (2-Transistor 0-Capacitor)
DRAM cell from **Zhu et al., IEDM 2026**:

> Haotong Zhu, Chenglin Ye, Lianliang Wu, Yongjia Wang, Ao Shi,
> Zheng Zhou, Xiaoyan Liu, Jinfeng Kang.
> *From Cell Metrics to Memory-Array-Tile Operability: DTCO of
> OSFET-Based 3D DRAM.* IEDM 2026.

This repository hosts a paper-anchored **single-cell, single-transient,
fixed-bias** SPICE flow that goes from the paper's I-V curves to a
functional write0 / write1 / read0 / read1 transient with operation-
energy integration. The sandbox is intended as a starting point for
research on IGZO 2T0C DRAM; it is **not** a reproduction of the
paper's final numbers and **not** intended to compete with the
paper's full TCAD-calibrated compact model.

## Scope of v0

* Single 2T0C cell, lumped unit-cell parasitics, fixed bias.
* A **behavioural surrogate** IGZO TFT model (a single B-source
  expression fitted to a hand-digitized subset of the paper's
  Fig. 5(d,e)).
* A **functional** sense amplifier stub — NOT a calibrated Si-MOS CSA.
* No 512x512 distributed RC, no BTI, no thermal, no aging, no
  workload, no TCAD.

See `experiments/spice_2t0c_v0/FINAL_REPORT.md` for the full
audit (parameters, fit errors, operation energies, gaps to the
paper) and `experiments/spice_2t0c_v0/UNRESOLVED.md` for the
list of things the v0 sandbox could NOT resolve.

## Repository layout

```
.
├── LICENSE                    MIT License
├── README.md                  (this file)
├── .gitignore
└── experiments/
    └── spice_2t0c_v0/        the v0 sandbox
        ├── README.md          sandbox-level readme
        ├── reference_notes.md  paper parameters + audit
        ├── UNRESOLVED.md      hard + soft UNRESOLVED list
        ├── FINAL_REPORT.md    results, errors, gaps, status
        ├── data/              hand-digitized Fig. 5 I-V data
        ├── models/            .lib / .inc SPICE subcircuits
        ├── netlists/          DC + transient .sp files
        ├── scripts/           Python tooling (fit, run, integrate)
        └── results/           DC + transient outputs, energy JSON
```

## Quick start

Requires `ngspice` (tested with ngspice-43 on Windows). Python 3.10+
with `numpy`, `scipy`, `matplotlib`.

```bash
cd MATspice
python experiments/spice_2t0c_v0/scripts/fit_device.py
python experiments/spice_2t0c_v0/scripts/run_spice.py dc_idvg
python experiments/spice_2t0c_v0/scripts/run_spice.py dc_idvd
python experiments/spice_2t0c_v0/scripts/run_spice.py write0
python experiments/spice_2t0c_v0/scripts/run_spice.py write1
python experiments/spice_2t0c_v0/scripts/run_spice.py read0
python experiments/spice_2t0c_v0/scripts/run_spice.py read1
python experiments/spice_2t0c_v0/scripts/integrate_energy.py
```

All outputs land in `experiments/spice_2t0c_v0/results/`.

## Citation

If you use this sandbox, please cite the original paper:

```bibtex
@inproceedings{zhu2026osfet3ddram,
  title  = {From Cell Metrics to Memory-Array-Tile Operability:
            DTCO of OSFET-Based 3D DRAM},
  author = {Zhu, Haotong and Ye, Chenglin and Wu, Lianliang and
            Wang, Yongjia and Shi, Ao and Zhou, Zheng and
            Liu, Xiaoyan and Kang, Jinfeng},
  booktitle = {IEDM},
  year   = {2026}
}
```

## License

MIT — see `LICENSE`.

## Acknowledgements

Developed as a starting point for OSFET 2T0C SPICE exploration.
The surrogate device model, parasitic values, and energy integration
pipeline are all designed to be replaced or extended as the
research progresses; nothing in v0 is intended to be the final form.
