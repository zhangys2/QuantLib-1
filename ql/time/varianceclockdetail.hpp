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
    \brief internal variance-clock run construction
*/

#ifndef quantlib_variance_clock_detail_hpp
#define quantlib_variance_clock_detail_hpp

#include <ql/time/varianceclocktables.hpp>
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

    }
}

#endif
