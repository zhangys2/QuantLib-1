"""Phase-77 tests: Turnbull-Wakeman arithmetic Asian options."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase77():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 78)


def _time_to_days(t: float) -> int:
    # Matches test-suite/utilities.hpp timeToDays(t, 360).
    return int(round(t * 360))


def _fixing_dates(today: ql.Date, first: float, expiry: float, fixings: int):
    dt = (expiry - first) / (fixings - 1)
    dates = [today + _time_to_days(first)]
    for i in range(1, fixings):
        dates.append(today + _time_to_days(i * dt + first))
    return dates


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _tw_option(today, option_type, strike, first, expiry, fixings, process):
    dates = _fixing_dates(today, first, expiry, fixings)
    opt = ql.DiscreteAveragingAsianOption(
        ql.AverageType.Arithmetic,
        0.0,
        0,
        dates,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + _time_to_days(expiry)),
    )
    opt.set_turnbull_wakeman_pricing_engine(process)
    return opt


# AsianOptionTests::testTurnbullWakemanAsianEngine — Haug Table 4-28 (tol 2.5e-3).
# b=0 ⇒ dividend yield equals the risk-free rate. Weekly 26 fixings, T=0.5.
_HAUG_FLAT = [
    (ql.OptionType.Call, 80.0, 19.5152),
    (ql.OptionType.Call, 100.0, 3.2700),
    (ql.OptionType.Put, 100.0, 3.2700),
    (ql.OptionType.Put, 80.0, 0.0090),
]


@pytest.mark.parametrize("option_type,strike,npv", _HAUG_FLAT)
def test_turnbull_wakeman_haug_flat(option_type, strike, npv):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 100.0, 0.05, 0.05, 0.20)
    opt = _tw_option(today, option_type, strike, 1.0 / 52, 0.5, 26, process)
    assert opt.NPV() == pytest.approx(npv, abs=2.5e-3)
    assert opt.is_expired() is False


def test_turnbull_wakeman_atm_greeks():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm(today, 100.0, 0.05, 0.05, 0.20)
    opt = _tw_option(today, ql.OptionType.Call, 100.0, 1.0 / 52, 0.5, 26, process)
    assert opt.delta() != 0.0
    assert opt.gamma() != 0.0


def test_compat_phase77_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.DiscreteAveragingAsianOption, "setTurnbullWakemanPricingEngine")
    assert hasattr(cql.DiscreteAveragingAsianOption, "isExpired")
    assert cql.TurnbullWakemanAsianEngine is not None
