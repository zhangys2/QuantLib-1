"""Phase-129 tests: VannaVolgaDoubleBarrierEngine<SuoWang>."""

from __future__ import annotations

import math
import sys

import pytest

import qlnb as ql


def test_version_is_phase129():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 0)


def _time_to_days(t: float, days_per_year: int = 365) -> int:
    return int(round(t * days_per_year))


def _bs_vanilla_price(
    option_type, strike: float, spot: float, q: float, r: float, t: float, vol: float
) -> float:
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


# Representative KO goldens from DoubleBarrierOptionTests::testVannaVolgaDoubleBarrierValues.
_KO_CASES = [
    # lo, hi, type, strike, s, q, r, t, vol25Put, volAtm, vol25Call, vol, expected_ko
    (1.1, 1.5, ql.OptionType.Call, 1.13321, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.11638, 0.14413),
    (1.1, 1.5, ql.OptionType.Call, 1.31179, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.08925, 0.02710),
    (1.1, 1.5, ql.OptionType.Put, 1.38843, 1.30265, 0.0003541, 0.0033871, 1.0, 0.10087, 0.08925, 0.08463, 0.08463, 0.06049),
    (1.0, 1.6, ql.OptionType.Call, 1.19545, 1.30265, 0.0009418, 0.0039788, 2.0, 0.10891, 0.09525, 0.09197, 0.10890, 0.10389),
    (1.0, 1.6, ql.OptionType.Put, 1.44298, 1.30265, 0.0009418, 0.0039788, 2.0, 0.10891, 0.09525, 0.09197, 0.09197, 0.09346),
]


def _price(barrier_type, lo, hi, option_type, strike, s, q, r, t, vol25_put, vol_atm, vol25_call, vol):
    today = ql.Date(5, ql.Month.March, 2013)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()

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

    opt = ql.DoubleBarrierOption(
        barrier_type,
        lo,
        hi,
        0.0,
        ql.PlainVanillaPayoff(option_type, strike),
        ql.EuropeanExercise(today + _time_to_days(t, 365)),
    )
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
    return opt.NPV(), bs


@pytest.mark.parametrize(
    "lo,hi,option_type,strike,s,q,r,t,vol25_put,vol_atm,vol25_call,vol,expected_ko",
    _KO_CASES,
)
def test_vanna_volga_double_barrier_knock_out(
    lo, hi, option_type, strike, s, q, r, t, vol25_put, vol_atm, vol25_call, vol, expected_ko
):
    npv, _ = _price(
        ql.DoubleBarrierType.KnockOut,
        lo,
        hi,
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
    )
    assert npv == pytest.approx(expected_ko, abs=1.0e-4)


@pytest.mark.parametrize(
    "lo,hi,option_type,strike,s,q,r,t,vol25_put,vol_atm,vol25_call,vol,expected_ko",
    _KO_CASES[:2],
)
def test_vanna_volga_double_barrier_knock_in_parity(
    lo, hi, option_type, strike, s, q, r, t, vol25_put, vol_atm, vol25_call, vol, expected_ko
):
    # Suite: KI expected = bsVanilla - KO result.
    ki, bs = _price(
        ql.DoubleBarrierType.KnockIn,
        lo,
        hi,
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
    )
    assert ki == pytest.approx(bs - expected_ko, abs=1.0e-4)


def test_native_vanna_volga_double_snake_case_only():
    assert hasattr(ql.DoubleBarrierOption, "set_vanna_volga_pricing_engine")
    if "qlnb.compat" in sys.modules:
        pytest.skip(
            "qlnb.compat already loaded; camelCase aliases mutate DoubleBarrierOption"
        )
    assert not hasattr(ql.DoubleBarrierOption, "setVannaVolgaPricingEngine")


def test_compat_phase129_aliases():
    import qlnb.compat as c

    assert hasattr(c.DoubleBarrierOption, "setVannaVolgaPricingEngine")
    assert c.DoubleBarrierOption.setVannaVolgaPricingEngine is (
        ql.DoubleBarrierOption.set_vanna_volga_pricing_engine
    )
