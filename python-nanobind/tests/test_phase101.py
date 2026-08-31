"""Phase-101 tests: AmortizingFixedRateBond (French amortization cashflows)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase101():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (1, 2)


# AmortizingBondTests::testAmortizingFixedRateBond — Excel PMT(rate/12, 360, -100).
_RATES = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12]
_PMT_AMOUNTS = [
    0.277777778,
    0.321639520,
    0.369619473,
    0.421604034,
    0.477415295,
    0.536821623,
    0.599550525,
    0.665302495,
    0.733764574,
    0.804622617,
    0.877571570,
    0.952323396,
    1.028612597,
]


def test_amortizing_fixed_rate_bond_french_pmt():
    freq = ql.Frequency.Monthly
    ref = ql.get_evaluation_date()
    tol = 1.0e-6
    bond_length = ql.Period(30, ql.TimeUnit.Years)

    for rate, expected_pmt in zip(_RATES, _PMT_AMOUNTS):
        schedule = ql.sinking_schedule(
            ref, bond_length, freq, ql.NullCalendar()
        )
        notionals = ql.sinking_notionals(bond_length, freq, rate, 100.0)
        bond = ql.AmortizingFixedRateBond(
            0,
            notionals,
            schedule,
            [rate],
            ql.ActualActual(ql.ActualActualConvention.ISMA),
        )
        amounts = bond.cashflow_amounts()
        assert bond.frequency() == freq

        # Coupons and principal amortizations alternate.
        n_pairs = len(amounts) // 2
        assert n_pairs == len(notionals) - 1 or n_pairs == len(notionals)
        for k in range(n_pairs):
            coupon = amounts[2 * k]
            principal = amounts[2 * k + 1]
            assert abs(coupon + principal - expected_pmt) < tol
            expected_coupon = notionals[k] * rate / 12.0
            assert abs(coupon - expected_coupon) < tol


def test_amortizing_fixed_rate_bond_npv():
    today = ql.Date(15, ql.Month.January, 2020)
    ql.set_evaluation_date(today)
    freq = ql.Frequency.Monthly
    bond_length = ql.Period(10, ql.TimeUnit.Years)
    rate = 0.05
    schedule = ql.sinking_schedule(
        today, bond_length, freq, ql.NullCalendar()
    )
    notionals = ql.sinking_notionals(bond_length, freq, rate, 100.0)
    bond = ql.AmortizingFixedRateBond(
        0,
        notionals,
        schedule,
        [rate],
        ql.ActualActual(ql.ActualActualConvention.ISMA),
    )
    curve = ql.FlatForward(today, 0.03, ql.Actual365Fixed())
    bond.set_pricing_engine(curve)
    npv = bond.NPV()
    assert npv == pytest.approx(bond.dirty_price(), abs=1e-10)
    assert npv > 0.0
    # Discount below coupon → price above par (initial notional 100).
    assert npv > 100.0


def test_amortizing_floating_rate_bond_constructs():
    today = ql.Date(15, ql.Month.January, 2020)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.03, ql.Actual365Fixed())
    index = ql.Euribor6M(curve)
    cal = index.fixing_calendar()
    start = cal.adjust(today)
    end = cal.advance(start, 2, ql.TimeUnit.Years)
    schedule = ql.Schedule(
        start,
        end,
        ql.Period(6, ql.TimeUnit.Months),
        cal,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.DateGeneration.Forward,
        False,
    )
    # One notional per coupon period (IborLeg.withNotionals).
    n_coupons = len(schedule) - 1
    notionals = [100.0 - (100.0 / n_coupons) * i for i in range(n_coupons)]
    bond = ql.AmortizingFloatingRateBond(
        2,
        notionals,
        schedule,
        index,
        ql.Actual360(),
    )
    bond.set_pricing_engine(curve)
    assert len(bond.cashflow_amounts()) >= 2
    assert bond.NPV() != 0.0


def test_compat_phase101_aliases():
    import qlnb.compat as cql

    assert cql.AmortizingFixedRateBond is not None
    assert cql.sinkingSchedule is not None
    assert cql.sinkingNotionals is not None
    assert hasattr(cql.AmortizingFixedRateBond, "cashflowAmounts")
    assert hasattr(cql.AmortizingFixedRateBond, "setPricingEngine")
    assert hasattr(cql.AmortizingFloatingRateBond, "setPricingEngine")
