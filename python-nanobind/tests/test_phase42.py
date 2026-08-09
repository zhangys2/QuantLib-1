"""Phase-42 tests: quanto barrier options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase42():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 43)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# Values from test-suite/quantooption.cpp testBarrierValues (tol=0.5).
# maturity = today+180 (Actual360 ≈ 0.5y).
_BARRIER_CASES = [
    # barrier_type, barrier, rebate, option_type, strike, expected
    (ql.BarrierType.DownOut, 95.0, 3.0, ql.OptionType.Call, 90.0, 8.247),
    (ql.BarrierType.DownOut, 95.0, 3.0, ql.OptionType.Put, 90.0, 2.274),
    (ql.BarrierType.DownIn, 95.0, 0.0, ql.OptionType.Put, 90.0, 2.85),
]


@pytest.mark.parametrize(
    "barrier_type,barrier,rebate,option_type,strike,expected",
    _BARRIER_CASES,
)
def test_quanto_barrier_values(
    barrier_type, barrier, rebate, option_type, strike, expected
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.04, 0.0212, 0.25)
    option = ql.QuantoBarrierOption(
        barrier_type,
        barrier,
        rebate,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + 180),
    )
    option.set_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.2, dc),
        0.3,
    )
    assert option.NPV() == pytest.approx(expected, abs=0.5)
    assert option.is_expired() is False


def test_quanto_barrier_quote_handle_correlation():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.04, 0.0212, 0.25)
    option = ql.QuantoBarrierOption(
        ql.BarrierType.DownOut,
        95.0,
        3.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
        ql.EuropeanExercise(today + 180),
    )
    option.set_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.2, dc),
        ql.make_quote_handle(0.3),
    )
    assert option.NPV() == pytest.approx(8.247, abs=0.5)
    # AnalyticBarrierEngine does not populate the greek slots quanto greeks
    # need; C++ testBarrierValues only checks NPV. Methods are still exposed.
    assert callable(option.qvega)
    assert callable(option.qrho)
    assert callable(option.qlambda)


def test_compat_phase42_aliases():
    import qlnb.compat as cql

    assert cql.QuantoBarrierOption is not None
    assert hasattr(cql.QuantoBarrierOption, "setPricingEngine")
    assert hasattr(cql.QuantoBarrierOption, "isExpired")
