"""Phase-48 tests: Heston model calibration."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase48():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 49)


def test_end_criteria_and_optimizer_ctors():
    ec = ql.EndCriteria(400, 40, 1e-8, 1e-8, 1e-8)
    assert ec.max_iterations() == 400
    assert ec.root_epsilon() == pytest.approx(1e-8)
    assert ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8) is not None
    assert ql.CalibrationErrorType.ImpliedVolError is not None
    assert ql.EndCriteriaType.None_ is not None


def test_heston_black_calibration():
    # Mirrors HestonModelTests::testBlackCalibration (sigma start = 0.1).
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual360()
    risk_free = ql.FlatForward(today, 0.04, dc)
    dividend = ql.FlatForward(today, 0.50, dc)
    s0 = ql.make_quote_handle(1.0)
    vol = ql.make_quote_handle(0.1)
    volatility = 0.1
    calendar = ql.NullCalendar()
    ref = risk_free.reference_date()

    maturities = [
        ql.Period(1, ql.TimeUnit.Months),
        ql.Period(2, ql.TimeUnit.Months),
        ql.Period(3, ql.TimeUnit.Months),
        ql.Period(6, ql.TimeUnit.Months),
        ql.Period(9, ql.TimeUnit.Months),
        ql.Period(1, ql.TimeUnit.Years),
        ql.Period(2, ql.TimeUnit.Years),
    ]
    helpers = []
    for maturity in maturities:
        for moneyness in (-1.0, 0.0, 1.0):
            exercise_date = calendar.advance(ref, maturity)
            tau = dc.year_fraction(ref, exercise_date)
            fwd = s0.current_link().value() * (
                dividend.discount(exercise_date) / risk_free.discount(exercise_date)
            )
            strike = fwd * math.exp(-moneyness * volatility * math.sqrt(tau))
            helpers.append(
                ql.HestonModelHelper(
                    maturity,
                    calendar,
                    s0,
                    strike,
                    vol,
                    risk_free,
                    dividend,
                )
            )

    process = ql.HestonProcess(
        risk_free, dividend, s0, 0.01, 0.2, 0.02, 0.1, -0.75
    )
    model = ql.HestonModel(process)
    for h in helpers:
        h.set_pricing_engine(model, integration_order=96)

    model.calibrate(
        helpers,
        ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8),
        ql.EndCriteria(400, 40, 1e-8, 1e-8, 1e-8),
    )

    tol = 3.0e-3
    assert model.sigma() <= tol
    assert abs(model.v0() - volatility * volatility) <= tol
    assert abs(model.kappa() * (model.theta() - volatility * volatility)) <= tol
    assert model.end_criteria() != ql.EndCriteriaType.None_
    params = model.params()
    assert len(params) == 5


def test_compat_phase48_aliases():
    import qlnb.compat as cql

    assert cql.HestonModelHelper is not None
    assert hasattr(cql.HestonModelHelper, "setPricingEngine")
    assert hasattr(cql.HestonModelHelper, "calibrationError")
    assert hasattr(cql.HestonModel, "setParams")
    assert hasattr(cql.HestonModel, "endCriteria")
