---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-session-source.md
claimed_by: none
---
# Historical price-data cutoff

Type: Grilling (HITL)

## Question
How should a backtest prevent historical price observations unavailable at its simulated valuation time from entering profile calibration?

## Context
The user requires point-in-time market-session information. The existing generator only warns when its price history extends after the schedule start, so a point-in-time calendar alone does not prevent price-data look-ahead. Decide whether to reject, explicitly trim, or otherwise handle unavailable observations, and what cutoff and provenance should be recorded.

## Resolution
- Exclude observations after the calibration cutoff before fitting, report how many were excluded, and fail if the eligible history is insufficient. Do not modify the original input file.
- Require and record an explicit timezone-aware calibration-as-of time for each reusable profile, separate from option expiry. Use a profile only for valuations at or after its calibration-as-of time.
- For backtests, require a trustworthy point-in-time price source or snapshot, or versioned observations with trustworthy availability times. Exclude values not yet available at the cutoff and fail if suitable evidence or history is unavailable; an observation timestamp alone does not prove availability.
- For versioned observations, use the latest trustworthy version available at or before the cutoff for each observation and exclude later corrections.
- Apply the cutoff before estimating drift, the reference rate, or profiles, and record source and cutoff provenance. Evidence standards and file formats remain separate decisions.
