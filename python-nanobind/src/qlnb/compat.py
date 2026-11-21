"""SWIG-flavored compatibility helpers for qlnb.

This module is a **best-effort shim**, not full QuantLib-SWIG parity. Prefer the
native snake_case qlnb API for new code. Import style:

    import qlnb.compat as ql
    # or
    from qlnb import compat as ql

Useful aliases include module-level months (`ql.May`), `ql.Option.Put`,
camelCase method aliases (`setPricingEngine`, `cleanPrice`), and
`Settings.instance().evaluationDate`.
"""

from __future__ import annotations

from typing import Any

import qlnb as _ql
from qlnb import *  # noqa: F403

# Re-export version from the native package.
__version__ = _ql.__version__

# ---------------------------------------------------------------------------
# Module-level month aliases (SWIG: ql.May)
# ---------------------------------------------------------------------------
January = _ql.Month.January
February = _ql.Month.February
March = _ql.Month.March
April = _ql.Month.April
May = _ql.Month.May
June = _ql.Month.June
July = _ql.Month.July
August = _ql.Month.August
September = _ql.Month.September
October = _ql.Month.October
November = _ql.Month.November
December = _ql.Month.December


# ---------------------------------------------------------------------------
# Option.Put / Option.Call (SWIG nests under Option, qlnb uses OptionType)
# ---------------------------------------------------------------------------
class Option:
    """SWIG-style Option.Put / Option.Call namespace."""

    Put = _ql.OptionType.Put
    Call = _ql.OptionType.Call


# ---------------------------------------------------------------------------
# Settings.evaluationDate camelCase property
# ---------------------------------------------------------------------------
class _SettingsProxy:
    """Thin proxy adding SWIG-style ``evaluationDate`` to Settings."""

    __slots__ = ("_settings",)

    def __init__(self, settings: Any) -> None:
        self._settings = settings

    @property
    def evaluation_date(self) -> Any:
        return self._settings.evaluation_date

    @evaluation_date.setter
    def evaluation_date(self, date: Any) -> None:
        self._settings.evaluation_date = date

    @property
    def evaluationDate(self) -> Any:  # noqa: N802 — SWIG alias
        return self._settings.evaluation_date

    @evaluationDate.setter
    def evaluationDate(self, date: Any) -> None:  # noqa: N802 — SWIG alias
        self._settings.evaluation_date = date

    def anchor_evaluation_date(self) -> None:
        self._settings.anchor_evaluation_date()

    def reset_evaluation_date(self) -> None:
        self._settings.reset_evaluation_date()

    def anchorEvaluationDate(self) -> None:  # noqa: N802
        self._settings.anchor_evaluation_date()

    def resetEvaluationDate(self) -> None:  # noqa: N802
        self._settings.reset_evaluation_date()


class Settings:
    """SWIG-style Settings with ``evaluationDate`` alias."""

    @staticmethod
    def instance() -> _SettingsProxy:
        return _SettingsProxy(_ql.Settings.instance())


# Module-level Settings helpers matching SWIG naming.
def evaluationDate() -> Any:  # noqa: N802
    """Return the current evaluation date (SWIG-style helper name)."""
    return _ql.get_evaluation_date()


