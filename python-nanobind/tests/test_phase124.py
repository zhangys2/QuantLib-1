"""Phase-124 tests: AnalyticHestonForwardEuropeanEngine."""

from __future__ import annotations

import sys

import pytest

import qlnb as ql


def test_version_is_phase124():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 5)


def _relative_error(a: float, b: float, scale: float) -> float:
    return abs(a - b) / scale


# ForwardOptionTests::testHestonMCPrices Test 2 (T=0 analytic cross-check).
_OPTION_TYPES = (ql.OptionType.Call, ql.OptionType.Put)
_MONEYNESS = (0.8, 0.9, 1.0, 1.1, 1.2)
_ANALYTIC_TOLERANCE = 5e-4


@pytest.mark.parametrize("option_type", _OPTION_TYPES)
@pytest.mark.parametrize("moneyness", _MONEYNESS)
def test_heston_forward_matches_vanilla_at_reset(option_type, moneyness):
    q = 0.04
    r = 0.01
    sigma_bs = 0.245
    s = 100.0

    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()

    v0 = sigma_bs * sigma_bs
    kappa = 1.0
    theta = 0.08
    sigma = 0.39
    rho = -0.93

    spot = ql.make_quote_handle(s)
    q_ts = ql.FlatForward(today, q, dc)
    r_ts = ql.FlatForward(today, r, dc)
    process = ql.HestonProcess(r_ts, q_ts, spot, v0, kappa, theta, sigma, rho)
    model = ql.HestonModel(process)

    exercise = ql.EuropeanExercise(today + ql.Period(1, ql.TimeUnit.Years))
    reset = today
    strike = s * moneyness

    vanilla = ql.VanillaOption(
        ql.PlainVanillaPayoff(option_type, strike),
        exercise,
    )
    vanilla.set_heston_pricing_engine(model, integration_order=96)

    forward = ql.ForwardVanillaOption(
        moneyness,
        reset,
        ql.PlainVanillaPayoff(option_type, 0.0),
        exercise,
    )
    forward.set_heston_forward_pricing_engine(process, integration_order=144)

    err = _relative_error(vanilla.NPV(), forward.NPV(), s)
    assert err <= _ANALYTIC_TOLERANCE, (option_type, moneyness, err)


def test_heston_forward_future_reset_prices():
    """Smoke: forward reset in the future under Heston (suite parameters)."""
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()

    q = 0.03
    r = 0.005
    s = 100.0
    vol = 0.3
    v0 = vol * vol
    process = ql.HestonProcess(
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, q, dc),
        ql.make_quote_handle(s),
        v0,
        11.35,
        0.022,
        0.618,
        -0.5,
    )

    exercise = ql.EuropeanExercise(today + ql.Period(1, ql.TimeUnit.Years))
    reset = today + ql.Period(6, ql.TimeUnit.Months)

    forward = ql.ForwardVanillaOption(
        1.0,
        reset,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),
        exercise,
    )
    forward.set_heston_forward_pricing_engine(process)
    npv = forward.NPV()
    assert npv > 0.0
    assert npv < s


def test_native_heston_forward_snake_case_only():
    assert hasattr(ql.ForwardVanillaOption, "set_heston_forward_pricing_engine")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate ForwardVanillaOption"
        )
    assert not hasattr(ql.ForwardVanillaOption, "setHestonForwardPricingEngine")


def test_compat_phase124_aliases():
    import qlnb.compat as c

    assert hasattr(c.ForwardVanillaOption, "setHestonForwardPricingEngine")
    assert c.ForwardVanillaOption.setHestonForwardPricingEngine is (
        ql.ForwardVanillaOption.set_heston_forward_pricing_engine
    )
