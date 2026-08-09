"""Phase-43 tests: quanto double-barrier options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase43():
    assert ql.__version__ == "0.44.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# Values from test-suite/quantooption.cpp testDoubleBarrierValues (tol=1e-4).
# maturity days = round(T * 360) with Actual360.
_DOUBLE_BARRIER_CASES = [
    # barrier_type, lo, hi, rebate, type, strike, q, r, days, vol, expected
    (
        ql.DoubleBarrierType.KnockOut,
        50.0,
        150.0,
        0.0,
        ql.OptionType.Call,
        100.0,
        0.00,
        0.1,
        90,
        0.15,
        3.4623,
    ),
    (
        ql.DoubleBarrierType.KnockOut,
        90.0,
        110.0,
        0.0,
        ql.OptionType.Call,
        100.0,
        0.00,
        0.1,
        180,
        0.15,
        0.5236,
    ),
    (
        ql.DoubleBarrierType.KnockOut,
        90.0,
        110.0,
        0.0,
        ql.OptionType.Put,
        100.0,
        0.00,
        0.1,
        90,
        0.15,
        1.1320,
    ),
    (
        ql.DoubleBarrierType.KnockIn,
        80.0,
        120.0,
        0.0,
        ql.OptionType.Call,
        102.0,
        0.00,
        0.1,
        90,
        0.25,
        2.6313,
    ),
    (
        ql.DoubleBarrierType.KnockIn,
        80.0,
        120.0,
        0.0,
        ql.OptionType.Call,
        102.0,
        0.00,
        0.1,
        180,
        0.15,
        1.9305,
    ),
]


@pytest.mark.parametrize(
    "barrier_type,lo,hi,rebate,option_type,strike,q,r,days,vol,expected",
    _DOUBLE_BARRIER_CASES,
)
def test_quanto_double_barrier_values(
    barrier_type, lo, hi, rebate, option_type, strike, q, r, days, vol, expected
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, q, r, vol)
    option = ql.QuantoDoubleBarrierOption(
        barrier_type,
        lo,
        hi,
        rebate,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + days),
    )
    option.set_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.2, dc),
        0.3,
    )
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)
    assert option.is_expired() is False


def test_quanto_double_barrier_quote_handle_correlation():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.00, 0.1, 0.15)
    option = ql.QuantoDoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        50.0,
        150.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(today + 90),
    )
    option.set_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.2, dc),
        ql.make_quote_handle(0.3),
    )
    assert option.NPV() == pytest.approx(3.4623, abs=1.0e-4)
    # AnalyticDoubleBarrierEngine does not populate slots for quanto greeks.
    assert callable(option.qvega)
    assert callable(option.qrho)
    assert callable(option.qlambda)


def test_compat_phase43_aliases():
    import qlnb.compat as cql

    assert cql.QuantoDoubleBarrierOption is not None
    assert hasattr(cql.QuantoDoubleBarrierOption, "setPricingEngine")
    assert hasattr(cql.QuantoDoubleBarrierOption, "isExpired")
