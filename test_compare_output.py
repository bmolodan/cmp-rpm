import csv
from pathlib import Path

import pytest

import compare_rpm_sizes as crs


def test_compare_rpms_output(monkeypatch, tmp_path, capsys):
    def fake_extract_info(path, normalize=None):
        if 'a' in path:
            return {'bin/foo': (10, 'elf')}
        return {'bin/foo': (12, 'elf')}

    monkeypatch.setattr(crs, 'extract_info', fake_extract_info)
    csv_file = tmp_path / 'out.csv'
    crs.compare_rpms('a.rpm', 'b.rpm', csv_path=csv_file)
    out = capsys.readouterr().out
    assert 'Type A' in out and 'Type B' in out
    with open(csv_file) as f:
        row = next(csv.reader(f))
    assert row == ['File', 'Size A (bytes)', 'Size B (bytes)', 'Diff %', 'Type A', 'Type B']
