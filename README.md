# RPM File Size Comparator

A Python utility to compare file sizes inside two RPM packages built for different architectures.

## 📦 Purpose

This tool helps identify differences in file sizes between two RPM packages compiled for different target architectures — for example, ARM vs RISC-V. It is useful for analyzing how architectural differences affect binary size and disk usage.

## 🔧 Features

- Takes two `.rpm` package file paths as input.
- Extracts and lists file sizes from each package.
- Outputs a comparison table with:
  - File paths
  - Size in Package A
  - Size in Package B
  - Size difference in bytes and percentage
- Optionally save the table to a CSV file using the `--csv` flag

## 🧠 Use Case

Use this tool to analyze size regressions or improvements when recompiling the same package for different platforms.

## 🛠️ Example

```bash
python compare_rpm_sizes.py ./package-arm.rpm ./package-riscv.rpm --csv
```

## Requirements

Python 3. Install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```
