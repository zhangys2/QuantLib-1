"""Phase-196 tests: attribute-syntax spellings of keyword-named members."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase196():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 67)


def test_gjr_garch_lambda_alias_matches_old_spelling():
    today = ql.Date(15, ql.Month.May, 1998)
    dc = ql.Actual365Fixed()
    process = ql.GJRGARCHProcess(
        ql.FlatForward(today, 0.05, dc),
        ql.FlatForward(today, 0.0, dc),
        ql.make_quote_handle(50.0),
        0.0003,
        2.0e-6,
        0.024,
        0.93,
        0.059,
        0.2,
        365.0,
    )
    assert process.lambda_() == getattr(process, "lambda")()
    assert process.lambda_() == 0.2
    model = ql.GJRGARCHModel(process)
    assert model.lambda_() == getattr(model, "lambda")() == 0.2
