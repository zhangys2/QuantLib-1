"""Phase-72 tests: bond yield / duration / convexity / z-spread."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase72():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 73)


def _cached_bond1():
    # BondsTests::testCached bond1 (no-schedule ActualActual ISMA).
    today = ql.Date(22, ql.Month.November, 2004)
    ql.set_evaluation_date(today)
    calendar = ql.NullCalendar()
    freq = ql.Frequency.Semiannual
    schedule = ql.Schedule(
        ql.Date(31, ql.Month.October, 2004),
        ql.Date(31, ql.Month.October, 2006),
        ql.Period(freq),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        True,
    )
    dc = ql.ActualActual(ql.ActualActualConvention.ISMA)
    bond = ql.FixedRateBond(
        1,
        1_000_000.0,
        schedule,
        [0.025],
        dc,
        ql.BusinessDayConvention.ModifiedFollowing,
        100.0,
        ql.Date(1, ql.Month.November, 2004),
    )
    curve = ql.FlatForward(today, 0.03, ql.Actual360())
    bond.set_pricing_engine(curve)
    return bond, dc, freq, curve


def test_fixed_rate_bond_cached_yield_and_price():
    bond, dc, freq, _curve = _cached_bond1()
    assert bond.clean_price() == pytest.approx(98.943393, abs=1.0e-6)

    y_comp = bond.bond_yield(
        99.203125, dc, ql.Compounding.Compounded, freq
    )
    assert y_comp == pytest.approx(0.029257, abs=1.0e-6)

    y_cont = bond.bond_yield(
        99.203125, dc, ql.Compounding.Continuous, freq
    )
    assert y_cont == pytest.approx(0.029045, abs=1.0e-6)

    px = bond.clean_price(
        0.02925, dc, ql.Compounding.Compounded, freq
    )
    assert px == pytest.approx(99.204505, abs=1.0e-6)


def test_fixed_rate_bond_z_spread_round_trip():
    bond, _dc, freq, curve = _cached_bond1()
    spread = 0.005
    px = bond.clean_price_from_z_spread(
        curve, spread, ql.Compounding.Compounded, freq
    )
    impl = bond.z_spread(px, curve, ql.Compounding.Compounded, freq)
    assert impl == pytest.approx(spread, abs=1.0e-7)


def test_thirty360_yield_duration_convexity_accrued():
    # BondsTests::testThirty360BondWithSettlementOn31st (CUSIP 3130A0X70).
    ql.set_evaluation_date(ql.Date(28, ql.Month.July, 2017))
    dated = ql.Date(13, ql.Month.February, 2014)
    settlement = ql.Date(31, ql.Month.July, 2017)
    maturity = ql.Date(13, ql.Month.August, 2018)
    dc = ql.Thirty360(ql.Thirty360Convention.USA)
    schedule = ql.Schedule(
        dated,
        maturity,
        ql.Period(ql.Frequency.Semiannual),
        ql.UnitedStates(ql.UnitedStatesMarket.GovernmentBond),
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Forward,
        False,
    )
    bond = ql.FixedRateBond(
        1,
        100.0,
        schedule,
        [0.015],
        dc,
        ql.BusinessDayConvention.Unadjusted,
        100.0,
    )
    yld = bond.bond_yield(
        100.0,
        dc,
        ql.Compounding.Compounded,
        ql.Frequency.Semiannual,
        settlement,
    )
    assert yld == pytest.approx(0.015, abs=1.0e-4)

    mac = bond.duration(
        yld,
        dc,
        ql.Compounding.Compounded,
        ql.Frequency.Semiannual,
        ql.DurationType.Macaulay,
        settlement,
    )
    assert mac == pytest.approx(1.022, abs=1.0e-3)

    conv = bond.convexity(
        yld,
        dc,
        ql.Compounding.Compounded,
        ql.Frequency.Semiannual,
        settlement,
    )
    assert conv / 100.0 == pytest.approx(0.015, abs=1.0e-3)

    assert bond.accrued_amount(settlement) == pytest.approx(0.7, abs=1.0e-6)


def test_zero_coupon_bond_yield_round_trip():
    # Phase-5 cached zero (BondsTests::testCachedZero bond1).
    today = ql.Date(22, ql.Month.November, 2004)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.03, ql.Actual360())
    bond = ql.ZeroCouponBond(
        1,
        ql.UnitedStates(ql.UnitedStatesMarket.GovernmentBond),
        1_000_000.0,
        ql.Date(30, ql.Month.November, 2008),
        ql.BusinessDayConvention.ModifiedFollowing,
        100.0,
        ql.Date(30, ql.Month.November, 2004),
    )
    bond.set_pricing_engine(curve)
    price = bond.clean_price()
    assert price == pytest.approx(88.551726, abs=1.0e-6)
    dc = ql.Actual360()
    yld = bond.bond_yield(
        price, dc, ql.Compounding.Compounded, ql.Frequency.Annual
    )
    assert bond.clean_price(
        yld, dc, ql.Compounding.Compounded, ql.Frequency.Annual
    ) == pytest.approx(price, abs=1.0e-6)


def test_compat_phase72_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.FixedRateBond, "bondYield")
    assert hasattr(cql.FixedRateBond, "zSpread")
    assert hasattr(cql.ZeroCouponBond, "bondYield")
    assert hasattr(cql.DurationType, "Macaulay")
