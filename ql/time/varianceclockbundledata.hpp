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

/*! \file varianceclockbundledata.hpp
    \brief internal variance-clock bundle data parsing and load budget
*/

#ifndef quantlib_variance_clock_bundle_data_hpp
#define quantlib_variance_clock_bundle_data_hpp

#include <ql/time/varianceclockmanifest.hpp>
#include <ql/time/varianceclockbundletypes.hpp>
#include <ql/time/varianceclocktables.hpp>
#include <ql/time/varianceclockcsv.hpp>
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace QuantLib {
    namespace detail {

        class VarianceClockLoadBudget {
          public:
            static constexpr std::size_t defaultLimit = 256U * 1024U * 1024U;

            class Reservation {
              public:
                Reservation() noexcept = default;
                Reservation(const Reservation&) = delete;
                Reservation& operator=(const Reservation&) = delete;
                Reservation(Reservation&& other) noexcept;
                Reservation& operator=(Reservation&& other) noexcept;
                ~Reservation();

                std::size_t bytes() const noexcept;
                void resize(std::size_t bytes);
                void release() noexcept;

              private:
                friend class VarianceClockLoadBudget;
                Reservation(VarianceClockLoadBudget* budget, std::size_t bytes) noexcept;

                VarianceClockLoadBudget* budget_ = nullptr;
                std::size_t bytes_ = 0;
            };

            explicit VarianceClockLoadBudget(std::size_t limit = defaultLimit);
            VarianceClockLoadBudget(const VarianceClockLoadBudget&) = delete;
            VarianceClockLoadBudget& operator=(const VarianceClockLoadBudget&) = delete;
            VarianceClockLoadBudget(VarianceClockLoadBudget&&) = delete;
            VarianceClockLoadBudget& operator=(VarianceClockLoadBudget&&) = delete;
            Reservation reserve(std::size_t bytes);
            std::size_t limit() const noexcept;
            std::size_t used() const noexcept;
            std::size_t remaining() const noexcept;
            const VarianceClockBundleScanCounts& scanCounts() const noexcept;
            VarianceClockBundleScanCounts& scanCounts() noexcept;
          private:
            void increase(std::size_t bytes);
            void decrease(std::size_t bytes) noexcept;

            std::size_t limit_;
            std::size_t used_ = 0;
            VarianceClockBundleScanCounts scanCounts_;
        };

        struct VarianceClockBundleCsvBytes {
            std::string_view profiles;
            std::string_view marketDays;
            std::string_view sessionSegments;
            std::string_view timezoneMapping;
            std::string_view slotEvidence;
        };

        class VarianceClockBundleEvidenceContext;

        struct VarianceClockSessionSegmentRow {
            std::array<std::string, VarianceClockSessionSegmentsCsv::columnCount> fields;
            Date localDate;
            VarianceClockInstant start;
            VarianceClockInstant end;

            const std::string& localDateText() const noexcept {
                return fields[VarianceClockSessionSegmentsCsv::localDate];
            }
            const std::string& sourceEvidenceId() const noexcept {
                return fields[VarianceClockSessionSegmentsCsv::sourceEvidenceId];
            }
        };

        struct VarianceClockSlotEvidenceRow {
            std::array<std::string, VarianceClockSlotEvidenceCsv::columnCount> fields;
            std::uint32_t profileId = 0;
            std::uint16_t minuteOfDay = 0;
            std::vector<std::string> evidenceIds;

            const std::string& targetGroupId() const noexcept {
                return fields[VarianceClockSlotEvidenceCsv::targetGroupId];
            }
            const std::string& targetReturnCount() const noexcept {
                return fields[VarianceClockSlotEvidenceCsv::targetReturnCount];
            }
            const std::string& targetDistinctLocalDateCount() const noexcept {
                return fields[VarianceClockSlotEvidenceCsv::targetDistinctLocalDateCount];
            }
            const std::string& estimationMethod() const noexcept {
                return fields[VarianceClockSlotEvidenceCsv::estimationMethod];
            }
            const std::string& fallbackId() const noexcept {
                return fields[VarianceClockSlotEvidenceCsv::fallbackId];
            }
            const std::string& warningCodes() const noexcept {
                return fields[VarianceClockSlotEvidenceCsv::warningCodes];
            }
        };

        struct ParsedVarianceClockTables {
            ParsedVarianceClockTables() = default;
            ParsedVarianceClockTables(const ParsedVarianceClockTables&) = delete;
            ParsedVarianceClockTables& operator=(const ParsedVarianceClockTables&) = delete;
            ParsedVarianceClockTables(ParsedVarianceClockTables&&) noexcept = default;
            ParsedVarianceClockTables& operator=(ParsedVarianceClockTables&& other) noexcept;

            // The budget must outlive this result; release the charge after its
            // vectors have destroyed their accounted capacity.
            VarianceClockLoadBudget::Reservation storageCharge;
            VarianceClockInstant start;
            VarianceClockInstant end;
            std::vector<VarianceClockProfileInput> profiles;
            std::vector<VarianceClockDateInput> dates;
            std::vector<VarianceClockOffsetInput> offsets;
        };

        VarianceClockInstant parseVarianceClockInstant(std::string_view text);

        ParsedVarianceClockTables parseVarianceClockBundleData(
            const VarianceClockManifest& manifest,
            const VarianceClockBundleCsvBytes& csv,
            VarianceClockLoadBudget& budget,
            VarianceClockBundleEvidenceContext* evidence = nullptr);

    }
}

#endif
