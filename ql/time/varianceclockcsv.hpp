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

#include <cstddef>
#include <string>
#include <string_view>

namespace QuantLib {
    namespace detail {

        enum class VarianceClockCsvSchema {
            Profiles,
            MarketDays,
            SessionSegments,
            TimezoneMapping,
            SlotEvidence
        };

        using VarianceClockCsvRowVisitor =
            bool (*)(void*, const std::string_view*, std::size_t);

        // The field array and its views are valid only during the callback.
        // Returns false if the visitor stops early; true means all rows were parsed.
        bool visitVarianceClockCsvRows(std::string_view bytes,
                                       VarianceClockCsvSchema schema,
                                       void* context,
                                       VarianceClockCsvRowVisitor visitor);

        // Decode one valid raw field lexeme, removing quote syntax and unescaping "".
        std::string decodeVarianceClockCsvField(std::string_view lexeme);

    }
}

#endif
