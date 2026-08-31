"""Phase-145 tests: AnalyticHestonHullWhiteEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase145():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 16)


def _compare_market(today: ql.Date):
    # HybridHestonHullWhiteProcessTests::testCompareBsmHWandHestonHW.
    dc = ql.Actual365Fixed()
    dates = [today + ql.Period(i, ql.TimeUnit.Years) for i in range(41)]
    rates = [0.01 + 0.0002 * math.exp(math.sin(i / 4.0)) for i in range(41)]
    div_rates = [0.02 + 0.0001 * math.exp(math.sin(i / 5.0)) for i in range(41)]
    spot = ql.make_quote_handle(100.0)
    r_ts = ql.ZeroCurve(dates, rates, dc)
    q_ts = ql.ZeroCurve(dates, div_rates, dc)
    vol = 0.25
    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc)
    bsm = ql.BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)
    heston = ql.HestonProcess(
        r_ts, q_ts, spot, vol * vol, 1.0, vol * vol, 1e-4, 0.0
    )
    heston_model = ql.HestonModel(heston)
    hw = ql.HullWhite(r_ts, 0.01, 0.01)
    return spot, q_ts, r_ts, bsm, heston_model, hw


_CASES = [
    # option_type, strike_moneyness, maturity_years
    (ql.OptionType.Call, 1.0, 5),
    (ql.OptionType.Put, 0.9, 10),
    (ql.OptionType.Call, 1.2, 2),
    (ql.OptionType.Put, 1.1, 20),
]


@pytest.mark.parametrize("option_type,moneyness,years", _CASES)
def test_heston_hw_matches_bsm_hw(option_type, moneyness, years):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    spot, q_ts, r_ts, bsm, heston_model, hw = _compare_market(today)
    maturity = today + ql.Period(years, ql.TimeUnit.Years)
    fwd = (
        moneyness
        * 100.0
        * q_ts.discount(maturity)
        / r_ts.discount(maturity)
    )
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(option_type, fwd),
        ql.EuropeanExercise(maturity),
    )
    opt.set_bsm_hull_white_pricing_engine(0.0, bsm, hw)
    bsm_npv = opt.NPV()
    opt.set_heston_hull_white_pricing_engine(heston_model, hw, 128)
    heston_npv = opt.NPV()
    assert heston_npv == pytest.approx(bsm_npv, abs=1e-5, rel=1e-5)


def test_compat_phase145_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setHestonHullWhitePricingEngine")
    assert cql.AnalyticHestonHullWhiteEngine is not None
