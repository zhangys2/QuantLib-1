---
brief_type: research
schema_version: 1
title: Reusable market variance schedules and cumulative clock
status: ready-for-delivery
research_brief: .wayfinder/tickets/variance-calendar-slot-identifiability.md
source_report: .wayfinder/tickets/variance-calendar-slot-identifiability.md
scope:
  - Generate reusable market-specific and symbol-independent variance schedule snapshots from five-minute historical prices.
  - Provide a shared in-memory cumulative variance clock for arbitrary observation and expiry instants without expiry-specific files.
  - Preserve auditable point-in-time inputs and the existing per-observation calendar and dated Parquet workflows.
constraints:
  - Support C++17 and the existing configurable QuantLib Real type without assuming all Real configurations are binary64.
  - Leave VarianceCalendar::weight behavior unchanged and do not multiply the new clock rate by another day-category factor.
  - Do not perform file I/O or clock-owned heap allocation on any query outcome; custom Real arithmetic is outside the allocation guarantee.
  - Use validated immutable snapshots, explicit UTC instants, offline versioned time-zone mappings, and point-in-time evidence for backtests.
  - Treat missing required coverage, evidence, profile eligibility, and stale expiry tokens as errors rather than inventing defaults.
acceptance_criteria:
  - Generate the approved reusable CSV bundle directly from eligible historical calibration data while retaining Parquet price input and the existing dated Parquet workflow.
  - Select distinct eligible full-day, early-close, holiday, and weekend profiles by market date and session pattern, with optional weekday variants and explicit date overrides.
  - Preserve complete local-day five-minute profiles, overnight and split sessions, closed dates, fallback provenance, sample counts, and the selected source per slot.
  - Verify immutable file digests, format version, rates, references, coverage, and required provenance before activating a snapshot.
  - Compute weighted-day cumulative time from constant bucket rates using actual UTC elapsed seconds and a common reference, without an extra category multiplier.
  - Maintain one snapshot per read view and expiry token, reject stale-token mismatches, and reclaim retired snapshots off the query path.
  - Return zero and expired status at or after expiry; reject out-of-coverage inputs and support both cumulative horizon endpoints.
  - Under the default IEEE-754 binary64 Real build, require absolute error no greater than 1e-12 plus 1e-10 times the absolute high-precision reference in weighted days.
  - Exercise slot boundaries, 23-hour and 25-hour DST days, repeated folds, zero rates, and near-expiry cases against an independent reference.
  - Verify no clock-owned heap allocation or file I/O for successful, expired, stale-token, and out-of-coverage queries and use indexed horizon lookups.
out_of_scope:
  - Pricing-engine integration, an implied-volatility model, and annualization or pricing conventions beyond the weighted-day clock.
  - Automatic event classification, first-class specialized event-group calibration, and live continuous recalibration.
  - A claim that futures are an accurate proxy for a cash index, or that available public data satisfies point-in-time or licensing requirements.
  - Deployment-specific latency and throughput targets without a representative workload, hardware, and measurement method.
---

# Reusable market variance schedules and cumulative clock

## Question

Deliver the user-approved design in the [variance-calendar map](maps/variance-calendar.md): generate reusable historical variance profiles for distinct market-day types and evaluate remaining variance time consistently across many expiries. The map is the originating planning assignment and decision record. The AFK research ticket named in the frontmatter contains both its original question/context and its completed source report; the other AFK reports below likewise retain their original questions and findings.

This brief records an approved design, not authorization to implement it. No representative production data, pricing model, or performance result has been validated.

## Claims

