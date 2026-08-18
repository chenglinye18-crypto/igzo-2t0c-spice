"""
integrate_energy.py
====================

Compute the operation energy for the v0 2T0C cell from the ngspice
transient logs.  Two accounting modes are reported for read:

    A. cell_and_RC_only
       E = integral over the operation window of:
         V(VVVDD) * I(V_DD)              <- VDD current for cell+RC
       This counts the energy delivered to the cell + the parasitic
       RC network, but NOT the sense amplifier.

    B. cell_RC_plus_sense_stub
       E = integral of V_DD * I(V_DD)   <- the same supply source, but
         we add the always-on sense-stub bias as an explicit term:
         E_sense = V_SA_HI * I_BIAS_SA * T_SENSE
       (the v0 sense stub is behavioral; the supply current i(v_dd)
        in our netlists already includes the sense comparator load
        because the comparator is powered from VDD.)

For v0, since the comparator is a behavioral voltage source fed from
VDD, the i(v_dd) current already includes the sense energy.  So mode
A and mode B are the SAME for v0 -- we still report both for
documentation of the protocol.

The integration bounds are:
    write: t in [t_write_start, t_write_end]
    read:  t in [t_read_start,  t_read_end]

The bounds are read from a small header in the .log file (the first
.Index  time. row) or fall back to a hard-coded default.
"""
from __future__ import annotations
import csv
import json
import math
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

PAPER_TABLE = {
    # Zhu Table I for 2T0C
    "write00": 0.30,
    "write01": 0.37,
    "write10": 0.58,
    "write11": 0.24,
    "read0":   0.60,
    "read1":   368.0,
    "refresh0": 0.90,
    "refresh1": 370.0,
    "P_hold_W_per_row": 4.26e-15,
}


def parse_tran_log(path: Path):
    """Return a dict of (vec_name -> [(time, value), ...]) for all .print columns.

    ngspice prints a table whose header is 'Index time v(x) v(y) ...' and
    each row is 'I time v(x) v(y) ...'.  We just parse all numeric rows
    after the header.
    """
    if not path.exists():
        return None
    txt = path.read_text(encoding="utf-8", errors="ignore")
    # Find all tables
    tables = []
    lines = txt.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Header line starts with 'Index' and has many columns
        if line.startswith("Index") and "time" in line.lower():
            header = line.split()
            # next line is the separator
            j = i + 2
            rows = []
            while j < len(lines):
                parts = lines[j].split()
                if not parts:
                    j += 1
                    continue
                try:
                    [float(p) for p in parts]
                except ValueError:
                    break
                rows.append(parts)
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


def merge_tables_by_time(tables):
    """Build a single dict {col_name: [(time, value), ...]} from all tables,
    matched by time.  Different tables may have different sample points; we
    interpolate to the union of all time points.
    """
    col_data = {}  # col_name -> {t: v}
    times_set = set()
    for header, rows in tables:
        h = [c.lower() for c in header]
        # find 'time' column
        t_idx = None
        for k, c in enumerate(h):
            if c == "time":
                t_idx = k
                break
        if t_idx is None:
            continue
        for k, c in enumerate(h):
            if k == t_idx:
                continue
            if c not in col_data:
                col_data[c] = {}
            for r in rows:
                if len(r) <= max(t_idx, k):
                    continue
                try:
                    t = float(r[t_idx])
                    v = float(r[k])
                except (ValueError, IndexError):
                    continue
                col_data[c][t] = v
                times_set.add(t)
    times = sorted(times_set)
    # For each column, interpolate to all times
    merged = {}
    for col, t_v in col_data.items():
        sorted_t = sorted(t_v.keys())
        sorted_v = [t_v[t] for t in sorted_t]
        merged[col] = [(t, _interp(sorted_t, sorted_v, t)) for t in times]
    return merged, times


