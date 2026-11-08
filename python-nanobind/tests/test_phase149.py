"""Phase-149 tests: AnalyticRoughHestonEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase149():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 20)


def _suite_market(today: ql.Date):
    # RoughHestonModelTests::testKnownReferenceValues.
    dc = ql.Actual365Fixed()
    spot = ql.make_quote_handle(100.0)
    r_ts = ql.FlatForward(today, 0.03, dc)
    q_ts = ql.FlatForward(today, 0.00, dc)
    model = ql.RoughHestonModel(r_ts, q_ts, spot, 0.04, 0.3, 0.04, 0.4, -0.7, 0.1)
    return model


# maturity_years, strike, expected (independent reference implementation).
_REFERENCES = [
    (0.25, 75.0, 25.762400),
    (0.25, 100.0, 3.793313),
    (0.25, 130.0, 0.001586),
    (1.00, 75.0, 28.394103),
    (1.00, 100.0, 8.336634),
    (1.00, 130.0, 0.202295),
    (2.00, 75.0, 31.520600),
    (2.00, 100.0, 12.722717),
    (2.00, 130.0, 1.285820),
]


def _maturity_date(today: ql.Date, years: float) -> ql.Date:
    days = int(round(years * 365.0))
    return today + ql.Period(days, ql.TimeUnit.Days)


@pytest.mark.parametrize("years,strike,expected", _REFERENCES)
def test_rough_heston_reference_prices(years, strike, expected):
    today = ql.Date(2, ql.Month.July, 2026)
    ql.set_evaluation_date(today)
    model = _suite_market(today)
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(_maturity_date(today, years)),
    )
    opt.set_rough_heston_pricing_engine(model, 128, 512)
    tol = 0.01 if years == 0.25 else 5e-4
    assert opt.NPV() == pytest.approx(expected, abs=tol)


def test_compat_phase149_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setRoughHestonPricingEngine")
    assert hasattr(cql.VanillaOption, "setRoughHestonPricingEngine")
    assert cql.AnalyticRoughHestonEngine is not None
    assert cql.RoughHestonModel is not None
