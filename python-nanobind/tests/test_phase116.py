"""Phase-116 tests: NonstandardSwaption + Gaussian1d nonstandard engine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase116():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 7)


def _gsr_european_swaption():
    # Mirrors test_phase8 gaussian1d vs Jamshidian setup (GsrTests::testGsrModel).
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


def test_nonstandard_swaption_matches_jamshidian():
    # GsrTests::testGsrModel — Jamshidian HW vs Gaussian1dNonstandardSwaptionEngine.
    swap, exercise, hw, gsr = _gsr_european_swaption()
    jam = ql.Swaption(swap, exercise)
    jam.set_jamshidian_pricing_engine(hw)
    hw_npv = jam.NPV()

    std = ql.Swaption(swap, exercise)
    nonstd = ql.NonstandardSwaption(std)
    nonstd.set_gaussian1d_pricing_engine(
        gsr, integration_points=64, stddevs=7.0, extrapolate_payoff=True, flat_payoff_extrapolation=False
    )
    assert nonstd.NPV() == pytest.approx(hw_npv, abs=5.0e-5)
    assert nonstd.type() == ql.SwapType.Payer
    assert nonstd.is_expired() is False


def test_nonstandard_matches_standard_gaussian1d():
    swap, exercise, _hw, gsr = _gsr_european_swaption()
    g1d = ql.Swaption(swap, exercise)
    g1d.set_gaussian1d_pricing_engine(
        gsr, integration_points=64, stddevs=7.0, extrapolate_payoff=True, flat_payoff_extrapolation=False
    )
    std = ql.Swaption(swap, exercise)
    nonstd = ql.NonstandardSwaption(std)
    nonstd.set_gaussian1d_pricing_engine(
        gsr, integration_points=64, stddevs=7.0, extrapolate_payoff=True, flat_payoff_extrapolation=False
    )
    assert nonstd.NPV() == pytest.approx(g1d.NPV(), abs=1.0e-12)


def test_compat_phase116_aliases():
    import qlnb.compat as c

    assert c.NonstandardSwaption is not None
    assert hasattr(c.NonstandardSwaption, "setGaussian1dPricingEngine")
