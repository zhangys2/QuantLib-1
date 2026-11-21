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

#ifndef NDEBUG
        void assertCovered(const VarianceClockTables& tables, VarianceClockInstant time) {
            QL_ASSERT(time.isValid() && tables.start <= time && time <= tables.end,
                      "variance-clock instant outside coverage");
        }
#endif

        VarianceClockInstant wholeSecond(std::int64_t seconds) {
            VarianceClockInstant result;
            QL_ENSURE(VarianceClockInstant::tryCreate(seconds, 0, result),
                      "invalid computed variance-clock instant");
            return result;
        }

        std::int64_t shiftedSeconds(std::int64_t seconds, std::int32_t offset) {
            const auto shift = static_cast<std::int64_t>(offset);
            QL_REQUIRE((shift <= 0 ||
                        seconds <= std::numeric_limits<std::int64_t>::max() - shift) &&
                           (shift >= 0 ||
                            seconds >= std::numeric_limits<std::int64_t>::min() - shift),
                       "variance-clock UTC offset overflows");
            return seconds + shift;
        }

        std::int64_t secondOfDay(std::int64_t localSeconds) noexcept {
            auto result = localSeconds % secondsPerDay;
            if (result < 0)
                result += secondsPerDay;
            return result;
        }

        std::int64_t localSecondOfDay(VarianceClockInstant time, std::int32_t offset) noexcept {
            return secondOfDay(time.unixSeconds() % secondsPerDay + offset);
        }

        double weightedDuration(double weight,
                                VarianceClockInstant start,
                                VarianceClockInstant end) noexcept {
            const auto nanoseconds =
                (end.unixSeconds() - start.unixSeconds()) * nanosecondsPerSecond +
                static_cast<std::int64_t>(end.nanosecond()) -
                static_cast<std::int64_t>(start.nanosecond());
            return weight * (static_cast<double>(nanoseconds) /
                             (static_cast<double>(secondsPerDay) * nanosecondsPerSecond));
        }

        double indexedSum(const double* tree,
                          Size size,
                          Size begin,
                          Size end,
                          std::size_t* visitedNodes) noexcept {
            double result = 0.0;
            for (begin += size, end += size; begin < end; begin /= 2, end /= 2) {
                if (begin % 2 != 0) {
                    result += tree[begin++];
                    if (visitedNodes)
                        ++*visitedNodes;
                }
                if (end % 2 != 0) {
                    result += tree[--end];
                    if (visitedNodes)
                        ++*visitedNodes;
                }
            }
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
            QL_REQUIRE(tables.start.isValid() && tables.end.isValid() &&
                           tables.availableFrom.isValid(),
                       "variance-clock coverage or availability is invalid");
            QL_REQUIRE(tables.start < tables.end,
                       "variance-clock coverage must be nonempty and ordered");

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
                      [](const VarianceClockProfileInput& lhs,
                         const VarianceClockProfileInput& rhs) {
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
                               offset.start < offset.end,
                           "invalid variance-clock offset interval");
                QL_REQUIRE(offset.offsetSeconds % secondsPerSlot == 0,
                           "variance-clock offsets must be multiples of 300 seconds");
            }
            std::sort(tables.offsets.begin(), tables.offsets.end(),
                      [](const VarianceClockOffsetInput& lhs, const VarianceClockOffsetInput& rhs) {
                          return lhs.start < rhs.start;
                      });
            for (Size i = 1; i < tables.offsets.size(); ++i)
                QL_REQUIRE(tables.offsets[i - 1].end <= tables.offsets[i].start,
                           "overlapping variance-clock offset intervals");
            return maximumWeight;
        }

        void validateFiniteSum(const VarianceClockTables& tables, double maximumWeight) {
            const long double seconds =
                static_cast<long double>(tables.end.unixSeconds()) -
                static_cast<long double>(tables.start.unixSeconds()) +
                (static_cast<long double>(tables.end.nanosecond()) -
                 static_cast<long double>(tables.start.nanosecond())) /
                    nanosecondsPerSecond;
            const long double days = seconds / secondsPerDay;
            const long double bound =
                static_cast<long double>(std::numeric_limits<double>::max()) / 4;
            QL_REQUIRE(static_cast<long double>(maximumWeight) * days <= bound,
                       "variance-clock conservative weighted bound exceeded");
        }

    }

    namespace detail {

        std::vector<VarianceClockRun> buildVarianceClockRuns(VarianceClockTables& tables) {
            const auto maximumWeight = validateTables(tables);
            validateFiniteSum(tables, maximumWeight);
            std::vector<VarianceClockRun> runs;
            runs.reserve(tables.dates.size() + tables.offsets.size());

            auto cursor = tables.start;
            Size offsetIndex = 0;
            while (offsetIndex < tables.offsets.size() &&
                   tables.offsets[offsetIndex].end <= cursor)
                ++offsetIndex;

            while (cursor < tables.end) {
                QL_REQUIRE(offsetIndex < tables.offsets.size(),
                           "variance-clock offset coverage is incomplete");
                const auto& offset = tables.offsets[offsetIndex];
                QL_REQUIRE(offset.start <= cursor,
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

                auto end = offset.end < tables.end ? offset.end : tables.end;
                const auto midnight = nextBoundary(cursor, secondsPerDay - secondOfDay(local));
                if (midnight < end)
                    end = midnight;

                runs.push_back(
                    {cursor, end, date, dateIt->profile, offset.offsetSeconds, offset.fold});
                cursor = end;
                if (offset.end <= cursor)
                    ++offsetIndex;
            }

            return runs;
        }

        VarianceClockNumericEngine::VarianceClockNumericEngine(VarianceClockTables&& tables)
        : tables_(std::move(tables)), runs_(buildVarianceClockRuns(tables_)) {
            constexpr Size slotsPerDay = 288;
            profileTrees_.resize(tables_.profiles.size());
            for (Size i = 0; i < tables_.profiles.size(); ++i) {
                auto& tree = profileTrees_[i];
                tree.fill(0.0);
                for (Size slot = 0; slot < slotsPerDay; ++slot) {
                    // Half-scale keeps even unused full-day trees finite for short coverage.
                    tree[slotsPerDay + slot] =
                        tables_.profiles[i].slots[slot].weight *
                        (static_cast<double>(secondsPerSlot) / secondsPerDay / 2.0);
                }
                for (Size node = slotsPerDay; node-- > 1;)
                    tree[node] = tree[2 * node] + tree[2 * node + 1];
            }

            runProfiles_.reserve(runs_.size());
            for (const auto& run : runs_) {
                const auto it =
                    std::lower_bound(tables_.profiles.begin(), tables_.profiles.end(), run.profile,
                                     [](const VarianceClockProfileInput& profile,
                                        VarianceClockProfileId id) { return profile.id < id; });
                runProfiles_.push_back(static_cast<Size>(it - tables_.profiles.begin()));
            }

            const Size count = runs_.size();
            runTree_.assign(2 * count, 0.0);
            calibrationTree_.resize(2 * count);
            for (Size i = 0; i < count; ++i) {
                runTree_[count + i] = runValue(i, runs_[i].start, runs_[i].end,
                                               endpointSlot(i, runs_[i].end), nullptr);
                calibrationTree_[count + i] = tables_.profiles[runProfiles_[i]].calibrationAsOf;
            }
            for (Size node = count; node-- > 1;) {
                runTree_[node] = runTree_[2 * node] + runTree_[2 * node + 1];
                calibrationTree_[node] =
                    std::max(calibrationTree_[2 * node], calibrationTree_[2 * node + 1]);
            }
        }

        VarianceClockInstant VarianceClockNumericEngine::coverageStart() const noexcept {
            return tables_.start;
        }

        VarianceClockInstant VarianceClockNumericEngine::coverageEnd() const noexcept {
            return tables_.end;
        }

        Size VarianceClockNumericEngine::endpointSlot(Size run,
                                                      VarianceClockInstant time) const noexcept {
            const auto local = localSecondOfDay(time, runs_[run].offsetSeconds);
            if (local == 0 && time.nanosecond() == 0 && time == runs_[run].end)
                return 288;
            return static_cast<Size>(local / secondsPerSlot);
        }

        VarianceClockNumericPosition
        VarianceClockNumericEngine::prepareExpiry(VarianceClockInstant time) const noexcept {
#ifndef NDEBUG
            assertCovered(tables_, time);
#endif
            const auto it =
                std::lower_bound(runs_.begin(), runs_.end(), time,
                                 [](const VarianceClockRun& run, VarianceClockInstant value) {
                                     return run.end < value;
                                 });
            const auto run = static_cast<Size>(it - runs_.begin());
            return {time, run, endpointSlot(run, time)};
        }

        double VarianceClockNumericEngine::runValue(Size run,
                                                    VarianceClockInstant start,
                                                    VarianceClockInstant end,
                                                    Size endSlot,
                                                    std::size_t* visitedNodes) const noexcept {
            if (!(start < end))
                return 0.0;

            constexpr Size slotsPerDay = 288;
            const auto& weights = tables_.profiles[runProfiles_[run]].slots;
            const auto localStart = localSecondOfDay(start, runs_[run].offsetSeconds);
            const Size startSlot = static_cast<Size>(localStart / secondsPerSlot);
            if (startSlot == endSlot)
                return weightedDuration(weights[startSlot].weight, start, end);

            VarianceClockInstant nextSlot;
            (void)VarianceClockInstant::tryCreate(
                start.unixSeconds() + secondsPerSlot - localStart % secondsPerSlot, 0, nextSlot);
            double result = weightedDuration(weights[startSlot].weight, start, nextSlot);
            // Restore the profile tree's half-scaled contributions.
            result += 2.0 * indexedSum(profileTrees_[runProfiles_[run]].data(), slotsPerDay,
                                       startSlot + 1, endSlot, visitedNodes);
            if (endSlot < slotsPerDay) {
                const auto localEnd = localSecondOfDay(end, runs_[run].offsetSeconds);
                if (localEnd % secondsPerSlot != 0 || end.nanosecond() != 0) {
                    VarianceClockInstant slotStart;
                    (void)VarianceClockInstant::tryCreate(
                        end.unixSeconds() - localEnd % secondsPerSlot, 0, slotStart);
                    result += weightedDuration(weights[endSlot].weight, slotStart, end);
                }
            }
            return result;
        }

        VarianceClockNumericResult VarianceClockNumericEngine::cumulativeFromCoverageStart(
            VarianceClockInstant time, std::size_t* visitedNodes) const noexcept {
#ifndef NDEBUG
            assertCovered(tables_, time);
#endif
            if (time == tables_.start)
                return {VarianceClockNumericStatus::Ok, 0.0};
            return cumulativeFromCoverageStart(prepareExpiry(time), visitedNodes);
        }

        VarianceClockNumericResult VarianceClockNumericEngine::cumulativeFromCoverageStart(
            const VarianceClockNumericPosition& end, std::size_t* visitedNodes) const noexcept {
#ifndef NDEBUG
            assertCovered(tables_, end.time);
#endif
            if (end.time == tables_.start)
                return {VarianceClockNumericStatus::Ok, 0.0};
            const double prior =
                indexedSum(runTree_.data(), runs_.size(), 0, end.run, visitedNodes);
            const double last =
                runValue(end.run, runs_[end.run].start, end.time, end.slot, visitedNodes);
            return {VarianceClockNumericStatus::Ok, prior + last};
        }

        bool VarianceClockNumericEngine::isEligible(VarianceClockInstant valuation,
                                                    VarianceClockInstant start,
                                                    const VarianceClockNumericPosition& end,
                                                    std::size_t* visitedNodes) const noexcept {
#ifndef NDEBUG
            assertCovered(tables_, valuation);
            assertCovered(tables_, start);
            assertCovered(tables_, end.time);
#endif
            if (valuation < tables_.availableFrom)
                return false;
            const auto it =
                std::lower_bound(runs_.begin(), runs_.end(), start,
                                 [](const VarianceClockRun& run, VarianceClockInstant value) {
                                     return run.end <= value;
                                 });
            Size begin = static_cast<Size>(it - runs_.begin()) + runs_.size();
            Size finish = end.run + 1 + runs_.size();
            VarianceClockInstant latest;
            for (; begin < finish; begin /= 2, finish /= 2) {
                if (begin % 2 != 0) {
                    latest = std::max(latest, calibrationTree_[begin++]);
                    if (visitedNodes)
                        ++*visitedNodes;
                }
                if (finish % 2 != 0) {
                    latest = std::max(latest, calibrationTree_[--finish]);
                    if (visitedNodes)
                        ++*visitedNodes;
                }
            }
            return latest <= valuation;
        }

        VarianceClockNumericResult
        VarianceClockNumericEngine::remaining(VarianceClockInstant time,
                                              const VarianceClockNumericPosition& expiry,
                                              std::size_t* visitedNodes) const noexcept {
#ifndef NDEBUG
            assertCovered(tables_, time);
            assertCovered(tables_, expiry.time);
#endif
            if (!(time < expiry.time))
                return {VarianceClockNumericStatus::Expired, 0.0};

            const auto it =
                std::lower_bound(runs_.begin(), runs_.end(), time,
                                 [](const VarianceClockRun& run, VarianceClockInstant value) {
                                     return run.end <= value;
                                 });
            const auto first = static_cast<Size>(it - runs_.begin());
            if (first == expiry.run)
                return {VarianceClockNumericStatus::Ok,
                        runValue(first, time, expiry.time, expiry.slot, visitedNodes)};

            const double tail = runValue(first, time, runs_[first].end,
                                         endpointSlot(first, runs_[first].end), visitedNodes);
            const double middle =
                indexedSum(runTree_.data(), runs_.size(), first + 1, expiry.run, visitedNodes);
            const double head = runValue(expiry.run, runs_[expiry.run].start, expiry.time,
                                         expiry.slot, visitedNodes);
            return {VarianceClockNumericStatus::Ok, tail + middle + head};
        }
    }

    struct VarianceClockSnapshot::Impl {
        explicit Impl(VarianceClockTables&& input) : engine(std::move(input)) {}

        detail::VarianceClockNumericEngine engine;
    };

    detail::VarianceClockGeneration::VarianceClockGeneration(
        std::unique_ptr<VarianceClockSnapshot> snapshot)
    : snapshot_(std::move(snapshot)) {}

    const detail::VarianceClockNumericEngine&
    detail::VarianceClockGeneration::engine() const noexcept {
        return snapshot_->impl_->engine;
    }

    VarianceClockSnapshot::VarianceClockSnapshot(std::unique_ptr<Impl> impl)
    : impl_(std::move(impl)) {}

    VarianceClockSnapshot::~VarianceClockSnapshot() = default;

    VarianceClockInstant VarianceClockSnapshot::coverageStart() const noexcept {
        return impl_->engine.coverageStart();
    }

    VarianceClockInstant VarianceClockSnapshot::coverageEnd() const noexcept {
        return impl_->engine.coverageEnd();
    }

    std::unique_ptr<VarianceClockSnapshot> makeVarianceClockSnapshot(VarianceClockTables&& tables) {
        auto impl = std::make_unique<VarianceClockSnapshot::Impl>(std::move(tables));
        return std::unique_ptr<VarianceClockSnapshot>(new VarianceClockSnapshot(std::move(impl)));
    }
}
