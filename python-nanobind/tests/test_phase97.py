"""Phase-97 tests: EverestOption (suite cached MC NPV)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase97():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 98)


def _bsm(today: ql.Date, q: float, r: float, vol: float):
    # Suite uses a shared dummy underlying of 1.0 for all assets.
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(1.0),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


_CORR = [
    1.00,
    0.50,
    0.30,
    0.10,
    0.50,
    1.00,
    0.20,
    0.40,
    0.30,
    0.20,
    1.00,
    0.60,
    0.10,
    0.40,
    0.60,
    1.00,
]


# EverestOptionTests::testCached — NPV 0.75784944, seed 86421, 1023 samples.
def test_everest_cached_npv():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)

    opt = ql.EverestOption(1.0, 0.0, ql.EuropeanExercise(today + 360))
    processes = [
        _bsm(today, 0.01, 0.05, 0.30),
        _bsm(today, 0.05, 0.05, 0.35),
        _bsm(today, 0.04, 0.05, 0.25),
        _bsm(today, 0.03, 0.05, 0.20),
    ]
    rho = ql.Matrix(4, 4, _CORR)

    opt.set_mc_pricing_engine(
        processes,
        rho,
        steps_per_year=1,
        required_samples=1023,
        seed=86421,
    )

    assert opt.NPV() == pytest.approx(0.75784944, abs=1e-8)
    assert opt.is_expired() is False
    assert opt.error_estimate() > 0.0
    # yield_ is priced after NPV; should be finite.
    assert isinstance(opt.yield_(), float)


def test_everest_absolute_tolerance():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)

    opt = ql.EverestOption(1.0, 0.0, ql.EuropeanExercise(today + 360))
    processes = [
        _bsm(today, 0.01, 0.05, 0.30),
        _bsm(today, 0.05, 0.05, 0.35),
        _bsm(today, 0.04, 0.05, 0.25),
        _bsm(today, 0.03, 0.05, 0.20),
    ]
    rho = ql.Matrix(4, 4, _CORR)

    opt.set_mc_pricing_engine(
        processes,
        rho,
        steps_per_year=1,
        required_samples=1023,
        seed=86421,
    )
    value = opt.NPV()
    minimum_tol = 1.0e-2
    tolerance = min(opt.error_estimate() / 2.0, minimum_tol * value)

    opt.set_mc_pricing_engine(
        processes,
        rho,
        steps_per_year=1,
        required_tolerance=tolerance,
        seed=86421,
    )
    opt.NPV()
    assert opt.error_estimate() <= tolerance


def test_native_everest_snake_case_only():
    # Native qlnb exposes snake_case; camelCase aliases live in qlnb.compat.
    # Compat mutates the shared class, so negative camelCase checks only hold
    # when compat has not been imported yet (full-suite order is not guaranteed).
    import sys

    assert hasattr(ql.EverestOption, "set_mc_pricing_engine")
    assert hasattr(ql.EverestOption, "error_estimate")
    assert hasattr(ql.EverestOption, "is_expired")
    if "qlnb.compat" in sys.modules:
        pytest.skip("qlnb.compat already loaded; camelCase aliases mutate EverestOption")
    assert not hasattr(ql.EverestOption, "setMCPricingEngine")
    assert not hasattr(ql.EverestOption, "errorEstimate")
    assert not hasattr(ql.EverestOption, "isExpired")
    with pytest.raises(AttributeError):
        ql.EverestOption.setMCPricingEngine  # type: ignore[attr-defined]


def test_compat_phase97_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EverestOption, "setMCPricingEngine")
    assert hasattr(cql.EverestOption, "errorEstimate")
    assert hasattr(cql.EverestOption, "isExpired")
    assert getattr(cql.EverestOption, "yield") is cql.EverestOption.yield_
    assert cql.MCEverestEngine is not None
    # Compat aliases call through to the native snake_case methods.
    assert cql.EverestOption.setMCPricingEngine is cql.EverestOption.set_mc_pricing_engine
    assert cql.EverestOption.errorEstimate is cql.EverestOption.error_estimate
    assert cql.EverestOption.isExpired is cql.EverestOption.is_expired
