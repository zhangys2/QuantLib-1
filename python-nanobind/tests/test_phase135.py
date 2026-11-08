"""Phase-135 tests: Merton76Process + JumpDiffusionEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase135():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 6)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


def _merton76(today, spot, q, r, total_vol, jump_intensity, gamma):
    """Build Merton76Process using Haug's gamma / jumpIntensity factorization."""
    dc = ql.Actual360()
    j_vol = total_vol * math.sqrt(gamma / jump_intensity)
    diffusion_vol = total_vol * math.sqrt(1.0 - gamma)
    # Haug assumes zero mean jump.
    mean_jump = 0.0
    mean_log = math.log(1.0 + mean_jump) - 0.5 * j_vol * j_vol
    return ql.Merton76Process(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), diffusion_vol, dc),
        ql.make_quote_handle(jump_intensity),
        ql.make_quote_handle(mean_log),
        ql.make_quote_handle(j_vol),
    )


# Representative Haug Merton cases from JumpDiffusionTests::testMerton76 (tol 1e-2).
_CASES = [
    # option_type, strike, spot, q, r, t, vol, jump_intensity, gamma, expected
    (ql.OptionType.Call, 80.0, 100.0, 0.0, 0.08, 0.10, 0.25, 1.0, 0.25, 20.67),
    (ql.OptionType.Call, 80.0, 100.0, 0.0, 0.08, 0.25, 0.25, 1.0, 0.25, 21.74),
    (ql.OptionType.Call, 100.0, 100.0, 0.0, 0.08, 0.10, 0.25, 1.0, 0.25, 3.42),
    (ql.OptionType.Call, 100.0, 100.0, 0.0, 0.08, 0.50, 0.25, 5.0, 0.25, 9.02),
    (ql.OptionType.Call, 110.0, 100.0, 0.0, 0.08, 0.25, 0.25, 1.0, 0.50, 1.93),
    (ql.OptionType.Call, 120.0, 100.0, 0.0, 0.08, 0.50, 0.25, 10.0, 0.75, 2.23),
]


@pytest.mark.parametrize(
    "option_type,strike,spot,q,r,t,vol,jump_intensity,gamma,expected",
    _CASES,
)
def test_merton76_haug_values(
    option_type, strike, spot, q, r, t, vol, jump_intensity, gamma, expected
):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _merton76(today, spot, q, r, vol, jump_intensity, gamma)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + _time_to_days(t)),
    )
    opt.set_jump_diffusion_pricing_engine(process)
    assert opt.NPV() == pytest.approx(expected, abs=1.0e-2)


def test_factory_alias_and_compat():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _merton76(today, 100.0, 0.0, 0.08, 0.25, 1.0, 0.25)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 80.0),
        ql.EuropeanExercise(today + _time_to_days(0.10)),
    )
    opt.set_jump_diffusion_pricing_engine(ql.JumpDiffusionEngine(process))
    assert opt.NPV() == pytest.approx(20.67, abs=1.0e-2)
    assert process.jump_intensity() == pytest.approx(1.0)
    assert process.x0() == pytest.approx(100.0)

    import qlnb.compat as c

    assert hasattr(c.VanillaOption, "setJumpDiffusionPricingEngine")
