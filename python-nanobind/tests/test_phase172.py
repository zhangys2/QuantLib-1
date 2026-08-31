"""Phase-172 tests: MarkovFunctional secondary calibration on md0 market."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase172():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 43)


def _md0_market():
    ref = ql.Date(14, ql.Month.November, 2012)
    ql.set_evaluation_date(ref)
    calendar = ql.TARGET()
    yts = ql.markov_functional_test_md0_yts()
    swaption_vol = ql.markov_functional_test_md0_swaption_vts()
    swap_index = ql.EuriborSwapIsdaFixA(ql.Period(1, ql.TimeUnit.Years))
    ibor = ql.Euribor6M(yts)
    return ref, calendar, yts, swaption_vol, swap_index, ibor


def _expiries_cal_basket1(ref: ql.Date, calendar: ql.Calendar) -> list[ql.Date]:
    return [calendar.advance(ref, i, ql.TimeUnit.Years) for i in range(1, 6)]


def _tenors_cal_basket1() -> list[ql.Period]:
    return [ql.Period(10, ql.TimeUnit.Years)] * 5


def test_secondary_calibration_md0_coterminal_swaptions():
    # MarkovFunctionalTests::testCalibrationTwoInstrumentSets — real md0 basket
    tol1 = 0.1
    money = [0.1, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 2.0, 5.0]
    ref, calendar, yts, swaption_vol, swap_index, ibor = _md0_market()

    vol_step_dates = [
        calendar.advance(ref, years, ql.TimeUnit.Years) for years in range(1, 5)
    ]
    vols = [1.0, 1.0, 1.0, 1.0, 1.0]
    helper_vols = ql.markov_functional_test_md0_coterminal_helper_vols()
    assert len(helper_vols) == 4
    helper_specs = [
        (ql.Period(1, ql.TimeUnit.Years), ql.Period(4, ql.TimeUnit.Years)),
        (ql.Period(2, ql.TimeUnit.Years), ql.Period(3, ql.TimeUnit.Years)),
        (ql.Period(3, ql.TimeUnit.Years), ql.Period(2, ql.TimeUnit.Years)),
        (ql.Period(4, ql.TimeUnit.Years), ql.Period(1, ql.TimeUnit.Years)),
    ]

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
        vol_step_dates,
        vols,
        swaption_vol,
        _expiries_cal_basket1(ref, calendar),
        _tenors_cal_basket1(),
        swap_index,
        settings,
    )

    helpers = []
    for (maturity, length), vol in zip(helper_specs, helper_vols):
        helper = ql.SwaptionHelper(
            maturity,
            length,
            ql.make_quote_handle(vol),
            ibor,
            ql.Period(1, ql.TimeUnit.Years),
            ql.Thirty360(ql.Thirty360Convention.BondBasis),
            ql.Actual360(),
            yts,
        )
        helper.set_gaussian1d_pricing_engine(mf)
        helpers.append(helper)

    om = ql.LevenbergMarquardt()
    ec = ql.EndCriteria(1000, 500, 1e-2, 1e-2, 1e-2)
    mf.calibrate(helpers, om, ec)
    assert len(mf.params()) >= 1

    secondary = [
        (ql.Period(4, ql.TimeUnit.Years), ql.Period(1, ql.TimeUnit.Years)),
        (ql.Period(3, ql.TimeUnit.Years), ql.Period(2, ql.TimeUnit.Years)),
        (ql.Period(2, ql.TimeUnit.Years), ql.Period(3, ql.TimeUnit.Years)),
        (ql.Period(1, ql.TimeUnit.Years), ql.Period(4, ql.TimeUnit.Years)),
    ]
    for i, ((swap_tenor, option_tenor), vol) in enumerate(
        zip(secondary, helper_vols)
    ):
        idx = ql.EuriborSwapIsdaFixA(swap_tenor, yts)
        swaption = ql.make_swaption(idx, option_tenor)
        swaption.set_pricing_engine(yts, vol)
        black_price = swaption.NPV()
        black_vega = swaption.vega()
        swaption.set_gaussian1d_pricing_engine(mf)
        mf_price = swaption.NPV()
        assert abs(black_price - mf_price) / black_vega <= tol1


def test_compat_phase172_aliases():
    import qlnb.compat as cql

    assert callable(cql.markovFunctionalTestMd0CoterminalHelperVols)
