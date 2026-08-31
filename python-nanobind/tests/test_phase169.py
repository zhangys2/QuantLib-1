"""Phase-169 tests: MarkovFunctional Bermudan swaption on md0 market."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase169():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 40)


def _expiries_cal_basket3(ref: ql.Date, calendar: ql.Calendar) -> list[ql.Date]:
    return [calendar.advance(ref, i, ql.TimeUnit.Years) for i in range(1, 10)]


def _tenors_cal_basket3() -> list[ql.Period]:
    return [ql.Period(y, ql.TimeUnit.Years) for y in range(9, 0, -1)]


def test_bermudan_swaption_md0_market():
    # MarkovFunctionalTests::testBermudanSwaption
    tol0 = 0.0001  # 1bp tolerance against cached values
    cached_european = [
        0.0030757,
        0.0107344,
        0.0179862,
        0.0225881,
        0.0243215,
        0.0229148,
        0.0191415,
        0.0139035,
        0.0076354,
    ]
    cached_bermudan = 0.0327776

    ref = ql.Date(14, ql.Month.November, 2012)
    ql.set_evaluation_date(ref)
    calendar = ql.TARGET()

    yts = ql.markov_functional_test_md0_yts()
    swaption_vol = ql.markov_functional_test_md0_swaption_vts()
    swap_index = ql.EuriborSwapIsdaFixA(ql.Period(1, ql.TimeUnit.Years))
    ibor = ql.Euribor6M(yts)

    settings = (
        ql.MarkovFunctionalModelSettings()
        .with_y_grid_points(32)
        .with_y_std_devs(7.0)
        .with_gauss_hermite_points(16)
        .with_market_rate_accuracy(1e-7)
        .with_digital_gap(1e-5)
        .with_lower_rate_bound(0.0)
        .with_upper_rate_bound(2.0)
    )
    mf = ql.MarkovFunctional(
        yts,
        0.01,
        [],
        [1.0],
        swaption_vol,
        _expiries_cal_basket3(ref, calendar),
        _tenors_cal_basket3(),
        swap_index,
        settings,
    )

    effective = calendar.advance(ref, 2, ql.TimeUnit.Days)
    underlying = ql.make_vanilla_swap(
        ql.Period(10, ql.TimeUnit.Years),
        ibor,
        0.03,
        effective,
    )

    expiries = _expiries_cal_basket3(ref, calendar)
    for i, expiry in enumerate(expiries):
        european = ql.Swaption(
            underlying,
            ql.EuropeanExercise(expiry),
        )
        european.set_gaussian1d_pricing_engine(mf)
        npv = european.NPV()
        assert abs(npv - cached_european[i]) <= tol0, (
            f"European swaption {i}: {npv} vs {cached_european[i]}"
        )

    bermudan = ql.Swaption(underlying, ql.BermudanExercise(expiries))
    bermudan.set_gaussian1d_pricing_engine(mf)
    npv = bermudan.NPV()
    assert abs(npv - cached_bermudan) <= tol0


def test_compat_phase169_aliases():
    import qlnb.compat as cql

    assert callable(cql.markovFunctionalTestMd0Yts)
    assert callable(cql.markovFunctionalTestMd0SwaptionVts)
