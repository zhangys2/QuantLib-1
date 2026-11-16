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
#include <ql/time/varianceclockdetail.hpp>
#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <utility>

namespace QuantLib {

    namespace {

        constexpr std::int64_t secondsPerDay = 86400;
        constexpr std::int64_t secondsPerSlot = 300;
        constexpr std::int64_t nanosecondsPerSecond = 1000000000;

        bool before(const VarianceClockInstant& lhs, const VarianceClockInstant& rhs) {
            return lhs.unixSeconds() < rhs.unixSeconds() ||
                   (lhs.unixSeconds() == rhs.unixSeconds() &&
                    lhs.nanosecond() < rhs.nanosecond());
        }

        VarianceClockInstant wholeSecond(std::int64_t seconds) {
            VarianceClockInstant result;
            QL_ENSURE(VarianceClockInstant::tryCreate(seconds, 0, result),
                      "invalid computed variance-clock instant");
            return result;
        }

        std::int64_t shiftedSeconds(std::int64_t seconds, std::int32_t offset) {
            const auto shift = static_cast<std::int64_t>(offset);
            QL_REQUIRE((shift <= 0 || seconds <= std::numeric_limits<std::int64_t>::max() - shift) &&
                           (shift >= 0 || seconds >= std::numeric_limits<std::int64_t>::min() - shift),
                       "variance-clock UTC offset overflows");
            return seconds + shift;
        }

        std::int64_t secondOfDay(std::int64_t localSeconds) {
            auto result = localSeconds % secondsPerDay;
            if (result < 0)
                result += secondsPerDay;
            return result;
        }

        Date localDate(std::int64_t localSeconds) {
            auto days = localSeconds / secondsPerDay;
            if (localSeconds % secondsPerDay < 0)
                --days;

            const auto epoch = static_cast<std::int64_t>(Date(1, January, 1970).serialNumber());
            const auto minimum = static_cast<std::int64_t>(Date::minDate().serialNumber()) - epoch;
            const auto maximum = static_cast<std::int64_t>(Date::maxDate().serialNumber()) - epoch;
            QL_REQUIRE(days >= minimum && days <= maximum,
                       "variance-clock local date is outside the QuantLib date range");
            return Date(static_cast<Date::serial_type>(epoch + days));
        }

        VarianceClockInstant nextBoundary(const VarianceClockInstant& instant,
                                          std::int64_t secondsToBoundary) {
            QL_REQUIRE(instant.unixSeconds() <=
                           std::numeric_limits<std::int64_t>::max() - secondsToBoundary,
                       "variance-clock boundary overflows");
            return wholeSecond(instant.unixSeconds() + secondsToBoundary);
        }

        const VarianceClockProfileInput&
        findProfile(const std::vector<VarianceClockProfileInput>& profiles,
                    VarianceClockProfileId id) {
            const auto it = std::lower_bound(
                profiles.begin(), profiles.end(), id,
                [](const VarianceClockProfileInput& profile, VarianceClockProfileId value) {
                    return profile.id < value;
                });
            QL_REQUIRE(it != profiles.end() && it->id == id,
                       "variance-clock date references a missing profile");
            return *it;
        }

