"""Phase-40 tests: quanto vanilla options (Haug p.105)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase40():
    assert ql.__version__ == "0.41.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


# Haug values from test-suite/quantooption.cpp (tol=1e-4).
# t=0.5y → 180 days (Actual360); Call result = 5.3280/1.5.
_HAUG_CASES = [
    (ql.OptionType.Call, 5.3280 / 1.5),
    (ql.OptionType.Put, 8.1636),
]


@pytest.mark.parametrize("option_type,expected", _HAUG_CASES)
def test_quanto_vanilla_haug(option_type, expected):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.04, 0.08, 0.20)
    foreign_rfr = ql.FlatForward(today, 0.05, dc)
    fx_vol = ql.BlackConstantVol(today, ql.TARGET(), 0.10, dc)
    option = ql.QuantoVanillaOption(
        ql.PlainVanillaPayoff(option_type, 105.0),
        ql.EuropeanExercise(today + 180),
    )
    option.set_pricing_engine(process, foreign_rfr, fx_vol, 0.3)
    assert option.NPV() == pytest.approx(expected, abs=1.0e-4)
    assert option.is_expired() is False


def test_quanto_quote_handle_correlation():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = _bsm(today, 100.0, 0.04, 0.08, 0.20)
    option = ql.QuantoVanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 105.0),
        ql.EuropeanExercise(today + 180),
    )
    option.set_pricing_engine(
        process,
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.10, dc),
        ql.make_quote_handle(0.3),
    )
    assert option.NPV() == pytest.approx(5.3280 / 1.5, abs=1.0e-4)
    # Quanto greeks should be finite after pricing.
    assert option.qvega() == option.qvega()
    assert option.qrho() == option.qrho()
    assert option.qlambda() == option.qlambda()


def test_compat_phase40_aliases():
    import qlnb.compat as cql

    assert cql.QuantoVanillaOption is not None
    assert hasattr(cql.QuantoVanillaOption, "setPricingEngine")
    assert hasattr(cql.QuantoVanillaOption, "isExpired")
