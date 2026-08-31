"""Phase-180 tests: multi-dimensional linear least-squares regression."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase180():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 51)


def test_multi_dim_linear_regression():
    # LinearLeastSquaresRegressionTests::testMultiDimRegression (intercept path)
    x = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [2.0, 1.0, 0.5, 0.0],
        [1.0, 2.0, 0.5, 0.25],
        [0.5, 0.5, 1.0, 0.5],
        [1.5, 0.0, 0.5, 1.0],
        [0.0, 2.0, 1.0, 0.5],
    ]
    coeff = [0.5, 1.25, -0.75, 0.4, 0.2]
    y = [
        coeff[0]
        + coeff[1] * row[0]
        + coeff[2] * row[1]
        + coeff[3] * row[2]
        + coeff[4] * row[3]
        for row in x
    ]

    model = ql.LinearRegression(x, y, intercept=1.0)
    assert model.dim() == 5
    assert model.size() == len(x)

    calculated = model.coefficients()
    for i in range(5):
        assert calculated[i] == pytest.approx(coeff[i], abs=1e-12)


def test_compat_phase180_multidim_regression():
    import qlnb.compat as cql

    assert cql.LinearRegression is not None
