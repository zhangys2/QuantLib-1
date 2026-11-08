"""Phase-64 tests: DAX Heston calibration golden (Sepp SSE ≈ 177.2)."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase64():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 65)


def _dax_market():
    # HestonModelTests::getDAXCalibrationMarketData (Sepp 2003).
    today = ql.Date(5, ql.Month.July, 2002)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    calendar = ql.TARGET()
    tenors = [13, 41, 75, 165, 256, 345, 524, 703]
    zeros = [0.0357, 0.0349, 0.0341, 0.0355, 0.0359, 0.0368, 0.0386, 0.0401]
    dates = [today] + [today + t for t in tenors]
    rates = [0.0357] + zeros
    risk_free = ql.ZeroCurve(dates, rates, dc)
    dividend = ql.FlatForward(today, 0.0, dc)
    s0 = ql.make_quote_handle(4468.17)
    vols = [
        0.6625, 0.4875, 0.4204, 0.3667, 0.3431, 0.3267, 0.3121, 0.3121,
        0.6007, 0.4543, 0.3967, 0.3511, 0.3279, 0.3154, 0.2984, 0.2921,
        0.5084, 0.4221, 0.3718, 0.3327, 0.3155, 0.3027, 0.2919, 0.2889,
        0.4541, 0.3869, 0.3492, 0.3149, 0.2963, 0.2926, 0.2819, 0.2800,
        0.4060, 0.3607, 0.3330, 0.2999, 0.2887, 0.2811, 0.2751, 0.2775,
        0.3726, 0.3396, 0.3108, 0.2781, 0.2788, 0.2722, 0.2661, 0.2686,
        0.3550, 0.3277, 0.3012, 0.2781, 0.2781, 0.2661, 0.2661, 0.2681,
        0.3428, 0.3209, 0.2958, 0.2740, 0.2688, 0.2627, 0.2580, 0.2620,
        0.3302, 0.3062, 0.2799, 0.2631, 0.2573, 0.2533, 0.2504, 0.2544,
        0.3343, 0.2959, 0.2705, 0.2540, 0.2504, 0.2464, 0.2448, 0.2462,
        0.3460, 0.2845, 0.2624, 0.2463, 0.2425, 0.2385, 0.2373, 0.2422,
        0.3857, 0.2860, 0.2578, 0.2399, 0.2357, 0.2327, 0.2312, 0.2351,
        0.3976, 0.2860, 0.2607, 0.2356, 0.2297, 0.2268, 0.2241, 0.2320,
    ]
    strikes = [
        3400, 3600, 3800, 4000, 4200, 4400,
        4500, 4600, 4800, 5000, 5200, 5400, 5600,
    ]
    helpers = []
    for s, strike in enumerate(strikes):
        for m, t in enumerate(tenors):
            helpers.append(
                ql.HestonModelHelper(
                    ql.Period((t + 3) // 7, ql.TimeUnit.Weeks),
                    calendar,
                    s0,
                    strike,
                    ql.make_quote_handle(vols[s * 8 + m]),
                    risk_free,
                    dividend,
                    error_type=ql.CalibrationErrorType.ImpliedVolError,
                )
            )
    return s0, risk_free, dividend, helpers


def test_dax_heston_calibration_sse():
    # HestonModelTests::testDAXCalibration — AnalyticHestonEngine, order 64.
    s0, risk_free, dividend, helpers = _dax_market()
    process = ql.HestonProcess(
        risk_free, dividend, s0, 0.1, 1.0, 0.1, 0.5, -0.5
    )
    model = ql.HestonModel(process)
    for helper in helpers:
        helper.set_pricing_engine(model, integration_order=64)
    model.calibrate(
        helpers,
        ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8),
        ql.EndCriteria(400, 40, 1e-8, 1e-8, 1e-8),
    )
    sse = sum((h.calibration_error() * 100.0) ** 2 for h in helpers)
    assert abs(sse - 177.2) < 1.0


def test_zero_curve_alias_and_compat():
    today = ql.Date(5, ql.Month.July, 2002)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    curve = ql.ZeroCurve([today, today + 365], [0.03, 0.04], dc)
    assert curve.discount(today + 365) > 0.0
    import qlnb.compat as cql

    assert cql.ZeroCurve is not None
