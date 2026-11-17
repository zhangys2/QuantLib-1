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
#include <ql/time/varianceclockbundledata.hpp>
#include <ql/time/varianceclockbundlesource.hpp>
#include <ql/time/varianceclockmanifest.hpp>
#include <ql/utilities/detail/variancesha256.hpp>
#include <boost/test/unit_test.hpp>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <locale>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>
#include <vector>
#include <random>
#ifndef _WIN32
#include <sys/stat.h>
#endif

using namespace QuantLib;

namespace {

    using QuantLib::detail::VarianceClockManifest;
    using QuantLib::detail::VarianceClockCsvSchema;
    using QuantLib::detail::decodeVarianceClockCsvField;
    using QuantLib::detail::parseEvidenceIdsJson;
    using QuantLib::detail::parseVarianceClockManifest;
    using QuantLib::detail::visitVarianceClockCsvRows;

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

    void replaceAll(std::string& input, const std::string& before, const std::string& after) {
        std::size_t position = 0;
        while ((position = input.find(before, position)) != std::string::npos) {
            input.replace(position, before.size(), after);
            position += after.size();
        }
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

    bool isEvidenceIdsAccepted(const std::string& input) {
        try {
            parseEvidenceIdsJson(input);
            return true;
        } catch (const Error&) {
            return false;
        }
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
    BOOST_TEST_MESSAGE("Testing rejection of a leading UTF-8 BOM in JSON input...");
    const std::string bom("\xEF\xBB\xBF", 3);
    BOOST_CHECK_THROW(parseVarianceClockManifest(bom + minimalManifest()), Error);
    // The evidence-ID helper shares the JSON stage, so it rejects a BOM as well.
    BOOST_CHECK_THROW(parseEvidenceIdsJson(bom + "[\"a\"]"), Error);
    BOOST_CHECK_EQUAL(parseEvidenceIdsJson("[\"a\"]").size(), 1U);
}

BOOST_AUTO_TEST_CASE(testIdentifierWhitespaceCoversEveryUnicodeSpace) {
    BOOST_TEST_MESSAGE("Testing leading and trailing Unicode whitespace in identifiers...");
    // Unicode White_Space code points that are not control characters.
    const std::vector<std::string> spaces = {
        "\\u0020", "\\u00a0", "\\u1680", "\\u2000", "\\u2005", "\\u200a", "\\u2028",
        "\\u2029", "\\u202f", "\\u205f", "\\u3000"};
    // Neighbours that are not White_Space: they are ordinary identifier characters.
    const std::vector<std::string> notSpaces = {
        "\\u00a1", "\\u167f", "\\u1681", "\\u1fff", "\\u200b", "\\u2027", "\\u202e",
        "\\u205e", "\\u2060", "\\u2fff", "\\u3001"};
    for (const std::string& space : spaces) {
        for (const std::string& pattern :
             {space + "id", "id" + space, space + "id" + space}) {
            std::string manifest = minimalManifest();
            replaceOnce(manifest, "\"snapshot_id\": \"snapshot\"",
                        "\"snapshot_id\": \"" + pattern + "\"");
            BOOST_CHECK_MESSAGE(!isAccepted(manifest), "accepted " << pattern);
            BOOST_CHECK_MESSAGE(!isEvidenceIdsAccepted("[\"" + pattern + "\"]"),
                                "accepted array element " << pattern);
        }
        // Interior whitespace is permitted.
        std::string interior = minimalManifest();
        replaceOnce(interior, "\"snapshot_id\": \"snapshot\"",
                    "\"snapshot_id\": \"a" + space + "b\"");
        BOOST_CHECK_MESSAGE(isAccepted(interior), "rejected interior " << space);
    }
    for (const std::string& other : notSpaces) {
        for (const std::string& pattern : {other + "id", "id" + other}) {
            std::string manifest = minimalManifest();
            replaceOnce(manifest, "\"snapshot_id\": \"snapshot\"",
                        "\"snapshot_id\": \"" + pattern + "\"");
            BOOST_CHECK_MESSAGE(isAccepted(manifest), "rejected " << pattern);
        }
    }
}

BOOST_AUTO_TEST_CASE(testIdentifierLimitCountsUtf8Bytes) {
    BOOST_TEST_MESSAGE("Testing that the identifier limit counts UTF-8 bytes, not characters...");
    const std::string euro = "\xE2\x82\xAC";
    std::string accepted;
    for (int i = 0; i < 42; ++i)
        accepted += euro;
    accepted += "xx";
    BOOST_REQUIRE_EQUAL(accepted.size(), 128U);
    BOOST_CHECK_EQUAL(parseEvidenceIdsJson("[\"" + accepted + "\"]").size(), 1U);
    BOOST_CHECK_THROW(parseEvidenceIdsJson("[\"" + accepted + "x\"]"), Error);
    std::string rejected;
    for (int i = 0; i < 43; ++i)
        rejected += euro;
    BOOST_REQUIRE_EQUAL(rejected.size(), 129U);
    BOOST_CHECK_THROW(parseEvidenceIdsJson("[\"" + rejected + "\"]"), Error);
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

    struct CsvTestRecord {
        std::vector<std::string> fields;
    };

    struct CsvTestTable {
        std::vector<CsvTestRecord> records;
    };

    bool collectAllCsvRows(void* context,
                           const std::string_view* fields,
                           std::size_t fieldCount) {
        auto& table = *static_cast<CsvTestTable*>(context);
        CsvTestRecord record;
        record.fields.reserve(fieldCount);
        for (std::size_t i = 0; i < fieldCount; ++i)
            record.fields.emplace_back(fields[i]);
        table.records.push_back(std::move(record));
        return true;
    }

    CsvTestTable parseVarianceClockCsv(std::string_view bytes,
                                       VarianceClockCsvSchema schema) {
        CsvTestTable table;
        QL_REQUIRE(visitVarianceClockCsvRows(bytes, schema, &table, collectAllCsvRows),
                   "test CSV visitor unexpectedly stopped");
        return table;
    }

    struct CsvRowCount {
        std::size_t count = 0;
    };

    bool countCsvRows(void* context,
                      const std::string_view*,
                      std::size_t) {
        ++static_cast<CsvRowCount*>(context)->count;
        return true;
    }

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

    struct CsvRows {
        std::size_t calls = 0;
        std::vector<std::string> lastRow;
        bool continueParsing = true;
        bool checkViews = false;
        bool viewsWithinInput = true;
        const char* inputBegin = nullptr;
        const char* inputEnd = nullptr;
    };

    bool collectCsvRow(void* context,
                       const std::string_view* fields,
                       std::size_t fieldCount) {
        auto& rows = *static_cast<CsvRows*>(context);
        ++rows.calls;
        rows.lastRow.clear();
        rows.lastRow.reserve(fieldCount);
        for (std::size_t i = 0; i < fieldCount; ++i) {
            if (rows.checkViews &&
                (fields[i].data() < rows.inputBegin ||
                 fields[i].data() + fields[i].size() > rows.inputEnd))
                rows.viewsWithinInput = false;
            rows.lastRow.emplace_back(fields[i]);
        }
        return rows.continueParsing;
    }

    struct CsvStopAfter {
        std::size_t stopAt;
        std::size_t seen;
        bool fail = false;
        std::string lastFirstField;
    };

    bool stopAfterRows(void* context, const std::string_view* fields, std::size_t) {
        auto& state = *static_cast<CsvStopAfter*>(context);
        ++state.seen;
        state.lastFirstField = std::string(fields[0]);
        if (state.seen == state.stopAt) {
            if (state.fail)
                throw std::runtime_error("visitor failure");
            return false;
        }
        return true;
    }

    bool decodesSuccessfully(const std::string& lexeme) {
        try {
            decodeVarianceClockCsvField(lexeme);
            return true;
        } catch (const Error&) {
            return false;
        }
    }

}

BOOST_AUTO_TEST_CASE(testParsesQuotedCommaEscapedQuoteAndEmbeddedNewline) {
    BOOST_TEST_MESSAGE("Testing CSV quoted commas, escaped quotes, and embedded newlines...");
    const std::string input = tzHeader + "a,\"b,c\",\"d\"\"e\",\"line1\nline2\"\n";
    CsvRows rows;
    rows.checkViews = true;
    rows.inputBegin = input.data();
    rows.inputEnd = input.data() + input.size();
    BOOST_CHECK(visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping,
                                          &rows, collectCsvRow));
    BOOST_REQUIRE_EQUAL(rows.calls, 1U);
    BOOST_REQUIRE_EQUAL(rows.lastRow.size(), 4U);
    BOOST_CHECK_EQUAL(rows.lastRow[0], "a");
    BOOST_CHECK_EQUAL(rows.lastRow[1], "\"b,c\"");
    BOOST_CHECK_EQUAL(rows.lastRow[2], "\"d\"\"e\"");
    BOOST_CHECK_EQUAL(rows.lastRow[3], "\"line1\nline2\"");

    // Embedded CRLF is preserved; a field made only of one escaped quote is one lexeme.
    const std::string crlf = tzHeader + "\"x\r\ny\",\"\"\"\",0,0\n";
    CsvRows second;
    BOOST_CHECK(visitVarianceClockCsvRows(crlf, VarianceClockCsvSchema::TimezoneMapping,
                                          &second, collectCsvRow));
    BOOST_REQUIRE_EQUAL(second.calls, 1U);
    BOOST_CHECK_EQUAL(second.lastRow[0], "\"x\r\ny\"");
    BOOST_CHECK_EQUAL(second.lastRow[1], "\"\"\"\"");

    // The row's field views point into the caller's buffer during the callback.
    BOOST_CHECK(rows.viewsWithinInput);
}

BOOST_AUTO_TEST_CASE(testDecodesCsvFieldLexemes) {
    BOOST_TEST_MESSAGE("Testing CSV field decoding and escaped quote handling...");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("plain"), "plain");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"d\"\"e\""), "d\"e");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"a,b\""), "a,b");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"line1\r\nline2\""), "line1\r\nline2");
    BOOST_CHECK_THROW(decodeVarianceClockCsvField("\"unterminated"), Error);
    BOOST_CHECK_THROW(decodeVarianceClockCsvField("a\"b"), Error);
}

BOOST_AUTO_TEST_CASE(testQuotedAndUnquotedEmptyFieldsDecodeEqually) {
    BOOST_TEST_MESSAGE("Testing quoted-empty and unquoted-empty CSV semantics...");
    const std::string unquoted = decodeVarianceClockCsvField("");
    const std::string quoted = decodeVarianceClockCsvField("\"\"");
    BOOST_CHECK(unquoted.empty());
    BOOST_CHECK_EQUAL(quoted, unquoted);
}

BOOST_AUTO_TEST_CASE(testAcceptsQuotedCsvHeader) {
    BOOST_TEST_MESSAGE("Testing CSV header comparison after field decoding...");
    const std::string input =
        "\"start_utc\",end_utc,offset_seconds,fold\na,b,0,0\n";
    CsvRows rows;
    BOOST_CHECK(visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping,
                                          &rows, collectCsvRow));
    BOOST_REQUIRE_EQUAL(rows.calls, 1U);
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField(rows.lastRow[0]), "a");
}

BOOST_AUTO_TEST_CASE(testCsvRowVisitorCanStopBeforeLaterRows) {
    BOOST_TEST_MESSAGE("Testing early stop of streaming CSV row visitation...");
    const std::string input = tzHeader + "a,b,0,0\nwrong-width\n";
    CsvRows rows;
    rows.continueParsing = false;
    BOOST_CHECK(!visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping,
                                           &rows, collectCsvRow));
    BOOST_CHECK_EQUAL(rows.calls, 1U);
}

BOOST_AUTO_TEST_CASE(testRejectsLeadingBomAndAllowsEmbeddedUfeff) {
    BOOST_TEST_MESSAGE("Testing leading-only CSV BOM rejection and embedded U+FEFF...");
    checkCsvRejected(std::string("\xEF\xBB\xBF", 3) + tzHeader, "BOM");

    const std::string embedded = std::string("\xEF\xBB\xBF", 3);
    CsvRows rows;
    BOOST_CHECK(visitVarianceClockCsvRows(timezoneRowWithUtf8(embedded),
                                          VarianceClockCsvSchema::TimezoneMapping,
                                          &rows, collectCsvRow));
    BOOST_REQUIRE_EQUAL(rows.calls, 1U);
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField(rows.lastRow[1]), embedded);
}

BOOST_AUTO_TEST_CASE(testRejectsMismatchedQuotedHeaders) {
    BOOST_TEST_MESSAGE("Testing rejection of quoted CSV headers that decode differently...");
    const char* wrongHeader = "wrong variance-clock CSV header";
    const std::vector<std::string> rejected = {
        "\"start_ut\",end_utc,offset_seconds,fold\n",
        "\"start_utcx\",end_utc,offset_seconds,fold\n",
        "\"START_UTC\",end_utc,offset_seconds,fold\n",
        "\"start\"\"utc\",end_utc,offset_seconds,fold\n",
        "\"\",end_utc,offset_seconds,fold\n",
        "start_utc,end_utc,offset_seconds,\"fold \"\n",
        "start_utc,end_utc,\"offset_secondS\",fold\n"};
    for (const std::string& header : rejected)
        checkCsvRejected(header, wrongHeader);

    // Every header field may be quoted when it decodes to the frozen name.
    CsvRows rows;
    BOOST_CHECK(visitVarianceClockCsvRows(
        "\"start_utc\",\"end_utc\",\"offset_seconds\",\"fold\"\n",
        VarianceClockCsvSchema::TimezoneMapping, &rows, collectCsvRow));
    BOOST_CHECK_EQUAL(rows.calls, 0U);
}

