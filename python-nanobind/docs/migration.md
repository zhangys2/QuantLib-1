# Migrating from QuantLib-SWIG to qlnb

`qlnb` is an experimental nanobind binding surface for QuantLib. It aims for
familiar APIs where practical, but **does not** mirror the full SWIG hierarchy.

Import style is intentionally close:

```python
import qlnb as ql   # instead of: import QuantLib as ql
```

## Design differences (read first)

nanobind does not support general multiple inheritance / base-pointer
adjustment. Types that are MI-heavy in C++ (`FlatForward`, bonds, swaps, rate
helpers, FRAs, option engines) are exposed as **factories** or **concrete
wrappers** rather than as full class hierarchies.

Consequences:

- `FlatForward(...)` returns a `YieldTermStructureHandle`, not a curve object.
- `BlackConstantVol(...)` returns a vol handle suitable for processes.
- Bond/swap/option engines are attached via `set_pricing_engine(...)` helpers
  that take handles or processes — you do not construct `DiscountingBondEngine`
  / `AnalyticEuropeanEngine` objects yourself in most paths (factory aliases
  exist for options).
- Day counters and calendars are value-semantic pimpl types (construct via
  factory functions: `ql.Actual365Fixed()`, `ql.TARGET()`, …).

## Dates and Settings

| SWIG (`QuantLib`) | qlnb |
| --- | --- |
| `ql.Date(15, ql.May, 1998)` | `ql.Date(15, ql.Month.May, 1998)` |
| `ql.Settings.instance().evaluationDate = d` | `ql.set_evaluation_date(d)` or `ql.Settings.instance().evaluation_date = d` |
| `ql.Settings.instance().evaluationDate` | `ql.get_evaluation_date()` / `.evaluation_date` |
| camelCase members (`dayOfMonth`) | snake_case (`day_of_month`) |

```python
import qlnb as ql

d = ql.Date(15, ql.Month.May, 1998)
ql.set_evaluation_date(d)
assert ql.get_evaluation_date() == d
```

Months live under `ql.Month.*`. Option types under `ql.OptionType.*` (not
`ql.Option.Put`).

## Quotes, handles, factories

```python
# SWIG
q = ql.SimpleQuote(36.0)
h = ql.QuoteHandle(q)

# qlnb — same, plus a convenience factory
q = ql.SimpleQuote(36.0)
h = ql.QuoteHandle(q)
h2 = ql.make_quote_handle(36.0)
```

Relinkable quote handles are available as `ql.RelinkableQuoteHandle`.

## FlatForward returns a handle

```python
# SWIG
curve = ql.FlatForward(ref, 0.06, dc)
ts = ql.YieldTermStructureHandle(curve)

# qlnb — FlatForward already returns YieldTermStructureHandle
ts = ql.FlatForward(ref, 0.06, dc)
print(ts.discount(maturity))
```

The same pattern applies to `PiecewiseLogLinearDiscountCurve(...)` and
`BlackConstantVol(...)` (vol handle).

## Schedule, calendars, day counters

```python
cal = ql.TARGET()
dc = ql.Actual365Fixed()
tenor = ql.Period(6, ql.TimeUnit.Months)
sched = ql.Schedule(
    start,
    end,
    tenor,
    cal,
    ql.BusinessDayConvention.ModifiedFollowing,
    ql.BusinessDayConvention.ModifiedFollowing,
    ql.DateGeneration.Forward,
    False,
)
dates = sched.dates()
```

Enums are nested (`ql.BusinessDayConvention.ModifiedFollowing`,
`ql.DateGeneration.Forward`, `ql.Frequency.Semiannual`).

## Bonds and swaps

Engines take a discount curve handle directly:

```python
bond = ql.FixedRateBond(
    settlement_days,
    face,
    schedule,
    [0.05],
    ql.ActualActual(ql.ActualActualConvention.ISDA),
)
bond.set_pricing_engine(discount_curve)  # YieldTermStructureHandle
npv = bond.NPV()
# See Phase 72 for bond_yield / duration / convexity / z_spread.

swap = ql.VanillaSwap(
    ql.SwapType.Payer,
    notional,
    fixed_schedule,
    fixed_rate,
    fixed_dc,
    float_schedule,
    ql.Euribor6M(forecast_curve),
    0.0,
    float_dc,
)
swap.set_pricing_engine(discount_curve)
print(swap.fair_rate(), swap.NPV())
```

Deposit helpers and piecewise curves:

```python
helpers = [
    ql.DepositRateHelper(
        0.01,
        ql.Period(3, ql.TimeUnit.Months),
        2,
        cal,
        ql.BusinessDayConvention.ModifiedFollowing,
        True,
        ql.Actual360(),
    ),
]
curve = ql.PiecewiseLogLinearDiscountCurve(ref, helpers, ql.Actual365Fixed())
```

## Options and engines

```python
process = ql.BlackScholesMertonProcess(
    ql.make_quote_handle(spot),
    dividend_ts,   # YieldTermStructureHandle
    risk_free_ts,  # YieldTermStructureHandle
    ql.BlackConstantVol(ref, cal, vol, dc),
)

payoff = ql.PlainVanillaPayoff(ql.OptionType.Put, strike)
exercise = ql.EuropeanExercise(maturity)
option = ql.EuropeanOption(payoff, exercise)

# Preferred: pass the process; engine is constructed inside the binding
option.set_pricing_engine(process)

# Or use the AnalyticEuropeanEngine factory alias (returns the process token)
option.set_pricing_engine(ql.AnalyticEuropeanEngine(process))

npv = option.NPV()
delta = option.delta()
iv = option.implied_volatility(npv, process)
```

American options use `ql.VanillaOption` + `ql.AmericanExercise` and
`set_pricing_engine` / `BaroneAdesiWhaleyEngine`.

Monte Carlo European:

```python
option.set_mc_pricing_engine(
    process,
    time_steps=84,
    required_samples=50_000,
    seed=42,
)
```

Forward rate agreements:

```python
fra = ql.ForwardRateAgreement(
    ql.Euribor3M(forecast),
    value_date,
    ql.Position.Long,
    strike,
    notional,
    discount,
)
print(fra.NPV(), float(fra.forward_rate()))
```

## NumPy path helper

```python
import numpy as np

paths = ql.simulate_gbm_paths(
    process,
    length=1.0,
    time_steps=84,
    samples=1_000,
    seed=7,
)
# shape: (samples, time_steps + 1)
assert isinstance(paths, np.ndarray)
```

Requires NumPy at import/use time (`pip install qlnb[numpy]` or the `test` extra).

## Quick SWIG → qlnb cheat sheet

| Topic | SWIG | qlnb |
| --- | --- | --- |
| Import | `import QuantLib as ql` | `import qlnb as ql` |
| Month enum | `ql.May` | `ql.Month.May` |
| Put/Call | `ql.Option.Put` | `ql.OptionType.Put` |
| Evaluation date | `Settings.instance().evaluationDate` | `set_evaluation_date` / `.evaluation_date` |
| Flat forward | curve object → wrap in handle | factory returns handle |
| Engines | construct engine, `setPricingEngine` | `set_pricing_engine(handle_or_process)` |
| Naming | camelCase | snake_case |
| Coverage | broad SWIG surface | focused phase 0–12 surface |

## Compatibility shim (`qlnb.compat`)

For scripts that expect SWIG-ish names, import the optional shim:

```python
import qlnb.compat as ql

d = ql.Date(15, ql.May, 1998)                 # module-level month
ql.Settings.instance().evaluationDate = d     # camelCase property
payoff = ql.PlainVanillaPayoff(ql.Option.Put, 40.0)
option = ql.EuropeanOption(payoff, ql.EuropeanExercise(d + 365))
option.setPricingEngine(process)              # camelCase method alias
bond.cleanPrice()                             # alias of clean_price()
```

**This is not full SWIG parity.** Prefer the native snake_case qlnb API for new
code. The shim only covers common renames documented above (months, Option
namespace, Settings, and camelCase aliases on types already bound by qlnb).

## Phase-4 instruments

Barrier options and caps/floors follow the same factory / concrete-wrapper
pattern (no Instrument MI hierarchy in Python):

```python
barrier = ql.BarrierOption(
    ql.BarrierType.DownIn,
    90.0,
    0.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
barrier.set_pricing_engine(process)  # AnalyticBarrierEngine

cap = ql.make_cap(ql.Period(5, ql.TimeUnit.Years), ql.Euribor6M(curve), 0.07)
cap.set_pricing_engine(curve, volatility=0.20)
```

See Phase 69 for `CapFloor.implied_volatility`.

## Phase-5 rates options and curve helpers

European swaptions and zero-coupon bonds use the same standalone-wrapper
pattern. Engines are attached via `set_pricing_engine` helpers (no MI engine
hierarchy in Python):

```python
swap = ql.make_vanilla_swap(
    ql.Period(10, ql.TimeUnit.Years),
    ql.Euribor6M(curve),
    0.06,
    effective_date,
)
swaption = ql.Swaption(swap, ql.EuropeanExercise(exercise_date))
swaption.set_pricing_engine(curve, volatility=0.20)

zcb = ql.ZeroCouponBond(2, ql.TARGET(), 100.0, maturity)
zcb.set_pricing_engine(curve)
```

Vectorized discount factors (requires NumPy):

```python
import numpy as np

dfs = ql.discount_times(curve, np.array([0.5, 1.0, 2.0]))
dfs2 = ql.discount_dates(curve, [d1, d2, d3])
```

`FraRateHelper` / `SwapRateHelper` extend the deposit-only bootstrap surface.
`qlnb.compat` adds `Settlement.Physical`, `VanillaSwap.Payer`, and camelCase
aliases on `Swaption` / `ZeroCouponBond`. See Phase 70 for
`Swaption.implied_volatility`.

## Phase-6 floating bonds, tree/FD, overnight indexes

Floating-rate bonds attach a discounting engine **and** a Black Ibor coupon
pricer inside `set_pricing_engine`:

```python
bond = ql.FloatingRateBond(
    2, 100.0, schedule, ql.Euribor6M(forecast), ql.ActualActual(ql.ActualActualConvention.ISDA)
)
bond.set_pricing_engine(discount)  # DiscountingBondEngine + BlackIborCouponPricer
```

American (or European) vanilla options can use tree / FD engines:

```python
opt = ql.VanillaOption(payoff, ql.AmericanExercise(today, maturity))
opt.set_binomial_pricing_engine(process, steps=801)   # Cox–Ross–Rubinstein
opt.set_fd_pricing_engine(process, t_grid=100, x_grid=100)
```

Overnight indexes and a thin MakeOIS helper. `OvernightIndex` is a standalone
opaque wrapper (not a Python subclass of `IborIndex` — Index MI):

```python
sofr = ql.Sofr(curve)
estr = ql.Estr(curve)
ois = ql.make_ois(ql.Period(2, ql.TimeUnit.Years), sofr, 0.03)
ois.set_pricing_engine(curve)
print(ois.fair_rate(), ois.NPV())
```

`FloatingRateBond(..., fixing_days=0)` means “use the index default”
(`Null<Natural>` in C++). Pass a positive value to override.

`qlnb.compat` adds camelCase aliases (`setBinomialPricingEngine`,
`FloatingRateBond.cleanPrice`, `makeOIS`).

## Phase-7 CDS, Bermudan tree swaption, FD mesher

Credit default swaps use a flat hazard-rate factory that returns a
`DefaultProbabilityTermStructureHandle` (same handle-factory pattern as
`FlatForward`):

```python
prob = ql.FlatHazardRate(today, 0.01234, ql.Actual360())
# or: ql.FlatHazardRate(0, calendar, 0.01234, ql.Actual360())
cds = ql.CreditDefaultSwap(
    ql.ProtectionSide.Seller,  # compat: ql.Protection.Seller
    notional,
    spread,
    schedule,
    ql.BusinessDayConvention.ModifiedFollowing,
    ql.Actual360(),
)
cds.set_pricing_engine(prob, recovery_rate=0.4, discount_curve=curve)
print(cds.NPV(), cds.fair_spread())
# See Phase 73 for CdsOption / BlackCdsOptionEngine.
```

Bermudan swaptions attach a Hull–White tree engine (no Gaussian1d/LGM stack):

```python
model = ql.HullWhite(curve, a=0.05, sigma=0.006)
berm = ql.Swaption(swap, ql.BermudanExercise(exercise_dates))
berm.set_tree_pricing_engine(model, time_steps=50)

euro = ql.Swaption(swap, ql.EuropeanExercise(exercise_dates[0]))
euro.set_jamshidian_pricing_engine(model)  # same HW model, European
```

FD mesher locations as NumPy (requires NumPy):

```python
import numpy as np

x = ql.uniform_1d_mesher_locations(0.0, 100.0, 51)
ln_s = ql.fdm_black_scholes_mesher_locations(101, process, maturity=1.0, strike=100.0)
```

`qlnb.compat` adds `Protection.Buyer` / `Protection.Seller`, camelCase CDS /
swaption tree aliases, and `uniform1dMesherLocations`.

## Phase-8 ISDA CDS, GSR / Gaussian1d, FD value grid

ISDA Standard Model engine (same handle args as mid-point, plus numerical
flags):

```python
cds.set_isda_pricing_engine(
    prob,
    recovery_rate=0.4,
    discount_curve=curve,
    numerical_fix=ql.IsdaCdsNumericalFix.Taylor,
    accrual_bias=ql.IsdaCdsAccrualBias.HalfDayBias,
    forwards_in_coupon_period=ql.IsdaCdsForwardsInCouponPeriod.Piecewise,
)
```

Piecewise hazard rates via BackwardFlat interpolation:

```python
haz = ql.InterpolatedHazardRateCurve(
    [today, today + ql.Period(5, ql.TimeUnit.Years)],
    [0.01, 0.015],
    ql.Actual365Fixed(),
    ql.TARGET(),
)
```

GSR / Gaussian1d European swaption (constant reversion / vol):

```python
model = ql.Gsr(curve, [], [0.01], 0.01, T=50.0)
swaption.set_gaussian1d_pricing_engine(model)
```

FD value grid export (European Black–Scholes; columns `[spot, value]`):

```python
grid = ql.fdm_black_scholes_values(
    process, strike=100.0, maturity=1.0, option_type=ql.OptionType.Call,
    t_grid=50, x_grid=51,
)
# grid.shape == (51, 2)
```

## Phase-9 CDS bootstrap, Asians, FD Hull–White swaption

Hazard-rate bootstrap from spread CDS quotes (same pattern as
`DepositRateHelper` + piecewise yield curves):

```python
helpers = [
    ql.SpreadCdsHelper(
        0.005, ql.Period(1, ql.TimeUnit.Years), 1, cal,
        ql.Frequency.Quarterly, ql.BusinessDayConvention.Following,
        ql.DateGeneration.TwentiethIMM, ql.Thirty360(...), 0.4, discount,
    ),
    # ...
]
hazard = ql.PiecewiseHazardRateCurve(today, helpers, ql.Thirty360(...))
# For fair-spread round-trip vs quotes, set:
ql.Settings.instance().include_todays_cash_flows = True
```

Geometric Asian options (analytic engines only in this phase):

```python
cont = ql.ContinuousAveragingAsianOption(
    ql.AverageType.Geometric, payoff, exercise
)
cont.set_pricing_engine(process)  # continuous geometric average-price

disc = ql.DiscreteAveragingAsianOption(
    ql.AverageType.Geometric, 1.0, 0, fixing_dates, payoff, exercise
)
disc.set_pricing_engine(process)  # discrete geometric average-price
```

FD Hull–White Bermudan swaption:

```python
berm.set_fd_hullwhite_pricing_engine(hw_model, t_grid=100, x_grid=100)
```

## Phase-10 CMS / SwapIndex / Hagan pricers

```python
swap_index = ql.EuriborSwapIsdaFixA(ql.Period(10, ql.TimeUnit.Years), curve)
vol = ql.ConstantSwaptionVolatility(
    today, ql.TARGET(), ql.BusinessDayConvention.Following, 0.20, ql.Actual365Fixed()
)
pricer = ql.AnalyticHaganPricer(vol, ql.YieldCurveModel.Standard, ql.make_quote_handle(0.0))
# compat: ql.GFunctionFactory.Standard

coupon = ql.CmsCoupon(pay, 1.0, start, pay, swap_index.fixing_days(), swap_index,
                      day_counter=ibor.day_counter())
coupon.set_pricer(pricer)
print(coupon.rate())

cms = ql.make_cms(ql.Period(5, ql.TimeUnit.Years), swap_index, ibor,
                  discount_curve=curve, pricer=pricer)
print(cms.NPV())
```

## Phase-11 CMS-spread

```python
cms10 = ql.EuriborSwapIsdaFixA(ql.Period(10, ql.TimeUnit.Years), curve, curve)
cms2 = ql.EuriborSwapIsdaFixA(ql.Period(2, ql.TimeUnit.Years), curve, curve)
spread = ql.SwapSpreadIndex("cms10y2y", cms10, cms2)  # make_swap_spread_index

tsr = ql.LinearTsrPricer(vol, ql.make_quote_handle(0.01), curve)
sp_pricer = ql.LognormalCmsSpreadPricer(
    tsr, ql.make_quote_handle(0.6), curve, integration_points=32
)
cpn = ql.CmsSpreadCoupon(pay, 10000.0, start, pay, spread.fixing_days(), spread,
                         day_counter=ql.Actual360())
cpn.set_pricer(sp_pricer)

capped = ql.CappedFlooredCmsSpreadCoupon(
    pay, 10000.0, start, pay, 2, spread, cap=0.03, day_counter=ql.Actual360()
)
```

