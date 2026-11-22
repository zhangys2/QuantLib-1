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
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>

namespace QuantLib {
    namespace detail {
        namespace {

            using EvidenceMap = std::map<std::string, const VarianceClockManifestEvidence*>;
            static_assert(std::is_nothrow_move_constructible<VarianceClockBundleWarning>::value,
                          "warning vector growth must not copy warning payloads");

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
                const std::vector<VarianceClockProfileInput>* profiles;
                std::vector<VarianceClockBundleWarning>& warnings;
                VarianceClockLoadBudget::Reservation& storageCharge;
            };

            void checkSession(StreamContext& context,
                              const VarianceClockSessionSegmentRow& row) {
                const auto& item = requireEvidence(context.evidence, row.sourceEvidenceId(),
                                                   "dangling session evidence ID");
                requireRole(item, "calendar_source", "session segment");
                context.used.insert(row.sourceEvidenceId());
            }

            void checkSlots(StreamContext& context, const VarianceClockSlotEvidenceRow& row) {
                const auto& evidenceIds = row.evidenceIds;
                const auto& method = row.estimationMethod();
                const auto& fallbackId = row.fallbackId();
                const auto& warningCode = row.warningCodes();
                QL_REQUIRE(!evidenceIds.empty(), "missing slot evidence");
                bool hasPriceInput = false;
                for (const auto& id : evidenceIds) {
                    const auto& item = requireEvidence(context.evidence, id,
                                                       "missing slot evidence");
                    if (item.role == "price_input")
                        hasPriceInput = true;
                    context.used.insert(id);
                }
                if (method == "direct" || method == "pooled" || method == "zero")
                    QL_REQUIRE(hasPriceInput,
                               "slot evidence must cite at least one price_input evidence ID");
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
                const auto profile = row.profileId;
                const auto minute = row.minuteOfDay;
                QL_REQUIRE(minute < 1440 && minute % 5 == 0,
                           "invalid warning slot minute");
                const auto profileInput = std::find_if(
                    context.profiles->begin(), context.profiles->end(),
                    [profile](const auto& value) { return value.id == profile; });
                QL_REQUIRE(profileInput != context.profiles->end(),
                           "orphan profile slot evidence");
                std::vector<VarianceClockBundleWarningCode> expectedWarnings;
                if (method == "zero") {
                    QL_REQUIRE(profileInput->slots[minute / 5].weight == 0.0,
                               "zero slot does not have zero rate");
                    expectedWarnings.emplace_back(VarianceClockBundleWarningCode::ZeroRateSlot);
                }
                if (method == "fallback" &&
                    (row.targetReturnCount() == "unknown" ||
                     row.targetDistinctLocalDateCount() == "unknown"))
                    expectedWarnings.emplace_back(
                        VarianceClockBundleWarningCode::UnknownCountFallback);
                QL_REQUIRE(warningCode.empty() ||
                               warningCode == toString(VarianceClockBundleWarningCode::ZeroRateSlot) ||
                               warningCode ==
                                   toString(VarianceClockBundleWarningCode::UnknownCountFallback),
                           "unknown slot warning code");
                const std::string_view expectedCode = expectedWarnings.empty()
                                                          ? std::string_view()
                                                          : toString(expectedWarnings.front());
                QL_REQUIRE(warningCode == expectedCode,
                           "slot warning codes differ from derived set");
                if (!expectedCode.empty()) {
                    // A valid bundle's manifest lists exactly the derived warnings, so more
                    // derived warnings than manifest entries can never validate. Rejecting
                    // here bounds the vector by the (4 MiB capped) manifest rather than by the
                    // CSV row count.
                    QL_REQUIRE(context.warnings.size() < context.manifest.warnings.size(),
                               "manifest warnings differ from derived warnings");
                    std::string target = row.targetGroupId();
                    auto ids = evidenceIds;
                    std::sort(ids.begin(), ids.end());
                    ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
                    QL_REQUIRE(ids.capacity() <=
                                   std::numeric_limits<std::size_t>::max() /
                                       sizeof(std::string),
                               "variance-clock warning accounting overflow");
                    std::size_t bytes = ids.capacity() * sizeof(std::string);
                    for (const auto& id : ids) {
                        QL_REQUIRE(id.capacity() <=
                                       std::numeric_limits<std::size_t>::max() - bytes,
                                   "variance-clock warning accounting overflow");
                        bytes += id.capacity();
                    }
                    QL_REQUIRE(target.capacity() <=
                                   std::numeric_limits<std::size_t>::max() - bytes,
                               "variance-clock warning accounting overflow");
                    bytes += target.capacity();
                    const auto previousCharge = context.storageCharge.bytes();
                    if (context.warnings.size() == context.warnings.capacity()) {
                        QL_REQUIRE(context.warnings.capacity() <
                                       std::numeric_limits<std::size_t>::max(),
                                   "variance-clock warning accounting overflow");
                        const auto oldCapacity = context.warnings.capacity();
                        QL_REQUIRE(oldCapacity <=
                                       std::numeric_limits<std::size_t>::max() /
                                           sizeof(VarianceClockBundleWarning),
                                   "variance-clock warning accounting overflow");
                        const auto oldBufferBytes =
                            oldCapacity * sizeof(VarianceClockBundleWarning);
                        QL_REQUIRE(previousCharge >= oldBufferBytes,
                                   "variance-clock warning budget mismatch");
                        // Grow geometrically, never past the manifest count. Growing by one
                        // element per warning reallocates and moves the whole vector every
                        // time, which is quadratic in the number of warnings.
                        const auto manifestCount = context.manifest.warnings.size();
                        const auto requestedCapacity =
                            oldCapacity >= manifestCount / 2
                                ? manifestCount
                                : std::max<std::size_t>(2 * oldCapacity, 1);
                        QL_REQUIRE(requestedCapacity <=
                                       std::numeric_limits<std::size_t>::max() /
                                           sizeof(VarianceClockBundleWarning),
                                   "variance-clock warning accounting overflow");
                        const auto requestedBytes =
                            requestedCapacity * sizeof(VarianceClockBundleWarning);
                        QL_REQUIRE(requestedBytes <=
                                       std::numeric_limits<std::size_t>::max() / 2,
                                   "variance-clock warning accounting overflow");
                        const auto nonBufferCharge = previousCharge - oldBufferBytes;
                        QL_REQUIRE(bytes <= std::numeric_limits<std::size_t>::max() -
                                                nonBufferCharge &&
                                       oldBufferBytes <= std::numeric_limits<std::size_t>::max() -
                                                             nonBufferCharge - bytes &&
                                       2 * requestedBytes <=
                                           std::numeric_limits<std::size_t>::max() -
                                               nonBufferCharge - bytes - oldBufferBytes,
                                   "variance-clock warning accounting overflow");
                        context.storageCharge.resize(nonBufferCharge + bytes +
                                                     oldBufferBytes + 2 * requestedBytes);
                        try {
                            context.warnings.reserve(requestedCapacity);
                        } catch (...) {
                            context.storageCharge.resize(previousCharge);
                            throw;
                        }
                        QL_REQUIRE(context.warnings.capacity() <=
                                       std::numeric_limits<std::size_t>::max() /
                                           sizeof(VarianceClockBundleWarning),
                                   "variance-clock warning accounting overflow");
                        const auto actualBufferBytes =
                            context.warnings.capacity() * sizeof(VarianceClockBundleWarning);
                        QL_REQUIRE(actualBufferBytes <=
                                       std::numeric_limits<std::size_t>::max() -
                                           nonBufferCharge - bytes,
                                   "variance-clock warning accounting overflow");
                        // std::vector::reserve may allocate more than requested. Reconcile
                        // the retained charge after allocation; the 2x pre-charge is
                        // conservative in practice, but the standard does not cap this
                        // implementation-chosen capacity multiplier.
                        context.storageCharge.resize(nonBufferCharge + bytes +
                                                     actualBufferBytes);
                    } else {
                        QL_REQUIRE(bytes <= std::numeric_limits<std::size_t>::max() -
                                                previousCharge,
                                   "variance-clock warning accounting overflow");
                        context.storageCharge.resize(previousCharge + bytes);
                    }
                    context.warnings.push_back(
                        {expectedWarnings.front(), VarianceClockBundleWarningSeverity::Warning,
                         profile, std::move(target),
                         static_cast<std::uint16_t>(minute), std::move(ids)});
                }
            }

        } // namespace

