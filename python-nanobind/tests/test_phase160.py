"""Phase-160 tests: LiborForwardModel + AnalyticCapFloorEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase160():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 31)


def _lfm_index():
    today = ql.Date(4, ql.Month.September, 2005)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    today = calendar.adjust(today)
    ql.set_evaluation_date(today)
    dates = [ql.Date(4, ql.Month.September, 2005), ql.Date(4, ql.Month.September, 2018)]
    rates = [0.039, 0.041]
    dc = ql.Actual360()
    index = ql.Euribor6M(ql.ZeroCurve(dates, rates, dc))
    start = index.fixing_calendar().advance(today, index.fixing_days(), ql.TimeUnit.Days)
    dates[0] = start
    curve = ql.ZeroCurve(dates, rates, dc)
    return ql.Euribor6M(curve), curve, today


def _make_caplet_vol_curve(process: ql.LiborForwardModelProcess, today: ql.Date):
    vols = [14.40, 17.15, 16.81, 16.64, 16.17, 15.78, 15.40, 15.21, 14.86]
    dates = [process.fixing_dates()[i + 1] for i in range(9)]
    return ql.CapletVarianceCurve(
        today, dates, [v / 100.0 for v in vols], ql.Actual360()
    )


def test_lfm_caplet_pricing():
    # LiborMarketModelTests::testCapletPricing
    index, curve, today = _lfm_index()
    size = 10
    process = ql.LiborForwardModelProcess(size, index)
    cap_vol = _make_caplet_vol_curve(process, today)
    vols = ql.lm_fixed_volatilities_from_caplet_curve(process, cap_vol)
    vola_model = ql.LmFixedVolatilityModel(vols, process.fixing_times())
    corr_model = ql.LmExponentialCorrelationModel(size, 0.3)
    model = ql.LiborForwardModel(process, vola_model, corr_model)

    cap = ql.make_lfm_cap(process, strike=0.04)
    cap.set_libor_forward_pricing_engine(model, discount_curve=curve)
    assert cap.NPV() == pytest.approx(0.015853935178, abs=1e-12)


def test_compat_phase160_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.Cap, "setLiborForwardPricingEngine")
    assert cql.LiborForwardModel is not None
    assert cql.make_lfm_cap is not None
