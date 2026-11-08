"""Phase-111 tests: ConstNotionalCrossCurrencySwap."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase111():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 2)


def _usd_discount_curve():
    dc = ql.Actual365Fixed()
    dates = [
        ql.Date(11, ql.Month.September, 2018),
        ql.Date(14, ql.Month.September, 2018),
        ql.Date(20, ql.Month.September, 2018),
        ql.Date(27, ql.Month.September, 2018),
        ql.Date(4, ql.Month.October, 2018),
        ql.Date(15, ql.Month.October, 2018),
        ql.Date(13, ql.Month.November, 2018),
        ql.Date(13, ql.Month.December, 2018),
        ql.Date(14, ql.Month.January, 2019),
        ql.Date(13, ql.Month.February, 2019),
        ql.Date(13, ql.Month.March, 2019),
        ql.Date(13, ql.Month.June, 2019),
        ql.Date(13, ql.Month.September, 2019),
        ql.Date(13, ql.Month.March, 2020),
        ql.Date(14, ql.Month.September, 2020),
        ql.Date(13, ql.Month.September, 2021),
        ql.Date(13, ql.Month.September, 2022),
        ql.Date(13, ql.Month.September, 2023),
        ql.Date(15, ql.Month.September, 2025),
        ql.Date(13, ql.Month.September, 2028),
        ql.Date(13, ql.Month.September, 2030),
        ql.Date(13, ql.Month.September, 2033),
        ql.Date(13, ql.Month.September, 2038),
        ql.Date(14, ql.Month.September, 2043),
        ql.Date(14, ql.Month.September, 2048),
        ql.Date(13, ql.Month.September, 2058),
        ql.Date(13, ql.Month.September, 2068),
    ]
    dfs = [
        1.0,
        0.99994666951096,
        0.999627719221066,
        0.999254084816959,
        0.998837020905631,
        0.998176132423265,
        0.99644587210048,
        0.994644668243218,
        0.992596634984033,
        0.990636503861861,
        0.988809127958345,
        0.982417991680868,
        0.975723193871552,
        0.96219213956104,
        0.948588232418325,
        0.92279636773464,
        0.898345201557914,
        0.874715322269088,
        0.828658611114833,
        0.763030152740947,
        0.722238847877756,
        0.664460629674362,
        0.580288693473926,
        0.510857007600479,
        0.44941525649436,
        0.352389176933952,
        0.28183300653329,
    ]
    return ql.DiscountCurve(dates, dfs, dc)


def _chf_discount_curve():
    dc = ql.Actual365Fixed()
    dates = [
        ql.Date(11, ql.Month.September, 2018),
        ql.Date(14, ql.Month.September, 2018),
        ql.Date(20, ql.Month.September, 2018),
        ql.Date(27, ql.Month.September, 2018),
        ql.Date(4, ql.Month.October, 2018),
        ql.Date(15, ql.Month.October, 2018),
        ql.Date(13, ql.Month.November, 2018),
        ql.Date(13, ql.Month.December, 2018),
        ql.Date(14, ql.Month.January, 2019),
        ql.Date(13, ql.Month.February, 2019),
        ql.Date(13, ql.Month.March, 2019),
        ql.Date(13, ql.Month.June, 2019),
        ql.Date(13, ql.Month.September, 2019),
        ql.Date(13, ql.Month.March, 2020),
        ql.Date(14, ql.Month.September, 2020),
        ql.Date(13, ql.Month.September, 2021),
        ql.Date(13, ql.Month.September, 2022),
        ql.Date(13, ql.Month.September, 2023),
        ql.Date(15, ql.Month.September, 2025),
        ql.Date(13, ql.Month.September, 2028),
        ql.Date(13, ql.Month.September, 2030),
        ql.Date(13, ql.Month.September, 2033),
        ql.Date(13, ql.Month.September, 2038),
        ql.Date(14, ql.Month.September, 2043),
        ql.Date(14, ql.Month.September, 2048),
        ql.Date(13, ql.Month.September, 2058),
        ql.Date(13, ql.Month.September, 2068),
    ]
    dfs = [
        1.0,
        0.99998,
        0.99975,
        0.99945,
        0.99910,
        0.99855,
        0.99700,
        0.99540,
        0.99360,
        0.99190,
        0.99030,
        0.98430,
        0.97800,
        0.96500,
        0.95200,
        0.92700,
        0.90300,
        0.88000,
        0.83600,
        0.77300,
        0.73400,
        0.67800,
        0.59600,
        0.52800,
        0.46800,
        0.36700,
        0.29700,
    ]
    return ql.DiscountCurve(dates, dfs, dc)


def test_fix_fix_xccy_swap_pricing():
    # ConstNotionalCrossCurrencySwapTests::testFixFixXCCYSwapPricing
    ql.set_evaluation_date(ql.Date(11, ql.Month.September, 2018))
    usd_nominal = 125_000_000.0
    spot_fx = 1.22
    swap = ql.make_fix_fix_xccy_swap(usd_nominal, spot_fx)

    fx_quote = ql.make_quote_handle(1.0 / spot_fx)
    swap.set_pricing_engine(
        ql.USDCurrency(),
        _usd_discount_curve(),
        ql.CHFCurrency(),
        _chf_discount_curve(),
        fx_quote,
    )

    tol = 0.01
    assert swap.NPV() == pytest.approx(-21108172.67, abs=tol)
    assert swap.leg_npv(0) == pytest.approx(-17892458.36, abs=tol)
    assert swap.leg_bps(0) == pytest.approx(-58317.61, abs=tol)
    assert swap.in_ccy_leg_npv(0) == pytest.approx(-17892458.36, abs=tol)
    assert swap.in_ccy_leg_bps(0) == pytest.approx(-58317.61, abs=tol)
    assert swap.leg_npv(1) == pytest.approx(-3215714.30, abs=tol)
    assert swap.leg_bps(1) == pytest.approx(58542.62, abs=tol)
    assert swap.in_ccy_leg_npv(1) == pytest.approx(-3215714.30 * spot_fx, abs=tol * spot_fx)
    assert swap.in_ccy_leg_bps(1) == pytest.approx(58542.62 * spot_fx, abs=tol * spot_fx)


def test_compat_phase111_aliases():
    import qlnb.compat as c

    assert c.ConstNotionalCrossCurrencySwap is not None
    assert c.makeFixFixXCCYSwap is not None
    assert c.CHFCurrency is not None
    assert c.Switzerland is not None
    assert hasattr(c.ConstNotionalCrossCurrencySwap, "setPricingEngine")
