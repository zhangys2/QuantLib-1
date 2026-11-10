/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2026

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
#include <ql/time/calendars/target.hpp>
#include <ql/time/variancecalendar.hpp>
#include <boost/test/unit_test.hpp>

using namespace QuantLib;

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
