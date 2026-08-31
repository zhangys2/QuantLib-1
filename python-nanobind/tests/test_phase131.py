"""Phase-131 tests: AnalyticDigitalAmericanKOEngine."""

from __future__ import annotations

import math
import sys

import pytest

import qlnb as ql


def test_version_is_phase131():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 2)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


def _bsm(today, spot, q, r, vol):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# DigitalOptionTests::testCashAtExpiryOrNothingAmericanValues — KO cases.
_CASH_KO_CASES = [
    (ql.OptionType.Put, 100.0, 105.0, 0.0, 0.10, 0.5, 0.20, 4.9081),
    (ql.OptionType.Call, 100.0, 95.0, 0.0, 0.10, 0.5, 0.20, 3.0461),
]


@pytest.mark.parametrize(
    "option_type,strike,spot,q,r,t,vol,expected",
    _CASH_KO_CASES,
)
def test_cash_at_expiry_ko(option_type, strike, spot, q, r, t, vol, expected):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, spot, q, r, vol)
    opt = ql.VanillaOption(
        ql.CashOrNothingPayoff(option_type, strike, 15.0),
        ql.AmericanExercise(today, today + _time_to_days(t), payoff_at_expiry=True),
    )
    opt.set_digital_american_ko_pricing_engine(process)
    assert opt.NPV() == pytest.approx(expected, abs=1.0e-4)


# DigitalOptionTests::testAssetAtExpiryOrNothingAmericanValues — KO cases.
_ASSET_KO_CASES = [
    (ql.OptionType.Put, 100.0, 105.0, 0.0, 0.10, 0.5, 0.20, 40.1574),
    (ql.OptionType.Call, 100.0, 95.0, 0.0, 0.10, 0.5, 0.20, 17.2983),
]


@pytest.mark.parametrize(
    "option_type,strike,spot,q,r,t,vol,expected",
    _ASSET_KO_CASES,
)
def test_asset_at_expiry_ko(option_type, strike, spot, q, r, t, vol, expected):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, spot, q, r, vol)
    opt = ql.VanillaOption(
        ql.AssetOrNothingPayoff(option_type, strike),
        ql.AmericanExercise(today, today + _time_to_days(t), payoff_at_expiry=True),
    )
    opt.set_digital_american_ko_pricing_engine(process)
    assert opt.NPV() == pytest.approx(expected, abs=1.0e-4)


def test_cash_at_expiry_knock_in_still_uses_ki_engine():
    # Same market as KO put, but knock-in engine + payoff_at_expiry.
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, 105.0, 0.0, 0.10, 0.20)
    opt = ql.VanillaOption(
        ql.CashOrNothingPayoff(ql.OptionType.Put, 100.0, 15.0),
        ql.AmericanExercise(today, today + _time_to_days(0.5), payoff_at_expiry=True),
    )
    opt.set_digital_american_pricing_engine(process)
    assert opt.NPV() == pytest.approx(9.3604, abs=1.0e-4)


def test_digital_american_ko_factory_alias():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, 105.0, 0.0, 0.10, 0.20)
    opt = ql.VanillaOption(
        ql.CashOrNothingPayoff(ql.OptionType.Put, 100.0, 15.0),
        ql.AmericanExercise(today, today + _time_to_days(0.5), payoff_at_expiry=True),
    )
    opt.set_digital_american_ko_pricing_engine(
        ql.AnalyticDigitalAmericanKOEngine(process)
    )
    assert opt.NPV() == pytest.approx(4.9081, abs=1.0e-4)


def test_native_digital_american_ko_snake_case_only():
    assert hasattr(ql.VanillaOption, "set_digital_american_ko_pricing_engine")
    assert hasattr(ql, "AnalyticDigitalAmericanKOEngine")
    if "qlnb.compat" in sys.modules:
        pytest.skip("qlnb.compat already loaded; camelCase aliases mutate VanillaOption")
    assert not hasattr(ql.VanillaOption, "setDigitalAmericanKoPricingEngine")


def test_compat_phase131_aliases():
    import qlnb.compat as c

    assert hasattr(c.VanillaOption, "setDigitalAmericanKoPricingEngine")
    assert c.VanillaOption.setDigitalAmericanKoPricingEngine is (
        ql.VanillaOption.set_digital_american_ko_pricing_engine
    )
