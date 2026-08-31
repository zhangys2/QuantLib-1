"""Phase-155 tests: Gaussian1dCapFloorEngine + AnalyticCapFloorEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase155():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 26)


def _cap_market():
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
    reversion = 0.01
    vol = 0.01
    hw = ql.HullWhite(curve, reversion, vol)
    gsr = ql.Gsr(curve, [], [vol], reversion, T=50.0)
    return curve, index, schedule, hw, gsr


@pytest.mark.parametrize("strike", (0.03, 0.05, 0.07))
def test_gsr_cap_matches_hw_analytic(strike: float):
    curve, index, schedule, hw, gsr = _cap_market()
    cap = ql.Cap(schedule, index, strike, nominal=100.0, fixing_days=2)
    cap.set_gaussian1d_pricing_engine(gsr, discount_curve=curve)
    gsr_npv = cap.NPV()
    cap.set_analytic_cap_floor_pricing_engine(hw, discount_curve=curve)
    assert gsr_npv == pytest.approx(cap.NPV(), abs=0.03)


def test_capfloor_wrapper_matches_cap():
    curve, index, schedule, hw, gsr = _cap_market()
    strike = 0.05
    cap = ql.Cap(schedule, index, strike, nominal=100.0, fixing_days=2)
    wrapper = ql.CapFloor(
        ql.CapFloorType.Cap, schedule, index, strike, nominal=100.0, fixing_days=2
    )
    cap.set_gaussian1d_pricing_engine(gsr, discount_curve=curve)
    wrapper.set_gaussian1d_pricing_engine(gsr, discount_curve=curve)
    assert cap.NPV() == pytest.approx(wrapper.NPV(), abs=1.0e-12)


def test_compat_phase155_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.CapFloor, "setGaussian1dPricingEngine")
    assert hasattr(cql.Cap, "setAnalyticCapFloorPricingEngine")
    assert cql.Gaussian1dCapFloorEngine is not None
    assert cql.AnalyticCapFloorEngine is not None
