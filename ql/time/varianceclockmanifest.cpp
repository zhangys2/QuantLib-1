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

#include <ql/time/varianceclockmanifest.hpp>
#include <ql/errors.hpp>

#if defined(__GNUC__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif
#include <ql/utilities/detail/thirdparty/nlohmann/json.hpp>
#if defined(__GNUC__)
#pragma GCC diagnostic pop
#endif

#include <array>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <limits>
#include <set>
#include <string>
#include <utility>

namespace QuantLib {
    namespace detail {
        namespace {

            using Json = nlohmann::json;

            constexpr std::size_t maxManifestBytes = 4U * 1024U * 1024U;
            constexpr std::size_t maxEvidenceIdsJsonBytes = 64U * 1024U;
            constexpr std::size_t maxJsonDepth = 32;
            constexpr std::size_t maxEvidenceIds = 256;

            struct Frame {
                Json value;
                bool object;
                std::string pendingKey;
                bool hasPendingKey;
                std::set<std::string> keys;
            };

            class SaxBuilder : public nlohmann::json_sax<Json> {
              public:
                bool null() override {
                    return add(nullptr);
                }

                bool boolean(bool value) override {
                    return add(value);
                }

                bool number_integer(number_integer_t value) override {
                    return add(value);
                }

                bool number_unsigned(number_unsigned_t value) override {
                    return add(value);
                }

                bool number_float(number_float_t value, const string_t&) override {
                    return add(value);
                }

                bool string(string_t& value) override {
                    return add(value);
                }

                bool binary(binary_t&) override {
                    return false;
                }

                bool start_object(std::size_t) override {
                    return start(Json::object(), true);
                }

                bool key(string_t& value) override {
                    if (frames_.empty() || !frames_.back().object ||
                        frames_.back().hasPendingKey ||
                        !frames_.back().keys.insert(value).second)
                        return false;
                    frames_.back().pendingKey = value;
                    frames_.back().hasPendingKey = true;
                    return true;
                }

                bool end_object() override {
                    return end(true);
                }

                bool start_array(std::size_t) override {
                    return start(Json::array(), false);
                }

                bool end_array() override {
                    return end(false);
                }

                bool parse_error(std::size_t, const std::string&,
                                 const nlohmann::detail::exception&) override {
                    return false;
                }

                Json result;
                bool hasResult = false;

                bool complete() const {
                    return frames_.empty();
                }

              private:
                bool start(Json value, bool object) {
                    if (frames_.size() + 1 > maxJsonDepth)
                        return false;
                    frames_.push_back({std::move(value), object, {}, false, {}});
                    return true;
                }

                bool end(bool object) {
                    if (frames_.empty() || frames_.back().object != object)
                        return false;
                    Json value = std::move(frames_.back().value);
                    frames_.pop_back();
                    return add(std::move(value));
                }

                bool add(Json value) {
                    if (frames_.empty()) {
                        if (hasResult)
                            return false;
                        result = std::move(value);
                        hasResult = true;
                        return true;
                    }
                    Frame& parent = frames_.back();
                    if (parent.object) {
                        if (!parent.hasPendingKey)
                            return false;
                        parent.value.emplace(std::move(parent.pendingKey), std::move(value));
                        parent.pendingKey.clear();
                        parent.hasPendingKey = false;
                    } else {
                        parent.value.push_back(std::move(value));
                    }
                    return true;
                }

                std::vector<Frame> frames_;
            };

            Json parseJson(std::string_view bytes, std::size_t maxBytes) {
                QL_REQUIRE(bytes.size() <= maxBytes, "JSON input exceeds size limit");
                SaxBuilder sax;
                try {
                    const bool parsed = Json::sax_parse(bytes.begin(), bytes.end(), &sax,
                                                        Json::input_format_t::json, true, false);
                    QL_REQUIRE(parsed && sax.hasResult && sax.complete(),
                               "invalid or unsupported JSON input");
                } catch (const std::exception& e) {
                    QL_FAIL("invalid JSON input: " << e.what());
                }
                return std::move(sax.result);
            }

            void requireObjectKeys(const Json& value,
                                   std::initializer_list<const char*> expected,
                                   const std::string& name) {
                QL_REQUIRE(value.is_object() && value.size() == expected.size(),
                           name << " must be an object with the exact required keys");
                for (const char* key : expected)
                    QL_REQUIRE(value.contains(key), name << " is missing key " << key);
            }

