"""Phase-70 tests: Swaption implied term volatility."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase70():
    assert ql.__version__ == "0.71.0"


def _cached_swaption_market():
    # Same market as SwaptionTest::testCachedValue / Phase 5.
    today = ql.Date(13, ql.Month.March, 2002)
    settlement = ql.Date(15, ql.Month.March, 2002)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual365Fixed())
    index = ql.Euribor6M(curve)
    calendar = index.fixing_calendar()
    exercise_date = calendar.advance(settlement, ql.Period(5, ql.TimeUnit.Years))
    start_date = calendar.advance(exercise_date, 2, ql.TimeUnit.Days)
    return curve, index, exercise_date, start_date


def _make_payer_swaption(curve, index, exercise_date, start_date, strike=0.06):
    swap = ql.make_vanilla_swap(
        ql.Period(10, ql.TimeUnit.Years),
        index,
        strike,
        start_date,
        fixed_leg_tenor=ql.Period(1, ql.TimeUnit.Years),
        fixed_day_count=ql.Thirty360(ql.Thirty360Convention.BondBasis),
        type=ql.SwapType.Payer,
        nominal=1.0,
    )
    return ql.Swaption(swap, ql.EuropeanExercise(exercise_date))


def test_swaption_implied_vol_recovers_input():
    # SwaptionTest::testImpliedVolatility (Phase-5 cached 5y×10y payer).
    curve, index, exercise_date, start_date = _cached_swaption_market()
    swaption = _make_payer_swaption(curve, index, exercise_date, start_date)
    swaption.set_pricing_engine(curve, 0.20)
    price = swaption.NPV()
    assert price == pytest.approx(0.036418158579, abs=1.0e-12)
    impl = swaption.implied_volatility(
        price, curve, guess=0.10, accuracy=1.0e-8, max_evaluations=100
    )
    assert impl == pytest.approx(0.20, abs=1.0e-8)
    swaption.set_pricing_engine(curve, impl)
    assert swaption.NPV() == pytest.approx(price, abs=1.0e-8)


def test_swaption_implied_vol_atm_strike_round_trip():
    curve, index, exercise_date, start_date = _cached_swaption_market()
    swaption = _make_payer_swaption(
        curve, index, exercise_date, start_date, strike=0.05
    )
    swaption.set_pricing_engine(curve, 0.25)
    price = swaption.NPV()
    impl = swaption.implied_volatility(
        price, curve, guess=0.10, accuracy=1.0e-8
    )
    swaption.set_pricing_engine(curve, impl)
    assert swaption.NPV() == pytest.approx(price, abs=1.0e-8)


def test_swaption_price_type_spot_default():
    assert ql.SwaptionPriceType.Spot is not None
    assert ql.SwaptionPriceType.Forward is not None
    curve, index, exercise_date, start_date = _cached_swaption_market()
    swaption = _make_payer_swaption(curve, index, exercise_date, start_date)
    swaption.set_pricing_engine(curve, 0.20)
    price = swaption.NPV()
    impl = swaption.implied_volatility(
        price,
        curve,
        guess=0.10,
        accuracy=1.0e-8,
        price_type=ql.SwaptionPriceType.Spot,
    )
    assert impl == pytest.approx(0.20, abs=1.0e-8)


def test_compat_phase70_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.Swaption, "impliedVolatility")
