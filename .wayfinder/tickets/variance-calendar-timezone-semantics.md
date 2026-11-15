---
status: closed
blocked_by: []
claimed_by: none
---
# Clock instants and daylight saving

Type: Grilling (HITL)

## Question
What time representation and caller responsibilities should the cumulative clock use across local dates, time zones, and daylight-saving transitions?

## Context
The existing C++ API uses timezone-free local minutes and leaves conversions to the caller; the Python schedule uses UTC instants and records repeated-time folds. Decide how to represent unambiguous instants, 23- and 25-hour days, ambiguous or nonexistent local times, and date rollover while respecting C++17 and the existing API's compatibility requirements.

## Resolution
- Use actual elapsed time: at weight `1`, 23- and 25-hour local days contribute `23/24` and `25/24` weighted days, respectively.
- Use the same profile rate for both occurrences of a repeated local time, while counting the two elapsed intervals separately.
- Reject unresolved ambiguous local session times and require a valid offset or fold; reject nonexistent local session times instead of shifting them.
- Accept unambiguous UTC instants at runtime and load a versioned UTC-to-local mapping for the shared calendar horizon, precomputed offline. This avoids a new C++ time-zone dependency; changed time-zone rules require regeneration.
- Identify each market's time zone using an IANA name and retain the versioned mapping produced from its rules.
- Backtests require a mapping based on time-zone rules available by the simulated valuation time and fail when a suitable snapshot is unavailable.
