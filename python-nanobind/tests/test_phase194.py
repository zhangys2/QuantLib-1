"""Phase-194 tests: bulk QuantLib random-number generation into NumPy arrays.

Golden values were drawn from the official QuantLib SWIG wheel (1.43), so they
pin qlnb to QuantLib's own sequences rather than to NumPy's.
"""

from __future__ import annotations

import numpy as np
import pytest

import qlnb as ql

MT42_UNIFORM = [
    0.37454011442605406,
    0.7965429843170568,
    0.9507143116788939,
    0.18343478778842837,
    0.7319939384469762,
]
MT42_GAUSSIAN = [
    -0.31985239197154675,
    0.8293364834726858,
    1.6518193787298954,
    -0.9023526306658766,
    0.6188546400812096,
]
SOBOL3 = [
    [0.5, 0.5, 0.5],
    [0.75, 0.25, 0.75],
    [0.25, 0.75, 0.25],
    [0.375, 0.375, 0.625],
]
SOBOL3_AT_10 = [0.4375, 0.5625, 0.0625]
HALTON3 = [
    [0.5, 1 / 3, 0.2],
    [0.25, 2 / 3, 0.4],
    [0.75, 1 / 9, 0.6000000000000001],
    [0.125, 4 / 9, 0.8],
]
HALTON3_RANDOM_START = [
    [0.8993458733893931, 0.3001155803323786, 0.40134817103872],
    [0.08684587338939309, 0.633448913665712, 0.60134817103872],
]


def test_version_is_phase194():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 65)


def test_mersenne_twister_matches_quantlib():
    u = ql.MersenneTwisterRng(42).uniform(5)
    assert u.dtype == np.float64 and u.shape == (5,)
    np.testing.assert_array_equal(u, MT42_UNIFORM)
    np.testing.assert_allclose(ql.MersenneTwisterRng(42).gaussian(5), MT42_GAUSSIAN, rtol=1e-12)


def test_mersenne_twister_stream_continues_across_calls():
    rng = ql.MersenneTwisterRng(42)
    first, second = rng.uniform(2), rng.uniform(3)
    np.testing.assert_array_equal(np.concatenate([first, second]), MT42_UNIFORM)
    assert ql.MersenneTwisterRng(42).uniform(0).shape == (0,)


def test_mersenne_twister_is_a_proper_uniform_and_normal_sample():
    u = ql.MersenneTwisterRng(7).uniform(200_000)
    assert 0.0 < u.min() and u.max() < 1.0
    assert u.mean() == pytest.approx(0.5, abs=0.005)
    z = ql.MersenneTwisterRng(7).gaussian(200_000)
    assert z.mean() == pytest.approx(0.0, abs=0.01)
    assert z.std() == pytest.approx(1.0, abs=0.01)


def test_sobol_matches_quantlib():
    seq = ql.SobolSequence(3, 42)
    assert seq.dimension == 3
    pts = seq.uniform(4)
    assert pts.shape == (4, 3)
    np.testing.assert_array_equal(pts, SOBOL3)


def test_sobol_skip_to_and_continuation():
    seq = ql.SobolSequence(3, 42)
    seq.skip_to(10)
    np.testing.assert_array_equal(seq.uniform(1)[0], SOBOL3_AT_10)
    head = ql.SobolSequence(3, 42)
    both = np.vstack([head.uniform(2), head.uniform(2)])
    np.testing.assert_array_equal(both, SOBOL3)


def test_sobol_gaussian_is_inverse_normal_of_uniform():
    g = ql.SobolSequence(3, 42).gaussian(4)
    expected = ql.inverse_cumulative_normal_array(np.array(SOBOL3).ravel()).reshape(4, 3)
    np.testing.assert_array_equal(g, expected)
    assert g[0].tolist() == [0.0, 0.0, 0.0]


def test_halton_matches_quantlib():
    plain = ql.HaltonSequence(3, 0, False, False).uniform(4)
    np.testing.assert_allclose(plain, HALTON3, rtol=1e-15)
    shifted = ql.HaltonSequence(3, 42, True, False).uniform(2)
    np.testing.assert_allclose(shifted, HALTON3_RANDOM_START, rtol=1e-14)
    assert ql.HaltonSequence(3, 0, False, False).dimension == 3


def test_halton_gaussian_is_inverse_normal_of_uniform():
    g = ql.HaltonSequence(3, 0, False, False).gaussian(4)
    expected = ql.inverse_cumulative_normal_array(np.array(HALTON3).ravel()).reshape(4, 3)
    np.testing.assert_allclose(g, expected, rtol=1e-14)


def test_inverse_cumulative_normal_array():
    got = ql.inverse_cumulative_normal_array([0.001, 0.3, 0.5, 0.975])
    np.testing.assert_allclose(
        got,
        [-3.090232304709404, -0.5244005132792953, 0.0, 1.959963986120195],
        rtol=1e-12,
        atol=1e-15,
    )
    shifted = ql.inverse_cumulative_normal_array(0.975, 2.0, 3.0)
    assert shifted[0] == pytest.approx(2.0 + 3.0 * 1.959963986120195, rel=1e-12)


def test_cumulative_normal_array_round_trips():
    x = np.linspace(-4.0, 4.0, 41)
    p = ql.cumulative_normal_array(x)
    assert p[20] == 0.5
    assert ql.cumulative_normal_array(1.0)[0] == pytest.approx(0.841344746068543, rel=1e-12)
    assert ql.cumulative_normal_array(-0.5)[0] == pytest.approx(0.3085375387259869, rel=1e-12)
    np.testing.assert_allclose(ql.inverse_cumulative_normal_array(p), x, atol=1e-9)


def test_invalid_probability_names_the_element():
    with pytest.raises(Exception, match="element 1"):
        ql.inverse_cumulative_normal_array([0.5, 1.5])