## Phase-12 zero inflation / ZCIS

```python
hz = ql.RelinkableZeroInflationTermStructureHandle()
index = ql.UKRPI(hz)
# add historic RPI fixings…
helpers = [
    ql.ZeroCouponInflationSwapHelper(
        ql.make_quote_handle(0.0293), ql.Period(3, ql.TimeUnit.Months),
        maturity, ql.UnitedKingdom(), ql.BusinessDayConvention.ModifiedFollowing,
        ql.Thirty360(...), index, ql.CPIInterpolationType.Flat,  # compat: ql.CPI.Flat
    )
]
curve = ql.PiecewiseZeroInflationCurve(today, index.last_fixing_date(),
                                       ql.Frequency.Monthly, dc, helpers)
hz.link_to(curve)

zcis = ql.ZeroCouponInflationSwap(
    ql.SwapType.Payer, 1e6, today, maturity, cal, bdc, dc, 0.0293,
    index, ql.Period(3, ql.TimeUnit.Months), ql.CPIInterpolationType.Flat,
)
zcis.set_pricing_engine(nominal_curve)  # DiscountingSwapEngine
print(zcis.NPV(), zcis.fair_rate())
```

## Phase-13 YoY inflation / YYIIS

```python
hy = ql.RelinkableYoYInflationTermStructureHandle()
rpi = ql.UKRPI()
# add historic RPI fixings on rpi…
yoy = ql.make_yoy_inflation_index(rpi, hy)  # ratio YoY index
# or quoted: yoy = ql.YYUKRPI(hy)

helpers = [
    ql.YearOnYearInflationSwapHelper(
        ql.make_quote_handle(0.0295), ql.Period(2, ql.TimeUnit.Months),
        maturity, ql.UnitedKingdom(), ql.BusinessDayConvention.ModifiedFollowing,
        ql.Thirty360(...), yoy, ql.CPIInterpolationType.Flat, nominal_curve,
    )
]
curve = ql.PiecewiseYoYInflationCurve(
    today, rpi.last_fixing_date(), 0.0295, ql.Frequency.Monthly, dc, helpers
)
hy.link_to(curve)

sched = ql.Schedule(today, maturity, ql.Period(ql.Frequency.Annual), cal,
                    ql.BusinessDayConvention.Unadjusted,
                    ql.BusinessDayConvention.Unadjusted,
                    ql.DateGeneration.Backward, False)
yyiis = ql.YearOnYearInflationSwap(
    ql.SwapType.Payer, 1e6, sched, 0.0295, dc, sched, yoy,
    ql.Period(2, ql.TimeUnit.Months), ql.CPIInterpolationType.Flat,
    0.0, dc, cal,
)
yyiis.set_pricing_engine(nominal_curve)
print(yyiis.NPV(), yyiis.fair_rate())
```

## Phase-14 YoY inflation caps / floors

```python
vol = ql.ConstantYoYOptionletVolatility(
    0.01, 0, cal, ql.BusinessDayConvention.ModifiedFollowing, dc,
    ql.Period(2, ql.TimeUnit.Months), ql.Frequency.Annual,
)
cap = ql.YoYInflationCapFloor(
    ql.YoYInflationCapFloorType.Cap, sched, yoy,
    ql.Period(2, ql.TimeUnit.Months), ql.CPIInterpolationType.Flat,
    0.03, cal, dc, nominal=1e6,
)
cap.set_pricing_engine(yoy, vol, nominal_curve, model="black")
print(cap.NPV())

# or MakeYoYInflationCapFloor helper:
cap2 = ql.make_yoy_inflation_capfloor(
    ql.YoYInflationCapFloorType.Cap, yoy, 5, cal,
    ql.Period(2, ql.TimeUnit.Months), ql.CPIInterpolationType.Flat, 0.03,
)
```

## Phase-15 CPISwap / CPIBond

```python
base = ql.cpi_lagged_fixing(index, today, lag, ql.CPIInterpolationType.Flat)
bond = ql.CPIBond(
    3, 1e6, 206.1, ql.Period(3, ql.TimeUnit.Months), index,
    ql.CPIInterpolationType.Flat, schedule, [0.1], ql.Actual365Fixed(),
)
bond.set_pricing_engine(nominal_curve)
print(bond.clean_price(), bond.dirty_price())

swap = ql.CPISwap(
    ql.SwapType.Payer, 1e6, True, 0.0, ql.Actual365Fixed(), float_sched,
    ql.BusinessDayConvention.ModifiedFollowing, 0, ql.GBPLibor(ql.Period(6, ql.TimeUnit.Months), nominal),
    0.1, 206.1, ql.Actual365Fixed(), fixed_sched,
    ql.BusinessDayConvention.ModifiedFollowing, lag, index,
)
swap.set_pricing_engine(nominal_curve)
```

## Phase-16 CPICapFloor

```python
cap_px = ql.Matrix(4, 7, flat_cap_prices)   # strikes × maturities, prices in absolute
floor_px = ql.Matrix(4, 7, flat_floor_prices)
surf = ql.InterpolatedCPICapFloorTermPriceSurface(
    1.0, base_zero_rate, lag, cal, bdc, dc, index,
    ql.CPIInterpolationType.Flat, nominal,
    [0.03, 0.04, 0.05, 0.06], [-0.01, 0.0, 0.01, 0.02],
    [ql.Period(3, ql.TimeUnit.Years), ...],
    cap_px, floor_px,
)
base = ql.cpi_lagged_fixing(index, today, lag, ql.CPIInterpolationType.Linear)
cap = ql.CPICapFloor(
    ql.OptionType.Call, 1.0, today, base, today + ql.Period(3, ql.TimeUnit.Years),
    cal, ql.BusinessDayConvention.Unadjusted, cal,
    ql.BusinessDayConvention.ModifiedFollowing, 0.03, index, lag,
    ql.CPIInterpolationType.Linear,
)
cap.set_pricing_engine(surf)
print(cap.NPV(), surf.cap_price(ql.Period(3, ql.TimeUnit.Years), 0.03))
```

## Phase-17 inflation seasonality

```python
factors = [1.003245, 1.0, 0.999715, 1.000495, 1.000929, 0.998687,
           0.995949, 0.994682, 0.995949, 1.000519, 1.003705, 1.004186]
base = ql.Date(31, ql.Month.January, curve.base_date().year())
seasonality = ql.MultiplicativePriceSeasonality(
    base, ql.Frequency.Monthly, factors
)
curve.set_seasonality(seasonality)   # adjusts forecast fixings
assert curve.has_seasonality()
curve.set_seasonality()              # clear
start, end = ql.inflation_period(ql.Date(15, ql.Month.March, 2007),
                                 ql.Frequency.Monthly)
```

## Phase-18 CPI coupons / CPILeg

```python
index.clear_fixings()  # IndexManager is process-global across tests

leg = ql.make_cpi_leg(
    schedule, index, ql.Period(3, ql.TimeUnit.Months), ql.Actual365Fixed(),
    base_cpi=206.1, notional=1e6, fixed_rate=0.1,
    payment_calendar=cal, subtract_inflation_nominal=False,
)
ql.set_cpi_coupon_pricer(leg, ql.CPICouponPricer(nominal_curve))
npv = ql.cashflows_npv(leg, nominal_curve, settlement)
accrued = ql.cashflows_accrued_amount(leg, settlement)
clean = (npv - accrued) * 100.0 / 1e6

cpn = ql.CPICoupon(
    206.1, pay, 1e6, start, end, index, lag,
    ql.CPIInterpolationType.Flat, ql.Actual365Fixed(), 0.1,
)
cpn.set_pricer(ql.CPICouponPricer(nominal_curve))
print(cpn.rate(), cpn.index_fixing() / cpn.base_CPI() * cpn.fixed_rate())
```

`CPILeg` already attaches a default `CPICouponPricer`; `set_cpi_coupon_pricer`
is optional when you need a nominal curve on the pricer.

Vol-dependent CPI optionlets need a Black/Bachelier pricer (QuantLib's base
`CPICouponPricer::optionletPriceImp` always fails). See Phase 65.

## Phase-19 YoY coupons / yoyInflationLeg

```python
leg = ql.make_yoy_inflation_leg(
    schedule, calendar, yoy_index,
    ql.Period(2, ql.TimeUnit.Months), ql.CPIInterpolationType.Flat,
    ql.Thirty360(ql.Thirty360Convention.BondBasis),
    notional=1e6,
)
ql.set_yoy_coupon_pricer(leg, ql.YoYInflationCouponPricer(nominal_curve))
npv = ql.cashflows_npv(leg, nominal_curve, settlement)

cpn = ql.YoYInflationCoupon(
    pay, 1e6, start, end, 0, yoy_index, lag,
    ql.CPIInterpolationType.Flat, dc, gearing=1.0, spread=0.0,
)
cpn.set_pricer(ql.YoYInflationCouponPricer(nominal_curve))
print(cpn.fixing_date(), cpn.rate(), cpn.index_fixing())
```

Uncapped `yoyInflationLeg` attaches a default `YoYInflationCouponPricer`.
Capped/floored legs need `BlackYoYInflationCouponPricer` (or unit-displaced /
Bachelier) with a `YoYOptionletVolatilitySurfaceHandle`.

## Phase-20 capped/floored YoY coupons

```python
vol = ql.ConstantYoYOptionletVolatility(
    0.01, 0, cal, bdc, dc, lag, ql.Frequency.Annual,
)
pricer = ql.BlackYoYInflationCouponPricer(nominal, vol)

capped = ql.make_yoy_inflation_leg(
    schedule, cal, yoy, lag, interp, dc, cap=0.10,
)
ql.set_yoy_coupon_pricer(capped, pricer)
assert isinstance(capped[0], ql.CappedFlooredYoYInflationCoupon)
assert capped[0].is_capped() and capped[0].cap() == 0.10

# Decomposition: capped ≈ vanilla − Cap (tol 1e-10)
vanilla = ql.make_yoy_inflation_leg(schedule, cal, yoy, lag, interp, dc)
cap = ql.YoYInflationCapFloor(ql.YoYInflationCapFloorType.Cap, vanilla, 0.10)
cap.set_pricing_engine(yoy, vol, nominal, "black")
```

## Phase-21 Indexed / CPI / ZeroInflation cash flows

```python
leg = ql.make_cpi_leg(..., base_cpi=206.1, subtract_inflation_nominal=False)
terminal = leg[-1]  # CPICashFlow (bond-style: notional * I(T)/I(0))
assert isinstance(terminal, ql.CPICashFlow)
assert terminal.amount() == terminal.notional() * terminal.index_fixing() / terminal.base_fixing()

cf = ql.ZeroInflationCashFlow(
    1e6, index, ql.CPIInterpolationType.Flat,
    start, end, lag, payment, growth_only=True,
)
# ZCIS inflation leg exposes the same type:
zcis = ql.ZeroCouponInflationSwap(...)
assert isinstance(zcis.inflation_leg()[0], ql.ZeroInflationCashFlow)
```

`subtract_inflation_nominal` on `make_cpi_leg` maps to CPICashFlow `growth_only`
(False = bond notional × ratio; True = swap-style ratio − 1).

## Phase-22 YoY cap/floor term price surface

```python
nominal = ql.InterpolatedZeroCurve(dates, yields, ql.Actual365Fixed(), "cubic")
surface = ql.InterpolatedYoYCapFloorTermPriceSurface(
    0, ql.Period(3, ql.TimeUnit.Months), yoy_index,
    ql.CPIInterpolationType.Linear, nominal, ql.Actual365Fixed(),
    ql.TARGET(), ql.BusinessDayConvention.ModifiedFollowing,
    cap_strikes, floor_strikes, maturities, cap_prices, floor_prices,
)
times, rates = surface.atm_yoy_swap_time_rates()
dates, _ = surface.atm_yoy_swap_date_rates()
print(surface.atm_yoy_swap_rate(dates[0]), surface.atm_yoy_rate(dates[0]))
yoy_ts = surface.yoy_ts()  # bootstrapped from put-call parity
```

Cap/floor matrix entries are **absolute prices** (unlike CPI Phase-16 which
uses quote/10000). YoY optionlet strippers remain deferred (`\bug` in QL).

## Phase-23 callable / puttable bonds

```python
calls = [
    ql.make_callability(110.0, ql.BondPriceType.Clean, ql.CallabilityType.Call, d)
    for d in call_dates
]
bond = ql.CallableFixedRateBond(
    3, 10000.0, schedule, [0.05],
    ql.Thirty360(ql.Thirty360Convention.BondBasis),
    ql.BusinessDayConvention.ModifiedFollowing,
    100.0, issue, calls,
)
model = ql.HullWhite(discount_curve)  # a=0.1, sigma=0.01
bond.set_tree_pricing_engine(model, 240, discount_curve)
print(bond.clean_price())
```

Tree engine via `set_tree_pricing_engine`. See Phase 54 for Black European
callable engines. Compat alias: `import qlnb.compat as ql` →
`ql.Callability(...)` maps to `make_callability`.

## Phase-54 Black callable bond engines

```python
bond = ql.CallableZeroCouponBond(
    3, 10000.0, calendar, maturity,
    ql.Thirty360(ql.Thirty360Convention.BondBasis),
    ql.BusinessDayConvention.ModifiedFollowing,
    100.0, issue,
    [ql.make_callability(
        100.0, ql.BondPriceType.Clean, ql.CallabilityType.Call, call_date
    )],
)
bond.set_black_pricing_engine(0.3, discount_curve)  # fwd yield vol
# or: bond.set_black_pricing_engine(ql.make_quote_handle(0.3), discount_curve)
print(bond.clean_price())  # ≈ 74.54521578 (cached European call)
```

`BlackCallableFixedRateBondEngine` / `BlackCallableZeroCouponBondEngine` for
European embedded options (Hull Ch.20). Compat: `setBlackPricingEngine`.
See Phase 55 for Black implied volatility.

## Phase-55 callable bond implied volatility

```python
vol = bond.implied_volatility(
    ql.BondPrice(78.50, ql.BondPriceType.Dirty),
    discount_curve,
    accuracy=1e-8,
    max_evaluations=200,
)
bond.set_black_pricing_engine(vol, discount_curve)
assert abs(bond.dirty_price() - 78.50) < 1e-4
```

Black fwd-yield implied vol matching a target `BondPrice` (Clean or Dirty).
Works for European callables (same Black engines as Phase 54). Compat:
`impliedVolatility`.

## Phase-56 callable bond OAS

```python
bond.set_tree_pricing_engine(model, 240, discount_curve)
oas = bond.oas(
    96.0, discount_curve, dc,
    ql.Compounding.Compounded, ql.Frequency.Semiannual,
)
price = bond.clean_price_oas(
    oas, discount_curve, dc,
    ql.Compounding.Compounded, ql.Frequency.Semiannual,
)
dur = bond.effective_duration(
    oas, discount_curve, dc,
    ql.Compounding.Compounded, ql.Frequency.Semiannual,
)
```

Option-adjusted spread and clean price at OAS require a **tree** pricing
engine (`set_tree_pricing_engine`); Black engines ignore the OAS spread.
Also: `effective_duration` / `effective_convexity` (default bump `2e-4`).
Compat: `OAS`, `cleanPriceOAS`, `effectiveDuration`, `effectiveConvexity`.

## Phase-57 convertible bonds

```python
process = ql.BlackScholesMertonProcess(spot, q, r, vol)
exercise = ql.EuropeanExercise(maturity)
bond = ql.ConvertibleZeroCouponBond(
    exercise, conversion_ratio, [], issue, 3, dc, schedule, 100.0,
)
bond.set_binomial_pricing_engine(process, 401, 0.005)  # credit spread
print(bond.NPV())
```

Standalone wrappers (Bond/Instrument MI). Engine is
`BinomialConvertibleEngine<CoxRossRubinstein>` (Tsiveriotis–Fernandes).
Credit spread is a `QuoteHandle` or scalar. Soft calls via
`make_soft_callability(amount, BondPriceType, date, trigger)`.
See Phase 58 for floating convertibles. Compat: `setBinomialPricingEngine`,
`SoftCallability`.

## Phase-58 floating convertible bonds

```python
index = ql.Euribor1Y(discount_curve)
bond = ql.ConvertibleFloatingRateBond(
    exercise, conversion_ratio, [], issue, 3,
    index, 2, [], dc, schedule, 100.0,
)
bond.set_binomial_pricing_engine(process, 401, 0.005)
print(bond.NPV())
```

Same CRR Tsiveriotis–Fernandes engine as Phase 57. Index is an `IborIndex`
(`Euribor1Y` / `Euribor3M` / `Euribor6M`). Empty `spreads` means `{0.0}`.
Compat: `setBinomialPricingEngine`.

## Phase-24 currencies / FX forward

```python
usd, sgd = ql.USDCurrency(), ql.SGDCurrency()
eur_usd = ql.ExchangeRate(ql.EURCurrency(), usd, 1.2042)
ql.set_money_conversion(ql.MoneyConversionType.NoConversion)
assert eur_usd.exchange(50000.0 * ql.EURCurrency()).value() == 60210.0

today = ql.Date(15, ql.Month.March, 2024)
ql.set_evaluation_date(today)
maturity = today + ql.Period(6, ql.TimeUnit.Months)
usd_curve = ql.FlatForward(today, 0.05, ql.Actual365Fixed())
sgd_curve = ql.FlatForward(today, 0.035, ql.Actual365Fixed())
fwd = ql.FxForward(1e6, usd, 1.35e6, sgd, maturity, True)
fwd.set_pricing_engine(usd_curve, sgd_curve, 1.35)
print(fwd.fair_forward_rate(), fwd.NPV())
```

