"""Phase-57 tests: convertible bonds (Tsiveriotis–Fernandes binomial)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase57():
    assert ql.__version__ == "0.58.0"


def _convertible_market():
    # Mirrors ConvertibleBondTests::CommonVars with a pinned evaluation date.
    calendar = ql.TARGET()
    today = ql.Date(3, ql.Month.June, 2004)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    issue = calendar.advance(today, 2, ql.TimeUnit.Days)
    maturity = calendar.advance(issue, 10, ql.TimeUnit.Years)
    issue = calendar.advance(maturity, -10, ql.TimeUnit.Years)
    spot = ql.make_quote_handle(50.0)
    q = ql.FlatForward(today, 0.02, dc)
    r = ql.FlatForward(today, 0.05, dc)
    vol = ql.BlackConstantVol(today, calendar, 0.15, dc)
    process = ql.BlackScholesMertonProcess(spot, q, r, vol)
    credit = ql.make_quote_handle(0.005)
    return today, calendar, dc, issue, maturity, process, credit, r


def test_otm_zero_convertible_matches_vanilla():
    # ConvertibleBondTests::testBond — deeply OTM ≈ plain zero.
    today, calendar, dc, issue, maturity, process, credit, r = _convertible_market()
    discount = ql.FlatForward(today, 0.055, dc)  # r + credit spread
    schedule = ql.Schedule(
        issue,
        maturity,
        ql.Period(ql.Frequency.Once),
        calendar,
        ql.BusinessDayConvention.Following,
        ql.BusinessDayConvention.Following,
        ql.DateGeneration.Backward,
        False,
    )
    exercise = ql.EuropeanExercise(maturity)
    conversion_ratio = 1.0e-16
    bond = ql.ConvertibleZeroCouponBond(
        exercise, conversion_ratio, [], issue, 3, dc, schedule, 100.0
    )
    bond.set_binomial_pricing_engine(process, 1001, credit)
    vanilla = ql.ZeroCouponBond(
        3, calendar, 100.0, maturity, ql.BusinessDayConvention.Following, 100.0, issue
    )
    vanilla.set_pricing_engine(discount)
    assert bond.NPV() == pytest.approx(vanilla.settlement_value(), abs=0.02)
    assert bond.conversion_ratio() == conversion_ratio


def test_otm_fixed_convertible_matches_vanilla():
    today, calendar, dc, issue, maturity, process, credit, r = _convertible_market()
    discount = ql.FlatForward(today, 0.055, dc)
    schedule = ql.Schedule(
        issue,
        maturity,
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.Following,
        ql.BusinessDayConvention.Following,
        ql.DateGeneration.Backward,
        False,
    )
    exercise = ql.AmericanExercise(issue, maturity)
    conversion_ratio = 1.0e-16
    coupons = [0.05]
    bond = ql.ConvertibleFixedCouponBond(
        exercise, conversion_ratio, [], issue, 3, coupons, dc, schedule, 100.0
    )
    bond.set_binomial_pricing_engine(process, 401, 0.005)
    vanilla = ql.FixedRateBond(
        3,
        100.0,
        schedule,
        coupons,
        dc,
        ql.BusinessDayConvention.Following,
        100.0,
        issue,
    )
    vanilla.set_pricing_engine(discount)
    assert bond.NPV() == pytest.approx(vanilla.settlement_value(), abs=0.04)


def test_zero_convertible_vs_vanilla_option():
    # ConvertibleBondTests::testOption — zero credit spread ≈ discounted
    # redemption + conversionRatio * CRR call.
    today, calendar, dc, issue, maturity, process, _credit, r = _convertible_market()
    conversion_ratio = 100.0 / 50.0
    strike = 100.0 / conversion_ratio
    schedule = ql.Schedule(
        issue,
        maturity,
        ql.Period(ql.Frequency.Once),
        calendar,
        ql.BusinessDayConvention.Following,
        ql.BusinessDayConvention.Following,
        ql.DateGeneration.Backward,
        False,
    )
    exercise = ql.EuropeanExercise(maturity)
    bond = ql.ConvertibleZeroCouponBond(
        exercise, conversion_ratio, [], issue, 0, dc, schedule, 100.0
    )
    bond.set_binomial_pricing_engine(process, 801, 0.0)
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        exercise,
    )
    option.set_binomial_pricing_engine(process, 801)
    expected = 100.0 * r.discount(maturity) + conversion_ratio * option.NPV()
    assert bond.NPV() == pytest.approx(expected, abs=0.10)


def test_soft_callability_and_compat():
    import qlnb.compat as cql

    d = ql.Date(1, ql.Month.June, 2010)
    soft = ql.make_soft_callability(
        110.0, ql.BondPriceType.Clean, d, 1.2
    )
    assert soft.date() == d
    assert soft.type() == ql.CallabilityType.Call
    assert callable(cql.SoftCallability)
    assert cql.ConvertibleZeroCouponBond is not None
    assert hasattr(cql.ConvertibleZeroCouponBond, "setBinomialPricingEngine")
    assert hasattr(cql.ConvertibleFixedCouponBond, "conversionRatio")
    assert hasattr(cql.FixedRateBond, "settlementValue")
    assert ql.BinomialConvertibleEngine is not None
