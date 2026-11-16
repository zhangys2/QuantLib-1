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
#include <boost/test/unit_test.hpp>
#include <cmath>
#include <cstdint>
#include <limits>
#include <string>
#include <utility>

using namespace QuantLib;

namespace {

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

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
