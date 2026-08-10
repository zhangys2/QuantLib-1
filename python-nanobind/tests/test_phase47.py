"""Phase-47 tests: FdmSchemeDesc for FD engines."""

from __future__ import annotations

import pytest

import qlnb as ql


def test_version_is_phase47():
    assert ql.__version__ == "0.48.0"


def test_fdm_scheme_desc_factories():
    h = ql.FdmSchemeDesc.Hundsdorfer()
    assert h.type == ql.FdmSchemeType.Hundsdorfer
    assert h.theta == h.theta
    assert h.mu == h.mu

    d = ql.FdmSchemeDesc.Douglas()
    assert d.type == ql.FdmSchemeType.Douglas

    cs = ql.FdmSchemeDesc.CraigSneyd()
    assert cs.type == ql.FdmSchemeType.CraigSneyd

    mcs = ql.FdmSchemeDesc.ModifiedCraigSneyd()
    assert mcs.type == ql.FdmSchemeType.ModifiedCraigSneyd

    cn = ql.FdmSchemeDesc.CrankNicolson()
    assert cn.type == ql.FdmSchemeType.CrankNicolson

    mol = ql.FdmSchemeDesc.MethodOfLines(eps=0.002, rel_init_step_size=0.02)
    assert mol.type == ql.FdmSchemeType.MethodOfLines

    custom = ql.FdmSchemeDesc(ql.FdmSchemeType.TrBDF2, 0.5, 0.0)
    assert custom.type == ql.FdmSchemeType.TrBDF2
    assert custom.theta == pytest.approx(0.5)
    assert custom.mu == pytest.approx(0.0)


def test_fd_heston_with_explicit_scheme():
    # Same setup as phase-37 American FD Heston; explicit Hundsdorfer matches.
    today = ql.Date(28, ql.Month.March, 2004)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,
        2.5,
        0.04,
        0.66,
        -0.8,
    )
    model = ql.HestonModel(process)
    maturity = ql.Date(28, ql.Month.March, 2005)
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0),
        ql.AmericanExercise(today, maturity),
    )
    option.set_fd_heston_pricing_engine(
        model,
        t_grid=200,
        x_grid=100,
        v_grid=50,
        scheme_desc=ql.FdmSchemeDesc.Hundsdorfer(),
    )
    assert option.NPV() == pytest.approx(5.66032, abs=0.01)


def test_fd_heston_craig_sneyd_runs():
    today = ql.Date(28, ql.Month.March, 2004)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.HestonProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(100.0),
        0.04,
        2.5,
        0.04,
        0.66,
        -0.8,
    )
    model = ql.HestonModel(process)
    option = ql.EuropeanOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0),
        ql.EuropeanExercise(ql.Date(28, ql.Month.March, 2005)),
    )
    option.set_fd_heston_pricing_engine(
        model,
        t_grid=50,
        x_grid=50,
        v_grid=30,
        scheme_desc=ql.FdmSchemeDesc.CraigSneyd(),
    )
    assert option.NPV() > 0.0


def test_fd_bs_douglas_scheme():
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(100.0),
        ql.FlatForward(today, 0.0, dc),
        ql.FlatForward(today, 0.05, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.2, dc),
    )
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0),
        ql.AmericanExercise(today, today + 365),
    )
    option.set_fd_pricing_engine(
        process,
        t_grid=50,
        x_grid=51,
        scheme_desc=ql.FdmSchemeDesc.Douglas(),
    )
    assert option.NPV() > 0.0
