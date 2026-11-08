"""Phase-94 tests: EquityTotalReturnSwap (suite equity-leg NPV + fair margin)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase94():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 95)


# Sofr overnight fixings from EquityTotalReturnSwapTests::CommonVars.
_SOFR_FIXINGS = (
    (ql.Date(3, ql.Month.January, 2023), 0.03),
    (ql.Date(4, ql.Month.January, 2023), 0.031),
    (ql.Date(5, ql.Month.January, 2023), 0.031),
    (ql.Date(6, ql.Month.January, 2023), 0.031),
    (ql.Date(9, ql.Month.January, 2023), 0.032),
    (ql.Date(10, ql.Month.January, 2023), 0.033),
    (ql.Date(11, ql.Month.January, 2023), 0.033),
    (ql.Date(12, ql.Month.January, 2023), 0.033),
    (ql.Date(13, ql.Month.January, 2023), 0.033),
    (ql.Date(17, ql.Month.January, 2023), 0.033),
    (ql.Date(18, ql.Month.January, 2023), 0.034),
    (ql.Date(19, ql.Month.January, 2023), 0.034),
    (ql.Date(20, ql.Month.January, 2023), 0.034),
    (ql.Date(23, ql.Month.January, 2023), 0.034),
    (ql.Date(24, ql.Month.January, 2023), 0.034),
    (ql.Date(25, ql.Month.January, 2023), 0.034),
    (ql.Date(26, ql.Month.January, 2023), 0.034),
)


def _common_vars():
    # EquityTotalReturnSwapTests::CommonVars — 27 Jan 2023, USD, 3.75%/0.5%.
    calendar = ql.UnitedStates(ql.UnitedStatesMarket.GovernmentBond)
    day_count = ql.Actual365Fixed()
    today = calendar.adjust(ql.Date(27, ql.Month.January, 2023))
    ql.set_evaluation_date(today)

    interest = ql.FlatForward(today, 0.0375, day_count)
    dividend = ql.FlatForward(today, 0.005, day_count)
    spot = ql.make_quote_handle(8700.0)

    equity = ql.EquityIndex(
        "eqIndex", calendar, ql.USDCurrency(), interest, dividend, spot
    )
    equity.add_fixing(ql.Date(5, ql.Month.January, 2023), 9010.0, True)
    equity.add_fixing(today, 8690.0, True)

    sofr = ql.Sofr(interest)
    for date, fixing in _SOFR_FIXINGS:
        sofr.add_fixing(date, fixing, True)

    libor = ql.USDLibor(ql.Period(3, ql.TimeUnit.Months), interest)
    libor.add_fixing(ql.Date(3, ql.Month.January, 2023), 0.035, True)

    return today, calendar, day_count, interest, equity, libor, sofr


def _make_schedule(calendar, start, end):
    return ql.Schedule(
        start,
        end,
        ql.Period(3, ql.TimeUnit.Months),
        calendar,
        ql.BusinessDayConvention.Following,
        ql.BusinessDayConvention.Following,
        ql.DateGeneration.Backward,
        False,
    )


def _create_trs(
    equity,
    interest_index,
    calendar,
    day_count,
    discount,
    typ,
    start,
    end,
    margin=0.0,
    nominal=1.0e7,
    gearing=1.0,
    payment_delay=0,
):
    trs = ql.EquityTotalReturnSwap(
        typ,
        nominal,
        _make_schedule(calendar, start, end),
        equity,
        interest_index,
        day_count,
        margin,
        gearing,
        calendar,
        ql.BusinessDayConvention.Following,
        payment_delay,
    )
    trs.set_pricing_engine(discount)
    return trs


def test_equity_leg_npv_replicates():
    # EquityTotalReturnSwapTests::testEquityLegNPV.
    _today, calendar, day_count, interest, equity, libor, _sofr = _common_vars()
    start = ql.Date(5, ql.Month.January, 2023)
    end = ql.Date(5, ql.Month.April, 2023)
    trs = _create_trs(
        equity, libor, calendar, day_count, interest, ql.SwapType.Receiver, start, end
    )
    expected = (
        (equity.fixing(end) / equity.fixing(start) - 1.0)
        * trs.nominal()
        * interest.discount(end)
    )
    assert trs.equity_leg_NPV() == pytest.approx(expected, abs=1.0e-8)
    assert trs.is_expired() is False
    assert trs.type() == ql.SwapType.Receiver
    assert trs.nominal() == pytest.approx(1.0e7)
    assert trs.margin() == pytest.approx(0.0)
    assert trs.gearing() == pytest.approx(1.0)


def test_fair_margin_zeros_npv_libor():
    # EquityTotalReturnSwapTests::testFairMargin (Libor receiver, default margin).
    _today, calendar, day_count, interest, equity, libor, _sofr = _common_vars()
    start = ql.Date(5, ql.Month.January, 2023)
    end = ql.Date(5, ql.Month.April, 2023)
    trs = _create_trs(
        equity, libor, calendar, day_count, interest, ql.SwapType.Receiver, start, end
    )
    par = _create_trs(
        equity,
        libor,
        calendar,
        day_count,
        interest,
        ql.SwapType.Receiver,
        start,
        end,
        margin=trs.fair_margin(),
    )
    assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)


def test_fair_margin_zeros_npv_overnight():
    # EquityTotalReturnSwapTests::testFairMargin (Sofr receiver).
    _today, calendar, day_count, interest, equity, _libor, sofr = _common_vars()
    start = ql.Date(5, ql.Month.January, 2023)
    end = ql.Date(5, ql.Month.April, 2023)
    trs = _create_trs(
        equity, sofr, calendar, day_count, interest, ql.SwapType.Receiver, start, end
    )
    par = _create_trs(
        equity,
        sofr,
        calendar,
        day_count,
        interest,
        ql.SwapType.Receiver,
        start,
        end,
        margin=trs.fair_margin(),
    )
    assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)


def test_fair_margin_payer_with_margin_and_delay():
    # Suite also checks payer+margin, zero gearing, and payment delay 2.
    _today, calendar, day_count, interest, equity, libor, sofr = _common_vars()
    start = ql.Date(5, ql.Month.January, 2023)
    end = ql.Date(5, ql.Month.April, 2023)
    delayed_start = ql.Date(31, ql.Month.January, 2023)
    delayed_end = ql.Date(30, ql.Month.April, 2023)

    cases = (
        (ql.SwapType.Payer, libor, 0.01, 1.0, 0, start, end),
        (ql.SwapType.Payer, libor, 0.0, 0.0, 0, start, end),
        (ql.SwapType.Receiver, libor, -0.005, 1.0, 2, delayed_start, delayed_end),
        (ql.SwapType.Payer, sofr, 0.01, 1.0, 0, start, end),
        (ql.SwapType.Receiver, sofr, -0.005, 1.0, 2, delayed_start, delayed_end),
    )
    for typ, index, margin, gearing, delay, s, e in cases:
        trs = _create_trs(
            equity,
            index,
            calendar,
            day_count,
            interest,
            typ,
            s,
            e,
            margin=margin,
            gearing=gearing,
            payment_delay=delay,
        )
        par = _create_trs(
            equity,
            index,
            calendar,
            day_count,
            interest,
            typ,
            s,
            e,
            margin=trs.fair_margin(),
            gearing=gearing,
            payment_delay=delay,
        )
        assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)
        assert trs.payment_delay() == delay


def test_trs_npv_equals_sum_of_legs():
    # EquityTotalReturnSwapTests::testTRSNPV (tol 1e-2).
    _today, calendar, day_count, interest, equity, libor, sofr = _common_vars()
    start = ql.Date(5, ql.Month.January, 2023)
    end = ql.Date(5, ql.Month.April, 2023)
    for typ, index, margin, gearing in (
        (ql.SwapType.Receiver, libor, 0.0, 1.0),
        (ql.SwapType.Payer, libor, 0.01, 1.0),
        (ql.SwapType.Payer, libor, 0.0, 0.0),
        (ql.SwapType.Receiver, sofr, 0.0, 1.0),
        (ql.SwapType.Payer, sofr, 0.01, 1.0),
    ):
        trs = _create_trs(
            equity,
            index,
            calendar,
            day_count,
            interest,
            typ,
            start,
            end,
            margin=margin,
            gearing=gearing,
        )
        assert trs.NPV() == pytest.approx(
            trs.equity_leg_NPV() + trs.interest_rate_leg_NPV(), abs=1.0e-2
        )


def test_negative_nominal_raises():
    # EquityTotalReturnSwapTests::testErrorWhenNegativeNominal.
    _today, calendar, day_count, interest, equity, libor, _sofr = _common_vars()
    with pytest.raises(RuntimeError, match="Nominal cannot be negative"):
        _create_trs(
            equity,
            libor,
            calendar,
            day_count,
            interest,
            ql.SwapType.Receiver,
            ql.Date(5, ql.Month.January, 2023),
            ql.Date(5, ql.Month.April, 2023),
            nominal=-1.0e7,
        )


def test_compat_phase94_aliases():
    import qlnb.compat as cql

    assert cql.USDLibor is not None
    assert cql.EquityIndex is not None
    assert cql.EquityTotalReturnSwap is not None
    assert hasattr(cql.EquityIndex, "addFixing")
    assert hasattr(cql.EquityTotalReturnSwap, "fairMargin")
    assert hasattr(cql.EquityTotalReturnSwap, "equityLegNPV")
    assert hasattr(cql.EquityTotalReturnSwap, "setPricingEngine")
