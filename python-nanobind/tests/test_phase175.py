"""Phase-175 tests: LMM Hull–White lambda bootstrapping."""

from __future__ import annotations

import numpy as np
import pytest

import qlnb as ql


def test_version_is_phase175():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 46)


def _matrix_to_numpy(matrix: ql.Matrix) -> np.ndarray:
    rows, cols = matrix.rows(), matrix.columns()
    return np.array([[matrix.at(i, j) for j in range(cols)] for i in range(rows)])


def _lmm_process_index():
    # LiborMarketModelProcessTests::makeIndex
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
    # LiborMarketModelProcessTests::makeCapVolCurve
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


def _make_hull_white_process():
    length = 10
    index, today = _lmm_process_index()
    process = ql.LiborForwardModelProcess(length, index)
    cap_vol = _make_caplet_vol_curve(today)
    param = ql.LfmHullWhiteParameterization(process, cap_vol)
    process.set_covar_param(param)
    return process, param


def test_lambda_bootstrapping():
    # LiborMarketModelProcessTests::testLambdaBootstrapping
    tolerance = 1e-10
    lambda_expected = [
        14.3010297550,
        19.3821411939,
        15.9816590141,
        15.9953118303,
        14.0570815635,
        13.5687599894,
        12.7477197786,
        13.7056638165,
        11.6191989567,
    ]

    process, param = _make_hull_white_process()
    covar = _matrix_to_numpy(process.covariance(0.0, None, 1.0))

    for i, expected_pct in enumerate(lambda_expected):
        calculated = float(np.sqrt(covar[i + 1, i + 1]))
        assert calculated == pytest.approx(expected_pct / 100.0, abs=tolerance)

    tmp = process.fixing_times()
    grid = ql.TimeGrid(tmp, 14)
    for step in range(grid.size()):
        t = grid[step]
        integrated = _matrix_to_numpy(param.integrated_covariance(t))
        base = _matrix_to_numpy(ql.lfm_base_integrated_covariance(param, t))
        assert np.max(np.abs(integrated - base)) < tolerance


def test_compat_phase175_aliases():
    import qlnb.compat as cql

    assert cql.LfmHullWhiteParameterization is not None
    assert hasattr(cql.LiborForwardModelProcess, "covarParam")
    assert hasattr(cql.LiborForwardModelProcess, "covariance")
    assert hasattr(cql.LfmCovarianceParameterization, "integratedCovariance")
