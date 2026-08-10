"""Phase-46 tests: Bates DetJump / DoubleExp variants."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase46():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 47)


def _near_black_process(today: ql.Date):
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    return ql.BatesProcess(
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


def test_bates_variant_accessors():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _near_black_process(today)

    det = ql.BatesDetJumpModel(process, kappa_lambda=1.0, theta_lambda=0.0001)
    assert det.kappa_lambda() == pytest.approx(1.0)
    assert det.theta_lambda() == pytest.approx(0.0001)
    assert det.jump_intensity() == pytest.approx(0.0001)

    dexp = ql.BatesDoubleExpModel(
        process, jump_intensity=0.0001, nu_up=0.0001, nu_down=0.0001
    )
    assert dexp.jump_intensity() == pytest.approx(0.0001)
    assert dexp.nu_up() == pytest.approx(0.0001)
    assert dexp.nu_down() == pytest.approx(0.0001)
    assert dexp.p() == pytest.approx(0.5)

    dexp_dj = ql.BatesDoubleExpDetJumpModel(
        process,
        jump_intensity=0.0001,
        nu_up=0.0001,
        nu_down=0.0001,
        p=0.5,
        kappa_lambda=1.0,
        theta_lambda=0.0001,
    )
    assert dexp_dj.kappa_lambda() == pytest.approx(1.0)
    assert dexp_dj.theta_lambda() == pytest.approx(0.0001)


@pytest.mark.parametrize(
    "attach",
    [
        "det_jump",
        "double_exp",
        "double_exp_det_jump",
    ],
)
def test_bates_variants_match_black_limit(attach):
    # Mirrors BatesModelTests::testAnalyticVsBlack variant engines.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = today + ql.Period(6, ql.TimeUnit.Months)
    r, q, spot, strike, v0 = 0.1, 0.04, 32.0, 30.0, 0.05
    process = _near_black_process(today)

    option = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    if attach == "det_jump":
        model = ql.BatesDetJumpModel(process, 1.0, 0.0001)
        option.set_bates_det_jump_pricing_engine(model, integration_order=64)
    elif attach == "double_exp":
        model = ql.BatesDoubleExpModel(process, 0.0001, 0.0001, 0.0001)
        option.set_bates_double_exp_pricing_engine(model, integration_order=64)
    else:
        model = ql.BatesDoubleExpDetJumpModel(
            process, 0.0001, 0.0001, 0.0001, 0.5, 1.0, 0.0001
        )
        option.set_bates_double_exp_det_jump_pricing_engine(
            model, integration_order=64
        )

    bsm = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), math.sqrt(v0), dc),
    )
    black = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    black.set_pricing_engine(bsm)
    assert option.NPV() == pytest.approx(black.NPV(), abs=2.0e-7)


def test_compat_phase46_aliases():
    import qlnb.compat as cql

    assert cql.BatesDetJumpModel is not None
    assert cql.BatesDoubleExpModel is not None
    assert cql.BatesDoubleExpDetJumpModel is not None
    assert hasattr(cql.EuropeanOption, "setBatesDetJumpPricingEngine")
    assert hasattr(cql.EuropeanOption, "setBatesDoubleExpPricingEngine")
    assert hasattr(cql.EuropeanOption, "setBatesDoubleExpDetJumpPricingEngine")
    assert hasattr(cql.VanillaOption, "setBatesDetJumpPricingEngine")
    assert cql.BatesDetJumpEngine is not None
    assert cql.BatesDoubleExpEngine is not None
    assert cql.BatesDoubleExpDetJumpEngine is not None
