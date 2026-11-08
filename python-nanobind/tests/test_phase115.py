"""Phase-115 tests: CmsRateBond + AssetSwap CMS underlying."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase115():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 6)


def _assetswap_market():
    # AssetSwapTests::CommonVars — today 24 Apr 2007, flat 5% Actual365Fixed.
    today = ql.Date(24, ql.Month.April, 2007)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.05, ql.Actual365Fixed())
    ibor = ql.Euribor6M(curve)
    swap_index = ql.EuriborSwapIsdaFixA(ql.Period(10, ql.TimeUnit.Years), curve)
    swaption_vol = ql.ConstantSwaptionVolatility(
        today,
        ql.TARGET(),
        ql.BusinessDayConvention.Following,
        0.2,
        ql.Actual365Fixed(),
    )
    cms_pricer = ql.AnalyticHaganPricer(
        swaption_vol,
        ql.YieldCurveModel.Standard,
        ql.make_quote_handle(0.01),
    )
    return today, curve, ibor, swap_index, cms_pricer


def _cms_bond_ispim(swap_index: ql.SwapIndex):
    # AssetSwapTests::testImpliedValue — ISPIM FR0003543847-style CMS bond #2.
    calendar = ql.TARGET()
    schedule = ql.Schedule(
        ql.Date(6, ql.Month.May, 2005),
        ql.Date(6, ql.Month.May, 2015),
        ql.Period(ql.Frequency.Annual),
        calendar,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    return ql.CmsRateBond(
        3,
        100.0,
        schedule,
        swap_index,
        ql.Thirty360(ql.Thirty360Convention.BondBasis),
        ql.BusinessDayConvention.Following,
        fixing_days=2,
        gearings=[0.84],
        spreads=[0.0],
        in_arrears=False,
        redemption=100.0,
        issue_date=ql.Date(6, ql.Month.May, 2005),
    )


def test_cms_bond_clean_price():
    _today, curve, _ibor, swap_index, cms_pricer = _assetswap_market()
    bond = _cms_bond_ispim(swap_index)
    bond.set_pricing_engine(curve)
    bond.set_cms_coupon_pricer(cms_pricer)
    swap_index.add_fixing(ql.Date(4, ql.Month.May, 2006), 0.04217)
    assert bond.clean_price() == pytest.approx(95.48461550443967, abs=1.0e-10)


def test_cms_bond_asset_swap_implied_value():
    # AssetSwapTests::testImpliedValue — CMS bond zero-spread fair clean.
    _today, curve, ibor, swap_index, cms_pricer = _assetswap_market()
    bond = _cms_bond_ispim(swap_index)
    bond.set_pricing_engine(curve)
    bond.set_cms_coupon_pricer(cms_pricer)
    swap_index.add_fixing(ql.Date(4, ql.Month.May, 2006), 0.04217)
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
    # Indexed CMS coupons: suite uses relaxed tol 1e-2 when not at-par.
    assert asw.fair_clean_price() == pytest.approx(bond_clean, abs=1.0e-2)


def test_compat_phase115_aliases():
    import qlnb.compat as c

    assert c.CmsRateBond is not None
    assert hasattr(c.CmsRateBond, "setCmsCouponPricer")
