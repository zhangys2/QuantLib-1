---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-price-asof-policy.md
  - variance-calendar-price-provenance-research.md
claimed_by: none
---
# Point-in-time price and profile evidence policy

Type: Grilling (HITL)

## Question
What evidence and trust policy should determine whether historical prices, revisions, and supplied fallback profiles are acceptable for backtest calibration?

## Context
The user requires data available by the calibration cutoff, the latest known revision, and failure when point-in-time evidence is unavailable. A supplied fallback can have an unknown sample count only with explicit approval, provenance, and a warning; that does not waive point-in-time evidence. Use the provenance research to decide which snapshots, source attestations, versioned records, or supplied profile artifacts are acceptable, how ambiguity is handled, and what provenance the CSV and metadata contract must retain.

## Resolution
- Documented availability from an approved source by the cutoff is sufficient; actual operator receipt is not required. Vendor capture time alone does not establish downstream publication or availability.
- Accept configured trusted sources with retained, auditable records binding content, availability, and revision completeness. Independent timestamp tokens are not mandatory, and an observation or bar timestamp alone is insufficient.
- Allow bars and supplied fallback profiles to be reconstructed after the cutoff from admissible pre-cutoff inputs with recorded transformations and no later corrections. Do not claim that a reconstructed artifact itself existed at the cutoff.
- Require continuous-futures contract mappings, roll rules and decision times, adjustment method, and supporting provenance. Fail when required lineage evidence is unavailable.
- For conflicting price revisions, use a trustworthy source sequence or revision order where available; fail rather than guess if the order is ambiguous.
- Accept an explicitly approved supplied fallback without all raw training inputs when an approved provider supplies an auditable attestation binding the exact profile to its source and pre-cutoff information. Keep unknown sample counts labeled unknown; provenance does not establish statistical quality.
- Apply the continuous-futures roll-lineage requirement to supplied fallback profiles as well, even when raw bars and sample counts are unavailable.
- Honor corrections and cancellations available by the cutoff. A completed bar is not available before its interval is complete and the source has made that version available.
