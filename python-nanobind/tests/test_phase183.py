"""Phase-183 tests: market-model pseudo-root factorization."""

from __future__ import annotations

import numpy as np

import qlnb as ql


def test_version_is_phase183():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 54)


def _matrix_to_numpy(matrix: ql.Matrix) -> np.ndarray:
    rows, cols = matrix.rows(), matrix.columns()
    return np.array([[matrix.at(i, j) for j in range(cols)] for i in range(rows)])


def _make_flat_vol_model(evolution_times: list[float]):
    n = 10
    rate_times = [float(i) for i in range(1, n + 1)]
    corr_matrix = ql.exponential_correlations(rate_times, 0.5, 0.2, 1.0, 0.0)
    correlation = ql.time_homogeneous_forward_correlation(corr_matrix, rate_times)
    evolution = ql.EvolutionDescription(rate_times, evolution_times)
    vols = [1.0] * (n - 1)
    rates = [0.0] * (n - 1)
    displ = [0.0] * (n - 1)
    return ql.FlatVol(vols, correlation, evolution, n - 1, rates, displ)


def test_pseudo_root_reconstructs_covariance():
    # MarketModel pseudoRoot(i) @ pseudoRoot(i).T == covariance(i)
    tol = 1e-14
    evolution_times = [0.5 * i for i in range(1, 19)]
    model = _make_flat_vol_model(evolution_times)
    assert model.number_of_steps() == len(evolution_times)
    assert model.number_of_rates() == 9
    assert model.number_of_factors() == 9

    for step in range(model.number_of_steps()):
        cov = _matrix_to_numpy(model.covariance(step))
        root = _matrix_to_numpy(model.pseudo_root(step))
        recon = root @ root.T
        assert np.max(np.abs(recon - cov)) <= tol


def test_abcd_vol_pseudo_root_reconstructs_covariance():
    tol = 1e-14
    n = 10
    rate_times = [float(i) for i in range(1, n + 1)]
    evolution_times = [float(i) for i in range(1, n)]
    corr_matrix = ql.exponential_correlations(rate_times, 0.5, 0.2, 1.0, 0.0)
    correlation = ql.time_homogeneous_forward_correlation(corr_matrix, rate_times)
    evolution = ql.EvolutionDescription(rate_times, evolution_times)
    ks = [1.0] * (n - 1)
    displ = [0.0] * (n - 1)
    rates = [0.0] * (n - 1)
    model = ql.AbcdVol(
        1.0, 0.0, 1.0e-50, 0.0, ks, correlation, evolution, n - 1, rates, displ
    )

    for step in range(model.number_of_steps()):
        cov = _matrix_to_numpy(model.covariance(step))
        root = _matrix_to_numpy(model.pseudo_root(step))
        assert np.max(np.abs(root @ root.T - cov)) <= tol


def test_compat_phase183_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.FlatVol, "pseudoRoot")
    assert hasattr(cql.FlatVol, "numberOfSteps")
    assert hasattr(cql.AbcdVol, "pseudoRoot")
