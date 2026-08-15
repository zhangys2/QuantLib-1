# qlnb — QuantLib nanobind bindings

Experimental Python package that binds a focused QuantLib surface with
[nanobind](https://github.com/wjakob/nanobind) and ships a wheel via
[scikit-build-core](https://github.com/scikit-build/scikit-build-core).

## Status

### Phase 0
- `Date`, `Settings`, quotes/handles
- `FlatForward` / `BlackConstantVol` factories
- `BlackScholesMertonProcess`, `EuropeanOption`

### Phase 1 (market stack)
- `Period`, calendars, day counters, `Schedule`
- Deposit helpers + `PiecewiseLogLinearDiscountCurve`
- `Euribor3M` / `Euribor6M`
- `FixedRateBond` + discounting engine
- `VanillaSwap` + discounting engine
- Type stubs in `qlnb/_qlnb.pyi`

### Phase 2 (pricing coverage)
- American `VanillaOption` + Barone-Adesi-Whaley engine
- European greeks (`delta` / `gamma` / `vega`) and `implied_volatility`
- Monte Carlo European engine (`set_mc_pricing_engine`)
- `simulate_gbm_paths` → NumPy `(samples, time_steps+1)` array
- `ForwardRateAgreement` (reuses curve / `Euribor` bindings)
- New translation unit: `src/bind_pricing.cpp`

### Phase 3 (productization)
- cibuildwheel workflow (manylinux x86_64 Stable ABI / cp312)
- Migration guide vs official SWIG bindings
- Benchmark + NPV drift CI job
- Packaging notes for monorepo wheel builds

### Phase 4 (stretch)
- `qlnb.compat` — best-effort SWIG-style aliases (`ql.May`, `Option.Put`,
  camelCase methods, `evaluationDate`); not full SWIG parity
- Experimental pricing: `BarrierOption` + `AnalyticBarrierEngine`,
  `make_cap` / `make_floor` + Black cap/floor engine
- Free-threading notes (`docs/free-threading.md`) and optional
  `QLNB_THREAD_SAFE_OBSERVER` CMake passthrough

### Phase 5 (rates options + ergonomics)
- European `Swaption` + Black swaption engine (`src/bind_rates_options.cpp`)
- `ZeroCouponBond` + discounting engine (same pattern as `FixedRateBond`)
- `make_vanilla_swap` helper for MakeVanillaSwap-style construction
- NumPy helpers: `discount_times` / `discount_dates` on curve handles
- Bootstrap helpers: `FraRateHelper`, `SwapRateHelper`
- Calendars: `Japan()`, `Germany(...)`
- Expanded `qlnb.compat` aliases (`Settlement.*`, bond/swaption camelCase)

### Phase 6 (floating bonds, tree/FD, overnight indexes)
- `FloatingRateBond` + discounting engine with `BlackIborCouponPricer` setup
- Cox–Ross–Rubinstein binomial and FD Black–Scholes engines on `VanillaOption`
  (`set_binomial_pricing_engine`, `set_fd_pricing_engine`)
- Overnight indexes: `Sofr`, `Estr`, `Eonia` (`OvernightIndex`)
- `make_ois` → `OvernightIndexedSwap` + discounting engine
- `qlnb.compat` aliases for floating bonds / tree-FD / OIS

### Phase 7 (CDS, Bermudan tree swaption, FD mesher NumPy)
- `CreditDefaultSwap` + `MidPointCdsEngine`; `FlatHazardRate` → default-probability handle
- Bermudan `Swaption` via `BermudanExercise` + `TreeSwaptionEngine` on `HullWhite`
  (`set_tree_pricing_engine` / `set_jamshidian_pricing_engine`)
- FD mesher NumPy helpers: `uniform_1d_mesher_locations`,
  `fdm_black_scholes_mesher_locations`
- New translation unit: `src/bind_credit.cpp`

### Phase 8 (ISDA CDS, GSR/Gaussian1d, FD value grid)
- `CreditDefaultSwap.set_isda_pricing_engine` + ISDA numerical enums
- `InterpolatedHazardRateCurve` (BackwardFlat) factory
- `Gsr` model + `Swaption.set_gaussian1d_pricing_engine`
- `fdm_black_scholes_values` → NumPy `(x_grid, 2)` `[spot, value]` grid

### Phase 9 (CDS bootstrap, Asians, FD Hull–White swaption)
- `SpreadCdsHelper` + `PiecewiseHazardRateCurve` hazard bootstrap
- Continuous / discrete geometric Asian options (analytic engines)
- `Swaption.set_fd_hullwhite_pricing_engine`
- `Settings.include_todays_cash_flows` (needed for CDS bootstrap parity)

### Phase 10 (CMS / SwapIndex / Hagan)
- `EuriborSwapIsdaFixA` → opaque `SwapIndex`
- `ConstantSwaptionVolatility` → `SwaptionVolatilityStructureHandle`
- `AnalyticHaganPricer` / `NumericHaganPricer` → `CmsCouponPricer`
- `CmsCoupon` + `make_cms` → standalone `Swap`
- New translation unit: `src/bind_cms.cpp`

### Phase 11 (CMS-spread)
- `SwapIndex.add_fixing` / `fixing` / `value_date`
- `SwapSpreadIndex` (`make_swap_spread_index`; also aliased as `ql.SwapSpreadIndex`)
- `LinearTsrPricer`, `LognormalCmsSpreadPricer`
- `CmsSpreadCoupon` / `CappedFlooredCmsSpreadCoupon`

### Phase 12 (zero inflation / ZCIS)
- `UKRPI` / `EUHICP` → `ZeroInflationIndex`
- `InterpolatedZeroInflationCurve` / `FlatZeroInflationCurve` /
  `PiecewiseZeroInflationCurve` + `ZeroCouponInflationSwapHelper`
- `ZeroCouponInflationSwap` + `DiscountingSwapEngine`
- New translation unit: `src/bind_inflation.cpp`

### Phase 13 (YoY inflation / YYIIS)
- `YYUKRPI` / `YYEUHICP` → `YoYInflationIndex` (quoted YoY)
- `make_yoy_inflation_index(zero_index, handle)` — ratio YoY from a zero index
- `InterpolatedYoYInflationCurve` / `FlatYoYInflationCurve` /
  `PiecewiseYoYInflationCurve` + `YearOnYearInflationSwapHelper`
- `YearOnYearInflationSwap` + `DiscountingSwapEngine`

### Phase 14 (YoY inflation caps / floors)
- `ConstantYoYOptionletVolatility` → `YoYOptionletVolatilitySurfaceHandle`
- `YoYInflationCapFloor` (Cap / Floor / Collar) + Black / unit-displaced /
  Bachelier engines via `set_pricing_engine(..., model=...)`
- `make_yoy_inflation_capfloor` (`MakeYoYInflationCapFloor`)

### Phase 15 (CPISwap / CPIBond)
- `CPISwap` + `DiscountingSwapEngine`; `cpi_lagged_fixing` (`CPI::laggedFixing`)
- `CPIBond` + `DiscountingBondEngine`
- Helpers: `GBPLibor`, `InterpolatedZeroCurve`, `Schedule(dates=…)`

### Phase 16 (CPICapFloor)
- `Matrix` helper + `InterpolatedCPICapFloorTermPriceSurface` (Bilinear)
- `CPICapFloor` + `InterpolatingCPICapFloorEngine` via `set_pricing_engine(surface)`

### Phase 17 (inflation seasonality)
- `MultiplicativePriceSeasonality` / `KerkhofSeasonality`
- `set_seasonality` / `has_seasonality` on zero & YoY inflation handles
- `inflation_period(date, frequency)` helper

### Phase 18 (CPI coupons / CPILeg)
- `CPICoupon` + `CPICouponPricer` / `set_pricer`
- `make_cpi_leg` (`CPILeg`) → `list[CashFlow]`
- `set_cpi_coupon_pricer`, `cashflows_npv`, `cashflows_accrued_amount`
- `clear_fixings` on zero / YoY inflation indexes (IndexManager isolation)

### Phase 65 (CPI vol-dependent optionlets)
- `ConstantCPIVolatility` → `CPIVolatilitySurfaceHandle`
- `BlackCPICouponPricer` / `BachelierCPICouponPricer` (binding-layer; QL has no descendents)
- `CPICoupon.caplet_price` / `floorlet_price` / `caplet_rate` / `floorlet_rate`

### Phase 19 (YoY coupons / yoyInflationLeg)
- `YoYInflationCoupon` + `YoYInflationCouponPricer` / `set_pricer`
- Black / unit-displaced Black / Bachelier YoY coupon pricers
- `make_yoy_inflation_leg` (`yoyInflationLeg`) → `list[CashFlow]`
- `set_yoy_coupon_pricer`

### Phase 20 (capped/floored YoY coupons)
- `CappedFlooredYoYInflationCoupon` (cap / floor / effective strikes)
- `YoYInflationCapFloor` from an existing YoY leg (decomposition identities)

### Phase 21 (Indexed / CPI / ZeroInflation cash flows)
- `IndexedCashFlow`, `CPICashFlow`, `ZeroInflationCashFlow`
- `ZeroCouponInflationSwap.inflation_leg` / `fixed_leg`

### Phase 22 (YoY cap/floor term price surface)
- `InterpolatedYoYCapFloorTermPriceSurface<Bicubic,Cubic>` → handle
- ATM YoY swap / forward rates from put-call parity
- `InterpolatedZeroCurve(..., interpolation="cubic")` support

### Phase 23 (callable / puttable bonds)
- `BondPrice` / `Callability` (`make_callability`)
- `CallableFixedRateBond` / `CallableZeroCouponBond`
- `set_tree_pricing_engine(HullWhite, time_steps, discount_curve)`

### Phase 54 (Black callable bond engines)
- `set_black_pricing_engine(fwd_yield_vol, discount_curve)` on callable bonds
- `BlackCallableFixedRateBondEngine` / `BlackCallableZeroCouponBondEngine` aliases

### Phase 55 (callable bond implied volatility)
- `CallableFixedRateBond` / `CallableZeroCouponBond.implied_volatility(BondPrice, curve, …)`
- Round-trips target clean/dirty prices via Black fwd-yield vol

### Phase 56 (callable bond OAS)
- `oas` / `clean_price_oas` on callable bonds (tree engines; Black ignores spread)
- `effective_duration` / `effective_convexity` at a given OAS

### Phase 57 (convertible bonds)
- `ConvertibleZeroCouponBond` / `ConvertibleFixedCouponBond`
- `set_binomial_pricing_engine(process, time_steps, credit_spread)` → CRR Tsiveriotis–Fernandes
- `make_soft_callability` (call with conversion trigger)
- `settlement_value` on vanilla `FixedRateBond` / `ZeroCouponBond`

### Phase 58 (floating convertibles)
- `ConvertibleFloatingRateBond` + `Euribor1Y`
- `settlement_value` on vanilla `FloatingRateBond`

### Phase 24 (currencies / FX forward)
- `Currency` factories: `USDCurrency` / `EURCurrency` / `GBPCurrency` / `SGDCurrency`
- `Money`, `ExchangeRate` (+ `chain` / `exchange`), `ExchangeRateManager` helpers
- `FxForward` + `set_pricing_engine(src_curve, tgt_curve, spot)` → `DiscountingFxForwardEngine`

### Phase 25 (double-barrier options)
- `DoubleBarrierType` (`KnockIn` / `KnockOut` / `KIKO` / `KOKI`)
- `DoubleBarrierOption` + `AnalyticDoubleBarrierEngine` (Ikeda/Kunitomo)

### Phase 26 (double-barrier binary options)
- `CashOrNothingPayoff`
- `DoubleBarrierOption.set_binary_pricing_engine` → `AnalyticDoubleBarrierBinaryEngine`
- European exercise for KnockIn/KnockOut; American for KIKO/KOKI

### Phase 27 (continuous lookback options)
- `FloatingTypePayoff`
- `ContinuousFloatingLookbackOption` + `AnalyticContinuousFloatingLookbackEngine`
- `ContinuousFixedLookbackOption` + `AnalyticContinuousFixedLookbackEngine`

### Phase 28 (partial-time lookback options)
- `ContinuousPartialFloatingLookbackOption` + analytic engine (Haug 2006 p.146)
- `ContinuousPartialFixedLookbackOption` + analytic engine (Haug 2006 p.148)

### Phase 29 (soft barrier options)
- `SoftBarrierOption` + `AnalyticSoftBarrierEngine` (Hart/Ross / Haug p.165)

### Phase 30 (partial-time barrier options)
- `PartialBarrierRange` (`Start` / `EndB1` / `EndB2`)
- `PartialTimeBarrierOption` + `AnalyticPartialTimeBarrierOptionEngine`

### Phase 31 (binary barrier options)
- `AssetOrNothingPayoff`
- `BarrierOption` cash/asset-or-nothing + American exercise overloads
- `set_binary_pricing_engine` → `AnalyticBinaryBarrierEngine` (Haug p.176)

### Phase 32 (two-asset barrier options)
- `TwoAssetBarrierOption` + `AnalyticTwoAssetBarrierEngine` (Haug)
- Asset 1 = strike/payoff; asset 2 = barrier monitor; `rho` = correlation
  (`QuoteHandle` or scalar)

### Phase 33 (two-asset correlation options)
- `TwoAssetCorrelationOption` + `AnalyticTwoAssetCorrelationEngine` (Zhang / Haug)
- Pays asset-2 payoff only if asset 1 finishes ITM; correlation via
  `QuoteHandle` or scalar

### Phase 34 (cliquet / ratchet options)
- `PercentageStrikePayoff` (moneyness strike)
- `CliquetOption` + `AnalyticCliquetEngine` (Haug p.37)

### Phase 35 (forward vanilla options)
- `ForwardVanillaOption` + `ForwardVanillaEngine<AnalyticEuropeanEngine>` (Haug p.37)
- `set_performance_pricing_engine` → performance forward engine

### Phase 36 (Heston stochastic volatility)
- `HestonProcess` / `HestonModel` / `HestonDiscretization`
- `VanillaOption` / `EuropeanOption.set_heston_pricing_engine` → `AnalyticHestonEngine`
- New translation unit: `src/bind_heston.cpp`

### Phase 59 (MC European Heston)
- `set_mc_heston_pricing_engine(process, steps_per_year=11, …)` → `MakeMCEuropeanHestonEngine`
- `error_estimate` on `EuropeanOption` / `VanillaOption`

### Phase 60 (MC lookback engines)
- `Continuous*LookbackOption.set_mc_pricing_engine` → `MakeMCLookbackEngine<Option, PseudoRandom>`
- `error_estimate` on all four lookback wrappers (Phases 27–28)

### Phase 61 (double-barrier binary FD-Heston / MC)
- Binary `DoubleBarrierOption.set_fd_heston_pricing_engine` vs analytic BS (Heston σ→0)
- `set_mc_pricing_engine` → `MakeMCDoubleBarrierEngine<PseudoRandom>`
- `error_estimate` on `DoubleBarrierOption`

### Phase 62 (binary-barrier FD-Heston / MC)
- Binary `BarrierOption.set_fd_heston_pricing_engine` vs analytic (Heston σ→0, European cash-or-nothing)
- `set_mc_pricing_engine` → `MakeMCBarrierEngine<PseudoRandom>`
- `error_estimate` on `BarrierOption`

### Phase 37 (FD Heston engine)
- `VanillaOption` / `EuropeanOption.set_fd_heston_pricing_engine` → `FdHestonVanillaEngine`
- Grid knobs: `t_grid`, `x_grid`, `v_grid`, `damping_steps` (Hundsdorfer)

### Phase 38 (FD Heston barrier engines)
- `BarrierOption.set_fd_heston_pricing_engine` → `FdHestonBarrierEngine`
- `DoubleBarrierOption.set_fd_heston_pricing_engine` → `FdHestonDoubleBarrierEngine`

### Phase 39 (Bates jump-diffusion)
- `BatesProcess` / `BatesModel` (Heston + log-normal jumps)
- `VanillaOption` / `EuropeanOption.set_bates_pricing_engine` → `BatesEngine`
- Jump intensity exposed as `jump_intensity` (Python keyword-safe)

### Phase 40 (quanto vanilla options)
- `QuantoVanillaOption` + `QuantoEngine<VanillaOption, AnalyticEuropeanEngine>` (Haug p.105)
- Quanto greeks: `qvega`, `qrho`, `qlambda`

### Phase 41 (quanto-forward vanilla options)
- `QuantoForwardVanillaOption` + quanto/`ForwardVanillaEngine` (Haug + FinCAD checks)
- Same quanto greeks; `moneyness` + `reset_date` like `ForwardVanillaOption`

### Phase 42 (quanto barrier options)
- `QuantoBarrierOption` + `QuantoEngine<BarrierOption, AnalyticBarrierEngine>`
- Same quanto greeks (`qvega`, `qrho`, `qlambda`); barrier/rebate like `BarrierOption`

### Phase 43 (quanto double-barrier options)
- `QuantoDoubleBarrierOption` + `QuantoEngine<DoubleBarrierOption, AnalyticDoubleBarrierEngine>`
- Same quanto greeks; `barrier_lo` / `barrier_hi` / rebate like `DoubleBarrierOption`

### Phase 44 (quanto-forward performance options)
- `QuantoForwardVanillaOption.set_performance_pricing_engine` → quanto/`ForwardPerformanceVanillaEngine`
- Same instrument as Phase 41; performance NPV ≈ 1/100 of non-performance

### Phase 45 (FD Bates vanilla engine)
- `VanillaOption` / `EuropeanOption.set_fd_bates_pricing_engine` → `FdBatesVanillaEngine`
- PIDE / Hundsdorfer scheme; grid args match FD Heston

### Phase 63 (FD Bates dividend overloads)
- `set_fd_bates_dividend_pricing_engine` → `FdBatesVanillaEngine` + discrete cash dividends

### Phase 46 (Bates DetJump / DoubleExp variants)
- `BatesDetJumpModel` / `BatesDoubleExpModel` / `BatesDoubleExpDetJumpModel`
- Matching engines via `set_bates_det_jump_pricing_engine`, `set_bates_double_exp_pricing_engine`, `set_bates_double_exp_det_jump_pricing_engine`

### Phase 47 (FdmSchemeDesc)
- `FdmSchemeDesc` / `FdmSchemeType` with static factories (`Hundsdorfer`, `Douglas`, …)
- Optional `scheme_desc=` on FD Heston / Bates / Black-Scholes / barrier engine setters

### Phase 48 (Heston model calibration)
- `HestonModelHelper`, `LevenbergMarquardt`, `EndCriteria`, `CalibrationErrorType`
- `HestonModel.calibrate(helpers, method, end_criteria)` + `params` / `set_params`

### Phase 64 (DAX Heston calibration golden)
- Sepp DAX vol surface → SSE ≈ 177.2 (`CalibrationErrorType.ImpliedVolError`)
- `ZeroCurve` alias for `InterpolatedZeroCurve` (linear)

### Phase 65 (CPI vol-dependent optionlets)
- `ConstantCPIVolatility` → `CPIVolatilitySurfaceHandle`
- `BlackCPICouponPricer` / `BachelierCPICouponPricer` fill QL's missing `optionletPriceImp`
- `CPICoupon.caplet_price` / `floorlet_price` after `set_pricer`

### Phase 49 (COS / exp-fitting Heston engines)
- `set_cos_heston_pricing_engine` → `COSHestonEngine` (Fang–Oosterlee)
- `set_exponential_fitting_heston_pricing_engine` → `ExponentialFittingHestonEngine`
- `HestonComplexLogFormula` control-variate enum

### Phase 50 (discrete-dividend European options)
- `FixedDividend`, `DividendVector(dates, amounts)`
- `EuropeanOption` / `VanillaOption.set_dividend_pricing_engine` → `AnalyticDividendEuropeanEngine`

### Phase 51 (FD discrete-dividend vanilla engines)
- `CashDividendModel` (`Spot` / `Escrowed`)
- `set_fd_dividend_pricing_engine` → `FdBlackScholesVanillaEngine` + dividends
- `set_fd_heston_dividend_pricing_engine` → `FdHestonVanillaEngine` + dividends

### Phase 52 (CashDividendEuropeanEngine)
- `set_cash_dividend_pricing_engine` → `CashDividendEuropeanEngine` (Spot / Escrowed)
- Semi-analytic alternative to analytic / FD discrete-dividend engines

### Phase 53 (FD quanto vanilla engines)
- `FdmQuantoHelper` + `quanto_adjustment`
- `set_fd_quanto_pricing_engine` / `set_fd_quanto_dividend_pricing_engine`
- `set_fd_heston_quanto_pricing_engine` / `set_fd_heston_quanto_dividend_pricing_engine`

QuantLib is built from the parent source tree as a **static** library with
`QL_USE_STD_SHARED_PTR=ON` and `CMAKE_POSITION_INDEPENDENT_CODE=ON`.

### Design notes

nanobind does not support general multiple inheritance / base-pointer
adjustment. MI-heavy types (`FlatForward`, bonds/swaps, rate helpers, FRA)
are exposed as factories or standalone wrappers rather than mirroring the
full C++ hierarchy. Day counters and calendars use QuantLib's value-semantic
pimpl types. Option engines are attached via lambdas on concrete wrappers
(no Instrument/OneAssetOption MI hierarchy in Python).

## Docs

- [SWIG → qlnb migration guide](docs/migration.md)
- [Packaging / wheel build notes](docs/packaging.md)
- [Free-threading readiness](docs/free-threading.md)

Compatibility shim (optional):

```python
import qlnb.compat as ql   # SWIG-flavored aliases; prefer native qlnb for new code
d = ql.Date(15, ql.May, 1998)
ql.Settings.instance().evaluationDate = d
```

## Build

Wheels must be built from a **full QuantLib checkout** (the parent tree is
compiled into the extension). An sdist of `python-nanobind/` alone is not
sufficient — see [docs/packaging.md](docs/packaging.md).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip pytest numpy nanobind scikit-build-core ninja
pip install --no-build-isolation .
pytest
```

Optional local wheel:

```bash
pip install build
python -m build --wheel
```

## Benchmark / NPV drift

```bash
python benchmarks/bench_phase0.py
python scripts/check_npv_drift.py --abs-tol 1e-8
pip install QuantLib   # optional SWIG comparison
python benchmarks/bench_phase0.py
```

CI builds manylinux wheels and uploads benchmark artifacts via
`.github/workflows/qlnb-wheels.yml`.
