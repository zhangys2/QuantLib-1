"""Phase-167 tests: MarkovFunctional calibration diagnostics."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase167():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 38)


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
    return ref, calendar, yts, swaption_vol, optionlet_vol, swap_index


def _expiries_cal_basket1(ref: ql.Date, calendar: ql.Calendar) -> list[ql.Date]:
    return [calendar.advance(ref, i, ql.TimeUnit.Years) for i in range(1, 6)]


def _tenors_cal_basket1() -> list[ql.Period]:
    return [ql.Period(10, ql.TimeUnit.Years)] * 5


def _expiries_cal_basket2(ref: ql.Date, calendar: ql.Calendar) -> list[ql.Date]:
    return [
        calendar.advance(ref, months, ql.TimeUnit.Months) for months in range(6, 66, 6)
    ]


def _assert_calibration_outputs(outputs: ql.MarkovFunctionalModelOutputs, tol0: float, tol1: float) -> None:
    for i in range(len(outputs.expiries)):
        assert outputs.market_zerorate[i] == pytest.approx(
            outputs.model_zerorate[i], abs=tol0
        )
    for i in range(len(outputs.expiries)):
        for j in range(len(outputs.smile_strikes[i])):
            assert outputs.market_call_premium[i][j] == pytest.approx(
                outputs.model_call_premium[i][j], abs=tol1
            )
            assert outputs.market_put_premium[i][j] == pytest.approx(
                outputs.model_put_premium[i][j], abs=tol1
            )


def test_swaption_calibration_flat_basket1():
    # MarkovFunctionalTests::testCalibrationOneInstrumentSet — basket 1 / flat
    tol0 = tol1 = 1.0e-4
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, swaption_vol, _, swap_index = _flat_market()
    settings = (
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
    _assert_calibration_outputs(mf.model_outputs(), tol0, tol1)


def test_caplet_calibration_flat_basket2():
    # MarkovFunctionalTests::testCalibrationOneInstrumentSet — basket 2 / flat
    tol0 = tol1 = 1.0e-4
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, _, optionlet_vol, _ = _flat_market()
    ibor = ql.Euribor6M()
    settings = (
        ql.MarkovFunctionalModelSettings()
        .with_y_grid_points(64)
        .with_y_std_devs(7.0)
        .with_gauss_hermite_points(32)
        .with_digital_gap(1e-5)
        .with_market_rate_accuracy(1e-7)
        .with_lower_rate_bound(0.0)
        .with_upper_rate_bound(2.0)
        .with_adjustments(ql.MarkovFunctionalAdjustment.AdjustNone)
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
    _assert_calibration_outputs(mf.model_outputs(), tol0, tol1)


def test_compat_phase167_aliases():
    import qlnb.compat as cql

    outputs = cql.MarkovFunctionalModelOutputs
    assert outputs is not None
