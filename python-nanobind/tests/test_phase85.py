"""Phase-85 tests: Bjerksund, Pearson, and operator-splitting spreads."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase85():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 86)


def _futures_bsm(today: ql.Date, spot: float, r: float, vol: float):
    # BlackProcess uses dividendTS = riskFreeTS (cost of carry 0).
    dc = ql.Actual365Fixed()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, r, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _spread_option(today: ql.Date, maturity: ql.Date, option_type, strike: float):
    return ql.BasketOption(
        ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(option_type, strike)),
        ql.EuropeanExercise(maturity),
    )


# BasketOptionTests::testBjerksundStenslandSpreadEngine — PyFENG 0.2.6 put.
def test_bjerksund_stensland_spread_put():
    today = ql.Date(1, ql.Month.March, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1 = _futures_bsm(today, 100.0, 0.05, 0.25)
    p2 = _futures_bsm(today, 110.0, 0.05, 0.35)
    put = _spread_option(today, maturity, ql.OptionType.Put, 5.0)
    put.set_bjerksund_stensland_pricing_engine(p1, p2, 0.75)
    assert put.NPV() == pytest.approx(17.850835947276213, abs=1.0e-8)
    assert put.is_expired() is False


def test_bjerksund_stensland_call_put_parity():
    today = ql.Date(1, ql.Month.March, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1 = _futures_bsm(today, 100.0, 0.05, 0.25)
    p2 = _futures_bsm(today, 110.0, 0.05, 0.35)
    call = _spread_option(today, maturity, ql.OptionType.Call, 5.0)
    put = _spread_option(today, maturity, ql.OptionType.Put, 5.0)
    call.set_bjerksund_stensland_pricing_engine(p1, p2, 0.75)
    put.set_bjerksund_stensland_pricing_engine(p1, p2, 0.75)
    df = ql.FlatForward(today, 0.05, ql.Actual365Fixed()).discount(maturity)
    fwd = (call.NPV() - put.NPV()) / df
    assert fwd == pytest.approx(100.0 - 110.0 - 5.0, abs=1.0e-10)


def test_pearson_call_put_parity():
    today = ql.Date(1, ql.Month.March, 2025)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1 = _futures_bsm(today, 100.0, 0.05, 0.25)
    p2 = _futures_bsm(today, 110.0, 0.05, 0.35)
    call = _spread_option(today, maturity, ql.OptionType.Call, 5.0)
    put = _spread_option(today, maturity, ql.OptionType.Put, 5.0)
    call.set_pearson_pricing_engine(p1, p2, 0.75)
    put.set_pearson_pricing_engine(p1, p2, 0.75)
    df = ql.FlatForward(today, 0.05, ql.Actual365Fixed()).discount(maturity)
    fwd = (call.NPV() - put.NPV()) / df
    assert fwd == pytest.approx(100.0 - 110.0 - 5.0, abs=1.0e-10)


def test_pearson_exchange_matches_bjerksund():
    today = ql.Date(1, ql.Month.March, 2025)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1 = _futures_bsm(today, 100.0, 0.05, 0.25)
    p2 = _futures_bsm(today, 110.0, 0.05, 0.35)
    pearson = _spread_option(today, maturity, ql.OptionType.Call, 0.0)
    bjerksund = _spread_option(today, maturity, ql.OptionType.Call, 0.0)
    pearson.set_pearson_pricing_engine(p1, p2, 0.75)
    bjerksund.set_bjerksund_stensland_pricing_engine(p1, p2, 0.75)
    assert pearson.NPV() == pytest.approx(bjerksund.NPV(), abs=1.0e-6)


# BasketOptionTests::testOperatorSplittingSpreadEngine — Lo 2015 table.
_LO2015 = [
    # rho, first, second
    (-0.9, 18.9323, 18.9361),
    (0.0, 14.284, 14.2843),
    (0.9, 6.9148, 6.9134),
]


def _lo2015_forwards(today: ql.Date, maturity: ql.Date):
    dc = ql.Actual365Fixed()
    r = ql.FlatForward(today, 0.05, dc)
    q1 = ql.FlatForward(today, 0.03, dc)
    q2 = ql.FlatForward(today, 0.02, dc)
    df = r.discount(maturity)
    f1 = 110.0 * q1.discount(maturity) / df
    f2 = 90.0 * q2.discount(maturity) / df
    return _futures_bsm(today, f1, 0.05, 0.3), _futures_bsm(today, f2, 0.05, 0.2)


@pytest.mark.parametrize("rho,first,second", _LO2015)
def test_operator_splitting_lo2015(rho, first, second):
    today = ql.Date(1, ql.Month.March, 2025)
    ql.set_evaluation_date(today)
    # yearFractionToDate(Actual365Fixed, today, 1.0) == today + 365
    maturity = today + 365
    p1, p2 = _lo2015_forwards(today, maturity)
    opt = _spread_option(today, maturity, ql.OptionType.Call, 20.0)
    opt.set_operator_splitting_pricing_engine(
        p1, p2, rho, ql.OperatorSplittingOrder.First
    )
    assert opt.NPV() == pytest.approx(first, abs=1.0e-4)
    opt.set_operator_splitting_pricing_engine(
        p1, p2, rho, ql.OperatorSplittingOrder.Second
    )
    assert opt.NPV() == pytest.approx(second, abs=1.0e-4)


def test_compat_phase85_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BasketOption, "setBjerksundStenslandPricingEngine")
    assert hasattr(cql.BasketOption, "setPearsonPricingEngine")
    assert hasattr(cql.BasketOption, "setOperatorSplittingPricingEngine")
    assert cql.BjerksundStenslandSpreadEngine is not None
    assert cql.PearsonSpreadEngine is not None
    assert cql.OperatorSplittingSpreadEngine is not None
    assert cql.OperatorSplittingOrder.First is not None
    assert cql.OperatorSplittingOrder.Second is not None
