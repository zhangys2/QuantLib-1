---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-clock-units.md
  - variance-calendar-clock-interpolation.md
  - variance-calendar-session-source.md
  - variance-calendar-price-asof-policy.md
  - variance-calendar-timezone-semantics.md
  - variance-calendar-sparse-profile-policy.md
  - variance-calendar-provenance-policy.md
  - variance-calendar-price-provenance-policy.md
  - variance-calendar-timezone-provenance-policy.md
claimed_by: none
---
# Reusable CSV schedule contract

Type: Grilling (HITL)

## Question
What versioned CSV and metadata contract should carry reusable variance profiles and dated market-session calendars between generation and runtime?

## Context
CSV output is requested; avoid requiring one file per expiry. Specify enough information to reconstruct the chosen clock, date/session mapping, units, timezone and fold treatment, sample counts, fallback provenance, and calendar version. Decide how direct CSV generation coexists with the existing Polars/Parquet workflow without silently discarding calibration metadata.

## Resolution
- Package each versioned reusable schedule as separate CSV tables for profiles, dated market sessions, and time-zone mappings, with a JSON manifest for versions, units, calibration, and provenance. Evidence may be retained separately and referenced. No file is required per expiry.
- Generate the reusable CSV bundle directly from calibration, while continuing to support Parquet price inputs and the existing dated Parquet workflow separately. Do not silently treat incomplete legacy Parquet schedules as compliant reusable bundles.
- Resolve the agreed date-to-profile selection when generating a snapshot. Store each date's selected profile ID, selection reason, and relevant date/session inputs; runtime loads that selected profile. Calendar or selection changes require a new snapshot. Slot-level fallback decisions remain auditable.
- Publish each complete snapshot as an immutable versioned bundle. Bind every data file to the manifest with a content digest and reject missing, mismatched, unsupported, or inconsistent files before activation. Manual edits require a new validated snapshot. Digests detect changes or mix-ups, not source trust or point-in-time validity.
- Support multiple scheduled session segments per local civil date in an additional CSV table. Split overnight intervals at local midnight, retain source session and trading-date identifiers, and record closed dates explicitly. Select profiles using the complete segment pattern; do not conflate the source trading date with the local profile date.
- Store rates separately from slot evidence. A separate CSV keyed by profile ID, target group, and local five-minute slot carries target/source counts and fallback provenance, so shared base rates are not duplicated merely because target statistics differ. Different fitted rates use different profiles; never average them to force sharing.

## CSV and metadata contract
- `profiles.csv`: `profile_id`, local `minute_of_day`, raw `variance_per_5m`, and normalized `weight`. Each profile has one constant rate for each of the 288 local five-minute slots, including closed hours. The common reference variance in the manifest is positive, and `weight = variance_per_5m / reference_variance_per_5m` within documented numeric precision.
- `market_days.csv`: one row per covered local civil date, with date type, open/closed status, selected `profile_id`, target-group ID, and selection reason. The date and session segments supply the weekday and complete session pattern used for selection. Closed dates remain explicit and still select a full-day variance profile.
- `session_segments.csv`: local civil date, inclusive UTC start, exclusive UTC end, stable session identifier, and source session/trading-date identifiers when supplied. Split intervals whenever the mapped local date changes, including overnight sessions; preserve breaks and source identity without inventing a trading date.
- `timezone_mapping.csv`: contiguous half-open UTC ranges with UTC offset in seconds and local fold. Split at offset or fold changes and cover the runtime horizon. The mapping is generated offline from the evidenced IANA rules; runtime needs no C++ time-zone database.
- `slot_evidence.csv`: one row per selected profile, target group, and local slot, including source-group ID, target/source direct-return counts and distinct-local-date counts, estimation method, grouping label, gap-pool contributing-return count when applicable, and the approved fallback ID when applicable. Distinguish unknown counts from zero and from not-applicable; unknown supplied-fallback counts retain their warning and provenance.
- `manifest.json`: supported format version, snapshot ID, actual generation time, UTC coverage and clock origin, market and IANA zone, common normalization reference and units, calibration settings and price cutoff, calendar and time-zone versions/as-of values, source and revision evidence, fallback approvals, warnings, and file names with SHA-256 digests. Include continuous-futures construction lineage when applicable and references to retained evidence or reproducible time-zone rule inputs. Do not imply that a later-generated artifact existed at the historical cutoff.
- Use UTF-8 comma-separated tables with headers and standard CSV quoting, ISO local dates, and explicit UTC timestamps. Numeric values must be finite; optional or unknown values must have unambiguous representations. Reject unsupported versions, missing coverage, duplicate keys, invalid references, inconsistent rates or mappings, and missing required evidence. A zero slot rate remains valid with the agreed warning.
- The UTC coverage start is the common zero origin for `v`; accumulate each slot's normalized rate over actual elapsed seconds divided by 86,400. Both folds use the same local profile, but their elapsed time is counted separately. Calculate `v(T) - v(t)` using one snapshot; after a snapshot change, recompute cached cumulative values under that snapshot. No expiry-specific schedule files or implicit category multiplier are needed.
