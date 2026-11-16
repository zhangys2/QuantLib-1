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

/*! \file varianceclockdetail.hpp
    \brief internal variance-clock run construction and numeric engine
*/

#ifndef quantlib_variance_clock_detail_hpp
#define quantlib_variance_clock_detail_hpp

#include <ql/time/varianceclocktables.hpp>
#include <array>
#include <cstddef>
#include <vector>

namespace QuantLib {
    namespace detail {

        struct VarianceClockRun {
            VarianceClockInstant start, end;
            Date localDate;
            VarianceClockProfileId profile;
            std::int32_t offsetSeconds;
            bool fold;
        };

        //! Validate and normalize the tables and split their covered UTC interval.
        std::vector<VarianceClockRun> buildVarianceClockRuns(VarianceClockTables& tables);

        enum class VarianceClockNumericStatus { Ok, Expired };

        struct VarianceClockNumericResult {
            VarianceClockNumericStatus status;
            double weightedDays;
        };

        struct VarianceClockNumericPosition {
            VarianceClockInstant time;
            Size run;
            Size slot;
        };

        //! Numeric operations require valid instants within the inclusive coverage endpoints.
        class VarianceClockNumericEngine {
          public:
            explicit VarianceClockNumericEngine(VarianceClockTables&& tables);

            VarianceClockInstant coverageStart() const noexcept;
            VarianceClockInstant coverageEnd() const noexcept;
            VarianceClockNumericPosition prepareExpiry(VarianceClockInstant time) const noexcept;
            VarianceClockNumericResult cumulativeFromCoverageStart(
                VarianceClockInstant time, std::size_t* visitedNodes = nullptr) const noexcept;
            VarianceClockNumericResult remaining(
                VarianceClockInstant time, const VarianceClockNumericPosition& expiry,
                std::size_t* visitedNodes = nullptr) const noexcept;

          private:
            using ProfileTree = std::array<double, 2 * 288>;
            Size endpointSlot(Size run, VarianceClockInstant time) const noexcept;
            double runValue(Size run, VarianceClockInstant start, VarianceClockInstant end,
                            Size endSlot, std::size_t* visitedNodes) const noexcept;

            VarianceClockTables tables_;
            std::vector<VarianceClockRun> runs_;
            std::vector<Size> runProfiles_;
            std::vector<ProfileTree> profileTrees_;
            std::vector<double> runTree_;
        };

    }
}

#endif
