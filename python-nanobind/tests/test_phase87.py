"""Phase-87 tests: n-D PDE basket engine and American BasketOption."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase87():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 88)


def _bsm(
    today: ql.Date,
    spot: float,
    q: float,
    r_ts,
    vol: float,
    dc=None,
):
    if dc is None:
        dc = ql.Actual365Fixed()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        r_ts,
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# BasketOptionTests::testNdimPDEinDifferentDims — 1-asset vs SingleFactor.
def test_fd_ndim_one_asset_matches_single_factor():
    today = ql.Date(25, ql.Month.February, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(6, ql.TimeUnit.Months)
    dc = ql.Actual365Fixed()
    r_ts = ql.FlatForward(today, 0.05, dc)
    process = _bsm(today, 100.0, 0.05, r_ts, 0.3, dc)
    rho = ql.Matrix(1, 1, [1.0])
    payoff = ql.AverageBasketPayoff(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 105.0), [1.0]
    )
    fd = ql.BasketOption(payoff, ql.EuropeanExercise(maturity))
    sf = ql.BasketOption(payoff, ql.EuropeanExercise(maturity))
    fd.set_fd_ndim_pricing_engine([process], rho, x_grid=30, t_grid=7)
    sf.set_single_factor_pricing_engine([process])
    assert fd.NPV() == pytest.approx(sf.NPV(), abs=0.05)
    assert fd.is_expired() is False


# BasketOptionTests::testNdimPDEvs2dimPDE — European spread.
def test_fd_ndim_matches_fd_2d_spread():
    today = ql.Date(25, ql.Month.February, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(6, ql.TimeUnit.Months)
    dc = ql.Actual365Fixed()
    r_ts = ql.FlatForward(today, 0.1, dc)
    p1 = _bsm(today, 110.0, 0.1, r_ts, 0.5, dc)
    p2 = _bsm(today, 100.0, 0.075, r_ts, 0.3, dc)
    rho = 0.75
    payoff = ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 5.0))
    fd2 = ql.BasketOption(payoff, ql.EuropeanExercise(maturity))
    fdn = ql.BasketOption(payoff, ql.EuropeanExercise(maturity))
    fd2.set_fd_2d_pricing_engine(p1, p2, rho, x_grid=25, y_grid=25, t_grid=15)
    fdn.set_fd_ndim_pricing_engine(
        [p1, p2],
        ql.Matrix(2, 2, [1.0, rho, rho, 1.0]),
        t_grid=15,
        x_grids=[25, 25],
    )
    assert fdn.NPV() == pytest.approx(fd2.NPV(), abs=0.2)


# BasketOptionTests::testFdmAmericanBasketOptions.
def test_fd_ndim_american_basket_golden():
    today = ql.Date(28, ql.Month.October, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(9, ql.TimeUnit.Months)
    dc = ql.Actual365Fixed()
    r_ts = ql.FlatForward(today, 0.1, dc)
    processes = [
        _bsm(today, 100.0, 0.02, r_ts, 0.4, dc),
        _bsm(today, 25.0, 0.035, r_ts, 0.5, dc),
        _bsm(today, 90.0, 0.08, r_ts, 0.25, dc),
    ]
    rho = ql.Matrix(
        3,
        3,
        [
            1.0, 0.2, 0.6,
            0.2, 1.0, -0.3,
            0.6, -0.3, 1.0,
        ],
    )
    opt = ql.BasketOption(
        ql.AverageBasketPayoff(
            ql.PlainVanillaPayoff(ql.OptionType.Put, -30.0), [1.0, -2.0, -1.0]
        ),
        ql.AmericanExercise(today, maturity),
    )
    opt.set_fd_ndim_pricing_engine(
        processes, rho, t_grid=15, x_grids=[20, 20, 20]
    )
    assert opt.NPV() == pytest.approx(15.1858, abs=0.01)


def test_compat_phase87_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BasketOption, "setFdNdimPricingEngine")
    assert cql.FdndimBlackScholesVanillaEngine is not None
    assert cql.AmericanExercise is not None
