"""Phase-193 tests: NumPy array APIs that take dates as serial-number arrays."""

from __future__ import annotations

import numpy as np
import pytest

import qlnb as ql

REF = ql.Date(17, ql.Month.May, 1998)
DC = ql.Actual365Fixed()


def _serials(n=40, step=37):
    return np.array([REF.serial_number() + step * i for i in range(n)], dtype=np.int64)


def _non_flat_curve():
    ql.set_evaluation_date(ql.Date(15, ql.Month.May, 1998))
    dates = [REF, REF + 365, REF + 3 * 365, REF + 10 * 365]
    return ql.ZeroCurve(dates, [0.02, 0.035, 0.05, 0.045], DC)


def test_version_is_phase193():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 64)


def test_date_serials_round_trip():
    dates = [REF + i for i in (0, 1, 30, 400)]
    serials = ql.date_serials(dates)
    assert serials.dtype == np.int64
    assert list(serials) == [d.serial_number() for d in dates]
    assert ql.dates_from_serials(serials) == dates
    assert ql.dates_from_serials([d.serial_number() for d in dates]) == dates
    assert ql.date_serials([]).shape == (0,)


def test_dates_from_serials_reports_the_bad_element():
    with pytest.raises(Exception, match="element 1"):
        ql.dates_from_serials([REF.serial_number(), 1])


@pytest.mark.parametrize("make_curve", [lambda: ql.FlatForward(REF, 0.06, DC), _non_flat_curve])
def test_discount_serials_matches_scalar(make_curve):
    curve = make_curve()
    serials = _serials()
    got = ql.discount_serials(curve, serials)
    want = [curve.discount(ql.Date(int(s))) for s in serials]
    assert got.dtype == np.float64
    np.testing.assert_array_equal(got, want)


def test_discount_serials_extrapolation_is_explicit():
    curve = _non_flat_curve()
    beyond = np.array([(REF + 20 * 365).serial_number()], dtype=np.int64)
    with pytest.raises(Exception, match="element 0"):
        ql.discount_serials(curve, beyond)
    assert ql.discount_serials(curve, beyond, extrapolate=True)[0] == pytest.approx(
        curve.discount(REF + 20 * 365, extrapolate=True)
    )


def test_zero_rates_serials_matches_scalar():
    curve = _non_flat_curve()
    serials = _serials(30)[1:]  # skip the reference date itself
    got = ql.zero_rates_serials(curve, serials, DC, ql.Compounding.Continuous)
    want = [
        curve.zero_rate(ql.Date(int(s)), DC, ql.Compounding.Continuous).rate()
        for s in serials
    ]
    np.testing.assert_array_equal(got, want)


def test_forward_rates_serials_matches_scalar_and_broadcasts():
    curve = _non_flat_curve()
    ends = _serials(20)[1:]
    start = REF + 30
    got = ql.forward_rates_serials(
        curve, start.serial_number(), ends, DC, ql.Compounding.Continuous
    )
    want = [
        curve.forward_rate(start, ql.Date(int(e)), DC, ql.Compounding.Continuous).rate()
        for e in ends
    ]
    np.testing.assert_array_equal(got, want)


def test_year_fractions_serials_matches_scalar_and_broadcasts():
    serials = _serials()
    got = ql.year_fractions_serials(DC, REF.serial_number(), serials)
    want = [DC.year_fraction(REF, ql.Date(int(s))) for s in serials]
    np.testing.assert_array_equal(got, want)
    pairwise = ql.year_fractions_serials(DC, serials[:-1], serials[1:])
    assert pairwise.shape == (len(serials) - 1,)
    np.testing.assert_allclose(pairwise, 37 / 365.0)


def test_mismatched_lengths_are_rejected():
    with pytest.raises(Exception, match="length"):
        ql.year_fractions_serials(DC, _serials(5), _serials(7))


def test_calendar_adjust_and_business_day():
    cal = ql.TARGET()
    serials = _serials(60, step=1)
    business = ql.is_business_day_serials(cal, serials)
    assert business.dtype == np.bool_
    assert list(business) == [cal.is_business_day(ql.Date(int(s))) for s in serials]
    assert not business.all() and business.any()  # weekends are in the range
    for convention in (
        ql.BusinessDayConvention.Following,
        ql.BusinessDayConvention.ModifiedFollowing,
        ql.BusinessDayConvention.Preceding,
    ):
        got = ql.adjust_serials(cal, serials, convention)
        want = [cal.adjust(ql.Date(int(s)), convention).serial_number() for s in serials]
        assert got.dtype == np.int64
        assert list(got) == want
    assert all(ql.is_business_day_serials(cal, ql.adjust_serials(cal, serials)))


def test_black_formula_array_matches_scalar():
    strikes = np.linspace(70.0, 130.0, 25)
    for option_type in (ql.OptionType.Call, ql.OptionType.Put):
        got = ql.black_formula_array(option_type, strikes, 100.0, 0.25, 0.97)
        want = [ql.black_formula(option_type, k, 100.0, 0.25, 0.97) for k in strikes]
        np.testing.assert_array_equal(got, want)


def test_black_formula_array_broadcasts_every_argument():
    std_devs = np.array([0.1, 0.2, 0.3])
    forwards = np.array([95.0, 100.0, 105.0])
    got = ql.black_formula_array(ql.OptionType.Call, 100.0, forwards, std_devs, [0.9])
    want = [
        ql.black_formula(ql.OptionType.Call, 100.0, f, s, 0.9)
        for f, s in zip(forwards, std_devs)
    ]
    np.testing.assert_array_equal(got, want)


def test_black_formula_implied_std_dev_array_round_trip():
    strikes = np.linspace(85.0, 115.0, 13)
    std_dev = 0.22
    prices = ql.black_formula_array(ql.OptionType.Call, strikes, 100.0, std_dev, 0.95)
    got = ql.black_formula_implied_std_dev_array(
        ql.OptionType.Call, strikes, 100.0, prices, 0.95
    )
    np.testing.assert_allclose(got, std_dev, atol=1e-7)
    scalar = [
        ql.black_formula_implied_std_dev(ql.OptionType.Call, k, 100.0, p, 0.95)
        for k, p in zip(strikes, prices)
    ]
    np.testing.assert_array_equal(got, scalar)


def test_implied_std_dev_failure_names_the_element():
    with pytest.raises(Exception, match="element 1"):
        ql.black_formula_implied_std_dev_array(
            ql.OptionType.Call, 100.0, 100.0, [5.0, -1.0], 1.0
        )


def test_empty_and_list_inputs():
    curve = ql.FlatForward(REF, 0.05, DC)
    assert ql.discount_serials(curve, np.array([], dtype=np.int64)).shape == (0,)
    assert ql.black_formula_array(ql.OptionType.Put, [], 100.0, 0.2).shape == (0,)
    as_list = ql.discount_serials(curve, [int(s) for s in _serials(5)])
    as_int32 = ql.discount_serials(curve, _serials(5).astype(np.int32))
    np.testing.assert_array_equal(as_list, as_int32)


def test_non_1d_input_is_rejected():
    curve = ql.FlatForward(REF, 0.05, DC)
    with pytest.raises(Exception):
        ql.discount_serials(curve, _serials(6).reshape(2, 3))
