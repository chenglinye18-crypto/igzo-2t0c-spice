# experiments/spice_2t0c_v0

A first SPICE sandbox for the Zhu 2T0C (IEDM 2026).

## Goal

Stand up a single-cell, single-transient, fixed-bias SPICE flow for
the Zhu 2T0C DRAM cell.  The cell uses a **paper-anchored BEHAVIORAL
SURROGATE** for the OSFET device (NOT the paper's full surface-
potential compact model), a **lumped** parasitic network (not the
512x512 distributed network), and a **functional** sense stub (not
a calibrated Si-MOS CSA).

This is a v0.  It is expected to be orders-of-magnitude off from
Zhu Table I; that is documented and called out everywhere.

## What is here

```
experiments/spice_2t0c_v0/
  reference_notes.md          - paper parameters + UNRESOLVED audit
  UNRESOLVED.md               - what v0 could NOT resolve
  README.md                   - this file
  data/
    idvg.csv                  - hand-digitized Fig 5(d) (2T0C Id-Vg)
    idvd.csv                  - hand-digitized Fig 5(e) (2T0C Id-Vd)
    DIGITIZATION_NOTES.md     - how the CSVs were produced
    *.png                     - the cropped figure images used to read
                               the curves
  models/
    igzo_2t0c_v0.lib          - SPICE subcircuit for the surrogate
                               2T0C OSFET (B-source based)
    zhu_2t0c_parasitics.inc   - paper Fig 4(b) unit-cell R/C values
    cell_2t0c.inc             - 5-port single-cell (WWL WBL RWL
                               RBL SN) subcircuit with parasitic
                               coupling caps
    sense_stub.inc            - v0 sense parameters (FUNCTIONAL
                               STUB, NOT calibrated FEOL SA)
  netlists/
    dc_idvg.sp                - Id-Vg sweep at Vd = 0.1 V and 1 V
    dc_idvd.sp                - Id-Vd sweep at Vg = 0.4, 1.2, 2.0 V
    write0.sp                 - write 0 transient
    write1.sp                 - write 1 transient
    read0.sp                  - read 0 transient (write0+read in one)
    read1.sp                  - read 1 transient (write1+read in one)
  scripts/
    extract_iv_curves.py      - hue-based digitizer for Fig 5
    fit_device.py             - fits the surrogate model, emits the lib
    run_spice.py              - ngspice wrapper (uses ngspice_con)
    integrate_energy.py       - operation energy integrator
  results/
    idvg_sim.csv              - DC Id-Vg sim
    idvd_sim.csv              - DC Id-Vd sim
    idvg_idvd_fit.png         - fit vs paper overlay
    fit_report.json           - fitted parameters + RMSE
    write0.log / .csv         - write 0 transient log + parsed table
    write1.log / .csv
    read0.log / .csv
    read1.log / .csv
    operation_energy.json     - final integrated energies
```

## How to run

The sandbox is self-contained.  From the project root:

```bash
# 1. fit the device model and emit the .lib
python experiments/spice_2t0c_v0/scripts/fit_device.py

# 2. DC validation
python experiments/spice_2t0c_v0/scripts/run_spice.py dc_idvg
python experiments/spice_2t0c_v0/scripts/run_spice.py dc_idvd

# 3. transients
python experiments/spice_2t0c_v0/scripts/run_spice.py write0
python experiments/spice_2t0c_v0/scripts/run_spice.py write1
python experiments/spice_2t0c_v0/scripts/run_spice.py read0
python experiments/spice_2t0c_v0/scripts/run_spice.py read1

# 4. integrate energies
python experiments/spice_2t0c_v0/scripts/integrate_energy.py
```

## ngspice notes (this machine)

* `ngspice.exe` (D:\Spice64\bin\ngspice.exe) is the GUI version.  When
  SPICE errors, it raises a Windows popup and stalls.  We do NOT use
  it.
* `ngspice_con.exe` (D:\Spice64\bin\ngspice_con.exe) is the console
  version.  Used in batch mode (`-b`).
* PowerShell's native I/O pipes into ngspice hang.  The Python
  wrapper invokes ngspice via a .bat file written into a temp dir,
  invoked by `cmd /c run.bat`.

## What the v0 IS

* A working single-cell 2T0C SPICE flow.
* An ngspice-compatible surrogate device model with the right
  orders of magnitude.
* A 5-port cell subcircuit with WWL/WBL/RWL/RBL line R and SN
  coupling caps.
* A write0 / write1 / read0 / read1 transient flow.
* A working energy integrator.
* A sense stub that distinguishes stored 0 vs stored 1 (V(RBL)
  threshold crossing).

## What the v0 is NOT

* A faithful reproduction of Zhu's compact model.
* A calibrated Si-MOS sense amplifier.
* A 512x512 distributed network.
* A thermal or BTI simulation.
* A workload-aware power simulation.

## Next step

The next iteration should:
1. Replace the surrogate B-source with a Verilog-A version of Zhu's
   surface-potential model (calibrated to Fig 5(d,e)).
2. Add a transistor-level CSA (with at least rough Si-MOS sizes
   scaled to 28 nm or 14 nm).
3. Build a 4x4 (or larger) distributed RC network to verify the
   2T0C's read-margin degradation at the array edge.
4. Add BTI aging (state-based, like Zhu's) and check the hold-"1"
   BTI degradation of T_w.
