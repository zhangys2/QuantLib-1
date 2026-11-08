"""Phase-152 tests: FdHestonHullWhiteVanillaEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase152():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 23)


# HybridHestonHullWhiteProcessTests::testFdmHestonHullWhiteEngine
_CORR = (-0.85, 0.5)
_STRIKES = (75.0, 120.0, 160.0)


def _suite_market(today: ql.Date):
    dc = ql.Actual365Fixed()
    spot = ql.make_quote_handle(100.0)
    r_ts = ql.FlatForward(today, 0.05, dc)
    q_ts = ql.FlatForward(today, 0.02, dc)
    vol = 0.30
    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc)
    bsm = ql.BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)

    v0 = vol * vol
    heston_process = ql.HestonProcess(
        r_ts, q_ts, spot, v0, 1.0, v0, 1e-6, 0.0
    )
    heston_model = ql.HestonModel(heston_process)
    hw_process = ql.HullWhiteProcess(r_ts, 0.00883, 0.01)
    hw_model = ql.HullWhite(r_ts, hw_process.a(), hw_process.sigma())
    maturity = ql.Date(28, ql.Month.March, 2012)
    return bsm, heston_model, hw_process, hw_model, maturity


@pytest.mark.parametrize("corr", _CORR)
@pytest.mark.parametrize("strike", _STRIKES)
def test_fd_heston_hull_white_vs_analytic(corr: float, strike: float):
    today = ql.Date(28, ql.Month.March, 2004)
    ql.set_evaluation_date(today)
    bsm, heston_model, hw_process, hw_model, maturity = _suite_market(today)
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
        ql.EuropeanExercise(maturity),
    )
    opt.set_fd_heston_hull_white_pricing_engine(
        heston_model,
        hw_process,
        corr,
        t_grid=50,
        x_grid=200,
        v_grid=10,
        r_grid=15,
    )
    fd_npv = opt.NPV()
    fd_delta = opt.delta()
    fd_gamma = opt.gamma()

    opt.set_bsm_hull_white_pricing_engine(corr, bsm, hw_model)
    assert fd_npv == pytest.approx(opt.NPV(), abs=0.01)
    assert fd_delta == pytest.approx(opt.delta(), abs=0.001)
    assert fd_gamma == pytest.approx(opt.gamma(), abs=0.001)


def test_compat_phase152_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.VanillaOption, "setFdHestonHullWhitePricingEngine")
    assert hasattr(cql.EuropeanOption, "setFdHestonHullWhitePricingEngine")
    assert cql.FdHestonHullWhiteVanillaEngine is not None
    assert cql.HullWhiteProcess is not None
