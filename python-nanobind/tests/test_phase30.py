"""Phase-30 tests: partial-time barrier options (analytic EndB1 knock-outs)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase30():
    assert ql.__version__ == "0.31.0"


def _market(today: ql.Date):
    dc = ql.Actual360()
    return (
        ql.FlatForward(today, 0.0, dc),  # q
        ql.FlatForward(today, 0.1, dc),  # r
        0.25,
        dc,
    )


def _process(today: ql.Date, spot: float):
    q_curve, r_curve, vol, dc = _market(today)
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        q_curve,
        r_curve,
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# From test-suite/partialtimebarrieroption.cpp::testAnalyticEngine
# DownOut + EndB1, barrier=100, rebate=0, maturity=today+360, q=0, r=0.1, vol=0.25
_CALL_CASES = [
    # underlying, strike, cover_days, expected
    (95.0, 90.0, 1, 0.0393),
    (105.0, 90.0, 1, 9.8751),
    (105.0, 110.0, 1, 6.2303),
    (95.0, 90.0, 90, 6.2747),
    (95.0, 110.0, 90, 3.7352),
    (105.0, 110.0, 90, 9.6812),
    (95.0, 90.0, 180, 10.3345),
    (105.0, 90.0, 270, 22.0753),
    (95.0, 110.0, 359, 7.5763),
    (105.0, 110.0, 359, 13.1376),
]


@pytest.mark.parametrize(
    "spot,strike,cover_days,expected",
    _CALL_CASES,
)
def test_partial_time_barrier_down_out_call(spot, strike, cover_days, expected):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 360
    cover = today + cover_days
    option = ql.PartialTimeBarrierOption(
        ql.BarrierType.DownOut,
        ql.PartialBarrierRange.EndB1,
        100.0,
        0.0,
        cover,
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(
        ql.AnalyticPartialTimeBarrierOptionEngine(_process(today, spot))
    )
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)


# From testAnalyticEnginePutOption — UpOut + EndB1
_PUT_CASES = [
    (95.0, 90.0, 1, 1.5551),
    (95.0, 95.0, 1, 2.0589),
    (90.0, 95.0, 90, 5.0624),
    (99.0, 90.0, 180, 2.1903),
    (95.0, 95.0, 270, 4.7362),
    (90.0, 95.0, 359, 6.8782),
]


@pytest.mark.parametrize(
    "spot,strike,cover_days,expected",
    _PUT_CASES,
)
def test_partial_time_barrier_up_out_put(spot, strike, cover_days, expected):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 360
    cover = today + cover_days
    option = ql.PartialTimeBarrierOption(
        ql.BarrierType.UpOut,
        ql.PartialBarrierRange.EndB1,
        100.0,
        0.0,
        cover,
        ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(_process(today, spot))
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)


def test_compat_phase30_aliases():
    import qlnb.compat as cql

    assert cql.PartialBarrierRange is not None
    assert cql.PartialTimeBarrierOption is not None
    assert hasattr(cql.PartialTimeBarrierOption, "setPricingEngine")
    assert cql.AnalyticPartialTimeBarrierOptionEngine is not None
