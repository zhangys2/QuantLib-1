"""Phase-83 tests: holder / writer extensible options (Haug)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase83():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 84)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# ExtensibleOptionsTests::testAnalyticHolderExtensibleOptionEngine (Haug).
def test_holder_extensible_haug():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = ql.HolderExtensibleOption(
        ql.OptionType.Call,
        1.0,
        today + 270,
        105.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(today + 180),
    )
    opt.set_pricing_engine(_bsm(today, 100.0, 0.0, 0.08, 0.25))
    assert opt.NPV() == pytest.approx(9.4233, abs=1.0e-4)
    assert opt.is_expired() is False


# ExtensibleOptionsTests::testAnalyticWriterExtensibleOptionEngine (Haug).
def test_writer_extensible_haug():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = ql.WriterExtensibleOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
        ql.EuropeanExercise(today + 180),
        ql.PlainVanillaPayoff(ql.OptionType.Call, 82.0),
        ql.EuropeanExercise(today + 270),
    )
    opt.set_pricing_engine(_bsm(today, 80.0, 0.0, 0.10, 0.30))
    assert opt.NPV() == pytest.approx(6.8238, abs=1.0e-4)
    assert opt.is_expired() is False


def test_compat_phase83_aliases():
    import qlnb.compat as cql

    assert cql.HolderExtensibleOption is not None
    assert hasattr(cql.HolderExtensibleOption, "setPricingEngine")
    assert hasattr(cql.HolderExtensibleOption, "isExpired")
    assert cql.AnalyticHolderExtensibleOptionEngine is not None
    assert cql.WriterExtensibleOption is not None
    assert hasattr(cql.WriterExtensibleOption, "setPricingEngine")
    assert hasattr(cql.WriterExtensibleOption, "isExpired")
    assert cql.AnalyticWriterExtensibleOptionEngine is not None