| Claim ID | Claim | Evidence IDs | Delivery relevance |
| --- | --- | --- | --- |
| CLM-001 | The existing intraday tool writes a dated Parquet schedule and stores calibration metadata in the Parquet file; exporting only its rows to CSV does not carry that metadata. | EVD-001 | Generate the reusable bundle directly and preserve the legacy workflow rather than silently treating a legacy export as a compliant bundle. |
| CLM-002 | The existing per-observation calendar interpolates knot values linearly and multiplies by a day-category weight. | EVD-002 | Its semantics differ from the approved constant-bucket cumulative clock and must remain unchanged. |
| CLM-003 | Under the stated additive model, a gap return identifies exposed combinations of slot variances, not necessarily the individual within-gap shape; rank alone does not establish estimator precision. | EVD-003 | Fail insufficient or unidentified estimates unless an explicitly approved, documented fallback applies. |
| CLM-004 | In the report's independent Gaussian, known-mean illustration, 30 observations imply about 25.8% relative standard error for a mean-square estimate. | EVD-003 | Treat the default sample threshold as a heuristic, not a production confidence guarantee. |
| CLM-005 | A bar event label or final corrected file does not establish the price version available at an earlier cutoff; continuous futures add contract-mapping and roll-lineage dependencies. | EVD-004 | Retain source availability, revision, correction, and continuous-futures evidence. |
| CLM-006 | A final calendar, an IANA rule set, or a content hash alone does not prove historical availability or market-session truth. | EVD-005, EVD-006 | Use the approved source and evidence policy; do not infer point-in-time validity from a self-declared timestamp or digest. |
| CLM-007 | QuantLib defaults Real to double but permits a configured replacement. | EVD-008 | Scope the approved numeric budget to the default IEEE-754 binary64 build and justify separate tolerances for other types. |
| CLM-008 | In the reproducible synthetic binary64 example below, subtracting two rounded global cumulative values misses the approved one-millisecond error budget by approximately 49 times. | EVD-007, EVD-009 | Test cancellation explicitly; mathematically equivalent stable differencing or rebasing may be necessary. |
| CLM-009 | The approved clock uses a complete normalized rate per local five-minute bucket and actual UTC elapsed seconds; DST folds reuse the same local profile but count twice. | EVD-009, EVD-013 | Preserve interval contributions and use weighted days rather than adding a second date-category factor. |
| CLM-010 | The user approved reusable CSV tables, preselected market-date profiles, auditable per-slot fallback evidence, and immutable versioned snapshots. | EVD-009, EVD-010, EVD-012 | Keep output reusable across dates and expiries while validating the chosen profile and evidence. |
| CLM-011 | The user approved a separate clock with snapshot-pinned views, expiry tokens, atomic activation, off-path reclamation, and allocation-free status-returning queries. | EVD-009, EVD-011 | The runtime contract must prevent mixed-snapshot results without requiring allocations or I/O per query. |

## Evidence

| Evidence ID | Source | Locator | Supports claims |
| --- | --- | --- | --- |
| EVD-001 | `tools/variance_schedule/INTRADAY.md` | Calibration, Parquet format, metadata, and CSV export sections; reviewed 2026-11-15 UTC. | CLM-001 |
| EVD-002 | `ql/time/variancecalendar.hpp`; `test-suite/variancecalendar.cpp` | Calendar profile and weight contract; category and interpolation test cases; reviewed 2026-11-15 UTC. | CLM-002 |
| EVD-003 | `.wayfinder/tickets/variance-calendar-slot-identifiability.md` | Completed research resolution, structural limits, synthetic rank example, Gaussian illustration, and coverage limitations. | CLM-003, CLM-004 |
| EVD-004 | `.wayfinder/tickets/variance-calendar-price-provenance-research.md` | Completed research resolution and cited Databento bar, timestamp, and continuous-symbology documentation. | CLM-005 |
| EVD-005 | `.wayfinder/tickets/variance-calendar-provenance-research.md` | Completed calendar-evidence resolution and cited NYSE, archive, and RFC 3161 sources. | CLM-006 |
| EVD-006 | `.wayfinder/tickets/variance-calendar-timezone-provenance-research.md` | Completed time-zone-evidence resolution and cited IANA, Python zoneinfo, and RFC 3161 sources. | CLM-006 |
| EVD-007 | This brief, reproducible synthetic calculation | Reproducibility Trail; Python 53-bit binary float and 60-digit Decimal; calculation performed 2026-11-15 UTC. | CLM-008 |
| EVD-008 | `ql/types.hpp`; `ql/qldefines.hpp` | Real alias and overridable default QL_REAL definition; reviewed 2026-11-15 UTC. | CLM-007 |
| EVD-009 | `.wayfinder/maps/variance-calendar.md` | User-approved destination, decisions, numerical acceptance criteria, and deferred items. | CLM-008, CLM-009, CLM-010, CLM-011 |
| EVD-010 | `.wayfinder/tickets/variance-calendar-profile-csv.md` | Closed CSV and metadata contract, including selected profiles and per-slot evidence. | CLM-010 |
| EVD-011 | `.wayfinder/tickets/variance-calendar-clock-runtime.md` | Closed runtime clock resolution. | CLM-009, CLM-011 |
| EVD-012 | `.wayfinder/tickets/variance-calendar-sparse-profile-policy.md` | Closed direct-observation, pooled-estimate, fallback, and provenance policy. | CLM-010 |
| EVD-013 | `.wayfinder/tickets/variance-calendar-clock-units.md`; `.wayfinder/tickets/variance-calendar-timezone-semantics.md` | Closed normalization, weighted-day, UTC, and daylight-saving decisions. | CLM-009 |

