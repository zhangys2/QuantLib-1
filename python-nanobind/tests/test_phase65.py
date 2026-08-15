"""Phase-65 tests: CPI vol-dependent optionlets (Black / Bachelier)."""

from __future__ import annotations

import pytest

import qlnb as ql

from test_phase18 import _uk_cpi_coupon_market


def test_version_is_phase65():
    assert ql.__version__ == "0.66.0"


def _future_cpi_coupon(index, calendar, bdc, interp, fixed_rate=0.1):
    # Evaluation is 25 Nov 2009; this coupon fixes in 2015 (unfixed).
    lag = ql.Period(3, ql.TimeUnit.Months)
    base_cpi = 206.1
    start = ql.Date(2, ql.Month.October, 2014)
    end = ql.Date(2, ql.Month.April, 2015)
    pay = calendar.adjust(end, bdc)
    cpn = ql.CPICoupon(
        base_cpi,
        pay,
        1_000_000.0,
        start,
        end,
        index,
        lag,
        interp,
        ql.Actual365Fixed(),
        fixed_rate,
    )
    return cpn, lag


def _const_cpi_vol(calendar, bdc, lag, volatility):
    return ql.ConstantCPIVolatility(
        volatility,
        0,
        calendar,
        bdc,
        ql.Actual365Fixed(),
        lag,
        ql.Frequency.Monthly,
        False,
    )


def test_constant_cpi_vol_handle():
    _, _, _, calendar, bdc, _ = _uk_cpi_coupon_market()
    lag = ql.Period(3, ql.TimeUnit.Months)
    vol = _const_cpi_vol(calendar, bdc, lag, 0.10)
    assert not vol.empty()
    assert vol.observation_lag() == lag
    assert vol.frequency() == ql.Frequency.Monthly
    assert not vol.index_is_interpolated()
    maturity = ql.Date(2, ql.Month.April, 2015)
    assert vol.volatility(maturity, 1.0) == pytest.approx(0.10, abs=1.0e-12)
    assert vol.total_variance(maturity, 1.0) > 0.0


def test_black_cpi_optionlet_positive():
    _, nominal, index, calendar, bdc, interp = _uk_cpi_coupon_market()
    cpn, lag = _future_cpi_coupon(index, calendar, bdc, interp)
    vol = _const_cpi_vol(calendar, bdc, lag, 0.10)
    pricer = ql.BlackCPICouponPricer(nominal, caplet_vol=vol)
    cpn.set_pricer(pricer)
    assert isinstance(pricer, ql.CPICouponPricer)
    assert not pricer.caplet_volatility().empty()

    fwd = cpn.adjusted_index_growth()
    cap = cpn.caplet_price(fwd)
    floor = cpn.floorlet_price(fwd)
    assert cap > 0.0
    assert floor > 0.0
    # ATM call/put parity on the optionlet rate (same stdDev, same forward).
    assert cpn.caplet_rate(fwd) == pytest.approx(cpn.floorlet_rate(fwd), rel=1.0e-8)


def test_zero_vol_optionlet_is_intrinsic():
    _, nominal, index, calendar, bdc, interp = _uk_cpi_coupon_market()
    cpn, lag = _future_cpi_coupon(index, calendar, bdc, interp)
    vol = _const_cpi_vol(calendar, bdc, lag, 0.0)
    cpn.set_pricer(ql.BlackCPICouponPricer(nominal, caplet_vol=vol))
    fwd = cpn.adjusted_index_growth()
    itm_strike = fwd * 0.95
    otm_strike = fwd * 1.05
    # Black with stdDev=0 → max(F-K, 0) (rate space), then * gearing.
    gearing = cpn.fixed_rate()
    assert cpn.caplet_rate(itm_strike) == pytest.approx(
        gearing * (fwd - itm_strike), abs=1.0e-10
    )
    assert cpn.caplet_rate(otm_strike) == pytest.approx(0.0, abs=1.0e-12)
    assert cpn.floorlet_rate(itm_strike) == pytest.approx(0.0, abs=1.0e-12)
    assert cpn.floorlet_rate(otm_strike) == pytest.approx(
        gearing * (otm_strike - fwd), abs=1.0e-10
    )


def test_swaplet_unchanged_vs_plain_pricer():
    _, nominal, index, calendar, bdc, interp = _uk_cpi_coupon_market()
    cpn_plain, _ = _future_cpi_coupon(index, calendar, bdc, interp)
    cpn_black, lag = _future_cpi_coupon(index, calendar, bdc, interp)
    vol = _const_cpi_vol(calendar, bdc, lag, 0.10)
    cpn_plain.set_pricer(ql.CPICouponPricer(nominal))
    cpn_black.set_pricer(ql.BlackCPICouponPricer(nominal, caplet_vol=vol))
    assert cpn_black.rate() == pytest.approx(cpn_plain.rate(), abs=1.0e-12)
    assert cpn_black.amount() == pytest.approx(cpn_plain.amount(), abs=1.0e-8)


def test_plain_pricer_rejects_future_optionlet():
    _, nominal, index, calendar, bdc, interp = _uk_cpi_coupon_market()
    cpn, lag = _future_cpi_coupon(index, calendar, bdc, interp)
    vol = _const_cpi_vol(calendar, bdc, lag, 0.10)
    cpn.set_pricer(ql.CPICouponPricer(nominal, caplet_vol=vol))
    fwd = cpn.adjusted_index_growth()
    with pytest.raises(RuntimeError, match="vol-dependent"):
        cpn.caplet_price(fwd)


def test_bachelier_cpi_optionlet_positive():
    _, nominal, index, calendar, bdc, interp = _uk_cpi_coupon_market()
    cpn, lag = _future_cpi_coupon(index, calendar, bdc, interp)
    vol = _const_cpi_vol(calendar, bdc, lag, 0.02)
    cpn.set_pricer(ql.BachelierCPICouponPricer(nominal, caplet_vol=vol))
    fwd = cpn.adjusted_index_growth()
    assert cpn.caplet_price(fwd) > 0.0
    assert cpn.floorlet_price(fwd) > 0.0


def test_compat_phase65_aliases():
    import qlnb.compat as cql

    assert callable(cql.ConstantCPIVolatility)
    assert callable(cql.BlackCPICouponPricer)
    assert callable(cql.BachelierCPICouponPricer)
    assert hasattr(cql.CPICoupon, "capletPrice")
    assert hasattr(cql.CPICoupon, "floorletPrice")
    assert hasattr(cql.CPICoupon, "indexRatio")
    assert hasattr(cql.CPICouponPricer, "setCapletVolatility")
    assert hasattr(cql.CPIVolatilitySurfaceHandle, "totalVariance")