            const Json& field(const Json& value, const char* key) {
                QL_REQUIRE(value.is_object() && value.contains(key),
                           "missing required JSON key " << key);
                return value.at(key);
            }

            std::string stringValue(const Json& value, const std::string& name) {
                QL_REQUIRE(value.is_string(), name << " must be a string");
                std::string result = value.get<std::string>();
                QL_REQUIRE(!result.empty(), name << " must not be empty");
                return result;
            }

            std::string requiredString(const Json& value, const char* key) {
                return stringValue(field(value, key), key);
            }

            std::optional<std::string> optionalString(const Json& value, const char* key) {
                const Json& item = field(value, key);
                if (item.is_null())
                    return std::nullopt;
                return stringValue(item, key);
            }

            std::uint32_t uint32Value(const Json& value, const std::string& name) {
                QL_REQUIRE(value.is_number_unsigned() &&
                               value.get<Json::number_unsigned_t>() <=
                                   std::numeric_limits<std::uint32_t>::max(),
                           name << " must be an unsigned 32-bit integer token");
                return static_cast<std::uint32_t>(value.get<Json::number_unsigned_t>());
            }

            std::vector<std::string> stringArray(const Json& value,
                                                 const std::string& name,
                                                 bool requireNonempty = false) {
                QL_REQUIRE(value.is_array(), name << " must be an array");
                QL_REQUIRE(!requireNonempty || !value.empty(), name << " must not be empty");
                std::vector<std::string> result;
                std::set<std::string> unique;
                result.reserve(value.size());
                for (const Json& item : value) {
                    std::string text = stringValue(item, name);
                    QL_REQUIRE(unique.insert(text).second, name << " contains duplicate values");
                    result.push_back(std::move(text));
                }
                return result;
            }

            void requireEnum(const std::string& value,
                             std::initializer_list<const char*> choices,
                             const std::string& name) {
                for (const char* choice : choices)
                    if (value == choice)
                        return;
                QL_FAIL("unsupported " << name << ": " << value);
            }

            bool isSha256(const std::string& value) {
                if (value.size() != 64)
                    return false;
                for (char c : value)
                    if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')))
                        return false;
                return true;
            }

