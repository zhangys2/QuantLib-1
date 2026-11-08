"""Phase-117 tests: NonstandardSwap + NonstandardSwaption from underlying."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase117():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 8)


def _payer_vanilla_swap():
    today = ql.Date(15, ql.Month.May, 2007)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    yts = ql.FlatForward(today, 0.03, ql.Actual365Fixed())
    index = ql.Euribor6M(yts)

    start = calendar.advance(today, 2, ql.TimeUnit.Days)
    maturity = calendar.advance(start, 10, ql.TimeUnit.Years)
    fixed_schedule = ql.Schedule(
        start,
        maturity,
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
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
    return (
        ql.VanillaSwap(
            ql.SwapType.Payer,
            1.0,
            fixed_schedule,
            0.03,
            ql.Thirty360(ql.Thirty360Convention.BondBasis),
            float_schedule,
            index,
            0.0,
            index.day_counter(),
        ),
        yts,
        fixed_schedule,
        float_schedule,
        index,
    )


def test_nonstandard_swap_from_vanilla_matches_npv():
    vanilla, yts, _fixed, _float, _index = _payer_vanilla_swap()
    vanilla.set_pricing_engine(yts)
    vanilla_npv = vanilla.NPV()

    nonstd = ql.NonstandardSwap(vanilla)
    nonstd.set_pricing_engine(yts)
    assert nonstd.NPV() == pytest.approx(vanilla_npv, abs=1.0e-12)
    assert nonstd.type() == ql.SwapType.Payer
    assert len(nonstd.fixed_nominal()) == len(nonstd.fixed_rate())
    assert len(nonstd.floating_nominal()) > 0
    assert all(abs(r - 0.03) < 1.0e-15 for r in nonstd.fixed_rate())
    assert nonstd.spread() == pytest.approx(0.0)
    assert nonstd.gearing() == pytest.approx(1.0)


def test_nonstandard_swap_explicit_constructor():
    vanilla, yts, fixed_schedule, float_schedule, index = _payer_vanilla_swap()
    ref = ql.NonstandardSwap(vanilla)
    n_fixed = len(ref.fixed_nominal())
    n_float = len(ref.floating_nominal())
    nonstd = ql.NonstandardSwap(
        ql.SwapType.Payer,
        [1.0] * n_fixed,
        [1.0] * n_float,
        fixed_schedule,
        [0.03] * n_fixed,
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        float_schedule,
        index,
        1.0,
        0.0,
        index.day_counter(),
    )
    vanilla.set_pricing_engine(yts)
    nonstd.set_pricing_engine(yts)
    assert nonstd.NPV() == pytest.approx(vanilla.NPV(), abs=1.0e-12)


def test_nonstandard_swaption_from_underlying_swap():
    vanilla, yts, fixed_schedule, _float, _index = _payer_vanilla_swap()
    exercise = ql.EuropeanExercise(fixed_schedule[0])
    gsr = ql.Gsr(yts, [], [0.01], 0.01, T=50.0)

    from_swaption = ql.NonstandardSwaption(ql.Swaption(vanilla, exercise))
    from_swaption.set_gaussian1d_pricing_engine(
        gsr, integration_points=64, stddevs=7.0, extrapolate_payoff=True, flat_payoff_extrapolation=False
    )

    nonstd_swap = ql.NonstandardSwap(vanilla)
    from_swap = ql.NonstandardSwaption(nonstd_swap, exercise)
    from_swap.set_gaussian1d_pricing_engine(
        gsr, integration_points=64, stddevs=7.0, extrapolate_payoff=True, flat_payoff_extrapolation=False
    )
    assert from_swap.NPV() == pytest.approx(from_swaption.NPV(), abs=1.0e-12)
    assert from_swap.underlying_swap().type() == ql.SwapType.Payer


def test_compat_phase117_aliases():
    import qlnb.compat as c

    assert c.NonstandardSwap is not None
    assert hasattr(c.NonstandardSwap, "setPricingEngine")
    assert hasattr(c.NonstandardSwaption, "underlyingSwap")
