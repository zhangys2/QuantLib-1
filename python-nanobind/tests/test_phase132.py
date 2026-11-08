"""Phase-132 tests: BinomialBarrierEngine (CRR / Boyle–Lau)."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase132():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 3)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


def _bsm(today, spot, q, r, vol):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# Representative European Haug cases from BarrierOptionTests::testHaugValues.
# Binomial (Boyle–Lau) suite tolerance is 1.1e-2.
_EURO_CASES = [
    # barrier_type, barrier, rebate, option_type, strike, spot, q, r, t, vol, expected
    (ql.BarrierType.DownOut, 95.0, 3.0, ql.OptionType.Call, 90.0, 100.0, 0.04, 0.08, 0.50, 0.25, 9.0246),
    (ql.BarrierType.DownOut, 95.0, 3.0, ql.OptionType.Call, 100.0, 100.0, 0.04, 0.08, 0.50, 0.25, 6.7924),
    (ql.BarrierType.UpOut, 105.0, 3.0, ql.OptionType.Call, 100.0, 100.0, 0.04, 0.08, 0.50, 0.25, 2.3580),
    (ql.BarrierType.DownIn, 95.0, 3.0, ql.OptionType.Call, 100.0, 100.0, 0.04, 0.08, 0.50, 0.25, 4.0109),
    (ql.BarrierType.UpIn, 105.0, 3.0, ql.OptionType.Put, 100.0, 100.0, 0.04, 0.08, 0.50, 0.25, 3.3721),
    (ql.BarrierType.DownOut, 95.0, 3.0, ql.OptionType.Put, 90.0, 100.0, 0.04, 0.08, 0.50, 0.25, 2.2798),
]


@pytest.mark.parametrize(
    "barrier_type,barrier,rebate,option_type,strike,spot,q,r,t,vol,expected",
    _EURO_CASES,
)
def test_haug_european_binomial(
    barrier_type, barrier, rebate, option_type, strike, spot, q, r, t, vol, expected
):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, spot, q, r, vol)
    opt = ql.BarrierOption(
        barrier_type,
        barrier,
        rebate,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + _time_to_days(t)),
    )
    opt.set_binomial_pricing_engine(process, time_steps=400)
    assert opt.NPV() == pytest.approx(expected, abs=1.1e-2)


# American out-options from the same suite (binomial is the primary engine).
_AMERICAN_CASES = [
    (ql.BarrierType.DownOut, 95.0, 0.0, ql.OptionType.Call, 90.0, 100.0, 0.04, 0.08, 0.50, 0.25, 10.4655),
    (ql.BarrierType.DownOut, 95.0, 0.0, ql.OptionType.Call, 100.0, 100.0, 0.04, 0.08, 0.50, 0.25, 4.5159),
    (ql.BarrierType.UpOut, 105.0, 0.0, ql.OptionType.Put, 100.0, 100.0, 0.04, 0.08, 0.50, 0.25, 3.3001),
]


@pytest.mark.parametrize(
    "barrier_type,barrier,rebate,option_type,strike,spot,q,r,t,vol,expected",
    _AMERICAN_CASES,
)
def test_haug_american_binomial(
    barrier_type, barrier, rebate, option_type, strike, spot, q, r, t, vol, expected
):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, spot, q, r, vol)
    opt = ql.BarrierOption(
        barrier_type,
        barrier,
        rebate,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.AmericanExercise(today, today + _time_to_days(t)),
    )
    opt.set_binomial_pricing_engine(process, time_steps=400)
    assert opt.NPV() == pytest.approx(expected, abs=1.1e-2)


def test_compat_set_binomial_pricing_engine():
    import qlnb.compat as c

    assert hasattr(c.BarrierOption, "setBinomialPricingEngine")
