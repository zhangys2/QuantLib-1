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
#include <ql/errors.hpp>
#include <ql/time/varianceclockdetail.hpp>
#include <boost/multiprecision/cpp_dec_float.hpp>
#include <boost/test/unit_test.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <utility>

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
    const auto minimum = (static_cast<std::int64_t>(Date::minDate().serialNumber()) - epoch) * 86400;
    const auto maximum = (static_cast<std::int64_t>(Date::maxDate().serialNumber()) - epoch) * 86400;

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
    const HighPrecision reference = HighPrecision("100") * HighPrecision("0.001") /
                                    HighPrecision("86400");
    checkWeightedDays(result.weightedDays, reference);
}

BOOST_AUTO_TEST_CASE(testNumericBoundariesAndStatuses) {
    BOOST_TEST_MESSAGE("Testing variance-clock slot boundaries and numeric statuses...");

    using Engine = detail::VarianceClockNumericEngine;
    using Position = detail::VarianceClockNumericPosition;
    static_assert(noexcept(std::declval<const Engine&>().prepareExpiry(
                      std::declval<VarianceClockInstant>())),
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

    const auto sameSlot = engine.remaining(instant(200), engine.prepareExpiry(instant(200, 500000000)));
    BOOST_CHECK(sameSlot.status == detail::VarianceClockNumericStatus::Ok);
    checkWeightedDays(sameSlot.weightedDays, HighPrecision("2") * HighPrecision("0.5") /
                                                HighPrecision("86400"));

    const auto before = instant(299, 999000000);
    const auto boundary = instant(300);
    const auto after = instant(300, 1000000);
    const auto left = engine.remaining(before, engine.prepareExpiry(boundary));
    const auto right = engine.remaining(boundary, engine.prepareExpiry(after));
    const auto both = engine.remaining(before, engine.prepareExpiry(after));
    checkWeightedDays(left.weightedDays, HighPrecision("2") * HighPrecision("0.001") /
                                            HighPrecision("86400"));
    checkWeightedDays(right.weightedDays, HighPrecision("3") * HighPrecision("0.001") /
                                             HighPrecision("86400"));
    const HighPrecision across = (HighPrecision("2") + HighPrecision("3")) *
                                 HighPrecision("0.001") / HighPrecision("86400");
    checkWeightedDays(both.weightedDays, across);
    checkWeightedDays(left.weightedDays + right.weightedDays, across);

    const auto startValue = engine.cumulativeFromCoverageStart(instant(100, 250000000));
    BOOST_CHECK(startValue.status == detail::VarianceClockNumericStatus::Ok);
    BOOST_CHECK_EQUAL(startValue.weightedDays, 0.0);
    const auto endValue = engine.cumulativeFromCoverageStart(instant(900, 750000000));
    BOOST_CHECK(endValue.status == detail::VarianceClockNumericStatus::Ok);
    const HighPrecision full = (HighPrecision("2") * HighPrecision("199.75") +
                                HighPrecision("3") * HighPrecision("300") +
                                HighPrecision("4") * HighPrecision("0.75")) /
                               HighPrecision("86400");
    checkWeightedDays(endValue.weightedDays, full);
    checkWeightedDays(engine.remaining(instant(100, 250000000),
                                       engine.prepareExpiry(instant(900, 750000000))).weightedDays,
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
    checkWeightedDays(springEngine.remaining(instant(1710046800),
                                             springEngine.prepareExpiry(instant(1710129600))).weightedDays,
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
    checkWeightedDays(unitEngine.remaining(instant(1730606400),
                                           unitEngine.prepareExpiry(instant(1730696400))).weightedDays,
                      HighPrecision("25") / HighPrecision("24"));

    for (Size slot = 12; slot < 24; ++slot)
        fall.profiles[0].slots[slot].weight = 3.0;
    const detail::VarianceClockNumericEngine fallEngine(std::move(fall));
    checkWeightedDays(fallEngine.remaining(instant(1730606400),
                                           fallEngine.prepareExpiry(instant(1730696400))).weightedDays,
                      HighPrecision("29") / HighPrecision("24"));
    checkWeightedDays(fallEngine.remaining(instant(1730610000),
                                           fallEngine.prepareExpiry(instant(1730613600))).weightedDays,
                      HighPrecision("3") / HighPrecision("24"));
    checkWeightedDays(fallEngine.remaining(instant(1730613600),
                                           fallEngine.prepareExpiry(instant(1730617200))).weightedDays,
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
    checkWeightedDays(dateResult.weightedDays,
                      (HighPrecision("2") + HighPrecision("5")) * HighPrecision("0.001") /
                          HighPrecision("86400"));
    const auto dateFull = dateEngine.cumulativeFromCoverageStart(instant(86500, 750000000));
    checkWeightedDays(dateFull.weightedDays,
                      (HighPrecision("2") * HighPrecision("99.75") +
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
    checkWeightedDays(negativeResult.weightedDays,
                      (HighPrecision("2") + HighPrecision("5")) * HighPrecision("0.001") /
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
    checkWeightedDays(offsetResult.weightedDays,
                      (HighPrecision("2") + HighPrecision("3")) * HighPrecision("0.001") /
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
    const auto nanosecondResult = extremeEngine.remaining(
        instant(299, 999999999), extremeEngine.prepareExpiry(instant(300)));
    checkWeightedDays(nanosecondResult.weightedDays,
                      HighPrecision("1e308") * HighPrecision("0.000000001") /
                          HighPrecision("86400"));

    VarianceClockTables maximum;
    maximum.start = instant(0);
    maximum.end = instant(0, 1000000);
    maximum.availableFrom = instant(-1);
    maximum.profiles = {profile(1, std::numeric_limits<double>::max())};
    maximum.dates = {{Date(1, January, 1970), 1}};
    maximum.offsets = {{maximum.start, maximum.end, 0, false}};
    const detail::VarianceClockNumericEngine maximumEngine(std::move(maximum));
    const auto maximumResult = maximumEngine.remaining(
        instant(0), maximumEngine.prepareExpiry(instant(0, 1000000)));
    BOOST_CHECK(std::isfinite(maximumResult.weightedDays));
    checkWeightedDays(maximumResult.weightedDays, HighPrecision("1.7976931348623157e308") *
                                                    HighPrecision("0.001") / HighPrecision("86400"));

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
    const auto longResult = longEngine.remaining(instant(150, 250000000),
                                                 longEngine.prepareExpiry(instant(end - 100, 750000000)),
                                                 &visited);
    const HighPrecision elapsed = HighPrecision(std::to_string(end)) - HighPrecision("249.5");
    checkWeightedDays(longResult.weightedDays, HighPrecision("2") * elapsed / HighPrecision("86400"));
    std::size_t depth = 0;
    for (Size n = days; n > 1; n = (n + 1) / 2)
        ++depth;
    BOOST_CHECK_LE(visited, 4 * depth + 64);
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
            tables.profiles[day].slots[slot].weight = std::stod(rates[(slot * 7 + day) % rates.size()]);
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
        const auto result = engine.remaining(asInstant(first), engine.prepareExpiry(asInstant(last)));
        BOOST_CHECK(result.status == detail::VarianceClockNumericStatus::Ok);
        checkWeightedDays(result.weightedDays, oracle(first, last));
        checkWeightedDays(engine.cumulativeFromCoverageStart(asInstant(last)).weightedDays,
                          oracle(0, last));
    }
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
