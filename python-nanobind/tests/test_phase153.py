"""Phase-153 tests: MCHestonHullWhiteEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase153():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 24)


# HybridHestonHullWhiteProcessTests::testMcVanillaPricing
_CORR = (-0.9, -0.5, 0.0, 0.5, 0.9)
_STRIKE = 100.0


def _mc_market(today: ql.Date):
    dc = ql.Actual360()
    dates = [today + ql.Period(i, ql.TimeUnit.Years) for i in range(41)]
    rates = [0.03 + 0.0003 * math.exp(math.sin(i / 4.0)) for i in range(41)]
    div_rates = [0.02 + 0.0001 * math.exp(math.sin(i / 5.0)) for i in range(41)]
    maturity = today + ql.Period(20, ql.TimeUnit.Years)
    spot = ql.make_quote_handle(100.0)
    r_ts = ql.ZeroCurve(dates, rates, dc)
    q_ts = ql.ZeroCurve(dates, div_rates, dc)
    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), 0.25, dc)
    bsm = ql.BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)
    heston = ql.HestonProcess(
        r_ts, q_ts, spot, 0.0625, 0.5, 0.0625, 1e-5, 0.3
    )
    hw_fwd = ql.HullWhiteForwardProcess(r_ts, 0.01, 0.01)
    hw_fwd.set_forward_measure_time(dc.year_fraction(today, maturity))
    hw = ql.HullWhite(r_ts, hw_fwd.a(), hw_fwd.sigma())
    return bsm, heston, hw_fwd, hw, maturity


@pytest.mark.parametrize("corr", _CORR)
def test_mc_heston_hull_white_vs_analytic(corr: float):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    bsm, heston, hw_fwd, hw, maturity = _mc_market(today)
    joint = ql.HybridHestonHullWhiteProcess(heston, hw_fwd, corr)
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, _STRIKE),
        ql.EuropeanExercise(maturity),
    )
    opt.set_mc_heston_hull_white_pricing_engine(
        joint,
        time_steps=1,
        required_tolerance=0.05,
        seed=42,
        antithetic=True,
        control_variate=True,
    )
    mc_npv = opt.NPV()
    mc_err = opt.error_estimate()

    opt.set_bsm_hull_white_pricing_engine(corr, bsm, hw)
    expected = opt.NPV()
    if corr != 0.0:
        assert abs(mc_npv - expected) <= 3.0 * mc_err
    else:
        assert mc_npv == pytest.approx(expected, abs=1e-4)


def test_compat_phase153_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setMcHestonHullWhitePricingEngine")
    assert hasattr(cql.VanillaOption, "setMcHestonHullWhitePricingEngine")
    assert cql.MCHestonHullWhiteEngine is not None
    assert cql.HullWhiteForwardProcess is not None
    assert cql.HybridHestonHullWhiteProcess is not None
