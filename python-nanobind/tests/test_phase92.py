"""Phase-92 tests: PerpetualFutures (AHJ 2024 analytic goldens)."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase92():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 93)


def _curves(r: float, q: float):
    # Suite uses Date::todaysDate(); formula is time-homogeneous.
    today = ql.Date(24, ql.Month.August, 2026)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    return (
        today,
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, q, dc),
        ql.make_quote_handle(10000.0),
        dc,
    )


def _price(payoff, funding, freq, r, q, k, i_diff):
    _today, dom, foreign, spot, dc = _curves(r, q)
    trade = ql.PerpetualFutures(
        payoff, funding, freq, ql.NullCalendar(), dc
    )
    trade.set_pricing_engine(dom, foreign, spot, [0.0], [k], [i_diff])
    return trade.NPV()


def test_linear_previous_spot_quarterly():
    # PerpetualFuturesTests::testPerpetualFuturesValues — Equation (12).
    s, r, q, k, i_diff, dt = 10000.0, 0.04, 0.02, 0.01, 0.005, 0.25
    expected = (
        s
        * (k - i_diff)
        * math.exp(q * dt)
        / (math.exp(q * dt) - math.exp(r * dt) + k * math.exp(q * dt))
    )
    npv = _price(
        ql.PerpetualFuturesPayoffType.Linear,
        ql.PerpetualFuturesFundingType.FundingWithPreviousSpot,
        ql.Period(3, ql.TimeUnit.Months),
        r,
        q,
        k,
        i_diff,
    )
    assert npv / expected == pytest.approx(1.0, rel=1.0e-6)


def test_linear_current_spot_quarterly():
    s, r, q, k, i_diff, dt = 10000.0, 0.04, 0.02, 0.01, 0.005, 0.25
    expected = (
        s
        * (k - i_diff)
        * math.exp(r * dt)
        / (math.exp(q * dt) - math.exp(r * dt) + k * math.exp(r * dt))
    )
    npv = _price(
        ql.PerpetualFuturesPayoffType.Linear,
        ql.PerpetualFuturesFundingType.FundingWithCurrentSpot,
        ql.Period(3, ql.TimeUnit.Months),
        r,
        q,
        k,
        i_diff,
    )
    assert npv / expected == pytest.approx(1.0, rel=1.0e-6)


def test_inverse_previous_spot_quarterly():
    # Proposition 2.
    s, r, q, k, i_diff, dt = 10000.0, 0.04, 0.02, 0.01, 0.005, 0.25
    expected = (
        s
        * (math.exp(r * dt) - math.exp(q * dt) + k * math.exp(r * dt))
        / (k - i_diff)
        / math.exp(r * dt)
    )
    npv = _price(
        ql.PerpetualFuturesPayoffType.Inverse,
        ql.PerpetualFuturesFundingType.FundingWithPreviousSpot,
        ql.Period(3, ql.TimeUnit.Months),
        r,
        q,
        k,
        i_diff,
    )
    assert npv / expected == pytest.approx(1.0, rel=1.0e-6)


def test_linear_continuous():
    # Proposition 3 — Period(0, Months).
    s, r, q, k, i_diff = 10000.0, 0.04, 0.02, 0.2, 0.005
    expected = s * (k - i_diff) / (q - r + k)
    npv = _price(
        ql.PerpetualFuturesPayoffType.Linear,
        ql.PerpetualFuturesFundingType.FundingWithPreviousSpot,
        ql.Period(0, ql.TimeUnit.Months),
        r,
        q,
        k,
        i_diff,
    )
    assert npv / expected == pytest.approx(1.0, rel=1.0e-6)
    trade = ql.PerpetualFutures(ql.PerpetualFuturesPayoffType.Linear)
    assert trade.is_expired() is False


def test_compat_phase92_aliases():
    import qlnb.compat as cql

    assert cql.PerpetualFutures is not None
    assert hasattr(cql.PerpetualFutures, "setPricingEngine")
    assert hasattr(cql.PerpetualFutures, "Linear")
    assert hasattr(cql.PerpetualFutures, "FundingWithPreviousSpot")
