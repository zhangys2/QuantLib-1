"""Phase-188 tests: AbcdFunction average volatility."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase188():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 59)


def test_abcd_volatility_squared_equals_variance():
    # AbcdFunction: variance == volatility^2 (used in testAbcdVolatilityFit checks).
    a, b, c, d = -0.0597, 0.1677, 0.5403, 0.1710
    f = ql.AbcdFunction(a, b, c, d)
    tol = 1e-14
    n = 10

    for i in range(n):
        t = 0.5 * (1 + i)
        for j in range(n):
            t_min = 0.5 * j
            for l in range(n - j):
                t_max = t_min + 0.5 * l
                if t_max <= t_min:
                    continue
                vol = f.volatility(t_min, t_max, t)
                var = f.variance(t_min, t_max, t)
                assert abs(vol * vol * (t_max - t_min) - var) <= tol


def test_compat_phase188_aliases():
    import qlnb.compat as cql

    assert cql.AbcdFunction is not None
    assert hasattr(cql.AbcdFunction, "volatility")
