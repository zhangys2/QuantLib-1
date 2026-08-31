"""Phase-119 tests: FFTVarianceGammaEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase119():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 0)


_PROCESS_0 = dict(s=6000.0, q=0.00, r=0.05, sigma=0.20, nu=0.05, theta=-0.50)
_GOLDEN_0_ATM = 687.2032
_GOLDEN_0_PUT = 234.4870


def _vg_market(params: dict):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    spot = ql.QuoteHandle(ql.SimpleQuote(params["s"]))
    q_ts = ql.FlatForward(today, params["q"], dc)
    r_ts = ql.FlatForward(today, params["r"], dc)
    process = ql.VarianceGammaProcess(
        spot,
        q_ts,
        r_ts,
        params["sigma"],
        params["nu"],
        params["theta"],
    )
    return today, process


def _call(today, strike: float) -> ql.EuropeanOption:
    return ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(today + int(round(1.0 * 360))),
    )


def test_fft_variance_gamma_single_option():
    today, process = _vg_market(_PROCESS_0)
    opt = _call(today, 6000.0)
    opt.set_fft_variance_gamma_pricing_engine(process)
    assert opt.NPV() == pytest.approx(_GOLDEN_0_ATM, abs=0.01)


def test_fft_variance_gamma_batch_precalculate():
    # VarianceGammaTests::testVarianceGamma — FFT batch path.
    today, process = _vg_market(_PROCESS_0)
    strikes = [5550.0, 5750.0, 6000.0, 6250.0, 6500.0]
    expected = [955.1637, 829.4197, 687.2032, 561.9416, 453.4700]
    options = [_call(today, k) for k in strikes]
    put = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 5550.0),
        ql.EuropeanExercise(today + int(round(1.0 * 360))),
    )
    options.append(put)
    expected.append(_GOLDEN_0_PUT)

    engine = ql.FFTVarianceGammaEngine(process)
    engine.precalculate(options)
    for opt, golden in zip(options, expected, strict=True):
        opt.set_fft_variance_gamma_pricing_engine(engine)
        assert opt.NPV() == pytest.approx(golden, abs=0.01)


def test_fft_matches_analytic_variance_gamma():
    today, process = _vg_market(_PROCESS_0)
    opt_fft = _call(today, 6100.0)
    opt_fft.set_fft_variance_gamma_pricing_engine(process)
    opt_analytic = _call(today, 6100.0)
    opt_analytic.set_variance_gamma_pricing_engine(process)
    assert opt_fft.NPV() == pytest.approx(opt_analytic.NPV(), abs=0.01)


def test_compat_phase119_aliases():
    import qlnb.compat as c

    assert ql.FFTVarianceGammaEngine is not None
    assert hasattr(c.EuropeanOption, "setFftVarianceGammaPricingEngine")
