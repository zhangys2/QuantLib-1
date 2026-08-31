"""Phase-134 tests: BjerksundStenslandApproximationEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase134():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 5)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


# AmericanOptionTests::testBjerksundStenslandValues (tol 5e-5).
_CASES = [
    # option_type, strike, spot, q, r, t, vol, expected
    (ql.OptionType.Call, 40.0, 42.0, 0.08, 0.04, 0.75, 0.35, 5.2704),
    (ql.OptionType.Put, 40.0, 36.0, 0.00, 0.06, 1.00, 0.20, 4.4531),
    (ql.OptionType.Call, 100.0, 100.0, 0.05, 0.05, 1.0, 0.0021, 0.08032314),
    (ql.OptionType.Call, 100.0, 110.0, 0.05, 0.05, 1.0, 0.0001, 10.0),
    (ql.OptionType.Put, 110.0, 100.0, 0.05, 0.05, 1.0, 0.0001, 10.0),
]


@pytest.mark.parametrize(
    "option_type,strike,spot,q,r,t,vol,expected",
    _CASES,
)
def test_bjerksund_stensland_values(
    option_type, strike, spot, q, r, t, vol, expected
):
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(option_type, strike),
        ql.AmericanExercise(today, today + _time_to_days(t)),
    )
    opt.set_bjerksund_stensland_pricing_engine(process)
    assert opt.NPV() == pytest.approx(expected, abs=5.0e-5)


def test_factory_alias_and_compat():
    today = ql.Date.todays_date()
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(42.0),
        ql.FlatForward(today, 0.08, dc),
        ql.FlatForward(today, 0.04, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.35, dc),
    )
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 40.0),
        ql.AmericanExercise(today, today + _time_to_days(0.75)),
    )
    opt.set_bjerksund_stensland_pricing_engine(
        ql.BjerksundStenslandEngine(process)
    )
    assert opt.NPV() == pytest.approx(5.2704, abs=5.0e-5)

    import qlnb.compat as c

    assert hasattr(c.VanillaOption, "setBjerksundStenslandPricingEngine")