def _interp(xs, ys, x):
    """Linear interpolation; xs is sorted ascending."""
    import bisect
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect.bisect_right(xs, x)
    x0, x1 = xs[i - 1], xs[i]
    y0, y1 = ys[i - 1], ys[i]
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def compute_energy(name: str, tables):
    """Compute E = integral V(vdd) * I(v_dd) dt for the given log.

    Strategy: assume the v0 netlist's last .print block contains
    columns `i(v_DD)` or `v_dd#branch`.  Sum V * I * dt over all rows.
    """
    # Find the table that has both v(vdd) (or v_dd#branch) and i(v_dd)
    # ngspice prints currents as 'i(v_xxx)' for sources; for VDD the
    # current through VDD source is 'v_dd#branch' (we used V_DD in netlist).
    for header, rows in tables:
        h = [c.lower() for c in header]
        v_idx = None
        i_idx = None
        # Find voltage of VDD node
        for k, c in enumerate(h):
            if c == "v(vdd)":
                v_idx = k
        # Find current through VDD source
        for k, c in enumerate(h):
            if "v_dd" in c and "branch" in c:
                i_idx = k
        if v_idx is not None and i_idx is not None:
            # Compute integral
            E = 0.0
            t_prev = None
            v_prev = None
            i_prev = None
            for r in rows:
                if len(r) <= max(v_idx, i_idx):
                    continue
                try:
                    t = float(r[1])  # 'time' is column 1 in the .print table
                    v = float(r[v_idx])
                    i = float(r[i_idx])
                except (ValueError, IndexError):
                    continue
                if t_prev is not None:
                    dt = t - t_prev
                    E += 0.5 * (v * i + v_prev * i_prev) * dt
                t_prev, v_prev, i_prev = t, v, i
            return E
    return None


def compute_vdd_current_for_window(tables, t_start, t_end):
    """Sum I(V_DD) over [t_start, t_end] in all tables."""
    out = 0.0
    for header, rows in tables:
        h = [c.lower() for c in header]
        i_idx = None
        for k, c in enumerate(h):
            if "v_dd" in c and "branch" in c:
                i_idx = k
        if i_idx is None:
            continue
        for r in rows:
            if len(r) <= i_idx:
                continue
            try:
                t = float(r[1])
                i = float(r[i_idx])
            except (ValueError, IndexError):
                continue
            if t_start <= t <= t_end:
                out += i
    return out


def find_write_read_windows(tables):
    """Try to detect write and read windows from a PWL-like inspection.

    v0: write window is t in [1ns, 11ns] (WWL pulse); read window is
    t in [15ns, 20ns] (RWL pulse).  We hard-code these for v0.
    """
    return {
        "write": (1.0e-9, 11.0e-9),
        "read":  (15.0e-9, 20.0e-9),
    }


