"""Phase-81 tests: MC variance swap + BlackVarianceCurve."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase81():
    assert ql.__version__ == "0.82.0"


def _time_to_days(t: float, days_per_year: int = 365) -> int:
    # Matches test-suite/utilities.hpp timeToDays(t, daysPerYear).
    return int(round(t * days_per_year))


# VarianceSwapTests::testMCVarianceSwap — Derman/Kamal/Zou 1999.
# Fair variance is v*v (0.20**2 = 0.04) for any 0 <= t1 < t, 0 <= v1 < v.
def test_mc_variance_swap_derman():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    interm = today + _time_to_days(0.1, 365)
    maturity = today + _time_to_days(0.246575, 365)
    vol_ts = ql.BlackVarianceCurve(
        today, [interm, maturity], [0.10, 0.20], dc, True
    )
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.00, dc),
        ql.FlatForward(today, 0.05, dc),
        vol_ts,
    )
    vs = ql.VarianceSwap(ql.Position.Long, 0.04, 50000.0, today, maturity)
    vs.set_mc_pricing_engine(
        process,
        steps_per_year=250,
        required_samples=1023,
        seed=42,
        antithetic=False,
        brownian_bridge=False,
    )
    assert vs.variance() == pytest.approx(0.04, abs=3.0e-4)
    assert vs.is_expired() is False
    assert vs.strike() == 0.04
    assert vs.notional() == 50000.0
    assert vs.maturity_date() == maturity


def test_compat_phase81_aliases():
    import qlnb.compat as cql

    assert cql.VarianceSwap is not None
    assert hasattr(cql.VarianceSwap, "setMcPricingEngine")
    assert cql.MCVarianceSwapEngine is not None
    assert cql.BlackVarianceCurve is not None
