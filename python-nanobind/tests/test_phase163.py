"""Phase-163 tests: LMM covariance model introspection."""

from __future__ import annotations

import math

import numpy as np
import pytest

import qlnb as ql


def test_version_is_phase163():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 34)


def _matrix_to_numpy(matrix: ql.Matrix) -> np.ndarray:
    rows, cols = matrix.rows(), matrix.columns()
    return np.array([[matrix.at(i, j) for j in range(cols)] for i in range(rows)])


def _lfm_index():
    today = ql.Date(4, ql.Month.September, 2005)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    today = calendar.adjust(today)
    ql.set_evaluation_date(today)
    dates = [
        ql.Date(4, ql.Month.September, 2005),
        ql.Date(4, ql.Month.September, 2018),
    ]
    rates = [0.039, 0.041]
    dc = ql.Actual360()
    index = ql.Euribor6M(ql.ZeroCurve(dates, rates, dc))
    start = index.fixing_calendar().advance(
        today, index.fixing_days(), ql.TimeUnit.Days
    )
    dates[0] = start
    curve = ql.ZeroCurve(dates, rates, dc)
    return ql.Euribor6M(curve)


def test_lmm_correlation_pseudo_sqrt_reconstruction():
    # LiborMarketModelTests::testSimpleCovarianceModels (correlation block)
    size = 10
    tolerance = 1e-14
    corr_model = ql.LmExponentialCorrelationModel(size, 0.1)
    corr = _matrix_to_numpy(corr_model.correlation(0.0))
    pseudo = _matrix_to_numpy(corr_model.pseudo_sqrt(0.0))
    recon = corr - pseudo @ pseudo.T
    assert np.max(np.abs(recon)) < tolerance


def test_lmm_covariance_proxy_and_volatility():
    # LiborMarketModelTests::testSimpleCovarianceModels (covariance/vol block)
    size = 10
    tolerance = 1e-14
    fixing_times = [0.5 * i for i in range(size)]
    a, b, c, d = 0.2, 0.1, 2.1, 0.3

    corr_model = ql.LmExponentialCorrelationModel(size, 0.1)
    vola_model = ql.LmLinearExponentialVolatilityModel(fixing_times, a, b, c, d)
    covar_proxy = ql.LfmCovarianceProxy(vola_model, corr_model)
    index = _lfm_index()
    process = ql.LiborForwardModelProcess(size, index)
    ql.LiborForwardModel(process, vola_model, corr_model)

    t = 0.0
    while t < 4.6:
        cov = _matrix_to_numpy(covar_proxy.covariance(t))
        diff = _matrix_to_numpy(covar_proxy.diffusion(t))
        recon = cov - diff @ diff.T
        assert np.max(np.abs(recon)) < tolerance

        vols = vola_model.volatility(t)
        for k in range(size):
            expected = 0.0
            if k > 2 * t:
                T = fixing_times[k]
                expected = (a * (T - t) + d) * math.exp(-b * (T - t)) + c
            assert vols[k] == pytest.approx(expected, abs=tolerance)

        t += 0.31


def test_compat_phase163_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.LmExponentialCorrelationModel, "correlation")
    assert hasattr(cql.LmExponentialCorrelationModel, "pseudoSqrt")
    assert hasattr(cql.LmLinearExponentialVolatilityModel, "volatility")
    assert hasattr(cql.LfmCovarianceProxy, "covariance")