Currency subclasses are sliced to value `Currency` (no MI hierarchy).
`FxForward` is a standalone wrapper; attach `DiscountingFxForwardEngine` via
`set_pricing_engine`. Spot FX is target per unit of source.

## Phase-25 double-barrier options

```python
opt = ql.DoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut,
    50.0, 150.0, 0.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process)  # AnalyticDoubleBarrierEngine
print(opt.NPV())
```

Standalone wrapper (no `OneAssetOption` MI hierarchy). Analytic engine covers
KnockIn/KnockOut European vanilla payoffs. See Phase 26 for binaries, Phase 38
for FD-Heston, Phase 61 for Monte Carlo, and Phase 71 for
`implied_volatility`.

## Phase-26 double-barrier binary options

```python
payoff = ql.CashOrNothingPayoff(ql.OptionType.Call, 0.0, 10.0)
# KnockIn / KnockOut → EuropeanExercise; KIKO / KOKI → AmericanExercise
opt = ql.DoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut,
    80.0, 120.0, 0.0, payoff, ql.EuropeanExercise(maturity),
)
opt.set_binary_pricing_engine(process)  # AnalyticDoubleBarrierBinaryEngine
print(opt.NPV())
```

Vanilla double-barrier path is unchanged (`set_pricing_engine` →
`AnalyticDoubleBarrierEngine`). Use the binary engine attach for cash-or-nothing
payoffs. See Phase 61 for FD-Heston (binary) and Monte Carlo.

## Phase-61 double-barrier binary FD-Heston / MC

```python
# Binary cash-or-nothing: FdHestonDoubleBarrierEngine in the BS limit
opt.set_fd_heston_pricing_engine(model, t_grid=201, x_grid=101, v_grid=3)

# Vanilla double-barrier Monte Carlo
opt.set_mc_pricing_engine(
    process, time_steps=200, required_samples=8192, seed=1, antithetic=True,
)
print(opt.NPV(), opt.error_estimate())
```

`MakeMCDoubleBarrierEngine<PseudoRandom>` on `DoubleBarrierOption`. Set exactly
one of `time_steps` / `steps_per_year` (default `time_steps=200`) and one of
`required_samples` / `required_tolerance` (default `required_samples=8192`).
Compat: `setMcPricingEngine`, `errorEstimate`. Binary FD-Heston reuses
`set_fd_heston_pricing_engine` (Phase 38) with `CashOrNothingPayoff`.

## Phase-27 continuous lookback options

```python
# Floating strike (minmax = prior extremum)
float_opt = ql.ContinuousFloatingLookbackOption(
    100.0,
    ql.FloatingTypePayoff(ql.OptionType.Call),
    ql.EuropeanExercise(maturity),
)
float_opt.set_pricing_engine(process)  # AnalyticContinuousFloatingLookbackEngine

# Fixed strike
fixed_opt = ql.ContinuousFixedLookbackOption(
    100.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 95.0),
    ql.EuropeanExercise(maturity),
)
fixed_opt.set_pricing_engine(process)  # AnalyticContinuousFixedLookbackEngine
```

Standalone wrappers (no `OneAssetOption` MI hierarchy).

## Phase-28 partial-time continuous lookbacks

```python
# Floating: lookback from t=0 to lookback_period_end; lambda_ scales extremum
partial_float = ql.ContinuousPartialFloatingLookbackOption(
    90.0, 1.0, lookback_end,
    ql.FloatingTypePayoff(ql.OptionType.Call),
    ql.EuropeanExercise(maturity),
)
partial_float.set_pricing_engine(process)

# Fixed: lookback starts at lookback_period_start
partial_fixed = ql.ContinuousPartialFixedLookbackOption(
    lookback_start,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
    ql.EuropeanExercise(maturity),
)
partial_fixed.set_pricing_engine(process)
```

Standalone wrappers. The Python kwarg is `lambda_` (avoids the Python keyword).
See Phase 60 for Monte Carlo engines.

## Phase-60 Monte Carlo lookback engines

```python
opt.set_pricing_engine(process)          # analytic
analytic = opt.NPV()
opt.set_mc_pricing_engine(
    process, time_steps=200, required_samples=8192, seed=1, antithetic=True,
)
print(opt.NPV(), opt.error_estimate())
```

`MakeMCLookbackEngine<Option, PseudoRandom>` on all four lookback wrappers
from Phases 27–28. Set exactly one of `time_steps` / `steps_per_year`
(default `time_steps=200`) and one of `required_samples` /
`required_tolerance` (default `required_samples=8192`). Compat:
`setMcPricingEngine`, `errorEstimate`.

## Phase-29 soft barrier options

```python
opt = ql.SoftBarrierOption(
    ql.BarrierType.DownOut,
    90.0,   # barrier_lo
    95.0,   # barrier_hi
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process)  # AnalyticSoftBarrierEngine
print(opt.NPV())
```

Knock-in/out is proportional across `[barrier_lo, barrier_hi]` rather than a
hard barrier. Analytic engine only (Haug p.165); European payoff style.
See Phase 71 for `implied_volatility`.

## Phase-30 partial-time barrier options

```python
opt = ql.PartialTimeBarrierOption(
    ql.BarrierType.DownOut,
    ql.PartialBarrierRange.EndB1,
    100.0, 0.0, cover_event_date,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process)  # AnalyticPartialTimeBarrierOptionEngine
print(opt.NPV())
```

Barrier monitoring covers only part of the option life (`Start` until cover
event, or `EndB1`/`EndB2` from cover event to expiry). Analytic knock-in
partial-time end options are not covered by the QL engine.

## Phase-31 binary barrier options

```python
opt = ql.BarrierOption(
    ql.BarrierType.DownIn,
    100.0, 0.0,
    ql.CashOrNothingPayoff(ql.OptionType.Call, 102.0, 15.0),
    ql.AmericanExercise(today, maturity, True),
)
opt.set_binary_pricing_engine(process)  # AnalyticBinaryBarrierEngine

asset = ql.BarrierOption(
    ql.BarrierType.DownIn,
    100.0, 0.0,
    ql.AssetOrNothingPayoff(ql.OptionType.Call, 102.0),
    ql.AmericanExercise(today, maturity, True),
)
asset.set_binary_pricing_engine(process)
```

Vanilla barrier path is unchanged (`set_pricing_engine` → `AnalyticBarrierEngine`).
Binary barriers use American exercise (Haug at-expiry / one-touch style).
See Phase 62 for FD-Heston (European cash-or-nothing) and Monte Carlo.

## Phase-62 binary-barrier FD-Heston / MC

```python
# European cash-or-nothing + FdHestonBarrierEngine in the BS limit
fd = ql.BarrierOption(
    ql.BarrierType.DownOut, 100.0, 0.0,
    ql.CashOrNothingPayoff(ql.OptionType.Call, 102.0, 15.0),
    ql.EuropeanExercise(maturity),
)
fd.set_fd_heston_pricing_engine(model, t_grid=100, x_grid=200, v_grid=3)

# Vanilla barrier Monte Carlo
opt.set_mc_pricing_engine(
    process, time_steps=200, required_samples=8192, seed=1, antithetic=True,
    brownian_bridge=True,
)
print(opt.NPV(), opt.error_estimate())
```

`MakeMCBarrierEngine<PseudoRandom>` on `BarrierOption`. Set exactly one of
`time_steps` / `steps_per_year` (default `time_steps=200`) and one of
`required_samples` / `required_tolerance` (default `required_samples=8192`).
Optional `biased` (default false). Compat: `setMcPricingEngine`,
`errorEstimate`. Binary FD-Heston reuses `set_fd_heston_pricing_engine`
(Phase 38) with `CashOrNothingPayoff` and European exercise.

## Phase-32 two-asset barrier options

```python
opt = ql.TwoAssetBarrierOption(
    ql.BarrierType.DownOut,
    95.0,  # barrier on asset 2
    ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),  # strike on asset 1
    ql.EuropeanExercise(maturity),
)
# process1 = strike asset, process2 = barrier asset, rho = correlation
opt.set_pricing_engine(process1, process2, 0.5)
# or: opt.set_pricing_engine(process1, process2, ql.make_quote_handle(0.5))
print(opt.NPV())
```

Standalone wrapper (no Option MI in Python). Engine attachment takes two
processes plus correlation rather than a single process factory.

## Phase-33 two-asset correlation options

```python
opt = ql.TwoAssetCorrelationOption(
    ql.OptionType.Call,
    50.0,   # strike1 — conditioning asset
    70.0,   # strike2 — payoff asset
    ql.EuropeanExercise(maturity),
)
# process1 = conditioning asset, process2 = payoff asset
opt.set_pricing_engine(process1, process2, 0.75)
# or: opt.set_pricing_engine(process1, process2, ql.make_quote_handle(0.75))
print(opt.NPV())
```

Pays the asset-2 vanilla payoff only when asset 1 finishes in the money;
otherwise the payoff is zero (Zhang / Haug analytic engine).

## Phase-34 cliquet / ratchet options

```python
opt = ql.CliquetOption(
    ql.PercentageStrikePayoff(ql.OptionType.Call, 1.1),  # moneyness
    ql.EuropeanExercise(maturity),
    [today + 90],  # reset dates
)
opt.set_pricing_engine(process)  # AnalyticCliquetEngine
print(opt.NPV(), opt.delta(), opt.gamma(), opt.vega())
```

Each reset sets the forward-start strike to `moneyness * spot` at that date.
Standalone wrapper (no OneAssetOption MI in Python).

## Phase-35 forward vanilla options

```python
opt = ql.ForwardVanillaOption(
    1.1,                # moneyness
    today + 90,         # reset date
    ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),  # strike ignored
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process)  # ForwardVanillaEngine<AnalyticEuropeanEngine>
print(opt.NPV())

perf = ql.ForwardVanillaOption(
    1.1, today + 90,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),
    ql.EuropeanExercise(maturity),
)
perf.set_performance_pricing_engine(process)
```

Single reset-date forward-start vanilla (vs multi-reset `CliquetOption`).
Standalone wrapper (no OneAssetOption MI in Python).

## Phase-36 Heston stochastic volatility

```python
process = ql.HestonProcess(
    ql.FlatForward(today, 0.0225, dc),
    ql.FlatForward(today, 0.02, dc),
    ql.make_quote_handle(1.0),
    0.1,   # v0
    3.16,  # kappa
    0.09,  # theta
    0.4,   # sigma
    -0.2,  # rho
)
model = ql.HestonModel(process)
opt = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 1.05),
    ql.EuropeanExercise(maturity),
)
opt.set_heston_pricing_engine(model, integration_order=64)
print(opt.NPV())
```

`HestonProcess` / `HestonModel` are concrete wrappers (no StochasticProcess /
CalibratedModel MI in Python). See Phase 37 for FD-Heston, Phase 48 for
calibration, and Phase 59 for Monte Carlo.

## Phase-59 MC European Heston

```python
process = ql.HestonProcess(
    r, q, ql.make_quote_handle(1.05),
    0.3, 1.16, 0.2, 0.8, 0.8,
    ql.HestonDiscretization.QuadraticExponentialMartingale,
)
opt = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Put, 1.05),
    ql.EuropeanExercise(exercise_date),
)
opt.set_mc_heston_pricing_engine(
    process, steps_per_year=11, required_samples=50000, seed=1234,
)
print(opt.NPV(), opt.error_estimate())  # NPV ≈ 0.0632851308977151
```

`MakeMCEuropeanHestonEngine<PseudoRandom>`. Set exactly one of `time_steps`
or `steps_per_year` (default `steps_per_year=11`). Compat:
`setMcHestonPricingEngine`, `errorEstimate`.

## Phase-37 FD Heston engine

```python
opt = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Put, 100.0),
    ql.AmericanExercise(today, maturity),
)
opt.set_fd_heston_pricing_engine(
    model, t_grid=200, x_grid=100, v_grid=50
)
print(opt.NPV(), opt.delta(), opt.gamma())
```

Uses `FdHestonVanillaEngine` with the default Hundsdorfer scheme. Analytic
path remains `set_heston_pricing_engine`. See Phase 47 for `scheme_desc`;
dividend / quanto overloads deferred.

## Phase-38 FD Heston barrier engines

```python
barrier = ql.BarrierOption(
    ql.BarrierType.UpOut,
    135.0,
    0.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
barrier.set_fd_heston_pricing_engine(model, t_grid=50, x_grid=400, v_grid=100)

dbl = ql.DoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut,
    80.0,
    120.0,
    0.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
dbl.set_fd_heston_pricing_engine(model, t_grid=100, x_grid=100, v_grid=50)
```

Analytic barrier paths are unchanged (`set_pricing_engine` /
`set_binary_pricing_engine`). See Phase 47 for `scheme_desc`; see Phase 66
for discrete-dividend overloads. `FdHestonDoubleBarrierEngine` has no
dividend constructor in QuantLib.

## Phase-39 Bates jump-diffusion

```python
process = ql.BatesProcess(
    ql.FlatForward(today, 0.1, dc),
    ql.FlatForward(today, 0.04, dc),
    ql.make_quote_handle(32.0),
    0.05,   # v0
    5.0,    # kappa
    0.05,   # theta
    1e-4,   # sigma
    0.0,    # rho
    0.0001, # jump_intensity (λ)
    0.0,    # nu
    0.0001, # delta
)
model = ql.BatesModel(process)
opt = ql.EuropeanOption(
    ql.PlainVanillaPayoff(ql.OptionType.Put, 30.0),
    ql.EuropeanExercise(maturity),
)
opt.set_bates_pricing_engine(model, integration_order=64)
print(opt.NPV())
```

`BatesProcess` / `BatesModel` are concrete wrappers (no HestonProcess /
HestonModel MI in Python). Use `jump_intensity` instead of C++ `lambda`.
See Phase 45 for FD-Bates and Phase 46 for DetJump / DoubleExp variants.

## Phase-45 FD Bates vanilla engine

```python
opt.set_fd_bates_pricing_engine(model, t_grid=50, x_grid=100, v_grid=30)
print(opt.NPV())
```

Uses `FdBatesVanillaEngine` with the default Hundsdorfer scheme. Analytic
`set_bates_pricing_engine` is unchanged. See Phase 47 for `scheme_desc`;
Phase 63 for dividend overloads.

## Phase-63 FD Bates dividend overloads

```python
opt.set_fd_bates_dividend_pricing_engine(
    model, dividend_dates, dividend_amounts,
    t_grid=50, x_grid=100, v_grid=30,
)
print(opt.NPV())
```

`FdBatesVanillaEngine` with a `DividendSchedule`. Empty dividends match
`set_fd_bates_pricing_engine`. Compat: `setFdBatesDividendPricingEngine`.

## Phase-46 Bates DetJump / DoubleExp variants

```python
det = ql.BatesDetJumpModel(bates_process, kappa_lambda=1.0, theta_lambda=1e-4)
opt.set_bates_det_jump_pricing_engine(det, integration_order=64)

dexp = ql.BatesDoubleExpModel(
    bates_process, jump_intensity=1e-4, nu_up=1e-4, nu_down=1e-4
)
opt.set_bates_double_exp_pricing_engine(dexp, integration_order=64)

dexp_dj = ql.BatesDoubleExpDetJumpModel(
    bates_process,
    jump_intensity=1e-4,
    nu_up=1e-4,
    nu_down=1e-4,
    p=0.5,
    kappa_lambda=1.0,
    theta_lambda=1e-4,
)
opt.set_bates_double_exp_det_jump_pricing_engine(dexp_dj, integration_order=64)
```

Standalone wrappers (no BatesModel / HestonModel MI). DoubleExp models accept
`HestonProcess` or `BatesProcess`. Use `jump_intensity` / `kappa_lambda` /
`theta_lambda` / `nu_up` / `nu_down` (Python-safe names).

## Phase-47 FdmSchemeDesc

```python
scheme = ql.FdmSchemeDesc.CraigSneyd()
opt.set_fd_heston_pricing_engine(
    model, t_grid=100, x_grid=100, v_grid=50, scheme_desc=scheme
)
# Defaults unchanged: Hundsdorfer for Heston/Bates/barrier FD; Douglas for BS FD.
assert scheme.type == ql.FdmSchemeType.CraigSneyd
```

Value-semantic descriptor (`type`, `theta`, `mu`) with static factories matching
C++ `FdmSchemeDesc::*()`. See Phase 51 for FD dividend overloads.

## Phase-48 Heston model calibration

```python
helpers = []
for maturity in maturities:
    for strike in strikes:
        h = ql.HestonModelHelper(
            maturity,
            ql.NullCalendar(),
            ql.make_quote_handle(1.0),
            strike,
            ql.make_quote_handle(0.1),  # market vol
            risk_free,
            dividend,
        )
        h.set_pricing_engine(model, integration_order=96)
        helpers.append(h)

model.calibrate(
    helpers,
    ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8),
    ql.EndCriteria(400, 40, 1e-8, 1e-8, 1e-8),
)
print(model.v0(), model.kappa(), model.theta(), model.sigma(), model.rho())
print(model.end_criteria())  # EndCriteriaType
```

Standalone helpers / optimizer (no CalibratedModel / OptimizationMethod MI).
`EndCriteriaType.None_` maps to C++ `EndCriteria::None` (Python keyword-safe).
See Phase 49 for COS / exponential-fitting engines on helpers.
See Phase 64 for the Sepp DAX calibration golden (SSE ≈ 177.2).

## Phase-64 DAX Heston calibration golden

