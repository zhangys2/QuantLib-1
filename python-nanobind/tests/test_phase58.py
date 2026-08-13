"""Phase-58 tests: floating convertible bonds + Euribor1Y."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase58():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 59)


def _convertible_market():
    # Same pinned market as Phase 57 / ConvertibleBondTests::CommonVars.
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
    return today, calendar, dc, issue, maturity, process, credit


def test_otm_floating_convertible_matches_vanilla():
    # ConvertibleBondTests::testBond floating section — deeply OTM ≈ plain FRN.
    today, calendar, dc, issue, maturity, process, credit = _convertible_market()
    discount = ql.FlatForward(today, 0.055, dc)
    index = ql.Euribor1Y(discount)
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
    conversion_ratio = 1.0e-16
    eu = ql.ConvertibleFloatingRateBond(
        ql.EuropeanExercise(maturity),
        conversion_ratio,
        [],
        issue,
        3,
        index,
        2,
        [],
        dc,
        schedule,
        100.0,
    )
    am = ql.ConvertibleFloatingRateBond(
        ql.AmericanExercise(issue, maturity),
        conversion_ratio,
        [],
        issue,
        3,
        index,
        2,
        [],
        dc,
        schedule,
        100.0,
    )
    eu.set_binomial_pricing_engine(process, 401, credit)
    am.set_binomial_pricing_engine(process, 401, 0.005)
    vanilla = ql.FloatingRateBond(
        3,
        100.0,
        schedule,
        index,
        dc,
        ql.BusinessDayConvention.Following,
        2,
        [1.0],
        [],
        [],
        [],
        False,
        100.0,
        issue,
    )
    vanilla.set_pricing_engine(discount)
    expected = vanilla.settlement_value()
    assert eu.NPV() == pytest.approx(expected, abs=0.04)
    assert am.NPV() == pytest.approx(expected, abs=0.04)
    assert eu.conversion_ratio() == conversion_ratio


def test_euribor1y_and_compat():
    import qlnb.compat as cql

    today = ql.Date(3, ql.Month.June, 2004)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.03, ql.Actual360())
    idx = ql.Euribor1Y(curve)
    assert "Euribor" in idx.name()
    assert idx.tenor() == ql.Period(1, ql.TimeUnit.Years)
    assert hasattr(cql.ConvertibleFloatingRateBond, "setBinomialPricingEngine")
    assert hasattr(cql.ConvertibleFloatingRateBond, "conversionRatio")
    assert hasattr(cql.FloatingRateBond, "settlementValue")
    assert ql.Euribor1Y is not None
