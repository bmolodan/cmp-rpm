import io
import zipfile

import pytest

from compare_rpm_sizes import detect_file_type


def _make_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("x", "x")
    return buf.getvalue()


_ZIP_BYTES = _make_zip_bytes()


@pytest.mark.parametrize(
    "magic,expected",
    [
        (b"\x7fELF" + b"\x00" * 20, "elf"),
        (_ZIP_BYTES, "zip"),
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
