---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-session-types.md
  - variance-calendar-slot-identifiability.md
claimed_by: none
---
# Sparse-profile fallback policy

Type: Grilling (HITL)

## Question
What should generation and runtime do when a required date-type and time-slot profile has insufficient or unidentifiable observations?

## Context
Consider the research evidence for rare early-close and holiday samples and missing market hours. Decide whether and when a documented broader profile, pooled estimate, explicit proxy, or failure is acceptable; record provenance and sample counts. A zero fitted rate is not automatically evidence of zero risk.

The [identifiability research](variance-calendar-slot-identifiability.md) also
showed that the existing category/time grouping can label a Saturday slot
`observed` using only Sunday returns. Decide how fallback provenance and sample
counts distinguish target-day observations from broader-group observations.

## Resolution
- An insufficient selected profile fails by default unless an applicable pooled, broader, or supplied fallback was explicitly configured. This does not remove the previously agreed selection of a date-type/session base profile when no weekday variant is supplied.
- Retain a configurable default threshold of 30 direct five-minute returns per selected profile group and report the number of distinct local dates separately. Thirty observations are a heuristic, not a precision guarantee.
- Record the target group, source group, method, direct-return counts, and distinct-date counts. Label broader-group estimates as grouped rather than directly observed for the target.
- Permit exactly zero estimated rates, but emit a named warning and record the zero in metadata. Zero remains allowed under the existing nonnegative-weight contract and is not proof of zero risk.
- Allow at most one explicitly named fallback for an insufficient profile; if it is unavailable or inadequate, fail rather than traverse a fallback chain.
- For an explicitly enabled gap pool, require the requested pooled rate to be identifiable and at least 30 contributing return observations with nonzero exposure by default; make the count configurable. This is a basic safeguard, not a precision guarantee.
- Runtime may accept fallback approval recorded in the generated snapshot after validation and must expose the provenance. It must not silently choose a new fallback at runtime.
- When no weekday variant is supplied and the date-type/session base meets its threshold, retain the earlier base-selection rule even if the target weekday has no direct observations. Label this as grouped and show target-weekday and source-group counts.
- Allow an explicitly approved supplied fallback with an unknown sample count when its source and as-of provenance are recorded; label the count unknown and warn. Backtests still require point-in-time evidence.
- Apply the named fallback only to insufficient five-minute slots; retain adequate direct estimates and record the source per slot. All rates must use the agreed common reference.
- Count each contributing return observation once for the gap-pool threshold, not once per five-minute slot it spans.
