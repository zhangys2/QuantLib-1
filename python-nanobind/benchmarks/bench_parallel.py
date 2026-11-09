#!/usr/bin/env python3
"""Scaling of ``qlnb.npv_many`` with the number of threads.

Prices a book of American options that share one Black-Scholes process, using
the binomial and finite-difference engines, at several thread counts, and checks
every result is bit-identical to the serial one.  Needs a build with thread-safe
observers (``qlnb.THREAD_SAFE_OBSERVER``); on a default build only the serial
timing is reported.

Usage:
    python benchmarks/bench_parallel.py [--options 800] [--repeats 3]
"""

from __future__ import annotations

import argparse
import math
import os
import time

import numpy as np

import qlnb as ql


def make_book(n: int, engine: str):
    today = ql.Date(15, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(100.0)),
        ql.FlatForward(today, 0.01, dc),
        ql.FlatForward(today, 0.03, dc),
        ql.BlackConstantVol(today, ql.TARGET(), 0.2, dc),
    )
    book = []
    for i in range(n):
        option = ql.VanillaOption(
            ql.PlainVanillaPayoff(ql.OptionType.Put, 80.0 + 40.0 * i / n),
            ql.AmericanExercise(today, today + 365),
        )
        if engine == "binomial":
            option.set_binomial_pricing_engine(process, 200)
        else:
            option.set_fd_pricing_engine(process, 100, 100)
        book.append(option)
    return book


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--options", type=int, default=800)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    cores = os.cpu_count() or 1
    counts = [1] + ([t for t in (2, 4, 8) if t <= 2 * cores] if ql.THREAD_SAFE_OBSERVER else [])
    print(f"thread-safe observers: {ql.THREAD_SAFE_OBSERVER}; cores: {cores}")
    for engine in ("binomial", "fd"):
        reference = None
        base = None
        print(f"{engine}: {args.options} American options, one shared process")
        for threads in counts:
            best = math.inf
            for _ in range(args.repeats):
                book = make_book(args.options, engine)  # fresh, uncalculated
                start = time.perf_counter()
                result = ql.npv_many(book, threads=threads)
                best = min(best, time.perf_counter() - start)
            if reference is None:
                reference, base = result, best
            same = np.array_equal(result, reference)
            print(
                f"  threads={threads}: {best * 1e3:8.1f} ms  "
                f"speedup {base / best:4.2f}x  bit-identical={same}"
            )


if __name__ == "__main__":
    main()
