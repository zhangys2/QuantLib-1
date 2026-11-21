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

#include <array>
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

        struct VarianceClockProfilesCsv {
            enum Column : std::size_t { profileId, minuteOfDay, variancePer5m, weight, columnCount };
            inline static constexpr std::array<std::string_view, columnCount> header{{
                "profile_id", "minute_of_day", "variance_per_5m", "weight"}};
        };

        struct VarianceClockMarketDaysCsv {
            enum Column : std::size_t {
                localDate, dateType, isOpen, profileId, targetGroupId, selectionReason, columnCount
            };
            inline static constexpr std::array<std::string_view, columnCount> header{{
                "local_date", "date_type", "is_open", "profile_id", "target_group_id",
                "selection_reason"}};
        };

        struct VarianceClockSessionSegmentsCsv {
            enum Column : std::size_t {
                localDate, startUtc, endUtc, sessionId, tradingDate, sourceSessionId,
                claimedLocalOffsetSeconds, sourceEvidenceId, columnCount
            };
            inline static constexpr std::array<std::string_view, columnCount> header{{
                "local_date", "start_utc", "end_utc", "session_id", "trading_date",
                "source_session_id", "claimed_local_offset_seconds", "source_evidence_id"}};
        };

        struct VarianceClockTimezoneMappingCsv {
            enum Column : std::size_t { startUtc, endUtc, offsetSeconds, fold, columnCount };
            inline static constexpr std::array<std::string_view, columnCount> header{{
                "start_utc", "end_utc", "offset_seconds", "fold"}};
        };

        struct VarianceClockSlotEvidenceCsv {
            enum Column : std::size_t {
                profileId, targetGroupId, minuteOfDay, sourceGroupId, targetReturnCount,
                sourceReturnCount, targetDistinctLocalDateCount, sourceDistinctLocalDateCount,
                estimationMethod, groupingLabel, gapPoolReturnCount, fallbackId, warningCodes,
                evidenceIdsJson, columnCount
            };
            inline static constexpr std::array<std::string_view, columnCount> header{{
                "profile_id", "target_group_id", "minute_of_day", "source_group_id",
                "target_return_count", "source_return_count",
                "target_distinct_local_date_count", "source_distinct_local_date_count",
                "estimation_method", "grouping_label", "gap_pool_return_count", "fallback_id",
                "warning_codes", "evidence_ids_json"}};
        };

        struct VarianceClockCsvFormat {
            const std::string_view* header;
            std::size_t columnCount;
        };

        inline VarianceClockCsvFormat varianceClockCsvFormat(VarianceClockCsvSchema schema) {
            switch (schema) {
              case VarianceClockCsvSchema::Profiles:
                return {VarianceClockProfilesCsv::header.data(),
                        VarianceClockProfilesCsv::header.size()};
              case VarianceClockCsvSchema::MarketDays:
                return {VarianceClockMarketDaysCsv::header.data(),
                        VarianceClockMarketDaysCsv::header.size()};
              case VarianceClockCsvSchema::SessionSegments:
                return {VarianceClockSessionSegmentsCsv::header.data(),
                        VarianceClockSessionSegmentsCsv::header.size()};
              case VarianceClockCsvSchema::TimezoneMapping:
                return {VarianceClockTimezoneMappingCsv::header.data(),
                        VarianceClockTimezoneMappingCsv::header.size()};
              case VarianceClockCsvSchema::SlotEvidence:
                return {VarianceClockSlotEvidenceCsv::header.data(),
                        VarianceClockSlotEvidenceCsv::header.size()};
            }
            return {nullptr, 0};
        }

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
