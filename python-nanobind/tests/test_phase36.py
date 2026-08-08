"""Phase-36 tests: Heston model + AnalyticHestonEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase36():
    assert ql.__version__ == "0.37.0"


def test_heston_process_accessors():
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.0225, dc),
        ql.FlatForward(today, 0.02, dc),
        ql.make_quote_handle(1.0),
        0.1,
        3.16,
        0.09,
        0.4,
        -0.2,
    )
    assert process.v0() == pytest.approx(0.1)
    assert process.kappa() == pytest.approx(3.16)
    assert process.theta() == pytest.approx(0.09)
    assert process.sigma() == pytest.approx(0.4)
    assert process.rho() == pytest.approx(-0.2)
    model = ql.HestonModel(process)
    assert model.v0() == pytest.approx(0.1)
    assert model.kappa() == pytest.approx(3.16)


def test_heston_analytic_vs_cached():
    # Mirrors HestonModelTests::testAnalyticVsCached first case.
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = ql.Date(28, ql.Month.March, 2005)
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.0225, dc),
        ql.FlatForward(today, 0.02, dc),
        ql.make_quote_handle(1.0),
        0.1,
        3.16,
        0.09,
        0.4,
        -0.2,
    )
    model = ql.HestonModel(process)
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 1.05),
        ql.EuropeanExercise(maturity),
    )
    option.set_heston_pricing_engine(model, integration_order=64)
    assert option.NPV() == pytest.approx(0.0404774515, abs=1.0e-8)


def test_heston_matches_black_limit():
    # sigma → 0 recovers Black with vol = sqrt(v0); mirrors testAnalyticVsBlack.
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
    heston_opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    heston_opt.set_heston_pricing_engine(model, integration_order=144)

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
    assert heston_opt.NPV() == pytest.approx(black_opt.NPV(), abs=2.0e-7)


def test_compat_phase36_aliases():
    import qlnb.compat as cql

    assert cql.HestonProcess is not None
    assert cql.HestonModel is not None
    assert hasattr(cql.VanillaOption, "setHestonPricingEngine")
    assert hasattr(cql.EuropeanOption, "setHestonPricingEngine")
