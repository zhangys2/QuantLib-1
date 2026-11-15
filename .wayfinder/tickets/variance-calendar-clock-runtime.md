---
status: open
blocked_by: []
resolved_dependencies:
  - variance-calendar-clock-units.md
  - variance-calendar-clock-interpolation.md
  - variance-calendar-session-types.md
  - variance-calendar-session-source.md
  - variance-calendar-price-asof-policy.md
  - variance-calendar-timezone-semantics.md
  - variance-calendar-sparse-profile-policy.md
  - variance-calendar-provenance-policy.md
  - variance-calendar-price-provenance-policy.md
  - variance-calendar-timezone-provenance-policy.md
  - variance-calendar-profile-csv.md
claimed_by: none
---
# Shared in-memory clock interface

Type: Grilling (HITL)

## Question
What runtime interface and snapshot lifecycle should provide reusable cumulative-clock lookups across dates and many expiries?

## Context
The user proposes keeping today's curve in memory, interpolating `v(t)`, and subtracting it from a cached cumulative `v(T)` measured from the same origin. Decide where the clock lives relative to the existing C++ `VarianceCalendar`, how it handles expiry and day rollover, snapshot changes and cache invalidation, and whether the existing `weight` API remains unchanged. Avoid per-query allocations or expiry-specific schedule files, and do not assume rates must be recalibrated continuously.
