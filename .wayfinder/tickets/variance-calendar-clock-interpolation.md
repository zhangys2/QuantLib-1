---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-clock-units.md
claimed_by: none
---
# Intraday clock interpolation

Type: Grilling (HITL)

## Question
How should the cumulative variance clock interpolate between five-minute observations?

## Context
The existing C++ `VarianceCalendar::weight` linearly interpolates instantaneous profile values; the Python generator treats its interval rates as piecewise constant. Linear cumulative-time interpolation under constant rates and integration of linearly interpolated rates are different models. Resolve how input knots or buckets are interpreted, preserve or explicitly amend the earlier interpolation decision, and specify behavior at interval boundaries.

## Resolution
- Treat each estimated five-minute variance as belonging to its complete interval. Hold the normalized rate constant within the interval and interpolate cumulative `v(t)` linearly, preserving the estimated full-bucket contribution.
- Buckets are start-inclusive and end-exclusive. At an exact boundary the next bucket supplies the rate, while cumulative `v(t)` remains continuous.
- This applies to the new cumulative clock. The earlier decision for the C++ `weight` API's linearly interpolated instantaneous profile remains recorded; compatibility between the two behaviors is a separate decision.
