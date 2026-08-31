"""Phase-143 tests: AnalyticPerformanceEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase143():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 14)


def _bsm(today, spot, q, r, vol):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(spot)),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _performance_option(today, moneyness, length, frequency, process):
    tenor = ql.Period(frequency)
    maturity = today + (tenor * length)
    reset = []
    d = today + tenor
    while d < maturity:
        reset.append(d)
        d = d + tenor
    opt = ql.CliquetOption(
        ql.PercentageStrikePayoff(ql.OptionType.Call, moneyness),
        ql.EuropeanExercise(maturity),
        reset,
    )
    opt.set_performance_pricing_engine(process)
    return opt


def test_performance_npv_greeks():
    # CliquetOptionTests::testMcPerformance-style market (fixed date).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 100.0, 0.04, 0.01, 0.10)
    opt = _performance_option(
        today, 1.1, 2, ql.Frequency.Semiannual, process
    )
    # Characterized against AnalyticPerformanceEngine on this fixed market.
    assert opt.NPV() == pytest.approx(0.0018776478428237022, abs=1e-12)
    # Performance payoffs are homogeneous of degree 0 in spot → delta 0.
    assert opt.delta() == pytest.approx(0.0, abs=1e-12)
    assert opt.vega() != 0.0
    assert opt.is_expired() is False


def test_performance_vega_fd():
    # CliquetOptionTests::testPerformanceGreeks (vega bump).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    vol = 0.50
    process = _bsm(today, 100.0, 0.04, 0.05, vol)
    opt = _performance_option(
        today, 0.9, 2, ql.Frequency.Quarterly, process
    )
    analytic_vega = opt.vega()
    dv = vol * 1.0e-4
    up = _performance_option(
        today, 0.9, 2, ql.Frequency.Quarterly, _bsm(today, 100.0, 0.04, 0.05, vol + dv)
    ).NPV()
    down = _performance_option(
        today, 0.9, 2, ql.Frequency.Quarterly, _bsm(today, 100.0, 0.04, 0.05, vol - dv)
    ).NPV()
    fd_vega = (up - down) / (2.0 * dv)
    assert analytic_vega == pytest.approx(fd_vega, abs=1.0e-5)


def test_performance_differs_from_cliquet():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 60.0, 0.04, 0.08, 0.30)
    opt = ql.CliquetOption(
        ql.PercentageStrikePayoff(ql.OptionType.Call, 1.1),
        ql.EuropeanExercise(today + 360),
        [today + 90],
    )
    opt.set_pricing_engine(process)
    cliquet_npv = opt.NPV()
    opt.set_performance_pricing_engine(process)
    perf_npv = opt.NPV()
    assert cliquet_npv == pytest.approx(4.4064, abs=1.0e-4)
    assert perf_npv != pytest.approx(cliquet_npv, abs=1.0e-4)


def test_compat_phase143_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CliquetOption, "setPerformancePricingEngine")
    assert cql.AnalyticPerformanceEngine is not None
