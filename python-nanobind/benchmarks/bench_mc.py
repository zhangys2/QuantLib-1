#!/usr/bin/env python3
"""Monte Carlo benchmark: path generation, MC pricing and random-number draws.

Three questions, answered with best-of-N wall times:

1. Path generation.  `qlnb.simulate_gbm_paths` fills one NumPy array in C++.
   The SWIG wheel has to be driven path by path from Python, so it is timed
   with that loop.  A plain NumPy log-normal simulation is the native ceiling.
2. MC pricing.  `EuropeanOption.set_mc_pricing_engine` against SWIG's
   `MCEuropeanEngine` for the same samples and time steps, and against the
   "paths to NumPy, payoff in NumPy" workflow.
3. Random draws.  qlnb fills NumPy arrays from QuantLib's own Mersenne Twister,
   Sobol and inverse cumulative normal in C++.  The same generators driven one
   call at a time through SWIG show the per-call cost that bulk fill removes;
   NumPy's own bulk generators are the speed reference (different sequences).

SWIG paths and draws use different generators from qlnb, so values are not
compared, only timings.  Prices are printed as a sanity check.

Usage:
    python benchmarks/bench_mc.py [--samples 2000] [--steps 50] [--repeats 5]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import numpy as np

SPOT, RATE, VOL, STRIKE, YEARS = 36.0, 0.06, 0.20, 40.0, 1.0


def best_seconds(fn, repeats: int) -> float:
    fn()
    best = math.inf
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


def qlnb_setup(steps: int):
    import qlnb as ql

    today = ql.Date(15, ql.Month.May, 1998)
    ref = ql.Date(17, ql.Month.May, 1998)
    ql.set_evaluation_date(today)
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.make_quote_handle(SPOT),
        ql.FlatForward(ref, 0.0, dc),
        ql.FlatForward(ref, RATE, dc),
        ql.BlackConstantVol(ref, ql.TARGET(), VOL, dc),
    )
    return ql, process, ref + 365


def swig_setup():
    import QuantLib as ql

    today = ql.Date(15, ql.May, 1998)
    ref = ql.Date(17, ql.May, 1998)
    ql.Settings.instance().evaluationDate = today
    dc = ql.Actual365Fixed()
    process = ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(SPOT)),
        ql.YieldTermStructureHandle(ql.FlatForward(ref, 0.0, dc)),
        ql.YieldTermStructureHandle(ql.FlatForward(ref, RATE, dc)),
        ql.BlackVolTermStructureHandle(ql.BlackConstantVol(ref, ql.TARGET(), VOL, dc)),
    )
    return ql, process, ref + 365


def numpy_paths(samples: int, steps: int, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    dt = YEARS / steps
    z = rng.standard_normal((samples, steps))
    drift = (RATE - 0.5 * VOL * VOL) * dt
    log_inc = drift + VOL * math.sqrt(dt) * z
    out = np.empty((samples, steps + 1))
    out[:, 0] = SPOT
    out[:, 1:] = SPOT * np.exp(np.cumsum(log_inc, axis=1))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--price-samples", type=int, default=20_000)
    parser.add_argument("--draws", type=int, default=50_000)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    samples, steps, reps = args.samples, args.steps, args.repeats

    results: dict[str, dict] = {}

    qlnb, q_process, q_maturity = qlnb_setup(steps)
    try:
        swig, s_process, s_maturity = swig_setup()
    except ImportError:
        swig = None

    # 1. Path generation ------------------------------------------------
    print(f"1. Path generation: {samples} paths x {steps} steps (ms per batch)")
    paths = {
        "qlnb simulate_gbm_paths": lambda: qlnb.simulate_gbm_paths(
            q_process, YEARS, steps, samples
        ),
        "numpy lognormal (ceiling)": lambda: numpy_paths(samples, steps),
    }
    if swig is not None:
        seq = swig.GaussianRandomSequenceGenerator(
            swig.UniformRandomSequenceGenerator(steps, swig.UniformRandomGenerator(42))
        )
        gen = swig.GaussianPathGenerator(s_process, YEARS, steps, seq, False)

        def swig_full():
            out = np.empty((samples, steps + 1))
            for i in range(samples):
                out[i] = list(gen.next().value())
            return out

        def swig_terminal():
            return np.array([gen.next().value().back() for _ in range(samples)])

        paths["SWIG path loop, full path to numpy"] = swig_full
        paths["SWIG path loop, terminal value only"] = swig_terminal
    base = None
    for name, fn in paths.items():
        t = best_seconds(fn, reps) * 1e3
        base = base or t
        print(f"   {name:40s} {t:10.2f} ms   {t / base:7.1f}x qlnb")
        results[f"paths: {name}"] = {"ms": t}

    # 2. MC pricing -----------------------------------------------------
    n = args.price_samples
    print(f"\n2. MC European put: {n} samples, {steps} steps (ms per NPV)")
    q_option = qlnb.EuropeanOption(
        qlnb.PlainVanillaPayoff(qlnb.OptionType.Put, STRIKE),
        qlnb.EuropeanExercise(q_maturity),
    )

    def qlnb_engine_npv(antithetic=True):
        # Setting the engine again forces a fresh calculation; NPV() is cached.
        q_option.set_mc_pricing_engine(q_process, steps, n, 42, antithetic)
        return q_option.NPV()

    def qlnb_numpy_payoff():
        p = qlnb.simulate_gbm_paths(q_process, YEARS, steps, n)
        return math.exp(-RATE * YEARS) * np.maximum(STRIKE - p[:, -1], 0.0).mean()

    pricing = {
        # Antithetic variates double the number of simulated paths.
        "qlnb MC engine (antithetic)": qlnb_engine_npv,
        "qlnb MC engine (no antithetic)": lambda: qlnb_engine_npv(False),
        "qlnb paths + numpy payoff": qlnb_numpy_payoff,
    }
    if swig is not None:
        s_option = swig.EuropeanOption(
            swig.PlainVanillaPayoff(swig.Option.Put, STRIKE),
            swig.EuropeanExercise(s_maturity),
        )

        def swig_engine_npv():
            s_option.setPricingEngine(
                swig.MCEuropeanEngine(
                    s_process,
                    "pseudorandom",
                    timeSteps=steps,
                    requiredSamples=n,
                    seed=42,
                    antitheticVariate=True,
                )
            )
            return s_option.NPV()

        pricing["SWIG MCEuropeanEngine"] = swig_engine_npv
    base = None
    for name, fn in pricing.items():
        t = best_seconds(fn, reps) * 1e3
        base = base or t
        npv = float(fn())
        print(f"   {name:40s} {t:10.2f} ms   {t / base:7.1f}x qlnb engine   NPV {npv:.4f}")
        results[f"pricing: {name}"] = {"ms": t, "npv": npv}

    # 3. Random draws ---------------------------------------------------
    d = args.draws
    print(f"\n3. Random draws: {d} values (ns per draw)")
    rng = np.random.default_rng(42)
    probabilities = np.random.default_rng(1).random(d)
    q_mt = qlnb.MersenneTwisterRng(42)
    q_sobol = qlnb.SobolSequence(5, 42)
    draws = {
        "qlnb MersenneTwisterRng.uniform (bulk)": lambda: q_mt.uniform(d),
        "qlnb MersenneTwisterRng.gaussian (bulk)": lambda: q_mt.gaussian(d),
        "qlnb SobolSequence(5).uniform (bulk)": lambda: q_sobol.uniform(d // 5),
        "qlnb inverse_cumulative_normal_array": (
            lambda: qlnb.inverse_cumulative_normal_array(probabilities)
        ),
        "numpy Generator.random (bulk)": lambda: rng.random(d),
        "numpy Generator.standard_normal (bulk)": lambda: rng.standard_normal(d),
    }
    if swig is not None:
        mt = swig.MersenneTwisterUniformRng(42)
        sobol = swig.SobolRsg(5, 42)
        icn = swig.InverseCumulativeNormal()
        draws["SWIG MersenneTwister, one call per draw"] = lambda: [
            mt.next().value() for _ in range(d)
        ]
        draws["SWIG Sobol 5-d, one call per point (x5)"] = lambda: [
            sobol.nextSequence().value() for _ in range(d // 5)
        ]
        draws["SWIG InverseCumulativeNormal per value"] = lambda: [
            icn(0.001 * (i % 999 + 1)) for i in range(d)
        ]
    for name, fn in draws.items():
        t = best_seconds(fn, reps) / d * 1e9
        print(f"   {name:40s} {t:10.1f} ns/draw")
        results[f"draws: {name}"] = {"ns_per_draw": t}

    out_dir = (
        Path(os.environ["QLNB_BENCH_OUT"])
        if "QLNB_BENCH_OUT" in os.environ
        else Path(__file__).resolve().parent / "out"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bench_mc.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
