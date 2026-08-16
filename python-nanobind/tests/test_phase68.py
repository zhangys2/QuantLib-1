"""Phase-68 tests: BarrierOption implied volatility."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase68():
    assert ql.__version__ == "0.69.0"


def _iv_market():
    # BarrierOptionTest::testImpliedVolatility.
    today = ql.Date(11, ql.Month.February, 2018)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    maturity = today + ql.Period(1, ql.TimeUnit.Years)
    dummy = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.0, dc),
    )
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, 105.0)
    exercise = ql.EuropeanExercise(maturity)
    return today, dc, dummy, payoff, exercise


def _process_at_vol(today, dc, vol):
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


def test_barrier_implied_vol_round_trips_analytic():
    today, dc, dummy, payoff, exercise = _iv_market()
    cases = [
        (ql.BarrierType.DownOut, 90.0, 1.0),
        (ql.BarrierType.UpOut, 110.0, 1.0),
        (ql.BarrierType.DownIn, 90.0, 5.0),
        (ql.BarrierType.UpIn, 110.0, 5.0),
    ]
    for barrier_type, barrier, target in cases:
        opt = ql.BarrierOption(barrier_type, barrier, 5.0, payoff, exercise)
        vol = opt.implied_volatility(target, dummy, accuracy=1.0e-6)
        assert vol > 0.0
        priced = ql.BarrierOption(barrier_type, barrier, 5.0, payoff, exercise)
        priced.set_pricing_engine(_process_at_vol(today, dc, vol))
        assert priced.NPV() == pytest.approx(target, abs=1.0e-5)


def test_barrier_implied_vol_round_trips_dividends():
    today, dc, dummy, payoff, exercise = _iv_market()
    div_dates = [today + ql.Period(6, ql.TimeUnit.Months)]
    div_amounts = [10.0]
    cases = [
        (ql.BarrierType.DownOut, 90.0, 8.0),
        (ql.BarrierType.UpOut, 110.0, 12.0),
        (ql.BarrierType.DownIn, 90.0, 9.0),
        (ql.BarrierType.UpIn, 110.0, 8.0),
    ]
    for barrier_type, barrier, target in cases:
        opt = ql.BarrierOption(barrier_type, barrier, 5.0, payoff, exercise)
        vol = opt.implied_volatility(
            target, dummy, div_dates, div_amounts, accuracy=1.0e-6
        )
        assert vol > 0.0
        priced = ql.BarrierOption(barrier_type, barrier, 5.0, payoff, exercise)
        priced.set_fd_dividend_pricing_engine(
            _process_at_vol(today, dc, vol), div_dates, div_amounts
        )
        assert priced.NPV() == pytest.approx(target, abs=1.0e-5)


def test_compat_phase68_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.BarrierOption, "impliedVolatility")
