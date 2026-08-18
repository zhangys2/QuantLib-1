"""Phase-76 tests: simple / complex chooser options (Haug)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase76():
    assert ql.__version__ == "0.77.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def test_simple_chooser_haug():
    # ChooserOptionTests::testAnalyticSimpleChooserEngine (Haug pp.39-40).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = ql.SimpleChooserOption(
        today + 90,
        50.0,
        ql.EuropeanExercise(today + 180),
    )
    opt.set_pricing_engine(_bsm(today, 50.0, 0.0, 0.08, 0.25))
    assert opt.NPV() == pytest.approx(6.1071, abs=3.0e-5)
    assert opt.is_expired() is False


def test_complex_chooser_haug():
    # ChooserOptionTests::testAnalyticComplexChooserEngine (Haug).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    choosing = today + 90
    opt = ql.ComplexChooserOption(
        choosing,
        55.0,
        48.0,
        ql.EuropeanExercise(choosing + 180),
        ql.EuropeanExercise(choosing + 210),
    )
    opt.set_pricing_engine(_bsm(today, 50.0, 0.05, 0.10, 0.35))
    assert opt.NPV() == pytest.approx(6.0508, abs=1.0e-4)
    assert opt.is_expired() is False


def test_compat_phase76_aliases():
    import qlnb.compat as cql

    assert cql.SimpleChooserOption is not None
    assert hasattr(cql.SimpleChooserOption, "setPricingEngine")
    assert hasattr(cql.SimpleChooserOption, "isExpired")
    assert cql.AnalyticSimpleChooserEngine is not None
    assert cql.ComplexChooserOption is not None
    assert hasattr(cql.ComplexChooserOption, "setPricingEngine")
    assert hasattr(cql.ComplexChooserOption, "isExpired")
    assert cql.AnalyticComplexChooserEngine is not None
