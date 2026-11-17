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

#include <ql/time/varianceclockbundleevidence.hpp>
#include <ql/errors.hpp>
#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>

namespace QuantLib {
    namespace detail {
        namespace {

            using EvidenceMap = std::map<std::string, const VarianceClockManifestEvidence*>;

            int digits(std::string_view value, std::size_t pos, std::size_t count) {
                QL_REQUIRE(pos + count <= value.size(), "invalid strict UTC timestamp");
                int result = 0;
                for (std::size_t i = 0; i < count; ++i) {
                    const char c = value[pos + i];
                    QL_REQUIRE(c >= '0' && c <= '9', "invalid strict UTC timestamp");
                    result = result * 10 + c - '0';
                }
                return result;
            }

            VarianceClockInstant parseInstant(std::string_view value) {
                QL_REQUIRE(value.size() >= 20 && value[4] == '-' && value[7] == '-' &&
                               value[10] == 'T' && value[13] == ':' && value[16] == ':',
                           "invalid strict UTC timestamp");
                const int year = digits(value, 0, 4);
                const int month = digits(value, 5, 2);
                const int day = digits(value, 8, 2);
                QL_REQUIRE(month >= 1 && month <= 12, "invalid UTC date");
                const Date date(day, static_cast<Month>(month), year);
                QL_REQUIRE(date.dayOfMonth() == day && static_cast<int>(date.month()) == month &&
                               date.year() == year,
                           "invalid UTC date");
                const int hour = digits(value, 11, 2);
                const int minute = digits(value, 14, 2);
                const int second = digits(value, 17, 2);
                QL_REQUIRE(hour < 24 && minute < 60 && second < 60, "invalid UTC time");
                std::uint32_t nanos = 0;
                std::size_t pos = 19;
                if (pos < value.size() && value[pos] == '.') {
                    ++pos;
                    unsigned int count = 0;
                    while (pos < value.size() && value[pos] >= '0' && value[pos] <= '9' &&
                           count < 9) {
                        nanos = nanos * 10 + static_cast<unsigned int>(value[pos++] - '0');
                        ++count;
                    }
                    QL_REQUIRE(count > 0 && (pos == value.size() || value[pos] == 'Z'),
                               "invalid UTC fractional seconds");
                    while (count++ < 9)
                        nanos *= 10;
                }
                QL_REQUIRE(pos + 1 == value.size() && value[pos] == 'Z',
                           "UTC timestamp must end with Z");
                const auto seconds =
                    (static_cast<std::int64_t>(date.serialNumber() -
                                               Date(1, January, 1970).serialNumber()) *
                     86400) +
                    hour * 3600 + minute * 60 + second;
                VarianceClockInstant result;
                QL_REQUIRE(VarianceClockInstant::tryCreate(seconds, nanos, result),
                           "invalid UTC instant");
                return result;
            }

            std::string decode(const std::string_view* fields, std::size_t index) {
                return decodeVarianceClockCsvField(fields[index]);
            }

            const VarianceClockManifestEvidence& requireEvidence(
                const EvidenceMap& evidence, const std::string& id, const char* message) {
                const auto it = evidence.find(id);
                QL_REQUIRE(it != evidence.end(), message << ": " << id);
                return *it->second;
            }

            void requireRole(const VarianceClockManifestEvidence& evidence,
                             const char* role,
                             const char* context) {
                QL_REQUIRE(evidence.role == role, context << " has wrong evidence role");
            }

            struct StreamContext {
                const VarianceClockManifest& manifest;
                const EvidenceMap& evidence;
                std::set<std::string>& used;
                const std::vector<VarianceClockProfileInput>& profiles;
                const std::vector<VarianceClockOffsetInput>& offsets;
                std::vector<VarianceClockBundleWarning>& warnings;
            };

