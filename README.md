# RPM File Size Comparator

A Python utility for comparing file sizes within two RPM packages built for different architectures.

## 📦 Purpose

This tool helps developers and maintainers identify differences in file sizes between two RPM packages compiled for different target architectures — for example, ARM vs RISC-V. It is especially useful for analyzing how architectural differences affect binary size and disk usage.

## 🔧 Features

- Takes two `.rpm` package file paths as input.
- Extracts and lists file sizes from each package.
- Outputs a comparison table with:
  - File paths
  - Size in Package A
  - Size in Package B
  - Size difference (in bytes and percentage)

## 🧠 Use Case

Typical use case: analyzing size regressions or improvements when recompiling the same package for different platforms.

## 🛠️ Example

```bash
python compare_rpm_sizes.py ./package-arm.rpm ./package-riscv.rpm
