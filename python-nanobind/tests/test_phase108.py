"""Phase-108 tests: Ibor Cap / Floor standalone wrappers."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase108():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 9)


def _cap_floor_market():
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


def test_cap_matches_capfloor_wrapper():
    curve, index, schedule = _cap_floor_market()
    strike = 0.07
    vol = 0.20

    cap = ql.Cap(schedule, index, strike, nominal=100.0, fixing_days=2)
    wrapper = ql.CapFloor(
        ql.CapFloorType.Cap, schedule, index, strike, nominal=100.0, fixing_days=2
    )
    cap.set_pricing_engine(curve, vol, ql.Actual365Fixed())
    wrapper.set_pricing_engine(curve, vol, ql.Actual365Fixed())

    assert cap.type() == ql.CapFloorType.Cap
    assert cap.NPV() == pytest.approx(wrapper.NPV(), abs=1.0e-12)


def test_floor_matches_capfloor_wrapper():
    curve, index, schedule = _cap_floor_market()
    strike = 0.03
    vol = 0.20

    floor = ql.Floor(schedule, index, strike, nominal=100.0, fixing_days=2)
    wrapper = ql.CapFloor(
        ql.CapFloorType.Floor, schedule, index, strike, nominal=100.0, fixing_days=2
    )
    floor.set_pricing_engine(curve, vol, ql.Actual365Fixed())
    wrapper.set_pricing_engine(curve, vol, ql.Actual365Fixed())

    assert floor.type() == ql.CapFloorType.Floor
    assert floor.NPV() == pytest.approx(wrapper.NPV(), abs=1.0e-12)


def test_cap_implied_vol_round_trip():
    # CapFloorTest::testImpliedVolatility (cap leg).
    curve, index, schedule = _cap_floor_market()
    cap = ql.Cap(schedule, index, 0.07, nominal=100.0)
    cap.set_pricing_engine(curve, 0.20, ql.Actual365Fixed())
    price = cap.NPV()
    impl = cap.implied_volatility(
        price, curve, guess=0.10, accuracy=1.0e-8, max_evaluations=100
    )
    assert impl == pytest.approx(0.20, abs=1.0e-8)


def test_compat_phase108_aliases():
    import qlnb.compat as c

    assert c.Cap is not None
    assert c.Floor is not None
    assert hasattr(c.Cap, "setPricingEngine")
    assert hasattr(c.Floor, "impliedVolatility")
