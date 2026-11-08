"""npv_many(): batch NPV with the GIL released.

Threaded runs are only exercised on a build with thread-safe observers
(``qlnb.THREAD_SAFE_OBSERVER``); the default build must refuse them.
"""

from __future__ import annotations

import numpy as np
import pytest

import qlnb as ql

THREADED = ql.THREAD_SAFE_OBSERVER
needs_threads = pytest.mark.skipif(
    not THREADED, reason="needs QLNB_THREAD_SAFE_OBSERVER=ON build"
)

TODAY = ql.Date(15, ql.Month.May, 1998)
DC = ql.Actual365Fixed()
CAL = ql.TARGET()


def _process() -> ql.BlackScholesMertonProcess:
    return ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(100.0)),
        ql.FlatForward(TODAY, 0.01, DC),
        ql.FlatForward(TODAY, 0.03, DC),
        ql.BlackConstantVol(TODAY, CAL, 0.2, DC),
    )


def _book(process: ql.BlackScholesMertonProcess, n: int = 60) -> list:
    """Mixed book that shares one process / one curve (the usual layout)."""
    ql.set_evaluation_date(TODAY)
    curve = ql.FlatForward(TODAY, 0.04, DC)
    schedule = ql.Schedule(
        TODAY,
        ql.Date(15, ql.Month.May, 2008),
        ql.Period(ql.Frequency.Annual),
        CAL,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    book = []
    for i in range(n):
        strike = 80.0 + 40.0 * i / n
        kind = i % 4
        if kind == 0:
            o = ql.VanillaOption(
                ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
                ql.AmericanExercise(TODAY, TODAY + 365),
            )
            o.set_binomial_pricing_engine(process, 40)
        elif kind == 1:
            o = ql.VanillaOption(
                ql.PlainVanillaPayoff(ql.OptionType.Put, strike),
                ql.AmericanExercise(TODAY, TODAY + 365),
            )
            o.set_fd_pricing_engine(process, 20, 40)
        elif kind == 2:
            o = ql.EuropeanOption(
                ql.PlainVanillaPayoff(ql.OptionType.Call, strike),
                ql.EuropeanExercise(TODAY + 200),
            )
            o.set_pricing_engine(ql.AnalyticEuropeanEngine(process))
        else:
            o = ql.FixedRateBond(
                3,
                100.0,
                schedule,
                [0.03 + 0.0005 * i],
                ql.Thirty360(ql.Thirty360Convention.BondBasis),
                ql.BusinessDayConvention.Following,
                100.0,
                TODAY,
            )
            o.set_pricing_engine(curve)
        book.append(o)
    return book


def _serial_reference(n: int = 60) -> np.ndarray:
    # Fresh, uncalculated instruments, priced one by one through the normal API.
    return np.array([o.NPV() for o in _book(_process(), n)])


def test_module_exposes_build_flag():
    assert isinstance(ql.THREAD_SAFE_OBSERVER, bool)


def test_serial_matches_individual_npv():
    ref = _serial_reference()
    got = ql.npv_many(_book(_process()), threads=1)
    assert got.dtype == np.float64
    assert got.shape == ref.shape
    assert np.array_equal(got, ref)


def test_default_threads_always_works_and_matches():
    # threads=0 is serial on a default build and parallel on a thread-safe one.
    ref = _serial_reference()
    assert np.array_equal(ql.npv_many(_book(_process())), ref)


@pytest.mark.parametrize("warmup", [True, False])
def test_warmup_flag_gives_same_values_serially(warmup):
    ref = _serial_reference()
    assert np.array_equal(ql.npv_many(_book(_process()), threads=1, warmup=warmup), ref)


def test_empty_sequence_gives_empty_array():
    out = ql.npv_many([])
    assert out.shape == (0,)


def test_accepts_any_sequence_and_keeps_cached_results():
    book = _book(_process(), 8)
    first = ql.npv_many(tuple(book), threads=1)
    # Already calculated: a second call returns identical values.
    assert np.array_equal(ql.npv_many(book, threads=1), first)
    assert first[0] == book[0].NPV()


def test_unsupported_type_is_rejected():
    with pytest.raises(TypeError, match="unsupported instrument type"):
        ql.npv_many([_book(_process(), 4)[0], object()], threads=1)


def test_negative_threads_is_rejected():
    with pytest.raises(ValueError, match="threads"):
        ql.npv_many(_book(_process(), 4), threads=-1)


def test_error_names_the_failing_element():
    book = _book(_process(), 8)
    # An option without a pricing engine fails to price.
    bare = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(TODAY + 100),
    )
    book[5] = bare
    with pytest.raises(RuntimeError, match=r"element 5:"):
        ql.npv_many(book, threads=1)


@pytest.mark.skipif(THREADED, reason="only the default build refuses threads")
def test_default_build_refuses_threads():
    with pytest.raises(RuntimeError, match="thread-safe observers"):
        ql.npv_many(_book(_process(), 4), threads=2)


@needs_threads
@pytest.mark.parametrize("threads", [2, 4, 8])
def test_threaded_matches_serial_on_shared_process(threads):
    ref = _serial_reference()
    # The shared process / curve is the layout that corrupts the heap without
    # thread-safe observers (binomial engine builds temporary observers).
    for _ in range(5):
        got = ql.npv_many(_book(_process()), threads=threads)
        assert np.array_equal(got, ref)


@needs_threads
def test_threaded_without_warmup_matches_serial():
    ref = _serial_reference()
    got = ql.npv_many(_book(_process()), threads=4, warmup=False)
    assert np.array_equal(got, ref)


@needs_threads
def test_threaded_error_names_an_element():
    book = _book(_process(), 40)
    book[23] = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
        ql.EuropeanExercise(TODAY + 100),
    )
    with pytest.raises(RuntimeError, match=r"element 23:"):
        ql.npv_many(book, threads=4)


@needs_threads
def test_more_threads_than_instruments():
    ref = _serial_reference(3)
    assert np.array_equal(ql.npv_many(_book(_process(), 3), threads=16), ref)


def _bond_book(curve: ql.YieldTermStructureHandle, n: int = 200) -> list:
    schedule = ql.Schedule(
        TODAY,
        ql.Date(15, ql.Month.May, 2008),
        ql.Period(ql.Frequency.Annual),
        CAL,
        ql.BusinessDayConvention.Unadjusted,
        ql.BusinessDayConvention.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    book = []
    for i in range(n):
        b = ql.FixedRateBond(
            3,
            100.0,
            schedule,
            [0.02 + 0.0001 * i],
            ql.Thirty360(ql.Thirty360Convention.BondBasis),
            ql.BusinessDayConvention.Following,
            100.0,
            TODAY,
        )
        b.set_pricing_engine(curve)
        book.append(b)
    return book


@needs_threads
def test_threaded_shared_lazy_curve_is_primed():
    # A freshly built curve is a lazy object that computes on first use.  Many
    # threads reaching it at once used to see it half initialised
    # ("null interest rate", or silently wrong values).  Fresh curve each round.
    ql.set_evaluation_date(TODAY)
    ref_curve = ql.FlatForward(TODAY, 0.04, DC)
    ref = np.array([b.NPV() for b in _bond_book(ref_curve)])
    for _ in range(150):
        curve = ql.FlatForward(TODAY, 0.04, DC)
        got = ql.npv_many(_bond_book(curve), threads=8, warmup=False)
        assert np.array_equal(got, ref)
