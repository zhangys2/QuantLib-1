"""Phase-146 tests: AnalyticH1HWEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase146():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 17)


# HybridHestonHullWhiteProcessTests::testH1HWPricingEngine.
_STRIKES = [40, 80, 100, 120, 180]
_SIGMA_V = [0.3, 0.6]
_EXPECTED = [
    [0.267503, 0.235742, 0.228223, 0.223461, 0.217855],
    [0.263626, 0.211625, 0.199907, 0.193502, 0.190025],
]


@pytest.mark.parametrize("j,sigma_v", list(enumerate(_SIGMA_V)))
@pytest.mark.parametrize("i,strike", list(enumerate(_STRIKES)))
def test_h1_hw_implied_vol(j, sigma_v, i, strike):
    today = ql.Date(15, ql.Month.July, 2012)
    ql.set_evaluation_date(today)
    maturity = ql.Date(13, ql.Month.July, 2022)
    dc = ql.Actual365Fixed()

    spot = ql.make_quote_handle(100.0)
    r_ts = ql.FlatForward(today, 0.02, dc)
    q_ts = ql.FlatForward(today, 0.00, dc)
    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), 0.20, dc)
    bs = ql.BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)

    heston = ql.HestonProcess(
        r_ts, q_ts, spot, 0.05, 0.3, 0.05, sigma_v, -0.30
    )
    heston_model = ql.HestonModel(heston)
    hw = ql.HullWhite(r_ts, 0.01, 0.01)

    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(maturity),
    )
    opt.set_h1_hw_pricing_engine(heston_model, hw, 0.6, 144)
    npv = opt.NPV()
    assert npv > 0.0

    impl = opt.implied_volatility(
        npv, bs, accuracy=1e-8, max_evaluations=100
    )
    assert impl == pytest.approx(_EXPECTED[j][i], abs=1e-4)


def test_compat_phase146_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setH1HWPricingEngine")
    assert cql.AnalyticH1HWEngine is not None
