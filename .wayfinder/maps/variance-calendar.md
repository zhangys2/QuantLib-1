## Destination
Design a symbol-independent variance calendar that generates reusable CSV intraday profiles from five-minute prices and supports full days, early closes, holidays, and weekends. Define an efficient in-memory cumulative clock for arbitrary observation and expiry times, including `v(T) - v(t)`, without requiring a schedule file per expiry or integrating into pricing engines.

## Notes
- Project: QuantLib; maintain C++17 compatibility and support market-specific calendars without making the model symbol-dependent.
- The existing abstraction in `ql/time/variancecalendar.hpp` and `.cpp` provides per-observation weights. This expanded destination also includes cumulative variance time; it does not automatically replace the existing API or its prior decisions.
- The existing C++ calendar keeps its linearly interpolated intraday weights; the separate cumulative clock uses constant rates within five-minute slots.
- The existing Python generator uses Polars and Parquet inputs, produces expiry-specific Parquet schedules, and permits CSV conversion. Reusable CSV profiles and market-day calendars are the new planning scope.
- The requested rates vary across times and date types; the user did not request continuous recalibration from live prices. Full days, half days, holidays, and weekends can have different profiles.
- HITL decisions require the user. Earlier decisions remain recorded below; a new decision ticket must explicitly resolve any conflict rather than silently replacing one.

## Decisions so far
- [Shared in-memory clock interface](../tickets/variance-calendar-clock-runtime.md) — Use a separate snapshot-backed clock with immutable read views, snapshot-bound expiry tokens, and allocation-free queries.
- [Reusable CSV schedule contract](../tickets/variance-calendar-profile-csv.md) — Generate immutable, validated CSV bundles with preselected daily profiles and a provenance manifest.
- [Point-in-time time-zone evidence policy](../tickets/variance-calendar-timezone-provenance-policy.md) — Use auditable latest-known approved IANA rules and reproducible mapping inputs; permit later causal reconstruction.
- [Separate reusable abstraction](../tickets/variance-calendar-abstraction.md) — Separate from `Calendar`, reusable, and exposes per-observation weights.
- [Day-category weighting](../tickets/variance-calendar-day-weights.md) — Support day-category weights and optional holiday classification; holiday overrides weekday.
- [Intraday decay schedule](../tickets/variance-calendar-decay-schedule.md) — The existing per-observation API linearly interpolates between five-minute profile knots.
- [Intraday schedule time axis](../tickets/variance-calendar-time-axis.md) — The existing per-observation API repeats daily weekday profiles on a timezone-free local wall-clock axis; timezone/DST conversion is the caller's responsibility.
- [Combine day and decay weights](../tickets/variance-calendar-weight-combination.md) — Multiply the day-category weight by the interpolated intraday decay multiplier for each observation.
- [Day categories and fallback weights](../tickets/variance-calendar-categories.md) — The existing per-observation API classifies weekday, weekend, and holiday, with unspecified category weights defaulting to `1.0`; the new clock follows the separate sparse-profile fallback policy.
- [Decay schedule outside knot range](../tickets/variance-calendar-knot-bounds.md) — Clamp lookups to the nearest endpoint value before the first or after the last knot.
- [Weight and multiplier value ranges](../tickets/variance-calendar-value-ranges.md) — Day weights and decay multipliers must be finite and nonnegative; zero is allowed.
- [Missing weekday decay profile](../tickets/variance-calendar-missing-weekday-profile.md) — Use a common default intraday decay profile when no weekday-specific profile is supplied.
- [Source of the common default profile](../tickets/variance-calendar-default-profile-source.md) — Use an implicit all-one decay profile if no common or weekday-specific profile is supplied.
- [Public variance-calendar API](../tickets/variance-calendar-public-api.md) — Use `VarianceCalendar::weight(date, minuteOfDay)` with category weights, a common profile, and weekday profile overrides.
- [Cumulative variance-clock units](../tickets/variance-calendar-clock-units.md) — Accumulate weighted days using each complete date-type/time variance estimate divided by one all-elapsed-time historical reference, with a common origin.
- [Intraday clock interpolation](../tickets/variance-calendar-clock-interpolation.md) — Hold each five-minute rate constant, interpolate cumulative variance time linearly, and use start-inclusive, end-exclusive buckets.
- [Market-day profile selection](../tickets/variance-calendar-session-types.md) — Select local-time profiles by date type, session hours, and optional weekday, with explicit date overrides and no automatic zero for closed hours.
- [Dated market-session source](../tickets/variance-calendar-session-source.md) — Require supplied, fully covered, versioned market-session snapshots; backtests require point-in-time calendar information.
- [Historical price-data cutoff](../tickets/variance-calendar-price-asof-policy.md) — Calibrate only from data available by an explicit as-of time; use the latest known revision and require point-in-time evidence for backtests.
- [Clock instants and daylight saving](../tickets/variance-calendar-timezone-semantics.md) — Use UTC elapsed time and an offline, versioned IANA mapping; repeated local hours share rates but count twice.
- [Identifiability of intraday profiles](../tickets/variance-calendar-slot-identifiability.md) — Direct returns inform grouped slots; gap returns identify only exposed combinations unless additional assumptions or observations supply the missing shape.
- [Sparse-profile fallback policy](../tickets/variance-calendar-sparse-profile-policy.md) — Fail insufficient slots without one explicit fallback; preserve per-slot provenance, configurable sample gates, and warnings for zero estimates.
- [Evidence for point-in-time time-zone rules](../tickets/variance-calendar-timezone-provenance-research.md) — Reproducible rule bytes and mappings do not alone prove historical availability; the approved trust policy is recorded separately.
- [Evidence for point-in-time calendars](../tickets/variance-calendar-provenance-research.md) — A session snapshot needs trustworthy source and availability evidence; a final calendar or self-declared as-of date alone is insufficient.
- [Evidence for point-in-time price and profile inputs](../tickets/variance-calendar-price-provenance-research.md) — Event labels, consumer availability, revisions, and continuous-futures derivations require distinct evidence.
- [Point-in-time calendar evidence policy](../tickets/variance-calendar-provenance-policy.md) — Accept auditable approved sources and later causal reconstruction; require complete latest-known records and configured evidence checks.
- [Point-in-time price and profile evidence policy](../tickets/variance-calendar-price-provenance-policy.md) — Require auditable source availability, revision order, and continuous-futures lineage; permit documented causal reconstruction.