## Counterevidence

- The legacy linearly interpolated instantaneous weight and the new constant bucket rate are not interchangeable, even when supplied with the same knot values. Keep them as distinct contracts rather than claiming equivalence (CLM-002, CLM-009).
- IANA explicitly disclaims absolute authority, and source notices and archived snapshots have trust and completeness limits. When an approved market source explicitly claims a conflicting market-local offset, the agreed policy rejects the affected snapshot pending an evidenced new version (CLM-006).
- The identifiability report's rolling public futures sample was a short coverage observation, not a validated production feed or paired futures/index study. Pooling and rank checks do not prove a useful market profile (CLM-003, CLM-004).
- The older research reports describe policy choices as open because they predate the subsequent closed policy tickets; the user-approved map records the later decisions. This is a chronology difference, not independent confirmation.

## Limits

- The numerical tolerance is a user-approved engineering acceptance threshold, not an empirical market-risk or calibration-accuracy bound. The cancellation example is synthetic and does not benchmark an implementation or prove a particular algorithm will meet the budget.
- No representative multi-year point-in-time price dataset, exchange-specific production archive, provider attestation, matched ES/SPX validation, or option-implied comparison was established. The 30-sample illustration relies on assumptions not generally true of market returns.
- Evidence validation depends on configured trust in source identity, availability, revision completeness, and rule inputs. Hashes detect inconsistencies but do not establish source truth, legal authority, or publication time.
- The approved numeric budget applies to default IEEE-754 binary64 only. Acceptance for custom Real types needs independently justified tolerances; their internal allocations are outside the query-allocation guarantee.
- The operator must supply and maintain approved sources and sufficiently fresh snapshot evidence. No query-time network check or automatic guarantee of detecting a newly published revision is implied.
- Latency and throughput targets, automatic event classification, and specialized event-group calibration remain deferred. No lock-free or speedup claim is made.

## Research Closure

- Answered questions: Clock units, slot interpolation, legacy compatibility, market-date selection, sparse fallbacks, point-in-time evidence, reusable file structure, snapshot lifecycle, and the requested numerical acceptance budget are recorded in the linked closed decisions.
- Remaining gaps: Deployment-specific approved data providers, real retained evidence, custom Real tolerances, and measured latency/throughput targets remain to be supplied; they are not evidence for an existing production deployment. Implementation details must satisfy the approved behavior without narrowing it.
- Contradictions: Legacy knot interpolation differs from constant bucket rates; later user decisions resolve formerly open research policies; IANA rules may conflict with an approved market-local offset. The counterevidence section records their effects.
- Single-source claims: CLM-001, CLM-002, CLM-003, CLM-004, CLM-005, CLM-007, and CLM-008 rely respectively on one repository workflow, interface, consolidated research report, configuration, or synthetic calculation; their use is limited as described above.
- Evidence review: Scope coverage and claim-to-evidence traceability were checked against the map and closed tickets. Source independence is limited for repository observations, policy choices, and synthetic calculations; counterevidence and limits are stated separately. Reproducibility is provided below. This is a local, non-independent review, not proof of source truth or empirical market performance.

## Decision Record

