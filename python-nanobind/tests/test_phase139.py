"""Phase-139 tests: ChoiAsianEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase139():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 10)


def _time_to_days(t: float) -> int:
    # Matches test-suite/utilities.hpp timeToDays(t, 360).
    return int(round(t * 360))


def _fixing_dates(today: ql.Date, first: float, length: float, fixings: int):
    dt = length / (fixings - 1)
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


def _choi_option(today, option_type, strike, first, length, fixings, process):
    dates = _fixing_dates(today, first, length, fixings)
    opt = ql.DiscreteAveragingAsianOption(
        ql.AverageType.Arithmetic,
        0.0,
        0,
        dates,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(dates[-1]),
    )
    # Suite: ChoiAsianEngine(process, 10, 2 << 12).
    opt.set_choi_pricing_engine(
        process, integration_lambda=10.0, max_nr_integration_steps=2 << 12
    )
    return opt


# AsianOptionTests::testMCDiscreteArithmeticAveragePrice — Levy 1997 cases
# (first=0, length=11/12) checked with Choi engine (tol 3e-2).
_LEVY = [
    (2, 1.3942835683),
    (4, 1.5852442983),
    (8, 1.66970673),
    (12, 1.6980019214),
]


@pytest.mark.parametrize("fixings,npv", _LEVY)
def test_choi_asian_levy(fixings, npv):
    today = ql.get_evaluation_date()
    ql.set_evaluation_date(today)
    process = _bsm(today, 90.0, 0.06, 0.025, 0.13)
    opt = _choi_option(
        today, ql.OptionType.Put, 87.0, 0.0, 11.0 / 12.0, fixings, process
    )
    assert opt.NPV() == pytest.approx(npv, abs=3e-2)
    assert opt.is_expired() is False


def test_compat_phase139_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.DiscreteAveragingAsianOption, "setChoiPricingEngine")
    assert cql.ChoiAsianEngine is not None
