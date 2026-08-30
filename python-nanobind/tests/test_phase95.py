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


# HimalayaOptionTests::testCached — NPV 5.93632056, seed 86421, 1023 samples.
def test_himalaya_cached_npv():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)

    fixing_dates = [today + i * 90 for i in range(5)]
    opt = ql.HimalayaOption(fixing_dates, 101.0)

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


def test_compat_phase95_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.HimalayaOption, "setMCPricingEngine")
    assert hasattr(cql.HimalayaOption, "errorEstimate")
    assert hasattr(cql.HimalayaOption, "isExpired")
    assert cql.MCHimalayaEngine is not None
