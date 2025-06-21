import pytest
from compare_rpm_sizes import strip_version

@pytest.mark.parametrize(
    "src,expected",
    [
        ("libfoo.so.1", "libfoo.so"),
        ("libfoo.so.1.2.3", "libfoo.so"),
        ("libfoo.so", "libfoo.so"),
        ("/usr/lib/libfoo.so.1.0", "/usr/lib/libfoo.so"),
    ],
)
def test_strip_version(src, expected):
    assert strip_version(src) == expected
