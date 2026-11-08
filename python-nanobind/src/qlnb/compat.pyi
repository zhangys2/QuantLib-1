"""Type stub for qlnb.compat.

qlnb.compat installs SWIG-style camelCase aliases onto the native classes at
import time.  The native stub (_qlnb.pyi) describes only the native snake_case
API, so the aliases are declared here, on subclasses, for code that imports
qlnb.compat.  Names compat defines that are not declared here are typed Any.
"""

from typing import Any, Iterable, Sequence, overload

import qlnb._qlnb as _native
from qlnb._qlnb import *  # noqa: F403

class BarrierOption(_native.BarrierOption):
    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
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
    def setFdPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
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
    ) -> None: ...
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

class BasketOption(_native.BasketOption):
    def setKirkPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def setStulzPricingEngine(
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
    def setSingleFactorPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
    ) -> None: ...
    def setDengLiZhouPricingEngine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
    ) -> None: ...
    def setBjerksundStenslandPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def setPearsonPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def setOperatorSplittingPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        order: OperatorSplittingOrder = ...,
    ) -> None: ...
    def setGaussianCopulaPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        n_points: int = ...,
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
    def isExpired(self) -> bool: ...

class CallableFixedRateBond(_native.CallableFixedRateBond):
    def impliedVolatility(
        self,
        target_price: BondPrice,
        discount_curve: YieldTermStructureHandle,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...
    def cleanPriceOAS(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
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
    def effectiveConvexity(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        bump: float = ...,
    ) -> float: ...
    def setBlackPricingEngine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

class CallableZeroCouponBond(_native.CallableZeroCouponBond):
    def impliedVolatility(
        self,
        target_price: BondPrice,
        discount_curve: YieldTermStructureHandle,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...
    def cleanPriceOAS(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
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
    def effectiveConvexity(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        bump: float = ...,
    ) -> float: ...
    def setBlackPricingEngine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

class CliquetOption(_native.CliquetOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def setPerformancePricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def isExpired(self) -> bool: ...

class ComplexChooserOption(_native.ComplexChooserOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

class ConvertibleFixedCouponBond(_native.ConvertibleFixedCouponBond):
    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

class ConvertibleFloatingRateBond(_native.ConvertibleFloatingRateBond):
    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

class ConvertibleZeroCouponBond(_native.ConvertibleZeroCouponBond):
    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

class DiscreteAveragingAsianOption(_native.DiscreteAveragingAsianOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def setTurnbullWakemanPricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
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
    def isExpired(self) -> bool: ...

class DoubleBarrierOption(_native.DoubleBarrierOption):
    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

class EuropeanOption(_native.EuropeanOption):
    def setDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...
    def setCashDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
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
    def setFdQuantoPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        quanto_helper: FdmQuantoHelper,
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
    def setMcHestonPricingEngine(
        self,
        process: HestonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int = ...,
        seed: int = ...,
        antithetic: bool = ...,
    ) -> None: ...
    def setHestonPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
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
    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
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
    def setBatesPricingEngine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...
    def setVarianceGammaPricingEngine(
        self, process: VarianceGammaProcess, absolute_error: float = ...
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
    def setBatesDetJumpPricingEngine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpPricingEngine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpDetJumpPricingEngine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...

class ForwardVanillaOption(_native.ForwardVanillaOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def setPerformancePricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def isExpired(self) -> bool: ...

class HestonModelHelper(_native.HestonModelHelper):
    def setPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
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

class HimalayaOption(_native.HimalayaOption):
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
    def errorEstimate(self) -> float: ...
    def isExpired(self) -> bool: ...

class HolderExtensibleOption(_native.HolderExtensibleOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

class MargrabeOption(_native.MargrabeOption):
    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def setAmericanPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class PagodaOption(_native.PagodaOption):
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
    def errorEstimate(self) -> float: ...
    def isExpired(self) -> bool: ...

class PercentageStrikePayoff(_native.PercentageStrikePayoff):
    def optionType(self) -> OptionType: ...

class QuantoBarrierOption(_native.QuantoBarrierOption):
    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class QuantoDoubleBarrierOption(_native.QuantoDoubleBarrierOption):
    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class QuantoForwardVanillaOption(_native.QuantoForwardVanillaOption):
    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def setPerformancePricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class QuantoVanillaOption(_native.QuantoVanillaOption):
    def setPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class SimpleChooserOption(_native.SimpleChooserOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

class TwoAssetBarrierOption(_native.TwoAssetBarrierOption):
    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        rho: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class TwoAssetCorrelationOption(_native.TwoAssetCorrelationOption):
    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class VanillaOption(_native.VanillaOption):
    def setDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...
    def setCashDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
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
    def setFdQuantoPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        quanto_helper: FdmQuantoHelper,
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
    def setMcHestonPricingEngine(
        self,
        process: HestonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int = ...,
        seed: int = ...,
        antithetic: bool = ...,
    ) -> None: ...
    def setHestonPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
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
    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
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
    def setBatesPricingEngine(
        self, model: BatesModel, integration_order: int = ...
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
    def setBatesDetJumpPricingEngine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpPricingEngine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpDetJumpPricingEngine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...

class VarianceSwap(_native.VarianceSwap):
    def setReplicatingPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        call_strikes: Sequence[float],
        put_strikes: Sequence[float],
        dk: float = ...,
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
    def isExpired(self) -> bool: ...
    def startDate(self) -> Date: ...
    def maturityDate(self) -> Date: ...

class WriterExtensibleOption(_native.WriterExtensibleOption):
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

def __getattr__(name: str) -> Any: ...
