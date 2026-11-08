"""Phase-195 tests: RiskStatistics fed from NumPy arrays.

Empirical golden values come from the official QuantLib SWIG wheel (1.43) for
2000 weighted samples (normal(0.001, 0.02) values, uniform(0.5, 2) weights).
SWIG does not expose percentile or the gaussian* measures, so those are checked
against closed forms and internal consistency.
"""

from __future__ import annotations

import numpy as np
import pytest

import qlnb as ql

N = 2000
VALUES = np.random.default_rng(3).normal(0.001, 0.02, 5000)[:N]
WEIGHTS = np.random.default_rng(4).uniform(0.5, 2.0, 5000)[:N]

GOLDEN = {
    "mean": 0.0015245743117573345,
    "standard_deviation": 0.01978704368494047,
    "variance": 0.00039152709778974247,
    "skewness": -0.018264064550616556,
    "kurtosis": -0.04484292944780455,
    "semi_deviation": 0.019891739009750845,
    "semi_variance": 0.00039568128083204354,
    "downside_deviation": 0.01942615590405906,
    "min": -0.06564162604799724,
    "max": 0.0787291054208216,
    "weight_sum": 2518.96785173734,
    "error_estimate": 0.0004424517475328482,
}


def _stats():
    s = ql.RiskStatistics()
    s.add_values(VALUES, WEIGHTS)
    return s


def test_version_is_phase195():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 66)


@pytest.mark.parametrize("name", sorted(GOLDEN))
def test_moments_match_quantlib(name):
    s = _stats()
    assert getattr(s, name)() == pytest.approx(GOLDEN[name], rel=1e-12)


def test_risk_measures_match_quantlib():
    s = _stats()
    assert s.samples() == N
    assert s.value_at_risk(0.99) == pytest.approx(0.04473445238260173, rel=1e-12)
    assert s.expected_shortfall(0.99) == pytest.approx(0.05235185835823692, rel=1e-12)
    assert s.potential_upside(0.99) == pytest.approx(0.04725942356769778, rel=1e-12)
    assert s.shortfall(-0.02) == pytest.approx(0.1409522350626406, rel=1e-12)
    assert s.average_shortfall(-0.02) == pytest.approx(0.00962736837781171, rel=1e-12)
    assert s.regret(-0.01) == pytest.approx(0.0002441190145947648, rel=1e-12)


def test_bulk_add_equals_one_by_one():
    bulk = _stats()
    one = ql.RiskStatistics()
    for v, w in zip(VALUES, WEIGHTS):
        one.add(float(v), float(w))
    for name in ("mean", "variance", "skewness", "kurtosis", "min", "max", "weight_sum"):
        assert getattr(bulk, name)() == getattr(one, name)()
    assert bulk.value_at_risk(0.95) == one.value_at_risk(0.95)


def test_unweighted_and_scalar_weight():
    a = ql.RiskStatistics()
    a.add_values(VALUES)
    b = ql.RiskStatistics()
    b.add_values(VALUES, 1.0)
    assert a.weight_sum() == N and b.weight_sum() == N
    assert a.mean() == b.mean() == pytest.approx(VALUES.mean(), rel=1e-12)
    assert a.standard_deviation() == pytest.approx(VALUES.std(ddof=1), rel=1e-12)


def test_add_values_accepts_lists_and_continues():
    s = ql.RiskStatistics()
    s.add_values([1.0, 2.0])
    s.add_values([3.0])
    s.add(4.0)
    assert s.samples() == 4 and s.mean() == 2.5
    s.reset()
    assert s.samples() == 0


def test_mismatched_weights_are_rejected():
    s = ql.RiskStatistics()
    with pytest.raises(Exception, match="length"):
        s.add_values([1.0, 2.0, 3.0], [1.0, 2.0])


def test_empirical_percentile_is_a_sample_with_enough_weight_below():
    s = _stats()
    for p in (0.05, 0.5, 0.95):
        q = s.percentile(p)
        assert q in VALUES
        below = WEIGHTS[VALUES <= q].sum()
        assert below >= p * WEIGHTS.sum() - 1e-9
    assert s.top_percentile(0.01) == s.percentile(0.99)


def test_gaussian_measures_match_closed_forms():
    s = _stats()
    mu, sigma = s.mean(), s.standard_deviation()
    z = ql.inverse_cumulative_normal_array([0.01, 0.99, 0.5])
    assert s.gaussian_percentile(0.5) == pytest.approx(mu, rel=1e-12)
    assert s.gaussian_percentile(0.99) == pytest.approx(mu + sigma * z[1], rel=1e-12)
    assert s.gaussian_top_percentile(0.01) == pytest.approx(mu + sigma * z[1], rel=1e-12)
    assert s.gaussian_value_at_risk(0.99) == pytest.approx(-min(mu + sigma * z[0], 0.0), rel=1e-12)
    assert s.gaussian_potential_upside(0.99) == pytest.approx(max(mu + sigma * z[1], 0.0), rel=1e-12)
    assert s.gaussian_expected_shortfall(0.99) >= s.gaussian_value_at_risk(0.99)
    # empirical and Gaussian VaR agree roughly on near-normal data
    assert s.gaussian_value_at_risk(0.99) == pytest.approx(s.value_at_risk(0.99), rel=0.15)
    assert s.gaussian_average_shortfall(-0.02) > 0.0
    assert 0.0 < s.gaussian_shortfall(-0.02) < 1.0


def test_invalid_percentile_is_rejected():
    s = _stats()
    with pytest.raises(Exception):
        s.value_at_risk(0.5)  # QuantLib requires [0.9, 1)
    with pytest.raises(Exception):
        s.gaussian_percentile(1.0)
