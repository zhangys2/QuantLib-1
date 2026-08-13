"""Phase-56 tests: callable bond OAS / cleanPriceOAS / effective risk."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase56():
    assert ql.__version__ == "0.57.0"


def _oas_notional_bonds():
    # Mirrors CallableBondTests::testCallableBondOasWithDifferentNotinals.
    calendar = ql.TARGET()
    today = ql.Date(10, ql.Month.January, 2020)
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
    dc = ql.Actual365Fixed()
    curve = ql.FlatForward(settlement, 0.03, dc)
    model = ql.HullWhite(curve)
    issue = calendar.adjust(today - 100)
    maturity = calendar.advance(issue, 10, ql.TimeUnit.Years)
    frequency = ql.Frequency.Semiannual
    bdc = ql.BusinessDayConvention.ModifiedFollowing
    schedule = ql.Schedule(
        issue,
        maturity,
        ql.Period(frequency),
        calendar,
        bdc,
        bdc,
        ql.DateGeneration.Backward,
        False,
    )
    first_call = schedule[schedule.size() - 5]
    last_call = schedule[schedule.size() - 2]
    calls = [
        ql.make_callability(
            100.0, ql.BondPriceType.Clean, ql.CallabilityType.Call, d
        )
        for d in schedule.dates()
        if first_call <= d <= last_call
    ]
    coupons = [0.055]
    bond100 = ql.CallableFixedRateBond(
        2, 100.0, schedule, coupons, dc, bdc, 100.0, issue, calls
    )
    bond25 = ql.CallableFixedRateBond(
        2, 25.0, schedule, coupons, dc, bdc, 100.0, issue, calls
    )
    bond100.set_tree_pricing_engine(model, 240, curve)
    bond25.set_tree_pricing_engine(model, 240, curve)
    return bond100, bond25, curve, dc, frequency


def test_oas_equal_across_notionals():
    bond100, bond25, curve, dc, frequency = _oas_notional_bonds()
    compounding = ql.Compounding.Compounded
    clean_price = 96.0
    oas100 = bond100.oas(clean_price, curve, dc, compounding, frequency)
    oas25 = bond25.oas(clean_price, curve, dc, compounding, frequency)
    assert oas100 == oas25

    oas = 0.03
    price100 = bond100.clean_price_oas(oas, curve, dc, compounding, frequency)
    price25 = bond25.clean_price_oas(oas, curve, dc, compounding, frequency)
    assert price100 == price25


def test_oas_roundtrip_from_model_clean_price():
    # Reuse Phase-23 cached callable setup (clean ≈ 110.60975477).
    calendar = ql.TARGET()
    today = ql.Date(3, ql.Month.June, 2004)
    ql.set_evaluation_date(today)
    settlement = calendar.advance(today, 3, ql.TimeUnit.Days)
    dc = ql.Actual365Fixed()
    curve = ql.FlatForward(settlement, 0.032, dc)
    model = ql.HullWhite(curve)
    issue = calendar.adjust(today - 100)
    maturity = calendar.advance(issue, 10, ql.TimeUnit.Years)
    bdc = ql.BusinessDayConvention.ModifiedFollowing
    schedule = ql.Schedule(
        issue,
        maturity,
        ql.Period(ql.Frequency.Semiannual),
        calendar,
        bdc,
        bdc,
        ql.DateGeneration.Backward,
        False,
    )
    calls = [
        ql.make_callability(
            110.0, ql.BondPriceType.Clean, ql.CallabilityType.Call, d
        )
        for d in (
            calendar.advance(issue, i, ql.TimeUnit.Years) for i in range(2, 10, 2)
        )
    ]
    bond = ql.CallableFixedRateBond(
        3,
        10000.0,
        schedule,
        [0.05],
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        bdc,
        100.0,
        issue,
        calls,
    )
    bond.set_tree_pricing_engine(model, 240, curve)
    model_clean = bond.clean_price()
    assert model_clean == pytest.approx(110.60975477, abs=1.0e-8)

    compounding = ql.Compounding.Compounded
    frequency = ql.Frequency.Semiannual
    oas = bond.oas(model_clean, curve, dc, compounding, frequency)
    assert oas == pytest.approx(0.0, abs=1.0e-6)
    recovered = bond.clean_price_oas(oas, curve, dc, compounding, frequency)
    assert recovered == pytest.approx(model_clean, abs=1.0e-4)


def test_effective_duration_and_convexity():
    # Mirrors CallableBondTests::testEffectiveDurationAndConvexity.
    settlement_date = ql.Date(30, ql.Month.November, 2023)
    ql.set_evaluation_date(settlement_date)
    effective = ql.Date(20, ql.Month.May, 2021)
    maturity = ql.Date(1, ql.Month.June, 2029)
    calendar = ql.UnitedStates(ql.UnitedStatesMarket.GovernmentBond)
    day_count = ql.Thirty360(ql.Thirty360Convention.ISDA)
    schedule = ql.Schedule(
        effective,
        maturity,
        ql.Period(6, ql.TimeUnit.Months),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        True,
    )
    calls = [
        ql.make_callability(
            102.438,
            ql.BondPriceType.Clean,
            ql.CallabilityType.Call,
            ql.Date(1, ql.Month.June, 2024),
        ),
        ql.make_callability(
            101.219,
            ql.BondPriceType.Clean,
            ql.CallabilityType.Call,
            ql.Date(1, ql.Month.June, 2025),
        ),
        ql.make_callability(
            100.0,
            ql.BondPriceType.Clean,
            ql.CallabilityType.Call,
            ql.Date(1, ql.Month.June, 2026),
        ),
        ql.make_callability(
            100.0,
            ql.BondPriceType.Clean,
            ql.CallabilityType.Call,
            ql.Date(1, ql.Month.June, 2029),
        ),
    ]
    bond = ql.CallableFixedRateBond(
        2,
        100.0,
        schedule,
        [0.04875],
        day_count,
        ql.BusinessDayConvention.Unadjusted,
        100.0,
        effective,
        calls,
    )
    ref = calendar.advance(settlement_date, 2, ql.TimeUnit.Days)
    curve = ql.FlatForward(ref, 0.05, day_count)
    model = ql.HullWhite(curve, 0.03, 0.012)
    grid_steps = (
        maturity.serial_number() - settlement_date.serial_number()
    ) // 30
    bond.set_tree_pricing_engine(model, grid_steps, curve)

    compounding = ql.Compounding.Compounded
    frequency = ql.Frequency.Semiannual
    clean_price = 70.926
    oas = bond.oas(
        clean_price, curve, day_count, compounding, frequency, settlement_date
    )
    shift = 0.001
    eff_dur = bond.effective_duration(
        oas, curve, day_count, compounding, frequency, shift
    )
    eff_conv = bond.effective_convexity(
        oas, curve, day_count, compounding, frequency, shift
    )

    # effective_duration/convexity use bond.settlement_date() (not the OAS
    # settlement override), so rebuild the finite-difference check the same way.
    accrued = bond.dirty_price() - bond.clean_price()
    p0 = bond.clean_price_oas(oas, curve, day_count, compounding, frequency) + accrued
    p_up = (
        bond.clean_price_oas(oas + shift, curve, day_count, compounding, frequency)
        + accrued
    )
    p_down = (
        bond.clean_price_oas(oas - shift, curve, day_count, compounding, frequency)
        + accrued
    )
    expected_dur = (p_down - p_up) / (2.0 * p0 * shift)
    expected_conv = (p_down + p_up - 2.0 * p0) / (p0 * shift * shift)
    assert eff_dur == pytest.approx(expected_dur, rel=1e-4)
    assert eff_conv == pytest.approx(expected_conv, rel=1e-4)
    assert eff_dur > 0.0


def test_compat_phase56_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CallableFixedRateBond, "OAS")
    assert hasattr(cql.CallableFixedRateBond, "cleanPriceOAS")
    assert hasattr(cql.CallableFixedRateBond, "effectiveDuration")
    assert hasattr(cql.CallableFixedRateBond, "effectiveConvexity")
    assert hasattr(cql.CallableZeroCouponBond, "OAS")
    assert hasattr(cql.CallableZeroCouponBond, "cleanPriceOAS")
