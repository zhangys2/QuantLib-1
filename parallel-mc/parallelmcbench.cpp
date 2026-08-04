/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2026 Zhang

 This file is part of QuantLib, a free-software/open-source library
 for financial quantitative analysts and developers - http://quantlib.org/

 QuantLib is free software: you can redistribute it and/or modify it
 under the terms of the QuantLib license.  You should have received a
 copy of the license along with this program; if not, please email
 <quantlib-dev@lists.sf.net>. The license is also available online at
 <https://www.quantlib.org/license.shtml>.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the license for more details.
*/

/*! Acceptance gates and benchmark for the parallel Monte Carlo layer.

    Gates
      1. analytic oracle  - MC price against the Black-Scholes closed form
      2. determinism      - byte-identical per-path results across thread counts
      3. scaling          - speedup against the serial run of the same kernel

    and an end-to-end comparison against QuantLib's own MCEuropeanEngine, which
    serves as an independent oracle: it shares no code with the parallel layer.

    Build with -ffp-contract=off. Fusing stdDeviation*dw + drift into an FMA
    changes the last bits and breaks the bit-identity the gates assert.
*/

#include <ql/exercise.hpp>
#include <ql/instruments/europeanoption.hpp>
#include <ql/math/randomnumbers/sobolrsg.hpp>
#include <ql/methods/montecarlo/blackscholespathmodel.hpp>
#include <ql/methods/montecarlo/parallelmontecarlomodel.hpp>
#include <ql/methods/montecarlo/simdparallelmontecarlomodel.hpp>
#include <ql/pricingengines/blackformula.hpp>
#include <ql/pricingengines/vanilla/mceuropeanengine.hpp>
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/quotes/simplequote.hpp>
#include <ql/termstructures/volatility/equityfx/blackconstantvol.hpp>
#include <ql/termstructures/yield/flatforward.hpp>
#include <ql/time/calendars/target.hpp>
#include <ql/time/daycounters/actual365fixed.hpp>

#include <exec/static_thread_pool.hpp>
#include <stdexec/execution.hpp>

#include <chrono>
#include <cstdio>
#include <vector>

using namespace QuantLib;

namespace {

    int failures = 0;

    void report(const char* what, bool ok) {
        std::printf("%-46s %s\n", what, ok ? "PASS" : "FAIL");
        if (!ok)
            ++failures;
    }

    double msSince(std::chrono::steady_clock::time_point t) {
        return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t)
            .count();
    }

    template <class PMCM, class Scheduler>
    std::vector<Real> runParallel(const PMCM& m, Size paths, Scheduler sch) {
        std::vector<Real> results(paths);
        const Size n = m.chunks(paths);
        auto work = stdexec::schedule(sch) |
                    stdexec::bulk(stdexec::par, n,
                                  [&](std::size_t c) { m.runChunk(c, paths, results); });
        stdexec::sync_wait(std::move(work));
        return results;
    }

    struct EuropeanCall {
        Real strike, discount;
        Real operator()(const std::vector<Real>& path) const {
            Real payoff = path.back() - strike;
            return discount * (payoff > 0.0 ? payoff : 0.0);
        }
    };

    //! arithmetic-average Asian call, sampled on the whole time grid
    struct AsianCall {
        Real strike, discount;
        Real operator()(const std::vector<Real>& path) const {
            Real sum = 0.0;
            for (Size i = 1; i < path.size(); ++i)
                sum += path[i];
            Real payoff = sum / Real(path.size() - 1) - strike;
            return discount * (payoff > 0.0 ? payoff : 0.0);
        }
    };

    struct Market {
        ext::shared_ptr<GeneralizedBlackScholesProcess> process;
        Real s0, vol, rate, div, maturity, discount, forward;
    };

    Market makeMarket(Real s0, Real vol, Real rate, Real div, Real maturity) {
        Date today = Settings::instance().evaluationDate();
        DayCounter dc = Actual365Fixed();
        Handle<Quote> spot(ext::make_shared<SimpleQuote>(s0));
        Handle<YieldTermStructure> r(ext::make_shared<FlatForward>(today, rate, dc));
        Handle<YieldTermStructure> q(ext::make_shared<FlatForward>(today, div, dc));
        Handle<BlackVolTermStructure> v(
            ext::make_shared<BlackConstantVol>(today, TARGET(), vol, dc));
        auto process = ext::make_shared<GeneralizedBlackScholesProcess>(spot, q, r, v);
        Real discount = r->discount(maturity);
        Real forward = s0 * q->discount(maturity) / r->discount(maturity);
        return {process, s0, vol, rate, div, maturity, discount, forward};
    }

}

