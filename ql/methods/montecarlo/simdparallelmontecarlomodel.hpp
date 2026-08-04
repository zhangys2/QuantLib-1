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

/*! \file simdparallelmontecarlomodel.hpp
    \brief SIMD-batched parallel Monte Carlo, bit-identical to the scalar layer
*/

#ifndef quantlib_simd_parallel_montecarlo_model_hpp
#define quantlib_simd_parallel_montecarlo_model_hpp

#include <ql/errors.hpp>
#include <ql/math/distributions/normaldistribution.hpp>
#include <ql/methods/montecarlo/brownianbridge.hpp>
#include <ql/shared_ptr.hpp>
#include <ql/types.hpp>

// P1928 <simd> has not shipped in libstdc++ or the MSVC STL as of 2026; the
// TS header carries the same design by the same author. Switching to the
// standard spelling later is confined to this alias.
#include <experimental/simd>

#include <algorithm>
#include <cstdint>
#include <utility>
#include <vector>

namespace QuantLib {

    namespace simd = std::experimental;

    //! SIMD batch of Real, one lane per path
    using RealBatch = simd::native_simd<Real>;

    /*! Profiling the serial kernel puts 44% of the time in the inverse
        cumulative normal and 13% in the Brownian bridge, against 41% in the
        path evolution. The first two are pure arithmetic and vectorise
        losslessly; the evolution is dominated by exp(), which libstdc++
        implements for simd as a lane-by-lane call to scalar exp
        (_GLIBCXX_SIMD_MATH_FALLBACK), so batching it buys nothing and a
        hand-written vector exp would not reproduce the scalar's last bits.
        The evolution is therefore left scalar and results stay bit-identical
        to both the scalar layer and MCEuropeanEngine.
    */
    namespace detail {

        // Must match InverseCumulativeNormal exactly; those members are private,
        // so they are repeated here and the equality is asserted by the gates
        // rather than by the compiler.
        inline constexpr Real icn_a1 = -3.969683028665376e+01;
        inline constexpr Real icn_a2 = 2.209460984245205e+02;
        inline constexpr Real icn_a3 = -2.759285104469687e+02;
        inline constexpr Real icn_a4 = 1.383577518672690e+02;
        inline constexpr Real icn_a5 = -3.066479806614716e+01;
        inline constexpr Real icn_a6 = 2.506628277459239e+00;
        inline constexpr Real icn_b1 = -5.447609879822406e+01;
        inline constexpr Real icn_b2 = 1.615858368580409e+02;
        inline constexpr Real icn_b3 = -1.556989798598866e+02;
        inline constexpr Real icn_b4 = 6.680131188771972e+01;
        inline constexpr Real icn_b5 = -1.328068155288572e+01;
        inline constexpr Real icn_x_low = 0.02425;
        inline constexpr Real icn_x_high = 1.0 - icn_x_low;

    }

    //! batched inverse cumulative normal, lane-wise equal to standard_value
    /*! The central rational approximation is evaluated for every lane in the
        same operation order as the scalar routine, which makes each lane
        bit-identical provided floating-point contraction is disabled. Lanes
        falling in the tails are rare and are recomputed with the scalar
        routine, so they are identical by construction.
    */
    inline RealBatch inverseCumulativeNormal(const RealBatch& x) {
        using namespace detail;
        RealBatch z = x - 0.5;
        RealBatch r = z * z;
        RealBatch num =
            (((((icn_a1 * r + icn_a2) * r + icn_a3) * r + icn_a4) * r + icn_a5) * r + icn_a6) * z;
        RealBatch den =
            (((((icn_b1 * r + icn_b2) * r + icn_b3) * r + icn_b4) * r + icn_b5) * r + 1.0);
        RealBatch result = num / den;

        auto tails = (x < icn_x_low) || (icn_x_high < x);
        if (simd::any_of(tails)) {
            for (std::size_t l = 0; l < RealBatch::size(); ++l)
                if (tails[l])
                    result[l] = InverseCumulativeNormal::standard_value(x[l]);
        }
        return result;
    }

    //! Monte Carlo driver batching whole paths across SIMD lanes
    /*! Chunking, indexing and reduction order are those of
        ParallelMonteCarloModel; only the per-path work is restructured. The
        path-to-index mapping is unchanged, so results do not depend on the
        lane width any more than they depend on the thread count.
    */
    template <class Model, class RsgFactory, class Pricer>
    class SimdParallelMonteCarloModel {
      public:
        SimdParallelMonteCarloModel(Model model,
                                    RsgFactory makeRsg,
                                    Pricer pricer,
                                    Size chunkSize = 1024,
                                    ext::shared_ptr<const BrownianBridge> bridge = {})
        : model_(std::move(model)), makeRsg_(std::move(makeRsg)), pricer_(std::move(pricer)),
          chunkSize_(chunkSize), bridge_(std::move(bridge)) {
            QL_REQUIRE(chunkSize_ > 0, "chunk size must be positive");
        }

        static constexpr Size laneCount() { return RealBatch::size(); }
        Size chunkSize() const { return chunkSize_; }
        Size chunks(Size paths) const { return (paths + chunkSize_ - 1) / chunkSize_; }

        void runChunk(Size chunkIndex, Size paths, std::vector<Real>& results) const {
            const Size begin = chunkIndex * chunkSize_;
            if (begin >= paths)
                return;
            const Size end = std::min(begin + chunkSize_, paths);
            const Size steps = model_.steps();
            const Size W = laneCount();

            auto generator = makeRsg_();
            generator.skipTo(static_cast<std::uint32_t>(begin));

            std::vector<RealBatch> uniforms(steps), normals(steps), bridged(steps);
            std::vector<Real> path(steps + 1);

            for (Size p = begin; p < end; p += W) {
                const Size lanes = std::min(W, end - p);

                // gather `lanes` consecutive paths and transpose into batches
                for (Size l = 0; l < lanes; ++l) {
                    const std::vector<std::uint32_t>& v = generator.nextInt32Sequence();
                    for (Size i = 0; i < steps; ++i)
                        uniforms[i][l] = v[i] * (0.5 / (1UL << 31));
                }
                // idle lanes must still hold a value in the central region,
                // or they would take the scalar tail path for nothing
                for (Size l = lanes; l < W; ++l)
                    for (Size i = 0; i < steps; ++i)
                        uniforms[i][l] = 0.5;

                for (Size i = 0; i < steps; ++i)
                    normals[i] = inverseCumulativeNormal(uniforms[i]);

                const RealBatch* increments = normals.data();
                if (bridge_) {
                    // BrownianBridge::transform is already generic over the
                    // element type; it needs no SIMD-specific overload.
                    bridge_->transform(normals.begin(), normals.end(), bridged.begin());
                    increments = bridged.data();
                }

                for (Size l = 0; l < lanes; ++l) {
                    path[0] = model_.x0();
                    for (Size i = 0; i < steps; ++i)
                        path[i + 1] = model_.evolve(i, path[i], increments[i][l]);
                    results[p + l] = pricer_(path);
                }
            }
        }

        std::vector<Real> runSerial(Size paths) const {
            std::vector<Real> results(paths);
            const Size n = chunks(paths);
            for (Size c = 0; c < n; ++c)
                runChunk(c, paths, results);
            return results;
        }

        static Real mean(const std::vector<Real>& results) {
            Real sum = 0.0;
            for (Real r : results)
                sum += r;
            return sum / Real(results.size());
        }

      private:
        Model model_;
        RsgFactory makeRsg_;
        Pricer pricer_;
        Size chunkSize_;
        ext::shared_ptr<const BrownianBridge> bridge_;
    };

}

#endif
