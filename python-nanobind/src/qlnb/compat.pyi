"""Type stub for qlnb.compat.

qlnb.compat installs SWIG-style camelCase aliases onto the native classes at
import time.  The native stub (_qlnb.pyi) describes only the native snake_case
API, so the aliases are declared here, on subclasses, for code that imports
qlnb.compat.  Names compat defines that are not declared here are typed Any.
"""

from typing import Any, Iterable, Sequence, overload

import qlnb._qlnb as _native
from qlnb._qlnb import *  # noqa: F403

# BEGIN GENERATED COMPAT ALIASES

# Not generated (runtime aliases only):
#   compat exports a different object under this class name:
#     YoYInflationIndex.addFixing
#     YoYInflationIndex.availabilityLag
#     YoYInflationIndex.clearFixings
#     YoYInflationIndex.lastFixingDate
#   the alias is a Python keyword:
#     EverestOption.yield

class AbcdCalibration(_native.AbcdCalibration):
    def endCriteria(self) -> EndCriteriaType: ...

class AbcdFunction(_native.AbcdFunction):
    def instantaneousCovariance(self, u: float, T: float, S: float) -> float: ...

    def instantaneousVariance(self, t: float, T: float) -> float: ...

    def instantaneousVolatility(self, t: float, T: float) -> float: ...

    def longTermVolatility(self) -> float: ...

    def maximumVolatility(self) -> float: ...

    def shortTermVolatility(self) -> float: ...

class AbcdVol(_native.AbcdVol):
    def numberOfFactors(self) -> int: ...

    def numberOfRates(self) -> int: ...

    def numberOfSteps(self) -> int: ...

    def pseudoRoot(self, step: int) -> Matrix: ...

class AmericanExercise(_native.AmericanExercise):
    def lastDate(self) -> Date: ...

class AmortizingFixedRateBond(_native.AmortizingFixedRateBond):
    def accruedAmount(self, date: Date = ...) -> float: ...

    def bondYield(
        self,
        price: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

    def cashflowAmounts(self) -> list[float]: ...

    @overload
    def cleanPrice(self) -> float: ...

    @overload
    def cleanPrice(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dayCounter(self) -> DayCounter: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def settlementDate(self) -> Date: ...

    def settlementValue(self) -> float: ...

class AmortizingFloatingRateBond(_native.AmortizingFloatingRateBond):
    def accruedAmount(self, date: Date = ...) -> float: ...

    def bondYield(
        self,
        price: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

    def cashflowAmounts(self) -> list[float]: ...

    @overload
    def cleanPrice(self) -> float: ...

    @overload
    def cleanPrice(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def settlementDate(self) -> Date: ...

    def settlementValue(self) -> float: ...

class AssetOrNothingPayoff(_native.AssetOrNothingPayoff):
    def optionType(self) -> OptionType: ...

class AssetSwap(_native.AssetSwap):
    def cleanPrice(self) -> float: ...

    def fairCleanPrice(self) -> float: ...

    def fairNonParRepayment(self) -> float: ...

    def fairSpread(self) -> float: ...

    def floatingLegBPS(self) -> float: ...

    def floatingLegNPV(self) -> float: ...

    def isExpired(self) -> bool: ...

    def nonParRepayment(self) -> float: ...

    def parSwap(self) -> bool: ...

    def payBondCoupon(self) -> bool: ...

    def setPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        include_settlement_date_flows: bool | None = ...,
        settlement_date: Date = ...,
        npv_date: Date = ...,
    ) -> None: ...

class BMAIndex(_native.BMAIndex):
    def addFixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...

    def dayCounter(self) -> DayCounter: ...

    def fixingCalendar(self) -> Calendar: ...

    def fixingDays(self) -> int: ...

    def isValidFixingDate(self, fixing_date: Date) -> bool: ...

class BMASwap(_native.BMASwap):
    def bmaLegBPS(self) -> float: ...

    def bmaLegNPV(self) -> float: ...

    def fairLiborFraction(self) -> float: ...

    def fairLiborSpread(self) -> float: ...

    def isExpired(self) -> bool: ...

    def liborFraction(self) -> float: ...

    def liborLegBPS(self) -> float: ...

    def liborLegNPV(self) -> float: ...

    def liborSpread(self) -> float: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class BarrierOption(_native.BarrierOption):
    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date] = ...,
        dividend_amounts: Sequence[float] = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def setBinaryPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int = ...,
        max_time_steps: int = ...,
    ) -> None: ...

    def setFdDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonDividendPricingEngine(
        self,
        model: HestonModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
        biased: bool = ...,
    ) -> None: ...

    def setPerturbativePricingEngine(
        self,
        process: BlackScholesMertonProcess,
        order: int = ...,
        zero_gamma: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

    def setVannaVolgaPricingEngine(
        self,
        atm_vol: DeltaVolQuote,
        vol25_put: DeltaVolQuote,
        vol25_call: DeltaVolQuote,
        spot_fx: QuoteHandle,
        domestic_ts: YieldTermStructureHandle,
        foreign_ts: YieldTermStructureHandle,
        adapt_van_delta: bool = ...,
        bs_price_with_smile: float = ...,
    ) -> None: ...

class BasketOption(_native.BasketOption):
    def isExpired(self) -> bool: ...

    def setBjerksundStenslandPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...

    def setChoiPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        integration_lambda: float = ...,
        max_nr_integration_steps: int | None = ...,
        calc_fwd_delta: bool = ...,
        control_variate: bool = ...,
    ) -> None: ...

    def setDengLiZhouPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
    ) -> None: ...

    def setFd2dPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        x_grid: int = ...,
        y_grid: int = ...,
        t_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
        local_vol: bool = ...,
    ) -> None: ...

    def setFdNdimPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        x_grid: int = ...,
        t_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
        x_grids: Sequence[int] | None = ...,
    ) -> None: ...

    def setGaussianCopulaPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        n_points: int = ...,
    ) -> None: ...

    def setKirkPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...

    def setMCAmericanPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
        calibration_samples: int | None = ...,
    ) -> None: ...

    def setMCEuropeanPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setOperatorSplittingPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        order: OperatorSplittingOrder = ...,
    ) -> None: ...

    def setPearsonPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...

    def setSingleFactorPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
    ) -> None: ...

    def setStulzPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...

class BatesDetJumpModel(_native.BatesDetJumpModel):
    def jumpIntensity(self) -> float: ...

    def kappaLambda(self) -> float: ...

    def thetaLambda(self) -> float: ...

class BatesDoubleExpDetJumpModel(_native.BatesDoubleExpDetJumpModel):
    def jumpIntensity(self) -> float: ...

    def kappaLambda(self) -> float: ...

    def nuDown(self) -> float: ...

    def nuUp(self) -> float: ...

    def thetaLambda(self) -> float: ...

