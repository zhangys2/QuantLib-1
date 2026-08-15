"""Phase-66 tests: FdHestonBarrierEngine discrete-dividend overload."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase66():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 67)


def _heston_barrier_market():
    # Same market as FdHestonTest::testFdmHestonBarrier / Phase 38.
    today = ql.Date(28, ql.Month.March, 2004)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,
        2.5,
        0.04,
        0.66,
        -0.8,
    )
    model = ql.HestonModel(process)
    maturity = ql.Date(28, ql.Month.March, 2005)
    return today, model, maturity


def _up_out_call(maturity, barrier=135.0):
    return ql.BarrierOption(
        ql.BarrierType.UpOut,
        barrier,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )


def test_fd_heston_barrier_empty_dividends_match_plain():
    _, model, maturity = _heston_barrier_market()
    plain = _up_out_call(maturity)
    plain.set_fd_heston_pricing_engine(model, t_grid=50, x_grid=200, v_grid=50)
    div = _up_out_call(maturity)
    div.set_fd_heston_dividend_pricing_engine(
        model, [], [], t_grid=50, x_grid=200, v_grid=50
    )
    assert div.NPV() == pytest.approx(plain.NPV(), abs=1.0e-10)


def test_fd_heston_barrier_dividends_cheapen_call():
    today, model, maturity = _heston_barrier_market()
    plain = _up_out_call(maturity)
    plain.set_fd_heston_pricing_engine(model, t_grid=50, x_grid=200, v_grid=50)
    div = _up_out_call(maturity)
    div.set_fd_heston_dividend_pricing_engine(
        model,
        [today + ql.Period(6, ql.TimeUnit.Months)],
        [5.0],
        t_grid=50,
        x_grid=200,
        v_grid=50,
    )
    assert div.NPV() < plain.NPV()
    assert div.NPV() > 0.0


def test_far_barrier_dividends_match_vanilla():
    # Barrier far above spot → knock-out never binds; match vanilla FD+div.
    today, model, maturity = _heston_barrier_market()
    div_dates = [today + ql.Period(6, ql.TimeUnit.Months)]
    div_amounts = [5.0]
    barrier = _up_out_call(maturity, barrier=10_000.0)
    barrier.set_fd_heston_dividend_pricing_engine(
        model, div_dates, div_amounts, t_grid=50, x_grid=200, v_grid=50
    )
    vanilla = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    vanilla.set_fd_heston_dividend_pricing_engine(
        model, div_dates, div_amounts, t_grid=50, x_grid=200, v_grid=50
    )
    assert barrier.NPV() == pytest.approx(vanilla.NPV(), abs=0.05)


def test_compat_phase66_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BarrierOption, "setFdHestonDividendPricingEngine")