# ---------------------------------------------------------------------------
# CamelCase method aliases on concrete classes
# ---------------------------------------------------------------------------
def _install_aliases() -> None:
    aliases = (
        ('AbcdCalibration', 'endCriteria', 'end_criteria'),
        ('AbcdFunction', 'instantaneousCovariance', 'instantaneous_covariance'),
        ('AbcdFunction', 'instantaneousVariance', 'instantaneous_variance'),
        ('AbcdFunction', 'instantaneousVolatility', 'instantaneous_volatility'),
        ('AbcdFunction', 'longTermVolatility', 'long_term_volatility'),
        ('AbcdFunction', 'maximumVolatility', 'maximum_volatility'),
        ('AbcdFunction', 'shortTermVolatility', 'short_term_volatility'),
        ('AbcdVol', 'numberOfFactors', 'number_of_factors'),
        ('AbcdVol', 'numberOfRates', 'number_of_rates'),
        ('AbcdVol', 'numberOfSteps', 'number_of_steps'),
        ('AbcdVol', 'pseudoRoot', 'pseudo_root'),
        ('AmericanExercise', 'lastDate', 'last_date'),
        ('AmortizingFixedRateBond', 'accruedAmount', 'accrued_amount'),
        ('AmortizingFixedRateBond', 'bondYield', 'bond_yield'),
        ('AmortizingFixedRateBond', 'cashflowAmounts', 'cashflow_amounts'),
        ('AmortizingFixedRateBond', 'cleanPrice', 'clean_price'),
        ('AmortizingFixedRateBond', 'dayCounter', 'day_counter'),
        ('AmortizingFixedRateBond', 'dirtyPrice', 'dirty_price'),
        ('AmortizingFixedRateBond', 'maturityDate', 'maturity_date'),
        ('AmortizingFixedRateBond', 'setPricingEngine', 'set_pricing_engine'),
        ('AmortizingFixedRateBond', 'settlementDate', 'settlement_date'),
        ('AmortizingFixedRateBond', 'settlementValue', 'settlement_value'),
        ('AmortizingFloatingRateBond', 'accruedAmount', 'accrued_amount'),
        ('AmortizingFloatingRateBond', 'bondYield', 'bond_yield'),
        ('AmortizingFloatingRateBond', 'cashflowAmounts', 'cashflow_amounts'),
        ('AmortizingFloatingRateBond', 'cleanPrice', 'clean_price'),
        ('AmortizingFloatingRateBond', 'dirtyPrice', 'dirty_price'),
        ('AmortizingFloatingRateBond', 'maturityDate', 'maturity_date'),
        ('AmortizingFloatingRateBond', 'setPricingEngine', 'set_pricing_engine'),
        ('AmortizingFloatingRateBond', 'settlementDate', 'settlement_date'),
        ('AmortizingFloatingRateBond', 'settlementValue', 'settlement_value'),
        ('AssetOrNothingPayoff', 'optionType', 'option_type'),
        ('AssetSwap', 'cleanPrice', 'clean_price'),
        ('AssetSwap', 'fairCleanPrice', 'fair_clean_price'),
        ('AssetSwap', 'fairNonParRepayment', 'fair_non_par_repayment'),
        ('AssetSwap', 'fairSpread', 'fair_spread'),
        ('AssetSwap', 'floatingLegBPS', 'floating_leg_BPS'),
        ('AssetSwap', 'floatingLegNPV', 'floating_leg_NPV'),
        ('AssetSwap', 'isExpired', 'is_expired'),
        ('AssetSwap', 'nonParRepayment', 'non_par_repayment'),
        ('AssetSwap', 'parSwap', 'par_swap'),
        ('AssetSwap', 'payBondCoupon', 'pay_bond_coupon'),
        ('AssetSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('BMAIndex', 'addFixing', 'add_fixing'),
        ('BMAIndex', 'dayCounter', 'day_counter'),
        ('BMAIndex', 'fixingCalendar', 'fixing_calendar'),
        ('BMAIndex', 'fixingDays', 'fixing_days'),
        ('BMAIndex', 'isValidFixingDate', 'is_valid_fixing_date'),
        ('BMASwap', 'bmaLegBPS', 'bma_leg_BPS'),
        ('BMASwap', 'bmaLegNPV', 'bma_leg_NPV'),
        ('BMASwap', 'fairLiborFraction', 'fair_libor_fraction'),
        ('BMASwap', 'fairLiborSpread', 'fair_libor_spread'),
        ('BMASwap', 'isExpired', 'is_expired'),
        ('BMASwap', 'liborFraction', 'libor_fraction'),
        ('BMASwap', 'liborLegBPS', 'libor_leg_BPS'),
        ('BMASwap', 'liborLegNPV', 'libor_leg_NPV'),
        ('BMASwap', 'liborSpread', 'libor_spread'),
        ('BMASwap', 'setPricingEngine', 'set_pricing_engine'),
        ('BarrierOption', 'errorEstimate', 'error_estimate'),
        ('BarrierOption', 'impliedVolatility', 'implied_volatility'),
        ('BarrierOption', 'setBinaryPricingEngine', 'set_binary_pricing_engine'),
        ('BarrierOption', 'setBinomialPricingEngine', 'set_binomial_pricing_engine'),
        ('BarrierOption', 'setFdDividendPricingEngine', 'set_fd_dividend_pricing_engine'),
        (
            'BarrierOption',
            'setFdHestonDividendPricingEngine',
            'set_fd_heston_dividend_pricing_engine',
        ),
        ('BarrierOption', 'setFdHestonPricingEngine', 'set_fd_heston_pricing_engine'),
        ('BarrierOption', 'setFdPricingEngine', 'set_fd_pricing_engine'),
        ('BarrierOption', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('BarrierOption', 'setPerturbativePricingEngine', 'set_perturbative_pricing_engine'),
        ('BarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('BarrierOption', 'setVannaVolgaPricingEngine', 'set_vanna_volga_pricing_engine'),
        ('BasketOption', 'isExpired', 'is_expired'),
        (
            'BasketOption',
            'setBjerksundStenslandPricingEngine',
            'set_bjerksund_stensland_pricing_engine',
        ),
        ('BasketOption', 'setChoiPricingEngine', 'set_choi_pricing_engine'),
        ('BasketOption', 'setDengLiZhouPricingEngine', 'set_deng_li_zhou_pricing_engine'),
        ('BasketOption', 'setFd2dPricingEngine', 'set_fd_2d_pricing_engine'),
        ('BasketOption', 'setFdNdimPricingEngine', 'set_fd_ndim_pricing_engine'),
        ('BasketOption', 'setGaussianCopulaPricingEngine', 'set_gaussian_copula_pricing_engine'),
        ('BasketOption', 'setKirkPricingEngine', 'set_kirk_pricing_engine'),
        ('BasketOption', 'setMCAmericanPricingEngine', 'set_mc_american_pricing_engine'),
        ('BasketOption', 'setMCEuropeanPricingEngine', 'set_mc_european_pricing_engine'),
        (
            'BasketOption',
            'setOperatorSplittingPricingEngine',
            'set_operator_splitting_pricing_engine',
        ),
        ('BasketOption', 'setPearsonPricingEngine', 'set_pearson_pricing_engine'),
        ('BasketOption', 'setSingleFactorPricingEngine', 'set_single_factor_pricing_engine'),
        ('BasketOption', 'setStulzPricingEngine', 'set_stulz_pricing_engine'),
        ('BatesDetJumpModel', 'jumpIntensity', 'jump_intensity'),
        ('BatesDetJumpModel', 'kappaLambda', 'kappa_lambda'),
        ('BatesDetJumpModel', 'thetaLambda', 'theta_lambda'),
        ('BatesDoubleExpDetJumpModel', 'jumpIntensity', 'jump_intensity'),
        ('BatesDoubleExpDetJumpModel', 'kappaLambda', 'kappa_lambda'),
        ('BatesDoubleExpDetJumpModel', 'nuDown', 'nu_down'),
        ('BatesDoubleExpDetJumpModel', 'nuUp', 'nu_up'),
        ('BatesDoubleExpDetJumpModel', 'thetaLambda', 'theta_lambda'),
        ('BatesDoubleExpModel', 'jumpIntensity', 'jump_intensity'),
        ('BatesDoubleExpModel', 'nuDown', 'nu_down'),
        ('BatesDoubleExpModel', 'nuUp', 'nu_up'),
        ('BatesModel', 'jumpIntensity', 'jump_intensity'),
        ('BatesProcess', 'jumpIntensity', 'jump_intensity'),
        ('BermudanExercise', 'lastDate', 'last_date'),
        ('BondForward', 'cleanForwardPrice', 'clean_forward_price'),
        ('BondForward', 'forwardPrice', 'forward_price'),
        ('BondForward', 'forwardValue', 'forward_value'),
        ('BondForward', 'isExpired', 'is_expired'),
        ('BondForward', 'settlementDate', 'settlement_date'),
        ('BondForward', 'spotIncome', 'spot_income'),
        ('BondForward', 'spotValue', 'spot_value'),
        ('CPIBond', 'baseCPI', 'base_CPI'),
        ('CPIBond', 'cleanPrice', 'clean_price'),
        ('CPIBond', 'dirtyPrice', 'dirty_price'),
        ('CPIBond', 'isExpired', 'is_expired'),
        ('CPIBond', 'maturityDate', 'maturity_date'),
        ('CPIBond', 'setPricingEngine', 'set_pricing_engine'),
        ('CPIBond', 'settlementDate', 'settlement_date'),
        ('CPICapFloor', 'fixingDate', 'fixing_date'),
        ('CPICapFloor', 'isExpired', 'is_expired'),
        ('CPICapFloor', 'payDate', 'pay_date'),
        ('CPICapFloor', 'setPricingEngine', 'set_pricing_engine'),
        ('CPICapFloorTermPriceSurfaceHandle', 'atmRate', 'atm_rate'),
        ('CPICapFloorTermPriceSurfaceHandle', 'capPrice', 'cap_price'),
        ('CPICapFloorTermPriceSurfaceHandle', 'floorPrice', 'floor_price'),
        ('CPICashFlow', 'cpiIndex', 'cpi_index'),
        ('CPICashFlow', 'observationDate', 'observation_date'),
        ('CPICashFlow', 'observationLag', 'observation_lag'),
        ('CPICoupon', 'adjustedIndexGrowth', 'adjusted_index_growth'),
        ('CPICoupon', 'baseCPI', 'base_CPI'),
        ('CPICoupon', 'capletPrice', 'caplet_price'),
        ('CPICoupon', 'capletRate', 'caplet_rate'),
        ('CPICoupon', 'fixedRate', 'fixed_rate'),
        ('CPICoupon', 'fixingDate', 'fixing_date'),
        ('CPICoupon', 'floorletPrice', 'floorlet_price'),
        ('CPICoupon', 'floorletRate', 'floorlet_rate'),
        ('CPICoupon', 'indexFixing', 'index_fixing'),
        ('CPICoupon', 'indexRatio', 'index_ratio'),
        ('CPICoupon', 'setPricer', 'set_pricer'),
        ('CPICouponPricer', 'capletPrice', 'caplet_price'),
        ('CPICouponPricer', 'capletRate', 'caplet_rate'),
        ('CPICouponPricer', 'capletVolatility', 'caplet_volatility'),
        ('CPICouponPricer', 'floorletPrice', 'floorlet_price'),
        ('CPICouponPricer', 'floorletRate', 'floorlet_rate'),
        ('CPICouponPricer', 'setCapletVolatility', 'set_caplet_volatility'),
        ('CPISwap', 'baseCPI', 'base_CPI'),
        ('CPISwap', 'fairRate', 'fair_rate'),
        ('CPISwap', 'fairSpread', 'fair_spread'),
        ('CPISwap', 'fixedLegNPV', 'fixed_leg_NPV'),
        ('CPISwap', 'fixedRate', 'fixed_rate'),
        ('CPISwap', 'floatLegNPV', 'float_leg_NPV'),
        ('CPISwap', 'inflationNominal', 'inflation_nominal'),
        ('CPISwap', 'isExpired', 'is_expired'),
        ('CPISwap', 'setPricingEngine', 'set_pricing_engine'),
        ('CPIVolatilitySurfaceHandle', 'indexIsInterpolated', 'index_is_interpolated'),
        ('CPIVolatilitySurfaceHandle', 'observationLag', 'observation_lag'),
        ('CPIVolatilitySurfaceHandle', 'totalVariance', 'total_variance'),
        ('Calendar', 'isBusinessDay', 'is_business_day'),
        ('Calendar', 'isHoliday', 'is_holiday'),
        ('CallableFixedRateBond', 'OAS', 'oas'),
        ('CallableFixedRateBond', 'cleanPrice', 'clean_price'),
        ('CallableFixedRateBond', 'cleanPriceOAS', 'clean_price_oas'),
        ('CallableFixedRateBond', 'dirtyPrice', 'dirty_price'),
        ('CallableFixedRateBond', 'effectiveConvexity', 'effective_convexity'),
        ('CallableFixedRateBond', 'effectiveDuration', 'effective_duration'),
        ('CallableFixedRateBond', 'impliedVolatility', 'implied_volatility'),
        ('CallableFixedRateBond', 'maturityDate', 'maturity_date'),
        ('CallableFixedRateBond', 'setBlackPricingEngine', 'set_black_pricing_engine'),
        ('CallableFixedRateBond', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('CallableFixedRateBond', 'settlementDate', 'settlement_date'),
        ('CallableZeroCouponBond', 'OAS', 'oas'),
        ('CallableZeroCouponBond', 'cleanPrice', 'clean_price'),
        ('CallableZeroCouponBond', 'cleanPriceOAS', 'clean_price_oas'),
        ('CallableZeroCouponBond', 'dirtyPrice', 'dirty_price'),
        ('CallableZeroCouponBond', 'effectiveConvexity', 'effective_convexity'),
        ('CallableZeroCouponBond', 'effectiveDuration', 'effective_duration'),
        ('CallableZeroCouponBond', 'impliedVolatility', 'implied_volatility'),
        ('CallableZeroCouponBond', 'maturityDate', 'maturity_date'),
        ('CallableZeroCouponBond', 'setBlackPricingEngine', 'set_black_pricing_engine'),
        ('CallableZeroCouponBond', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('CallableZeroCouponBond', 'settlementDate', 'settlement_date'),
        ('Cap', 'atmRate', 'atm_rate'),
        ('Cap', 'errorEstimate', 'error_estimate'),
        ('Cap', 'impliedVolatility', 'implied_volatility'),
        ('Cap', 'maturityDate', 'maturity_date'),
        ('Cap', 'setAnalyticCapFloorPricingEngine', 'set_analytic_cap_floor_pricing_engine'),
        ('Cap', 'setBachelierPricingEngine', 'set_bachelier_pricing_engine'),
        ('Cap', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('Cap', 'setLiborForwardPricingEngine', 'set_libor_forward_pricing_engine'),
        ('Cap', 'setMcHullWhitePricingEngine', 'set_mc_hull_white_pricing_engine'),
        ('Cap', 'setPricingEngine', 'set_pricing_engine'),
        ('Cap', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('Cap', 'startDate', 'start_date'),
        ('CapFloor', 'atmRate', 'atm_rate'),
        ('CapFloor', 'errorEstimate', 'error_estimate'),
        ('CapFloor', 'impliedVolatility', 'implied_volatility'),
        ('CapFloor', 'maturityDate', 'maturity_date'),
        ('CapFloor', 'setAnalyticCapFloorPricingEngine', 'set_analytic_cap_floor_pricing_engine'),
        ('CapFloor', 'setBachelierPricingEngine', 'set_bachelier_pricing_engine'),
        ('CapFloor', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('CapFloor', 'setLiborForwardPricingEngine', 'set_libor_forward_pricing_engine'),
        ('CapFloor', 'setMcHullWhitePricingEngine', 'set_mc_hull_white_pricing_engine'),
        ('CapFloor', 'setPricingEngine', 'set_pricing_engine'),
        ('CapFloor', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('CapFloor', 'startDate', 'start_date'),
        ('CapHelper', 'calibrationError', 'calibration_error'),
        ('CapHelper', 'marketValue', 'market_value'),
        ('CapHelper', 'modelValue', 'model_value'),
        ('CapHelper', 'setLfmPricingEngine', 'set_lfm_pricing_engine'),
        ('CappedFlooredCmsSpreadCoupon', 'setPricer', 'set_pricer'),
        ('CappedFlooredYoYInflationCoupon', 'effectiveCap', 'effective_cap'),
        ('CappedFlooredYoYInflationCoupon', 'effectiveFloor', 'effective_floor'),
        ('CappedFlooredYoYInflationCoupon', 'isCapped', 'is_capped'),
        ('CappedFlooredYoYInflationCoupon', 'isFloored', 'is_floored'),
        ('CappedFlooredYoYInflationCoupon', 'setPricer', 'set_pricer'),
        ('CappedFlooredYoYInflationCoupon', 'underlyingRate', 'underlying_rate'),
        ('CashOrNothingPayoff', 'cashPayoff', 'cash_payoff'),
        ('CashOrNothingPayoff', 'optionType', 'option_type'),
        ('CdsOption', 'atmRate', 'atm_rate'),
        ('CdsOption', 'impliedVolatility', 'implied_volatility'),
        ('CdsOption', 'isExpired', 'is_expired'),
        ('CdsOption', 'riskyAnnuity', 'risky_annuity'),
        ('CdsOption', 'setPricingEngine', 'set_pricing_engine'),
        ('CliquetOption', 'isExpired', 'is_expired'),
        ('CliquetOption', 'setPerformancePricingEngine', 'set_performance_pricing_engine'),
        ('CliquetOption', 'setPricingEngine', 'set_pricing_engine'),
        ('CmsCoupon', 'accrualEndDate', 'accrual_end_date'),
        ('CmsCoupon', 'accrualStartDate', 'accrual_start_date'),
        ('CmsCoupon', 'setPricer', 'set_pricer'),
        ('CmsRateBond', 'accruedAmount', 'accrued_amount'),
        ('CmsRateBond', 'bondYield', 'bond_yield'),
        ('CmsRateBond', 'cleanPrice', 'clean_price'),
        ('CmsRateBond', 'cleanPriceFromZSpread', 'clean_price_from_z_spread'),
        ('CmsRateBond', 'dirtyPrice', 'dirty_price'),
        ('CmsRateBond', 'maturityDate', 'maturity_date'),
        ('CmsRateBond', 'setCmsCouponPricer', 'set_cms_coupon_pricer'),
        ('CmsRateBond', 'setPricingEngine', 'set_pricing_engine'),
        ('CmsRateBond', 'settlementDate', 'settlement_date'),
        ('CmsRateBond', 'settlementValue', 'settlement_value'),
        ('CmsRateBond', 'zSpread', 'z_spread'),
        ('CmsSpreadCoupon', 'fixingDate', 'fixing_date'),
        ('CmsSpreadCoupon', 'setPricer', 'set_pricer'),
        ('Collar', 'atmRate', 'atm_rate'),
        ('Collar', 'errorEstimate', 'error_estimate'),
        ('Collar', 'impliedVolatility', 'implied_volatility'),
        ('Collar', 'maturityDate', 'maturity_date'),
        ('Collar', 'setAnalyticCapFloorPricingEngine', 'set_analytic_cap_floor_pricing_engine'),
        ('Collar', 'setBachelierPricingEngine', 'set_bachelier_pricing_engine'),
        ('Collar', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('Collar', 'setLiborForwardPricingEngine', 'set_libor_forward_pricing_engine'),
        ('Collar', 'setMcHullWhitePricingEngine', 'set_mc_hull_white_pricing_engine'),
        ('Collar', 'setPricingEngine', 'set_pricing_engine'),
        ('Collar', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('Collar', 'startDate', 'start_date'),
        ('ComplexChooserOption', 'isExpired', 'is_expired'),
        ('ComplexChooserOption', 'setPricingEngine', 'set_pricing_engine'),
        ('CompositeInstrument', 'isExpired', 'is_expired'),
        ('CompoundOption', 'isExpired', 'is_expired'),
        ('CompoundOption', 'setPricingEngine', 'set_pricing_engine'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'fairPaySpread', 'fair_pay_spread'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'fairRecSpread', 'fair_rec_spread'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'inCcyLegBPS', 'in_ccy_leg_bps'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'inCcyLegNPV', 'in_ccy_leg_npv'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'legBPS', 'leg_bps'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'legNPV', 'leg_npv'),
        ('ConstNotionalCrossCurrencyBasisSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'fairRate', 'fair_rate'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'fairSpread', 'fair_spread'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'inCcyLegBPS', 'in_ccy_leg_bps'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'inCcyLegNPV', 'in_ccy_leg_npv'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'legBPS', 'leg_bps'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'legNPV', 'leg_npv'),
        ('ConstNotionalCrossCurrencyFixedVsFloatingSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('ConstNotionalCrossCurrencySwap', 'inCcyLegBPS', 'in_ccy_leg_bps'),
        ('ConstNotionalCrossCurrencySwap', 'inCcyLegNPV', 'in_ccy_leg_npv'),
        ('ConstNotionalCrossCurrencySwap', 'isExpired', 'is_expired'),
        ('ConstNotionalCrossCurrencySwap', 'legBPS', 'leg_bps'),
        ('ConstNotionalCrossCurrencySwap', 'legNPV', 'leg_npv'),
        ('ConstNotionalCrossCurrencySwap', 'setPricingEngine', 'set_pricing_engine'),
        ('ContinuousAveragingAsianOption', 'setHestonPricingEngine', 'set_heston_pricing_engine'),
        ('ContinuousAveragingAsianOption', 'setLevyPricingEngine', 'set_levy_pricing_engine'),
        ('ContinuousAveragingAsianOption', 'setPricingEngine', 'set_pricing_engine'),
        ('ContinuousAveragingAsianOption', 'setVecerPricingEngine', 'set_vecer_pricing_engine'),
        ('ContinuousFixedLookbackOption', 'errorEstimate', 'error_estimate'),
        ('ContinuousFixedLookbackOption', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('ContinuousFixedLookbackOption', 'setPricingEngine', 'set_pricing_engine'),
        ('ContinuousFloatingLookbackOption', 'errorEstimate', 'error_estimate'),
        ('ContinuousFloatingLookbackOption', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('ContinuousFloatingLookbackOption', 'setPricingEngine', 'set_pricing_engine'),
        ('ContinuousPartialFixedLookbackOption', 'errorEstimate', 'error_estimate'),
        ('ContinuousPartialFixedLookbackOption', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('ContinuousPartialFixedLookbackOption', 'setPricingEngine', 'set_pricing_engine'),
        ('ContinuousPartialFloatingLookbackOption', 'errorEstimate', 'error_estimate'),
        ('ContinuousPartialFloatingLookbackOption', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('ContinuousPartialFloatingLookbackOption', 'setPricingEngine', 'set_pricing_engine'),
        ('ConvertibleFixedCouponBond', 'cleanPrice', 'clean_price'),
        ('ConvertibleFixedCouponBond', 'conversionRatio', 'conversion_ratio'),
        ('ConvertibleFixedCouponBond', 'dirtyPrice', 'dirty_price'),
        ('ConvertibleFixedCouponBond', 'maturityDate', 'maturity_date'),
        ('ConvertibleFixedCouponBond', 'setBinomialPricingEngine', 'set_binomial_pricing_engine'),
        ('ConvertibleFixedCouponBond', 'settlementDate', 'settlement_date'),
        ('ConvertibleFloatingRateBond', 'cleanPrice', 'clean_price'),
        ('ConvertibleFloatingRateBond', 'conversionRatio', 'conversion_ratio'),
        ('ConvertibleFloatingRateBond', 'dirtyPrice', 'dirty_price'),
        ('ConvertibleFloatingRateBond', 'maturityDate', 'maturity_date'),
        ('ConvertibleFloatingRateBond', 'setBinomialPricingEngine', 'set_binomial_pricing_engine'),
        ('ConvertibleFloatingRateBond', 'settlementDate', 'settlement_date'),
        ('ConvertibleZeroCouponBond', 'cleanPrice', 'clean_price'),
        ('ConvertibleZeroCouponBond', 'conversionRatio', 'conversion_ratio'),
        ('ConvertibleZeroCouponBond', 'dirtyPrice', 'dirty_price'),
        ('ConvertibleZeroCouponBond', 'maturityDate', 'maturity_date'),
        ('ConvertibleZeroCouponBond', 'setBinomialPricingEngine', 'set_binomial_pricing_engine'),
        ('ConvertibleZeroCouponBond', 'settlementDate', 'settlement_date'),
        ('CreditDefaultSwap', 'couponLegNPV', 'coupon_leg_NPV'),
        ('CreditDefaultSwap', 'defaultLegNPV', 'default_leg_NPV'),
        ('CreditDefaultSwap', 'fairSpread', 'fair_spread'),
        ('CreditDefaultSwap', 'fairUpfront', 'fair_upfront'),
        ('CreditDefaultSwap', 'isExpired', 'is_expired'),
        ('CreditDefaultSwap', 'runningSpread', 'running_spread'),
        ('CreditDefaultSwap', 'setIsdaPricingEngine', 'set_isda_pricing_engine'),
        ('CreditDefaultSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('Currency', 'fractionSymbol', 'fraction_symbol'),
        ('Currency', 'fractionsPerUnit', 'fractions_per_unit'),
        ('Currency', 'numericCode', 'numeric_code'),
        ('Date', 'dayOfMonth', 'day_of_month'),
        ('Date', 'maxDate', 'max_date'),
        ('Date', 'minDate', 'min_date'),
        ('Date', 'serialNumber', 'serial_number'),
        ('Date', 'todaysDate', 'todays_date'),
        ('DayCounter', 'dayCount', 'day_count'),
        ('DayCounter', 'yearFraction', 'year_fraction'),
        ('DefaultProbabilityTermStructureHandle', 'defaultProbability', 'default_probability'),
        ('DefaultProbabilityTermStructureHandle', 'hazardRate', 'hazard_rate'),
        ('DefaultProbabilityTermStructureHandle', 'maxDate', 'max_date'),
        ('DefaultProbabilityTermStructureHandle', 'referenceDate', 'reference_date'),
        ('DefaultProbabilityTermStructureHandle', 'survivalProbability', 'survival_probability'),
        ('DiscreteAveragingAsianOption', 'isExpired', 'is_expired'),
        ('DiscreteAveragingAsianOption', 'setChoiPricingEngine', 'set_choi_pricing_engine'),
        ('DiscreteAveragingAsianOption', 'setFdPricingEngine', 'set_fd_pricing_engine'),
        ('DiscreteAveragingAsianOption', 'setHestonPricingEngine', 'set_heston_pricing_engine'),
        ('DiscreteAveragingAsianOption', 'setPricingEngine', 'set_pricing_engine'),
        (
            'DiscreteAveragingAsianOption',
            'setTurnbullWakemanPricingEngine',
            'set_turnbull_wakeman_pricing_engine',
        ),
        ('DoubleBarrierOption', 'errorEstimate', 'error_estimate'),
        ('DoubleBarrierOption', 'impliedVolatility', 'implied_volatility'),
        ('DoubleBarrierOption', 'setBinaryPricingEngine', 'set_binary_pricing_engine'),
        ('DoubleBarrierOption', 'setBinomialPricingEngine', 'set_binomial_pricing_engine'),
        ('DoubleBarrierOption', 'setFdHestonPricingEngine', 'set_fd_heston_pricing_engine'),
        ('DoubleBarrierOption', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('DoubleBarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('DoubleBarrierOption', 'setSuoWangPricingEngine', 'set_suo_wang_pricing_engine'),
        ('DoubleBarrierOption', 'setVannaVolgaPricingEngine', 'set_vanna_volga_pricing_engine'),
        ('EquityIndex', 'addFixing', 'add_fixing'),
        ('EquityIndex', 'fixingCalendar', 'fixing_calendar'),
        ('EquityTotalReturnSwap', 'equityLegNPV', 'equity_leg_NPV'),
        ('EquityTotalReturnSwap', 'fairMargin', 'fair_margin'),
        ('EquityTotalReturnSwap', 'interestRateLegNPV', 'interest_rate_leg_NPV'),
        ('EquityTotalReturnSwap', 'isExpired', 'is_expired'),
        ('EquityTotalReturnSwap', 'paymentDelay', 'payment_delay'),
        ('EquityTotalReturnSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('EuropeanExercise', 'lastDate', 'last_date'),
        ('EuropeanOption', 'errorEstimate', 'error_estimate'),
        ('EuropeanOption', 'impliedVolatility', 'implied_volatility'),
        ('EuropeanOption', 'setBatesDetJumpPricingEngine', 'set_bates_det_jump_pricing_engine'),
        (
            'EuropeanOption',
            'setBatesDoubleExpDetJumpPricingEngine',
            'set_bates_double_exp_det_jump_pricing_engine',
        ),
        ('EuropeanOption', 'setBatesDoubleExpPricingEngine', 'set_bates_double_exp_pricing_engine'),
        ('EuropeanOption', 'setBatesPricingEngine', 'set_bates_pricing_engine'),
        ('EuropeanOption', 'setBsmHullWhitePricingEngine', 'set_bsm_hull_white_pricing_engine'),
        ('EuropeanOption', 'setCashDividendPricingEngine', 'set_cash_dividend_pricing_engine'),
        ('EuropeanOption', 'setCosHestonPricingEngine', 'set_cos_heston_pricing_engine'),
        ('EuropeanOption', 'setDividendPricingEngine', 'set_dividend_pricing_engine'),
        (
            'EuropeanOption',
            'setExponentialFittingHestonPricingEngine',
            'set_exponential_fitting_heston_pricing_engine',
        ),
        (
            'EuropeanOption',
            'setFdBatesDividendPricingEngine',
            'set_fd_bates_dividend_pricing_engine',
        ),
        ('EuropeanOption', 'setFdBatesPricingEngine', 'set_fd_bates_pricing_engine'),
        ('EuropeanOption', 'setFdDividendPricingEngine', 'set_fd_dividend_pricing_engine'),
        (
            'EuropeanOption',
            'setFdHestonDividendPricingEngine',
            'set_fd_heston_dividend_pricing_engine',
        ),
        (
            'EuropeanOption',
            'setFdHestonHullWhitePricingEngine',
            'set_fd_heston_hull_white_pricing_engine',
        ),
        ('EuropeanOption', 'setFdHestonPricingEngine', 'set_fd_heston_pricing_engine'),
        (
            'EuropeanOption',
            'setFdHestonQuantoDividendPricingEngine',
            'set_fd_heston_quanto_dividend_pricing_engine',
        ),
        ('EuropeanOption', 'setFdHestonQuantoPricingEngine', 'set_fd_heston_quanto_pricing_engine'),
        (
            'EuropeanOption',
            'setFdQuantoDividendPricingEngine',
            'set_fd_quanto_dividend_pricing_engine',
        ),
        ('EuropeanOption', 'setFdQuantoPricingEngine', 'set_fd_quanto_pricing_engine'),
        ('EuropeanOption', 'setFftVanillaPricingEngine', 'set_fft_vanilla_pricing_engine'),
        (
            'EuropeanOption',
            'setFftVarianceGammaPricingEngine',
            'set_fft_variance_gamma_pricing_engine',
        ),
        ('EuropeanOption', 'setGjrGarchPricingEngine', 'set_gjr_garch_pricing_engine'),
        ('EuropeanOption', 'setH1HWPricingEngine', 'set_h1_hw_pricing_engine'),
        (
            'EuropeanOption',
            'setHestonHullWhitePricingEngine',
            'set_heston_hull_white_pricing_engine',
        ),
        ('EuropeanOption', 'setHestonPricingEngine', 'set_heston_pricing_engine'),
        (
            'EuropeanOption',
            'setMcHestonHullWhitePricingEngine',
            'set_mc_heston_hull_white_pricing_engine',
        ),
        ('EuropeanOption', 'setMcHestonPricingEngine', 'set_mc_heston_pricing_engine'),
        ('EuropeanOption', 'setPricingEngine', 'set_pricing_engine'),
        ('EuropeanOption', 'setPtdHestonPricingEngine', 'set_ptd_heston_pricing_engine'),
        ('EuropeanOption', 'setRoughHestonPricingEngine', 'set_rough_heston_pricing_engine'),
        ('EuropeanOption', 'setVarianceGammaPricingEngine', 'set_variance_gamma_pricing_engine'),
        ('EverestOption', 'errorEstimate', 'error_estimate'),
        ('EverestOption', 'isExpired', 'is_expired'),
        ('EverestOption', 'setMCPricingEngine', 'set_mc_pricing_engine'),
        ('EverestOption', 'yield', 'yield_'),
        ('EvolutionDescription', 'evolutionTimes', 'evolution_times'),
        ('EvolutionDescription', 'firstAliveRate', 'first_alive_rate'),
        ('EvolutionDescription', 'numberOfRates', 'number_of_rates'),
        ('EvolutionDescription', 'numberOfSteps', 'number_of_steps'),
        ('EvolutionDescription', 'rateTaus', 'rate_taus'),
        ('EvolutionDescription', 'rateTimes', 'rate_times'),
        ('FixedRateBond', 'accruedAmount', 'accrued_amount'),
        ('FixedRateBond', 'bondYield', 'bond_yield'),
        ('FixedRateBond', 'cleanPrice', 'clean_price'),
        ('FixedRateBond', 'cleanPriceFromZSpread', 'clean_price_from_z_spread'),
        ('FixedRateBond', 'dirtyPrice', 'dirty_price'),
        ('FixedRateBond', 'maturityDate', 'maturity_date'),
        ('FixedRateBond', 'setPricingEngine', 'set_pricing_engine'),
        ('FixedRateBond', 'settlementDate', 'settlement_date'),
        ('FixedRateBond', 'settlementValue', 'settlement_value'),
        ('FixedRateBond', 'zSpread', 'z_spread'),
        ('FlatVol', 'numberOfFactors', 'number_of_factors'),
        ('FlatVol', 'numberOfRates', 'number_of_rates'),
        ('FlatVol', 'numberOfSteps', 'number_of_steps'),
        ('FlatVol', 'pseudoRoot', 'pseudo_root'),
        ('FloatFloatSwap', 'fairSpread1', 'fair_spread1'),
        ('FloatFloatSwap', 'fairSpread2', 'fair_spread2'),
        ('FloatFloatSwap', 'isExpired', 'is_expired'),
        ('FloatFloatSwap', 'legBPS', 'leg_BPS'),
        ('FloatFloatSwap', 'legNPV', 'leg_NPV'),
        ('FloatFloatSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('FloatingRateBond', 'accruedAmount', 'accrued_amount'),
        ('FloatingRateBond', 'bondYield', 'bond_yield'),
        ('FloatingRateBond', 'cleanPrice', 'clean_price'),
        ('FloatingRateBond', 'cleanPriceFromZSpread', 'clean_price_from_z_spread'),
        ('FloatingRateBond', 'dirtyPrice', 'dirty_price'),
        ('FloatingRateBond', 'maturityDate', 'maturity_date'),
        ('FloatingRateBond', 'setPricingEngine', 'set_pricing_engine'),
        ('FloatingRateBond', 'settlementDate', 'settlement_date'),
        ('FloatingRateBond', 'settlementValue', 'settlement_value'),
        ('FloatingRateBond', 'zSpread', 'z_spread'),
        ('FloatingTypePayoff', 'optionType', 'option_type'),
        ('Floor', 'atmRate', 'atm_rate'),
        ('Floor', 'errorEstimate', 'error_estimate'),
        ('Floor', 'impliedVolatility', 'implied_volatility'),
        ('Floor', 'maturityDate', 'maturity_date'),
        ('Floor', 'setAnalyticCapFloorPricingEngine', 'set_analytic_cap_floor_pricing_engine'),
        ('Floor', 'setBachelierPricingEngine', 'set_bachelier_pricing_engine'),
        ('Floor', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('Floor', 'setLiborForwardPricingEngine', 'set_libor_forward_pricing_engine'),
        ('Floor', 'setMcHullWhitePricingEngine', 'set_mc_hull_white_pricing_engine'),
        ('Floor', 'setPricingEngine', 'set_pricing_engine'),
        ('Floor', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('Floor', 'startDate', 'start_date'),
        ('ForwardRateAgreement', 'fixingDate', 'fixing_date'),
        ('ForwardRateAgreement', 'forwardRate', 'forward_rate'),
        ('ForwardVanillaOption', 'isExpired', 'is_expired'),
        (
            'ForwardVanillaOption',
            'setHestonForwardPricingEngine',
            'set_heston_forward_pricing_engine',
        ),
        ('ForwardVanillaOption', 'setPerformancePricingEngine', 'set_performance_pricing_engine'),
        ('ForwardVanillaOption', 'setPricingEngine', 'set_pricing_engine'),
        ('FxForward', 'fairForwardRate', 'fair_forward_rate'),
        ('FxForward', 'forwardRate', 'forward_rate'),
        ('FxForward', 'isExpired', 'is_expired'),
        ('FxForward', 'maturityDate', 'maturity_date'),
        ('FxForward', 'npvSourceCurrency', 'npv_source_currency'),
        ('FxForward', 'npvTargetCurrency', 'npv_target_currency'),
        ('FxForward', 'paySourceCurrency', 'pay_source_currency'),
        ('FxForward', 'setPricingEngine', 'set_pricing_engine'),
        ('FxForward', 'settlementCalendar', 'settlement_calendar'),
        ('FxForward', 'settlementDate', 'settlement_date'),
        ('FxForward', 'settlementDays', 'settlement_days'),
        ('FxForward', 'sourceCurrency', 'source_currency'),
        ('FxForward', 'sourceNominal', 'source_nominal'),
        ('FxForward', 'targetCurrency', 'target_currency'),
        ('FxForward', 'targetNominal', 'target_nominal'),
        ('GapPayoff', 'optionType', 'option_type'),
        ('GapPayoff', 'secondStrike', 'second_strike'),
        ('GeneralStatistics', 'errorEstimate', 'error_estimate'),
        ('Gsr', 'numeraireTime', 'numeraire_time'),
        ('HestonModel', 'endCriteria', 'end_criteria'),
        ('HestonModel', 'setParams', 'set_params'),
        ('HestonModelHelper', 'calibrationError', 'calibration_error'),
        ('HestonModelHelper', 'marketValue', 'market_value'),
        ('HestonModelHelper', 'modelValue', 'model_value'),
        ('HestonModelHelper', 'setCosHestonPricingEngine', 'set_cos_heston_pricing_engine'),
        (
            'HestonModelHelper',
            'setExponentialFittingHestonPricingEngine',
            'set_exponential_fitting_heston_pricing_engine',
        ),
        ('HestonModelHelper', 'setPricingEngine', 'set_pricing_engine'),
        ('HimalayaOption', 'errorEstimate', 'error_estimate'),
        ('HimalayaOption', 'isExpired', 'is_expired'),
        ('HimalayaOption', 'setMCPricingEngine', 'set_mc_pricing_engine'),
        ('HolderExtensibleOption', 'isExpired', 'is_expired'),
        ('HolderExtensibleOption', 'setPricingEngine', 'set_pricing_engine'),
        ('IborIndex', 'addFixing', 'add_fixing'),
        ('IborIndex', 'businessDayConvention', 'business_day_convention'),
        ('IborIndex', 'dayCounter', 'day_counter'),
        ('IborIndex', 'endOfMonth', 'end_of_month'),
        ('IborIndex', 'fixingCalendar', 'fixing_calendar'),
        ('IborIndex', 'fixingDays', 'fixing_days'),
        ('IndexedCashFlow', 'baseDate', 'base_date'),
        ('IndexedCashFlow', 'baseFixing', 'base_fixing'),
        ('IndexedCashFlow', 'fixingDate', 'fixing_date'),
        ('IndexedCashFlow', 'growthOnly', 'growth_only'),
        ('IndexedCashFlow', 'indexFixing', 'index_fixing'),
        ('KahaleSmileSection', 'digitalOptionPrice', 'digital_option_price'),
        ('KahaleSmileSection', 'leftCoreStrike', 'left_core_strike'),
        ('KahaleSmileSection', 'rightCoreStrike', 'right_core_strike'),
        ('LMMDriftCalculator', 'computePlain', 'compute_plain'),
        ('LMMDriftCalculator', 'computeReduced', 'compute_reduced'),
        ('LfmCovarianceParameterization', 'integratedCovariance', 'integrated_covariance'),
        ('LiborForwardModel', 'endCriteria', 'end_criteria'),
        ('LiborForwardModel', 'setParams', 'set_params'),
        ('LiborForwardModelProcess', 'accrualEndTimes', 'accrual_end_times'),
        ('LiborForwardModelProcess', 'accrualStartTimes', 'accrual_start_times'),
        ('LiborForwardModelProcess', 'covarParam', 'covar_param'),
        ('LiborForwardModelProcess', 'discountBond', 'discount_bond'),
        ('LiborForwardModelProcess', 'fixingDates', 'fixing_dates'),
        ('LiborForwardModelProcess', 'fixingTimes', 'fixing_times'),
        ('LiborForwardModelProcess', 'nextIndexReset', 'next_index_reset'),
        ('LiborForwardModelProcess', 'setCovarParam', 'set_covar_param'),
        ('LinearRegression', 'standardErrors', 'standard_errors'),
        ('LmExponentialCorrelationModel', 'pseudoSqrt', 'pseudo_sqrt'),
        ('LmExtLinearExponentialVolModel', 'integratedVariance', 'integrated_variance'),
        ('LmLinearExponentialCorrelationModel', 'pseudoSqrt', 'pseudo_sqrt'),
        ('MargrabeOption', 'isExpired', 'is_expired'),
        ('MargrabeOption', 'setAmericanPricingEngine', 'set_american_pricing_engine'),
        ('MargrabeOption', 'setPricingEngine', 'set_pricing_engine'),
        ('MarkovFunctional', 'modelOutputs', 'model_outputs'),
        ('MarkovFunctional', 'modelSettings', 'model_settings'),
        ('MarkovFunctional', 'numeraireDate', 'numeraire_date'),
        ('MarkovFunctional', 'numeraireTime', 'numeraire_time'),
        ('MarkovFunctionalModelSettings', 'addAdjustment', 'add_adjustment'),
        ('MarkovFunctionalModelSettings', 'removeAdjustment', 'remove_adjustment'),
        ('MarkovFunctionalModelSettings', 'withAdjustments', 'with_adjustments'),
        ('MarkovFunctionalModelSettings', 'withDigitalGap', 'with_digital_gap'),
        ('MarkovFunctionalModelSettings', 'withGaussHermitePoints', 'with_gauss_hermite_points'),
        ('MarkovFunctionalModelSettings', 'withLowerRateBound', 'with_lower_rate_bound'),
        ('MarkovFunctionalModelSettings', 'withMarketRateAccuracy', 'with_market_rate_accuracy'),
        (
            'MarkovFunctionalModelSettings',
            'withSmileMoneynessCheckpoints',
            'with_smile_moneyness_checkpoints',
        ),
        ('MarkovFunctionalModelSettings', 'withUpperRateBound', 'with_upper_rate_bound'),
        ('MarkovFunctionalModelSettings', 'withYGridPoints', 'with_y_grid_points'),
        ('MarkovFunctionalModelSettings', 'withYStdDevs', 'with_y_std_devs'),
        ('MfStateProcess', 'stdDeviation', 'std_deviation'),
        ('MultipleResetsSwap', 'averagingMethod', 'averaging_method'),
        ('MultipleResetsSwap', 'fairRate', 'fair_rate'),
        ('MultipleResetsSwap', 'fairSpread', 'fair_spread'),
        ('MultipleResetsSwap', 'fixedLegNPV', 'fixed_leg_NPV'),
        ('MultipleResetsSwap', 'fixedRate', 'fixed_rate'),
        ('MultipleResetsSwap', 'floatingLegNPV', 'floating_leg_NPV'),
        ('MultipleResetsSwap', 'isExpired', 'is_expired'),
        ('MultipleResetsSwap', 'resetsPerCoupon', 'resets_per_coupon'),
        ('MultipleResetsSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('MultiplicativePriceSeasonality', 'seasonalityBaseDate', 'seasonality_base_date'),
        ('MultiplicativePriceSeasonality', 'seasonalityFactor', 'seasonality_factor'),
        ('MultiplicativePriceSeasonality', 'seasonalityFactors', 'seasonality_factors'),
        ('NonstandardSwap', 'fixedDayCount', 'fixed_day_count'),
        ('NonstandardSwap', 'fixedNominal', 'fixed_nominal'),
        ('NonstandardSwap', 'fixedRate', 'fixed_rate'),
        ('NonstandardSwap', 'fixedSchedule', 'fixed_schedule'),
        ('NonstandardSwap', 'floatingDayCount', 'floating_day_count'),
        ('NonstandardSwap', 'floatingNominal', 'floating_nominal'),
        ('NonstandardSwap', 'floatingSchedule', 'floating_schedule'),
        ('NonstandardSwap', 'iborIndex', 'ibor_index'),
        ('NonstandardSwap', 'paymentConvention', 'payment_convention'),
        ('NonstandardSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('NonstandardSwaption', 'isExpired', 'is_expired'),
        ('NonstandardSwaption', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('NonstandardSwaption', 'settlementMethod', 'settlement_method'),
        ('NonstandardSwaption', 'settlementType', 'settlement_type'),
        ('NonstandardSwaption', 'underlyingSwap', 'underlying_swap'),
        ('OvernightIndex', 'addFixing', 'add_fixing'),
        ('OvernightIndex', 'dayCounter', 'day_counter'),
        ('OvernightIndex', 'fixingCalendar', 'fixing_calendar'),
        ('OvernightIndex', 'fixingDays', 'fixing_days'),
        ('OvernightIndexFuture', 'convexityAdjustment', 'convexity_adjustment'),
        ('OvernightIndexFuture', 'isExpired', 'is_expired'),
        ('OvernightIndexFuture', 'maturityDate', 'maturity_date'),
        ('OvernightIndexFuture', 'valueDate', 'value_date'),
        ('OvernightIndexedSwap', 'fairRate', 'fair_rate'),
        ('OvernightIndexedSwap', 'fairSpread', 'fair_spread'),
        ('OvernightIndexedSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('PagodaOption', 'errorEstimate', 'error_estimate'),
        ('PagodaOption', 'isExpired', 'is_expired'),
        ('PagodaOption', 'setMCPricingEngine', 'set_mc_pricing_engine'),
        ('PartialTimeBarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('PercentageStrikePayoff', 'optionType', 'option_type'),
        ('PerpetualFutures', 'isExpired', 'is_expired'),
        ('PerpetualFutures', 'setPricingEngine', 'set_pricing_engine'),
        ('PlainVanillaPayoff', 'optionType', 'option_type'),
        ('QuantoBarrierOption', 'isExpired', 'is_expired'),
        ('QuantoBarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('QuantoDoubleBarrierOption', 'isExpired', 'is_expired'),
        ('QuantoDoubleBarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('QuantoForwardVanillaOption', 'isExpired', 'is_expired'),
        (
            'QuantoForwardVanillaOption',
            'setPerformancePricingEngine',
            'set_performance_pricing_engine',
        ),
        ('QuantoForwardVanillaOption', 'setPricingEngine', 'set_pricing_engine'),
        ('QuantoVanillaOption', 'isExpired', 'is_expired'),
        ('QuantoVanillaOption', 'setPricingEngine', 'set_pricing_engine'),
        ('Quote', 'isValid', 'is_valid'),
        ('QuoteHandle', 'currentLink', 'current_link'),
        ('RelinkableQuoteHandle', 'currentLink', 'current_link'),
        ('RelinkableQuoteHandle', 'linkTo', 'link_to'),
        ('RelinkableYoYInflationTermStructureHandle', 'asHandle', 'as_handle'),
        ('RelinkableYoYInflationTermStructureHandle', 'hasSeasonality', 'has_seasonality'),
        ('RelinkableYoYInflationTermStructureHandle', 'linkTo', 'link_to'),
        ('RelinkableYoYInflationTermStructureHandle', 'setSeasonality', 'set_seasonality'),
        ('RelinkableZeroInflationTermStructureHandle', 'asHandle', 'as_handle'),
        ('RelinkableZeroInflationTermStructureHandle', 'hasSeasonality', 'has_seasonality'),
        ('RelinkableZeroInflationTermStructureHandle', 'linkTo', 'link_to'),
        ('RelinkableZeroInflationTermStructureHandle', 'setSeasonality', 'set_seasonality'),
        ('Schedule', 'endDate', 'end_date'),
        ('Schedule', 'startDate', 'start_date'),
        ('SimpleChooserOption', 'isExpired', 'is_expired'),
        ('SimpleChooserOption', 'setPricingEngine', 'set_pricing_engine'),
        ('SimpleQuote', 'isValid', 'is_valid'),
        ('SimpleQuote', 'setValue', 'set_value'),
        ('SmileSectionUtils', 'arbitragefreeIndices', 'arbitragefree_indices'),
        ('SmileSectionUtils', 'arbitragefreeRegion', 'arbitragefree_region'),
        ('SmileSectionUtils', 'atmLevel', 'atm_level'),
        ('SoftBarrierOption', 'impliedVolatility', 'implied_volatility'),
        ('SoftBarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('Stock', 'isExpired', 'is_expired'),
        ('SuperFundPayoff', 'optionType', 'option_type'),
        ('SuperFundPayoff', 'secondStrike', 'second_strike'),
        ('SuperSharePayoff', 'cashPayoff', 'cash_payoff'),
        ('SuperSharePayoff', 'optionType', 'option_type'),
        ('SuperSharePayoff', 'secondStrike', 'second_strike'),
        ('Swap', 'isExpired', 'is_expired'),
        ('Swap', 'numberOfLegs', 'number_of_legs'),
        ('Swap', 'setCmsCouponPricer', 'set_cms_coupon_pricer'),
        ('Swap', 'setPricingEngine', 'set_pricing_engine'),
        ('SwapIndex', 'addFixing', 'add_fixing'),
        ('SwapIndex', 'dayCounter', 'day_counter'),
        ('SwapIndex', 'fixingCalendar', 'fixing_calendar'),
        ('SwapIndex', 'fixingDays', 'fixing_days'),
        ('SwapIndex', 'valueDate', 'value_date'),
        ('Swaption', 'impliedVolatility', 'implied_volatility'),
        ('Swaption', 'isExpired', 'is_expired'),
        ('Swaption', 'setBachelierPricingEngine', 'set_bachelier_pricing_engine'),
        ('Swaption', 'setFdG2PricingEngine', 'set_fd_g2_pricing_engine'),
        ('Swaption', 'setFdHullWhitePricingEngine', 'set_fd_hullwhite_pricing_engine'),
        ('Swaption', 'setG2PricingEngine', 'set_g2_pricing_engine'),
        ('Swaption', 'setG2TreePricingEngine', 'set_g2_tree_pricing_engine'),
        (
            'Swaption',
            'setGaussian1dJamshidianPricingEngine',
            'set_gaussian1d_jamshidian_pricing_engine',
        ),
        ('Swaption', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('Swaption', 'setJamshidianPricingEngine', 'set_jamshidian_pricing_engine'),
        ('Swaption', 'setLfmPricingEngine', 'set_lfm_pricing_engine'),
        ('Swaption', 'setPricingEngine', 'set_pricing_engine'),
        ('Swaption', 'setTreePricingEngine', 'set_tree_pricing_engine'),
        ('Swaption', 'settlementMethod', 'settlement_method'),
        ('Swaption', 'settlementType', 'settlement_type'),
        ('SwaptionHelper', 'calibrationError', 'calibration_error'),
        ('SwaptionHelper', 'marketValue', 'market_value'),
        ('SwaptionHelper', 'modelValue', 'model_value'),
        ('SwaptionHelper', 'setGaussian1dPricingEngine', 'set_gaussian1d_pricing_engine'),
        ('SwaptionHelper', 'setLfmPricingEngine', 'set_lfm_pricing_engine'),
        ('SwingExercise', 'lastDate', 'last_date'),
        ('TwoAssetBarrierOption', 'isExpired', 'is_expired'),
        ('TwoAssetBarrierOption', 'setPricingEngine', 'set_pricing_engine'),
        ('TwoAssetCorrelationOption', 'isExpired', 'is_expired'),
        ('TwoAssetCorrelationOption', 'setPricingEngine', 'set_pricing_engine'),
        ('VanillaForwardPayoff', 'optionType', 'option_type'),
        ('VanillaOption', 'errorEstimate', 'error_estimate'),
        ('VanillaOption', 'setBatesDetJumpPricingEngine', 'set_bates_det_jump_pricing_engine'),
        (
            'VanillaOption',
            'setBatesDoubleExpDetJumpPricingEngine',
            'set_bates_double_exp_det_jump_pricing_engine',
        ),
        ('VanillaOption', 'setBatesDoubleExpPricingEngine', 'set_bates_double_exp_pricing_engine'),
        ('VanillaOption', 'setBatesPricingEngine', 'set_bates_pricing_engine'),
        ('VanillaOption', 'setBinomialPricingEngine', 'set_binomial_pricing_engine'),
        (
            'VanillaOption',
            'setBjerksundStenslandPricingEngine',
            'set_bjerksund_stensland_pricing_engine',
        ),
        ('VanillaOption', 'setCashDividendPricingEngine', 'set_cash_dividend_pricing_engine'),
        ('VanillaOption', 'setCevPricingEngine', 'set_cev_pricing_engine'),
        ('VanillaOption', 'setCosHestonPricingEngine', 'set_cos_heston_pricing_engine'),
        (
            'VanillaOption',
            'setDigitalAmericanKoPricingEngine',
            'set_digital_american_ko_pricing_engine',
        ),
        ('VanillaOption', 'setDigitalAmericanPricingEngine', 'set_digital_american_pricing_engine'),
        ('VanillaOption', 'setDividendPricingEngine', 'set_dividend_pricing_engine'),
        (
            'VanillaOption',
            'setExponentialFittingHestonPricingEngine',
            'set_exponential_fitting_heston_pricing_engine',
        ),
        (
            'VanillaOption',
            'setFdBatesDividendPricingEngine',
            'set_fd_bates_dividend_pricing_engine',
        ),
        ('VanillaOption', 'setFdBatesPricingEngine', 'set_fd_bates_pricing_engine'),
        ('VanillaOption', 'setFdCevPricingEngine', 'set_fd_cev_pricing_engine'),
        ('VanillaOption', 'setFdCirPricingEngine', 'set_fd_cir_pricing_engine'),
        ('VanillaOption', 'setFdDividendPricingEngine', 'set_fd_dividend_pricing_engine'),
        (
            'VanillaOption',
            'setFdHestonDividendPricingEngine',
            'set_fd_heston_dividend_pricing_engine',
        ),
        (
            'VanillaOption',
            'setFdHestonHullWhitePricingEngine',
            'set_fd_heston_hull_white_pricing_engine',
        ),
        ('VanillaOption', 'setFdHestonPricingEngine', 'set_fd_heston_pricing_engine'),
        (
            'VanillaOption',
            'setFdHestonQuantoDividendPricingEngine',
            'set_fd_heston_quanto_dividend_pricing_engine',
        ),
        ('VanillaOption', 'setFdHestonQuantoPricingEngine', 'set_fd_heston_quanto_pricing_engine'),
        ('VanillaOption', 'setFdPricingEngine', 'set_fd_pricing_engine'),
        (
            'VanillaOption',
            'setFdQuantoDividendPricingEngine',
            'set_fd_quanto_dividend_pricing_engine',
        ),
        ('VanillaOption', 'setFdQuantoPricingEngine', 'set_fd_quanto_pricing_engine'),
        ('VanillaOption', 'setFdShoutPricingEngine', 'set_fd_shout_pricing_engine'),
        ('VanillaOption', 'setGjrGarchPricingEngine', 'set_gjr_garch_pricing_engine'),
        ('VanillaOption', 'setHestonPricingEngine', 'set_heston_pricing_engine'),
        ('VanillaOption', 'setJumpDiffusionPricingEngine', 'set_jump_diffusion_pricing_engine'),
        (
            'VanillaOption',
            'setMcHestonHullWhitePricingEngine',
            'set_mc_heston_hull_white_pricing_engine',
        ),
        ('VanillaOption', 'setMcHestonPricingEngine', 'set_mc_heston_pricing_engine'),
        ('VanillaOption', 'setPdfHestonPricingEngine', 'set_pdf_heston_pricing_engine'),
        ('VanillaOption', 'setPricingEngine', 'set_pricing_engine'),
        ('VanillaOption', 'setPtdHestonPricingEngine', 'set_ptd_heston_pricing_engine'),
        ('VanillaOption', 'setRoughHestonPricingEngine', 'set_rough_heston_pricing_engine'),
        ('VanillaStorageOption', 'isExpired', 'is_expired'),
        ('VanillaStorageOption', 'setFdPricingEngine', 'set_fd_pricing_engine'),
        ('VanillaStorageOption', 'setPricingEngine', 'set_fd_pricing_engine'),
        ('VanillaSwap', 'fairRate', 'fair_rate'),
        ('VanillaSwap', 'fairSpread', 'fair_spread'),
        ('VanillaSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('VanillaSwingOption', 'isExpired', 'is_expired'),
        ('VanillaSwingOption', 'setFdPricingEngine', 'set_fd_pricing_engine'),
        ('VanillaSwingOption', 'setPricingEngine', 'set_fd_pricing_engine'),
        ('VarianceOption', 'isExpired', 'is_expired'),
        ('VarianceOption', 'maturityDate', 'maturity_date'),
        ('VarianceOption', 'setIntegralHestonPricingEngine', 'set_integral_heston_pricing_engine'),
        ('VarianceOption', 'startDate', 'start_date'),
        ('VarianceSwap', 'isExpired', 'is_expired'),
        ('VarianceSwap', 'maturityDate', 'maturity_date'),
        ('VarianceSwap', 'setMcPricingEngine', 'set_mc_pricing_engine'),
        ('VarianceSwap', 'setReplicatingPricingEngine', 'set_replicating_pricing_engine'),
        ('VarianceSwap', 'startDate', 'start_date'),
        ('WriterExtensibleOption', 'isExpired', 'is_expired'),
        ('WriterExtensibleOption', 'setPricingEngine', 'set_pricing_engine'),
        ('YearOnYearInflationSwap', 'fairRate', 'fair_rate'),
        ('YearOnYearInflationSwap', 'fairSpread', 'fair_spread'),
        ('YearOnYearInflationSwap', 'fixedLegNPV', 'fixed_leg_NPV'),
        ('YearOnYearInflationSwap', 'fixedRate', 'fixed_rate'),
        ('YearOnYearInflationSwap', 'isExpired', 'is_expired'),
        ('YearOnYearInflationSwap', 'maturityDate', 'maturity_date'),
        ('YearOnYearInflationSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('YearOnYearInflationSwap', 'startDate', 'start_date'),
        ('YearOnYearInflationSwap', 'yoyLegNPV', 'yoy_leg_NPV'),
        ('YieldTermStructureHandle', 'referenceDate', 'reference_date'),
        ('YieldTermStructureHandle', 'zeroRate', 'zero_rate'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'YoYTS', 'yoy_ts'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'atmYoYRate', 'atm_yoy_rate'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'atmYoYSwapDateRates', 'atm_yoy_swap_date_rates'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'atmYoYSwapRate', 'atm_yoy_swap_rate'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'atmYoYSwapTimeRates', 'atm_yoy_swap_time_rates'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'capPrice', 'cap_price'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'capStrikes', 'cap_strikes'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'floorPrice', 'floor_price'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'floorStrikes', 'floor_strikes'),
        ('YoYCapFloorTermPriceSurfaceHandle', 'observationLag', 'observation_lag'),
        ('YoYInflationCap', 'atmRate', 'atm_rate'),
        ('YoYInflationCap', 'isExpired', 'is_expired'),
        ('YoYInflationCap', 'maturityDate', 'maturity_date'),
        ('YoYInflationCap', 'setPricingEngine', 'set_pricing_engine'),
        ('YoYInflationCap', 'startDate', 'start_date'),
        ('YoYInflationCapFloor', 'atmRate', 'atm_rate'),
        ('YoYInflationCapFloor', 'isExpired', 'is_expired'),
        ('YoYInflationCapFloor', 'maturityDate', 'maturity_date'),
        ('YoYInflationCapFloor', 'setPricingEngine', 'set_pricing_engine'),
        ('YoYInflationCapFloor', 'startDate', 'start_date'),
        ('YoYInflationCollar', 'atmRate', 'atm_rate'),
        ('YoYInflationCollar', 'isExpired', 'is_expired'),
        ('YoYInflationCollar', 'maturityDate', 'maturity_date'),
        ('YoYInflationCollar', 'setPricingEngine', 'set_pricing_engine'),
        ('YoYInflationCollar', 'startDate', 'start_date'),
        ('YoYInflationCoupon', 'adjustedFixing', 'adjusted_fixing'),
        ('YoYInflationCoupon', 'fixingDate', 'fixing_date'),
        ('YoYInflationCoupon', 'indexFixing', 'index_fixing'),
        ('YoYInflationCoupon', 'setPricer', 'set_pricer'),
        ('YoYInflationCoupon', 'yoyIndex', 'yoy_index'),
        ('YoYInflationFloor', 'atmRate', 'atm_rate'),
        ('YoYInflationFloor', 'isExpired', 'is_expired'),
        ('YoYInflationFloor', 'maturityDate', 'maturity_date'),
        ('YoYInflationFloor', 'setPricingEngine', 'set_pricing_engine'),
        ('YoYInflationFloor', 'startDate', 'start_date'),
        ('YoYInflationIndex', 'addFixing', 'add_fixing'),
        ('YoYInflationIndex', 'availabilityLag', 'availability_lag'),
        ('YoYInflationIndex', 'clearFixings', 'clear_fixings'),
        ('YoYInflationIndex', 'lastFixingDate', 'last_fixing_date'),
        ('YoYInflationTermStructureHandle', 'baseDate', 'base_date'),
        ('YoYInflationTermStructureHandle', 'baseRate', 'base_rate'),
        ('YoYInflationTermStructureHandle', 'hasSeasonality', 'has_seasonality'),
        ('YoYInflationTermStructureHandle', 'maxDate', 'max_date'),
        ('YoYInflationTermStructureHandle', 'referenceDate', 'reference_date'),
        ('YoYInflationTermStructureHandle', 'setSeasonality', 'set_seasonality'),
        ('YoYInflationTermStructureHandle', 'yoyRate', 'yoy_rate'),
        ('ZeroCouponBond', 'accruedAmount', 'accrued_amount'),
        ('ZeroCouponBond', 'bondYield', 'bond_yield'),
        ('ZeroCouponBond', 'cleanPrice', 'clean_price'),
        ('ZeroCouponBond', 'cleanPriceFromZSpread', 'clean_price_from_z_spread'),
        ('ZeroCouponBond', 'dirtyPrice', 'dirty_price'),
        ('ZeroCouponBond', 'maturityDate', 'maturity_date'),
        ('ZeroCouponBond', 'setPricingEngine', 'set_pricing_engine'),
        ('ZeroCouponBond', 'settlementDate', 'settlement_date'),
        ('ZeroCouponBond', 'settlementValue', 'settlement_value'),
        ('ZeroCouponBond', 'zSpread', 'z_spread'),
        ('ZeroCouponInflationSwap', 'fairRate', 'fair_rate'),
        ('ZeroCouponInflationSwap', 'fixedLeg', 'fixed_leg'),
        ('ZeroCouponInflationSwap', 'fixedLegNPV', 'fixed_leg_NPV'),
        ('ZeroCouponInflationSwap', 'fixedRate', 'fixed_rate'),
        ('ZeroCouponInflationSwap', 'inflationLeg', 'inflation_leg'),
        ('ZeroCouponInflationSwap', 'inflationLegNPV', 'inflation_leg_NPV'),
        ('ZeroCouponInflationSwap', 'isExpired', 'is_expired'),
        ('ZeroCouponInflationSwap', 'maturityDate', 'maturity_date'),
        ('ZeroCouponInflationSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('ZeroCouponInflationSwap', 'startDate', 'start_date'),
        ('ZeroCouponSwap', 'baseNominal', 'base_nominal'),
        ('ZeroCouponSwap', 'fairFixedPayment', 'fair_fixed_payment'),
        ('ZeroCouponSwap', 'fairFixedRate', 'fair_fixed_rate'),
        ('ZeroCouponSwap', 'fixedLegNPV', 'fixed_leg_NPV'),
        ('ZeroCouponSwap', 'fixedPayment', 'fixed_payment'),
        ('ZeroCouponSwap', 'floatingLegNPV', 'floating_leg_NPV'),
        ('ZeroCouponSwap', 'isExpired', 'is_expired'),
        ('ZeroCouponSwap', 'maturityDate', 'maturity_date'),
        ('ZeroCouponSwap', 'setPricingEngine', 'set_pricing_engine'),
        ('ZeroCouponSwap', 'startDate', 'start_date'),
        ('ZeroInflationCashFlow', 'observationInterpolation', 'observation_interpolation'),
        ('ZeroInflationCashFlow', 'zeroInflationIndex', 'zero_inflation_index'),
        ('ZeroInflationIndex', 'addFixing', 'add_fixing'),
        ('ZeroInflationIndex', 'availabilityLag', 'availability_lag'),
        ('ZeroInflationIndex', 'clearFixings', 'clear_fixings'),
        ('ZeroInflationIndex', 'lastFixingDate', 'last_fixing_date'),
        ('ZeroInflationTermStructureHandle', 'baseDate', 'base_date'),
        ('ZeroInflationTermStructureHandle', 'hasSeasonality', 'has_seasonality'),
        ('ZeroInflationTermStructureHandle', 'maxDate', 'max_date'),
        ('ZeroInflationTermStructureHandle', 'referenceDate', 'reference_date'),
        ('ZeroInflationTermStructureHandle', 'setSeasonality', 'set_seasonality'),
        ('ZeroInflationTermStructureHandle', 'zeroRate', 'zero_rate'),
    )
    static_methods = {
        ('Date', 'maxDate'),
        ('Date', 'minDate'),
        ('Date', 'todaysDate'),
    }
    for class_name, alias, target in aliases:
        cls = getattr(_ql, class_name, None)
        if cls is None or not isinstance(cls, type):
            continue
        for base in cls.__mro__:
            namespace = vars(base)
            if target in namespace:
                descriptor = namespace[target]
                if (class_name, alias) in static_methods:
                    descriptor = staticmethod(descriptor)
                setattr(cls, alias, descriptor)
                break

    Date = _ql.Date

    SimpleQuote = _ql.SimpleQuote

    Quote = _ql.Quote

    QuoteHandle = _ql.QuoteHandle

    RelinkableQuoteHandle = _ql.RelinkableQuoteHandle

    DayCounter = _ql.DayCounter

    Calendar = _ql.Calendar

    Schedule = _ql.Schedule

    YieldTermStructureHandle = _ql.YieldTermStructureHandle

    FixedRateBond = _ql.FixedRateBond

    ZeroCouponBond = getattr(_ql, "ZeroCouponBond", None)

    FloatingRateBond = getattr(_ql, "FloatingRateBond", None)

    VanillaSwap = _ql.VanillaSwap

    NonstandardSwap = getattr(_ql, "NonstandardSwap", None)

    AssetSwap = getattr(_ql, "AssetSwap", None)

    ZeroCouponSwap = getattr(_ql, "ZeroCouponSwap", None)

    Swaption = getattr(_ql, "Swaption", None)

    NonstandardSwaption = getattr(_ql, "NonstandardSwaption", None)

    CreditDefaultSwap = getattr(_ql, "CreditDefaultSwap", None)

    CdsOption = getattr(_ql, "CdsOption", None)

    BermudanExercise = getattr(_ql, "BermudanExercise", None)

    DefaultProbabilityTermStructureHandle = getattr(
        _ql, "DefaultProbabilityTermStructureHandle", None
    )

    Gsr = getattr(_ql, "Gsr", None)

    MfStateProcess = getattr(_ql, "MfStateProcess", None)

    KahaleSmileSection = getattr(_ql, "KahaleSmileSection", None)

    SmileSectionUtils = getattr(_ql, "SmileSectionUtils", None)

    MarkovFunctionalModelSettings = getattr(_ql, "MarkovFunctionalModelSettings", None)

    MarkovFunctional = getattr(_ql, "MarkovFunctional", None)

    EuropeanOption = _ql.EuropeanOption

    VanillaOption = _ql.VanillaOption

    # Phase-39 / Phase-46 Bates aliases.
    BatesDetJumpModel = getattr(_ql, "BatesDetJumpModel", None)
    BatesDoubleExpModel = getattr(_ql, "BatesDoubleExpModel", None)
    BatesDoubleExpDetJumpModel = getattr(_ql, "BatesDoubleExpDetJumpModel", None)

    # Phase-39 Bates aliases.
    BatesProcess = getattr(_ql, "BatesProcess", None)
    BatesModel = getattr(_ql, "BatesModel", None)

    # Phase-48 Heston calibration aliases.
    HestonModelHelper = getattr(_ql, "HestonModelHelper", None)
    HestonModel = getattr(_ql, "HestonModel", None)

    CapHelper = getattr(_ql, "CapHelper", None)

    SwaptionHelper = getattr(_ql, "SwaptionHelper", None)

    LiborForwardModel = getattr(_ql, "LiborForwardModel", None)

    LiborForwardModelProcess = getattr(_ql, "LiborForwardModelProcess", None)

    GeneralStatistics = getattr(_ql, "GeneralStatistics", None)

    MultiPathGenerator = getattr(_ql, "MultiPathGenerator", None)
    LowDiscrepancyMultiPathGenerator = getattr(
        _ql, "LowDiscrepancyMultiPathGenerator", None
    )
    TimeGrid = getattr(_ql, "TimeGrid", None)

    LfmCovarianceParameterization = getattr(
        _ql, "LfmCovarianceParameterization", None
    )

    LfmHullWhiteParameterization = getattr(_ql, "LfmHullWhiteParameterization", None)

    LinearRegression = getattr(_ql, "LinearRegression", None)

    linear_regression_with_basis = getattr(_ql, "linear_regression_with_basis", None)
    if linear_regression_with_basis is not None:
        linearRegressionWithBasis = linear_regression_with_basis  # noqa: N816

    exponential_correlations = getattr(_ql, "exponential_correlations", None)
    if exponential_correlations is not None:
        exponentialCorrelations = exponential_correlations  # noqa: N816

    time_homogeneous_forward_correlation = getattr(
        _ql, "time_homogeneous_forward_correlation", None
    )
    if time_homogeneous_forward_correlation is not None:
        timeHomogeneousForwardCorrelation = (  # noqa: N816
            time_homogeneous_forward_correlation
        )

    EvolutionDescription = getattr(_ql, "EvolutionDescription", None)

    FlatVol = getattr(_ql, "FlatVol", None)
    AbcdVol = getattr(_ql, "AbcdVol", None)

    LMMDriftCalculator = getattr(_ql, "LMMDriftCalculator", None)

    PiecewiseConstantCorrelationHandle = getattr(
        _ql, "PiecewiseConstantCorrelationHandle", None
    )

    AbcdFunction = getattr(_ql, "AbcdFunction", None)

    AbcdCalibration = getattr(_ql, "AbcdCalibration", None)

    LmExponentialCorrelationModel = getattr(_ql, "LmExponentialCorrelationModel", None)

    LmExtLinearExponentialVolModel = getattr(_ql, "LmExtLinearExponentialVolModel", None)

    LmLinearExponentialCorrelationModel = getattr(
        _ql, "LmLinearExponentialCorrelationModel", None
    )

    OvernightIndexedSwap = getattr(_ql, "OvernightIndexedSwap", None)

    IborIndex = _ql.IborIndex

    OvernightIndex = getattr(_ql, "OvernightIndex", None)

    PlainVanillaPayoff = _ql.PlainVanillaPayoff

    CashOrNothingPayoff = getattr(_ql, "CashOrNothingPayoff", None)

    AssetOrNothingPayoff = getattr(_ql, "AssetOrNothingPayoff", None)

    GapPayoff = getattr(_ql, "GapPayoff", None)

    SuperFundPayoff = getattr(_ql, "SuperFundPayoff", None)

    SuperSharePayoff = getattr(_ql, "SuperSharePayoff", None)

    FloatingTypePayoff = getattr(_ql, "FloatingTypePayoff", None)

    PercentageStrikePayoff = getattr(_ql, "PercentageStrikePayoff", None)

    ContinuousFloatingLookbackOption = getattr(
        _ql, "ContinuousFloatingLookbackOption", None
    )

    ContinuousFixedLookbackOption = getattr(
        _ql, "ContinuousFixedLookbackOption", None
    )

    AnalyticContinuousFloatingLookbackEngine = getattr(
        _ql, "AnalyticContinuousFloatingLookbackEngine", None
    )
    AnalyticContinuousFixedLookbackEngine = getattr(
        _ql, "AnalyticContinuousFixedLookbackEngine", None
    )

    ContinuousPartialFloatingLookbackOption = getattr(
        _ql, "ContinuousPartialFloatingLookbackOption", None
    )

    ContinuousPartialFixedLookbackOption = getattr(
        _ql, "ContinuousPartialFixedLookbackOption", None
    )

    AnalyticContinuousPartialFloatingLookbackEngine = getattr(
        _ql, "AnalyticContinuousPartialFloatingLookbackEngine", None
    )
    AnalyticContinuousPartialFixedLookbackEngine = getattr(
        _ql, "AnalyticContinuousPartialFixedLookbackEngine", None
    )

    EuropeanExercise = _ql.EuropeanExercise

    AmericanExercise = _ql.AmericanExercise

    ForwardRateAgreement = _ql.ForwardRateAgreement

    BondForward = getattr(_ql, "BondForward", None)

    PerpetualFutures = getattr(_ql, "PerpetualFutures", None)
    if PerpetualFutures is not None:
        PerpetualFuturesPayoffType = getattr(  # noqa: N816
            _ql, "PerpetualFuturesPayoffType", None
        )
        PerpetualFuturesFundingType = getattr(  # noqa: N816
            _ql, "PerpetualFuturesFundingType", None
        )
        if PerpetualFuturesPayoffType is not None:
            PerpetualFutures.Linear = (  # type: ignore[attr-defined]
                PerpetualFuturesPayoffType.Linear
            )
            PerpetualFutures.Inverse = (  # type: ignore[attr-defined]
                PerpetualFuturesPayoffType.Inverse
            )
            PerpetualFutures.Quanto = (  # type: ignore[attr-defined]
                PerpetualFuturesPayoffType.Quanto
            )
        if PerpetualFuturesFundingType is not None:
            PerpetualFutures.FundingWithPreviousSpot = (  # type: ignore[attr-defined]
                PerpetualFuturesFundingType.FundingWithPreviousSpot
            )
            PerpetualFutures.FundingWithCurrentSpot = (  # type: ignore[attr-defined]
                PerpetualFuturesFundingType.FundingWithCurrentSpot
            )

    # Phase-4 / Phase-31 barrier instruments (present when bindings are built).
    BarrierOption = getattr(_ql, "BarrierOption", None)
    AnalyticBinaryBarrierEngine = getattr(
        _ql, "AnalyticBinaryBarrierEngine", None
    )

    # Phase-29 soft barrier aliases.
    SoftBarrierOption = getattr(_ql, "SoftBarrierOption", None)
    AnalyticSoftBarrierEngine = getattr(_ql, "AnalyticSoftBarrierEngine", None)

    # Phase-30 partial-time barrier aliases.
    PartialBarrierRange = getattr(_ql, "PartialBarrierRange", None)
    PartialTimeBarrierOption = getattr(_ql, "PartialTimeBarrierOption", None)
    AnalyticPartialTimeBarrierOptionEngine = getattr(
        _ql, "AnalyticPartialTimeBarrierOptionEngine", None
    )

    # Phase-32 two-asset barrier aliases.
    TwoAssetBarrierOption = getattr(_ql, "TwoAssetBarrierOption", None)

    # Phase-33 two-asset correlation aliases.
    TwoAssetCorrelationOption = getattr(_ql, "TwoAssetCorrelationOption", None)

    # Phase-34/143 cliquet aliases.
    CliquetOption = getattr(_ql, "CliquetOption", None)

    CompoundOption = getattr(_ql, "CompoundOption", None)

    # Phase-75 Margrabe exchange-option aliases.
    MargrabeOption = getattr(_ql, "MargrabeOption", None)

    # Phase-76 simple / complex chooser aliases.
    SimpleChooserOption = getattr(_ql, "SimpleChooserOption", None)
    ComplexChooserOption = getattr(_ql, "ComplexChooserOption", None)

    # Phase-83 holder / writer extensible aliases.
    HolderExtensibleOption = getattr(_ql, "HolderExtensibleOption", None)
    WriterExtensibleOption = getattr(_ql, "WriterExtensibleOption", None)

    # Phase-78 Kirk / Phase-79 Stulz basket aliases.
    SpreadBasketPayoff = getattr(_ql, "SpreadBasketPayoff", None)
    MinBasketPayoff = getattr(_ql, "MinBasketPayoff", None)
    MaxBasketPayoff = getattr(_ql, "MaxBasketPayoff", None)
    BasketOption = getattr(_ql, "BasketOption", None)

    # Phase-80 variance-swap aliases.
    VarianceSwap = getattr(_ql, "VarianceSwap", None)

    # Phase-110 variance-option aliases.
    VarianceOption = getattr(_ql, "VarianceOption", None)

    # Phase-35 forward vanilla aliases.
    ForwardVanillaOption = getattr(_ql, "ForwardVanillaOption", None)

    # Phase-25/26 double-barrier aliases.
    DoubleBarrierType = getattr(_ql, "DoubleBarrierType", None)
    DoubleBarrierOption = getattr(_ql, "DoubleBarrierOption", None)
    AnalyticDoubleBarrierEngine = getattr(
        _ql, "AnalyticDoubleBarrierEngine", None
    )
    AnalyticDoubleBarrierBinaryEngine = getattr(
        _ql, "AnalyticDoubleBarrierBinaryEngine", None
    )

    CapFloor = getattr(_ql, "CapFloor", None)

    Collar = getattr(_ql, "Collar", None)

    Cap = getattr(_ql, "Cap", None)

    Floor = getattr(_ql, "Floor", None)


_install_aliases()

AbcdCalibration = getattr(_ql, "AbcdCalibration", None)  # noqa: N816

LMMDriftCalculator = getattr(_ql, "LMMDriftCalculator", None)  # noqa: N816

terminalMeasure = getattr(_ql, "terminal_measure", None)  # noqa: N816
moneyMarketMeasure = getattr(_ql, "money_market_measure", None)  # noqa: N816
moneyMarketPlusMeasure = getattr(_ql, "money_market_plus_measure", None)  # noqa: N816
isInTerminalMeasure = getattr(_ql, "is_in_terminal_measure", None)  # noqa: N816
isInMoneyMarketMeasure = getattr(_ql, "is_in_money_market_measure", None)  # noqa: N816
isInMoneyMarketPlusMeasure = getattr(  # noqa: N816
    _ql, "is_in_money_market_plus_measure", None
)
isInSubset = getattr(_ql, "is_in_subset", None)  # noqa: N816
mergeTimes = getattr(_ql, "merge_times", None)  # noqa: N816
checkIncreasingTimesAndCalculateTaus = getattr(  # noqa: N816
    _ql, "check_increasing_times_and_calculate_taus", None
)

# Convenience aliases matching common SWIG free functions / names.
setEvaluationDate = _ql.set_evaluation_date  # noqa: N816
getEvaluationDate = _ql.get_evaluation_date  # noqa: N816

# Settlement nested namespace (SWIG: ql.Settlement.Physical).
class Settlement:
    """SWIG-style Settlement.Physical / Settlement.Cash namespace."""

    Physical = getattr(_ql, "SettlementType").Physical
    Cash = getattr(_ql, "SettlementType").Cash
    PhysicalOTC = getattr(_ql, "SettlementMethod").PhysicalOTC
    PhysicalCleared = getattr(_ql, "SettlementMethod").PhysicalCleared
    CollateralizedCashPrice = getattr(_ql, "SettlementMethod").CollateralizedCashPrice
    ParYieldCurve = getattr(_ql, "SettlementMethod").ParYieldCurve


# Attach Payer/Receiver on VanillaSwap class for SWIG-like access.
_ql.VanillaSwap.Payer = _ql.SwapType.Payer  # type: ignore[attr-defined]
_ql.VanillaSwap.Receiver = _ql.SwapType.Receiver  # type: ignore[attr-defined]

# Phase-6 MakeOIS-style alias.
makeOIS = getattr(_ql, "make_ois", None)

# Phase-93 MakeMultipleResetsSwap-style alias.
makeMultipleResetsSwap = getattr(_ql, "make_multiple_resets_swap", None)
MakeMultipleResetsSwap = makeMultipleResetsSwap
MultipleResetsSwap = getattr(_ql, "MultipleResetsSwap", None)

# Phase-98 FloatFloatSwap aliases.
FloatFloatSwap = getattr(_ql, "FloatFloatSwap", None)
makeFloatFloatSwap = getattr(_ql, "make_float_float_swap", None)
MakeFloatFloatSwap = makeFloatFloatSwap

# Phase-99 OvernightIndexFuture / SOFR futures aliases.
OvernightIndexFuture = getattr(_ql, "OvernightIndexFuture", None)
SofrFutureRateHelper = getattr(_ql, "SofrFutureRateHelper", None)
PiecewiseLinearDiscountCurve = getattr(_ql, "PiecewiseLinearDiscountCurve", None)

# Phase-100 BMASwap / BMAIndex aliases.
BMAIndex = getattr(_ql, "BMAIndex", None)
BMASwap = getattr(_ql, "BMASwap", None)
makeBMASwap = getattr(_ql, "make_bma_swap", None)
MakeBMASwap = makeBMASwap
BMASwapRateHelper = getattr(_ql, "BMASwapRateHelper", None)
JointCalendar = getattr(_ql, "JointCalendar", None)
JointCalendarRule = getattr(_ql, "JointCalendarRule", None)

# Phase-101 AmortizingFixedRateBond / AmortizingFloatingRateBond aliases.
AmortizingFixedRateBond = getattr(_ql, "AmortizingFixedRateBond", None)
AmortizingFloatingRateBond = getattr(_ql, "AmortizingFloatingRateBond", None)
sinkingSchedule = getattr(_ql, "sinking_schedule", None)
sinkingNotionals = getattr(_ql, "sinking_notionals", None)
SinkingSchedule = sinkingSchedule
SinkingNotionals = sinkingNotionals

# Phase-102 VanillaSwingOption aliases.
SwingExercise = getattr(_ql, "SwingExercise", None)
VanillaForwardPayoff = getattr(_ql, "VanillaForwardPayoff", None)
VanillaSwingOption = getattr(_ql, "VanillaSwingOption", None)
FdSimpleBSSwingEngine = getattr(_ql, "FdSimpleBSSwingEngine", None)

# Phase-103 VanillaStorageOption / ExtendedOrnsteinUhlenbeck aliases.
ExtendedOrnsteinUhlenbeckProcess = getattr(
    _ql, "ExtendedOrnsteinUhlenbeckProcess", None
)
ExtendedOrnsteinUhlenbeckDiscretization = getattr(
    _ql, "ExtendedOrnsteinUhlenbeckDiscretization", None
)
VanillaStorageOption = getattr(_ql, "VanillaStorageOption", None)
FdSimpleExtOUStorageEngine = getattr(_ql, "FdSimpleExtOUStorageEngine", None)

# Phase-104 Stock / CompositeInstrument aliases.
Stock = getattr(_ql, "Stock", None)
CompositeInstrument = getattr(_ql, "CompositeInstrument", None)

# Phase-106 cross-currency fix/float swap aliases.
ConstNotionalCrossCurrencyFixedVsFloatingSwap = getattr(
    _ql, "ConstNotionalCrossCurrencyFixedVsFloatingSwap", None
)

# Phase-109 cross-currency basis swap aliases.
ConstNotionalCrossCurrencyBasisSwap = getattr(
    _ql, "ConstNotionalCrossCurrencyBasisSwap", None
)

# Phase-111 generic cross-currency swap aliases.
ConstNotionalCrossCurrencySwap = getattr(
    _ql, "ConstNotionalCrossCurrencySwap", None
)

makeFixFixXCCYSwap = getattr(_ql, "make_fix_fix_xccy_swap", None)
makeFloatFloatXCCYSwap = getattr(_ql, "make_float_float_xccy_swap", None)
makeFixFloatXCCYSwap = getattr(_ql, "make_fix_float_xccy_swap", None)
CmsRateBond = getattr(_ql, "CmsRateBond", None)
CHFCurrency = getattr(_ql, "CHFCurrency", None)
Switzerland = getattr(_ql, "Switzerland", None)

TRYCurrency = getattr(_ql, "TRYCurrency", None)
Turkey = getattr(_ql, "Turkey", None)
DiscountCurve = getattr(_ql, "DiscountCurve", None)

# Phase-94 EquityTotalReturnSwap / EquityIndex aliases.
USDLibor = getattr(_ql, "USDLibor", None)
EquityIndex = getattr(_ql, "EquityIndex", None)
EquityTotalReturnSwap = getattr(_ql, "EquityTotalReturnSwap", None)

# Phase-95 HimalayaOption aliases.
HimalayaOption = getattr(_ql, "HimalayaOption", None)
MCHimalayaEngine = getattr(_ql, "MCHimalayaEngine", None)

# Phase-96 PagodaOption aliases.
PagodaOption = getattr(_ql, "PagodaOption", None)
MCPagodaEngine = getattr(_ql, "MCPagodaEngine", None)

# Phase-97 EverestOption aliases.
EverestOption = getattr(_ql, "EverestOption", None)
MCEverestEngine = getattr(_ql, "MCEverestEngine", None)

# Phase-7 Protection nested namespace (SWIG: ql.Protection.Seller).
class Protection:
    """SWIG-style Protection.Buyer / Protection.Seller namespace."""

    Buyer = getattr(_ql, "ProtectionSide").Buyer
    Seller = getattr(_ql, "ProtectionSide").Seller

# FD mesher / value-grid NumPy helpers (camelCase aliases).
uniform1dMesherLocations = getattr(_ql, "uniform_1d_mesher_locations", None)
fdmBlackScholesMesherLocations = getattr(
    _ql, "fdm_black_scholes_mesher_locations", None
)
fdmBlackScholesValues = getattr(_ql, "fdm_black_scholes_values", None)

# Phase-9 CDS bootstrap / Asian aliases.
SpreadCdsHelper = getattr(_ql, "SpreadCdsHelper", None)
PiecewiseHazardRateCurve = getattr(_ql, "PiecewiseHazardRateCurve", None)
ContinuousAveragingAsianOption = getattr(
    _ql, "ContinuousAveragingAsianOption", None
)
DiscreteAveragingAsianOption = getattr(
    _ql, "DiscreteAveragingAsianOption", None
)

# Phase-10 CMS / SwapIndex aliases.
EuriborSwapIsdaFixA = getattr(_ql, "EuriborSwapIsdaFixA", None)
ConstantSwaptionVolatility = getattr(_ql, "ConstantSwaptionVolatility", None)
ConstantOptionletVolatility = getattr(_ql, "ConstantOptionletVolatility", None)
MarkovFunctional = getattr(_ql, "MarkovFunctional", None)
MarkovFunctionalModelSettings = getattr(_ql, "MarkovFunctionalModelSettings", None)
MarkovFunctionalModelOutputs = getattr(_ql, "MarkovFunctionalModelOutputs", None)
MarkovFunctionalAdjustment = getattr(_ql, "MarkovFunctionalAdjustment", None)
markovFunctionalTestMd0Yts = getattr(_ql, "markov_functional_test_md0_yts", None)
markovFunctionalTestMd0SwaptionVts = getattr(
    _ql, "markov_functional_test_md0_swaption_vts", None
)
markovFunctionalTestMd0OptionletVts = getattr(
    _ql, "markov_functional_test_md0_optionlet_vts", None
)
markovFunctionalTestMd0CoterminalHelperVols = getattr(
    _ql, "markov_functional_test_md0_coterminal_helper_vols", None
)
AnalyticHaganPricer = getattr(_ql, "AnalyticHaganPricer", None)
NumericHaganPricer = getattr(_ql, "NumericHaganPricer", None)
makeCms = getattr(_ql, "make_cms", None)
makeSwaption = getattr(_ql, "make_swaption", None)

CmsCoupon = getattr(_ql, "CmsCoupon", None)

Swap = getattr(_ql, "Swap", None)

SwapIndex = getattr(_ql, "SwapIndex", None)

# Phase-11 CMS-spread aliases.
LinearTsrPricer = getattr(_ql, "LinearTsrPricer", None)
LognormalCmsSpreadPricer = getattr(_ql, "LognormalCmsSpreadPricer", None)
SwapSpreadIndex = getattr(_ql, "make_swap_spread_index", None)
CmsSpreadCoupon = getattr(_ql, "CmsSpreadCoupon", None)
CappedFlooredCmsSpreadCoupon = getattr(_ql, "CappedFlooredCmsSpreadCoupon", None)

# Phase-12 zero-inflation / ZCIS aliases.
UKRPI = getattr(_ql, "UKRPI", None)
EUHICP = getattr(_ql, "EUHICP", None)
ZeroCouponInflationSwapHelper = getattr(
    _ql, "ZeroCouponInflationSwapHelper", None
)
PiecewiseZeroInflationCurve = getattr(_ql, "PiecewiseZeroInflationCurve", None)
InterpolatedZeroInflationCurve = getattr(
    _ql, "InterpolatedZeroInflationCurve", None
)
FlatZeroInflationCurve = getattr(_ql, "FlatZeroInflationCurve", None)

ZeroInflationIndex = getattr(_ql, "ZeroInflationIndex", None)

ZeroCouponInflationSwap = getattr(_ql, "ZeroCouponInflationSwap", None)

ZeroInflationTermStructureHandle = getattr(
    _ql, "ZeroInflationTermStructureHandle", None
)

RelinkableZeroInflationTermStructureHandle = getattr(
    _ql, "RelinkableZeroInflationTermStructureHandle", None
)

# Phase-13 YoY-inflation / YYIIS aliases.
YYUKRPI = getattr(_ql, "YYUKRPI", None)
YYEUHICP = getattr(_ql, "YYEUHICP", None)
YoYInflationIndex = getattr(_ql, "make_yoy_inflation_index", None)
YearOnYearInflationSwapHelper = getattr(
    _ql, "YearOnYearInflationSwapHelper", None
)
PiecewiseYoYInflationCurve = getattr(_ql, "PiecewiseYoYInflationCurve", None)
InterpolatedYoYInflationCurve = getattr(
    _ql, "InterpolatedYoYInflationCurve", None
)
FlatYoYInflationCurve = getattr(_ql, "FlatYoYInflationCurve", None)

_YoYInflationIndexType = getattr(_ql, "YoYInflationIndex", None)

YearOnYearInflationSwap = getattr(_ql, "YearOnYearInflationSwap", None)

YoYInflationTermStructureHandle = getattr(
    _ql, "YoYInflationTermStructureHandle", None
)

RelinkableYoYInflationTermStructureHandle = getattr(
    _ql, "RelinkableYoYInflationTermStructureHandle", None
)

# Phase-14 YoY inflation cap/floor aliases.
ConstantYoYOptionletVolatility = getattr(
    _ql, "ConstantYoYOptionletVolatility", None
)
makeYoYInflationCapFloor = getattr(_ql, "make_yoy_inflation_capfloor", None)
MakeYoYInflationCapFloor = makeYoYInflationCapFloor

YoYInflationCapFloor = getattr(_ql, "YoYInflationCapFloor", None)

YoYInflationCapFloorType = getattr(_ql, "YoYInflationCapFloorType", None)
YoYInflationCap = getattr(_ql, "YoYInflationCap", None)
YoYInflationFloor = getattr(_ql, "YoYInflationFloor", None)
YoYInflationCollar = getattr(_ql, "YoYInflationCollar", None)
YoYOptionletVolatilitySurfaceHandle = getattr(
    _ql, "YoYOptionletVolatilitySurfaceHandle", None
)

# Phase-15 CPISwap / CPIBond aliases.
GBPLibor = getattr(_ql, "GBPLibor", None)
InterpolatedZeroCurve = getattr(_ql, "InterpolatedZeroCurve", None)
ZeroCurve = getattr(_ql, "ZeroCurve", InterpolatedZeroCurve)
CPISwap = getattr(_ql, "CPISwap", None)

CPIBond = getattr(_ql, "CPIBond", None)

# Phase-16 CPICapFloor aliases.
Matrix = getattr(_ql, "Matrix", None)
InterpolatedCPICapFloorTermPriceSurface = getattr(
    _ql, "InterpolatedCPICapFloorTermPriceSurface", None
)
CPICapFloor = getattr(_ql, "CPICapFloor", None)

CPICapFloorTermPriceSurfaceHandle = getattr(
    _ql, "CPICapFloorTermPriceSurfaceHandle", None
)

# Phase-17 seasonality aliases.
MultiplicativePriceSeasonality = getattr(
    _ql, "MultiplicativePriceSeasonality", None
)
KerkhofSeasonality = getattr(_ql, "KerkhofSeasonality", None)
inflationPeriod = getattr(_ql, "inflation_period", None)
Seasonality = getattr(_ql, "Seasonality", None)



# Phase-18 CPI coupon / CPILeg aliases.
CashFlow = getattr(_ql, "CashFlow", None)
CPICouponPricer = getattr(_ql, "CPICouponPricer", None)
CPICoupon = getattr(_ql, "CPICoupon", None)


# Phase-65 CPI vol-dependent optionlet aliases.
ConstantCPIVolatility = getattr(_ql, "ConstantCPIVolatility", None)
CPIVolatilitySurfaceHandle = getattr(
    _ql, "CPIVolatilitySurfaceHandle", None
)
BlackCPICouponPricer = getattr(_ql, "BlackCPICouponPricer", None)
BachelierCPICouponPricer = getattr(_ql, "BachelierCPICouponPricer", None)

CPILeg = getattr(_ql, "make_cpi_leg", None)
setCouponPricer = getattr(_ql, "set_cpi_coupon_pricer", None)
CashFlows_npv = getattr(_ql, "cashflows_npv", None)
CashFlows_accruedAmount = getattr(_ql, "cashflows_accrued_amount", None)

# Phase-19 YoY coupon / yoyInflationLeg aliases.
YoYInflationCouponPricer = getattr(_ql, "YoYInflationCouponPricer", None)
BlackYoYInflationCouponPricer = getattr(
    _ql, "BlackYoYInflationCouponPricer", None
)
UnitDisplacedBlackYoYInflationCouponPricer = getattr(
    _ql, "UnitDisplacedBlackYoYInflationCouponPricer", None
)
BachelierYoYInflationCouponPricer = getattr(
    _ql, "BachelierYoYInflationCouponPricer", None
)
YoYInflationCoupon = getattr(_ql, "YoYInflationCoupon", None)

yoyInflationLeg = getattr(_ql, "make_yoy_inflation_leg", None)
setYoYCouponPricer = getattr(_ql, "set_yoy_coupon_pricer", None)

# Phase-20 capped/floored YoY coupon aliases.
CappedFlooredYoYInflationCoupon = getattr(
    _ql, "CappedFlooredYoYInflationCoupon", None
)

# Phase-21 Indexed / CPI / ZeroInflation cash-flow aliases.
IndexedCashFlow = getattr(_ql, "IndexedCashFlow", None)

CPICashFlow = getattr(_ql, "CPICashFlow", None)

ZeroInflationCashFlow = getattr(_ql, "ZeroInflationCashFlow", None)

# Phase-22 YoY cap/floor term price surface aliases.
InterpolatedYoYCapFloorTermPriceSurface = getattr(
    _ql, "InterpolatedYoYCapFloorTermPriceSurface", None
)
YoYCapFloorTermPriceSurfaceHandle = getattr(
    _ql, "YoYCapFloorTermPriceSurfaceHandle", None
)

# Phase-23 callable / puttable bond aliases.
BondPriceType = getattr(_ql, "BondPriceType", None)
BondPrice = getattr(_ql, "BondPrice", None)
CallabilityType = getattr(_ql, "CallabilityType", None)
Callability = getattr(_ql, "make_callability", None)
CallableFixedRateBond = getattr(_ql, "CallableFixedRateBond", None)
CallableZeroCouponBond = getattr(_ql, "CallableZeroCouponBond", None)

def make_soft_callability(*args: Any, **kwargs: Any) -> Any:
    return _ql.make_soft_callability(*args, **kwargs)


SoftCallability = make_soft_callability
ConvertibleZeroCouponBond = getattr(_ql, "ConvertibleZeroCouponBond", None)
ConvertibleFixedCouponBond = getattr(_ql, "ConvertibleFixedCouponBond", None)
ConvertibleFloatingRateBond = getattr(_ql, "ConvertibleFloatingRateBond", None)

# Phase-24 currency / FX aliases.
Currency = getattr(_ql, "Currency", None)
USDCurrency = getattr(_ql, "USDCurrency", None)
EURCurrency = getattr(_ql, "EURCurrency", None)
GBPCurrency = getattr(_ql, "GBPCurrency", None)
SGDCurrency = getattr(_ql, "SGDCurrency", None)
MoneyConversionType = getattr(_ql, "MoneyConversionType", None)
Money = getattr(_ql, "Money", None)
ExchangeRateType = getattr(_ql, "ExchangeRateType", None)
ExchangeRate = getattr(_ql, "ExchangeRate", None)
FxForward = getattr(_ql, "FxForward", None)

# Phase-40 quanto vanilla aliases.
QuantoVanillaOption = getattr(_ql, "QuantoVanillaOption", None)

# Phase-41 / Phase-44 quanto-forward vanilla aliases.
QuantoForwardVanillaOption = getattr(_ql, "QuantoForwardVanillaOption", None)

# Phase-42 quanto barrier aliases.
QuantoBarrierOption = getattr(_ql, "QuantoBarrierOption", None)

# Phase-43 quanto double-barrier aliases.
QuantoDoubleBarrierOption = getattr(_ql, "QuantoDoubleBarrierOption", None)

# SWIG-style CPI.Flat nested namespace.
class CPI:
    """SWIG-style CPI.Flat / CPI.Linear namespace."""

    Flat = getattr(_ql, "CPIInterpolationType").Flat
    Linear = getattr(_ql, "CPIInterpolationType").Linear
    laggedFixing = staticmethod(getattr(_ql, "cpi_lagged_fixing"))

# SWIG-style GFunctionFactory.Standard nested namespace.
class GFunctionFactory:
    """SWIG-style GFunctionFactory.Standard / ExactYield / … namespace."""

    Standard = getattr(_ql, "YieldCurveModel").Standard
    ExactYield = getattr(_ql, "YieldCurveModel").ExactYield
    ParallelShifts = getattr(_ql, "YieldCurveModel").ParallelShifts
    NonParallelShifts = getattr(_ql, "YieldCurveModel").NonParallelShifts


__all__ = [name for name in globals() if not name.startswith("_")]
