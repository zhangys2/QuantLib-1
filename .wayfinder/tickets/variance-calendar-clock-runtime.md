---
status: closed
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

## Resolution
- Add a separate snapshot-backed cumulative clock type alongside `VarianceCalendar`. It does not subclass `VarianceCalendar` or use the existing interpolated `weight` method to integrate five-minute bucket variance.
- Leave `VarianceCalendar::weight` unchanged, including its linearly interpolated knots and category multiplier. The separate clock exposes cumulative-time queries and uses complete, piecewise-constant bucket rates internally; its cumulative value is linear within each bucket. Document that the legacy pointwise weight is not the clock's bucket rate, and do not apply an additional category multiplier.
- Build and validate immutable snapshot candidates off the valuation path, then explicitly activate them atomically. Each in-flight calculation retains its captured snapshot throughout. A failed candidate does not replace the active snapshot; the old snapshot is usable only while it satisfies the requested coverage and point-in-time rules.
- Prepare an expiry token outside the valuation path against a chosen snapshot. It retains the expiry's cumulative `v(T)` and snapshot identity. A query must reject a token that does not match its captured snapshot; after activation, prepare new tokens outside the valuation path. In-flight work may finish on its captured old snapshot.
- Precompute reusable profile and date/transition prefix information across the covered snapshot horizon. Queries take an explicit UTC instant and select its applicable local-date profile; day rollover requires no mutable today-state, background job, or recalibration. Fail outside coverage.
- A remaining-time query at `t >= T` returns exactly zero with an explicit expired status. The status is a clock comparison, not an assertion about trading or exercise rights. Both the valuation instant and expiry must be covered by the selected snapshot; out-of-coverage inputs still fail.
- Schedule intervals cover `[start, end)`, while the cumulative clock is defined at both boundary instants `[start, end]`; an expiry or valuation exactly at `end` is valid, but anything outside those endpoints is not.
- On every query outcome, including expired, stale-token, and out-of-coverage results, the clock itself initiates no heap allocation or file I/O. Return status values rather than constructing exceptions on this path. Loading, activation, and token preparation may allocate; custom `Real` implementations' own allocations are outside the guarantee. This is not a lock-free or latency guarantee.
- Keep retired snapshots alive until all readers and tokens release them, and reclaim their storage on a non-query control path. Obsolete tokens can retain old snapshot memory until explicitly released.
- Provide an explicit read view captured once per calculation or multi-expiry batch. All cumulative queries and expiry tokens in that batch must match the view. A batch already in flight may finish on its captured old view after a swap; release views promptly so retired snapshots can be reclaimed.
