"""Phase-182 tests: market-model covariance (FlatVol / AbcdVol)."""

from __future__ import annotations

import numpy as np

import qlnb as ql


def test_version_is_phase182():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 53)


def _matrix_to_numpy(matrix: ql.Matrix) -> np.ndarray:
    rows, cols = matrix.rows(), matrix.columns()
    return np.array([[matrix.at(i, j) for j in range(cols)] for i in range(rows)])


def _check_model_covariance(model, rate_times, evolution_times, corr_matrix, label: str):
    tol = 1e-14
    c = _matrix_to_numpy(corr_matrix)
    n = len(rate_times)
    for step, evol_time in enumerate(evolution_times):
        dt = evol_time - (evolution_times[step - 1] if step > 0 else 0.0)
        cov = _matrix_to_numpy(model.covariance(step))
        for x in range(n - 1):
            for y in range(n - 1):
                if min(rate_times[x], rate_times[y]) >= evol_time:
                    expected = c[x, y] * dt
                    assert abs(cov[x, y] - expected) <= tol, (
                        f"{label} step {step} ({x},{y}): "
                        f"expected {expected}, got {cov[x, y]}"
                    )


def test_market_model_covariance():
    # MarketModelTests::testCovariance
    n = 10
    rate_times = [float(i) for i in range(1, n + 1)]
    evolution_schedules = [
        [float(n - 1)],
        [float(i) for i in range(1, n)],
        [0.5 * i for i in range(1, 2 * n - 1)],
        [0.3, 1.3, 2.0, 4.5, 8.2],
    ]
    corr_matrix = ql.exponential_correlations(rate_times, 0.5, 0.2, 1.0, 0.0)
    correlation = ql.time_homogeneous_forward_correlation(corr_matrix, rate_times)
    ks = [1.0] * (n - 1)
    displ = [0.0] * (n - 1)
    rates = [0.0] * (n - 1)
    vols = [1.0] * (n - 1)

    for evolution_times in evolution_schedules:
        evolution = ql.EvolutionDescription(rate_times, evolution_times)
        flat = ql.FlatVol(
            vols, correlation, evolution, n - 1, rates, displ
        )
        _check_model_covariance(
            flat, rate_times, evolution_times, corr_matrix, "FlatVol"
        )

        abcd = ql.AbcdVol(
            1.0, 0.0, 1.0e-50, 0.0, ks, correlation, evolution, n - 1, rates, displ
        )
        _check_model_covariance(
            abcd, rate_times, evolution_times, corr_matrix, "AbcdVol"
        )


def test_compat_phase182_aliases():
    import qlnb.compat as cql

    assert cql.exponential_correlations is not None
    assert cql.time_homogeneous_forward_correlation is not None
    assert cql.EvolutionDescription is not None
    assert cql.FlatVol is not None
    assert cql.AbcdVol is not None
