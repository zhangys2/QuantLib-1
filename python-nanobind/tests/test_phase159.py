"""Phase-159 tests: MC pure Heston via HybridHestonHullWhiteProcess."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase159():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 30)


# HybridHestonHullWhiteProcessTests::testMcPureHestonPricing
_CORR = (-0.45, 0.45, 0.25)
_STRIKES = (100.0, 75.0, 50.0, 150.0)
_TOL = 0.001


def _pure_heston_market(today: ql.Date):
    dc = ql.Actual360()
    dates = [today + ql.Period(i, ql.TimeUnit.Months) for i in range(101)]
    rates = [0.02 + 0.0002 * math.exp(math.sin(i / 10.0)) for i in range(101)]
    div_rates = [0.02 + 0.0001 * math.exp(math.sin(i / 20.0)) for i in range(101)]
    maturity = today + ql.Period(2, ql.TimeUnit.Years)
    spot = ql.make_quote_handle(100.0)
    r_ts = ql.ZeroCurve(dates, rates, dc)
    q_ts = ql.ZeroCurve(dates, div_rates, dc)
    heston = ql.HestonProcess(r_ts, q_ts, spot, 0.08, 1.5, 0.0625, 0.5, -0.8)
    hw_fwd = ql.HullWhiteForwardProcess(r_ts, 0.1, 1e-8)
    hw_fwd.set_forward_measure_time(
        dc.year_fraction(today, maturity + ql.Period(1, ql.TimeUnit.Years))
    )
    return heston, hw_fwd, maturity


@pytest.mark.parametrize("corr", _CORR)
@pytest.mark.parametrize("strike", _STRIKES)
def test_mc_pure_heston_matches_analytic(corr: float, strike: float):
    today = ql.Date(15, ql.Month.May, 2007)
    ql.set_evaluation_date(today)
    heston, hw_fwd, maturity = _pure_heston_market(today)
    joint = ql.HybridHestonHullWhiteProcess(
        heston, hw_fwd, corr, ql.HybridHestonHullWhiteDiscretization.Euler
    )
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    opt.set_heston_pricing_engine(ql.HestonModel(heston))
    expected = opt.NPV()

    opt.set_mc_heston_hull_white_pricing_engine(
        joint,
        time_steps=2,
        required_tolerance=_TOL,
        seed=42,
        antithetic=True,
        control_variate=True,
    )
    calculated = opt.NPV()
    error = opt.error_estimate()
    assert abs(calculated - expected) <= max(3.0 * error, _TOL)


def test_compat_phase159_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.VanillaOption, "setMcHestonHullWhitePricingEngine")
    assert cql.HybridHestonHullWhiteDiscretization.Euler is not None
