"""Phase-144 tests: AnalyticBSMHullWhiteEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase144():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 15)


def _suite_market(today: ql.Date):
    # HybridHestonHullWhiteProcessTests::testBsmHullWhiteEngine.
    dc = ql.Actual365Fixed()
    spot = ql.make_quote_handle(100.0)
    q_ts = ql.FlatForward(today, 0.04, dc)
    r_ts = ql.FlatForward(today, 0.0525, dc)
    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), 0.25, dc)
    process = ql.BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)
    hw = ql.HullWhite(r_ts, 0.00883, 0.00526)
    maturity = today + ql.Period(20, ql.TimeUnit.Years)
    fwd = 100.0 * q_ts.discount(maturity) / r_ts.discount(maturity)
    opt = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, fwd),
        ql.EuropeanExercise(maturity),
    )
    return process, hw, opt, q_ts, r_ts, spot, dc, maturity, fwd


# corr → expected equivalent Black vol (suite table).
_CORR_VOL = [
    (-0.75, 0.217064577),
    (-0.25, 0.243995801),
    (0.0, 0.256402830),
    (0.25, 0.268236596),
    (0.75, 0.290461343),
]


@pytest.mark.parametrize("corr,expected_vol", _CORR_VOL)
def test_bsm_hull_white_implied_vol(corr, expected_vol):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    process, hw, opt, q_ts, r_ts, spot, dc, maturity, fwd = _suite_market(today)
    opt.set_bsm_hull_white_pricing_engine(corr, process, hw)
    npv = opt.NPV()
    assert npv > 0.0

    bs_process = ql.BlackScholesMertonProcess(
        spot,
        q_ts,
        r_ts,
        ql.BlackConstantVol(today, ql.NullCalendar(), expected_vol, dc),
    )
    impl = opt.implied_volatility(
        npv, bs_process, accuracy=1e-10, max_evaluations=100
    )
    assert impl == pytest.approx(expected_vol, abs=1e-8)

    comp = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, fwd),
        ql.EuropeanExercise(maturity),
    )
    comp.set_pricing_engine(bs_process)
    assert comp.NPV() == pytest.approx(npv, rel=1e-8)
    assert comp.delta() == pytest.approx(opt.delta(), abs=1e-8)


def test_compat_phase144_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.EuropeanOption, "setBsmHullWhitePricingEngine")
    assert cql.AnalyticBSMHullWhiteEngine is not None
