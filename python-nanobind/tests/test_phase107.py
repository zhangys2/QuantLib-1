"""Phase-107 tests: Ibor Collar."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase107():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 8)


def _cap_floor_market(length_years: int = 5):
    today = ql.Date(14, ql.Month.March, 2002)
    settlement = ql.Date(18, ql.Month.March, 2002)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual360())
    index = ql.Euribor6M(curve)
    calendar = index.fixing_calendar()
    convention = ql.BusinessDayConvention.ModifiedFollowing
    start = curve.reference_date()
    end = calendar.advance(start, length_years, ql.TimeUnit.Years, convention)
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


def test_collar_consistency_with_cap_floor():
    # CapFloorTest::testConsistency (cap - floor == collar)
    curve, index, schedule = _cap_floor_market(5)
    cap_rate = 0.05
    floor_rate = 0.03
    vol = 0.20

    cap = ql.CapFloor(
        ql.CapFloorType.Cap, schedule, index, cap_rate, nominal=100.0, fixing_days=2
    )
    floor = ql.CapFloor(
        ql.CapFloorType.Floor, schedule, index, floor_rate, nominal=100.0, fixing_days=2
    )
    collar = ql.Collar(
        schedule, index, cap_rate, floor_rate, nominal=100.0, fixing_days=2
    )

    cap.set_pricing_engine(curve, vol, ql.Actual365Fixed())
    floor.set_pricing_engine(curve, vol, ql.Actual365Fixed())
    collar.set_pricing_engine(curve, vol, ql.Actual365Fixed())

    assert collar.type() == ql.CapFloorType.Collar
    assert cap.NPV() - floor.NPV() == pytest.approx(collar.NPV(), abs=1.0e-10)


def test_collar_implied_vol_round_trip():
    curve, index, schedule = _cap_floor_market(10)
    collar = ql.Collar(schedule, index, 0.04, 0.03, nominal=100.0)
    collar.set_pricing_engine(curve, 0.20, ql.Actual365Fixed())
    price = collar.NPV()
    impl = collar.implied_volatility(
        price, curve, guess=0.10, accuracy=1.0e-8, max_evaluations=100
    )
    assert impl == pytest.approx(0.20, abs=1.0e-8)
    collar.set_pricing_engine(curve, impl, ql.Actual365Fixed())
    assert collar.NPV() == pytest.approx(price, abs=1.0e-8)


def test_compat_phase107_aliases():
    import qlnb.compat as c

    assert c.Collar is not None
    assert hasattr(c.Collar, "setPricingEngine")
    assert hasattr(c.Collar, "impliedVolatility")
