"""Phase-59 tests: Monte Carlo European Heston engine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase59():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 60)


def test_mc_heston_vs_cached():
    # HestonModelTests::testMcVsCached
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    exercise_date = ql.Date(28, ql.Month.March, 2005)
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.7, dc),
        ql.FlatForward(today, 0.4, dc),
        ql.make_quote_handle(1.05),
        0.3,
        1.16,
        0.2,
        0.8,
        0.8,
        ql.HestonDiscretization.QuadraticExponentialMartingale,
    )
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 1.05),
        ql.EuropeanExercise(exercise_date),
    )
    option.set_mc_heston_pricing_engine(
        process,
        steps_per_year=11,
        required_samples=50000,
        seed=1234,
        antithetic=True,
    )
    npv = option.NPV()
    err = option.error_estimate()
    expected = 0.0632851308977151
    assert abs(npv - expected) < 2.34 * err
    assert err < 7.5e-4


def test_mc_heston_european_option_and_compat():
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.7, dc),
        ql.FlatForward(today, 0.4, dc),
        ql.make_quote_handle(1.05),
        0.3,
        1.16,
        0.2,
        0.8,
        0.8,
    )
    option = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 1.05),
        ql.EuropeanExercise(ql.Date(28, ql.Month.March, 2005)),
    )
    option.set_mc_heston_pricing_engine(
        process, time_steps=20, required_samples=4000, seed=42
    )
    assert option.NPV() > 0.0
    assert option.error_estimate() > 0.0

    import qlnb.compat as cql

    assert hasattr(cql.VanillaOption, "setMcHestonPricingEngine")
    assert hasattr(cql.EuropeanOption, "setMcHestonPricingEngine")
    assert hasattr(cql.VanillaOption, "errorEstimate")
    assert ql.MCEuropeanHestonEngine is not None
