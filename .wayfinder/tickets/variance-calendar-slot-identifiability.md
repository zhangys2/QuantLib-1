---
status: closed
blocked_by: []
claimed_by: none
---
# Identifiability of intraday profiles

Type: Research (AFK)

## Question
Which full-day, early-close, holiday, and weekend variance profiles can be identified from available five-minute prices and gaps?

## Context
Inspect the current Polars calibration and gap-pooling assumptions, and distinguish directly observed slots from periods covered only by aggregate returns. Use representative real data if available or clearly labeled synthetic examples, record data limitations, and identify evidence needed to evaluate sparse-day estimates and an ES-to-SPX proxy. Do not invent within-gap shapes or claim that a market closure implies zero variance.

## Resolution

**Position — supported by the current model and synthetic examples:** directly
observed five-minute returns inform the variance of their grouped slot. A gap
return informs an aggregate across the exposed slots; separate rates within the
gap require additional independent exposures or modeling assumptions. A rank
check can establish identifiability under the model, not precision or validity
of the model.

### Current calibration

- [`fit_profile`](../../tools/variance_schedule/intraday_model.py) groups direct
  five-minute squared, drift-adjusted returns by `(category, minute)`. A group
  becomes `observed` at `--min-samples`, currently 30; otherwise the model fits
  one pooled rate per needed category using direct and gap returns. It subtracts
  the estimated contributions of sufficiently sampled slots before nonnegative
  least squares. A zero pooled rate can be a constrained-fit boundary.
- The pool is a **constant-rate assumption** for the unknown slots in a category,
  not evidence of the five-minute shape inside a gap. A requested coefficient can
  be identifiable even when unrelated nuisance coefficients are not: the current
  code checks the rank contribution of each required category.
- The current `sample_count` is the count for a category/time group, not necessarily
  the requested weekday. A direct experiment with 30 Sunday 18:00 returns and no
  Saturday observations requested Saturday 18:00; the current fitter returned
  `calibration_method=observed`, `sample_count=30`. Sunday and Saturday share the
  weekend group. The result is evidence about the group, not a Saturday sample.

### Structural and statistical limits

Under an additive expected-variance model with negligible or known drift and
uncorrelated increments, a gap's expected squared return is the sum of the slot
variances it spans. Forty identical six-slot gaps give an exposure matrix with
rank 1, not 6. Both `[1, 1, 1, 1, 1, 1]` and
`[2, 1.5, 1, 0.5, 0.5, 0.5]` have the same exposure in every gap. A local
NumPy calculation confirmed the rank and equality. Adding five independent
single-slot exposures produced rank 6; other independent gap patterns can also
add information. Nonnegativity or other constraints can identify special
boundary cases, so rank deficiency does not by itself prove that every individual
coefficient is unidentified.

Thirty observations is not a precision guarantee. For independent zero-mean
Gaussian returns with a fixed known mean, the standard error of the sample
mean-square estimate is `sqrt(2/n)` relative to the true variance: about 25.8%
at `n=30` and 70.7% at `n=4`. A 95% chi-square interval for the true variance
is approximately `[0.639, 1.787]` times the estimate at `n=30`, and
`[0.359, 8.257]` at `n=4`. These are illustrative calculations, not confidence
intervals for the implementation: it estimates drift, and market returns can
be nonstationary, dependent, or non-Gaussian.
[NIST's chi-square reference](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3666.htm)
states the sum-of-squared-normals distribution used for this calculation.

### Coverage observation

On 2026-11-15 UTC, a rolling
[Yahoo ES=F five-minute sample](https://query1.finance.yahoo.com/v8/finance/chart/ES%3DF?range=60d&interval=5m)
reported observations from 2026-09-08 04:00 UTC through 2026-11-13 21:55 UTC
after excluding null/nonpositive closes and one off-grid timestamp for this
coverage analysis. It contained 13,388 on-grid positive closes and 13,287
adjacent five-minute pairs. Grouping reported timestamps only by local
weekday/weekend and minute, 273 weekday buckets had at least 30 pairs, versus
zero weekend buckets; weekend buckets had at most 9. The sample had bars on
9 Sundays and no Saturdays. When split by individual weekday, the maximum
count in any bucket was 10.

This was a coverage count, not a fitted schedule or validated data source.
The response had 3,244 null/invalid closes and one positive off-grid timestamp,
which the current generator would reject if passed through unchanged. Vendor
bar-label semantics, revision history, roll construction, licensing, and
point-in-time provenance were not established. The endpoint is rolling and
the sample is too short to establish holiday or early-close behavior.

[NYSE's published calendar](https://www.nyse.com/trade/hours-calendars) lists
13:00 Eastern cash-equity early closes on 2026-11-27 and 2026-12-24. Both were
future dates at the observation time and are not training samples. As an
illustration only, a group with one qualifying date per year needs roughly
30 years to reach 30 direct observations per ordinary slot; changes in market
regime and the actual calendar make the usefulness of such a window uncertain.

### Proxy and fallback implications

ES is a proxy, not a direct SPX observation. Algebraically,
`change(log(ES)) = change(log(SPX)) + change(log(ES/SPX))`; changes and
covariances in the ratio can make the variances differ. Overnight cash-index
observations, futures rolls, and historical revisions require separate evidence.
No matched ES/SPX validation or option-implied calibration was performed.

- Direct-only estimation avoids inventing missing shapes but can leave rare or
  closed-hour profiles unavailable.
- Category pooling can estimate an average where the exposure model identifies
  it, but does not recover within-gap shape.
- A broader or shrinkage-based profile can supply a model-dependent estimate;
  its source and uncertainty must be disclosed and validated out of sample.
  Selecting that policy remains the user's decision.

**Cheapest disconfirming observation:** obtain trustworthy paired five-minute
prices for a currently unobserved target slot over representative dates, or
independently varying gap exposures, and check the resulting information matrix
and out-of-sample stability.

**Load-bearing assumption:** the additive expected-variance model and the
comparability of observations within each selected profile group. A full-rank
matrix cannot correct a wrong proxy, correlated increments, or regime change.

**Search and limitations:** this was a narrow English-language check of the
repository, the NYSE calendar, NIST's statistical reference, and one rolling
public ES sample on 2026-11-15; it was not a systematic data or literature
survey. CME contract and basis pages returned HTTP 403, so their content was
not verified. No representative multi-year point-in-time ES/SPX dataset was
available in the inspected unignored repository files, and no production
profile or empirical ES-to-SPX error estimate is claimed. The counterexample
and alternative explanations were checked locally, not by an independent
reviewer.
