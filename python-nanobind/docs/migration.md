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
