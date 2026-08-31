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
- See Phase 66 for discrete-dividend overload on the single-barrier engine

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

### Phase 66 (FD Heston barrier dividends)
- `BarrierOption.set_fd_heston_dividend_pricing_engine` → `FdHestonBarrierEngine` + cash dividends
- Empty schedule matches the plain Phase-38 engine; far barrier ≈ vanilla FD+div

### Phase 67 (FD Black-Scholes barrier)
- `BarrierOption.set_fd_pricing_engine` → `FdBlackScholesBarrierEngine` (Douglas)
- `set_fd_dividend_pricing_engine` + `BarrierOptionTest::testDividendBarrier` goldens

### Phase 68 (barrier implied volatility)
- `BarrierOption.implied_volatility(target, process, …)` — analytic if no dividends
- Cash-dividend overload uses `FdBlackScholesBarrierEngine` internally
- Round-trips `BarrierOptionTest::testImpliedVolatility` targets

### Phase 69 (cap/floor implied volatility)
- `CapFloor.implied_volatility(target, discount_curve, guess=0.10, …)`
- Recovers Black term vol from `CapFloorTest::testCachedValue` NPVs

### Phase 70 (swaption implied volatility)
- `Swaption.implied_volatility(target, discount_curve, guess=0.10, …)`
- Recovers Black term vol from `SwaptionTest::testCachedValue` / Phase-5 NPV
- `SwaptionPriceType` (`Spot` / `Forward`) matches C++ `Swaption::PriceType`

### Phase 71 (double / soft barrier implied volatility)
- `DoubleBarrierOption.implied_volatility(target, process, …)` — analytic European
- `SoftBarrierOption.implied_volatility(target, process, …)` — analytic European
- Recovers Haug vols from Phase-25 / Phase-29 NPVs

### Phase 72 (bond yield / duration / z-spread)
- `bond_yield` / `clean_price(yield_rate, …)` on fixed / zero / floating bonds
- `duration` / `convexity` / `accrued_amount` via `BondFunctions`
- `z_spread` / `clean_price_from_z_spread` vs a discount curve
- Recovers `BondsTests::testCached` and `testThirty360BondWithSettlementOn31st`

### Phase 73 (CDS option)
- `CdsOption` + `BlackCdsOptionEngine` on a running-spread `CreditDefaultSwap`
- `atm_rate` / `risky_annuity` / `implied_volatility`
- Recovers `CdsOptionTests::testCached` NPV 270.976348

### Phase 74 (compound option)
- `CompoundOption` + `AnalyticCompoundOptionEngine` (Wystup / Haug)
- Mother/daughter European vanillas; NPV, delta, gamma, vega, theta
- Recovers Haug 2007 / sitmo goldens and put-call parity

### Phase 75 (Margrabe exchange option)
- `MargrabeOption` + `AnalyticEuropeanMargrabeEngine` / `AnalyticAmericanMargrabeEngine`
- Exchange Q2 of asset 2 for Q1 of asset 1; `delta1` / `delta2` / `gamma1` / `gamma2` / `theta`
- Recovers `MargrabeOptionTests` Haug European 2.125 and American 2.1357

### Phase 76 (chooser options)
- `SimpleChooserOption` + `AnalyticSimpleChooserEngine` (Haug 6.1071)
- `ComplexChooserOption` + `AnalyticComplexChooserEngine` (Haug 6.0508)
- Choose call vs put at a future date; simple shares strike/expiry, complex does not

### Phase 77 (Turnbull-Wakeman arithmetic Asian)
- `DiscreteAveragingAsianOption.set_turnbull_wakeman_pricing_engine`
- Arithmetic average-price (Haug Table 4-28); `delta` / `gamma`
- Recovers ATM call/put 3.2700 and ITM call 19.5152 (tol 2.5e-3)

### Phase 78 (Kirk spread basket)
- `BasketOption` + `SpreadBasketPayoff` + `KirkEngine` (Haug pp.59-60)
- Two futures-style underlyings (`q = r`); recovers 4.7530 / 3.7970 / 2.5537

### Phase 79 (Stulz min/max basket)
- `MinBasketPayoff` / `MaxBasketPayoff` + `StulzEngine` (Stulz 1982)
- Recovers Firth/Haug two-asset min call 10.898 and max call 17.565

### Phase 80 (variance swap)
- `VarianceSwap` + `ReplicatingVarianceSwapEngine` (Demeterfi–Derman–Kamal–Zou)
- `BlackVarianceSurface` factory; recovers fair variance 0.04189

### Phase 81 (MC variance swap)
- `VarianceSwap.set_mc_pricing_engine` → `MakeMCVarianceSwapEngine`
- `BlackVarianceCurve` factory; recovers fair variance 0.04 (tol 3e-4)

### Phase 82 (Choi average basket)
- `AverageBasketPayoff` + `ChoiBasketEngine` (Choi 2018)
- Recovers golden put 15.920085 / call 22.361227 (tol 1e-5)

