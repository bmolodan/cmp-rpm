import argparse
import csv
import os
import rpmfile


def normalize_lib_paths(path):
    """Normalize lib directories so /lib64 and /usr/lib64 map to /lib and
    /usr/lib respectively. This helps compare 32-bit and 64-bit packages.
    """
    replacements = [
        ("/lib64/", "/lib/"),
        ("/lib32/", "/lib/"),
        ("/usr/lib64/", "/usr/lib/"),
        ("/usr/lib32/", "/usr/lib/"),
    ]
    for old, new in replacements:
        if path.startswith(old):
            path = new + path[len(old):]
    return path


def extract_sizes(path, normalize=None):
    sizes = {}
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
            sizes[name] = member.size
    return sizes


def compare_rpms(path_a, path_b, csv_path=None, normalize=False):
    norm = normalize_lib_paths if normalize else None
    sizes_a = extract_sizes(path_a, normalize=norm)
    sizes_b = extract_sizes(path_b, normalize=norm)
    files = sorted(set(sizes_a) | set(sizes_b))

    csv_file = None
    writer = None
    if csv_path:
        csv_file = open(csv_path, "w", newline="")
        writer = csv.writer(csv_file)
        writer.writerow(["File", "Size A (bytes)", "Size B (bytes)", "Diff %"])

    print(f"{'File':<50} {'Size A (bytes)':>15} {'Size B (bytes)':>15} {'Diff %':>8}")
    for name in files:
        size_a = sizes_a.get(name)
        size_b = sizes_b.get(name)
        if size_a is None or size_b is None:
            continue
        diff_percent = ((size_b - size_a) * 100.0 / size_a) if size_a else float('inf')
        print(f"{name:<50} {size_a:>15} {size_b:>15} {diff_percent:>7.2f}%")
        if writer:
            writer.writerow([name, size_a, size_b, f"{diff_percent:.2f}%"]) 

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
