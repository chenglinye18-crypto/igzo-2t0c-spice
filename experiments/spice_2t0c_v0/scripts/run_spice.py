"""
run_spice.py
=============

Wrapper around ngspice for the v0 sandbox. Handles:

* Building small parametric .sp files at runtime (different Vd / Vg
  values that the static .sp files in netlists/ use as templates).
* Invoking ngspice via cmd.exe (PowerShell piping into ngspice hangs
  the I/O on this machine; cmd /c with -b flag is reliable).
* Parsing the ASCII log output and emitting tidy CSVs in results/.

Usage examples
--------------
    python scripts/run_spice.py dc_idvg
    python scripts/run_spice.py dc_idvd
    python scripts/run_spice.py write0
    python scripts/run_spice.py write1
    python scripts/run_spice.py read0
    python scripts/run_spice.py read1
"""
from __future__ import annotations
import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NETLISTS = ROOT / "netlists"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

NGSPICE = Path(r"D:\Spice64\bin\ngspice_con.exe")


def run_spice_text(cir_text: str, workdir: Path) -> str:
    """Write cir_text to workdir/test.cir, run ngspice -b, return log text."""
    cir_path = workdir / "test.cir"
    cir_path.write_text(cir_text, encoding="utf-8")
    log_path = workdir / "test.log"
    if log_path.exists():
        log_path.unlink()
    # Use a small batch file to avoid PowerShell quoting issues.
    bat_path = workdir / "run.bat"
    bat_path.write_text(
        f'@echo off\r\n"{NGSPICE}" -b -o "test.log" "test.cir"\r\nif errorlevel 1 echo NGSPICE_FAILED > ngspice_err.txt\r\n',
        encoding="utf-8",
    )
    try:
        proc = subprocess.run(
            ["cmd", "/c", "run.bat"],
            cwd=str(workdir), capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired as e:
        sys.stderr.write(f"ngspice timeout in {workdir}\n")
        return ""
    err_marker = workdir / "ngspice_err.txt"
    if err_marker.exists():
        sys.stderr.write(f"ngspice error in {workdir}\n")
        # Print first 500 chars of the (non-existent) log
        if log_path.exists():
            sys.stderr.write(log_path.read_text(encoding="utf-8", errors="ignore")[:2000] + "\n")
        return ""
    return log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""


def parse_dc_log(log_text: str, vec_name: str, ncols_expected: int = 2) -> list[list[str]]:
    """Parse ngspice ASCII .print output.

    The .print dc line produces a table like:
        Index   v-sweep     v(d)         i(vd)
        0       0.000e+00   0.000e+00    0.000e+00
        ...
    The columns we want: the v-sweep value (col 1) and the vector named
    vec_name (col 2 in the .print line).
    """
    rows = []
    in_table = False
    header = None
    for line in log_text.splitlines():
        if "Index" in line and "v-sweep" in line:
            in_table = True
            header = line.split()
            continue
        if in_table:
            parts = line.split()
            if not parts:
                in_table = False
                continue
            if len(parts) < ncols_expected + 2:
                continue
            try:
                float(parts[0])
            except ValueError:
                in_table = False
                continue
            rows.append(parts)
    return rows


def cmd_dc_idvg() -> None:
    """Two Vd values: 0.1 V and 1 V. Output: idvg_sim.csv."""
    out_csv = RESULTS / "idvg_sim.csv"
    out_rows = []
    for vd in (0.1, 1.0):
        cir = f"""* Auto-generated Id-Vg at Vd={vd} V
.include igzo_2t0c_v0.lib
Vd D 0 {vd}
Vg G 0 0
X1 D G 0 XOSFET_DC
.dc Vg -1 2 0.05
.print dc v(g) i(vd)
.end
"""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            shutil.copy(ROOT / "models" / "igzo_2t0c_v0.lib", tdp / "igzo_2t0c_v0.lib")
            log = run_spice_text(cir, tdp)
        if not log:
            print(f"  Vd={vd} V: no log produced")
            continue
        rows = parse_dc_log(log, "i(vd)", ncols_expected=2)
        if not rows:
            print(f"  Vd={vd} V: no rows parsed from log")
            continue
        for r in rows:
            vg = float(r[1])
            id_a = float(r[3])
            out_rows.append((vg, vd, id_a))
    # Sort by Vg, then Vd
    out_rows.sort()
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Vg_V", "Vd_V", "Id_A"])
        for vg, vd, ida in out_rows:
            w.writerow([f"{vg:.6e}", f"{vd:.6e}", f"{ida:.6e}"])
    print(f"  -> {out_csv}  ({len(out_rows)} rows)")


def cmd_dc_idvd() -> None:
    """Three Vg values: 0.4, 1.2, 2.0 V. Output: idvd_sim.csv."""
    out_csv = RESULTS / "idvd_sim.csv"
    out_rows = []
    for vg in (0.4, 1.2, 2.0):
        cir = f"""* Auto-generated Id-Vd at Vg={vg} V
.include igzo_2t0c_v0.lib
Vd D 0 0
Vg G 0 {vg}
X1 D G 0 XOSFET_DC
.dc Vd 0 3 0.1
.print dc v(d) i(vd)
.end
"""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            shutil.copy(ROOT / "models" / "igzo_2t0c_v0.lib", tdp / "igzo_2t0c_v0.lib")
            log = run_spice_text(cir, tdp)
        if not log:
            print(f"  Vg={vg} V: no log produced")
            continue
        rows = parse_dc_log(log, "i(vd)", ncols_expected=2)
        if not rows:
            print(f"  Vg={vg} V: no rows parsed from log")
            continue
        for r in rows:
            vd = float(r[1])
            id_a = float(r[3])
            out_rows.append((vd, vg, id_a))
    out_rows.sort()
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Vd_V", "Vg_V", "Id_A"])
        for vd, vg, ida in out_rows:
            w.writerow([f"{vd:.6e}", f"{vg:.6e}", f"{ida:.6e}"])
    print(f"  -> {out_csv}  ({len(out_rows)} rows)")


def cmd_transient(name: str) -> None:
    """Run a transient netlist from netlists/<name>.sp."""
    sp_path = NETLISTS / f"{name}.sp"
    if not sp_path.exists():
        print(f"  netlist not found: {sp_path}")
        return
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # Copy the model files alongside
        for m in ("igzo_2t0c_v0.lib", "zhu_2t0c_parasitics.inc",
                  "cell_2t0c.inc", "sense_stub.inc"):
            src = ROOT / "models" / m
            if src.exists():
                shutil.copy(src, tdp / m)
        # Rewrite includes to be local
        cir_text = sp_path.read_text(encoding="utf-8")
        cir_text = cir_text.replace("../models/", "")
        log = run_spice_text(cir_text, tdp)
        if not log:
            print(f"  no log produced for {name}")
            return
        # Save the raw log
        out_log = RESULTS / f"{name}.log"
        out_log.write_text(log, encoding="utf-8")
        print(f"  -> {out_log}")
        # Parse the .print tran table
        out_csv = RESULTS / f"{name}.csv"
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["# raw tran data -- see " + name + ".log for the full ngspice output"])
            in_table = False
            for line in log.splitlines():
                if "Index" in line and ("time" in line.lower() or "t-sweep" in line.lower() or "v-sweep" in line.lower()):
                    in_table = True
                    w.writerow(line.split())
                    continue
                if in_table:
                    parts = line.split()
                    if not parts:
                        in_table = False
                        continue
                    try:
                        float(parts[0])
                    except ValueError:
                        in_table = False
                        continue
                    w.writerow(parts)
        print(f"  -> {out_csv}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=[
        "dc_idvg", "dc_idvd",
        "write0", "write1", "read0", "read1",
    ])
    args = ap.parse_args()
    if args.which == "dc_idvg":
        cmd_dc_idvg()
    elif args.which == "dc_idvd":
        cmd_dc_idvd()
    else:
        cmd_transient(args.which)


if __name__ == "__main__":
    main()
