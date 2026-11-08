"""Phase-125 tests: SuoWangDoubleBarrierEngine."""

from __future__ import annotations

import math
import sys

import pytest

import qlnb as ql


def test_version_is_phase125():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 6)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


# Representative Haug cases from DoubleBarrierOptionTests::testEuropeanHaugValues.
_CASES = [
    # barrier_type, lo, hi, option_type, strike, s, q, r, t, v, expected
    (ql.DoubleBarrierType.KnockOut, 50.0, 150.0, ql.OptionType.Call, 100.0, 100.0, 0.0, 0.1, 0.25, 0.15, 4.3515),
    (ql.DoubleBarrierType.KnockOut, 50.0, 150.0, ql.OptionType.Call, 100.0, 100.0, 0.0, 0.1, 0.25, 0.25, 6.1644),
    (ql.DoubleBarrierType.KnockOut, 80.0, 120.0, ql.OptionType.Call, 100.0, 100.0, 0.0, 0.1, 0.50, 0.25, 1.5098),
    (ql.DoubleBarrierType.KnockOut, 90.0, 110.0, ql.OptionType.Put, 100.0, 100.0, 0.0, 0.1, 0.25, 0.15, 0.9473),
    (ql.DoubleBarrierType.KnockIn, 50.0, 150.0, ql.OptionType.Call, 100.0, 100.0, 0.0, 0.1, 0.25, 0.15, 0.0000),
    (ql.DoubleBarrierType.KnockIn, 70.0, 130.0, ql.OptionType.Call, 100.0, 100.0, 0.0, 0.1, 0.50, 0.25, 5.5818),
    (ql.DoubleBarrierType.KnockIn, 80.0, 120.0, ql.OptionType.Call, 100.0, 100.0, 0.0, 0.1, 0.25, 0.35, 6.7007),
]


@pytest.mark.parametrize(
    "barrier_type,lo,hi,option_type,strike,s,q,r,t,v,expected",
    _CASES,
)
def test_suo_wang_haug_values(
    barrier_type, lo, hi, option_type, strike, s, q, r, t, v, expected
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(s),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), v, dc),
    )
    opt = ql.DoubleBarrierOption(
        barrier_type,
        lo,
        hi,
        0.0,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + _time_to_days(t)),
    )
    opt.set_suo_wang_pricing_engine(process)
    assert opt.NPV() == pytest.approx(expected, abs=1.0e-4)


def test_suo_wang_factory_alias():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.1, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.15, dc),
    )
    opt = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        50.0,
        150.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(today + _time_to_days(0.25)),
    )
    opt.set_suo_wang_pricing_engine(ql.SuoWangDoubleBarrierEngine(process))
    assert opt.NPV() == pytest.approx(4.3515, abs=1.0e-4)


def test_native_suo_wang_snake_case_only():
    assert hasattr(ql.DoubleBarrierOption, "set_suo_wang_pricing_engine")
    assert hasattr(ql, "SuoWangDoubleBarrierEngine")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate DoubleBarrierOption"
        )
    assert not hasattr(ql.DoubleBarrierOption, "setSuoWangPricingEngine")


def test_compat_phase125_aliases():
    import qlnb.compat as c

    assert hasattr(c.DoubleBarrierOption, "setSuoWangPricingEngine")
    assert c.DoubleBarrierOption.setSuoWangPricingEngine is (
        ql.DoubleBarrierOption.set_suo_wang_pricing_engine
    )
