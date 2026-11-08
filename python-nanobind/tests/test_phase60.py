"""Phase-60 tests: Monte Carlo lookback engines."""

from __future__ import annotations

import math

import qlnb as ql


def test_version_is_phase60():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 61)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


def _lookback_market():
    # LookbackOptionTests::testMonteCarloLookback market, pinned date.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.06, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.1, dc),
    )
    maturity = today + _time_to_days(1.0)
    t1 = today + _time_to_days(0.25)
    return today, process, maturity, t1


def _mc_kwargs():
    # Suite uses 2000 steps + abs tolerance 0.1 (too slow for pytest).
    return dict(
        time_steps=200,
        required_samples=8192,
        seed=1,
        antithetic=True,
    )


def _assert_mc_near_analytic(option, process, abs_tol=1.0):
    option.set_pricing_engine(process)
    analytic = option.NPV()
    option.set_mc_pricing_engine(process, **_mc_kwargs())
    mc = option.NPV()
    err = option.error_estimate()
    assert err > 0.0
    assert abs(mc - analytic) < abs_tol


def test_mc_continuous_floating_lookback_call():
    _, process, maturity, _ = _lookback_market()
    option = ql.ContinuousFloatingLookbackOption(
        100.0,
        ql.FloatingTypePayoff(ql.OptionType.Call),
        ql.EuropeanExercise(maturity),
    )
    _assert_mc_near_analytic(option, process)


def test_mc_continuous_fixed_lookback_call():
    _, process, maturity, _ = _lookback_market()
    option = ql.ContinuousFixedLookbackOption(
        100.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
        ql.EuropeanExercise(maturity),
    )
    _assert_mc_near_analytic(option, process)


def test_mc_partial_floating_lookback_call():
    _, process, maturity, t1 = _lookback_market()
    option = ql.ContinuousPartialFloatingLookbackOption(
        100.0,
        1.0,
        t1,
        ql.FloatingTypePayoff(ql.OptionType.Call),
        ql.EuropeanExercise(maturity),
    )
    _assert_mc_near_analytic(option, process)


def test_mc_partial_fixed_lookback_call():
    _, process, maturity, t1 = _lookback_market()
    option = ql.ContinuousPartialFixedLookbackOption(
        t1,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
        ql.EuropeanExercise(maturity),
    )
    _assert_mc_near_analytic(option, process)


def test_compat_phase60_aliases():
    import qlnb.compat as cql

    for name in (
        "ContinuousFloatingLookbackOption",
        "ContinuousFixedLookbackOption",
        "ContinuousPartialFloatingLookbackOption",
        "ContinuousPartialFixedLookbackOption",
    ):
        cls = getattr(cql, name)
        assert cls is not None
        assert hasattr(cls, "setMcPricingEngine")
        assert hasattr(cls, "errorEstimate")
    assert ql.MCLookbackEngine is not None
