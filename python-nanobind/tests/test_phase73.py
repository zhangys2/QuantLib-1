"""Phase-73 tests: CDS option (BlackCdsOptionEngine)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase73():
    assert ql.__version__ == "0.74.0"


def _cached_cds_option_market():
    # CdsOptionTests::testCached.
    today = ql.Date(10, ql.Month.December, 2007)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    curve = ql.FlatForward(today, 0.02, ql.Actual360())
    expiry = calendar.advance(today, 9, ql.TimeUnit.Months)
    start = calendar.advance(expiry, 1, ql.TimeUnit.Months)
    maturity = calendar.advance(start, 7, ql.TimeUnit.Years)
    convention = ql.BusinessDayConvention.ModifiedFollowing
    dc = ql.Actual360()
    probability = ql.FlatHazardRate(0, calendar, 0.001, dc)
    schedule = ql.Schedule(
        start,
        maturity,
        ql.Period(ql.Frequency.Quarterly),
        calendar,
        convention,
        convention,
        ql.DateGeneration.Forward,
        False,
    )
    helper = ql.CreditDefaultSwap(
        ql.ProtectionSide.Seller, 1_000_000.0, 0.001, schedule, convention, dc
    )
    helper.set_pricing_engine(probability, 0.4, curve)
    strike = helper.fair_spread()
    return curve, probability, schedule, convention, dc, expiry, strike


def _make_option(side, curve, probability, schedule, convention, dc, expiry, strike):
    swap = ql.CreditDefaultSwap(
        side, 1_000_000.0, strike, schedule, convention, dc
    )
    swap.set_pricing_engine(probability, 0.4, curve)
    option = ql.CdsOption(swap, ql.EuropeanExercise(expiry))
    option.set_pricing_engine(probability, 0.4, curve, 0.20)
    return option


def test_cds_option_seller_cached_npv():
    market = _cached_cds_option_market()
    option = _make_option(ql.ProtectionSide.Seller, *market)
    assert option.NPV() == pytest.approx(270.976348, abs=1.0e-5)
    assert not option.is_expired()
    assert option.risky_annuity() > 0.0
    assert option.atm_rate() == pytest.approx(option.underlying().fair_spread())


def test_cds_option_buyer_cached_npv():
    market = _cached_cds_option_market()
    option = _make_option(ql.ProtectionSide.Buyer, *market)
    assert option.NPV() == pytest.approx(270.976348, abs=1.0e-5)


def test_cds_option_implied_vol_recovers_input():
    curve, probability, schedule, convention, dc, expiry, strike = (
        _cached_cds_option_market()
    )
    option = _make_option(
        ql.ProtectionSide.Seller,
        curve,
        probability,
        schedule,
        convention,
        dc,
        expiry,
        strike,
    )
    price = option.NPV()
    impl = option.implied_volatility(
        price, curve, probability, 0.4, accuracy=1.0e-6
    )
    assert impl == pytest.approx(0.20, abs=1.0e-6)
    # NPV is steep in vol (~2e-5 per 1.6e-8 vol); match C++ IV price accuracy.
    option.set_pricing_engine(probability, 0.4, curve, impl)
    assert option.NPV() == pytest.approx(price, abs=5.0e-5)


def test_compat_phase73_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CdsOption, "setPricingEngine")
    assert hasattr(cql.CdsOption, "impliedVolatility")
    assert hasattr(cql.CdsOption, "riskyAnnuity")
