import argparse
import csv
import os
import re
import rpmfile
import magic


_magic = magic.Magic(mime=False)


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


def extract_info(path, normalize=None, ignore_links=False, ignore_versions=False):
    """Return a mapping of file path to (size, type)."""
    info = {}
    with rpmfile.open(path) as rpm:
        link_map = set()
        if ignore_links:
            modes = rpm.headers.get("filemodes") or []
            names = rpm.headers.get("filenames") or []
            names = [n.decode() if isinstance(n, bytes) else n for n in names]
            for name, mode in zip(names, modes):
                if int(mode) & 0o170000 == 0o120000:
                    link_map.add("./" + name if not name.startswith("./") else name)
        for member in rpm.getmembers():
            name = member.name
            if ignore_links and name in link_map:
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
                header = f.read(2048)
            info[name] = (member.size, detect_file_type(header))
    return info


def to_kb(size: int) -> float:
    """Convert bytes to kilobytes."""
    return size / 1024


def compare_rpms(
    path_a,
    path_b,
    csv_path=None,
    normalize=False,
    hide_equal=False,
    ignore_versions=False,
    ignore_links=False,
):
    norm = normalize_lib_paths if normalize else None
    info_a = extract_info(
        path_a, normalize=norm, ignore_links=ignore_links, ignore_versions=ignore_versions
    )
    info_b = extract_info(
        path_b, normalize=norm, ignore_links=ignore_links, ignore_versions=ignore_versions
    )
    files = sorted(set(info_a) | set(info_b))

    csv_file = None
    writer = None
    if csv_path:
        csv_file = open(csv_path, "w", newline="")
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow([
            "File",
            "Size A (KB)",
            "Size B (KB)",
            "Diff (KB)",
            "Diff %",
            "Type A",
            "Type B",
        ])

    print(
        f"{'File':<50} {'Size A (KB)':>12} {'Size B (KB)':>12} {'Diff (KB)':>12} {'Diff %':>8} {'Type A':<10} {'Type B':<10}"
    )
    total_a = total_b = 0
    for name in files:
        info_a_entry = info_a.get(name)
        info_b_entry = info_b.get(name)
        if info_a_entry is None or info_b_entry is None:
            continue
        size_a, type_a = info_a_entry
        size_b, type_b = info_b_entry
        if hide_equal and size_a == size_b:
            continue
        total_a += size_a
        total_b += size_b
        diff_kb = to_kb(size_b - size_a)
        diff_percent = ((size_b - size_a) * 100.0 / size_a) if size_a else float('inf')
        sign = '+' if diff_kb > 0 else ''
        ftype_a = type_a
        ftype_b = type_b
        print(
            f"{name:<50} {to_kb(size_a):>12.2f} {to_kb(size_b):>12.2f} {sign}{diff_kb:>11.2f} {sign}{diff_percent:>7.2f}% {ftype_a:<10} {ftype_b:<10}"
        )
        if writer:
            writer.writerow(
                [
                    name,
                    f"{to_kb(size_a):.2f}",
                    f"{to_kb(size_b):.2f}",
                    f"{sign}{diff_kb:.2f}",
                    f"{sign}{diff_percent:.2f}%",
                    ftype_a,
                    ftype_b,
                ]
            )

    diff_total_kb = to_kb(total_b - total_a)
    sign_total = '+' if diff_total_kb > 0 else ''
    print(
        f"{'TOTAL':<50} {to_kb(total_a):>12.2f} {to_kb(total_b):>12.2f} {sign_total}{diff_total_kb:>11.2f} {sign_total}{((total_b - total_a) * 100.0 / total_a) if total_a else float('inf'):>7.2f}%"
    )
    if writer:
        writer.writerow(
            [
                'TOTAL',
                f"{to_kb(total_a):.2f}",
                f"{to_kb(total_b):.2f}",
                f"{sign_total}{diff_total_kb:.2f}",
                f"{sign_total}{((total_b - total_a) * 100.0 / total_a) if total_a else float('inf'):.2f}%",
                '',
                '',
            ]
        )

    if csv_file:
        csv_file.close()
        print(f"\nResults saved to {csv_path}")


def main():
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
