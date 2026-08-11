"""Phase-49 tests: COS / exponential-fitting Heston engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase49():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 50)


def test_cos_heston_engine_prices():
    # Mirrors HestonModelTests::testCosHestonEngine.
    today = ql.Date(7, ql.Month.February, 2017)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.15, dc),
        ql.FlatForward(today, 0.07, dc),
        ql.make_quote_handle(100.0),
        0.1,    # v0
        4.0,    # kappa
        0.22,   # theta
        1.8,    # sigma
        -0.75,  # rho
    )
    model = ql.HestonModel(process)
    maturity = today + ql.Period(1, ql.TimeUnit.Years)
    cases = [
        (ql.OptionType.Call, 120.0, 9.364410588426075),
        (ql.OptionType.Call, 250.0, 0.01036797658132471),
        (ql.OptionType.Put, 80.0, 5.319092971836708),
        (ql.OptionType.Put, 10.0, 0.01032681906278383),
    ]
    for option_type, strike, expected in cases:
        opt = ql.EuropeanOption(
            ql.PlainVanillaPayoff(option_type, strike),
            ql.EuropeanExercise(maturity),
        )
        opt.set_cos_heston_pricing_engine(model, L=25, N=600)
        assert opt.NPV() == pytest.approx(expected, abs=1e-10)


def test_exponential_fitting_heston_matches_analytic():
    today = ql.Date(7, ql.Month.February, 2017)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.02, dc),
        ql.make_quote_handle(100.0),
        0.04,
        1.5,
        0.04,
        0.3,
        -0.5,
    )
    model = ql.HestonModel(process)
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)
    exercise = ql.EuropeanExercise(today + ql.Period(1, ql.TimeUnit.Years))

    analytic = ql.EuropeanOption(payoff, exercise)
    analytic.set_heston_pricing_engine(model, integration_order=144)

    fitted = ql.EuropeanOption(payoff, exercise)
    fitted.set_exponential_fitting_heston_pricing_engine(model)
    assert fitted.NPV() == pytest.approx(analytic.NPV(), rel=1e-4, abs=1e-4)


def test_helper_cos_engine_and_compat():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.04, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,
        1.0,
        0.04,
        0.2,
        -0.5,
    )
    model = ql.HestonModel(process)
    helper = ql.HestonModelHelper(
        ql.Period(1, ql.TimeUnit.Years),
        ql.NullCalendar(),
        ql.make_quote_handle(100.0),
        100.0,
        ql.make_quote_handle(0.2),
        ql.FlatForward(today, 0.04, dc),
        ql.FlatForward(today, 0.0, dc),
    )
    helper.set_cos_heston_pricing_engine(model, L=16, N=200)
    assert helper.model_value() > 0.0

    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setCosHestonPricingEngine")
    assert hasattr(
        cql.EuropeanOption, "setExponentialFittingHestonPricingEngine"
    )
    assert hasattr(cql.HestonModelHelper, "setCosHestonPricingEngine")
    assert ql.HestonComplexLogFormula.OptimalCV is not None
    assert ql.COSHestonEngine is not None
    assert ql.ExponentialFittingHestonEngine is not None
