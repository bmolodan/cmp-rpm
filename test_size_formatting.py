import pytest

from compare_rpm_sizes import _format_diff, to_kb


@pytest.mark.parametrize(
    "size,expected",
    [
        (0,     0.0),
        (1024,  1.0),
        (512,   0.5),
        (2048,  2.0),
        (1,     pytest.approx(1 / 1024)),
        (-1024, -1.0),
    ],
)
def test_to_kb(size, expected):
    assert to_kb(size) == expected


@pytest.mark.parametrize(
    "size_a,size_b,exp_sign,exp_diff_kb,exp_pct_col,exp_pct_csv",
    [
        pytest.param(0,    0,    "",  0.0,                "     N/A",  "N/A",       id="both_zero"),
        pytest.param(0,    1024, "+", 1.0,                "     N/A",  "N/A",       id="zero_baseline_positive"),
        pytest.param(1024, 1024, "",  0.0,                "   0.00%",  "0.00%",     id="equal"),
        pytest.param(1024, 2048, "+", 1.0,                "+ 100.00%", "+100.00%",  id="doubled"),
        pytest.param(2048, 1024, "",  -1.0,               " -50.00%",  "-50.00%",   id="halved"),
        pytest.param(1024, 0,    "",  -1.0,               "-100.00%",  "-100.00%",  id="removed"),
        pytest.param(100,  133,  "+", pytest.approx(33 / 1024), "+  33.00%", "+33.00%", id="fractional"),
    ],
)
def test_format_diff(size_a, size_b, exp_sign, exp_diff_kb, exp_pct_col, exp_pct_csv):
    sign, diff_kb, pct_col, pct_csv = _format_diff(size_a, size_b)
    assert sign == exp_sign
    assert diff_kb == exp_diff_kb
    assert pct_col == exp_pct_col
    assert pct_csv == exp_pct_csv
