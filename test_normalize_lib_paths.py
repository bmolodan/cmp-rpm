import pytest
from compare_rpm_sizes import normalize_lib_paths

@pytest.mark.parametrize(
    "src,expected",
    [
        ("/usr/lib64/lib.so", "/usr/lib/lib.so"),
        ("/lib32/foo", "/lib/foo"),
        ("usr/lib64/lib.so", "usr/lib/lib.so"),
        ("lib64/bar", "lib/bar"),
        ("/home/user/lib64/file", "/home/user/lib64/file"),
    ],
)
def test_normalize_lib_paths(src, expected):
    assert normalize_lib_paths(src) == expected
