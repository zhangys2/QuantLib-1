"""Phase-127 tests: PerturbativeBarrierOptionEngine."""

from __future__ import annotations

import sys

import pytest

import qlnb as ql


def test_version_is_phase127():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 8)


def _suite_market():
    # BarrierOptionTests::testPerturbative market setup.
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    vol_ts = ql.BlackVarianceCurve(
        today,
        [today + 90, today + 180],
        [0.105, 0.11],
        dc,
        True,
    )
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.02, dc),
        ql.FlatForward(today, 0.03, dc),
        vol_ts,
    )
    opt = ql.BarrierOption(
        ql.BarrierType.UpOut,
        101.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Put, 101.0),
        ql.EuropeanExercise(today + 180),
    )
    return process, opt


@pytest.mark.parametrize("order,expected", [(0, 0.897365), (1, 0.894374)])
def test_perturbative_suite_orders(order, expected):
    process, opt = _suite_market()
    opt.set_perturbative_pricing_engine(process, order=order, zero_gamma=False)
    assert opt.NPV() == pytest.approx(expected, abs=1.0e-6)


def test_perturbative_factory_alias():
    process, opt = _suite_market()
    opt.set_perturbative_pricing_engine(
        ql.PerturbativeBarrierOptionEngine(process), order=0
    )
    assert opt.NPV() == pytest.approx(0.897365, abs=1.0e-6)


def test_native_perturbative_snake_case_only():
    assert hasattr(ql.BarrierOption, "set_perturbative_pricing_engine")
    assert hasattr(ql, "PerturbativeBarrierOptionEngine")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate BarrierOption"
        )
    assert not hasattr(ql.BarrierOption, "setPerturbativePricingEngine")


def test_compat_phase127_aliases():
    import qlnb.compat as c

    assert hasattr(c.BarrierOption, "setPerturbativePricingEngine")
    assert c.BarrierOption.setPerturbativePricingEngine is (
        ql.BarrierOption.set_perturbative_pricing_engine
    )
