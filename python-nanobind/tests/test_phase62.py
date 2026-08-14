"""Phase-62 tests: binary-barrier FD-Heston and MC barrier engine."""

from __future__ import annotations

import math

import qlnb as ql


def test_version_is_phase62():
    assert ql.__version__ == "0.63.0"


def test_fd_heston_binary_barrier_black_limit():
    # European cash-or-nothing DownOut vs AnalyticBinaryBarrierEngine
    # (American, payoff-at-expiry) in the Heston σ → 0 limit.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    maturity = today + int(math.floor(0.5 * 360 + 0.5))
    spot, q, r, vol = 105.0, 0.0, 0.10, 0.20
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
    payoff = ql.CashOrNothingPayoff(ql.OptionType.Call, 102.0, 15.0)
    analytic = ql.BarrierOption(
        ql.BarrierType.DownOut,
        100.0,
        0.0,
        payoff,
        ql.AmericanExercise(today, maturity, True),
    )
    analytic.set_binary_pricing_engine(bsm)
    expected = analytic.NPV()
    fd = ql.BarrierOption(
        ql.BarrierType.DownOut,
        100.0,
        0.0,
        payoff,
        ql.EuropeanExercise(maturity),
    )
    fd.set_fd_heston_pricing_engine(model, t_grid=100, x_grid=200, v_grid=3)
    assert abs(fd.NPV() - expected) < 0.05


def test_mc_barrier_beaglehole_down_out_call():
    # BarrierOptionTest::testBeagleholeValues market vs analytic.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    maturity = today + 360
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(50.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, math.log(1.1), dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.50, dc),
    )
    option = ql.BarrierOption(
        ql.BarrierType.DownOut,
        45.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 50.0),
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(process)
    analytic = option.NPV()
    option.set_mc_pricing_engine(
        process,
        time_steps=200,
        required_samples=8192,
        seed=10,
        antithetic=True,
        brownian_bridge=True,
    )
    mc = option.NPV()
    err = option.error_estimate()
    assert err > 0.0
    assert abs(mc - analytic) < 1.0


def test_compat_phase62_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BarrierOption, "setMcPricingEngine")
    assert hasattr(cql.BarrierOption, "errorEstimate")
    assert ql.MCBarrierEngine is not None
