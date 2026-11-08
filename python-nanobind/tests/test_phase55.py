"""Phase-55 tests: callable bond Black implied volatility."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase55():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 56)


def _implied_vol_bond():
    # Mirrors CallableBondTests::testImpliedVol / Globals.
    calendar = ql.TARGET()
    today = ql.Date(3, ql.Month.June, 2004)
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
    curve = ql.FlatForward(settlement, 0.03, ql.Actual365Fixed())
    issue = calendar.adjust(today - 100)
    maturity = calendar.advance(issue, 10, ql.TimeUnit.Years)
    schedule = ql.Schedule(
        issue,
        maturity,
        ql.Period(ql.Frequency.Semiannual),
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.DateGeneration.Backward,
        False,
    )
    calls = [
        ql.make_callability(
            100.0,
            ql.BondPriceType.Clean,
            ql.CallabilityType.Call,
            schedule[8],
        )
    ]
    bond = ql.CallableFixedRateBond(
        3,
        10000.0,
        schedule,
        [0.01],
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        ql.BusinessDayConvention.ModifiedFollowing,
        100.0,
        issue,
        calls,
    )
    return bond, curve


def test_implied_vol_roundtrip_dirty():
    bond, curve = _implied_vol_bond()
    target = ql.BondPrice(78.50, ql.BondPriceType.Dirty)
    vol = bond.implied_volatility(
        target, curve, accuracy=1e-8, max_evaluations=200, min_vol=1e-4, max_vol=1.0
    )
    assert vol > 0.0
    bond.set_black_pricing_engine(vol, curve)
    assert bond.dirty_price() == pytest.approx(78.50, abs=1e-4)


def test_implied_vol_roundtrip_clean():
    bond, curve = _implied_vol_bond()
    target = ql.BondPrice(78.50, ql.BondPriceType.Clean)
    vol = bond.implied_volatility(target, curve)
    assert vol > 0.0
    bond.set_black_pricing_engine(vol, curve)
    assert bond.clean_price() == pytest.approx(78.50, abs=1e-4)


def test_zero_coupon_implied_vol_and_compat():
    calendar = ql.TARGET()
    today = ql.Date(20, ql.Month.September, 2022)
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 3, ql.TimeUnit.Days)
    curve = ql.FlatForward(settlement, 0.03, ql.Actual365Fixed())
    issue = calendar.adjust(today - 100)
    maturity = calendar.advance(issue, 10, ql.TimeUnit.Years)
    call_date = calendar.advance(issue, 4, ql.TimeUnit.Years)
    bond = ql.CallableZeroCouponBond(
        3,
        10000.0,
        calendar,
        maturity,
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        ql.BusinessDayConvention.ModifiedFollowing,
        100.0,
        issue,
        [
            ql.make_callability(
                100.0,
                ql.BondPriceType.Clean,
                ql.CallabilityType.Call,
                call_date,
            )
        ],
    )
    # Price at known vol 0.3, then recover IV from that clean price.
    bond.set_black_pricing_engine(0.3, curve)
    target_clean = bond.clean_price()
    vol = bond.implied_volatility(
        ql.BondPrice(target_clean, ql.BondPriceType.Clean), curve
    )
    assert vol == pytest.approx(0.3, abs=1e-4)

    import qlnb.compat as cql

    assert hasattr(cql.CallableFixedRateBond, "impliedVolatility")
    assert hasattr(cql.CallableZeroCouponBond, "impliedVolatility")
