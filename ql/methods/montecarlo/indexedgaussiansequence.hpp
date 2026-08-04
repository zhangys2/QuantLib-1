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

/*! \file indexedgaussiansequence.hpp
    \brief Randomly-addressable Gaussian sequence source
*/

#ifndef quantlib_indexed_gaussian_sequence_hpp
#define quantlib_indexed_gaussian_sequence_hpp

#include <ql/math/distributions/normaldistribution.hpp>
#include <ql/types.hpp>

#include <concepts>
#include <cstdint>
#include <vector>

namespace QuantLib {

    //! A uniform sequence generator that can be positioned at an arbitrary index
    /*! Satisfied by SobolRsg and Burley2020SobolRsg. skipTo(n) leaves the
        generator so that the following n-th, (n+1)-th, ... draws are returned
        by successive calls to nextInt32Sequence().
    */
    template <class G>
    concept SkippableUniformSequence = requires(const G& g, std::uint32_t n) {
        { g.skipTo(n) } -> std::same_as<const std::vector<std::uint32_t>&>;
        { g.nextInt32Sequence() } -> std::same_as<const std::vector<std::uint32_t>&>;
        { g.dimension() } -> std::convertible_to<Size>;
    };

    //! Gaussian sequence source addressable by absolute path index
    /*! Wraps a skippable low-discrepancy generator and reproduces exactly the
        conversion performed by SobolRsg::nextSequence() followed by
        InverseCumulativeRsg, so that a run assembled from positioned chunks is
        bit-identical to a straight sequential run.

        Each instance owns its generator and its scratch buffer, so instances
        are independent; one per worker is required. Note that copying is
        deliberately not used to spawn workers: Burley2020SobolRsg holds its
        underlying SobolRsg by shared_ptr, so a copy would share mutable state
        and race. Construct a fresh instance per chunk instead.
    */
    template <SkippableUniformSequence RSG>
    class IndexedGaussianSequence {
      public:
        IndexedGaussianSequence(RSG generator)
        : generator_(std::move(generator)), normals_(generator_.dimension()) {}

        Size dimension() const { return normals_.size(); }

        //! positions the source so the next draw is that of path \p index
        void positionAt(std::uint64_t index) {
            generator_.skipTo(static_cast<std::uint32_t>(index));
        }

        //! returns the standard normal vector for the current path, then advances
        const std::vector<Real>& next() {
            const std::vector<std::uint32_t>& v = generator_.nextInt32Sequence();
            for (Size k = 0; k < normals_.size(); ++k) {
                // matches SobolRsg::nextSequence() exactly
                Real u = v[k] * (0.5 / (1UL << 31));
                normals_[k] = icn_(u);
            }
            return normals_;
        }

      private:
        RSG generator_;
        InverseCumulativeNormal icn_;
        std::vector<Real> normals_;
    };

}

#endif
