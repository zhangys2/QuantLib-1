"""Phase-61 tests: double-barrier binary FD-Heston and MC engine."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase61():
    assert ql.__version__ == "0.62.0"


def test_fd_heston_double_binary_black_limit():
    # DoubleBarrierOptionTest::testFdHeston vs analytic BS (Heston σ → 0).
    today = ql.Date(30, ql.Month.January, 2023)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    spot, r, q, vol = 100.0, 0.075, 0.03, 0.4
    theta = vol * vol
    heston = ql.HestonProcess(
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, q, dc),
        ql.make_quote_handle(spot),
        theta,
        1.0,
        theta,
        1.0e-4,
        0.0,
    )
    model = ql.HestonModel(heston)
    bsm = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )
    maturity = today + ql.Period(1, ql.TimeUnit.Years)
    # i=5 in the suite loop → dist = 10 + 5*5 = 35
    option = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        65.0,
        135.0,
        0.0,
        ql.CashOrNothingPayoff(ql.OptionType.Call, 0.0, 1.0),
        ql.EuropeanExercise(maturity),
    )
    option.set_binary_pricing_engine(bsm)
    analytic = option.NPV()
    option.set_fd_heston_pricing_engine(
        model, t_grid=201, x_grid=101, v_grid=3
    )
    assert abs(option.NPV() - analytic) < 5.0e-3


def test_mc_double_barrier_knockout_put():
    # DoubleBarrierOptionTest::testMonteCarloDoubleBarrierWithAnalytical
    today = ql.Date(15, ql.Month.May, 1998)
    settlement = ql.Date(17, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    spot = 36.0
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(settlement, 0.0, dc),
        ql.FlatForward(settlement, 0.06, dc),
        ql.BlackConstantVol(settlement, ql.TARGET(), 0.20, dc),
    )
    option = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        spot * 0.9,
        spot * 1.1,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Put, 40.0),
        ql.EuropeanExercise(ql.Date(17, ql.Month.May, 1999)),
    )
    option.set_pricing_engine(process)
    analytic = option.NPV()
    option.set_mc_pricing_engine(
        process, time_steps=200, required_samples=8192, seed=10, antithetic=True
    )
    mc = option.NPV()
    err = option.error_estimate()
    assert err > 0.0
    assert abs(mc - analytic) < 1.0


def test_compat_phase61_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.DoubleBarrierOption, "setMcPricingEngine")
    assert hasattr(cql.DoubleBarrierOption, "errorEstimate")
    assert ql.MCDoubleBarrierEngine is not None
