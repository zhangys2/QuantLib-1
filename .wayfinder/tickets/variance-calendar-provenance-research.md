---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-session-source.md
claimed_by: none
---
# Evidence for point-in-time calendars

Type: Research (AFK)

## Question
What evidence can substantiate that a market-session snapshot reflects information available at a historical valuation time?

## Context
The user requires point-in-time calendar snapshots for backtests and noted that an as-of timestamp alone is not proof. Investigate practical evidence and trust limitations for archived exchange or vendor calendars, retained snapshots, and producer attestations without assuming a particular provider or access to paid data. Distinguish publication, retrieval, correction, and valuation times, and identify what software can and cannot verify.

## Resolution

**Position:** point-in-time calendar validity requires evidence connecting the
exact session records to a source and to availability by the valuation cutoff.
A calendar's own as-of field, a later content hash, or a final corrected
calendar alone is not enough to establish that connection.

### Verified evidence

- The [NYSE 2025 trading calendar](https://www.nyse.com/publicdocs/ICE_NYSE_2025_Yearly_Trading_Calendar.pdf)
  states that its dates were correct as of 2024-12-12 and subject to change.
  That printed date is a publisher statement, not independent proof of when
  the currently retrieved PDF was published or whether its bytes were changed.
- A [NYSE Regulation memo dated 2025-01-02](https://www.nyse.com/publicdocs/nyse/markets/american-options/rule-interpretations/2025/National_Day_of_Mourning_20250102.pdf)
  identifies the 2025-01-09 market closure for a national day of mourning. The
  earlier calendar statement and later-dated memo illustrate why a final
  schedule cannot automatically be treated as information available at an
  earlier valuation. The memo's printed date alone is not independent proof
  of publication time.
- The [Library of Congress CDX description](https://www.loc.gov/preservation/digital/formats/fdd/fdd000590.shtml)
  defines an archive timestamp as the capture time recorded by the index and
  a digest as a fingerprint of the captured payload. An archive capture can
  corroborate historical availability subject to trust in the archive; it
  need not be the exchange's first publication or a complete revision history.
- [RFC 3161, sections 1 and 2](https://www.rfc-editor.org/rfc/rfc3161.html)
  describes a trusted timestamp over a data hash as evidence that bytes existed
  by a time, under the authority's trust and verification assumptions. It does
  not establish who published the content or whether the session record is true.

### Implications and remaining decision

Distinguish a source's claimed publication time, an independently or
operationally trusted capture time, an override or correction time, the
simulated valuation time, and the realized session outcome. An announced future
schedule is not proof that a session actually occurred as planned.

Possible evidence includes retained exchange notices, independently archived
captures, controlled append-only or immutable captures, vendor records, signed
releases, and trusted timestamp tokens. Each has different trust and coverage
limits. A hash establishes byte consistency against a trusted digest; a
signature authenticates a trusted key's statement but does not alone prove when
it existed. Neither establishes complete revision history.

The human policy must choose acceptable source and capture authorities, whether
proven internal possession or public availability is required, and how to treat
unavailable archives or subsequent corrections. The previously selected rule
is to fail a backtest when a suitable point-in-time snapshot is unavailable.

**Limitations:** the directly checked exchange example concerns NYSE, not CME
or every market. CME pages investigated by the worker returned HTTP 403; no
specific vendor archive, signature, timestamp token, or operational retention
system was verified. The worker's key claims were checked against the primary
sources by the coordinating session; this was not a formal independent review.
