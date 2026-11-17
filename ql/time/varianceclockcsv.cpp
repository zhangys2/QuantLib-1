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

#include <ql/time/varianceclockcsv.hpp>
#include <ql/errors.hpp>

#include <array>
#include <cstddef>
#include <string_view>
#include <utility>

namespace QuantLib {
    namespace detail {
        namespace {

            constexpr std::size_t maxCsvBytes = 32U * 1024U * 1024U;
            constexpr std::size_t maxCsvRows = 400000U;
            constexpr std::size_t maxCsvRecordBytes = 4U * 1024U * 1024U;
            constexpr std::size_t maxCsvFieldBytes = 1024U * 1024U;

            const std::string_view* expectedHeader(VarianceClockCsvSchema schema,
                                                   std::size_t& size) {
                static constexpr std::array<std::string_view, 4> profiles{{
                    "profile_id", "minute_of_day", "variance_per_5m", "weight"}};
                static constexpr std::array<std::string_view, 6> marketDays{{
                    "local_date", "date_type", "is_open", "profile_id", "target_group_id",
                    "selection_reason"}};
                static constexpr std::array<std::string_view, 8> sessionSegments{{
                    "local_date", "start_utc", "end_utc", "session_id", "trading_date",
                    "source_session_id", "claimed_local_offset_seconds", "source_evidence_id"}};
                static constexpr std::array<std::string_view, 4> timezoneMapping{{
                    "start_utc", "end_utc", "offset_seconds", "fold"}};
                static constexpr std::array<std::string_view, 14> slotEvidence{{
                    "profile_id", "target_group_id", "minute_of_day", "source_group_id",
                    "target_return_count", "source_return_count",
                    "target_distinct_local_date_count", "source_distinct_local_date_count",
                    "estimation_method", "grouping_label", "gap_pool_return_count",
                    "fallback_id", "warning_codes", "evidence_ids_json"}};

                switch (schema) {
                  case VarianceClockCsvSchema::Profiles:
                    size = profiles.size();
                    return profiles.data();
                  case VarianceClockCsvSchema::MarketDays:
                    size = marketDays.size();
                    return marketDays.data();
                  case VarianceClockCsvSchema::SessionSegments:
                    size = sessionSegments.size();
                    return sessionSegments.data();
                  case VarianceClockCsvSchema::TimezoneMapping:
                    size = timezoneMapping.size();
                    return timezoneMapping.data();
                  case VarianceClockCsvSchema::SlotEvidence:
                    size = slotEvidence.size();
                    return slotEvidence.data();
                }
                QL_FAIL("invalid variance-clock CSV schema");
            }

            void validateUtf8(std::string_view bytes) {
                for (std::size_t i = 0; i < bytes.size();) {
                    const auto first = static_cast<unsigned char>(bytes[i]);
                    QL_REQUIRE(first != 0, "NUL byte in variance-clock CSV");

                    if (i + 2 < bytes.size() && first == 0xEF &&
                        static_cast<unsigned char>(bytes[i + 1]) == 0xBB &&
                        static_cast<unsigned char>(bytes[i + 2]) == 0xBF)
                        QL_FAIL("UTF-8 BOM in variance-clock CSV");

                    if (first <= 0x7F) {
                        ++i;
                        continue;
                    }

                    std::size_t continuationCount = 0;
                    unsigned char secondMinimum = 0x80;
                    unsigned char secondMaximum = 0xBF;
                    if (first >= 0xC2 && first <= 0xDF) {
                        continuationCount = 1;
                    } else if (first == 0xE0) {
                        continuationCount = 2;
                        secondMinimum = 0xA0;
                    } else if (first >= 0xE1 && first <= 0xEC) {
                        continuationCount = 2;
                    } else if (first == 0xED) {
                        continuationCount = 2;
                        secondMaximum = 0x9F;
                    } else if (first >= 0xEE && first <= 0xEF) {
                        continuationCount = 2;
                    } else if (first == 0xF0) {
                        continuationCount = 3;
                        secondMinimum = 0x90;
                    } else if (first >= 0xF1 && first <= 0xF3) {
                        continuationCount = 3;
                    } else if (first == 0xF4) {
                        continuationCount = 3;
                        secondMaximum = 0x8F;
                    } else {
                        QL_FAIL("invalid UTF-8 in variance-clock CSV");
                    }

                    QL_REQUIRE(i + continuationCount < bytes.size(),
                               "truncated UTF-8 in variance-clock CSV");
                    const auto second = static_cast<unsigned char>(bytes[i + 1]);
                    QL_REQUIRE(second >= secondMinimum && second <= secondMaximum,
                               "invalid UTF-8 scalar in variance-clock CSV");
                    for (std::size_t j = 2; j <= continuationCount; ++j) {
                        const auto next = static_cast<unsigned char>(bytes[i + j]);
                        QL_REQUIRE(next >= 0x80 && next <= 0xBF,
                                   "invalid UTF-8 continuation in variance-clock CSV");
                    }
                    i += continuationCount + 1;
                }
            }

