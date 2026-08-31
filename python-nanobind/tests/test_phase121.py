"""Phase-121 tests: discrete geometric Asian under Heston."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase121():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 2)


# AsianOptionTests::testAnalyticDiscreteGeometricAveragePriceHeston
# (days, strike, expected, suite tol[])
_CASES = [
    (30, 90.0, 10.2732, 3.0e-2),
    (91, 90.0, 10.9554, 2.0e-2),
    (182, 100.0, 5.2132, 1.0e-2),
    (365, 100.0, 7.2243, 3.0e-2),
    (730, 110.0, 5.3531, 3.0e-2),
    (1095, 110.0, 7.3315, 4.0e-2),
    (30, 110.0, 0.1012, 2.0e-2),
    (365, 90.0, 13.6950, 2.0e-2),
]


def _weekly_fixings(today: ql.Date, days: int) -> list[ql.Date]:
    expiry = today + days
    future_fixings = int(math.floor(days / 7.0))
    return [expiry - i * 7 for i in range(future_fixings - 1, -1, -1)]


def test_discrete_geometric_asian_heston_tables():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    spot = ql.QuoteHandle(ql.SimpleQuote(100.0))
    q_ts = ql.FlatForward(today, 0.0, dc)
    r_ts = ql.FlatForward(today, 0.05, dc)
    process = ql.HestonProcess(
        r_ts, q_ts, spot, 0.09, 1.15, 0.0348, 0.39, -0.64
    )

    for days, strike, expected, tol in _CASES:
        fixing_dates = _weekly_fixings(today, days)
        opt = ql.DiscreteAveragingAsianOption(
            ql.AverageType.Geometric,
            1.0,
            0,
            fixing_dates,
            ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
            ql.EuropeanExercise(today + days),
        )
        opt.set_heston_pricing_engine(process)
        assert opt.NPV() == pytest.approx(expected, abs=tol), (days, strike)


def test_compat_phase121_aliases():
    import qlnb.compat as c

    assert hasattr(c.DiscreteAveragingAsianOption, "setHestonPricingEngine")
