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

#include <ql/errors.hpp>
#include <ql/time/variancecalendar.hpp>
#include <cmath>

namespace QuantLib {

    namespace {
        void validateProfile(const VarianceCalendar::Profile& profile) {
            if (profile.values.empty())
                return;
            QL_REQUIRE(profile.startMinute >= 0 && profile.startMinute <= 1440 &&
                       profile.startMinute % 5 == 0,
                       "intraday profile start must be a five-minute time in [0, 1440]");
            QL_REQUIRE(profile.startMinute + 5 * (profile.values.size() - 1) <= 1440,
                       "intraday profile extends past 24:00");
            for (Real value : profile.values)
                QL_REQUIRE(std::isfinite(value) && value >= 0.0,
                           "intraday profile values must be finite and nonnegative");
        }
    }

    VarianceCalendar::VarianceCalendar(const CategoryWeights& categoryWeights,
                                       const Profile& defaultProfile,
                                       const WeekdayProfiles& weekdayProfiles,
                                       const Calendar& calendar)
    : categoryWeights_(categoryWeights), defaultProfile_(defaultProfile),
      weekdayProfiles_(weekdayProfiles), calendar_(calendar) {
        for (Real value : categoryWeights_)
            QL_REQUIRE(std::isfinite(value) && value >= 0.0,
                       "day-category weights must be finite and nonnegative");
        validateProfile(defaultProfile_);
        for (const auto& item : weekdayProfiles_) {
            QL_REQUIRE(item.first >= Sunday && item.first <= Saturday,
                       "invalid weekday in intraday profiles");
            validateProfile(item.second);
        }
    }

    VarianceDayCategory VarianceCalendar::category(const Date& date) const {
        const Weekday weekday = date.weekday();
        if (calendar_.empty())
            return (weekday == Saturday || weekday == Sunday) ? VarianceDayCategory::Weekend :
                                                                VarianceDayCategory::Weekday;
        // Business-day status comes first: a weekend day opened with
        // removeHoliday() is a business day and must not be classified as a weekend.
        if (calendar_.isBusinessDay(date))
            return VarianceDayCategory::Weekday;
        return calendar_.isWeekend(weekday) ? VarianceDayCategory::Weekend :
                                              VarianceDayCategory::Holiday;
    }

    const VarianceCalendar::Profile& VarianceCalendar::profile(Weekday weekday) const {
        const auto it = weekdayProfiles_.find(weekday);
        if (it != weekdayProfiles_.end())
            return it->second;
        return defaultProfile_;
    }

    Real VarianceCalendar::weight(const Date& date, Real minuteOfDay) const {
        QL_REQUIRE(std::isfinite(minuteOfDay) && minuteOfDay >= 0.0 && minuteOfDay <= 1440.0,
                   "minute of day must be finite and in [0, 1440]");

        const VarianceDayCategory dayCategory = category(date);
        const Size categoryIndex = dayCategory == VarianceDayCategory::Weekday
                                       ? 0
                                       : (dayCategory == VarianceDayCategory::Weekend ? 1 : 2);
        const Profile& intraday = profile(date.weekday());
        Real multiplier = 1.0;
        if (!intraday.values.empty()) {
            const Real knot = (minuteOfDay - intraday.startMinute) / 5.0;
            if (knot <= 0.0) {
                multiplier = intraday.values.front();
            } else if (knot >= static_cast<Real>(intraday.values.size() - 1)) {
                multiplier = intraday.values.back();
            } else {
                const Size lower = static_cast<Size>(knot);
                const Real fraction = knot - static_cast<Real>(lower);
                multiplier = (1.0 - fraction) * intraday.values[lower] +
                             fraction * intraday.values[lower + 1];
            }
        }
        return categoryWeights_[categoryIndex] * multiplier;
    }

}
