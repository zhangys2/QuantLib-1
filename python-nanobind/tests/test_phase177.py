"""Phase-177 tests: LMM process next-index-reset initialisation."""

from __future__ import annotations

import qlnb as ql


def test_version_is_phase177():
    parts = tuple(int(x) for x in ql.__version__.split(".")[:2])
    assert parts >= (4, 48)


def test_process_next_index_reset():
    # LiborMarketModelProcessTests::testInitialisation
    dc = ql.Actual360()
    calendar = ql.TARGET()
    seed_index = ql.Euribor6M(ql.FlatForward(ql.Date.todays_date(), 0.04, dc))

    for days_offset in range(0, 1825, 8):
        todays_date = calendar.adjust(ql.Date.todays_date() + days_offset)
        ql.set_evaluation_date(todays_date)
        settlement = calendar.advance(
            todays_date, seed_index.fixing_days(), ql.TimeUnit.Days
        )
        curve = ql.FlatForward(settlement, 0.04, dc)
        index = ql.Euribor6M(curve)
        process = ql.LiborForwardModelProcess(60, index)
        fixings = process.fixing_times()
        for i in range(1, len(fixings) - 1):
            t = fixings[i]
            assert process.next_index_reset(t - 0.000001) == i
            assert process.next_index_reset(t + 0.000001) == i + 1
            assert process.next_index_reset(t) == i + 1


def test_compat_phase177_aliases():
    import qlnb.compat as cql

    assert hasattr(cql.LiborForwardModelProcess, "nextIndexReset")
