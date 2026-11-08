"""Phase-136 tests: AnalyticPDFHestonEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase136():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 7)


def _suite_model():
    # HestonModelTests::testAnalyticPDFHestonEngine market setup.
    today = ql.Date(5, ql.Month.January, 2014)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.07, dc),
        ql.FlatForward(today, 0.185, dc),
        ql.make_quote_handle(100.0),
        0.1,
        4.0,
        0.05,
        1.0,
        -0.5,
    )
    return today, ql.HestonModel(process)


@pytest.mark.parametrize("strike", [40.0, 80.0, 100.0, 120.0, 180.0])
def test_pdf_matches_analytic_heston_vanilla(strike):
    today, model = _suite_model()
    maturity = ql.Date(5, ql.Month.July, 2014)
    exercise = ql.EuropeanExercise(maturity)
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, strike)

    pdf = ql.VanillaOption(payoff, exercise)
    pdf.set_pdf_heston_pricing_engine(model, gauss_lobatto_eps=1e-6)

    ref = ql.VanillaOption(payoff, exercise)
    ref.set_heston_pricing_engine(model, integration_order=178)

    assert pdf.NPV() == pytest.approx(ref.NPV(), abs=3.0e-6)


@pytest.mark.parametrize("strike", [40.0, 100.0, 160.0])
def test_pdf_digital_vs_call_spread(strike):
    today, model = _suite_model()
    maturity = ql.Date(5, ql.Month.July, 2014)
    exercise = ql.EuropeanExercise(maturity)
    eps = 0.01

    digital = ql.VanillaOption(
        ql.CashOrNothingPayoff(ql.OptionType.Call, strike, 1.0),
        exercise,
    )
    digital.set_pdf_heston_pricing_engine(model, gauss_lobatto_eps=1e-6)

    long_call = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike - eps),
        exercise,
    )
    long_call.set_heston_pricing_engine(model, integration_order=178)
    short_call = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike + eps),
        exercise,
    )
    short_call.set_heston_pricing_engine(model, integration_order=178)
    expected = (long_call.NPV() - short_call.NPV()) / (2.0 * eps)

    assert digital.NPV() == pytest.approx(expected, abs=1.0e-6)


def test_factory_alias_and_compat():
    today, model = _suite_model()
    maturity = ql.Date(5, ql.Month.July, 2014)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_pdf_heston_pricing_engine(ql.AnalyticPDFHestonEngine(model))
    assert opt.NPV() > 0.0

    import qlnb.compat as c

    assert hasattr(c.VanillaOption, "setPdfHestonPricingEngine")
