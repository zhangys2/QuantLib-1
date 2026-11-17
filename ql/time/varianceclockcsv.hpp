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

/*! \file varianceclockcsv.hpp
    \brief internal variance-clock CSV parser types
*/

#ifndef quantlib_variance_clock_csv_hpp
#define quantlib_variance_clock_csv_hpp

#include <string_view>
#include <vector>

namespace QuantLib {
    namespace detail {

        enum class VarianceClockCsvSchema {
            Profiles,
            MarketDays,
            SessionSegments,
            TimezoneMapping,
            SlotEvidence
        };

        struct VarianceClockCsvRecord {
            std::vector<std::string_view> fields;
        };

        struct VarianceClockCsvTable {
            std::vector<VarianceClockCsvRecord> records;
        };

        // Field views contain the original CSV lexemes, including quote syntax.
        // The input buffer must outlive the returned table.
        VarianceClockCsvTable parseVarianceClockCsv(std::string_view bytes,
                                                    VarianceClockCsvSchema schema);

    }
}

#endif
