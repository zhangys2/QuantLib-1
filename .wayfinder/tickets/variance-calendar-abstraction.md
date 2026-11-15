---
status: closed
blocked_by: []
claimed_by: none
---
# Separate reusable abstraction

Type: Grilling (HITL)

## Question
Should the feature be a reusable abstraction separate from `Calendar`, return an effective weight per observation, and leave aggregation and annualization to consumers?

## Resolution
Yes. Keep it separate from `Calendar`; make it reusable; return per-observation effective weights; leave aggregation and annualization to consuming instruments or engines.
