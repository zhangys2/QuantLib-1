/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2026 JOHN SAM

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
#include <ql/time/calendars/bespokecalendar.hpp>
#include <ql/time/calendars/target.hpp>
#include <ql/time/variancecalendar.hpp>
#include <boost/test/unit_test.hpp>
#include <limits>

using namespace QuantLib;

BOOST_FIXTURE_TEST_SUITE(QuantLibTests, TopLevelFixture)

BOOST_AUTO_TEST_SUITE(VarianceCalendarTests)

BOOST_AUTO_TEST_CASE(variance_calendar_weights) {
    BOOST_TEST_MESSAGE("Testing variance-calendar categories and weights...");

    VarianceCalendar::Profile common{0, std::vector<Real>(289, 2.0)};
    common.values[0] = 0.0;
    common.values[1] = 10.0;
    VarianceCalendar::Profile monday{60, std::vector<Real>{4.0, 8.0}};
    VarianceCalendar::WeekdayProfiles profiles{{Monday, monday}};
    VarianceCalendar::CategoryWeights categoryWeights{{3.0, 5.0, 7.0}};
    VarianceCalendar varianceCalendar(categoryWeights, common, profiles, TARGET());

    const Date holiday(25, December, 2024);
    const Date weekend(6, January, 2024);
    const Date weekday(8, January, 2024);
    BOOST_CHECK(varianceCalendar.category(holiday) == VarianceDayCategory::Holiday);
    BOOST_CHECK(varianceCalendar.category(weekend) == VarianceDayCategory::Weekend);
    BOOST_CHECK(varianceCalendar.category(weekday) == VarianceDayCategory::Weekday);
    QL_CHECK_CLOSE(varianceCalendar.weight(weekday, 62.5), 3.0 * 6.0, 1E-12);
    QL_CHECK_CLOSE(varianceCalendar.weight(weekday, 30.0), 3.0 * 4.0, 1E-12);
    QL_CHECK_CLOSE(varianceCalendar.weight(weekday, 120.0), 3.0 * 8.0, 1E-12);
    QL_CHECK_CLOSE(varianceCalendar.weight(holiday, 2.5), 7.0 * 5.0, 1E-12);
    QL_CHECK_CLOSE(varianceCalendar.weight(holiday, 1440.0), 7.0 * 2.0, 1E-12);
    QL_CHECK_CLOSE(varianceCalendar.weight(weekend, 720.0), 5.0 * 2.0, 1E-12);

    VarianceCalendar defaultCalendar;
    QL_CHECK_CLOSE(defaultCalendar.weight(weekday, 713.25), 1.0, 1E-12);
}

BOOST_AUTO_TEST_CASE(variance_calendar_validation) {
    BOOST_TEST_MESSAGE("Testing variance-calendar input validation...");

    VarianceCalendar::Profile invalid{0, std::vector<Real>(289, 1.0)};
    invalid.values[10] = -1.0;
    BOOST_CHECK_THROW(VarianceCalendar(VarianceCalendar::CategoryWeights{{1.0, 1.0, 1.0}},
                                       invalid), Error);
    BOOST_CHECK_THROW(
        VarianceCalendar(VarianceCalendar::CategoryWeights{{1.0, 1.0, 1.0}},
                         VarianceCalendar::Profile{1, std::vector<Real>(2, 1.0)}),
        Error);
    VarianceCalendar varianceCalendar;
    BOOST_CHECK_THROW(varianceCalendar.weight(Date(8, January, 2024), 1440.1), Error);
}

BOOST_AUTO_TEST_CASE(variance_calendar_validation_extra) {
    BOOST_TEST_MESSAGE("Testing variance-calendar rejection of NaN weights, "
                       "overlong profiles and invalid weekdays...");

    const VarianceCalendar::CategoryWeights nan{{1.0, std::numeric_limits<Real>::quiet_NaN(), 1.0}};
    BOOST_CHECK_THROW(VarianceCalendar{nan}, Error);

    // 1435 + 5 * 2 = 1445 minutes: runs past 24:00
    VarianceCalendar::Profile tooLong{1435, std::vector<Real>(3, 1.0)};
    BOOST_CHECK_THROW(VarianceCalendar(VarianceCalendar::CategoryWeights{{1.0, 1.0, 1.0}}, tooLong),
                      Error);

    VarianceCalendar::WeekdayProfiles badWeekday{
        {static_cast<Weekday>(0), VarianceCalendar::Profile()}};
    BOOST_CHECK_THROW(VarianceCalendar(VarianceCalendar::CategoryWeights{{1.0, 1.0, 1.0}},
                                       VarianceCalendar::Profile(), badWeekday),
                      Error);
}

