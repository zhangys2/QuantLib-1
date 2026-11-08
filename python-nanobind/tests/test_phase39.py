"""Phase-39 tests: Bates model + BatesEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase39():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 40)


def test_bates_process_accessors():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    process = ql.BatesProcess(
        ql.FlatForward(today, 0.1, dc),
        ql.FlatForward(today, 0.04, dc),
        ql.make_quote_handle(32.0),
        0.05,
        5.0,
        0.05,
        1.0e-4,
        0.0,
        0.0001,
        0.0,
        0.0001,
    )
    assert process.v0() == pytest.approx(0.05)
    assert process.jump_intensity() == pytest.approx(0.0001)
    assert process.nu() == pytest.approx(0.0)
    assert process.delta() == pytest.approx(0.0001)
    model = ql.BatesModel(process)
    assert model.jump_intensity() == pytest.approx(0.0001)
    assert model.kappa() == pytest.approx(5.0)


def test_bates_matches_black_limit():
    # Mirrors BatesModelTests::testAnalyticVsBlack (BatesEngine branch).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = today + ql.Period(6, ql.TimeUnit.Months)
    r, q, spot, strike, v0 = 0.1, 0.04, 32.0, 30.0, 0.05
    process = ql.BatesProcess(
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, q, dc),
        ql.make_quote_handle(spot),
        v0,
        5.0,
        v0,
        1.0e-4,
        0.0,
        0.0001,
        0.0,
        0.0001,
    )
    model = ql.BatesModel(process)
    bates_opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    bates_opt.set_bates_pricing_engine(model, integration_order=64)

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
    assert bates_opt.NPV() == pytest.approx(black_opt.NPV(), abs=2.0e-7)


def test_compat_phase39_aliases():
    import qlnb.compat as cql

    assert cql.BatesProcess is not None
    assert cql.BatesModel is not None
    assert hasattr(cql.VanillaOption, "setBatesPricingEngine")
    assert hasattr(cql.EuropeanOption, "setBatesPricingEngine")
    assert cql.BatesEngine is not None
