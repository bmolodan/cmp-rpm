from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections.abc import Callable
from contextlib import nullcontext
from typing import NamedTuple

import magic
import rpmfile
from rpmfile.errors import RPMError

# Column widths for the console table
COL_NAME = 50
COL_SIZE = 12
COL_DIFF = 12
COL_PCT  = 8
COL_TYPE = 10
ABSENT   = "---"

# Type alias for the dict returned by extract_info
FileInfo = dict[str, tuple[int, str]]

_magic = magic.Magic(mime=False)


class FileRow(NamedTuple):
    name:   str
    size_a: int | None
    type_a: str | None
    size_b: int | None
    type_b: str | None


def detect_file_type(data: bytes) -> str:
    """Identify the file type using libmagic."""
    if not data:
        return "empty"
    try:
        return _magic.from_buffer(data)
    except Exception:
        return "unknown"


def normalize_lib_paths(path: str) -> str:
    """Normalize library directory prefixes for RPM paths.

    RPM entries often begin with ``./``. Only those prefixes are handled and no
    attempt is made to deal with absolute paths.
    """
    replacements = [
        ("./lib64/", "./lib/"),
        ("./lib32/", "./lib/"),
        ("./usr/lib64/", "./usr/lib/"),
        ("./usr/lib32/", "./usr/lib/"),
    ]
    for old, new in replacements:
        if path.startswith(old):
            return new + path[len(old):]
    return path


def strip_version(path: str) -> str:
    """Remove trailing numeric version components from shared library names."""
    return re.sub(r"(\.so)(?:\.[0-9]+)+$", r"\1", path)


def extract_info(
    path: str | os.PathLike[str],
    normalize: Callable[[str], str] | None = None,
    ignore_links: bool = False,
    ignore_versions: bool = False,
) -> FileInfo:
    """Return a mapping of file path to (size, file-type string)."""
    try:
        rpm_context = rpmfile.open(path)
    except FileNotFoundError:
        sys.exit(f"Error: File not found: {path}")
    except RPMError:
        sys.exit(f"Error: Not a valid RPM file: {path}")
    except OSError as e:
        sys.exit(f"Error: I/O error reading {path}: {e}")

    info: FileInfo = {}
    with rpm_context as rpm:
        symlink_paths: set[str] = set()
        if ignore_links:
            modes = rpm.headers.get("filemodes") or []
            raw_names = rpm.headers.get("filenames") or []
            names = [n.decode() if isinstance(n, bytes) else n for n in raw_names]
            for name, mode in zip(names, modes):
                if int(mode) & 0o170000 == 0o120000:
                    symlink_paths.add("./" + name if not name.startswith("./") else name)

        for member in rpm.getmembers():
            name = member.name
            if ignore_links and name in symlink_paths:
                continue
            is_dir = getattr(member, "isdir", False)
            if callable(is_dir):
                is_dir = is_dir()
            if is_dir:
                continue
            if normalize:
                name = normalize(name)
            if ignore_versions:
                name = strip_version(name)
            with rpm.extractfile(member) as f:
                sample_bytes = f.read(2048)
            info[name] = (member.size, detect_file_type(sample_bytes))

    return info


def to_kb(size: int) -> float:
    """Convert bytes to kilobytes."""
    return size / 1024


def _format_diff(size_a: int, size_b: int) -> tuple[str, float, str, str]:
    """Return (sign, diff_kb, diff_pct_col, diff_pct_csv) for a size delta."""
    diff_kb = to_kb(size_b - size_a)
    sign = '+' if diff_kb > 0 else ''
    if size_a == 0:
        return sign, diff_kb, "     N/A", "N/A"
    pct = (size_b - size_a) * 100.0 / size_a
    return sign, diff_kb, f"{sign}{pct:>7.2f}%", f"{sign}{pct:.2f}%"


def _emit_row(
    writer: csv.writer | None,
    name: str,
    size_a_str: str,
    size_b_str: str,
    diff_kb_str: str,
    diff_pct_col: str,
    type_a: str,
    type_b: str,
) -> None:
    """Print one table row and optionally write it to CSV."""
    print(
        f"{name:<{COL_NAME}} {size_a_str:>{COL_SIZE}} {size_b_str:>{COL_SIZE}} "
        f"{diff_kb_str:>{COL_DIFF}} {diff_pct_col:>{COL_PCT}} {type_a:<{COL_TYPE}} {type_b:<{COL_TYPE}}"
    )
    if writer:
        writer.writerow([name, size_a_str, size_b_str, diff_kb_str, diff_pct_col, type_a, type_b])


