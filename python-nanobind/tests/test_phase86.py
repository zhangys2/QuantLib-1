"""Phase-86 tests: Gaussian copula and 2-D PDE spread engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase86():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 87)


def _copula_market(today: ql.Date):
    # GaussianCopulaSpreadEngine requires a shared risk-free TS handle.
    dc = ql.Actual365Fixed()
    r_ts = ql.FlatForward(today, 0.05, dc)

    def process(spot: float, vol: float):
        return ql.BlackScholesMertonProcess(
            ql.make_quote_handle(spot),
            r_ts,
            r_ts,
            ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
        )

    return process(100.0, 0.20), process(96.0, 0.25), r_ts


def _spread_option(maturity: ql.Date, option_type, strike: float):
    return ql.BasketOption(
        ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(option_type, strike)),
        ql.EuropeanExercise(maturity),
    )


# BasketOptionTests::testGaussianCopulaSpreadEngineFlatVol
def test_gaussian_copula_call_put_parity():
    today = ql.Date(1, ql.Month.March, 2025)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1, p2, r_ts = _copula_market(today)
    call = _spread_option(maturity, ql.OptionType.Call, 3.0)
    put = _spread_option(maturity, ql.OptionType.Put, 3.0)
    call.set_gaussian_copula_pricing_engine(p1, p2, 0.5)
    put.set_gaussian_copula_pricing_engine(p1, p2, 0.5)
    fwd = (call.NPV() - put.NPV()) / r_ts.discount(maturity)
    expected = 100.0 - 96.0 - 3.0
    assert fwd == pytest.approx(expected, rel=1.0e-3)
    assert call.is_expired() is False


def test_gaussian_copula_exchange_matches_bjerksund():
    today = ql.Date(1, ql.Month.March, 2025)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1, p2, _ = _copula_market(today)
    copula = _spread_option(maturity, ql.OptionType.Call, 0.0)
    bjerksund = _spread_option(maturity, ql.OptionType.Call, 0.0)
    copula.set_gaussian_copula_pricing_engine(p1, p2, 0.5)
    bjerksund.set_bjerksund_stensland_pricing_engine(p1, p2, 0.5)
    assert copula.NPV() == pytest.approx(bjerksund.NPV(), rel=1.0e-3)


def test_fd_2d_matches_bjerksund():
    today = ql.Date(1, ql.Month.March, 2025)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)
    p1, p2, _ = _copula_market(today)
    fd = _spread_option(maturity, ql.OptionType.Call, 3.0)
    bs = _spread_option(maturity, ql.OptionType.Call, 3.0)
    fd.set_fd_2d_pricing_engine(p1, p2, 0.5, x_grid=50, y_grid=50, t_grid=15)
    bs.set_bjerksund_stensland_pricing_engine(p1, p2, 0.5)
    assert fd.NPV() == pytest.approx(bs.NPV(), abs=0.05)


def test_compat_phase86_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BasketOption, "setGaussianCopulaPricingEngine")
    assert hasattr(cql.BasketOption, "setFd2dPricingEngine")
    assert cql.GaussianCopulaSpreadEngine is not None
    assert cql.Fd2dBlackScholesVanillaEngine is not None
