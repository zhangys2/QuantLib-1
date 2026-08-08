"""Phase-34 tests: cliquet / ratchet options (Haug p.37 / AnalyticCliquetEngine)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase34():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 35)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


def test_percentage_strike_payoff():
    payoff = ql.PercentageStrikePayoff(ql.OptionType.Call, 1.1)
    assert payoff.strike() == pytest.approx(1.1)
    assert payoff.moneyness() == pytest.approx(1.1)
    assert payoff.option_type() == ql.OptionType.Call


def test_cliquet_haug():
    # Mirrors CliquetOptionTests::testValues (Haug p.37).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 360
    process = _bsm(today, 60.0, 0.04, 0.08, 0.30)
    option = ql.CliquetOption(
        ql.PercentageStrikePayoff(ql.OptionType.Call, 1.1),
        ql.EuropeanExercise(maturity),
        [today + 90],
    )
    option.set_pricing_engine(process)
    assert option.NPV() == pytest.approx(4.4064, abs=1.0e-4)
    assert option.is_expired() is False
    # Analytic engine fills greeks; smoke-check they are finite and non-zero.
    assert option.delta() != 0.0
    assert option.vega() != 0.0


def test_cliquet_factory_alias():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 60.0, 0.04, 0.08, 0.30)
    alias = ql.AnalyticCliquetEngine(process)
    option = ql.CliquetOption(
        ql.PercentageStrikePayoff(ql.OptionType.Call, 1.1),
        ql.EuropeanExercise(today + 360),
        [today + 90],
    )
    option.set_pricing_engine(alias)
    assert option.NPV() == pytest.approx(4.4064, abs=1.0e-4)


def test_compat_phase34_aliases():
    import qlnb.compat as cql

    assert cql.PercentageStrikePayoff is not None
    assert hasattr(cql.PercentageStrikePayoff, "optionType")
    assert cql.CliquetOption is not None
    assert hasattr(cql.CliquetOption, "setPricingEngine")
    assert hasattr(cql.CliquetOption, "isExpired")
