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

#include "toplevelfixture.hpp"
#include "utilities.hpp"
#include <ql/errors.hpp>
#include <ql/time/varianceclockcsv.hpp>
#include <ql/time/varianceclockmanifest.hpp>
#include <boost/test/unit_test.hpp>
#include <array>
#include <locale>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using namespace QuantLib;

namespace {

    using QuantLib::detail::VarianceClockManifest;
    using QuantLib::detail::VarianceClockCsvSchema;
    using QuantLib::detail::parseEvidenceIdsJson;
    using QuantLib::detail::parseVarianceClockCsv;
    using QuantLib::detail::parseVarianceClockManifest;

    std::string minimalManifest() {
        return R"json({
  "format_version": 1,
  "snapshot_id": "snapshot",
  "generated_at_utc": "2024-01-01T00:00:00Z",
  "coverage_start_utc": "2024-01-01T00:00:00Z",
  "coverage_end_utc": "2025-01-01T00:00:00Z",
  "clock_origin_utc": "2024-01-01T00:00:00Z",
  "market_id": "market",
  "iana_zone": "Etc/UTC",
  "reference_variance_per_5m": "0.01",
  "reference_unit": "variance_per_5m",
  "price_cutoff_utc": "2024-01-01T00:00:00Z",
  "calendar_version": "calendar-v1",
  "calendar_as_of_utc": "2024-01-01T00:00:00Z",
  "calendar_evidence_ids": ["calendar"],
  "timezone_database": "tzdb",
  "timezone_version": "2024a",
  "timezone_as_of_utc": "2024-01-01T00:00:00Z",
  "timezone_evidence_ids": ["timezone"],
  "timezone_rules_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "calibration_settings": {
    "method": "historical_variance_over_common_reference",
    "minimum_direct_returns": 1,
    "gap_pool_return_threshold": null,
    "price_cutoff_utc": "2024-01-01T00:00:00Z"
  },
  "profile_calibrations": [{
    "profile_id": 1,
    "calibration_as_of_utc": "2024-01-01T00:00:00Z",
    "evidence_ids": ["price"]
  }],
  "evidence": [
    {
      "evidence_id": "calendar",
      "role": "calendar_source",
      "source_id": "calendar-feed",
      "revision_id": null,
      "published_at_utc": null,
      "available_at_utc": "2024-01-01T00:00:00Z",
      "uri": "memory:calendar",
      "content_sha256": null,
      "attestation_ref": "receipt:calendar"
    },
    {
      "evidence_id": "timezone",
      "role": "timezone_rules",
      "source_id": "tzdb",
      "revision_id": "2024a",
      "published_at_utc": null,
      "available_at_utc": "2024-01-01T00:00:00Z",
      "uri": "memory:timezone",
      "content_sha256": null,
      "attestation_ref": "receipt:timezone"
    },
    {
      "evidence_id": "price",
      "role": "price_input",
      "source_id": "prices",
      "revision_id": "r1",
      "published_at_utc": "2024-01-01T00:00:00Z",
      "available_at_utc": "2024-01-01T00:00:00Z",
      "uri": "memory:prices",
      "content_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "attestation_ref": null
    }
  ],
  "fallback_approvals": [],
  "warnings": [],
  "files": {
    "profiles.csv": "0000000000000000000000000000000000000000000000000000000000000000",
    "market_days.csv": "0000000000000000000000000000000000000000000000000000000000000000",
    "session_segments.csv": "0000000000000000000000000000000000000000000000000000000000000000",
    "timezone_mapping.csv": "0000000000000000000000000000000000000000000000000000000000000000",
    "slot_evidence.csv": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "continuous_futures_lineage": null
})json";
    }

    void replaceOnce(std::string& input,
                     const std::string& before,
                     const std::string& after) {
        const auto position = input.find(before);
        BOOST_REQUIRE(position != std::string::npos);
        input.replace(position, before.size(), after);
    }

    std::string withUnknownRootKey() {
        std::string input = minimalManifest();
        input.insert(input.find('{') + 1, "\"unexpected\":true,");
        return input;
    }

    void checkManifestRejected(std::string_view input) {
        BOOST_CHECK_THROW(parseVarianceClockManifest(input), Error);
    }

    class CommaDecimalPoint : public std::numpunct<char> {
      protected:
        char do_decimal_point() const override {
            return ',';
        }
    };

    class GlobalLocaleGuard {
      public:
        GlobalLocaleGuard()
        : original_(std::locale()) {
            std::locale::global(std::locale(original_, new CommaDecimalPoint));
        }

        ~GlobalLocaleGuard() {
            std::locale::global(original_);
        }

      private:
        std::locale original_;
    };

}

