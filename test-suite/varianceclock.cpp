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

#include "toplevelfixture.hpp"
#include "utilities.hpp"
#include <ql/errors.hpp>
#include <ql/time/varianceclock.hpp>
#include <ql/time/varianceclockdetail.hpp>
#include <boost/multiprecision/cpp_dec_float.hpp>
#include <boost/test/unit_test.hpp>
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <condition_variable>
#include <limits>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>
#include <vector>

using namespace QuantLib;

namespace {

    using HighPrecision = boost::multiprecision::cpp_dec_float_100;

    VarianceClockInstant instant(std::int64_t seconds, std::uint32_t nanoseconds = 0) {
        VarianceClockInstant result;
        QL_REQUIRE(VarianceClockInstant::tryCreate(seconds, nanoseconds, result),
                   "invalid test instant");
        return result;
    }

    VarianceClockProfileInput profile(VarianceClockProfileId id, double weight = 1.0) {
        VarianceClockProfileInput result;
        result.id = id;
        result.calibrationAsOf = instant(0);
        for (auto& slot : result.slots)
            slot.weight = weight;
        return result;
    }

    VarianceClockTables foldTables() {
        VarianceClockTables tables;
        tables.start = instant(1730606399, 500000000);
        tables.end = instant(1730613900, 1000000);
        tables.availableFrom = instant(0);
        tables.profiles = {profile(2), profile(1)};
        tables.dates = {{Date(3, November, 2024), 2}, {Date(2, November, 2024), 1}};
        tables.offsets = {{instant(1730613600), tables.end, -18000, true},
                          {tables.start, instant(1730613600), -14400, false}};
        return tables;
    }

    void checkInstant(const VarianceClockInstant& actual,
                      std::int64_t seconds,
                      std::uint32_t nanoseconds = 0) {
        BOOST_CHECK(actual.isValid());
        BOOST_CHECK_EQUAL(actual.unixSeconds(), seconds);
        BOOST_CHECK_EQUAL(actual.nanosecond(), nanoseconds);
    }

    void checkInvalid(VarianceClockTables tables, const std::string& expected) {
        BOOST_CHECK_EXCEPTION(makeVarianceClockSnapshot(std::move(tables)), Error,
                              [&expected](const Error& e) {
                                  return std::string(e.what()).find(expected) != std::string::npos;
                              });
    }

    void checkWeightedDays(double actual, const HighPrecision& reference) {
        const HighPrecision error = abs(HighPrecision(actual) - reference);
        const HighPrecision tolerance = HighPrecision("1e-12") +
                                        HighPrecision("1e-10") * abs(reference);
        BOOST_CHECK_GE(actual, 0.0);
        BOOST_CHECK_MESSAGE(error <= tolerance,
                            "weighted days " << actual << ", reference " << reference
                                             << ", error " << error << ", tolerance " << tolerance);
    }

}

BOOST_FIXTURE_TEST_SUITE(QuantLibTests, TopLevelFixture)

BOOST_AUTO_TEST_SUITE(VarianceClockTests)

BOOST_AUTO_TEST_CASE(testRunSplittingAtMidnightAndFold) {
    BOOST_TEST_MESSAGE("Testing variance-clock runs at midnight and a repeated hour...");

    auto tables = foldTables();
    const auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 3);

    checkInstant(runs[0].start, 1730606399, 500000000);
    checkInstant(runs[0].end, 1730606400);
    BOOST_CHECK(runs[0].localDate == Date(2, November, 2024));
    BOOST_CHECK_EQUAL(runs[0].profile, 1);
    BOOST_CHECK_EQUAL(runs[0].offsetSeconds, -14400);
    BOOST_CHECK(!runs[0].fold);

    checkInstant(runs[1].start, 1730606400);
    checkInstant(runs[1].end, 1730613600);
    BOOST_CHECK(runs[1].localDate == Date(3, November, 2024));
    BOOST_CHECK_EQUAL(runs[1].profile, 2);
    BOOST_CHECK_EQUAL(runs[1].offsetSeconds, -14400);
    BOOST_CHECK(!runs[1].fold);

    checkInstant(runs[2].start, 1730613600);
    checkInstant(runs[2].end, 1730613900, 1000000);
    BOOST_CHECK(runs[2].localDate == Date(3, November, 2024));
    BOOST_CHECK_EQUAL(runs[2].profile, 2);
    BOOST_CHECK_EQUAL(runs[2].offsetSeconds, -18000);
    BOOST_CHECK(runs[2].fold);

    const auto snapshot = makeVarianceClockSnapshot(std::move(tables));
    checkInstant(snapshot->coverageStart(), 1730606399, 500000000);
    checkInstant(snapshot->coverageEnd(), 1730613900, 1000000);
}

BOOST_AUTO_TEST_CASE(testInstantValidationAndNegativeEpoch) {
    BOOST_TEST_MESSAGE("Testing variance-clock instants around the Unix epoch...");

    VarianceClockInstant value;
    BOOST_CHECK(!value.isValid());
    BOOST_REQUIRE(VarianceClockInstant::tryCreate(-1, 999000000, value));
    checkInstant(value, -1, 999000000);
    BOOST_CHECK(!VarianceClockInstant::tryCreate(0, 1000000000, value));
    checkInstant(value, -1, 999000000);
    BOOST_REQUIRE(VarianceClockInstant::tryCreate(0, 0, value));
    checkInstant(value, 0);

    VarianceClockTables tables;
    tables.start = instant(-1, 999000000);
    tables.end = instant(0, 1000000);
    tables.availableFrom = instant(-10);
    tables.profiles = {profile(1), profile(2)};
    tables.dates = {{Date(31, December, 1969), 1}, {Date(1, January, 1970), 2}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    const auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 2);
    BOOST_CHECK(runs[0].localDate == Date(31, December, 1969));
    BOOST_CHECK(runs[1].localDate == Date(1, January, 1970));
    checkInstant(runs[0].end, 0);
    checkInstant(runs[1].start, 0);
}

BOOST_AUTO_TEST_CASE(testInstantComparisons) {
    BOOST_TEST_MESSAGE("Testing variance-clock instant comparisons...");

    const VarianceClockInstant invalid;
    const auto negative = instant(-1, 999999999);
    const auto epoch = instant(0);
    const auto later = instant(0, 1);

    BOOST_CHECK(invalid == VarianceClockInstant());
    BOOST_CHECK(invalid < negative);
    BOOST_CHECK(!(negative < invalid));
    BOOST_CHECK(negative < epoch);
    BOOST_CHECK(epoch < later);
    BOOST_CHECK(epoch == instant(0));
    BOOST_CHECK(!(epoch == later));
    BOOST_CHECK(epoch <= epoch);
    BOOST_CHECK(epoch <= later);
    BOOST_CHECK(!(later <= epoch));
}

BOOST_AUTO_TEST_CASE(testOffsetTransitionInsideBucket) {
    BOOST_TEST_MESSAGE("Testing variance-clock offset transitions inside a slot...");

    VarianceClockTables tables;
    tables.start = instant(0, 250000000);
    tables.end = instant(600, 750000000);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1)};
    tables.dates = {{Date(1, January, 1970), 1}};
    tables.offsets = {{tables.start, instant(150, 500000000), 0, false},
                      {instant(150, 500000000), tables.end, 300, false}};
    const auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 2);
    checkInstant(runs[0].end, 150, 500000000);
    checkInstant(runs[1].start, 150, 500000000);
    BOOST_CHECK_EQUAL(runs[0].offsetSeconds, 0);
    BOOST_CHECK_EQUAL(runs[1].offsetSeconds, 300);
}

BOOST_AUTO_TEST_CASE(testSpringForwardDay) {
    BOOST_TEST_MESSAGE("Testing a 23-hour variance-clock spring-forward day...");

    VarianceClockTables tables;
    tables.start = instant(1710046800);
    tables.end = instant(1710129601);
    tables.availableFrom = instant(0);
    tables.profiles = {profile(1), profile(2)};
    tables.dates = {{Date(10, March, 2024), 1}, {Date(11, March, 2024), 2}};
    tables.offsets = {{tables.start, instant(1710054000), -18000, false},
                      {instant(1710054000), tables.end, -14400, false}};

    const auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 3);
    checkInstant(runs[0].start, 1710046800);
    checkInstant(runs[0].end, 1710054000);
    checkInstant(runs[1].start, 1710054000);
    checkInstant(runs[1].end, 1710129600);
    BOOST_CHECK_EQUAL(runs[1].end.unixSeconds() - runs[0].start.unixSeconds(), 23 * 3600);
    BOOST_CHECK(runs[0].localDate == Date(10, March, 2024));
    BOOST_CHECK(runs[1].localDate == Date(10, March, 2024));
    BOOST_CHECK_EQUAL(runs[0].profile, 1);
    BOOST_CHECK_EQUAL(runs[1].profile, 1);
    BOOST_CHECK_EQUAL(runs[0].offsetSeconds, -18000);
    BOOST_CHECK_EQUAL(runs[1].offsetSeconds, -14400);
    BOOST_CHECK(!runs[0].fold);
    BOOST_CHECK(!runs[1].fold);
    checkInstant(runs[2].start, 1710129600);
    BOOST_CHECK(runs[2].localDate == Date(11, March, 2024));
    BOOST_CHECK_EQUAL(runs[2].profile, 2);
}