def main():
    out = {
        "schema": {
            "version": "v0",
            "note": "Single 2T0C cell, lumped parasitics, surrogate device model, "
                    "functional sense stub.  See reference_notes.md and the final report.",
            "units_E": "J (Joules)",
            "units_P": "W (Watts)",
        },
        "operations": {},
        "paper_table_I_comparison": {
            "read0":  PAPER_TABLE["read0"] * 1e-15,
            "read1":  PAPER_TABLE["read1"] * 1e-15,
            "write00": PAPER_TABLE["write00"] * 1e-15,
            "write01": PAPER_TABLE["write01"] * 1e-15,
            "write10": PAPER_TABLE["write10"] * 1e-15,
            "write11": PAPER_TABLE["write11"] * 1e-15,
            "P_hold_W_per_row": PAPER_TABLE["P_hold_W_per_row"],
        },
        "caveats": [
            "All operation energies are integrated from the ngspice transient of a single 2T0C cell.",
            "The surrogate OSFET model is a non-physical behavioral B-source fitted to a hand-digitized subset of Zhu Fig 5(d,e).  The Id-Vg fit has log10 RMSE ~1 decade; Id-Vd rel RMSE ~0.5.",
            "WWL/WBL/RWL/RBL line resistances are taken from Fig 4(b) of the paper (a few ohms per cell).",
            "Storage-node intrinsic C is a v0 MODELING_CHOICE of 1 fF (paper does not publish a 2T0C intrinsic C).",
            "The sense amplifier is a functional behavioral stub, NOT a calibrated Si-MOS CSA.  Read energy includes the stub bias.",
            "No 512x512 distributed network, no BTI, no thermal, no aging, no workload -- this is a single-cell, fixed-bias, single-transient sandbox.",
        ],
    }

    for name in ("write0", "write1", "read0", "read1"):
        log = RESULTS / f"{name}.log"
        tables = parse_tran_log(log)
        if not tables:
            out["operations"][name] = {"error": "no log"}
            continue
        # Merge by time
        merged, times = merge_tables_by_time(tables)
        # Find v_dd#branch and v(vdd)
        i_vdd = None
        v_vdd = None
        for col in merged:
            if "v_dd" in col and "branch" in col:
                i_vdd = col
            if col == "v(vdd)":
                v_vdd = col
        if i_vdd is None or v_vdd is None:
            out["operations"][name] = {
                "error": f"missing columns: i_vdd={i_vdd} v_vdd={v_vdd} cols={list(merged.keys())}",
            }
            continue
        # Compute window
        if name.startswith("write"):
            t_start, t_end = 1.0e-9, 11.0e-9
        else:
            t_start, t_end = 15.0e-9, 20.0e-9
        # Build aligned arrays on the time grid
        i_data = dict(merged[i_vdd])
        v_data = dict(merged[v_vdd])
        times_in = [t for t in times if t_start <= t <= t_end]
        if not times_in:
            out["operations"][name] = {"error": "no samples in window"}
            continue
        E = 0.0
        for k in range(1, len(times_in)):
            t0, t1 = times_in[k - 1], times_in[k]
            dt = t1 - t0
            v0 = v_data.get(t0, 0.0)
            v1 = v_data.get(t1, 0.0)
            i0 = i_data.get(t0, 0.0)
            i1 = i_data.get(t1, 0.0)
            E += 0.5 * (v0 * i0 + v1 * i1) * dt
        # Also compute total E (full transient)
        E_total = 0.0
        for k in range(1, len(times)):
            t0, t1 = times[k - 1], times[k]
            dt = t1 - t0
            v0 = v_data.get(t0, 0.0)
            v1 = v_data.get(t1, 0.0)
            i0 = i_data.get(t0, 0.0)
            i1 = i_data.get(t1, 0.0)
            E_total += 0.5 * (v0 * i0 + v1 * i1) * dt
        out["operations"][name] = {
            "E_window_J": E,
            "E_total_J": E_total,
            "window_s": [t_start, t_end],
        }
    # For reads, split into cell+RC vs cell+RC+SA
    for name in ("read0", "read1"):
        op = out["operations"].get(name, {})
        E = op.get("E_window_J")
        if E is None:
            continue
        op["E_cell_and_RC_J"] = E
        op["E_with_sense_stub_J"] = E
    # Convert to fJ for readability
    for name in list(out["operations"].keys()):
        op = out["operations"][name]
        for k, v in list(op.items()):
            if k.endswith("_J") and isinstance(v, (int, float)):
                op[k.replace("_J", "_fJ")] = v * 1e15
    out_path = RESULTS / "operation_energy.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"  -> {out_path}")
    print()
    print("Operation energies (fJ):")
    for name in ("write0", "write1", "read0", "read1"):
        op = out["operations"].get(name, {})
        if "error" in op:
            print(f"  {name:6s}: {op['error']}")
            continue
        E = op.get("E_window_fJ", float("nan"))
        print(f"  {name:6s}: E_window = {E:12.3f} fJ  (V_DD integral over {op.get('window_s')} s)")


if __name__ == "__main__":
    main()
