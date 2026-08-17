"""Phase-74 tests: compound options (AnalyticCompoundOptionEngine)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase74():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 75)


def _time_to_days(t: float) -> int:
    # Matches test-suite/utilities.hpp timeToDays (lround, 360 days/year).
    return int(round(t * 360))


def _bsm_process(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


def _compound_option(
    today, type_m, type_d, k_m, k_d, t_m, t_d, process
):
    opt = ql.CompoundOption(
        ql.PlainVanillaPayoff(type_m, k_m),
        ql.EuropeanExercise(today + _time_to_days(t_m)),
        ql.PlainVanillaPayoff(type_d, k_d),
        ql.EuropeanExercise(today + _time_to_days(t_d)),
    )
    opt.set_pricing_engine(process)
    return opt


# CompoundOptionTests::testValues — Haug 2007 / sitmo (tol 1e-3).
_HAUG_SITMO = [
    # mother, daughter, Km, Kd, S, q, r, tm, td, vol, npv, delta
    (ql.OptionType.Put, ql.OptionType.Call, 50.0, 520.0, 500.0, 0.03, 0.08, 0.25, 0.5, 0.35, 21.1965, -0.1966),
    (ql.OptionType.Call, ql.OptionType.Call, 50.0, 520.0, 500.0, 0.03, 0.08, 0.25, 0.5, 0.35, 17.5945, 0.3219),
    (ql.OptionType.Call, ql.OptionType.Put, 50.0, 520.0, 500.0, 0.03, 0.08, 0.25, 0.5, 0.35, 18.7128, -0.2906),
    (ql.OptionType.Put, ql.OptionType.Put, 50.0, 520.0, 500.0, 0.03, 0.08, 0.25, 0.5, 0.35, 15.2601, 0.1760),
]


@pytest.mark.parametrize(
    "type_m,type_d,k_m,k_d,spot,q,r,t_m,t_d,vol,npv,delta",
    _HAUG_SITMO,
)
def test_compound_option_haug_sitmo_values(
    type_m, type_d, k_m, k_d, spot, q, r, t_m, t_d, vol, npv, delta
):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm_process(today, spot, q, r, vol)
    opt = _compound_option(today, type_m, type_d, k_m, k_d, t_m, t_d, process)
    assert opt.NPV() == pytest.approx(npv, abs=1.0e-3)
    assert opt.delta() == pytest.approx(delta, abs=1.0e-3)
    assert not opt.is_expired()


def test_compound_option_put_call_parity():
    # CompoundOptionTests::testPutCallParity (Wystup eq. 9.5).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process = _bsm_process(today, 500.0, 0.03, 0.08, 0.35)
    t_m, t_d = 0.25, 0.5
    call_on_call = _compound_option(
        today, ql.OptionType.Call, ql.OptionType.Call, 50.0, 520.0, t_m, t_d, process
    )
    put_on_call = _compound_option(
        today, ql.OptionType.Put, ql.OptionType.Call, 50.0, 520.0, t_m, t_d, process
    )
    daughter = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 520.0),
        ql.EuropeanExercise(today + _time_to_days(t_d)),
    )
    daughter.set_pricing_engine(process)
    curve = ql.FlatForward(today, 0.08, ql.Actual360())
    mat_m = today + _time_to_days(t_m)
    parity = (
        call_on_call.NPV()
        + 50.0 * curve.discount(mat_m)
        - put_on_call.NPV()
        - daughter.NPV()
    )
    assert parity == pytest.approx(0.0, abs=1.0e-8)


def test_compat_phase74_aliases():
    import qlnb.compat as cql

    assert cql.CompoundOption is not None
    assert hasattr(cql.CompoundOption, "setPricingEngine")
    assert hasattr(cql.CompoundOption, "isExpired")
    assert cql.AnalyticCompoundOptionEngine is not None
