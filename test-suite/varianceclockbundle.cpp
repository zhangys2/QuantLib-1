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
#include <ql/utilities/detail/variancesha256.hpp>
#include <boost/test/unit_test.hpp>
#include <array>
#include <cstddef>
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

    std::string manifestWithOptionalSections() {
        std::string input = minimalManifest();
        replaceOnce(input, "\"gap_pool_return_threshold\": null",
                    "\"gap_pool_return_threshold\": 3");
        replaceOnce(input, "\"fallback_approvals\": []",
                    "\"fallback_approvals\": [{\"fallback_id\": \"fb\", \"approved\": true, "
                    "\"approval_evidence_ids\": [\"approval\"], "
                    "\"source_evidence_ids\": [\"price\"]}]");
        replaceOnce(input, "\"warnings\": []",
                    "\"warnings\": [{\"code\": \"ZERO_RATE_SLOT\", \"severity\": \"warning\", "
                    "\"profile_id\": 1, \"target_group_id\": \"group\", \"minute_of_day\": 5, "
                    "\"evidence_ids\": [\"price\"]}]");
        replaceOnce(input, "\"continuous_futures_lineage\": null",
                    "\"continuous_futures_lineage\": {\"construction_method\": \"roll\", "
                    "\"source_instrument\": \"ES\", \"continuous_symbol\": \"ES1\", "
                    "\"roll_rule\": \"volume\", \"roll_schedule_evidence_ids\": [\"roll\"], "
                    "\"contract_mapping_evidence_ids\": [\"map\"]}");
        return input;
    }

    // A rejection raised by the JSON stage (SAX handler or lexer) rather than by a
    // later schema check; the message comes from parseJson().
    bool isJsonStageError(const Error& e) {
        return std::string(e.what()).find("invalid or unsupported JSON input") !=
               std::string::npos;
    }

    bool isSizeLimitError(const Error& e) {
        return std::string(e.what()).find("exceeds size limit") != std::string::npos;
    }

    void checkJsonStageRejected(std::string_view input) {
        BOOST_CHECK_EXCEPTION(parseVarianceClockManifest(input), Error, isJsonStageError);
    }

    // Nested arrays under one root object, so the document has 1 + arrays levels.
    std::string nestedArraysDocument(std::size_t arrays) {
        std::string input = "{\"nested\":";
        input.append(arrays, '[');
        input += '0';
        input.append(arrays, ']');
        input += '}';
        return input;
    }

    std::string withUnknownRootKey() {
        std::string input = minimalManifest();
        input.insert(input.find('{') + 1, "\"unexpected\":true,");
        return input;
    }

    bool isAccepted(std::string_view input) {
        try {
            parseVarianceClockManifest(input);
            return true;
        } catch (const Error&) {
            return false;
        }
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
    // Otherwise valid manifest: only the repeated nested key can cause the rejection.
    std::string input = minimalManifest();
    const std::string method = "\"method\": \"historical_variance_over_common_reference\",";
    replaceOnce(input, method, method + "\n    " + method);
    std::optional<VarianceClockManifest> parsed;
    BOOST_CHECK_EXCEPTION(parsed.emplace(parseVarianceClockManifest(input)), Error,
                          isJsonStageError);
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
    const std::size_t limit = 4U * 1024U * 1024U;
    std::string input = minimalManifest();
    input.append(limit - input.size(), ' ');
    BOOST_REQUIRE_EQUAL(input.size(), limit);
    BOOST_CHECK_NO_THROW(parseVarianceClockManifest(input));
    input += ' ';
    BOOST_CHECK_EXCEPTION(parseVarianceClockManifest(input), Error, isSizeLimitError);
}

BOOST_AUTO_TEST_CASE(testRejectsDuplicateRootKeys) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate root object keys...");
    std::string input = minimalManifest();
    const std::string key = "\"snapshot_id\": \"snapshot\",";
    replaceOnce(input, key, key + "\n  " + key);
    std::optional<VarianceClockManifest> parsed;
    BOOST_CHECK_EXCEPTION(parsed.emplace(parseVarianceClockManifest(input)), Error,
                          isJsonStageError);
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
    // Control: an escaped spelling of a key decodes to the schema key and is accepted.
    std::string control = minimalManifest();
    replaceOnce(control, "\"snapshot_id\"", "\"snapshot\\u005fid\"");
    BOOST_CHECK_EQUAL(parseVarianceClockManifest(control).snapshotId, "snapshot");

    std::string root = minimalManifest();
    const std::string key = "\"snapshot_id\": \"snapshot\",";
    replaceOnce(root, key, key + "\n  \"snapshot\\u005fid\": \"snapshot\",");
    checkJsonStageRejected(root);

    std::string nested = minimalManifest();
    const std::string method = "\"method\": \"historical_variance_over_common_reference\",";
    replaceOnce(nested, method,
                method + "\n    \"\\u006dethod\": \"historical_variance_over_common_reference\",");
    checkJsonStageRejected(nested);
}

