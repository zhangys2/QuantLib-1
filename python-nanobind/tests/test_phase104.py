"""Phase-104 tests: Stock and CompositeInstrument."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase104():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 5)


def test_stock_npv_tracks_quote():
    q = ql.SimpleQuote(3.14)
    stock = ql.Stock(ql.QuoteHandle(q))
    assert stock.NPV() == pytest.approx(3.14)
    q.set_value(2.71)
    assert stock.NPV() == pytest.approx(2.71)
    assert stock.is_expired() is False


def test_composite_when_shifting_dates():
    # InstrumentTests::testCompositeWhenShiftingDates
    today = ql.get_evaluation_date()
    dc = ql.Actual360()
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)
    exercise = ql.EuropeanExercise(today + 30)
    opt = ql.EuropeanOption(payoff, exercise)
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.01, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.1, dc),
    )
    opt.set_pricing_engine(process)

    composite = ql.CompositeInstrument()
    composite.add(opt)

    ql.set_evaluation_date(today + 45)
    assert composite.is_expired() is True
    assert composite.NPV() == 0.0

    ql.set_evaluation_date(today)
    assert composite.is_expired() is False
    assert composite.NPV() != 0.0


def test_compat_phase104_aliases():
    import qlnb.compat as c

    assert c.Stock is not None
    assert c.CompositeInstrument is not None
    assert hasattr(c.Stock, "isExpired")
    assert hasattr(c.CompositeInstrument, "isExpired")
