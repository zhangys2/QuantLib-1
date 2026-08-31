"""Phase-166 tests: MarkovFunctional + vanilla engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase166():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 37)


def _flat_market():
    ref = ql.Date(14, ql.Month.November, 2012)
    ql.set_evaluation_date(ref)
    calendar = ql.TARGET()
    yts = ql.FlatForward(ref, 0.03, ql.Actual365Fixed())
    swaption_vol = ql.ConstantSwaptionVolatility(
        ref,
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        0.20,
        ql.Actual365Fixed(),
    )
    optionlet_vol = ql.ConstantOptionletVolatility(
        ref,
        calendar,
        ql.BusinessDayConvention.ModifiedFollowing,
        0.20,
        ql.Actual365Fixed(),
    )
    swap_index = ql.EuriborSwapIsdaFixA(ql.Period(1, ql.TimeUnit.Years))
    ibor = ql.Euribor6M(yts)
    return ref, calendar, yts, swaption_vol, optionlet_vol, swap_index, ibor


def _mf_settings(money: list[float]) -> ql.MarkovFunctionalModelSettings:
    return (
        ql.MarkovFunctionalModelSettings()
        .with_y_grid_points(64)
        .with_y_std_devs(7.0)
        .with_gauss_hermite_points(32)
        .with_digital_gap(1e-5)
        .with_market_rate_accuracy(1e-7)
        .with_lower_rate_bound(0.0)
        .with_upper_rate_bound(2.0)
        .with_smile_moneyness_checkpoints(money)
    )


def _expiries_cal_basket1(ref: ql.Date, calendar: ql.Calendar) -> list[ql.Date]:
    return [calendar.advance(ref, i, ql.TimeUnit.Years) for i in range(1, 6)]


def _tenors_cal_basket1() -> list[ql.Period]:
    return [ql.Period(10, ql.TimeUnit.Years)] * 5


def _expiries_cal_basket2(ref: ql.Date, calendar: ql.Calendar) -> list[ql.Date]:
    return [
        calendar.advance(ref, months, ql.TimeUnit.Months) for months in range(6, 66, 6)
    ]


def test_markov_functional_swaption_engine_matches_black_flat():
    # MarkovFunctionalTests::testVanillaEngines — basket 1 / flat term structures
    tol = 1.0e-4
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, swaption_vol, _, swap_index, ibor = _flat_market()
    settings = _mf_settings(money)
    mf = ql.MarkovFunctional(
        yts,
        0.01,
        [],
        [1.0],
        swaption_vol,
        _expiries_cal_basket1(ref, calendar),
        _tenors_cal_basket1(),
        swap_index,
        settings,
    )
    outputs = mf.model_outputs()
    assert len(outputs.expiries) > 0
    assert len(outputs.smile_strikes) == len(outputs.expiries)

    for i in range(len(outputs.expiries)):
        expiry = outputs.expiries[i]
        tenor = outputs.tenors[i]
        effective = calendar.advance(expiry, 2, ql.TimeUnit.Days)
        for j, strike in enumerate(outputs.smile_strikes[i]):
            call_swap = ql.make_vanilla_swap(
                tenor,
                ibor,
                strike,
                effective,
                type=ql.SwapType.Payer,
            )
            put_swap = ql.make_vanilla_swap(
                tenor,
                ibor,
                strike,
                effective,
                type=ql.SwapType.Receiver,
            )
            exercise = ql.EuropeanExercise(expiry)
            swaption_c = ql.Swaption(call_swap, exercise)
            swaption_p = ql.Swaption(put_swap, exercise)
            swaption_c.set_pricing_engine(yts, swaption_vol)
            swaption_p.set_pricing_engine(yts, swaption_vol)
            black_call = swaption_c.NPV()
            black_put = swaption_p.NPV()
            swaption_c.set_gaussian1d_pricing_engine(mf)
            swaption_p.set_gaussian1d_pricing_engine(mf)
            assert swaption_c.NPV() == pytest.approx(black_call, abs=tol)
            assert swaption_p.NPV() == pytest.approx(black_put, abs=tol)


def test_markov_functional_capfloor_engine_matches_black_flat():
    # MarkovFunctionalTests::testVanillaEngines — basket 2 / flat term structures
    tol = 1.0e-4
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, _, optionlet_vol, _, ibor = _flat_market()
    settings = (
        ql.MarkovFunctionalModelSettings()
        .with_y_grid_points(64)
        .with_y_std_devs(7.0)
        .with_gauss_hermite_points(16)
        .with_digital_gap(1e-5)
        .with_market_rate_accuracy(1e-7)
        .with_lower_rate_bound(0.0)
        .with_upper_rate_bound(2.0)
        .with_smile_moneyness_checkpoints(money)
    )
    mf = ql.MarkovFunctional(
        yts,
        0.01,
        [],
        [1.0],
        optionlet_vol,
        _expiries_cal_basket2(ref, calendar),
        ibor,
        settings,
    )
    assert len(mf.model_outputs().expiries) == 10

    strikes = (0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10)
    for strike in strikes:
        cap = ql.make_cap(
            ql.Period(5, ql.TimeUnit.Years), ibor, strike, nominal=1.0
        )
        cap.set_pricing_engine(yts, optionlet_vol)
        black_price = cap.NPV()
        cap.set_gaussian1d_pricing_engine(mf)
        assert cap.NPV() == pytest.approx(black_price, abs=tol)

        floor = ql.make_floor(
            ql.Period(5, ql.TimeUnit.Years), ibor, strike, nominal=1.0
        )
        floor.set_pricing_engine(yts, optionlet_vol)
        black_price = floor.NPV()
        floor.set_gaussian1d_pricing_engine(mf)
        assert floor.NPV() == pytest.approx(black_price, abs=tol)


def test_compat_phase166_aliases():
    import qlnb.compat as cql

    assert cql.MarkovFunctional is not None
    assert cql.MarkovFunctionalModelSettings is not None
    assert cql.ConstantOptionletVolatility is not None
    assert hasattr(cql.MarkovFunctionalModelSettings, "withYGridPoints")
