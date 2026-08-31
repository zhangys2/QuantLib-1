"""Phase-171 tests: MarkovFunctional vanilla engines on real md0 market."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase171():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 42)


def _md0_market():
    ref = ql.Date(14, ql.Month.November, 2012)
    ql.set_evaluation_date(ref)
    calendar = ql.TARGET()
    yts = ql.markov_functional_test_md0_yts()
    swaption_vol = ql.markov_functional_test_md0_swaption_vts()
    optionlet_vol = ql.markov_functional_test_md0_optionlet_vts()
    swap_index = ql.EuriborSwapIsdaFixA(ql.Period(1, ql.TimeUnit.Years))
    ibor = ql.Euribor6M(yts)
    return ref, calendar, yts, swaption_vol, optionlet_vol, swap_index, ibor


def _mf_settings(money: list[float], *, gh: int = 32) -> ql.MarkovFunctionalModelSettings:
    return (
        ql.MarkovFunctionalModelSettings()
        .with_y_grid_points(64)
        .with_y_std_devs(7.0)
        .with_gauss_hermite_points(gh)
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


def test_swaption_engine_matches_black_md0_basket1():
    # MarkovFunctionalTests::testVanillaEngines — basket 1 / real term structures
    tol = 1.0e-4
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, swaption_vol, _, swap_index, ibor = _md0_market()
    mf = ql.MarkovFunctional(
        yts,
        0.01,
        [],
        [1.0],
        swaption_vol,
        _expiries_cal_basket1(ref, calendar),
        _tenors_cal_basket1(),
        swap_index,
        _mf_settings(money),
    )
    outputs = mf.model_outputs()
    n_strikes = len(outputs.smile_strikes[0])

    for i in range(len(outputs.expiries)):
        expiry = outputs.expiries[i]
        tenor = outputs.tenors[i]
        effective = calendar.advance(expiry, 2, ql.TimeUnit.Days)
        for j in range(n_strikes):
            strike = outputs.smile_strikes[i][j]
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
            smile_corr_call = (
                outputs.market_call_premium[i][j]
                - outputs.market_raw_call_premium[i][j]
            )
            smile_corr_put = (
                outputs.market_put_premium[i][j]
                - outputs.market_raw_put_premium[i][j]
            )
            swaption_c.set_gaussian1d_pricing_engine(mf)
            swaption_p.set_gaussian1d_pricing_engine(mf)
            mf_call = swaption_c.NPV()
            mf_put = swaption_p.NPV()
            assert black_call - mf_call + smile_corr_call == pytest.approx(0.0, abs=tol)
            assert black_put - mf_put + smile_corr_put == pytest.approx(0.0, abs=tol)


def test_capfloor_engine_matches_black_md0_basket2():
    # MarkovFunctionalTests::testVanillaEngines — basket 2 / real term structures
    tol = 1.0e-4
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, _, optionlet_vol, _, ibor = _md0_market()
    mf = ql.MarkovFunctional(
        yts,
        0.01,
        [],
        [1.0],
        optionlet_vol,
        _expiries_cal_basket2(ref, calendar),
        ibor,
        _mf_settings(money),
    )
    assert len(mf.model_outputs().expiries) == 10

    for strike in (0.01, 0.02, 0.03, 0.04, 0.05, 0.06):
        for make_instrument, kind in (
            (ql.make_cap, "cap"),
            (ql.make_floor, "floor"),
        ):
            inst = make_instrument(
                ql.Period(5, ql.TimeUnit.Years), ibor, strike, nominal=1.0
            )
            inst.set_pricing_engine(yts, optionlet_vol)
            black_price = inst.NPV()
            inst.set_gaussian1d_pricing_engine(mf)
            mf_price = inst.NPV()
            assert mf_price == pytest.approx(black_price, abs=tol), kind