            bool checkSession(void* opaque, const std::string_view* fields, std::size_t) {
                auto& context = *static_cast<StreamContext*>(opaque);
                const auto id = decode(fields, 7);
                const auto& item = requireEvidence(context.evidence, id,
                                                   "dangling session evidence ID");
                requireRole(item, "calendar_source", "session segment");
                context.used.insert(id);
                const auto claim = decode(fields, 6);
                if (!claim.empty()) {
                    std::int32_t claimed = 0;
                    const auto parsed =
                        std::from_chars(claim.data(), claim.data() + claim.size(), claimed);
                    QL_REQUIRE(parsed.ec == std::errc() &&
                                   parsed.ptr == claim.data() + claim.size(),
                               "invalid claimed local offset");
                    const auto start = parseInstant(decode(fields, 1));
                    const auto run = std::find_if(
                        context.offsets.begin(), context.offsets.end(),
                        [start](const auto& value) {
                            return value.start <= start && start < value.end;
                        });
                    QL_REQUIRE(run != context.offsets.end() &&
                                   run->offsetSeconds == claimed,
                               "claimed local offset conflicts with timezone mapping");
                }
                return true;
            }

            bool checkSlots(void* opaque, const std::string_view* fields, std::size_t) {
                auto& context = *static_cast<StreamContext*>(opaque);
                const auto idsJson = decode(fields, 13);
                const auto evidenceIds = parseEvidenceIdsJson(idsJson);
                const auto method = decode(fields, 8);
                const auto fallbackId = decode(fields, 11);
                const auto warningCode = decode(fields, 12);
                QL_REQUIRE(!evidenceIds.empty(), "missing slot evidence");
                for (const auto& id : evidenceIds) {
                    const auto& item = requireEvidence(context.evidence, id,
                                                       "missing slot evidence");
                    if (method == "direct" || method == "pooled" || method == "zero")
                        requireRole(item, "price_input", "slot evidence");
                    context.used.insert(id);
                }
                if (method == "fallback") {
                    const auto approval = std::find_if(
                        context.manifest.fallbackApprovals.begin(),
                        context.manifest.fallbackApprovals.end(),
                        [&fallbackId](const auto& value) { return value.fallbackId == fallbackId; });
                    QL_REQUIRE(approval != context.manifest.fallbackApprovals.end() &&
                                   approval->approved,
                               "fallback lacks manifest approval");
                    std::set<std::string> required(approval->approvalEvidenceIds.begin(),
                                                   approval->approvalEvidenceIds.end());
                    required.insert(approval->sourceEvidenceIds.begin(),
                                    approval->sourceEvidenceIds.end());
                    const std::set<std::string> actual(evidenceIds.begin(), evidenceIds.end());
                    QL_REQUIRE(actual == required, "fallback evidence does not match approval union");
                    for (const auto& id : approval->approvalEvidenceIds) {
                        const auto& item = requireEvidence(context.evidence, id,
                                                           "dangling fallback evidence ID");
                        requireRole(item, "fallback_approval", "fallback evidence");
                        context.used.insert(id);
                    }
                    for (const auto& id : approval->sourceEvidenceIds) {
                        const auto& item = requireEvidence(context.evidence, id,
                                                           "dangling fallback evidence ID");
                        QL_REQUIRE(item.role != "fallback_approval",
                                   "fallback source evidence has fallback_approval role");
                        context.used.insert(id);
                    }
                }
                const std::uint32_t profile = [&]() {
                    std::uint32_t result = 0;
                    const auto text = decode(fields, 0);
                    const auto parsed = std::from_chars(text.data(), text.data() + text.size(),
                                                        result);
                    QL_REQUIRE(parsed.ec == std::errc() &&
                                   parsed.ptr == text.data() + text.size(),
                               "invalid slot profile ID");
                    return result;
                }();
                const auto target = decode(fields, 1);
                const auto minute = [&]() {
                    unsigned int result = 0;
                    const auto text = decode(fields, 2);
                    const auto parsed = std::from_chars(text.data(), text.data() + text.size(),
                                                        result);
                    QL_REQUIRE(parsed.ec == std::errc() &&
                                   parsed.ptr == text.data() + text.size(),
                               "invalid slot minute");
                    return result;
                }();
                QL_REQUIRE(minute < 1440 && minute % 5 == 0,
                           "invalid warning slot minute");
                const auto profileInput = std::find_if(
                    context.profiles.begin(), context.profiles.end(),
                    [profile](const auto& value) { return value.id == profile; });
                QL_REQUIRE(profileInput != context.profiles.end(), "orphan profile slot evidence");
                std::vector<std::string> expectedWarnings;
                if (method == "zero") {
                    QL_REQUIRE(profileInput->slots[minute / 5].weight == 0.0,
                               "zero slot does not have zero rate");
                    expectedWarnings.emplace_back("ZERO_RATE_SLOT");
                }
                if (method == "fallback" &&
                    (decode(fields, 4) == "unknown" || decode(fields, 6) == "unknown"))
                    expectedWarnings.emplace_back("UNKNOWN_COUNT_FALLBACK");
                QL_REQUIRE(warningCode.empty() || warningCode == "ZERO_RATE_SLOT" ||
                               warningCode == "UNKNOWN_COUNT_FALLBACK",
                           "unknown slot warning code");
                const std::string expectedCode =
                    expectedWarnings.empty() ? std::string() : expectedWarnings.front();
                QL_REQUIRE(warningCode == expectedCode,
                           "slot warning codes differ from derived set");
                if (!expectedCode.empty()) {
                    auto ids = evidenceIds;
                    std::sort(ids.begin(), ids.end());
                    ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
                    context.warnings.push_back(
                        {expectedCode, "warning", profile, target,
                         static_cast<std::uint16_t>(minute), std::move(ids)});
                }
                return true;
            }

        } // namespace

