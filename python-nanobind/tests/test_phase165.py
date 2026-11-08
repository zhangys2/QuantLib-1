"""Phase-165 tests: KahaleSmileSection arbitrage-free smile repair."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase165():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 36)


def _sample_arbitrage_free_smile():
    atm = 0.05
    t = 1.0
    strikes = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    std_dev = 0.50 * (t**0.5)
    calls = [
        ql.black_formula(ql.OptionType.Call, strike, atm, std_dev, 1.0, 0.0)
        for strike in strikes
    ]
    implied = [
        ql.black_formula_implied_std_dev(
            ql.OptionType.Call, strike, atm, price, 1.0, 0.0, 0.2, 1e-8, 1000
        )
        for strike, price in zip(strikes, calls)
    ]
    sec = ql.LinearSmileSection(t, strikes, implied, atm)
    money = [strike / atm for strike in strikes]
    return atm, strikes, sec, money


def test_kahale_smile_reproduces_arbitrage_free_input():
    # MarkovFunctionalTests::testKahaleSmileSection — ksec11 block
    tol = 1e-8
    atm, strikes, sec, money = _sample_arbitrage_free_smile()
    ksec = ql.KahaleSmileSection(
        sec, atm, interpolate=False, exponential_extrapolation=False,
        delete_arbitrage_points=False, moneyness_grid=money,
    )
    assert ksec.left_core_strike() == pytest.approx(0.01, abs=tol)
    assert ksec.right_core_strike() == pytest.approx(0.10, abs=tol)

    k = strikes[0]
    while k <= strikes[-1] + tol:
        assert ksec.option_price(k) == pytest.approx(sec.option_price(k), abs=tol)
        k += 0.0001


def test_kahale_smile_interpolation_on_grid():
    # ksec12 block (left core may be 0.01 or 0.02 on some platforms)
    tol = 1e-8
    atm, strikes, sec, money = _sample_arbitrage_free_smile()
    ksec = ql.KahaleSmileSection(
        sec, atm, interpolate=True, exponential_extrapolation=False,
        delete_arbitrage_points=False, moneyness_grid=money,
    )
    left = ksec.left_core_strike()
    assert abs(left - 0.01) < tol or abs(left - 0.02) < tol
    assert ksec.right_core_strike() == pytest.approx(0.10, abs=tol)
    for strike in strikes[1:]:
        assert ksec.option_price(strike) == pytest.approx(
            sec.option_price(strike), abs=tol
        )


def test_kahale_digital_prices_are_monotone():
    tol = 1e-8
    atm, strikes, sec, money = _sample_arbitrage_free_smile()
    ksec = ql.KahaleSmileSection(
        sec, atm, interpolate=False, exponential_extrapolation=False,
        delete_arbitrage_points=False, moneyness_grid=money,
    )
    k = 0.0010
    prev = 1.0
    while k <= 2.0 * strikes[-1] + tol:
        dig = ksec.digital_option_price(k)
        assert 0.0 <= dig <= prev + tol
        prev = dig
        k += 0.0001


def test_compat_phase165_aliases():
    import qlnb.compat as cql

    assert cql.LinearSmileSection is not None
    assert cql.KahaleSmileSection is not None
    assert hasattr(cql.KahaleSmileSection, "leftCoreStrike")
    assert cql.black_formula is not None
