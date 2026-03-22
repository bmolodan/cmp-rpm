import csv
import io

import pytest

from compare_rpm_sizes import (
    ABSENT,
    COL_DIFF,
    COL_NAME,
    COL_PCT,
    COL_SIZE,
    COL_TYPE,
    FileRow,
    _emit_row,
    _iter_rows,
    _report,
)


# ---------------------------------------------------------------------------
# _iter_rows
# ---------------------------------------------------------------------------

def test_iter_rows_both_empty():
    assert _iter_rows({}, {}, hide_equal=False) == []


def test_iter_rows_only_in_a():
    result = _iter_rows({"a.so": (1024, "elf")}, {}, hide_equal=False)
    assert result == [FileRow("a.so", 1024, "elf", None, None)]


def test_iter_rows_only_in_b():
    result = _iter_rows({}, {"b.so": (2048, "elf")}, hide_equal=False)
    assert result == [FileRow("b.so", None, None, 2048, "elf")]


def test_iter_rows_in_both_different():
    result = _iter_rows({"c.so": (1024, "elf")}, {"c.so": (2048, "data")}, hide_equal=False)
    assert result == [FileRow("c.so", 1024, "elf", 2048, "data")]


def test_iter_rows_same_size_hide_equal_false():
    result = _iter_rows({"d.so": (512, "elf")}, {"d.so": (512, "elf")}, hide_equal=False)
    assert result == [FileRow("d.so", 512, "elf", 512, "elf")]


def test_iter_rows_same_size_hide_equal_true():
    result = _iter_rows({"d.so": (512, "elf")}, {"d.so": (512, "elf")}, hide_equal=True)
    assert result == []


def test_iter_rows_mixed_hide_equal_true():
    info_a = {"d.so": (512, "elf"), "e.txt": (100, "text")}
    info_b = {"d.so": (512, "elf"), "e.txt": (200, "text")}
    result = _iter_rows(info_a, info_b, hide_equal=True)
    assert result == [FileRow("e.txt", 100, "text", 200, "text")]


def test_iter_rows_sort_order():
    info_a = {"z.so": (100, "elf"), "a.so": (200, "elf")}
    info_b = {"z.so": (100, "elf"), "a.so": (300, "elf")}
    result = _iter_rows(info_a, info_b, hide_equal=False)
    assert [r.name for r in result] == ["a.so", "z.so"]


# ---------------------------------------------------------------------------
# _emit_row
# ---------------------------------------------------------------------------

def _make_writer() -> tuple[csv.writer, io.StringIO]:
    buf = io.StringIO()
    return csv.writer(buf, delimiter=";"), buf


def test_emit_row_no_writer(capsys):
    _emit_row(None, "libfoo.so", "1.00", "2.00", "+1.00", "+ 100.00%", "elf", "elf")
    out = capsys.readouterr().out.rstrip("\n")
    assert out.startswith("libfoo.so")
    assert "1.00" in out
    assert "2.00" in out
    assert "+1.00" in out
    assert "100.00%" in out
    # column widths: name field is COL_NAME chars wide
    assert out[COL_NAME] == " "


def test_emit_row_with_writer(capsys):
    writer, buf = _make_writer()
    _emit_row(writer, "libfoo.so", "1.00", "2.00", "+1.00", "+ 100.00%", "elf", "elf")
    stdout = capsys.readouterr().out
    assert "libfoo.so" in stdout
    csv_content = buf.getvalue()
    assert "libfoo.so" in csv_content
    assert ";" in csv_content
    fields = csv_content.strip().split(";")
    assert fields[0] == "libfoo.so"
    assert fields[1] == "1.00"
    assert fields[2] == "2.00"


def test_emit_row_only_in_b(capsys):
    _emit_row(None, "new.so", ABSENT, "2.00", ABSENT, f"{'+new':>{COL_PCT}}", ABSENT, "elf")
    out = capsys.readouterr().out
    assert ABSENT in out
    assert "+new" in out


def test_emit_row_only_in_a(capsys):
    _emit_row(None, "old.so", "1.00", ABSENT, ABSENT, f"{'-removed':>{COL_PCT}}", "elf", ABSENT)
    out = capsys.readouterr().out
    assert ABSENT in out
    assert "-removed" in out


def test_emit_row_total_empty_types(capsys):
    _emit_row(None, "TOTAL", "1.25", "2.50", "+1.25", "+ 100.00%", "", "")
    out = capsys.readouterr().out
    assert "TOTAL" in out
    assert "1.25" in out
    assert "2.50" in out


# ---------------------------------------------------------------------------
# _report
# ---------------------------------------------------------------------------

HEADER = (
    f"{'File':<{COL_NAME}} {'Size A (KB)':>{COL_SIZE}} {'Size B (KB)':>{COL_SIZE}} "
    f"{'Diff (KB)':>{COL_DIFF}} {'Diff %':>{COL_PCT}} {'Type A':<{COL_TYPE}} {'Type B':<{COL_TYPE}}"
)


def test_report_empty_rows(capsys):
    _report([], None)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0] == HEADER
    assert lines[1].startswith("TOTAL")
    assert "N/A" in lines[1]


def test_report_only_in_b(capsys):
    _report([FileRow("new.so", None, None, 2048, "elf")], None)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert lines[1].startswith("new.so")
    assert ABSENT in lines[1]
    assert "+new" in lines[1]
    assert lines[2].startswith("TOTAL")
    assert "N/A" in lines[2]   # total_a=0 → N/A


def test_report_only_in_a(capsys):
    _report([FileRow("old.so", 1024, "elf", None, None)], None)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert "-removed" in lines[1]
    assert "-100.00%" in lines[2]


def test_report_both_present(capsys):
    _report([FileRow("lib.so", 1024, "elf", 2048, "elf")], None)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert "100.00%" in lines[1]
    assert lines[2].startswith("TOTAL")
    assert "100.00%" in lines[2]


def test_report_mixed_with_csv(capsys, tmp_path):
    rows = [
        FileRow("aaa.so", 1024, "elf",  2048, "elf"),
        FileRow("bbb.so", None, None,   512,  "text"),
        FileRow("ccc.so", 256,  "elf",  None, None),
    ]
    csv_file = tmp_path / "out.csv"
    _report(rows, str(csv_file))

    lines = capsys.readouterr().out.splitlines()
    # header + 3 data rows + TOTAL + "Results saved" (blank line + message = 2 items via splitlines)
    assert len(lines) >= len(rows) + 2
    assert lines[0] == HEADER
    total_line = next(l for l in lines if l.startswith("TOTAL"))
    assert total_line is not None

    assert csv_file.exists()
    csv_lines = csv_file.read_text().splitlines()
    # header + 3 data rows + TOTAL = 5 lines
    assert len(csv_lines) == 5
    assert csv_lines[0] == "File;Size A (KB);Size B (KB);Diff (KB);Diff %;Type A;Type B"
    assert csv_lines[-1].startswith("TOTAL")