class BatesDoubleExpModel(_native.BatesDoubleExpModel):
    def jumpIntensity(self) -> float: ...

    def nuDown(self) -> float: ...

    def nuUp(self) -> float: ...

class BatesModel(_native.BatesModel):
    def jumpIntensity(self) -> float: ...

class BatesProcess(_native.BatesProcess):
    def jumpIntensity(self) -> float: ...

class BermudanExercise(_native.BermudanExercise):
    def lastDate(self) -> Date: ...

class BondForward(_native.BondForward):
    def cleanForwardPrice(self) -> float: ...

    def forwardPrice(self) -> float: ...

    def forwardValue(self) -> float: ...

    def isExpired(self) -> bool: ...

    def settlementDate(self) -> Date: ...

    def spotIncome(self, income_discount_curve: YieldTermStructureHandle) -> float: ...

    def spotValue(self) -> float: ...

class CPIBond(_native.CPIBond):
    def baseCPI(self) -> float: ...

    def cleanPrice(self) -> float: ...

    def dirtyPrice(self) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

    def settlementDate(self) -> Date: ...

class CPICapFloor(_native.CPICapFloor):
    def fixingDate(self) -> Date: ...

    def isExpired(self) -> bool: ...

    def payDate(self) -> Date: ...

    def setPricingEngine(
        self, price_surface: CPICapFloorTermPriceSurfaceHandle
    ) -> None: ...

class CPICapFloorTermPriceSurfaceHandle(_native.CPICapFloorTermPriceSurfaceHandle):
    def atmRate(self, maturity: Date) -> float: ...

    def capPrice(self, tenor: Period, strike: float) -> float: ...

    def floorPrice(self, tenor: Period, strike: float) -> float: ...

class CPICashFlow(_native.CPICashFlow):
    def cpiIndex(self) -> ZeroInflationIndex: ...

    def observationDate(self) -> Date: ...

    def observationLag(self) -> Period: ...

class CPICoupon(_native.CPICoupon):
    def adjustedIndexGrowth(self) -> float: ...

    def baseCPI(self) -> float: ...

    def capletPrice(self, effective_cap: float) -> float: ...

    def capletRate(self, effective_cap: float) -> float: ...

    def fixedRate(self) -> float: ...

    def fixingDate(self) -> Date: ...

    def floorletPrice(self, effective_floor: float) -> float: ...

    def floorletRate(self, effective_floor: float) -> float: ...

    def indexFixing(self) -> float: ...

    def indexRatio(self, date: Date) -> float: ...

    def setPricer(self, pricer: InflationCouponPricer) -> None: ...

class CPICouponPricer(_native.CPICouponPricer):
    def capletPrice(self, effective_cap: float) -> float: ...

    def capletRate(self, effective_cap: float) -> float: ...

    def capletVolatility(self) -> CPIVolatilitySurfaceHandle: ...

    def floorletPrice(self, effective_floor: float) -> float: ...

    def floorletRate(self, effective_floor: float) -> float: ...

    def setCapletVolatility(
        self, caplet_vol: CPIVolatilitySurfaceHandle
    ) -> None: ...

class CPISwap(_native.CPISwap):
    def baseCPI(self) -> float: ...

    def fairRate(self) -> float: ...

    def fairSpread(self) -> float: ...

    def fixedLegNPV(self) -> float: ...

    def fixedRate(self) -> float: ...

    def floatLegNPV(self) -> float: ...

    def inflationNominal(self) -> float: ...

    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

class CPIVolatilitySurfaceHandle(_native.CPIVolatilitySurfaceHandle):
    def indexIsInterpolated(self) -> bool: ...

    def observationLag(self) -> Period: ...

    def totalVariance(
        self,
        date: Date,
        strike: float,
        observation_lag: Period = ...,
        extrapolate: bool = ...,
    ) -> float: ...

class Calendar(_native.Calendar):
    def isBusinessDay(self, date: Date) -> bool: ...

    def isHoliday(self, date: Date) -> bool: ...

