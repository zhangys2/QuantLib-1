"""Phase-51 tests: FD discrete-dividend vanilla engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase51():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 52)


def test_fd_bs_escrowed_matches_analytic():
    # Mirrors DividendOptionTests escrowed PDE vs AnalyticDividendEuropeanEngine.
    today = ql.Date(12, ql.Month.October, 2019)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    spot = 100.0
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, 0.063, dc),
        ql.FlatForward(today, 0.094, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.3, dc),
    )
    maturity = today + ql.Period(1, ql.TimeUnit.Years)
    div_dates = [
        today + ql.Period(3, ql.TimeUnit.Months),
        today + ql.Period(9, ql.TimeUnit.Months),
    ]
    div_amounts = [8.3, 6.8]
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, spot)
    exercise = ql.EuropeanExercise(maturity)

    analytic = ql.EuropeanOption(payoff, exercise)
    analytic.set_dividend_pricing_engine(process, div_dates, div_amounts)

    fd = ql.EuropeanOption(payoff, exercise)
    fd.set_fd_dividend_pricing_engine(
        process,
        div_dates,
        div_amounts,
        t_grid=50,
        x_grid=200,
        damping_steps=1,
        cash_dividend_model=ql.CashDividendModel.Escrowed,
    )
    assert fd.NPV() == pytest.approx(analytic.NPV(), abs=0.0025)
    assert fd.delta() == pytest.approx(analytic.delta(), abs=0.0025)


def test_fd_heston_dividends_cached():
    # Mirrors HestonModelTests::testFdVanillaWithDividendsVsCached.
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,
        1.0,
        0.04,
        0.001,
        0.0,
    )
    model = ql.HestonModel(process)
    maturity = ql.Date(28, ql.Month.March, 2006)
    div_dates = []
    div_amounts = []
    d = today + ql.Period(3, ql.TimeUnit.Months)
    while d < maturity:
        div_dates.append(d)
        div_amounts.append(1.0)
        d = d + ql.Period(6, ql.TimeUnit.Months)

    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 95.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_fd_heston_dividend_pricing_engine(
        model,
        div_dates,
        div_amounts,
        t_grid=200,
        x_grid=400,
        v_grid=100,
    )
    assert opt.NPV() == pytest.approx(12.946, abs=5e-3)


def test_cash_dividend_model_and_compat():
    assert ql.CashDividendModel.Spot is not None
    assert ql.CashDividendModel.Escrowed is not None
    assert ql.FdBlackScholesVanillaEngine is not None

    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setFdDividendPricingEngine")
    assert hasattr(cql.EuropeanOption, "setFdHestonDividendPricingEngine")
    assert hasattr(cql.VanillaOption, "setFdDividendPricingEngine")
    assert hasattr(cql.VanillaOption, "setFdHestonDividendPricingEngine")