BOOST_AUTO_TEST_CASE(testDecodesCsvFieldEdgeCases) {
    BOOST_TEST_MESSAGE("Testing CSV field decoding of quotes, whitespace and UTF-8...");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"\"\"\""), "\"");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"\"\"a\"\"\""), "\"a\"");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"a\"\"\"\"b\""), "a\"\"b");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"line1\nline2\""), "line1\nline2");
    // Nothing is trimmed or normalised, and U+FEFF is ordinary data.
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField(" a "), " a ");
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\" a \""), " a ");
    const std::string euro = "\xE2\x82\xAC";
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField(euro), euro);
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"" + euro + "\""), euro);
    const std::string feff = "\xEF\xBB\xBF";
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField(feff + "id"), feff + "id");
    // A JSON array cell as it is stored in slot_evidence.csv.
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField("\"[\"\"a\"\",\"\"b\"\"]\""), "[\"a\",\"b\"]");
    // The field size limit counts the lexeme.
    BOOST_CHECK_EQUAL(decodeVarianceClockCsvField(std::string(oneMiB, 'x')).size(), oneMiB);
    BOOST_CHECK_THROW(decodeVarianceClockCsvField(std::string(oneMiB + 1U, 'x')), Error);
    BOOST_CHECK_THROW(decodeVarianceClockCsvField("\"" + std::string(oneMiB - 1U, 'x') + "\""),
                      Error);
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidCsvFieldLexemes) {
    BOOST_TEST_MESSAGE("Testing that the CSV field decoder rejects non-field lexemes...");
    const std::vector<std::string> invalid = {
        "a,b",          "a\nb",          "a\r\nb",   "a\rb",      "a\"b",  "\"a\"b",
        "\"a\" ",       "\"",            "\"a",      "\"a\"\"",   "\"a\"\"\"b", "\"\"\"",
        std::string("a\0b", 3), std::string("\xC0\x80", 2), std::string("\xE2\x82", 2),
        std::string("\"\xED\xA0\x80\"", 5)};
    for (const std::string& lexeme : invalid)
        BOOST_CHECK_MESSAGE(!decodesSuccessfully(lexeme), "decoded invalid lexeme");
}

BOOST_AUTO_TEST_CASE(testCsvRowVisitorContract) {
    BOOST_TEST_MESSAGE("Testing the CSV row visitor contract...");
    BOOST_CHECK_THROW(visitVarianceClockCsvRows(tzHeader, VarianceClockCsvSchema::TimezoneMapping,
                                                nullptr, nullptr),
                      Error);

    // Header-only input visits no rows and reports completion.
    CsvRows none;
    BOOST_CHECK(visitVarianceClockCsvRows(tzHeader, VarianceClockCsvSchema::TimezoneMapping,
                                          &none, collectCsvRow));
    BOOST_CHECK_EQUAL(none.calls, 0U);

    // Rows arrive in file order; stopping on the second row reports false.
    const std::string input = tzHeader + "a,b,0,0\nc,d,1,0\ne,f,2,0\n";
    CsvStopAfter stop{2, 0};
    BOOST_CHECK(!visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping, &stop,
                                           stopAfterRows));
    BOOST_CHECK_EQUAL(stop.seen, 2U);
    BOOST_CHECK_EQUAL(stop.lastFirstField, "c");

    // An exception from the visitor propagates and ends the scan.
    CsvStopAfter thrower{2, 0};
    thrower.fail = true;
    BOOST_CHECK_THROW(visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping,
                                                &thrower, stopAfterRows),
                      std::runtime_error);
    BOOST_CHECK_EQUAL(thrower.seen, 2U);
}

BOOST_AUTO_TEST_CASE(testRejectsRecordsWithTooManyFields) {
    BOOST_TEST_MESSAGE("Testing CSV records and headers with far more fields than expected...");
    // The visitor's field array is fixed-size; a hostile record must be rejected on count
    // before it can overrun it (run under ASAN/UBSAN to see the overrun, if any).
    for (std::size_t count : {5U, 9U, 15U, 20U, 1000U}) {
        std::string row;
        for (std::size_t i = 0; i < count; ++i)
            row += (i == 0 ? "x" : ",x");
        checkCsvRejected(tzHeader + row + "\n", "wrong field count");
        checkCsvRejected(row + "\n", "wrong field count");
        checkCsvRejected(slotHeader + row + "\n", "wrong field count",
                         VarianceClockCsvSchema::SlotEvidence);
    }
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
    CsvRowCount count;
    BOOST_CHECK(visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping,
                                          &count, countCsvRows));
    BOOST_CHECK_EQUAL(count.count, 400000U);
    input += "a,b,0,0\n";
    try {
        count = {};
        visitVarianceClockCsvRows(input, VarianceClockCsvSchema::TimezoneMapping,
                                  &count, countCsvRows);
        BOOST_FAIL("accepted over-limit CSV row count");
    } catch (const Error& e) {
        BOOST_CHECK_MESSAGE(std::string(e.what()).find("400,000") != std::string::npos,
                            "expected row-limit error but got: " << e.what());
    }
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

BOOST_AUTO_TEST_SUITE(VarianceClockBundleSourceTests)

namespace {

    using QuantLib::detail::VarianceClockBundleSource;
    using QuantLib::detail::VarianceClockCapturedBundle;
    using QuantLib::detail::VarianceClockDirectorySource;
    using QuantLib::detail::VarianceClockLoadBudget;
    using QuantLib::detail::captureVarianceClockBundle;
    using QuantLib::detail::isVarianceClockBundleFileName;

    const std::array<std::string, 5> bundleCsvNames{{
        "profiles.csv", "market_days.csv", "session_segments.csv", "timezone_mapping.csv",
        "slot_evidence.csv"}};

    std::string bundleDigest(std::string_view bytes) {
        QuantLib::detail::VarianceSha256 hash;
        hash.update(bytes);
        return hash.finishHex();
    }

    std::vector<unsigned char> byteVector(std::string_view bytes) {
        return std::vector<unsigned char>(bytes.begin(), bytes.end());
    }

    struct FakeBundleSource : VarianceClockBundleSource {
        std::map<std::string, std::vector<unsigned char>> files;
        mutable std::vector<std::string> readOrder;
        mutable std::map<std::string, std::size_t> requestedLimits;
        std::string maliciousName;
        std::vector<unsigned char> maliciousBytes;

        std::vector<unsigned char> read(const std::string& flatName,
                                        std::size_t maxBytes) const override {
            readOrder.push_back(flatName);
            requestedLimits.emplace(flatName, maxBytes);
            if (flatName == maliciousName)
                return maliciousBytes;
            const auto file = files.find(flatName);
            QL_REQUIRE(file != files.end(), "missing fake bundle file");
            return file->second;
        }
    };

    FakeBundleSource validFakeBundle() {
        FakeBundleSource source;
        const std::array<std::string, 5> csvContents{{
            "profiles bytes\n", "market days bytes\n", "session bytes\n", "timezone bytes\n",
            "slot evidence bytes\n"}};
        std::string manifest = minimalManifest();
        for (std::size_t i = 0; i < bundleCsvNames.size(); ++i) {
            const std::string before = "\"" + bundleCsvNames[i] + "\": \"" +
                                       std::string(64, '0') + "\"";
            const std::string after =
                "\"" + bundleCsvNames[i] + "\": \"" + bundleDigest(csvContents[i]) + "\"";
            replaceOnce(manifest, before, after);
            source.files.emplace(bundleCsvNames[i], byteVector(csvContents[i]));
        }
        source.files.emplace("manifest.json", byteVector(manifest));
        return source;
    }

    struct TemporaryDirectory {
        std::filesystem::path path;

        TemporaryDirectory() {
            // The system temporary directory (TMPDIR on POSIX, TMP/TEMP on Windows).
            std::random_device device;
            for (int attempt = 0; attempt < 100; ++attempt) {
                path = std::filesystem::temp_directory_path() /
                       ("quantlib-variance-clock-" + std::to_string(device()) + "-" +
                        std::to_string(device()));
                std::error_code error;
                if (std::filesystem::create_directory(path, error) && !error)
                    return;
            }
            BOOST_FAIL("cannot create a temporary test directory");
        }

        ~TemporaryDirectory() {
            std::error_code error;
            std::filesystem::remove_all(path, error);
        }
    };

    const std::array<std::string, 6> allBundleNames{{
        "manifest.json", "profiles.csv", "market_days.csv", "session_segments.csv",
        "timezone_mapping.csv", "slot_evidence.csv"}};

}

BOOST_AUTO_TEST_CASE(testSourceReadLimitIsRecheckedByLoader) {
    BOOST_TEST_MESSAGE("Testing that the loader rejects source bytes above maxBytes...");
    auto source = validFakeBundle();
    source.maliciousName = "manifest.json";
    source.maliciousBytes.resize(4U * 1024U * 1024U + 1U);
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
    BOOST_CHECK_EQUAL(source.readOrder.size(), 1U);
    BOOST_CHECK_EQUAL(source.requestedLimits.at("manifest.json"), 4U * 1024U * 1024U);
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testCapturesCsvBytesInManifestOrder) {
    BOOST_TEST_MESSAGE("Testing one-time manifest-ordered capture and digest verification...");
    auto source = validFakeBundle();
    VarianceClockLoadBudget budget;
    {
        const auto captured = captureVarianceClockBundle(source, budget);
        const std::vector<std::string> expected{
            "manifest.json", "profiles.csv", "market_days.csv", "session_segments.csv",
            "timezone_mapping.csv", "slot_evidence.csv"};
        const auto csv = captured.csvBytes();
        BOOST_CHECK_EQUAL_COLLECTIONS(source.readOrder.begin(), source.readOrder.end(),
                                      expected.begin(), expected.end());
        BOOST_CHECK_EQUAL(csv.profiles, "profiles bytes\n");
        BOOST_CHECK_EQUAL(csv.slotEvidence, "slot evidence bytes\n");
        BOOST_CHECK_GT(budget.used(), 0U);
    }
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testRejectsDigestMismatch) {
    BOOST_TEST_MESSAGE("Testing rejection of a captured CSV with a digest mismatch...");
    auto source = validFakeBundle();
    source.files.at("profiles.csv").push_back('x');
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingBundleFile) {
    BOOST_TEST_MESSAGE("Testing rejection of a missing required bundle file...");
    auto source = validFakeBundle();
    source.files.erase("profiles.csv");
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testRejectsBundleSizeLimit) {
    BOOST_TEST_MESSAGE("Testing rejection of a source response above the CSV size limit...");
    auto source = validFakeBundle();
    source.maliciousName = "profiles.csv";
    source.maliciousBytes.resize(32U * 1024U * 1024U + 1U);
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testRejectsTraversalAndAbsolutePaths) {
    BOOST_TEST_MESSAGE("Testing rejection of path components in bundle input names...");
    const std::array<std::string, 7> invalid{{
        "../manifest.json", "./manifest.json", "dir/profiles.csv", "/etc/passwd",
        "manifest.json/..", "profiles.csv/extra", ""}};
    for (const auto& name : invalid)
        BOOST_CHECK(!isVarianceClockBundleFileName(name));
}

BOOST_AUTO_TEST_CASE(testRejectsWindowsPathAliases) {
    BOOST_TEST_MESSAGE("Testing portable rejection of Windows path aliases...");
    const std::array<std::string, 12> invalid{{
        R"(C:\x)", R"(C:x)", R"(\\server\share)", R"(\\?\C:\x)", R"(\\.\device)",
        R"(profiles.csv\)", R"(profiles.csv.)", R"(profiles.csv )", "Profiles.csv",
        "profiles.CSV", "profiles.csv//", R"(profiles.csv\.)"}};
    for (const auto& name : invalid)
        BOOST_CHECK(!isVarianceClockBundleFileName(name));
}

BOOST_AUTO_TEST_CASE(testRejectsOneByteChangeInProfilesCsv) {
    BOOST_TEST_MESSAGE("Testing digest mismatch after one changed profiles.csv byte...");
    auto source = validFakeBundle();
    source.files.at("profiles.csv")[0] ^= 1U;
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsOneByteChangeInMarketDaysCsv) {
    BOOST_TEST_MESSAGE("Testing digest mismatch after one changed market_days.csv byte...");
    auto source = validFakeBundle();
    source.files.at("market_days.csv")[0] ^= 1U;
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsOneByteChangeInSessionSegmentsCsv) {
    BOOST_TEST_MESSAGE("Testing digest mismatch after one changed session_segments.csv byte...");
    auto source = validFakeBundle();
    source.files.at("session_segments.csv")[0] ^= 1U;
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsOneByteChangeInTimezoneMappingCsv) {
    BOOST_TEST_MESSAGE("Testing digest mismatch after one changed timezone_mapping.csv byte...");
    auto source = validFakeBundle();
    source.files.at("timezone_mapping.csv")[0] ^= 1U;
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsOneByteChangeInSlotEvidenceCsv) {
    BOOST_TEST_MESSAGE("Testing digest mismatch after one changed slot_evidence.csv byte...");
    auto source = validFakeBundle();
    source.files.at("slot_evidence.csv")[0] ^= 1U;
    VarianceClockLoadBudget budget;
    BOOST_CHECK_THROW(captureVarianceClockBundle(source, budget), Error);
}