BOOST_AUTO_TEST_CASE(variance_calendar_without_calendar) {
    BOOST_TEST_MESSAGE("Testing variance-calendar categories without a calendar...");

    VarianceCalendar::CategoryWeights categoryWeights{{3.0, 5.0, 7.0}};
    VarianceCalendar varianceCalendar(categoryWeights);

    // no calendar: only Saturday and Sunday are special, 25 Dec 2024 is a Wednesday
    BOOST_CHECK(varianceCalendar.category(Date(25, December, 2024)) ==
                VarianceDayCategory::Weekday);
    BOOST_CHECK(varianceCalendar.category(Date(6, January, 2024)) ==
                VarianceDayCategory::Weekend);
    BOOST_CHECK(varianceCalendar.category(Date(7, January, 2024)) ==
                VarianceDayCategory::Weekend);
    QL_CHECK_CLOSE(varianceCalendar.weight(Date(6, January, 2024), 600.0), 5.0, 1E-12);
}

BOOST_AUTO_TEST_CASE(variance_calendar_opened_weekend_day) {
    BOOST_TEST_MESSAGE("Testing variance-calendar classification of an opened weekend day...");

    // BespokeCalendar owns its implementation, so removeHoliday() does not leak
    // into other calendars (unlike TARGET, whose implementation is shared).
    BespokeCalendar bespoke;
    bespoke.addWeekend(Saturday);
    bespoke.addWeekend(Sunday);
    const Date saturday(6, January, 2024);
    const Date sunday(7, January, 2024);

    VarianceCalendar::Profile common{0, std::vector<Real>(289, 2.0)};
    VarianceCalendar::CategoryWeights categoryWeights{{3.0, 5.0, 7.0}};
    VarianceCalendar before(categoryWeights, common, VarianceCalendar::WeekdayProfiles(), bespoke);
    BOOST_CHECK(before.category(saturday) == VarianceDayCategory::Weekend);
    QL_CHECK_CLOSE(before.weight(saturday, 600.0), 5.0 * 2.0, 1E-12);

    bespoke.removeHoliday(saturday);
    VarianceCalendar opened(categoryWeights, common, VarianceCalendar::WeekdayProfiles(), bespoke);
    BOOST_CHECK(opened.category(saturday) == VarianceDayCategory::Weekday);
    QL_CHECK_CLOSE(opened.weight(saturday, 600.0), 3.0 * 2.0, 1E-12);
    // the next day is untouched
    BOOST_CHECK(opened.category(sunday) == VarianceDayCategory::Weekend);

    // a closed weekday is a holiday
    const Date monday(8, January, 2024);
    bespoke.addHoliday(monday);
    VarianceCalendar closed(categoryWeights, common, VarianceCalendar::WeekdayProfiles(), bespoke);
    BOOST_CHECK(closed.category(monday) == VarianceDayCategory::Holiday);
}

BOOST_AUTO_TEST_CASE(variance_calendar_weekday_profiles) {
    BOOST_TEST_MESSAGE("Testing variance-calendar weekday profile selection...");

    VarianceCalendar::Profile common{0, std::vector<Real>(289, 2.0)};
    VarianceCalendar::CategoryWeights categoryWeights{{3.0, 5.0, 7.0}};

    // An empty weekday entry flattens the day to an all-one profile.
    VarianceCalendar::WeekdayProfiles flat{{Monday, VarianceCalendar::Profile()}};
    VarianceCalendar flattened(categoryWeights, common, flat, TARGET());
    const Date monday(8, January, 2024);
    const Date tuesday(9, January, 2024);
    QL_CHECK_CLOSE(flattened.weight(monday, 0.0), 3.0, 1E-12);
    QL_CHECK_CLOSE(flattened.weight(tuesday, 0.0), 3.0 * 2.0, 1E-12);

    // A holiday keeps the profile of the weekday it falls on: 1 Jan 2024 is a
    // Monday and a TARGET holiday.
    VarianceCalendar::Profile mondayProfile{60, std::vector<Real>{4.0, 8.0}};
    VarianceCalendar::WeekdayProfiles profiles{{Monday, mondayProfile}};
    VarianceCalendar withProfile(categoryWeights, common, profiles, TARGET());
    const Date newYear(1, January, 2024);
    BOOST_CHECK(withProfile.category(newYear) == VarianceDayCategory::Holiday);
    QL_CHECK_CLOSE(withProfile.weight(newYear, 62.5), 7.0 * 6.0, 1E-12);
}

BOOST_AUTO_TEST_SUITE_END()

BOOST_AUTO_TEST_SUITE_END()
