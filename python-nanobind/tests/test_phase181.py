"""Phase-181 tests: custom-basis linear least-squares regression."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase181():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 52)


def _expected_y(x: float, coeff: list[float]) -> float:
    return (
        coeff[0]
        + coeff[1] * x
        + coeff[2] * x * x
        + coeff[3] * math.sin(x)
    )


def test_regression_with_named_basis():
    # LinearLeastSquaresRegressionTests::testRegression (basis v)
    coeff = [0.5, 1.2, -0.3, 0.8]
    x = [0.15, 0.42, 0.88, 1.25, 1.70, 2.05, 2.60, 3.05, 3.40]
    y = [_expected_y(v, coeff) for v in x]
    basis = ["const", "x", "x2", "sin"]

    model = ql.linear_regression_with_basis(x, y, basis)
    assert model.dim() == 4
    calculated = model.coefficients()
    for i in range(4):
        assert calculated[i] == pytest.approx(coeff[i], abs=1e-12)


def test_regression_with_duplicate_basis_term():
    # LinearLeastSquaresRegressionTests::testRegression (basis w)
    coeff = [0.25, -0.4, 0.65, 0.15]
    x = [0.20, 0.55, 0.95, 1.35, 1.85, 2.35, 2.75, 3.15]
    y = [_expected_y(v, coeff) for v in x]
    basis = ["const", "x", "x2", "sin", "x2"]

    model = ql.linear_regression_with_basis(x, y, basis)
    assert model.dim() == 5
    calculated = model.coefficients()
    merged = [
        calculated[0],
        calculated[1],
        calculated[2] + calculated[4],
        calculated[3],
    ]
    for i in range(4):
        assert merged[i] == pytest.approx(coeff[i], abs=1e-12)


def test_compat_phase181_aliases():
    import qlnb.compat as cql

    assert cql.linear_regression_with_basis is not None