BOOST_AUTO_TEST_CASE(testDirectoryRejectsSymlinkedRoot) {
    BOOST_TEST_MESSAGE("Testing rejection of a bundle root symlink...");
    TemporaryDirectory temporary;
    const auto target = temporary.path / "target";
    std::filesystem::create_directory(target);
    const auto link = temporary.path / "root-link";
    std::error_code error;
    std::filesystem::create_directory_symlink(target, link, error);
    if (error) {
        BOOST_TEST_MESSAGE("Skipping root-symlink filesystem check because symlink creation "
                           "is unavailable: " << error.message());
        return;
    }
    BOOST_CHECK_THROW(VarianceClockDirectorySource(link.string()), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsExtraDirectoryEntries) {
    BOOST_TEST_MESSAGE("Testing rejection of unrecognized bundle-root entries...");
    TemporaryDirectory temporary;
    std::ofstream extra(temporary.path / "README");
    extra << "unexpected";
    extra.close();
    BOOST_CHECK_THROW(VarianceClockDirectorySource(temporary.path.string()), Error);
}

BOOST_AUTO_TEST_CASE(testDirectoryReadsBinaryBytesFromOpenedFile) {
    BOOST_TEST_MESSAGE("Testing binary reads from the checked input handle...");
    TemporaryDirectory temporary;
    const std::string payload("line1\r\nline2\0tail", 17);
    std::ofstream file(temporary.path / "profiles.csv", std::ios::binary);
    file.write(payload.data(), static_cast<std::streamsize>(payload.size()));
    file.close();
    VarianceClockDirectorySource source(temporary.path.string());
    const auto bytes = source.read("profiles.csv", 32);
    BOOST_CHECK_EQUAL(bytes.size(), payload.size());
    BOOST_CHECK_EQUAL_COLLECTIONS(bytes.begin(), bytes.end(), payload.begin(), payload.end());
}

BOOST_AUTO_TEST_CASE(testDirectoryChecksFileSizeBeforeAllocation) {
    BOOST_TEST_MESSAGE("Testing opened-handle size rejection before bounded input reads...");
    TemporaryDirectory temporary;
    std::ofstream file(temporary.path / "profiles.csv", std::ios::binary);
    file << "larger than limit";
    file.close();
    VarianceClockDirectorySource source(temporary.path.string());
    BOOST_CHECK_THROW(source.read("profiles.csv", 4), Error);
}

BOOST_AUTO_TEST_CASE(testRejectsSymlinkedInputs) {
    BOOST_TEST_MESSAGE("Testing rejection of a symlinked bundle input...");
    TemporaryDirectory temporary;
    const auto target = std::filesystem::path(temporary.path.string() + "-target.csv");
    std::ofstream file(target);
    file << "bytes";
    file.close();
    std::error_code error;
    std::filesystem::create_symlink(target, temporary.path / "profiles.csv", error);
    if (error) {
        BOOST_TEST_MESSAGE("Skipping input-symlink filesystem check because symlink creation "
                           "is unavailable: " << error.message());
        std::filesystem::remove(target);
        return;
    }
    VarianceClockDirectorySource source(temporary.path.string());
    BOOST_CHECK_THROW(source.read("profiles.csv", 32), Error);
    std::filesystem::remove(target);
}

namespace {

    // Records the budget level at each read so the test can see what was reserved
    // before the source was asked for bytes.
    struct ObservingBundleSource : FakeBundleSource {
        const VarianceClockLoadBudget* budget = nullptr;
        mutable std::vector<std::size_t> usedAtRead;
        std::size_t extraCapacity = 0;

        std::vector<unsigned char> read(const std::string& flatName,
                                        std::size_t maxBytes) const override {
            usedAtRead.push_back(budget->used());
            auto bytes = FakeBundleSource::read(flatName, maxBytes);
            if (extraCapacity != 0)
                bytes.reserve(bytes.size() + extraCapacity);
            return bytes;
        }
    };

    void checkCaptureRejectedWith(const VarianceClockBundleSource& source,
                                  const char* expected,
                                  std::size_t budgetLimit = VarianceClockLoadBudget::defaultLimit) {
        VarianceClockLoadBudget budget(budgetLimit);
        try {
            captureVarianceClockBundle(source, budget);
            BOOST_ERROR("captured bundle; expected a rejection mentioning: " << expected);
        } catch (const Error& e) {
            BOOST_CHECK_MESSAGE(std::string(e.what()).find(expected) != std::string::npos,
                                "expected \"" << expected << "\" but got: " << e.what());
        }
        BOOST_CHECK_EQUAL(budget.used(), 0U);
    }

    // Writes the six files of a valid fake bundle into a directory.
    void writeBundleFiles(const std::filesystem::path& directory,
                          const FakeBundleSource& source) {
        for (const auto& file : source.files) {
            std::ofstream out(directory / file.first, std::ios::binary);
            out.write(reinterpret_cast<const char*>(file.second.data()),
                      static_cast<std::streamsize>(file.second.size()));
        }
    }

}

BOOST_AUTO_TEST_CASE(testCaptureReservesTheCeilingBeforeEachRead) {
    BOOST_TEST_MESSAGE("Testing that capture reserves each read ceiling before reading...");
    ObservingBundleSource source;
    source.files = validFakeBundle().files;
    VarianceClockLoadBudget budget;
    source.budget = &budget;
    const auto captured = captureVarianceClockBundle(source, budget);
    BOOST_REQUIRE_EQUAL(source.usedAtRead.size(), 6U);
    // The manifest ceiling is reserved first and released after parsing; each CSV ceiling is
    // reserved on top of the capacity retained for the CSVs before it.
    std::size_t retained = 0;
    BOOST_CHECK_EQUAL(source.usedAtRead[0], 4U * 1024U * 1024U);
    for (std::size_t i = 0; i < bundleCsvNames.size(); ++i) {
        BOOST_CHECK_EQUAL(source.usedAtRead[i + 1],
                          retained + source.requestedLimits.at(bundleCsvNames[i]));
        BOOST_CHECK_EQUAL(source.requestedLimits.at(bundleCsvNames[i]), 32U * 1024U * 1024U);
        retained += source.files.at(bundleCsvNames[i]).size();
    }
    BOOST_CHECK_EQUAL(budget.used(), retained);
}

BOOST_AUTO_TEST_CASE(testCaptureMapsEveryFileToItsTable) {
    BOOST_TEST_MESSAGE("Testing that each captured CSV lands in its own table...");
    auto source = validFakeBundle();
    VarianceClockLoadBudget budget;
    const auto captured = captureVarianceClockBundle(source, budget);
    const auto csv = captured.csvBytes();
    BOOST_CHECK_EQUAL(csv.profiles, "profiles bytes\n");
    BOOST_CHECK_EQUAL(csv.marketDays, "market days bytes\n");
    BOOST_CHECK_EQUAL(csv.sessionSegments, "session bytes\n");
    BOOST_CHECK_EQUAL(csv.timezoneMapping, "timezone bytes\n");
    BOOST_CHECK_EQUAL(csv.slotEvidence, "slot evidence bytes\n");
    BOOST_CHECK_EQUAL(captured.manifest().snapshotId, "snapshot");
    // Each file is read exactly once.
    BOOST_CHECK_EQUAL(source.readOrder.size(), 6U);
    BOOST_CHECK(source.requestedLimits.at("manifest.json") == 4U * 1024U * 1024U);
}

BOOST_AUTO_TEST_CASE(testCaptureChargesReturnedCapacity) {
    BOOST_TEST_MESSAGE("Testing that capture charges the capacity a source returns...");
    ObservingBundleSource source;
    source.files = validFakeBundle().files;
    source.extraCapacity = 4096;
    VarianceClockLoadBudget budget;
    source.budget = &budget;
    {
        const auto captured = captureVarianceClockBundle(source, budget);
        // Five retained buffers, each with at least the extra capacity it was returned with.
        BOOST_CHECK_GE(budget.used(), 5U * 4096U);
    }
    BOOST_CHECK_EQUAL(budget.used(), 0U);

    // A source whose capacity alone exceeds the budget is refused even though its size fits.
    ObservingBundleSource fat;
    fat.files = validFakeBundle().files;
    fat.extraCapacity = 64U * 1024U;
    VarianceClockLoadBudget small(32U * 1024U);
    fat.budget = &small;
    BOOST_CHECK_THROW(captureVarianceClockBundle(fat, small), Error);
    BOOST_CHECK_EQUAL(small.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testCaptureCeilingsFollowTheRemainingBudget) {
    BOOST_TEST_MESSAGE("Testing that read ceilings shrink with the remaining load budget...");
    auto source = validFakeBundle();
    const std::size_t limit = 10000;
    VarianceClockLoadBudget budget(limit);
    const auto captured = captureVarianceClockBundle(source, budget);
    BOOST_CHECK_EQUAL(source.requestedLimits.at("manifest.json"), limit);
    std::size_t retained = 0;
    for (const auto& name : bundleCsvNames) {
        BOOST_CHECK_EQUAL(source.requestedLimits.at(name), limit - retained);
        retained += source.files.at(name).size();
    }

    // An exhausted budget is refused before the source is touched; a ceiling smaller than the
    // manifest is refused by the over-return check.
    auto untouched = validFakeBundle();
    checkCaptureRejectedWith(untouched, "exhausted", 0);
    BOOST_CHECK(untouched.readOrder.empty());
    auto tooSmall = validFakeBundle();
    checkCaptureRejectedWith(tooSmall, "more bytes than requested", 100);
}

BOOST_AUTO_TEST_CASE(testCaptureShrinksTheCeilingToTheAggregateLimit) {
    BOOST_TEST_MESSAGE("Testing the 128 MiB aggregate input limit across captured files...");
    constexpr std::size_t file = 32U * 1024U * 1024U;
    struct BigSource : FakeBundleSource {
        std::size_t size = 0;
        mutable std::vector<std::size_t> limits;
        std::vector<unsigned char> read(const std::string& name,
                                        std::size_t maxBytes) const override {
            limits.push_back(maxBytes);
            if (name == "manifest.json")
                return files.at(name);
            // Three files of exactly 32 MiB, then one byte more than the ceiling allows.
            return std::vector<unsigned char>(
                limits.size() <= 4 ? size : maxBytes + 1, static_cast<unsigned char>('x'));
        }
    };
    BigSource source;
    source.size = file;
    // The manifest needs the digest of 32 MiB of 'x' for the first three files.
    std::string manifest = minimalManifest();
    const std::string digest = bundleDigest(std::string(file, 'x'));
    for (std::size_t i = 0; i < 3; ++i)
        replaceOnce(manifest, "\"" + bundleCsvNames[i] + "\": \"" + std::string(64, '0') + "\"",
                    "\"" + bundleCsvNames[i] + "\": \"" + digest + "\"");
    source.files.emplace("manifest.json", byteVector(manifest));
    VarianceClockLoadBudget budget;
    try {
        captureVarianceClockBundle(source, budget);
        BOOST_ERROR("captured a bundle larger than the aggregate limit");
    } catch (const Error& e) {
        BOOST_CHECK(std::string(e.what()).find("more bytes than requested") !=
                    std::string::npos);
    }
    BOOST_REQUIRE_EQUAL(source.limits.size(), 5U);
    BOOST_CHECK_EQUAL(source.limits[0], 4U * 1024U * 1024U);
    for (std::size_t i = 1; i <= 3; ++i)
        BOOST_CHECK_EQUAL(source.limits[i], file);
    // The fourth CSV may use what is left of 128 MiB after the manifest and three files.
    BOOST_CHECK_EQUAL(source.limits[4], 128U * 1024U * 1024U - 3U * file - manifest.size());
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testRejectsDigestMismatchByFileName) {
    BOOST_TEST_MESSAGE("Testing that a digest mismatch names the offending CSV...");
    for (const auto& name : bundleCsvNames) {
        auto source = validFakeBundle();
        source.files.at(name).front() ^= 1U;
        checkCaptureRejectedWith(source, ("digest mismatch for " + name).c_str());
    }
}

BOOST_AUTO_TEST_CASE(testBundleFileNamesAreExact) {
    BOOST_TEST_MESSAGE("Testing that only the six exact bundle file names are accepted...");
    for (const auto& name : allBundleNames)
        BOOST_CHECK(isVarianceClockBundleFileName(name));
    std::vector<std::string> invalid = {
        "manifest.jsonx", "xmanifest.json", "manifest.json.bak", "Manifest.json",
        "profiles.csvx", "xprofiles.csv", "profile.csv", "slot_evidence.csv.tmp",
        "profiles.csv::$DATA", "profiles.csv:stream", "PROFILES~1.CSV", "CON", "NUL",
        "profiles.csv\\..\\manifest.json", ".", "..", " ", "\n"};
    invalid.emplace_back(std::string("profiles.csv\0x", 14));
    invalid.emplace_back(std::string("manifest.json\0", 14));
    for (const auto& name : invalid)
        BOOST_CHECK_MESSAGE(!isVarianceClockBundleFileName(name), "accepted: " << name);
}

BOOST_AUTO_TEST_CASE(testDirectorySourceRejectsNonBundleNamesBeforeOpening) {
    BOOST_TEST_MESSAGE("Testing that the directory source validates names before any open...");
    TemporaryDirectory temporary;
    VarianceClockDirectorySource source(temporary.path.string());
    std::vector<std::string> names = {"../manifest.json", "/etc/passwd", "C:x", R"(C:\x)",
                                      R"(\\server\share)", "profiles.csv::$DATA", "PROFILES.CSV",
                                      "manifest.json/..", ""};
    names.emplace_back(std::string("profiles.csv\0x", 14));
    for (const auto& name : names) {
        try {
            source.read(name, 100);
            BOOST_ERROR("read accepted the name: " << name);
        } catch (const Error& e) {
            BOOST_CHECK_MESSAGE(
                std::string(e.what()).find("invalid variance-clock bundle input name") !=
                    std::string::npos,
                "wrong rejection for \"" << name << "\": " << e.what());
        }
    }
    // A valid name that is simply absent is rejected by the open, not by the name check.
    BOOST_CHECK_THROW(source.read("profiles.csv", 100), Error);
}

BOOST_AUTO_TEST_CASE(testDirectorySourceCapturesAValidBundle) {
    BOOST_TEST_MESSAGE("Testing end-to-end capture from a real directory...");
    TemporaryDirectory temporary;
    const auto fake = validFakeBundle();
    writeBundleFiles(temporary.path, fake);
    VarianceClockDirectorySource source(temporary.path.string());
    VarianceClockLoadBudget budget;
    {
        const auto captured = captureVarianceClockBundle(source, budget);
        BOOST_CHECK_EQUAL(captured.csvBytes().marketDays, "market days bytes\n");
        BOOST_CHECK_EQUAL(captured.manifest().snapshotId, "snapshot");
    }
    BOOST_CHECK_EQUAL(budget.used(), 0U);

    // A trailing separator on the root is accepted for a real directory.
    VarianceClockDirectorySource slash(temporary.path.string() + "/");
    BOOST_CHECK_NO_THROW(captureVarianceClockBundle(slash, budget));

    // One changed byte on disk is a digest mismatch.
    {
        std::fstream file(temporary.path / "timezone_mapping.csv",
                          std::ios::binary | std::ios::in | std::ios::out);
        file.put('X');
    }
    VarianceClockDirectorySource changed(temporary.path.string());
    BOOST_CHECK_THROW(captureVarianceClockBundle(changed, budget), Error);
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testDirectoryRejectsEveryUnrecognizedRootEntry) {
    BOOST_TEST_MESSAGE("Testing rejection of extra entries of every kind in the bundle root...");
    for (const char* extra :
         {"README", "profiles.csv.bak", "manifest.json.bak", ".hidden", "sub"}) {
        TemporaryDirectory temporary;
        writeBundleFiles(temporary.path, validFakeBundle());
        if (std::string(extra) == "sub")
            std::filesystem::create_directory(temporary.path / extra);
        else
            std::ofstream(temporary.path / extra) << "x";
        const auto rejectedAsUnrecognized = [&temporary]() -> bool {
            try {
                VarianceClockDirectorySource source(temporary.path.string());
                return false;
            } catch (const Error& e) {
                return std::string(e.what()).find("unrecognized") != std::string::npos;
            }
        };
        BOOST_CHECK_MESSAGE(rejectedAsUnrecognized(), "extra entry not rejected: " << extra);
    }
}

BOOST_AUTO_TEST_CASE(testDirectoryRejectsUnusableRoots) {
    BOOST_TEST_MESSAGE("Testing rejection of roots that are not real directories...");
    TemporaryDirectory temporary;
    BOOST_CHECK_THROW(VarianceClockDirectorySource(""), Error);
    BOOST_CHECK_THROW(VarianceClockDirectorySource((temporary.path / "missing").string()),
                      Error);
    // An embedded NUL would silently truncate the path handed to the operating system.
    BOOST_CHECK_THROW(VarianceClockDirectorySource(temporary.path.string() + std::string("\0x", 2)),
                      Error);
    const auto regular = temporary.path / "regular-file";
    std::ofstream(regular) << "x";
    BOOST_CHECK_THROW(VarianceClockDirectorySource(regular.string()), Error);

    // A symlink to a directory is rejected, also when written with a trailing separator.
    const auto target = temporary.path / "target";
    std::filesystem::create_directory(target);
    const auto link = temporary.path / "root-link";
    std::error_code error;
    std::filesystem::create_directory_symlink(target, link, error);
    if (error) {
        BOOST_TEST_MESSAGE("Skipping symlink-root variants: " << error.message());
        return;
    }
    BOOST_CHECK_THROW(VarianceClockDirectorySource(link.string()), Error);
    BOOST_CHECK_THROW(VarianceClockDirectorySource(link.string() + "/"), Error);
}

BOOST_AUTO_TEST_CASE(testDirectoryRejectsDotComponentsInRootPath) {
    BOOST_TEST_MESSAGE("Testing rejection of dot and dot-dot root path components...");
    TemporaryDirectory temporary;
    const std::string root = temporary.path.string();
    const std::string leaf = temporary.path.filename().string();
    const auto checkRejected = [](const std::string& path) {
        try {
            VarianceClockDirectorySource source(path);
            BOOST_ERROR("accepted root path containing a dot component: " << path);
        } catch (const Error& e) {
            BOOST_CHECK_MESSAGE(std::string(e.what()).find("dot component") != std::string::npos,
                                "wrong rejection for \"" << path << "\": " << e.what());
        }
    };
    for (const auto& path : {root + "/.", root + "/./", root + "//.",
                             root + "/../" + leaf})
        checkRejected(path);
#if defined(_WIN32)
    for (const auto& path : {root + "\\.", root + "\\.\\", root + "\\\\.",
                             root + "\\..\\" + leaf})
        checkRejected(path);
#endif

    const auto recognizedChild = temporary.path / "profiles.csv";
    std::filesystem::create_directory(recognizedChild);
    checkRejected(recognizedChild.string() + "/..");
#if defined(_WIN32)
    checkRejected(recognizedChild.string() + "\\..");
#endif

    const auto target = temporary.path / "target";
    std::filesystem::create_directory(target);
    const auto link = temporary.path / "root-link";
    std::error_code error;
    std::filesystem::create_directory_symlink(target, link, error);
    if (error) {
        BOOST_TEST_MESSAGE("Skipping symlink path variants: " << error.message());
        return;
    }
    const std::string symlink = link.string();
    for (const auto& path : {symlink + "/.", symlink + "/./", symlink + "//.",
                             symlink + "/../target"})
        checkRejected(path);
}

BOOST_AUTO_TEST_CASE(testDirectoryRejectsNonRegularAndOversizedInputs) {
    BOOST_TEST_MESSAGE("Testing rejection of directories and FIFOs named like inputs...");
    TemporaryDirectory temporary;
    std::filesystem::create_directory(temporary.path / "profiles.csv");
#ifndef _WIN32
    BOOST_REQUIRE_EQUAL(::mkfifo((temporary.path / "market_days.csv").c_str(), 0600), 0);
#endif
    {
        std::ofstream exact(temporary.path / "slot_evidence.csv", std::ios::binary);
        exact << "0123456789";
    }
    VarianceClockDirectorySource source(temporary.path.string());
    BOOST_CHECK_THROW(source.read("profiles.csv", 100), Error);
#ifndef _WIN32
    // Must be refused without blocking on the FIFO.
    BOOST_CHECK_THROW(source.read("market_days.csv", 100), Error);
#endif
    // The size ceiling is inclusive.
    BOOST_CHECK_EQUAL(source.read("slot_evidence.csv", 10).size(), 10U);
    BOOST_CHECK_THROW(source.read("slot_evidence.csv", 9), Error);
    std::ofstream(temporary.path / "session_segments.csv", std::ios::binary);
    BOOST_CHECK(source.read("session_segments.csv", 0).empty());
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE(VarianceClockBundleTableTests)

namespace {

    struct BundleTableFixture {
        QuantLib::detail::VarianceClockManifest manifest;
        std::string profiles;
        std::string marketDays;
        std::string sessionSegments;
        std::string timezoneMapping;
        std::string slotEvidence;

        QuantLib::detail::VarianceClockBundleCsvBytes csv() const {
            return {profiles, marketDays, sessionSegments, timezoneMapping, slotEvidence};
        }
    };

    std::string csvEvidenceIds(std::string_view json = R"(["price"])") {
        std::string result = "\"";
        for (char c : json) {
            if (c == '"')
                result += "\"\"";
            else
                result += c;
        }
        result += '"';
        return result;
    }

    std::string utcTimestamp(std::int64_t seconds) {
        const std::int64_t days = seconds / 86400;
        const std::int64_t daySeconds = seconds % 86400;
        const Date date = Date(1, January, 1970) + static_cast<Integer>(days);
        const auto twoDigits = [](int value) {
            return std::string(value < 10 ? "0" : "") + std::to_string(value);
        };
        return std::to_string(date.year()) + "-" +
               twoDigits(static_cast<int>(date.month())) + "-" +
               twoDigits(date.dayOfMonth()) + "T" +
               twoDigits(static_cast<int>(daySeconds / 3600)) + ":" +
               twoDigits(static_cast<int>((daySeconds / 60) % 60)) + ":" +
               twoDigits(static_cast<int>(daySeconds % 60)) + "Z";
    }

    std::string isoDate(const Date& date) {
        const auto twoDigits = [](int value) {
            return std::string(value < 10 ? "0" : "") + std::to_string(value);
        };
        return std::to_string(date.year()) + "-" +
               twoDigits(static_cast<int>(date.month())) + "-" +
               twoDigits(date.dayOfMonth());
    }

    BundleTableFixture validBundleTableFixture() {
        BundleTableFixture result{
            parseVarianceClockManifest(minimalManifest()),
            "profile_id,minute_of_day,variance_per_5m,weight\n",
            "local_date,date_type,is_open,profile_id,target_group_id,selection_reason\n",
            "local_date,start_utc,end_utc,session_id,trading_date,source_session_id,"
            "claimed_local_offset_seconds,source_evidence_id\n",
            "start_utc,end_utc,offset_seconds,fold\n",
            "profile_id,target_group_id,minute_of_day,source_group_id,target_return_count,"
            "source_return_count,target_distinct_local_date_count,source_distinct_local_date_count,"
            "estimation_method,grouping_label,gap_pool_return_count,fallback_id,warning_codes,"
            "evidence_ids_json\n"};
        for (unsigned int minute = 0; minute < 1440; minute += 5)
            result.profiles += "1," + std::to_string(minute) + ",0.01,1\n";
        result.marketDays += "2024-01-01,full_day,true,1,group,date_override\n";
        result.sessionSegments +=
            "2024-01-01,2024-01-01T09:30:00Z,2024-01-01T16:00:00Z,session,,source,0,calendar\n";
        result.timezoneMapping +=
            "2024-01-01T00:00:00Z,2025-01-01T00:00:00Z,0,0\n";
        const std::string evidence = csvEvidenceIds();
        for (unsigned int minute = 0; minute < 1440; minute += 5) {
            result.slotEvidence +=
                "1,group," + std::to_string(minute) +
                ",,1,not_applicable,1,not_applicable,direct,,not_applicable,,," +
                evidence + "\n";
        }
        return result;
    }

    struct ParsedBundleTables {
        std::unique_ptr<QuantLib::detail::VarianceClockLoadBudget> budget;
        QuantLib::detail::ParsedVarianceClockTables tables;
    };

    ParsedBundleTables parseBundleTables(
        const BundleTableFixture& fixture,
        std::size_t budgetLimit = QuantLib::detail::VarianceClockLoadBudget::defaultLimit) {
        ParsedBundleTables result{
            std::make_unique<QuantLib::detail::VarianceClockLoadBudget>(budgetLimit), {}};
        result.tables = QuantLib::detail::parseVarianceClockBundleData(
            fixture.manifest, fixture.csv(), *result.budget);
        return result;
    }

    void checkBundleTablesRejected(const BundleTableFixture& fixture,
                                   std::size_t budgetLimit =
                                       QuantLib::detail::VarianceClockLoadBudget::defaultLimit) {
        BOOST_CHECK_THROW(parseBundleTables(fixture, budgetLimit), Error);
    }

    void replaceProfileLine(BundleTableFixture& fixture,
                            const std::string& before,
                            const std::string& after) {
        replaceOnce(fixture.profiles, before, after);
    }

    void replaceMarketDay(BundleTableFixture& fixture,
                          const std::string& before,
                          const std::string& after) {
        replaceOnce(fixture.marketDays, before, after);
    }

    void replaceSession(BundleTableFixture& fixture,
                        const std::string& before,
                        const std::string& after) {
        replaceOnce(fixture.sessionSegments, before, after);
    }

    void replaceSlotEvidence(BundleTableFixture& fixture,
                             const std::string& before,
                             const std::string& after) {
        replaceOnce(fixture.slotEvidence, before, after);
    }

}

namespace {

    void checkBundleTablesRejectedWith(
        const BundleTableFixture& fixture,
        const char* expected,
        std::size_t budgetLimit = QuantLib::detail::VarianceClockLoadBudget::defaultLimit) {
        try {
            parseBundleTables(fixture, budgetLimit);
            BOOST_ERROR("accepted tables; expected a rejection mentioning: " << expected);
        } catch (const Error& e) {
            BOOST_CHECK_MESSAGE(std::string(e.what()).find(expected) != std::string::npos,
                                "expected \"" << expected << "\" but got: " << e.what());
        }
    }

    // Replaces every slot-evidence row of the fixture's single (profile 1, "group") pair by
    // rows made of `tail`, the thirteen fields after the minute: source_group_id through
    // evidence_ids_json. An empty evidence tail uses the default one-ID array.
    void rewriteSlotRows(BundleTableFixture& fixture, const std::string& tail) {
        std::string rows = fixture.slotEvidence.substr(0, fixture.slotEvidence.find('\n') + 1);
        for (unsigned int minute = 0; minute < 1440; minute += 5)
            rows += "1,group," + std::to_string(minute) + "," + tail + "\n";
        fixture.slotEvidence = rows;
    }

    void useZeroWeightProfile(BundleTableFixture& fixture) {
        replaceAll(fixture.profiles, "0.01,1", "0,0");
    }

    void useOffsetRuns(BundleTableFixture& fixture, const std::string& rows) {
        fixture.timezoneMapping = "start_utc,end_utc,offset_seconds,fold\n" + rows;
    }

}

BOOST_AUTO_TEST_CASE(testRejectsMissingProfileSlot) {
    BOOST_TEST_MESSAGE("Testing rejection of a profile with one missing five-minute slot...");
    auto fixture = validBundleTableFixture();
    const std::size_t lastRecord = fixture.profiles.rfind("1,1435,0.01,1\n");
    BOOST_REQUIRE(lastRecord != std::string::npos);
    fixture.profiles.erase(lastRecord);
    checkBundleTablesRejected(fixture);

    fixture = validBundleTableFixture();
    const auto tables = parseBundleTables(fixture);
    BOOST_REQUIRE_EQUAL(tables.tables.profiles.size(), 1U);
    BOOST_CHECK_EQUAL(tables.tables.profiles[0].slots.size(), 288U);
}

BOOST_AUTO_TEST_CASE(testRejectsDuplicateProfileSlot) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate profile slots...");
    auto fixture = validBundleTableFixture();
    fixture.profiles += "1,0,0.01,1\n";
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsOffGridProfileMinute) {
    BOOST_TEST_MESSAGE("Testing rejection of a profile minute off the five-minute grid...");
    auto fixture = validBundleTableFixture();
    replaceProfileLine(fixture, "1,5,0.01,1\n", "1,6,0.01,1\n");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsProfileSlotOutsideDay) {
    BOOST_TEST_MESSAGE("Testing rejection of a profile minute outside the local day...");
    auto fixture = validBundleTableFixture();
    replaceProfileLine(fixture, "1,1435,0.01,1\n", "1,1440,0.01,1\n");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testParsesStrictUtcNanosecondTimestamp) {
    BOOST_TEST_MESSAGE("Testing strict UTC timestamp parsing with nanoseconds...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.coverageStartUtc = "2024-01-01T00:00:00.000000001Z";
    fixture.manifest.clockOriginUtc = fixture.manifest.coverageStartUtc;
    fixture.timezoneMapping =
        "start_utc,end_utc,offset_seconds,fold\n"
        "2024-01-01T00:00:00.000000001Z,2025-01-01T00:00:00Z,0,0\n";
    const auto tables = parseBundleTables(fixture);
    BOOST_CHECK_EQUAL(tables.tables.start.nanosecond(), 1U);
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidTimestampGrammar) {
    BOOST_TEST_MESSAGE("Testing rejection of noncanonical UTC timestamp grammar...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.coverageStartUtc = "2024-01-01T00:00:00+00:00";
    fixture.manifest.clockOriginUtc = fixture.manifest.coverageStartUtc;
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsDateOutsideQuantLibRange) {
    BOOST_TEST_MESSAGE("Testing rejection of a Gregorian date outside QuantLib's range...");
    auto fixture = validBundleTableFixture();
    replaceMarketDay(fixture, "2024-01-01", "1800-01-01");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsDuplicateLocalDate) {
    BOOST_TEST_MESSAGE("Testing rejection of duplicate market-day dates...");
    auto fixture = validBundleTableFixture();
    fixture.marketDays += "2024-01-01,holiday,false,1,group,date_override\n";
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsDuplicateSlotEvidenceKey) {
    BOOST_TEST_MESSAGE("Testing rejection of a duplicate slot-evidence key...");
    auto fixture = validBundleTableFixture();
    fixture.slotEvidence += fixture.slotEvidence.substr(
        fixture.slotEvidence.find('\n') + 1,
        fixture.slotEvidence.find('\n', fixture.slotEvidence.find('\n') + 1) -
            fixture.slotEvidence.find('\n') - 1);
    fixture.slotEvidence += '\n';
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsDanglingMarketDayProfileId) {
    BOOST_TEST_MESSAGE("Testing rejection of a market day that references no profile...");
    auto fixture = validBundleTableFixture();
    replaceMarketDay(fixture, ",true,1,", ",true,2,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsUnreferencedProfile) {
    BOOST_TEST_MESSAGE("Testing rejection of a profile not selected by any market day...");
    auto fixture = validBundleTableFixture();
    for (unsigned int minute = 0; minute < 1440; minute += 5)
        fixture.profiles += "2," + std::to_string(minute) + ",0.01,1\n";
    fixture.manifest.profileCalibrations.push_back(
        {2, "2024-01-01T00:00:00Z", {"price"}});
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingOrExtraSelectedPairSlotEvidence) {
    BOOST_TEST_MESSAGE("Testing exact selected-pair slot-evidence completeness...");
    auto missing = validBundleTableFixture();
    const std::size_t finalRow = missing.slotEvidence.rfind("1,group,1435,");
    BOOST_REQUIRE(finalRow != std::string::npos);
    missing.slotEvidence.erase(finalRow);
    checkBundleTablesRejected(missing);

    auto extra = validBundleTableFixture();
    replaceSlotEvidence(extra, "1,group,0,", "1,other,0,");
    checkBundleTablesRejected(extra);
}

BOOST_AUTO_TEST_CASE(testRejectsSessionDateMissingFromMarketDays) {
    BOOST_TEST_MESSAGE("Testing rejection of a session date absent from market_days...");
    auto fixture = validBundleTableFixture();
    replaceSession(fixture, "2024-01-01", "2024-01-02");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsEmptyRequiredSessionFields) {
    BOOST_TEST_MESSAGE("Testing rejection of empty required session fields...");
    auto fixture = validBundleTableFixture();
    replaceSession(fixture, ",session,,source,", ",,,,source,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testAcceptsOnlyPolicyAllowedEmptySessionFields) {
    BOOST_TEST_MESSAGE("Testing policy-allowed empty session metadata fields...");
    auto fixture = validBundleTableFixture();
    replaceSession(fixture, ",session,,source,0,calendar", ",session,,,,calendar");
    BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
}

BOOST_AUTO_TEST_CASE(testRejectsSessionCrossingLocalDate) {
    BOOST_TEST_MESSAGE("Testing rejection of a session segment crossing local midnight...");
    auto fixture = validBundleTableFixture();
    replaceSession(fixture, "2024-01-01T09:30:00Z", "2024-01-01T23:30:00Z");
    replaceSession(fixture, "2024-01-01T16:00:00Z", "2024-01-02T00:30:00Z");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsOverlappingSessionSegments) {
    BOOST_TEST_MESSAGE("Testing rejection of overlapping UTC session segments...");
    auto fixture = validBundleTableFixture();
    fixture.sessionSegments +=
        "2024-01-01,2024-01-01T10:00:00Z,2024-01-01T11:00:00Z,other,,,0,calendar\n";
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsOpenDateWithoutSegments) {
    BOOST_TEST_MESSAGE("Testing rejection of an open market date without sessions...");
    auto fixture = validBundleTableFixture();
    fixture.sessionSegments =
        "local_date,start_utc,end_utc,session_id,trading_date,source_session_id,"
        "claimed_local_offset_seconds,source_evidence_id\n";
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsClosedDateWithSegments) {
    BOOST_TEST_MESSAGE("Testing rejection of a closed market date with sessions...");
    auto fixture = validBundleTableFixture();
    replaceMarketDay(fixture, ",full_day,true,", ",holiday,false,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsDirectBelowMinimumReturns) {
    BOOST_TEST_MESSAGE("Testing rejection of a direct row below its minimum return count...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.calibrationSettings.minimumDirectReturns = 2;
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsPooledWithoutGapThreshold) {
    BOOST_TEST_MESSAGE("Testing rejection of pooled estimation without a threshold...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.calibrationSettings.minimumDirectReturns = 2;
    replaceSlotEvidence(fixture,
                        "1,group,0,,1,not_applicable,1,not_applicable,direct,,"
                        "not_applicable,,,",
                        "1,group,0,source,1,2,1,1,pooled,group,2,,,"
                        + csvEvidenceIds());
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsMinuteOfDayOutsideRange) {
    BOOST_TEST_MESSAGE("Testing rejection of slot-evidence minutes outside the day...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, "1,group,0,", "1,group,1440,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsMinuteOffFiveMinuteGrid) {
    BOOST_TEST_MESSAGE("Testing rejection of slot-evidence minutes off the five-minute grid...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, "1,group,0,", "1,group,1,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsIntegerLeadingZero) {
    BOOST_TEST_MESSAGE("Testing rejection of a leading zero in a canonical integer...");
    auto fixture = validBundleTableFixture();
    replaceProfileLine(fixture, "1,0,0.01,1\n", "01,0,0.01,1\n");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsIntegerPlusSign) {
    BOOST_TEST_MESSAGE("Testing rejection of a plus sign in an unsigned integer...");
    auto fixture = validBundleTableFixture();
    replaceProfileLine(fixture, "1,0,0.01,1\n", "+1,0,0.01,1\n");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsIntegerOverflow) {
    BOOST_TEST_MESSAGE("Testing rejection of an integer outside uint32 range...");
    auto fixture = validBundleTableFixture();
    replaceProfileLine(fixture, "1,0,0.01,1\n", "4294967296,0,0.01,1\n");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsUnknownCountOutsideFallback) {
    BOOST_TEST_MESSAGE("Testing rejection of unknown counts for direct estimation...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, "1,group,0,,1,not_applicable,1,not_applicable,direct",
                        "1,group,0,,unknown,not_applicable,1,not_applicable,direct");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsNotApplicableTargetCount) {
    BOOST_TEST_MESSAGE("Testing rejection of not_applicable target counts...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, "1,group,0,,1,not_applicable,1,not_applicable,direct",
                        "1,group,0,,not_applicable,not_applicable,1,not_applicable,direct");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsFallbackIdOnNonFallback) {
    BOOST_TEST_MESSAGE("Testing rejection of fallback IDs on direct rows...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, ",not_applicable,,,", ",not_applicable,fb,,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingFallbackId) {
    BOOST_TEST_MESSAGE("Testing rejection of fallback rows without an approval ID...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, "direct", "fallback");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsSourceGroupOnNonPooledRow) {
    BOOST_TEST_MESSAGE("Testing rejection of a source group on a direct row...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, "1,group,0,,1,", "1,group,0,source,1,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsGroupingLabelOnNonPooledRow) {
    BOOST_TEST_MESSAGE("Testing rejection of a grouping label on a direct row...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, ",direct,,not_applicable", ",direct,label,not_applicable");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsZeroMethodWithNonzeroWeight) {
    BOOST_TEST_MESSAGE("Testing rejection of zero estimation with nonzero profile weight...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, ",direct,", ",zero,");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsNonzeroMethodWithZeroWeight) {
    BOOST_TEST_MESSAGE("Testing rejection of nonzero estimation with zero profile weight...");
    auto fixture = validBundleTableFixture();
    for (std::size_t position = 0;
         (position = fixture.profiles.find("0.01,1", position)) != std::string::npos;
         position += 4)
        fixture.profiles.replace(position, 6, "0,0");
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testRejectsMissingMethodEvidenceIds) {
    BOOST_TEST_MESSAGE("Testing rejection of direct rows without method evidence...");
    auto fixture = validBundleTableFixture();
    replaceSlotEvidence(fixture, csvEvidenceIds(), csvEvidenceIds("[]"));
    checkBundleTablesRejected(fixture);
}

BOOST_AUTO_TEST_CASE(testAcceptsZeroRowsWithNoDistinctDates) {
    BOOST_TEST_MESSAGE("Testing zero rows with integer zero distinct-date counts...");
    auto fixture = validBundleTableFixture();
    useZeroWeightProfile(fixture);
    rewriteSlotRows(fixture, ",0,not_applicable,0,not_applicable,zero,,not_applicable,,"
                             "ZERO_RATE_SLOT," +
                                 csvEvidenceIds());
    BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
}

BOOST_AUTO_TEST_CASE(testAcceptsFallbackRowsWithUnknownTargetCounts) {
    BOOST_TEST_MESSAGE("Testing fallback rows with unknown target counts...");
    auto fixture = validBundleTableFixture();
    rewriteSlotRows(fixture, ",unknown,not_applicable,unknown,not_applicable,fallback,,"
                             "not_applicable,fb,UNKNOWN_COUNT_FALLBACK," +
                                 csvEvidenceIds());
    BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
}

BOOST_AUTO_TEST_CASE(testAcceptsPooledRowsWithZeroSourceCounts) {
    BOOST_TEST_MESSAGE("Testing pooled rows with zero source counts and a met gap threshold...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.calibrationSettings.gapPoolReturnThreshold = 1;
    rewriteSlotRows(fixture, "source,0,0,1,0,pooled,group,1,,," + csvEvidenceIds());
    BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
}

BOOST_AUTO_TEST_CASE(testRejectsInjectedSmallValidationBudget) {
    BOOST_TEST_MESSAGE("Testing rejection before exceeding an injected validation budget...");
    auto fixture = validBundleTableFixture();
    QuantLib::detail::VarianceClockLoadBudget budget(1024);
    BOOST_CHECK_EXCEPTION(
        QuantLib::detail::parseVarianceClockBundleData(fixture.manifest, fixture.csv(), budget),
        Error, [](const Error& e) {
            return std::string(e.what()).find("exceeds size limit") != std::string::npos;
        });
    BOOST_CHECK_LE(budget.used(), budget.limit());
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testParsesMaximumSlotRowsWithinFileAndRuntimeLimits) {
    BOOST_TEST_MESSAGE("Testing parsing at the 400,000-row CSV and 32 MiB limits...");
    auto fixture = validBundleTableFixture();
    fixture.timezoneMapping = "start_utc,end_utc,offset_seconds,fold\n";
    const std::int64_t start = 1704067200;
    const std::int64_t duration = 31622400;
    constexpr std::int64_t rows = 400000;
    for (std::int64_t i = 0; i < rows; ++i) {
        const std::int64_t from = start + duration * i / rows;
        const std::int64_t to = start + duration * (i + 1) / rows;
        fixture.timezoneMapping +=
            utcTimestamp(from) + "," + utcTimestamp(to) + ",0,0\n";
    }
    BOOST_REQUIRE_LE(fixture.timezoneMapping.size(), 32U * 1024U * 1024U);
    const auto parsed = parseBundleTables(fixture);
    BOOST_CHECK_EQUAL(parsed.tables.offsets.size(), static_cast<std::size_t>(rows));
}

BOOST_AUTO_TEST_CASE(testStreamsLargeSlotEvidenceWithinBudget) {
    BOOST_TEST_MESSAGE("Testing streaming of a large slot-evidence table under a bounded budget...");
    constexpr std::size_t targetGroups = 1300;
    constexpr std::size_t slotsPerPair = 288;
    auto fixture = validBundleTableFixture();
    fixture.marketDays =
        "local_date,date_type,is_open,profile_id,target_group_id,selection_reason\n";
    fixture.sessionSegments =
        "local_date,start_utc,end_utc,session_id,trading_date,source_session_id,"
        "claimed_local_offset_seconds,source_evidence_id\n";
    fixture.slotEvidence =
        "profile_id,target_group_id,minute_of_day,source_group_id,target_return_count,"
        "source_return_count,target_distinct_local_date_count,source_distinct_local_date_count,"
        "estimation_method,grouping_label,gap_pool_return_count,fallback_id,warning_codes,"
        "evidence_ids_json\n";
    fixture.manifest.calibrationSettings.gapPoolReturnThreshold = 1;
    const std::string evidence = csvEvidenceIds(R"(["p"])");
    Date day(1, January, 2024);
    for (std::size_t group = 0; group < targetGroups; ++group, ++day) {
        const std::string localDate = isoDate(day);
        const std::string targetGroup = "g" + std::to_string(group);
        fixture.marketDays += localDate + ",holiday,false,1," + targetGroup +
                              ",date_override\n";
        for (unsigned int minute = 0; minute < 1440; minute += 5) {
            fixture.slotEvidence +=
                "1," + targetGroup + "," + std::to_string(minute) +
                ",source,0,1,1,1,pooled,group,1,,," + evidence + "\n";
        }
    }
    BOOST_REQUIRE_EQUAL(targetGroups * slotsPerPair, 374400U);
    BOOST_REQUIRE_LE(fixture.slotEvidence.size(), 32U * 1024U * 1024U);

    const auto csv = fixture.csv();
    const std::size_t capturedBytes = csv.profiles.size() + csv.marketDays.size() +
                                      csv.sessionSegments.size() + csv.timezoneMapping.size() +
                                      csv.slotEvidence.size();
    QuantLib::detail::VarianceClockLoadBudget budget(32U * 1024U * 1024U);
    auto captured = budget.reserve(capturedBytes);
    const auto parsed = QuantLib::detail::parseVarianceClockBundleData(
        fixture.manifest, csv, budget);
    BOOST_CHECK_EQUAL(parsed.dates.size(), targetGroups);
    BOOST_CHECK_LE(budget.used(), budget.limit());
}

BOOST_AUTO_TEST_CASE(testProfileOutputReservationUsesProfileCount) {
    BOOST_TEST_MESSAGE("Testing profile-output reservation against distinct profile count...");
    constexpr std::size_t profileCount = 400;
    constexpr std::size_t slotsPerProfile = 288;
    auto fixture = validBundleTableFixture();
    fixture.profiles = "profile_id,minute_of_day,variance_per_5m,weight\n";
    fixture.marketDays =
        "local_date,date_type,is_open,profile_id,target_group_id,selection_reason\n";
    fixture.sessionSegments =
        "local_date,start_utc,end_utc,session_id,trading_date,source_session_id,"
        "claimed_local_offset_seconds,source_evidence_id\n";
    fixture.slotEvidence =
        "profile_id,target_group_id,minute_of_day,source_group_id,target_return_count,"
        "source_return_count,target_distinct_local_date_count,source_distinct_local_date_count,"
        "estimation_method,grouping_label,gap_pool_return_count,fallback_id,warning_codes,"
        "evidence_ids_json\n";
    fixture.manifest.profileCalibrations.clear();
    const std::string evidence = csvEvidenceIds();
    Date day(1, January, 2024);
    for (std::size_t index = 0; index < profileCount; ++index, ++day) {
        const std::uint32_t profile = static_cast<std::uint32_t>(index + 1);
        const std::string profileId = std::to_string(profile);
        fixture.marketDays += isoDate(day) + ",holiday,false," + profileId +
                              ",group,date_override\n";
        fixture.manifest.profileCalibrations.push_back(
            {profile, "2024-01-01T00:00:00Z", {"price"}});
        for (unsigned int minute = 0; minute < 1440; minute += 5) {
            fixture.profiles += profileId + "," + std::to_string(minute) + ",0.01,1\n";
            fixture.slotEvidence +=
                profileId + ",group," + std::to_string(minute) +
                ",,1,not_applicable,1,not_applicable,direct,,not_applicable,,," +
                evidence + "\n";
        }
    }
    BOOST_REQUIRE_EQUAL(profileCount * slotsPerProfile, 115200U);
    BOOST_REQUIRE_LE(fixture.slotEvidence.size(), 32U * 1024U * 1024U);
    const auto parsed = parseBundleTables(fixture);
    BOOST_CHECK_EQUAL(parsed.tables.profiles.size(), profileCount);
    BOOST_CHECK_EQUAL(parsed.tables.dates.size(), profileCount);
}

BOOST_AUTO_TEST_CASE(testWeightConsistencyAcceptsHalfPicounitRelativeError) {
    BOOST_TEST_MESSAGE("Testing acceptance within half a picounit of relative rate error...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.referenceVariancePer5m = "1";
    replaceAll(fixture.profiles, "0.01,1", "1,1.0000000000005");
    BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
}

BOOST_AUTO_TEST_CASE(testWeightConsistencyRejectsTwoPicounitRelativeError) {
    BOOST_TEST_MESSAGE("Testing rejection at two picounits of relative rate error...");
    auto fixture = validBundleTableFixture();
    fixture.manifest.referenceVariancePer5m = "1";
    replaceAll(fixture.profiles, "0.01,1", "1,1.000000000002");
    checkBundleTablesRejectedWith(fixture, "does not match variance rate");
}

BOOST_AUTO_TEST_CASE(testWeightConsistencyAcceptsExactZero) {
    BOOST_TEST_MESSAGE("Testing consistency of exact-zero variance rates...");
    auto zero = validBundleTableFixture();
    replaceAll(zero.profiles, "0.01,1", "0,0");
    replaceAll(zero.slotEvidence, "direct", "zero");
    BOOST_CHECK_NO_THROW(parseBundleTables(zero));
}

BOOST_AUTO_TEST_CASE(testRejectsPositiveToZeroWeightUnderflow) {
    BOOST_TEST_MESSAGE("Testing rejection when a positive rate underflows to zero weight...");
    auto underflow = validBundleTableFixture();
    underflow.manifest.referenceVariancePer5m = "1e308";
    replaceProfileLine(underflow, "0.01,1", "1e-320,0");
    checkBundleTablesRejected(underflow);
}

BOOST_AUTO_TEST_CASE(testDecimalParsingIgnoresGlobalNumpunct) {
    BOOST_TEST_MESSAGE("Testing decimal parsing under a comma-decimal global locale...");
    GlobalLocaleGuard localeGuard;
    auto fixture = validBundleTableFixture();
    BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
}

BOOST_AUTO_TEST_CASE(testLoadBudgetReservesReleasesAndReconciles) {
    BOOST_TEST_MESSAGE("Testing load-budget reservation, release, resize and moves...");
    using QuantLib::detail::VarianceClockLoadBudget;
    VarianceClockLoadBudget budget(100);
    BOOST_CHECK_EQUAL(budget.limit(), 100U);
    BOOST_CHECK_EQUAL(budget.used(), 0U);
    BOOST_CHECK_EQUAL(budget.remaining(), 100U);
    {
        auto first = budget.reserve(60);
        BOOST_CHECK_EQUAL(first.bytes(), 60U);
        BOOST_CHECK_EQUAL(budget.used(), 60U);
        BOOST_CHECK_EQUAL(budget.remaining(), 40U);
        // A refused reservation changes nothing; the limit itself is allowed.
        BOOST_CHECK_THROW(budget.reserve(41), Error);
        BOOST_CHECK_THROW(budget.reserve(static_cast<std::size_t>(-1)), Error);
        BOOST_CHECK_EQUAL(budget.used(), 60U);
        auto second = budget.reserve(40);
        BOOST_CHECK_EQUAL(budget.used(), 100U);
        BOOST_CHECK_EQUAL(budget.remaining(), 0U);
        BOOST_CHECK_THROW(budget.reserve(1), Error);

        second.release();
        BOOST_CHECK_EQUAL(second.bytes(), 0U);
        BOOST_CHECK_EQUAL(budget.used(), 60U);
        second.release();  // releasing twice is harmless
        BOOST_CHECK_EQUAL(budget.used(), 60U);
        BOOST_CHECK_THROW(second.resize(1), Error);

        // Reconcile a reservation with the actual size: shrink, grow, and refuse excess.
        first.resize(10);
        BOOST_CHECK_EQUAL(first.bytes(), 10U);
        BOOST_CHECK_EQUAL(budget.used(), 10U);
        first.resize(100);
        BOOST_CHECK_EQUAL(budget.used(), 100U);
        BOOST_CHECK_THROW(first.resize(101), Error);
        BOOST_CHECK_EQUAL(first.bytes(), 100U);
        BOOST_CHECK_EQUAL(budget.used(), 100U);
        first.resize(0);
        BOOST_CHECK_EQUAL(budget.used(), 0U);
    }
    BOOST_CHECK_EQUAL(budget.used(), 0U);

    {
        auto source = budget.reserve(30);
        auto moved = std::move(source);
        BOOST_CHECK_EQUAL(budget.used(), 30U);
        BOOST_CHECK_EQUAL(moved.bytes(), 30U);
        BOOST_CHECK_EQUAL(source.bytes(), 0U);
        BOOST_CHECK_THROW(source.resize(1), Error);

        auto other = budget.reserve(10);
        BOOST_CHECK_EQUAL(budget.used(), 40U);
        other = std::move(moved);  // the overwritten reservation is released
        BOOST_CHECK_EQUAL(budget.used(), 30U);
        BOOST_CHECK_EQUAL(other.bytes(), 30U);
    }
    BOOST_CHECK_EQUAL(budget.used(), 0U);

    VarianceClockLoadBudget::Reservation empty;
    BOOST_CHECK_EQUAL(empty.bytes(), 0U);
    empty.release();
    BOOST_CHECK_THROW(empty.resize(1), Error);
    BOOST_CHECK_NO_THROW(budget.reserve(100));
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testBundleTablesChargeAndReleaseTheLoadBudget) {
    BOOST_TEST_MESSAGE("Testing that parsing charges its retained output and releases it...");
    using QuantLib::detail::VarianceClockLoadBudget;
    const auto fixture = validBundleTableFixture();

    // The smallest budget that admits the fixture, found by bisection.
    std::size_t low = 0;
    std::size_t high = VarianceClockLoadBudget::defaultLimit;
    while (low + 1 < high) {
        const std::size_t middle = low + (high - low) / 2;
        bool accepted = true;
        try {
            parseBundleTables(fixture, middle);
        } catch (const Error&) {
            accepted = false;
        }
        (accepted ? high : low) = middle;
    }
    const std::size_t smallest = high;
    // The parser holds decoded text for the rows it reads, so it must reserve at least the
    // size of the CSV bytes before it starts.
    const std::size_t inputBytes = fixture.profiles.size() + fixture.marketDays.size() +
                                   fixture.sessionSegments.size() +
                                   fixture.timezoneMapping.size() + fixture.slotEvidence.size();
    BOOST_CHECK_GE(smallest, inputBytes);
    BOOST_CHECK_LT(smallest, 64U * 1024U * 1024U);

    // At the threshold parsing succeeds and keeps charging exactly its retained output;
    // one byte less is refused before anything is retained.
    {
        auto parsed = parseBundleTables(fixture, smallest);
        const std::size_t retained =
            parsed.tables.profiles.capacity() *
                sizeof(QuantLib::VarianceClockProfileInput) +
            parsed.tables.dates.capacity() *
                sizeof(QuantLib::VarianceClockDateInput) +
            parsed.tables.offsets.capacity() *
                sizeof(QuantLib::VarianceClockOffsetInput);
        BOOST_CHECK_EQUAL(parsed.budget->used(), retained);
        BOOST_CHECK_EQUAL(parsed.tables.storageCharge.bytes(), retained);
        BOOST_CHECK_LE(parsed.budget->used(), smallest);
    }
    QuantLib::detail::VarianceClockLoadBudget refused(smallest - 1);
    BOOST_CHECK_THROW(QuantLib::detail::parseVarianceClockBundleData(
                          fixture.manifest, fixture.csv(), refused),
                      Error);
    BOOST_CHECK_EQUAL(refused.used(), 0U);

    // The retained charge is released with the result.
    QuantLib::detail::VarianceClockLoadBudget budget;
    {
        auto tables = QuantLib::detail::parseVarianceClockBundleData(
            fixture.manifest, fixture.csv(), budget);
        BOOST_CHECK_GT(budget.used(), 0U);
        BOOST_CHECK_EQUAL(budget.used(), tables.storageCharge.bytes());
        auto moved = std::move(tables);
        BOOST_CHECK_EQUAL(budget.used(), moved.storageCharge.bytes());
    }
    BOOST_CHECK_EQUAL(budget.used(), 0U);
}

BOOST_AUTO_TEST_CASE(testRejectedTablesReleaseEveryReservation) {
    BOOST_TEST_MESSAGE("Testing that a late validation failure leaves no budget charged...");
    // Every rejection, early or after the retained-output charge, returns the budget to zero
    // and exposes no partial tables.
    auto early = validBundleTableFixture();
    early.profiles += "1,0,0.01,1\n";
    auto late = validBundleTableFixture();
    late.sessionSegments =
        "local_date,start_utc,end_utc,session_id,trading_date,source_session_id,"
        "claimed_local_offset_seconds,source_evidence_id\n";
    auto malformed = validBundleTableFixture();
    malformed.slotEvidence += "1,group\n";
    for (const BundleTableFixture* fixture : {&early, &late, &malformed}) {
        QuantLib::detail::VarianceClockLoadBudget budget;
        std::optional<QuantLib::detail::ParsedVarianceClockTables> escaped;
        BOOST_CHECK_THROW(escaped.emplace(QuantLib::detail::parseVarianceClockBundleData(
                              fixture->manifest, fixture->csv(), budget)),
                          Error);
        BOOST_CHECK(!escaped);
        BOOST_CHECK_EQUAL(budget.used(), 0U);
    }
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidMarketDayEnumerations) {
    BOOST_TEST_MESSAGE("Testing rejection of unknown market-day enumeration values...");
    for (const char* value : {"yes", "TRUE", "True", "1", ""}) {
        auto fixture = validBundleTableFixture();
        replaceMarketDay(fixture, ",full_day,true,", std::string(",full_day,") + value + ",");
        checkBundleTablesRejectedWith(fixture, "invalid is_open");
    }
    for (const char* value : {"bogus", "Full_Day", "half_day", ""}) {
        auto fixture = validBundleTableFixture();
        replaceMarketDay(fixture, ",full_day,true,", std::string(",") + value + ",true,");
        checkBundleTablesRejectedWith(fixture, "invalid market date type");
    }
    for (const char* value : {"bogus", "DATE_OVERRIDE", ""}) {
        auto fixture = validBundleTableFixture();
        replaceMarketDay(fixture, ",group,date_override", std::string(",group,") + value);
        checkBundleTablesRejectedWith(fixture, "invalid selection reason");
    }
    for (const char* type : {"early_close", "holiday", "weekend", "special"}) {
        auto fixture = validBundleTableFixture();
        replaceMarketDay(fixture, ",full_day,", std::string(",") + type + ",");
        BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
    }
}

BOOST_AUTO_TEST_CASE(testAcceptsEveryFrozenSelectionReason) {
    BOOST_TEST_MESSAGE("Testing every selection_reason allowed by the frozen schema...");
    for (const char* reason : {"date_override", "date_type_session_pattern",
                               "date_type_session_pattern_weekday", "base_profile_fallback"}) {
        auto fixture = validBundleTableFixture();
        replaceMarketDay(fixture, ",group,date_override", std::string(",group,") + reason);
        BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
    }
    for (const char* reason : {"regular", "emergency_override", "closed_override"}) {
        auto fixture = validBundleTableFixture();
        replaceMarketDay(fixture, ",group,date_override", std::string(",group,") + reason);
        checkBundleTablesRejectedWith(fixture, "invalid selection reason");
    }
}

BOOST_AUTO_TEST_CASE(testTradingDateMustBeGregorian) {
    BOOST_TEST_MESSAGE("Testing optional trading_date Gregorian grammar...");
    auto valid = validBundleTableFixture();
    replaceSession(valid, ",session,,source,0,calendar",
                   ",session,2024-02-29,source,0,calendar");
    BOOST_CHECK_NO_THROW(parseBundleTables(valid));

    for (const char* value : {"2023-02-29", "2024-13-01", "2024-2-09", "not-a-date"}) {
        auto invalid = validBundleTableFixture();
        replaceSession(invalid, ",session,,source,0,calendar",
                       std::string(",session,") + value + ",source,0,calendar");
        checkBundleTablesRejectedWith(invalid, "invalid Gregorian date");
    }
}

BOOST_AUTO_TEST_CASE(testDecimalGrammarMatchesFrozenRule) {
    BOOST_TEST_MESSAGE("Testing accepted and rejected frozen decimal grammar forms...");
    for (const auto& input : {std::pair<std::string, std::string>{"0.5", "0.5"},
                              {"1", "1"},
                              {"1e3", "1000"},
                              {"1E-3", "0.001"}}) {
        auto fixture = validBundleTableFixture();
        fixture.manifest.referenceVariancePer5m = "1";
        replaceAll(fixture.profiles, "0.01,1", input.first + "," + input.second);
        BOOST_CHECK_NO_THROW(parseBundleTables(fixture));
    }
    for (const auto& input : {std::pair<std::string, std::string>{".5", "0.5"},
                              {"5.", "5"},
                              {"007", "7"}}) {
        auto fixture = validBundleTableFixture();
        fixture.manifest.referenceVariancePer5m = "1";
        replaceAll(fixture.profiles, "0.01,1", input.first + "," + input.second);
        checkBundleTablesRejectedWith(fixture, "invalid decimal grammar");
    }
}

BOOST_AUTO_TEST_CASE(testSignedIntegerGrammarRejectsLeadingZeroes) {
    BOOST_TEST_MESSAGE("Testing signed-integer leading-zero rejection in both CSV columns...");
    for (const char* value : {"00", "01", "-01"}) {
        auto offset = validBundleTableFixture();
        replaceOnce(offset.timezoneMapping, "Z,0,0\n", std::string("Z,") + value + ",0\n");
        checkBundleTablesRejectedWith(offset, "invalid canonical signed integer");

        auto claim = validBundleTableFixture();
        replaceOnce(claim.timezoneMapping, "Z,0,0\n", std::string("Z,") + value + ",0\n");
        replaceSession(claim, ",source,0,calendar",
                       std::string(",source,") + value + ",calendar");
        checkBundleTablesRejectedWith(claim, "invalid canonical signed integer");
    }
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidBundleIdentifiers) {
    BOOST_TEST_MESSAGE("Testing identifier length, whitespace and control rules in tables...");
    for (const std::string& group : {std::string(" group"), std::string("group "),
                                     std::string("gr\x01oup"), std::string(129, 'g'),
                                     std::string("gr\x7f" "oup")}) {
        auto fixture = validBundleTableFixture();
        replaceAll(fixture.marketDays, ",group,", "," + group + ",");
        replaceAll(fixture.slotEvidence, ",group,", "," + group + ",");
        checkBundleTablesRejectedWith(fixture, "target group ID");
    }
    auto longest = validBundleTableFixture();
    replaceAll(longest.marketDays, ",group,", "," + std::string(128, 'g') + ",");
    replaceAll(longest.slotEvidence, ",group,", "," + std::string(128, 'g') + ",");
    BOOST_CHECK_NO_THROW(parseBundleTables(longest));

    auto session = validBundleTableFixture();
    replaceSession(session, ",session,", ", session,");
    checkBundleTablesRejectedWith(session, "session ID");
    auto evidence = validBundleTableFixture();
    replaceSession(evidence, ",calendar\n", ",calendar\x01\n");
    checkBundleTablesRejectedWith(evidence, "session evidence ID");
    auto source = validBundleTableFixture();
    replaceSession(source, ",source,", ",source ,");
    checkBundleTablesRejectedWith(source, "source session ID");
}

BOOST_AUTO_TEST_CASE(testBundleIdentifiersUseManifestUnicodeRules) {
    BOOST_TEST_MESSAGE("Testing table identifiers against B1 Unicode whitespace and controls...");
    const std::vector<std::pair<std::string, std::string>> rejected = {
        {std::string("\xC2\xA0") + "group", "surrounding whitespace"},
        {"group" + std::string("\xC2\xA0"), "surrounding whitespace"},
        {std::string("\xE3\x80\x80") + "g", "surrounding whitespace"},
        {"g" + std::string("\xE2\x80\xA8"), "surrounding whitespace"},
        {std::string("\xC2\x85") + "g", "control characters"}};
    for (const auto& item : rejected) {
        auto fixture = validBundleTableFixture();
        replaceAll(fixture.marketDays, ",group,", "," + item.first + ",");
        replaceAll(fixture.slotEvidence, ",group,", "," + item.first + ",");
        checkBundleTablesRejectedWith(fixture, item.second.c_str());
    }

    auto interiorWhitespace = validBundleTableFixture();
    const std::string embedded = std::string("g") + "\xE3\x80\x80" + "x";
    replaceAll(interiorWhitespace.marketDays, ",group,", "," + embedded + ",");
    replaceAll(interiorWhitespace.slotEvidence, ",group,", "," + embedded + ",");
    BOOST_CHECK_NO_THROW(parseBundleTables(interiorWhitespace));
}

BOOST_AUTO_TEST_CASE(testChecksSessionOffsetClaimAgainstTheRunAtItsStart) {
    BOOST_TEST_MESSAGE("Testing session offset claims against the timezone run at start...");
    // Offset 0 until 12:00Z, then +1 hour.
    const std::string runs =
        "2024-01-01T00:00:00Z,2024-01-01T12:00:00Z,0,0\n"
        "2024-01-01T12:00:00Z,2025-01-01T00:00:00Z,3600,1\n";
    auto withClaim = [&runs](const std::string& start, const std::string& end,
                             const std::string& claim) {
        auto fixture = validBundleTableFixture();
        useOffsetRuns(fixture, runs);
        fixture.sessionSegments =
            fixture.sessionSegments.substr(0, fixture.sessionSegments.find('\n') + 1) +
            "2024-01-01," + start + "," + end + ",session,,," + claim + ",calendar\n";
        return fixture;
    };
    // A segment spanning the change takes the run containing its start.
    BOOST_CHECK_NO_THROW(parseBundleTables(
        withClaim("2024-01-01T11:00:00Z", "2024-01-01T14:00:00Z", "0")));
    checkBundleTablesRejectedWith(
        withClaim("2024-01-01T11:00:00Z", "2024-01-01T14:00:00Z", "3600"),
        "offset claim disagrees");
    // A segment beginning exactly at the boundary uses the new run.
    BOOST_CHECK_NO_THROW(parseBundleTables(
        withClaim("2024-01-01T12:00:00Z", "2024-01-01T14:00:00Z", "3600")));
    checkBundleTablesRejectedWith(
        withClaim("2024-01-01T12:00:00Z", "2024-01-01T14:00:00Z", "0"),
        "offset claim disagrees");
    // An empty claim is allowed; noncanonical spellings are not.
    BOOST_CHECK_NO_THROW(parseBundleTables(
        withClaim("2024-01-01T12:00:00Z", "2024-01-01T14:00:00Z", "")));
    for (const char* claim : {"+3600", "-0", "3600.0", "abc", "2147483648"})
        checkBundleTablesRejectedWith(
            withClaim("2024-01-01T12:00:00Z", "2024-01-01T14:00:00Z", claim), "signed integer");
}

BOOST_AUTO_TEST_CASE(testSessionSegmentsStayInsideTheirLocalDate) {
    BOOST_TEST_MESSAGE("Testing half-open session intervals against the local date...");
    auto session = [](const std::string& start, const std::string& end, int offset) {
        auto fixture = validBundleTableFixture();
        fixture.manifest.coverageStartUtc = "2023-12-30T00:00:00Z";
        fixture.manifest.clockOriginUtc = fixture.manifest.coverageStartUtc;
        useOffsetRuns(fixture, "2023-12-30T00:00:00Z,2025-01-01T00:00:00Z," +
                                   std::to_string(offset) + ",0\n");
        fixture.sessionSegments =
            fixture.sessionSegments.substr(0, fixture.sessionSegments.find('\n') + 1) +
            "2024-01-01," + start + "," + end + ",session,,,,calendar\n";
        return fixture;
    };
    // The end instant is exclusive: ending at local midnight stays inside the date.
    BOOST_CHECK_NO_THROW(parseBundleTables(
        session("2024-01-01T09:00:00Z", "2024-01-02T00:00:00Z", 0)));
    checkBundleTablesRejectedWith(
        session("2024-01-01T09:00:00Z", "2024-01-02T00:00:00.000000001Z", 0),
        "crosses its declared local date");
    checkBundleTablesRejectedWith(
        session("2024-01-01T09:00:00Z", "2024-01-02T00:00:01Z", 0),
        "crosses its declared local date");
    checkBundleTablesRejectedWith(
        session("2023-12-31T23:59:59Z", "2024-01-01T10:00:00Z", 0),
        "crosses its declared local date");
    BOOST_CHECK_NO_THROW(parseBundleTables(
        session("2024-01-01T00:00:00Z", "2024-01-01T10:00:00Z", 0)));
    // The local date follows the supplied offset, not UTC.
    BOOST_CHECK_NO_THROW(parseBundleTables(
        session("2023-12-31T23:00:00Z", "2024-01-01T10:00:00Z", 3600)));
    checkBundleTablesRejectedWith(
        session("2023-12-31T22:59:59Z", "2024-01-01T10:00:00Z", 3600),
        "crosses its declared local date");
    BOOST_CHECK_NO_THROW(parseBundleTables(
        session("2024-01-01T05:00:00Z", "2024-01-02T04:59:59Z", -18000)));
    checkBundleTablesRejectedWith(
        session("2024-01-01T05:00:00Z", "2024-01-02T05:00:01Z", -18000),
        "crosses its declared local date");
    // Empty and reversed intervals.
    checkBundleTablesRejectedWith(
        session("2024-01-01T10:00:00Z", "2024-01-01T10:00:00Z", 0), "empty session segment");
    checkBundleTablesRejectedWith(
        session("2024-01-01T11:00:00Z", "2024-01-01T10:00:00Z", 0), "empty session segment");
}

BOOST_AUTO_TEST_CASE(testRejectsSessionDateAbsentFromMarketDaysByName) {
    BOOST_TEST_MESSAGE("Testing the session-date membership rule on its own...");
    auto fixture = validBundleTableFixture();
    fixture.sessionSegments +=
        "2024-01-02,2024-01-02T09:30:00Z,2024-01-02T16:00:00Z,session,,,0,calendar\n";
    checkBundleTablesRejectedWith(fixture, "absent from market days");
}

BOOST_AUTO_TEST_CASE(testRejectsMarketDayWithUnknownProfileByName) {
    BOOST_TEST_MESSAGE("Testing a market day that selects an unknown profile...");
    auto fixture = validBundleTableFixture();
    fixture.marketDays += "2024-01-02,holiday,false,3,group,date_override\n";
    checkBundleTablesRejectedWith(fixture, "unknown profile");
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidTimezoneMappingRuns) {
    BOOST_TEST_MESSAGE("Testing timezone mapping fold, range, contiguity and coverage...");
    auto rejected = [](const std::string& rows, const char* expected) {
        auto fixture = validBundleTableFixture();
        useOffsetRuns(fixture, rows);
        checkBundleTablesRejectedWith(fixture, expected);
    };
    rejected("2024-01-01T00:00:00Z,2025-01-01T00:00:00Z,0,2\n", "invalid timezone fold");
    rejected("2024-01-01T00:00:00Z,2025-01-01T00:00:00Z,0,\n", "invalid timezone fold");
    rejected("2024-01-01T00:00:00Z,2024-01-01T00:00:00Z,0,0\n"
             "2024-01-01T00:00:00Z,2025-01-01T00:00:00Z,0,0\n",
             "empty timezone mapping range");
    rejected("2024-01-01T00:00:00Z,2024-06-01T00:00:00Z,0,0\n"
             "2024-06-02T00:00:00Z,2025-01-01T00:00:00Z,0,0\n",
             "not contiguous");
    rejected("2024-01-01T00:00:00Z,2024-06-01T00:00:00Z,0,0\n"
             "2024-05-31T00:00:00Z,2025-01-01T00:00:00Z,0,0\n",
             "not contiguous");
    rejected("2024-01-01T00:00:01Z,2025-01-01T00:00:00Z,0,0\n", "does not cover");
    rejected("2024-01-01T00:00:00Z,2024-12-31T23:59:59Z,0,0\n", "does not cover");
    rejected("2024-01-01T00:00:00Z,2025-01-01T00:00:00Z,2147483648,0\n", "signed integer");
    rejected("2024-01-01T00:00:00Z,2025-01-01T00:00:00Z,+0,0\n", "signed integer");
    rejected("", "does not cover");

    // Coverage need not end at a run boundary, but must be fully covered.
    auto exact = validBundleTableFixture();
    useOffsetRuns(exact, "2024-01-01T00:00:00Z,2026-01-01T00:00:00Z,0,0\n");
    BOOST_CHECK_EQUAL(parseBundleTables(exact).tables.offsets.size(), 1U);

    auto empty = validBundleTableFixture();
    empty.manifest.coverageEndUtc = empty.manifest.coverageStartUtc;
    checkBundleTablesRejectedWith(empty, "coverage is empty");
    auto reversed = validBundleTableFixture();
    reversed.manifest.coverageEndUtc = "2023-01-01T00:00:00Z";
    checkBundleTablesRejectedWith(reversed, "coverage is empty");
}

BOOST_AUTO_TEST_CASE(testRejectsProfileCalibrationMismatch) {
    BOOST_TEST_MESSAGE("Testing manifest profile calibrations against the profile table...");
    auto unreferenced = validBundleTableFixture();
    unreferenced.manifest.profileCalibrations.push_back({2, "2024-01-01T00:00:00Z", {"price"}});
    checkBundleTablesRejectedWith(unreferenced, "unreferenced profile calibration");
    auto missing = validBundleTableFixture();
    missing.manifest.profileCalibrations.clear();
    checkBundleTablesRejectedWith(missing, "missing profile calibration");
    auto duplicate = validBundleTableFixture();
    duplicate.manifest.profileCalibrations.push_back(
        duplicate.manifest.profileCalibrations.front());
    checkBundleTablesRejectedWith(duplicate, "duplicate profile calibration");
    auto grammar = validBundleTableFixture();
    grammar.manifest.profileCalibrations.front().calibrationAsOfUtc = "2024-01-01 00:00:00";
    checkBundleTablesRejectedWith(grammar, "UTC");
}

BOOST_AUTO_TEST_CASE(testRejectsInvalidProfileRates) {
    BOOST_TEST_MESSAGE("Testing profile reference variance and rate validation...");
    auto reference = validBundleTableFixture();
    reference.manifest.referenceVariancePer5m = "0";
    checkBundleTablesRejectedWith(reference, "reference variance must be positive");
    auto negative = validBundleTableFixture();
    replaceAll(negative.profiles, "0.01,1", "-0.01,-1");
    checkBundleTablesRejectedWith(negative, "nonnegative decimal");
    for (const char* bad : {"abc", "", "1e", "0x10", "\"1,5\"", "inf", "nan", "+1"}) {
        auto fixture = validBundleTableFixture();
        replaceAll(fixture.profiles, "0.01,1", std::string(bad) + ",1");
        checkBundleTablesRejectedWith(fixture, "decimal");
    }
    // An extra row for the first slot past the end of the day.
    auto beyond = validBundleTableFixture();
    beyond.profiles += "1,1440,0.01,1\n";
    checkBundleTablesRejectedWith(beyond, "five-minute grid");
}

BOOST_AUTO_TEST_CASE(testSlotEvidenceMethodRules) {
    BOOST_TEST_MESSAGE("Testing slot-evidence method rules for pooled, zero and unknown...");
    const std::string ids = csvEvidenceIds();
    // Minimum direct returns 5 with a gap-pool threshold of 2: a pooled slot.
    auto pooled = [&ids](const std::string& tail) {
        auto fixture = validBundleTableFixture();
        fixture.manifest.calibrationSettings.minimumDirectReturns = 5;
        fixture.manifest.calibrationSettings.gapPoolReturnThreshold = 2U;
        rewriteSlotRows(fixture, tail + "," + ids);
        return fixture;
    };
    const std::string goodPooled = "src,1,2,1,1,pooled,label,2,,";
    BOOST_CHECK_NO_THROW(parseBundleTables(pooled(goodPooled)));
    for (const char* bad : {
             "src,1,2,1,1,pooled,label,1,,",       // gap-pool count below the threshold
             "src,5,2,1,1,pooled,label,2,,",       // target returns not below the minimum
             ",1,2,1,1,pooled,label,2,,",          // no source group
             "src,1,2,1,1,pooled,,2,,",            // no grouping label
             "src,1,not_applicable,1,1,pooled,label,2,,",
             "src,1,2,1,1,pooled,label,not_applicable,,",
             "src,1,2,1,1,pooled,label,2,fb,"})    // fallback ID on a pooled row
        checkBundleTablesRejectedWith(pooled(bad), "invalid pooled slot evidence");

    auto noThreshold = pooled(goodPooled);
    noThreshold.manifest.calibrationSettings.gapPoolReturnThreshold.reset();
    checkBundleTablesRejectedWith(noThreshold, "invalid pooled slot evidence");

    // A zero slot needs a zero rate, exact counts, no pooling data and cited evidence.
    auto zero = [&ids](const std::string& tail, const std::string& evidence) {
        auto fixture = validBundleTableFixture();
        useZeroWeightProfile(fixture);
        rewriteSlotRows(fixture, tail + "," + evidence);
        return fixture;
    };
    const std::string goodZero = ",5,not_applicable,1,not_applicable,zero,,not_applicable,,";
    BOOST_CHECK_NO_THROW(parseBundleTables(zero(goodZero, ids)));
    for (const char* bad : {
             "src,5,not_applicable,1,not_applicable,zero,,not_applicable,,",
             ",unknown,not_applicable,1,not_applicable,zero,,not_applicable,,",
             ",5,3,1,not_applicable,zero,,not_applicable,,",
             ",5,not_applicable,1,not_applicable,zero,label,not_applicable,,",
             ",5,not_applicable,1,not_applicable,zero,,3,,",
             ",5,not_applicable,1,not_applicable,zero,,not_applicable,fb,"})
        checkBundleTablesRejectedWith(zero(bad, ids), "invalid zero slot evidence");
    checkBundleTablesRejectedWith(zero(goodZero, csvEvidenceIds("[]")),
                                  "invalid zero slot evidence");

    // Method names are exact.
    for (const char* method : {"bogus", "Direct", ""}) {
        auto fixture = validBundleTableFixture();
        rewriteSlotRows(fixture, std::string(",1,not_applicable,1,not_applicable,") + method +
                                     ",,not_applicable,,," + ids);
        checkBundleTablesRejectedWith(fixture, "invalid estimation method");
    }

    // A fallback slot may have an unknown return count.
    auto fallback = validBundleTableFixture();
    rewriteSlotRows(fallback,
                    ",unknown,not_applicable,1,not_applicable,fallback,,not_applicable,fb,," + ids);
    BOOST_CHECK_NO_THROW(parseBundleTables(fallback));
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

    std::string sha256HexInChunks(std::string_view bytes, std::size_t chunk) {
        QuantLib::detail::VarianceSha256 digest;
        for (std::size_t i = 0; i < bytes.size(); i += chunk) {
            digest.update(bytes.substr(i, chunk));
            digest.update(std::string_view());  // an empty update changes nothing
        }
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

BOOST_AUTO_TEST_CASE(testSha256NistTwoBlockVector) {
    BOOST_TEST_MESSAGE("Testing the SHA-256 896-bit two-block NIST vector...");
    BOOST_CHECK_EQUAL(
        sha256Hex("abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopq"
                  "klmnopqrlmnopqrsmnopqrstnopqrstu"),
        "cf5b16a778af8380036ce59e7b0492370b249b11e8f07a51afac45037afee9d1");
}

BOOST_AUTO_TEST_CASE(testSha256NistMillionAVector) {
    BOOST_TEST_MESSAGE("Testing the SHA-256 one-million-'a' NIST vector...");
    const std::string input(1000000, 'a');
    BOOST_CHECK_EQUAL(sha256Hex(input),
                      "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
    BOOST_CHECK_EQUAL(sha256HexInChunks(input, 1000),
                      "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
}

BOOST_AUTO_TEST_CASE(testSha256ChunkedUpdatesMatchOracle) {
    BOOST_TEST_MESSAGE("Testing SHA-256 under every chunking of boundary-length inputs...");
    const std::vector<std::pair<std::size_t, std::string_view>> vectors = {
        {0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
        {1, "6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d"},
        {55, "463eb28e72f82e0a96c0a4cc53690c571281131f672aa229e0d45ae59b598b59"},
        {56, "da2ae4d6b36748f2a318f23e7ab1dfdf45acdc9d049bd80e59de82a60895f562"},
        {57, "2fe741af801cc238602ac0ec6a7b0c3a8a87c7fc7d7f02a3fe03d1c12eac4d8f"},
        {63, "29af2686fd53374a36b0846694cc342177e428d1647515f078784d69cdb9e488"},
        {64, "fdeab9acf3710362bd2658cdc9a29e8f9c757fcf9811603a8c447cd1d9151108"},
        {65, "4bfd2c8b6f1eec7a2afeb48b934ee4b2694182027e6d0fc075074f2fabb31781"},
        {119, "da18797ed7c3a777f0847f429724a2d8cd5138e6ed2895c3fa1a6d39d18f7ec6"},
        {120, "f52b23db1fbb6ded89ef42a23ce0c8922c45f25c50b568a93bf1c075420bbb7c"},
        {121, "335a461692b30bba1d647cc71604e88e676c90e4c22455d0b8c83f4bd7c8ac9b"},
        {127, "92ca0fa6651ee2f97b884b7246a562fa71250fedefe5ebf270d31c546bfea976"},
        {128, "471fb943aa23c511f6f72f8d1652d9c880cfa392ad80503120547703e56a2be5"},
        {129, "5099c6a56203f9687f7d33f4bfdf576d31dc91f6b695ecea38b2770c87631135"},
        {130, "8d39b60b9c767c58975b270c1d6b13c9b4507e5aee7ad496a3528e4c7f880721"},
        {191, "d280f473c251cb75c91880ea0eca2a2f1cda3152bef54a38c4a3aedad615c819"},
        {192, "8b4a544837a1a0280fa8a7c82865c27a1064b3cc6281fda0753566b9bb104a87"},
        {193, "7daafa7aed7d63d06a98b7b6f785eab5427d084f30d5c9ee6dd0d2f3ada329e6"},
        {255, "3f8591112c6bbe5c963965954e293108b7208ed2af893e500d859368c654eabe"},
        {256, "40aff2e9d2d8922e47afd4648e6967497158785fbd1da870e7110266bf944880"}
    };
    const std::vector<std::size_t> chunks = {1,  2,  3,  5,   31,  32,  33, 63,
                                             64, 65, 100, 127, 128, 129, 200};
    for (const auto& vector : vectors) {
        const std::string input = byteRange(vector.first);
        BOOST_CHECK_EQUAL(sha256Hex(input), vector.second);
        for (std::size_t chunk : chunks)
            BOOST_CHECK_MESSAGE(sha256HexInChunks(input, chunk) == vector.second,
                                "length " << vector.first << " chunk " << chunk);
    }
}

BOOST_AUTO_TEST_CASE(testSha256HighBytesAreUnsigned) {
    BOOST_TEST_MESSAGE("Testing SHA-256 of bytes with the high bit set...");
    const std::vector<std::pair<std::size_t, std::string_view>> vectors = {
        {1, "a8100ae6aa1940d0b663bb31cd466142ebbdbd5187131b92d93818987832eb89"},
        {55, "aadaed00a3c5fbb8072ae7f1984ba8199fbe5272de427d11eaf31583af37db51"},
        {56, "528ff50ab05e77bbbd224a9ec86165dbb6824a9a9efb544be0a1d57d5b416457"},
        {64, "8667e718294e9e0df1d30600ba3eeb201f764aad2dad72748643e4a285e1d1f7"},
        {65, "855c9a28fff2bbbd71327165554a00c6fdd44d5d58c1f12b8fdff29b5d67f001"},
        {128, "e9175db65a9789096ca9cb5524d3abc2107df03e3c9ba3af1aca628f9c5d3bd2"}
    };
    for (const auto& vector : vectors) {
        const std::string input(vector.first, static_cast<char>(0xFF));
        BOOST_CHECK_EQUAL(sha256Hex(input), vector.second);
        BOOST_CHECK_EQUAL(sha256HexInChunks(input, 7), vector.second);
    }
}

BOOST_AUTO_TEST_CASE(testSha256RejectsUseAfterFinish) {
    BOOST_TEST_MESSAGE("Testing that a finished SHA-256 digest cannot be reused...");
    QuantLib::detail::VarianceSha256 digest;
    digest.update("abc");
    BOOST_CHECK_EQUAL(digest.finishHex(),
                      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    BOOST_CHECK_THROW(digest.finishHex(), Error);
    BOOST_CHECK_THROW(digest.update("d"), Error);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