        double validateTables(VarianceClockTables& tables) {
            QL_REQUIRE(tables.start.isValid() && tables.end.isValid() && tables.availableFrom.isValid(),
                       "variance-clock coverage or availability is invalid");
            QL_REQUIRE(!before(tables.end, tables.start), "variance-clock coverage is reversed");

            double maximumWeight = 0.0;
            for (const auto& profile : tables.profiles) {
                QL_REQUIRE(profile.calibrationAsOf.isValid(),
                           "variance-clock calibration instant is invalid");
                for (const auto& slot : profile.slots) {
                    QL_REQUIRE(std::isfinite(slot.weight) && slot.weight >= 0.0,
                               "variance-clock weights must be finite and nonnegative");
                    maximumWeight = std::max(maximumWeight, slot.weight);
                }
            }
            std::sort(tables.profiles.begin(), tables.profiles.end(),
                      [](const VarianceClockProfileInput& lhs, const VarianceClockProfileInput& rhs) {
                          return lhs.id < rhs.id;
                      });
            for (Size i = 1; i < tables.profiles.size(); ++i)
                QL_REQUIRE(tables.profiles[i - 1].id != tables.profiles[i].id,
                           "duplicate variance-clock profile");

            for (const auto& entry : tables.dates) {
                QL_REQUIRE(entry.localDate != Date(), "variance-clock local date is null");
#ifdef QL_HIGH_RESOLUTION_DATE
                QL_REQUIRE(entry.localDate ==
                               Date(entry.localDate.dayOfMonth(), entry.localDate.month(),
                                    entry.localDate.year()),
                           "variance-clock local date contains a time");
#endif
                findProfile(tables.profiles, entry.profile);
            }
            std::sort(tables.dates.begin(), tables.dates.end(),
                      [](const VarianceClockDateInput& lhs, const VarianceClockDateInput& rhs) {
                          return lhs.localDate < rhs.localDate;
                      });
            for (Size i = 1; i < tables.dates.size(); ++i)
                QL_REQUIRE(tables.dates[i - 1].localDate != tables.dates[i].localDate,
                           "duplicate variance-clock local date");

            for (const auto& offset : tables.offsets) {
                QL_REQUIRE(offset.start.isValid() && offset.end.isValid() &&
                               before(offset.start, offset.end),
                           "invalid variance-clock offset interval");
                QL_REQUIRE(offset.offsetSeconds % secondsPerSlot == 0,
                           "variance-clock offsets must be multiples of 300 seconds");
            }
            std::sort(tables.offsets.begin(), tables.offsets.end(),
                      [](const VarianceClockOffsetInput& lhs, const VarianceClockOffsetInput& rhs) {
                          return before(lhs.start, rhs.start);
                      });
            for (Size i = 1; i < tables.offsets.size(); ++i)
                QL_REQUIRE(!before(tables.offsets[i].start, tables.offsets[i - 1].end),
                           "overlapping variance-clock offset intervals");
            return maximumWeight;
        }

        constexpr unsigned int sumBits =
            std::numeric_limits<double>::max_exponent -
            std::numeric_limits<double>::min_exponent + std::numeric_limits<double>::digits + 64;
        using SumBackend = boost::multiprecision::cpp_int_backend<
            sumBits, sumBits, boost::multiprecision::unsigned_magnitude,
            boost::multiprecision::unchecked, void>;
        using ScaledSum =
            boost::multiprecision::number<SumBackend, boost::multiprecision::et_off>;

        ScaledSum scaledWeight(double weight) {
            static_assert(std::numeric_limits<double>::radix == 2 &&
                              std::numeric_limits<double>::digits <= 64,
                          "variance-clock weight validation requires binary double");
            if (weight == 0.0)
                return 0;
            constexpr int digits = std::numeric_limits<double>::digits;
            constexpr int scale = std::numeric_limits<double>::min_exponent - digits;
            int exponent = 0;
            const auto fraction = std::frexp(weight, &exponent);
            auto significand = static_cast<std::uint64_t>(std::ldexp(fraction, digits));
            const int shift = exponent - digits - scale;
            if (shift < 0)
                significand >>= -shift;
            ScaledSum result(significand);
            if (shift > 0)
                result <<= shift;
            return result;
        }

