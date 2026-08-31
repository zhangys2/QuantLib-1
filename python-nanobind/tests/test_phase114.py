"""Phase-114 tests: YoY inflation Cap / Floor / Collar standalone wrappers."""

from __future__ import annotations

import pytest

import qlnb as ql

from test_phase14 import _uk_yoy_market


def test_version_is_phase114():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 5)


def _yoy_schedule(evaluation, calendar, length_years: int):
    end = calendar.advance(evaluation, length_years, ql.TimeUnit.Years)
    return ql.Schedule(
        evaluation,
        end,
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Forward,
        False,
    )


def _yoy_vol(vol_level, calendar, bdc, dc, lag):
    return ql.ConstantYoYOptionletVolatility(
        vol_level, 0, calendar, bdc, dc, lag, ql.Frequency.Annual
    )


def test_yoy_cap_matches_wrapper():
    evaluation, nominal, yoy, lag, calendar, dc, interp, bdc = _uk_yoy_market()
    sched = _yoy_schedule(evaluation, calendar, 5)
    strike = 0.03
    vol = _yoy_vol(0.01, calendar, bdc, dc, lag)

    cap = ql.YoYInflationCap(
        sched, yoy, lag, interp, strike, calendar, dc
    )
    wrapper = ql.YoYInflationCapFloor(
        ql.YoYInflationCapFloorType.Cap,
        sched,
        yoy,
        lag,
        interp,
        strike,
        calendar,
        dc,
    )
    cap.set_pricing_engine(yoy, vol, nominal, model="black")
    wrapper.set_pricing_engine(yoy, vol, nominal, model="black")

    assert cap.type() == ql.YoYInflationCapFloorType.Cap
    assert cap.NPV() == pytest.approx(wrapper.NPV(), abs=1.0e-12)


def test_yoy_floor_matches_wrapper():
    evaluation, nominal, yoy, lag, calendar, dc, interp, bdc = _uk_yoy_market()
    sched = _yoy_schedule(evaluation, calendar, 5)
    strike = 0.025
    vol = _yoy_vol(0.01, calendar, bdc, dc, lag)

    floor = ql.YoYInflationFloor(
        sched, yoy, lag, interp, strike, calendar, dc
    )
    wrapper = ql.YoYInflationCapFloor(
        ql.YoYInflationCapFloorType.Floor,
        sched,
        yoy,
        lag,
        interp,
        strike,
        calendar,
        dc,
    )
    floor.set_pricing_engine(yoy, vol, nominal, model="black")
    wrapper.set_pricing_engine(yoy, vol, nominal, model="black")

    assert floor.type() == ql.YoYInflationCapFloorType.Floor
    assert floor.NPV() == pytest.approx(wrapper.NPV(), abs=1.0e-12)


def test_yoy_collar_matches_wrapper():
    evaluation, nominal, yoy, lag, calendar, dc, interp, bdc = _uk_yoy_market()
    sched = _yoy_schedule(evaluation, calendar, 5)
    cap_strike = 0.03
    floor_strike = 0.025
    vol = _yoy_vol(0.01, calendar, bdc, dc, lag)

    collar = ql.YoYInflationCollar(
        sched,
        yoy,
        lag,
        interp,
        cap_strike,
        floor_strike,
        calendar,
        dc,
    )
    wrapper = ql.YoYInflationCapFloor(
        ql.YoYInflationCapFloorType.Collar,
        sched,
        yoy,
        lag,
        interp,
        cap_strike,
        calendar,
        dc,
        floor_strike=floor_strike,
    )
    collar.set_pricing_engine(yoy, vol, nominal, model="black")
    wrapper.set_pricing_engine(yoy, vol, nominal, model="black")

    assert collar.type() == ql.YoYInflationCapFloorType.Collar
    assert collar.NPV() == pytest.approx(wrapper.NPV(), abs=1.0e-12)


def test_yoy_cap_floor_collar_consistency():
    # InflationCapFloorTests::testConsistency (single scenario).
    evaluation, nominal, yoy, lag, calendar, dc, interp, bdc = _uk_yoy_market()
    sched = _yoy_schedule(evaluation, calendar, 5)
    cap_strike = 0.03
    floor_strike = 0.025
    vol = _yoy_vol(0.01, calendar, bdc, dc, lag)

    cap = ql.YoYInflationCap(
        sched, yoy, lag, interp, cap_strike, calendar, dc
    )
    floor = ql.YoYInflationFloor(
        sched, yoy, lag, interp, floor_strike, calendar, dc
    )
    collar = ql.YoYInflationCollar(
        sched,
        yoy,
        lag,
        interp,
        cap_strike,
        floor_strike,
        calendar,
        dc,
    )
    for instrument in (cap, floor, collar):
        instrument.set_pricing_engine(yoy, vol, nominal, model="black")

    assert (cap.NPV() - floor.NPV()) == pytest.approx(collar.NPV(), abs=1.0e-6)


def test_compat_phase114_aliases():
    import qlnb.compat as c

    assert c.YoYInflationCap is not None
    assert c.YoYInflationFloor is not None
    assert c.YoYInflationCollar is not None
    assert hasattr(c.YoYInflationCap, "setPricingEngine")