        VarianceClockBundleEvidenceContext::VarianceClockBundleEvidenceContext(
            const VarianceClockManifest& manifest,
            VarianceClockLoadMode mode,
            VarianceClockLoadBudget& budget)
        : manifest_(manifest), mode_(mode), budget_(budget), evidenceCharge_(budget.reserve(0)) {
            QL_REQUIRE(mode_ == VarianceClockLoadMode::Strict ||
                           mode_ == VarianceClockLoadMode::Reconstruction,
                       "invalid variance-clock load mode");
            QL_REQUIRE(manifest_.evidence.size() <= 4000,
                       "evidence record limit (4,000) exceeded");
            constexpr std::size_t perEvidence = 512;
            QL_REQUIRE(manifest_.evidence.size() <=
                           std::numeric_limits<std::size_t>::max() / perEvidence,
                       "variance-clock evidence accounting overflow");

            const auto& generatedAt = manifest_.generatedAtUtc;
            const auto& coverageEnd = manifest_.coverageEndUtc;
            const auto& priceCutoff = manifest_.priceCutoffUtc;
            const auto& calendarAsOf = manifest_.calendarAsOfUtc;
            const auto& timezoneAsOf = manifest_.timezoneAsOfUtc;
            QL_REQUIRE(manifest_.coverageStartUtc == manifest_.clockOriginUtc,
                       "clock_origin_utc must equal coverage_start_utc");
            QL_REQUIRE(mode_ != VarianceClockLoadMode::Strict || generatedAt < coverageEnd,
                       "Strict generated_at_utc must be before coverage_end_utc");
            QL_REQUIRE(priceCutoff <= generatedAt, "price cutoff is after generated_at_utc");
            QL_REQUIRE(calendarAsOf <= generatedAt, "calendar as-of is after generated_at_utc");
            QL_REQUIRE(timezoneAsOf <= generatedAt, "timezone as-of is after generated_at_utc");

            evidenceCharge_.resize(manifest_.evidence.size() * perEvidence);
            for (const auto& item : manifest_.evidence) {
                QL_REQUIRE(evidence_.emplace(item.evidenceId, &item).second,
                           "duplicate evidence ID");
                QL_REQUIRE(item.contentSha256 || item.attestationRef,
                           "evidence without content_sha256 requires attestation_ref");
                QL_REQUIRE(item.availableAtUtc <= generatedAt,
                           "evidence is available after generated_at_utc");
                if (latestAvailability_ < item.availableAtUtc)
                    latestAvailability_ = item.availableAtUtc;
            }

            VarianceClockInstant latestCalendar;
            for (const auto& id : manifest_.calendarEvidenceIds) {
                const auto& item =
                    requireEvidence(evidence_, id, "dangling calendar evidence ID");
                requireRole(item, "calendar_source", "calendar evidence");
                used_.insert(id);
                if (latestCalendar < item.availableAtUtc)
                    latestCalendar = item.availableAtUtc;
            }
            QL_REQUIRE(!manifest_.calendarEvidenceIds.empty(), "empty calendar evidence IDs");
            QL_REQUIRE(latestCalendar <= calendarAsOf,
                       "calendar as-of precedes cited evidence");

            VarianceClockInstant latestTimezone;
            for (const auto& id : manifest_.timezoneEvidenceIds) {
                const auto& item =
                    requireEvidence(evidence_, id, "dangling timezone evidence ID");
                requireRole(item, "timezone_rules", "timezone evidence");
                used_.insert(id);
                if (latestTimezone < item.availableAtUtc)
                    latestTimezone = item.availableAtUtc;
            }
            QL_REQUIRE(!manifest_.timezoneEvidenceIds.empty(), "empty timezone evidence IDs");
            QL_REQUIRE(latestTimezone <= timezoneAsOf,
                       "timezone as-of precedes cited evidence");

            for (const auto& approval : manifest_.fallbackApprovals) {
                QL_REQUIRE(!approval.fallbackId.empty(), "empty fallback approval ID");
                for (const auto& id : approval.approvalEvidenceIds) {
                    const auto& item =
                        requireEvidence(evidence_, id, "dangling fallback approval evidence ID");
                    requireRole(item, "fallback_approval", "fallback approval");
                    used_.insert(id);
                }
                for (const auto& id : approval.sourceEvidenceIds) {
                    const auto& item =
                        requireEvidence(evidence_, id, "dangling fallback source evidence ID");
                    QL_REQUIRE(item.role != "fallback_approval",
                               "fallback source evidence has fallback_approval role");
                    used_.insert(id);
                }
            }
            if (manifest_.continuousFuturesLineage) {
                for (const auto* ids : {
                         &manifest_.continuousFuturesLineage->rollScheduleEvidenceIds,
                         &manifest_.continuousFuturesLineage->contractMappingEvidenceIds}) {
                    for (const auto& id : *ids) {
                        const auto& item = requireEvidence(
                            evidence_, id, "dangling continuous-futures evidence ID");
                        requireRole(item, "continuous_roll_mapping",
                                    "continuous-futures lineage");
                        used_.insert(id);
                    }
                }
            }
        }

