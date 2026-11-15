---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-session-source.md
  - variance-calendar-provenance-research.md
claimed_by: none
---
# Point-in-time calendar evidence policy

Type: Grilling (HITL)

## Question
What evidence and trust policy should determine whether a historical calendar snapshot is acceptable for a backtest?

## Context
The user requires information available by the simulated valuation time and failure when no suitable snapshot is available. Use the provenance research to decide which archived records or producer attestations are acceptable, how uncertainty is reported, and what evidence the CSV and metadata contract must retain. A user-supplied as-of timestamp alone is not proof.

## Resolution
- Accept an approved exchange, archive, or vendor's availability claim when supported by retained, auditable records binding source, content, and pre-cutoff availability. An independent trusted timestamp token is not mandatory; trust in the source and its records must be explicit.
- Documented source availability by the cutoff is sufficient; the operator need not prove actual possession. This supports a research backtest but does not claim the operator received the data.
- Allow a calendar file to be reconstructed after valuation from admissible pre-cutoff source records, retaining inputs and transformation provenance and excluding later corrections. Do not claim the derived file itself existed at the cutoff.
- Use the latest applicable records and corrections available through the cutoff, and require the source or audit trail to support revision-history completeness. Fail if completeness cannot be established under the configured trust policy.
- Configure trusted sources explicitly and validate available structured evidence, including source approval, content digest, cutoff, coverage, and retained evidence references. Source truth and completeness remain trust assumptions, not facts established by metadata alone.
- Retain source/version, publication and capture times where available, transformation lineage, and the completeness assertion. Missing required evidence or coverage fails the backtest.