        VarianceClockValidatedBundle validateVarianceClockBundleEvidence(
            const VarianceClockManifest& manifest,
            const VarianceClockBundleCsvBytes& csv,
            ParsedVarianceClockTables&& parsed,
            VarianceClockLoadMode mode,
            VarianceClockLoadBudget& budget) {
            QL_REQUIRE(mode == VarianceClockLoadMode::Strict ||
                           mode == VarianceClockLoadMode::Reconstruction,
                       "invalid variance-clock load mode");
            constexpr std::size_t perEvidence = 512;
            QL_REQUIRE(csv.sessionSegments.size() <=
                           std::numeric_limits<std::size_t>::max() - csv.slotEvidence.size(),
                       "variance-clock evidence accounting overflow");
            const auto streamBytes = csv.sessionSegments.size() + csv.slotEvidence.size();
            QL_REQUIRE(streamBytes <= std::numeric_limits<std::size_t>::max() -
                                          parsed.storageCharge.bytes(),
                       "variance-clock evidence accounting overflow");
            QL_REQUIRE(manifest.evidence.size() <=
                           (std::numeric_limits<std::size_t>::max() -
                            parsed.storageCharge.bytes() - streamBytes) /
                               perEvidence,
                       "variance-clock evidence accounting overflow");
            const auto validationBytes = streamBytes + manifest.evidence.size() * perEvidence;
            parsed.storageCharge.resize(parsed.storageCharge.bytes() + validationBytes);
            QL_ENSURE(budget.used() >= parsed.storageCharge.bytes(),
                     "variance-clock evidence load budget mismatch");
            const auto generatedAt = parseInstant(manifest.generatedAtUtc);
            const auto coverageEnd = parseInstant(manifest.coverageEndUtc);
            const auto priceCutoff = parseInstant(manifest.priceCutoffUtc);
            const auto calendarAsOf = parseInstant(manifest.calendarAsOfUtc);
            const auto timezoneAsOf = parseInstant(manifest.timezoneAsOfUtc);
            QL_REQUIRE(mode != VarianceClockLoadMode::Strict || generatedAt < coverageEnd,
                       "Strict generated_at_utc must be before coverage_end_utc");
            QL_REQUIRE(priceCutoff <= generatedAt, "price cutoff is after generated_at_utc");
            QL_REQUIRE(calendarAsOf <= generatedAt, "calendar as-of is after generated_at_utc");
            QL_REQUIRE(timezoneAsOf <= generatedAt, "timezone as-of is after generated_at_utc");

            EvidenceMap evidence;
            VarianceClockInstant latestAvailability;
            for (const auto& item : manifest.evidence) {
                QL_REQUIRE(evidence.emplace(item.evidenceId, &item).second,
                           "duplicate evidence ID");
                const auto availableAt = parseInstant(item.availableAtUtc);
                QL_REQUIRE(availableAt <= generatedAt,
                           "evidence is available after generated_at_utc");
                if (latestAvailability < availableAt)
                    latestAvailability = availableAt;
            }

            std::set<std::string> used;
            VarianceClockInstant latestCalendar;
            for (const auto& id : manifest.calendarEvidenceIds) {
                const auto& item = requireEvidence(evidence, id, "dangling calendar evidence ID");
                requireRole(item, "calendar_source", "calendar evidence");
                used.insert(id);
                const auto availableAt = parseInstant(item.availableAtUtc);
                if (latestCalendar < availableAt)
                    latestCalendar = availableAt;
            }
            QL_REQUIRE(!manifest.calendarEvidenceIds.empty(), "empty calendar evidence IDs");
            QL_REQUIRE(latestCalendar <= calendarAsOf,
                       "calendar as-of precedes cited evidence");

            VarianceClockInstant latestTimezone;
            for (const auto& id : manifest.timezoneEvidenceIds) {
                const auto& item = requireEvidence(evidence, id, "dangling timezone evidence ID");
                requireRole(item, "timezone_rules", "timezone evidence");
                used.insert(id);
                const auto availableAt = parseInstant(item.availableAtUtc);
                if (latestTimezone < availableAt)
                    latestTimezone = availableAt;
            }
            QL_REQUIRE(!manifest.timezoneEvidenceIds.empty(), "empty timezone evidence IDs");
            QL_REQUIRE(latestTimezone <= timezoneAsOf,
                       "timezone as-of precedes cited evidence");

            for (const auto& approval : manifest.fallbackApprovals) {
                QL_REQUIRE(!approval.fallbackId.empty(), "empty fallback approval ID");
                for (const auto& id : approval.approvalEvidenceIds) {
                    const auto& item = requireEvidence(evidence, id,
                                                       "dangling fallback approval evidence ID");
                    requireRole(item, "fallback_approval", "fallback approval");
                    used.insert(id);
                }
                for (const auto& id : approval.sourceEvidenceIds) {
                    const auto& item = requireEvidence(evidence, id,
                                                       "dangling fallback source evidence ID");
                    QL_REQUIRE(item.role != "fallback_approval",
                               "fallback source evidence has fallback_approval role");
                    used.insert(id);
                }
            }
            if (manifest.continuousFuturesLineage) {
                for (const auto* ids : {&manifest.continuousFuturesLineage->rollScheduleEvidenceIds,
                                        &manifest.continuousFuturesLineage->contractMappingEvidenceIds}) {
                    for (const auto& id : *ids) {
                        const auto& item = requireEvidence(
                            evidence, id, "dangling continuous-futures evidence ID");
                        requireRole(item, "continuous_roll_mapping",
                                    "continuous-futures lineage");
                        used.insert(id);
                    }
                }
            }

            std::set<VarianceClockProfileId> calibratedProfiles;
            for (const auto& calibration : manifest.profileCalibrations)
                QL_REQUIRE(calibratedProfiles.insert(calibration.profileId).second,
                           "duplicate profile calibration");
            QL_REQUIRE(manifest.profileCalibrations.size() == parsed.profiles.size(),
                       "profile calibration set does not match profiles");
            for (const auto& calibration : manifest.profileCalibrations) {
                QL_REQUIRE(!calibration.evidenceIds.empty(),
                           "profile calibration has no evidence");
                VarianceClockInstant calibrationEvidence;
                for (const auto& id : calibration.evidenceIds) {
                    const auto& item = requireEvidence(evidence, id,
                                                       "dangling profile calibration evidence ID");
                    requireRole(item, "price_input", "profile calibration");
                    used.insert(id);
                    const auto availableAt = parseInstant(item.availableAtUtc);
                    if (calibrationEvidence < availableAt)
                        calibrationEvidence = availableAt;
                }
                const auto calibrationAsOf = parseInstant(calibration.calibrationAsOfUtc);
                QL_REQUIRE(calibrationEvidence <= calibrationAsOf,
                           "calibration precedes cited evidence");
                QL_REQUIRE(calibrationAsOf <= priceCutoff,
                           "calibration is after price cutoff");
                const auto profile = std::find_if(
                    parsed.profiles.begin(), parsed.profiles.end(),
                    [&calibration](const auto& value) { return value.id == calibration.profileId; });
                QL_REQUIRE(profile != parsed.profiles.end(), "orphan profile calibration");
                profile->calibrationAsOf = calibrationAsOf;
            }

            std::vector<VarianceClockBundleWarning> warnings;
            StreamContext context{manifest, evidence, used, parsed.profiles, parsed.offsets,
                                  warnings};
            QL_REQUIRE(visitVarianceClockCsvRows(csv.sessionSegments,
                                                 VarianceClockCsvSchema::SessionSegments,
                                                 &context, checkSession),
                       "session evidence validation stopped");
            QL_REQUIRE(visitVarianceClockCsvRows(csv.slotEvidence,
                                                 VarianceClockCsvSchema::SlotEvidence,
                                                 &context, checkSlots),
                       "slot evidence validation stopped");
            const auto warningOrder = [](const auto& left, const auto& right) {
                return std::tie(left.code, left.profileId, left.targetGroupId,
                                left.minuteOfDay, left.evidenceIds) <
                       std::tie(right.code, right.profileId, right.targetGroupId,
                                right.minuteOfDay, right.evidenceIds);
            };
            std::sort(warnings.begin(), warnings.end(), warningOrder);
            std::vector<VarianceClockManifestWarning> manifestWarnings = manifest.warnings;
            std::sort(manifestWarnings.begin(), manifestWarnings.end(),
                      [](const auto& left, const auto& right) {
                          return std::tie(left.code, left.profileId, left.targetGroupId,
                                          left.minuteOfDay, left.evidenceIds) <
                                 std::tie(right.code, right.profileId, right.targetGroupId,
                                          right.minuteOfDay, right.evidenceIds);
                      });
            QL_REQUIRE(warnings.size() == manifestWarnings.size(),
                       "manifest warnings differ from derived warnings");
            for (std::size_t i = 0; i < warnings.size(); ++i) {
                const auto& derived = warnings[i];
                const auto& supplied = manifestWarnings[i];
                QL_REQUIRE(supplied.severity == "warning" && supplied.code == derived.code &&
                               supplied.profileId == derived.profileId &&
                               supplied.targetGroupId == derived.targetGroupId &&
                               supplied.minuteOfDay == derived.minuteOfDay &&
                               supplied.evidenceIds == derived.evidenceIds,
                           "manifest warnings differ from derived warnings");
            }
            for (const auto& item : manifest.evidence)
                QL_REQUIRE(used.count(item.evidenceId) != 0, "orphan evidence");

            VarianceClockValidatedBundle result;
            result.tables.start = parsed.start;
            result.tables.end = parsed.end;
            result.tables.availableFrom =
                mode == VarianceClockLoadMode::Strict ? generatedAt : latestAvailability;
            result.tables.profiles = std::move(parsed.profiles);
            result.tables.dates = std::move(parsed.dates);
            result.tables.offsets = std::move(parsed.offsets);
            result.provenance.snapshotId = manifest.snapshotId;
            result.provenance.availableFrom = result.tables.availableFrom;
            result.provenance.mode = mode;
            result.provenance.reconstructed = mode == VarianceClockLoadMode::Reconstruction;
            result.warnings = std::move(warnings);
            result.storageCharge = std::move(parsed.storageCharge);
            return result;
        }

    }
}
