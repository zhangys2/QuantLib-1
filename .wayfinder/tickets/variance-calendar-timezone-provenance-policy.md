---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-timezone-semantics.md
  - variance-calendar-timezone-provenance-research.md
claimed_by: none
---
# Point-in-time time-zone evidence policy

Type: Grilling (HITL)

## Question
What evidence and trust policy should determine whether a time-zone mapping is acceptable for a historical backtest?

## Context
The user requires mappings based on rules available by the simulated valuation time and failure when a suitable snapshot is unavailable. Use the provenance research to decide which archived releases, generated mappings, or producer attestations are acceptable and what evidence the CSV and metadata contract must retain.

## Resolution
- Accept an approved IANA archive or provider when retained, auditable evidence binds the rule data to pre-cutoff availability. Independent timestamp tokens are not mandatory; a zone name or self-declared as-of time alone is insufficient.
- Use the latest applicable approved IANA release available by the cutoff, supported by evidence of release completeness. Do not silently ignore an earlier-known rules update.
- Allow a UTC mapping to be generated after the cutoff from admissible pre-cutoff rule data with transformation lineage; do not claim the mapping itself existed at the cutoff.
- Retain the actual rule data used, or a verifiable release and reproducible compilation details, along with the generated mapping and content digests.
- If an approved, point-in-time market-session source explicitly states a market-local UTC offset that conflicts with the IANA rules, reject the affected snapshot. Require an evidenced, point-in-time resolution in a new versioned snapshot; do not silently prefer either source. An offset used only to specify an instant is not a market-local offset claim.
- Fail backtests when suitable evidence or mapping is unavailable. Content digests establish consistency, not source accuracy or market law; a pinned Python package alone does not prove which rule data were loaded.
