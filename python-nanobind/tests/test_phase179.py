"""Phase-179 tests: AbcdFunction degenerate covariance cases."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase179():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 50)


def test_abcd_degenerate_covariance():
    # MarketModelTests::testAbcdDegenerateCases
    tol = 1e-14

    f1 = ql.AbcdFunction(0.0, 0.0, 1.0e-15, 1.0)
    cov1 = f1.covariance(0.0, 1.0, 1.0, 1.0)
    assert not math.isnan(cov1)
    assert not math.isinf(cov1)
    assert cov1 == pytest.approx(1.0, abs=tol)

    f2 = ql.AbcdFunction(1.0, 0.0, 1.0e-50, 0.0)
    cov2 = f2.covariance(0.0, 1.0, 1.0, 1.0)
    assert not math.isnan(cov2)
    assert not math.isinf(cov2)
    assert cov2 == pytest.approx(1.0, abs=tol)


def test_compat_phase179_aliases():
    import qlnb.compat as cql

    assert cql.AbcdFunction is not None
    assert hasattr(cql.AbcdFunction, "maximumVolatility")
    assert hasattr(cql.AbcdFunction, "shortTermVolatility")
    assert hasattr(cql.AbcdFunction, "longTermVolatility")
