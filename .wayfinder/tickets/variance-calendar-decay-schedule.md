---
status: closed
blocked_by: []
claimed_by: none
---
# Intraday decay schedule

Type: Grilling (HITL)

## Question
Should decay be supplied as an intraday schedule with five-minute knots, linearly interpolated and evaluable at arbitrary intraday observation times?

## Resolution
Yes. The schedule is intraday, uses five-minute knots, and is evaluated at any intraday observation time using linear interpolation.
