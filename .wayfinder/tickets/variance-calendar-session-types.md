---
status: closed
blocked_by: []
claimed_by: none
---
# Market-day profile selection

Type: Grilling (HITL)

## Question
How should dated market sessions select reusable profiles for full days, early closes, holidays, weekends, and exceptional closures?

## Context
The user wants rates that vary across times and date types without a symbol-specific design. Settle profile-selection precedence, including interactions with existing weekday overrides and holiday/weekend classification, as well as whether session boundaries or date-specific overrides affect selection. Keep cash-equity, futures, and option sessions distinct rather than assuming their calendars coincide.

## Resolution
- Select a date type from the chosen market calendar independently of the price symbol. The existing weekend-versus-holiday precedence remains in effect.
- Use an explicit date-to-profile override first. Otherwise select a profile for the date type and scheduled session hours, using a weekday-specific variant when supplied and the corresponding base profile otherwise. A holiday never implicitly selects an ordinary weekday profile.
- Separate profiles by scheduled session hours within each date type, so dates with different close times do not silently share a profile. Handling sparse or missing profiles remains a separate decision.
- Index five-minute profiles by local clock time and cover the local date, including closed hours. Do not automatically shift weights with session hours or force closed hours to have zero variance.
- Calendar sourcing, daylight-saving details, and compatibility with the existing C++ API remain separate decisions.
