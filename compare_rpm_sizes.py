import argparse
import rpmfile


def extract_sizes(path):
    sizes = {}
    with rpmfile.open(path) as rpm:
        for member in rpm.getmembers():
            # Skip directory entries. `isdir` can be a property or a method
            is_dir = getattr(member, "isdir", False)
            if callable(is_dir):
                is_dir = is_dir()
            if is_dir:
                continue
            sizes[member.name] = member.size
    return sizes


def compare_rpms(path_a, path_b):
    sizes_a = extract_sizes(path_a)
    sizes_b = extract_sizes(path_b)
    files = sorted(set(sizes_a) | set(sizes_b))

    print(f"{'File':<50} {'Size A (bytes)':>15} {'Size B (bytes)':>15} {'Diff %':>8}")
    for name in files:
        size_a = sizes_a.get(name)
        size_b = sizes_b.get(name)
        if size_a is None or size_b is None:
            continue
        diff_percent = ((size_b - size_a) * 100.0 / size_a) if size_a else float('inf')
        print(f"{name:<50} {size_a:>15} {size_b:>15} {diff_percent:>7.2f}%")


def main():
    parser = argparse.ArgumentParser(description="Compare file sizes in two RPM packages")
    parser.add_argument('rpm_a', help='First RPM package (reference)')
    parser.add_argument('rpm_b', help='Second RPM package to compare')
    args = parser.parse_args()

    compare_rpms(args.rpm_a, args.rpm_b)


if __name__ == '__main__':
    main()
