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

/*! \file varianceclockbundleevidence.hpp
    \brief variance-clock bundle evidence validation interface
*/

#ifndef quantlib_variance_clock_bundle_evidence_hpp
#define quantlib_variance_clock_bundle_evidence_hpp

#include <ql/time/varianceclockbundletypes.hpp>
#include <ql/time/varianceclockbundledata.hpp>
#include <ql/time/varianceclockcsv.hpp>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace QuantLib {
    namespace detail {

        struct VarianceClockValidatedBundle {
            VarianceClockTables tables;
            std::vector<VarianceClockBundleWarning> warnings;
            VarianceClockBundleProvenance provenance;
            VarianceClockLoadBudget::Reservation storageCharge;
        };

        class VarianceClockBundleEvidenceContext {
          public:
            VarianceClockBundleEvidenceContext(const VarianceClockManifest& manifest,
                                               VarianceClockLoadMode mode,
                                               VarianceClockLoadBudget& budget);
            VarianceClockBundleEvidenceContext(const VarianceClockBundleEvidenceContext&) = delete;
            VarianceClockBundleEvidenceContext& operator=(
                const VarianceClockBundleEvidenceContext&) = delete;
            VarianceClockBundleEvidenceContext(VarianceClockBundleEvidenceContext&&) = delete;
            VarianceClockBundleEvidenceContext& operator=(
                VarianceClockBundleEvidenceContext&&) = delete;

            void attachStorageCharge(VarianceClockLoadBudget::Reservation& charge) noexcept;
            void validateProfileCalibrations(
                std::vector<VarianceClockProfileInput>& profiles);
            void validateSessionRow(const VarianceClockSessionSegmentRow& row);
            void validateSlotRow(const VarianceClockSlotEvidenceRow& row,
                                 const std::vector<VarianceClockProfileInput>& profiles);
            VarianceClockValidatedBundle finish(ParsedVarianceClockTables&& parsed);

          private:
            using EvidenceMap =
                std::map<std::string, const VarianceClockManifestEvidence*>;

            const VarianceClockManifest& manifest_;
            VarianceClockLoadMode mode_;
            VarianceClockLoadBudget& budget_;
            VarianceClockLoadBudget::Reservation evidenceCharge_;
            VarianceClockLoadBudget::Reservation* storageCharge_ = nullptr;
            EvidenceMap evidence_;
            std::set<std::string> used_;
            std::vector<VarianceClockBundleWarning> warnings_;
            VarianceClockInstant latestAvailability_;
        };

    }
}

#endif
