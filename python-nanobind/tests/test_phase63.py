"""Phase-63 tests: FdBatesVanillaEngine discrete-dividend overload."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase63():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 64)


def _bates_market():
    today = ql.Date(30, ql.Month.March, 2007)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    process = ql.BatesProcess(
        ql.FlatForward(today, 0.025, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,
        1.5,
        0.04,
        0.3,
        -0.9,
        2.0,
        -0.2,
        0.1,
    )
    model = ql.BatesModel(process)
    maturity = ql.Date(30, ql.Month.March, 2012)
    return today, model, maturity


def test_fd_bates_empty_dividends_match_plain():
    _, model, maturity = _bates_market()
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0)
    exercise = ql.EuropeanExercise(maturity)
    plain = ql.EuropeanOption(payoff, exercise)
    plain.set_fd_bates_pricing_engine(model, t_grid=50, x_grid=100, v_grid=30)
    div = ql.EuropeanOption(payoff, exercise)
    div.set_fd_bates_dividend_pricing_engine(
        model, [], [], t_grid=50, x_grid=100, v_grid=30
    )
    assert abs(div.NPV() - plain.NPV()) < 1.0e-10


def test_fd_bates_dividends_cheapen_call():
    today, model, maturity = _bates_market()
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)
    exercise = ql.EuropeanExercise(maturity)
    plain = ql.EuropeanOption(payoff, exercise)
    plain.set_fd_bates_pricing_engine(model, t_grid=50, x_grid=100, v_grid=30)
    div = ql.EuropeanOption(payoff, exercise)
    div.set_fd_bates_dividend_pricing_engine(
        model,
        [today + ql.Period(1, ql.TimeUnit.Years)],
        [5.0],
        t_grid=50,
        x_grid=100,
        v_grid=30,
    )
    assert div.NPV() < plain.NPV()
    assert div.NPV() > 0.0


def test_fd_bates_tiny_jump_dividends_match_heston():
    # Bates λ → 0 should track FdHestonVanillaEngine with the same dividends.
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    r = ql.FlatForward(today, 0.05, dc)
    q = ql.FlatForward(today, 0.0, dc)
    spot = ql.make_quote_handle(100.0)
    heston = ql.HestonProcess(r, q, spot, 0.04, 1.0, 0.04, 0.001, 0.0)
    bates = ql.BatesProcess(
        r, q, spot, 0.04, 1.0, 0.04, 0.001, 0.0, 1.0e-8, -0.2, 0.1
    )
    maturity = ql.Date(28, ql.Month.March, 2006)
    div_dates = []
    div_amounts = []
    d = today + ql.Period(3, ql.TimeUnit.Months)
    while d < maturity:
        div_dates.append(d)
        div_amounts.append(1.0)
        d = d + ql.Period(6, ql.TimeUnit.Months)
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 95.0)
    exercise = ql.EuropeanExercise(maturity)
    h_opt = ql.VanillaOption(payoff, exercise)
    h_opt.set_fd_heston_dividend_pricing_engine(
        ql.HestonModel(heston),
        div_dates,
        div_amounts,
        t_grid=50,
        x_grid=100,
        v_grid=30,
    )
    b_opt = ql.VanillaOption(payoff, exercise)
    b_opt.set_fd_bates_dividend_pricing_engine(
        ql.BatesModel(bates),
        div_dates,
        div_amounts,
        t_grid=50,
        x_grid=100,
        v_grid=30,
    )
    assert abs(b_opt.NPV() - h_opt.NPV()) < 0.05


def test_compat_phase63_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setFdBatesDividendPricingEngine")
    assert hasattr(cql.VanillaOption, "setFdBatesDividendPricingEngine")
