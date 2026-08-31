"""Phase-148 tests: AnalyticGJRGARCHEngine."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase148():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 19)


def _gjr_v0(omega: float, alpha: float, beta: float, gamma: float, lam: float) -> float:
    n = 0.5 * (1.0 + math.erf(lam / math.sqrt(2.0)))
    m1 = (
        beta
        + (alpha + gamma * n) * (1.0 + lam * lam)
        + gamma * lam * math.exp(-lam * lam / 2.0) / math.sqrt(2.0 * math.pi)
    )
    return omega / (1.0 - m1)


# GJRGARCHModelTests::testEngines analytic table.
_LAMBDAS = [0.0, 0.1, 0.2]
_MATURITIES = [90, 180]
_STRIKES = [35, 40, 45, 50, 55, 60]
_EXPECTED = [
    [
        [15.4315, 10.5552, 5.9625, 2.3282, 0.5408, 0.0835],
        [15.8969, 11.2173, 6.9112, 3.4788, 1.3769, 0.4357],
    ],
    [
        [15.4556, 10.6929, 6.2381, 2.6831, 0.7822, 0.1738],
        [16.0587, 11.5338, 7.3170, 3.9074, 1.7279, 0.6568],
    ],
    [
        [15.8000, 11.2734, 7.0376, 3.6767, 1.5871, 0.5934],
        [16.9286, 12.3170, 8.0405, 4.6348, 2.3429, 1.0590],
    ],
]


@pytest.mark.parametrize("k,lam", list(enumerate(_LAMBDAS)))
@pytest.mark.parametrize("i,days", list(enumerate(_MATURITIES)))
@pytest.mark.parametrize("j,strike", list(enumerate(_STRIKES)))
def test_gjr_garch_analytic_npv(k, lam, i, days, j, strike):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)

    omega = 2.0e-6
    alpha = 0.024
    beta = 0.93
    gamma = 0.059
    v0 = _gjr_v0(omega, alpha, beta, gamma, lam)

    spot = ql.make_quote_handle(50.0)
    r_ts = ql.FlatForward(today, 0.05, dc)
    q_ts = ql.FlatForward(today, 0.00, dc)
    process = ql.GJRGARCHProcess(
        r_ts, q_ts, spot, v0, omega, alpha, beta, gamma, lam, 365.0
    )
    model = ql.GJRGARCHModel(process)

    maturity = today + ql.Period(days, ql.TimeUnit.Days)
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(maturity),
    )
    opt.set_gjr_garch_pricing_engine(model)
    assert opt.NPV() == pytest.approx(_EXPECTED[k][i][j], abs=0.15)


def test_compat_phase148_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setGjrGarchPricingEngine")
    assert hasattr(cql.VanillaOption, "setGjrGarchPricingEngine")
    assert cql.AnalyticGJRGARCHEngine is not None
    assert cql.GJRGARCHModel is not None
