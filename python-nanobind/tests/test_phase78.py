"""Phase-78 tests: Kirk two-asset spread basket options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase78():
    assert ql.__version__ == "0.79.0"


def _time_to_days(t: float) -> int:
    # Matches test-suite/utilities.hpp timeToDays (lround, 360 days/year).
    return int(round(t * 360))


def _futures_bsm(today: ql.Date, spot: float, r: float, vol: float):
    # BlackProcess uses dividendTS = riskFreeTS (cost of carry 0).
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# BasketOptionTests::testEuroTwoValues — Haug pp.59-60 Kirk futures spread.
_HAUG_KIRK = [
    # t, v1, v2, rho, npv
    (0.1, 0.20, 0.20, -0.50, 4.7530),
    (0.1, 0.20, 0.20, 0.00, 3.7970),
    (0.1, 0.20, 0.20, 0.50, 2.5537),
    (0.5, 0.20, 0.20, -0.50, 10.7517),
]


@pytest.mark.parametrize("t,v1,v2,rho,npv", _HAUG_KIRK)
def test_kirk_spread_haug(t, v1, v2, rho, npv):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    opt = ql.BasketOption(
        ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 3.0)),
        ql.EuropeanExercise(today + _time_to_days(t)),
    )
    opt.set_kirk_pricing_engine(
        _futures_bsm(today, 122.0, 0.10, v1),
        _futures_bsm(today, 120.0, 0.10, v2),
        rho,
    )
    assert opt.NPV() == pytest.approx(npv, abs=1.0e-3)
    assert opt.is_expired() is False


def test_compat_phase78_aliases():
    import qlnb.compat as cql

    assert cql.SpreadBasketPayoff is not None
    assert cql.BasketOption is not None
    assert hasattr(cql.BasketOption, "setKirkPricingEngine")
    assert hasattr(cql.BasketOption, "isExpired")
    assert cql.KirkEngine is not None
