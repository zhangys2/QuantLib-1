"""Phase-178 tests: 1D linear least-squares regression."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase178():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 49)


def test_1d_linear_regression():
    # LinearLeastSquaresRegressionTests::test1dLinearRegression
    x = [2.4, 1.8, 2.5, 3.0, 2.1, 1.2, 2.0, 2.7, 3.6]
    y = [7.8, 5.5, 8.0, 9.0, 6.5, 4.0, 6.3, 8.4, 10.2]
    tol = 0.0002
    coeff_expected = [0.9448, 2.6853]
    errors_expected = [0.3654, 0.1487]

    model = ql.LinearRegression(x, y)
    coeffs = model.coefficients()
    errors = model.standard_errors()

    assert model.dim() == 2
    assert model.size() == len(x)

    for i in range(2):
        assert coeffs[i] == pytest.approx(coeff_expected[i], abs=tol)
        assert errors[i] == pytest.approx(errors_expected[i], abs=tol)


def test_compat_phase178_aliases():
    import qlnb.compat as cql

    assert cql.LinearRegression is not None
    assert hasattr(cql.LinearRegression, "standardErrors")
    assert hasattr(cql.LinearRegression, "coefficients")
