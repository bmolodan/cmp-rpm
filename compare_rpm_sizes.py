import argparse
import csv
import os
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


def extract_info(path, normalize=None):
    """Return a mapping of file path to (size, type)."""
    info = {}
    with rpmfile.open(path) as rpm:
        for member in rpm.getmembers():
            # Skip directory entries. `isdir` can be a property or a method
            is_dir = getattr(member, "isdir", False)
            if callable(is_dir):
                is_dir = is_dir()
            if is_dir:
                continue
            name = member.name
            if normalize:
                name = normalize(name)
            with rpm.extractfile(member) as f:
                header = f.read(2048)
            info[name] = (member.size, detect_file_type(header))
    return info


def compare_rpms(path_a, path_b, csv_path=None, normalize=False):
    norm = normalize_lib_paths if normalize else None
    info_a = extract_info(path_a, normalize=norm)
    info_b = extract_info(path_b, normalize=norm)
    files = sorted(set(info_a) | set(info_b))

    csv_file = None
    writer = None
    if csv_path:
        csv_file = open(csv_path, "w", newline="")
        writer = csv.writer(csv_file)
        writer.writerow(["File", "Size A (bytes)", "Size B (bytes)", "Diff %", "Type"])

    print(f"{'File':<50} {'Size A (bytes)':>15} {'Size B (bytes)':>15} {'Diff %':>8} {'Type':<10}")
    for name in files:
        info_a_entry = info_a.get(name)
        info_b_entry = info_b.get(name)
        if info_a_entry is None or info_b_entry is None:
            continue
        size_a, type_a = info_a_entry
        size_b, type_b = info_b_entry
        diff_percent = ((size_b - size_a) * 100.0 / size_a) if size_a else float('inf')
        ftype = type_a if type_a == type_b else f"{type_a}/{type_b}"
        print(f"{name:<50} {size_a:>15} {size_b:>15} {diff_percent:>7.2f}% {ftype:<10}")
        if writer:
            writer.writerow([name, size_a, size_b, f"{diff_percent:.2f}%", ftype])

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
    args = parser.parse_args()

    csv_path = None
    if args.csv is not None:
        csv_path = args.csv or os.path.splitext(args.rpm_a)[0] + '.csv'

    compare_rpms(args.rpm_a, args.rpm_b, csv_path, normalize=args.arch64)


if __name__ == '__main__':
    main()