BOOST_AUTO_TEST_CASE(testRejectsLoneSurrogate) {
    BOOST_TEST_MESSAGE("Testing rejection of an unpaired UTF-16 surrogate escape...");
    // Control: a valid surrogate pair decodes to one UTF-8 code point.
    std::string pair = minimalManifest();
    replaceOnce(pair, "\"snapshot_id\": \"snapshot\"", "\"snapshot_id\": \"\\uD83D\\uDE00\"");
    BOOST_CHECK_EQUAL(parseVarianceClockManifest(pair).snapshotId, "\xF0\x9F\x98\x80");

    for (const char* lone : {"\\uD800", "\\uDC00", "\\uD800x", "\\uD800\\u0041"}) {
        std::string input = minimalManifest();
        replaceOnce(input, "\"snapshot_id\": \"snapshot\"",
                    std::string("\"snapshot_id\": \"") + lone + "\"");
        checkJsonStageRejected(input);
    }
}

BOOST_AUTO_TEST_CASE(testRejectsExcessiveNesting) {
    BOOST_TEST_MESSAGE("Testing rejection of JSON nesting deeper than 32 levels...");
    // 32 levels (root object plus 31 arrays) pass the JSON stage and fail the schema
    // check instead; 33 levels are rejected by the JSON stage.
    BOOST_CHECK_EXCEPTION(parseVarianceClockManifest(nestedArraysDocument(31)), Error,
                          [](const Error& e) { return !isJsonStageError(e); });
    checkJsonStageRejected(nestedArraysDocument(32));
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
    checkJsonStageRejected(minimalManifest() + " null");
    checkJsonStageRejected(minimalManifest() + minimalManifest());
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidUtf8) {
    BOOST_TEST_MESSAGE("Testing rejection of invalid UTF-8 in a manifest string...");
    for (const std::string& invalid : {std::string("\xC0\x80", 2), std::string("\xFF", 1),
                                       std::string("\xED\xA0\x80", 3),
                                       std::string("\xE2\x82", 2)}) {
        std::string input = minimalManifest();
        replaceOnce(input, "\"snapshot_id\": \"snapshot\"",
                    "\"snapshot_id\": \"" + invalid + "\"");
        checkJsonStageRejected(input);
    }
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
    const std::size_t limit = 64U * 1024U;
    std::string input = "[\"a\"]";
    input.append(limit - input.size(), ' ');
    BOOST_REQUIRE_EQUAL(input.size(), limit);
    BOOST_CHECK_EQUAL(parseEvidenceIdsJson(input).size(), 1U);
    input += ' ';
    BOOST_CHECK_EXCEPTION(parseEvidenceIdsJson(input), Error, isSizeLimitError);
}

BOOST_AUTO_TEST_CASE(testEvidenceIdsJsonRejectsTooManyIds) {
    BOOST_TEST_MESSAGE("Testing rejection of more than 256 evidence identifiers...");
    auto array = [](std::size_t count) {
        std::string input = "[";
        for (std::size_t i = 0; i < count; ++i) {
            if (i != 0)
                input += ',';
            input += "\"id-" + std::to_string(i) + "\"";
        }
        return input + ']';
    };
    BOOST_CHECK_EQUAL(parseEvidenceIdsJson(array(256)).size(), 256U);
    BOOST_CHECK_THROW(parseEvidenceIdsJson(array(257)), Error);
}