### Phase 83 (holder / writer extensible options)
- `HolderExtensibleOption` + `AnalyticHolderExtensibleOptionEngine` (Haug 9.4233)
- `WriterExtensibleOption` + `AnalyticWriterExtensibleOptionEngine` (Haug 6.8238)

### Phase 84 (more basket engines)
- `BasketOption.set_single_factor_pricing_engine` → `SingleFactorBsmBasketEngine`
- `BasketOption.set_deng_li_zhou_pricing_engine` → `DengLiZhouBasketEngine`
- Recovers Deng-Li-Zhou negative-strike golden 3.34412 (tol 1e-5)

### Phase 85 (spread basket engines)
- `BasketOption.set_bjerksund_stensland_pricing_engine` → `BjerksundStenslandSpreadEngine`
- `BasketOption.set_pearson_pricing_engine` → `PearsonSpreadEngine`
- `BasketOption.set_operator_splitting_pricing_engine` → `OperatorSplittingSpreadEngine`
- Recovers PyFENG put 17.850835947276213 and Lo 2015 rho=0 Second 14.2843

### Phase 86 (Gaussian copula / 2-D PDE spreads)
- `BasketOption.set_gaussian_copula_pricing_engine` → `GaussianCopulaSpreadEngine`
- `BasketOption.set_fd_2d_pricing_engine` → `Fd2dBlackScholesVanillaEngine`
- Copula K=0 exchange matches Bjerksund (rel 1e-3); 2-D PDE matches Bjerksund (abs 0.05)

### Phase 87 (n-D PDE basket engine)
- `BasketOption.set_fd_ndim_pricing_engine` → `FdndimBlackScholesVanillaEngine`
- American `BasketOption` + n-D PDE recovers golden **15.1858** (tol 0.01)

### Phase 88 (MC European / American baskets)
- `BasketOption.set_mc_european_pricing_engine` → `MakeMCEuropeanBasketEngine`
- `BasketOption.set_mc_american_pricing_engine` → `MakeMCAmericanBasketEngine`
- Recovers Haug Kirk 4.7530 and 1-asset American put 21.6059

### Phase 89 (AssetSwap)
- `AssetSwap` (par / market) on `FixedRateBond` / `ZeroCouponBond` / `FloatingRateBond`
- `set_pricing_engine` → `DiscountingSwapEngine`
- Recovers suite implied-value (zero-spread fair clean = bond clean) and fair-price/spread NPV-zeroing

### Phase 90 (ZeroCouponSwap)
- `ZeroCouponSwap` (fixed payment or compounded fixed rate)
- `set_pricing_engine` → `DiscountingSwapEngine`
- Recovers suite fixed-leg NPV replication and fair payment / fair rate NPV-zeroing

### Phase 91 (BondForward)
- `BondForward` on `FixedRateBond` (standalone Forward/Instrument wrapper)
- Recovers suite futures price **207.47** (clean forward / 0.76871)

### Phase 92 (PerpetualFutures)
- `PerpetualFutures` + `set_pricing_engine` → `DiscountingPerpetualFuturesEngine`
- Recovers Ackerer–Hugonnier–Jermann analytic goldens (rel 1e-6)

### Phase 93 (MultipleResetsSwap)
- `make_multiple_resets_swap` → `MakeMultipleResetsSwap` (value copy)
- Recovers suite fair-rate NPV-zeroing (tol 1e-8) and legs-sum identity

### Phase 94 (EquityTotalReturnSwap)
- `EquityIndex` + `USDLibor` + `EquityTotalReturnSwap` (standalone Swap wrapper)
- Engine: `set_pricing_engine` → `DiscountingSwapEngine`
- Recovers suite equity-leg NPV (tol 1e-8) and fair-margin NPV-zeroing (tol 1e-8)

### Phase 95 (HimalayaOption)
- `HimalayaOption` (standalone MultiAssetOption wrapper)
- Engine: `set_mc_pricing_engine` → `MakeMCHimalayaEngine<PseudoRandom>`
- Recovers suite cached NPV **5.93632056** (tol 1e-8, seed 86421, 1023 samples)

### Phase 96 (PagodaOption)
- `PagodaOption` (standalone MultiAssetOption wrapper)
- Engine: `set_mc_pricing_engine` → `MakeMCPagodaEngine<PseudoRandom>`
- Recovers suite cached NPV **0.01221094** (tol 1e-8, seed 86421, 1023 samples)

### Phase 97 (EverestOption)
- `EverestOption` (standalone MultiAssetOption wrapper) + `yield_`
- Engine: `set_mc_pricing_engine` → `MakeMCEverestEngine<PseudoRandom>`
- Recovers suite cached NPV **0.75784944** (tol 1e-8, seed 86421, 1023 samples, 1 step/year)

### Phase 98 (FloatFloatSwap)
- `FloatFloatSwap` (standalone Swap wrapper) + `make_float_float_swap`
- Engine: `set_pricing_engine` → `DiscountingSwapEngine` + `BlackIborCouponPricer`
- Recovers suite fair-spread NPV-zeroing / payer–receiver symmetry (tol 1e-10)

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