        void VarianceClockBundleEvidenceContext::attachStorageCharge(
            VarianceClockLoadBudget::Reservation& charge) noexcept {
            storageCharge_ = &charge;
        }

        void VarianceClockBundleEvidenceContext::validateProfileCalibrations(
            std::vector<VarianceClockProfileInput>& profiles) {
            for (const auto& calibration : manifest_.profileCalibrations) {
                QL_REQUIRE(!calibration.evidenceIds.empty(),
                           "profile calibration has no evidence");
                VarianceClockInstant calibrationEvidence;
                for (const auto& id : calibration.evidenceIds) {
                    const auto& item = requireEvidence(
                        evidence_, id, "dangling profile calibration evidence ID");
                    requireRole(item, "price_input", "profile calibration");
                    used_.insert(id);
                    if (calibrationEvidence < item.availableAtUtc)
                        calibrationEvidence = item.availableAtUtc;
                }
                QL_REQUIRE(calibrationEvidence <= calibration.calibrationAsOfUtc,
                           "calibration precedes cited evidence");
                QL_REQUIRE(calibration.calibrationAsOfUtc <= manifest_.priceCutoffUtc,
                           "calibration is after price cutoff");
                const auto profile = std::find_if(
                    profiles.begin(), profiles.end(),
                    [&calibration](const auto& value) {
                        return value.id == calibration.profileId;
                    });
                QL_REQUIRE(profile != profiles.end(), "orphan profile calibration");
                profile->calibrationAsOf = calibration.calibrationAsOfUtc;
            }
        }

