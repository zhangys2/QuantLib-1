---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-timezone-semantics.md
claimed_by: none
---
# Evidence for point-in-time time-zone rules

Type: Research (AFK)

## Question
What evidence can substantiate that a precomputed IANA time-zone mapping used only rules available by a historical valuation time?

## Context
The user requires point-in-time time-zone rules for backtests and retains a versioned UTC-to-local mapping. Investigate practical evidence and limits for archived IANA releases, release or retrieval timestamps, generated mappings, and source attestations. Distinguish reproducibility of a mapping from proof that its rules were available at the simulated valuation time.

## Resolution

**Position:** a reproducible mapping and a historical as-of label are not, by
themselves, evidence that the mapping's underlying rules were available at the
valuation cutoff. Preserve the exact input rules and derived mapping, and
evaluate evidence of the input's historical availability under an explicit
trust policy.

### Verified evidence

- [IANA's time-zone documentation](https://www.iana.org/time-zones/repository/tz-link.html)
  says old releases are archived, releases are updated as political rules change,
  and the data is “by no means authoritative.” An IANA release describes that
  release's rules; it does not by itself prove exchange hours or legal truth.
- The [IANA 2022f announcement](https://lists.iana.org/hyperkitty/list/tz%40iana.org/thread/65JMZVURDDM3XOABROYJX5ZN4N6TATZ5/)
  was posted on 2022-10-29 and says the release includes a Chihuahua change
  effective 2022-10-30. Using that release for a 2022-10-12 backtest would use a
  release announced after the cutoff. The announcement lists checksums and
  detached signatures; those signatures were not independently verified here.
- [Python's `zoneinfo` documentation](https://docs.python.org/3/library/zoneinfo.html#data-sources)
  says it searches system `TZPATH` before the PyPI `tzdata` package. Therefore,
  recording only an IANA zone name or pinning the Python package does not establish
  which rule bytes were used.
- [RFC 3161, sections 1 and 2](https://www.rfc-editor.org/rfc/rfc3161.html)
  describes a trusted timestamp binding a datum's hash to a time, under the
  timestamp authority's trust and verification assumptions. It can support
  evidence of existence by a time; it does not prove that the content is
  legally correct, publicly available, or appropriate for the market.

### Implications and remaining decision

Retaining the actual rule input or compiled zone files, generator identity and
parameters, resulting UTC mapping, and content hashes supports reproducibility.
A hash does not authenticate its publisher or prove historical availability;
signatures and trusted timestamps also depend on trusted keys and authorities.
Archived publisher announcements, independently retained releases, and producer
attestations provide different levels of evidence.

Whether a mapping generated after the cutoff from provably pre-cutoff rule
inputs is acceptable, which authorities or attestations to trust, and the
minimum retained evidence remain for the human policy decision. An official
release or reconstructed mapping does not itself verify a market's session
calendar.

**Limitations:** this was a focused check of IANA, Python, and RFC primary
sources, including one 2022 example; no exchange's applicable legal rules or
particular data vendor were audited. Release signatures and timestamp tokens
were not verified. The worker's evidence was checked against the primary
sources by the coordinating session; this was not a formal independent review.
