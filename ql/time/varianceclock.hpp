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

/*! \file varianceclock.hpp
    \brief fixed-snapshot variance clock
*/

#ifndef quantlib_variance_clock_hpp
#define quantlib_variance_clock_hpp

#include <ql/shared_ptr.hpp>
#include <ql/time/varianceclocktables.hpp>
#include <ql/types.hpp>
#include <memory>

namespace QuantLib {

    enum class VarianceClockStatus {
        Ok,
        Expired,
        InvalidView,
        InvalidToken,
        StaleToken,
        InvalidInstant,
        OutOfCoverage,
        BeforeCalibration
    };

    struct VarianceClockResult {
        VarianceClockStatus status;
        double weightedDays;
    };

    //! Convert a successful or expired result outside the noexcept query path.
    Real varianceClockAsReal(const VarianceClockResult& result);

    class VarianceClockExpiryToken {
      public:
        VarianceClockExpiryToken() noexcept = default;

      private:
        friend class VarianceClockView;
        ext::shared_ptr<const detail::VarianceClockGeneration> generation_;
        VarianceClockInstant expiry_;
        Size run_ = 0;
        Size slot_ = 0;
    };

    //! Immutable view of a single fixed snapshot.
    class VarianceClockView {
      public:
        VarianceClockView() noexcept = default;
        VarianceClockInstant coverageStart() const noexcept;
        VarianceClockInstant coverageEnd() const noexcept;
        VarianceClockStatus prepareExpiry(VarianceClockInstant expiry,
                                          VarianceClockExpiryToken& result) const noexcept;

        //! Cumulative weighted days from the coverage start.
        /*! Subtracting two cumulative values does not have the numerical
            accuracy guarantee of remaining().
        */
        VarianceClockResult cumulativeFromCoverageStart(VarianceClockInstant time) const noexcept;
        VarianceClockResult remaining(VarianceClockInstant time,
                                      const VarianceClockExpiryToken& expiry) const noexcept;

      private:
        friend class VarianceClock;
        explicit VarianceClockView(
            const ext::shared_ptr<const detail::VarianceClockGeneration>& generation) noexcept;
        ext::shared_ptr<const detail::VarianceClockGeneration> generation_;
    };

    //! Fixed-snapshot owner; live replacement and reclamation are not provided.
    /*! Destroying this owner with live views or tokens violates the lifetime
        precondition and aborts in debug builds. In release builds those
        handles retain the snapshot and can destroy it off the control path.
        Capture must not race with destruction.
    */
    class VarianceClock {
      public:
        explicit VarianceClock(std::unique_ptr<VarianceClockSnapshot> snapshot);
        ~VarianceClock() noexcept;
        VarianceClock(const VarianceClock&) = delete;
        VarianceClock& operator=(const VarianceClock&) = delete;

        VarianceClockView capture() const;

      private:
        ext::shared_ptr<const detail::VarianceClockGeneration> generation_;
    };

}

#endif