class CallableFixedRateBond(_native.CallableFixedRateBond):
    def OAS(
        self,
        clean_price: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_iterations: int = ...,
        guess: float = ...,
    ) -> float: ...

    def cleanPrice(self) -> float: ...

    def cleanPriceOAS(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def effectiveConvexity(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        bump: float = ...,
    ) -> float: ...

    def effectiveDuration(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        bump: float = ...,
    ) -> float: ...

    def impliedVolatility(
        self,
        target_price: BondPrice,
        discount_curve: YieldTermStructureHandle,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def maturityDate(self) -> Date: ...

    def setBlackPricingEngine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

    def setTreePricingEngine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...

    def settlementDate(self) -> Date: ...

class CallableZeroCouponBond(_native.CallableZeroCouponBond):
    def OAS(
        self,
        clean_price: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_iterations: int = ...,
        guess: float = ...,
    ) -> float: ...

    def cleanPrice(self) -> float: ...

    def cleanPriceOAS(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def effectiveConvexity(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        bump: float = ...,
    ) -> float: ...

    def effectiveDuration(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        bump: float = ...,
    ) -> float: ...

    def impliedVolatility(
        self,
        target_price: BondPrice,
        discount_curve: YieldTermStructureHandle,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def maturityDate(self) -> Date: ...

    def setBlackPricingEngine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

    def setTreePricingEngine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...

    def settlementDate(self) -> Date: ...

class Cap(_native.Cap):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        discount_curve: YieldTermStructureHandle,
        guess: float = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
        vol_type: VolatilityType = ...,
        displacement: float = ...,
    ) -> float: ...

    def maturityDate(self) -> Date: ...

    def setAnalyticCapFloorPricingEngine(
        self,
        model: HullWhite,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setBachelierPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...

    def setGaussian1dPricingEngine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setLiborForwardPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setMcHullWhitePricingEngine(
        self,
        model: HullWhite,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...

    def setTreePricingEngine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class CapFloor(_native.CapFloor):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        discount_curve: YieldTermStructureHandle,
        guess: float = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
        vol_type: VolatilityType = ...,
        displacement: float = ...,
    ) -> float: ...

    def maturityDate(self) -> Date: ...

    def setAnalyticCapFloorPricingEngine(
        self,
        model: HullWhite,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setBachelierPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...

    def setGaussian1dPricingEngine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setLiborForwardPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setMcHullWhitePricingEngine(
        self,
        model: HullWhite,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...

    def setTreePricingEngine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class CapHelper(_native.CapHelper):
    def calibrationError(self) -> float: ...

    def marketValue(self) -> float: ...

    def modelValue(self) -> float: ...

    def setLfmPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...

class CappedFlooredCmsSpreadCoupon(_native.CappedFlooredCmsSpreadCoupon):
    def setPricer(self, pricer: CmsSpreadCouponPricer) -> None: ...

class CappedFlooredYoYInflationCoupon(_native.CappedFlooredYoYInflationCoupon):
    def effectiveCap(self) -> float: ...

    def effectiveFloor(self) -> float: ...

    def isCapped(self) -> bool: ...

    def isFloored(self) -> bool: ...

    def setPricer(self, pricer: YoYInflationCouponPricer) -> None: ...

    def underlyingRate(self) -> float: ...

class CashOrNothingPayoff(_native.CashOrNothingPayoff):
    def cashPayoff(self) -> float: ...

    def optionType(self) -> OptionType: ...

class CdsOption(_native.CdsOption):
    def atmRate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        discount_curve: YieldTermStructureHandle,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def isExpired(self) -> bool: ...

    def riskyAnnuity(self) -> float: ...

    def setPricingEngine(
        self,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
    ) -> None: ...

class CliquetOption(_native.CliquetOption):
    def isExpired(self) -> bool: ...

    def setPerformancePricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class CmsCoupon(_native.CmsCoupon):
    def accrualEndDate(self) -> Date: ...

    def accrualStartDate(self) -> Date: ...

    def setPricer(self, pricer: CmsCouponPricer) -> None: ...

class CmsRateBond(_native.CmsRateBond):
    def accruedAmount(self, date: Date = ...) -> float: ...

    def bondYield(
        self,
        price: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

    @overload
    def cleanPrice(self) -> float: ...

    @overload
    def cleanPrice(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def cleanPriceFromZSpread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setCmsCouponPricer(self, pricer: CmsCouponPricer) -> None: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def settlementDate(self) -> Date: ...

    def settlementValue(self) -> float: ...

    def zSpread(
        self,
        price: float,
        discount_curve: YieldTermStructureHandle,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

class CmsSpreadCoupon(_native.CmsSpreadCoupon):
    def fixingDate(self) -> Date: ...

    def setPricer(self, pricer: CmsSpreadCouponPricer) -> None: ...

class Collar(_native.Collar):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        discount_curve: YieldTermStructureHandle,
        guess: float = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
        vol_type: VolatilityType = ...,
        displacement: float = ...,
    ) -> float: ...

    def maturityDate(self) -> Date: ...

    def setAnalyticCapFloorPricingEngine(
        self,
        model: HullWhite,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setBachelierPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...

    def setGaussian1dPricingEngine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setLiborForwardPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setMcHullWhitePricingEngine(
        self,
        model: HullWhite,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...

    def setTreePricingEngine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class ComplexChooserOption(_native.ComplexChooserOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class CompositeInstrument(_native.CompositeInstrument):
    def isExpired(self) -> bool: ...

class CompoundOption(_native.CompoundOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class ConstNotionalCrossCurrencyBasisSwap(_native.ConstNotionalCrossCurrencyBasisSwap):
    def fairPaySpread(self) -> float: ...

    def fairRecSpread(self) -> float: ...

    def inCcyLegBPS(self, leg: int) -> float: ...

    def inCcyLegNPV(self, leg: int) -> float: ...

    def legBPS(self, leg: int) -> float: ...

    def legNPV(self, leg: int) -> float: ...

    def setPricingEngine(
        self,
        domestic_currency: Currency,
        domestic_discount: YieldTermStructureHandle,
        foreign_currency: Currency,
        foreign_discount: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

class ConstNotionalCrossCurrencyFixedVsFloatingSwap(_native.ConstNotionalCrossCurrencyFixedVsFloatingSwap):
    def fairRate(self) -> float: ...

    def fairSpread(self) -> float: ...

    def inCcyLegBPS(self, leg: int) -> float: ...

    def inCcyLegNPV(self, leg: int) -> float: ...

    def legBPS(self, leg: int) -> float: ...

    def legNPV(self, leg: int) -> float: ...

    def setPricingEngine(
        self,
        domestic_currency: Currency,
        domestic_discount: YieldTermStructureHandle,
        foreign_currency: Currency,
        foreign_discount: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

class ConstNotionalCrossCurrencySwap(_native.ConstNotionalCrossCurrencySwap):
    def inCcyLegBPS(self, leg: int) -> float: ...

    def inCcyLegNPV(self, leg: int) -> float: ...

    def isExpired(self) -> bool: ...

    def legBPS(self, leg: int) -> float: ...

    def legNPV(self, leg: int) -> float: ...

    def setPricingEngine(
        self,
        domestic_currency: Currency,
        domestic_discount: YieldTermStructureHandle,
        foreign_currency: Currency,
        foreign_discount: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

class ContinuousAveragingAsianOption(_native.ContinuousAveragingAsianOption):
    def setHestonPricingEngine(
        self,
        process: HestonProcess,
        summation_cutoff: int = ...,
        xi_right_limit: float = ...,
    ) -> None: ...

    def setLevyPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        current_average: QuoteHandle,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

    def setVecerPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        current_average: QuoteHandle,
        start_date: Date,
        time_steps: int = ...,
        asset_steps: int = ...,
        z_min: float = ...,
        z_max: float = ...,
    ) -> None: ...

class ContinuousFixedLookbackOption(_native.ContinuousFixedLookbackOption):
    def errorEstimate(self) -> float: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class ContinuousFloatingLookbackOption(_native.ContinuousFloatingLookbackOption):
    def errorEstimate(self) -> float: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class ContinuousPartialFixedLookbackOption(_native.ContinuousPartialFixedLookbackOption):
    def errorEstimate(self) -> float: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class ContinuousPartialFloatingLookbackOption(_native.ContinuousPartialFloatingLookbackOption):
    def errorEstimate(self) -> float: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class ConvertibleFixedCouponBond(_native.ConvertibleFixedCouponBond):
    def cleanPrice(self) -> float: ...

    def conversionRatio(self) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

    def settlementDate(self) -> Date: ...

class ConvertibleFloatingRateBond(_native.ConvertibleFloatingRateBond):
    def cleanPrice(self) -> float: ...

    def conversionRatio(self) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

    def settlementDate(self) -> Date: ...

class ConvertibleZeroCouponBond(_native.ConvertibleZeroCouponBond):
    def cleanPrice(self) -> float: ...

    def conversionRatio(self) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

    def settlementDate(self) -> Date: ...

class CreditDefaultSwap(_native.CreditDefaultSwap):
    def couponLegNPV(self) -> float: ...

    def defaultLegNPV(self) -> float: ...

    def fairSpread(self) -> float: ...

    def fairUpfront(self) -> float: ...

    def isExpired(self) -> bool: ...

    def runningSpread(self) -> float: ...

    def setIsdaPricingEngine(
        self,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        discount_curve: YieldTermStructureHandle,
        numerical_fix: IsdaCdsNumericalFix = ...,
        accrual_bias: IsdaCdsAccrualBias = ...,
        forwards_in_coupon_period: IsdaCdsForwardsInCouponPeriod = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

class Currency(_native.Currency):
    def fractionSymbol(self) -> str: ...

    def fractionsPerUnit(self) -> int: ...

    def numericCode(self) -> int: ...

class Date(_native.Date):
    def dayOfMonth(self) -> int: ...

    @staticmethod
    def maxDate() -> Date: ...

    @staticmethod
    def minDate() -> Date: ...

    def serialNumber(self) -> int: ...

    @staticmethod
    def todaysDate() -> Date: ...

class DayCounter(_native.DayCounter):
    def dayCount(self, d1: Date, d2: Date) -> int: ...

    def yearFraction(self, d1: Date, d2: Date) -> float: ...

class DefaultProbabilityTermStructureHandle(_native.DefaultProbabilityTermStructureHandle):
    def defaultProbability(
        self, date: Date, extrapolate: bool = ...
    ) -> float: ...

    def hazardRate(self, date: Date, extrapolate: bool = ...) -> float: ...

    def maxDate(self) -> Date: ...

    def referenceDate(self) -> Date: ...

    def survivalProbability(
        self, date: Date | float, extrapolate: bool = ...
    ) -> float: ...

class DiscreteAveragingAsianOption(_native.DiscreteAveragingAsianOption):
    def isExpired(self) -> bool: ...

    def setChoiPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        integration_lambda: float = ...,
        max_nr_integration_steps: int = ...,
    ) -> None: ...

    def setFdPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        a_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setHestonPricingEngine(
        self, process: HestonProcess, xi_right_limit: float = ...
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

    def setTurnbullWakemanPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

class DoubleBarrierOption(_native.DoubleBarrierOption):
    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def setBinaryPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setBinomialPricingEngine(
        self, process: BlackScholesMertonProcess, time_steps: int = ...
    ) -> None: ...

    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

    def setSuoWangPricingEngine(
        self, process: BlackScholesMertonProcess, series: int = ...
    ) -> None: ...

    def setVannaVolgaPricingEngine(
        self,
        atm_vol: DeltaVolQuote,
        vol25_put: DeltaVolQuote,
        vol25_call: DeltaVolQuote,
        spot_fx: QuoteHandle,
        domestic_ts: YieldTermStructureHandle,
        foreign_ts: YieldTermStructureHandle,
        adapt_van_delta: bool = ...,
        bs_price_with_smile: float = ...,
        series: int = ...,
    ) -> None: ...

class EquityIndex(_native.EquityIndex):
    def addFixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...

    def fixingCalendar(self) -> Calendar: ...

class EquityTotalReturnSwap(_native.EquityTotalReturnSwap):
    def equityLegNPV(self) -> float: ...

    def fairMargin(self) -> float: ...

    def interestRateLegNPV(self) -> float: ...

    def isExpired(self) -> bool: ...

    def paymentDelay(self) -> int: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class EuropeanExercise(_native.EuropeanExercise):
    def lastDate(self) -> Date: ...

class EuropeanOption(_native.EuropeanOption):
    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def setBatesDetJumpPricingEngine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...

    def setBatesDoubleExpDetJumpPricingEngine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...

    def setBatesDoubleExpPricingEngine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...

    def setBatesPricingEngine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...

    def setBsmHullWhitePricingEngine(
        self,
        equity_short_rate_correlation: float,
        process: BlackScholesMertonProcess,
        model: "HullWhite",
    ) -> None: ...

    def setCashDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...

    def setCosHestonPricingEngine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...

    def setDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...

    def setExponentialFittingHestonPricingEngine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...

    def setFdBatesDividendPricingEngine(
        self,
        model: BatesModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdBatesPricingEngine(
        self,
        model: BatesModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...

    def setFdHestonDividendPricingEngine(
        self,
        model: HestonModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonHullWhitePricingEngine(
        self,
        heston_model: HestonModel,
        hw_process: HullWhiteProcess,
        equity_short_rate_correlation: float,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        r_grid: int = ...,
        damping_steps: int = ...,
        control_variate: bool = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonQuantoDividendPricingEngine(
        self,
        model: HestonModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonQuantoPricingEngine(
        self,
        model: HestonModel,
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdQuantoDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdQuantoPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    @overload
    def setFftVanillaPricingEngine(
        self, process: BlackScholesMertonProcess, log_strike_spacing: float = ...
    ) -> None: ...

    @overload
    def setFftVanillaPricingEngine(
        self, engine: FFTVanillaEngine
    ) -> None: ...

    @overload
    def setFftVarianceGammaPricingEngine(
        self, process: VarianceGammaProcess, log_strike_spacing: float = ...
    ) -> None: ...

    @overload
    def setFftVarianceGammaPricingEngine(
        self, engine: FFTVarianceGammaEngine
    ) -> None: ...

    def setGjrGarchPricingEngine(self, model: GJRGARCHModel) -> None: ...

    def setH1HWPricingEngine(
        self,
        heston_model: HestonModel,
        hull_white_model: "HullWhite",
        equity_short_rate_correlation: float,
        integration_order: int = ...,
    ) -> None: ...

    def setHestonHullWhitePricingEngine(
        self,
        heston_model: HestonModel,
        hull_white_model: "HullWhite",
        integration_order: int = ...,
    ) -> None: ...

    def setHestonPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...

    def setMcHestonHullWhitePricingEngine(
        self,
        process: HybridHestonHullWhiteProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        control_variate: bool = ...,
    ) -> None: ...

    def setMcHestonPricingEngine(
        self,
        process: HestonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int = ...,
        seed: int = ...,
        antithetic: bool = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

    def setPtdHestonPricingEngine(
        self,
        model: PiecewiseTimeDependentHestonModel,
        integration_order: int = ...,
    ) -> None: ...

    def setRoughHestonPricingEngine(
        self,
        model: RoughHestonModel,
        integration_order: int = ...,
        time_steps: int = ...,
        approximation: RoughHestonApproximation = ...,
    ) -> None: ...

    def setVarianceGammaPricingEngine(
        self, process: VarianceGammaProcess, absolute_error: float = ...
    ) -> None: ...

class EverestOption(_native.EverestOption):
    def errorEstimate(self) -> float: ...

    def isExpired(self) -> bool: ...

    def setMCPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
        max_samples: int | None = ...,
    ) -> None: ...

class EvolutionDescription(_native.EvolutionDescription):
    def evolutionTimes(self) -> list[float]: ...

    def firstAliveRate(self) -> list[int]: ...

    def numberOfRates(self) -> int: ...

    def numberOfSteps(self) -> int: ...

    def rateTaus(self) -> list[float]: ...

    def rateTimes(self) -> list[float]: ...

class FixedRateBond(_native.FixedRateBond):
    def accruedAmount(self, date: Date = ...) -> float: ...

    def bondYield(
        self,
        price: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

    @overload
    def cleanPrice(self) -> float: ...

    @overload
    def cleanPrice(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def cleanPriceFromZSpread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def settlementDate(self) -> Date: ...

    def settlementValue(self) -> float: ...

    def zSpread(
        self,
        price: float,
        discount_curve: YieldTermStructureHandle,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

class FlatVol(_native.FlatVol):
    def numberOfFactors(self) -> int: ...

    def numberOfRates(self) -> int: ...

    def numberOfSteps(self) -> int: ...

    def pseudoRoot(self, step: int) -> Matrix: ...

class FloatFloatSwap(_native.FloatFloatSwap):
    def fairSpread1(self) -> float: ...

    def fairSpread2(self) -> float: ...

    def isExpired(self) -> bool: ...

    def legBPS(self, i: int) -> float: ...

    def legNPV(self, i: int) -> float: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class FloatingRateBond(_native.FloatingRateBond):
    def accruedAmount(self, date: Date = ...) -> float: ...

    def bondYield(
        self,
        price: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

    @overload
    def cleanPrice(self) -> float: ...

    @overload
    def cleanPrice(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def cleanPriceFromZSpread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def settlementDate(self) -> Date: ...

    def settlementValue(self) -> float: ...

    def zSpread(
        self,
        price: float,
        discount_curve: YieldTermStructureHandle,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

class FloatingTypePayoff(_native.FloatingTypePayoff):
    def optionType(self) -> OptionType: ...

class Floor(_native.Floor):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def errorEstimate(self) -> float: ...

    def impliedVolatility(
        self,
        target_price: float,
        discount_curve: YieldTermStructureHandle,
        guess: float = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
        vol_type: VolatilityType = ...,
        displacement: float = ...,
    ) -> float: ...

    def maturityDate(self) -> Date: ...

    def setAnalyticCapFloorPricingEngine(
        self,
        model: HullWhite,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setBachelierPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...

    def setGaussian1dPricingEngine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setLiborForwardPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def setMcHullWhitePricingEngine(
        self,
        model: HullWhite,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...

    def setTreePricingEngine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle | None = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class ForwardRateAgreement(_native.ForwardRateAgreement):
    def fixingDate(self) -> Date: ...

    def forwardRate(self) -> InterestRate: ...

class ForwardVanillaOption(_native.ForwardVanillaOption):
    def isExpired(self) -> bool: ...

    def setHestonForwardPricingEngine(
        self, process: HestonProcess, integration_order: int = ...
    ) -> None: ...

    def setPerformancePricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class FxForward(_native.FxForward):
    def fairForwardRate(self) -> float: ...

    def forwardRate(self) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def npvSourceCurrency(self) -> float: ...

    def npvTargetCurrency(self) -> float: ...

    def paySourceCurrency(self) -> bool: ...

    @overload
    def setPricingEngine(
        self,
        source_curve: YieldTermStructureHandle,
        target_curve: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

    @overload
    def setPricingEngine(
        self,
        source_curve: YieldTermStructureHandle,
        target_curve: YieldTermStructureHandle,
        spot_fx: float,
    ) -> None: ...

    def settlementCalendar(self) -> Calendar: ...

    def settlementDate(self) -> Date: ...

    def settlementDays(self) -> int: ...

    def sourceCurrency(self) -> Currency: ...

    def sourceNominal(self) -> float: ...

    def targetCurrency(self) -> Currency: ...

    def targetNominal(self) -> float: ...

class GapPayoff(_native.GapPayoff):
    def optionType(self) -> OptionType: ...

    def secondStrike(self) -> float: ...

class GeneralStatistics(_native.GeneralStatistics):
    def errorEstimate(self) -> float: ...

class Gsr(_native.Gsr):
    def numeraireTime(self) -> float: ...

class HestonModel(_native.HestonModel):
    def endCriteria(self) -> EndCriteriaType: ...

    def setParams(self, params: list[float]) -> None: ...

class HestonModelHelper(_native.HestonModelHelper):
    def calibrationError(self) -> float: ...

    def marketValue(self) -> float: ...

    def modelValue(self) -> float: ...

    def setCosHestonPricingEngine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...

    def setExponentialFittingHestonPricingEngine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...

    def setPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...

class HimalayaOption(_native.HimalayaOption):
    def errorEstimate(self) -> float: ...

    def isExpired(self) -> bool: ...

    def setMCPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
        max_samples: int | None = ...,
    ) -> None: ...

class HolderExtensibleOption(_native.HolderExtensibleOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class IborIndex(_native.IborIndex):
    def addFixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...

    def businessDayConvention(self) -> BusinessDayConvention: ...

    def dayCounter(self) -> DayCounter: ...

    def endOfMonth(self) -> bool: ...

    def fixingCalendar(self) -> Calendar: ...

    def fixingDays(self) -> int: ...

class IndexedCashFlow(_native.IndexedCashFlow):
    def baseDate(self) -> Date: ...

    def baseFixing(self) -> float: ...

    def fixingDate(self) -> Date: ...

    def growthOnly(self) -> bool: ...

    def indexFixing(self) -> float: ...

class KahaleSmileSection(_native.KahaleSmileSection):
    def digitalOptionPrice(self, strike: float) -> float: ...

    def leftCoreStrike(self) -> float: ...

    def rightCoreStrike(self) -> float: ...

class LMMDriftCalculator(_native.LMMDriftCalculator):
    def computePlain(self, forwards: list[float]) -> list[float]: ...

    def computeReduced(self, forwards: list[float]) -> list[float]: ...

class LfmCovarianceParameterization(_native.LfmCovarianceParameterization):
    def integratedCovariance(self, t: float) -> Matrix: ...

class LiborForwardModel(_native.LiborForwardModel):
    def endCriteria(self) -> int: ...

    def setParams(self, params: list[float]) -> None: ...

class LiborForwardModelProcess(_native.LiborForwardModelProcess):
    def accrualEndTimes(self) -> list[float]: ...

    def accrualStartTimes(self) -> list[float]: ...

    def covarParam(self) -> LfmCovarianceParameterization: ...

    def discountBond(self, rates: list[float]) -> list[float]: ...

    def fixingDates(self) -> list[Date]: ...

    def fixingTimes(self) -> list[float]: ...

    def nextIndexReset(self, t: float) -> int: ...

    def setCovarParam(self, covar_param: LfmCovarianceParameterization) -> None: ...

class LinearRegression(_native.LinearRegression):
    def standardErrors(self) -> list[float]: ...

class LmExponentialCorrelationModel(_native.LmExponentialCorrelationModel):
    def pseudoSqrt(self, t: float) -> Matrix: ...

class LmExtLinearExponentialVolModel(_native.LmExtLinearExponentialVolModel):
    def integratedVariance(self, i: int, j: int, u: float) -> float: ...

class LmLinearExponentialCorrelationModel(_native.LmLinearExponentialCorrelationModel):
    def pseudoSqrt(self, t: float) -> Matrix: ...

class MargrabeOption(_native.MargrabeOption):
    def isExpired(self) -> bool: ...

    def setAmericanPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...

    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...

class MarkovFunctional(_native.MarkovFunctional):
    def modelOutputs(self) -> MarkovFunctionalModelOutputs: ...

    def modelSettings(self) -> MarkovFunctionalModelSettings: ...

    def numeraireDate(self) -> Date: ...

    def numeraireTime(self) -> float: ...

class MarkovFunctionalModelSettings(_native.MarkovFunctionalModelSettings):
    def addAdjustment(self, a: int) -> MarkovFunctionalModelSettings: ...

    def removeAdjustment(self, a: int) -> MarkovFunctionalModelSettings: ...

    def withAdjustments(self, a: int) -> MarkovFunctionalModelSettings: ...

    def withDigitalGap(self, d: float) -> MarkovFunctionalModelSettings: ...

    def withGaussHermitePoints(self, n: int) -> MarkovFunctionalModelSettings: ...

    def withLowerRateBound(self, l: float) -> MarkovFunctionalModelSettings: ...

    def withMarketRateAccuracy(self, a: float) -> MarkovFunctionalModelSettings: ...

    def withSmileMoneynessCheckpoints(
        self, m: list[float]
    ) -> MarkovFunctionalModelSettings: ...

    def withUpperRateBound(self, u: float) -> MarkovFunctionalModelSettings: ...

    def withYGridPoints(self, n: int) -> MarkovFunctionalModelSettings: ...

    def withYStdDevs(self, s: float) -> MarkovFunctionalModelSettings: ...

class MfStateProcess(_native.MfStateProcess):
    def stdDeviation(self, t0: float, x0: float, dt: float) -> float: ...

class MultipleResetsSwap(_native.MultipleResetsSwap):
    def averagingMethod(self) -> RateAveraging: ...

    def fairRate(self) -> float: ...

    def fairSpread(self) -> float: ...

    def fixedLegNPV(self) -> float: ...

    def fixedRate(self) -> float: ...

    def floatingLegNPV(self) -> float: ...

    def isExpired(self) -> bool: ...

    def resetsPerCoupon(self) -> int: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class MultiplicativePriceSeasonality(_native.MultiplicativePriceSeasonality):
    def seasonalityBaseDate(self) -> Date: ...

    def seasonalityFactor(self, date: Date) -> float: ...

    def seasonalityFactors(self) -> list[float]: ...

class NonstandardSwap(_native.NonstandardSwap):
    def fixedDayCount(self) -> DayCounter: ...

    def fixedNominal(self) -> list[float]: ...

    def fixedRate(self) -> list[float]: ...

    def fixedSchedule(self) -> Schedule: ...

    def floatingDayCount(self) -> DayCounter: ...

    def floatingNominal(self) -> list[float]: ...

    def floatingSchedule(self) -> Schedule: ...

    def iborIndex(self) -> IborIndex: ...

    def paymentConvention(self) -> BusinessDayConvention: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class NonstandardSwaption(_native.NonstandardSwaption):
    def isExpired(self) -> bool: ...

    def setGaussian1dPricingEngine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
    ) -> None: ...

    def settlementMethod(self) -> SettlementMethod: ...

    def settlementType(self) -> SettlementType: ...

    def underlyingSwap(self) -> NonstandardSwap: ...

class OvernightIndex(_native.OvernightIndex):
    def addFixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...

    def dayCounter(self) -> DayCounter: ...

    def fixingCalendar(self) -> Calendar: ...

    def fixingDays(self) -> int: ...

class OvernightIndexFuture(_native.OvernightIndexFuture):
    def convexityAdjustment(self) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def valueDate(self) -> Date: ...

class OvernightIndexedSwap(_native.OvernightIndexedSwap):
    def fairRate(self) -> float: ...

    def fairSpread(self) -> float: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class PagodaOption(_native.PagodaOption):
    def errorEstimate(self) -> float: ...

    def isExpired(self) -> bool: ...

    def setMCPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
        max_samples: int | None = ...,
    ) -> None: ...

class PartialTimeBarrierOption(_native.PartialTimeBarrierOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class PercentageStrikePayoff(_native.PercentageStrikePayoff):
    def optionType(self) -> OptionType: ...

class PerpetualFutures(_native.PerpetualFutures):
    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self,
        domestic_curve: YieldTermStructureHandle,
        foreign_curve: YieldTermStructureHandle,
        asset_spot: QuoteHandle,
        funding_times: Sequence[float],
        funding_rates: Sequence[float],
        interest_rate_diffs: Sequence[float],
        funding_interp_type: PerpetualFuturesInterpType = ...,
        max_t: float = ...,
    ) -> None: ...

class PlainVanillaPayoff(_native.PlainVanillaPayoff):
    def optionType(self) -> OptionType: ...

class QuantoBarrierOption(_native.QuantoBarrierOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...

class QuantoDoubleBarrierOption(_native.QuantoDoubleBarrierOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...

class QuantoForwardVanillaOption(_native.QuantoForwardVanillaOption):
    def isExpired(self) -> bool: ...

    def setPerformancePricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...

    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...

class QuantoVanillaOption(_native.QuantoVanillaOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...

class Quote(_native.Quote):
    def isValid(self) -> bool: ...

class QuoteHandle(_native.QuoteHandle):
    def currentLink(self) -> Quote: ...

class RelinkableQuoteHandle(_native.RelinkableQuoteHandle):
    def currentLink(self) -> Quote: ...

    def linkTo(self, value: Quote) -> None: ...

class RelinkableYoYInflationTermStructureHandle(_native.RelinkableYoYInflationTermStructureHandle):
    def asHandle(self) -> YoYInflationTermStructureHandle: ...

    def hasSeasonality(self) -> bool: ...

    def linkTo(self, handle: YoYInflationTermStructureHandle) -> None: ...

    def setSeasonality(self, seasonality: object | None = ...) -> None: ...

class RelinkableZeroInflationTermStructureHandle(_native.RelinkableZeroInflationTermStructureHandle):
    def asHandle(self) -> ZeroInflationTermStructureHandle: ...

    def hasSeasonality(self) -> bool: ...

    def linkTo(self, handle: ZeroInflationTermStructureHandle) -> None: ...

    def setSeasonality(self, seasonality: object | None = ...) -> None: ...

class Schedule(_native.Schedule):
    def endDate(self) -> Date: ...

    def startDate(self) -> Date: ...

class SimpleChooserOption(_native.SimpleChooserOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class SimpleQuote(_native.SimpleQuote):
    def isValid(self) -> bool: ...

    def setValue(self, value: float) -> float: ...

class SmileSectionUtils(_native.SmileSectionUtils):
    def arbitragefreeIndices(self) -> tuple[int, int]: ...

    def arbitragefreeRegion(self) -> tuple[float, float]: ...

    def atmLevel(self) -> float: ...

class SoftBarrierOption(_native.SoftBarrierOption):
    def impliedVolatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class Stock(_native.Stock):
    def isExpired(self) -> bool: ...

class SuperFundPayoff(_native.SuperFundPayoff):
    def optionType(self) -> OptionType: ...

    def secondStrike(self) -> float: ...

class SuperSharePayoff(_native.SuperSharePayoff):
    def cashPayoff(self) -> float: ...

    def optionType(self) -> OptionType: ...

    def secondStrike(self) -> float: ...

class Swap(_native.Swap):
    def isExpired(self) -> bool: ...

    def numberOfLegs(self) -> int: ...

    def setCmsCouponPricer(self, pricer: CmsCouponPricer) -> None: ...

    def setPricingEngine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

class SwapIndex(_native.SwapIndex):
    def addFixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...

    def dayCounter(self) -> DayCounter: ...

    def fixingCalendar(self) -> Calendar: ...

    def fixingDays(self) -> int: ...

    def valueDate(self, fixing_date: Date) -> Date: ...

class Swaption(_native.Swaption):
    def impliedVolatility(
        self,
        target_price: float,
        discount_curve: YieldTermStructureHandle,
        guess: float = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
        vol_type: VolatilityType = ...,
        displacement: float = ...,
        price_type: SwaptionPriceType = ...,
    ) -> float: ...

    def isExpired(self) -> bool: ...

    def setBachelierPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...

    def setFdG2PricingEngine(
        self,
        model: G2,
        t_grid: int = ...,
        x_grid: int = ...,
        y_grid: int = ...,
        damping_steps: int = ...,
        inv_eps: float = ...,
    ) -> None: ...

    def setFdHullWhitePricingEngine(
        self,
        model: HullWhite,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
    ) -> None: ...

    def setG2PricingEngine(
        self,
        model: G2,
        range: float = ...,
        intervals: int = ...,
    ) -> None: ...

    def setG2TreePricingEngine(
        self, model: G2, time_steps: int = ...
    ) -> None: ...

    def setGaussian1dJamshidianPricingEngine(self, model: Gsr) -> None: ...

    def setGaussian1dPricingEngine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
    ) -> None: ...

    def setJamshidianPricingEngine(self, model: HullWhite) -> None: ...

    def setLfmPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

    def setPricingEngine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...

    def setTreePricingEngine(
        self, model: HullWhite, time_steps: int = ...
    ) -> None: ...

    def settlementMethod(self) -> SettlementMethod: ...

    def settlementType(self) -> SettlementType: ...

class SwaptionHelper(_native.SwaptionHelper):
    def calibrationError(self) -> float: ...

    def marketValue(self) -> float: ...

    def modelValue(self) -> float: ...

    def setGaussian1dPricingEngine(
        self,
        model: MarkovFunctional,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
    ) -> None: ...

    def setLfmPricingEngine(
        self,
        model: LiborForwardModel,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...

class SwingExercise(_native.SwingExercise):
    def lastDate(self) -> Date: ...

class TwoAssetBarrierOption(_native.TwoAssetBarrierOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        rho: QuoteHandle | float,
    ) -> None: ...

class TwoAssetCorrelationOption(_native.TwoAssetCorrelationOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: QuoteHandle | float,
    ) -> None: ...

class VanillaForwardPayoff(_native.VanillaForwardPayoff):
    def optionType(self) -> OptionType: ...

class VanillaOption(_native.VanillaOption):
    def errorEstimate(self) -> float: ...

    def setBatesDetJumpPricingEngine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...

    def setBatesDoubleExpDetJumpPricingEngine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...

    def setBatesDoubleExpPricingEngine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...

    def setBatesPricingEngine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...

    def setBinomialPricingEngine(
        self, process: BlackScholesMertonProcess, steps: int = ...
    ) -> None: ...

    def setBjerksundStenslandPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setCashDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...

    def setCevPricingEngine(
        self,
        f0: float,
        alpha: float,
        beta: float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

    def setCosHestonPricingEngine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...

    def setDigitalAmericanKoPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setDigitalAmericanPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...

    def setDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...

    def setExponentialFittingHestonPricingEngine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...

    def setFdBatesDividendPricingEngine(
        self,
        model: BatesModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdBatesPricingEngine(
        self,
        model: BatesModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdCevPricingEngine(
        self,
        f0: float,
        alpha: float,
        beta: float,
        discount_curve: YieldTermStructureHandle,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scaling_factor: float = ...,
        eps: float = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdCirPricingEngine(
        self,
        cir_process: CoxIngersollRossProcess,
        bs_process: BlackScholesMertonProcess,
        equity_rate_correlation: float,
        t_grid: int = ...,
        x_grid: int = ...,
        r_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...

    def setFdHestonDividendPricingEngine(
        self,
        model: HestonModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonHullWhitePricingEngine(
        self,
        heston_model: HestonModel,
        hw_process: HullWhiteProcess,
        equity_short_rate_correlation: float,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        r_grid: int = ...,
        damping_steps: int = ...,
        control_variate: bool = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonQuantoDividendPricingEngine(
        self,
        model: HestonModel,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdHestonQuantoPricingEngine(
        self,
        model: HestonModel,
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdQuantoDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdQuantoPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setFdShoutPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setGjrGarchPricingEngine(self, model: GJRGARCHModel) -> None: ...

    def setHestonPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...

    def setJumpDiffusionPricingEngine(
        self,
        process: Merton76Process,
        relative_accuracy: float = ...,
        max_iterations: int = ...,
    ) -> None: ...

    def setMcHestonHullWhitePricingEngine(
        self,
        process: HybridHestonHullWhiteProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        control_variate: bool = ...,
    ) -> None: ...

    def setMcHestonPricingEngine(
        self,
        process: HestonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int = ...,
        seed: int = ...,
        antithetic: bool = ...,
    ) -> None: ...

    def setPdfHestonPricingEngine(
        self,
        model: HestonModel,
        gauss_lobatto_eps: float = ...,
        gauss_lobatto_integration_order: int = ...,
    ) -> None: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

    def setPtdHestonPricingEngine(
        self,
        model: PiecewiseTimeDependentHestonModel,
        integration_order: int = ...,
    ) -> None: ...

    def setRoughHestonPricingEngine(
        self,
        model: RoughHestonModel,
        integration_order: int = ...,
        time_steps: int = ...,
        approximation: RoughHestonApproximation = ...,
    ) -> None: ...

class VanillaStorageOption(_native.VanillaStorageOption):
    def isExpired(self) -> bool: ...

    def setFdPricingEngine(
        self,
        process: ExtendedOrnsteinUhlenbeckProcess,
        risk_free_ts: YieldTermStructureHandle,
        t_grid: int = ...,
        x_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        process: ExtendedOrnsteinUhlenbeckProcess,
        risk_free_ts: YieldTermStructureHandle,
        t_grid: int = ...,
        x_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

class VanillaSwap(_native.VanillaSwap):
    def fairRate(self) -> float: ...

    def fairSpread(self) -> float: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class VanillaSwingOption(_native.VanillaSwingOption):
    def isExpired(self) -> bool: ...

    def setFdPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

class VarianceOption(_native.VarianceOption):
    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setIntegralHestonPricingEngine(self, process: HestonProcess) -> None: ...

    def startDate(self) -> Date: ...

class VarianceSwap(_native.VarianceSwap):
    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setMcPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int | None = ...,
        required_tolerance: float | None = ...,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...

    def setReplicatingPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        call_strikes: Sequence[float],
        put_strikes: Sequence[float],
        dk: float = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class WriterExtensibleOption(_native.WriterExtensibleOption):
    def isExpired(self) -> bool: ...

    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...

class YearOnYearInflationSwap(_native.YearOnYearInflationSwap):
    def fairRate(self) -> float: ...

    def fairSpread(self) -> float: ...

    def fixedLegNPV(self) -> float: ...

    def fixedRate(self) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

    def startDate(self) -> Date: ...

    def yoyLegNPV(self) -> float: ...

class YieldTermStructureHandle(_native.YieldTermStructureHandle):
    def referenceDate(self) -> Date: ...

    def zeroRate(
        self,
        date: Date,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency = ...,
        extrapolate: bool = ...,
    ) -> InterestRate: ...

class YoYCapFloorTermPriceSurfaceHandle(_native.YoYCapFloorTermPriceSurfaceHandle):
    def YoYTS(self) -> YoYInflationTermStructureHandle: ...

    def atmYoYRate(self, date: Date, extrapolate: bool = ...) -> float: ...

    def atmYoYSwapDateRates(self) -> tuple[list[Date], list[float]]: ...

    def atmYoYSwapRate(
        self, date: Date, extrapolate: bool = ...
    ) -> float: ...

    def atmYoYSwapTimeRates(self) -> tuple[list[float], list[float]]: ...

    def capPrice(self, tenor: Period, strike: float) -> float: ...

    def capStrikes(self) -> list[float]: ...

    def floorPrice(self, tenor: Period, strike: float) -> float: ...

    def floorStrikes(self) -> list[float]: ...

    def observationLag(self) -> Period: ...

class YoYInflationCap(_native.YoYInflationCap):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class YoYInflationCapFloor(_native.YoYInflationCapFloor):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class YoYInflationCollar(_native.YoYInflationCollar):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class YoYInflationCoupon(_native.YoYInflationCoupon):
    def adjustedFixing(self) -> float: ...

    def fixingDate(self) -> Date: ...

    def indexFixing(self) -> float: ...

    def setPricer(self, pricer: InflationCouponPricer) -> None: ...

    def yoyIndex(self) -> YoYInflationIndex: ...

class YoYInflationFloor(_native.YoYInflationFloor):
    def atmRate(self, discount_curve: YieldTermStructureHandle) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

    def startDate(self) -> Date: ...

class YoYInflationTermStructureHandle(_native.YoYInflationTermStructureHandle):
    def baseDate(self) -> Date: ...

    def baseRate(self) -> float: ...

    def hasSeasonality(self) -> bool: ...

    def maxDate(self) -> Date: ...

    def referenceDate(self) -> Date: ...

    def setSeasonality(self, seasonality: object | None = ...) -> None: ...

    def yoyRate(self, date: Date, extrapolate: bool = ...) -> float: ...

class ZeroCouponBond(_native.ZeroCouponBond):
    def accruedAmount(self, date: Date = ...) -> float: ...

    def bondYield(
        self,
        price: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

    @overload
    def cleanPrice(self) -> float: ...

    @overload
    def cleanPrice(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def cleanPriceFromZSpread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...

    def dirtyPrice(self) -> float: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def settlementDate(self) -> Date: ...

    def settlementValue(self) -> float: ...

    def zSpread(
        self,
        price: float,
        discount_curve: YieldTermStructureHandle,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
        accuracy: float = ...,
        max_evaluations: int = ...,
        guess: float = ...,
        price_type: BondPriceType = ...,
    ) -> float: ...

class ZeroCouponInflationSwap(_native.ZeroCouponInflationSwap):
    def fairRate(self) -> float: ...

    def fixedLeg(self) -> list[object]: ...

    def fixedLegNPV(self) -> float: ...

    def fixedRate(self) -> float: ...

    def inflationLeg(self) -> list[object]: ...

    def inflationLegNPV(self) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

    def startDate(self) -> Date: ...

class ZeroCouponSwap(_native.ZeroCouponSwap):
    def baseNominal(self) -> float: ...

    def fairFixedPayment(self) -> float: ...

    def fairFixedRate(self, day_counter: DayCounter) -> float: ...

    def fixedLegNPV(self) -> float: ...

    def fixedPayment(self) -> float: ...

    def floatingLegNPV(self) -> float: ...

    def isExpired(self) -> bool: ...

    def maturityDate(self) -> Date: ...

    def setPricingEngine(self, discount_curve: YieldTermStructureHandle) -> None: ...

    def startDate(self) -> Date: ...

class ZeroInflationCashFlow(_native.ZeroInflationCashFlow):
    def observationInterpolation(self) -> CPIInterpolationType: ...

    def zeroInflationIndex(self) -> ZeroInflationIndex: ...

class ZeroInflationIndex(_native.ZeroInflationIndex):
    def addFixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...

    def availabilityLag(self) -> Period: ...

    def clearFixings(self) -> None: ...

    def lastFixingDate(self) -> Date: ...

class ZeroInflationTermStructureHandle(_native.ZeroInflationTermStructureHandle):
    def baseDate(self) -> Date: ...

    def hasSeasonality(self) -> bool: ...

    def maxDate(self) -> Date: ...

    def referenceDate(self) -> Date: ...

    def setSeasonality(self, seasonality: object | None = ...) -> None: ...

    def zeroRate(self, date: Date, extrapolate: bool = ...) -> float: ...

# END GENERATED COMPAT ALIASES

def __getattr__(name: str) -> Any: ...
