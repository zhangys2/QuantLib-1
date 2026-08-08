"""Phase-31 tests: cash/asset-or-nothing binary barriers (Haug p.180)."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase31():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 32)


def _bsm_process(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


# Haug p.180 cases from test-suite/binaryoption.cpp::testCashOrNothingHaugValues
# cash=15, t=0.5, vol=0.20 unless noted; American exercise.
_CASH_CASES = [
    # barrier_type, barrier, option_type, strike, spot, q, expected
    (ql.BarrierType.DownIn, 100, ql.OptionType.Call, 102, 105, 0.0, 4.9289),
    (ql.BarrierType.DownIn, 100, ql.OptionType.Call, 98, 105, 0.0, 6.2150),
    (ql.BarrierType.UpIn, 100, ql.OptionType.Call, 102, 95, 0.0, 5.8926),
    (ql.BarrierType.UpIn, 100, ql.OptionType.Call, 98, 95, 0.0, 7.4519),
    (ql.BarrierType.DownIn, 100, ql.OptionType.Put, 102, 105, 0.0, 4.4314),
    (ql.BarrierType.UpIn, 100, ql.OptionType.Put, 98, 95, 0.0, 3.7704),
    (ql.BarrierType.DownOut, 100, ql.OptionType.Call, 102, 105, 0.0, 4.8758),
    (ql.BarrierType.UpOut, 100, ql.OptionType.Call, 102, 95, 0.0, 0.0000),
    (ql.BarrierType.DownOut, 100, ql.OptionType.Put, 98, 105, 0.0, 0.0000),
    (ql.BarrierType.UpOut, 100, ql.OptionType.Put, 102, 95, 0.0, 3.0461),
    (ql.BarrierType.UpIn, 100, ql.OptionType.Call, 102, 95, -0.14, 8.6806),
    (ql.BarrierType.DownIn, 100, ql.OptionType.Call, 98, 95, 0.0, 7.4926),  # touched
]


@pytest.mark.parametrize(
    "barrier_type,barrier,option_type,strike,spot,q,expected",
    _CASH_CASES,
)
def test_cash_or_nothing_binary_barrier_haug(
    barrier_type, barrier, option_type, strike, spot, q, expected
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.5)
    process = _bsm_process(today, spot, q, 0.10, 0.20)
    option = ql.BarrierOption(
        barrier_type,
        barrier,
        0.0,
        ql.CashOrNothingPayoff(option_type, strike, 15.0),
        ql.AmericanExercise(today, maturity, True),
    )
    option.set_binary_pricing_engine(ql.AnalyticBinaryBarrierEngine(process))
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)


# Asset-or-nothing subset from testAssetOrNothingHaugValues
_ASSET_CASES = [
    (ql.BarrierType.DownIn, ql.OptionType.Call, 102, 105, 37.2782),
    (ql.BarrierType.UpIn, ql.OptionType.Call, 98, 95, 54.9262),
    (ql.BarrierType.DownOut, ql.OptionType.Call, 102, 105, 39.9391),
    (ql.BarrierType.UpOut, ql.OptionType.Call, 102, 95, 0.0000),
    (ql.BarrierType.DownIn, ql.OptionType.Put, 102, 105, 27.5644),
    (ql.BarrierType.UpIn, ql.OptionType.Put, 98, 95, 22.7755),
]


@pytest.mark.parametrize(
    "barrier_type,option_type,strike,spot,expected",
    _ASSET_CASES,
)
def test_asset_or_nothing_binary_barrier_haug(
    barrier_type, option_type, strike, spot, expected
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.5)
    process = _bsm_process(today, spot, 0.0, 0.10, 0.20)
    option = ql.BarrierOption(
        barrier_type,
        100.0,
        0.0,
        ql.AssetOrNothingPayoff(option_type, strike),
        ql.AmericanExercise(today, maturity, True),
    )
    option.set_binary_pricing_engine(process)
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)


def test_asset_or_nothing_payoff_inspectors():
    payoff = ql.AssetOrNothingPayoff(ql.OptionType.Call, 102.0)
    assert payoff.option_type() == ql.OptionType.Call
    assert payoff.strike() == pytest.approx(102.0)


def test_compat_phase31_aliases():
    import qlnb.compat as cql

    assert cql.AssetOrNothingPayoff is not None
    assert hasattr(cql.AssetOrNothingPayoff, "optionType")
    assert hasattr(cql.BarrierOption, "setBinaryPricingEngine")
    assert cql.AnalyticBinaryBarrierEngine is not None
