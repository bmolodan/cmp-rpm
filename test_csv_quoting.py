import compare_rpm_sizes as cmp


def dummy_extract_info(path, normalize=None, ignore_links=False, ignore_versions=False):
    if path == 'a':
        return {'./file': (100, 'text')}
    else:
        return {'./file': (110, 'text')}


def test_csv_all_fields_quoted(tmp_path, monkeypatch):
    out = tmp_path / "report.csv"
    monkeypatch.setattr(cmp, 'extract_info', dummy_extract_info)
    cmp.compare_rpms('a', 'b', csv_path=str(out))
    with open(out, newline='') as f:
        for row in f:
            fields = row.strip().split(';')
            for field in fields:
                assert field.startswith('"') and field.endswith('"')
