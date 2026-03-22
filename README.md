# RPM File Size Comparator

A Python utility to compare file sizes inside two RPM packages built for different architectures.

## 📦 Purpose

This tool helps identify differences in file sizes between two RPM packages compiled for different target architectures — for example, ARM vs RISC-V. It is useful for analyzing how architectural differences affect binary size and disk usage, both locally and in CI pipelines.

## 🔧 Features

- Takes two `.rpm` package files as input (reference vs. comparison)
- Outputs a comparison table with:
  - File paths
  - Size in Package A (KB)
  - Size in Package B (KB)
  - Size difference in KB and percentage (shows `N/A` for zero-size files)
  - File type detected via libmagic for each package
- Flags files unique to one package as `-removed` or `+new`
- Prints a `TOTAL` summary row at the bottom
- Exits with a clear error message for missing or invalid RPM files
- `--csv` — save results to a semicolon-delimited CSV file
- `--json` — output structured JSON instead of the ASCII table (CSV can coexist)
- `--quiet` — suppress per-file rows, print only the TOTAL line
- `--fail-threshold N` — exit 1 if RPM B total size grew more than N% vs RPM A
- `--64` — normalize `/lib*` and `/usr/lib*` paths when comparing 32-bit vs 64-bit packages
- `--hide-equal` — hide files with identical sizes
- `--ignore-versions` — remove version suffixes from `.so` filenames
- `--ignore-links` — skip symbolic links

## 🧠 Use Case

Use this tool to detect size regressions when recompiling a package for a different architecture, or to automatically fail a CI pipeline when a release grows beyond an acceptable threshold.

## 🛠️ Usage

```bash
# Basic comparison
./cmp-rpm ./package-a.rpm ./package-b.rpm

# Save to CSV, normalize 64-bit lib paths
./cmp-rpm ./package-32bit.rpm ./package-64bit.rpm --64 --csv

# CI mode: fail if B is more than 5% larger than A
./cmp-rpm ./old.rpm ./new.rpm --fail-threshold 5

# Machine-readable JSON output
./cmp-rpm ./old.rpm ./new.rpm --json

# Quiet + threshold: minimal output, non-zero exit on regression
./cmp-rpm ./old.rpm ./new.rpm --quiet --fail-threshold 10
```

### Example table output

```
File                                                Size A (KB)  Size B (KB)    Diff (KB)   Diff % Type A     Type B
./usr/bin/busybox                                      1282.60      1086.64      -195.96  -15.28% ELF        ELF
./usr/share/licenses/busybox/LICENSE                     17.92        17.92         0.00    0.00% ASCII text ASCII text
./usr/bin/only_in_a                                       4.00          ---          ---  -removed ELF        ---
./usr/bin/only_in_b                                        ---         8.00          ---      +new ---        ELF
TOTAL                                                  1351.64      1155.68      -195.96  -14.50%
```

### Example JSON output (`--json`)

```json
{
  "summary": {
    "total_a_kb": 1351.64,
    "total_b_kb": 1155.68,
    "diff_kb": -195.96,
    "diff_pct": -14.5
  },
  "files": [
    {
      "name": "./usr/bin/busybox",
      "size_a_kb": 1282.60,
      "size_b_kb": 1086.64,
      "diff_kb": -195.96,
      "diff_pct": -15.28,
      "type_a": "ELF",
      "type_b": "ELF",
      "status": "changed"
    }
  ]
}
```

## 🤖 GitHub Actions

```yaml
- name: Install cmp-rpm
  run: bash install.sh

- name: Compare RPM sizes
  run: |
    ./cmp-rpm old.rpm new.rpm \
      --json --csv report.csv \
      --fail-threshold 5
```

- Exits **0** if size growth ≤ 5% → workflow passes
- Exits **1** if size growth > 5% → workflow fails with a clear message on stderr
- `report.csv` can be uploaded as an artifact for review

## Requirements

- Python 3.10+
- `libmagic` system library (installed automatically by `install.sh`)

## Installation

```bash
bash install.sh
```

The script:
1. Checks Python 3.10+ is available
2. Installs `libmagic` via `brew` / `apt` / `dnf` / `zypper` if missing (sudo-aware: skips `sudo` when running as root)
3. Creates a `venv/` virtual environment
4. Installs all Python dependencies from `requirements.txt`
5. Runs a smoke test to confirm everything works

Then run the tool:

```bash
# No activation needed — wrapper handles the venv
./cmp-rpm <rpm_a> <rpm_b>

# Or activate manually
source venv/bin/activate
python compare_rpm_sizes.py <rpm_a> <rpm_b>
```
