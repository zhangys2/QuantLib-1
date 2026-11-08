"""Phase-71 tests: DoubleBarrier / SoftBarrier implied volatility."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_at_least_phase71():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 72)


def _time_to_days(t: float) -> int:
    return int(math.floor(t * 360 + 0.5))


def _bsm_process(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual360()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.TARGET(), vol, dc),
    )


def test_double_barrier_implied_vol_knock_out_needs_tight_bracket():
    # Phase-25 Haug KO call (50/150, t=0.25, vol=0.15, NPV=4.3515).
    # Ikeda/Kunitomo KO price is not monotonic in vol (peaks then falls
    # to ~0 at both extremes), so C++ defaults [1e-7, 4] fail to bracket.
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.25)
    process = _bsm_process(today, 100.0, 0.0, 0.1, 0.15)
    dummy = _bsm_process(today, 100.0, 0.0, 0.1, 0.20)
    opt = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockOut,
        50.0,
        150.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_pricing_engine(process)
    price = opt.NPV()
    assert price == pytest.approx(4.3515, abs=1.0e-4)
    impl = opt.implied_volatility(
        price, dummy, accuracy=1.0e-6, min_vol=0.05, max_vol=0.50
    )
    assert impl == pytest.approx(0.15, abs=1.0e-6)
    impl_haug = opt.implied_volatility(
        4.3515, dummy, accuracy=1.0e-6, min_vol=0.05, max_vol=0.50
    )
    assert impl_haug == pytest.approx(0.15, abs=5.0e-4)


def test_double_barrier_implied_vol_knock_in_round_trip():
    # Phase-25 Haug KI call (70/130, t=0.50, vol=0.25, NPV=5.5818).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.50)
    process = _bsm_process(today, 100.0, 0.0, 0.1, 0.25)
    dummy = _bsm_process(today, 100.0, 0.0, 0.1, 0.0)
    opt = ql.DoubleBarrierOption(
        ql.DoubleBarrierType.KnockIn,
        70.0,
        130.0,
        0.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_pricing_engine(process)
    price = opt.NPV()
    assert price == pytest.approx(5.5818, abs=1.0e-4)
    impl = opt.implied_volatility(price, dummy, accuracy=1.0e-6)
    assert impl == pytest.approx(0.25, abs=1.0e-6)


def test_soft_barrier_implied_vol_recovers_input():
    # Phase-29 Haug DownOut call (L=U=95, t=0.5, vol=0.1, NPV=3.8075).
    today = ql.Date(8, ql.Month.August, 2025)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.5)
    process = _bsm_process(today, 100.0, 0.05, 0.1, 0.1)
    dummy = _bsm_process(today, 100.0, 0.05, 0.1, 0.0)
    opt = ql.SoftBarrierOption(
        ql.BarrierType.DownOut,
        95.0,
        95.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_pricing_engine(process)
    price = opt.NPV()
    assert price == pytest.approx(3.8075, abs=1.0e-4)
    impl = opt.implied_volatility(price, dummy, accuracy=1.0e-6)
    assert impl == pytest.approx(0.1, abs=1.0e-6)
    priced = ql.SoftBarrierOption(
        ql.BarrierType.DownOut,
        95.0,
        95.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    priced.set_pricing_engine(_bsm_process(today, 100.0, 0.05, 0.1, impl))
    assert priced.NPV() == pytest.approx(price, abs=1.0e-5)


def test_soft_barrier_implied_vol_inverts_haug_target():
    today = ql.Date(8, ql.Month.August, 2025)
    ql.set_evaluation_date(today)
    maturity = today + _time_to_days(0.5)
    dummy = _bsm_process(today, 100.0, 0.05, 0.1, 0.0)
    opt = ql.SoftBarrierOption(
        ql.BarrierType.DownOut,
        95.0,
        95.0,
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(maturity),
    )
    impl = opt.implied_volatility(4.5263, dummy, accuracy=1.0e-6)
    # Haug p.166 L=95, t=0.5, vol=0.2 → 4.5263
    assert impl == pytest.approx(0.2, abs=5.0e-4)


def test_compat_phase71_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.DoubleBarrierOption, "impliedVolatility")
    assert hasattr(cql.SoftBarrierOption, "impliedVolatility")
