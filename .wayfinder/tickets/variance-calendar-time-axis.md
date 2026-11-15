---
status: closed
blocked_by: []
claimed_by: none
---
# Intraday schedule time axis

Type: Grilling (HITL)

## Question
Should decay schedules repeat each observation day, optionally selecting a different intraday profile by weekday, and what time-zone/day-boundary convention defines profile timestamps?

## Resolution
- Decay schedules repeat each observation day, with different profiles allowed by weekday.
- Knots are timezone-free market-local wall-clock times; the observation's calendar date defines the day.
- Time-zone and DST conversion are left to the caller.
