"""Phase-50 tests: discrete-dividend European options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase50():
    assert ql.__version__ == "0.51.0"


def test_hull_european_known_value():
    # Mirrors DividendOptionTests::testEuropeanKnownValue (Hull 5th ed. Ex 12.8).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(40.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.09, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.30, dc),
    )
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 40.0),
        ql.EuropeanExercise(today + 180),
    )
    opt.set_dividend_pricing_engine(
        process,
        [today + 60, today + 150],
        [0.50, 0.50],
    )
    assert opt.NPV() == pytest.approx(3.67, abs=1e-2)


def test_zero_dividends_match_analytic_european():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.02, dc),
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.20, dc),
    )
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)
    exercise = ql.EuropeanExercise(today + 365)

    plain = ql.EuropeanOption(payoff, exercise)
    plain.set_pricing_engine(process)

    with_div = ql.EuropeanOption(payoff, exercise)
    with_div.set_dividend_pricing_engine(
        process,
        [today + 90, today + 270],
        [0.0, 0.0],
    )
    assert with_div.NPV() == pytest.approx(plain.NPV(), abs=1e-8)


def test_fixed_dividend_helper_and_compat():
    today = ql.Date(15, ql.Month.May, 1998)
    d = ql.FixedDividend(0.50, today + 60)
    assert d.amount() == pytest.approx(0.50)
    assert d.date() == today + 60

    divs = ql.DividendVector([today + 60, today + 150], [0.50, 0.75])
    assert len(divs) == 2
    assert divs[0].amount() == pytest.approx(0.50)
    assert divs[1].amount() == pytest.approx(0.75)
    assert divs[1].date() == today + 150

    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setDividendPricingEngine")
    assert hasattr(cql.VanillaOption, "setDividendPricingEngine")
    assert ql.AnalyticDividendEuropeanEngine is not None
