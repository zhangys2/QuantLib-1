---
status: closed
blocked_by: []
resolved_dependencies:
  - variance-calendar-price-asof-policy.md
claimed_by: none
---
# Evidence for point-in-time price and profile inputs

Type: Research (AFK)

## Question
What evidence can substantiate that historical five-minute prices, revisions, and externally supplied fallback profiles were available by a calibration cutoff?

## Context
The user requires a trustworthy point-in-time source or versioned observations for backtests; observation timestamps alone are insufficient. An explicitly approved supplied fallback may have an unknown sample count, but still requires source/as-of provenance and point-in-time evidence for backtests. Investigate practical evidence and limitations for retained snapshots, source attestations, availability timestamps, revisions, derived continuous futures series, and externally supplied profiles without assuming a particular vendor or access to paid data. Distinguish point-in-time evidence from statistical sample quality, and what software can verify from what requires trust in a producer.

## Resolution

**Position:** a bar's event timestamp and a reproducible final file do not
establish which price version was available at a historical cutoff. The
required evidence depends on the source, revision history, consumer-availability
boundary, and any derivation used to construct the input or fallback profile.

### Verified evidence

- [Databento's timestamp documentation](https://databento.com/docs/conventions/common-fields-enums-types.md)
  distinguishes matching-engine event time, publisher sending time, and the
  vendor's capture-server receive time. These are the vendor's descriptions of
  its fields, not proof of when a particular downstream consumer received data.
- [Databento's OHLCV documentation](https://databento.com/docs/schemas/ohlcv.md)
  says its bar `ts_event` is the start of the aggregation period and recommends
  constructing five-minute bars from finer data. It notes differences in
  handling late publication and retroactive trade breaks. A bar-start label
  cannot establish that the close of that bar or a later correction was
  available at the label time.
- [Databento's continuous-symbology documentation](https://databento.com/docs/conventions/symbology.md#continuous)
  describes a continuous symbol mapping to different outright contracts, and
  says its own continuous prices are unadjusted; its volume rule uses the
  previous day's volume. Its [ES example](https://databento.com/docs/examples/symbology/continuous.md)
  shows the mapped instrument changing on 2025-03-19. These statements do not
  prove the point-in-time provenance of a particular downloaded dataset or
  establish that every roll or adjustment method leaks future information.
- [RFC 3161, sections 1 and 2](https://www.rfc-editor.org/rfc/rfc3161.html)
  describes trusted timestamp tokens as evidence that a hashed datum existed
  by a time, subject to authority and verification assumptions. A timestamped
  hash does not establish the claimed vendor, delivery to the consumer,
  complete revisions, or statistical quality of a supplied profile.

### Causal selection and derived inputs

For an observation's identity, preserve its instrument or contract, interval,
price definition, source, and any mapping or adjustment. A point-in-time view
selects the latest trustworthy version available by the cutoff; a correction
arriving later must not be substituted merely because its event label is old.
The policy for which authority and availability boundary is trusted remains
open. For derived bars or profiles, the availability and construction of
their inputs matter as well as the output artifact's timestamp.

Illustration, not an asserted market event: a bar for `[14:00, 14:05)` initially
available at 14:05:01 and corrected at 14:12 must use its initial version at a
14:06 cutoff. A present-day file carrying the corrected value with a 14:00
interval label would otherwise leak the later correction.

Continuous futures require the contract mapping, roll rule and decision time,
adjustment method, and their vintages. Do not conflate absolute price changes
with log returns: for prices 100 and 101, adding 10 to both changes the log
return from about 0.0099503 to 0.0090498; multiplying both by 2 leaves it
unchanged. Effects across roll boundaries or differently adjusted segments
depend on the method. No blanket claim is made that every back-adjusted series
leaks or that an unadjusted roll is harmless.

### Evidence options and remaining decision

Contemporaneous receiver-side captures, vendor versioned records or signed
attestations, and independently timestamped immutable snapshots can provide
different evidence. Their value depends on clock accuracy, source identity,
revision completeness, custody, trusted keys, and the meaning of “available.”
An external fallback profile also needs its own source, cutoff, construction,
and availability evidence; an unknown sample count remains unknown and is a
separate statistical limitation.

The human policy must decide whether exchange event, vendor receipt or
publication, or consumer receipt defines availability; which attestations or
archives are trusted; and what revision and derivation evidence is sufficient.
The user has already decided to fail backtests without suitable point-in-time
evidence and to use the latest trustworthy version available by the cutoff.

**Limitations:** this was a focused English-language review of public Databento
documentation and RFC 3161. No licensed historical dataset, customer delivery
record, signed vendor attestation, or supplied profile was examined. The CME
feed specification could not be directly fetched (HTTP 403). Vendor
documentation was not independently verified against its implementation.
The worker's key claims were checked against the cited sources, and the
adjustment arithmetic was checked in the coordinating session; this was not a
formal independent review.
