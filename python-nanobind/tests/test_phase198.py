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


def _third_wednesday(year, month):
    first = ql.Date(1, month, year)
    # Weekday: Sunday = 1 ... Saturday = 7 (QuantLib); Wednesday = 4.
    offset = (int(first.weekday()) - 4) % 7
    return first + ((7 - offset) % 7) + 14


def _add_months(year, month, n):
    index = month.value - 1 + n
    return year + index // 12, ql.Month(index % 12 + 1)


def _futures_end(start, year, month, mode):
    """Contract end date as the helper itself defines it."""
    if mode == "imm":
        # A null end date makes the helper step three IMM (third-Wednesday) dates.
        end_year, end_month = _add_months(year, month, 3)
        return _third_wednesday(end_year, end_month)
    # The length-in-months constructor only uses calendar.advance.
    return ql.TARGET().advance(
        start, 3, ql.TimeUnit.Months, ql.BusinessDayConvention.ModifiedFollowing, True
    )


def _futures_curve(today, convexity=0.0, mode="imm", **kwargs):
    deposit = ql.DepositRateHelper(
        0.0310,
        ql.Period(3, ql.TimeUnit.Months),
        2,
        ql.TARGET(),
        ql.BusinessDayConvention.ModifiedFollowing,
        True,
        ql.Actual360(),
    )
    months = [
        (ql.Month.June, 2026, 96.90),
        (ql.Month.September, 2026, 96.80),
        (ql.Month.December, 2026, 96.70),
        (ql.Month.March, 2027, 96.60),
    ]
    helpers = [deposit]
    for month, year, price in months:
        start = _third_wednesday(year, month)
        if mode == "imm":
            helper = ql.FuturesRateHelper(
                price, start, ql.Date(), ql.Actual360(), convexity, **kwargs
            )
        else:
            helper = ql.FuturesRateHelper(
                price,
                start,
                3,
                ql.TARGET(),
                ql.BusinessDayConvention.ModifiedFollowing,
                True,
                ql.Actual360(),
                convexity,
                **kwargs,
            )
        helpers.append(helper)
    return ql.PiecewiseLogLinearDiscountCurve(today, helpers, ql.Actual365Fixed()), months


def _forward(curve, today, start, end):
    dc = ql.Actual365Fixed()
    d1 = curve.discount(dc.year_fraction(today, start))
    d2 = curve.discount(dc.year_fraction(today, end))
    return (d1 / d2 - 1.0) / ql.Actual360().year_fraction(start, end)


@pytest.mark.parametrize("mode", ["imm", "months"])
def test_futures_ratehelper_reproduces_implied_rates(mode):
    today = _today()
    curve, months = _futures_curve(today, mode=mode)
    for month, year, price in months:
        start = _third_wednesday(year, month)
        forward = _forward(curve, today, start, _futures_end(start, year, month, mode))
        assert forward == pytest.approx((100.0 - price) / 100.0, abs=1.0e-9)


@pytest.mark.parametrize("mode", ["imm", "months"])
def test_futures_ratehelper_convexity_adjustment_lowers_the_forward(mode):
    today = _today()
    curve, months = _futures_curve(today, convexity=0.0005, mode=mode)
    for month, year, price in months:
        start = _third_wednesday(year, month)
        forward = _forward(curve, today, start, _futures_end(start, year, month, mode))
        # impliedQuote = 100 * (1 - (forward + convexity)), so the curve forward
        # is (100 - price) / 100 - convexity.
        assert forward == pytest.approx((100.0 - price) / 100.0 - 0.0005, abs=1.0e-9)


def test_futures_ratehelper_imm_contract_ends_on_the_next_imm_date():
    # 2026-06-17 + 3 months with calendar.advance is 2026-09-17, but the IMM
    # contract ends on 2026-09-16: the two constructors give different curves.
    today = _today()
    start = _third_wednesday(2026, ql.Month.June)
    assert _futures_end(start, 2026, ql.Month.June, "imm") == ql.Date(16, 9, 2026)
    assert _futures_end(start, 2026, ql.Month.June, "months") == ql.Date(17, 9, 2026)
    imm, _ = _futures_curve(today, mode="imm")
    adv, _ = _futures_curve(today, mode="months")
    assert imm.discount(0.4) != pytest.approx(adv.discount(0.4), abs=1.0e-12)


