"""Phase-192 tests: AbcdFunction instantaneous volatility."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase192():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 63)


def test_instantaneous_variance_is_volatility_squared():
    a, b, c, d = -0.0597, 0.1677, 0.5403, 0.1710
    f = ql.AbcdFunction(a, b, c, d)
    tol = 1e-14
    for t in (0.0, 0.5, 1.0, 2.0):
        for T in (1.0, 2.0, 3.0, 5.0):
            vol = f.instantaneous_volatility(t, T)
            var = f.instantaneous_variance(t, T)
            assert abs(var - vol * vol) <= tol


def test_instantaneous_covariance_matches_product():
    a, b, c, d = -0.0597, 0.1677, 0.5403, 0.1710
    f = ql.AbcdFunction(a, b, c, d)
    tol = 1e-14
    for u in (0.0, 0.25, 1.0):
        for T in (1.0, 2.0, 4.0):
            for S in (1.0, 3.0, 5.0):
                cov = f.instantaneous_covariance(u, T, S)
                product = f.instantaneous_volatility(u, T) * f.instantaneous_volatility(
                    u, S
                )
                assert abs(cov - product) <= tol


def test_compat_phase192_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.AbcdFunction, "instantaneousVolatility")
    assert hasattr(cql.AbcdFunction, "instantaneousVariance")
    assert hasattr(cql.AbcdFunction, "instantaneousCovariance")