BOOST_FIXTURE_TEST_SUITE(QuantLibTests, TopLevelFixture)

BOOST_AUTO_TEST_SUITE(VarianceBundleManifestTests)

BOOST_AUTO_TEST_CASE(testRejectsDuplicateNestedObjectKeys) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate nested JSON object keys...");
    std::optional<VarianceClockManifest> parsed;
    BOOST_CHECK_THROW(
        parsed.emplace(parseVarianceClockManifest(R"({"outer":{"key":1,"key":2}})")), Error);
    BOOST_CHECK(!parsed);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingRequiredKey) {
    BOOST_TEST_MESSAGE("Testing rejection of a missing required manifest key...");
    std::string input = minimalManifest();
    replaceOnce(input, "  \"snapshot_id\": \"snapshot\",\n", "");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsWrongJsonType) {
    BOOST_TEST_MESSAGE("Testing rejection of a manifest value with the wrong JSON type...");
    std::string input = minimalManifest();
    replaceOnce(input, "\"snapshot_id\": \"snapshot\"", "\"snapshot_id\": 1");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingCalendarEvidenceIds) {
    BOOST_TEST_MESSAGE("Testing rejection of missing calendar evidence identifiers...");
    std::string input = minimalManifest();
    replaceOnce(input, "  \"calendar_evidence_ids\": [\"calendar\"],\n", "");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingTimezoneEvidenceIds) {
    BOOST_TEST_MESSAGE("Testing rejection of missing timezone evidence identifiers...");
    std::string input = minimalManifest();
    replaceOnce(input, "  \"timezone_evidence_ids\": [\"timezone\"],\n", "");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsNullRequiredValue) {
    BOOST_TEST_MESSAGE("Testing rejection of null for a required manifest value...");
    std::string input = minimalManifest();
    replaceOnce(input, "\"snapshot_id\": \"snapshot\"", "\"snapshot_id\": null");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitManifest) {
    BOOST_TEST_MESSAGE("Testing rejection of a manifest larger than four MiB...");
    const std::string input(4U * 1024U * 1024U + 1U, ' ');
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsDuplicateRootKeys) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate root object keys...");
    std::optional<VarianceClockManifest> parsed;
    BOOST_CHECK_THROW(
        parsed.emplace(parseVarianceClockManifest(
            R"({"format_version":1,"format_version":1})")), Error);
    BOOST_CHECK(!parsed);
}

BOOST_AUTO_TEST_CASE(testRejectsDuplicateArrayEntries) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate entries in a unique manifest array...");
    std::string input = minimalManifest();
    replaceOnce(input,
                "\"calendar_evidence_ids\": [\"calendar\"]",
                "\"calendar_evidence_ids\": [\"calendar\", \"calendar\"]");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsEscapedDuplicateKeys) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate keys after JSON escape decoding...");
    checkManifestRejected(R"({"outer":{"a":1,"\u0061":2}})");
}

BOOST_AUTO_TEST_CASE(testRejectsLoneSurrogate) {
    BOOST_TEST_MESSAGE("Testing rejection of an unpaired UTF-16 surrogate escape...");
    checkManifestRejected(R"({"snapshot_id":"\uD800"})");
}

BOOST_AUTO_TEST_CASE(testRejectsExcessiveNesting) {
    BOOST_TEST_MESSAGE("Testing rejection of JSON nesting deeper than 32 levels...");
    std::string input = "{\"nested\":";
    input.append(32, '[');
    input += '0';
    input.append(32, ']');
    input += '}';
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsUnsupportedFormatVersion) {
    BOOST_TEST_MESSAGE("Testing rejection of an unsupported manifest format version...");
    std::string input = minimalManifest();
    replaceOnce(input, "\"format_version\": 1", "\"format_version\": 2");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsNonIntegerFormatVersion) {
    BOOST_TEST_MESSAGE("Testing rejection of a non-integer format-version token...");
    std::string input = minimalManifest();
    replaceOnce(input, "\"format_version\": 1", "\"format_version\": 1.0");
    checkManifestRejected(input);
    input = minimalManifest();
    replaceOnce(input, "\"format_version\": 1", "\"format_version\": 1e0");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testRejectsUnknownManifestKey) {
    BOOST_TEST_MESSAGE("Testing rejection of an unknown top-level manifest key...");
    checkManifestRejected(withUnknownRootKey());
}

