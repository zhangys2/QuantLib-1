"""Phase-52 tests: CashDividendEuropeanEngine (Spot / Escrowed)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase52():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 53)


def _single_div_process(today: ql.Date):
    dc = ql.Actual365Fixed()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.025, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.3, dc),
    )


def test_cash_dividend_engine_matches_fd_spot_and_escrowed():
    # Mirrors DividendOptionTests::testCashDividendEuropeanEngineWithSingleDividends
    # for a mid-life dividend date.
    today = ql.Date(11, ql.Month.November, 2025)
    ql.set_evaluation_date(today)
    process = _single_div_process(today)
    maturity = today + ql.Period(18, ql.TimeUnit.Months)
    div_dates = [today + ql.Period(6, ql.TimeUnit.Months)]
    div_amounts = [5.0]
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 95.0)
    exercise = ql.EuropeanExercise(maturity)

    for model in (ql.CashDividendModel.Spot, ql.CashDividendModel.Escrowed):
        fd = ql.EuropeanOption(payoff, exercise)
        fd.set_fd_dividend_pricing_engine(
            process,
            div_dates,
            div_amounts,
            t_grid=200,
            x_grid=400,
            cash_dividend_model=model,
        )
        cash = ql.EuropeanOption(payoff, exercise)
        cash.set_cash_dividend_pricing_engine(
            process, div_dates, div_amounts, cash_dividend_model=model
        )
        assert cash.NPV() == pytest.approx(fd.NPV(), abs=0.001)


def test_cash_dividend_put_and_compat():
    today = ql.Date(11, ql.Month.November, 2025)
    ql.set_evaluation_date(today)
    process = _single_div_process(today)
    maturity = today + ql.Period(18, ql.TimeUnit.Months)
    div_dates = [today + ql.Period(6, ql.TimeUnit.Months)]
    div_amounts = [5.0]

    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 95.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_cash_dividend_pricing_engine(
        process,
        div_dates,
        div_amounts,
        cash_dividend_model=ql.CashDividendModel.Escrowed,
    )
    assert opt.NPV() > 0.0

    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setCashDividendPricingEngine")
    assert hasattr(cql.VanillaOption, "setCashDividendPricingEngine")
    assert ql.CashDividendEuropeanEngine is not None
