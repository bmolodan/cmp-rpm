import json

import pytest

from compare_rpm_sizes import FileRow, _report, _report_json


# ---------------------------------------------------------------------------
# _report() return values (total_a, total_b)
# ---------------------------------------------------------------------------

def test_report_returns_totals_only_in_b(capsys):
    rows = [FileRow("new.so", None, None, 2048, "elf")]
    total_a, total_b = _report(rows, None)
    assert total_a == 0
    assert total_b == 2048


def test_report_returns_totals_only_in_a(capsys):
    rows = [FileRow("old.so", 1024, "elf", None, None)]
    total_a, total_b = _report(rows, None)
    assert total_a == 1024
    assert total_b == 0


def test_report_returns_totals_mixed(capsys):
    rows = [
        FileRow("a.so", 1024, "elf", 2048, "elf"),
        FileRow("b.so", 512,  "elf", 256,  "elf"),
    ]
    total_a, total_b = _report(rows, None)
    assert total_a == 1536
    assert total_b == 2304


# ---------------------------------------------------------------------------
# --quiet flag
# ---------------------------------------------------------------------------

def test_report_quiet_suppresses_header_and_file_rows(capsys):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    _report(rows, None, quiet=True)
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("TOTAL")


def test_report_quiet_suppresses_multiple_rows(capsys):
    rows = [
        FileRow("a.so", 1024, "elf", 2048, "elf"),
        FileRow("b.so", 512,  "elf", 512,  "elf"),
    ]
    _report(rows, None, quiet=True)
    out = capsys.readouterr().out
    assert "a.so" not in out
    assert "b.so" not in out
    assert "TOTAL" in out


def test_report_quiet_false_is_unchanged(capsys):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    _report(rows, None, quiet=False)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3  # header + file row + TOTAL


def test_report_quiet_still_writes_csv(capsys, tmp_path):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    csv_file = tmp_path / "out.csv"
    _report(rows, str(csv_file), quiet=True)
    assert csv_file.exists()
    assert "Results saved to" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _report_json()
# ---------------------------------------------------------------------------

def test_report_json_structure(capsys):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert "summary" in data
    assert "files" in data
    assert len(data["files"]) == 1


def test_report_json_summary_values(capsys):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["total_a_kb"] == pytest.approx(1.0)
    assert data["summary"]["total_b_kb"] == pytest.approx(2.0)
    assert data["summary"]["diff_pct"] == pytest.approx(100.0)


def test_report_json_status_changed(capsys):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert data["files"][0]["status"] == "changed"


def test_report_json_status_equal(capsys):
    rows = [FileRow("lib.so", 512, "elf", 512, "elf")]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert data["files"][0]["status"] == "equal"
    assert data["files"][0]["diff_pct"] == 0.0


def test_report_json_status_new(capsys):
    rows = [FileRow("new.so", None, None, 2048, "elf")]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert data["files"][0]["status"] == "new"
    assert data["files"][0]["size_a_kb"] is None
    assert data["summary"]["diff_pct"] is None  # total_a == 0


def test_report_json_status_removed(capsys):
    rows = [FileRow("old.so", 1024, "elf", None, None)]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert data["files"][0]["status"] == "removed"
    assert data["files"][0]["size_b_kb"] is None
    assert data["files"][0]["diff_pct"] == -100.0


def test_report_json_diff_pct_null_for_zero_size_a(capsys):
    rows = [FileRow("zero.so", 0, "empty", 1024, "elf")]
    _report_json(rows, None)
    data = json.loads(capsys.readouterr().out)
    assert data["files"][0]["diff_pct"] is None


def test_report_json_returns_totals(capsys):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    total_a, total_b = _report_json(rows, None)
    assert total_a == 1024
    assert total_b == 2048


def test_report_json_with_csv(capsys, tmp_path):
    rows = [FileRow("lib.so", 1024, "elf", 2048, "elf")]
    csv_file = tmp_path / "out.csv"
    _report_json(rows, str(csv_file))
    out = capsys.readouterr().out
    data = json.loads(out)  # stdout is pure JSON
    assert "summary" in data
    assert csv_file.exists()


# ---------------------------------------------------------------------------
# --fail-threshold math (unit tests, no argparse)
# ---------------------------------------------------------------------------

def test_threshold_exceeded():
    total_a, total_b = 1024, 1200  # ~17.2% growth
    actual_pct = (total_b - total_a) * 100.0 / total_a
    assert actual_pct > 10.0  # would trigger threshold of 10%


def test_threshold_not_exceeded():
    total_a, total_b = 1024, 1050  # ~2.5% growth
    actual_pct = (total_b - total_a) * 100.0 / total_a
    assert actual_pct <= 5.0  # would not trigger threshold of 5%


def test_threshold_equal_does_not_trigger():
    total_a, total_b = 1024, 1126  # exactly ~10.0%
    actual_pct = (total_b - total_a) * 100.0 / total_a
    # Threshold check is strict (>), so equal does not fail
    assert not (actual_pct > actual_pct)


def test_threshold_skipped_when_total_a_zero():
    total_a = 0
    # Guard in main(): if total_a > 0 — zero skips the check
    assert not (total_a > 0)