        void VarianceClockBundleEvidenceContext::validateSessionRow(
            const VarianceClockSessionSegmentRow& row) {
            QL_REQUIRE(storageCharge_, "variance-clock evidence storage charge is not attached");
            StreamContext context{manifest_, evidence_, used_, nullptr, warnings_,
                                  *storageCharge_};
            checkSession(context, row);
        }

        void VarianceClockBundleEvidenceContext::validateSlotRow(
            const VarianceClockSlotEvidenceRow& row,
            const std::vector<VarianceClockProfileInput>& profiles) {
            QL_REQUIRE(storageCharge_, "variance-clock evidence storage charge is not attached");
            StreamContext context{manifest_, evidence_, used_, &profiles, warnings_,
                                  *storageCharge_};
            checkSlots(context, row);
        }

        VarianceClockValidatedBundle
        VarianceClockBundleEvidenceContext::finish(ParsedVarianceClockTables&& parsed) {
            QL_REQUIRE(storageCharge_, "variance-clock evidence storage charge is not attached");
            QL_ENSURE(budget_.used() >= parsed.storageCharge.bytes(),
                     "variance-clock evidence load budget mismatch");
            const auto& manifest = manifest_;
            const auto& generatedAt = manifest_.generatedAtUtc;
            const auto& latestAvailability = latestAvailability_;
            auto& warnings = warnings_;
            auto& used = used_;
            auto& budget = budget_;
            const auto warningOrder = [](const auto& left, const auto& right) {
                return std::tie(left.code, left.profileId, left.targetGroupId,
                                left.minuteOfDay, left.evidenceIds) <
                       std::tie(right.code, right.profileId, right.targetGroupId,
                                right.minuteOfDay, right.evidenceIds);
            };
            std::sort(warnings.begin(), warnings.end(), warningOrder);
            auto manifestWarningCharge = budget.reserve(0);
            std::vector<const VarianceClockManifestWarning*> manifestWarnings;
            if (!manifest.warnings.empty()) {
                QL_REQUIRE(manifest.warnings.size() <=
                               std::numeric_limits<std::size_t>::max() /
                                   sizeof(const VarianceClockManifestWarning*),
                           "variance-clock warning accounting overflow");
                const auto requestedBytes =
                    manifest.warnings.size() * sizeof(const VarianceClockManifestWarning*);
                QL_REQUIRE(requestedBytes <= std::numeric_limits<std::size_t>::max() / 2,
                           "variance-clock warning accounting overflow");
                manifestWarningCharge.resize(2 * requestedBytes);
                try {
                    manifestWarnings.reserve(manifest.warnings.size());
                } catch (...) {
                    manifestWarningCharge.release();
                    throw;
                }
                QL_REQUIRE(manifestWarnings.capacity() <=
                               std::numeric_limits<std::size_t>::max() /
                                   sizeof(const VarianceClockManifestWarning*),
                           "variance-clock warning accounting overflow");
                const auto actualBytes =
                    manifestWarnings.capacity() * sizeof(const VarianceClockManifestWarning*);
                manifestWarningCharge.resize(actualBytes);
                for (const auto& warning : manifest.warnings)
                    manifestWarnings.push_back(&warning);
            }
            std::sort(manifestWarnings.begin(), manifestWarnings.end(),
                      [](const auto* left, const auto* right) {
                          return std::tie(left->code, left->profileId, left->targetGroupId,
                                          left->minuteOfDay, left->evidenceIds) <
                                 std::tie(right->code, right->profileId, right->targetGroupId,
                                          right->minuteOfDay, right->evidenceIds);
                      });
            QL_REQUIRE(warnings.size() == manifestWarnings.size(),
                       "manifest warnings differ from derived warnings");
            for (std::size_t i = 0; i < warnings.size(); ++i) {
                const auto& derived = warnings[i];
                const auto& supplied = *manifestWarnings[i];
                QL_REQUIRE(supplied.severity == VarianceClockBundleWarningSeverity::Warning &&
                               supplied.code == derived.code &&
                               supplied.profileId == derived.profileId &&
                               supplied.targetGroupId == derived.targetGroupId &&
                               supplied.minuteOfDay == derived.minuteOfDay &&
                               supplied.evidenceIds == derived.evidenceIds,
                           "manifest warnings differ from derived warnings");
            }
            for (const auto& item : manifest.evidence)
                QL_REQUIRE(used.count(item.evidenceId) != 0, "orphan evidence");

            std::size_t retainedWarningBytes = 0;
            QL_REQUIRE(warnings.capacity() <=
                           std::numeric_limits<std::size_t>::max() /
                               sizeof(VarianceClockBundleWarning),
                       "variance-clock warning accounting overflow");
            retainedWarningBytes =
                warnings.capacity() * sizeof(VarianceClockBundleWarning);
            for (const auto& warning : warnings) {
                QL_REQUIRE(warning.evidenceIds.capacity() <=
                               std::numeric_limits<std::size_t>::max() /
                                   sizeof(std::string),
                           "variance-clock warning accounting overflow");
                const auto idVectorBytes =
                    warning.evidenceIds.capacity() * sizeof(std::string);
                QL_REQUIRE(idVectorBytes <=
                               std::numeric_limits<std::size_t>::max() -
                                   retainedWarningBytes,
                           "variance-clock warning accounting overflow");
                retainedWarningBytes += idVectorBytes;
                QL_REQUIRE(warning.targetGroupId.capacity() <=
                               std::numeric_limits<std::size_t>::max() -
                                   retainedWarningBytes,
                           "variance-clock warning accounting overflow");
                retainedWarningBytes += warning.targetGroupId.capacity();
                for (const auto& id : warning.evidenceIds) {
                    QL_REQUIRE(id.capacity() <=
                                   std::numeric_limits<std::size_t>::max() -
                                       retainedWarningBytes,
                               "variance-clock warning accounting overflow");
                    retainedWarningBytes += id.capacity();
                }
            }
            const std::size_t retainedTables =
                parsed.profiles.capacity() * sizeof(VarianceClockProfileInput) +
                parsed.dates.capacity() * sizeof(VarianceClockDateInput) +
                parsed.offsets.capacity() * sizeof(VarianceClockOffsetInput);
            QL_REQUIRE(retainedWarningBytes <=
                           std::numeric_limits<std::size_t>::max() - retainedTables,
                       "variance-clock warning accounting overflow");
            parsed.storageCharge.resize(retainedTables + retainedWarningBytes);

            VarianceClockValidatedBundle result;
            result.tables.start = parsed.start;
            result.tables.end = parsed.end;
            result.tables.availableFrom =
                mode_ == VarianceClockLoadMode::Strict ? generatedAt : latestAvailability;
            result.tables.profiles = std::move(parsed.profiles);
            result.tables.dates = std::move(parsed.dates);
            result.tables.offsets = std::move(parsed.offsets);
            result.provenance.snapshotId = manifest.snapshotId;
            result.provenance.availableFrom = result.tables.availableFrom;
            result.provenance.mode = mode_;
            result.provenance.reconstructed = mode_ == VarianceClockLoadMode::Reconstruction;
            result.warnings = std::move(warnings);
            result.storageCharge = std::move(parsed.storageCharge);
            evidence_.clear();
            used_.clear();
            evidenceCharge_.release();
            storageCharge_ = nullptr;
            return result;
        }

    }
}
