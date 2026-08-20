"""Phase-82 tests: Choi weighted-sum average basket."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase82():
    assert ql.__version__ == "0.83.0"


def _bsm(today: ql.Date, spot: float, q: float, r: float, vol: float):
    dc = ql.Actual365Fixed()
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )


# BasketOptionTests::testGoldenChoiBasketEngineExample.
_RHO = [
    1.0, 0.2, 0.3, 0.0,
    0.2, 1.0, -0.3, 0.1,
    0.3, -0.3, 1.0, 0.7,
    0.0, 0.1, 0.7, 1.0,
]
_WEIGHTS = [1.0, -2.0, -1.0, 4.0]


def _choi_option(option_type: ql.OptionType):
    today = ql.Date(26, ql.Month.September, 2024)
    ql.set_evaluation_date(today)
    maturity = today + ql.Period(18, ql.TimeUnit.Months)
    processes = [
        _bsm(today, 100.0, 0.075, 0.05, 0.45),
        _bsm(today, 50.0, 0.035, 0.05, 0.40),
        _bsm(today, 75.0, 0.08, 0.05, 0.35),
        _bsm(today, 25.0, 0.02, 0.05, 0.20),
    ]
    rho = ql.Matrix(4, 4, _RHO)
    opt = ql.BasketOption(
        ql.AverageBasketPayoff(
            ql.PlainVanillaPayoff(option_type, 20.0), _WEIGHTS
        ),
        ql.EuropeanExercise(maturity),
    )
    opt.set_choi_pricing_engine(
        processes,
        rho,
        integration_lambda=7.0,
        max_nr_integration_steps=10000,
        calc_fwd_delta=True,
        control_variate=True,
    )
    return opt


def test_choi_average_basket_put():
    opt = _choi_option(ql.OptionType.Put)
    assert opt.NPV() == pytest.approx(15.92008513388834, abs=1.0e-5)
    assert opt.is_expired() is False


def test_choi_average_basket_call():
    opt = _choi_option(ql.OptionType.Call)
    assert opt.NPV() == pytest.approx(22.36122704630282, abs=1.0e-5)


def test_compat_phase82_aliases():
    import qlnb.compat as cql

    assert cql.AverageBasketPayoff is not None
    assert hasattr(cql.BasketOption, "setChoiPricingEngine")
    assert cql.ChoiBasketEngine is not None
