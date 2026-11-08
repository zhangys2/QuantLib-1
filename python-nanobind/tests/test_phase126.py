"""Phase-126 tests: FFTVanillaEngine."""

from __future__ import annotations

import sys

import pytest

import qlnb as ql


def test_version_is_phase126():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 7)


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _european(today: ql.Date, option_type, strike: float, years: int = 1):
    return ql.EuropeanOption(
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + years * 360),
    )


# EuropeanOptionTests::testFFTEngines relativeTol["value"] = 0.01
_REL_TOL = 0.01


@pytest.mark.parametrize("option_type", [ql.OptionType.Call, ql.OptionType.Put])
@pytest.mark.parametrize("strike", [75.0, 100.0, 125.0])
@pytest.mark.parametrize("q,r,vol", [(0.0, 0.05, 0.20), (0.05, 0.01, 0.50)])
def test_fft_vanilla_matches_analytic(option_type, strike, q, r, vol):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, 100.0, q, r, vol)

    analytic = _european(today, option_type, strike)
    analytic.set_pricing_engine(process)
    expected = analytic.NPV()

    fft = _european(today, option_type, strike)
    fft.set_fft_vanilla_pricing_engine(process)
    err = abs(fft.NPV() - expected) / max(expected, 1.0)
    assert err <= _REL_TOL, (option_type, strike, q, r, vol, err)


def test_fft_vanilla_batch_precalculate():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, 100.0, 0.0, 0.05, 0.20)
    strikes = [80.0, 100.0, 120.0]
    options = [_european(today, ql.OptionType.Call, k) for k in strikes]

    engine = ql.FFTVanillaEngine(process)
    engine.precalculate(options)

    for opt, k in zip(options, strikes, strict=True):
        opt.set_fft_vanilla_pricing_engine(engine)
        ref = _european(today, ql.OptionType.Call, k)
        ref.set_pricing_engine(process)
        err = abs(opt.NPV() - ref.NPV()) / max(ref.NPV(), 1.0)
        assert err <= _REL_TOL


def test_native_fft_vanilla_snake_case_only():
    assert hasattr(ql.EuropeanOption, "set_fft_vanilla_pricing_engine")
    assert hasattr(ql, "FFTVanillaEngine")
    assert hasattr(ql.FFTVanillaEngine, "precalculate")
    if "qlnb.compat" in sys.modules:
        pytest.skip("qlnb.compat already loaded; camelCase aliases mutate EuropeanOption")
    assert not hasattr(ql.EuropeanOption, "setFftVanillaPricingEngine")


def test_compat_phase126_aliases():
    import qlnb.compat as c

    assert hasattr(c.EuropeanOption, "setFftVanillaPricingEngine")
    assert c.EuropeanOption.setFftVanillaPricingEngine is (
        ql.EuropeanOption.set_fft_vanilla_pricing_engine
    )
