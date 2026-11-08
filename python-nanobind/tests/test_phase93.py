"""Phase-93 tests: MultipleResetsSwap (suite fair rate + legs identity)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase93():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 94)


def _common_vars():
    # MultipleResetsSwapTests::CommonVars — 15 Jan 2024, flat 5%, Euribor3M.
    calendar = ql.TARGET()
    today = calendar.adjust(ql.Date(15, ql.Month.January, 2024))
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.05, ql.Actual365Fixed())
    ibor = ql.Euribor3M(curve)
    ibor.add_fixing(ql.Date(11, ql.Month.January, 2024), 0.05, True)
    return today, curve, ibor


def _make_swap(ibor, fixed_rate=0.06, averaging=None, typ=None, nominal=1.0e6):
    kwargs = {
        "fixed_rate": fixed_rate,
        "settlement_days": 0,
        "nominal": nominal,
    }
    if averaging is not None:
        kwargs["averaging_method"] = averaging
    if typ is not None:
        kwargs["type"] = typ
    return ql.make_multiple_resets_swap(
        ql.Period(2, ql.TimeUnit.Years), ibor, 2, **kwargs
    )


def test_fair_rate_zeros_npv():
    # MultipleResetsSwapTests::testFairRate.
    _today, _curve, ibor = _common_vars()
    swap = _make_swap(ibor, 0.06)
    fair = swap.fair_rate()
    assert fair == pytest.approx(0.05, abs=5.0e-4)
    par = _make_swap(ibor, fair)
    assert par.NPV() == pytest.approx(0.0, abs=1.0e-8)
    assert swap.NPV() == pytest.approx(
        swap.fixed_leg_NPV() + swap.floating_leg_NPV(), abs=1.0e-10
    )
    assert swap.resets_per_coupon() == 2
    assert swap.averaging_method() == ql.RateAveraging.Compound
    assert swap.is_expired() is False


def test_auto_fair_rate_zeros_npv():
    # Omitting fixed_rate triggers MakeMultipleResetsSwap fair-rate lock.
    _today, _curve, ibor = _common_vars()
    auto = ql.make_multiple_resets_swap(
        ql.Period(2, ql.TimeUnit.Years),
        ibor,
        2,
        settlement_days=0,
        nominal=1.0e6,
    )
    assert auto.NPV() == pytest.approx(0.0, abs=1.0e-8)


def test_consistency_with_legs():
    # MultipleResetsSwapTests::testConsistencyWithLeg — both swap types.
    _today, _curve, ibor = _common_vars()
    for typ in (ql.SwapType.Payer, ql.SwapType.Receiver):
        swap = _make_swap(ibor, 0.05, typ=typ)
        assert swap.NPV() == pytest.approx(
            swap.fixed_leg_NPV() + swap.floating_leg_NPV(), abs=1.0e-10
        )


def test_averaging_vs_compounding():
    # MultipleResetsSwapTests::testAveragingVsCompounding.
    _today, _curve, ibor = _common_vars()
    compound = _make_swap(ibor, 0.05, averaging=ql.RateAveraging.Compound)
    simple = _make_swap(ibor, 0.05, averaging=ql.RateAveraging.Simple)
    assert abs(compound.fair_rate() - simple.fair_rate()) > 1.0e-10


def test_compat_phase93_aliases():
    import qlnb.compat as cql

    assert cql.makeMultipleResetsSwap is not None
    assert cql.MultipleResetsSwap is not None
    assert hasattr(cql.MultipleResetsSwap, "fairRate")
    assert hasattr(cql.MultipleResetsSwap, "fixedLegNPV")
    assert hasattr(cql.MultipleResetsSwap, "setPricingEngine")
