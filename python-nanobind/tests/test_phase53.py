"""Phase-53 tests: FdmQuantoHelper and FD quanto vanilla engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase53():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 54)


def test_fdm_quanto_helper_adjustment():
    # Mirrors QuantoOptionTests quanto drift check.
    today = ql.Date(21, ql.Month.April, 2019)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    domestic_r, foreign_r = 0.025, 0.075
    vol, fx_vol, corr = 0.3, 0.15, -0.75
    helper = ql.FdmQuantoHelper(
        ql.FlatForward(today, domestic_r, dc),
        ql.FlatForward(today, foreign_r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), fx_vol, dc),
        corr,
    )
    expected = domestic_r - foreign_r + corr * vol * fx_vol
    assert helper.quanto_adjustment(vol, 0.0, 1.0) == pytest.approx(
        expected, abs=1e-10
    )


def test_fd_bs_quanto_matches_analytic():
    # Mirrors QuantoOptionTests::testPDEOptionValues (first Call case).
    today = ql.Date(21, ql.Month.April, 2019)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.04, dc),
        ql.FlatForward(today, 0.08, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.2, dc),
    )
    foreign = ql.FlatForward(today, 0.05, dc)
    fx_vol = ql.BlackConstantVol(today, ql.NullCalendar(), 0.10, dc)
    helper = ql.FdmQuantoHelper(
        ql.FlatForward(today, 0.08, dc), foreign, fx_vol, 0.3
    )
    maturity = today + 180  # t=0.5 on Actual360
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 105.0)
    exercise = ql.EuropeanExercise(maturity)

    fd = ql.EuropeanOption(payoff, exercise)
    fd.set_fd_quanto_pricing_engine(
        process, helper, t_grid=100, x_grid=500, damping_steps=1
    )

    analytic = ql.QuantoVanillaOption(payoff, exercise)
    analytic.set_pricing_engine(process, foreign, fx_vol, 0.3)
    assert fd.NPV() == pytest.approx(analytic.NPV(), abs=2e-4)


def test_american_quanto_dividend_cached():
    # Mirrors QuantoOptionTests::testAmericanQuantoOption (BS path).
    today = ql.Date(21, ql.Month.April, 2019)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.03, dc),
        ql.FlatForward(today, 0.025, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.3, dc),
    )
    helper = ql.FdmQuantoHelper(
        ql.FlatForward(today, 0.025, dc),
        ql.FlatForward(today, 0.075, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.15, dc),
        -0.75,
    )
    maturity = today + ql.Period(9, ql.TimeUnit.Months)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 105.0),
        ql.AmericanExercise(today, maturity),
    )
    opt.set_fd_quanto_dividend_pricing_engine(
        process,
        [today + ql.Period(6, ql.TimeUnit.Months)],
        [8.0],
        helper,
        t_grid=100,
        x_grid=400,
        damping_steps=1,
    )
    assert opt.NPV() == pytest.approx(8.90611734, abs=1e-4)


def test_heston_quanto_dividend_and_compat():
    today = ql.Date(21, ql.Month.April, 2019)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    domestic = ql.FlatForward(today, 0.025, dc)
    dividend = ql.FlatForward(today, 0.03, dc)
    vol = 0.3
    process = ql.HestonProcess(
        domestic,
        dividend,
        ql.make_quote_handle(100.0),
        vol * vol,
        1.0,
        vol * vol,
        1e-4,
        0.0,
    )
    model = ql.HestonModel(process)
    helper = ql.FdmQuantoHelper(
        domestic,
        ql.FlatForward(today, 0.075, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.15, dc),
        -0.75,
    )
    maturity = today + ql.Period(9, ql.TimeUnit.Months)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 105.0),
        ql.AmericanExercise(today, maturity),
    )
    opt.set_fd_heston_quanto_dividend_pricing_engine(
        model,
        [today + ql.Period(6, ql.TimeUnit.Months)],
        [8.0],
        helper,
        t_grid=100,
        x_grid=400,
        v_grid=3,
        damping_steps=1,
    )
    assert opt.NPV() == pytest.approx(8.90611734, abs=1e-4)

    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setFdQuantoPricingEngine")
    assert hasattr(cql.VanillaOption, "setFdQuantoDividendPricingEngine")
    assert hasattr(cql.VanillaOption, "setFdHestonQuantoDividendPricingEngine")