## Acceptance criteria
- Compare the clock against an independent high-precision reference using deterministic cases covering near-expiry cancellation, five-minute and DST boundaries, and mixed profiles. Define and justify tolerances for the supported numeric type, horizon, and rate range before acceptance testing.
- Verify that successful, expired, stale-token, and out-of-coverage queries initiate no clock-owned heap allocation or file I/O; custom `Real` arithmetic is outside that guarantee. Use precomputed indexed lookups rather than scanning the full horizon per query.
- Support distinct eligible full-day, early-close, holiday, and weekend profiles with rates varying by local time and date type. Preserve market-specific session patterns, including overnight segments and breaks, without tying the calendar to a price symbol or implicitly zeroing closed hours.
- Support explicit date-to-profile overrides for exceptional dates using eligible supplied profiles. Apply the agreed sample, provenance, and fallback requirements; do not silently substitute an unsupported profile.

## Deferred
- Concrete numerical error budgets must be chosen and justified before acceptance testing. Deployment-specific latency and throughput targets require a representative workload, hardware, and measurement method; no speedup or latency claim is implied.
- Automatic event classification and first-class specialized event-group calibration beyond the agreed date types and explicit overrides are deferred.

## Out of scope
- Integrating the abstraction into a pricing engine or selecting an implied-volatility model.
- Choosing pricing or annualization conventions beyond the units needed to define the cumulative clock.
