"""Phase-80 tests: variance swap (replicating engine)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase80():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 81)


def _time_to_days(t: float, days_per_year: int = 365) -> int:
    # Matches test-suite/utilities.hpp timeToDays(t, daysPerYear).
    return int(round(t * days_per_year))


# VarianceSwapTests::testReplicatingVarianceSwap — Derman/Kamal/Zou 1999.
_PUTS = [
    (50.0, 0.30),
    (55.0, 0.29),
    (60.0, 0.28),
    (65.0, 0.27),
    (70.0, 0.26),
    (75.0, 0.25),
    (80.0, 0.24),
    (85.0, 0.23),
    (90.0, 0.22),
    (95.0, 0.21),
    (100.0, 0.20),
]
_CALLS = [
    (100.0, 0.20),
    (105.0, 0.19),
    (110.0, 0.18),
    (115.0, 0.17),
    (120.0, 0.16),
    (125.0, 0.15),
    (130.0, 0.14),
    (135.0, 0.13),
]


def test_replicating_variance_swap_derman():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    maturity = today + _time_to_days(0.246575, 365)

    put_strikes = [k for k, _ in _PUTS]
    call_strikes = [k for k, _ in _CALLS]
    # Surface skips the duplicate ATM call (same as the C++ suite).
    strikes = put_strikes + call_strikes[1:]
    vols = [v for _, v in _PUTS] + [v for _, v in _CALLS[1:]]
    vol_ts = ql.BlackVarianceSurface(
        today,
        ql.NullCalendar(),
        [maturity],
        strikes,
        ql.Matrix(len(strikes), 1, vols),
        dc,
    )
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.00, dc),
        ql.FlatForward(today, 0.05, dc),
        vol_ts,
    )
    vs = ql.VarianceSwap(ql.Position.Long, 0.04, 50000.0, today, maturity)
    vs.set_replicating_pricing_engine(process, call_strikes, put_strikes, dk=5.0)
    assert vs.variance() == pytest.approx(0.04189, abs=1.0e-4)
    assert vs.NPV() > 0.0
    assert vs.is_expired() is False
    assert vs.strike() == 0.04
    assert vs.notional() == 50000.0
    assert vs.position() == ql.Position.Long
    assert vs.start_date() == today
    assert vs.maturity_date() == maturity


def test_compat_phase80_aliases():
    import qlnb.compat as cql

    assert cql.VarianceSwap is not None
    assert hasattr(cql.VarianceSwap, "setReplicatingPricingEngine")
    assert hasattr(cql.VarianceSwap, "isExpired")
    assert hasattr(cql.VarianceSwap, "startDate")
    assert hasattr(cql.VarianceSwap, "maturityDate")
    assert cql.ReplicatingVarianceSwapEngine is not None
    assert cql.BlackVarianceSurface is not None
