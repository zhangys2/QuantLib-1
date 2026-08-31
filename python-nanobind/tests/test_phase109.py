"""Phase-109 tests: ConstNotionalCrossCurrencyBasisSwap."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase109():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 0)


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


def _gbp_discount_curve():
    return _usd_discount_curve()


def _gbp_projection_curve():
    return _usd_projection_curve()


def _make_basis_xccy_swap(spot_fx: float, gbp_spread: float):
    gbp_nominal = 10_000_000.0
    pay_calendar = ql.JointCalendar(
        ql.UnitedStates(ql.UnitedStatesMarket.Settlement),
        ql.UnitedKingdom(),
    )

    today = ql.get_evaluation_date()
    reference_date = pay_calendar.adjust(today)
    start = pay_calendar.advance(reference_date, 2, ql.TimeUnit.Days)
    end = start + ql.Period(5, ql.TimeUnit.Years)
    schedule = ql.Schedule(
        start,
        end,
        ql.Period(3, ql.TimeUnit.Months),
        pay_calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.DateGeneration.Backward,
        False,
    )

    usd_index = ql.USDLibor(ql.Period(3, ql.TimeUnit.Months), _usd_projection_curve())
    gbp_index = ql.GBPLibor(ql.Period(3, ql.TimeUnit.Months), _gbp_projection_curve())

    return ql.ConstNotionalCrossCurrencyBasisSwap(
        gbp_nominal,
        ql.GBPCurrency(),
        schedule,
        gbp_index,
        gbp_spread,
        1.0,
        gbp_nominal * spot_fx,
        ql.USDCurrency(),
        schedule,
        usd_index,
        0.0,
        1.0,
    )


def test_basis_xccy_swap_pricing():
    # ConstNotionalCrossCurrencyBasisSwapTest::testBasisXCCYSwapPricing
    ql.set_evaluation_date(ql.Date(11, ql.Month.September, 2018))
    spot_fx = 1.0
    spread = 0.0
    swap = _make_basis_xccy_swap(spot_fx, spread)

    fx_quote = ql.make_quote_handle(spot_fx)
    swap.set_pricing_engine(
        ql.USDCurrency(),
        _usd_discount_curve(),
        ql.GBPCurrency(),
        _gbp_discount_curve(),
        fx_quote,
    )

    tol = 0.01
    assert swap.NPV() == pytest.approx(0.0, abs=tol)
    assert swap.leg_bps(0) == pytest.approx(-4670.170509677384, abs=tol)


def test_compat_phase109_aliases():
    import qlnb.compat as c

    assert c.ConstNotionalCrossCurrencyBasisSwap is not None
    assert hasattr(c.ConstNotionalCrossCurrencyBasisSwap, "setPricingEngine")
    assert hasattr(c.ConstNotionalCrossCurrencyBasisSwap, "legBPS")
    assert hasattr(c.ConstNotionalCrossCurrencyBasisSwap, "fairPaySpread")
