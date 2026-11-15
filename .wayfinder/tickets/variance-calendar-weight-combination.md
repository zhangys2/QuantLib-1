---
status: closed
blocked_by: []
claimed_by: none
---
# Combine day and decay weights

Type: Grilling (HITL)

## Question
How should the day-category weight and intraday decay multiplier combine into the effective weight for an observation—for example, multiply, add, or use one as an override?

## Resolution
Multiply them: effective observation weight is the day-category weight times the interpolated intraday decay multiplier.
