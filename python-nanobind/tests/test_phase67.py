"""Phase-67 tests: FdBlackScholesBarrierEngine (+ discrete dividends)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase67():
    assert ql.__version__ == "0.68.0"


def _haug_down_in_call():
    # BarrierOptionTest / Haug DownIn call (Phase 4 analytic golden 1.64005).
    todays = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(todays)
    dc = ql.Actual360()
    maturity = todays + 360
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(todays, 0.02, dc),
        ql.FlatForward(todays, 0.05, dc),
        ql.BlackConstantVol(todays, ql.TARGET(), 0.20, dc),
    )
    option = ql.BarrierOption(
        ql.BarrierType.DownIn,
        90.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    return process, option


def test_fd_bs_barrier_matches_analytic_haug():
    process, fd = _haug_down_in_call()
    fd.set_fd_pricing_engine(process, t_grid=200, x_grid=400)
    _, analytic = _haug_down_in_call()
    analytic.set_pricing_engine(process)
    assert fd.NPV() == pytest.approx(analytic.NPV(), abs=5.0e-3)
    assert fd.NPV() == pytest.approx(1.64005, abs=5.0e-3)


def test_fd_bs_barrier_empty_dividends_match_plain():
    process, plain = _haug_down_in_call()
    plain.set_fd_pricing_engine(process, t_grid=100, x_grid=200)
    _, div = _haug_down_in_call()
    div.set_fd_dividend_pricing_engine(process, [], [], t_grid=100, x_grid=200)
    assert div.NPV() == pytest.approx(plain.NPV(), abs=1.0e-10)


def test_fd_bs_barrier_dividend_goldens():
    # BarrierOptionTest::testDividendBarrier (low-vol cash dividend).
    today = ql.Date(11, ql.Month.February, 2018)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    maturity = today + ql.Period(1, ql.TimeUnit.Years)
    r_ts = ql.FlatForward(today, 0.05, dc)
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        r_ts,
        ql.BlackConstantVol(today, ql.TARGET(), 0.02, dc),
    )
    div_date = today + ql.Period(6, ql.TimeUnit.Months)
    div_amount = 30.0
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, 105.0)
    exercise = ql.EuropeanExercise(maturity)
    rebate = 5.0

    down_in = ql.BarrierOption(
        ql.BarrierType.DownIn, 80.0, rebate, payoff, exercise
    )
    down_in.set_fd_dividend_pricing_engine(
        process, [div_date], [div_amount], t_grid=100, x_grid=100
    )
    assert down_in.NPV() == pytest.approx(29.154, rel=2.0e-4)

    up_in = ql.BarrierOption(
        ql.BarrierType.UpIn, 120.0, rebate, payoff, exercise
    )
    up_in.set_fd_dividend_pricing_engine(
        process, [div_date], [div_amount], t_grid=100, x_grid=100
    )
    assert up_in.NPV() == pytest.approx(4.765, rel=2.0e-4)

    down_out = ql.BarrierOption(
        ql.BarrierType.DownOut, 80.0, rebate, payoff, exercise
    )
    down_out.set_fd_dividend_pricing_engine(
        process, [div_date], [div_amount], t_grid=100, x_grid=100
    )
    assert down_out.NPV() == pytest.approx(
        r_ts.discount(div_date) * rebate, rel=2.0e-4
    )

    up_out = ql.BarrierOption(
        ql.BarrierType.UpOut, 120.0, rebate, payoff, exercise
    )
    up_out.set_fd_dividend_pricing_engine(
        process, [div_date], [div_amount], t_grid=100, x_grid=100
    )
    fwd = (100.0 - div_amount * r_ts.discount(div_date)) / r_ts.discount(
        maturity
    )
    expected_up_out = max(105.0 - fwd, 0.0) * r_ts.discount(maturity)
    assert up_out.NPV() == pytest.approx(expected_up_out, rel=2.0e-4)


def test_compat_phase67_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BarrierOption, "setFdPricingEngine")
    assert hasattr(cql.BarrierOption, "setFdDividendPricingEngine")
    assert cql.FdBlackScholesBarrierEngine is not None
