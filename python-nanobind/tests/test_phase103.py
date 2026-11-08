"""Phase-103 tests: VanillaStorageOption (ExtOU FD cached NPV)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase103():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 4)


def _storage_setup():
    # VPPOptionTest::testSimpleExtOUStorageEngine with fixed evaluation date.
    today = ql.Date(18, ql.Month.December, 2011)
    ql.set_evaluation_date(today)
    dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
    maturity = today + ql.Period(12, ql.TimeUnit.Months)

    exercise_dates = [today + ql.Period(1, ql.TimeUnit.Days)]
    while exercise_dates[-1] < maturity:
        exercise_dates.append(exercise_dates[-1] + ql.Period(1, ql.TimeUnit.Days))

    process = ql.ExtendedOrnsteinUhlenbeckProcess(1.0, 0.5, 3.0, 3.0)
    r_ts = ql.FlatForward(today, 0.1, dc)
    return exercise_dates, process, r_ts


def test_simple_extou_storage_cached_npv():
    # VPPOptionTest::testSimpleExtOUStorageEngine — cached 69.5755.
    exercise_dates, process, r_ts = _storage_setup()
    opt = ql.VanillaStorageOption(ql.BermudanExercise(exercise_dates), 50, 0, 1)
    opt.set_fd_pricing_engine(process, r_ts, t_grid=1, x_grid=25)
    assert opt.NPV() == pytest.approx(69.5755, abs=5.0e-2)
    assert opt.is_expired() is False


def test_compat_phase103_aliases():
    import qlnb.compat as c

    assert c.ExtendedOrnsteinUhlenbeckProcess is not None
    assert c.VanillaStorageOption is not None
    assert hasattr(c.VanillaStorageOption, "setPricingEngine")
    assert hasattr(c.VanillaStorageOption, "isExpired")