```python
# HestonModelTests::testDAXCalibration (Sepp DAX vol surface)
today = ql.Date(5, ql.Month.July, 2002)
ql.set_evaluation_date(today)
risk_free = ql.ZeroCurve(dates, rates, ql.Actual365Fixed())
helpers = [
    ql.HestonModelHelper(
        ql.Period((t + 3) // 7, ql.TimeUnit.Weeks),
        ql.TARGET(), s0, strike, vol, risk_free, dividend,
        error_type=ql.CalibrationErrorType.ImpliedVolError,
    )
    for ...
]
for h in helpers:
    h.set_pricing_engine(model, integration_order=64)
model.calibrate(
    helpers,
    ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8),
    ql.EndCriteria(400, 40, 1e-8, 1e-8, 1e-8),
)
sse = sum((h.calibration_error() * 100.0) ** 2 for h in helpers)
# sse ≈ 177.2
```

`ZeroCurve` is an alias for linear `InterpolatedZeroCurve`. Calibrate with
`CalibrationErrorType.ImpliedVolError` (the Phase-48 default is
`RelativePriceError`).

## Phase-65 CPI vol-dependent optionlets

QuantLib's `CPICouponPricer` prices swaplets but `optionletPriceImp` is a
stub (`QL_FAIL`). Unlike YoY, there are no Black/Bachelier descendents in
`ql/`. qlnb fills them at the binding layer.

```python
vol = ql.ConstantCPIVolatility(
    0.10, 0, calendar, ql.BusinessDayConvention.ModifiedFollowing,
    dc, observation_lag, ql.Frequency.Monthly, False,
)
pricer = ql.BlackCPICouponPricer(nominal, caplet_vol=vol)
cpn.set_pricer(pricer)
fwd = cpn.adjusted_index_growth()   # index ratio, not a YoY rate
print(cpn.caplet_price(fwd), cpn.floorlet_price(fwd))
```

Strikes are in **index-ratio** space (same units as `adjusted_index_growth`).
`BachelierCPICouponPricer` is the normal-vol alternative. Swaplets are
unchanged versus plain `CPICouponPricer`. YoY optionlet strippers remain
deferred (`\bug` in QL).

## Phase-66 FD Heston barrier dividends

```python
barrier = ql.BarrierOption(
    ql.BarrierType.UpOut, 135.0, 0.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
barrier.set_fd_heston_dividend_pricing_engine(
    model, [today + 180], [5.0], t_grid=50, x_grid=200, v_grid=50
)
print(barrier.NPV())
```

`FdHestonBarrierEngine` dividend constructor (Phase 38 deferred this). An
empty schedule matches `set_fd_heston_pricing_engine`. Double-barrier FD
Heston has no dividend overload in QuantLib.

## Phase-67 FD Black-Scholes barrier

```python
barrier.set_fd_pricing_engine(process, t_grid=200, x_grid=400)
barrier.set_fd_dividend_pricing_engine(
    process, [today + 180], [30.0], t_grid=100, x_grid=100
)
```

`FdBlackScholesBarrierEngine` (default Douglas scheme). Matches analytic
Haug barriers within the suite FD tolerance (5e-3). Dividend goldens from
`BarrierOptionTest::testDividendBarrier`. See Phase 66 for the Heston FD
dividend path. See Phase 68 for implied volatility.

## Phase-68 barrier implied volatility

```python
vol = barrier.implied_volatility(1.0, dummy_process, accuracy=1e-6)
barrier.set_pricing_engine(process_at(vol))

vol_div = barrier.implied_volatility(
    8.0, dummy_process, [today + 180], [10.0], accuracy=1e-6
)
barrier.set_fd_dividend_pricing_engine(process_at(vol_div), dates, amounts)
```

No-dividend path uses `AnalyticBarrierEngine`; cash dividends use
`FdBlackScholesBarrierEngine` (same as C++). Dummy process vol is unused
(the solver clones and replaces it). Compat: `impliedVolatility`.

## Phase-69 cap/floor implied volatility

```python
cap.set_pricing_engine(curve, 0.20)
price = cap.NPV()
vol = cap.implied_volatility(price, curve, guess=0.10, accuracy=1e-8)
# vol ≈ 0.20
```

Black (or normal) term vol matching a target NPV. Defaults match C++
(`guess=0.10`, `vol_type=ShiftedLognormal`). Compat: `impliedVolatility`.
See Phase 70 for `Swaption.implied_volatility`.

## Phase-70 swaption implied volatility

```python
swaption.set_pricing_engine(curve, 0.20)
price = swaption.NPV()
vol = swaption.implied_volatility(price, curve, guess=0.10, accuracy=1e-8)
# vol ≈ 0.20
```

Black (or normal) term vol matching a target spot or forward price.
Defaults match C++ (`guess=0.10`, `vol_type=ShiftedLognormal`,
`price_type=SwaptionPriceType.Spot`). Compat: `impliedVolatility`.

## Phase-71 double / soft barrier implied volatility

```python
vol = double_barrier.implied_volatility(4.3515, dummy_process, accuracy=1e-6)
# vol ≈ 0.15  (Haug KO call 50/150, t=0.25)

vol = soft_barrier.implied_volatility(3.8075, dummy_process, accuracy=1e-6)
# vol ≈ 0.10  (Haug DownOut L=U=95, t=0.5)
```

Analytic engines only (`AnalyticDoubleBarrierEngine` /
`AnalyticSoftBarrierEngine`). Dummy process vol is unused (the solver
clones and replaces it). Soft-barrier `min_vol` defaults to `1e-6`
(zero vol can NaN the formula). Knock-out double-barrier price is not
monotonic in vol — tighten `min_vol` / `max_vol` if the default
bracket fails. Compat: `impliedVolatility`.

## Phase-72 bond yield / duration / z-spread

```python
y = bond.bond_yield(99.203125, dc, ql.Compounding.Compounded, ql.Frequency.Semiannual)
px = bond.clean_price(0.02925, dc, ql.Compounding.Compounded, ql.Frequency.Semiannual)
mac = bond.duration(y, dc, ql.Compounding.Compounded, ql.Frequency.Semiannual,
                    ql.DurationType.Macaulay, settlement)
zs = bond.z_spread(px, curve, ql.Compounding.Compounded, ql.Frequency.Semiannual)
```

`bond_yield` is named that way because `yield` is a Python keyword
(compat: `bondYield`). Duration / convexity / z-spread wrap
`BondFunctions` on the existing standalone bond wrappers. Convexity is
the raw C++ value (Bloomberg quotes `convexity/100`). `BondPrice` /
`BondPriceType` now register in `bind_instruments` so yield helpers can
take them before callable bonds load.

## Phase-73 CDS option

```python
swap = ql.CreditDefaultSwap(
    ql.ProtectionSide.Seller, notional, strike, schedule, convention, dc
)
swap.set_pricing_engine(prob, 0.4, curve)
opt = ql.CdsOption(swap, ql.EuropeanExercise(expiry))
opt.set_pricing_engine(prob, 0.4, curve, volatility=0.20)
print(opt.NPV(), opt.risky_annuity())
vol = opt.implied_volatility(opt.NPV(), curve, prob, 0.4)
```

Standalone wrapper (no `Option` MI hierarchy). The side of the option is
the side of the underlying CDS. Engine assumes the exercise date equals
the CDS start date (as in C++). Compat: `setPricingEngine`,
`impliedVolatility`, `riskyAnnuity`.

## Phase-74 compound option

```python
opt = ql.CompoundOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 50.0),   # mother
    ql.EuropeanExercise(mat_mother),
    ql.PlainVanillaPayoff(ql.OptionType.Call, 520.0),  # daughter
    ql.EuropeanExercise(mat_daughter),
)
opt.set_pricing_engine(process)  # AnalyticCompoundOptionEngine
print(opt.NPV(), opt.delta(), opt.theta())
```

Standalone wrapper (no `OneAssetOption` MI hierarchy). Wystup closed form
(Haug 2007 values; greeks from sitmo). Compat: `setPricingEngine`.

## Phase-75 Margrabe exchange option

```python
opt = ql.MargrabeOption(1, 1, ql.EuropeanExercise(maturity))
opt.set_pricing_engine(process1, process2, rho=-0.50)
print(opt.NPV(), opt.delta1(), opt.delta2())

am = ql.MargrabeOption(1, 1, ql.AmericanExercise(today, maturity))
am.set_american_pricing_engine(process1, process2, rho=-0.50)
print(am.NPV())
```

Standalone wrapper (no `MultiAssetOption` MI hierarchy). European engine is
Margrabe 1978; American engine reduces to Bjerksund-Stensland. Correlation is
a scalar `Real` (not a `Handle<Quote>`). Compat: `setPricingEngine`,
`setAmericanPricingEngine`, `isExpired`.

## Phase-76 chooser options

```python
simple = ql.SimpleChooserOption(
    choosing_date, 50.0, ql.EuropeanExercise(maturity)
)
simple.set_pricing_engine(process)  # AnalyticSimpleChooserEngine

complex_opt = ql.ComplexChooserOption(
    choosing_date,
    55.0,
    48.0,
    ql.EuropeanExercise(call_maturity),
    ql.EuropeanExercise(put_maturity),
)
complex_opt.set_pricing_engine(process)  # AnalyticComplexChooserEngine
```

Standalone wrappers (no `OneAssetOption` MI hierarchy). Holder chooses call
or put at `choosing_date`. Simple chooser shares strike and expiry; complex
chooser has distinct call/put strikes and expiries. Haug goldens 6.1071 /
6.0508. Compat: `setPricingEngine`, `isExpired`.

## Phase-77 Turnbull-Wakeman arithmetic Asian

```python
opt = ql.DiscreteAveragingAsianOption(
    ql.AverageType.Arithmetic, 0.0, 0, fixing_dates, payoff, exercise
)
opt.set_turnbull_wakeman_pricing_engine(process)
print(opt.NPV(), opt.delta(), opt.gamma())
```

Moment-matching arithmetic average-price engine (Haug Table 4-28 / Clark).
Requires `AverageType.Arithmetic`. Geometric Asians still use
`set_pricing_engine`. Compat: `setTurnbullWakemanPricingEngine`.

## Phase-78 Kirk spread basket

```python
opt = ql.BasketOption(
    ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 3.0)),
    ql.EuropeanExercise(maturity),
)
opt.set_kirk_pricing_engine(process1, process2, rho=-0.50)
print(opt.NPV())
```

Standalone wrapper (no `MultiAssetOption` MI hierarchy). Kirk 1995
approximation for a European spread on two futures. Pass processes with
`q = r` (QuantLib `BlackProcess` cost-of-carry). Compat:
`setKirkPricingEngine`, `isExpired`.

## Phase-79 Stulz min/max basket

```python
mn = ql.BasketOption(
    ql.MinBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)),
    ql.EuropeanExercise(maturity),
)
mn.set_stulz_pricing_engine(process1, process2, rho=0.90)

mx = ql.BasketOption(
    ql.MaxBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0)),
    ql.EuropeanExercise(maturity),
)
mx.set_stulz_pricing_engine(process1, process2, rho=0.90)
```

Stulz 1982 closed form for a European option on the min or max of two
assets. Compat: `setStulzPricingEngine`.

## Phase-80 variance swap

```python
vs = ql.VarianceSwap(
    ql.Position.Long, 0.04, 50000.0, today, maturity
)
vs.set_replicating_pricing_engine(
    process, call_strikes, put_strikes, dk=5.0
)
print(vs.variance(), vs.NPV())
```

Unseasoned forward variance swap. Replicating engine uses a strip of
vanillas on a `BlackVarianceSurface` smile (Derman, Kamal & Zou 1999).
Compat: `setReplicatingPricingEngine`, `isExpired`, `startDate`,
`maturityDate`.

## Phase-81 MC variance swap

```python
vol_ts = ql.BlackVarianceCurve(
    today, [interm, maturity], [0.10, 0.20], dc
)
vs = ql.VarianceSwap(ql.Position.Long, 0.04, 50000.0, today, maturity)
vs.set_mc_pricing_engine(
    process, steps_per_year=250, required_samples=1023, seed=42
)
print(vs.variance())
```

Monte Carlo fair variance on a `BlackVarianceCurve` (the C++ suite notes
`BlackVarianceSurface` is unreliable for this check). Defaults match the
suite: 250 steps/year, 1023 samples, seed 42. Compat: `setMcPricingEngine`.

## Phase-82 Choi average basket

```python
opt = ql.BasketOption(
    ql.AverageBasketPayoff(
        ql.PlainVanillaPayoff(ql.OptionType.Put, 20.0),
        [1.0, -2.0, -1.0, 4.0],
    ),
    ql.EuropeanExercise(maturity),
)
opt.set_choi_pricing_engine(
    processes, rho, integration_lambda=7.0,
    max_nr_integration_steps=10000,
    calc_fwd_delta=True, control_variate=True,
)
print(opt.NPV())
```

Weighted-sum basket (weights may be negative). Choi 2018 closed-form /
quadrature engine. `rho` is a `Matrix`. Compat: `setChoiPricingEngine`.

## Phase-83 holder / writer extensible options

```python
holder = ql.HolderExtensibleOption(
    ql.OptionType.Call, 1.0, today + 270, 105.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(today + 180),
)
holder.set_pricing_engine(process)

writer = ql.WriterExtensibleOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
    ql.EuropeanExercise(today + 180),
    ql.PlainVanillaPayoff(ql.OptionType.Call, 82.0),
    ql.EuropeanExercise(today + 270),
)
writer.set_pricing_engine(process)
```

Haug closed forms. The holder may pay a premium to extend; the writer
extends automatically if the option is OTM at the first expiry. Compat:
`setPricingEngine`, `isExpired`.

## Phase-84 SingleFactor / Deng-Li-Zhou baskets

```python
opt.set_single_factor_pricing_engine([process])

opt.set_deng_li_zhou_pricing_engine(processes, rho)
print(opt.NPV())
```

`SingleFactorBsmBasketEngine` prices a weighted-sum basket driven by one
factor (1-asset case matches European Black–Scholes). `DengLiZhouBasketEngine`
is the Deng–Li–Zhou 2008 spread/basket closed form (`rho` is a `Matrix`).
Compat: `setSingleFactorPricingEngine`, `setDengLiZhouPricingEngine`.

## Phase-85 Bjerksund / Pearson / operator-splitting spreads

```python
opt = ql.BasketOption(
    ql.SpreadBasketPayoff(ql.PlainVanillaPayoff(ql.OptionType.Put, 5.0)),
    ql.EuropeanExercise(maturity),
)
opt.set_bjerksund_stensland_pricing_engine(p1, p2, rho=0.75)
opt.set_pearson_pricing_engine(p1, p2, rho=0.75)
opt.set_operator_splitting_pricing_engine(
    p1, p2, rho=0.0, order=ql.OperatorSplittingOrder.Second
)
print(opt.NPV())
```

Remaining two-asset spread engines on `BasketOption` + `SpreadBasketPayoff`
(Kirk is Phase 78). Processes are futures-style: pass `BlackScholesMertonProcess`
with `q = r`. `OperatorSplittingOrder` is `First` or `Second` (default Second).
Compat: `setBjerksundStenslandPricingEngine`, `setPearsonPricingEngine`,
`setOperatorSplittingPricingEngine`.

## Phase-86 Gaussian copula / 2-D PDE spreads

```python
opt.set_gaussian_copula_pricing_engine(p1, p2, rho=0.5)
opt.set_fd_2d_pricing_engine(
    p1, p2, rho=0.5, x_grid=50, y_grid=50, t_grid=15
)
print(opt.NPV())
```

`GaussianCopulaSpreadEngine` prices two-asset spreads with nested
Gauss-Hermite quadrature on a Gaussian copula. Both processes must share
the same risk-free `YieldTermStructure` handle. `Fd2dBlackScholesVanillaEngine`
is the 2-D PDE engine used to benchmark it. Processes are futures-style:
pass `BlackScholesMertonProcess` with `q = r`. Compat:
`setGaussianCopulaPricingEngine`, `setFd2dPricingEngine`.

## Phase-87 n-D PDE basket engine

```python
opt = ql.BasketOption(
    ql.AverageBasketPayoff(
        ql.PlainVanillaPayoff(ql.OptionType.Put, -30.0), [1.0, -2.0, -1.0]
    ),
    ql.AmericanExercise(today, maturity),
)
opt.set_fd_ndim_pricing_engine(
    processes, rho, t_grid=15, x_grids=[20, 20, 20]
)
print(opt.NPV())
```

`FdndimBlackScholesVanillaEngine` prices European or American baskets in
up to 4 dimensions. Pass `x_grid` for auto-scaled meshes, or `x_grids` for
per-factor sizes. Compat: `setFdNdimPricingEngine`.

## Phase-88 MC European / American baskets

```python
opt.set_mc_european_pricing_engine(
    [p1, p2], rho, steps_per_year=1, required_samples=10000, seed=42
)
am.set_mc_american_pricing_engine(
    [process],
    ql.Matrix(1, 1, [1.0]),
    time_steps=53,
    required_samples=10001,
    calibration_samples=2500,
    seed=0,
)
```

Monte Carlo engines build a `StochasticProcessArray` internally from BSM
processes and a correlation `Matrix`. European matches Haug/Kirk with
`steps_per_year=1`. American is Longstaff–Schwartz. Compat:
`setMCEuropeanPricingEngine`, `setMCAmericanPricingEngine`.

## Phase-89 AssetSwap

