"""Phase-176 tests: LMM LowDiscrepancy MC caplet pricing."""

from __future__ import annotations

import numpy as np
import pytest

import qlnb as ql


def test_version_is_phase176():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 47)


def _lmm_process_index():
    today = ql.Date(4, ql.Month.September, 2005)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    today = calendar.adjust(today)
    ql.set_evaluation_date(today)
    dates = [
        ql.Date(4, ql.Month.September, 2005),
        ql.Date(4, ql.Month.September, 2018),
    ]
    rates = [0.01, 0.08]
    dc = ql.Actual360()
    index = ql.Euribor1Y(ql.ZeroCurve(dates, rates, dc))
    start = index.fixing_calendar().advance(
        today, index.fixing_days(), ql.TimeUnit.Days
    )
    dates[0] = start
    curve = ql.ZeroCurve(dates, rates, dc)
    return ql.Euribor1Y(curve), ql.Settings.instance().evaluation_date


def _make_caplet_vol_curve(today: ql.Date):
    length = 10
    helper = ql.LiborForwardModelProcess(length + 1, _lmm_process_index()[0])
    vols = [14.40, 17.15, 16.81, 16.64, 16.17, 15.78, 15.40, 15.21, 14.86, 14.54]
    dates = [helper.fixing_dates()[i + 1] for i in range(length)]
    return ql.CapletVarianceCurve(
        today,
        dates,
        [v / 100.0 for v in vols],
        ql.ActualActual(ql.ActualActualConvention.ISDA),
    )


def _make_hull_white_process(vola_comp: np.ndarray | None = None):
    length = 10
    index, today = _lmm_process_index()
    process = ql.LiborForwardModelProcess(length, index)
    cap_vol = _make_caplet_vol_curve(today)
    if vola_comp is None:
        param = ql.LfmHullWhiteParameterization(process, cap_vol)
    else:
        corr = vola_comp @ vola_comp.T
        rows, cols = corr.shape
        factors = vola_comp.shape[1]
        param = ql.LfmHullWhiteParameterization(
            process,
            cap_vol,
            ql.Matrix(rows, cols, corr.reshape(-1).tolist()),
            factors,
        )
    process.set_covar_param(param)
    return process


def test_mc_caplet_and_ratchet_pricing():
    # LiborMarketModelProcessTests::testMonteCarloCapletPricing
    comp_values = [
        0.85549771, 0.46707264, 0.22353259,
        0.91915359, 0.37716089, 0.11360610,
        0.96438280, 0.26413316, -0.01412414,
        0.97939148, 0.13492952, -0.15028753,
        0.95970595, -0.00000000, -0.28100621,
        0.97939148, -0.13492952, -0.15028753,
        0.96438280, -0.26413316, -0.01412414,
        0.91915359, -0.37716089, 0.11360610,
        0.85549771, -0.46707264, 0.22353259,
    ]
    vola_comp = np.array(comp_values, dtype=float).reshape(9, 3)

    process1 = _make_hull_white_process()
    process2 = _make_hull_white_process(vola_comp)
    tmp = process1.fixing_times()
    grid = ql.TimeGrid(tmp, 12)
    locations = [grid.index(t) for t in tmp]

    gen1 = ql.LowDiscrepancyMultiPathGenerator(process1, grid, seed=42)
    gen2 = ql.LowDiscrepancyMultiPathGenerator(process2, grid, seed=42)

    nr_trails = 250_000
    stat1 = [ql.GeneralStatistics() for _ in range(process1.size())]
    stat2 = [ql.GeneralStatistics() for _ in range(process2.size())]
    stat3 = [ql.GeneralStatistics() for _ in range(process2.size() - 1)]

    accrual_start = process1.accrual_start_times()
    accrual_end = process1.accrual_end_times()
    length = process1.size()

    for _ in range(nr_trails):
        path1 = gen1.next()
        path2 = gen2.next()
        rates1 = [path1[j][locations[j]] for j in range(length)]
        rates2 = [path2[j][locations[j]] for j in range(length)]
        dis1 = process1.discount_bond(rates1)
        dis2 = process2.discount_bond(rates2)

        for k in range(length):
            accrual_period = accrual_end[k] - accrual_start[k]
            payoff1 = max(rates1[k] - 0.04, 0.0) * accrual_period
            payoff2 = max(rates2[k] - 0.04, 0.0) * accrual_period
            stat1[k].add(dis1[k] * payoff1)
            stat2[k].add(dis2[k] * payoff2)
            if k != 0:
                payoff3 = max(rates2[k] - (rates2[k - 1] + 0.0025), 0.0) * accrual_period
                stat3[k - 1].add(dis2[k] * payoff3)

    caplet_npv = [
        0.000000000000,
        0.000002841629,
        0.002533279333,
        0.009577143571,
        0.017746502618,
        0.025216116835,
        0.031608230268,
        0.036645683881,
        0.039792254012,
        0.041829864365,
    ]
    ratchet_npv = [
        0.0082644895,
        0.0082754754,
        0.0082159966,
        0.0082982822,
        0.0083803357,
        0.0084366961,
        0.0084173270,
        0.0081803406,
        0.0079533814,
    ]
    ref_error = 1e-5

    for k in range(length):
        calculated1 = stat1[k].mean()
        tolerance1 = stat1[k].error_estimate()
        assert abs(calculated1 - caplet_npv[k]) <= tolerance1

        calculated2 = stat2[k].mean()
        tolerance2 = stat2[k].error_estimate()
        assert abs(calculated2 - caplet_npv[k]) <= tolerance2

        if k != 0:
            calculated3 = stat3[k - 1].mean()
            tolerance3 = stat3[k - 1].error_estimate() + ref_error
            assert abs(calculated3 - ratchet_npv[k - 1]) <= tolerance3


def test_compat_phase176_aliases():
    import qlnb.compat as cql

    assert cql.LowDiscrepancyMultiPathGenerator is not None
