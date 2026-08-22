"""Phase-88 tests: MC European and American basket engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase88():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 89)


def _time_to_days(t: float) -> int:
    # Matches test-suite/utilities.hpp timeToDays (lround, 360 days/year).
    return int(round(t * 360))


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# BasketOptionTests::testEuroTwoValues — Haug Kirk futures spread, MC seed 42.
def test_mc_european_kirk_haug():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    p1 = _bsm(today, 122.0, 0.10, 0.10, 0.20)
    p2 = _bsm(today, 120.0, 0.10, 0.10, 0.20)
    rho = ql.Matrix(2, 2, [1.0, -0.50, -0.50, 1.0])
    opt = ql.BasketOption(
        ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 3.0)),
        ql.EuropeanExercise(today + _time_to_days(0.1)),
    )
    opt.set_mc_european_pricing_engine(
        [p1, p2],
        rho,
        steps_per_year=1,
        required_samples=10000,
        seed=42,
    )
    # Suite uses relativeError(npv, expected, s1) with tol 0.01.
    assert abs(opt.NPV() - 4.7530) / 122.0 < 0.01
    assert opt.is_expired() is False


# BasketOptionTests::testEuroTwoValues — Haug min-basket Stulz 10.898.
def test_mc_european_stulz_min():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    p1 = _bsm(today, 100.0, 0.00, 0.05, 0.30)
    p2 = _bsm(today, 100.0, 0.00, 0.05, 0.30)
    rho = ql.Matrix(2, 2, [1.0, 0.90, 0.90, 1.0])
    opt = ql.BasketOption(
        ql.MinBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)),
        ql.EuropeanExercise(today + _time_to_days(1.0)),
    )
    opt.set_mc_european_pricing_engine(
        [p1, p2],
        rho,
        steps_per_year=1,
        required_samples=10000,
        seed=42,
    )
    assert abs(opt.NPV() - 10.898) / 100.0 < 0.01


# BasketOptionTests::testOddSamples — 1-asset American max-basket put.
def test_mc_american_one_asset_put():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 80.0, 0.0, 0.06, 0.4)
    opt = ql.BasketOption(
        ql.MaxBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0)),
        ql.AmericanExercise(today, today + _time_to_days(0.5)),
    )
    opt.set_mc_american_pricing_engine(
        [process],
        ql.Matrix(1, 1, [1.0]),
        time_steps=53,
        required_samples=10001,
        calibration_samples=2500,
        seed=0,
        antithetic=True,
    )
    assert opt.NPV() == pytest.approx(21.6059, abs=0.25)


def test_compat_phase88_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BasketOption, "setMCEuropeanPricingEngine")
    assert hasattr(cql.BasketOption, "setMCAmericanPricingEngine")
    assert cql.MCEuropeanBasketEngine is not None
    assert cql.MCAmericanBasketEngine is not None
