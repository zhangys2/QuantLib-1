"""Phase-128 tests: VannaVolgaBarrierEngine + DeltaVolQuote."""

from __future__ import annotations

import math
import sys

import pytest

import qlnb as ql


def test_version_is_phase128():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (3, 9)


def _time_to_days(t: float, days_per_year: int = 365) -> int:
    return int(round(t * days_per_year))


def _bs_vanilla_price(
    option_type, strike: float, spot: float, q: float, r: float, t: float, vol: float
) -> float:
    # Mirrors blackFormula used in BarrierOptionTests::testVannaVolgaSimpleBarrierValues.
    df_r = math.exp(-r * t)
    df_q = math.exp(-q * t)
    forward = spot * df_q / df_r
    std_dev = vol * math.sqrt(t)
    d1 = math.log(forward / strike) / std_dev + 0.5 * std_dev
    d2 = d1 - std_dev
    nd = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    if option_type == ql.OptionType.Call:
        return df_r * (forward * nd(d1) - strike * nd(d2))
    return df_r * (strike * nd(-d2) - forward * nd(-d1))


# Representative cases from BarrierOptionTests::testVannaVolgaSimpleBarrierValues.
_CASES = [
    # barrier_type, barrier, type, strike, s, q, r, t, vol25Put, volAtm, vol25Call, vol, expected
    (ql.BarrierType.UpOut, 1.5, ql.OptionType.Call, 1.13321, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.11638, 0.148127),
    (ql.BarrierType.UpOut, 1.5, ql.OptionType.Put, 1.31179, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.08925, 0.0489395),
    (ql.BarrierType.UpIn, 1.5, ql.OptionType.Call, 1.22687, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.10088, 0.0241491),
    (ql.BarrierType.DownOut, 1.1, ql.OptionType.Call, 1.13321, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.11638, 0.17746),
    (ql.BarrierType.DownIn, 1.3, ql.OptionType.Put, 1.46047, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.08412, 0.15752),
    (ql.BarrierType.UpOut, 1.6, ql.OptionType.Call, 1.19545, 1.30265, 0.0009418, 0.0039788, 2.0, 0.10891, 0.09525, 0.09197, 0.1089, 0.105577),
]


@pytest.mark.parametrize(
    "barrier_type,barrier,option_type,strike,s,q,r,t,vol25_put,vol_atm,vol25_call,vol,expected",
    _CASES,
)
def test_vanna_volga_simple_barrier_values(
    barrier_type,
    barrier,
    option_type,
    strike,
    s,
    q,
    r,
    t,
    vol25_put,
    vol_atm,
    vol25_call,
    vol,
    expected,
):
    today = ql.Date(5, ql.Month.March, 2013)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()

    spot = ql.make_quote_handle(s)
    foreign_ts = ql.FlatForward(today, q, dc)
    domestic_ts = ql.FlatForward(today, r, dc)

    atm = ql.DeltaVolQuote(
        ql.make_quote_handle(vol_atm),
        ql.DeltaVolDeltaType.Fwd,
        t,
        ql.DeltaVolAtmType.AtmDeltaNeutral,
    )
    put25 = ql.DeltaVolQuote(
        -0.25, ql.make_quote_handle(vol25_put), t, ql.DeltaVolDeltaType.Fwd
    )
    call25 = ql.DeltaVolQuote(
        0.25, ql.make_quote_handle(vol25_call), t, ql.DeltaVolDeltaType.Fwd
    )

    exercise = ql.EuropeanExercise(today + _time_to_days(t, 365))
    payoff = ql.PlainVanillaPayoff(option_type, strike)
    opt = ql.BarrierOption(barrier_type, barrier, 0.0, payoff, exercise)

    bs = _bs_vanilla_price(option_type, strike, s, q, r, t, vol)
    opt.set_vanna_volga_pricing_engine(
        atm,
        put25,
        call25,
        spot,
        domestic_ts,
        foreign_ts,
        adapt_van_delta=True,
        bs_price_with_smile=bs,
    )
    assert opt.NPV() == pytest.approx(expected, abs=1.0e-4)


def test_delta_vol_quote_accessors():
    q = ql.DeltaVolQuote(
        -0.25, ql.make_quote_handle(0.10), 1.0, ql.DeltaVolDeltaType.Fwd
    )
    assert q.value() == pytest.approx(0.10)
    assert q.delta() == pytest.approx(-0.25)
    assert q.maturity() == pytest.approx(1.0)
    assert q.delta_type() == ql.DeltaVolDeltaType.Fwd
    assert q.is_valid()


def test_native_vanna_volga_snake_case_only():
    assert hasattr(ql.BarrierOption, "set_vanna_volga_pricing_engine")
    assert hasattr(ql, "DeltaVolQuote")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate BarrierOption"
        )
    assert not hasattr(ql.BarrierOption, "setVannaVolgaPricingEngine")


def test_compat_phase128_aliases():
    import qlnb.compat as c

    assert hasattr(c.BarrierOption, "setVannaVolgaPricingEngine")
    assert c.BarrierOption.setVannaVolgaPricingEngine is (
        ql.BarrierOption.set_vanna_volga_pricing_engine
    )