BOOST_AUTO_TEST_CASE(testRejectsTrailingJson) {
    BOOST_TEST_MESSAGE("Testing rejection of trailing JSON after the manifest...");
    checkManifestRejected(minimalManifest() + " null");
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidUtf8) {
    BOOST_TEST_MESSAGE("Testing rejection of invalid UTF-8 in a manifest string...");
    std::string input = minimalManifest();
    const std::string invalidUtf8("\xC0\x80", 2);
    replaceOnce(input,
                "\"snapshot_id\": \"snapshot\"",
                "\"snapshot_id\": \"" + invalidUtf8 + "\"");
    checkManifestRejected(input);
}

BOOST_AUTO_TEST_CASE(testAcceptsMinimalVersionOneManifest) {
    BOOST_TEST_MESSAGE("Testing acceptance of a minimal version-one manifest...");
    const auto manifest = parseVarianceClockManifest(minimalManifest());
    BOOST_CHECK_EQUAL(manifest.formatVersion, 1U);
    BOOST_CHECK_EQUAL(manifest.snapshotId, "snapshot");
    BOOST_CHECK_EQUAL(manifest.calendarEvidenceIds.size(), 1U);
    BOOST_CHECK_EQUAL(manifest.timezoneEvidenceIds.size(), 1U);
    BOOST_CHECK_EQUAL(manifest.evidence.size(), 3U);
    BOOST_CHECK_EQUAL(manifest.files.size(), 5U);
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonAcceptsFlatStringArray) {
    BOOST_TEST_MESSAGE("Testing acceptance of a flat evidence-ID string array...");
    const auto ids = parseEvidenceIdsJson(R"(["price-a","price-b"])");
    BOOST_REQUIRE_EQUAL(ids.size(), 2U);
    BOOST_CHECK_EQUAL(ids[0], "price-a");
    BOOST_CHECK_EQUAL(ids[1], "price-b");
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonRejectsDuplicateIds) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate evidence identifiers...");
    BOOST_CHECK_THROW(parseEvidenceIdsJson(R"(["same","same"])"), Error);
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonRejectsNonStringElements) {
    BOOST_TEST_MESSAGE("Testing rejection of non-string evidence-ID array elements...");
    BOOST_CHECK_THROW(parseEvidenceIdsJson(R"(["price",1])"), Error);
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonRejectsNestedValues) {
    BOOST_TEST_MESSAGE("Testing rejection of nested values in evidence-ID JSON...");
    BOOST_CHECK_THROW(parseEvidenceIdsJson(R"(["price",["nested"]])"), Error);
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonRejectsOverLimitCell) {
    BOOST_TEST_MESSAGE("Testing rejection of an evidence-ID cell larger than 64 KiB...");
    const std::string input(64U * 1024U + 1U, ' ');
    BOOST_CHECK_THROW(parseEvidenceIdsJson(input), Error);
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonRejectsTooManyIds) {
    BOOST_TEST_MESSAGE("Testing rejection of more than 256 evidence identifiers...");
    std::string input = "[";
    for (std::size_t i = 0; i < 257; ++i) {
        if (i != 0)
            input += ',';
        input += "\"id-" + std::to_string(i) + "\"";
    }
    input += ']';
    BOOST_CHECK_THROW(parseEvidenceIdsJson(input), Error);
}