| Decision ID | Decision or requirement | Basis claim IDs | Status |
| --- | --- | --- | --- |
| DEC-001 | Keep the existing linearly interpolated weight API unchanged and expose the cumulative clock separately. | CLM-002, CLM-009, CLM-011 | User approved |
| DEC-002 | Use each five-minute bucket's historical variance divided by one positive all-elapsed-time reference as the complete constant clock rate; integrate over actual UTC seconds divided by 86,400. | CLM-003, CLM-009 | User approved |
| DEC-003 | Generate immutable reusable CSV tables for profiles, market days, session segments, time-zone mappings, and slot evidence, plus a versioned manifest with SHA-256 file digests, calibration metadata, and evidence references. | CLM-001, CLM-006, CLM-010 | User approved |
| DEC-004 | Select an explicit date override first; otherwise use date type, complete scheduled session pattern, and an optional weekday variant, falling back to the matching base profile. Preserve distinct rates and full local-day coverage. | CLM-003, CLM-009, CLM-010 | User approved |
| DEC-005 | Default to 30 direct returns per selected group and report distinct dates; permit at most one explicitly approved fallback for insufficient slots. An enabled gap pool also needs an identifiable rate and 30 contributing unique returns by default. Counts and thresholds remain configurable and auditable. | CLM-003, CLM-004, CLM-010 | User approved |
| DEC-006 | Require approved auditable source availability and latest eligible revision evidence for price, market-session, and time-zone inputs; retain continuous-futures lineage. Permit later causal reconstruction without claiming the derived artifact existed at the cutoff. | CLM-005, CLM-006 | User approved |
| DEC-007 | Build and validate a snapshot off-path, atomically activate it, and pin a read view for each calculation or batch. Prepare expiry tokens against a snapshot, reject mismatches, and reclaim retired snapshots off the query path after readers and tokens release them. | CLM-008, CLM-011 | User approved |
| DEC-008 | Query with explicit UTC instants and precomputed indexed prefixes. Treat rate intervals as start-inclusive and end-exclusive, permit the cumulative horizon end, return exact zero and expired status at or after expiry, and reject values outside coverage. | CLM-009, CLM-011 | User approved |
| DEC-009 | For binary64, require remaining-time error at most 1e-12 plus 1e-10 times the absolute independent reference in weighted days. Test up to 30-year synthetic horizons, rates zero through 100, one-millisecond intervals, near-expiry cancellation, slot boundaries, DST, and exact-zero status cases; these fixtures are not input caps. | CLM-007, CLM-008, CLM-009 | User approved |
| DEC-010 | Return query outcomes without clock-owned heap allocation, file I/O, or error-path exception construction; use status results and keep loading, activation, and token preparation off the query path. | CLM-007, CLM-011 | User approved |

## Reproducibility Trail

- Originating planning map: `.wayfinder/maps/variance-calendar.md`; the named AFK research ticket contains its original research assignment and completed report in one file.
- Additional completed reports: `.wayfinder/tickets/variance-calendar-provenance-research.md`, `.wayfinder/tickets/variance-calendar-price-provenance-research.md`, and `.wayfinder/tickets/variance-calendar-timezone-provenance-research.md`. Their original retrieval dates are not uniformly recorded. Their contents were reviewed on 2026-11-15 UTC; linked external sources were not re-fetched for this brief.
- The synthetic cancellation calculation below was run on 2026-11-15 UTC with a Python float having 53 binary significand bits. It produces approximately `4.8957e-11` weighted days of error against a budget of `1.0000e-12`, or `48.96` times the budget. It is an illustration, not a production benchmark.

```python
from decimal import Decimal, getcontext
import sys

getcontext().prec = 60
assert sys.float_info.mant_dig == 53
base = Decimal("1000000")
reference = Decimal("0.001") / Decimal("86400")
naive = float(base + reference) - float(base)
error = abs(Decimal.from_float(naive) - reference)
budget = Decimal("1e-12") + Decimal("1e-10") * abs(reference)
print(error, budget, error / budget)
```

- Reference cases use an independent decimal or rational integral of serialized rates over UTC intervals, not the implementation's cached prefixes. With unit rate, 23 and 25 elapsed hours are `23/24` and `25/24` weighted days. On the 25-hour day, 23 hours at rate 1 plus the two occurrences of one hour at rate 3 equal `29/24`.
- Illustrative New York UTC fixtures are `[2024-03-10T05:00Z, 2024-03-11T04:00Z)` and `[2024-11-03T04:00Z, 2024-11-04T05:00Z)`; the latter has two local 01:30 instants at 05:30Z and 06:30Z. A local Python zoneinfo check confirmed these mappings on 2026-11-15 UTC; its host rule source was not pinned and is not point-in-time evidence.
- Validate the finished brief with `python3 -B /home/zhangy/git/plugins/research-to-delivery/skills/deliver-research-brief/scripts/validate_research_brief.py .wayfinder/variance-calendar-delivery-brief.md`. Delivery must retain the CLM, EVD, and DEC identifiers when preparing its implementation plan.
