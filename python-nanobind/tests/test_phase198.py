"""Phase-198 tests: OISRateHelper (bootstrap an overnight index curve from OIS quotes)."""

from __future__ import annotations

import pytest

import qlnb as ql

TENORS = (
    (1, ql.TimeUnit.Years, 0.0300),
    (2, ql.TimeUnit.Years, 0.0320),
    (5, ql.TimeUnit.Years, 0.0350),
    (10, ql.TimeUnit.Years, 0.0370),
)


def _today():
    today = ql.Date(15, ql.Month.May, 2026)
    ql.set_evaluation_date(today)
    return today


def _helpers(index, rates=None, **kwargs):
    rates = rates or [r for _, _, r in TENORS]
    return [
        ql.OISRateHelper(2, ql.Period(n, unit), rate, index, **kwargs)
        for (n, unit, _), rate in zip(TENORS, rates)
    ]


def _bootstrap(today, **kwargs):
    index = ql.Estr()
    return ql.PiecewiseLogLinearDiscountCurve(
        today, _helpers(index, **kwargs), ql.Actual365Fixed()
    )


def _par_rate(curve, tenor):
    # make_ois already applies the 2-day spot lag, matching settlement_days=2 on
    # the helpers, so no extra forward start here.
    index = ql.Estr(curve)
    swap = ql.make_ois(tenor, index, 0.03, ql.Period(0, ql.TimeUnit.Days))
    swap.set_pricing_engine(curve)
    return swap.fair_rate()


def test_oisratehelper_bootstraps_a_curve_that_reprices_the_quotes():
    today = _today()
    curve = _bootstrap(today)
    assert curve.discount(1.0) < 1.0
    for n, unit, rate in TENORS:
        assert _par_rate(curve, ql.Period(n, unit)) == pytest.approx(rate, abs=1.0e-6)


def test_oisratehelper_quote_handle_moves_the_curve():
    today = _today()
    index = ql.Estr()
    quotes = [ql.SimpleQuote(r) for _, _, r in TENORS]
    helpers = [
        ql.OISRateHelper(2, ql.Period(n, unit), ql.QuoteHandle(q), index)
        for (n, unit, _), q in zip(TENORS, quotes)
    ]
    curve = ql.PiecewiseLogLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
    before = curve.discount(5.0)
    for q in quotes:
        q.set_value(q.value() + 0.01)
    after = curve.discount(5.0)
    assert after < before
    # The curve reprices the bumped 5y quote.
    assert _par_rate(curve, ql.Period(5, ql.TimeUnit.Years)) == pytest.approx(
        0.0450, abs=1.0e-6
    )


def test_oisratehelper_float_and_quote_handle_agree():
    today = _today()
    by_float = _bootstrap(today)
    index = ql.Estr()
    helpers = [
        ql.OISRateHelper(2, ql.Period(n, unit), ql.QuoteHandle(ql.SimpleQuote(r)), index)
        for n, unit, r in TENORS
    ]
    by_handle = ql.PiecewiseLogLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
    for t in (0.5, 1.0, 3.0, 7.0, 10.0):
        assert by_handle.discount(t) == pytest.approx(by_float.discount(t), abs=1.0e-14)


def test_oisratehelper_exogenous_discounting_curve_changes_the_projection():
    today = _today()
    single = _bootstrap(today)
    discount = ql.FlatForward(today, 0.01, ql.Actual365Fixed())
    dual = _bootstrap(today, discounting_curve=discount)
    # Projection differs once discounting is taken from a different curve.
    assert abs(dual.discount(10.0) - single.discount(10.0)) > 1.0e-4
    # The bootstrapped curve still reprices the quotes when swaps are discounted
    # off the exogenous curve.
    index = ql.Estr(dual)
    swap = ql.make_ois(
        ql.Period(5, ql.TimeUnit.Years), index, 0.0350, ql.Period(0, ql.TimeUnit.Days)
    )
    swap.set_pricing_engine(discount)
    assert swap.fair_rate() == pytest.approx(0.0350, abs=1.0e-6)


def test_oisratehelper_options_change_the_result():
    today = _today()
    base = _bootstrap(today)
    simple = _bootstrap(today, averaging_method=ql.RateAveraging.Simple)
    lagged = _bootstrap(today, payment_lag=2)
    spread = _bootstrap(today, overnight_spread=0.001)
    for other in (simple, lagged, spread):
        assert abs(other.discount(10.0) - base.discount(10.0)) > 1.0e-7


def test_oisratehelper_rejects_null_index():
    _today()
    with pytest.raises(Exception):
        ql.OISRateHelper(2, ql.Period(1, ql.TimeUnit.Years), 0.03, None)


def test_oisratehelper_in_compat_namespace():
    import qlnb.compat as ql_c

    assert ql_c.OISRateHelper is ql.OISRateHelper


def _dated_helpers(index, today, rates=None, **kwargs):
    calendar = ql.TARGET()
    start = calendar.advance(today, 2, ql.TimeUnit.Days)
    rates = rates or [r for _, _, r in TENORS]
    return [
        ql.DatedOISRateHelper(
            start,
            calendar.advance(start, ql.Period(n, unit), ql.BusinessDayConvention.ModifiedFollowing),
            rate,
            index,
            **kwargs,
        )
        for (n, unit, _), rate in zip(TENORS, rates)
    ]


def test_dated_oisratehelper_matches_the_tenor_helper():
    today = _today()
    by_tenor = _bootstrap(today)
    dated = ql.PiecewiseLogLinearDiscountCurve(
        today, _dated_helpers(ql.Estr(), today), ql.Actual365Fixed()
    )
    for t in (0.5, 1.0, 3.0, 7.0, 10.0):
        assert dated.discount(t) == pytest.approx(by_tenor.discount(t), abs=1.0e-12)
    for n, unit, rate in TENORS:
        assert _par_rate(dated, ql.Period(n, unit)) == pytest.approx(rate, abs=1.0e-6)


def test_dated_oisratehelper_quote_handle_moves_the_curve():
    today = _today()
    quotes = [ql.SimpleQuote(r) for _, _, r in TENORS]
    helpers = _dated_helpers(ql.Estr(), today, rates=[ql.QuoteHandle(q) for q in quotes])
    curve = ql.PiecewiseLogLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
    before = curve.discount(5.0)
    for q in quotes:
        q.set_value(q.value() + 0.01)
    assert curve.discount(5.0) < before


def test_dated_oisratehelper_forward_starting_quote():
    today = _today()
    index = ql.Estr()
    calendar = ql.TARGET()
    spot = calendar.advance(today, 2, ql.TimeUnit.Days)
    forward = calendar.advance(spot, 1, ql.TimeUnit.Years)
    end = calendar.advance(forward, 1, ql.TimeUnit.Years)
    helpers = _helpers(index)[:1] + [ql.DatedOISRateHelper(forward, end, 0.034, index)]
    curve = ql.PiecewiseLogLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
    # A single-period OIS reprices to the simple Act/360 forward rate between its dates.
    dc = ql.Actual365Fixed()
    d_start = curve.discount(dc.year_fraction(today, forward))
    d_end = curve.discount(dc.year_fraction(today, end))
    simple = (d_start / d_end - 1.0) / ql.Actual360().year_fraction(forward, end)
    assert simple == pytest.approx(0.034, abs=1.0e-9)


def test_dated_oisratehelper_rejects_bad_input():
    today = _today()
    index = ql.Estr()
    with pytest.raises(Exception):
        ql.DatedOISRateHelper(today + 365, today, 0.03, index)
    with pytest.raises(Exception):
        ql.DatedOISRateHelper(today, today + 365, 0.03, None)