```python
asw = ql.AssetSwap(
    True, bond, bond.clean_price(), euribor6m, 0.0,
    floating_day_count=euribor6m.day_counter(),
    par_asset_swap=True,
)
asw.set_pricing_engine(curve)
print(asw.fair_clean_price(), asw.fair_spread(), asw.NPV())
```

Standalone wrapper (Swap/Instrument MI). Accepts `FixedRateBond`,
`ZeroCouponBond`, or `FloatingRateBond`. Default empty float schedule
builds from the bond settlement/maturity and the Ibor tenor. Engine is
`DiscountingSwapEngine`. Compat: `fairCleanPrice`, `fairSpread`,
`setPricingEngine`.

Fair prices are wrong with indexed coupons (QuantLib `\bug`); match the
suite's at-par coupon settings.

## Phase-90 ZeroCouponSwap

```python
zc = ql.ZeroCouponSwap(
    ql.SwapType.Receiver, 1e6, start, end, 1.2e6, euribor6m, calendar,
    ql.BusinessDayConvention.ModifiedFollowing, 1,
)
zc.set_pricing_engine(curve)
print(zc.NPV(), zc.fixed_leg_NPV(), zc.fair_fixed_payment())

zc_rate = ql.ZeroCouponSwap(
    ql.SwapType.Receiver, 1e6, start, end, 0.01, ql.Actual365Fixed(),
    euribor6m, calendar,
)
```

Standalone wrapper (Swap/Instrument MI). Two constructors: known fixed
cashflow, or compounded annual fixed rate. Engine is
`DiscountingSwapEngine`. Compat: `fairFixedPayment`, `fairFixedRate`,
`fixedLegNPV`, `setPricingEngine`.

## Phase-91 BondForward

```python
bond.set_pricing_engine(curve)
fwd = ql.BondForward(
    curve.reference_date(), delivery, ql.Position.Long, 0.0, 2,
    ql.ActualActual(ql.ActualActualConvention.ISDA), ql.TARGET(),
    ql.BusinessDayConvention.Following, bond, curve, curve,
)
print(fwd.clean_forward_price() / 0.76871)  # suite 207.47
```

Standalone wrapper (Forward/Instrument MI). The underlying
`FixedRateBond` is copied; attach `DiscountingBondEngine` on the bond
before constructing the forward. Discount / income curves are constructor
arguments (no separate engine). Compat: `cleanForwardPrice`,
`forwardValue`, `spotValue`.

## Phase-92 PerpetualFutures

```python
pf = ql.PerpetualFutures(
    ql.PerpetualFuturesPayoffType.Linear,
    ql.PerpetualFuturesFundingType.FundingWithPreviousSpot,
    ql.Period(3, ql.TimeUnit.Months),
)
pf.set_pricing_engine(dom, foreign, ql.make_quote_handle(10000.0),
                      [0.0], [0.01], [0.005])
print(pf.NPV())
```

Standalone wrapper (Instrument/LazyObject MI). Engine is
`DiscountingPerpetualFuturesEngine` (Linear / Inverse only). Compat:
`setPricingEngine`, plus `PerpetualFutures.Linear` / `.Inverse` nested
aliases. Recovers the AHJ 2024 closed form (rel 1e-6).

## Phase-93 MultipleResetsSwap

```python
swap = ql.make_multiple_resets_swap(
    ql.Period(2, ql.TimeUnit.Years), euribor3m, 2,
    fixed_rate=0.06, settlement_days=0, nominal=1e6,
)
print(swap.fair_rate(), swap.NPV())
par = ql.make_multiple_resets_swap(
    ql.Period(2, ql.TimeUnit.Years), euribor3m, 2,
    fixed_rate=swap.fair_rate(), settlement_days=0, nominal=1e6,
)
print(par.NPV())  # ~0
```

Standalone wrapper (FixedVsFloatingSwap/Instrument MI). Builder attaches
`DiscountingSwapEngine` from the Ibor forwarding curve. Omit `fixed_rate`
to lock the fair rate (NPV 0). Compat: `makeMultipleResetsSwap`,
`fairRate`, `fixedLegNPV`.

## Phase-94 EquityTotalReturnSwap

```python
eq = ql.EquityIndex("eqIndex", calendar, ql.USDCurrency(), interest, dividend, spot)
eq.add_fixing(ql.Date(5, ql.Month.January, 2023), 9010.0)
libor = ql.USDLibor(ql.Period(3, ql.TimeUnit.Months), interest)
trs = ql.EquityTotalReturnSwap(
    ql.SwapType.Receiver, 1e7, schedule, eq, libor,
    ql.Actual365Fixed(), 0.0, 1.0, calendar,
    ql.BusinessDayConvention.Following, 0,
)
trs.set_pricing_engine(interest)
print(trs.equity_leg_NPV(), trs.fair_margin(), trs.NPV())
```

Standalone wrapper (Swap/Instrument MI). `EquityIndex` is an Index
(Observable+Observer MI) standalone wrapper; `USDLibor` is an IborIndex
factory. Overnight (Sofr) overload dispatches on the interest-rate index.
Engine is `DiscountingSwapEngine`. Compat: `fairMargin`, `equityLegNPV`,
`setPricingEngine`. Recovers suite equity-leg NPV (tol 1e-8) and
fair-margin par rebuild (tol 1e-8).

## Phase-95 HimalayaOption

```python
today = ql.Date(15, ql.Month.May, 1998)
ql.set_evaluation_date(today)
dc = ql.Actual360()

def bsm(spot, q, r, vol):
    return ql.BlackScholesMertonProcess(
        ql.make_quote_handle(spot),
        ql.FlatForward(today, q, dc),
        ql.FlatForward(today, r, dc),
        ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc),
    )

fixings = [today + i * 90 for i in range(5)]
opt = ql.HimalayaOption(fixings, 101.0)
processes = [
    bsm(100.0, 0.01, 0.05, 0.30),
    bsm(110.0, 0.05, 0.05, 0.35),
    bsm(90.0, 0.04, 0.05, 0.25),
    bsm(105.0, 0.03, 0.05, 0.20),
]
rho = ql.Matrix(
    4, 4,
    [
        1.00, 0.50, 0.30, 0.10,
        0.50, 1.00, 0.20, 0.40,
        0.30, 0.20, 1.00, 0.60,
        0.10, 0.40, 0.60, 1.00,
    ],
)
opt.set_mc_pricing_engine(
    processes, rho, required_samples=1023, seed=86421
)
print(opt.NPV())  # 5.93632056
```

Standalone wrapper (MultiAssetOption/Instrument MI). Engine is
`MakeMCHimalayaEngine<PseudoRandom>` (time grid from fixing dates);
pass BSM processes plus a correlation `Matrix` as for other multi-asset
MC engines. Empty `fixing_dates` raises. Compat: `setMCPricingEngine`,
`errorEstimate`, `isExpired`. Recovers suite cached NPV 5.93632056
(tol 1e-8).

## Phase-96 PagodaOption

```python
today = ql.Date(15, ql.Month.May, 1998)
ql.set_evaluation_date(today)
fixings = [today + i * 90 for i in range(1, 5)]
opt = ql.PagodaOption(fixings, roof=0.20, fraction=0.62)
opt.set_mc_pricing_engine(
    processes, rho, required_samples=1023, seed=86421
)
print(opt.NPV())  # 0.01221094
```

Standalone wrapper (MultiAssetOption/Instrument MI). Engine is
`MakeMCPagodaEngine<PseudoRandom>` (time grid from fixing dates).
Compat: `setMCPricingEngine`, `errorEstimate`, `isExpired`. Recovers
suite cached NPV 0.01221094 (tol 1e-8).

## Phase-97 EverestOption

```python
today = ql.Date(15, ql.Month.May, 1998)
ql.set_evaluation_date(today)
opt = ql.EverestOption(1.0, 0.0, ql.EuropeanExercise(today + 360))
opt.set_mc_pricing_engine(
    processes, rho, steps_per_year=1, required_samples=1023, seed=86421
)
print(opt.NPV(), opt.yield_())  # 0.75784944, ...
```

Standalone wrapper (MultiAssetOption/Instrument MI). Engine is
`MakeMCEverestEngine<PseudoRandom>` (default 1 step/year). Method
`yield_` avoids the Python `yield` keyword; compat exposes `yield` via
setattr. Compat: `setMCPricingEngine`, `errorEstimate`, `isExpired`.
Recovers suite cached NPV 0.75784944 (tol 1e-8).

## Phase-98 FloatFloatSwap

```python
calendar = ql.TARGET()
today = calendar.adjust(ql.get_evaluation_date())
ql.set_evaluation_date(today)
settlement = calendar.advance(today, 2, ql.TimeUnit.Days)
curve = ql.FlatForward(settlement, 0.05, ql.Actual365Fixed())
index1, index2 = ql.Euribor3M(curve), ql.Euribor6M(curve)

swap = ql.make_float_float_swap(
    ql.SwapType.Payer, 100.0, index1, index2, curve, spread2=0.002
)
fair = swap.fair_spread1()
par = ql.make_float_float_swap(
    ql.SwapType.Payer, 100.0, index1, index2, curve, spread1=fair, spread2=0.002
)
assert abs(par.NPV()) < 1e-10
```

Standalone wrapper (Swap/Instrument MI). Engine is `DiscountingSwapEngine`
with `BlackIborCouponPricer` on both legs (attached by
`set_pricing_engine` / `make_float_float_swap`). Compat: `fairSpread1`,
`fairSpread2`, `legNPV`, `setPricingEngine`, `makeFloatFloatSwap`. Recovers
suite fair-spread NPV-zeroing and payer/receiver symmetry (tol 1e-10).

## Phase-99 OvernightIndexFuture

```python
today = ql.Date(26, ql.Month.October, 2018)
ql.set_evaluation_date(today)
# ... add SOFR fixings, build SofrFutureRateHelper list ...
curve = ql.PiecewiseLinearDiscountCurve(today, helpers, ql.Actual365Fixed())
sofr = ql.Sofr(curve)
conv = ql.SimpleQuote(0.0)
fut = ql.OvernightIndexFuture(
    sofr,
    ql.Date(20, ql.Month.March, 2019),
    ql.Date(19, ql.Month.June, 2019),
    ql.QuoteHandle(conv),
)
assert abs(fut.NPV() - 97.44) < 1e-9
conv.set_value(0.1)
assert abs(fut.NPV() - 87.44) < 1e-9  # 100*(1-(0.0256+0.1))
```

Self-priced Instrument (no external engine). Bootstrap helpers:
`SofrFutureRateHelper` + `PiecewiseLinearDiscountCurve`. Compat:
`isExpired`, `convexityAdjustment`, `valueDate`, `maturityDate`. Recovers
`SofrFuturesTests::testBootstrap` (97.44 / 87.44) and
`testBootstrapWithJuneteenth` (97.220), tol 1e-9.

## Phase-100 BMASwap

```python
calendar = ql.JointCalendar(
    ql.BMAIndex().fixing_calendar(),
    ql.USDLibor(ql.Period(3, ql.TimeUnit.Months)).fixing_calendar(),
)
today = calendar.adjust(ql.Date(15, ql.Month.January, 2020))
ql.set_evaluation_date(today)
# ... bootstrap BMASwapRateHelper list into PiecewiseLinearDiscountCurve ...
swap = ql.make_bma_swap(
    ql.SwapType.Payer, 100.0, ql.Period(5, ql.TimeUnit.Years),
    0.75, 0.0, libor, bma, libor_curve,
)
assert abs(swap.fair_libor_fraction() - 0.6881) < 1e-9
```

Standalone Swap/Instrument wrapper + `BMAIndex`, `BMASwapRateHelper`,
`JointCalendar`. Engine is `DiscountingSwapEngine` (via `set_pricing_engine`
/ `make_bma_swap`). Compat: `fairLiborFraction`, `liborLegNPV`,
`setPricingEngine`, `makeBMASwap`. Recovers piecewise BMA curve fair libor
fractions from `PiecewiseYieldCurve` BMA consistency (tol 1e-9).

## Phase-101 AmortizingFixedRateBond

```python
today = ql.get_evaluation_date()
freq = ql.Frequency.Monthly
schedule = ql.sinking_schedule(
    today, ql.Period(30, ql.TimeUnit.Years), freq, ql.NullCalendar()
)
notionals = ql.sinking_notionals(
    ql.Period(30, ql.TimeUnit.Years), freq, 0.05, 100.0
)
bond = ql.AmortizingFixedRateBond(
    0, notionals, schedule, [0.05],
    ql.ActualActual(ql.ActualActualConvention.ISMA),
)
amounts = bond.cashflow_amounts()
# coupon + principal ≈ Excel PMT(0.05/12, 360, -100) each period
assert abs(amounts[0] + amounts[1] - 0.536821623) < 1e-6
bond.set_pricing_engine(ql.FlatForward(today, 0.03, ql.Actual365Fixed()))
assert bond.NPV() > 0.0
```

Standalone Bond wrappers (`AmortizingFixedRateBond` /
`AmortizingFloatingRateBond`) + French amortization helpers. Engine is
`DiscountingBondEngine` (floating also attaches `BlackIborCouponPricer`).
Compat: `sinkingSchedule`, `sinkingNotionals`, `cashflowAmounts`,
`setPricingEngine`. Recovers `AmortizingBondTests::testAmortizingFixedRateBond`
pmt / coupon amounts (tol 1e-6).

## Phase-102 VanillaSwingOption

```python
today = ql.Date(15, ql.Month.January, 2020)
ql.set_evaluation_date(today)
dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
process = ql.BlackScholesMertonProcess(
    ql.make_quote_handle(30.0),
    ql.FlatForward(today, 0.02, dc),
    ql.FlatForward(today, 0.14, dc),
    ql.BlackConstantVol(today, ql.NullCalendar(), 0.4, dc),
)
dates = []
d = today + ql.Period(1, ql.TimeUnit.Months)
maturity = today + ql.Period(12, ql.TimeUnit.Months)
while d <= maturity:
    dates.append(d)
    d = d + ql.Period(1, ql.TimeUnit.Months)
swing = ql.SwingExercise(dates)
opt = ql.VanillaSwingOption(
    ql.VanillaForwardPayoff(ql.OptionType.Put, 30.0), swing, 0, 2
)
opt.set_fd_pricing_engine(process, t_grid=50, x_grid=200)
print(opt.NPV())
```

Standalone OneAssetOption wrapper + `SwingExercise` /
`VanillaForwardPayoff`. Engine is `FdSimpleBSSwingEngine`. Also adds
`VanillaOption(BermudanExercise)` for suite upper-bound checks. Compat:
`isExpired`, `setPricingEngine` → `set_fd_pricing_engine`. Recovers
`SwingOptionTest::testFdBSSwingOption` upper/lower bounds.

## Phase-103 VanillaStorageOption

```python
today = ql.Date(18, ql.Month.December, 2011)
ql.set_evaluation_date(today)
dc = ql.ActualActual(ql.ActualActualConvention.ISDA)
maturity = today + ql.Period(12, ql.TimeUnit.Months)
dates = [today + ql.Period(1, ql.TimeUnit.Days)]
while dates[-1] < maturity:
    dates.append(dates[-1] + ql.Period(1, ql.TimeUnit.Days))
process = ql.ExtendedOrnsteinUhlenbeckProcess(1.0, 0.5, 3.0, 3.0)
opt = ql.VanillaStorageOption(ql.BermudanExercise(dates), 50, 0, 1)
opt.set_fd_pricing_engine(
    process, ql.FlatForward(today, 0.1, dc), t_grid=1, x_grid=25
)
assert abs(opt.NPV() - 69.5755) < 5e-2
```

Standalone OneAssetOption wrapper + `ExtendedOrnsteinUhlenbeckProcess`
(constant `b`). Engine is `FdSimpleExtOUStorageEngine`. Compat:
`isExpired`, `setPricingEngine`. Recovers
`VPPOptionTest::testSimpleExtOUStorageEngine` cached NPV (tol 5e-2).

## Phase-104 Stock / CompositeInstrument

```python
stock = ql.Stock(ql.make_quote_handle(3.14))
assert stock.NPV() == 3.14

today = ql.get_evaluation_date()
opt = ql.EuropeanOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(today + 30),
)
opt.set_pricing_engine(process)
composite = ql.CompositeInstrument()
composite.add(opt)
ql.set_evaluation_date(today + 45)
assert composite.is_expired()
assert composite.NPV() == 0.0
```

Standalone Instrument wrappers. `Stock` NPV tracks its quote;
`CompositeInstrument` sums weighted leg NPVs, retaining shared
`Instrument` ownership (not value copies). Compat: `isExpired`.
Recovers `InstrumentTests::testCompositeWhenShiftingDates`.

## Phase-105 Gap / SuperFund / SuperShare payoffs

```python
today = ql.get_evaluation_date()
process = ql.BlackScholesMertonProcess(...)
opt = ql.EuropeanOption(
    ql.GapPayoff(ql.OptionType.Call, 50.0, 57.0),
    ql.EuropeanExercise(today + 180),
)
opt.set_pricing_engine(process)
```

Standalone binary payoffs (no Payoff MI hierarchy). `EuropeanOption`
accepts `GapPayoff`, `SuperFundPayoff`, and `SuperSharePayoff`; analytic
European pricing recovers `DigitalOptionTest::testGapEuropeanValues` for
`GapPayoff` (tol 1e-4). Compat: `optionType`, `secondStrike`, `cashPayoff`.

## Phase-106 ConstNotionalCrossCurrencyFixedVsFloatingSwap

```python
swap = ql.ConstNotionalCrossCurrencyFixedVsFloatingSwap(...)
swap.set_pricing_engine(
    ql.USDCurrency(), usd_curve, ql.TRYCurrency(), try_curve, fx_quote
)
assert swap.NPV() == pytest.approx(129777.91, abs=0.01)
```

