"""Phase-173 tests: SmileSectionUtils W-shaped smile."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase173():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 44)


def test_smile_section_utils_w_shaped_smile():
    # MarkovFunctionalTests::testSmileSectionUtilsWShapedSmile
    atm = 0.05
    t = 1.0
    strikes = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    vols = [0.35, 0.15, 0.40, 0.15, 0.35, 0.15, 0.40, 0.15, 0.35, 0.20]
    money = [strike / atm for strike in strikes]
    calls = [
        ql.black_formula(
            ql.OptionType.Call, strike, atm, vol * (t**0.5), 1.0, 0.0
        )
        for strike, vol in zip(strikes, vols)
    ]
    std_devs = [
        ql.black_formula_implied_std_dev(
            ql.OptionType.Call, strike, atm, price, 1.0, 0.0, 0.2, 1e-8, 1000
        )
        for strike, price in zip(strikes, calls)
    ]
    sec = ql.LinearSmileSection(t, strikes, std_devs, atm)
    utils = ql.SmileSectionUtils(sec, money, atm)
    left, right = utils.arbitragefree_indices()
    assert right > left


def test_compat_phase173_aliases():
    import qlnb.compat as cql

    assert cql.SmileSectionUtils is not None
    assert hasattr(cql.SmileSectionUtils, "arbitragefreeIndices")
