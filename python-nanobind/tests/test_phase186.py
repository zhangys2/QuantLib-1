"""Phase-186 tests: AbcdFunction variance."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase186():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 57)


def test_abcd_variance_matches_covariance_when_t1_equals_t2():
    # MarketModelTests::testAbcdVolatilityIntegration (T1 == T2 branch).
    a, b, c, d = -0.0597, 0.1677, 0.5403, 0.1710
    inst_vol = ql.AbcdFunction(a, b, c, d)
    tol = 1e-14
    n = 10

    for i in range(n):
        t1 = 0.5 * (1 + i)
        for j in range(n):
            x_min = 0.5 * j
            for l in range(n - j):
                x_max = x_min + 0.5 * l
                analytical = inst_vol.covariance(x_min, x_max, t1, t1)
                variance = inst_vol.variance(x_min, x_max, t1)
                assert abs(analytical - variance) <= tol


def test_compat_phase186_aliases():
    import qlnb.compat as cql

    assert cql.AbcdFunction is not None
    assert hasattr(cql.AbcdFunction, "variance")
