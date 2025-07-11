# RPM File Size Comparator

A Python utility to compare file sizes inside two RPM packages built for different architectures.

## 📦 Purpose

This tool helps identify differences in file sizes between two RPM packages compiled for different target architectures — for example, ARM vs RISC-V. It is useful for analyzing how architectural differences affect binary size and disk usage.

## 🔧 Features

- Takes two `.rpm` package file paths as input.
- Extracts and lists file sizes from each package.
- Outputs a comparison table with:
  - File paths
  - Size in Package A (KB)
  - Size in Package B (KB)
  - Size difference in KB and percentage
  - File type detected via libmagic for each package
- Optionally save the table to a CSV file using the `--csv` flag
  (semicolon `;` delimited)
- Use `--64` to normalize `/lib*` and `/usr/lib*` paths when comparing 32-bit and 64-bit packages
- Hide files with the same size using `--hide-equal`
- Remove version suffixes from `.so` files with `--ignore-versions`
- Skip symbolic links with `--ignore-links`

## 🧠 Use Case

Use this tool to analyze size regressions or improvements when recompiling the same package for different platforms.

## 🛠️ Example

```bash
python compare_rpm_sizes.py ./package-32bit.rpm ./package-64bit.rpm --64 --csv
```

## Requirements

Python 3. Install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```
