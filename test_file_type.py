import pytest
from compare_rpm_sizes import detect_file_type

@pytest.mark.parametrize(
    "magic,expected",
    [
        (b"\x7fELF" + b"\x00" * 20, "elf"),
        (b"PK\x03\x04" + b"\x00" * 100, "zip"),
        (b"\x1f\x8b\x08" + b"\x00" * 100, "gzip"),
        (b"BZh" + b"9" * 100, "bzip2"),
        (b"\xfd7zXZ\x00" + b"\x00" * 100, "xz"),
        (b"#! /bin/sh\n", "script"),
        (b"", "empty"),
        (b"Hello", "text"),
    ],
)
def test_detect_file_type(magic, expected):
    assert expected in detect_file_type(magic).lower()
