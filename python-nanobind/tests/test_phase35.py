"""Phase-35 tests: forward vanilla options (Haug p.37)."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase35():
    assert ql.__version__ == "0.36.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# Haug values from test-suite/forwardoption.cpp (tol=1e-4).
# start=0.25y → 90 days; maturity=1.0y → 360 days (Actual360).
_HAUG_CASES = [
    (ql.OptionType.Call, 4.4064),
    (ql.OptionType.Put, 8.2971),
]


@pytest.mark.parametrize("option_type,expected", _HAUG_CASES)
def test_forward_vanilla_haug(option_type, expected):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 60.0, 0.04, 0.08, 0.30)
    option = ql.ForwardVanillaOption(
        1.1,
        today + 90,
        ql.PlainVanillaPayoff(option_type, 0.0),
        ql.EuropeanExercise(today + 360),
    )
    option.set_pricing_engine(process)
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)
    assert option.is_expired() is False


@pytest.mark.parametrize("option_type,forward_npv", _HAUG_CASES)
def test_forward_performance_haug(option_type, forward_npv):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 60.0, 0.04, 0.08, 0.30)
    option = ql.ForwardVanillaOption(
        1.1,
        today + 90,
        ql.PlainVanillaPayoff(option_type, 0.0),
        ql.EuropeanExercise(today + 360),
    )
    option.set_performance_pricing_engine(process)
    expected = forward_npv / 60.0 * math.exp(-0.04 * 0.25)
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)


def test_forward_vanilla_factory_alias():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 60.0, 0.04, 0.08, 0.30)
    option = ql.ForwardVanillaOption(
        1.1,
        today + 90,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),
        ql.EuropeanExercise(today + 360),
    )
    option.set_pricing_engine(ql.ForwardVanillaEngine(process))
    assert option.NPV() == pytest.approx(4.4064, abs=1.0e-4)


def test_compat_phase35_aliases():
    import qlnb.compat as cql

    assert cql.ForwardVanillaOption is not None
    assert hasattr(cql.ForwardVanillaOption, "setPricingEngine")
    assert hasattr(cql.ForwardVanillaOption, "setPerformancePricingEngine")
    assert hasattr(cql.ForwardVanillaOption, "isExpired")
