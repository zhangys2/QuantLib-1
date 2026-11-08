#!/usr/bin/env python3
"""Per-call overhead benchmark: where would vectorized qlnb APIs help most?

For each cheap QuantLib operation this measures the cost of one call made from
a Python loop.  When the operation costs well under a microsecond in C++, the
loop time is mostly interpreter and binding overhead, so an array-in/array-out
wrapper would remove most of it.  Operations that already have an array API
(`discount_times`, `discount_dates`, `simulate_gbm_paths`) are timed against
the equivalent Python loop, which shows how much a vectorized wrapper buys.

Compares qlnb with the official QuantLib SWIG wheel when it is importable.
Reports the best of several repeats, in microseconds per call.

Usage:
    python benchmarks/bench_call_overhead.py [--n 20000] [--repeats 5]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import numpy as np


def best_us_per_call(fn, calls_per_run: int, repeats: int) -> float:
    fn()
    best = math.inf
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best / calls_per_run * 1e6


def build_qlnb(n: int):
    import qlnb as ql

    today = ql.Date(15, ql.Month.May, 1998)
    ref = ql.Date(17, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    cal = ql.TARGET()
    curve = ql.FlatForward(ref, 0.06, dc)
    dates = [ref + (i % 3000) for i in range(n)]
    strikes = np.linspace(80.0, 120.0, n)
    call = ql.OptionType.Call
    following = ql.BusinessDayConvention.Following
    comp = ql.Compounding.Continuous

    forward, std_dev, disc = 100.0, 0.2, 0.97
    prices = [ql.black_formula(call, k, forward, std_dev, disc) for k in strikes[:200]]

    ops = {
        "trivial: Date == Date": lambda: [d == today for d in dates],
        "Date + int": lambda: [d + 1 for d in dates],
        "Calendar.is_business_day": lambda: [cal.is_business_day(d) for d in dates],
        "Calendar.adjust": lambda: [cal.adjust(d, following) for d in dates],
        "DayCounter.year_fraction": lambda: [dc.year_fraction(ref, d) for d in dates],
        "Curve.discount(date)": lambda: [curve.discount(d) for d in dates],
        "Curve.discount(time)": lambda: [curve.discount(0.001 * (i % 3000)) for i in range(n)],
        "Curve.zero_rate(date)": lambda: [curve.zero_rate(d, dc, comp) for d in dates],
        "black_formula": lambda: [
            ql.black_formula(call, k, forward, std_dev, disc) for k in strikes
        ],
        "black_formula_implied_std_dev (200)": lambda: [
            ql.black_formula_implied_std_dev(call, k, forward, p, disc)
            for k, p in zip(strikes[:200], prices)
        ],
    }
    calls = {name: n for name in ops}
    calls["black_formula_implied_std_dev (200)"] = 200

    # Array APIs that already exist, timed against the loop they replace.
    times = 0.001 * (np.arange(n) % 3000)
    arrays = {
        "discount_times (ndarray)": (lambda: ql.discount_times(curve, times), n),
        "discount_dates (list[Date])": (lambda: ql.discount_dates(curve, dates), n),
    }
    return ops, calls, arrays


def build_swig(n: int):
    import QuantLib as ql

    today = ql.Date(15, ql.May, 1998)
    ref = ql.Date(17, ql.May, 1998)
    ql.Settings.instance().evaluationDate = today
    dc = ql.Actual365Fixed()
    cal = ql.TARGET()
    curve = ql.FlatForward(ref, 0.06, dc)
    dates = [ref + (i % 3000) for i in range(n)]
    strikes = np.linspace(80.0, 120.0, n)
    call = ql.Option.Call
    following = ql.Following
    comp = ql.Continuous

    forward, std_dev, disc = 100.0, 0.2, 0.97
    prices = [ql.blackFormula(call, float(k), forward, std_dev, disc) for k in strikes[:200]]

    ops = {
        "trivial: Date == Date": lambda: [d == today for d in dates],
        "Date + int": lambda: [d + 1 for d in dates],
        "Calendar.is_business_day": lambda: [cal.isBusinessDay(d) for d in dates],
        "Calendar.adjust": lambda: [cal.adjust(d, following) for d in dates],
        "DayCounter.year_fraction": lambda: [dc.yearFraction(ref, d) for d in dates],
        "Curve.discount(date)": lambda: [curve.discount(d) for d in dates],
        "Curve.discount(time)": lambda: [curve.discount(0.001 * (i % 3000)) for i in range(n)],
        "Curve.zero_rate(date)": lambda: [curve.zeroRate(d, dc, comp) for d in dates],
        "black_formula": lambda: [
            ql.blackFormula(call, float(k), forward, std_dev, disc) for k in strikes
        ],
        "black_formula_implied_std_dev (200)": lambda: [
            ql.blackFormulaImpliedStdDev(call, float(k), forward, p, disc)
            for k, p in zip(strikes[:200], prices)
        ],
    }
    calls = {name: n for name in ops}
    calls["black_formula_implied_std_dev (200)"] = 200
    return ops, calls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20_000)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    q_ops, q_calls, q_arrays = build_qlnb(args.n)
    try:
        s_ops, s_calls = build_swig(args.n)
    except ImportError:
        s_ops, s_calls = None, None

    results: dict[str, dict[str, float | None]] = {}
    header = f"{'operation':38s} {'qlnb us':>9s} {'SWIG us':>9s} {'SWIG/qlnb':>10s}"
    print(header)
    print("-" * len(header))
    for name, fn in q_ops.items():
        q = best_us_per_call(fn, q_calls[name], args.repeats)
        s = (
            best_us_per_call(s_ops[name], s_calls[name], args.repeats)
            if s_ops is not None
            else None
        )
        ratio = f"{s / q:10.2f}" if s is not None else f"{'n/a':>10s}"
        print(f"{name:38s} {q:9.3f} {s if s is not None else float('nan'):9.3f} {ratio}")
        results[name] = {"qlnb_us": q, "swig_us": s}

    loop_date = results["Curve.discount(date)"]["qlnb_us"]
    loop_time = results["Curve.discount(time)"]["qlnb_us"]
    if q_arrays:
        print()
        print("Existing array APIs (us per element) vs the qlnb Python loop")
        for name, (fn, calls) in q_arrays.items():
            us = best_us_per_call(fn, calls, args.repeats)
            loop = loop_time if "times" in name else loop_date
            print(f"{name:38s} {us:9.4f}   loop {loop:7.3f}   speedup {loop / us:7.1f}x")
            results[name] = {"qlnb_us": us, "loop_us": loop}

    out_dir = (
        Path(os.environ["QLNB_BENCH_OUT"])
        if "QLNB_BENCH_OUT" in os.environ
        else Path(__file__).resolve().parent / "out"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bench_call_overhead.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
