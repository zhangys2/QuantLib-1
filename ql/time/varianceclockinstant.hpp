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

/*! \file varianceclockinstant.hpp
    \brief POSIX instants for variance clocks
*/

#ifndef quantlib_variance_clock_instant_hpp
#define quantlib_variance_clock_instant_hpp

#include <cstdint>

namespace QuantLib {

    //! A POSIX second and its nonnegative nanosecond fraction.
    /*! The default value is invalid and compares before all valid instants;
        invalid instants compare equal. Negative instants use floor seconds;
        leap seconds are not represented.
    */
    class VarianceClockInstant {
      public:
        VarianceClockInstant() noexcept = default;

        //! Leave result unchanged if the fraction is not canonical.
        static bool tryCreate(std::int64_t unixSeconds,
                              std::uint32_t nanosecond,
                              VarianceClockInstant& result) noexcept {
            if (nanosecond >= 1000000000U)
                return false;
            result.seconds_ = unixSeconds;
            result.nanosecond_ = nanosecond;
            result.valid_ = true;
            return true;
        }

        bool isValid() const noexcept { return valid_; }
        std::int64_t unixSeconds() const noexcept { return seconds_; }
        std::uint32_t nanosecond() const noexcept { return nanosecond_; }

        bool operator==(const VarianceClockInstant& other) const noexcept {
            return valid_ == other.valid_ &&
                   (!valid_ || (seconds_ == other.seconds_ && nanosecond_ == other.nanosecond_));
        }

        bool operator<(const VarianceClockInstant& other) const noexcept {
            if (valid_ != other.valid_)
                return !valid_;
            return valid_ && (seconds_ < other.seconds_ ||
                              (seconds_ == other.seconds_ && nanosecond_ < other.nanosecond_));
        }

        bool operator<=(const VarianceClockInstant& other) const noexcept {
            return *this < other || *this == other;
        }

      private:
        std::int64_t seconds_ = 0;
        std::uint32_t nanosecond_ = 0;
        bool valid_ = false;
    };

}

#endif
