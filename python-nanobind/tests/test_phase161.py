"""Phase-161 tests: LfmSwaptionEngine + LMM forward swap rates."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase161():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 32)


def _lfm_swaption_index():
    today = ql.Date(4, ql.Month.September, 2005)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    today = calendar.adjust(today)
    ql.set_evaluation_date(today)
    dates = [ql.Date(4, ql.Month.September, 2005), ql.Date(4, ql.Month.September, 2011)]
    rates = [0.04, 0.08]
    dc = ql.Actual360()
    index = ql.Euribor6M(ql.ZeroCurve(dates, rates, dc))
    start = index.fixing_calendar().advance(today, index.fixing_days(), ql.TimeUnit.Days)
    dates[0] = start
    curve = ql.ZeroCurve(dates, rates, dc)
    return ql.Euribor6M(curve), curve


def _lfm_model(size: int = 10):
    index, curve = _lfm_swaption_index()
    process = ql.LiborForwardModelProcess(size, index)
    corr = ql.LmExponentialCorrelationModel(size, 0.5)
    vola = ql.LmLinearExponentialVolatilityModel(
        process.fixing_times(), 0.291, 1.483, 0.116, 0.00001
    )
    process.set_covar_param(ql.LfmCovarianceProxy(vola, corr))
    model = ql.LiborForwardModel(process, vola, corr)
    return index, curve, process, model


def _forward_receiver_swap(
    index: ql.Euribor6M, curve: ql.YieldTermStructureHandle, i: int, j: int, swap_rate: float
):
    calendar = index.fixing_calendar()
    convention = index.business_day_convention()
    settlement = curve.reference_date()
    fwd_start = settlement + ql.Period(6 * i, ql.TimeUnit.Months)
    fwd_maturity = fwd_start + ql.Period(6 * j, ql.TimeUnit.Months)
    schedule = ql.Schedule(
        fwd_start,
        fwd_maturity,
        index.tenor(),
        calendar,
        convention,
        convention,
        ql.DateGeneration.Forward,
        False,
    )
    day_counter = ql.Actual360()
    swap = ql.VanillaSwap(
        ql.SwapType.Receiver,
        1.0,
        schedule,
        swap_rate,
        day_counter,
        schedule,
        index,
        0.0,
        index.day_counter(),
    )
    swap.set_pricing_engine(curve)
    return swap, schedule


def test_lfm_forward_swap_rate_matches_s0():
    # LiborMarketModelTests::testSwaptionPricing forward-rate check.
    index, curve, _, model = _lfm_model()
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            if i + j > 10:
                continue
            swap, _ = _forward_receiver_swap(index, curve, i, j, 0.0404)
            assert model.s_0(i - 1, i + j - 1) == pytest.approx(
                swap.fair_rate(), abs=1e-12
            )


def test_lfm_swaption_npv():
    # Same test case: i == j == 1 European swaption on fair-rate receiver swap.
    index, curve, process, model = _lfm_model()
    i = j = 1
    swap, _ = _forward_receiver_swap(index, curve, i, j, 0.0404)
    fair = swap.fair_rate()
    swap, _ = _forward_receiver_swap(index, curve, i, j, fair)
    exercise = ql.EuropeanExercise(process.fixing_dates()[i])
    swaption = ql.Swaption(swap, exercise)
    swaption.set_lfm_pricing_engine(model, curve)
    assert swaption.NPV() == pytest.approx(0.001124392271618904, abs=1e-12)


def test_compat_phase161_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.Swaption, "setLfmPricingEngine")
    assert cql.LfmSwaptionEngine is not None
    assert cql.LmLinearExponentialVolatilityModel is not None
