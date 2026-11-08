"""Phase-79 tests: Stulz min/max two-asset basket options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase79():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 80)


def _time_to_days(t: float) -> int:
    # Matches test-suite/utilities.hpp timeToDays (lround, 360 days/year).
    return int(round(t * 360))


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _stulz(today, payoff, t, s1, s2, q1, q2, r, v1, v2, rho):
    opt = ql.BasketOption(payoff, ql.EuropeanExercise(today + _time_to_days(t)))
    opt.set_stulz_pricing_engine(
        _bsm(today, s1, q1, r, v1),
        _bsm(today, s2, q2, r, v2),
        rho,
    )
    return opt


def test_stulz_min_call_firth():
    # BasketOptionTests::testEuroTwoValues first min-call row.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = _stulz(
        today,
        ql.MinBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)),
        1.0, 100.0, 100.0, 0.0, 0.0, 0.05, 0.30, 0.30, 0.90,
    )
    assert opt.NPV() == pytest.approx(10.898, abs=1.0e-3)
    assert opt.is_expired() is False


def test_stulz_max_call_firth():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = _stulz(
        today,
        ql.MaxBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)),
        1.0, 100.0, 100.0, 0.0, 0.0, 0.05, 0.30, 0.30, 0.90,
    )
    assert opt.NPV() == pytest.approx(17.565, abs=1.0e-3)


def test_stulz_min_put_firth():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = _stulz(
        today,
        ql.MinBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0)),
        1.0, 100.0, 100.0, 0.0, 0.0, 0.05, 0.30, 0.30, 0.90,
    )
    assert opt.NPV() == pytest.approx(11.369, abs=1.0e-3)


def test_stulz_haug_min_max_call():
    # Haug spreadsheet / p.58 (tol 1e-4).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    mn = _stulz(
        today,
        ql.MinBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 98.0)),
        0.50, 100.0, 105.0, 0.0, 0.0, 0.05, 0.11, 0.16, 0.63,
    )
    mx = _stulz(
        today,
        ql.MaxBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 98.0)),
        0.50, 100.0, 105.0, 0.0, 0.0, 0.05, 0.11, 0.16, 0.63,
    )
    assert mn.NPV() == pytest.approx(4.8177, abs=1.0e-4)
    assert mx.NPV() == pytest.approx(11.6323, abs=1.0e-4)


def test_compat_phase79_aliases():
    import qlnb.compat as cql

    assert cql.MinBasketPayoff is not None
    assert cql.MaxBasketPayoff is not None
    assert hasattr(cql.BasketOption, "setStulzPricingEngine")
    assert cql.StulzEngine is not None
