"""Phase-174 tests: LMM MultiPathGenerator swaption MC loop."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase174():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 45)


def _lfm_swaption_setup(size: int = 10):
    today = ql.Date(4, ql.Month.September, 2005)
    ql.set_evaluation_date(today)
    calendar = ql.TARGET()
    today = calendar.adjust(today)
    ql.set_evaluation_date(today)
    dates = [ql.Date(4, ql.Month.September, 2005), ql.Date(4, ql.Month.September, 2011)]
    rates = [0.04, 0.08]
    dc = ql.Actual360()
    index = ql.Euribor6M(ql.ZeroCurve(dates, rates, dc))
    start = index.fixing_calendar().advance(
        today, index.fixing_days(), ql.TimeUnit.Days
    )
    dates[0] = start
    curve = ql.ZeroCurve(dates, rates, dc)
    index = ql.Euribor6M(curve)
    process = ql.LiborForwardModelProcess(size, index)
    corr = ql.LmExponentialCorrelationModel(size, 0.5)
    vola = ql.LmLinearExponentialVolatilityModel(
        process.fixing_times(), 0.291, 1.483, 0.116, 0.00001
    )
    process.set_covar_param(ql.LfmCovarianceProxy(vola, corr))
    model = ql.LiborForwardModel(process, vola, corr)
    return index, curve, process, model


def _forward_receiver_swap(index, curve, i: int, j: int, swap_rate: float):
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
    return swap


def test_mc_swaption_matches_lfm_engine():
    # LiborMarketModelTests::testSwaptionPricing — MC loop for i == j == 1
    size = 10
    steps = 8 * size
    nr_trails = 5000
    index, curve, process, model = _lfm_swaption_setup(size)

    tmp = process.fixing_times()
    grid = ql.TimeGrid(tmp, steps)
    locations = [grid.index(t) for t in tmp]
    gen = ql.MultiPathGenerator(process, grid, seed=42)

    i = j = 1
    swap = _forward_receiver_swap(index, curve, i, j, 0.0404)
    swap_rate = swap.fair_rate()
    swap = _forward_receiver_swap(index, curve, i, j, swap_rate)
    exercise = ql.EuropeanExercise(process.fixing_dates()[i])
    swaption = ql.Swaption(swap, exercise)
    swaption.set_lfm_pricing_engine(model, curve)
    engine_npv = swaption.NPV()

    accr_start = process.accrual_start_times()
    accr_end = process.accrual_end_times()
    loc = locations[i]
    stat = ql.GeneralStatistics()
    for n in range(nr_trails):
        path = gen.antithetic() if n % 2 else gen.next()
        rates = [path[k][loc] for k in range(process.size())]
        dis = process.discount_bond(rates)
        npv = 0.0
        for m in range(i, i + j):
            npv += (swap_rate - rates[m]) * (accr_end[m] - accr_start[m]) * dis[m]
        stat.add(max(npv, 0.0))

    assert abs(engine_npv - stat.mean()) <= stat.error_estimate() * 2.35


def test_compat_phase174_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.LiborForwardModelProcess, "discountBond")
    assert hasattr(cql.LiborForwardModelProcess, "accrualStartTimes")
    assert hasattr(cql.GeneralStatistics, "errorEstimate")
    assert cql.MultiPathGenerator is not None
    assert cql.TimeGrid is not None
