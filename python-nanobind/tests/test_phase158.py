"""Phase-158 tests: G2 model and G2 swaption engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase158():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 29)


def _g2_swaption_market():
    today = ql.Date(15, ql.Month.September, 2016)
    ql.set_evaluation_date(today)
    settlement = ql.Date(19, ql.Month.September, 2016)
    curve = ql.FlatForward(settlement, 0.04875825, ql.Actual365Fixed())
    index = ql.Euribor6M(curve)
    calendar = index.fixing_calendar()
    fixed_dc = ql.Thirty360(ql.Thirty360Convention.BondBasis)
    start = calendar.advance(settlement, 1, ql.TimeUnit.Years)
    maturity = calendar.advance(start, 5, ql.TimeUnit.Years)
    fixed_schedule = ql.Schedule(
        start,
        maturity,
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Forward,
        False,
    )
    float_schedule = ql.Schedule(
        start,
        maturity,
        ql.Period(ql.Frequency.Semiannual),
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.DateGeneration.Forward,
        False,
    )
    probe = ql.VanillaSwap(
        ql.SwapType.Payer,
        1000.0,
        fixed_schedule,
        0.0,
        fixed_dc,
        float_schedule,
        index,
        0.0,
        index.day_counter(),
    )
    probe.set_pricing_engine(curve)
    atm_rate = probe.fair_rate()
    return curve, fixed_schedule, float_schedule, fixed_dc, index, atm_rate


def _bermudan_swaption(fixed_rate: float):
    curve, fixed_schedule, float_schedule, fixed_dc, index, _ = _g2_swaption_market()
    swap = ql.VanillaSwap(
        ql.SwapType.Payer,
        1000.0,
        fixed_schedule,
        fixed_rate,
        fixed_dc,
        float_schedule,
        index,
        0.0,
        index.day_counter(),
    )
    exercise_dates = list(fixed_schedule.dates())[:-1]
    return ql.Swaption(swap, ql.BermudanExercise(exercise_dates)), curve


@pytest.mark.parametrize(
    ("scale", "expected_fdm", "expected_tree"),
    [
        (0.50, 103.227, 103.248),
        (0.75, 54.6502, 54.6726),
        (1.00, 20.0469, 20.1685),
        (1.25, 5.26924, 5.44118),
        (1.50, 1.07093, 1.12737),
    ],
)
def test_g2_cached_bermudan_values(scale: float, expected_fdm: float, expected_tree: float):
    # Golden values from test-suite/bermudanswaption.cpp::testCachedG2Values (at-par).
    _, _, _, _, _, atm = _g2_swaption_market()
    swaption, curve = _bermudan_swaption(scale * atm)
    g2 = ql.G2(curve, 0.1, 0.01, 0.2, 0.013, -0.5)

    swaption.set_fd_g2_pricing_engine(
        g2, t_grid=50, x_grid=75, y_grid=75, inv_eps=1e-3
    )
    assert swaption.NPV() == pytest.approx(expected_fdm, abs=0.005)

    swaption.set_g2_tree_pricing_engine(g2, time_steps=50)
    assert swaption.NPV() == pytest.approx(expected_tree, abs=0.005)


def test_g2_european_analytic_near_fd():
    curve, fixed_schedule, float_schedule, fixed_dc, index, atm = _g2_swaption_market()
    swap = ql.VanillaSwap(
        ql.SwapType.Payer,
        1000.0,
        fixed_schedule,
        atm,
        fixed_dc,
        float_schedule,
        index,
        0.0,
        index.day_counter(),
    )
    exercise_date = list(fixed_schedule.dates())[:-1][0]
    european = ql.Swaption(swap, ql.EuropeanExercise(exercise_date))
    g2 = ql.G2(curve, 0.1, 0.01, 0.2, 0.013, -0.5)

    european.set_g2_pricing_engine(g2, range=7.0, intervals=64)
    analytic = european.NPV()

    european.set_fd_g2_pricing_engine(
        g2, t_grid=50, x_grid=75, y_grid=75, inv_eps=1e-3
    )
    fdm = european.NPV()
    assert analytic == pytest.approx(fdm, rel=0.02)


def test_compat_phase158_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.Swaption, "setG2PricingEngine")
    assert hasattr(cql.Swaption, "setFdG2PricingEngine")
    assert hasattr(cql.Swaption, "setG2TreePricingEngine")
    assert cql.G2SwaptionEngine is not None
    assert cql.FdG2SwaptionEngine is not None
