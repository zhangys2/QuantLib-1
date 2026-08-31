"""Phase-100 tests: BMASwap (piecewise BMA fair libor fractions)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase100():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 1)


# PiecewiseYieldCurve BMA market data (libor fraction * 100).
_BMA_DATA = [
    (1, 67.56),
    (2, 68.00),
    (3, 68.25),
    (4, 68.50),
    (5, 68.81),
    (7, 69.50),
    (10, 70.44),
    (15, 71.69),
    (20, 72.69),
    (30, 73.81),
]


def _last_wednesday(today: ql.Date) -> ql.Date:
    w = int(today.weekday())
    # QuantLib Weekday: Sunday=1 .. Saturday=7; Wednesday=4.
    if w >= 4:
        return today - (w - 4)
    return today + (4 - w - 7)


def _bma_bootstrap():
    # testBMACurveConsistency setup with a fixed evaluation date.
    settlement_days = 2
    bma_frequency = ql.Frequency.Quarterly
    bma_convention = ql.BusinessDayConvention.Following
    bma_day_count = ql.ActualActual(ql.ActualActualConvention.ISDA)

    bma_index0 = ql.BMAIndex()
    libor0 = ql.USDLibor(ql.Period(3, ql.TimeUnit.Months))
    calendar = ql.JointCalendar(
        bma_index0.fixing_calendar(),
        libor0.fixing_calendar(),
        ql.JointCalendarRule.JoinHolidays,
    )
    today = calendar.adjust(ql.Date(15, ql.Month.January, 2020))
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, settlement_days, ql.TimeUnit.Days)

    risk_free = ql.FlatForward(settlement, 0.04, ql.Actual360())
    bma_index = ql.BMAIndex()
    libor_index = ql.USDLibor(ql.Period(3, ql.TimeUnit.Months), risk_free)

    helpers = []
    for years, fraction_pct in _BMA_DATA:
        helpers.append(
            ql.BMASwapRateHelper(
                ql.make_quote_handle(fraction_pct / 100.0),
                ql.Period(years, ql.TimeUnit.Years),
                settlement_days,
                calendar,
                ql.Period(bma_frequency),
                bma_convention,
                bma_day_count,
                bma_index,
                libor_index,
            )
        )

    last_fixing = bma_index.fixing_calendar().adjust(_last_wednesday(today))
    bma_index.add_fixing(last_fixing, 0.03)

    curve = ql.PiecewiseLinearDiscountCurve(today, helpers, ql.Actual360())
    bma = ql.BMAIndex(curve)
    libor = ql.USDLibor(ql.Period(3, ql.TimeUnit.Months), risk_free)
    return risk_free, bma, libor, bma_frequency, bma_convention, bma_day_count


def test_bma_curve_fair_libor_fractions():
    # PiecewiseYieldCurve::testBMACurveConsistency — fairLiborFraction
    # recovers the input BMA quotes after bootstrap.
    risk_free, bma, libor, bma_freq, bma_conv, bma_dc = _bma_bootstrap()
    for years, fraction_pct in _BMA_DATA:
        swap = ql.make_bma_swap(
            ql.SwapType.Payer,
            100.0,
            ql.Period(years, ql.TimeUnit.Years),
            0.75,
            0.0,
            libor,
            bma,
            risk_free,
            settlement_days=2,
            bma_frequency=bma_freq,
            bma_convention=bma_conv,
            bma_day_count=bma_dc,
        )
        expected = fraction_pct / 100.0
        assert swap.fair_libor_fraction() == pytest.approx(expected, abs=1.0e-9)


def test_fair_libor_fraction_zeros_npv():
    risk_free, bma, libor, bma_freq, bma_conv, bma_dc = _bma_bootstrap()
    probe = ql.make_bma_swap(
        ql.SwapType.Payer,
        100.0,
        ql.Period(5, ql.TimeUnit.Years),
        0.75,
        0.0,
        libor,
        bma,
        risk_free,
        bma_frequency=bma_freq,
        bma_convention=bma_conv,
        bma_day_count=bma_dc,
    )
    fair = probe.fair_libor_fraction()
    par = ql.make_bma_swap(
        ql.SwapType.Payer,
        100.0,
        ql.Period(5, ql.TimeUnit.Years),
        fair,
        0.0,
        libor,
        bma,
        risk_free,
        bma_frequency=bma_freq,
        bma_convention=bma_conv,
        bma_day_count=bma_dc,
    )
    assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)
    assert par.is_expired() is False


def test_payer_receiver_symmetry():
    risk_free, bma, libor, bma_freq, bma_conv, bma_dc = _bma_bootstrap()
    payer = ql.make_bma_swap(
        ql.SwapType.Payer,
        100.0,
        ql.Period(10, ql.TimeUnit.Years),
        0.70,
        0.0,
        libor,
        bma,
        risk_free,
        bma_frequency=bma_freq,
        bma_convention=bma_conv,
        bma_day_count=bma_dc,
    )
    receiver = ql.make_bma_swap(
        ql.SwapType.Receiver,
        100.0,
        ql.Period(10, ql.TimeUnit.Years),
        0.70,
        0.0,
        libor,
        bma,
        risk_free,
        bma_frequency=bma_freq,
        bma_convention=bma_conv,
        bma_day_count=bma_dc,
    )
    assert payer.NPV() + receiver.NPV() == pytest.approx(0.0, abs=1.0e-10)


def test_compat_phase100_aliases():
    import qlnb.compat as cql

    assert cql.BMAIndex is not None
    assert cql.BMASwap is not None
    assert cql.makeBMASwap is not None
    assert cql.BMASwapRateHelper is not None
    assert cql.JointCalendar is not None
    assert hasattr(cql.BMASwap, "fairLiborFraction")
    assert hasattr(cql.BMASwap, "liborLegNPV")
    assert hasattr(cql.BMASwap, "setPricingEngine")
    assert hasattr(cql.BMAIndex, "addFixing")
    assert hasattr(cql.BMAIndex, "isValidFixingDate")
