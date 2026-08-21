"""Phase-84 tests: SingleFactor and Deng-Li-Zhou basket engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase84():
    assert ql.__version__ == "0.85.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float, dc=None):
    if dc is None:
        dc = ql.Actual365Fixed()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# One-asset AverageBasketPayoff + SingleFactorBsmBasketEngine == European BS.
def test_single_factor_matches_european():
    today = ql.Date(3, ql.Month.July, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(18, ql.TimeUnit.Months)
    process = _bsm(today, 100.0, 0.03, 0.045, 0.40)
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)
    exercise = ql.EuropeanExercise(maturity)
    euro = ql.EuropeanOption(payoff, exercise)
    euro.set_pricing_engine(process)
    basket = ql.BasketOption(
        ql.AverageBasketPayoff(payoff, [1.0]), exercise
    )
    basket.set_single_factor_pricing_engine([process])
    assert basket.NPV() == pytest.approx(euro.NPV(), abs=1.0e-8)
    assert basket.is_expired() is False


# BasketOptionTests::testDengLiZhouWithNegativeStrike.
def test_deng_li_zhou_negative_strike():
    today = ql.Date(27, ql.Month.May, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(6, ql.TimeUnit.Months)
    spots = [220.0, 105.0, 45.0, 1e-12]
    qs = [0.04, 0.075, 0.05, 0.10]
    vols = [0.40, 0.25, 0.30, 0.25]
    processes = [_bsm(today, s, q, 0.03, v) for s, q, v in zip(spots, qs, vols)]
    rho = ql.Matrix(
        4,
        4,
        [
            1.0, 0.8, -0.2, 0.0,
            0.8, 1.0, 0.3, 0.3,
            -0.2, 0.3, 1.0, 0.0,
            0.0, 0.3, 0.0, 1.0,
        ],
    )
    opt = ql.BasketOption(
        ql.AverageBasketPayoff(
            ql.PlainVanillaPayoff(ql.OptionType.Call, -2.0),
            [0.5, -2.0, 2.0, -0.75],
        ),
        ql.EuropeanExercise(maturity),
    )
    opt.set_deng_li_zhou_pricing_engine(processes, rho)
    assert opt.NPV() == pytest.approx(3.34412, abs=1.0e-5)


def test_compat_phase84_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BasketOption, "setSingleFactorPricingEngine")
    assert hasattr(cql.BasketOption, "setDengLiZhouPricingEngine")
    assert cql.SingleFactorBsmBasketEngine is not None
    assert cql.DengLiZhouBasketEngine is not None
