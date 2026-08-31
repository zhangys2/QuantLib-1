"""Phase-156 tests: TreeCapFloorEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase156():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 27)


def _cap_market(years: int = 5):
    today = ql.Date(14, ql.Month.March, 2002)
    settlement = ql.Date(18, ql.Month.March, 2002)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(settlement, 0.05, ql.Actual360())
    index = ql.Euribor6M(curve)
    calendar = index.fixing_calendar()
    convention = ql.BusinessDayConvention.ModifiedFollowing
    start = curve.reference_date()
    end = calendar.advance(start, years, ql.TimeUnit.Years, convention)
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
    hw = ql.HullWhite(curve, 0.01, 0.01)
    return curve, index, schedule, hw


@pytest.mark.parametrize("strike", (0.04, 0.05, 0.06))
def test_tree_cap_matches_analytic(strike: float):
    curve, index, schedule, hw = _cap_market(5)
    cap = ql.Cap(schedule, index, strike, nominal=100.0, fixing_days=2)
    cap.set_analytic_cap_floor_pricing_engine(hw, discount_curve=curve)
    analytic = cap.NPV()
    cap.set_tree_pricing_engine(hw, time_steps=200, discount_curve=curve)
    assert cap.NPV() == pytest.approx(analytic, abs=0.05)


def test_tree_floor_matches_analytic():
    curve, index, schedule, hw = _cap_market(5)
    floor = ql.Floor(schedule, index, 0.05, nominal=100.0, fixing_days=2)
    floor.set_analytic_cap_floor_pricing_engine(hw, discount_curve=curve)
    analytic = floor.NPV()
    floor.set_tree_pricing_engine(hw, time_steps=200, discount_curve=curve)
    assert floor.NPV() == pytest.approx(analytic, abs=0.05)


def test_compat_phase156_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CapFloor, "setTreePricingEngine")
    assert hasattr(cql.Cap, "setTreePricingEngine")
    assert cql.TreeCapFloorEngine is not None
