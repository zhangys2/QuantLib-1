"""Phase-98 tests: FloatFloatSwap (suite fair-spread NPV-zeroing)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase98():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 99)


def _common_vars():
    # FloatFloatSwapTests::CommonVars — flat 5%, Euribor3M vs Euribor6M.
    calendar = ql.TARGET()
    today = calendar.adjust(ql.get_evaluation_date())
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual365Fixed())
    index1 = ql.Euribor3M(curve)
    index2 = ql.Euribor6M(curve)
    return calendar, curve, index1, index2


def _make_swap(curve, index1, index2, typ, spread1, spread2, nominal=100.0, years=10):
    return ql.make_float_float_swap(
        typ,
        nominal,
        index1,
        index2,
        curve,
        spread1=spread1,
        spread2=spread2,
        length_in_years=years,
        settlement_days=2,
    )


def test_fair_spread1_zeros_npv():
    # FloatFloatSwapTests::testFairSpread1.
    _cal, curve, index1, index2 = _common_vars()
    for typ in (ql.SwapType.Payer, ql.SwapType.Receiver):
        for spread2 in (-0.002, 0.0, 0.002, 0.005):
            swap = _make_swap(curve, index1, index2, typ, 0.0, spread2)
            fair = swap.fair_spread1()
            par = _make_swap(curve, index1, index2, typ, fair, spread2)
            assert par.NPV() == pytest.approx(0.0, abs=1.0e-10)


def test_fair_spread2_zeros_npv():
    # FloatFloatSwapTests::testFairSpread2.
    _cal, curve, index1, index2 = _common_vars()
    for typ in (ql.SwapType.Payer, ql.SwapType.Receiver):
        for spread1 in (-0.002, 0.0, 0.002, 0.005):
            swap = _make_swap(curve, index1, index2, typ, spread1, 0.0)
            fair = swap.fair_spread2()
            par = _make_swap(curve, index1, index2, typ, spread1, fair)
            assert par.NPV() == pytest.approx(0.0, abs=1.0e-10)


def test_payer_receiver_symmetry():
    # FloatFloatSwapTests::testPayerReceiverSymmetry.
    _cal, curve, index1, index2 = _common_vars()
    payer = _make_swap(curve, index1, index2, ql.SwapType.Payer, 0.001, 0.003)
    receiver = _make_swap(
        curve, index1, index2, ql.SwapType.Receiver, 0.001, 0.003
    )
    assert payer.NPV() + receiver.NPV() == pytest.approx(0.0, abs=1.0e-10)
    assert payer.is_expired() is False


def test_fair_spread_payer_receiver_consistency():
    # FloatFloatSwapTests::testFairSpreadPayerReceiverConsistency.
    _cal, curve, index1, index2 = _common_vars()
    payer = _make_swap(curve, index1, index2, ql.SwapType.Payer, 0.0, 0.002)
    receiver = _make_swap(
        curve, index1, index2, ql.SwapType.Receiver, 0.0, 0.002
    )
    assert payer.fair_spread1() == pytest.approx(
        receiver.fair_spread1(), abs=1.0e-10
    )

    payer2 = _make_swap(curve, index1, index2, ql.SwapType.Payer, 0.002, 0.0)
    receiver2 = _make_swap(
        curve, index1, index2, ql.SwapType.Receiver, 0.002, 0.0
    )
    assert payer2.fair_spread2() == pytest.approx(
        receiver2.fair_spread2(), abs=1.0e-10
    )


def test_zero_bps_fair_spread_unavailable():
    # FloatFloatSwapTests::testZeroBpsFairSpread.
    _cal, curve, index1, index2 = _common_vars()
    swap = _make_swap(curve, index1, index2, ql.SwapType.Payer, 0.0, 0.0, nominal=0.0)
    assert swap.is_expired() is False
    assert swap.leg_BPS(0) == 0.0
    assert swap.leg_BPS(1) == 0.0
    with pytest.raises(RuntimeError, match="fair spread 1 not available"):
        swap.fair_spread1()
    with pytest.raises(RuntimeError, match="fair spread 2 not available"):
        swap.fair_spread2()


def test_expired_swap_fair_spread_unavailable():
    # FloatFloatSwapTests::testExpiredSwapFairSpread.
    calendar, curve, index1, index2 = _common_vars()
    settlement = calendar.advance(ql.get_evaluation_date(), 2, ql.TimeUnit.Days)
    swap = _make_swap(curve, index1, index2, ql.SwapType.Payer, 0.0, 0.0)
    ql.set_evaluation_date(settlement + ql.Period(20, ql.TimeUnit.Years))
    assert swap.is_expired() is True
    with pytest.raises(RuntimeError, match="fair spread 1 not available"):
        swap.fair_spread1()
    with pytest.raises(RuntimeError, match="fair spread 2 not available"):
        swap.fair_spread2()


def test_native_constructor_and_engine():
    calendar, curve, index1, index2 = _common_vars()
    today = ql.get_evaluation_date()
    settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
    maturity = calendar.advance(
        settlement, 10, ql.TimeUnit.Years, ql.BusinessDayConvention.ModifiedFollowing
    )
    sched1 = ql.Schedule(
        settlement,
        maturity,
        index1.tenor(),
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.DateGeneration.Forward,
        False,
    )
    sched2 = ql.Schedule(
        settlement,
        maturity,
        index2.tenor(),
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.DateGeneration.Forward,
        False,
    )
    swap = ql.FloatFloatSwap(
        ql.SwapType.Payer,
        100.0,
        100.0,
        sched1,
        index1,
        index1.day_counter(),
        sched2,
        index2,
        index2.day_counter(),
        spread1=0.0,
        spread2=0.002,
    )
    swap.set_pricing_engine(curve)
    fair = swap.fair_spread1()
    assert isinstance(fair, float)
    assert swap.NPV() != 0.0 or abs(fair) < 1.0e-12


def test_compat_phase98_aliases():
    import qlnb.compat as cql

    assert cql.makeFloatFloatSwap is not None
    assert cql.FloatFloatSwap is not None
    assert hasattr(cql.FloatFloatSwap, "fairSpread1")
    assert hasattr(cql.FloatFloatSwap, "fairSpread2")
    assert hasattr(cql.FloatFloatSwap, "legNPV")
    assert hasattr(cql.FloatFloatSwap, "setPricingEngine")
    assert hasattr(cql.FloatFloatSwap, "isExpired")