            bool isRecordEnd(std::string_view bytes, std::size_t position) {
                return position == bytes.size() || bytes[position] == '\n' ||
                       bytes[position] == '\r';
            }

            void validateRecordEnd(std::string_view bytes, std::size_t& position) {
                if (position == bytes.size())
                    return;
                if (bytes[position] == '\n') {
                    ++position;
                    return;
                }
                QL_REQUIRE(bytes[position] == '\r' && position + 1 < bytes.size() &&
                               bytes[position + 1] == '\n',
                           "bare CR in variance-clock CSV");
                position += 2;
            }

            std::string_view parseField(std::string_view bytes,
                                        std::size_t& position) {
                const std::size_t start = position;
                if (position < bytes.size() && bytes[position] == '"') {
                    ++position;
                    bool closed = false;
                    while (position < bytes.size()) {
                        if (bytes[position] == '"') {
                            if (position + 1 < bytes.size() && bytes[position + 1] == '"') {
                                position += 2;
                            } else {
                                ++position;
                                closed = true;
                                break;
                            }
                        } else if (bytes[position] == '\r') {
                            QL_REQUIRE(position + 1 < bytes.size() &&
                                           bytes[position + 1] == '\n',
                                       "bare CR in quoted variance-clock CSV field");
                            position += 2;
                        } else {
                            ++position;
                        }
                    }
                    QL_REQUIRE(closed, "unterminated quoted variance-clock CSV field");
                    QL_REQUIRE(isRecordEnd(bytes, position) || bytes[position] == ',',
                               "unexpected byte after quoted variance-clock CSV field");
                } else {
                    while (position < bytes.size() && bytes[position] != ',' &&
                           bytes[position] != '\n' && bytes[position] != '\r') {
                        QL_REQUIRE(bytes[position] != '"',
                                   "quote in unquoted variance-clock CSV field");
                        ++position;
                    }
                }
                const std::size_t length = position - start;
                QL_REQUIRE(length <= maxCsvFieldBytes,
                           "variance-clock CSV field exceeds 1 MiB");
                return bytes.substr(start, length);
            }

        }

        VarianceClockCsvTable parseVarianceClockCsv(std::string_view bytes,
                                                    VarianceClockCsvSchema schema) {
            QL_REQUIRE(bytes.size() <= maxCsvBytes,
                       "variance-clock CSV exceeds 32 MiB");
            validateUtf8(bytes);
            QL_REQUIRE(!bytes.empty(), "empty variance-clock CSV");

            std::size_t expectedCount = 0;
            const auto* header = expectedHeader(schema, expectedCount);
            VarianceClockCsvTable result;
            bool isHeader = true;
            std::size_t position = 0;

            while (position < bytes.size()) {
                const std::size_t recordStart = position;
                VarianceClockCsvRecord record;
                bool finishedRecord = false;
                while (!finishedRecord) {
                    record.fields.push_back(parseField(bytes, position));
                    QL_REQUIRE(position - recordStart <= maxCsvRecordBytes,
                               "variance-clock CSV record exceeds 4 MiB");
                    if (position == bytes.size()) {
                        finishedRecord = true;
                    } else if (bytes[position] == ',') {
                        ++position;
                    } else {
                        validateRecordEnd(bytes, position);
                        finishedRecord = true;
                    }
                }

                QL_REQUIRE(record.fields.size() == expectedCount,
                           "wrong field count in variance-clock CSV");
                if (isHeader) {
                    for (std::size_t i = 0; i < expectedCount; ++i)
                        QL_REQUIRE(record.fields[i] == header[i],
                                   "wrong variance-clock CSV header");
                    isHeader = false;
                } else {
                    QL_REQUIRE(result.records.size() < maxCsvRows,
                               "variance-clock CSV exceeds 400,000 data rows");
                    result.records.push_back(std::move(record));
                }
            }

            QL_REQUIRE(!isHeader, "missing variance-clock CSV header");
            return result;
        }

    }
}
