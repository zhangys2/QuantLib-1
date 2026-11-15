---
status: closed
blocked_by: []
claimed_by: none
---
# Cumulative variance-clock units

Type: Grilling (HITL)

## Question
What quantity and units should the cumulative clock `v(t)` represent, and how should five-minute historical variance estimates map to it?

## Context
The user wants remaining variance time calculated as `v(T) - v(t)` from a common origin. The existing generator records both historical `variance_per_5m` and normalized weights, while `VarianceCalendar` exposes a product of category weights and intraday multipliers. Distinguish historical variance, normalized variance time, and option-implied total variance; avoid implicitly counting a category weight twice. Record the normalization, origin, and how the outcome relates to the existing per-observation API.

## Resolution
- `v(t)` accumulates normalized variance time in weighted days: one calendar day at weight `1` contributes one variance day. Divide historical five-minute variance estimates by a reference estimate to obtain weights, and retain the raw estimates in the profile. Historical estimates are not option-implied variance.
- The reference rate is the existing generator's all-elapsed-time estimate: total squared drift-adjusted historical returns divided by the total elapsed number of five-minute slots, including gaps.
- A date-type/time variance estimate divided by the common reference is the complete clock rate. Do not multiply it by an additional day-category factor; compatibility with the existing C++ weight API remains a separate decision.
- `v(t)` and `v(T)` are cumulative from the same origin. Interpolation, daylight-saving handling, runtime rebasing, and existing API compatibility remain separate decisions.

## Amendment — 2026-11-15
- The earlier reference to one calendar day at weight `1` means 24 elapsed hours, not necessarily one local civil date. As resolved in [Clock instants and daylight saving](variance-calendar-timezone-semantics.md), 23- and 25-hour local days contribute `23/24` and `25/24` weighted days at weight `1`.
