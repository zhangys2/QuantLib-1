"""Phase-105 tests: Gap / SuperFund / SuperShare payoffs."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase105():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 6)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


def _bsm_process(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def test_gap_european_haug():
    # DigitalOptionTest::testGapEuropeanValues (Haug p.88)
    today = ql.get_evaluation_date()
    maturity = today + _time_to_days(0.5)
    process = _bsm_process(today, spot=50.0, q=0.0, r=0.09, vol=0.20)
    opt = ql.EuropeanOption(
        ql.GapPayoff(ql.OptionType.Call, 50.0, 57.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_pricing_engine(process)
    assert opt.NPV() == pytest.approx(-0.0053, abs=1.0e-4)


def test_gap_payoff_inspectors():
    payoff = ql.GapPayoff(ql.OptionType.Put, 50.0, 57.0)
    assert payoff.option_type() == ql.OptionType.Put
    assert payoff.strike() == pytest.approx(50.0)
    assert payoff.second_strike() == pytest.approx(57.0)


def test_superfund_european_constructs():
    today = ql.get_evaluation_date()
    maturity = today + _time_to_days(0.5)
    opt = ql.EuropeanOption(
        ql.SuperFundPayoff(50.0, 100.0),
        ql.EuropeanExercise(maturity),
    )
    assert opt is not None


def test_superfund_payoff_inspectors():
    payoff = ql.SuperFundPayoff(50.0, 100.0)
    assert payoff.option_type() == ql.OptionType.Call
    assert payoff.strike() == pytest.approx(50.0)
    assert payoff.second_strike() == pytest.approx(100.0)


def test_supershare_european_constructs():
    today = ql.get_evaluation_date()
    maturity = today + _time_to_days(0.5)
    opt = ql.EuropeanOption(
        ql.SuperSharePayoff(50.0, 100.0, 10.0),
        ql.EuropeanExercise(maturity),
    )
    assert opt is not None


def test_supershare_payoff_inspectors():
    payoff = ql.SuperSharePayoff(50.0, 100.0, 10.0)
    assert payoff.option_type() == ql.OptionType.Call
    assert payoff.strike() == pytest.approx(50.0)
    assert payoff.second_strike() == pytest.approx(100.0)
    assert payoff.cash_payoff() == pytest.approx(10.0)


def test_compat_phase105_aliases():
    import qlnb.compat as c

    assert c.GapPayoff is not None
    assert c.SuperFundPayoff is not None
    assert c.SuperSharePayoff is not None
    assert hasattr(c.GapPayoff, "optionType")
    assert hasattr(c.GapPayoff, "secondStrike")
    assert hasattr(c.SuperSharePayoff, "cashPayoff")
