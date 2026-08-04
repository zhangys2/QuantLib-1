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

/*! \file parallelmontecarlomodel.hpp
    \brief Thread-count-invariant parallel Monte Carlo over senders
*/

#ifndef quantlib_parallel_montecarlo_model_hpp
#define quantlib_parallel_montecarlo_model_hpp

#include <ql/errors.hpp>
#include <ql/methods/montecarlo/brownianbridge.hpp>
#include <ql/methods/montecarlo/indexedgaussiansequence.hpp>
#include <ql/shared_ptr.hpp>
#include <ql/types.hpp>

#include <algorithm>

#include <cstdint>
#include <utility>
#include <vector>

namespace QuantLib {

    //! Parallel Monte Carlo driver with results independent of thread count
    /*! Paths are partitioned into fixed-size chunks. The chunk size is a
        property of the problem, never of the machine: if it varied with the
        number of threads, so would the path-to-index mapping and hence the
        result. Chunks are then scheduled onto whatever workers exist.

        Each chunk builds its own generator and positions it at the chunk's
        first path index, which reproduces a straight sequential run exactly
        for skippable low-discrepancy sequences.

        Per-path results are written into a preallocated buffer at their own
        index and reduced afterwards in index order, so the floating-point
        summation order is fixed regardless of completion order.

        \c runChunk deliberately knows nothing about schedulers: the same
        kernel backs the serial reference run and any sender-based run.
    */
    template <class Model, class RsgFactory, class Pricer>
    class ParallelMonteCarloModel {
      public:
        /*! \param bridge if supplied, the per-step normals are reordered by a
                   Brownian bridge. This concentrates the variance of the path
                   in the earliest sequence dimensions, which are the best
                   distributed ones of a low-discrepancy sequence; without it
                   the integration error grows quickly with the step count.
                   The bridge is immutable and is shared by all workers.
        */
        ParallelMonteCarloModel(Model model,
                                RsgFactory makeRsg,
                                Pricer pricer,
                                Size chunkSize = 1024,
                                ext::shared_ptr<const BrownianBridge> bridge = {})
        : model_(std::move(model)), makeRsg_(std::move(makeRsg)), pricer_(std::move(pricer)),
          chunkSize_(chunkSize), bridge_(std::move(bridge)) {
            QL_REQUIRE(chunkSize_ > 0, "chunk size must be positive");
        }

        Size chunkSize() const { return chunkSize_; }
        Size chunks(Size paths) const { return (paths + chunkSize_ - 1) / chunkSize_; }
        const Model& model() const { return model_; }

        //! prices every path of one chunk into \p results at absolute indices
        void runChunk(Size chunkIndex, Size paths, std::vector<Real>& results) const {
            const Size begin = chunkIndex * chunkSize_;
            if (begin >= paths)
                return;
            const Size end = std::min(begin + chunkSize_, paths);

            IndexedGaussianSequence source(makeRsg_());
            source.positionAt(begin);

            Pricer pricer = pricer_;
            const Size steps = model_.steps();
            std::vector<Real> path(steps + 1);
            std::vector<Real> bridged(bridge_ ? steps : 0);

            for (Size p = begin; p < end; ++p) {
                const std::vector<Real>& normals = source.next();
                const Real* dw = normals.data();
                if (bridge_) {
                    bridge_->transform(normals.begin(), normals.end(), bridged.begin());
                    dw = bridged.data();
                }
                path[0] = model_.x0();
                for (Size i = 0; i < steps; ++i)
                    path[i + 1] = model_.evolve(i, path[i], dw[i]);
                results[p] = pricer(path);
            }
        }

        //! serial reference run; identical results to any parallel run
        std::vector<Real> runSerial(Size paths) const {
            std::vector<Real> results(paths);
            const Size n = chunks(paths);
            for (Size c = 0; c < n; ++c)
                runChunk(c, paths, results);
            return results;
        }

        //! reduction in index order, so the summation order is fixed
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
