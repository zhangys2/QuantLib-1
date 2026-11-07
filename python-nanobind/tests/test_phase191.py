"""Phase-191 tests: market-model time utilities."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase191():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 62)


def test_merge_times():
    times = [[1.0, 2.0, 4.0], [2.0, 3.0, 4.0]]
    result = ql.merge_times(times)
    assert result.merged_times == [1.0, 2.0, 3.0, 4.0]
    # is_present rows follow QuantLib's sorted pre-unique timeline (includes duplicates).
    assert result.is_present[0] == [True, True, False, True, True, True]
    assert result.is_present[1] == [False, True, True, True, True, True]


def test_check_increasing_times_and_calculate_taus():
    taus = ql.check_increasing_times_and_calculate_taus([1.0, 2.5, 4.0])
    assert taus == [1.5, 1.5]


def test_check_increasing_times_and_calculate_taus_rejects_invalid():
    with pytest.raises(RuntimeError):
        ql.check_increasing_times_and_calculate_taus([0.0, 1.0, 2.0])


def test_compat_phase191_aliases():
    import qlnb.compat as cql

    assert hasattr(cql, "mergeTimes")
    assert hasattr(cql, "checkIncreasingTimesAndCalculateTaus")
