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

#include <ql/errors.hpp>
#include <ql/time/varianceclockbundle.hpp>
#include <ql/time/varianceclockbundlecapture.hpp>
#include <ql/time/varianceclockbundledata.hpp>
#include <ql/time/varianceclockbundleevidence.hpp>
#include <ql/time/varianceclocktables.hpp>
#include <algorithm>
#include <limits>
#include <string>

namespace QuantLib {

    namespace {

        std::size_t checkedAdd(std::size_t left, std::size_t right) {
            QL_REQUIRE(right <= std::numeric_limits<std::size_t>::max() - left,
                       "variance-clock snapshot estimate overflow");
            return left + right;
        }

        std::size_t checkedMultiply(std::size_t left, std::size_t right) {
            QL_REQUIRE(left == 0 || right <= std::numeric_limits<std::size_t>::max() / left,
                       "variance-clock snapshot estimate overflow");
            return left * right;
        }

        std::size_t snapshotEstimate(const VarianceClockTables& tables) {
            std::size_t bytes = sizeof(VarianceClockSnapshot) + 4096U;
            bytes = checkedAdd(
                bytes, checkedMultiply(tables.profiles.size(),
                                       sizeof(VarianceClockProfileInput) + 256U));
            bytes = checkedAdd(bytes, checkedMultiply(tables.dates.size(),
                                                       sizeof(VarianceClockDateInput) + 128U));
            bytes = checkedAdd(bytes, checkedMultiply(tables.offsets.size(),
                                                       sizeof(VarianceClockOffsetInput) + 128U));
            return bytes;
        }

        std::size_t resultEstimate(const detail::VarianceClockValidatedBundle& validated,
                                   const detail::VarianceClockManifest& manifest) {
            std::size_t bytes = checkedMultiply(validated.warnings.size(),
                                                sizeof(VarianceClockBundleWarning) + 256U);
            for (const auto& warning : validated.warnings)
                bytes = checkedAdd(bytes, warning.targetGroupId.capacity() + 128U);
            for (const auto& warning : validated.warnings)
                for (const auto& id : warning.evidenceIds)
                    bytes = checkedAdd(bytes, id.capacity() + 128U);
            bytes = checkedAdd(bytes, validated.provenance.snapshotId.capacity() + 128U);
            bytes = checkedAdd(bytes, checkedMultiply(manifest.evidence.size(),
                                                       sizeof(std::string) + 128U));
            for (const auto& item : manifest.evidence)
                bytes = checkedAdd(bytes, item.evidenceId.size() + 128U);
            return bytes;
        }

    }

    VarianceClockLoadedBundle loadVarianceClockBundle(
        const VarianceClockBundleSource& source,
        VarianceClockLoadMode mode) {
        detail::VarianceClockLoadBudget budget;
        auto captured = detail::captureVarianceClockBundle(source, budget);
        const auto csv = captured.csvBytes();
        detail::VarianceClockBundleEvidenceContext evidence(captured.manifest(), mode, budget);
        auto parsed =
            detail::parseVarianceClockBundleData(captured.manifest(), csv, budget, &evidence);
        auto validated = evidence.finish(std::move(parsed));

        auto resultCharge = budget.reserve(resultEstimate(validated, captured.manifest()));
        validated.provenance.validatedEvidenceIds.reserve(
            captured.manifest().evidence.size());
        for (const auto& evidence : captured.manifest().evidence)
            validated.provenance.validatedEvidenceIds.push_back(evidence.evidenceId);
        std::sort(validated.provenance.validatedEvidenceIds.begin(),
                  validated.provenance.validatedEvidenceIds.end());

        auto candidateCharge = budget.reserve(snapshotEstimate(validated.tables));
        VarianceClockLoadedBundle result;
        result.snapshot = makeVarianceClockSnapshot(std::move(validated.tables));
        result.warnings = std::move(validated.warnings);
        result.provenance = std::move(validated.provenance);
        return result;
    }

    VarianceClockLoadedBundle loadVarianceClockBundleFromDirectory(
        const std::string& nativeDirectory,
        VarianceClockLoadMode mode) {
        detail::VarianceClockDirectorySource source(nativeDirectory);
        return loadVarianceClockBundle(source, mode);
    }

}
