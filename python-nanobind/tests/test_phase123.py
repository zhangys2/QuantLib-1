"""Phase-123 tests: ContinuousArithmeticAsianLevyEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase123():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 4)


# AsianOptionTests::testLevyEngine / Haug p.99-100 sample cases.
# type, spot, currentAverage, strike, q, r, vol, length, elapsed, expected
_CASES = [
    (ql.OptionType.Call, 6.80, 6.80, 6.90, 0.09, 0.07, 0.14, 180, 0, 0.0944),
    (ql.OptionType.Put, 6.80, 6.80, 6.90, 0.09, 0.07, 0.14, 180, 0, 0.2237),
    (ql.OptionType.Call, 100.0, 100.0, 95.0, 0.05, 0.1, 0.15, 270, 0, 7.0544),
    (ql.OptionType.Call, 100.0, 100.0, 95.0, 0.05, 0.1, 0.15, 270, 90, 5.6731),
    (ql.OptionType.Call, 100.0, 100.0, 95.0, 0.05, 0.1, 0.15, 270, 180, 5.0806),
    (ql.OptionType.Call, 100.0, 100.0, 100.0, 0.05, 0.1, 0.35, 270, 90, 4.0687),
    (ql.OptionType.Call, 100.0, 100.0, 105.0, 0.05, 0.1, 0.15, 270, 0, 1.6729),
    (ql.OptionType.Call, 100.0, 100.0, 105.0, 0.05, 0.1, 0.35, 270, 180, 0.1552),
]


def test_levy_engine_haug_cases():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()

    for opt_type, spot, avg, strike, q, r, vol, length, elapsed, expected in _CASES:
        start = today - elapsed
        maturity = start + length
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(ql.SimpleQuote(spot)),
            ql.FlatForward(today, q, dc),
            ql.FlatForward(today, r, dc),
            ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
        )
        option = ql.ContinuousAveragingAsianOption(
            ql.AverageType.Arithmetic,
            start,
            ql.PlainVanillaPayoff(opt_type, strike),
            ql.EuropeanExercise(maturity),
        )
        option.set_levy_pricing_engine(
            process, ql.QuoteHandle(ql.SimpleQuote(avg))
        )
        assert option.NPV() == pytest.approx(expected, abs=1.0e-4), (
            spot,
            strike,
            elapsed,
        )


def test_native_levy_snake_case_only():
    import sys

    assert hasattr(ql.ContinuousAveragingAsianOption, "set_levy_pricing_engine")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate ContinuousAveragingAsianOption"
        )
    assert not hasattr(ql.ContinuousAveragingAsianOption, "setLevyPricingEngine")


def test_compat_phase123_aliases():
    import qlnb.compat as c

    assert hasattr(c.ContinuousAveragingAsianOption, "setLevyPricingEngine")
    assert c.ContinuousAveragingAsianOption.setLevyPricingEngine is (
        ql.ContinuousAveragingAsianOption.set_levy_pricing_engine
    )