            VarianceClockManifest parseManifest(const Json& root) {
                requireObjectKeys(root,
                    {"format_version", "snapshot_id", "generated_at_utc",
                     "coverage_start_utc", "coverage_end_utc", "clock_origin_utc",
                     "market_id", "iana_zone", "reference_variance_per_5m",
                     "reference_unit", "price_cutoff_utc", "calendar_version",
                     "calendar_as_of_utc", "calendar_evidence_ids", "timezone_database",
                     "timezone_version", "timezone_as_of_utc", "timezone_evidence_ids",
                     "timezone_rules_sha256", "calibration_settings", "profile_calibrations",
                     "evidence", "fallback_approvals", "warnings", "files",
                     "continuous_futures_lineage"}, "manifest");

                VarianceClockManifest result{};
                result.formatVersion = uint32Value(field(root, "format_version"),
                                                   "format_version");
                QL_REQUIRE(result.formatVersion == 1, "unsupported manifest format_version");
                result.snapshotId = requiredString(root, "snapshot_id");
                result.generatedAtUtc = requiredString(root, "generated_at_utc");
                result.coverageStartUtc = requiredString(root, "coverage_start_utc");
                result.coverageEndUtc = requiredString(root, "coverage_end_utc");
                result.clockOriginUtc = requiredString(root, "clock_origin_utc");
                result.marketId = requiredString(root, "market_id");
                result.ianaZone = requiredString(root, "iana_zone");
                result.referenceVariancePer5m = requiredString(root, "reference_variance_per_5m");
                result.referenceUnit = requiredString(root, "reference_unit");
                QL_REQUIRE(result.referenceUnit == "variance_per_5m",
                           "unsupported reference_unit");
                result.priceCutoffUtc = requiredString(root, "price_cutoff_utc");
                result.calendarVersion = requiredString(root, "calendar_version");
                result.calendarAsOfUtc = requiredString(root, "calendar_as_of_utc");
                result.calendarEvidenceIds =
                    stringArray(field(root, "calendar_evidence_ids"),
                                "calendar_evidence_ids", true);
                result.timezoneDatabase = requiredString(root, "timezone_database");
                result.timezoneVersion = requiredString(root, "timezone_version");
                result.timezoneAsOfUtc = requiredString(root, "timezone_as_of_utc");
                result.timezoneEvidenceIds =
                    stringArray(field(root, "timezone_evidence_ids"),
                                "timezone_evidence_ids", true);
                result.timezoneRulesSha256 = requiredString(root, "timezone_rules_sha256");
                QL_REQUIRE(isSha256(result.timezoneRulesSha256),
                           "timezone_rules_sha256 must be lowercase SHA-256");

                const Json& calibration = field(root, "calibration_settings");
                requireObjectKeys(calibration,
                    {"method", "minimum_direct_returns", "gap_pool_return_threshold",
                     "price_cutoff_utc"}, "calibration_settings");
                result.calibrationSettings.method = requiredString(calibration, "method");
                QL_REQUIRE(result.calibrationSettings.method ==
                               "historical_variance_over_common_reference",
                           "unsupported calibration method");
                result.calibrationSettings.minimumDirectReturns =
                    uint32Value(field(calibration, "minimum_direct_returns"),
                                "minimum_direct_returns");
                QL_REQUIRE(result.calibrationSettings.minimumDirectReturns > 0,
                           "minimum_direct_returns must be positive");
                const Json& threshold = field(calibration, "gap_pool_return_threshold");
                if (threshold.is_null())
                    result.calibrationSettings.gapPoolReturnThreshold = std::nullopt;
                else {
                    const std::uint32_t parsed =
                        uint32Value(threshold, "gap_pool_return_threshold");
                    QL_REQUIRE(parsed > 0, "gap_pool_return_threshold must be positive");
                    result.calibrationSettings.gapPoolReturnThreshold = parsed;
                }
                result.calibrationSettings.priceCutoffUtc =
                    requiredString(calibration, "price_cutoff_utc");
                QL_REQUIRE(result.calibrationSettings.priceCutoffUtc == result.priceCutoffUtc,
                           "nested and top-level price cutoffs differ");

                const Json& profileCalibrations = field(root, "profile_calibrations");
                QL_REQUIRE(profileCalibrations.is_array(),
                           "profile_calibrations must be an array");
                std::set<std::uint32_t> profileIds;
                for (const Json& item : profileCalibrations) {
                    requireObjectKeys(item, {"profile_id", "calibration_as_of_utc", "evidence_ids"},
                                      "profile calibration");
                    VarianceClockManifestProfileCalibration entry{};
                    entry.profileId = uint32Value(field(item, "profile_id"), "profile_id");
                    QL_REQUIRE(profileIds.insert(entry.profileId).second,
                               "duplicate profile calibration");
                    entry.calibrationAsOfUtc = requiredString(item, "calibration_as_of_utc");
                    entry.evidenceIds =
                        stringArray(field(item, "evidence_ids"), "profile evidence_ids", true);
                    result.profileCalibrations.push_back(std::move(entry));
                }

                const Json& evidence = field(root, "evidence");
                QL_REQUIRE(evidence.is_array(), "evidence must be an array");
                std::set<std::string> evidenceIds;
                for (const Json& item : evidence) {
                    requireObjectKeys(item,
                        {"evidence_id", "role", "source_id", "revision_id",
                         "published_at_utc", "available_at_utc", "uri", "content_sha256",
                         "attestation_ref"}, "evidence");
                    VarianceClockManifestEvidence entry{};
                    entry.evidenceId = requiredString(item, "evidence_id");
                    QL_REQUIRE(evidenceIds.insert(entry.evidenceId).second,
                               "duplicate evidence_id");
                    entry.role = requiredString(item, "role");
                    requireEnum(entry.role,
                        {"price_input", "calendar_source", "timezone_rules",
                         "fallback_approval", "continuous_roll_mapping", "other_required_source"},
                        "evidence role");
                    entry.sourceId = requiredString(item, "source_id");
                    entry.revisionId = optionalString(item, "revision_id");
                    entry.publishedAtUtc = optionalString(item, "published_at_utc");
                    entry.availableAtUtc = requiredString(item, "available_at_utc");
                    entry.uri = optionalString(item, "uri");
                    entry.contentSha256 = optionalString(item, "content_sha256");
                    if (entry.contentSha256)
                        QL_REQUIRE(isSha256(*entry.contentSha256),
                                   "content_sha256 must be lowercase SHA-256");
                    entry.attestationRef = optionalString(item, "attestation_ref");
                    result.evidence.push_back(std::move(entry));
                }

                const Json& approvals = field(root, "fallback_approvals");
                QL_REQUIRE(approvals.is_array(), "fallback_approvals must be an array");
                std::set<std::string> fallbackIds;
                for (const Json& item : approvals) {
                    requireObjectKeys(item,
                        {"fallback_id", "approved", "approval_evidence_ids",
                         "source_evidence_ids"}, "fallback approval");
                    VarianceClockManifestFallbackApproval entry{};
                    entry.fallbackId = requiredString(item, "fallback_id");
                    QL_REQUIRE(fallbackIds.insert(entry.fallbackId).second,
                               "duplicate fallback_id");
                    const Json& approved = field(item, "approved");
                    QL_REQUIRE(approved.is_boolean(), "approved must be a Boolean");
                    entry.approved = approved.get<bool>();
                    entry.approvalEvidenceIds =
                        stringArray(field(item, "approval_evidence_ids"),
                                    "approval_evidence_ids", true);
                    entry.sourceEvidenceIds =
                        stringArray(field(item, "source_evidence_ids"),
                                    "source_evidence_ids", true);
                    result.fallbackApprovals.push_back(std::move(entry));
                }

                const Json& warnings = field(root, "warnings");
                QL_REQUIRE(warnings.is_array(), "warnings must be an array");
                for (const Json& item : warnings) {
                    requireObjectKeys(item,
                        {"code", "severity", "profile_id", "target_group_id",
                         "minute_of_day", "evidence_ids"}, "warning");
                    VarianceClockManifestWarning entry{};
                    entry.code = requiredString(item, "code");
                    requireEnum(entry.code, {"ZERO_RATE_SLOT", "UNKNOWN_COUNT_FALLBACK"},
                                "warning code");
                    entry.severity = requiredString(item, "severity");
                    QL_REQUIRE(entry.severity == "warning", "unsupported warning severity");
                    entry.profileId = uint32Value(field(item, "profile_id"), "profile_id");
                    entry.targetGroupId = requiredString(item, "target_group_id");
                    const std::uint32_t minute =
                        uint32Value(field(item, "minute_of_day"), "minute_of_day");
                    QL_REQUIRE(minute <= 1435 && minute % 5 == 0,
                               "minute_of_day must be a five-minute slot");
                    entry.minuteOfDay = static_cast<std::uint16_t>(minute);
                    entry.evidenceIds =
                        stringArray(field(item, "evidence_ids"), "warning evidence_ids");
                    result.warnings.push_back(std::move(entry));
                }

                const Json& files = field(root, "files");
                requireObjectKeys(files,
                    {"profiles.csv", "market_days.csv", "session_segments.csv",
                     "timezone_mapping.csv", "slot_evidence.csv"}, "files");
                for (auto it = files.begin(); it != files.end(); ++it) {
                    const std::string digest = stringValue(it.value(), "file digest");
                    QL_REQUIRE(isSha256(digest), "file digest must be lowercase SHA-256");
                    result.files.emplace(it.key(), digest);
                }

                const Json& lineage = field(root, "continuous_futures_lineage");
                if (!lineage.is_null()) {
                    requireObjectKeys(lineage,
                        {"construction_method", "source_instrument", "continuous_symbol",
                         "roll_rule", "roll_schedule_evidence_ids",
                         "contract_mapping_evidence_ids"}, "continuous_futures_lineage");
                    VarianceClockManifestContinuousFuturesLineage entry{};
                    entry.constructionMethod = requiredString(lineage, "construction_method");
                    entry.sourceInstrument = requiredString(lineage, "source_instrument");
                    entry.continuousSymbol = requiredString(lineage, "continuous_symbol");
                    entry.rollRule = requiredString(lineage, "roll_rule");
                    entry.rollScheduleEvidenceIds =
                        stringArray(field(lineage, "roll_schedule_evidence_ids"),
                                    "roll_schedule_evidence_ids", true);
                    entry.contractMappingEvidenceIds =
                        stringArray(field(lineage, "contract_mapping_evidence_ids"),
                                    "contract_mapping_evidence_ids", true);
                    result.continuousFuturesLineage = std::move(entry);
                }

                return result;
            }

        }

        VarianceClockManifest parseVarianceClockManifest(std::string_view bytes) {
            return parseManifest(parseJson(bytes, maxManifestBytes));
        }

        std::vector<std::string> parseEvidenceIdsJson(std::string_view bytes) {
            const Json value = parseJson(bytes, maxEvidenceIdsJsonBytes);
            std::vector<std::string> result = stringArray(value, "evidence_ids_json");
            QL_REQUIRE(result.size() <= maxEvidenceIds,
                       "evidence_ids_json exceeds 256 identifiers");
            return result;
        }

    }
}
