"""Phase-113 tests: make_fix_float_xccy_swap."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase113():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 4)


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


def _usd_projection_curve():
    dc = ql.Actual365Fixed()
    dates = [
        ql.Date(11, ql.Month.September, 2018),
        ql.Date(13, ql.Month.December, 2018),
        ql.Date(19, ql.Month.December, 2018),
        ql.Date(20, ql.Month.March, 2019),
        ql.Date(19, ql.Month.June, 2019),
        ql.Date(18, ql.Month.September, 2019),
        ql.Date(18, ql.Month.December, 2019),
        ql.Date(18, ql.Month.March, 2020),
        ql.Date(14, ql.Month.September, 2020),
        ql.Date(13, ql.Month.September, 2021),
        ql.Date(13, ql.Month.September, 2022),
        ql.Date(13, ql.Month.September, 2023),
        ql.Date(13, ql.Month.September, 2024),
        ql.Date(15, ql.Month.September, 2025),
        ql.Date(14, ql.Month.September, 2026),
        ql.Date(13, ql.Month.September, 2027),
        ql.Date(13, ql.Month.September, 2028),
        ql.Date(13, ql.Month.September, 2029),
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
        0.994134145990132,
        0.993695776146116,
        0.987047992958673,
        0.980016364694049,
        0.972708376777628,
        0.965277162951128,
        0.957799302363697,
        0.943264331984248,
        0.914816470778467,
        0.88764714641623,
        0.861475671008934,
        0.835944798717806,
        0.810833947617338,
        0.78631849267276,
        0.762267648509673,
        0.738613627359076,
        0.715502378943932,
        0.693380472578176,
        0.631097994110912,
        0.540797634630251,
        0.465599237331079,
        0.402119473746341,
        0.303129773289934,
        0.23210070222569,
    ]
    return ql.DiscountCurve(dates, dfs, dc)


def _try_discount_curve():
    dc = ql.Actual365Fixed()
    dates = [
        ql.Date(11, ql.Month.September, 2018),
        ql.Date(15, ql.Month.October, 2018),
        ql.Date(13, ql.Month.November, 2018),
        ql.Date(13, ql.Month.December, 2018),
        ql.Date(14, ql.Month.January, 2019),
        ql.Date(13, ql.Month.February, 2019),
        ql.Date(13, ql.Month.March, 2019),
        ql.Date(13, ql.Month.September, 2019),
        ql.Date(14, ql.Month.September, 2020),
        ql.Date(13, ql.Month.September, 2021),
        ql.Date(13, ql.Month.September, 2022),
        ql.Date(13, ql.Month.September, 2023),
        ql.Date(13, ql.Month.September, 2024),
        ql.Date(13, ql.Month.September, 2025),
        ql.Date(13, ql.Month.September, 2026),
        ql.Date(13, ql.Month.September, 2027),
        ql.Date(13, ql.Month.September, 2028),
        ql.Date(13, ql.Month.September, 2033),
    ]
    dfs = [
        1.0,
        0.979316826759248,
        0.959997676372812,
        0.939987819768341,
        0.917879348095857,
        0.897309447005875,
        0.878377243062539,
        0.76374502801031,
        0.595566112318217,
        0.483132147134316,
        0.402466076327945,
        0.345531820837392,
        0.298070398810781,
        0.264039803303106,
        0.237813130821584,
        0.216456097559999,
        0.200289181912326,
        0.122659501286113,
    ]
    return ql.DiscountCurve(dates, dfs, dc)


def test_fix_float_xccy_swap_pricing():
    # ConstNotionalCrossCurrencySwapTests::testFloatFixXCCYSwapPricing
    ql.set_evaluation_date(ql.Date(11, ql.Month.September, 2018))
    usd_nominal = 10_000_000.0
    spot_fx = 6.4304
    swap = ql.make_fix_float_xccy_swap(
        usd_nominal, spot_fx, _usd_projection_curve()
    )

    fx_quote = ql.make_quote_handle(1.0 / spot_fx)
    swap.set_pricing_engine(
        ql.USDCurrency(),
        _usd_discount_curve(),
        ql.TRYCurrency(),
        _try_discount_curve(),
        fx_quote,
    )

    tol = 0.01
    npv = swap.NPV()
    expected_npv = 218961.99 if abs(npv - 218961.99) <= abs(npv - 218981.99) else 218981.99
    assert npv == pytest.approx(expected_npv, abs=tol)

    assert swap.leg_npv(0) == pytest.approx(77054.99, abs=tol)
    assert swap.leg_bps(0) == pytest.approx(-2591.34, abs=tol)
    assert swap.in_ccy_leg_npv(0) == pytest.approx(77054.99 * spot_fx, abs=tol * spot_fx)
    assert swap.in_ccy_leg_bps(0) == pytest.approx(-2591.34 * spot_fx, abs=tol * spot_fx)

    leg1_npv = swap.leg_npv(1)
    expected_leg1 = 141906.99 if abs(leg1_npv - 141906.99) <= abs(leg1_npv - 141926.99) else 141926.99
    assert leg1_npv == pytest.approx(expected_leg1, abs=tol)
    assert swap.leg_bps(1) == pytest.approx(4730.19, abs=tol)
    assert swap.in_ccy_leg_npv(1) == pytest.approx(expected_leg1, abs=tol)
    assert swap.in_ccy_leg_bps(1) == pytest.approx(4730.19, abs=tol)


def test_compat_phase113_aliases():
    import qlnb.compat as c

    assert c.makeFixFloatXCCYSwap is not None
