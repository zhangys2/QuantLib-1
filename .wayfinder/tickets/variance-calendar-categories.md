---
status: closed
blocked_by: []
claimed_by: none
---
# Day categories and fallback weights

Type: Grilling (HITL)

## Question
Which day categories should be supported (for example weekday, weekend, and holiday), and what default or fallback weight should apply when a date does not match an explicitly weighted category?

## Resolution
- Built-in categories are weekday, weekend, and holiday. Weekend dates classify as weekend; non-weekend calendar holidays classify as holidays, so a holiday overrides the weekday category.
- Custom categories can be supported later if needed.
- An unspecified category uses the neutral weight `1.0`.
