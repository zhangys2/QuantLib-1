"""Phase-37 tests: FdHestonVanillaEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase37():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 38)


def test_fd_heston_american():
    # Mirrors FdHestonTest::testFdmHestonAmerican.
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
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0),
        ql.AmericanExercise(today, maturity),
    )
    option.set_fd_heston_pricing_engine(model, t_grid=200, x_grid=100, v_grid=50)
    assert option.NPV() == pytest.approx(5.66032, abs=0.01)
    assert option.delta() == pytest.approx(-0.30065, abs=0.01)
    assert option.gamma() == pytest.approx(0.02202, abs=0.01)


def test_fd_heston_matches_black_limit():
    # sigma → 0 recovers Black; mirrors HestonModelTests::testAnalyticVsBlack FD branch.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = today + ql.Period(6, ql.TimeUnit.Months)
    r, q, spot, strike, v0 = 0.1, 0.04, 32.0, 30.0, 0.05
    process = ql.HestonProcess(
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, q, dc),
        ql.make_quote_handle(spot),
        v0,
        5.0,
        v0,
        1.0e-4,
        0.0,
    )
    model = ql.HestonModel(process)
    fd_opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    fd_opt.set_fd_heston_pricing_engine(
        model, t_grid=200, x_grid=200, v_grid=100
    )

    bsm = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), math.sqrt(v0), dc),
    )
    black_opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    black_opt.set_pricing_engine(bsm)
    assert fd_opt.NPV() == pytest.approx(black_opt.NPV(), abs=1.0e-3)


def test_compat_phase37_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.VanillaOption, "setFdHestonPricingEngine")
    assert hasattr(cql.EuropeanOption, "setFdHestonPricingEngine")
    assert cql.FdHestonVanillaEngine is not None
