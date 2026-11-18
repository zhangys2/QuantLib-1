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

/*! \file varianceclockbundlecapture.hpp
    \brief internal verified-byte capture representation
*/

#ifndef quantlib_variance_clock_bundle_capture_hpp
#define quantlib_variance_clock_bundle_capture_hpp

#include <ql/time/varianceclockbundledata.hpp>
#include <ql/time/varianceclockbundlesource.hpp>
#include <string_view>
#include <utility>
#include <vector>

namespace QuantLib {
    namespace detail {

        class VarianceClockCapturedBundle;

        class VarianceClockVerifiedBytes {
          public:
            VarianceClockVerifiedBytes(const VarianceClockVerifiedBytes&) = delete;
            VarianceClockVerifiedBytes& operator=(const VarianceClockVerifiedBytes&) = delete;
            VarianceClockVerifiedBytes(VarianceClockVerifiedBytes&& other) noexcept
            : charge_(std::move(other.charge_)), bytes_(std::move(other.bytes_)) {}
            VarianceClockVerifiedBytes& operator=(VarianceClockVerifiedBytes&& other) noexcept {
                if (this != &other) {
                    bytes_ = std::move(other.bytes_);
                    charge_ = std::move(other.charge_);
                }
                return *this;
            }

            std::string_view bytes() const noexcept;

          private:
            friend class VarianceClockCapturedBundle;
            friend VarianceClockCapturedBundle captureVarianceClockBundle(
                const VarianceClockBundleSource&, VarianceClockLoadBudget&);

            VarianceClockVerifiedBytes() = default;
            VarianceClockLoadBudget::Reservation charge_;
            std::vector<unsigned char> bytes_;
        };

        class VarianceClockCapturedBundle {
          public:
            VarianceClockCapturedBundle(const VarianceClockCapturedBundle&) = delete;
            VarianceClockCapturedBundle& operator=(const VarianceClockCapturedBundle&) = delete;
            VarianceClockCapturedBundle(VarianceClockCapturedBundle&&) noexcept = default;
            VarianceClockCapturedBundle& operator=(
                VarianceClockCapturedBundle&&) noexcept = default;

            const VarianceClockManifest& manifest() const noexcept;
            VarianceClockBundleCsvBytes csvBytes() const noexcept;

          private:
            friend VarianceClockCapturedBundle captureVarianceClockBundle(
                const VarianceClockBundleSource&, VarianceClockLoadBudget&);

            VarianceClockCapturedBundle() = default;

            VarianceClockManifest manifest_;
            VarianceClockVerifiedBytes profiles_;
            VarianceClockVerifiedBytes marketDays_;
            VarianceClockVerifiedBytes sessionSegments_;
            VarianceClockVerifiedBytes timezoneMapping_;
            VarianceClockVerifiedBytes slotEvidence_;
        };

        bool isVarianceClockBundleFileName(std::string_view name) noexcept;
        VarianceClockCapturedBundle captureVarianceClockBundle(
            const VarianceClockBundleSource& source,
            VarianceClockLoadBudget& budget);

    }
}

#endif