int main() {
    const Date today(15, May, 2026);
    Settings::instance().evaluationDate() = today;

    const Size steps = 50;
    const Size paths = 262144;
    const Real strike = 105.0, maturity = 1.0;

    Market mkt = makeMarket(100.0, 0.20, 0.03, 0.01, maturity);
    TimeGrid grid(maturity, steps);
    BlackScholesPathModel model(*mkt.process, grid);
    report("path model consistent with process", model.consistentWith(*mkt.process, grid));

    const Real analytic =
        blackFormula(Option::Call, strike, mkt.forward, mkt.vol * std::sqrt(maturity), mkt.discount);

    auto makeRsg = [steps] { return SobolRsg(steps, 42); };
    auto bridge = ext::make_shared<const BrownianBridge>(grid);
    ParallelMonteCarloModel mc(model, makeRsg, EuropeanCall{strike, mkt.discount}, 1024, bridge);

    std::printf("\n--- gate 1: analytic oracle ---\n");
    auto t0 = std::chrono::steady_clock::now();
    std::vector<Real> serial = mc.runSerial(paths);
    double serialMs = msSince(t0);
    Real mcPrice = mc.mean(serial);
    std::printf("analytic = %.10f   monte carlo = %.10f   err = %.3e\n", analytic, mcPrice,
                std::fabs(mcPrice - analytic));
    report("european price within 1e-3 of closed form", std::fabs(mcPrice - analytic) < 1e-3);

    std::printf("\n--- gate 2: determinism across thread counts ---\n");
    for (unsigned n : {1u, 4u, 28u}) {
        exec::static_thread_pool pool(n);
        std::vector<Real> res = runParallel(mc, paths, pool.get_scheduler());
        char label[64];
        std::snprintf(label, sizeof(label), "%u threads identical to serial", n);
        report(label, res == serial);
    }

    std::printf("\n--- gate 3: scaling ---\n");
    std::printf("serial kernel   : %8.1f ms  (1.00x)\n", serialMs);
    double best = serialMs;
    for (unsigned n : {2u, 4u, 8u, 16u, 28u}) {
        exec::static_thread_pool pool(n);
        auto a = std::chrono::steady_clock::now();
        std::vector<Real> res = runParallel(mc, paths, pool.get_scheduler());
        double ms = msSince(a);
        best = std::min(best, ms);
        std::printf("%2u threads      : %8.1f ms  (%.2fx)\n", n, ms, serialMs / ms);
    }
    report("parallel run at least 4x the serial kernel", serialMs / best >= 4.0);

    // The SIMD layer repeats the inverse-cumulative-normal constants because
    // InverseCumulativeNormal keeps them private. Check the two agree bit for
    // bit across the central region and both tails before trusting the rest.
    std::printf("\n--- gate 4: SIMD inverse cumulative normal ---\n");
    {
        Size checked = 0, differing = 0;
        const Size W = RealBatch::size();
        for (Size k = 1; k + W < 200000; k += W) {
            RealBatch u;
            for (Size l = 0; l < W; ++l)
                u[l] = Real(k + l) / 200000.0;
            RealBatch got = inverseCumulativeNormal(u);
            for (Size l = 0; l < W; ++l) {
                ++checked;
                if (got[l] != InverseCumulativeNormal::standard_value(u[l]))
                    ++differing;
            }
        }
        std::printf("checked %zu values (both tails included), %zu differ\n", checked, differing);
        report("SIMD icn bit-identical to scalar", differing == 0);
    }

    std::printf("\n--- gate 5: SIMD path batching ---\n");
    double simdMs = 0.0;
    {
        SimdParallelMonteCarloModel simdMc(model, makeRsg, EuropeanCall{strike, mkt.discount}, 1024,
                                           bridge);
        auto ts = std::chrono::steady_clock::now();
        std::vector<Real> simdRes = simdMc.runSerial(paths);
        simdMs = msSince(ts);
        std::printf("lane width      : %zu doubles\n", SimdParallelMonteCarloModel<
                    BlackScholesPathModel, decltype(makeRsg), EuropeanCall>::laneCount());
        std::printf("scalar kernel   : %8.1f ms\n", serialMs);
        std::printf("simd kernel     : %8.1f ms  (%.2fx)\n", simdMs, serialMs / simdMs);
        report("SIMD results bit-identical to scalar", simdRes == serial);
    }

    std::printf("\n--- end-to-end vs MCEuropeanEngine ---\n");
    EuropeanOption option(ext::make_shared<PlainVanillaPayoff>(Option::Call, strike),
                          ext::make_shared<EuropeanExercise>(today + Period(365, Days)));
    option.setPricingEngine(MakeMCEuropeanEngine<LowDiscrepancy>(mkt.process)
                                .withSteps(steps)
                                .withSamples(paths)
                                .withBrownianBridge(true)
                                .withSeed(42));
    auto t1 = std::chrono::steady_clock::now();
    Real qlPrice = option.NPV();
    double qlMs = msSince(t1);
    std::printf("MCEuropeanEngine : %.17g  (%8.1f ms)\n", qlPrice, qlMs);
    std::printf("parallel serial  : %.17g  (%8.1f ms, %.2fx)\n", mcPrice, serialMs, qlMs / serialMs);
    std::printf("parallel best    : %*s  (%8.1f ms, %.2fx)\n", 17, "", best, qlMs / best);
    report("bit-identical to MCEuropeanEngine", qlPrice == mcPrice);

    // Broadened evidence: the bit-identity claim above rests on a single
    // parameter set. Sweep moneyness, volatility and maturity and require it
    // to hold everywhere. Maturities are whole numbers of days so that the
    // engine's exercise date and our time grid agree exactly under
    // Actual365Fixed; otherwise the two would integrate different grids.
    std::printf("\n--- broadened sweep vs MCEuropeanEngine ---\n");
    const Size sweepPaths = 65536;
    Size cases = 0, identical = 0;
    Real worstError = 0.0;
    std::printf("%5s %5s %6s %14s %14s %11s %10s\n", "S0", "vol", "days", "analytic", "ours",
                "abs err", "identical");
    for (Real s : {80.0, 100.0, 120.0}) {
        for (Real vl : {0.10, 0.20, 0.40}) {
            for (int days : {91, 365, 1095}) {
                const Real T = Real(days) / 365.0;
                Market m = makeMarket(s, vl, 0.03, 0.01, T);
                TimeGrid g(T, steps);
                BlackScholesPathModel pm_model(*m.process, g);
                if (!pm_model.consistentWith(*m.process, g)) {
                    report("sweep: model consistent with process", false);
                    continue;
                }
                auto mkRsg = [] { return SobolRsg(steps, 42); };
                auto bb = ext::make_shared<const BrownianBridge>(g);
                ParallelMonteCarloModel sweep(pm_model, mkRsg, EuropeanCall{strike, m.discount},
                                              1024, bb);
                Real ours = sweep.mean(sweep.runSerial(sweepPaths));

                EuropeanOption opt(ext::make_shared<PlainVanillaPayoff>(Option::Call, strike),
                                   ext::make_shared<EuropeanExercise>(today + Period(days, Days)));
                opt.setPricingEngine(MakeMCEuropeanEngine<LowDiscrepancy>(m.process)
                                         .withSteps(steps)
                                         .withSamples(sweepPaths)
                                         .withBrownianBridge(true)
                                         .withSeed(42));
                Real theirs = opt.NPV();

                Real ref = blackFormula(Option::Call, strike, m.forward, vl * std::sqrt(T),
                                        m.discount);
                bool same = (ours == theirs);
                ++cases;
                identical += same ? 1 : 0;
                worstError = std::max(worstError, std::fabs(ours - ref));
                std::printf("%5.0f %5.2f %6d %14.8f %14.8f %11.2e %10s\n", s, vl, days, ref, ours,
                            std::fabs(ours - ref), same ? "yes" : "NO");
            }
        }
    }
    std::printf("bit-identical in %zu of %zu cases, worst error vs closed form %.2e\n", identical,
                cases, worstError);
    report("bit-identical across the whole sweep", identical == cases);

    std::printf("\n%s (%d failure%s)\n", failures == 0 ? "ALL GATES PASSED" : "GATES FAILED",
                failures, failures == 1 ? "" : "s");
    return failures == 0 ? 0 : 1;
}