        void validateFiniteSum(const VarianceClockTables& tables,
                               const std::vector<detail::VarianceClockRun>& runs,
                               double maximumWeight) {
            if (runs.empty() || maximumWeight == 0.0)
                return;

            const long double seconds =
                static_cast<long double>(tables.end.unixSeconds()) -
                static_cast<long double>(tables.start.unixSeconds()) +
                (static_cast<long double>(tables.end.nanosecond()) -
                 static_cast<long double>(tables.start.nanosecond())) /
                    nanosecondsPerSecond;
            const long double days = seconds / secondsPerDay;
            if (days <= (static_cast<long double>(std::numeric_limits<double>::max()) / 2) /
                            maximumWeight)
                return;

            // The usual bound is inconclusive only for extreme rates; compare those sums exactly.
            auto maximum = scaledWeight(std::numeric_limits<double>::max());
            maximum *= secondsPerDay * nanosecondsPerSecond;
            ScaledSum total = 0;
            for (const auto& run : runs) {
                const auto& profile = findProfile(tables.profiles, run.profile);
                auto cursor = run.start;
                while (before(cursor, run.end)) {
                    const auto local = shiftedSeconds(cursor.unixSeconds(), run.offsetSeconds);
                    const auto withinDay = secondOfDay(local);
                    const auto boundary = nextBoundary(cursor, secondsPerSlot - withinDay % secondsPerSlot);
                    const auto end = before(boundary, run.end) ? boundary : run.end;
                    const auto duration =
                        (end.unixSeconds() - cursor.unixSeconds()) * nanosecondsPerSecond +
                        static_cast<std::int64_t>(end.nanosecond()) -
                        static_cast<std::int64_t>(cursor.nanosecond());
                    auto contribution = scaledWeight(profile.slots[withinDay / secondsPerSlot].weight);
                    contribution *= static_cast<std::uint64_t>(duration);
                    total += contribution;
                    QL_REQUIRE(total <= maximum, "variance-clock weighted sum overflows");
                    cursor = end;
                }
            }
        }

    }

    namespace detail {

        std::vector<VarianceClockRun> buildVarianceClockRuns(VarianceClockTables& tables) {
            const auto maximumWeight = validateTables(tables);
            std::vector<VarianceClockRun> runs;
            runs.reserve(tables.dates.size() + tables.offsets.size());

            auto cursor = tables.start;
            Size offsetIndex = 0;
            while (offsetIndex < tables.offsets.size() &&
                   !before(cursor, tables.offsets[offsetIndex].end))
                ++offsetIndex;

            while (before(cursor, tables.end)) {
                QL_REQUIRE(offsetIndex < tables.offsets.size(),
                           "variance-clock offset coverage is incomplete");
                const auto& offset = tables.offsets[offsetIndex];
                QL_REQUIRE(!before(cursor, offset.start),
                           "variance-clock offset coverage contains a gap");

                const auto local = shiftedSeconds(cursor.unixSeconds(), offset.offsetSeconds);
                const auto date = localDate(local);
                const auto dateIt = std::lower_bound(
                    tables.dates.begin(), tables.dates.end(), date,
                    [](const VarianceClockDateInput& entry, const Date& value) {
                        return entry.localDate < value;
                    });
                QL_REQUIRE(dateIt != tables.dates.end() && dateIt->localDate == date,
                           "variance-clock local date is not covered");

                auto end = before(offset.end, tables.end) ? offset.end : tables.end;
                const auto midnight = nextBoundary(cursor, secondsPerDay - secondOfDay(local));
                if (before(midnight, end))
                    end = midnight;

                runs.push_back({cursor, end, date, dateIt->profile, offset.offsetSeconds, offset.fold});
                cursor = end;
                if (!before(cursor, offset.end))
                    ++offsetIndex;
            }

            validateFiniteSum(tables, runs, maximumWeight);
            return runs;
        }

    }

    struct VarianceClockSnapshot::Impl {
        Impl(VarianceClockTables&& input, std::vector<detail::VarianceClockRun>&& inputRuns)
        : tables(std::move(input)), runs(std::move(inputRuns)) {}

        VarianceClockTables tables;
        std::vector<detail::VarianceClockRun> runs;
    };

    VarianceClockSnapshot::VarianceClockSnapshot(std::unique_ptr<Impl> impl)
    : impl_(std::move(impl)) {}

    VarianceClockSnapshot::~VarianceClockSnapshot() = default;

    VarianceClockInstant VarianceClockSnapshot::coverageStart() const noexcept {
        return impl_->tables.start;
    }

    VarianceClockInstant VarianceClockSnapshot::coverageEnd() const noexcept {
        return impl_->tables.end;
    }

    std::unique_ptr<VarianceClockSnapshot> makeVarianceClockSnapshot(VarianceClockTables&& tables) {
        auto runs = detail::buildVarianceClockRuns(tables);
        auto impl = std::make_unique<VarianceClockSnapshot::Impl>(std::move(tables), std::move(runs));
        return std::unique_ptr<VarianceClockSnapshot>(new VarianceClockSnapshot(std::move(impl)));
    }

}
