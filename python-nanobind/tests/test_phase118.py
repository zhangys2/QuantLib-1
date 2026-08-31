"""Phase-118 tests: VarianceGammaProcess + VarianceGammaEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase118():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (2, 9)


# VarianceGammaTests::testVarianceGamma — first process / ATM call & OTM put.
_PROCESS_0 = dict(s=6000.0, q=0.00, r=0.05, sigma=0.20, nu=0.05, theta=-0.50)
_PROCESS_1 = dict(s=6000.0, q=0.02, r=0.05, sigma=0.15, nu=0.01, theta=-0.50)

# Suite results[0][9] ATM call 6000, results[0][21] put 5550, results[1][9] ATM.
_GOLDEN_0_ATM = 687.2032
_GOLDEN_0_PUT = 234.4870
_GOLDEN_1_ATM = 457.9064


def _vg_market(params: dict):
    # Suite uses Date::todaysDate() + Actual360 flat curves.
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


def test_variance_gamma_atm_call_process0():
    today, process = _vg_market(_PROCESS_0)
    exercise = ql.EuropeanExercise(today + int(round(1.0 * 360)))
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 6000.0), exercise
    )
    opt.set_variance_gamma_pricing_engine(process)
    assert opt.NPV() == pytest.approx(_GOLDEN_0_ATM, abs=0.01)
    assert process.sigma() == pytest.approx(0.20)
    assert process.nu() == pytest.approx(0.05)
    assert process.theta() == pytest.approx(-0.50)


def test_variance_gamma_put_and_second_process():
    today, process0 = _vg_market(_PROCESS_0)
    put = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 5550.0),
        ql.EuropeanExercise(today + int(round(1.0 * 360))),
    )
    put.set_variance_gamma_pricing_engine(process0)
    assert put.NPV() == pytest.approx(_GOLDEN_0_PUT, abs=0.01)

    today1, process1 = _vg_market(_PROCESS_1)
    call = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 6000.0),
        ql.EuropeanExercise(today1 + int(round(1.0 * 360))),
    )
    call.set_variance_gamma_pricing_engine(process1)
    assert call.NPV() == pytest.approx(_GOLDEN_1_ATM, abs=0.01)


def test_variance_gamma_strike_grid_sample():
    # Spot-check a few more strikes from results[0] (tol 0.01).
    today, process = _vg_market(_PROCESS_0)
    samples = [
        (5550.0, 955.1637),
        (5750.0, 829.4197),
        (6250.0, 561.9416),
        (6500.0, 453.4700),
    ]
    for strike, expected in samples:
        opt = ql.EuropeanOption(
            ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
            ql.EuropeanExercise(today + int(round(1.0 * 360))),
        )
        opt.set_variance_gamma_pricing_engine(process)
        assert opt.NPV() == pytest.approx(expected, abs=0.01), strike


def test_compat_phase118_aliases():
    import qlnb.compat as c

    assert c.VarianceGammaProcess is not None or hasattr(ql, "VarianceGammaProcess")
    assert hasattr(c.EuropeanOption, "setVarianceGammaPricingEngine")
