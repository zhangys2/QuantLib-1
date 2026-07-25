/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2026 Zhang

 This file is part of QuantLib, a free-software/open-source library
 for financial quantitative analysts and developers - http://quantlib.org/

 QuantLib is free software: you can redistribute it and/or modify it
 under the terms of the QuantLib license.  You should have received a
 copy of the license along with this program; if not, please email
 <quantlib-dev@lists.sf.net>. The license is also available online at
 <http://quantlib.org/license.shtml>.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the license for more details.
*/

/*! \file blackscholespathmodel.hpp
    \brief Precomputed, non-virtual Black-Scholes evolution kernel
*/

#ifndef quantlib_black_scholes_path_model_hpp
#define quantlib_black_scholes_path_model_hpp

#include <ql/processes/blackscholesprocess.hpp>
#include <ql/timegrid.hpp>
#include <cmath>
#include <concepts>
#include <vector>

namespace QuantLib {

    //! Scalar type usable as the state of a path evolution
    /*! Satisfied by Real and by SIMD batch types such as std::simd<Real>.
        \c exp is required to be reachable by ADL or from namespace std.
    */
    template <class T>
    concept PathScalar = requires(const T& a, const T& b) {
        { a + b } -> std::convertible_to<T>;
        { a * b } -> std::convertible_to<T>;
    };

    //! Precomputed one-factor Black-Scholes evolution over a fixed time grid
    /*! GeneralizedBlackScholesProcess::evolve recomputes the per-step drift and
        variance on every call even though, for a strike-independent volatility
        term structure, both depend only on the time grid and not on the state.
        In a Monte Carlo run that repeats two blackVariance() and two
        forwardRate() term-structure lookups once per path per timestep.

        This class hoists those lookups into per-step arrays built once. The
        resulting object is immutable, so it is safe to share across threads,
        holds no term-structure handles, and its evolution step is a non-virtual
        template that inlines and vectorises.

        \warning Only valid when the process volatility is strike-independent
                 and the process does not force discretization; otherwise the
                 per-step coefficients are state-dependent and this model does
                 not reproduce the process. Use consistentWith() to check.
    */
    class BlackScholesPathModel {
      public:
        BlackScholesPathModel(const GeneralizedBlackScholesProcess& process,
                              const TimeGrid& grid)
        : x0_(process.x0()), drift_(grid.size() - 1), stdDeviation_(grid.size() - 1) {
            const auto& vol = process.blackVolatility();
            const auto& r = process.riskFreeRate();
            const auto& q = process.dividendYield();
            for (Size i = 0; i < grid.size() - 1; ++i) {
                Time t = grid[i];
                Time dt = grid.dt(i);
                // strike is irrelevant by the strike-independence precondition;
                // 0.01 matches what the process itself passes
                Real variance = vol->blackVariance(t + dt, 0.01) - vol->blackVariance(t, 0.01);
                drift_[i] = (r->forwardRate(t, t + dt, Continuous, NoFrequency, true).rate() -
                             q->forwardRate(t, t + dt, Continuous, NoFrequency, true).rate()) *
                                dt -
                            0.5 * variance;
                stdDeviation_[i] = std::sqrt(variance);
            }
        }

        Size steps() const { return drift_.size(); }
        Real x0() const { return x0_; }
        Real drift(Size i) const { return drift_[i]; }
        Real stdDeviation(Size i) const { return stdDeviation_[i]; }

        //! advances the state over step \p i given a standard normal increment
        /*! The operand order matches GeneralizedBlackScholesProcess::evolve so
            that results are bit-identical to the serial engine for the same
            increments -- provided floating-point contraction is disabled, since
            fusing stdDeviation*dw + drift into an FMA changes the result.
        */
        template <PathScalar T>
        T evolve(Size i, const T& x, const T& dw) const {
            using std::exp;
            return x * exp(stdDeviation_[i] * dw + drift_[i]);
        }

        //! checks that the model reproduces the process it was built from
        /*! Guards the strike-independence precondition, which is not otherwise
            observable through the public process interface.
        */
        bool consistentWith(const GeneralizedBlackScholesProcess& process,
                            const TimeGrid& grid,
                            Real tolerance = 1e-12) const {
            Real x = x0_;
            Real y = x0_;
            for (Size i = 0; i < steps(); ++i) {
                Real dw = 0.5 - Real(i % 3);
                x = evolve(i, x, dw);
                y = process.evolve(grid[i], y, grid.dt(i), dw);
                if (std::fabs(x - y) > tolerance * std::fmax(Real(1.0), std::fabs(y)))
                    return false;
            }
            return true;
        }

      private:
        Real x0_;
        std::vector<Real> drift_, stdDeviation_;
    };

}

#endif
