"""Phase-164 tests: MfStateProcess (Markov functional state process)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase164():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 35)


def test_mf_state_process_constant_vol():
    # MarkovFunctionalTests::testMfStateProcess — constant volatility case
    tolerance = 1e-10
    sp = ql.MfStateProcess(0.0, [], [1.0])
    assert sp.variance(0.0, 0.0, 1.0) == pytest.approx(1.0, abs=tolerance)
    assert sp.variance(0.0, 0.0, 2.0) == pytest.approx(2.0, abs=tolerance)


def test_mf_state_process_piecewise_vol_zero_reversion():
    # Piecewise vol schedule, zero reversion
    tolerance = 1e-10
    times = [1.0, 2.0]
    vols = [1.0, 2.0, 3.0]
    sp = ql.MfStateProcess(0.0, times, vols)

    assert sp.diffusion(0.0, 0.0) == pytest.approx(1.0, abs=tolerance)
    assert sp.diffusion(0.99, 0.0) == pytest.approx(1.0, abs=tolerance)
    assert sp.diffusion(1.0, 0.0) == pytest.approx(2.0, abs=tolerance)
    assert sp.diffusion(1.9, 0.0) == pytest.approx(2.0, abs=tolerance)
    assert sp.diffusion(2.0, 0.0) == pytest.approx(3.0, abs=tolerance)
    assert sp.diffusion(3.0, 0.0) == pytest.approx(3.0, abs=tolerance)
    assert sp.diffusion(5.0, 0.0) == pytest.approx(3.0, abs=tolerance)

    assert sp.variance(0.0, 0.0, 0.0) == pytest.approx(0.0, abs=tolerance)
    assert sp.variance(0.0, 0.0, 0.5) == pytest.approx(0.5, abs=tolerance)
    assert sp.variance(0.0, 0.0, 1.0) == pytest.approx(1.0, abs=tolerance)
    assert sp.variance(0.0, 0.0, 1.5) == pytest.approx(3.0, abs=tolerance)
    assert sp.variance(0.0, 0.0, 3.0) == pytest.approx(14.0, abs=tolerance)
    assert sp.variance(0.0, 0.0, 5.0) == pytest.approx(32.0, abs=tolerance)
    assert sp.variance(1.2, 0.0, 1.0) == pytest.approx(5.0, abs=tolerance)


def test_mf_state_process_piecewise_vol_with_reversion():
    # Non-zero reversion (0.01)
    tolerance = 1e-10
    times = [1.0, 2.0]
    vols = [1.0, 2.0, 3.0]
    sp = ql.MfStateProcess(0.01, times, vols)

    assert sp.variance(0.0, 0.0, 0.0) == pytest.approx(0.0, abs=tolerance)
    assert sp.variance(0.0, 0.0, 0.5) == pytest.approx(0.502508354208, abs=tolerance)
    assert sp.variance(0.0, 0.0, 1.0) == pytest.approx(1.01006700134, abs=tolerance)
    assert sp.variance(0.0, 0.0, 1.5) == pytest.approx(3.06070578669, abs=tolerance)
    assert sp.variance(0.0, 0.0, 3.0) == pytest.approx(14.5935513933, abs=tolerance)
    assert sp.variance(0.0, 0.0, 5.0) == pytest.approx(34.0940185819, abs=tolerance)
    assert sp.variance(1.2, 0.0, 1.0) == pytest.approx(5.18130257358, abs=tolerance)


def test_compat_phase164_aliases():
    import qlnb.compat as cql

    assert cql.MfStateProcess is not None
    assert hasattr(cql.MfStateProcess, "stdDeviation")
