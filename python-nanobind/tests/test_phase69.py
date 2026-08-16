"""Phase-69 tests: CapFloor implied term volatility."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_at_least_phase69():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 70)


def _cached_cap_floor_market():
    # Same market as CapFloorTest::testCachedValue / Phase 4.
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


def test_cap_implied_vol_recovers_input():
    # CapFloorTest::testImpliedVolatility (single cached point).
    curve, index, schedule = _cached_cap_floor_market()
    cap = ql.CapFloor(
        ql.CapFloorType.Cap, schedule, index, 0.07, nominal=100.0, fixing_days=2
    )
    cap.set_pricing_engine(curve, 0.20, ql.Actual365Fixed())
    price = cap.NPV()
    impl = cap.implied_volatility(
        price, curve, guess=0.10, accuracy=1.0e-8, max_evaluations=100
    )
    assert impl == pytest.approx(0.20, abs=1.0e-8)
    cap.set_pricing_engine(curve, impl, ql.Actual365Fixed())
    assert cap.NPV() == pytest.approx(price, abs=1.0e-8)


def test_floor_implied_vol_recovers_input():
    curve, index, schedule = _cached_cap_floor_market()
    floor = ql.CapFloor(
        ql.CapFloorType.Floor, schedule, index, 0.03, nominal=100.0, fixing_days=2
    )
    floor.set_pricing_engine(curve, 0.20, ql.Actual365Fixed())
    price = floor.NPV()
    impl = floor.implied_volatility(
        price, curve, guess=0.10, accuracy=1.0e-8, max_evaluations=100
    )
    assert impl == pytest.approx(0.20, abs=1.0e-8)
    floor.set_pricing_engine(curve, impl, ql.Actual365Fixed())
    assert floor.NPV() == pytest.approx(price, abs=1.0e-8)


def test_make_cap_implied_vol_round_trip():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual365Fixed())
    index = ql.Euribor6M(curve)
    cap = ql.make_cap(ql.Period(5, ql.TimeUnit.Years), index, 0.05, nominal=100.0)
    cap.set_pricing_engine(curve, 0.25, ql.Actual365Fixed())
    price = cap.NPV()
    impl = cap.implied_volatility(price, curve, guess=0.10, accuracy=1.0e-8)
    cap.set_pricing_engine(curve, impl, ql.Actual365Fixed())
    assert cap.NPV() == pytest.approx(price, abs=1.0e-8)


def test_compat_phase69_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CapFloor, "impliedVolatility")