Standalone swap wrapper with `DiscountingConstNotionalCrossCurrencySwapEngine`.
Also adds `DiscountCurve`, `TRYCurrency`, and `Turkey` calendar helpers.
Recovers `ConstNotionalCrossCurrencyFixedVsFloatingSwapTest` (tol 0.01).

## Phase-107 Ibor Collar

```python
collar = ql.Collar(schedule, index, cap_strike=0.05, floor_strike=0.03)
collar.set_pricing_engine(curve, volatility=0.20)
assert cap.NPV() - floor.NPV() == pytest.approx(collar.NPV(), abs=1e-10)
```

Standalone `Collar` wrapper (CapFloor MI avoided). Compat: `setPricingEngine`,
`impliedVolatility`. Recovers `CapFloorTest::testConsistency` (tol 1e-10).

## Phase-108 Ibor Cap / Floor

```python
cap = ql.Cap(schedule, index, strike=0.07)
cap.set_pricing_engine(curve, volatility=0.20)
```

Standalone `Cap` / `Floor` wrappers matching SWIG class names. NPV agrees
with `CapFloor(CapFloorType.Cap|Floor, …)`. Compat: `setPricingEngine`,
`impliedVolatility`. Recovers `CapFloorTest::testImpliedVolatility` (tol 1e-8).

## Phase-109 ConstNotionalCrossCurrencyBasisSwap

```python
swap = ql.ConstNotionalCrossCurrencyBasisSwap(
    gbp_nominal, ql.GBPCurrency(), schedule, gbp_index, spread, 1.0,
    usd_nominal, ql.USDCurrency(), schedule, usd_index, 0.0, 1.0,
)
swap.set_pricing_engine(
    ql.USDCurrency(), usd_discount, ql.GBPCurrency(), gbp_discount, fx_quote
)
assert swap.NPV() == pytest.approx(0.0, abs=0.01)
assert swap.leg_bps(0) == pytest.approx(-4670.17, abs=0.01)
```

Cross-currency floating-vs-floating basis swap. Reuses
`DiscountingConstNotionalCrossCurrencySwapEngine` from Phase 106.
Optional OIS kwargs support overnight-index legs (Sonia/Sofr). Compat:
`setPricingEngine`, `legNPV`, `legBPS`, `fairPaySpread`, `fairRecSpread`.
Recovers `ConstNotionalCrossCurrencyBasisSwapTest::testBasisXCCYSwapPricing`.
Also recovers `testBasisONXCCYSwapPricing` (Sonia/Sofr overnight legs).

## Phase-110 VarianceOption

```python
process = ql.HestonProcess(
    ql.FlatForward(today, 0.0, ql.Actual360()),
    ql.YieldTermStructureHandle(),
    ql.make_quote_handle(1.0),
    2.0, 2.0, 0.01, 0.1, -0.5,
)
opt = ql.VarianceOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 0.05),
    1.0, today, today + 540,
)
opt.set_integral_heston_pricing_engine(process)
assert opt.NPV() == pytest.approx(0.9104619, abs=1e-7)
```

Standalone variance option on realized variance. Compat: `setIntegralHestonPricingEngine`,
`isExpired`, `startDate`, `maturityDate`. Recovers `VarianceOptionTests::testIntegralHeston`.

## Phase-111 ConstNotionalCrossCurrencySwap

```python
swap = ql.make_fix_fix_xccy_swap(125_000_000.0, 1.22)
swap.set_pricing_engine(
    ql.USDCurrency(), usd_discount, ql.CHFCurrency(), chf_discount, fx_quote
)
assert swap.NPV() == pytest.approx(-21108172.67, abs=0.01)
```

Generic two-leg XCCY swap wrapper (factory builds fix/fix legs with notional
exchange). Reuses `DiscountingConstNotionalCrossCurrencySwapEngine` from Phase 106.
Also adds `CHFCurrency` and `Switzerland`. Compat: `setPricingEngine`, `legNPV`,
`legBPS`, `makeFixFixXCCYSwap`. Recovers `testFixFixXCCYSwapPricing`.

## Phase-112 float/float XCCY factory

```python
swap = ql.make_float_float_xccy_swap(
    125_000_000.0, 1.35, usd_projection, gbp_projection
)
swap.set_pricing_engine(
    ql.USDCurrency(), usd_discount, ql.GBPCurrency(), gbp_discount, fx_quote
)
assert swap.NPV() == pytest.approx(0.0, abs=0.01)
```

Adds `make_float_float_xccy_swap` for USD/GBP Libor legs with notional exchange.
Compat: `makeFloatFloatXCCYSwap`. Recovers `testFloatFloatXCCYSwapPricing`.

## Phase-113 fix/float XCCY factory

```python
swap = ql.make_fix_float_xccy_swap(10_000_000.0, 6.4304, usd_projection)
swap.set_pricing_engine(
    ql.USDCurrency(), usd_discount, ql.TRYCurrency(), try_discount, fx_quote
)
assert swap.NPV() == pytest.approx(218961.99, abs=0.01)  # or 218981.99
```

Adds `make_fix_float_xccy_swap` for TRY fixed vs USD 3M Libor float legs.
Compat: `makeFixFloatXCCYSwap`. Recovers `testFloatFixXCCYSwapPricing`.

## Phase-114 YoY inflation Cap / Floor / Collar

```python
cap = ql.YoYInflationCap(sched, yoy, lag, interp, strike, calendar, dc)
cap.set_pricing_engine(yoy, vol, nominal, model="black")
assert cap.NPV() == pytest.approx(wrapper.NPV(), abs=1e-12)
```

Standalone wrappers mirror SWIG class names; NPV matches `YoYInflationCapFloor(type, …)`.
Compat: `YoYInflationCap`, `YoYInflationFloor`, `YoYInflationCollar`.
Recovers `InflationCapFloorTests::testConsistency`.

## Phase-115 CmsRateBond

```python
bond = ql.CmsRateBond(3, 100.0, schedule, swap_index, dc, gearings=[0.84])
bond.set_pricing_engine(curve)
bond.set_cms_coupon_pricer(cms_pricer)
asw = ql.AssetSwap(True, bond, bond.clean_price(), ibor, 0.0, floating_day_count=ibor.day_counter())
```

Adds `CmsRateBond` with CMS coupon pricer attachment and `AssetSwap(CmsRateBond, …)`.
Compat: `CmsRateBond`, `setCmsCouponPricer`. Recovers CMS leg of `AssetSwapTests::testImpliedValue`.

## Phase-116 NonstandardSwaption

```python
nonstd = ql.NonstandardSwaption(std_swaption)
nonstd.set_gaussian1d_pricing_engine(gsr)
assert nonstd.NPV() == pytest.approx(hw_jam.NPV(), abs=5e-5)
```

Wraps a standard `Swaption` as `NonstandardSwaption`; prices with
`Gaussian1dNonstandardSwaptionEngine`. Compat: `NonstandardSwaption`,
`setGaussian1dPricingEngine`. Recovers `GsrTests::testGsrModel` NPV check.

## Phase-117 NonstandardSwap

```python
nonstd_swap = ql.NonstandardSwap(vanilla_swap)
nonstd_swap.set_pricing_engine(curve)
assert nonstd_swap.NPV() == pytest.approx(vanilla_swap.NPV(), abs=1e-12)

nonstd_swaption = ql.NonstandardSwaption(nonstd_swap, exercise)
```

Vanilla swap with per-period nominals and fixed rates; wraps from
`VanillaSwap` or explicit vectors. `NonstandardSwaption` also accepts
`(NonstandardSwap, exercise)`. Compat: `NonstandardSwap`, `setPricingEngine`,
inspector camelCase aliases. Discounting NPV parity with source vanilla swap.

## Phase-118 VarianceGamma

```python
process = ql.VarianceGammaProcess(spot, q_ts, r_ts, sigma=0.20, nu=0.05, theta=-0.50)
opt = ql.EuropeanOption(ql.PlainVanillaPayoff(ql.OptionType.Call, 6000.0), exercise)
opt.set_variance_gamma_pricing_engine(process)
assert opt.NPV() == pytest.approx(687.2032, abs=0.01)
```

Variance-gamma process and analytic integral engine for European options.
Compat: `setVarianceGammaPricingEngine`. Recovers
`VarianceGammaTests::testVarianceGamma` goldens (tol 0.01).

## Phase-119 FFTVarianceGamma

```python
engine = ql.FFTVarianceGammaEngine(process)
engine.precalculate(options)
for opt in options:
    opt.set_fft_variance_gamma_pricing_engine(engine)
assert opt.NPV() == pytest.approx(687.2032, abs=0.01)
```

FFT batch engine for variance-gamma Europeans; single-option uncached path
also supported. Compat: `setFftVarianceGammaPricingEngine`. Recovers
`VarianceGammaTests::testVarianceGamma` FFT values (tol 0.01).

## Phase-120 Asian continuous geometric Heston

```python
asian = ql.ContinuousAveragingAsianOption(
    ql.AverageType.Geometric, payoff, exercise
)
asian.set_heston_pricing_engine(heston_process)
assert asian.NPV() == pytest.approx(3.4478, abs=1e-2)
```

Attaches `AnalyticContinuousGeometricAveragePriceAsianHestonEngine`.
Compat: `setHestonPricingEngine`. Recovers Kim–Wee Table 1/4 cases from
`AsianOptionTests::testAnalyticContinuousGeometricAveragePriceHeston`.

## Phase-121 Asian discrete geometric Heston

```python
asian = ql.DiscreteAveragingAsianOption(
    ql.AverageType.Geometric, 1.0, 0, fixing_dates, payoff, exercise
)
asian.set_heston_pricing_engine(heston_process)
assert asian.NPV() == pytest.approx(5.2132, abs=2e-2)
```

Attaches `AnalyticDiscreteGeometricAveragePriceAsianHestonEngine`.
Compat: `setHestonPricingEngine`. Recovers Tables 1–3 from
`AsianOptionTests::testAnalyticDiscreteGeometricAveragePriceHeston`.

## Phase-122 Asian Vecer continuous arithmetic

```python
asian = ql.ContinuousAveragingAsianOption(
    ql.AverageType.Arithmetic, payoff, exercise
)
asian.set_vecer_pricing_engine(
    process, ql.QuoteHandle(ql.SimpleQuote(0.0)), today, 200, 200
)
assert asian.NPV() == pytest.approx(0.246416, abs=1e-5)
```

Attaches `ContinuousArithmeticAsianVecerEngine`. Compat: `setVecerPricingEngine`
(compat-only). Recovers `AsianOptionTests::testVecerEngine`.

## Phase-123 Asian Levy continuous arithmetic

```python
asian = ql.ContinuousAveragingAsianOption(
    ql.AverageType.Arithmetic, start_date, payoff, exercise
)
asian.set_levy_pricing_engine(process, ql.QuoteHandle(ql.SimpleQuote(100.0)))
assert asian.NPV() == pytest.approx(7.0544, abs=1e-4)
```

Attaches `ContinuousArithmeticAsianLevyEngine` for (seasoned) continuous
arithmetic Asians. Compat: `setLevyPricingEngine` (compat-only). Recovers
Haug cases from `AsianOptionTests::testLevyEngine`.

## Phase-124 forward Heston analytic

```python
forward = ql.ForwardVanillaOption(
    1.0, today, ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0), exercise
)
forward.set_heston_forward_pricing_engine(heston_process, integration_order=96)
assert forward.NPV() == pytest.approx(vanilla_heston_npv, rel=5e-4)
```

Attaches `AnalyticHestonForwardEuropeanEngine` for forward-start vanillas under
Heston. Compat: `setHestonForwardPricingEngine` (compat-only). Recovers
`ForwardOptionTests::testHestonMCPrices` T=0 analytic cross-check.

## Phase-125 SuoWang double barrier

```python
opt = ql.DoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut, 50.0, 150.0, 0.0, payoff, exercise
)
opt.set_suo_wang_pricing_engine(process, series=5)
assert opt.NPV() == pytest.approx(4.3515, abs=1e-4)
```

Attaches `SuoWangDoubleBarrierEngine` (Wulin Suo / Yong Wang). Compat:
`setSuoWangPricingEngine` (compat-only). Recovers Haug cases from
`DoubleBarrierOptionTests::testEuropeanHaugValues`.

## Phase-126 FFT vanilla (Black–Scholes)

```python
opt.set_fft_vanilla_pricing_engine(process)
# or batch:
engine = ql.FFTVanillaEngine(process)
engine.precalculate(options)
for opt in options:
    opt.set_fft_vanilla_pricing_engine(engine)
```

Attaches `FFTVanillaEngine` (Carr–Madan FFT under BS). Compat:
`setFftVanillaPricingEngine` (compat-only). Recovers
`EuropeanOptionTests::testFFTEngines` consistency vs analytic (rel tol 1%).

## Phase-127 perturbative barrier

```python
opt = ql.BarrierOption(
    ql.BarrierType.UpOut, 101.0, 0.0, payoff, exercise
)
opt.set_perturbative_pricing_engine(process, order=0, zero_gamma=False)
assert opt.NPV() == pytest.approx(0.897365, abs=1e-6)
```

Attaches `PerturbativeBarrierOptionEngine` (Recchioni). Compat:
`setPerturbativePricingEngine` (compat-only). Recovers
`BarrierOptionTests::testPerturbative` (orders 0 and 1).

## Phase-128 Vanna/Volga barrier

```python
atm = ql.DeltaVolQuote(
    ql.make_quote_handle(0.08925), ql.DeltaVolDeltaType.Fwd, 1.0,
    ql.DeltaVolAtmType.AtmDeltaNeutral,
)
put25 = ql.DeltaVolQuote(-0.25, ql.make_quote_handle(0.10087), 1.0, ql.DeltaVolDeltaType.Fwd)
call25 = ql.DeltaVolQuote(0.25, ql.make_quote_handle(0.08463), 1.0, ql.DeltaVolDeltaType.Fwd)
opt.set_vanna_volga_pricing_engine(
    atm, put25, call25, spot, domestic_ts, foreign_ts,
    adapt_van_delta=True, bs_price_with_smile=bs_vanilla,
)
```

Attaches `VannaVolgaBarrierEngine`. Compat: `setVannaVolgaPricingEngine`
(compat-only). Recovers cases from
`BarrierOptionTests::testVannaVolgaSimpleBarrierValues`.

## Phase-129 Vanna/Volga double barrier

```python
opt = ql.DoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut, 1.1, 1.5, 0.0, payoff, exercise
)
opt.set_vanna_volga_pricing_engine(
    atm, put25, call25, spot, domestic_ts, foreign_ts,
    adapt_van_delta=True, bs_price_with_smile=bs_vanilla, series=5,
)
```

Attaches `VannaVolgaDoubleBarrierEngine<SuoWangDoubleBarrierEngine>`. Compat:
`setVannaVolgaPricingEngine` (compat-only). Recovers KO goldens (and KI as
vanilla − KO) from `DoubleBarrierOptionTests::testVannaVolgaDoubleBarrierValues`.

## Phase-130 digital American

```python
opt = ql.VanillaOption(
    ql.CashOrNothingPayoff(ql.OptionType.Put, 100.0, 15.0),
    ql.AmericanExercise(today, today + 180),
)
opt.set_digital_american_pricing_engine(process)
assert opt.NPV() == pytest.approx(9.7264, abs=1e-4)
```

Attaches `AnalyticDigitalAmericanEngine` for American cash/asset digital
payoffs. Compat: `setDigitalAmericanPricingEngine` (compat-only). Recovers
Haug at-hit cases from `DigitalOptionTests`.

## Phase-131 digital American KO

```python
opt = ql.VanillaOption(
    ql.CashOrNothingPayoff(ql.OptionType.Put, 100.0, 15.0),
    ql.AmericanExercise(today, today + 180, payoff_at_expiry=True),
)
opt.set_digital_american_ko_pricing_engine(process)
assert opt.NPV() == pytest.approx(4.9081, abs=1e-4)
```

Attaches `AnalyticDigitalAmericanKOEngine` for knock-out digital Americans
(typically with `payoff_at_expiry=True`). Compat:
`setDigitalAmericanKoPricingEngine` (compat-only). Recovers at-expiry KO
Haug cases from `DigitalOptionTests`.

## Phase-132 binomial barrier

```python
opt = ql.BarrierOption(
    ql.BarrierType.DownOut,
    95.0,
    3.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
    ql.EuropeanExercise(today + 180),
)
opt.set_binomial_pricing_engine(process, time_steps=400)
assert opt.NPV() == pytest.approx(9.0246, abs=1.1e-2)
```

Attaches `BinomialBarrierEngine<CoxRossRubinstein, DiscretizedBarrierOption>`
(Boyle–Lau barrier adjustment when `max_time_steps==0`). Also adds
`BarrierOption(..., PlainVanillaPayoff, AmericanExercise)`. Compat:
`setBinomialPricingEngine` (compat-only). Recovers Haug cases from
`BarrierOptionTests::testHaugValues`.

## Phase-133 binomial double barrier

```python
opt = ql.DoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut,
    50.0,
    150.0,
    0.0,
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(today + 90),
)
opt.set_binomial_pricing_engine(process, time_steps=300)
assert opt.NPV() == pytest.approx(4.3515, abs=0.28)
```

Attaches `BinomialDoubleBarrierEngine<CoxRossRubinstein,
DiscretizedDoubleBarrierOption>`. Compat: `setBinomialPricingEngine`
(compat-only). Recovers Haug cases from
`DoubleBarrierOptionTests::testEuropeanHaugValues`.