def _iter_rows(
    info_a: FileInfo,
    info_b: FileInfo,
    hide_equal: bool,
) -> list[FileRow]:
    """Merge two FileInfo dicts into a sorted list of FileRows."""
    rows = []
    for name in sorted(set(info_a) | set(info_b)):
        entry_a = info_a.get(name)
        entry_b = info_b.get(name)
        size_a, type_a = entry_a if entry_a else (None, None)
        size_b, type_b = entry_b if entry_b else (None, None)
        if hide_equal and size_a == size_b:
            continue
        rows.append(FileRow(name, size_a, type_a, size_b, type_b))
    return rows


def _report(rows: list[FileRow], csv_path: str | None) -> None:
    """Print the comparison table and optionally write a CSV file."""
    ctx = open(csv_path, "w", newline="") if csv_path else nullcontext()
    with ctx as csv_file:
        writer = csv.writer(csv_file, delimiter=';') if csv_path else None
        if writer:
            writer.writerow(["File", "Size A (KB)", "Size B (KB)", "Diff (KB)", "Diff %", "Type A", "Type B"])

        print(
            f"{'File':<{COL_NAME}} {'Size A (KB)':>{COL_SIZE}} {'Size B (KB)':>{COL_SIZE}} "
            f"{'Diff (KB)':>{COL_DIFF}} {'Diff %':>{COL_PCT}} {'Type A':<{COL_TYPE}} {'Type B':<{COL_TYPE}}"
        )

        total_a = total_b = 0
        for row in rows:
            if row.size_a is None:
                total_b += row.size_b
                _emit_row(writer, row.name, ABSENT, f"{to_kb(row.size_b):.2f}",
                          ABSENT, f"{'+new':>{COL_PCT}}", ABSENT, row.type_b)
            elif row.size_b is None:
                total_a += row.size_a
                _emit_row(writer, row.name, f"{to_kb(row.size_a):.2f}", ABSENT,
                          ABSENT, f"{'-removed':>{COL_PCT}}", row.type_a, ABSENT)
            else:
                total_a += row.size_a
                total_b += row.size_b
                sign, diff_kb, diff_pct_col, diff_pct_csv = _format_diff(row.size_a, row.size_b)
                _emit_row(
                    writer, row.name,
                    f"{to_kb(row.size_a):.2f}", f"{to_kb(row.size_b):.2f}",
                    f"{sign}{diff_kb:.2f}", diff_pct_col,
                    row.type_a, row.type_b,
                )

        sign_t, diff_kb_t, diff_pct_col_t, diff_pct_csv_t = _format_diff(total_a, total_b)
        _emit_row(
            writer, "TOTAL",
            f"{to_kb(total_a):.2f}", f"{to_kb(total_b):.2f}",
            f"{sign_t}{diff_kb_t:.2f}", diff_pct_col_t,
            "", "",
        )

    if csv_path:
        print(f"\nResults saved to {csv_path}")


def compare_rpms(
    path_a: str | os.PathLike[str],
    path_b: str | os.PathLike[str],
    csv_path: str | None = None,
    normalize: bool = False,
    hide_equal: bool = False,
    ignore_versions: bool = False,
    ignore_links: bool = False,
) -> None:
    """Compare file sizes in two RPM packages and print a summary table."""
    path_normalizer = normalize_lib_paths if normalize else None
    info_a = extract_info(path_a, normalize=path_normalizer, ignore_links=ignore_links, ignore_versions=ignore_versions)
    info_b = extract_info(path_b, normalize=path_normalizer, ignore_links=ignore_links, ignore_versions=ignore_versions)
    rows = _iter_rows(info_a, info_b, hide_equal)
    _report(rows, csv_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare file sizes in two RPM packages")
    parser.add_argument('rpm_a', help='First RPM package (reference)')
    parser.add_argument('rpm_b', help='Second RPM package to compare')
    parser.add_argument('--csv', nargs='?', metavar='FILE', const='',
                        help='Save results to CSV. If FILE not provided, uses <rpm_a> name with .csv')
    parser.add_argument('--64', dest='arch64', action='store_true',
                        help='Normalize lib paths for comparing 32-bit vs 64-bit packages')
    parser.add_argument('--hide-equal', action='store_true', help='Hide files with identical sizes')
    parser.add_argument('--ignore-versions', action='store_true', help='Ignore version suffix in .so filenames')
    parser.add_argument('--ignore-links', action='store_true', help='Ignore symbolic links in RPMs')
    args = parser.parse_args()

    csv_path = None
    if args.csv is not None:
        csv_path = args.csv or os.path.splitext(args.rpm_a)[0] + '.csv'

    compare_rpms(
        args.rpm_a,
        args.rpm_b,
        csv_path,
        normalize=args.arch64,
        hide_equal=args.hide_equal,
        ignore_versions=args.ignore_versions,
        ignore_links=args.ignore_links,
    )


if __name__ == '__main__':
    main()
