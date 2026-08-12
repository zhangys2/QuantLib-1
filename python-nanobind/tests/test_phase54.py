"""Phase-54 tests: Black callable bond engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase54():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 55)


def test_black_zero_coupon_cached_price():
    # Mirrors CallableBondTests::testBlackEngine.
    calendar = ql.TARGET()
    today = ql.Date(20, ql.Month.September, 2022)
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 3, ql.TimeUnit.Days)
    dc = ql.Actual365Fixed()
    curve = ql.FlatForward(settlement, 0.03, dc)
    issue = calendar.adjust(today - 100)
    maturity = calendar.advance(issue, 10, ql.TimeUnit.Years)
    call_date = calendar.advance(issue, 4, ql.TimeUnit.Years)
    calls = [
        ql.make_callability(
            100.0, ql.BondPriceType.Clean, ql.CallabilityType.Call, call_date
        )
    ]
    bond = ql.CallableZeroCouponBond(
        3,
        10000.0,
        calendar,
        maturity,
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        ql.BusinessDayConvention.ModifiedFollowing,
        100.0,
        issue,
        calls,
    )
    bond.set_black_pricing_engine(0.3, curve)
    assert bond.clean_price() == pytest.approx(74.54521578, abs=1e-4)


def test_black_fixed_rate_deep_itm():
    # Mirrors CallableBondTests::testBlackEngineDeepInTheMoney.
    calendar = ql.TARGET()
    today = ql.Date(20, ql.Month.September, 2022)
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 3, ql.TimeUnit.Days)
    dc = ql.Actual365Fixed()
    curve = ql.FlatForward(settlement, 0.05, dc)
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
    # schedule.at(6) — 0-based index 6 in the coupon schedule.
    call_date = schedule[6]
    strike = 50.0
    calls = [
        ql.make_callability(
            strike, ql.BondPriceType.Clean, ql.CallabilityType.Call, call_date
        )
    ]
    bond = ql.CallableFixedRateBond(
        3,
        10000.0,
        schedule,
        [0.0],
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        ql.BusinessDayConvention.ModifiedFollowing,
        100.0,
        issue,
        calls,
    )
    bond.set_black_pricing_engine(1e-10, curve)
    expected = (
        strike
        * curve.discount(call_date)
        / curve.discount(bond.settlement_date())
    )
    assert bond.clean_price() == pytest.approx(expected, abs=1e-8)


def test_black_engine_quote_handle_and_compat():
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
    bond.set_black_pricing_engine(ql.make_quote_handle(0.3), curve)
    assert bond.clean_price() == pytest.approx(74.54521578, abs=1e-4)

    import qlnb.compat as cql

    assert hasattr(cql.CallableZeroCouponBond, "setBlackPricingEngine")
    assert hasattr(cql.CallableFixedRateBond, "setBlackPricingEngine")
    assert ql.BlackCallableZeroCouponBondEngine is not None
    assert ql.BlackCallableFixedRateBondEngine is not None