## Phase-134 Bjerksund–Stensland American

```python
opt = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 40.0),
    ql.AmericanExercise(today, today + 270),
)
opt.set_bjerksund_stensland_pricing_engine(process)
assert opt.NPV() == pytest.approx(5.2704, abs=5e-5)
```

Attaches `BjerksundStenslandApproximationEngine`. Compat:
`setBjerksundStenslandPricingEngine` (compat-only). Recovers Haug cases
from `AmericanOptionTests::testBjerksundStenslandValues`.

## Phase-135 Merton 76 jump diffusion

```python
j_vol = 0.25 * math.sqrt(0.25 / 1.0)
diff_vol = 0.25 * math.sqrt(1.0 - 0.25)
mean_log = math.log(1.0) - 0.5 * j_vol * j_vol
process = ql.Merton76Process(
    ql.make_quote_handle(100.0),
    ql.FlatForward(today, 0.0, dc),
    ql.FlatForward(today, 0.08, dc),
    ql.BlackConstantVol(today, ql.NullCalendar(), diff_vol, dc),
    ql.make_quote_handle(1.0),
    ql.make_quote_handle(mean_log),
    ql.make_quote_handle(j_vol),
)
opt.set_jump_diffusion_pricing_engine(process)
assert opt.NPV() == pytest.approx(20.67, abs=1e-2)
```

Adds `Merton76Process` and `JumpDiffusionEngine` (via
`set_jump_diffusion_pricing_engine`). Compat:
`setJumpDiffusionPricingEngine` (compat-only). Recovers Haug Merton cases
from `JumpDiffusionTests::testMerton76`.

## Phase-136 Analytic PDF Heston

```python
opt = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pdf_heston_pricing_engine(model, gauss_lobatto_eps=1e-6)
ref = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
ref.set_heston_pricing_engine(model, integration_order=178)
assert opt.NPV() == pytest.approx(ref.NPV(), abs=3e-6)
```

Attaches `AnalyticPDFHestonEngine` (Dragulescu–Yakovenko). Also adds
European cash-or-nothing `VanillaOption` ctor for digital PDF pricing.
Compat: `setPdfHestonPricingEngine` (compat-only). Matches
`HestonModelTests::testAnalyticPDFHestonEngine`.

## Phase-137 Analytic CEV

```python
opt = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 2.3),
    ql.EuropeanExercise(today + ql.Period(12, ql.TimeUnit.Months)),
)
opt.set_cev_pricing_engine(2.1, 0.75, 0.45, ql.FlatForward(today, 0.15, dc))
assert opt.NPV() > 0.0
```

Attaches `AnalyticCEVEngine` (`df = α f^β dW`). Compat: `setCevPricingEngine`
(compat-only). Recovers the analytic CEV setup from `FdCEVTests`
(finite-difference delta consistency across β).

## Phase-138 FD CEV

```python
opt.set_fd_cev_pricing_engine(
    2.1, 0.75, 0.45, discount, t_grid=100, x_grid=1000, damping_steps=1, eps=1e-6
)
assert opt.NPV() == pytest.approx(analytic_npv, abs=0.01)
```

Attaches `FdCEVVanillaEngine`. Compat: `setFdCevPricingEngine` (compat-only).
Matches analytic CEV NPV/delta from `FdCEVTests` (tol 0.01).

## Phase-139 Choi arithmetic Asian

```python
opt = ql.DiscreteAveragingAsianOption(
    ql.AverageType.Arithmetic, 0.0, 0, fixing_dates, payoff, exercise
)
opt.set_choi_pricing_engine(process, integration_lambda=10.0, max_nr_integration_steps=8192)
assert opt.NPV() == pytest.approx(1.3942835683, abs=3e-2)
```

Attaches `ChoiAsianEngine` (Choi 2018 basket replication). Compat:
`setChoiPricingEngine` (compat-only). Recovers Levy cases from
`AsianOptionTests::testMCDiscreteArithmeticAveragePrice` (tol 3e-2).

## Phase-140 Bachelier Cap/Floor

```python
cap.set_bachelier_pricing_engine(curve, 0.01, ql.Actual365Fixed())
price = cap.NPV()
impl = cap.implied_volatility(
    price, curve, guess=0.005, accuracy=1e-8, vol_type=ql.VolatilityType.Normal
)
assert impl == pytest.approx(0.01, abs=1e-8)
```

Attaches `BachelierCapFloorEngine` (normal vol). Compat:
`setBachelierPricingEngine` (compat-only). Also on Cap / Floor / Collar.

## Phase-141 Bachelier Swaption

```python
swaption.set_bachelier_pricing_engine(curve, 0.01)
price = swaption.NPV()
impl = swaption.implied_volatility(
    price, curve, guess=0.005, accuracy=1e-8, vol_type=ql.VolatilityType.Normal
)
assert impl == pytest.approx(0.01, abs=1e-8)
```

Attaches `BachelierSwaptionEngine` (normal vol). Compat:
`setBachelierPricingEngine` (compat-only).

## Phase-142 FD Black–Scholes Asian

```python
opt.set_fd_pricing_engine(process, t_grid=100, x_grid=100, a_grid=100)
assert opt.NPV() == pytest.approx(1.3942835683, abs=2e-2)
```

Attaches `FdBlackScholesAsianEngine` (arithmetic average-price). Compat:
`setFdPricingEngine` (compat-only). Recovers Levy cases from
`AsianOptionTests::testMCDiscreteArithmeticAveragePrice` (tol 2e-2).

## Phase-143 Analytic performance engine

```python
opt.set_performance_pricing_engine(process)
assert opt.NPV() > 0.0
```

Attaches `AnalyticPerformanceEngine` on `CliquetOption`. Compat:
`setPerformancePricingEngine` (compat-only). Recovers FD-delta consistency
from `CliquetOptionTests::testPerformanceGreeks`.

## Phase-144 BSM + Hull–White

```python
opt.set_bsm_hull_white_pricing_engine(corr, process, hull_white)
impl = opt.implied_volatility(opt.NPV(), bs_process_at_expected_vol)
assert impl == pytest.approx(0.256402830, abs=1e-8)  # corr=0
```

Attaches `AnalyticBSMHullWhiteEngine`. Compat: `setBsmHullWhitePricingEngine`
(compat-only). Recovers `HybridHestonHullWhiteProcessTests::testBsmHullWhiteEngine`.

## Phase-145 Heston + Hull–White

```python
opt.set_heston_hull_white_pricing_engine(heston_model, hull_white, integration_order=128)
assert opt.NPV() == pytest.approx(bsm_hw_npv, abs=1e-5)
```

Attaches `AnalyticHestonHullWhiteEngine`. Compat:
`setHestonHullWhitePricingEngine` (compat-only). Matches BSM–HW when Heston
σ→0 (`testCompareBsmHWandHestonHW`).

## Phase-146 H1–HW approximation

```python
opt.set_h1_hw_pricing_engine(
    heston_model, hull_white, equity_short_rate_correlation=0.6, integration_order=144
)
impl = opt.implied_volatility(opt.NPV(), bs_process)
```

Attaches `AnalyticH1HWEngine` (Grzelak–Oosterlee H1–HW). Compat:
`setH1HWPricingEngine` (compat-only). Recovers
`HybridHestonHullWhiteProcessTests::testH1HWPricingEngine`.

## Phase-147 FD shout options

```python
opt = ql.VanillaOption(payoff, ql.AmericanExercise(maturity))
opt.set_fd_shout_pricing_engine(process, t_grid=400, x_grid=200)
assert opt.NPV() == pytest.approx(expected, abs=2e-2)
```

Attaches `FdBlackScholesShoutEngine`. Compat: `setFdShoutPricingEngine`
(compat-only). Recovers `AmericanOptionTests::testFDShoutNPV`.

## Phase-148 GJR-GARCH analytic engine

```python
process = ql.GJRGARCHProcess(r_ts, q_ts, spot, v0, omega, alpha, beta, gamma, lam, 365.0)
model = ql.GJRGARCHModel(process)
opt.set_gjr_garch_pricing_engine(model)
assert opt.NPV() == pytest.approx(expected, abs=0.15)
```

Attaches `AnalyticGJRGARCHEngine`. Compat: `setGjrGarchPricingEngine`
(compat-only). Recovers `GJRGARCHModelTests::testEngines`.

## Phase-149 rough Heston analytic engine

```python
model = ql.RoughHestonModel(r_ts, q_ts, spot, v0, kappa, theta, sigma, rho, hurst)
opt.set_rough_heston_pricing_engine(model, integration_order=128, time_steps=512)
assert opt.NPV() == pytest.approx(expected, abs=5e-4)
```

Attaches `AnalyticRoughHestonEngine`. Compat: `setRoughHestonPricingEngine`
(compat-only). Recovers `RoughHestonModelTests::testKnownReferenceValues`.

## Phase-150 piecewise time-dependent Heston

```python
ptd = ql.PiecewiseTimeDependentHestonModel(
    r_ts, q_ts, spot, v0, theta, kappa, sigma, rho, grid_end=20.0, grid_steps=2
)
opt.set_ptd_heston_pricing_engine(ptd, integration_order=192)
assert opt.NPV() == pytest.approx(heston_npv, abs=1e-7)
```

Attaches `AnalyticPTDHestonEngine`. Compat: `setPtdHestonPricingEngine`
(compat-only). Matches `HestonModelTests::testAnalyticPiecewiseTimeDependent`.

## Phase-151 FD CIR + equity

```python
cir = ql.CoxIngersollRossProcess(new_speed, cir_sigma, initial_rate, new_level)
opt.set_fd_cir_pricing_engine(cir, bsm, equity_rate_correlation=rho)
assert opt.NPV() == pytest.approx(4.275, abs=3e-4)
```

Attaches `FdCIRVanillaEngine`. Compat: `setFdCirPricingEngine` (compat-only).
Recovers `FdCIRTests::testFdmCIRConvergence`.

## Phase-152 FD Heston + Hull–White

```python
heston = ql.HestonModel(heston_process)
hw = ql.HullWhiteProcess(r_ts, 0.00883, 0.01)
opt.set_fd_heston_hull_white_pricing_engine(
    heston, hw, equity_short_rate_correlation=corr,
    t_grid=50, x_grid=200, v_grid=10, r_grid=15,
)
# Compare to AnalyticBSMHullWhiteEngine when Heston vol → 0 (BSM limit).
```

Attaches `FdHestonHullWhiteVanillaEngine`. Compat:
`setFdHestonHullWhitePricingEngine` (compat-only). Recovers
`HybridHestonHullWhiteProcessTests::testFdmHestonHullWhiteEngine`.

## Phase-153 MC Heston + Hull–White

```python
joint = ql.HybridHestonHullWhiteProcess(heston, hw_fwd, corr)
opt.set_mc_heston_hull_white_pricing_engine(
    joint,
    time_steps=1,
    required_tolerance=0.05,
    seed=42,
    antithetic=True,
    control_variate=True,
)
# Compare to AnalyticBSMHullWhiteEngine (testMcVanillaPricing).
```

Attaches `MCHestonHullWhiteEngine`. Compat:
`setMcHestonHullWhitePricingEngine` (compat-only). Recovers
`HybridHestonHullWhiteProcessTests::testMcVanillaPricing`.

## Phase-154 GSR Jamshidian swaption

```python
gsr = ql.Gsr(yts, [], [vol], reversion, T=50.0)
swaption.set_gaussian1d_jamshidian_pricing_engine(gsr)
# Compare to HullWhite JamshidianSwaptionEngine (GsrTests::testGsrModel).
```

Attaches `Gaussian1dJamshidianSwaptionEngine`. Compat:
`setGaussian1dJamshidianPricingEngine` (compat-only). Recovers
`GsrTests::testGsrModel` Jamshidian NPV check (tol 5e-5).

## Phase-155 GSR / affine cap–floor

```python
gsr = ql.Gsr(yts, [], [vol], reversion, T=50.0)
hw = ql.HullWhite(yts, reversion, vol)
cap.set_gaussian1d_pricing_engine(gsr, discount_curve=yts)
cap.set_analytic_cap_floor_pricing_engine(hw, discount_curve=yts)
```

Attaches `Gaussian1dCapFloorEngine` and `AnalyticCapFloorEngine`. Compat:
`setGaussian1dPricingEngine`, `setAnalyticCapFloorPricingEngine`. GSR vs Hull–White
analytic on constant parameters (reference golden).

## Phase-156 tree cap–floor

```python
hw = ql.HullWhite(yts, reversion, vol)
cap.set_tree_pricing_engine(hw, time_steps=200, discount_curve=yts)
# Compare to AnalyticCapFloorEngine on the same Hull–White model.
```

Attaches `TreeCapFloorEngine`. Compat: `setTreePricingEngine`. Lattice NPV
matches Hull–White analytic for a 5Y ATM cap (tol 0.05).

## Phase-157 MC Hull–White cap–floor

```python
hw = ql.HullWhite(yts, reversion, vol)
cap.set_mc_hull_white_pricing_engine(
    hw, required_tolerance=0.05, seed=42, antithetic=True
)
# Compare to AnalyticCapFloorEngine (within 3 * error_estimate).
```

Attaches `MCHullWhiteCapFloorEngine`. Compat: `setMcHullWhitePricingEngine`.

## Phase-158 G2 swaption engines

```python
g2 = ql.G2(yts, a=0.1, sigma=0.01, b=0.2, eta=0.013, rho=-0.5)
swaption.set_fd_g2_pricing_engine(g2, t_grid=50, x_grid=75, y_grid=75, inv_eps=1e-3)
swaption.set_g2_tree_pricing_engine(g2, time_steps=50)
# European: swaption.set_g2_pricing_engine(g2, range=7.0, intervals=64)
```

Attaches `G2SwaptionEngine`, `FdG2SwaptionEngine`, and G2 `TreeSwaptionEngine`.
Compat: `setG2PricingEngine`, `setFdG2PricingEngine`, `setG2TreePricingEngine`.

## Phase-159 MC pure Heston (hybrid process)

```python
joint = ql.HybridHestonHullWhiteProcess(
    heston, hw_fwd, corr, ql.HybridHestonHullWhiteDiscretization.Euler
)
opt.set_mc_heston_hull_white_pricing_engine(
    joint,
    time_steps=2,
    required_tolerance=0.001,
    seed=42,
    antithetic=True,
    control_variate=True,
)
# Compare to AnalyticHestonEngine when HW vol is ~0 (pure Heston limit).
```

Recovers `HybridHestonHullWhiteProcessTests::testMcPureHestonPricing`.

## Phase-160 Libor forward model cap

```python
process = ql.LiborForwardModelProcess(size, index)
vols = ql.lm_fixed_volatilities_from_caplet_curve(process, caplet_vol)
model = ql.LiborForwardModel(
    process,
    ql.LmFixedVolatilityModel(vols, process.fixing_times()),
    ql.LmExponentialCorrelationModel(size, 0.3),
)
cap = ql.make_lfm_cap(process, strike=0.04)
cap.set_libor_forward_pricing_engine(model, discount_curve=yts)
```

Attaches `AnalyticCapFloorEngine` on `LiborForwardModel`. Compat:
`setLiborForwardPricingEngine`.

## Phase-161 LFM swaption engine

```python
vola = ql.LmLinearExponentialVolatilityModel(
    process.fixing_times(), 0.291, 1.483, 0.116, 1e-5
)
process.set_covar_param(ql.LfmCovarianceProxy(vola, corr))
model = ql.LiborForwardModel(process, vola, corr)
swaption.set_lfm_pricing_engine(model, discount_curve=yts)
```

Recovers `LiborMarketModelTests::testSwaptionPricing`. Compat: `setLfmPricingEngine`.

## Phase-162 LMM calibration

```python
vola = ql.LmExtLinearExponentialVolModel(process.fixing_times(), 0.5, 0.6, 0.1, 0.1)
corr = ql.LmLinearExponentialCorrelationModel(size, 0.5, 0.8)
model = ql.LiborForwardModel(process, vola, corr)

cap_helper = ql.CapHelper(
    maturity, vol, index, ql.Frequency.Annual, index.day_counter(),
    True, yts, ql.CalibrationErrorType.ImpliedVolError,
)
cap_helper.set_lfm_pricing_engine(model, discount_curve=yts)

swaption_helper = ql.SwaptionHelper(
    maturity, length, vol, index, index.tenor(),
    day_counter, index.day_counter(), yts,
    ql.CalibrationErrorType.ImpliedVolError,
)
swaption_helper.set_lfm_pricing_engine(model, discount_curve=yts)

model.calibrate(helpers, ql.LevenbergMarquardt(1e-6, 1e-6, 1e-6),
                ql.EndCriteria(2000, 100, 1e-6, 1e-6, 1e-6))
```

Recovers `LiborMarketModelTests::testCalibration` (RMSE < 8e-3). Compat:
`setLfmPricingEngine` on helpers.

## Phase-163 LMM covariance introspection

```python
corr = ql.LmExponentialCorrelationModel(size, 0.1)
corr.correlation(0.0)
corr.pseudo_sqrt(0.0)

vola = ql.LmLinearExponentialVolatilityModel(fixing_times, a, b, c, d)
proxy = ql.LfmCovarianceProxy(vola, corr)
proxy.covariance(t)
proxy.diffusion(t)
vola.volatility(t)
```

Recovers `LiborMarketModelTests::testSimpleCovarianceModels`. Compat:
`pseudoSqrt`, `volatility`, `covariance`, `diffusion`.

