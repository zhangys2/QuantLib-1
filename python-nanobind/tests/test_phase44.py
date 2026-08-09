"""Phase-44 tests: quanto-forward performance options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase44():
    assert ql.__version__ == "0.45.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# Values from test-suite/quantooption.cpp testForwardPerformanceValues.
# maturity=0.5y → 180 days; reset=0 → today; reset=0.25y → 90 days.
_PERF_CASES = [
    # option_type, reset_days, expected
    (ql.OptionType.Call, 0, 5.3280 / 150),
    (ql.OptionType.Put, 0, 0.0816),
    (ql.OptionType.Call, 90, 0.0201),
    (ql.OptionType.Put, 90, 0.0672),
]


@pytest.mark.parametrize("option_type,reset_days,expected", _PERF_CASES)
def test_quanto_forward_performance_values(option_type, reset_days, expected):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.04, 0.08, 0.20)
    option = ql.QuantoForwardVanillaOption(
        1.05,
        today + reset_days,
        ql.PlainVanillaPayoff(option_type, 0.0),
        ql.EuropeanExercise(today + 180),
    )
    option.set_performance_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.10, dc),
        0.3,
    )
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)
    assert option.is_expired() is False


def test_quanto_forward_performance_quote_handle():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.04, 0.08, 0.20)
    option = ql.QuantoForwardVanillaOption(
        1.05,
        today + 90,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),
        ql.EuropeanExercise(today + 180),
    )
    option.set_performance_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.10, dc),
        ql.make_quote_handle(0.3),
    )
    assert option.NPV() == pytest.approx(0.0201, abs=1.0e-4)
    assert option.qvega() == option.qvega()
    assert option.qrho() == option.qrho()
    assert option.qlambda() == option.qlambda()


def test_compat_phase44_aliases():
    import qlnb.compat as cql

    assert cql.QuantoForwardVanillaOption is not None
    assert hasattr(cql.QuantoForwardVanillaOption, "setPerformancePricingEngine")
