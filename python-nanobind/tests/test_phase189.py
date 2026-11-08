"""Phase-189 tests: AbcdCalibration fit."""

from __future__ import annotations

import qlnb as ql

# MarketModelTests::setup() cap/floor Black volatilities.
_MKT_VOLS = [
    0.15541283,
    0.18719678,
    0.20890740,
    0.22318179,
    0.23212717,
    0.23731450,
    0.23988649,
    0.24066384,
    0.24023111,
    0.23900189,
    0.23726699,
    0.23522952,
    0.23303022,
    0.23076564,
    0.22850101,
    0.22627951,
    0.22412881,
    0.22206569,
    0.22009939,
]


def test_version_is_phase189():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 60)


def _market_model_fixing_times():
    # Fixing times for 19 caplet vols (matches mktVols length in MarketModelTests::setup).
    return [0.5 * (i + 1) for i in range(19)]


def test_abcd_volatility_fit():
    # MarketModelTests::testAbcdVolatilityFit
    times = _market_model_fixing_times()
    black_vols = _MKT_VOLS[: len(times)]
    inst_vol = ql.AbcdCalibration(times, black_vols)
    error0 = inst_vol.error()
    inst_vol.compute()
    error1 = inst_vol.error()
    assert error1 < error0

    abcd = ql.AbcdFunction(inst_vol.a(), inst_vol.b(), inst_vol.c(), inst_vol.d())
    ks = inst_vol.k(times, black_vols)
    tol = 3.0e-4
    for i, (t, k) in enumerate(zip(times, ks, strict=True)):
        assert abs(k - 1.0) <= tol, f"tenor {i} t={t}: k={k}"
        model_vol = abcd.volatility(0.0, t, t)
        assert model_vol > 0.0


def test_compat_phase189_aliases():
    import qlnb.compat as cql

    assert cql.AbcdCalibration is not None
    assert hasattr(cql.AbcdCalibration, "endCriteria")
