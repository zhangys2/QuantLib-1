"""Phase-138 tests: FdCEVVanillaEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase138():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 9)


def _suite_market():
    # FdCEVTests market setup.
    today = ql.Date(22, ql.Month.February, 2018)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    discount = ql.FlatForward(today, 0.15, dc)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    return today, discount, maturity


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
def test_fd_cev_matches_analytic(option_type, beta):
    today, discount, maturity = _suite_market()
    f0, alpha = 2.1, 0.75
    strike = 2.3
    eps = 1e-3
    payoff = ql.PlainVanillaPayoff(option_type, strike)
    exercise = ql.EuropeanExercise(maturity)

    analytic = ql.VanillaOption(payoff, exercise)
    analytic.set_cev_pricing_engine(f0, alpha, beta, discount)
    analytic_npv = analytic.NPV()

    analytic.set_cev_pricing_engine(f0 * (1.0 + eps), alpha, beta, discount)
    up = analytic.NPV()
    analytic.set_cev_pricing_engine(f0 * (1.0 - eps), alpha, beta, discount)
    down = analytic.NPV()
    analytic_delta = (up - down) / (2.0 * eps * f0)

    fd = ql.VanillaOption(payoff, exercise)
    fd.set_fd_cev_pricing_engine(
        f0,
        alpha,
        beta,
        discount,
        t_grid=100,
        x_grid=1000,
        damping_steps=1,
        scaling_factor=1.0,
        eps=1e-6,
    )
    assert fd.NPV() == pytest.approx(analytic_npv, abs=0.01)
    assert fd.delta() == pytest.approx(analytic_delta, abs=0.01)


def test_compat_set_fd_cev_pricing_engine():
    import qlnb.compat as c

    assert hasattr(c.VanillaOption, "setFdCevPricingEngine")
