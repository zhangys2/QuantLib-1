/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2026 QuantLib contributors

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

/*! \file varianceclockbundletypes.hpp
    \brief public types for loaded variance-clock bundles
*/

#ifndef quantlib_variance_clock_bundle_types_hpp
#define quantlib_variance_clock_bundle_types_hpp

#include <ql/time/varianceclocktables.hpp>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <new>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

namespace QuantLib {

    namespace detail {

        class VarianceClockBundleBudgetState {
          public:
            explicit VarianceClockBundleBudgetState(
                std::size_t limit = std::numeric_limits<std::size_t>::max()) noexcept;
            void increase(std::size_t bytes);
            void decrease(std::size_t bytes) noexcept;
            std::size_t used() const noexcept;
            std::size_t limit() const noexcept;

          private:
            std::size_t limit_;
            std::atomic<std::size_t> used_{0};
        };

        template <class T>
        class VarianceClockBundleBudgetAllocator {
          public:
            using value_type = T;
            using size_type = std::size_t;
            using difference_type = std::ptrdiff_t;
            using propagate_on_container_move_assignment = std::true_type;

            template <class U>
            struct rebind {
                using other = VarianceClockBundleBudgetAllocator<U>;
            };

            VarianceClockBundleBudgetAllocator()
            : state_(std::make_shared<VarianceClockBundleBudgetState>()) {}

            explicit VarianceClockBundleBudgetAllocator(
                std::shared_ptr<VarianceClockBundleBudgetState> state) noexcept
            : state_(std::move(state)) {}

            template <class U>
            VarianceClockBundleBudgetAllocator(
                const VarianceClockBundleBudgetAllocator<U>& other) noexcept
            : state_(other.state()) {}

            T* allocate(std::size_t count) {
                if (count > std::numeric_limits<std::size_t>::max() / sizeof(T))
                    throw std::bad_array_new_length();
                const std::size_t bytes = count * sizeof(T);
                // Charge the allocator request before the allocation; vector reserve capacity
                // is not a portable proxy for the number of allocated elements.
                state_->increase(bytes);
                try {
                    return std::allocator<T>{}.allocate(count);
                } catch (...) {
                    state_->decrease(bytes);
                    throw;
                }
            }

            void deallocate(T* address, std::size_t count) noexcept {
                std::allocator<T>{}.deallocate(address, count);
                state_->decrease(count * sizeof(T));
            }

            const std::shared_ptr<VarianceClockBundleBudgetState>& state() const noexcept {
                return state_;
            }

            template <class U>
            bool operator==(const VarianceClockBundleBudgetAllocator<U>& other) const noexcept {
                return state_ == other.state();
            }

            template <class U>
            bool operator!=(const VarianceClockBundleBudgetAllocator<U>& other) const noexcept {
                return !(*this == other);
            }

          private:
            template <class>
            friend class VarianceClockBundleBudgetAllocator;
            std::shared_ptr<VarianceClockBundleBudgetState> state_;
        };

    } // namespace detail

    enum class VarianceClockLoadMode { Strict, Reconstruction };

    struct VarianceClockBundleWarning {
        std::string code;
        std::string severity;
        VarianceClockProfileId profileId;
        std::string targetGroupId;
        std::uint16_t minuteOfDay;
        std::vector<std::string> evidenceIds;
    };

    using VarianceClockBundleWarningVector =
        std::vector<VarianceClockBundleWarning,
                    detail::VarianceClockBundleBudgetAllocator<VarianceClockBundleWarning>>;

    struct VarianceClockBundleProvenance {
        std::string snapshotId;
        std::vector<std::string> validatedEvidenceIds;
        VarianceClockInstant availableFrom;
        VarianceClockLoadMode mode = VarianceClockLoadMode::Strict;
        bool reconstructed = false;
    };

    struct VarianceClockLoadedBundle {
        std::unique_ptr<VarianceClockSnapshot> snapshot;
        VarianceClockBundleWarningVector warnings;
        VarianceClockBundleProvenance provenance;
    };

}

#endif
