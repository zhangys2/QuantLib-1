---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-session-types.md
claimed_by: none
---
# Dated market-session source

Type: Grilling (HITL)

## Question
What source and coverage rules should provide historical and future session dates, early closes, holidays, and exceptional overrides?

## Context
QuantLib `Calendar` classifies business days but does not supply the full session boundaries needed for early-close profiles. Decide how market-specific session data is supplied and versioned, which dates must be covered, and what happens when a required date or session boundary is missing. Do not assume that an NYSE cash-equity holiday is an ES futures closure.

## Resolution
- Supply authoritative market-specific dated session records for historical and future dates, including explicit closures and session hours. Exchange or vendor data can be used to produce the calendar file.
- Require complete coverage for every date touched by historical returns, including gaps, and for the requested valuation-to-expiry range. Fail rather than assume a full or closed day when a required date or open-session boundary is missing; explicitly closed dates need no open or close hours.
- Use a consistent versioned calendar snapshot for a calculation and record its source, as-of time, version, and date coverage.
- Historical backtests require a snapshot representing information available by the simulated valuation time and fail when one is unavailable. An as-of timestamp alone does not prove point-in-time provenance.
