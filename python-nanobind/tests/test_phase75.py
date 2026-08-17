"""Phase-75 tests: Margrabe exchange options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase75():
    assert ql.__version__ == "0.76.0"


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


# MargrabeOptionTests::testEuroExchangeTwoAssets (Haug p.52, tol 1e-3).
_EURO_ROWS = [
    # s1, s2, Q1, Q2, q1, q2, r, t, v1, v2, rho, npv, d1, d2, g1, g2, theta
    (22.0, 20.0, 1, 1, 0.06, 0.04, 0.10, 0.10, 0.20, 0.15, -0.50,
     2.125, 0.841, -0.818, 0.112, 0.135, -2.043),
    (22.0, 20.0, 1, 1, 0.06, 0.04, 0.10, 0.10, 0.20, 0.20, 0.00,
     2.091, 0.857, -0.838, 0.112, 0.135, -1.698),
    (22.0, 10.0, 1, 2, 0.06, 0.04, 0.10, 0.50, 0.20, 0.15, 0.50,
     2.138, 0.746, -1.426, 0.106, 0.255, -0.987),
]


@pytest.mark.parametrize(
    "s1,s2,q1,q2,div1,div2,r,t,v1,v2,rho,npv,d1,d2,g1,g2,theta",
    _EURO_ROWS,
)
def test_european_margrabe_haug(
    s1, s2, q1, q2, div1, div2, r, t, v1, v2, rho, npv, d1, d2, g1, g2, theta
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(t)
    opt = ql.MargrabeOption(q1, q2, ql.EuropeanExercise(maturity))
    opt.set_pricing_engine(
        _bsm(today, s1, div1, r, v1),
        _bsm(today, s2, div2, r, v2),
        rho,
    )
    assert opt.NPV() == pytest.approx(npv, abs=1.0e-3)
    assert opt.delta1() == pytest.approx(d1, abs=1.0e-3)
    assert opt.delta2() == pytest.approx(d2, abs=1.0e-3)
    assert opt.gamma1() == pytest.approx(g1, abs=1.0e-3)
    assert opt.gamma2() == pytest.approx(g2, abs=1.0e-3)
    assert opt.theta() == pytest.approx(theta, abs=1.0e-3)
    assert opt.is_expired() is False


def test_american_margrabe_haug():
    # MargrabeOptionTests::testAmericanExchangeTwoAssets first Haug row.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.10)
    opt = ql.MargrabeOption(1, 1, ql.AmericanExercise(today, maturity))
    opt.set_american_pricing_engine(
        _bsm(today, 22.0, 0.06, 0.10, 0.20),
        _bsm(today, 20.0, 0.04, 0.10, 0.15),
        -0.50,
    )
    assert opt.NPV() == pytest.approx(2.1357, abs=1.0e-3)
    assert opt.is_expired() is False


def test_american_premium_over_european():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.10)
    p1 = _bsm(today, 22.0, 0.06, 0.10, 0.20)
    p2 = _bsm(today, 20.0, 0.04, 0.10, 0.15)
    euro = ql.MargrabeOption(1, 1, ql.EuropeanExercise(maturity))
    euro.set_pricing_engine(p1, p2, -0.50)
    amer = ql.MargrabeOption(1, 1, ql.AmericanExercise(today, maturity))
    amer.set_american_pricing_engine(p1, p2, -0.50)
    assert amer.NPV() > euro.NPV()


def test_compat_phase75_aliases():
    import qlnb.compat as cql

    assert cql.MargrabeOption is not None
    assert hasattr(cql.MargrabeOption, "setPricingEngine")
    assert hasattr(cql.MargrabeOption, "setAmericanPricingEngine")
    assert hasattr(cql.MargrabeOption, "isExpired")
    assert cql.AnalyticEuropeanMargrabeEngine is not None
    assert cql.AnalyticAmericanMargrabeEngine is not None
