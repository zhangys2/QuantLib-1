"""Phase-99 tests: OvernightIndexFuture (SOFR futures suite NPVs)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase99():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 0)


def _add_fixings_oct_2018(index):
    # SofrFuturesTests::testBootstrap historical SOFR fixings.
    for d, r in (
        (ql.Date(1, ql.Month.October, 2018), 0.0222),
        (ql.Date(2, ql.Month.October, 2018), 0.022),
        (ql.Date(3, ql.Month.October, 2018), 0.022),
        (ql.Date(4, ql.Month.October, 2018), 0.0218),
        (ql.Date(5, ql.Month.October, 2018), 0.0216),
        (ql.Date(9, ql.Month.October, 2018), 0.0215),
        (ql.Date(10, ql.Month.October, 2018), 0.0215),
        (ql.Date(11, ql.Month.October, 2018), 0.0217),
        (ql.Date(12, ql.Month.October, 2018), 0.0218),
        (ql.Date(15, ql.Month.October, 2018), 0.0221),
        (ql.Date(16, ql.Month.October, 2018), 0.0218),
        (ql.Date(17, ql.Month.October, 2018), 0.0218),
        (ql.Date(18, ql.Month.October, 2018), 0.0219),
        (ql.Date(19, ql.Month.October, 2018), 0.0219),
        (ql.Date(22, ql.Month.October, 2018), 0.0218),
        (ql.Date(23, ql.Month.October, 2018), 0.0217),
        (ql.Date(24, ql.Month.October, 2018), 0.0218),
        (ql.Date(25, ql.Month.October, 2018), 0.0219),
    ):
        index.add_fixing(d, r)


def test_sofr_futures_bootstrap_npv():
    # SofrFuturesTests::testBootstrap.
    today = ql.Date(26, ql.Month.October, 2018)
    ql.set_evaluation_date(today)

    quotes = [
        (ql.Frequency.Monthly, ql.Month.October, 2018, 97.8175),
        (ql.Frequency.Monthly, ql.Month.November, 2018, 97.770),
        (ql.Frequency.Monthly, ql.Month.December, 2018, 97.685),
        (ql.Frequency.Monthly, ql.Month.January, 2019, 97.595),
        (ql.Frequency.Monthly, ql.Month.February, 2019, 97.590),
        (ql.Frequency.Monthly, ql.Month.March, 2019, 97.525),
        (ql.Frequency.Quarterly, ql.Month.March, 2019, 97.440),
        (ql.Frequency.Quarterly, ql.Month.June, 2019, 97.295),
        (ql.Frequency.Quarterly, ql.Month.September, 2019, 97.220),
        (ql.Frequency.Quarterly, ql.Month.December, 2019, 97.170),
        (ql.Frequency.Quarterly, ql.Month.March, 2020, 97.160),
        (ql.Frequency.Quarterly, ql.Month.June, 2020, 97.165),
        (ql.Frequency.Quarterly, ql.Month.September, 2020, 97.175),
    ]

    index = ql.Sofr()
    _add_fixings_oct_2018(index)

    helpers = [
        ql.SofrFutureRateHelper(price, month, year, freq)
        for freq, month, year, price in quotes
    ]
    curve = ql.PiecewiseLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
    sofr = ql.Sofr(curve)
    conv = ql.SimpleQuote(0.0)
    fut = ql.OvernightIndexFuture(
        sofr,
        ql.Date(20, ql.Month.March, 2019),
        ql.Date(19, ql.Month.June, 2019),
        ql.QuoteHandle(conv),
    )

    for conv_adj in (0.0, 0.1):
        conv.set_value(conv_adj)
        expected = 100.0 * (1.0 - (0.0256 + conv_adj))
        assert fut.NPV() == pytest.approx(expected, abs=1.0e-9)

    assert fut.is_expired() is False
    assert fut.value_date() == ql.Date(20, ql.Month.March, 2019)
    assert fut.maturity_date() == ql.Date(19, ql.Month.June, 2019)


def test_sofr_futures_juneteenth_bootstrap():
    # SofrFuturesTests::testBootstrapWithJuneteenth.
    today = ql.Date(27, ql.Month.June, 2024)
    ql.set_evaluation_date(today)

    quotes = [
        (ql.Frequency.Quarterly, ql.Month.June, 2024, 97.220),
        (ql.Frequency.Quarterly, ql.Month.September, 2024, 97.170),
        (ql.Frequency.Quarterly, ql.Month.December, 2024, 97.160),
        (ql.Frequency.Quarterly, ql.Month.March, 2025, 97.165),
        (ql.Frequency.Quarterly, ql.Month.June, 2025, 97.175),
    ]

    index = ql.Sofr()
    for d in (
        ql.Date(18, ql.Month.June, 2024),
        ql.Date(20, ql.Month.June, 2024),
        ql.Date(21, ql.Month.June, 2024),
        ql.Date(24, ql.Month.June, 2024),
        ql.Date(25, ql.Month.June, 2024),
        ql.Date(26, ql.Month.June, 2024),
        ql.Date(27, ql.Month.June, 2024),
    ):
        index.add_fixing(d, 0.02)

    helpers = [
        ql.SofrFutureRateHelper(price, month, year, freq)
        for freq, month, year, price in quotes
    ]
    curve = ql.PiecewiseLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
    sofr = ql.Sofr(curve)
    fut = ql.OvernightIndexFuture(
        sofr,
        ql.Date(19, ql.Month.June, 2024),
        ql.Date(18, ql.Month.September, 2024),
    )
    assert fut.NPV() == pytest.approx(97.220, abs=1.0e-9)


def test_compat_phase99_aliases():
    import qlnb.compat as cql

    assert cql.OvernightIndexFuture is not None
    assert cql.SofrFutureRateHelper is not None
    assert cql.PiecewiseLinearDiscountCurve is not None
    assert hasattr(cql.OvernightIndexFuture, "isExpired")
    assert hasattr(cql.OvernightIndexFuture, "convexityAdjustment")
    assert hasattr(cql.OvernightIndexFuture, "valueDate")
    assert hasattr(cql.OvernightIndexFuture, "maturityDate")