BOOST_AUTO_TEST_CASE(testFallBackDay) {
    BOOST_TEST_MESSAGE("Testing a 25-hour variance-clock fall-back day...");

    VarianceClockTables tables;
    tables.start = instant(1730606400);
    tables.end = instant(1730696401);
    tables.availableFrom = instant(0);
    tables.profiles = {profile(1), profile(2)};
    tables.dates = {{Date(3, November, 2024), 1}, {Date(4, November, 2024), 2}};
    tables.offsets = {{tables.start, instant(1730613600), -14400, false},
                      {instant(1730613600), instant(1730617200), -18000, true},
                      {instant(1730617200), tables.end, -18000, false}};

    const auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 4);
    checkInstant(runs[0].start, 1730606400);
    checkInstant(runs[0].end, 1730613600);
    checkInstant(runs[1].start, 1730613600);
    checkInstant(runs[1].end, 1730617200);
    checkInstant(runs[2].start, 1730617200);
    checkInstant(runs[2].end, 1730696400);
    BOOST_CHECK_EQUAL(runs[2].end.unixSeconds() - runs[0].start.unixSeconds(), 25 * 3600);
    for (Size i = 0; i != 3; ++i) {
        BOOST_CHECK(runs[i].localDate == Date(3, November, 2024));
        BOOST_CHECK_EQUAL(runs[i].profile, 1);
    }
    BOOST_CHECK_EQUAL(runs[0].offsetSeconds, -14400);
    BOOST_CHECK_EQUAL(runs[1].offsetSeconds, -18000);
    BOOST_CHECK_EQUAL(runs[2].offsetSeconds, -18000);
    BOOST_CHECK(!runs[0].fold);
    BOOST_CHECK(runs[1].fold);
    BOOST_CHECK(!runs[2].fold);
    checkInstant(runs[3].start, 1730696400);
    BOOST_CHECK(runs[3].localDate == Date(4, November, 2024));
    BOOST_CHECK_EQUAL(runs[3].profile, 2);
}

BOOST_AUTO_TEST_CASE(testOffsetAndUnusedInputsOutsideCoverage) {
    BOOST_TEST_MESSAGE("Testing variance-clock offset clipping and unused inputs...");

    VarianceClockTables tables;
    tables.start = instant(100);
    tables.end = instant(200);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1), profile(2), profile(3)};
    tables.dates = {{Date(1, January, 1970), 1}, {Date(2, January, 1970), 2}};
    tables.offsets = {{instant(-2000), instant(-1000), -3600, false},
                      {instant(0), instant(1000), 0, false},
                      {instant(2000), instant(3000), 3600, false}};

    const auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 1);
    checkInstant(runs[0].start, 100);
    checkInstant(runs[0].end, 200);
    BOOST_CHECK(runs[0].localDate == Date(1, January, 1970));
    BOOST_CHECK_EQUAL(runs[0].profile, 1);
    BOOST_CHECK_EQUAL(runs[0].offsetSeconds, 0);
}

BOOST_AUTO_TEST_CASE(testInvalidTableStructure) {
    BOOST_TEST_MESSAGE("Testing variance-clock table validation...");

    auto tables = foldTables();
    tables.availableFrom = VarianceClockInstant();
    checkInvalid(std::move(tables), "coverage or availability is invalid");

    tables = foldTables();
    tables.profiles[0].calibrationAsOf = VarianceClockInstant();
    checkInvalid(std::move(tables), "calibration instant is invalid");

    tables = foldTables();
    tables.profiles.push_back(profile(1));
    checkInvalid(std::move(tables), "duplicate variance-clock profile");

    tables = foldTables();
    tables.dates.push_back(tables.dates.front());
    checkInvalid(std::move(tables), "duplicate variance-clock local date");

    tables = foldTables();
    tables.dates[0].profile = 999;
    checkInvalid(std::move(tables), "date references a missing profile");

    tables = foldTables();
    tables.dates.pop_back();
    checkInvalid(std::move(tables), "local date is not covered");

    tables = foldTables();
    tables.offsets[0].start = instant(1730613601);
    checkInvalid(std::move(tables), "offset coverage contains a gap");

    tables = foldTables();
    tables.offsets[0].start = instant(1730613599);
    checkInvalid(std::move(tables), "overlapping variance-clock offset intervals");

    tables = foldTables();
    tables.offsets[0].offsetSeconds = -18001;
    checkInvalid(std::move(tables), "offsets must be multiples of 300 seconds");

    tables = foldTables();
    tables.offsets[0].offsetSeconds = std::numeric_limits<std::int32_t>::min();
    checkInvalid(std::move(tables), "offsets must be multiples of 300 seconds");

    tables = foldTables();
    tables.offsets[0].end = VarianceClockInstant();
    checkInvalid(std::move(tables), "invalid variance-clock offset interval");
}

BOOST_AUTO_TEST_CASE(testEmptyAndReversedCoverage) {
    BOOST_TEST_MESSAGE("Testing variance-clock empty and reversed coverage...");

    auto tables = foldTables();
    tables.end = tables.start;
    checkInvalid(std::move(tables), "coverage must be nonempty and ordered");

    tables = foldTables();
    const auto start = tables.start;
    tables.start = tables.end;
    tables.end = start;
    checkInvalid(std::move(tables), "coverage must be nonempty and ordered");
}

BOOST_AUTO_TEST_CASE(testConservativeOverflowBound) {
    BOOST_TEST_MESSAGE("Testing the conservative variance-clock overflow bound...");

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(86400);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1)};
    tables.dates = {{Date(1, January, 1970), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};

    const double limit = std::numeric_limits<double>::max() / 4.0;
    tables.profiles[0] = profile(1, std::nextafter(limit, 0.0));
    auto below = tables;
    checkInstant(makeVarianceClockSnapshot(std::move(below))->coverageEnd(), 86400);
    tables.profiles[0] = profile(1, limit);
    auto equal = tables;
    checkInstant(makeVarianceClockSnapshot(std::move(equal))->coverageEnd(), 86400);

    tables.profiles[0] = profile(1, std::nextafter(limit, std::numeric_limits<double>::infinity()));
    checkInvalid(tables, "conservative weighted bound exceeded");
    tables.profiles[0] = profile(1, std::numeric_limits<double>::max());
    checkInvalid(tables, "conservative weighted bound exceeded");

    tables.profiles[0] = profile(1, std::numeric_limits<double>::denorm_min());
    checkInstant(makeVarianceClockSnapshot(std::move(tables))->coverageEnd(), 86400);
}

