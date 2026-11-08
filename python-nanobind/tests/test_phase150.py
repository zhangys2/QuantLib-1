"""Phase-150 tests: AnalyticPTDHestonEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase150():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 21)


def test_ptd_heston_matches_analytic_heston():
    # HestonModelTests::testAnalyticPiecewiseTimeDependent (Gatheral path).
    today = ql.Date(27, ql.Month.December, 2004)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    exercise = ql.Date(28, ql.Month.March, 2005)
    dates = [today, ql.Date(1, ql.Month.January, 2007)]
    r_ts = ql.ZeroCurve(dates, [0.0, 0.2], dc)
    q_ts = ql.ZeroCurve(dates, [0.0, 0.3], dc)
    spot = ql.make_quote_handle(1.0)

    ptd = ql.PiecewiseTimeDependentHestonModel(
        r_ts, q_ts, spot, 0.1, 0.09, 3.16, 4.40, -0.8, 20.0, 2
    )
    heston = ql.HestonProcess(r_ts, q_ts, spot, 0.1, 3.16, 0.09, 4.40, -0.8)
    heston_model = ql.HestonModel(heston)

    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 1.0),
        ql.EuropeanExercise(exercise),
    )
    opt.set_heston_pricing_engine(heston_model)
    expected = opt.NPV()

    opt.set_ptd_heston_pricing_engine(ptd, 192)
    assert opt.NPV() == pytest.approx(expected, abs=1e-7)


def test_compat_phase150_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setPtdHestonPricingEngine")
    assert hasattr(cql.VanillaOption, "setPtdHestonPricingEngine")
    assert cql.AnalyticPTDHestonEngine is not None
    assert cql.PiecewiseTimeDependentHestonModel is not None
