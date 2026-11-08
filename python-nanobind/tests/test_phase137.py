"""Phase-137 tests: AnalyticCEVEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase137():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 8)


def _suite_market():
    # FdCEVTests analytic CEV market setup.
    today = ql.Date(22, ql.Month.February, 2018)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    discount = ql.FlatForward(today, 0.15, dc)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    return today, discount, maturity


# Representative betas from FdCEVTests (analytic engine reference).
_CASES = [
    # option_type, beta
    (ql.OptionType.Call, -2.0),
    (ql.OptionType.Call, -0.5),
    (ql.OptionType.Call, 0.45),
    (ql.OptionType.Call, 0.9),
    (ql.OptionType.Put, 0.45),
    (ql.OptionType.Put, 1.45),
]


@pytest.mark.parametrize("option_type,beta", _CASES)
def test_cev_finite_diff_delta_consistency(option_type, beta):
    today, discount, maturity = _suite_market()
    f0, alpha = 2.1, 0.75
    strike = 2.3
    eps = 1e-3

    def price(spot: float) -> float:
        opt = ql.VanillaOption(
            ql.PlainVanillaPayoff(option_type, strike),
            ql.EuropeanExercise(maturity),
        )
        opt.set_cev_pricing_engine(spot, alpha, beta, discount)
        return opt.NPV()

    mid = price(f0)
    up = price(f0 * (1.0 + eps))
    down = price(f0 * (1.0 - eps))
    delta = (up - down) / (2.0 * eps * f0)

    assert mid > 0.0
    # Analytic CEV prices should respond smoothly to spot bumps.
    assert abs(delta) > 0.0
    assert abs(up - down) > 0.0


def test_cev_call_put_positive_and_ordered():
    today, discount, maturity = _suite_market()
    f0, alpha, beta = 2.1, 0.75, 0.45
    strike = 2.3

    call = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(maturity),
    )
    call.set_cev_pricing_engine(f0, alpha, beta, discount)
    put = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    put.set_cev_pricing_engine(f0, alpha, beta, discount)

    # Spot 2.1 < strike 2.3 → OTM call, ITM put.
    assert call.NPV() > 0.0
    assert put.NPV() > call.NPV()


def test_compat_set_cev_pricing_engine():
    import qlnb.compat as c

    assert hasattr(c.VanillaOption, "setCevPricingEngine")
