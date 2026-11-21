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

/*! \file varianceclockmanifest.hpp
    \brief internal variance-clock bundle manifest types and JSON parser
*/

#ifndef quantlib_variance_clock_manifest_hpp
#define quantlib_variance_clock_manifest_hpp

#include <ql/time/varianceclockbundletypes.hpp>
#include <ql/time/varianceclockinstant.hpp>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace QuantLib {
    namespace detail {

        struct VarianceClockManifestCalibrationSettings {
            std::string method;
            std::uint32_t minimumDirectReturns;
            std::optional<std::uint32_t> gapPoolReturnThreshold;
            VarianceClockInstant priceCutoffUtc;
        };

        struct VarianceClockManifestProfileCalibration {
            std::uint32_t profileId;
            VarianceClockInstant calibrationAsOfUtc;
            std::vector<std::string> evidenceIds;
        };

        struct VarianceClockManifestEvidence {
            std::string evidenceId;
            std::string role;
            std::string sourceId;
            std::optional<std::string> revisionId;
            std::optional<VarianceClockInstant> publishedAtUtc;
            VarianceClockInstant availableAtUtc;
            std::optional<std::string> uri;
            std::optional<std::string> contentSha256;
            std::optional<std::string> attestationRef;
        };

        struct VarianceClockManifestFallbackApproval {
            std::string fallbackId;
            bool approved;
            std::vector<std::string> approvalEvidenceIds;
            std::vector<std::string> sourceEvidenceIds;
        };

        using VarianceClockManifestWarning = VarianceClockBundleWarning;

        struct VarianceClockManifestContinuousFuturesLineage {
            std::string constructionMethod;
            std::string sourceInstrument;
            std::string continuousSymbol;
            std::string rollRule;
            std::vector<std::string> rollScheduleEvidenceIds;
            std::vector<std::string> contractMappingEvidenceIds;
        };

        struct VarianceClockManifest {
            std::uint32_t formatVersion;
            std::string snapshotId;
            VarianceClockInstant generatedAtUtc;
            VarianceClockInstant coverageStartUtc;
            VarianceClockInstant coverageEndUtc;
            VarianceClockInstant clockOriginUtc;
            std::string marketId;
            std::string ianaZone;
            std::string referenceVariancePer5m;
            std::string referenceUnit;
            VarianceClockInstant priceCutoffUtc;
            std::string calendarVersion;
            VarianceClockInstant calendarAsOfUtc;
            std::vector<std::string> calendarEvidenceIds;
            std::string timezoneDatabase;
            std::string timezoneVersion;
            VarianceClockInstant timezoneAsOfUtc;
            std::vector<std::string> timezoneEvidenceIds;
            std::string timezoneRulesSha256;
            VarianceClockManifestCalibrationSettings calibrationSettings;
            std::vector<VarianceClockManifestProfileCalibration> profileCalibrations;
            std::vector<VarianceClockManifestEvidence> evidence;
            std::vector<VarianceClockManifestFallbackApproval> fallbackApprovals;
            std::vector<VarianceClockManifestWarning> warnings;
            std::map<std::string, std::string> files;
            std::optional<VarianceClockManifestContinuousFuturesLineage>
                continuousFuturesLineage;
        };

        VarianceClockManifest parseVarianceClockManifest(std::string_view bytes);
        std::vector<std::string> parseEvidenceIdsJson(std::string_view bytes);
        void validateVarianceClockIdentifier(std::string_view value, const char* name);

    }
}

#endif
