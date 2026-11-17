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

/*! \file varianceclockbundletypes.hpp
    \brief public types for loaded variance-clock bundles
*/

#ifndef quantlib_variance_clock_bundle_types_hpp
#define quantlib_variance_clock_bundle_types_hpp

#include <ql/time/varianceclocktables.hpp>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace QuantLib {

    enum class VarianceClockLoadMode { Strict, Reconstruction };

    struct VarianceClockBundleWarning {
        std::string code;
        std::string severity;
        VarianceClockProfileId profileId;
        std::string targetGroupId;
        std::uint16_t minuteOfDay;
        std::vector<std::string> evidenceIds;
    };

    struct VarianceClockBundleProvenance {
        std::string snapshotId;
        std::vector<std::string> validatedEvidenceIds;
        VarianceClockInstant availableFrom;
        VarianceClockLoadMode mode = VarianceClockLoadMode::Strict;
        bool reconstructed = false;
    };

    struct VarianceClockLoadedBundle {
        std::unique_ptr<VarianceClockSnapshot> snapshot;
        std::vector<VarianceClockBundleWarning> warnings;
        VarianceClockBundleProvenance provenance;
    };

}

#endif
