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

/*! \file varianceclocktables.hpp
    \brief in-memory variance-clock input tables
*/

#ifndef quantlib_variance_clock_tables_hpp
#define quantlib_variance_clock_tables_hpp

#include <ql/time/date.hpp>
#include <ql/time/varianceclockinstant.hpp>
#include <array>
#include <cstdint>
#include <limits>
#include <memory>
#include <vector>

namespace QuantLib {

    namespace detail {
        class VarianceClockGeneration;
    }

    using VarianceClockProfileId = std::uint32_t;

    //! Complete clock rate for one local five-minute slot.
    struct VarianceClockRateSlot {
        double weight = std::numeric_limits<double>::quiet_NaN();
    };

    struct VarianceClockProfileInput {
        VarianceClockProfileId id = 0;
        VarianceClockInstant calibrationAsOf;
        std::array<VarianceClockRateSlot, 288> slots;
    };

    struct VarianceClockDateInput {
        Date localDate;
        VarianceClockProfileId profile = 0;
    };

    //! UTC interval, local offset in seconds, and repeated-time fold marker.
    struct VarianceClockOffsetInput {
        VarianceClockInstant start, end;
        // INT32_MIN is not divisible by 300, so an omitted offset fails validation.
        std::int32_t offsetSeconds = std::numeric_limits<std::int32_t>::min();
        bool fold = false;
    };

    struct VarianceClockTables {
        VarianceClockInstant start, end, availableFrom;
        std::vector<VarianceClockProfileInput> profiles;
        std::vector<VarianceClockDateInput> dates;
        std::vector<VarianceClockOffsetInput> offsets;
    };

    //! Validated, immutable in-memory tables for a variance clock.
    /*! The local dates represented by the mapping must fall in the range
        supported by QuantLib::Date.  Coverage is start-inclusive and
        end-exclusive and must be nonempty; both endpoints are available to callers.
        Construction rejects the conservative maximum-weight times coverage-days
        bound above DBL_MAX/4, even if the actual weighted sum would fit.
    */
    class VarianceClockSnapshot {
      public:
        ~VarianceClockSnapshot();
        VarianceClockInstant coverageStart() const noexcept;
        VarianceClockInstant coverageEnd() const noexcept;

      private:
        struct Impl;
        explicit VarianceClockSnapshot(std::unique_ptr<Impl> impl);
        std::unique_ptr<Impl> impl_;

        friend std::unique_ptr<VarianceClockSnapshot>
        makeVarianceClockSnapshot(VarianceClockTables&&);
        friend class detail::VarianceClockGeneration;
    };

    //! Validate the tables and construct a snapshot off the query path.
    std::unique_ptr<VarianceClockSnapshot> makeVarianceClockSnapshot(VarianceClockTables&& tables);

}

#endif
