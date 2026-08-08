"""Phase-32 tests: two-asset barrier options (Haug / AnalyticTwoAssetBarrierEngine)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase32():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 33)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# Haug values from test-suite/twoassetbarrieroption.cpp (tol=4e-3).
# Maturity = today + 180; s1/s2 spots, barrier on asset 2, strike on asset 1.
_HAUG_CASES = [
    # barrier_type, option_type, barrier, strike, corr, expected
    (ql.BarrierType.DownOut, ql.OptionType.Call, 95, 90, 0.5, 6.6592),
    (ql.BarrierType.UpOut, ql.OptionType.Call, 105, 90, -0.5, 4.6670),
    (ql.BarrierType.DownOut, ql.OptionType.Put, 95, 90, -0.5, 0.6184),
    (ql.BarrierType.UpOut, ql.OptionType.Put, 105, 100, 0.0, 0.8246),
]


@pytest.mark.parametrize(
    "barrier_type,option_type,barrier,strike,corr,expected",
    _HAUG_CASES,
)
def test_two_asset_barrier_haug(
    barrier_type, option_type, barrier, strike, corr, expected
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 180
    process1 = _bsm(today, 100.0, 0.0, 0.08, 0.2)
    process2 = _bsm(today, 100.0, 0.0, 0.08, 0.2)
    option = ql.TwoAssetBarrierOption(
        barrier_type,
        barrier,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(process1, process2, corr)
    assert option.NPV() == pytest.approx(expected, abs=4.0e-3)
    assert option.is_expired() is False


def test_two_asset_barrier_quote_handle_rho():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 180
    process1 = _bsm(today, 100.0, 0.0, 0.08, 0.2)
    process2 = _bsm(today, 100.0, 0.0, 0.08, 0.2)
    option = ql.TwoAssetBarrierOption(
        ql.BarrierType.DownOut,
        95.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(process1, process2, ql.make_quote_handle(0.5))
    assert option.NPV() == pytest.approx(6.6592, abs=4.0e-3)


def test_compat_phase32_aliases():
    import qlnb.compat as cql

    assert cql.TwoAssetBarrierOption is not None
    assert hasattr(cql.TwoAssetBarrierOption, "setPricingEngine")
    assert hasattr(cql.TwoAssetBarrierOption, "isExpired")
