"""Phase-95 tests: HimalayaOption (suite cached MC NPV)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase95():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 96)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _suite_market(today: ql.Date):
    processes = [
        _bsm(today, 100.0, 0.01, 0.05, 0.30),
        _bsm(today, 110.0, 0.05, 0.05, 0.35),
        _bsm(today, 90.0, 0.04, 0.05, 0.25),
        _bsm(today, 105.0, 0.03, 0.05, 0.20),
    ]
    rho = ql.Matrix(
        4,
        4,
        [
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
        ],
    )
    return processes, rho


# HimalayaOptionTests::testCached — NPV 5.93632056, seed 86421, 1023 samples.
def test_himalaya_cached_npv():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)

    fixing_dates = [today + i * 90 for i in range(5)]
    opt = ql.HimalayaOption(fixing_dates, 101.0)
    processes, rho = _suite_market(today)

    opt.set_mc_pricing_engine(
        processes,
        rho,
        required_samples=1023,
        seed=86421,
    )

    assert opt.NPV() == pytest.approx(5.93632056, abs=1e-8)
    assert opt.is_expired() is False
    assert opt.error_estimate() > 0.0


def test_himalaya_absolute_tolerance():
    # Suite second leg: tighten MC until errorEstimate <= tolerance.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)

    fixing_dates = [today + i * 90 for i in range(5)]
    opt = ql.HimalayaOption(fixing_dates, 101.0)
    processes, rho = _suite_market(today)

    opt.set_mc_pricing_engine(
        processes,
        rho,
        required_samples=1023,
        seed=86421,
    )
    value = opt.NPV()
    minimum_tol = 1.0e-2
    tolerance = min(opt.error_estimate() / 2.0, minimum_tol * value)

    opt.set_mc_pricing_engine(
        processes,
        rho,
        required_tolerance=tolerance,
        seed=86421,
    )
    opt.NPV()
    assert opt.error_estimate() <= tolerance


def test_himalaya_empty_fixing_dates_raises():
    # Binding guards before HimalayaOption(fixingDates.back()).
    with pytest.raises(RuntimeError, match="no fixing dates given"):
        ql.HimalayaOption([], 101.0)


def test_himalaya_samples_and_tolerance_mutually_exclusive():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = ql.HimalayaOption([today + 90], 101.0)
    processes, rho = _suite_market(today)
    with pytest.raises(
        RuntimeError,
        match="set only one of required_samples or required_tolerance",
    ):
        opt.set_mc_pricing_engine(
            processes,
            rho,
            required_samples=1023,
            required_tolerance=1.0e-2,
            seed=86421,
        )


def test_himalaya_empty_processes_raises():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = ql.HimalayaOption([today + 90], 101.0)
    with pytest.raises(RuntimeError, match="no processes given"):
        opt.set_mc_pricing_engine([], ql.Matrix(0, 0, []), seed=86421)


def test_compat_phase95_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.HimalayaOption, "setMCPricingEngine")
    assert hasattr(cql.HimalayaOption, "errorEstimate")
    assert hasattr(cql.HimalayaOption, "isExpired")
    assert cql.MCHimalayaEngine is not None
    # SWIG-style name kept for discovery; not an engine factory (no fixing_dates).
    doc = ql.MCHimalayaEngine.__doc__ or ""
    assert "Documentation alias" in doc
    assert "set_mc_pricing_engine" in doc
    assert "Factory" not in doc
    today = ql.Date(15, ql.Month.May, 1998)
    processes, rho = _suite_market(today)
    # Returns a process token only; attach via HimalayaOption.set_mc_pricing_engine.
    returned = ql.MCHimalayaEngine(processes, rho)
    assert isinstance(returned, ql.BlackScholesMertonProcess)
    with pytest.raises(RuntimeError, match="no processes given"):
        ql.MCHimalayaEngine([], ql.Matrix(0, 0, []))
