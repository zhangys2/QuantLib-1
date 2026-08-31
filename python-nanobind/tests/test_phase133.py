"""Phase-133 tests: BinomialDoubleBarrierEngine (CRR)."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase133():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 4)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


# Representative Haug cases from DoubleBarrierOptionTests::testEuropeanHaugValues.
# Plain binomial suite tolerance is 0.28.
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
def test_haug_binomial_double_barrier(
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
    opt.set_binomial_pricing_engine(process, time_steps=300)
    assert opt.NPV() == pytest.approx(expected, abs=0.28)


def test_factory_alias_and_compat():
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
        ql.EuropeanExercise(today + 90),
    )
    opt.set_binomial_pricing_engine(ql.BinomialDoubleBarrierEngine(process))
    assert opt.NPV() == pytest.approx(4.3515, abs=0.28)

    import qlnb.compat as c

    assert hasattr(c.DoubleBarrierOption, "setBinomialPricingEngine")
