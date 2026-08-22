"""Phase-89 tests: AssetSwap (suite implied value + fair price/spread)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase89():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 90)


def _common_vars():
    # AssetSwapTests::CommonVars — today 24 Apr 2007, flat 5% Actual365Fixed.
    today = ql.Date(24, ql.Month.April, 2007)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.05, ql.Actual365Fixed())
    ibor = ql.Euribor6M(curve)
    return today, curve, ibor


def _dbr_bond():
    # DE0001135275 DBR 4 01/04/37 — AssetSwapTests::testImpliedValue.
    calendar = ql.TARGET()
    schedule = ql.Schedule(
        ql.Date(4, ql.Month.January, 2005),
        ql.Date(4, ql.Month.January, 2037),
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    return ql.FixedRateBond(
        3,
        100.0,
        schedule,
        [0.04],
        ql.ActualActual(ql.ActualActualConvention.ISDA),
        ql.BusinessDayConvention.Following,
        100.0,
        ql.Date(4, ql.Month.January, 2005),
    )


def test_implied_value_fixed_bond():
    # AssetSwapTests::testImpliedValue — zero-spread fair clean = bond clean.
    _today, curve, ibor = _common_vars()
    bond = _dbr_bond()
    bond.set_pricing_engine(curve)
    bond_clean = bond.clean_price()
    asw = ql.AssetSwap(
        True,
        bond,
        bond_clean,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    asw.set_pricing_engine(curve)
    # At-par coupons: suite tolerance 1e-13.
    assert asw.fair_clean_price() == pytest.approx(bond_clean, abs=1.0e-13)
    assert asw.is_expired() is False
    assert asw.par_swap() is True
    assert asw.pay_bond_coupon() is True
    assert asw.spread() == 0.0
    assert asw.clean_price() == pytest.approx(bond_clean, abs=0.0)


def test_consistency_fair_price_and_spread():
    # AssetSwapTests::testConsistency — fair clean / fair spread zero NPV.
    _today, curve, ibor = _common_vars()
    bond = _dbr_bond()
    bond_price = 95.0
    asw = ql.AssetSwap(
        True,
        bond,
        bond_price,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    asw.set_pricing_engine(
        curve,
        include_settlement_date_flows=True,
        settlement_date=bond.settlement_date(),
        npv_date=ql.Date(24, ql.Month.April, 2007),
    )
    fair_clean = asw.fair_clean_price()
    fair_spread = asw.fair_spread()

    asw_price = ql.AssetSwap(
        True,
        bond,
        fair_clean,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    asw_price.set_pricing_engine(
        curve,
        include_settlement_date_flows=True,
        settlement_date=bond.settlement_date(),
        npv_date=ql.Date(24, ql.Month.April, 2007),
    )
    assert asw_price.NPV() == pytest.approx(0.0, abs=1.0e-13)
    assert asw_price.fair_clean_price() == pytest.approx(fair_clean, abs=1.0e-13)
    assert asw_price.fair_spread() == pytest.approx(0.0, abs=1.0e-13)

    asw_spread = ql.AssetSwap(
        True,
        bond,
        bond_price,
        ibor,
        fair_spread,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    asw_spread.set_pricing_engine(
        curve,
        include_settlement_date_flows=True,
        settlement_date=bond.settlement_date(),
        npv_date=ql.Date(24, ql.Month.April, 2007),
    )
    assert asw_spread.NPV() == pytest.approx(0.0, abs=1.0e-13)
    assert asw_spread.fair_clean_price() == pytest.approx(bond_price, abs=1.0e-13)
    assert asw_spread.fair_spread() == pytest.approx(fair_spread, abs=1.0e-13)


def test_implied_value_ibrd_and_zero_coupon():
    # Second fixed bond (IT0006527060) + a zero-coupon from the same fixture.
    _today, curve, ibor = _common_vars()
    calendar = ql.TARGET()
    schedule = ql.Schedule(
        ql.Date(5, ql.Month.February, 2005),
        ql.Date(5, ql.Month.February, 2019),
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    bond = ql.FixedRateBond(
        3,
        100.0,
        schedule,
        [0.05],
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        ql.BusinessDayConvention.Following,
        100.0,
        ql.Date(5, ql.Month.February, 2005),
    )
    bond.set_pricing_engine(curve)
    bond_clean = bond.clean_price()
    asw = ql.AssetSwap(
        True,
        bond,
        bond_clean,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    asw.set_pricing_engine(curve)
    assert asw.fair_clean_price() == pytest.approx(bond_clean, abs=1.0e-13)

    zc = ql.ZeroCouponBond(
        3,
        calendar,
        100.0,
        ql.Date(20, ql.Month.December, 2015),
        ql.BusinessDayConvention.Following,
        100.0,
        ql.Date(19, ql.Month.December, 1985),
    )
    zc.set_pricing_engine(curve)
    zc_clean = zc.clean_price()
    zc_asw = ql.AssetSwap(
        True,
        zc,
        zc_clean,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    zc_asw.set_pricing_engine(curve)
    assert zc_asw.fair_clean_price() == pytest.approx(zc_clean, abs=1.0e-13)


def test_implied_value_floating_bond():
    # AssetSwapTests::testImpliedValue — ISPIM FRN IT0003543847.
    _today, curve, ibor = _common_vars()
    calendar = ql.TARGET()
    schedule = ql.Schedule(
        ql.Date(29, ql.Month.September, 2003),
        ql.Date(29, ql.Month.September, 2013),
        ql.Period(ql.Frequency.Semiannual),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    bond = ql.FloatingRateBond(
        3,
        100.0,
        schedule,
        ibor,
        ql.Actual360(),
        ql.BusinessDayConvention.Following,
        2,
        [1.0],
        [0.0056],
        [],
        [],
        False,
        100.0,
        ql.Date(29, ql.Month.September, 2003),
    )
    bond.set_pricing_engine(curve)
    ibor.add_fixing(ql.Date(27, ql.Month.March, 2007), 0.0402)
    bond_clean = bond.clean_price()
    asw = ql.AssetSwap(
        True,
        bond,
        bond_clean,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=True,
    )
    asw.set_pricing_engine(curve)
    assert asw.fair_clean_price() == pytest.approx(bond_clean, abs=1.0e-13)


def test_market_asset_swap_consistency():
    # AssetSwapTests::testConsistency market (par_asset_swap=False) path.
    _today, curve, ibor = _common_vars()
    bond = _dbr_bond()
    bond_price = 95.0
    asw = ql.AssetSwap(
        True,
        bond,
        bond_price,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=False,
    )
    asw.set_pricing_engine(curve)
    assert asw.par_swap() is False
    fair_clean = asw.fair_clean_price()
    asw2 = ql.AssetSwap(
        True,
        bond,
        fair_clean,
        ibor,
        0.0,
        floating_day_count=ibor.day_counter(),
        par_asset_swap=False,
    )
    asw2.set_pricing_engine(curve)
    assert asw2.NPV() == pytest.approx(0.0, abs=1.0e-10)


def test_compat_phase89_aliases():
    import qlnb.compat as cql

    assert cql.AssetSwap is not None
    assert hasattr(cql.AssetSwap, "fairCleanPrice")
    assert hasattr(cql.AssetSwap, "fairSpread")
    assert hasattr(cql.AssetSwap, "setPricingEngine")
    assert hasattr(cql.AssetSwap, "payBondCoupon")
