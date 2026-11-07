"""Phase-192 tests: AbcdFunction instantaneous volatility."""

from __future__ import annotations

import math

import qlnb as ql

PARAM_SETS = (
    (-0.0597, 0.1677, 0.5403, 0.1710),  # typical calibrated
    (-0.1, 0.3, 1.2, 0.2),  # different shape: faster decay, larger b
)


def abcd_ref(a, b, c, d, tau):
    """Closed-form (a + b*tau)*exp(-c*tau) + d, zero for tau < 0."""
    return 0.0 if tau < 0.0 else (a + b * tau) * math.exp(-c * tau) + d


def test_version_is_phase192():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 63)


def test_instantaneous_variance_is_volatility_squared():
    a, b, c, d = -0.0597, 0.1677, 0.5403, 0.1710
    f = ql.AbcdFunction(a, b, c, d)
    tol = 1e-14
    for t in (0.0, 0.5, 1.0, 2.0):
        for T in (1.0, 2.0, 3.0, 5.0):
            vol = f.instantaneous_volatility(t, T)
            var = f.instantaneous_variance(t, T)
            assert abs(var - vol * vol) <= tol


def test_instantaneous_covariance_matches_product():
    a, b, c, d = -0.0597, 0.1677, 0.5403, 0.1710
    f = ql.AbcdFunction(a, b, c, d)
    tol = 1e-14
    for u in (0.0, 0.25, 1.0):
        for T in (1.0, 2.0, 4.0):
            for S in (1.0, 3.0, 5.0):
                cov = f.instantaneous_covariance(u, T, S)
                product = f.instantaneous_volatility(u, T) * f.instantaneous_volatility(
                    u, S
                )
                assert abs(cov - product) <= tol


def test_compat_phase192_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.AbcdFunction, "instantaneousVolatility")
    assert hasattr(cql.AbcdFunction, "instantaneousVariance")
    assert hasattr(cql.AbcdFunction, "instantaneousCovariance")


def test_instantaneous_volatility_closed_form():
    # Independent reference: vol(u, T) = sqrt(f(T-u)^2) = |f(T - u)|, f(tau) = (a+b*tau)e^{-c*tau}+d.
    # Asymmetric (u, T) pairs so a swapped argument order would be caught.
    for a, b, c, d in PARAM_SETS:
        f = ql.AbcdFunction(a, b, c, d)
        for u, T in ((0.0, 1.0), (0.5, 2.0), (0.25, 5.0), (1.0, 1.0), (1.0, 3.5)):
            expected = abs(abcd_ref(a, b, c, d, T - u))
            assert abs(f.instantaneous_volatility(u, T) - expected) <= 1e-14
            assert abs(f.instantaneous_variance(u, T) - expected**2) <= 1e-14
    # Argument order matters: (u, T) != (T, u) when u != T.
    f = ql.AbcdFunction(*PARAM_SETS[0])
    assert f.instantaneous_volatility(0.5, 2.0) != f.instantaneous_volatility(2.0, 0.5)


def test_instantaneous_covariance_closed_form():
    for a, b, c, d in PARAM_SETS:
        f = ql.AbcdFunction(a, b, c, d)
        for u, T, S in ((0.0, 1.0, 3.0), (0.25, 2.0, 5.0), (1.0, 4.0, 1.5)):
            expected = abcd_ref(a, b, c, d, T - u) * abcd_ref(a, b, c, d, S - u)
            assert abs(f.instantaneous_covariance(u, T, S) - expected) <= 1e-14
            # symmetric in (T, S)
            assert (
                abs(f.instantaneous_covariance(u, S, T) - expected) <= 1e-14
            )


def test_instantaneous_after_fixing_is_zero():
    # u > T (or u > S for covariance): AbcdMathFunction is 0 for tau < 0.
    for a, b, c, d in PARAM_SETS:
        f = ql.AbcdFunction(a, b, c, d)
        for u, T in ((1.5, 1.0), (3.0, 2.0), (10.0, 0.5)):
            assert f.instantaneous_volatility(u, T) == 0.0
            assert f.instantaneous_variance(u, T) == 0.0
        # covariance vanishes if either rate has already fixed
        assert f.instantaneous_covariance(2.0, 1.0, 3.0) == 0.0
        assert f.instantaneous_covariance(2.0, 3.0, 1.0) == 0.0
        assert f.instantaneous_covariance(2.0, 1.0, 1.5) == 0.0
        # boundary u == T is still alive: f(0) = a + d
        assert abs(f.instantaneous_volatility(1.0, 1.0) - abs(a + d)) <= 1e-14
