"""Phase-45 tests: FdBatesVanillaEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase45():
    assert ql.__version__ == "0.46.0"


# 't Hout case 1 from test-suite/batesmodel.cpp testAnalyticVsMCPricing.
# FD vs analytic tol = 0.2.
def test_fd_bates_vs_analytic():
    today = ql.Date(30, ql.Month.March, 2007)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = ql.Date(30, ql.Month.March, 2012)
    process = ql.BatesProcess(
        ql.FlatForward(today, 0.025, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,   # v0
        1.5,    # kappa
        0.04,   # theta
        0.3,    # sigma
        -0.9,   # rho
        2.0,    # jump_intensity
        -0.2,   # nu
        0.1,    # delta
    )
    model = ql.BatesModel(process)
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0)
    exercise = ql.EuropeanExercise(maturity)

    analytic = ql.EuropeanOption(payoff, exercise)
    analytic.set_bates_pricing_engine(model, integration_order=160)

    fd = ql.EuropeanOption(payoff, exercise)
    fd.set_fd_bates_pricing_engine(model, t_grid=50, x_grid=100, v_grid=30)
    assert fd.NPV() == pytest.approx(analytic.NPV(), abs=0.2)


def test_fd_bates_vanilla_option():
    today = ql.Date(30, ql.Month.March, 2007)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    process = ql.BatesProcess(
        ql.FlatForward(today, 0.03, dc),
        ql.FlatForward(today, 0.035, dc),
        ql.make_quote_handle(100.0),
        0.07,
        2.0,
        0.04,
        0.55,
        -0.8,
        2.0,
        -0.2,
        0.1,
    )
    model = ql.BatesModel(process)
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0),
        ql.EuropeanExercise(ql.Date(30, ql.Month.March, 2012)),
    )
    option.set_fd_bates_pricing_engine(model, 50, 100, 30)
    assert option.NPV() > 0.0


def test_compat_phase45_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setFdBatesPricingEngine")
    assert hasattr(cql.VanillaOption, "setFdBatesPricingEngine")
    assert cql.FdBatesVanillaEngine is not None
