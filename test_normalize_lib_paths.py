import pytest
from compare_rpm_sizes import normalize_lib_paths

@pytest.mark.parametrize(
    "src,expected",
    [
        ("./usr/lib64/lib.so", "./usr/lib/lib.so"),
        ("./usr/lib32/libX.so", "./usr/lib/libX.so"),
        ("./lib64/file", "./lib/file"),
        ("./lib32/foo/bar", "./lib/foo/bar"),
        ("/home/user/lib64/file", "/home/user/lib64/file"),
        ("/usr/lib64/lib.so", "/usr/lib64/lib.so"),
    ],
)
def test_normalize_lib_paths(src, expected):
    assert normalize_lib_paths(src) == expected
