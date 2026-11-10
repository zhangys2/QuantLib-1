/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/* This file is part of QuantLib, a free-software/open-source library
   for financial quantitative analysts and developers - http://quantlib.org/

   Copyright (C) 2026

   SPDX-License-Identifier: BSD-3-Clause
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

        If a calendar is supplied, its weekend definition and holidays classify dates.
        Without one, Saturday and Sunday are weekends and no other dates are holidays.
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
