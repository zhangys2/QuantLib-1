"""Phase-38 tests: FdHestonBarrierEngine / FdHestonDoubleBarrierEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase38():
    assert ql.__version__ == "0.39.0"


def test_fd_heston_barrier():
    # Mirrors FdHestonTest::testFdmHestonBarrier.
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
    option = ql.BarrierOption(
        ql.BarrierType.UpOut,
        135.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    option.set_fd_heston_pricing_engine(model, t_grid=50, x_grid=400, v_grid=100)
    assert option.NPV() == pytest.approx(9.1530, abs=0.01)
    assert option.delta() == pytest.approx(0.5218, abs=0.01)
    assert option.gamma() == pytest.approx(-0.0354, abs=0.01)


def test_fd_heston_double_barrier_black_limit():
    # sigma → 0 should track AnalyticDoubleBarrierEngine within FD tolerance.
    today = ql.Date(28, ql.Month.March, 2004)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    spot, strike, vol = 100.0, 100.0, 0.20
    maturity = ql.Date(28, ql.Month.March, 2005)
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(spot),
        vol * vol,
        1.0,
        vol * vol,
        1.0e-4,
        0.0,
    )
    model = ql.HestonModel(process)
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, strike)
    exercise = ql.EuropeanExercise(maturity)

    fd = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        80.0,
        120.0,
        0.0,
        payoff,
        exercise,
    )
    fd.set_fd_heston_pricing_engine(model, t_grid=100, x_grid=200, v_grid=50)

    bsm = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )
    analytic = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        80.0,
        120.0,
        0.0,
        payoff,
        exercise,
    )
    analytic.set_pricing_engine(bsm)
    assert fd.NPV() == pytest.approx(analytic.NPV(), abs=0.05)


def test_compat_phase38_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BarrierOption, "setFdHestonPricingEngine")
    assert hasattr(cql.DoubleBarrierOption, "setFdHestonPricingEngine")
    assert cql.FdHestonBarrierEngine is not None
    assert cql.FdHestonDoubleBarrierEngine is not None
