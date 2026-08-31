"""Phase-101 tests: VanillaSwingOption (BS FD upper/lower bounds)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase101():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 2)


def _swing_setup():
    # SwingOptionTest::testFdBSSwingOption with a fixed evaluation date.
    today = ql.Date(15, ql.Month.January, 2020)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)

    strike = 30.0
    payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, strike)
    forward = ql.VanillaForwardPayoff(ql.OptionType.Put, strike)

    exercise_dates = [today + ql.Period(1, ql.TimeUnit.Months)]
    while exercise_dates[-1] < maturity:
        exercise_dates.append(exercise_dates[-1] + ql.Period(1, ql.TimeUnit.Months))

    swing_exercise = ql.SwingExercise(exercise_dates)
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(30.0),
        ql.FlatForward(today, 0.02, dc),
        ql.FlatForward(today, 0.14, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.4, dc),
    )
    return today, payoff, forward, exercise_dates, swing_exercise, process


def test_fd_bs_swing_option_bounds():
    # SwingOptionTest::testFdBSSwingOption — upper / lower bounds.
    _today, payoff, forward, exercise_dates, swing_exercise, process = (
        _swing_setup()
    )

    bermudan = ql.VanillaOption(
        payoff, ql.BermudanExercise(exercise_dates)
    )
    bermudan.set_fd_pricing_engine(process, t_grid=50, x_grid=200)
    bermudan_npv = bermudan.NPV()

    for i in range(len(exercise_dates)):
        rights = i + 1
        swing = ql.VanillaSwingOption(forward, swing_exercise, 0, rights)
        swing.set_fd_pricing_engine(process, t_grid=50, x_grid=200)
        swing_npv = swing.NPV()

        upper = rights * bermudan_npv
        assert swing_npv - upper <= 0.01

        lower = 0.0
        for j in range(len(exercise_dates) - i - 1, len(exercise_dates)):
            european = ql.EuropeanOption(
                payoff, ql.EuropeanExercise(exercise_dates[j])
            )
            european.set_pricing_engine(process)
            lower += european.NPV()
        assert lower - swing_npv <= 4.0e-2

    assert swing.is_expired() is False


def test_compat_phase101_aliases():
    import qlnb.compat as c

    assert c.SwingExercise is not None
    assert c.VanillaForwardPayoff is not None
    assert c.VanillaSwingOption is not None
    assert hasattr(c.VanillaSwingOption, "setPricingEngine")
    assert hasattr(c.VanillaSwingOption, "isExpired")
