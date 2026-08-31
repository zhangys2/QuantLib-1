"""Phase-140 tests: BachelierCapFloorEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase140():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 11)


def _cached_cap_floor_market():
    # Same market as CapFloorTest::testCachedValue / Phase 4 / 69.
    today = ql.Date(14, ql.Month.March, 2002)
    settlement = ql.Date(18, ql.Month.March, 2002)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual360())
    index = ql.Euribor6M(curve)
    calendar = index.fixing_calendar()
    convention = ql.BusinessDayConvention.ModifiedFollowing
    start = curve.reference_date()
    end = calendar.advance(start, 20, ql.TimeUnit.Years, convention)
    schedule = ql.Schedule(
        start,
        end,
        ql.Period(ql.Frequency.Semiannual),
        calendar,
        convention,
        convention,
        ql.DateGeneration.Forward,
        False,
    )
    return curve, index, schedule


def test_bachelier_cap_implied_vol_round_trip():
    # CapFloorTest Bachelier path (normal vol 0.01, ATM strike 0.05).
    curve, index, schedule = _cached_cap_floor_market()
    vol = 0.01
    cap = ql.CapFloor(
        ql.CapFloorType.Cap, schedule, index, 0.05, nominal=100.0, fixing_days=2
    )
    cap.set_bachelier_pricing_engine(curve, vol, ql.Actual365Fixed())
    price = cap.NPV()
    assert price > 0.0
    impl = cap.implied_volatility(
        price,
        curve,
        guess=0.005,
        accuracy=1.0e-8,
        max_evaluations=100,
        vol_type=ql.VolatilityType.Normal,
    )
    assert impl == pytest.approx(vol, abs=1.0e-8)
    cap.set_bachelier_pricing_engine(curve, impl, ql.Actual365Fixed())
    assert cap.NPV() == pytest.approx(price, abs=1.0e-8)


def test_bachelier_floor_implied_vol_round_trip():
    curve, index, schedule = _cached_cap_floor_market()
    vol = 0.01
    floor = ql.Floor(schedule, index, 0.05, nominal=100.0, fixing_days=2)
    floor.set_bachelier_pricing_engine(curve, vol, ql.Actual365Fixed())
    price = floor.NPV()
    assert price > 0.0
    impl = floor.implied_volatility(
        price,
        curve,
        guess=0.005,
        accuracy=1.0e-8,
        vol_type=ql.VolatilityType.Normal,
    )
    assert impl == pytest.approx(vol, abs=1.0e-8)


def test_bachelier_collar_parity():
    # Cap - Floor ≈ Collar under the same Bachelier engine.
    curve, index, schedule = _cached_cap_floor_market()
    vol = 0.01
    cap = ql.Cap(schedule, index, 0.06, nominal=100.0, fixing_days=2)
    floor = ql.Floor(schedule, index, 0.04, nominal=100.0, fixing_days=2)
    collar = ql.Collar(schedule, index, 0.06, 0.04, nominal=100.0, fixing_days=2)
    for inst in (cap, floor, collar):
        inst.set_bachelier_pricing_engine(curve, vol, ql.Actual365Fixed())
    assert cap.NPV() - floor.NPV() == pytest.approx(collar.NPV(), abs=1.0e-10)


def test_compat_phase140_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CapFloor, "setBachelierPricingEngine")
    assert hasattr(cql.Cap, "setBachelierPricingEngine")
    assert hasattr(cql.Floor, "setBachelierPricingEngine")
    assert hasattr(cql.Collar, "setBachelierPricingEngine")
    assert cql.BachelierCapFloorEngine is not None
