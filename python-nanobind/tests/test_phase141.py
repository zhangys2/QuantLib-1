"""Phase-141 tests: BachelierSwaptionEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase141():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 12)


def _cached_swaption_market():
    # Same market as SwaptionTest::testCachedValue / Phase 5 / 70.
    today = ql.Date(13, ql.Month.March, 2002)
    settlement = ql.Date(15, ql.Month.March, 2002)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual365Fixed())
    index = ql.Euribor6M(curve)
    calendar = index.fixing_calendar()
    exercise_date = calendar.advance(settlement, ql.Period(5, ql.TimeUnit.Years))
    start_date = calendar.advance(exercise_date, 2, ql.TimeUnit.Days)
    return curve, index, exercise_date, start_date


def _make_payer_swaption(curve, index, exercise_date, start_date, strike=0.05):
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


def test_bachelier_swaption_implied_vol_round_trip():
    # SwaptionTest Bachelier path (normal vol on ATM-ish strike).
    curve, index, exercise_date, start_date = _cached_swaption_market()
    vol = 0.01
    swaption = _make_payer_swaption(curve, index, exercise_date, start_date)
    swaption.set_bachelier_pricing_engine(curve, vol)
    price = swaption.NPV()
    assert price > 0.0
    impl = swaption.implied_volatility(
        price,
        curve,
        guess=0.005,
        accuracy=1.0e-8,
        max_evaluations=100,
        vol_type=ql.VolatilityType.Normal,
    )
    assert impl == pytest.approx(vol, abs=1.0e-8)
    swaption.set_bachelier_pricing_engine(curve, impl)
    assert swaption.NPV() == pytest.approx(price, abs=1.0e-8)


def test_bachelier_differs_from_black():
    curve, index, exercise_date, start_date = _cached_swaption_market()
    swaption = _make_payer_swaption(
        curve, index, exercise_date, start_date, strike=0.06
    )
    swaption.set_pricing_engine(curve, 0.20)
    black_npv = swaption.NPV()
    swaption.set_bachelier_pricing_engine(curve, 0.01)
    bachelier_npv = swaption.NPV()
    assert black_npv != pytest.approx(bachelier_npv, abs=1.0e-6)


def test_compat_phase141_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.Swaption, "setBachelierPricingEngine")
    assert cql.BachelierSwaptionEngine is not None
