"""Phase-122 tests: ContinuousArithmeticAsianVecerEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase122():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 3)


# AsianOptionTests::testVecerEngine cases.
_CASES = [
    # spot, r, vol, strike, years, expected, tol
    (1.9, 0.05, 0.5, 2.0, 1, 0.193174, 1.0e-5),
    (2.0, 0.05, 0.5, 2.0, 1, 0.246416, 1.0e-5),
    (2.1, 0.05, 0.5, 2.0, 1, 0.306220, 1.0e-4),
    (2.0, 0.02, 0.1, 2.0, 1, 0.055986, 2.0e-4),
    (2.0, 0.18, 0.3, 2.0, 1, 0.218388, 1.0e-4),
    (2.0, 0.0125, 0.25, 2.0, 2, 0.172269, 1.0e-4),
    (2.0, 0.05, 0.5, 2.0, 2, 0.350095, 2.0e-4),
]


def test_vecer_engine_suite_cases():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    q_ts = ql.FlatForward(today, 0.0, dc)
    average = ql.QuoteHandle(ql.SimpleQuote(0.0))

    for spot, r, vol, strike, years, expected, tol in _CASES:
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(ql.SimpleQuote(spot)),
            q_ts,
            ql.FlatForward(today, r, dc),
            ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
        )
        maturity = today + years * 360
        opt = ql.ContinuousAveragingAsianOption(
            ql.AverageType.Arithmetic,
            ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
            ql.EuropeanExercise(maturity),
        )
        opt.set_vecer_pricing_engine(
            process,
            average,
            today,
            time_steps=200,
            asset_steps=200,
            z_min=-1.0,
            z_max=1.0,
        )
        assert opt.NPV() == pytest.approx(expected, abs=tol), (spot, r, vol, years)


def test_native_vecer_snake_case_only():
    import sys

    assert hasattr(ql.ContinuousAveragingAsianOption, "set_vecer_pricing_engine")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate ContinuousAveragingAsianOption"
        )
    assert not hasattr(ql.ContinuousAveragingAsianOption, "setVecerPricingEngine")


def test_compat_phase122_aliases():
    import qlnb.compat as c

    assert hasattr(c.ContinuousAveragingAsianOption, "setVecerPricingEngine")
    assert c.ContinuousAveragingAsianOption.setVecerPricingEngine is (
        ql.ContinuousAveragingAsianOption.set_vecer_pricing_engine
    )
