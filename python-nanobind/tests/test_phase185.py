"""Phase-185 tests: LMM drift calculator."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase185():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 56)


def _drift_calculator_setup():
    n = 10
    rate_times = [float(i) for i in range(1, n + 1)]
    evolution_times = [float(i) for i in range(1, n)]
    evolution = ql.EvolutionDescription(rate_times, evolution_times)
    corr_matrix = ql.exponential_correlations(rate_times, 0.5, 0.2, 1.0, 0.0)
    correlation = ql.time_homogeneous_forward_correlation(corr_matrix, rate_times)
    forwards = [0.03 + 0.001 * i for i in range(n - 1)]
    displacements = [0.0] * (n - 1)
    vols = [1.0] * (n - 1)
    return evolution, correlation, forwards, displacements, vols


def _assert_plain_matches_reduced(model, evolution, forwards, measure_offset=5):
    tolerance = 1e-16
    rate_taus = evolution.rate_taus()
    numeraires = ql.money_market_plus_measure(evolution, measure_offset)
    alive = evolution.first_alive_rate()
    number_of_steps = evolution.number_of_steps()

    for step in range(number_of_steps):
        pseudo = model.pseudo_root(step)
        displacements = model.displacements()
        inf = max(0, alive[step])
        for h in range(inf, len(numeraires)):
            calc = ql.LMMDriftCalculator(
                pseudo, displacements, rate_taus, numeraires[h], alive[step]
            )
            plain = calc.compute_plain(forwards)
            reduced = calc.compute_reduced(forwards)
            for i, (p, r) in enumerate(zip(plain, reduced, strict=True)):
                assert abs(r - p) <= tolerance, (
                    f"step={step}, numeraire={h}, drift={i}: "
                    f"plain={p}, reduced={r}"
                )


def test_drift_calculator_flat_vol():
    evolution, correlation, forwards, displacements, vols = _drift_calculator_setup()
    model = ql.FlatVol(
        vols, correlation, evolution, len(forwards), forwards, displacements
    )
    _assert_plain_matches_reduced(model, evolution, forwards)


def test_drift_calculator_abcd_vol():
    evolution, correlation, forwards, displacements, vols = _drift_calculator_setup()
    model = ql.AbcdVol(
        0.0,
        0.0,
        1.0,
        1.0,
        vols,
        correlation,
        evolution,
        len(forwards),
        forwards,
        displacements,
    )
    _assert_plain_matches_reduced(model, evolution, forwards)


def test_compat_phase185_aliases():
    import qlnb.compat as cql

    assert cql.LMMDriftCalculator is not None
    assert hasattr(cql.LMMDriftCalculator, "computePlain")
    assert hasattr(cql.LMMDriftCalculator, "computeReduced")
    assert hasattr(cql.EvolutionDescription, "rateTaus")
    assert hasattr(cql.EvolutionDescription, "firstAliveRate")
    assert hasattr(cql.FlatVol, "displacements")
