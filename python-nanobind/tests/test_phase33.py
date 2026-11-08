"""Phase-33 tests: two-asset correlation options (Zhang / Haug)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase33():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 34)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


def test_two_asset_correlation_haug():
    # Mirrors TwoAssetCorrelationOptionTests::testAnalyticEngine.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 180
    process1 = _bsm(today, 52.0, 0.0, 0.1, 0.2)
    process2 = _bsm(today, 65.0, 0.0, 0.1, 0.3)
    option = ql.TwoAssetCorrelationOption(
        ql.OptionType.Call,
        50.0,
        70.0,
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(process1, process2, 0.75)
    assert option.NPV() == pytest.approx(4.7073, abs=1.0e-4)
    assert option.is_expired() is False


def test_two_asset_correlation_quote_handle():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + 180
    process1 = _bsm(today, 52.0, 0.0, 0.1, 0.2)
    process2 = _bsm(today, 65.0, 0.0, 0.1, 0.3)
    option = ql.TwoAssetCorrelationOption(
        ql.OptionType.Call,
        50.0,
        70.0,
        ql.EuropeanExercise(maturity),
    )
    option.set_pricing_engine(process1, process2, ql.make_quote_handle(0.75))
    assert option.NPV() == pytest.approx(4.7073, abs=1.0e-4)


def test_compat_phase33_aliases():
    import qlnb.compat as cql

    assert cql.TwoAssetCorrelationOption is not None
    assert hasattr(cql.TwoAssetCorrelationOption, "setPricingEngine")
    assert hasattr(cql.TwoAssetCorrelationOption, "isExpired")
