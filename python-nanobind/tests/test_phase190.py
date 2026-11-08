"""Phase-190 tests: market-model is_in_subset utility."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase190():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 61)


def test_is_in_subset_disjoint_sets():
    # MarketModelTests::testIsInSubset
    dim = 100
    times = [float(i) for i in range(dim)]
    subset = [float(dim + i) for i in range(dim)]
    result = ql.is_in_subset(times, subset)
    assert len(result) == dim
    assert result == [False] * dim


def test_is_in_subset_partial_overlap():
    times = [1.0, 2.0, 3.0, 4.0]
    subset = [2.0, 4.0, 5.0]
    assert ql.is_in_subset(times, subset) == [False, True, False, True]


def test_compat_phase190_aliases():
    import qlnb.compat as cql

    assert hasattr(cql, "isInSubset")
