"""Phase-110 tests: VarianceOption."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase110():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 1)


def _heston_process(v0: float):
    today = ql.get_evaluation_date()
    dc = ql.Actual360()
    return ql.HestonProcess(
        ql.FlatForward(today, 0.0, dc),
        ql.YieldTermStructureHandle(),
        ql.make_quote_handle(1.0),
        v0,
        2.0,
        0.01,
        0.1,
        -0.5,
    )


def test_integral_heston_variance_option_call():
    # VarianceOptionTests::testIntegralHeston — call leg
    today = ql.get_evaluation_date()
    ql.set_evaluation_date(today)

    process = _heston_process(2.0)
    ex_date = today + 540  # int(360 * 1.5) with Actual360 convention in suite

    opt = ql.VarianceOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 0.05),
        1.0,
        today,
        ex_date,
    )
    opt.set_integral_heston_pricing_engine(process)

    assert opt.NPV() == pytest.approx(0.9104619, abs=1e-7)


def test_integral_heston_variance_option_put():
    # VarianceOptionTests::testIntegralHeston — put leg
    today = ql.get_evaluation_date()
    ql.set_evaluation_date(today)

    process = _heston_process(1.5)
    ex_date = today + 360

    opt = ql.VarianceOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 0.7),
        1.0,
        today,
        ex_date,
    )
    opt.set_integral_heston_pricing_engine(process)

    assert opt.NPV() == pytest.approx(0.0466796, abs=1e-7)


def test_native_variance_option_snake_case_only():
    # Native qlnb exposes snake_case; camelCase aliases live in qlnb.compat.
    import sys

    assert hasattr(ql.VarianceOption, "set_integral_heston_pricing_engine")
    assert hasattr(ql.VarianceOption, "is_expired")
    assert hasattr(ql.VarianceOption, "start_date")
    assert hasattr(ql.VarianceOption, "maturity_date")
    if "qlnb.compat" in sys.modules:
        pytest.skip("qlnb.compat already loaded; camelCase aliases mutate VarianceOption")
    assert not hasattr(ql.VarianceOption, "setIntegralHestonPricingEngine")
    assert not hasattr(ql.VarianceOption, "isExpired")
    assert not hasattr(ql.VarianceOption, "startDate")
    assert not hasattr(ql.VarianceOption, "maturityDate")


def test_compat_phase110_aliases():
    import qlnb.compat as c

    assert c.VarianceOption is not None
    assert hasattr(c.VarianceOption, "setIntegralHestonPricingEngine")
    assert hasattr(c.VarianceOption, "isExpired")
    assert hasattr(c.VarianceOption, "startDate")
    assert hasattr(c.VarianceOption, "maturityDate")
    assert c.IntegralHestonVarianceOptionEngine is not None
    assert (
        c.VarianceOption.setIntegralHestonPricingEngine
        is c.VarianceOption.set_integral_heston_pricing_engine
    )
    assert c.VarianceOption.isExpired is c.VarianceOption.is_expired
    assert c.VarianceOption.startDate is c.VarianceOption.start_date
    assert c.VarianceOption.maturityDate is c.VarianceOption.maturity_date