def test_futures_ratehelper_type_validates_the_start_date():
    start = _third_wednesday(2026, ql.Month.June)
    off_imm = start + 1
    end = start + 91
    ql.FuturesRateHelper(96.9, start, end, ql.Actual360(), 0.0, ql.FuturesType.IMM)
    with pytest.raises(Exception):
        ql.FuturesRateHelper(96.9, off_imm, end, ql.Actual360(), 0.0, ql.FuturesType.IMM)
    # Custom accepts any start date; ASX needs an ASX (second-Friday) date.
    ql.FuturesRateHelper(96.9, off_imm, end, ql.Actual360(), 0.0, ql.FuturesType.Custom)
    with pytest.raises(Exception):
        ql.FuturesRateHelper(96.9, start, end, ql.Actual360(), 0.0, ql.FuturesType.ASX)


def test_futures_ratehelper_custom_type_reproduces_implied_rate():
    today = _today()
    start = today + 120
    end = start + 91
    deposit = ql.DepositRateHelper(
        0.0310, ql.Period(3, ql.TimeUnit.Months), 2, ql.TARGET(),
        ql.BusinessDayConvention.ModifiedFollowing, True, ql.Actual360(),
    )
    future = ql.FuturesRateHelper(96.9, start, end, ql.Actual360(), 0.0, ql.FuturesType.Custom)
    curve = ql.PiecewiseLogLinearDiscountCurve(today, [deposit, future], ql.Actual365Fixed())
    assert _forward(curve, today, start, end) == pytest.approx(0.031, abs=1.0e-9)


def test_futures_ratehelper_quote_handles_move_the_curve():
    today = _today()
    start = _third_wednesday(2026, ql.Month.June)
    price = ql.SimpleQuote(96.90)
    adjustment = ql.SimpleQuote(0.0)
    deposit = ql.DepositRateHelper(
        0.0310, ql.Period(3, ql.TimeUnit.Months), 2, ql.TARGET(),
        ql.BusinessDayConvention.ModifiedFollowing, True, ql.Actual360(),
    )
    future = ql.FuturesRateHelper(
        ql.QuoteHandle(price),
        start,
        3,
        ql.TARGET(),
        ql.BusinessDayConvention.ModifiedFollowing,
        True,
        ql.Actual360(),
        ql.QuoteHandle(adjustment),
    )
    curve = ql.PiecewiseLogLinearDiscountCurve(today, [deposit, future], ql.Actual365Fixed())
    end = _futures_end(start, 2026, ql.Month.June, "months")
    base = _forward(curve, today, start, end)
    assert base == pytest.approx(0.031, abs=1.0e-9)
    price.set_value(96.40)
    assert _forward(curve, today, start, end) == pytest.approx(0.036, abs=1.0e-9)
    adjustment.set_value(0.001)
    assert _forward(curve, today, start, end) == pytest.approx(0.035, abs=1.0e-9)


def test_futures_ratehelper_end_date_and_index_overloads_agree():
    today = _today()
    start = _third_wednesday(2026, ql.Month.June)
    calendar = ql.TARGET()
    end = calendar.advance(start, 3, ql.TimeUnit.Months, ql.BusinessDayConvention.ModifiedFollowing, True)
    deposit = ql.DepositRateHelper(
        0.0310, ql.Period(3, ql.TimeUnit.Months), 2, calendar,
        ql.BusinessDayConvention.ModifiedFollowing, True, ql.Actual360(),
    )
    variants = [
        ql.FuturesRateHelper(96.9, start, end, ql.Actual360()),
        ql.FuturesRateHelper(96.9, start, ql.Euribor3M()),
        ql.FuturesRateHelper(
            96.9, start, 3, calendar, ql.BusinessDayConvention.ModifiedFollowing, True,
            ql.Actual360(), 0.0, ql.FuturesType.IMM,
        ),
    ]
    curves = [
        ql.PiecewiseLogLinearDiscountCurve(today, [deposit, h], ql.Actual365Fixed())
        for h in variants
    ]
    for curve in curves[1:]:
        assert curve.discount(0.3) == pytest.approx(curves[0].discount(0.3), abs=1.0e-12)


def test_futures_ratehelper_rejects_null_index():
    today = _today()
    with pytest.raises(Exception):
        ql.FuturesRateHelper(96.9, _third_wednesday(2026, ql.Month.June), None)
