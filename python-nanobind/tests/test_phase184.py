"""Phase-184 tests: market-model numeraire measures."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase184():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 55)


def _drift_calculator_evolution():
    # MarketModelTests::testDriftCalculator evolution schedule (integer times).
    n = 10
    rate_times = [float(i) for i in range(1, n + 1)]
    evolution_times = [float(i) for i in range(1, n)]
    return ql.EvolutionDescription(rate_times, evolution_times)


def test_terminal_measure():
    evolution = _drift_calculator_evolution()
    numeraires = ql.terminal_measure(evolution)
    assert numeraires == [9] * 9
    assert ql.is_in_terminal_measure(evolution, numeraires)


def test_money_market_measures():
    evolution = _drift_calculator_evolution()
    mm = ql.money_market_measure(evolution)
    assert mm == list(range(9))
    assert ql.is_in_money_market_measure(evolution, mm)

    offset = 5
    mm_plus = ql.money_market_plus_measure(evolution, offset)
    assert mm_plus == [5, 6, 7, 8, 9, 9, 9, 9, 9]
    assert ql.is_in_money_market_plus_measure(evolution, mm_plus, offset)


def test_compat_phase184_aliases():
    import qlnb.compat as cql

    assert hasattr(cql, "terminalMeasure")
    assert hasattr(cql, "moneyMarketMeasure")
    assert hasattr(cql, "moneyMarketPlusMeasure")
    assert hasattr(cql, "isInTerminalMeasure")
    assert hasattr(cql, "isInMoneyMarketMeasure")
    assert hasattr(cql, "isInMoneyMarketPlusMeasure")
