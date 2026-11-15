---
status: closed
blocked_by: []
claimed_by: none
---
# Public variance-calendar API

Type: Task (AFK)

## Question
What minimal public C++ representation expresses category weights, five-minute intraday decay profiles, weekday overrides, and per-observation lookup?

## Resolution
`VarianceCalendar` accepts an ordered `std::array<Real, 3>` of weekday/weekend/holiday weights, a profile of values spaced five minutes apart from `startMinute`, an optional common profile, optional weekday-keyed profiles, and an optional `Calendar`. `weight(Date, Real minuteOfDay)` returns the category weight times the interpolated decay multiplier. Time is timezone-free local minutes after midnight. An empty profile means multiplier 1.0.

Implementation is in `ql/time/variancecalendar.hpp` and `ql/time/variancecalendar.cpp`; it was independently reviewed. Focused translation units passed C++17 syntax checks. Full test execution was unavailable because CMake is not installed in this environment.
