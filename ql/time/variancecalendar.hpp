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

/*! \file variancecalendar.hpp
    \brief variance calendar
*/

#ifndef quantlib_variance_calendar_hpp
#define quantlib_variance_calendar_hpp

#include <ql/time/calendar.hpp>
#include <ql/time/date.hpp>
#include <ql/time/weekday.hpp>
#include <ql/types.hpp>
#include <array>
#include <map>
#include <vector>

namespace QuantLib {

    //! Day categories used by a variance calendar.
    enum class VarianceDayCategory { Weekday, Weekend, Holiday };

    //! Per-observation variance weights with optional weekday and intraday profiles.
    /*! Intraday profiles contain values at five-minute intervals, starting at
        \c startMinute. Values are linearly interpolated between knots and clamped to
        the endpoint values outside the knot range. An empty profile uses an implicit
        all-one profile. Times are local wall-clock minutes after midnight;
        timezone and daylight-saving conversions are the caller's responsibility.

        If a calendar is supplied, a date is a weekday if it is a business day of the
        calendar (this includes weekend days opened with \c removeHoliday), otherwise a
        weekend if its weekday is a weekend day of the calendar, otherwise a holiday.
        Without a calendar, Saturday and Sunday are weekends and no other dates are
        holidays.

        The intraday profile is chosen by the date's weekday only, whatever its category:
        a weekday entry replaces the default profile even if that entry is empty (an
        empty entry flattens the day to an all-one profile), and a holiday keeps the
        profile of the weekday it falls on.
    */
    class VarianceCalendar {
      public:
        struct Profile {
            Profile() : startMinute(0) {}
            Profile(Integer startMinute, const std::vector<Real>& values)
            : startMinute(startMinute), values(values) {}

            Integer startMinute;
            std::vector<Real> values;
        };
        using WeekdayProfiles = std::map<Weekday, Profile>;
        //! Weights ordered as weekday, weekend, holiday.
        using CategoryWeights = std::array<Real, 3>;

        //! Construct a profile; all category weights default to one.
        explicit VarianceCalendar(const CategoryWeights& categoryWeights = {{1.0, 1.0, 1.0}},
                                  const Profile& defaultProfile = Profile(),
                                  const WeekdayProfiles& weekdayProfiles = WeekdayProfiles(),
                                  const Calendar& calendar = Calendar());

        //! Return the category assigned to the date.
        VarianceDayCategory category(const Date& date) const;

        //! Return the category weight multiplied by the intraday profile value.
        //! \throw Error if minuteOfDay is outside [0, 1440].
        Real weight(const Date& date, Real minuteOfDay) const;

      private:
        CategoryWeights categoryWeights_;
        Profile defaultProfile_;
        WeekdayProfiles weekdayProfiles_;
        Calendar calendar_;

        const Profile& profile(Weekday weekday) const;
    };

}

#endif
