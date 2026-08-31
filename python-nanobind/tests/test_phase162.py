"""Phase-162 tests: LiborForwardModel calibration (caps + swaptions)."""

from __future__ import annotations

import math

import pytest

import qlnb as ql


def test_version_is_phase162():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 33)


def _lfm_calibration_index():
    today = ql.Date(4, ql.Month.September, 2005)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    today = calendar.adjust(today)
    ql.set_evaluation_date(today)
    dates = [
        ql.Date(4, ql.Month.September, 2005),
        ql.Date(4, ql.Month.September, 2018),
    ]
    rates = [0.039, 0.041]
    dc = ql.Actual360()
    index = ql.Euribor6M(ql.ZeroCurve(dates, rates, dc))
    start = index.fixing_calendar().advance(
        today, index.fixing_days(), ql.TimeUnit.Days
    )
    dates[0] = start
    curve = ql.ZeroCurve(dates, rates, dc)
    return ql.Euribor6M(curve), curve


def test_lfm_calibration_rmse():
    # LiborMarketModelTests::testCalibration
    size = 14
    tolerance = 8e-3
    cap_vols = [
        0.145708,
        0.158465,
        0.166248,
        0.168672,
        0.169007,
        0.167956,
        0.166261,
        0.164239,
        0.162082,
        0.159923,
        0.157781,
        0.155745,
        0.153776,
        0.151950,
        0.150189,
        0.148582,
        0.147034,
        0.145598,
        0.144248,
    ]
    swaption_vols = [
        0.170595,
        0.166844,
        0.158306,
        0.147444,
        0.136930,
        0.126833,
        0.118135,
        0.175963,
        0.166359,
        0.155203,
        0.143712,
        0.132769,
        0.122947,
        0.114310,
        0.174455,
        0.162265,
        0.150539,
        0.138734,
        0.128215,
        0.118470,
        0.110540,
        0.169780,
        0.156860,
        0.144821,
        0.133537,
        0.123167,
        0.114363,
        0.106500,
        0.164521,
        0.151223,
        0.139670,
        0.128632,
        0.119123,
        0.110330,
        0.103114,
        0.158956,
        0.146036,
        0.134555,
        0.124393,
        0.115038,
        0.106996,
        0.100064,
    ]

    index, curve = _lfm_calibration_index()
    process = ql.LiborForwardModelProcess(size, index)
    vola = ql.LmExtLinearExponentialVolModel(
        process.fixing_times(), 0.5, 0.6, 0.1, 0.1
    )
    corr = ql.LmLinearExponentialCorrelationModel(size, 0.5, 0.8)
    model = ql.LiborForwardModel(process, vola, corr)

    day_counter = ql.Actual360()
    helpers: list[ql.CapHelper | ql.SwaptionHelper] = []
    swap_vol_index = 0

    for i in range(2, size):
        maturity = index.tenor() * i
        cap_helper = ql.CapHelper(
            maturity,
            ql.make_quote_handle(cap_vols[i - 2]),
            index,
            ql.Frequency.Annual,
            index.day_counter(),
            True,
            curve,
            ql.CalibrationErrorType.ImpliedVolError,
        )
        cap_helper.set_lfm_pricing_engine(model, discount_curve=curve)
        helpers.append(cap_helper)

        if i <= size // 2:
            for j in range(1, size // 2 + 1):
                length = index.tenor() * j
                swaption_helper = ql.SwaptionHelper(
                    maturity,
                    length,
                    ql.make_quote_handle(swaption_vols[swap_vol_index]),
                    index,
                    index.tenor(),
                    day_counter,
                    index.day_counter(),
                    curve,
                    ql.CalibrationErrorType.ImpliedVolError,
                )
                swap_vol_index += 1
                swaption_helper.set_lfm_pricing_engine(model, discount_curve=curve)
                helpers.append(swaption_helper)

    method = ql.LevenbergMarquardt(1e-6, 1e-6, 1e-6)
    end_criteria = ql.EndCriteria(2000, 100, 1e-6, 1e-6, 1e-6)
    model.calibrate(helpers, method, end_criteria)

    rmse = math.sqrt(sum(h.calibration_error() ** 2 for h in helpers))
    assert rmse < tolerance


def test_compat_phase162_aliases():
    import qlnb.compat as cql

    assert cql.CapHelper is not None
    assert cql.SwaptionHelper is not None
    assert hasattr(cql.CapHelper, "setLfmPricingEngine")
    assert hasattr(cql.SwaptionHelper, "setLfmPricingEngine")
    assert cql.LmExtLinearExponentialVolModel is not None
    assert cql.LmLinearExponentialCorrelationModel is not None
