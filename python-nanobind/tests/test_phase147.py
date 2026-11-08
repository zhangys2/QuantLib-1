"""Phase-147 tests: FdBlackScholesShoutEngine."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase147():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 18)


# AmericanOptionTests::testFDShoutNPV
_CASES = [
    (105.0, ql.OptionType.Put, 19.136),
    (105.0, ql.OptionType.Call, 28.211),
    (120.0, ql.OptionType.Put, 28.02),
    (80.0, ql.OptionType.Call, 40.785),
]


@pytest.mark.parametrize("strike,option_type,expected", _CASES)
def test_fd_shout_npv(strike, option_type, expected):
    today = ql.Date(4, ql.Month.February, 2021)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.03, dc),
        ql.FlatForward(today, 0.06, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), 0.25, dc),
    )
    maturity = today + ql.Period(5, ql.TimeUnit.Years)
    opt = ql.VanillaOption(
        ql.PlainVanillaPayoff(option_type, strike),
        ql.AmericanExercise(maturity),
    )
    opt.set_fd_shout_pricing_engine(process, t_grid=400, x_grid=200)
    assert opt.NPV() == pytest.approx(expected, abs=2e-2)


def test_compat_phase147_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.VanillaOption, "setFdShoutPricingEngine")
    assert cql.FdBlackScholesShoutEngine is not None