BOOST_AUTO_TEST_CASE(testEnforcesIdentifierByteLimit) {
    BOOST_TEST_MESSAGE("Testing the 128-byte manifest and evidence-ID limit...");
    const std::string accepted(128, 'x');
    const std::string rejected(129, 'x');
    std::string manifest = minimalManifest();
    replaceOnce(manifest, "\"snapshot_id\": \"snapshot\"",
                "\"snapshot_id\": \"" + accepted + "\"");
    BOOST_CHECK_NO_THROW(parseVarianceClockManifest(manifest));
    manifest = minimalManifest();
    replaceOnce(manifest, "\"snapshot_id\": \"snapshot\"",
                "\"snapshot_id\": \"" + rejected + "\"");
    BOOST_CHECK_THROW(parseVarianceClockManifest(manifest), Error);

    BOOST_CHECK_EQUAL(parseEvidenceIdsJson("[\"" + accepted + "\"]").size(), 1U);
    BOOST_CHECK_THROW(parseEvidenceIdsJson("[\"" + rejected + "\"]"), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsManifestIdentifiersWithWhitespaceOrControls) {
    BOOST_TEST_MESSAGE("Testing manifest identifier whitespace and control-character rules...");
    const std::vector<std::pair<std::string, std::string>> minimalEdits = {
        {"\"snapshot_id\": \"snapshot\"", "\"snapshot_id\": \" snapshot\""},
        {"\"snapshot_id\": \"snapshot\"", "\"snapshot_id\": \"snapshot \""},
        {"\"snapshot_id\": \"snapshot\"", "\"snapshot_id\": \"\\u00a0snapshot\""},
        {"\"market_id\": \"market\"", "\"market_id\": \"mar\\u0000ket\""},
        {"\"iana_zone\": \"Etc/UTC\"", "\"iana_zone\": \"Etc/UTC\\u0085\""},
        {"\"calendar_version\": \"calendar-v1\"", "\"calendar_version\": \"calendar\\u001fv1\""},
        {"\"timezone_database\": \"tzdb\"", "\"timezone_database\": \"tz\\u007fdb\""},
        {"\"timezone_version\": \"2024a\"", "\"timezone_version\": \"2024a\\u009f\""},
        {"\"evidence_id\": \"calendar\"", "\"evidence_id\": \"calendar\\u0000\""},
        {"\"source_id\": \"calendar-feed\"", "\"source_id\": \" calendar-feed\""},
        {"\"revision_id\": \"2024a\"", "\"revision_id\": \"2024a\\u0085\""},
    };
    for (const auto& edit : minimalEdits) {
        std::string input = minimalManifest();
        replaceOnce(input, edit.first, edit.second);
        BOOST_CHECK_THROW(parseVarianceClockManifest(input), Error);
    }

    const std::vector<std::pair<std::string, std::string>> optionalEdits = {
        {"\"fallback_id\": \"fb\"", "\"fallback_id\": \"fb\\u0000\""},
        {"\"target_group_id\": \"group\"", "\"target_group_id\": \" group\""},
        {"\"source_instrument\": \"ES\"", "\"source_instrument\": \"ES\\u007f\""},
        {"\"continuous_symbol\": \"ES1\"", "\"continuous_symbol\": \"ES1\\u0085\""},
    };
    for (const auto& edit : optionalEdits) {
        std::string input = manifestWithOptionalSections();
        replaceOnce(input, edit.first, edit.second);
        BOOST_CHECK_THROW(parseVarianceClockManifest(input), Error);
    }
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidEvidenceArrayIdentifiers) {
    BOOST_TEST_MESSAGE("Testing identifier rules in manifest and embedded evidence-ID arrays...");
    for (const std::string& input : {
             std::string(R"([" leading"])"), std::string(R"(["trailing "])"),
             std::string(R"(["inside\u0000control"])"),
             std::string(R"(["\u0085control"])")})
        BOOST_CHECK_THROW(parseEvidenceIdsJson(input), Error);

    std::string manifest = minimalManifest();
    replaceOnce(manifest, "\"calendar_evidence_ids\": [\"calendar\"]",
                "\"calendar_evidence_ids\": [\"calendar\\u0000\"]");
    BOOST_CHECK_THROW(parseVarianceClockManifest(manifest), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsManifestUtf8Bom) {
    BOOST_TEST_MESSAGE("Testing rejection of a leading UTF-8 BOM in the manifest...");
    const std::string input = std::string("\xEF\xBB\xBF", 3) + minimalManifest();
    BOOST_CHECK_THROW(parseVarianceClockManifest(input), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidScalarValues) {
    BOOST_TEST_MESSAGE("Testing rejection of out-of-schema scalar manifest values...");
    const std::vector<std::pair<std::string, std::string>> edits = {
        {"\"role\": \"calendar_source\"", "\"role\": \"bogus\""},
        {"\"content_sha256\": \"0", "\"content_sha256\": \"A"},
        {"\"minimum_direct_returns\": 1", "\"minimum_direct_returns\": 0"},
        {"\"minimum_direct_returns\": 1", "\"minimum_direct_returns\": -1"},
        {"\"reference_unit\": \"variance_per_5m\"", "\"reference_unit\": \"other\""},
        {"\"profile_id\": 1,", "\"profile_id\": 4294967296,"},
        {"\"profile_id\": 1,", "\"profile_id\": \"1\","},
        {"\"profile_id\": 1,", "\"profile_id\": 1.0,"},
        {"\"profile_id\": 1,", "\"profile_id\": -0,"},
        {"\"timezone_mapping.csv\"", "\"timezone.csv\""},
        {"\"timezone_rules_sha256\": \"0", "\"timezone_rules_sha256\": \"F"},
        {"null,\n    \"price_cutoff_utc\": \"2024-01-01T00:00:00Z\"",
         "null,\n    \"price_cutoff_utc\": \"2024-01-01T00:00:01Z\""},
        {"\"fallback_approvals\": []", "\"fallback_approvals\": {}"},
        {"\"profile_calibrations\": [{", "\"profile_calibrations\": [{\"profile_id\": 1}, {"},
    };
    for (const auto& edit : edits) {
        std::string input = minimalManifest();
        replaceOnce(input, edit.first, edit.second);
        BOOST_CHECK_MESSAGE(!isAccepted(input), "accepted invalid edit: " << edit.second);
    }
}

BOOST_AUTO_TEST_CASE(testAcceptsOptionalVersionOneSections) {
    BOOST_TEST_MESSAGE("Testing acceptance of populated optional manifest sections...");
    const std::string input = manifestWithOptionalSections();
    const auto manifest = parseVarianceClockManifest(input);
    BOOST_REQUIRE(manifest.calibrationSettings.gapPoolReturnThreshold);
    BOOST_CHECK_EQUAL(*manifest.calibrationSettings.gapPoolReturnThreshold, 3U);
    BOOST_REQUIRE_EQUAL(manifest.fallbackApprovals.size(), 1U);
    BOOST_CHECK_EQUAL(manifest.fallbackApprovals[0].fallbackId, "fb");
    BOOST_CHECK(manifest.fallbackApprovals[0].approved);
    BOOST_CHECK_EQUAL(manifest.fallbackApprovals[0].approvalEvidenceIds[0], "approval");
    BOOST_CHECK_EQUAL(manifest.fallbackApprovals[0].sourceEvidenceIds[0], "price");
    BOOST_REQUIRE_EQUAL(manifest.warnings.size(), 1U);
    BOOST_CHECK_EQUAL(manifest.warnings[0].code, "ZERO_RATE_SLOT");
    BOOST_CHECK_EQUAL(manifest.warnings[0].profileId, 1U);
    BOOST_CHECK_EQUAL(manifest.warnings[0].targetGroupId, "group");
    BOOST_CHECK_EQUAL(manifest.warnings[0].minuteOfDay, 5U);
    BOOST_REQUIRE(manifest.continuousFuturesLineage);
    BOOST_CHECK_EQUAL(manifest.continuousFuturesLineage->continuousSymbol, "ES1");
    BOOST_CHECK_EQUAL(manifest.continuousFuturesLineage->rollScheduleEvidenceIds[0], "roll");
    BOOST_CHECK_EQUAL(manifest.continuousFuturesLineage->contractMappingEvidenceIds[0], "map");
    BOOST_REQUIRE_EQUAL(manifest.evidence.size(), 3U);
    BOOST_CHECK(!manifest.evidence[0].revisionId);
    BOOST_CHECK(!manifest.evidence[0].contentSha256);
    BOOST_CHECK(manifest.evidence[2].contentSha256);
}

BOOST_AUTO_TEST_CASE(testJsonParsingIgnoresGlobalNumpunct) {
    BOOST_TEST_MESSAGE("Testing JSON manifest parsing under a comma-decimal global locale...");
    GlobalLocaleGuard localeGuard;
    const auto manifest = parseVarianceClockManifest(minimalManifest());
    BOOST_CHECK_EQUAL(manifest.calibrationSettings.minimumDirectReturns, 1U);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(VarianceBundleCsvTests)

namespace {

    const std::string tzHeader = "start_utc,end_utc,offset_seconds,fold\n";
    const std::string slotHeader =
        "profile_id,target_group_id,minute_of_day,source_group_id,target_return_count,"
        "source_return_count,target_distinct_local_date_count,"
        "source_distinct_local_date_count,estimation_method,grouping_label,"
        "gap_pool_return_count,fallback_id,warning_codes,evidence_ids_json\n";

    const std::size_t oneMiB = 1024U * 1024U;

    // Requires a rejection whose message names the rule that fired, so a test cannot pass
    // because some other check happened to reject the input.
    void checkCsvRejected(
        std::string_view input,
        const char* expected,
        VarianceClockCsvSchema schema = VarianceClockCsvSchema::TimezoneMapping) {
        try {
            parseVarianceClockCsv(input, schema);
            BOOST_ERROR("accepted input; expected a rejection mentioning: " << expected);
        } catch (const Error& e) {
            BOOST_CHECK_MESSAGE(std::string(e.what()).find(expected) != std::string::npos,
                                "expected \"" << expected << "\" but got: " << e.what());
        }
    }

    // A slot-evidence record of 14 fields in which only the first four are non-empty.
    // Its size up to the last field is 3 * first + fourth + 13.
    std::string slotRecord(std::size_t first, std::size_t fourth) {
        std::string record(first, 'x');
        record += ',';
        record.append(first, 'x');
        record += ',';
        record.append(first, 'x');
        record += ',';
        record.append(fourth, 'x');
        record.append(10, ',');
        return record;
    }

    std::string timezoneRowWithUtf8(const std::string& bytes) {
        return tzHeader + "a," + bytes + ",0,0\n";
    }

}

BOOST_AUTO_TEST_CASE(testParsesQuotedCommaEscapedQuoteAndEmbeddedNewline) {
    BOOST_TEST_MESSAGE("Testing CSV quoted commas, escaped quotes, and embedded newlines...");
    const std::string input = tzHeader + "a,\"b,c\",\"d\"\"e\",\"line1\nline2\"\n";
    const auto table = parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_REQUIRE_EQUAL(table.records[0].fields.size(), 4U);
    BOOST_CHECK_EQUAL(table.records[0].fields[0], "a");
    BOOST_CHECK_EQUAL(table.records[0].fields[1], "\"b,c\"");
    BOOST_CHECK_EQUAL(table.records[0].fields[2], "\"d\"\"e\"");
    BOOST_CHECK_EQUAL(table.records[0].fields[3], "\"line1\nline2\"");

    // Embedded CRLF is preserved; a field made only of one escaped quote is one lexeme.
    const std::string crlf = tzHeader + "\"x\r\ny\",\"\"\"\",0,0\n";
    const auto second = parseVarianceClockCsv(crlf, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(second.records.size(), 1U);
    BOOST_CHECK_EQUAL(second.records[0].fields[0], "\"x\r\ny\"");
    BOOST_CHECK_EQUAL(second.records[0].fields[1], "\"\"\"\"");

    // Field views point into the caller's buffer.
    const char* begin = input.data();
    const char* end = input.data() + input.size();
    for (const auto& field : table.records[0].fields)
        BOOST_CHECK(field.data() >= begin && field.data() + field.size() <= end);
}

BOOST_AUTO_TEST_CASE(testRejectsUnterminatedQuote) {
    BOOST_TEST_MESSAGE("Testing rejection of an unterminated CSV quote...");
    checkCsvRejected(tzHeader + "a,\"b,c,d", "unterminated");
    checkCsvRejected(tzHeader + "a,b,c,\"", "unterminated");
    // An escaped quote at the end does not close the field.
    checkCsvRejected(tzHeader + "a,b,c,\"d\"\"", "unterminated");
}

BOOST_AUTO_TEST_CASE(testRejectsQuoteInUnquotedField) {
    BOOST_TEST_MESSAGE("Testing rejection of a quote in an unquoted CSV field...");
    checkCsvRejected(tzHeader + "a,ab\"c,d,e\n", "quote in unquoted");
    checkCsvRejected(tzHeader + "a,b,c,d\"\n", "quote in unquoted");
}

BOOST_AUTO_TEST_CASE(testRejectsBytesAfterClosingQuote) {
    BOOST_TEST_MESSAGE("Testing rejection of bytes after a closing CSV quote...");
    checkCsvRejected(tzHeader + "\"a\"x,b,c,d\n", "after quoted");
    checkCsvRejected(tzHeader + "\"a\" ,b,c,d\n", "after quoted");
    checkCsvRejected(tzHeader + "a,b,c,\"d\"\"\"x\n", "after quoted");
}

BOOST_AUTO_TEST_CASE(testAcceptsCrLfAndLf) {
    BOOST_TEST_MESSAGE("Testing acceptance of CRLF and LF CSV record endings...");
    const std::string input =
        "start_utc,end_utc,offset_seconds,fold\r\n"
        "a,b,0,0\r\n"
        "c,d,1,0\n";
    const auto table = parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 2U);
    BOOST_CHECK_EQUAL(table.records[0].fields[0], "a");
    BOOST_CHECK_EQUAL(table.records[0].fields[3], "0");
    BOOST_CHECK_EQUAL(table.records[1].fields[0], "c");
    BOOST_CHECK_EQUAL(table.records[1].fields[2], "1");
}

BOOST_AUTO_TEST_CASE(testAcceptsMultibyteUtf8) {
    BOOST_TEST_MESSAGE("Testing acceptance of valid multibyte UTF-8 in CSV...");
    // The first and last scalar of every encoding length and lead-byte range.
    const std::vector<std::string> valid = {
        std::string("\xC2\x80", 2),         std::string("\xDF\xBF", 2),
        std::string("\xE0\xA0\x80", 3),     std::string("\xE1\x80\x80", 3),
        std::string("\xEC\xBF\xBF", 3),     std::string("\xED\x9F\xBF", 3),
        std::string("\xEE\x80\x80", 3),     std::string("\xEF\xBF\xBD", 3),
        std::string("\xF0\x90\x80\x80", 4), std::string("\xF3\xBF\xBF\xBF", 4),
        std::string("\xF4\x8F\xBF\xBF", 4), std::string("\xE2\x82\xAC", 3)};
    for (const std::string& bytes : valid) {
        const std::string input = timezoneRowWithUtf8(bytes);
        const auto table =
            parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
        BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
        BOOST_CHECK_EQUAL(table.records[0].fields[1], bytes);
    }
}

BOOST_AUTO_TEST_CASE(testRejectsOverlongUtf8) {
    BOOST_TEST_MESSAGE("Testing rejection of overlong UTF-8 in CSV...");
    const std::vector<std::string> overlong = {
        std::string("\xC0\x80", 2),         std::string("\xC0\xAF", 2),
        std::string("\xC1\xBF", 2),         std::string("\xE0\x80\x80", 3),
        std::string("\xE0\x9F\xBF", 3),     std::string("\xF0\x80\x80\x80", 4),
        std::string("\xF0\x8F\xBF\xBF", 4)};
    for (const std::string& bytes : overlong)
        checkCsvRejected(timezoneRowWithUtf8(bytes), "UTF-8");
}

BOOST_AUTO_TEST_CASE(testRejectsUtf8Surrogate) {
    BOOST_TEST_MESSAGE("Testing rejection of a UTF-8 encoded surrogate in CSV...");
    for (const std::string& bytes : {std::string("\xED\xA0\x80", 3),
                                     std::string("\xED\xAF\xBF", 3),
                                     std::string("\xED\xB0\x80", 3),
                                     std::string("\xED\xBF\xBF", 3)})
        checkCsvRejected(timezoneRowWithUtf8(bytes), "UTF-8");
}

BOOST_AUTO_TEST_CASE(testRejectsUtf8OutsideUnicodeRange) {
    BOOST_TEST_MESSAGE("Testing rejection of UTF-8 lead bytes and scalars above U+10FFFF...");
    const std::vector<std::string> invalid = {
        std::string("\xF4\x90\x80\x80", 4), std::string("\xF5\x80\x80\x80", 4),
        std::string("\xF7\xBF\xBF\xBF", 4), std::string("\xF8\x88\x80\x80\x80", 5),
        std::string("\xFF", 1),             std::string("\x80", 1),
        std::string("\xBF", 1)};
    for (const std::string& bytes : invalid)
        checkCsvRejected(timezoneRowWithUtf8(bytes), "UTF-8");
}

BOOST_AUTO_TEST_CASE(testRejectsTruncatedUtf8) {
    BOOST_TEST_MESSAGE("Testing rejection of a truncated UTF-8 sequence in CSV...");
    // A sequence cut short by the next delimiter, and sequences cut off by the end of input.
    checkCsvRejected(timezoneRowWithUtf8(std::string("\xE2\x82", 2)), "UTF-8");
    const std::string prefix = tzHeader + "a,b,0,";
    checkCsvRejected(prefix + std::string("\xE2\x82", 2), "truncated UTF-8");
    checkCsvRejected(prefix + std::string("\xC3", 1), "truncated UTF-8");
    checkCsvRejected(prefix + std::string("\xF0\x9F\x98", 3), "truncated UTF-8");
}

BOOST_AUTO_TEST_CASE(testRejectsNulByte) {
    BOOST_TEST_MESSAGE("Testing rejection of a NUL byte in CSV...");
    checkCsvRejected(tzHeader + std::string("a,\0,c,d\n", 8), "NUL byte");
    checkCsvRejected(tzHeader + std::string("a,\"b\0c\",c,d\n", 12), "NUL byte");
    checkCsvRejected(tzHeader + std::string("a,b,c,d\0", 8), "NUL byte");
    checkCsvRejected(std::string("\0", 1) + tzHeader, "NUL byte");
}

BOOST_AUTO_TEST_CASE(testDistinguishesEmptyAndQuotedEmptyFields) {
    BOOST_TEST_MESSAGE("Testing distinction between empty and quoted-empty CSV fields...");
    const std::string input = tzHeader + ",\"\",0,\n";
    const auto table = parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_REQUIRE_EQUAL(table.records[0].fields.size(), 4U);
    BOOST_CHECK(table.records[0].fields[0].empty());
    BOOST_CHECK_EQUAL(table.records[0].fields[1], "\"\"");
    BOOST_CHECK_EQUAL(table.records[0].fields[2], "0");
    BOOST_CHECK(table.records[0].fields[3].empty());
}

BOOST_AUTO_TEST_CASE(testAcceptsFinalRecordWithoutNewline) {
    BOOST_TEST_MESSAGE("Testing acceptance of a final CSV record without a newline...");
    const auto table = parseVarianceClockCsv(tzHeader + "a,b,0,0",
                                             VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 1U);
    BOOST_CHECK_EQUAL(table.records[0].fields[3], "0");

    // A quoted final field and a trailing empty final field, both without a newline.
    const auto quoted = parseVarianceClockCsv(tzHeader + "a,b,0,\"0\"",
                                              VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(quoted.records.size(), 1U);
    BOOST_CHECK_EQUAL(quoted.records[0].fields[3], "\"0\"");
    const auto empty = parseVarianceClockCsv(tzHeader + "a,b,0,",
                                             VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(empty.records.size(), 1U);
    BOOST_REQUIRE_EQUAL(empty.records[0].fields.size(), 4U);
    BOOST_CHECK(empty.records[0].fields[3].empty());
}

BOOST_AUTO_TEST_CASE(testRejectsBlankLine) {
    BOOST_TEST_MESSAGE("Testing rejection of a blank CSV record...");
    checkCsvRejected(tzHeader + "\n", "wrong field count");
    checkCsvRejected(tzHeader + "a,b,0,0\n\na,b,0,0\n", "wrong field count");
    checkCsvRejected(tzHeader + "a,b,0,0\r\n\r\n", "wrong field count");
    checkCsvRejected("\n" + tzHeader, "wrong field count");
}

BOOST_AUTO_TEST_CASE(testRejectsBareCr) {
    BOOST_TEST_MESSAGE("Testing rejection of a bare CR in CSV...");
    checkCsvRejected(tzHeader + "a,b\r,c,d\n", "bare CR");
    checkCsvRejected(tzHeader + "a,b,c,d\r", "bare CR");
    checkCsvRejected(tzHeader + "a,b,c,d\r\r\n", "bare CR");
    checkCsvRejected("start_utc,end_utc,offset_seconds,fold\ra,b,c,d\n", "bare CR");
    checkCsvRejected(tzHeader + "a,b,c,\"x\ry\"\n", "bare CR in quoted");
    checkCsvRejected(tzHeader + "a,b,c,\"x\r\"\n", "bare CR in quoted");
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
        // The same header without its final newline, and with CRLF, is also header-only.
        const std::string trimmed(entry.second.substr(0, entry.second.size() - 1));
        BOOST_CHECK(parseVarianceClockCsv(trimmed, entry.first).records.empty());
        BOOST_CHECK(parseVarianceClockCsv(trimmed + "\r\n", entry.first).records.empty());
        // Every other schema rejects this header.
        for (const auto& other : headers)
            if (other.first != entry.first)
                BOOST_CHECK_THROW(parseVarianceClockCsv(entry.second, other.first), Error);
    }
    checkCsvRejected("", "empty");
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitRowCount) {
    BOOST_TEST_MESSAGE("Testing rejection of more than 400,000 CSV data rows...");
    std::string input = tzHeader;
    input.reserve(input.size() + 400001U * 8U);
    for (std::size_t i = 0; i < 400000; ++i)
        input += "a,b,0,0\n";
    const auto table = parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_CHECK_EQUAL(table.records.size(), 400000U);
    input += "a,b,0,0\n";
    checkCsvRejected(input, "400,000");
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitField) {
    BOOST_TEST_MESSAGE("Testing rejection of a CSV field larger than one MiB...");
    const auto accepted =
        parseVarianceClockCsv(tzHeader + std::string(oneMiB, 'x') + ",b,0,0\n",
                              VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(accepted.records.size(), 1U);
    BOOST_CHECK_EQUAL(accepted.records[0].fields[0].size(), oneMiB);
    checkCsvRejected(tzHeader + std::string(oneMiB + 1U, 'x') + ",b,0,0\n", "1 MiB");
    // The limit applies to the lexeme, so a quoted field counts its quotes.
    checkCsvRejected(tzHeader + "\"" + std::string(oneMiB - 1U, 'x') + "\",b,0,0\n", "1 MiB");
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitRecord) {
    BOOST_TEST_MESSAGE("Testing rejection of a CSV record larger than four MiB...");
    // Three one-MiB fields plus a fourth sized so the record is exactly four MiB.
    const std::size_t fourth = oneMiB - 13U;
    const auto accepted = parseVarianceClockCsv(
        slotHeader + slotRecord(oneMiB, fourth) + "\n", VarianceClockCsvSchema::SlotEvidence);
    BOOST_REQUIRE_EQUAL(accepted.records.size(), 1U);
    BOOST_CHECK_EQUAL(accepted.records[0].fields.size(), 14U);
    checkCsvRejected(slotHeader + slotRecord(oneMiB, fourth + 1U) + "\n", "record exceeds",
                     VarianceClockCsvSchema::SlotEvidence);
}

BOOST_AUTO_TEST_CASE(testRejectsOverLimitFile) {
    BOOST_TEST_MESSAGE("Testing the 32 MiB CSV file limit...");
    // Seven four-MiB records plus one that brings the whole file to exactly 32 MiB.
    const std::size_t limit = 32U * oneMiB;
    std::string input = slotHeader;
    for (std::size_t i = 0; i < 7; ++i)
        input += slotRecord(oneMiB, oneMiB - 13U) + "\n";
    const std::size_t lastRecord = limit - input.size() - 1U;
    input += slotRecord(oneMiB, lastRecord - 3U * oneMiB - 13U) + "\n";
    BOOST_REQUIRE_EQUAL(input.size(), limit);
    const auto table = parseVarianceClockCsv(input, VarianceClockCsvSchema::SlotEvidence);
    BOOST_CHECK_EQUAL(table.records.size(), 8U);
    input += '\n';
    checkCsvRejected(input, "32 MiB", VarianceClockCsvSchema::SlotEvidence);
}

BOOST_AUTO_TEST_CASE(testRejectsUnexpectedBom) {
    BOOST_TEST_MESSAGE("Testing rejection of a UTF-8 BOM before the CSV header...");
    checkCsvRejected(std::string("\xEF\xBB\xBF", 3) + tzHeader, "BOM");
    checkCsvRejected(std::string("\xEF\xBB\xBF", 3), "BOM");
}

BOOST_AUTO_TEST_CASE(testRejectsWrongHeaderOrFieldCount) {
    BOOST_TEST_MESSAGE("Testing rejection of a wrong CSV header or field count...");
    const char* header = "wrong variance-clock CSV header";
    checkCsvRejected("start_utc,end_utc,offset_seconds,other\n", header);
    checkCsvRejected("start_utc,end_utc,fold,offset_seconds\n", header);
    checkCsvRejected("START_UTC,end_utc,offset_seconds,fold\n", header);
    checkCsvRejected("start_utc,end_utc,offset_seconds\n", "wrong field count");
    checkCsvRejected("start_utc,end_utc,offset_seconds,fold,extra\n", "wrong field count");
    checkCsvRejected(tzHeader + "a,b,0\n", "wrong field count");
    checkCsvRejected(tzHeader + "a,b,0,0,0\n", "wrong field count");
    // A header of the wrong width is also caught for a different schema.
    checkCsvRejected(tzHeader, "wrong field count", VarianceClockCsvSchema::MarketDays);
}

BOOST_AUTO_TEST_CASE(testCsvScanningIgnoresGlobalNumpunct) {
    BOOST_TEST_MESSAGE("Testing CSV scanning under a comma-decimal global locale...");
    GlobalLocaleGuard localeGuard;
    const std::string input = tzHeader + "a,b,123,0\na,b,\"1,5\",0\n";
    const auto table = parseVarianceClockCsv(input, VarianceClockCsvSchema::TimezoneMapping);
    BOOST_REQUIRE_EQUAL(table.records.size(), 2U);
    BOOST_CHECK_EQUAL(table.records[0].fields[2], "123");
    BOOST_CHECK_EQUAL(table.records[1].fields[2], "\"1,5\"");
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(VarianceClockHashTests)

namespace {

    std::string byteRange(std::size_t size) {
        std::string result;
        result.reserve(size);
        for (std::size_t i = 0; i < size; ++i)
            result.push_back(static_cast<char>(i));
        return result;
    }

    std::string sha256Hex(std::string_view bytes) {
        QuantLib::detail::VarianceSha256 digest;
        digest.update(bytes);
        return digest.finishHex();
    }

}

BOOST_AUTO_TEST_CASE(testSha256EmptyVector) {
    BOOST_TEST_MESSAGE("Testing the SHA-256 empty-input NIST vector...");
    BOOST_CHECK_EQUAL(
        sha256Hex(""),
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
}

BOOST_AUTO_TEST_CASE(testSha256NistAbcVector) {
    BOOST_TEST_MESSAGE("Testing the SHA-256 abc NIST vector...");
    BOOST_CHECK_EQUAL(
        sha256Hex("abc"),
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
}

BOOST_AUTO_TEST_CASE(testSha256NistLongMessageVector) {
    BOOST_TEST_MESSAGE("Testing the SHA-256 long-message NIST vector...");
    BOOST_CHECK_EQUAL(
        sha256Hex("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"),
        "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
}

BOOST_AUTO_TEST_CASE(testSha256BlockAndPaddingBoundaries) {
    BOOST_TEST_MESSAGE("Testing SHA-256 block and first padding boundaries...");
    const std::array<std::pair<std::size_t, std::string_view>, 5> vectors{{
        {55, "463eb28e72f82e0a96c0a4cc53690c571281131f672aa229e0d45ae59b598b59"},
        {56, "da2ae4d6b36748f2a318f23e7ab1dfdf45acdc9d049bd80e59de82a60895f562"},
        {63, "29af2686fd53374a36b0846694cc342177e428d1647515f078784d69cdb9e488"},
        {64, "fdeab9acf3710362bd2658cdc9a29e8f9c757fcf9811603a8c447cd1d9151108"},
        {65, "4bfd2c8b6f1eec7a2afeb48b934ee4b2694182027e6d0fc075074f2fabb31781"}
    }};
    for (const auto& vector : vectors)
        BOOST_CHECK_EQUAL(sha256Hex(byteRange(vector.first)), vector.second);
}

BOOST_AUTO_TEST_CASE(testSha256SecondBlockPaddingBoundaries) {
    BOOST_TEST_MESSAGE("Testing SHA-256 second-block padding boundaries...");
    const std::array<std::pair<std::size_t, std::string_view>, 4> vectors{{
        {119, "da18797ed7c3a777f0847f429724a2d8cd5138e6ed2895c3fa1a6d39d18f7ec6"},
        {120, "f52b23db1fbb6ded89ef42a23ce0c8922c45f25c50b568a93bf1c075420bbb7c"},
        {127, "92ca0fa6651ee2f97b884b7246a562fa71250fedefe5ebf270d31c546bfea976"},
        {128, "471fb943aa23c511f6f72f8d1652d9c880cfa392ad80503120547703e56a2be5"}
    }};
    for (const auto& vector : vectors)
        BOOST_CHECK_EQUAL(sha256Hex(byteRange(vector.first)), vector.second);
}

BOOST_AUTO_TEST_CASE(testSha256IncrementalUpdates) {
    BOOST_TEST_MESSAGE("Testing incremental SHA-256 updates across block boundaries...");
    const std::string input = byteRange(130);
    QuantLib::detail::VarianceSha256 digest;
    digest.update(std::string_view(input).substr(0, 1));
    digest.update(std::string_view(input).substr(1, 63));
    digest.update(std::string_view(input).substr(64, 2));
    digest.update(std::string_view(input).substr(66));
    BOOST_CHECK_EQUAL(
        digest.finishHex(),
        "8d39b60b9c767c58975b270c1d6b13c9b4507e5aee7ad496a3528e4c7f880721");
}

BOOST_AUTO_TEST_CASE(testSha256MatchesPrecomputedOracle) {
    BOOST_TEST_MESSAGE("Testing SHA-256 against precomputed byte-range oracle values...");
    const std::array<std::pair<std::size_t, std::string_view>, 10> vectors{{
        {55, "463eb28e72f82e0a96c0a4cc53690c571281131f672aa229e0d45ae59b598b59"},
        {56, "da2ae4d6b36748f2a318f23e7ab1dfdf45acdc9d049bd80e59de82a60895f562"},
        {63, "29af2686fd53374a36b0846694cc342177e428d1647515f078784d69cdb9e488"},
        {64, "fdeab9acf3710362bd2658cdc9a29e8f9c757fcf9811603a8c447cd1d9151108"},
        {65, "4bfd2c8b6f1eec7a2afeb48b934ee4b2694182027e6d0fc075074f2fabb31781"},
        {119, "da18797ed7c3a777f0847f429724a2d8cd5138e6ed2895c3fa1a6d39d18f7ec6"},
        {120, "f52b23db1fbb6ded89ef42a23ce0c8922c45f25c50b568a93bf1c075420bbb7c"},
        {127, "92ca0fa6651ee2f97b884b7246a562fa71250fedefe5ebf270d31c546bfea976"},
        {128, "471fb943aa23c511f6f72f8d1652d9c880cfa392ad80503120547703e56a2be5"},
        {130, "8d39b60b9c767c58975b270c1d6b13c9b4507e5aee7ad496a3528e4c7f880721"}
    }};
    for (const auto& vector : vectors)
        BOOST_CHECK_EQUAL(sha256Hex(byteRange(vector.first)), vector.second);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
