"""Phase-187 tests: LmExtLinearExponentialVolModel integrated variance vs AbcdFunction."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase187():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 58)


def test_abcd_volatility_compare():
    # MarketModelTests::testAbcdVolatilityCompare parameter mapping.
    a, b, c, d = 0.0597, 0.1677, 0.5403, 0.1710
    rate_times = [float(i) for i in range(1, 20)]
    lm_abcd = ql.LmExtLinearExponentialVolModel(rate_times, b, c, d, a)
    abcd = ql.AbcdFunction(a, b, c, d)
    tol = 1e-10

    for i1, t1 in enumerate(rate_times):
        for i2, t2 in enumerate(rate_times):
            t = 0.0
            limit = min(t1, t2)
            while t < limit:
                lm_cov = lm_abcd.integrated_variance(i1, i2, t)
                abcd_cov = abcd.covariance(0.0, t, t1, t2)
                assert abs(lm_cov - abcd_cov) <= tol, (
                    f"i1={i1}, i2={i2}, t={t}: lm={lm_cov}, abcd={abcd_cov}"
                )
                t += 0.5


def test_compat_phase187_aliases():
    import qlnb.compat as cql

    assert cql.LmExtLinearExponentialVolModel is not None
    assert hasattr(cql.LmExtLinearExponentialVolModel, "integratedVariance")
