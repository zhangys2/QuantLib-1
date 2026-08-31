"""Phase-120 tests: continuous geometric Asian under Heston."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase120():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 1)


def _heston_market(v0, kappa, theta, sigma, rho):
    # AsianOptionTests::testAnalyticContinuousGeometricAveragePriceHeston.
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    spot = ql.QuoteHandle(ql.SimpleQuote(100.0))
    q_ts = ql.FlatForward(today, 0.0, dc)
    r_ts = ql.FlatForward(today, 0.05, dc)
    process = ql.HestonProcess(r_ts, q_ts, spot, v0, kappa, theta, sigma, rho)
    return today, process


def test_continuous_geometric_asian_heston_table1():
    # Kim & Wee Table 1 (Feller-obeying params); suite tol 1e-2.
    today, process = _heston_market(0.09, 1.15, 0.348, 0.39, -0.64)
    cases = [
        (73, 90.0, 10.6571),
        (73, 100.0, 3.4478),
        (73, 110.0, 0.4724),
        (548, 100.0, 11.3374),
        (1095, 90.0, 20.5102),
        (1095, 110.0, 12.7882),
    ]
    for days, strike, expected in cases:
        opt = ql.ContinuousAveragingAsianOption(
            ql.AverageType.Geometric,
            ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
            ql.EuropeanExercise(today + days),
        )
        opt.set_heston_pricing_engine(process)
        assert opt.NPV() == pytest.approx(expected, abs=1.0e-2), (days, strike)


def test_continuous_geometric_asian_heston_table4():
    # Kim & Wee Table 4 (non-Feller params).
    today, process = _heston_market(0.09, 2.0, 0.09, 1.0, -0.3)
    cases = [
        (73, 95.0, 6.4362),
        (73, 100.0, 3.1578),
        (548, 105.0, 6.3818),
        (1095, 100.0, 12.5707),
    ]
    for days, strike, expected in cases:
        opt = ql.ContinuousAveragingAsianOption(
            ql.AverageType.Geometric,
            ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
            ql.EuropeanExercise(today + days),
        )
        opt.set_heston_pricing_engine(process)
        assert opt.NPV() == pytest.approx(expected, abs=1.0e-2), (days, strike)


def test_compat_phase120_aliases():
    import qlnb.compat as c

    assert hasattr(c.ContinuousAveragingAsianOption, "setHestonPricingEngine")
