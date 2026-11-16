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
#include <cstdint>
#include <limits>
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

    void checkInvalid(VarianceClockTables tables) {
        BOOST_CHECK_THROW(makeVarianceClockSnapshot(std::move(tables)), Error);
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

BOOST_AUTO_TEST_CASE(testInvalidTableStructure) {
    BOOST_TEST_MESSAGE("Testing variance-clock table validation...");

    auto tables = foldTables();
    tables.availableFrom = VarianceClockInstant();
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.profiles[0].calibrationAsOf = VarianceClockInstant();
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.profiles.push_back(profile(1));
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.dates.push_back(tables.dates.front());
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.dates[0].profile = 999;
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.dates.pop_back();
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.offsets[0].start = instant(1730613601);
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.offsets[0].start = instant(1730613599);
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.offsets[0].offsetSeconds = -18001;
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.offsets[0].end = VarianceClockInstant();
    checkInvalid(std::move(tables));
}

BOOST_AUTO_TEST_CASE(testInvalidAndOverflowingWeights) {
    BOOST_TEST_MESSAGE("Testing variance-clock rate and sum validation...");

    for (const double invalid : {std::numeric_limits<double>::quiet_NaN(),
                                 std::numeric_limits<double>::infinity(), -1.0}) {
        auto tables = foldTables();
        tables.profiles[0].slots[0].weight = invalid;
        checkInvalid(std::move(tables));
    }

    VarianceClockTables tables;
    tables.start = instant(0);
    tables.end = instant(172800);
    tables.availableFrom = instant(-1);
    tables.profiles = {profile(1, std::numeric_limits<double>::max())};
    tables.dates = {{Date(1, January, 1970), 1}, {Date(2, January, 1970), 1}};
    tables.offsets = {{tables.start, tables.end, 0, false}};
    checkInvalid(tables);

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
    checkInvalid(std::move(tables));

    tables = foldTables();
    tables.start = instant(std::numeric_limits<std::int64_t>::min() + 1);
    tables.end = instant(std::numeric_limits<std::int64_t>::min() + 10);
    tables.offsets = {{tables.start, tables.end, -300, false}};
    checkInvalid(std::move(tables));
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
