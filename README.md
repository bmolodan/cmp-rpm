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
  - Size difference in KB and percentage (shows `N/A` for zero-size files)
  - File type detected via libmagic for each package
- Flags files unique to one package as `-removed` or `+new`
- Prints a `TOTAL` summary row at the bottom
- Exits with a clear error message for missing or invalid RPM files
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

Example output:

```
File                                                 Size A (KB)  Size B (KB)    Diff (KB)   Diff % Type A     Type B
./usr/bin/busybox                                       1282.60      1086.64      -195.96  -15.28% ELF 64...  ELF 64...
./usr/share/licenses/busybox/LICENSE                      17.91        17.91         0.00    0.00% ASCII t... ASCII t...
./usr/bin/only_in_a                                        4.00          ---          ---  -removed ELF 64...  ---
./usr/bin/only_in_b                                         ---         8.00          ---      +new ---        ELF 64...
TOTAL                                                   1351.64      1155.68      -195.96  -14.50%
```

## Requirements

Python 3. Install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```