BOOST_AUTO_TEST_CASE(testInvalidAndOverflowingWeights) {
    BOOST_TEST_MESSAGE("Testing variance-clock rate and sum validation...");

    for (const double invalid : {std::numeric_limits<double>::quiet_NaN(),
                                 std::numeric_limits<double>::infinity(), -1.0}) {
        auto tables = foldTables();
        tables.profiles[0].slots[0].weight = invalid;
        checkInvalid(std::move(tables), "weights must be finite and nonnegative");
    }

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(172800);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1, std::numeric_limits<double>::max())};
    tables.dates = {{Date(1, January, 1970), 1}, {Date(2, January, 1970), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    checkInvalid(tables, "conservative weighted bound exceeded");

    tables.end = instant(0, 1000000);
    tables.dates.pop_back();
    tables.offsets[0].end = tables.end;
    const auto snapshot = makeVarianceClockSnapshot(std::move(tables));
    checkInstant(snapshot->coverageEnd(), 0, 1000000);
}

BOOST_AUTO_TEST_CASE(testInstantArithmeticOverflow) {
    BOOST_TEST_MESSAGE("Testing variance-clock offset arithmetic overflow...");

    auto tables = foldTables();
    tables.start = instant(std::numeric_limits<std::int64_t>::max() - 10);
    tables.end = instant(std::numeric_limits<std::int64_t>::max() - 1);
    tables.offsets = {{tables.start, tables.end, 300, false}};
    checkInvalid(std::move(tables), "UTC offset overflows");

    tables = foldTables();
    tables.start = instant(std::numeric_limits<std::int64_t>::min() + 1);
    tables.end = instant(std::numeric_limits<std::int64_t>::min() + 10);
    tables.offsets = {{tables.start, tables.end, -300, false}};
    checkInvalid(std::move(tables), "UTC offset overflows");
}

BOOST_AUTO_TEST_CASE(testDateRangeLimits) {
    BOOST_TEST_MESSAGE("Testing variance-clock QuantLib date range limits...");

    const auto epoch = static_cast<std::int64_t>(Date(1, January, 1970).serialNumber());
    const auto minimum =
        (static_cast<std::int64_t>(Date::minDate().serialNumber()) - epoch) * 86400;
    const auto maximum =
        (static_cast<std::int64_t>(Date::maxDate().serialNumber()) - epoch) * 86400;

    VarianceClockTables tables;
    tables.availableFrom = instant(0);
    tables.profiles = {profile(1)};
    tables.start = instant(minimum);
    tables.end = instant(minimum + 1);
    tables.dates = {{Date::minDate(), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    auto runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 1);
    BOOST_CHECK(runs[0].localDate == Date::minDate());

    tables.start = instant(minimum - 1);
    tables.end = instant(minimum);
    tables.offsets = {{tables.start, tables.end, 0, false}};
    checkInvalid(tables, "local date is outside the QuantLib date range");

    tables.start = instant(maximum + 86399);
    tables.end = instant(maximum + 86400);
    tables.dates = {{Date::maxDate(), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    runs = detail::buildVarianceClockRuns(tables);
    BOOST_REQUIRE_EQUAL(runs.size(), 1);
    BOOST_CHECK(runs[0].localDate == Date::maxDate());

    tables.start = instant(maximum + 86400);
    tables.end = instant(maximum + 86401);
    tables.offsets = {{tables.start, tables.end, 0, false}};
    checkInvalid(std::move(tables), "local date is outside the QuantLib date range");
}

BOOST_AUTO_TEST_CASE(testOneMillisecondAfterThirtyYears) {
    BOOST_TEST_MESSAGE("Testing a millisecond interval after thirty years...");

    constexpr Size days = 30 * 365;
    constexpr std::int64_t end = static_cast<std::int64_t>(days) * 86400;
    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(end);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1, 100.0)};
    tables.dates.reserve(days);
    for (Size i = 0; i < days; ++i)
        tables.dates.push_back({Date(1, January, 1970) + static_cast<Integer>(i), 1});
    tables.offsets = {{tables.start, tables.end, 0, false}};

    const detail::VarianceClockNumericEngine engine(std::move(tables));
    const auto expiry = engine.prepareExpiry(instant(end));
    const auto result = engine.remaining(instant(end - 1, 999000000), expiry);
    BOOST_CHECK(result.status == detail::VarianceClockNumericStatus::Ok);
    const HighPrecision reference =
        HighPrecision("100") * HighPrecision("0.001") / HighPrecision("86400");
    checkWeightedDays(result.weightedDays, reference);

    const auto cumulativeEnd = engine.cumulativeFromCoverageStart(instant(end));
    const auto cumulativeBefore = engine.cumulativeFromCoverageStart(instant(end - 1, 999000000));
    const HighPrecision subtracted(cumulativeEnd.weightedDays - cumulativeBefore.weightedDays);
    const HighPrecision tolerance =
        HighPrecision("1e-12") + HighPrecision("1e-10") * abs(reference);
    BOOST_CHECK_MESSAGE(abs(subtracted - reference) > tolerance,
                        "rounded cumulative subtraction unexpectedly met the interval budget");
}

BOOST_AUTO_TEST_CASE(testNumericBoundariesAndStatuses) {
    BOOST_TEST_MESSAGE("Testing variance-clock slot boundaries and numeric statuses...");

    using Engine = detail::VarianceClockNumericEngine;
    using Position = detail::VarianceClockNumericPosition;
    static_assert(
        noexcept(std::declval<const Engine&>().prepareExpiry(std::declval<VarianceClockInstant>())),
        "expiry preparation must not throw");
    static_assert(noexcept(std::declval<const Engine&>().cumulativeFromCoverageStart(
                      std::declval<VarianceClockInstant>())),
                  "cumulative query must not throw");
    static_assert(noexcept(std::declval<const Engine&>().remaining(
                      std::declval<VarianceClockInstant>(), std::declval<const Position&>())),
                  "remaining query must not throw");

    VarianceClockTables tables;
    tables.start = instant(100, 250000000);
    tables.end = instant(900, 750000000);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1)};
    tables.profiles[0].slots[0].weight = 2.0;
    tables.profiles[0].slots[1].weight = 3.0;
    tables.profiles[0].slots[2].weight = 0.0;
    tables.profiles[0].slots[3].weight = 4.0;
    tables.dates = {{Date(1, January, 1970), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    const detail::VarianceClockNumericEngine engine(std::move(tables));

    const auto sameSlot =
        engine.remaining(instant(200), engine.prepareExpiry(instant(200, 500000000)));
    BOOST_CHECK(sameSlot.status == detail::VarianceClockNumericStatus::Ok);
    checkWeightedDays(sameSlot.weightedDays,
                      HighPrecision("2") * HighPrecision("0.5") / HighPrecision("86400"));

    const auto before = instant(299, 999000000);
    const auto boundary = instant(300);
    const auto after = instant(300, 1000000);
    const auto left = engine.remaining(before, engine.prepareExpiry(boundary));
    const auto right = engine.remaining(boundary, engine.prepareExpiry(after));
    const auto both = engine.remaining(before, engine.prepareExpiry(after));
    checkWeightedDays(left.weightedDays,
                      HighPrecision("2") * HighPrecision("0.001") / HighPrecision("86400"));
    checkWeightedDays(right.weightedDays,
                      HighPrecision("3") * HighPrecision("0.001") / HighPrecision("86400"));
    const HighPrecision across =
        (HighPrecision("2") + HighPrecision("3")) * HighPrecision("0.001") / HighPrecision("86400");
    checkWeightedDays(both.weightedDays, across);
    checkWeightedDays(left.weightedDays + right.weightedDays, across);

    const auto startValue = engine.cumulativeFromCoverageStart(instant(100, 250000000));
    BOOST_CHECK(startValue.status == detail::VarianceClockNumericStatus::Ok);
    BOOST_CHECK_EQUAL(startValue.weightedDays, 0.0);
    const auto endValue = engine.cumulativeFromCoverageStart(instant(900, 750000000));
    BOOST_CHECK(endValue.status == detail::VarianceClockNumericStatus::Ok);
    const HighPrecision full =
        (HighPrecision("2") * HighPrecision("199.75") + HighPrecision("3") * HighPrecision("300") +
         HighPrecision("4") * HighPrecision("0.75")) /
        HighPrecision("86400");
    checkWeightedDays(endValue.weightedDays, full);
    checkWeightedDays(
        engine.remaining(instant(100, 250000000), engine.prepareExpiry(instant(900, 750000000)))
            .weightedDays,
        full);

    const auto zero = engine.remaining(instant(600), engine.prepareExpiry(instant(899)));
    BOOST_CHECK(zero.status == detail::VarianceClockNumericStatus::Ok);
    BOOST_CHECK_EQUAL(zero.weightedDays, 0.0);
    for (const auto time : {instant(400), instant(500)}) {
        const auto expired = engine.remaining(time, engine.prepareExpiry(instant(400)));
        BOOST_CHECK(expired.status == detail::VarianceClockNumericStatus::Expired);
        BOOST_CHECK_EQUAL(expired.weightedDays, 0.0);
    }
}

BOOST_AUTO_TEST_CASE(testNumericDstDaysAndFolds) {
    BOOST_TEST_MESSAGE("Testing variance-clock integration across DST days and folds...");

    VarianceClockTables spring;
    spring.start = instant(1710046800);
    spring.end = instant(1710129600);
    spring.availableFrom = instant(0);
    spring.profiles = {profile(1)};
    spring.dates = {{Date(10, March, 2024), 1}};
    spring.offsets = {{spring.start, instant(1710054000), -18000, false},
                      {instant(1710054000), spring.end, -14400, false}};
    const detail::VarianceClockNumericEngine springEngine(std::move(spring));
    checkWeightedDays(
        springEngine.remaining(instant(1710046800), springEngine.prepareExpiry(instant(1710129600)))
            .weightedDays,
        HighPrecision("23") / HighPrecision("24"));

    VarianceClockTables fall;
    fall.start = instant(1730606400);
    fall.end = instant(1730696400);
    fall.availableFrom = instant(0);
    fall.profiles = {profile(1)};
    fall.dates = {{Date(3, November, 2024), 1}};
    fall.offsets = {{fall.start, instant(1730613600), -14400, false},
                    {instant(1730613600), instant(1730617200), -18000, true},
                    {instant(1730617200), fall.end, -18000, false}};
    auto unitFall = fall;
    const detail::VarianceClockNumericEngine unitEngine(std::move(unitFall));
    checkWeightedDays(
        unitEngine.remaining(instant(1730606400), unitEngine.prepareExpiry(instant(1730696400)))
            .weightedDays,
        HighPrecision("25") / HighPrecision("24"));

    for (Size slot = 12; slot < 24; ++slot)
        fall.profiles[0].slots[slot].weight = 3.0;
    const detail::VarianceClockNumericEngine fallEngine(std::move(fall));
    checkWeightedDays(
        fallEngine.remaining(instant(1730606400), fallEngine.prepareExpiry(instant(1730696400)))
            .weightedDays,
        HighPrecision("29") / HighPrecision("24"));
    checkWeightedDays(
        fallEngine.remaining(instant(1730610000), fallEngine.prepareExpiry(instant(1730613600)))
            .weightedDays,
        HighPrecision("3") / HighPrecision("24"));
    checkWeightedDays(
        fallEngine.remaining(instant(1730613600), fallEngine.prepareExpiry(instant(1730617200)))
            .weightedDays,
        HighPrecision("3") / HighPrecision("24"));
}

BOOST_AUTO_TEST_CASE(testNumericProfileAndOffsetTransitions) {
    BOOST_TEST_MESSAGE("Testing variance-clock profile and offset transitions...");

    VarianceClockTables dates;
    dates.start = instant(86300, 250000000);
    dates.end = instant(86500, 750000000);
    dates.availableFrom = instant(0);
    dates.profiles = {profile(1, 2.0), profile(2, 5.0)};
    dates.dates = {{Date(1, January, 1970), 1}, {Date(2, January, 1970), 2}};
    dates.offsets = {{dates.start, dates.end, 0, false}};
    const detail::VarianceClockNumericEngine dateEngine(std::move(dates));
    const auto dateResult = dateEngine.remaining(instant(86399, 999000000),
                                                 dateEngine.prepareExpiry(instant(86400, 1000000)));
    checkWeightedDays(dateResult.weightedDays, (HighPrecision("2") + HighPrecision("5")) *
                                                   HighPrecision("0.001") / HighPrecision("86400"));
    const auto dateFull = dateEngine.cumulativeFromCoverageStart(instant(86500, 750000000));
    checkWeightedDays(dateFull.weightedDays, (HighPrecision("2") * HighPrecision("99.75") +
                                              HighPrecision("5") * HighPrecision("100.75")) /
                                                 HighPrecision("86400"));

    VarianceClockTables negative;
    negative.start = instant(-1, 999000000);
    negative.end = instant(0, 1000000);
    negative.availableFrom = instant(-10);
    negative.profiles = {profile(1, 2.0), profile(2, 5.0)};
    negative.dates = {{Date(31, December, 1969), 1}, {Date(1, January, 1970), 2}};
    negative.offsets = {{negative.start, negative.end, 0, false}};
    const detail::VarianceClockNumericEngine negativeEngine(std::move(negative));
    const auto negativeResult = negativeEngine.remaining(
        instant(-1, 999000000), negativeEngine.prepareExpiry(instant(0, 1000000)));
    checkWeightedDays(negativeResult.weightedDays, (HighPrecision("2") + HighPrecision("5")) *
                                                       HighPrecision("0.001") /
                                                       HighPrecision("86400"));

    VarianceClockTables offsets;
    offsets.start = instant(0, 250000000);
    offsets.end = instant(600, 750000000);
    offsets.availableFrom = instant(-1);
    offsets.profiles = {profile(1)};
    offsets.profiles[0].slots[0].weight = 2.0;
    offsets.profiles[0].slots[1].weight = 3.0;
    offsets.dates = {{Date(1, January, 1970), 1}};
    offsets.offsets = {{offsets.start, instant(150, 500000000), 0, false},
                       {instant(150, 500000000), offsets.end, 300, false}};
    const detail::VarianceClockNumericEngine offsetEngine(std::move(offsets));
    const auto offsetResult = offsetEngine.remaining(
        instant(150, 499000000), offsetEngine.prepareExpiry(instant(150, 501000000)));
    checkWeightedDays(offsetResult.weightedDays, (HighPrecision("2") + HighPrecision("3")) *
                                                     HighPrecision("0.001") /
                                                     HighPrecision("86400"));
}

BOOST_AUTO_TEST_CASE(testLargeWeightsAndIndexedTraversal) {
    BOOST_TEST_MESSAGE("Testing variance-clock large weights and indexed traversal...");

    VarianceClockTables extreme;
    extreme.start = instant(0);
    extreme.end = instant(3600);
    extreme.availableFrom = instant(-1);
    extreme.profiles = {profile(1, 1.0e308)};
    extreme.dates = {{Date(1, January, 1970), 1}};
    extreme.offsets = {{extreme.start, extreme.end, 0, false}};
    const detail::VarianceClockNumericEngine extremeEngine(std::move(extreme));
    const auto extremeResult =
        extremeEngine.remaining(instant(0), extremeEngine.prepareExpiry(instant(300)));
    BOOST_CHECK(std::isfinite(extremeResult.weightedDays));
    checkWeightedDays(extremeResult.weightedDays,
                      HighPrecision("1e308") * HighPrecision("300") / HighPrecision("86400"));
    const auto nanosecondResult =
        extremeEngine.remaining(instant(299, 999999999), extremeEngine.prepareExpiry(instant(300)));
    checkWeightedDays(nanosecondResult.weightedDays, HighPrecision("1e308") *
                                                         HighPrecision("0.000000001") /
                                                         HighPrecision("86400"));

    VarianceClockTables maximum;
    maximum.start = instant(0);
    maximum.end = instant(0, 1000000);
    maximum.availableFrom = instant(-1);
    maximum.profiles = {profile(1, std::numeric_limits<double>::max())};
    maximum.dates = {{Date(1, January, 1970), 1}};
    maximum.offsets = {{maximum.start, maximum.end, 0, false}};
    const detail::VarianceClockNumericEngine maximumEngine(std::move(maximum));
    const auto maximumResult =
        maximumEngine.remaining(instant(0), maximumEngine.prepareExpiry(instant(0, 1000000)));
    BOOST_CHECK(std::isfinite(maximumResult.weightedDays));
    checkWeightedDays(maximumResult.weightedDays, HighPrecision("1.7976931348623157e308") *
                                                      HighPrecision("0.001") /
                                                      HighPrecision("86400"));

    constexpr Size days = 30 * 365;
    constexpr std::int64_t end = static_cast<std::int64_t>(days) * 86400;
    VarianceClockTables longHorizon;
    longHorizon.start = instant(0);
    longHorizon.end = instant(end);
    longHorizon.availableFrom = instant(-1);
    longHorizon.profiles = {profile(1, 2.0)};
    longHorizon.dates.reserve(days);
    for (Size i = 0; i < days; ++i)
        longHorizon.dates.push_back({Date(1, January, 1970) + static_cast<Integer>(i), 1});
    longHorizon.offsets = {{longHorizon.start, longHorizon.end, 0, false}};
    const detail::VarianceClockNumericEngine longEngine(std::move(longHorizon));
    std::size_t visited = 0;
    const auto longResult = longEngine.remaining(
        instant(150, 250000000), longEngine.prepareExpiry(instant(end - 100, 750000000)), &visited);
    const HighPrecision elapsed = HighPrecision(std::to_string(end)) - HighPrecision("249.5");
    checkWeightedDays(longResult.weightedDays,
                      HighPrecision("2") * elapsed / HighPrecision("86400"));
    std::size_t depth = 0;
    for (Size n = days; n > 1; n = (n + 1) / 2)
        ++depth;
    BOOST_CHECK_LE(visited, 4 * depth + 64);

    std::size_t cumulativeVisited = 0;
    const auto cumulative =
        longEngine.cumulativeFromCoverageStart(instant(end - 100, 750000000), &cumulativeVisited);
    checkWeightedDays(cumulative.weightedDays,
                      HighPrecision("2") *
                          (HighPrecision(std::to_string(end)) - HighPrecision("99.25")) /
                          HighPrecision("86400"));
    BOOST_CHECK_LE(cumulativeVisited, 4 * depth + 64);

    std::size_t eligibilityVisited = 0;
    BOOST_CHECK(longEngine.isEligible(
        instant(1), instant(1), longEngine.prepareExpiry(instant(end - 1)), &eligibilityVisited));
    BOOST_CHECK_LE(eligibilityVisited, 4 * depth + 4);
}

BOOST_AUTO_TEST_CASE(testMultiRunMixedProfileDecimalOracle) {
    BOOST_TEST_MESSAGE("Testing mixed profiles across multiple variance-clock runs...");

    constexpr Size days = 20;
    constexpr std::int64_t nanosPerSecond = 1000000000;
    constexpr std::int64_t slotNanos = 300 * nanosPerSecond;
    constexpr std::int64_t totalNanos = days * 86400 * nanosPerSecond;
    const std::array<VarianceClockProfileId, 4> ids = {97, 3, 1009, 42};
    const std::array<const char*, 5> rates = {"0", "0.25", "1.5", "3.75", "17.25"};
    std::array<Size, days> dayProfiles{};

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(days * 86400);
    tables.availableFrom = instant(-1);
    for (Size p = 0; p < ids.size(); ++p) {
        auto input = profile(ids[p]);
        for (Size slot = 0; slot < input.slots.size(); ++slot)
            input.slots[slot].weight = std::stod(rates[(slot * 7 + p * 3) % rates.size()]);
        tables.profiles.push_back(std::move(input));
    }
    for (Size day = 0; day < days; ++day) {
        dayProfiles[day] = (day * 7 + day / 3) % ids.size();
        tables.dates.push_back(
            {Date(1, January, 1970) + static_cast<Integer>(day), ids[dayProfiles[day]]});
    }
    tables.offsets = {{tables.start, tables.end, 0, false}};
    const detail::VarianceClockNumericEngine engine(std::move(tables));

    const auto oracle = [&rates, &dayProfiles](std::int64_t start,
                                               std::int64_t end) -> HighPrecision {
        HighPrecision total("0");
        for (Size slot = 0; slot < days * 288; ++slot) {
            const auto left = std::max(start, static_cast<std::int64_t>(slot) * slotNanos);
            const auto right = std::min(end, static_cast<std::int64_t>(slot + 1) * slotNanos);
            if (left < right) {
                const Size day = slot / 288;
                const Size localSlot = slot % 288;
                const Size rate = (localSlot * 7 + dayProfiles[day] * 3) % rates.size();
                total += HighPrecision(rates[rate]) * HighPrecision(std::to_string(right - left)) /
                         HighPrecision("86400000000000");
            }
        }
        return total;
    };
    const auto asInstant = [](std::int64_t nanos) {
        return instant(nanos / nanosPerSecond, static_cast<std::uint32_t>(nanos % nanosPerSecond));
    };
    const auto checkInterval = [&](std::int64_t start, std::int64_t end) {
        const auto result =
            engine.remaining(asInstant(start), engine.prepareExpiry(asInstant(end)));
        BOOST_CHECK(result.status == detail::VarianceClockNumericStatus::Ok);
        checkWeightedDays(result.weightedDays, oracle(start, end));
        checkWeightedDays(engine.cumulativeFromCoverageStart(asInstant(end)).weightedDays,
                          oracle(0, end));
    };

    checkInterval(150 * nanosPerSecond, totalNanos - 150 * nanosPerSecond);
    std::uint64_t state = 0x243f6a8885a308d3ULL;
    for (Size i = 0; i < 64; ++i) {
        state = state * 6364136223846793005ULL + 1;
        auto first = static_cast<std::int64_t>(state % totalNanos);
        state = state * 6364136223846793005ULL + 1;
        auto last = static_cast<std::int64_t>(state % totalNanos);
        if (last < first)
            std::swap(first, last);
        if (first == last)
            ++last;
        checkInterval(first, last);
    }
}

BOOST_AUTO_TEST_CASE(testMixedRateDecimalOracle) {
    BOOST_TEST_MESSAGE("Testing variance-clock mixed rates against a decimal oracle...");

    constexpr std::int64_t nanosPerSecond = 1000000000;
    constexpr std::int64_t slotNanos = 300 * nanosPerSecond;
    constexpr std::int64_t totalNanos = 2 * 86400 * nanosPerSecond;
    const std::array<const char*, 5> rates = {"0", "0.25", "1.5", "3.75", "17.25"};
    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(2 * 86400);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1), profile(2)};
    tables.dates = {{Date(1, January, 1970), 1}, {Date(2, January, 1970), 2}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    for (Size day = 0; day < 2; ++day)
        for (Size slot = 0; slot < 288; ++slot)
            tables.profiles[day].slots[slot].weight =
                std::stod(rates[(slot * 7 + day) % rates.size()]);
    const detail::VarianceClockNumericEngine engine(std::move(tables));

    const auto oracle = [&rates](std::int64_t start, std::int64_t end) -> HighPrecision {
        HighPrecision total("0");
        for (Size slot = 0; slot < 2 * 288; ++slot) {
            const auto left = std::max(start, static_cast<std::int64_t>(slot) * slotNanos);
            const auto right = std::min(end, static_cast<std::int64_t>(slot + 1) * slotNanos);
            if (left < right) {
                const Size day = slot / 288;
                const Size dailySlot = slot % 288;
                total += HighPrecision(rates[(dailySlot * 7 + day) % rates.size()]) *
                         HighPrecision(std::to_string(right - left)) /
                         HighPrecision("86400000000000");
            }
        }
        return total;
    };
    const auto asInstant = [](std::int64_t nanos) {
        return instant(nanos / nanosPerSecond, static_cast<std::uint32_t>(nanos % nanosPerSecond));
    };

    std::uint64_t state = 0x6a09e667f3bcc909ULL;
    for (Size i = 0; i < 64; ++i) {
        state = state * 6364136223846793005ULL + 1;
        auto first = static_cast<std::int64_t>(state % totalNanos);
        state = state * 6364136223846793005ULL + 1;
        auto last = static_cast<std::int64_t>(state % totalNanos);
        if (last < first)
            std::swap(first, last);
        if (first == last)
            ++last;
        const auto result =
            engine.remaining(asInstant(first), engine.prepareExpiry(asInstant(last)));
        BOOST_CHECK(result.status == detail::VarianceClockNumericStatus::Ok);
        checkWeightedDays(result.weightedDays, oracle(first, last));
        checkWeightedDays(engine.cumulativeFromCoverageStart(asInstant(last)).weightedDays,
                          oracle(0, last));
    }
}

BOOST_AUTO_TEST_CASE(testFutureProfileIsNotEligible) {
    BOOST_TEST_MESSAGE("Testing variance-clock profile and snapshot availability...");

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(3 * 86400);
    tables.availableFrom = instant(50);
    tables.profiles = {profile(71, 2.0), profile(3, 3.0), profile(19, 5.0)};
    tables.profiles[0].calibrationAsOf = instant(0);
    tables.profiles[1].calibrationAsOf = instant(86400 + 300);
    tables.profiles[2].calibrationAsOf = instant(3 * 86400 + 100);
    tables.dates = {
        {Date(3, January, 1970), 19}, {Date(2, January, 1970), 3}, {Date(1, January, 1970), 71}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    VarianceClock clock(makeVarianceClockSnapshot(std::move(tables)));
    const auto view = clock.capture();

    VarianceClockExpiryToken firstDay, nextDay, afterBoundary;
    BOOST_REQUIRE(view.prepareExpiry(instant(86400), firstDay) == VarianceClockStatus::Ok);
    BOOST_REQUIRE(view.prepareExpiry(instant(2 * 86400), nextDay) == VarianceClockStatus::Ok);
    BOOST_REQUIRE(view.prepareExpiry(instant(86401), afterBoundary) == VarianceClockStatus::Ok);

    const auto future = view.remaining(instant(100), afterBoundary);
    BOOST_CHECK(future.status == VarianceClockStatus::BeforeCalibration);
    BOOST_CHECK_EQUAL(future.weightedDays, 0.0);
    const auto eligible = view.remaining(instant(100), firstDay);
    BOOST_CHECK(eligible.status == VarianceClockStatus::Ok);
    checkWeightedDays(eligible.weightedDays,
                      HighPrecision("2") * HighPrecision("86300") / HighPrecision("86400"));

    const auto unavailable = view.remaining(instant(1), firstDay);
    BOOST_CHECK(unavailable.status == VarianceClockStatus::BeforeCalibration);
    BOOST_CHECK_EQUAL(unavailable.weightedDays, 0.0);
    const auto atAvailability = view.remaining(instant(50), firstDay);
    BOOST_CHECK(atAvailability.status == VarianceClockStatus::Ok);
    checkWeightedDays(atAvailability.weightedDays,
                      HighPrecision("2") * HighPrecision("86350") / HighPrecision("86400"));
    const auto emptyCumulative = view.cumulativeFromCoverageStart(instant(0));
    BOOST_CHECK(emptyCumulative.status == VarianceClockStatus::Ok);
    BOOST_CHECK_EQUAL(emptyCumulative.weightedDays, 0.0);
    const auto atBoundary = view.cumulativeFromCoverageStart(instant(86400));
    BOOST_CHECK(atBoundary.status == VarianceClockStatus::Ok);
    checkWeightedDays(atBoundary.weightedDays, HighPrecision("2"));
    const auto futureCumulative = view.cumulativeFromCoverageStart(instant(86400 + 100));
    BOOST_CHECK(futureCumulative.status == VarianceClockStatus::BeforeCalibration);
    BOOST_CHECK_EQUAL(futureCumulative.weightedDays, 0.0);
    const auto availableCumulative = view.cumulativeFromCoverageStart(instant(86400 + 300));
    BOOST_CHECK(availableCumulative.status == VarianceClockStatus::Ok);
    checkWeightedDays(availableCumulative.weightedDays,
                      HighPrecision("2") +
                          HighPrecision("3") * HighPrecision("300") / HighPrecision("86400"));
    const auto laterEligible = view.remaining(instant(86400 + 300), nextDay);
    BOOST_CHECK(laterEligible.status == VarianceClockStatus::Ok);
    checkWeightedDays(laterEligible.weightedDays,
                      HighPrecision("3") * HighPrecision("86100") / HighPrecision("86400"));
}

BOOST_AUTO_TEST_CASE(testViewStatusPrecedenceAndTokenSafety) {
    BOOST_TEST_MESSAGE("Testing variance-clock view status precedence and token safety...");

    static_assert(std::is_trivially_copyable<VarianceClockResult>::value,
                  "the numeric result must be trivially copyable");
    static_assert(std::is_standard_layout<VarianceClockResult>::value,
                  "the numeric result must have standard layout");
    static_assert(
        noexcept(std::declval<const VarianceClockView&>().prepareExpiry(
            std::declval<VarianceClockInstant>(), std::declval<VarianceClockExpiryToken&>())),
        "expiry preparation must not throw");
    static_assert(noexcept(std::declval<const VarianceClockView&>().cumulativeFromCoverageStart(
                      std::declval<VarianceClockInstant>())),
                  "cumulative query must not throw");
    static_assert(
        noexcept(std::declval<const VarianceClockView&>().remaining(
            std::declval<VarianceClockInstant>(), std::declval<const VarianceClockExpiryToken&>())),
        "remaining query must not throw");

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(86400);
    tables.availableFrom = instant(0);
    tables.profiles = {profile(1)};
    tables.dates = {{Date(1, January, 1970), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    auto otherTables = tables;
    auto unavailableTables = tables;
    unavailableTables.availableFrom = instant(600);
    VarianceClock first(makeVarianceClockSnapshot(std::move(tables)));
    VarianceClock second(makeVarianceClockSnapshot(std::move(otherTables)));
    VarianceClock unavailable(makeVarianceClockSnapshot(std::move(unavailableTables)));
    const auto view = first.capture();
    const auto sameGeneration = first.capture();
    const auto other = second.capture();
    const auto notYetAvailable = unavailable.capture();
    const VarianceClockView invalidView;
    const VarianceClockExpiryToken invalidToken;
    VarianceClockExpiryToken token;
    BOOST_REQUIRE(view.prepareExpiry(instant(300), token) == VarianceClockStatus::Ok);
    checkInstant(view.coverageStart(), 0);
    checkInstant(view.coverageEnd(), 86400);
    BOOST_CHECK(!invalidView.coverageStart().isValid());
    BOOST_CHECK(!invalidView.coverageEnd().isValid());

    const auto checkError = [](const VarianceClockResult& result, VarianceClockStatus expected) {
        BOOST_CHECK(result.status == expected);
        BOOST_CHECK_EQUAL(result.weightedDays, 0.0);
    };
    checkError(invalidView.remaining(VarianceClockInstant(), invalidToken),
               VarianceClockStatus::InvalidView);
    checkError(view.remaining(VarianceClockInstant(), invalidToken),
               VarianceClockStatus::InvalidToken);
    checkError(other.remaining(VarianceClockInstant(), token), VarianceClockStatus::StaleToken);
    checkError(view.remaining(VarianceClockInstant(), token), VarianceClockStatus::InvalidInstant);
    checkError(view.remaining(instant(-1), token), VarianceClockStatus::OutOfCoverage);
    checkError(view.remaining(instant(86401), token), VarianceClockStatus::OutOfCoverage);
    checkError(invalidView.cumulativeFromCoverageStart(VarianceClockInstant()),
               VarianceClockStatus::InvalidView);
    checkError(view.cumulativeFromCoverageStart(VarianceClockInstant()),
               VarianceClockStatus::InvalidInstant);
    checkError(view.cumulativeFromCoverageStart(instant(86401)),
               VarianceClockStatus::OutOfCoverage);

    BOOST_CHECK(invalidView.prepareExpiry(instant(700), token) == VarianceClockStatus::InvalidView);
    BOOST_CHECK(view.prepareExpiry(VarianceClockInstant(), token) ==
                VarianceClockStatus::InvalidInstant);
    BOOST_CHECK(view.prepareExpiry(instant(86401), token) == VarianceClockStatus::OutOfCoverage);
    const auto preserved = view.remaining(instant(299), token);
    BOOST_CHECK(preserved.status == VarianceClockStatus::Ok);
    const HighPrecision preservedOracle = HighPrecision("1") / HighPrecision("86400");
    checkWeightedDays(preserved.weightedDays, preservedOracle);
    QL_CHECK_SMALL(varianceClockAsReal(preserved) - Real(preservedOracle.convert_to<double>()),
                   1e-15);
    const auto crossView = sameGeneration.remaining(instant(150), token);
    BOOST_CHECK(crossView.status == VarianceClockStatus::Ok);
    checkWeightedDays(crossView.weightedDays, HighPrecision("150") / HighPrecision("86400"));
    BOOST_CHECK_THROW(varianceClockAsReal(view.remaining(VarianceClockInstant(), token)), Error);

    VarianceClockExpiryToken unavailableExpiry;
    BOOST_REQUIRE(notYetAvailable.prepareExpiry(instant(300), unavailableExpiry) ==
                  VarianceClockStatus::Ok);
    checkError(notYetAvailable.remaining(instant(299), unavailableExpiry),
               VarianceClockStatus::BeforeCalibration);
    checkError(notYetAvailable.remaining(instant(300), unavailableExpiry),
               VarianceClockStatus::Expired);

    VarianceClockExpiryToken coverageEnd;
    BOOST_REQUIRE(view.prepareExpiry(instant(86400), coverageEnd) == VarianceClockStatus::Ok);
    checkError(view.remaining(instant(86400), coverageEnd), VarianceClockStatus::Expired);
    BOOST_CHECK_THROW(VarianceClock(std::unique_ptr<VarianceClockSnapshot>()), Error);
}

BOOST_AUTO_TEST_CASE(testAsOfAcrossMiddleRuns) {
    BOOST_TEST_MESSAGE("Testing variance-clock as-of maxima across middle runs...");

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(5 * 86400);
    tables.availableFrom = instant(0);
    tables.profiles = {profile(1, 1.0), profile(2, 0.0)};
    tables.profiles[1].calibrationAsOf = instant(4 * 86400);
    for (Size day = 0; day < 5; ++day)
        tables.dates.push_back(
            {Date(1, January, 1970) + static_cast<Integer>(day), day == 2 ? 2U : 1U});
    tables.offsets = {{tables.start, tables.end, 0, false}};
    VarianceClock clock(makeVarianceClockSnapshot(std::move(tables)));
    const auto view = clock.capture();
    VarianceClockExpiryToken expiry;
    BOOST_REQUIRE(view.prepareExpiry(instant(4 * 86400), expiry) == VarianceClockStatus::Ok);
    const auto includingFuture = view.remaining(instant(1), expiry);
    BOOST_CHECK(includingFuture.status == VarianceClockStatus::BeforeCalibration);
    BOOST_CHECK_EQUAL(includingFuture.weightedDays, 0.0);
    const auto excludingFuture = view.remaining(instant(3 * 86400), expiry);
    BOOST_CHECK(excludingFuture.status == VarianceClockStatus::Ok);
    checkWeightedDays(excludingFuture.weightedDays, HighPrecision("1"));
    const auto cumulativeFuture = view.cumulativeFromCoverageStart(instant(3 * 86400));
    BOOST_CHECK(cumulativeFuture.status == VarianceClockStatus::BeforeCalibration);
    BOOST_CHECK_EQUAL(cumulativeFuture.weightedDays, 0.0);
    const auto cumulativeEligible = view.cumulativeFromCoverageStart(instant(4 * 86400));
    BOOST_CHECK(cumulativeEligible.status == VarianceClockStatus::Ok);
    checkWeightedDays(cumulativeEligible.weightedDays, HighPrecision("3"));
}

BOOST_AUTO_TEST_CASE(testRandomizedEligibilityAgainstBruteForce) {
    BOOST_TEST_MESSAGE("Testing variance-clock eligibility against a brute-force oracle...");

    constexpr Size days = 37;
    constexpr std::int64_t secondsPerDay = 86400;
    constexpr std::int64_t end = days * secondsPerDay;
    constexpr std::int64_t availableFrom = 4 * secondsPerDay + 123;
    const std::array<VarianceClockProfileId, 5> ids = {71, 3, 201, 19, 7};
    const std::array<std::int64_t, 5> asOf = {
        0, 3 * secondsPerDay, 12 * secondsPerDay, 25 * secondsPerDay, end + 1};
    std::array<Size, days> selected{};

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(end);
    tables.availableFrom = instant(availableFrom);
    for (Size i = 0; i < ids.size(); ++i) {
        tables.profiles.push_back(profile(ids[i], i == 2 ? 0.0 : 1.0 + i));
        tables.profiles.back().calibrationAsOf = instant(asOf[i]);
    }
    for (Size day = 0; day < days; ++day) {
        selected[day] = (7 * day + day / 3 + 1) % ids.size();
        tables.dates.push_back(
            {Date(1, January, 1970) + static_cast<Integer>(day), ids[selected[day]]});
    }
    tables.offsets = {{tables.start, tables.end, 0, false}};
    VarianceClock clock(makeVarianceClockSnapshot(std::move(tables)));
    const auto view = clock.capture();

    std::uint64_t state = 0xc1a0c5eedULL;
    const auto random = [&state]() {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        return state;
    };
    std::array<Size, 3> outcomes{};
    for (Size i = 0; i < 4096; ++i) {
        std::int64_t valuation = static_cast<std::int64_t>(random() % (end + 1));
        std::int64_t expiry = static_cast<std::int64_t>(random() % (end + 1));
        if (i % 8 == 0)
            valuation = static_cast<std::int64_t>(random() % (days + 1)) * secondsPerDay;
        if (i % 8 == 1)
            expiry = static_cast<std::int64_t>(random() % (days + 1)) * secondsPerDay;

        VarianceClockStatus expected = VarianceClockStatus::Ok;
        if (valuation >= expiry) {
            expected = VarianceClockStatus::Expired;
        } else if (valuation < availableFrom) {
            expected = VarianceClockStatus::BeforeCalibration;
        } else {
            for (Size day = 0; day < days; ++day) {
                const auto dayStart = static_cast<std::int64_t>(day) * secondsPerDay;
                if (dayStart < expiry && valuation < dayStart + secondsPerDay &&
                    asOf[selected[day]] > valuation)
                    expected = VarianceClockStatus::BeforeCalibration;
            }
        }

        VarianceClockExpiryToken token;
        BOOST_REQUIRE(view.prepareExpiry(instant(expiry), token) == VarianceClockStatus::Ok);
        const auto result = view.remaining(instant(valuation), token);
        BOOST_CHECK_MESSAGE(result.status == expected,
                            "eligibility mismatch at " << valuation << " to " << expiry);
        if (expected == VarianceClockStatus::Ok) {
            ++outcomes[0];
        } else {
            BOOST_CHECK_EQUAL(result.weightedDays, 0.0);
            ++outcomes[expected == VarianceClockStatus::Expired ? 1 : 2];
        }

        bool cumulativeEligible = valuation == 0 || valuation >= availableFrom;
        for (Size day = 0; day < days && cumulativeEligible; ++day) {
            const auto dayStart = static_cast<std::int64_t>(day) * secondsPerDay;
            if (dayStart < valuation && asOf[selected[day]] > valuation)
                cumulativeEligible = false;
        }
        const auto cumulative = view.cumulativeFromCoverageStart(instant(valuation));
        const auto expectedCumulative =
            cumulativeEligible ? VarianceClockStatus::Ok : VarianceClockStatus::BeforeCalibration;
        BOOST_CHECK_MESSAGE(cumulative.status == expectedCumulative,
                            "cumulative eligibility mismatch at " << valuation);
        if (!cumulativeEligible)
            BOOST_CHECK_EQUAL(cumulative.weightedDays, 0.0);
    }
    for (Size count : outcomes)
        BOOST_CHECK_GT(count, 0);
}

BOOST_AUTO_TEST_CASE(testFixedViewLifetimeAndZeroRates) {
    BOOST_TEST_MESSAGE("Testing variance-clock fixed-view lifetime and zero rates...");

    VarianceClockView retained;
    VarianceClockExpiryToken token;
    {
        VarianceClockTables tables;
        tables.start = instant(0);
        tables.end = instant(86400);
        tables.availableFrom = instant(0);
        tables.profiles = {profile(1, 0.0)};
        tables.dates = {{Date(1, January, 1970), 1}};
        tables.offsets = {{tables.start, tables.end, 0, false}};
        VarianceClock clock(makeVarianceClockSnapshot(std::move(tables)));
        retained = clock.capture();
        BOOST_REQUIRE(retained.prepareExpiry(instant(300), token) == VarianceClockStatus::Ok);
        const auto zero = retained.remaining(instant(0), token);
        BOOST_CHECK(zero.status == VarianceClockStatus::Ok);
        BOOST_CHECK_EQUAL(zero.weightedDays, 0.0);
#ifndef NDEBUG
        token = VarianceClockExpiryToken();
        retained = VarianceClockView();
#endif
    }
#ifdef NDEBUG
    const auto afterOwner = retained.remaining(instant(0), token);
    BOOST_CHECK(afterOwner.status == VarianceClockStatus::Ok);
    BOOST_CHECK_EQUAL(afterOwner.weightedDays, 0.0);
#endif
}

BOOST_AUTO_TEST_CASE(testOldTokenRejectedAfterABA) {
    BOOST_TEST_MESSAGE("Testing variance-clock token invalidation after A-B-A activation...");

    const auto makeTables = [](double weight) {
        VarianceClockTables tables;
        tables.start = instant(0);
        tables.end = instant(86400);
        tables.availableFrom = instant(0);
        tables.profiles = {profile(1, weight)};
        tables.dates = {{Date(1, January, 1970), 1}};
        tables.offsets = {{tables.start, tables.end, 0, false}};
        return tables;
    };

    VarianceClock clock(makeVarianceClockSnapshot(makeTables(1.0)));
    const auto firstA = clock.capture();
    VarianceClockExpiryToken firstAToken;
    BOOST_REQUIRE(firstA.prepareExpiry(instant(600), firstAToken) == VarianceClockStatus::Ok);

    clock.activate(makeVarianceClockSnapshot(makeTables(2.0)));
    const auto viewB = clock.capture();
    VarianceClockExpiryToken tokenB;
    BOOST_REQUIRE(viewB.prepareExpiry(instant(600), tokenB) == VarianceClockStatus::Ok);
    const auto resultB = viewB.remaining(instant(0), tokenB);
    BOOST_REQUIRE(resultB.status == VarianceClockStatus::Ok);
    checkWeightedDays(resultB.weightedDays,
                      HighPrecision("2") * HighPrecision("600") / HighPrecision("86400"));
    const auto oldAWhileBActive = firstA.remaining(instant(0), firstAToken);
    BOOST_REQUIRE(oldAWhileBActive.status == VarianceClockStatus::Ok);
    checkWeightedDays(oldAWhileBActive.weightedDays,
                      HighPrecision("600") / HighPrecision("86400"));
    const auto staleOnB = viewB.remaining(instant(0), firstAToken);
    BOOST_CHECK(staleOnB.status == VarianceClockStatus::StaleToken);
    BOOST_CHECK_EQUAL(staleOnB.weightedDays, 0.0);

    BOOST_CHECK_EXCEPTION(clock.activate(nullptr), Error,
                          [](const Error&) { return true; });
    const auto stillB = viewB.remaining(instant(0), tokenB);
    BOOST_CHECK(stillB.status == VarianceClockStatus::Ok);

    clock.activate(makeVarianceClockSnapshot(makeTables(1.0)));
    const auto secondA = clock.capture();
    const auto stale = secondA.remaining(instant(0), firstAToken);
    BOOST_CHECK(stale.status == VarianceClockStatus::StaleToken);
    BOOST_CHECK_EQUAL(stale.weightedDays, 0.0);

    VarianceClockExpiryToken secondAToken;
    BOOST_REQUIRE(secondA.prepareExpiry(instant(600), secondAToken) == VarianceClockStatus::Ok);
    const auto resultA = secondA.remaining(instant(0), secondAToken);
    BOOST_REQUIRE(resultA.status == VarianceClockStatus::Ok);
    checkWeightedDays(resultA.weightedDays,
                      HighPrecision("600") / HighPrecision("86400"));
}

BOOST_AUTO_TEST_CASE(testReclaimWaitsForViewsAndTokens) {
    BOOST_TEST_MESSAGE("Testing variance-clock control-thread reclamation...");

    auto makeTables = [](double weight) {
        VarianceClockTables tables;
        tables.start = instant(0);
        tables.end = instant(86400);
        tables.availableFrom = instant(0);
        tables.profiles = {profile(1, weight)};
        tables.dates = {{Date(1, January, 1970), 1}};
        tables.offsets = {{tables.start, tables.end, 0, false}};
        return tables;
    };

    VarianceClock clock(makeVarianceClockSnapshot(makeTables(1.0)));
    auto retiredView = clock.capture();
    VarianceClockExpiryToken retiredToken;
    BOOST_REQUIRE(retiredView.prepareExpiry(instant(600), retiredToken) ==
                  VarianceClockStatus::Ok);
    clock.activate(makeVarianceClockSnapshot(makeTables(2.0)));

    BOOST_CHECK_EQUAL(clock.reclaim(), 0U);
    BOOST_CHECK(retiredView.remaining(instant(0), retiredToken).status ==
                VarianceClockStatus::Ok);
    retiredView = VarianceClockView();
    BOOST_CHECK_EQUAL(clock.reclaim(), 0U);
    retiredToken = VarianceClockExpiryToken();

    const Size reclaimed = clock.reclaim();
    BOOST_CHECK_EQUAL(reclaimed, 1U);
    const auto active = clock.capture();
    VarianceClockExpiryToken activeToken;
    BOOST_REQUIRE(active.prepareExpiry(instant(600), activeToken) ==
                  VarianceClockStatus::Ok);
    BOOST_CHECK(active.remaining(instant(0), activeToken).status ==
                VarianceClockStatus::Ok);
}

BOOST_AUTO_TEST_CASE(testShutdownWaitsForActiveGenerationHandles) {
    BOOST_TEST_MESSAGE("Testing variance-clock shutdown with active handles...");

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(86400);
    tables.availableFrom = instant(0);
    tables.profiles = {profile(1)};
    tables.dates = {{Date(1, January, 1970), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};

    VarianceClock clock(makeVarianceClockSnapshot(std::move(tables)));
    auto activeView = clock.capture();
    VarianceClockExpiryToken activeToken;
    BOOST_REQUIRE(activeView.prepareExpiry(instant(600), activeToken) ==
                  VarianceClockStatus::Ok);

    BOOST_CHECK(!clock.shutdown());
    BOOST_CHECK(activeView.remaining(instant(0), activeToken).status ==
                VarianceClockStatus::Ok);

    activeView = VarianceClockView();
    activeToken = VarianceClockExpiryToken();
    BOOST_CHECK(clock.shutdown());
}

BOOST_AUTO_TEST_CASE(testShutdownWaitsForHandlesAndIsTerminal) {
    BOOST_TEST_MESSAGE("Testing variance-clock busy and terminal shutdown...");

    const auto newTables = [] {
        VarianceClockTables replacement;
        replacement.start = instant(0);
        replacement.end = instant(86400);
        replacement.availableFrom = instant(0);
        replacement.profiles = {profile(1)};
        replacement.dates = {{Date(1, January, 1970), 1}};
        replacement.offsets = {{replacement.start, replacement.end, 0, false}};
        return replacement;
    };

    VarianceClock clock(makeVarianceClockSnapshot(newTables()));

    auto liveView = clock.capture();
    VarianceClockExpiryToken liveToken;
    BOOST_REQUIRE(liveView.prepareExpiry(instant(600), liveToken) ==
                  VarianceClockStatus::Ok);
    clock.activate(makeVarianceClockSnapshot(newTables()));
    BOOST_CHECK(!clock.shutdown());
    BOOST_CHECK(liveView.remaining(instant(0), liveToken).status ==
                VarianceClockStatus::Ok);
    auto stillActive = clock.capture();
    VarianceClockExpiryToken activeToken;
    BOOST_REQUIRE(stillActive.prepareExpiry(instant(600), activeToken) ==
                  VarianceClockStatus::Ok);
    BOOST_CHECK(stillActive.remaining(instant(0), activeToken).status ==
                VarianceClockStatus::Ok);

    stillActive = VarianceClockView();
    activeToken = VarianceClockExpiryToken();
    BOOST_CHECK(!clock.shutdown());
    BOOST_CHECK(liveView.remaining(instant(0), liveToken).status ==
                VarianceClockStatus::Ok);
    liveView = VarianceClockView();
    liveToken = VarianceClockExpiryToken();
    BOOST_CHECK(clock.shutdown());
    BOOST_CHECK(!clock.capture().coverageStart().isValid());
    BOOST_CHECK_EXCEPTION(
        clock.activate(makeVarianceClockSnapshot(newTables())), Error,
        [](const Error&) { return true; });
    BOOST_CHECK(clock.shutdown());
}

BOOST_AUTO_TEST_CASE(testConcurrentCaptureNeverMixesSnapshots) {
    BOOST_TEST_MESSAGE("Testing variance-clock concurrent capture and activation...");

    const auto makeTables = [](double weight) {
        VarianceClockTables tables;
        tables.start = instant(0);
        tables.end = instant(86400);
        tables.availableFrom = instant(0);
        tables.profiles = {profile(1, weight)};
        tables.dates = {{Date(1, January, 1970), 1}};
        tables.offsets = {{tables.start, tables.end, 0, false}};
        return tables;
    };
    const auto makeSnapshot = [&makeTables](double weight) {
        return makeVarianceClockSnapshot(makeTables(weight));
    };

    VarianceClock clock(makeSnapshot(1.0));
    auto pinnedView = clock.capture();
    VarianceClockExpiryToken pinnedToken;
    BOOST_REQUIRE(pinnedView.prepareExpiry(instant(600), pinnedToken) ==
                  VarianceClockStatus::Ok);

    const double oneRate = 600.0 / 86400.0;
    const double twoRates = 2.0 * oneRate;
    const auto matchesSingleGeneration = [oneRate, twoRates](
                                             const VarianceClockResult& result) {
        return result.status == VarianceClockStatus::Ok &&
               (std::abs(result.weightedDays - oneRate) <= 1e-15 ||
                std::abs(result.weightedDays - twoRates) <= 1e-15);
    };
    const VarianceClockResult injectedMixedResult{
        VarianceClockStatus::Ok, (oneRate + twoRates) / 2.0};
    BOOST_CHECK_MESSAGE(!matchesSingleGeneration(injectedMixedResult),
                        "single-generation oracle accepted an injected mixed result");

    clock.activate(makeSnapshot(2.0));
    {
        const auto newView = clock.capture();
        const auto stale = newView.remaining(instant(0), pinnedToken);
        BOOST_CHECK(stale.status == VarianceClockStatus::StaleToken);
        BOOST_CHECK_EQUAL(stale.weightedDays, 0.0);
    }

    constexpr std::size_t activationCount = 256;
    constexpr std::size_t readerIterations = 2000;
    std::vector<std::unique_ptr<VarianceClockSnapshot>> candidates;
    candidates.reserve(activationCount);
    for (std::size_t i = 0; i != activationCount; ++i)
        candidates.push_back(makeSnapshot(i % 2 == 0 ? 1.0 : 2.0));

    std::mutex startMutex;
    std::condition_variable startCondition;
    unsigned readyThreads = 0;
    bool start = false;
    const auto waitForStart = [&] {
        std::unique_lock<std::mutex> lock(startMutex);
        ++readyThreads;
        startCondition.notify_all();
        startCondition.wait(lock, [&] { return start; });
    };

    std::atomic<unsigned> invalidResults{0};
    const auto reader = [&] {
        waitForStart();
        for (std::size_t i = 0; i != readerIterations; ++i) {
            const auto view = clock.capture();
            VarianceClockExpiryToken token;
            if (view.prepareExpiry(instant(600), token) != VarianceClockStatus::Ok) {
                invalidResults.fetch_add(1, std::memory_order_relaxed);
                continue;
            }
            if (!matchesSingleGeneration(view.remaining(instant(0), token)))
                invalidResults.fetch_add(1, std::memory_order_relaxed);
        }
    };
    const auto writer = [&] {
        waitForStart();
        for (auto& candidate : candidates)
            clock.activate(std::move(candidate));
    };

    std::thread firstReader(reader);
    std::thread secondReader(reader);
    std::thread activationWriter(writer);
    {
        std::unique_lock<std::mutex> lock(startMutex);
        startCondition.wait(lock, [&] { return readyThreads == 3; });
        start = true;
    }
    startCondition.notify_all();

    firstReader.join();
    secondReader.join();
    activationWriter.join();

    BOOST_CHECK_EQUAL(invalidResults.load(std::memory_order_relaxed), 0U);
    BOOST_CHECK(matchesSingleGeneration(pinnedView.remaining(instant(0), pinnedToken)));
    BOOST_CHECK_EQUAL(clock.reclaim(), activationCount);
    pinnedView = VarianceClockView();
    pinnedToken = VarianceClockExpiryToken();
    BOOST_CHECK_EQUAL(clock.reclaim(), 1U);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
