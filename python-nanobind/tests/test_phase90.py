"""Phase-90 tests: ZeroCouponSwap (suite NPV replication + fair payment/rate)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase90():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 91)


def _common_vars():
    # ZeroCouponSwapTests::CommonVars — 15 Mar 2021, flat 0.7% Actual365Fixed.
    calendar = ql.TARGET()
    today = calendar.adjust(ql.Date(15, ql.Month.March, 2021))
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
    dc = ql.Actual365Fixed()
    curve = ql.FlatForward(settlement, 0.007, dc)
    ibor = ql.Euribor6M(curve)
    ibor.add_fixing(ql.Date(10, ql.Month.February, 2021), 0.0085, True)
    return calendar, today, settlement, dc, curve, ibor


def _zc_swap(typ, start, end, payment=1.2e6):
    calendar, _today, _settlement, _dc, curve, ibor = _common_vars()
    swap = ql.ZeroCouponSwap(
        typ,
        1.0e6,
        start,
        end,
        payment,
        ibor,
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        1,
    )
    swap.set_pricing_engine(curve)
    return swap, calendar, curve


def _type_sign(typ) -> int:
    # QuantLib Swap::Receiver = -1, Swap::Payer = +1.
    return -1 if typ == ql.SwapType.Receiver else 1


def test_instrument_valuation_ongoing_receiver():
    # ZeroCouponSwapTests::testInstrumentValuation — ongoing Receiver.
    start = ql.Date(12, ql.Month.February, 2021)
    end = ql.Date(12, ql.Month.February, 2041)
    swap, calendar, curve = _zc_swap(ql.SwapType.Receiver, start, end)
    payment_date = calendar.advance(
        end, 1, ql.TimeUnit.Days, ql.BusinessDayConvention.ModifiedFollowing
    )
    discount = curve.discount(payment_date)
    expected_fixed = -_type_sign(ql.SwapType.Receiver) * discount * 1.2e6
    assert swap.fixed_leg_NPV() == pytest.approx(expected_fixed, abs=1.0e-8)
    assert swap.NPV() == pytest.approx(
        swap.fixed_leg_NPV() + swap.floating_leg_NPV(), abs=1.0e-10
    )
    assert swap.is_expired() is False
    assert swap.fixed_payment() == pytest.approx(1.2e6)
    assert swap.base_nominal() == pytest.approx(1.0e6)
    assert swap.type() == ql.SwapType.Receiver


def test_instrument_valuation_forward_payer():
    # Forward-starting Payer 15 Apr 2021 → 12 Feb 2041.
    start = ql.Date(15, ql.Month.April, 2021)
    end = ql.Date(12, ql.Month.February, 2041)
    swap, calendar, curve = _zc_swap(ql.SwapType.Payer, start, end)
    payment_date = calendar.advance(
        end, 1, ql.TimeUnit.Days, ql.BusinessDayConvention.ModifiedFollowing
    )
    discount = curve.discount(payment_date)
    expected_fixed = -_type_sign(ql.SwapType.Payer) * discount * 1.2e6
    assert swap.fixed_leg_NPV() == pytest.approx(expected_fixed, abs=1.0e-8)
    assert swap.NPV() == pytest.approx(
        swap.fixed_leg_NPV() + swap.floating_leg_NPV(), abs=1.0e-10
    )


def test_instrument_valuation_expired():
    # Expired 12 Feb 2000 → 12 Feb 2020 — payment before settlement ⇒ NPV 0.
    start = ql.Date(12, ql.Month.February, 2000)
    end = ql.Date(12, ql.Month.February, 2020)
    swap, _calendar, _curve = _zc_swap(ql.SwapType.Receiver, start, end)
    assert swap.NPV() == pytest.approx(0.0, abs=1.0e-8)
    assert swap.fixed_leg_NPV() == pytest.approx(0.0, abs=1.0e-8)
    assert swap.floating_leg_NPV() == pytest.approx(0.0, abs=1.0e-8)
    assert swap.is_expired() is True


def test_fair_fixed_payment():
    # ZeroCouponSwapTests::testFairFixedPayment — ongoing Receiver.
    start = ql.Date(12, ql.Month.February, 2021)
    end = ql.Date(12, ql.Month.February, 2041)
    swap, _calendar, _curve = _zc_swap(ql.SwapType.Receiver, start, end)
    fair = swap.fair_fixed_payment()
    par, _cal, _crv = _zc_swap(ql.SwapType.Receiver, start, end, payment=fair)
    assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)


def test_fair_fixed_rate():
    # ZeroCouponSwapTests::testFairFixedRate — ongoing Receiver via rate ctor.
    calendar, _today, _settlement, dc, curve, ibor = _common_vars()
    start = ql.Date(12, ql.Month.February, 2021)
    end = ql.Date(12, ql.Month.February, 2041)
    swap = ql.ZeroCouponSwap(
        ql.SwapType.Receiver,
        1.0e6,
        start,
        end,
        1.2e6,
        ibor,
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        1,
    )
    swap.set_pricing_engine(curve)
    fair_rate = swap.fair_fixed_rate(dc)
    par = ql.ZeroCouponSwap(
        ql.SwapType.Receiver,
        1.0e6,
        start,
        end,
        fair_rate,
        dc,
        ibor,
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        1,
    )
    par.set_pricing_engine(curve)
    assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)


def test_compat_phase90_aliases():
    import qlnb.compat as cql

    assert cql.ZeroCouponSwap is not None
    assert hasattr(cql.ZeroCouponSwap, "fairFixedPayment")
    assert hasattr(cql.ZeroCouponSwap, "fairFixedRate")
    assert hasattr(cql.ZeroCouponSwap, "fixedLegNPV")
    assert hasattr(cql.ZeroCouponSwap, "setPricingEngine")
