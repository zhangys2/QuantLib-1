"""Phase-151 tests: FdCIRVanillaEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase151():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 22)


# FdCIRTests::testFdmCIRConvergence (expected NPV across FD schemes).
_SCHEMES = [
    ql.FdmSchemeDesc.Hundsdorfer(),
    ql.FdmSchemeDesc.ModifiedCraigSneyd(),
    ql.FdmSchemeDesc.ModifiedHundsdorfer(),
    ql.FdmSchemeDesc.CraigSneyd(),
    ql.FdmSchemeDesc.TrBDF2(),
    ql.FdmSchemeDesc.CrankNicolson(),
]
_EXPECTED = 4.275


def _suite_market(today: ql.Date):
    dc = ql.Actual365Fixed()
    spot = ql.make_quote_handle(36.0)
    r_ts = ql.FlatForward(today, 0.06, dc)
    q_ts = ql.FlatForward(today, 0.00, dc)
    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), 0.20, dc)
    bsm = ql.BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)

    speed = 1.2188
    cir_sigma = 0.02438
    level = 0.0183
    initial_rate = 0.06
    rho = 0.00789
    lam = -0.5726
    new_speed = speed + cir_sigma * lam
    new_level = level * speed / (speed + cir_sigma * lam)
    cir = ql.CoxIngersollRossProcess(new_speed, cir_sigma, initial_rate, new_level)
    maturity = today + ql.Period(365, ql.TimeUnit.Days)
    return bsm, cir, rho, maturity


@pytest.mark.parametrize("scheme", _SCHEMES)
def test_fd_cir_convergence(scheme):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    bsm, cir, rho, maturity = _suite_market(today)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 40.0),
        ql.EuropeanExercise(maturity),
    )
    opt.set_fd_cir_pricing_engine(cir, bsm, rho, scheme_desc=scheme)
    assert opt.NPV() == pytest.approx(_EXPECTED, abs=3e-4)


def test_compat_phase151_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.VanillaOption, "setFdCirPricingEngine")
    assert cql.FdCIRVanillaEngine is not None
    assert cql.CoxIngersollRossProcess is not None