## Phase-164 Markov functional state process

```python
sp = ql.MfStateProcess(reversion=0.0, times=[], vols=[1.0])
assert sp.variance(0.0, 0.0, 1.0) == 1.0

sp = ql.MfStateProcess(0.01, [1.0, 2.0], [1.0, 2.0, 3.0])
sp.diffusion(1.0, 0.0)
sp.variance(0.0, 0.0, 1.5)
```

Recovers `MarkovFunctionalTests::testMfStateProcess`. Compat: `stdDeviation`.

## Phase-165 Kahale smile section

```python
sec = ql.LinearSmileSection(t, strikes, std_devs, atm)
ksec = ql.KahaleSmileSection(
    sec, atm, interpolate=False, moneyness_grid=[k / atm for k in strikes]
)
ksec.left_core_strike()
ksec.option_price(strike)
```

Recovers `MarkovFunctionalTests::testKahaleSmileSection`. Compat: `leftCoreStrike`,
`rightCoreStrike`, `digitalOptionPrice`.

## Phase-166 MarkovFunctional vanilla engines

```python
settings = (
    ql.MarkovFunctionalModelSettings()
    .with_y_grid_points(64)
    .with_smile_moneyness_checkpoints([0.5, 1.0, 1.5])
)
mf = ql.MarkovFunctional(
    yts, 0.01, [], [1.0], swaption_vol, expiries, tenors, swap_index, settings
)
outputs = mf.model_outputs()

swaption.set_pricing_engine(yts, swaption_vol)  # Black
swaption.set_gaussian1d_pricing_engine(mf)

cap.set_pricing_engine(yts, optionlet_vol)
cap.set_gaussian1d_pricing_engine(mf)
```

Recovers `MarkovFunctionalTests::testVanillaEngines` (flat baskets). Compat:
`modelOutputs`, `withYGridPoints`, `ConstantOptionletVolatility`.

## Phase-167 MarkovFunctional calibration diagnostics

```python
outputs = mf.model_outputs()
outputs.market_zerorate[i]  # vs outputs.model_zerorate[i]
outputs.market_call_premium[i][j]  # vs outputs.model_call_premium[i][j]
```

Recovers `MarkovFunctionalTests::testCalibrationOneInstrumentSet` (flat baskets 1–2).

## Phase-168 MarkovFunctional secondary calibration

```python
helper.set_gaussian1d_pricing_engine(mf)
mf.calibrate(helpers, ql.LevenbergMarquardt(), end_criteria)
mf.params()

swaption = ql.make_swaption(swap_index, option_tenor)
swaption.set_pricing_engine(yts, vol)
black_vega = swaption.vega()
swaption.set_gaussian1d_pricing_engine(mf)
```

Recovers `MarkovFunctionalTests::testCalibrationTwoInstrumentSets` (flat basket).
Compat: `setGaussian1dPricingEngine` on `SwaptionHelper`, `makeSwaption`.

## Phase-169 MarkovFunctional Bermudan swaption

```python
yts = ql.markov_functional_test_md0_yts()
swaption_vol = ql.markov_functional_test_md0_swaption_vts()
mf = ql.MarkovFunctional(yts, 0.01, [], [1.0], swaption_vol, expiries, tenors, swap_index, settings)
underlying = ql.make_vanilla_swap(
    ql.Period(10, ql.TimeUnit.Years), ibor, 0.03, effective_date
)
swaption = ql.Swaption(underlying, ql.BermudanExercise(exercise_dates))
swaption.set_gaussian1d_pricing_engine(mf)
```

Recovers `MarkovFunctionalTests::testBermudanSwaption` (md0 market, coterminal basket 3).
Compat: `markovFunctionalTestMd0Yts`, `markovFunctionalTestMd0SwaptionVts`.

## Phase-170 MarkovFunctional real-market calibration

```python
yts = ql.markov_functional_test_md0_yts()
swaption_vol = ql.markov_functional_test_md0_swaption_vts()
optionlet_vol = ql.markov_functional_test_md0_optionlet_vts()
outputs = mf.model_outputs()
outputs.market_zerorate[i]  # vs outputs.model_zerorate[i]
```

Recovers `MarkovFunctionalTests::testCalibrationOneInstrumentSet` (real md0 baskets 1–2).
Compat: `markovFunctionalTestMd0OptionletVts`.

## Phase-171 MarkovFunctional real-market vanilla engines

```python
outputs = mf.model_outputs()
smile_corr = (
    outputs.market_call_premium[i][j] - outputs.market_raw_call_premium[i][j]
)
swaption.set_pricing_engine(yts, swaption_vol)
black = swaption.NPV()
swaption.set_gaussian1d_pricing_engine(mf)
assert abs(black - swaption.NPV() + smile_corr) <= tol
```

Recovers `MarkovFunctionalTests::testVanillaEngines` (real md0 baskets 1–2).

## Phase-172 MarkovFunctional md0 secondary calibration

```python
helper_vols = ql.markov_functional_test_md0_coterminal_helper_vols()
mf.calibrate(helpers, ql.LevenbergMarquardt(), end_criteria)
assert abs(black_price - mf_price) / black_vega <= 0.1
```

Recovers `MarkovFunctionalTests::testCalibrationTwoInstrumentSets` (real md0 basket).
Compat: `markovFunctionalTestMd0CoterminalHelperVols`.

## Phase-173 SmileSectionUtils W-shaped smile

```python
sec = ql.LinearSmileSection(t, strikes, std_devs, atm)
utils = ql.SmileSectionUtils(sec, money, atm)
left, right = utils.arbitragefree_indices()
assert right > left
```

Recovers `MarkovFunctionalTests::testSmileSectionUtilsWShapedSmile`.

## Phase-174 LMM MC swaption loop

```python
grid = ql.TimeGrid(process.fixing_times(), steps)
gen = ql.MultiPathGenerator(process, grid, seed=42)
path = gen.next()  # path[asset][time]
dis = process.discount_bond(rates)
stat = ql.GeneralStatistics()
stat.add(max(npv, 0.0))
```

Recovers `LiborMarketModelTests::testSwaptionPricing` Monte-Carlo loop.
Compat: `discountBond`, `accrualStartTimes`, `errorEstimate`.

## Phase-175 LMM Hull–White lambda bootstrapping

```python
param = ql.LfmHullWhiteParameterization(process, caplet_vol)
process.set_covar_param(param)
covar = process.covariance(0.0, None, 1.0)
vol = math.sqrt(covar.at(i + 1, i + 1))
base = ql.lfm_base_integrated_covariance(param, t)
```

Recovers `LiborMarketModelProcessTests::testLambdaBootstrapping`.
Compat: `covarParam`, `integratedCovariance`.

## Phase-176 LMM LowDiscrepancy MC caplet pricing

```python
gen = ql.LowDiscrepancyMultiPathGenerator(process, grid, seed=42)
path = gen.next()
```

Recovers `LiborMarketModelProcessTests::testMonteCarloCapletPricing`
(one- and three-factor Hull–White LMM caplet / ratchet MC).

## Phase-177 LMM process next-index-reset

```python
process = ql.LiborForwardModelProcess(60, index)
idx = process.next_index_reset(fixing_time)
```

Recovers `LiborMarketModelProcessTests::testInitialisation`.
Compat: `nextIndexReset`.

## Phase-178 linear least-squares regression

```python
model = ql.LinearRegression(x, y)
model.coefficients()
model.standard_errors()
```

Recovers `LinearLeastSquaresRegressionTests::test1dLinearRegression`.
Compat: `standardErrors`.

## Phase-179 AbcdFunction degenerate covariance

```python
f = ql.AbcdFunction(0.0, 0.0, 1.0e-15, 1.0)
cov = f.covariance(0.0, 1.0, 1.0, 1.0)
```

Recovers `MarketModelTests::testAbcdDegenerateCases`.
Compat: `maximumVolatility`, `shortTermVolatility`, `longTermVolatility`.

## Phase-180 multi-dimensional linear regression

```python
model = ql.LinearRegression(x_rows, y, intercept=1.0)
```

Recovers the intercept-based path in
`LinearLeastSquaresRegressionTests::testMultiDimRegression`.

## Phase-181 custom-basis linear regression

```python
model = ql.linear_regression_with_basis(
    x, y, basis=["const", "x", "x2", "sin"]
)
```

Recovers `LinearLeastSquaresRegressionTests::testRegression`.

## Phase-182 market-model covariance

```python
corr = ql.time_homogeneous_forward_correlation(
    ql.exponential_correlations(rate_times), rate_times
)
model = ql.FlatVol(vols, corr, evolution, n - 1, rates, displ)
cov = model.covariance(step)
```

Recovers `MarketModelTests::testCovariance` (FlatVol and AbcdVol).

## Phase-183 market-model pseudo-root

```python
root = model.pseudo_root(step)
cov = model.covariance(step)
assert np.allclose(root @ root.T, cov)
```

Verifies `pseudoRoot(i) @ pseudoRoot(i).T == covariance(i)` for `FlatVol` and `AbcdVol`.

## Phase-184 market-model numeraire measures

```python
evolution = ql.EvolutionDescription(rate_times, evolution_times)
numeraires = ql.money_market_plus_measure(evolution, offset=5)
assert ql.is_in_money_market_plus_measure(evolution, numeraires, 5)
```

Recovers numeraire schedules used in `MarketModelTests::testDriftCalculator`.

## Phase-185 LMM drift calculator

```python
calc = ql.LMMDriftCalculator(
    model.pseudo_root(step), model.displacements(),
    evolution.rate_taus(), numeraire, alive,
)
plain = calc.compute_plain(forwards)
reduced = calc.compute_reduced(forwards)
assert all(abs(p - r) <= 1e-16 for p, r in zip(plain, reduced))
```

Recovers `MarketModelTests::testDriftCalculator` (FlatVol and AbcdVol).

## Phase-186 AbcdFunction variance

```python
f = ql.AbcdFunction(a, b, c, d)
assert f.variance(x_min, x_max, T) == f.covariance(x_min, x_max, T, T)
```

Recovers the `T1 == T2` branch of `MarketModelTests::testAbcdVolatilityIntegration`.

## Phase-49 COS / exponential-fitting Heston engines

```python
opt.set_cos_heston_pricing_engine(model, L=25, N=600)
print(opt.NPV())

opt.set_exponential_fitting_heston_pricing_engine(
    model, control_variate=ql.HestonComplexLogFormula.OptimalCV
)
# Helpers:
helper.set_cos_heston_pricing_engine(model, L=12, N=75)
```

Fourier-Cosine (`COSHestonEngine`) and exponentially fitted Gauss–Laguerre
(`ExponentialFittingHestonEngine`) alternatives to Laguerre
`set_heston_pricing_engine`. Both work for European vanillas and calibration helpers.

## Phase-50 discrete-dividend European options

```python
opt = ql.EuropeanOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 40.0),
    ql.EuropeanExercise(today + 180),
)
opt.set_dividend_pricing_engine(
    process,
    [today + 60, today + 150],
    [0.50, 0.50],
)
print(opt.NPV())

# Inspect cash dividends:
divs = ql.DividendVector([today + 60], [0.50])
assert divs[0].amount() == 0.50
d = ql.FixedDividend(0.50, today + 60)
```

`AnalyticDividendEuropeanEngine` via dates/amounts (no CashFlow / Dividend MI).
Compat: `setDividendPricingEngine`. See Phase 51 for FD dividend overloads.

## Phase-51 FD discrete-dividend vanilla engines

```python
opt.set_fd_dividend_pricing_engine(
    process,
    [today + ql.Period(3, ql.TimeUnit.Months),
     today + ql.Period(9, ql.TimeUnit.Months)],
    [8.3, 6.8],
    t_grid=50,
    x_grid=200,
    damping_steps=1,
    cash_dividend_model=ql.CashDividendModel.Escrowed,
)

opt.set_fd_heston_dividend_pricing_engine(
    model,
    dividend_dates,
    dividend_amounts,
    t_grid=200,
    x_grid=400,
    v_grid=100,
)
```

FD Black–Scholes / Heston engines with discrete cash dividends.
`CashDividendModel.Spot` (default) or `.Escrowed`. Compat:
`setFdDividendPricingEngine` / `setFdHestonDividendPricingEngine`. See Phase 52
for `CashDividendEuropeanEngine` and Phase 53 for FD quanto overloads.

## Phase-52 CashDividendEuropeanEngine

```python
opt.set_cash_dividend_pricing_engine(
    process,
    [today + ql.Period(6, ql.TimeUnit.Months)],
    [5.0],
    cash_dividend_model=ql.CashDividendModel.Escrowed,
)
print(opt.NPV())
```

Semi-analytic Spot / Escrowed cash-dividend European engine (Healy). Prefer
this over FD when exercise is European; use Phase 51 FD setters for American.
Compat: `setCashDividendPricingEngine`.

## Phase-53 FD quanto vanilla engines

```python
helper = ql.FdmQuantoHelper(
    domestic_rfr, foreign_rfr, fx_vol, equity_fx_correlation=-0.75
)
print(helper.quanto_adjustment(0.3, 0.0, 1.0))
# ≈ domestic_r - foreign_r + corr * equity_vol * fx_vol

# European FD quanto ≈ analytic QuantoVanillaOption
opt.set_fd_quanto_pricing_engine(process, helper, t_grid=100, x_grid=500)

# American + discrete dividends + quanto (cached NPV ≈ 8.90611734)
opt.set_fd_quanto_dividend_pricing_engine(
    process, [today + ql.Period(6, ql.TimeUnit.Months)], [8.0], helper,
    t_grid=100, x_grid=400, damping_steps=1,
)
opt.set_fd_heston_quanto_dividend_pricing_engine(
    model, div_dates, div_amounts, helper, t_grid=100, x_grid=400, v_grid=3,
)
```

`FdmQuantoHelper` for FD Black–Scholes / Heston quanto (and dividend+quanto)
overloads. Escrowed cash-dividend model is unsupported with quanto (QL).
Compat: `setFdQuantoPricingEngine`, `setFdQuantoDividendPricingEngine`,
`setFdHestonQuantoPricingEngine`, `setFdHestonQuantoDividendPricingEngine`.

## Phase-54 Black callable bond engines

See the Phase-54 section above (after Phase-23).

## Phase-40 quanto vanilla options

```python
opt = ql.QuantoVanillaOption(
    ql.PlainVanillaPayoff(ql.OptionType.Call, 105.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(
    process,                 # domestic BSM process
    foreign_risk_free,       # YieldTermStructureHandle
    fx_vol,                  # BlackVolTermStructureHandle
    0.3,                     # FX/asset correlation (or QuoteHandle)
)
print(opt.NPV(), opt.qvega(), opt.qrho(), opt.qlambda())
```

Standalone wrapper (no OneAssetOption MI). See Phase 41 for forward quanto
and Phase 42 for barrier quanto.

## Phase-41 quanto-forward vanilla options

```python
opt = ql.QuantoForwardVanillaOption(
    1.05,           # moneyness
    today + 90,     # reset date (0 → today for plain quanto parity)
    ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),  # strike ignored
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process, foreign_risk_free, fx_vol, 0.3)
print(opt.NPV(), opt.qvega(), opt.qrho(), opt.qlambda())
```

Combines forward-start strike reset with quanto adjustment. See Phase 42 for
barrier quanto and Phase 44 for performance-forward quanto.

## Phase-42 quanto barrier options

```python
opt = ql.QuantoBarrierOption(
    ql.BarrierType.DownOut,
    95.0,           # barrier
    3.0,            # rebate
    ql.PlainVanillaPayoff(ql.OptionType.Call, 90.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process, foreign_risk_free, fx_vol, 0.3)
print(opt.NPV(), opt.qvega(), opt.qrho(), opt.qlambda())
```

Standalone wrapper (no BarrierOption MI). See Phase 43 for double-barrier
quanto and Phase 44 for performance-forward quanto.

## Phase-43 quanto double-barrier options

```python
opt = ql.QuantoDoubleBarrierOption(
    ql.DoubleBarrierType.KnockOut,
    50.0,           # barrier_lo
    150.0,          # barrier_hi
    0.0,            # rebate
    ql.PlainVanillaPayoff(ql.OptionType.Call, 100.0),
    ql.EuropeanExercise(maturity),
)
opt.set_pricing_engine(process, foreign_risk_free, fx_vol, 0.3)
print(opt.NPV())
```

Standalone wrapper (no DoubleBarrierOption MI). Analytic double-barrier
engine does not populate slots for quanto greeks (NPV-only, like Phase 42).
See Phase 44 for performance-forward quanto.

## Phase-44 quanto-forward performance options

```python
opt = ql.QuantoForwardVanillaOption(
    1.05,           # moneyness
    today + 90,     # reset date
    ql.PlainVanillaPayoff(ql.OptionType.Call, 0.0),
    ql.EuropeanExercise(maturity),
)
opt.set_performance_pricing_engine(process, foreign_risk_free, fx_vol, 0.3)
print(opt.NPV())  # ~1/100 of non-performance quanto-forward NPV
```

Same `QuantoForwardVanillaOption` instrument as Phase 41; attaches
`QuantoEngine` over `ForwardPerformanceVanillaEngine<AnalyticEuropeanEngine>`.

## When to stay on SWIG

Use the official `QuantLib` PyPI wheel if you need broad instrument coverage,
legacy examples, or full class hierarchies. Use `qlnb` when you want a smaller
nanobind surface, Stable ABI wheels, and NumPy-friendly helpers.

See also [packaging.md](packaging.md) for how wheels are built and
[free-threading.md](free-threading.md) for threaded / free-threaded notes.
