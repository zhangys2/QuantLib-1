"""Phase-154 tests: Gaussian1dJamshidianSwaptionEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase154():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 25)


def _gsr_european_swaption():
    # GsrTests::testGsrModel — same setup as test_phase116.
    today = ql.Date(15, ql.Month.May, 2007)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    yts = ql.FlatForward(today, 0.03, ql.Actual365Fixed())
    index = ql.Euribor6M(yts)

    start = calendar.advance(today, 5, ql.TimeUnit.Years)
    maturity = calendar.advance(start, 10, ql.TimeUnit.Years)
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
    swap = ql.VanillaSwap(
        ql.SwapType.Payer,
        1.0,
        fixed_schedule,
        0.03,
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        float_schedule,
        index,
        0.0,
        index.day_counter(),
    )
    exercise = ql.EuropeanExercise(start)
    reversion = 0.01
    vol = 0.01
    hw = ql.HullWhite(yts, reversion, vol)
    gsr = ql.Gsr(yts, [], [vol], reversion, T=50.0)
    return swap, exercise, hw, gsr


def test_gsr_jamshidian_matches_hw_jamshidian():
    swap, exercise, hw, gsr = _gsr_european_swaption()
    hw_swaption = ql.Swaption(swap, exercise)
    hw_swaption.set_jamshidian_pricing_engine(hw)
    hw_npv = hw_swaption.NPV()

    gsr_swaption = ql.Swaption(swap, exercise)
    gsr_swaption.set_gaussian1d_jamshidian_pricing_engine(gsr)
    assert gsr_swaption.NPV() == pytest.approx(hw_npv, abs=5.0e-5)


def test_gsr_jamshidian_matches_gaussian1d_numeric():
    swap, exercise, hw, gsr = _gsr_european_swaption()
    hw_swaption = ql.Swaption(swap, exercise)
    hw_swaption.set_jamshidian_pricing_engine(hw)
    hw_npv = hw_swaption.NPV()

    numeric = ql.Swaption(swap, exercise)
    numeric.set_gaussian1d_pricing_engine(
        gsr,
        integration_points=64,
        stddevs=7.0,
        extrapolate_payoff=True,
        flat_payoff_extrapolation=False,
    )
    assert numeric.NPV() == pytest.approx(hw_npv, abs=5.0e-5)


def test_compat_phase154_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.Swaption, "setGaussian1dJamshidianPricingEngine")
    assert cql.Gaussian1dJamshidianSwaptionEngine is not None
