---
status: closed
blocked_by:
  - variance-calendar-time-axis
claimed_by: none
---
# Decay schedule outside knot range

Type: Grilling (HITL)

## Question
For an observation time before the first decay knot or after the last knot, should the schedule reject the lookup, clamp to the nearest endpoint value, or extrapolate linearly?

## Resolution
Clamp to the nearest endpoint value at both ends of the schedule.
