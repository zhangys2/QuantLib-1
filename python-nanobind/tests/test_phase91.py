"""Phase-91 tests: BondForward (suite futures price 207.47)."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase91():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (0, 92)


def _common_bond():
    # BondForwardTests::CommonVars + buildBond (2.5% Aug-15 / Aug-46).
    today = ql.Date(7, ql.Month.March, 2022)
    ql.set_evaluation_date(today)
    curve = ql.FlatForward(today, 0.0004977, ql.Actual365Fixed())
    schedule = ql.Schedule(
        ql.Date(15, ql.Month.August, 2015),
        ql.Date(15, ql.Month.August, 2046),
        ql.Period(ql.Frequency.Annual),
        ql.TARGET(),
        ql.BusinessDayConvention.Following,
        ql.BusinessDayConvention.Following,
        ql.DateGeneration.Backward,
        False,
    )
    bond = ql.FixedRateBond(
        2,
        1.0e5,
        schedule,
        [0.025],
        ql.ActualActual(ql.ActualActualConvention.ISDA),
    )
    bond.set_pricing_engine(curve)
    return today, curve, bond


def _bond_forward(curve, bond, delivery):
    return ql.BondForward(
        curve.reference_date(),
        delivery,
        ql.Position.Long,
        0.0,
        2,
        ql.ActualActual(ql.ActualActualConvention.ISDA),
        ql.TARGET(),
        ql.BusinessDayConvention.Following,
        bond,
        curve,
        curve,
    )


def test_futures_price_replication():
    # BondForwardTests::testFuturesPriceReplication — conversion 0.76871.
    _today, curve, bond = _common_bond()
    delivery = ql.Date(10, ql.Month.March, 2022)
    fwd = _bond_forward(curve, bond, delivery)
    futures_price = fwd.clean_forward_price() / 0.76871
    assert futures_price == pytest.approx(207.47, abs=1.0e-2)
    assert fwd.is_expired() is False


def test_clean_forward_price_replication():
    # BondForwardTests::testCleanForwardPriceReplication.
    _today, curve, bond = _common_bond()
    delivery = ql.Date(10, ql.Month.March, 2022)
    fwd = _bond_forward(curve, bond, delivery)
    expected = fwd.forward_value() - bond.accrued_amount(delivery)
    assert fwd.clean_forward_price() == pytest.approx(expected, abs=1.0e-2)
    assert fwd.forward_price() == pytest.approx(fwd.forward_value(), abs=0.0)


def test_forward_value_equals_spot_if_no_income():
    # BondForwardTests::testThatForwardValueIsEqualToSpotValueIfNoIncome.
    _today, curve, bond = _common_bond()
    delivery = ql.Date(10, ql.Month.March, 2022)
    fwd = _bond_forward(curve, bond, delivery)
    assert fwd.forward_value() == pytest.approx(bond.dirty_price(), abs=1.0e-2)
    assert fwd.spot_value() == pytest.approx(bond.dirty_price(), abs=1.0e-2)
    assert fwd.spot_income(curve) == pytest.approx(0.0, abs=1.0e-10)


def test_compat_phase91_aliases():
    import qlnb.compat as cql

    assert cql.BondForward is not None
    assert hasattr(cql.BondForward, "cleanForwardPrice")
    assert hasattr(cql.BondForward, "forwardValue")
    assert hasattr(cql.BondForward, "spotValue")
    assert hasattr(cql.BondForward, "settlementDate")