BOOST_AUTO_TEST_CASE(testJsonParsingIgnoresGlobalNumpunct) {
    BOOST_TEST_MESSAGE("Testing JSON manifest parsing under a comma-decimal global locale...");
    GlobalLocaleGuard localeGuard;
    const auto manifest = parseVarianceClockManifest(minimalManifest());
    BOOST_CHECK_EQUAL(manifest.calibrationSettings.minimumDirectReturns, 1U);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(VarianceBundleCsvTests)

BOOST_AUTO_TEST_CASE(testParsesQuotedCommaEscapedQuoteAndEmbeddedNewline) {
    BOOST_TEST_MESSAGE("Testing CSV quoted commas, escaped quotes, and embedded newlines...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\n"
        "a,\"b,c\",\"d\"\"e\",\"line1\nline2\"\n";
    const auto table =
        parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_REQUIRE_EQUAL(table.records[0].fields.size(), 4U);
    BOOST_CHECK_EQUAL(table.records[0].fields[0], "a");
    BOOST_CHECK_EQUAL(table.records[0].fields[1], "\"b,c\"");
    BOOST_CHECK_EQUAL(table.records[0].fields[2], "\"d\"\"e\"");
    BOOST_CHECK_EQUAL(table.records[0].fields[3], "\"line1\nline2\"");
}

BOOST_AUTO_TEST_CASE(testRejectsUnterminatedQuote) {
    BOOST_TEST_MESSAGE("Testing rejection of an unterminated CSV quote...");
    const std::string input = "start_utc,end_utc,offset_seconds,fold\na,\"b,c,d";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsQuoteInUnquotedField) {
    BOOST_TEST_MESSAGE("Testing rejection of a quote in an unquoted CSV field...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na,ab\"c,d,e\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsBytesAfterClosingQuote) {
    BOOST_TEST_MESSAGE("Testing rejection of bytes after a closing CSV quote...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\n\"a\"x,b,c,d\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testAcceptsCrLfAndLf) {
    BOOST_TEST_MESSAGE("Testing acceptance of CRLF and LF CSV record endings...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\r\n"
        "a,b,0,0\r\n"
        "c,d,1,0\n";
    const auto table =
        parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 2U);
    BOOST_CHECK_EQUAL(table.records[0].fields[0], "a");
    BOOST_CHECK_EQUAL(table.records[1].fields[0], "c");
}

BOOST_AUTO_TEST_CASE(testAcceptsMultibyteUtf8) {
    BOOST_TEST_MESSAGE("Testing acceptance of valid multibyte UTF-8 in CSV...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na," + std::string("\xE2\x82\xAC", 3) +
        ",0,0\n";
    const auto table =
        parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_CHECK_EQUAL(table.records[0].fields[1], std::string("\xE2\x82\xAC", 3));
}

BOOST_AUTO_TEST_CASE(testRejectsOverlongUtf8) {
    BOOST_TEST_MESSAGE("Testing rejection of overlong UTF-8 in CSV...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na," + std::string("\xC0\xAF", 2) +
        ",0,0\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsUtf8Surrogate) {
    BOOST_TEST_MESSAGE("Testing rejection of a UTF-8 encoded surrogate in CSV...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na," + std::string("\xED\xA0\x80", 3) +
        ",0,0\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsTruncatedUtf8) {
    BOOST_TEST_MESSAGE("Testing rejection of a truncated UTF-8 sequence in CSV...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na," + std::string("\xE2\x82", 2) +
        ",0,0\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsNulByte) {
    BOOST_TEST_MESSAGE("Testing rejection of a NUL byte in CSV...");
    std::string input = "start_utc,end_utc,offset_seconds,fold\n";
    input.append("a,\0,c,d\n", 8);
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testDistinguishesEmptyAndQuotedEmptyFields) {
    BOOST_TEST_MESSAGE("Testing distinction between empty and quoted-empty CSV fields...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\n,\"\",0,0\n";
    const auto table =
        parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_CHECK(table.records[0].fields[0].empty());
    BOOST_CHECK_EQUAL(table.records[0].fields[1], "\"\"");
}

BOOST_AUTO_TEST_CASE(testAcceptsFinalRecordWithoutNewline) {
    BOOST_TEST_MESSAGE("Testing acceptance of a final CSV record without a newline...");
    const std::string input = "start_utc,end_utc,offset_seconds,fold\na,b,0,0";
    const auto table =
        parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_CHECK_EQUAL(table.records[0].fields[3], "0");
}

BOOST_AUTO_TEST_CASE(testRejectsBlankLine) {
    BOOST_TEST_MESSAGE("Testing rejection of a blank CSV record...");
    const std::string input = "start_utc,end_utc,offset_seconds,fold\n\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsBareCr) {
    BOOST_TEST_MESSAGE("Testing rejection of a bare CR in CSV...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na,b\r,c,d\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testAcceptsHeaderOnlySyntax) {
    BOOST_TEST_MESSAGE("Testing exact frozen CSV headers with no data records...");
    const std::array<std::pair<VarianceClockCsvSchema, std::string_view>, 5> headers{{
        {VarianceClockCsvSchema::Profiles,
         "profile_id,minute_of_day,variance_per_5m,weight\n"},
        {VarianceClockCsvSchema::MarketDays,
         "local_date,date_type,is_open,profile_id,target_group_id,selection_reason\n"},
        {VarianceClockCsvSchema::SessionSegments,
         "local_date,start_utc,end_utc,session_id,trading_date,source_session_id,"
         "claimed_local_offset_seconds,source_evidence_id\n"},
        {VarianceClockCsvSchema::TimezoneMapping,
         "start_utc,end_utc,offset_seconds,fold\n"},
        {VarianceClockCsvSchema::SlotEvidence,
         "profile_id,target_group_id,minute_of_day,source_group_id,target_return_count,"
         "source_return_count,target_distinct_local_date_count,"
         "source_distinct_local_date_count,estimation_method,grouping_label,"
         "gap_pool_return_count,fallback_id,warning_codes,evidence_ids_json\n"}
    }};
    for (const auto& entry : headers) {
        const auto table = parseVarianceClockCsv(entry.second, entry.first);
        BOOST_CHECK(table.records.empty());
    }
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitRowCount) {
    BOOST_TEST_MESSAGE("Testing rejection of more than 400,000 CSV data rows...");
    std::string input = "start_utc,end_utc,offset_seconds,fold\n";
    input.reserve(input.size() + 400001U * 8U);
    for (std::size_t i = 0; i < 400001; ++i)
        input += "a,b,0,0\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitField) {
    BOOST_TEST_MESSAGE("Testing rejection of a CSV field larger than one MiB...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\n" +
        std::string(1024U * 1024U + 1U, 'x') + ",b,0,0\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitRecord) {
    BOOST_TEST_MESSAGE("Testing rejection of a CSV record larger than four MiB...");
    std::string input =
        "profile_id,target_group_id,minute_of_day,source_group_id,target_return_count,"
        "source_return_count,target_distinct_local_date_count,"
        "source_distinct_local_date_count,estimation_method,grouping_label,"
        "gap_pool_return_count,fallback_id,warning_codes,evidence_ids_json\n";
    const std::string field(900U * 1024U, 'x');
    for (std::size_t i = 0; i < 14; ++i) {
        if (i != 0)
            input += ',';
        if (i < 5)
            input += field;
    }
    input += '\n';
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::SlotEvidence),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsUnexpectedBom) {
    BOOST_TEST_MESSAGE("Testing rejection of a UTF-8 BOM before the CSV header...");
    const std::string input =
        std::string("\xEF\xBB\xBF", 3) + "start_utc,end_utc,offset_seconds,fold\n";
    BOOST_CHECK_THROW(parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsWrongHeaderOrFieldCount) {
    BOOST_TEST_MESSAGE("Testing rejection of a wrong CSV header or field count...");
    const std::string wrongHeader = "start_utc,end_utc,offset_seconds,other\n";
    BOOST_CHECK_THROW(
        parseVarianceClockCsv(wrongHeader, VarianceClockCsvSchema::TimezoneMapping), Error);
    const std::string wrongWidth =
        "start_utc,end_utc,offset_seconds,fold\na,b,0\n";
    BOOST_CHECK_THROW(
        parseVarianceClockCsv(wrongWidth, VarianceClockCsvSchema::TimezoneMapping), Error);
}

BOOST_AUTO_TEST_CASE(testCsvScanningIgnoresGlobalNumpunct) {
    BOOST_TEST_MESSAGE("Testing CSV scanning under a comma-decimal global locale...");
    GlobalLocaleGuard localeGuard;
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\na,b,123,0\n";
    const auto table =
        parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_CHECK_EQUAL(table.records[0].fields[2], "123");
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
