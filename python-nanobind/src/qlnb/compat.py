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
    Date = _ql.Date
    Date.dayOfMonth = Date.day_of_month  # type: ignore[attr-defined]
    Date.serialNumber = Date.serial_number  # type: ignore[attr-defined]
    Date.todaysDate = staticmethod(Date.todays_date)  # type: ignore[attr-defined]
    Date.minDate = staticmethod(Date.min_date)  # type: ignore[attr-defined]
    Date.maxDate = staticmethod(Date.max_date)  # type: ignore[attr-defined]

    SimpleQuote = _ql.SimpleQuote
    SimpleQuote.setValue = SimpleQuote.set_value  # type: ignore[attr-defined]
    SimpleQuote.isValid = SimpleQuote.is_valid  # type: ignore[attr-defined]

    Quote = _ql.Quote
    Quote.isValid = Quote.is_valid  # type: ignore[attr-defined]

    QuoteHandle = _ql.QuoteHandle
    QuoteHandle.currentLink = QuoteHandle.current_link  # type: ignore[attr-defined]

    RelinkableQuoteHandle = _ql.RelinkableQuoteHandle
    RelinkableQuoteHandle.currentLink = RelinkableQuoteHandle.current_link  # type: ignore[attr-defined]
    RelinkableQuoteHandle.linkTo = RelinkableQuoteHandle.link_to  # type: ignore[attr-defined]

    DayCounter = _ql.DayCounter
    DayCounter.yearFraction = DayCounter.year_fraction  # type: ignore[attr-defined]
    DayCounter.dayCount = DayCounter.day_count  # type: ignore[attr-defined]

    Calendar = _ql.Calendar
    Calendar.isBusinessDay = Calendar.is_business_day  # type: ignore[attr-defined]
    Calendar.isHoliday = Calendar.is_holiday  # type: ignore[attr-defined]

    Schedule = _ql.Schedule
    Schedule.startDate = Schedule.start_date  # type: ignore[attr-defined]
    Schedule.endDate = Schedule.end_date  # type: ignore[attr-defined]

    YieldTermStructureHandle = _ql.YieldTermStructureHandle
    YieldTermStructureHandle.referenceDate = (  # type: ignore[attr-defined]
        YieldTermStructureHandle.reference_date
    )
    YieldTermStructureHandle.zeroRate = YieldTermStructureHandle.zero_rate  # type: ignore[attr-defined]

    FixedRateBond = _ql.FixedRateBond
    FixedRateBond.cleanPrice = FixedRateBond.clean_price  # type: ignore[attr-defined]
    FixedRateBond.dirtyPrice = FixedRateBond.dirty_price  # type: ignore[attr-defined]
    FixedRateBond.settlementDate = FixedRateBond.settlement_date  # type: ignore[attr-defined]
    FixedRateBond.maturityDate = FixedRateBond.maturity_date  # type: ignore[attr-defined]
    if hasattr(FixedRateBond, "settlement_value"):
        FixedRateBond.settlementValue = (  # type: ignore[attr-defined]
            FixedRateBond.settlement_value
        )
    FixedRateBond.setPricingEngine = FixedRateBond.set_pricing_engine  # type: ignore[attr-defined]
    if hasattr(FixedRateBond, "bond_yield"):
        FixedRateBond.bondYield = FixedRateBond.bond_yield  # type: ignore[attr-defined]
        FixedRateBond.zSpread = FixedRateBond.z_spread  # type: ignore[attr-defined]
        FixedRateBond.cleanPriceFromZSpread = (  # type: ignore[attr-defined]
            FixedRateBond.clean_price_from_z_spread
        )
        FixedRateBond.accruedAmount = (  # type: ignore[attr-defined]
            FixedRateBond.accrued_amount
        )

    ZeroCouponBond = getattr(_ql, "ZeroCouponBond", None)
    if ZeroCouponBond is not None:
        ZeroCouponBond.cleanPrice = ZeroCouponBond.clean_price  # type: ignore[attr-defined]
        ZeroCouponBond.dirtyPrice = ZeroCouponBond.dirty_price  # type: ignore[attr-defined]
        ZeroCouponBond.settlementDate = ZeroCouponBond.settlement_date  # type: ignore[attr-defined]
        ZeroCouponBond.maturityDate = ZeroCouponBond.maturity_date  # type: ignore[attr-defined]
        if hasattr(ZeroCouponBond, "settlement_value"):
            ZeroCouponBond.settlementValue = (  # type: ignore[attr-defined]
                ZeroCouponBond.settlement_value
            )
        ZeroCouponBond.setPricingEngine = ZeroCouponBond.set_pricing_engine  # type: ignore[attr-defined]
        if hasattr(ZeroCouponBond, "bond_yield"):
            ZeroCouponBond.bondYield = ZeroCouponBond.bond_yield  # type: ignore[attr-defined]
            ZeroCouponBond.zSpread = ZeroCouponBond.z_spread  # type: ignore[attr-defined]
            ZeroCouponBond.cleanPriceFromZSpread = (  # type: ignore[attr-defined]
                ZeroCouponBond.clean_price_from_z_spread
            )
            ZeroCouponBond.accruedAmount = (  # type: ignore[attr-defined]
                ZeroCouponBond.accrued_amount
            )

    FloatingRateBond = getattr(_ql, "FloatingRateBond", None)
    if FloatingRateBond is not None:
        FloatingRateBond.cleanPrice = FloatingRateBond.clean_price  # type: ignore[attr-defined]
        FloatingRateBond.dirtyPrice = FloatingRateBond.dirty_price  # type: ignore[attr-defined]
        FloatingRateBond.settlementDate = FloatingRateBond.settlement_date  # type: ignore[attr-defined]
        FloatingRateBond.maturityDate = FloatingRateBond.maturity_date  # type: ignore[attr-defined]
        if hasattr(FloatingRateBond, "settlement_value"):
            FloatingRateBond.settlementValue = (  # type: ignore[attr-defined]
                FloatingRateBond.settlement_value
            )
        FloatingRateBond.setPricingEngine = (  # type: ignore[attr-defined]
            FloatingRateBond.set_pricing_engine
        )
        if hasattr(FloatingRateBond, "bond_yield"):
            FloatingRateBond.bondYield = (  # type: ignore[attr-defined]
                FloatingRateBond.bond_yield
            )
            FloatingRateBond.zSpread = (  # type: ignore[attr-defined]
                FloatingRateBond.z_spread
            )
            FloatingRateBond.cleanPriceFromZSpread = (  # type: ignore[attr-defined]
                FloatingRateBond.clean_price_from_z_spread
            )
            FloatingRateBond.accruedAmount = (  # type: ignore[attr-defined]
                FloatingRateBond.accrued_amount
            )

    VanillaSwap = _ql.VanillaSwap
    VanillaSwap.fairRate = VanillaSwap.fair_rate  # type: ignore[attr-defined]
    VanillaSwap.fairSpread = VanillaSwap.fair_spread  # type: ignore[attr-defined]
    VanillaSwap.setPricingEngine = VanillaSwap.set_pricing_engine  # type: ignore[attr-defined]

    AssetSwap = getattr(_ql, "AssetSwap", None)
    if AssetSwap is not None:
        AssetSwap.fairSpread = AssetSwap.fair_spread  # type: ignore[attr-defined]
        AssetSwap.fairCleanPrice = AssetSwap.fair_clean_price  # type: ignore[attr-defined]
        AssetSwap.fairNonParRepayment = (  # type: ignore[attr-defined]
            AssetSwap.fair_non_par_repayment
        )
        AssetSwap.floatingLegBPS = AssetSwap.floating_leg_BPS  # type: ignore[attr-defined]
        AssetSwap.floatingLegNPV = AssetSwap.floating_leg_NPV  # type: ignore[attr-defined]
        AssetSwap.parSwap = AssetSwap.par_swap  # type: ignore[attr-defined]
        AssetSwap.cleanPrice = AssetSwap.clean_price  # type: ignore[attr-defined]
        AssetSwap.nonParRepayment = (  # type: ignore[attr-defined]
            AssetSwap.non_par_repayment
        )
        AssetSwap.payBondCoupon = AssetSwap.pay_bond_coupon  # type: ignore[attr-defined]
        AssetSwap.isExpired = AssetSwap.is_expired  # type: ignore[attr-defined]
        AssetSwap.setPricingEngine = AssetSwap.set_pricing_engine  # type: ignore[attr-defined]

    ZeroCouponSwap = getattr(_ql, "ZeroCouponSwap", None)
    if ZeroCouponSwap is not None:
        ZeroCouponSwap.baseNominal = (  # type: ignore[attr-defined]
            ZeroCouponSwap.base_nominal
        )
        ZeroCouponSwap.startDate = ZeroCouponSwap.start_date  # type: ignore[attr-defined]
        ZeroCouponSwap.maturityDate = (  # type: ignore[attr-defined]
            ZeroCouponSwap.maturity_date
        )
        ZeroCouponSwap.fixedPayment = (  # type: ignore[attr-defined]
            ZeroCouponSwap.fixed_payment
        )
        ZeroCouponSwap.fixedLegNPV = (  # type: ignore[attr-defined]
            ZeroCouponSwap.fixed_leg_NPV
        )
        ZeroCouponSwap.floatingLegNPV = (  # type: ignore[attr-defined]
            ZeroCouponSwap.floating_leg_NPV
        )
        ZeroCouponSwap.fairFixedPayment = (  # type: ignore[attr-defined]
            ZeroCouponSwap.fair_fixed_payment
        )
        ZeroCouponSwap.fairFixedRate = (  # type: ignore[attr-defined]
            ZeroCouponSwap.fair_fixed_rate
        )
        ZeroCouponSwap.isExpired = ZeroCouponSwap.is_expired  # type: ignore[attr-defined]
        ZeroCouponSwap.setPricingEngine = (  # type: ignore[attr-defined]
            ZeroCouponSwap.set_pricing_engine
        )

    Swaption = getattr(_ql, "Swaption", None)
    if Swaption is not None:
        Swaption.setPricingEngine = Swaption.set_pricing_engine  # type: ignore[attr-defined]
        Swaption.settlementType = Swaption.settlement_type  # type: ignore[attr-defined]
        Swaption.settlementMethod = Swaption.settlement_method  # type: ignore[attr-defined]
        Swaption.isExpired = Swaption.is_expired  # type: ignore[attr-defined]
        if hasattr(Swaption, "implied_volatility"):
            Swaption.impliedVolatility = (  # type: ignore[attr-defined]
                Swaption.implied_volatility
            )
        if hasattr(Swaption, "set_tree_pricing_engine"):
            Swaption.setTreePricingEngine = (  # type: ignore[attr-defined]
                Swaption.set_tree_pricing_engine
            )
        if hasattr(Swaption, "set_jamshidian_pricing_engine"):
            Swaption.setJamshidianPricingEngine = (  # type: ignore[attr-defined]
                Swaption.set_jamshidian_pricing_engine
            )
        if hasattr(Swaption, "set_gaussian1d_pricing_engine"):
            Swaption.setGaussian1dPricingEngine = (  # type: ignore[attr-defined]
                Swaption.set_gaussian1d_pricing_engine
            )
        if hasattr(Swaption, "set_fd_hullwhite_pricing_engine"):
            Swaption.setFdHullWhitePricingEngine = (  # type: ignore[attr-defined]
                Swaption.set_fd_hullwhite_pricing_engine
            )

    CreditDefaultSwap = getattr(_ql, "CreditDefaultSwap", None)
    if CreditDefaultSwap is not None:
        CreditDefaultSwap.fairSpread = CreditDefaultSwap.fair_spread  # type: ignore[attr-defined]
        CreditDefaultSwap.fairUpfront = CreditDefaultSwap.fair_upfront  # type: ignore[attr-defined]
        CreditDefaultSwap.couponLegNPV = (  # type: ignore[attr-defined]
            CreditDefaultSwap.coupon_leg_NPV
        )
        CreditDefaultSwap.defaultLegNPV = (  # type: ignore[attr-defined]
            CreditDefaultSwap.default_leg_NPV
        )
        CreditDefaultSwap.runningSpread = (  # type: ignore[attr-defined]
            CreditDefaultSwap.running_spread
        )
        CreditDefaultSwap.setPricingEngine = (  # type: ignore[attr-defined]
            CreditDefaultSwap.set_pricing_engine
        )
        CreditDefaultSwap.isExpired = CreditDefaultSwap.is_expired  # type: ignore[attr-defined]
        if hasattr(CreditDefaultSwap, "set_isda_pricing_engine"):
            CreditDefaultSwap.setIsdaPricingEngine = (  # type: ignore[attr-defined]
                CreditDefaultSwap.set_isda_pricing_engine
            )

    CdsOption = getattr(_ql, "CdsOption", None)
    if CdsOption is not None:
        CdsOption.setPricingEngine = CdsOption.set_pricing_engine  # type: ignore[attr-defined]
        CdsOption.isExpired = CdsOption.is_expired  # type: ignore[attr-defined]
        CdsOption.atmRate = CdsOption.atm_rate  # type: ignore[attr-defined]
        CdsOption.riskyAnnuity = CdsOption.risky_annuity  # type: ignore[attr-defined]
        if hasattr(CdsOption, "implied_volatility"):
            CdsOption.impliedVolatility = (  # type: ignore[attr-defined]
                CdsOption.implied_volatility
            )

    BermudanExercise = getattr(_ql, "BermudanExercise", None)
    if BermudanExercise is not None:
        BermudanExercise.lastDate = BermudanExercise.last_date  # type: ignore[attr-defined]

    DefaultProbabilityTermStructureHandle = getattr(
        _ql, "DefaultProbabilityTermStructureHandle", None
    )
    if DefaultProbabilityTermStructureHandle is not None:
        DefaultProbabilityTermStructureHandle.survivalProbability = (  # type: ignore[attr-defined]
            DefaultProbabilityTermStructureHandle.survival_probability
        )
        DefaultProbabilityTermStructureHandle.hazardRate = (  # type: ignore[attr-defined]
            DefaultProbabilityTermStructureHandle.hazard_rate
        )
        DefaultProbabilityTermStructureHandle.referenceDate = (  # type: ignore[attr-defined]
            DefaultProbabilityTermStructureHandle.reference_date
        )
        if hasattr(DefaultProbabilityTermStructureHandle, "default_probability"):
            DefaultProbabilityTermStructureHandle.defaultProbability = (  # type: ignore[attr-defined]
                DefaultProbabilityTermStructureHandle.default_probability
            )
        if hasattr(DefaultProbabilityTermStructureHandle, "max_date"):
            DefaultProbabilityTermStructureHandle.maxDate = (  # type: ignore[attr-defined]
                DefaultProbabilityTermStructureHandle.max_date
            )

    Gsr = getattr(_ql, "Gsr", None)
    if Gsr is not None and hasattr(Gsr, "numeraire_time"):
        Gsr.numeraireTime = Gsr.numeraire_time  # type: ignore[attr-defined]

    EuropeanOption = _ql.EuropeanOption
    EuropeanOption.setPricingEngine = EuropeanOption.set_pricing_engine  # type: ignore[attr-defined]
    EuropeanOption.impliedVolatility = EuropeanOption.implied_volatility  # type: ignore[attr-defined]
    if hasattr(EuropeanOption, "set_dividend_pricing_engine"):
        EuropeanOption.setDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_cash_dividend_pricing_engine"):
        EuropeanOption.setCashDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_cash_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_dividend_pricing_engine"):
        EuropeanOption.setFdDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_quanto_pricing_engine"):
        EuropeanOption.setFdQuantoPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_quanto_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_quanto_dividend_pricing_engine"):
        EuropeanOption.setFdQuantoDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_quanto_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_heston_dividend_pricing_engine"):
        EuropeanOption.setFdHestonDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_heston_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_heston_quanto_pricing_engine"):
        EuropeanOption.setFdHestonQuantoPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_heston_quanto_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_heston_quanto_dividend_pricing_engine"):
        EuropeanOption.setFdHestonQuantoDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_heston_quanto_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_heston_pricing_engine"):
        EuropeanOption.setHestonPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_heston_pricing_engine
        )
    if hasattr(EuropeanOption, "set_mc_heston_pricing_engine"):
        EuropeanOption.setMcHestonPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_mc_heston_pricing_engine
        )
    if hasattr(EuropeanOption, "error_estimate"):
        EuropeanOption.errorEstimate = (  # type: ignore[attr-defined]
            EuropeanOption.error_estimate
        )
    if hasattr(EuropeanOption, "set_cos_heston_pricing_engine"):
        EuropeanOption.setCosHestonPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_cos_heston_pricing_engine
        )
    if hasattr(EuropeanOption, "set_exponential_fitting_heston_pricing_engine"):
        EuropeanOption.setExponentialFittingHestonPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_exponential_fitting_heston_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_heston_pricing_engine"):
        EuropeanOption.setFdHestonPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_heston_pricing_engine
        )
    if hasattr(EuropeanOption, "set_bates_pricing_engine"):
        EuropeanOption.setBatesPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_bates_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_bates_pricing_engine"):
        EuropeanOption.setFdBatesPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_bates_pricing_engine
        )
    if hasattr(EuropeanOption, "set_fd_bates_dividend_pricing_engine"):
        EuropeanOption.setFdBatesDividendPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_fd_bates_dividend_pricing_engine
        )
    if hasattr(EuropeanOption, "set_bates_det_jump_pricing_engine"):
        EuropeanOption.setBatesDetJumpPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_bates_det_jump_pricing_engine
        )
    if hasattr(EuropeanOption, "set_bates_double_exp_pricing_engine"):
        EuropeanOption.setBatesDoubleExpPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_bates_double_exp_pricing_engine
        )
    if hasattr(EuropeanOption, "set_bates_double_exp_det_jump_pricing_engine"):
        EuropeanOption.setBatesDoubleExpDetJumpPricingEngine = (  # type: ignore[attr-defined]
            EuropeanOption.set_bates_double_exp_det_jump_pricing_engine
        )

    VanillaOption = _ql.VanillaOption
    VanillaOption.setPricingEngine = VanillaOption.set_pricing_engine  # type: ignore[attr-defined]
    if hasattr(VanillaOption, "set_dividend_pricing_engine"):
        VanillaOption.setDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_cash_dividend_pricing_engine"):
        VanillaOption.setCashDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_cash_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_dividend_pricing_engine"):
        VanillaOption.setFdDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_quanto_pricing_engine"):
        VanillaOption.setFdQuantoPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_quanto_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_quanto_dividend_pricing_engine"):
        VanillaOption.setFdQuantoDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_quanto_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_heston_dividend_pricing_engine"):
        VanillaOption.setFdHestonDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_heston_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_heston_quanto_pricing_engine"):
        VanillaOption.setFdHestonQuantoPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_heston_quanto_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_heston_quanto_dividend_pricing_engine"):
        VanillaOption.setFdHestonQuantoDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_heston_quanto_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_binomial_pricing_engine"):
        VanillaOption.setBinomialPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_binomial_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_pricing_engine"):
        VanillaOption.setFdPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_pricing_engine
        )
    if hasattr(VanillaOption, "set_heston_pricing_engine"):
        VanillaOption.setHestonPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_heston_pricing_engine
        )
    if hasattr(VanillaOption, "set_mc_heston_pricing_engine"):
        VanillaOption.setMcHestonPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_mc_heston_pricing_engine
        )
    if hasattr(VanillaOption, "error_estimate"):
        VanillaOption.errorEstimate = (  # type: ignore[attr-defined]
            VanillaOption.error_estimate
        )
    if hasattr(VanillaOption, "set_cos_heston_pricing_engine"):
        VanillaOption.setCosHestonPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_cos_heston_pricing_engine
        )
    if hasattr(VanillaOption, "set_exponential_fitting_heston_pricing_engine"):
        VanillaOption.setExponentialFittingHestonPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_exponential_fitting_heston_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_heston_pricing_engine"):
        VanillaOption.setFdHestonPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_heston_pricing_engine
        )
    if hasattr(VanillaOption, "set_bates_pricing_engine"):
        VanillaOption.setBatesPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_bates_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_bates_pricing_engine"):
        VanillaOption.setFdBatesPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_bates_pricing_engine
        )
    if hasattr(VanillaOption, "set_fd_bates_dividend_pricing_engine"):
        VanillaOption.setFdBatesDividendPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_fd_bates_dividend_pricing_engine
        )
    if hasattr(VanillaOption, "set_bates_det_jump_pricing_engine"):
        VanillaOption.setBatesDetJumpPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_bates_det_jump_pricing_engine
        )
    if hasattr(VanillaOption, "set_bates_double_exp_pricing_engine"):
        VanillaOption.setBatesDoubleExpPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_bates_double_exp_pricing_engine
        )
    if hasattr(VanillaOption, "set_bates_double_exp_det_jump_pricing_engine"):
        VanillaOption.setBatesDoubleExpDetJumpPricingEngine = (  # type: ignore[attr-defined]
            VanillaOption.set_bates_double_exp_det_jump_pricing_engine
        )

    # Phase-39 / Phase-46 Bates aliases.
    BatesDetJumpModel = getattr(_ql, "BatesDetJumpModel", None)
    if BatesDetJumpModel is not None:
        if hasattr(BatesDetJumpModel, "jump_intensity"):
            BatesDetJumpModel.jumpIntensity = (  # type: ignore[attr-defined]
                BatesDetJumpModel.jump_intensity
            )
        if hasattr(BatesDetJumpModel, "kappa_lambda"):
            BatesDetJumpModel.kappaLambda = (  # type: ignore[attr-defined]
                BatesDetJumpModel.kappa_lambda
            )
        if hasattr(BatesDetJumpModel, "theta_lambda"):
            BatesDetJumpModel.thetaLambda = (  # type: ignore[attr-defined]
                BatesDetJumpModel.theta_lambda
            )
    BatesDoubleExpModel = getattr(_ql, "BatesDoubleExpModel", None)
    if BatesDoubleExpModel is not None:
        if hasattr(BatesDoubleExpModel, "jump_intensity"):
            BatesDoubleExpModel.jumpIntensity = (  # type: ignore[attr-defined]
                BatesDoubleExpModel.jump_intensity
            )
        if hasattr(BatesDoubleExpModel, "nu_up"):
            BatesDoubleExpModel.nuUp = BatesDoubleExpModel.nu_up  # type: ignore[attr-defined]
        if hasattr(BatesDoubleExpModel, "nu_down"):
            BatesDoubleExpModel.nuDown = (  # type: ignore[attr-defined]
                BatesDoubleExpModel.nu_down
            )
    BatesDoubleExpDetJumpModel = getattr(_ql, "BatesDoubleExpDetJumpModel", None)
    if BatesDoubleExpDetJumpModel is not None:
        if hasattr(BatesDoubleExpDetJumpModel, "jump_intensity"):
            BatesDoubleExpDetJumpModel.jumpIntensity = (  # type: ignore[attr-defined]
                BatesDoubleExpDetJumpModel.jump_intensity
            )
        if hasattr(BatesDoubleExpDetJumpModel, "nu_up"):
            BatesDoubleExpDetJumpModel.nuUp = (  # type: ignore[attr-defined]
                BatesDoubleExpDetJumpModel.nu_up
            )
        if hasattr(BatesDoubleExpDetJumpModel, "nu_down"):
            BatesDoubleExpDetJumpModel.nuDown = (  # type: ignore[attr-defined]
                BatesDoubleExpDetJumpModel.nu_down
            )
        if hasattr(BatesDoubleExpDetJumpModel, "kappa_lambda"):
            BatesDoubleExpDetJumpModel.kappaLambda = (  # type: ignore[attr-defined]
                BatesDoubleExpDetJumpModel.kappa_lambda
            )
        if hasattr(BatesDoubleExpDetJumpModel, "theta_lambda"):
            BatesDoubleExpDetJumpModel.thetaLambda = (  # type: ignore[attr-defined]
                BatesDoubleExpDetJumpModel.theta_lambda
            )

    # Phase-39 Bates aliases.
    BatesProcess = getattr(_ql, "BatesProcess", None)
    if BatesProcess is not None and hasattr(BatesProcess, "jump_intensity"):
        BatesProcess.jumpIntensity = BatesProcess.jump_intensity  # type: ignore[attr-defined]
    BatesModel = getattr(_ql, "BatesModel", None)
    if BatesModel is not None and hasattr(BatesModel, "jump_intensity"):
        BatesModel.jumpIntensity = BatesModel.jump_intensity  # type: ignore[attr-defined]

    # Phase-48 Heston calibration aliases.
    HestonModelHelper = getattr(_ql, "HestonModelHelper", None)
    if HestonModelHelper is not None:
        HestonModelHelper.setPricingEngine = (  # type: ignore[attr-defined]
            HestonModelHelper.set_pricing_engine
        )
        if hasattr(HestonModelHelper, "set_cos_heston_pricing_engine"):
            HestonModelHelper.setCosHestonPricingEngine = (  # type: ignore[attr-defined]
                HestonModelHelper.set_cos_heston_pricing_engine
            )
        if hasattr(
            HestonModelHelper, "set_exponential_fitting_heston_pricing_engine"
        ):
            HestonModelHelper.setExponentialFittingHestonPricingEngine = (  # type: ignore[attr-defined]
                HestonModelHelper.set_exponential_fitting_heston_pricing_engine
            )
        if hasattr(HestonModelHelper, "calibration_error"):
            HestonModelHelper.calibrationError = (  # type: ignore[attr-defined]
                HestonModelHelper.calibration_error
            )
        if hasattr(HestonModelHelper, "market_value"):
            HestonModelHelper.marketValue = (  # type: ignore[attr-defined]
                HestonModelHelper.market_value
            )
        if hasattr(HestonModelHelper, "model_value"):
            HestonModelHelper.modelValue = (  # type: ignore[attr-defined]
                HestonModelHelper.model_value
            )
    HestonModel = getattr(_ql, "HestonModel", None)
    if HestonModel is not None:
        if hasattr(HestonModel, "set_params"):
            HestonModel.setParams = HestonModel.set_params  # type: ignore[attr-defined]
        if hasattr(HestonModel, "end_criteria"):
            HestonModel.endCriteria = HestonModel.end_criteria  # type: ignore[attr-defined]

    OvernightIndexedSwap = getattr(_ql, "OvernightIndexedSwap", None)
    if OvernightIndexedSwap is not None:
        OvernightIndexedSwap.fairRate = OvernightIndexedSwap.fair_rate  # type: ignore[attr-defined]
        OvernightIndexedSwap.fairSpread = (  # type: ignore[attr-defined]
            OvernightIndexedSwap.fair_spread
        )
        OvernightIndexedSwap.setPricingEngine = (  # type: ignore[attr-defined]
            OvernightIndexedSwap.set_pricing_engine
        )

    IborIndex = _ql.IborIndex
    IborIndex.fixingCalendar = IborIndex.fixing_calendar  # type: ignore[attr-defined]
    IborIndex.dayCounter = IborIndex.day_counter  # type: ignore[attr-defined]
    IborIndex.fixingDays = IborIndex.fixing_days  # type: ignore[attr-defined]
    IborIndex.addFixing = IborIndex.add_fixing  # type: ignore[attr-defined]

    OvernightIndex = getattr(_ql, "OvernightIndex", None)
    if OvernightIndex is not None:
        OvernightIndex.fixingCalendar = OvernightIndex.fixing_calendar  # type: ignore[attr-defined]
        OvernightIndex.dayCounter = OvernightIndex.day_counter  # type: ignore[attr-defined]
        OvernightIndex.fixingDays = OvernightIndex.fixing_days  # type: ignore[attr-defined]
        OvernightIndex.addFixing = OvernightIndex.add_fixing  # type: ignore[attr-defined]

    PlainVanillaPayoff = _ql.PlainVanillaPayoff
    PlainVanillaPayoff.optionType = PlainVanillaPayoff.option_type  # type: ignore[attr-defined]

    CashOrNothingPayoff = getattr(_ql, "CashOrNothingPayoff", None)
    if CashOrNothingPayoff is not None:
        CashOrNothingPayoff.optionType = (  # type: ignore[attr-defined]
            CashOrNothingPayoff.option_type
        )
        CashOrNothingPayoff.cashPayoff = (  # type: ignore[attr-defined]
            CashOrNothingPayoff.cash_payoff
        )

    AssetOrNothingPayoff = getattr(_ql, "AssetOrNothingPayoff", None)
    if AssetOrNothingPayoff is not None:
        AssetOrNothingPayoff.optionType = (  # type: ignore[attr-defined]
            AssetOrNothingPayoff.option_type
        )

    FloatingTypePayoff = getattr(_ql, "FloatingTypePayoff", None)
    if FloatingTypePayoff is not None:
        FloatingTypePayoff.optionType = (  # type: ignore[attr-defined]
            FloatingTypePayoff.option_type
        )

    PercentageStrikePayoff = getattr(_ql, "PercentageStrikePayoff", None)
    if PercentageStrikePayoff is not None:
        PercentageStrikePayoff.optionType = (  # type: ignore[attr-defined]
            PercentageStrikePayoff.option_type
        )

    ContinuousFloatingLookbackOption = getattr(
        _ql, "ContinuousFloatingLookbackOption", None
    )
    if ContinuousFloatingLookbackOption is not None:
        ContinuousFloatingLookbackOption.setPricingEngine = (  # type: ignore[attr-defined]
            ContinuousFloatingLookbackOption.set_pricing_engine
        )
        if hasattr(ContinuousFloatingLookbackOption, "set_mc_pricing_engine"):
            ContinuousFloatingLookbackOption.setMcPricingEngine = (  # type: ignore[attr-defined]
                ContinuousFloatingLookbackOption.set_mc_pricing_engine
            )
        if hasattr(ContinuousFloatingLookbackOption, "error_estimate"):
            ContinuousFloatingLookbackOption.errorEstimate = (  # type: ignore[attr-defined]
                ContinuousFloatingLookbackOption.error_estimate
            )

    ContinuousFixedLookbackOption = getattr(
        _ql, "ContinuousFixedLookbackOption", None
    )
    if ContinuousFixedLookbackOption is not None:
        ContinuousFixedLookbackOption.setPricingEngine = (  # type: ignore[attr-defined]
            ContinuousFixedLookbackOption.set_pricing_engine
        )
        if hasattr(ContinuousFixedLookbackOption, "set_mc_pricing_engine"):
            ContinuousFixedLookbackOption.setMcPricingEngine = (  # type: ignore[attr-defined]
                ContinuousFixedLookbackOption.set_mc_pricing_engine
            )
        if hasattr(ContinuousFixedLookbackOption, "error_estimate"):
            ContinuousFixedLookbackOption.errorEstimate = (  # type: ignore[attr-defined]
                ContinuousFixedLookbackOption.error_estimate
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
    if ContinuousPartialFloatingLookbackOption is not None:
        ContinuousPartialFloatingLookbackOption.setPricingEngine = (  # type: ignore[attr-defined]
            ContinuousPartialFloatingLookbackOption.set_pricing_engine
        )
        if hasattr(ContinuousPartialFloatingLookbackOption, "set_mc_pricing_engine"):
            ContinuousPartialFloatingLookbackOption.setMcPricingEngine = (  # type: ignore[attr-defined]
                ContinuousPartialFloatingLookbackOption.set_mc_pricing_engine
            )
        if hasattr(ContinuousPartialFloatingLookbackOption, "error_estimate"):
            ContinuousPartialFloatingLookbackOption.errorEstimate = (  # type: ignore[attr-defined]
                ContinuousPartialFloatingLookbackOption.error_estimate
            )

    ContinuousPartialFixedLookbackOption = getattr(
        _ql, "ContinuousPartialFixedLookbackOption", None
    )
    if ContinuousPartialFixedLookbackOption is not None:
        ContinuousPartialFixedLookbackOption.setPricingEngine = (  # type: ignore[attr-defined]
            ContinuousPartialFixedLookbackOption.set_pricing_engine
        )
        if hasattr(ContinuousPartialFixedLookbackOption, "set_mc_pricing_engine"):
            ContinuousPartialFixedLookbackOption.setMcPricingEngine = (  # type: ignore[attr-defined]
                ContinuousPartialFixedLookbackOption.set_mc_pricing_engine
            )
        if hasattr(ContinuousPartialFixedLookbackOption, "error_estimate"):
            ContinuousPartialFixedLookbackOption.errorEstimate = (  # type: ignore[attr-defined]
                ContinuousPartialFixedLookbackOption.error_estimate
            )

    AnalyticContinuousPartialFloatingLookbackEngine = getattr(
        _ql, "AnalyticContinuousPartialFloatingLookbackEngine", None
    )
    AnalyticContinuousPartialFixedLookbackEngine = getattr(
        _ql, "AnalyticContinuousPartialFixedLookbackEngine", None
    )

    EuropeanExercise = _ql.EuropeanExercise
    EuropeanExercise.lastDate = EuropeanExercise.last_date  # type: ignore[attr-defined]

    AmericanExercise = _ql.AmericanExercise
    AmericanExercise.lastDate = AmericanExercise.last_date  # type: ignore[attr-defined]

    ForwardRateAgreement = _ql.ForwardRateAgreement
    ForwardRateAgreement.forwardRate = ForwardRateAgreement.forward_rate  # type: ignore[attr-defined]
    ForwardRateAgreement.fixingDate = ForwardRateAgreement.fixing_date  # type: ignore[attr-defined]

    BondForward = getattr(_ql, "BondForward", None)
    if BondForward is not None:
        BondForward.cleanForwardPrice = (  # type: ignore[attr-defined]
            BondForward.clean_forward_price
        )
        BondForward.forwardPrice = BondForward.forward_price  # type: ignore[attr-defined]
        BondForward.forwardValue = BondForward.forward_value  # type: ignore[attr-defined]
        BondForward.spotValue = BondForward.spot_value  # type: ignore[attr-defined]
        BondForward.spotIncome = BondForward.spot_income  # type: ignore[attr-defined]
        BondForward.settlementDate = (  # type: ignore[attr-defined]
            BondForward.settlement_date
        )
        BondForward.isExpired = BondForward.is_expired  # type: ignore[attr-defined]

    # Phase-4 / Phase-31 barrier instruments (present when bindings are built).
    BarrierOption = getattr(_ql, "BarrierOption", None)
    AnalyticBinaryBarrierEngine = getattr(
        _ql, "AnalyticBinaryBarrierEngine", None
    )
    if BarrierOption is not None:
        BarrierOption.setPricingEngine = BarrierOption.set_pricing_engine  # type: ignore[attr-defined]
        if hasattr(BarrierOption, "set_binary_pricing_engine"):
            BarrierOption.setBinaryPricingEngine = (  # type: ignore[attr-defined]
                BarrierOption.set_binary_pricing_engine
            )
        if hasattr(BarrierOption, "set_fd_heston_pricing_engine"):
            BarrierOption.setFdHestonPricingEngine = (  # type: ignore[attr-defined]
                BarrierOption.set_fd_heston_pricing_engine
            )
        if hasattr(BarrierOption, "set_fd_heston_dividend_pricing_engine"):
            BarrierOption.setFdHestonDividendPricingEngine = (  # type: ignore[attr-defined]
                BarrierOption.set_fd_heston_dividend_pricing_engine
            )
        if hasattr(BarrierOption, "set_fd_pricing_engine"):
            BarrierOption.setFdPricingEngine = (  # type: ignore[attr-defined]
                BarrierOption.set_fd_pricing_engine
            )
        if hasattr(BarrierOption, "set_fd_dividend_pricing_engine"):
            BarrierOption.setFdDividendPricingEngine = (  # type: ignore[attr-defined]
                BarrierOption.set_fd_dividend_pricing_engine
            )
        if hasattr(BarrierOption, "implied_volatility"):
            BarrierOption.impliedVolatility = (  # type: ignore[attr-defined]
                BarrierOption.implied_volatility
            )
        if hasattr(BarrierOption, "set_mc_pricing_engine"):
            BarrierOption.setMcPricingEngine = (  # type: ignore[attr-defined]
                BarrierOption.set_mc_pricing_engine
            )
        if hasattr(BarrierOption, "error_estimate"):
            BarrierOption.errorEstimate = (  # type: ignore[attr-defined]
                BarrierOption.error_estimate
            )

    # Phase-29 soft barrier aliases.
    SoftBarrierOption = getattr(_ql, "SoftBarrierOption", None)
    AnalyticSoftBarrierEngine = getattr(_ql, "AnalyticSoftBarrierEngine", None)
    if SoftBarrierOption is not None:
        SoftBarrierOption.setPricingEngine = (  # type: ignore[attr-defined]
            SoftBarrierOption.set_pricing_engine
        )
        if hasattr(SoftBarrierOption, "implied_volatility"):
            SoftBarrierOption.impliedVolatility = (  # type: ignore[attr-defined]
                SoftBarrierOption.implied_volatility
            )

    # Phase-30 partial-time barrier aliases.
    PartialBarrierRange = getattr(_ql, "PartialBarrierRange", None)
    PartialTimeBarrierOption = getattr(_ql, "PartialTimeBarrierOption", None)
    AnalyticPartialTimeBarrierOptionEngine = getattr(
        _ql, "AnalyticPartialTimeBarrierOptionEngine", None
    )
    if PartialTimeBarrierOption is not None:
        PartialTimeBarrierOption.setPricingEngine = (  # type: ignore[attr-defined]
            PartialTimeBarrierOption.set_pricing_engine
        )

    # Phase-32 two-asset barrier aliases.
    TwoAssetBarrierOption = getattr(_ql, "TwoAssetBarrierOption", None)
    if TwoAssetBarrierOption is not None:
        TwoAssetBarrierOption.setPricingEngine = (  # type: ignore[attr-defined]
            TwoAssetBarrierOption.set_pricing_engine
        )
        TwoAssetBarrierOption.isExpired = (  # type: ignore[attr-defined]
            TwoAssetBarrierOption.is_expired
        )

    # Phase-33 two-asset correlation aliases.
    TwoAssetCorrelationOption = getattr(_ql, "TwoAssetCorrelationOption", None)
    if TwoAssetCorrelationOption is not None:
        TwoAssetCorrelationOption.setPricingEngine = (  # type: ignore[attr-defined]
            TwoAssetCorrelationOption.set_pricing_engine
        )
        TwoAssetCorrelationOption.isExpired = (  # type: ignore[attr-defined]
            TwoAssetCorrelationOption.is_expired
        )

    # Phase-34 cliquet aliases.
    CliquetOption = getattr(_ql, "CliquetOption", None)
    if CliquetOption is not None:
        CliquetOption.setPricingEngine = (  # type: ignore[attr-defined]
            CliquetOption.set_pricing_engine
        )
        CliquetOption.isExpired = CliquetOption.is_expired  # type: ignore[attr-defined]

    CompoundOption = getattr(_ql, "CompoundOption", None)
    if CompoundOption is not None:
        CompoundOption.setPricingEngine = (  # type: ignore[attr-defined]
            CompoundOption.set_pricing_engine
        )
        CompoundOption.isExpired = CompoundOption.is_expired  # type: ignore[attr-defined]

    # Phase-75 Margrabe exchange-option aliases.
    MargrabeOption = getattr(_ql, "MargrabeOption", None)
    if MargrabeOption is not None:
        MargrabeOption.setPricingEngine = (  # type: ignore[attr-defined]
            MargrabeOption.set_pricing_engine
        )
        MargrabeOption.setAmericanPricingEngine = (  # type: ignore[attr-defined]
            MargrabeOption.set_american_pricing_engine
        )
        MargrabeOption.isExpired = MargrabeOption.is_expired  # type: ignore[attr-defined]

    # Phase-76 simple / complex chooser aliases.
    SimpleChooserOption = getattr(_ql, "SimpleChooserOption", None)
    if SimpleChooserOption is not None:
        SimpleChooserOption.setPricingEngine = (  # type: ignore[attr-defined]
            SimpleChooserOption.set_pricing_engine
        )
        SimpleChooserOption.isExpired = SimpleChooserOption.is_expired  # type: ignore[attr-defined]
    ComplexChooserOption = getattr(_ql, "ComplexChooserOption", None)
    if ComplexChooserOption is not None:
        ComplexChooserOption.setPricingEngine = (  # type: ignore[attr-defined]
            ComplexChooserOption.set_pricing_engine
        )
        ComplexChooserOption.isExpired = ComplexChooserOption.is_expired  # type: ignore[attr-defined]

    # Phase-83 holder / writer extensible aliases.
    HolderExtensibleOption = getattr(_ql, "HolderExtensibleOption", None)
    if HolderExtensibleOption is not None:
        HolderExtensibleOption.setPricingEngine = (  # type: ignore[attr-defined]
            HolderExtensibleOption.set_pricing_engine
        )
        HolderExtensibleOption.isExpired = (  # type: ignore[attr-defined]
            HolderExtensibleOption.is_expired
        )
    WriterExtensibleOption = getattr(_ql, "WriterExtensibleOption", None)
    if WriterExtensibleOption is not None:
        WriterExtensibleOption.setPricingEngine = (  # type: ignore[attr-defined]
            WriterExtensibleOption.set_pricing_engine
        )
        WriterExtensibleOption.isExpired = (  # type: ignore[attr-defined]
            WriterExtensibleOption.is_expired
        )

    # Phase-78 Kirk / Phase-79 Stulz basket aliases.
    SpreadBasketPayoff = getattr(_ql, "SpreadBasketPayoff", None)
    MinBasketPayoff = getattr(_ql, "MinBasketPayoff", None)
    MaxBasketPayoff = getattr(_ql, "MaxBasketPayoff", None)
    BasketOption = getattr(_ql, "BasketOption", None)
    if BasketOption is not None:
        if hasattr(BasketOption, "set_kirk_pricing_engine"):
            BasketOption.setKirkPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_kirk_pricing_engine
            )
        if hasattr(BasketOption, "set_stulz_pricing_engine"):
            BasketOption.setStulzPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_stulz_pricing_engine
            )
        if hasattr(BasketOption, "set_choi_pricing_engine"):
            BasketOption.setChoiPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_choi_pricing_engine
            )
        if hasattr(BasketOption, "set_single_factor_pricing_engine"):
            BasketOption.setSingleFactorPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_single_factor_pricing_engine
            )
        if hasattr(BasketOption, "set_deng_li_zhou_pricing_engine"):
            BasketOption.setDengLiZhouPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_deng_li_zhou_pricing_engine
            )
        if hasattr(BasketOption, "set_bjerksund_stensland_pricing_engine"):
            BasketOption.setBjerksundStenslandPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_bjerksund_stensland_pricing_engine
            )
        if hasattr(BasketOption, "set_pearson_pricing_engine"):
            BasketOption.setPearsonPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_pearson_pricing_engine
            )
        if hasattr(BasketOption, "set_operator_splitting_pricing_engine"):
            BasketOption.setOperatorSplittingPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_operator_splitting_pricing_engine
            )
        if hasattr(BasketOption, "set_gaussian_copula_pricing_engine"):
            BasketOption.setGaussianCopulaPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_gaussian_copula_pricing_engine
            )
        if hasattr(BasketOption, "set_fd_2d_pricing_engine"):
            BasketOption.setFd2dPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_fd_2d_pricing_engine
            )
        if hasattr(BasketOption, "set_fd_ndim_pricing_engine"):
            BasketOption.setFdNdimPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_fd_ndim_pricing_engine
            )
        if hasattr(BasketOption, "set_mc_european_pricing_engine"):
            BasketOption.setMCEuropeanPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_mc_european_pricing_engine
            )
        if hasattr(BasketOption, "set_mc_american_pricing_engine"):
            BasketOption.setMCAmericanPricingEngine = (  # type: ignore[attr-defined]
                BasketOption.set_mc_american_pricing_engine
            )
        if hasattr(BasketOption, "is_expired"):
            BasketOption.isExpired = BasketOption.is_expired  # type: ignore[attr-defined]

    # Phase-80 variance-swap aliases.
    VarianceSwap = getattr(_ql, "VarianceSwap", None)
    if VarianceSwap is not None:
        VarianceSwap.setReplicatingPricingEngine = (  # type: ignore[attr-defined]
            VarianceSwap.set_replicating_pricing_engine
        )
        VarianceSwap.isExpired = VarianceSwap.is_expired  # type: ignore[attr-defined]
        VarianceSwap.startDate = VarianceSwap.start_date  # type: ignore[attr-defined]
        VarianceSwap.maturityDate = VarianceSwap.maturity_date  # type: ignore[attr-defined]
        if hasattr(VarianceSwap, "set_mc_pricing_engine"):
            VarianceSwap.setMcPricingEngine = (  # type: ignore[attr-defined]
                VarianceSwap.set_mc_pricing_engine
            )

    # Phase-35 forward vanilla aliases.
    ForwardVanillaOption = getattr(_ql, "ForwardVanillaOption", None)
    if ForwardVanillaOption is not None:
        ForwardVanillaOption.setPricingEngine = (  # type: ignore[attr-defined]
            ForwardVanillaOption.set_pricing_engine
        )
        if hasattr(ForwardVanillaOption, "set_performance_pricing_engine"):
            ForwardVanillaOption.setPerformancePricingEngine = (  # type: ignore[attr-defined]
                ForwardVanillaOption.set_performance_pricing_engine
            )
        ForwardVanillaOption.isExpired = (  # type: ignore[attr-defined]
            ForwardVanillaOption.is_expired
        )

    # Phase-25/26 double-barrier aliases.
    DoubleBarrierType = getattr(_ql, "DoubleBarrierType", None)
    DoubleBarrierOption = getattr(_ql, "DoubleBarrierOption", None)
    AnalyticDoubleBarrierEngine = getattr(
        _ql, "AnalyticDoubleBarrierEngine", None
    )
    AnalyticDoubleBarrierBinaryEngine = getattr(
        _ql, "AnalyticDoubleBarrierBinaryEngine", None
    )
    if DoubleBarrierOption is not None:
        DoubleBarrierOption.setPricingEngine = (  # type: ignore[attr-defined]
            DoubleBarrierOption.set_pricing_engine
        )
        if hasattr(DoubleBarrierOption, "implied_volatility"):
            DoubleBarrierOption.impliedVolatility = (  # type: ignore[attr-defined]
                DoubleBarrierOption.implied_volatility
            )
        if hasattr(DoubleBarrierOption, "set_binary_pricing_engine"):
            DoubleBarrierOption.setBinaryPricingEngine = (  # type: ignore[attr-defined]
                DoubleBarrierOption.set_binary_pricing_engine
            )
        if hasattr(DoubleBarrierOption, "set_fd_heston_pricing_engine"):
            DoubleBarrierOption.setFdHestonPricingEngine = (  # type: ignore[attr-defined]
                DoubleBarrierOption.set_fd_heston_pricing_engine
            )
        if hasattr(DoubleBarrierOption, "set_mc_pricing_engine"):
            DoubleBarrierOption.setMcPricingEngine = (  # type: ignore[attr-defined]
                DoubleBarrierOption.set_mc_pricing_engine
            )
        if hasattr(DoubleBarrierOption, "error_estimate"):
            DoubleBarrierOption.errorEstimate = (  # type: ignore[attr-defined]
                DoubleBarrierOption.error_estimate
            )

    CapFloor = getattr(_ql, "CapFloor", None)
    if CapFloor is not None:
        CapFloor.setPricingEngine = CapFloor.set_pricing_engine  # type: ignore[attr-defined]
        CapFloor.atmRate = CapFloor.atm_rate  # type: ignore[attr-defined]
        CapFloor.startDate = CapFloor.start_date  # type: ignore[attr-defined]
        CapFloor.maturityDate = CapFloor.maturity_date  # type: ignore[attr-defined]
        if hasattr(CapFloor, "implied_volatility"):
            CapFloor.impliedVolatility = (  # type: ignore[attr-defined]
                CapFloor.implied_volatility
            )


_install_aliases()


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
if ContinuousAveragingAsianOption is not None:
    ContinuousAveragingAsianOption.setPricingEngine = (  # type: ignore[attr-defined]
        ContinuousAveragingAsianOption.set_pricing_engine
    )
if DiscreteAveragingAsianOption is not None:
    DiscreteAveragingAsianOption.setPricingEngine = (  # type: ignore[attr-defined]
        DiscreteAveragingAsianOption.set_pricing_engine
    )
    if hasattr(DiscreteAveragingAsianOption, "set_turnbull_wakeman_pricing_engine"):
        DiscreteAveragingAsianOption.setTurnbullWakemanPricingEngine = (  # type: ignore[attr-defined]
            DiscreteAveragingAsianOption.set_turnbull_wakeman_pricing_engine
        )
    if hasattr(DiscreteAveragingAsianOption, "is_expired"):
        DiscreteAveragingAsianOption.isExpired = (  # type: ignore[attr-defined]
            DiscreteAveragingAsianOption.is_expired
        )

# Phase-10 CMS / SwapIndex aliases.
EuriborSwapIsdaFixA = getattr(_ql, "EuriborSwapIsdaFixA", None)
ConstantSwaptionVolatility = getattr(_ql, "ConstantSwaptionVolatility", None)
AnalyticHaganPricer = getattr(_ql, "AnalyticHaganPricer", None)
NumericHaganPricer = getattr(_ql, "NumericHaganPricer", None)
makeCms = getattr(_ql, "make_cms", None)

CmsCoupon = getattr(_ql, "CmsCoupon", None)
if CmsCoupon is not None:
    CmsCoupon.setPricer = CmsCoupon.set_pricer  # type: ignore[attr-defined]
    CmsCoupon.accrualStartDate = CmsCoupon.accrual_start_date  # type: ignore[attr-defined]
    CmsCoupon.accrualEndDate = CmsCoupon.accrual_end_date  # type: ignore[attr-defined]

Swap = getattr(_ql, "Swap", None)
if Swap is not None:
    Swap.setPricingEngine = Swap.set_pricing_engine  # type: ignore[attr-defined]
    Swap.isExpired = Swap.is_expired  # type: ignore[attr-defined]
    Swap.numberOfLegs = Swap.number_of_legs  # type: ignore[attr-defined]
    if hasattr(Swap, "set_cms_coupon_pricer"):
        Swap.setCmsCouponPricer = Swap.set_cms_coupon_pricer  # type: ignore[attr-defined]

SwapIndex = getattr(_ql, "SwapIndex", None)
if SwapIndex is not None:
    SwapIndex.fixingDays = SwapIndex.fixing_days  # type: ignore[attr-defined]
    SwapIndex.fixingCalendar = SwapIndex.fixing_calendar  # type: ignore[attr-defined]
    SwapIndex.dayCounter = SwapIndex.day_counter  # type: ignore[attr-defined]
    if hasattr(SwapIndex, "add_fixing"):
        SwapIndex.addFixing = SwapIndex.add_fixing  # type: ignore[attr-defined]
    if hasattr(SwapIndex, "value_date"):
        SwapIndex.valueDate = SwapIndex.value_date  # type: ignore[attr-defined]

# Phase-11 CMS-spread aliases.
LinearTsrPricer = getattr(_ql, "LinearTsrPricer", None)
LognormalCmsSpreadPricer = getattr(_ql, "LognormalCmsSpreadPricer", None)
SwapSpreadIndex = getattr(_ql, "make_swap_spread_index", None)
CmsSpreadCoupon = getattr(_ql, "CmsSpreadCoupon", None)
if CmsSpreadCoupon is not None:
    CmsSpreadCoupon.setPricer = CmsSpreadCoupon.set_pricer  # type: ignore[attr-defined]
    CmsSpreadCoupon.fixingDate = CmsSpreadCoupon.fixing_date  # type: ignore[attr-defined]
CappedFlooredCmsSpreadCoupon = getattr(_ql, "CappedFlooredCmsSpreadCoupon", None)
if CappedFlooredCmsSpreadCoupon is not None:
    CappedFlooredCmsSpreadCoupon.setPricer = (  # type: ignore[attr-defined]
        CappedFlooredCmsSpreadCoupon.set_pricer
    )

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
if ZeroInflationIndex is not None:
    ZeroInflationIndex.addFixing = ZeroInflationIndex.add_fixing  # type: ignore[attr-defined]
    ZeroInflationIndex.clearFixings = (  # type: ignore[attr-defined]
        ZeroInflationIndex.clear_fixings
    )
    ZeroInflationIndex.lastFixingDate = (  # type: ignore[attr-defined]
        ZeroInflationIndex.last_fixing_date
    )
    ZeroInflationIndex.availabilityLag = (  # type: ignore[attr-defined]
        ZeroInflationIndex.availability_lag
    )

ZeroCouponInflationSwap = getattr(_ql, "ZeroCouponInflationSwap", None)
if ZeroCouponInflationSwap is not None:
    ZeroCouponInflationSwap.setPricingEngine = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.set_pricing_engine
    )
    ZeroCouponInflationSwap.fairRate = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.fair_rate
    )
    ZeroCouponInflationSwap.fixedRate = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.fixed_rate
    )
    ZeroCouponInflationSwap.fixedLegNPV = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.fixed_leg_NPV
    )
    ZeroCouponInflationSwap.inflationLegNPV = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.inflation_leg_NPV
    )
    ZeroCouponInflationSwap.inflationLeg = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.inflation_leg
    )
    ZeroCouponInflationSwap.fixedLeg = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.fixed_leg
    )
    ZeroCouponInflationSwap.startDate = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.start_date
    )
    ZeroCouponInflationSwap.maturityDate = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.maturity_date
    )
    ZeroCouponInflationSwap.isExpired = (  # type: ignore[attr-defined]
        ZeroCouponInflationSwap.is_expired
    )

ZeroInflationTermStructureHandle = getattr(
    _ql, "ZeroInflationTermStructureHandle", None
)
if ZeroInflationTermStructureHandle is not None:
    ZeroInflationTermStructureHandle.zeroRate = (  # type: ignore[attr-defined]
        ZeroInflationTermStructureHandle.zero_rate
    )
    ZeroInflationTermStructureHandle.baseDate = (  # type: ignore[attr-defined]
        ZeroInflationTermStructureHandle.base_date
    )
    ZeroInflationTermStructureHandle.maxDate = (  # type: ignore[attr-defined]
        ZeroInflationTermStructureHandle.max_date
    )
    ZeroInflationTermStructureHandle.referenceDate = (  # type: ignore[attr-defined]
        ZeroInflationTermStructureHandle.reference_date
    )

RelinkableZeroInflationTermStructureHandle = getattr(
    _ql, "RelinkableZeroInflationTermStructureHandle", None
)
if RelinkableZeroInflationTermStructureHandle is not None:
    RelinkableZeroInflationTermStructureHandle.linkTo = (  # type: ignore[attr-defined]
        RelinkableZeroInflationTermStructureHandle.link_to
    )
    RelinkableZeroInflationTermStructureHandle.asHandle = (  # type: ignore[attr-defined]
        RelinkableZeroInflationTermStructureHandle.as_handle
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
if _YoYInflationIndexType is not None:
    _YoYInflationIndexType.addFixing = (  # type: ignore[attr-defined]
        _YoYInflationIndexType.add_fixing
    )
    _YoYInflationIndexType.clearFixings = (  # type: ignore[attr-defined]
        _YoYInflationIndexType.clear_fixings
    )
    _YoYInflationIndexType.lastFixingDate = (  # type: ignore[attr-defined]
        _YoYInflationIndexType.last_fixing_date
    )
    _YoYInflationIndexType.availabilityLag = (  # type: ignore[attr-defined]
        _YoYInflationIndexType.availability_lag
    )

YearOnYearInflationSwap = getattr(_ql, "YearOnYearInflationSwap", None)
if YearOnYearInflationSwap is not None:
    YearOnYearInflationSwap.setPricingEngine = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.set_pricing_engine
    )
    YearOnYearInflationSwap.fairRate = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.fair_rate
    )
    YearOnYearInflationSwap.fairSpread = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.fair_spread
    )
    YearOnYearInflationSwap.fixedRate = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.fixed_rate
    )
    YearOnYearInflationSwap.fixedLegNPV = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.fixed_leg_NPV
    )
    YearOnYearInflationSwap.yoyLegNPV = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.yoy_leg_NPV
    )
    YearOnYearInflationSwap.startDate = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.start_date
    )
    YearOnYearInflationSwap.maturityDate = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.maturity_date
    )
    YearOnYearInflationSwap.isExpired = (  # type: ignore[attr-defined]
        YearOnYearInflationSwap.is_expired
    )

YoYInflationTermStructureHandle = getattr(
    _ql, "YoYInflationTermStructureHandle", None
)
if YoYInflationTermStructureHandle is not None:
    YoYInflationTermStructureHandle.yoyRate = (  # type: ignore[attr-defined]
        YoYInflationTermStructureHandle.yoy_rate
    )
    YoYInflationTermStructureHandle.baseDate = (  # type: ignore[attr-defined]
        YoYInflationTermStructureHandle.base_date
    )
    YoYInflationTermStructureHandle.baseRate = (  # type: ignore[attr-defined]
        YoYInflationTermStructureHandle.base_rate
    )
    YoYInflationTermStructureHandle.maxDate = (  # type: ignore[attr-defined]
        YoYInflationTermStructureHandle.max_date
    )
    YoYInflationTermStructureHandle.referenceDate = (  # type: ignore[attr-defined]
        YoYInflationTermStructureHandle.reference_date
    )

RelinkableYoYInflationTermStructureHandle = getattr(
    _ql, "RelinkableYoYInflationTermStructureHandle", None
)
if RelinkableYoYInflationTermStructureHandle is not None:
    RelinkableYoYInflationTermStructureHandle.linkTo = (  # type: ignore[attr-defined]
        RelinkableYoYInflationTermStructureHandle.link_to
    )
    RelinkableYoYInflationTermStructureHandle.asHandle = (  # type: ignore[attr-defined]
        RelinkableYoYInflationTermStructureHandle.as_handle
    )

# Phase-14 YoY inflation cap/floor aliases.
ConstantYoYOptionletVolatility = getattr(
    _ql, "ConstantYoYOptionletVolatility", None
)
makeYoYInflationCapFloor = getattr(_ql, "make_yoy_inflation_capfloor", None)
MakeYoYInflationCapFloor = makeYoYInflationCapFloor

YoYInflationCapFloor = getattr(_ql, "YoYInflationCapFloor", None)
if YoYInflationCapFloor is not None:
    YoYInflationCapFloor.setPricingEngine = (  # type: ignore[attr-defined]
        YoYInflationCapFloor.set_pricing_engine
    )
    YoYInflationCapFloor.atmRate = (  # type: ignore[attr-defined]
        YoYInflationCapFloor.atm_rate
    )
    YoYInflationCapFloor.startDate = (  # type: ignore[attr-defined]
        YoYInflationCapFloor.start_date
    )
    YoYInflationCapFloor.maturityDate = (  # type: ignore[attr-defined]
        YoYInflationCapFloor.maturity_date
    )
    YoYInflationCapFloor.isExpired = (  # type: ignore[attr-defined]
        YoYInflationCapFloor.is_expired
    )

YoYInflationCapFloorType = getattr(_ql, "YoYInflationCapFloorType", None)
YoYOptionletVolatilitySurfaceHandle = getattr(
    _ql, "YoYOptionletVolatilitySurfaceHandle", None
)

# Phase-15 CPISwap / CPIBond aliases.
GBPLibor = getattr(_ql, "GBPLibor", None)
InterpolatedZeroCurve = getattr(_ql, "InterpolatedZeroCurve", None)
ZeroCurve = getattr(_ql, "ZeroCurve", InterpolatedZeroCurve)
CPISwap = getattr(_ql, "CPISwap", None)
if CPISwap is not None:
    CPISwap.setPricingEngine = CPISwap.set_pricing_engine  # type: ignore[attr-defined]
    CPISwap.fairRate = CPISwap.fair_rate  # type: ignore[attr-defined]
    CPISwap.fairSpread = CPISwap.fair_spread  # type: ignore[attr-defined]
    CPISwap.fixedRate = CPISwap.fixed_rate  # type: ignore[attr-defined]
    CPISwap.baseCPI = CPISwap.base_CPI  # type: ignore[attr-defined]
    CPISwap.fixedLegNPV = CPISwap.fixed_leg_NPV  # type: ignore[attr-defined]
    CPISwap.floatLegNPV = CPISwap.float_leg_NPV  # type: ignore[attr-defined]
    CPISwap.isExpired = CPISwap.is_expired  # type: ignore[attr-defined]
    CPISwap.inflationNominal = CPISwap.inflation_nominal  # type: ignore[attr-defined]

CPIBond = getattr(_ql, "CPIBond", None)
if CPIBond is not None:
    CPIBond.setPricingEngine = CPIBond.set_pricing_engine  # type: ignore[attr-defined]
    CPIBond.cleanPrice = CPIBond.clean_price  # type: ignore[attr-defined]
    CPIBond.dirtyPrice = CPIBond.dirty_price  # type: ignore[attr-defined]
    CPIBond.baseCPI = CPIBond.base_CPI  # type: ignore[attr-defined]
    CPIBond.settlementDate = CPIBond.settlement_date  # type: ignore[attr-defined]
    CPIBond.maturityDate = CPIBond.maturity_date  # type: ignore[attr-defined]
    CPIBond.isExpired = CPIBond.is_expired  # type: ignore[attr-defined]

# Phase-16 CPICapFloor aliases.
Matrix = getattr(_ql, "Matrix", None)
InterpolatedCPICapFloorTermPriceSurface = getattr(
    _ql, "InterpolatedCPICapFloorTermPriceSurface", None
)
CPICapFloor = getattr(_ql, "CPICapFloor", None)
if CPICapFloor is not None:
    CPICapFloor.setPricingEngine = (  # type: ignore[attr-defined]
        CPICapFloor.set_pricing_engine
    )
    CPICapFloor.fixingDate = CPICapFloor.fixing_date  # type: ignore[attr-defined]
    CPICapFloor.payDate = CPICapFloor.pay_date  # type: ignore[attr-defined]
    CPICapFloor.isExpired = CPICapFloor.is_expired  # type: ignore[attr-defined]

CPICapFloorTermPriceSurfaceHandle = getattr(
    _ql, "CPICapFloorTermPriceSurfaceHandle", None
)
if CPICapFloorTermPriceSurfaceHandle is not None:
    CPICapFloorTermPriceSurfaceHandle.capPrice = (  # type: ignore[attr-defined]
        CPICapFloorTermPriceSurfaceHandle.cap_price
    )
    CPICapFloorTermPriceSurfaceHandle.floorPrice = (  # type: ignore[attr-defined]
        CPICapFloorTermPriceSurfaceHandle.floor_price
    )
    CPICapFloorTermPriceSurfaceHandle.atmRate = (  # type: ignore[attr-defined]
        CPICapFloorTermPriceSurfaceHandle.atm_rate
    )

# Phase-17 seasonality aliases.
MultiplicativePriceSeasonality = getattr(
    _ql, "MultiplicativePriceSeasonality", None
)
KerkhofSeasonality = getattr(_ql, "KerkhofSeasonality", None)
inflationPeriod = getattr(_ql, "inflation_period", None)
Seasonality = getattr(_ql, "Seasonality", None)

for _hname in (
    "ZeroInflationTermStructureHandle",
    "RelinkableZeroInflationTermStructureHandle",
    "YoYInflationTermStructureHandle",
    "RelinkableYoYInflationTermStructureHandle",
):
    _h = getattr(_ql, _hname, None)
    if _h is not None:
        _h.setSeasonality = _h.set_seasonality  # type: ignore[attr-defined]
        _h.hasSeasonality = _h.has_seasonality  # type: ignore[attr-defined]

if MultiplicativePriceSeasonality is not None:
    MultiplicativePriceSeasonality.seasonalityBaseDate = (  # type: ignore[attr-defined]
        MultiplicativePriceSeasonality.seasonality_base_date
    )
    MultiplicativePriceSeasonality.seasonalityFactors = (  # type: ignore[attr-defined]
        MultiplicativePriceSeasonality.seasonality_factors
    )
    MultiplicativePriceSeasonality.seasonalityFactor = (  # type: ignore[attr-defined]
        MultiplicativePriceSeasonality.seasonality_factor
    )

# Phase-18 CPI coupon / CPILeg aliases.
CashFlow = getattr(_ql, "CashFlow", None)
CPICouponPricer = getattr(_ql, "CPICouponPricer", None)
CPICoupon = getattr(_ql, "CPICoupon", None)
if CPICoupon is not None:
    CPICoupon.setPricer = CPICoupon.set_pricer  # type: ignore[attr-defined]
    CPICoupon.fixedRate = CPICoupon.fixed_rate  # type: ignore[attr-defined]
    CPICoupon.baseCPI = CPICoupon.base_CPI  # type: ignore[attr-defined]
    CPICoupon.indexFixing = CPICoupon.index_fixing  # type: ignore[attr-defined]
    CPICoupon.adjustedIndexGrowth = (  # type: ignore[attr-defined]
        CPICoupon.adjusted_index_growth
    )
    CPICoupon.fixingDate = CPICoupon.fixing_date  # type: ignore[attr-defined]
    CPICoupon.indexRatio = CPICoupon.index_ratio  # type: ignore[attr-defined]
    CPICoupon.capletPrice = CPICoupon.caplet_price  # type: ignore[attr-defined]
    CPICoupon.floorletPrice = CPICoupon.floorlet_price  # type: ignore[attr-defined]
    CPICoupon.capletRate = CPICoupon.caplet_rate  # type: ignore[attr-defined]
    CPICoupon.floorletRate = CPICoupon.floorlet_rate  # type: ignore[attr-defined]

if CPICouponPricer is not None:
    CPICouponPricer.setCapletVolatility = (  # type: ignore[attr-defined]
        CPICouponPricer.set_caplet_volatility
    )
    CPICouponPricer.capletVolatility = (  # type: ignore[attr-defined]
        CPICouponPricer.caplet_volatility
    )
    CPICouponPricer.capletPrice = (  # type: ignore[attr-defined]
        CPICouponPricer.caplet_price
    )
    CPICouponPricer.floorletPrice = (  # type: ignore[attr-defined]
        CPICouponPricer.floorlet_price
    )
    CPICouponPricer.capletRate = CPICouponPricer.caplet_rate  # type: ignore[attr-defined]
    CPICouponPricer.floorletRate = (  # type: ignore[attr-defined]
        CPICouponPricer.floorlet_rate
    )

# Phase-65 CPI vol-dependent optionlet aliases.
ConstantCPIVolatility = getattr(_ql, "ConstantCPIVolatility", None)
CPIVolatilitySurfaceHandle = getattr(
    _ql, "CPIVolatilitySurfaceHandle", None
)
if CPIVolatilitySurfaceHandle is not None:
    CPIVolatilitySurfaceHandle.totalVariance = (  # type: ignore[attr-defined]
        CPIVolatilitySurfaceHandle.total_variance
    )
    CPIVolatilitySurfaceHandle.observationLag = (  # type: ignore[attr-defined]
        CPIVolatilitySurfaceHandle.observation_lag
    )
    CPIVolatilitySurfaceHandle.indexIsInterpolated = (  # type: ignore[attr-defined]
        CPIVolatilitySurfaceHandle.index_is_interpolated
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
if YoYInflationCoupon is not None:
    YoYInflationCoupon.setPricer = YoYInflationCoupon.set_pricer  # type: ignore[attr-defined]
    YoYInflationCoupon.indexFixing = (  # type: ignore[attr-defined]
        YoYInflationCoupon.index_fixing
    )
    YoYInflationCoupon.adjustedFixing = (  # type: ignore[attr-defined]
        YoYInflationCoupon.adjusted_fixing
    )
    YoYInflationCoupon.fixingDate = (  # type: ignore[attr-defined]
        YoYInflationCoupon.fixing_date
    )
    YoYInflationCoupon.yoyIndex = YoYInflationCoupon.yoy_index  # type: ignore[attr-defined]

yoyInflationLeg = getattr(_ql, "make_yoy_inflation_leg", None)
setYoYCouponPricer = getattr(_ql, "set_yoy_coupon_pricer", None)

# Phase-20 capped/floored YoY coupon aliases.
CappedFlooredYoYInflationCoupon = getattr(
    _ql, "CappedFlooredYoYInflationCoupon", None
)
if CappedFlooredYoYInflationCoupon is not None:
    CappedFlooredYoYInflationCoupon.effectiveCap = (  # type: ignore[attr-defined]
        CappedFlooredYoYInflationCoupon.effective_cap
    )
    CappedFlooredYoYInflationCoupon.effectiveFloor = (  # type: ignore[attr-defined]
        CappedFlooredYoYInflationCoupon.effective_floor
    )
    CappedFlooredYoYInflationCoupon.underlyingRate = (  # type: ignore[attr-defined]
        CappedFlooredYoYInflationCoupon.underlying_rate
    )
    CappedFlooredYoYInflationCoupon.isCapped = (  # type: ignore[attr-defined]
        CappedFlooredYoYInflationCoupon.is_capped
    )
    CappedFlooredYoYInflationCoupon.isFloored = (  # type: ignore[attr-defined]
        CappedFlooredYoYInflationCoupon.is_floored
    )
    CappedFlooredYoYInflationCoupon.setPricer = (  # type: ignore[attr-defined]
        CappedFlooredYoYInflationCoupon.set_pricer
    )

# Phase-21 Indexed / CPI / ZeroInflation cash-flow aliases.
IndexedCashFlow = getattr(_ql, "IndexedCashFlow", None)
if IndexedCashFlow is not None:
    IndexedCashFlow.baseDate = IndexedCashFlow.base_date  # type: ignore[attr-defined]
    IndexedCashFlow.fixingDate = (  # type: ignore[attr-defined]
        IndexedCashFlow.fixing_date
    )
    IndexedCashFlow.growthOnly = (  # type: ignore[attr-defined]
        IndexedCashFlow.growth_only
    )
    IndexedCashFlow.baseFixing = (  # type: ignore[attr-defined]
        IndexedCashFlow.base_fixing
    )
    IndexedCashFlow.indexFixing = (  # type: ignore[attr-defined]
        IndexedCashFlow.index_fixing
    )

CPICashFlow = getattr(_ql, "CPICashFlow", None)
if CPICashFlow is not None:
    CPICashFlow.observationDate = (  # type: ignore[attr-defined]
        CPICashFlow.observation_date
    )
    CPICashFlow.observationLag = (  # type: ignore[attr-defined]
        CPICashFlow.observation_lag
    )
    CPICashFlow.cpiIndex = CPICashFlow.cpi_index  # type: ignore[attr-defined]

ZeroInflationCashFlow = getattr(_ql, "ZeroInflationCashFlow", None)
if ZeroInflationCashFlow is not None:
    ZeroInflationCashFlow.zeroInflationIndex = (  # type: ignore[attr-defined]
        ZeroInflationCashFlow.zero_inflation_index
    )
    ZeroInflationCashFlow.observationInterpolation = (  # type: ignore[attr-defined]
        ZeroInflationCashFlow.observation_interpolation
    )

# Phase-22 YoY cap/floor term price surface aliases.
InterpolatedYoYCapFloorTermPriceSurface = getattr(
    _ql, "InterpolatedYoYCapFloorTermPriceSurface", None
)
YoYCapFloorTermPriceSurfaceHandle = getattr(
    _ql, "YoYCapFloorTermPriceSurfaceHandle", None
)
if YoYCapFloorTermPriceSurfaceHandle is not None:
    YoYCapFloorTermPriceSurfaceHandle.capPrice = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.cap_price
    )
    YoYCapFloorTermPriceSurfaceHandle.floorPrice = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.floor_price
    )
    YoYCapFloorTermPriceSurfaceHandle.atmYoYSwapRate = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.atm_yoy_swap_rate
    )
    YoYCapFloorTermPriceSurfaceHandle.atmYoYRate = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.atm_yoy_rate
    )
    YoYCapFloorTermPriceSurfaceHandle.atmYoYSwapTimeRates = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.atm_yoy_swap_time_rates
    )
    YoYCapFloorTermPriceSurfaceHandle.atmYoYSwapDateRates = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.atm_yoy_swap_date_rates
    )
    YoYCapFloorTermPriceSurfaceHandle.YoYTS = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.yoy_ts
    )
    YoYCapFloorTermPriceSurfaceHandle.capStrikes = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.cap_strikes
    )
    YoYCapFloorTermPriceSurfaceHandle.floorStrikes = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.floor_strikes
    )
    YoYCapFloorTermPriceSurfaceHandle.observationLag = (  # type: ignore[attr-defined]
        YoYCapFloorTermPriceSurfaceHandle.observation_lag
    )

# Phase-23 callable / puttable bond aliases.
BondPriceType = getattr(_ql, "BondPriceType", None)
BondPrice = getattr(_ql, "BondPrice", None)
CallabilityType = getattr(_ql, "CallabilityType", None)
Callability = getattr(_ql, "make_callability", None)
CallableFixedRateBond = getattr(_ql, "CallableFixedRateBond", None)
if CallableFixedRateBond is not None:
    CallableFixedRateBond.cleanPrice = (  # type: ignore[attr-defined]
        CallableFixedRateBond.clean_price
    )
    CallableFixedRateBond.dirtyPrice = (  # type: ignore[attr-defined]
        CallableFixedRateBond.dirty_price
    )
    CallableFixedRateBond.settlementDate = (  # type: ignore[attr-defined]
        CallableFixedRateBond.settlement_date
    )
    CallableFixedRateBond.maturityDate = (  # type: ignore[attr-defined]
        CallableFixedRateBond.maturity_date
    )
    CallableFixedRateBond.setTreePricingEngine = (  # type: ignore[attr-defined]
        CallableFixedRateBond.set_tree_pricing_engine
    )
    if hasattr(CallableFixedRateBond, "set_black_pricing_engine"):
        CallableFixedRateBond.setBlackPricingEngine = (  # type: ignore[attr-defined]
            CallableFixedRateBond.set_black_pricing_engine
        )
    if hasattr(CallableFixedRateBond, "implied_volatility"):
        CallableFixedRateBond.impliedVolatility = (  # type: ignore[attr-defined]
            CallableFixedRateBond.implied_volatility
        )
    if hasattr(CallableFixedRateBond, "oas"):
        CallableFixedRateBond.OAS = CallableFixedRateBond.oas  # type: ignore[attr-defined]
        CallableFixedRateBond.cleanPriceOAS = (  # type: ignore[attr-defined]
            CallableFixedRateBond.clean_price_oas
        )
        CallableFixedRateBond.effectiveDuration = (  # type: ignore[attr-defined]
            CallableFixedRateBond.effective_duration
        )
        CallableFixedRateBond.effectiveConvexity = (  # type: ignore[attr-defined]
            CallableFixedRateBond.effective_convexity
        )
CallableZeroCouponBond = getattr(_ql, "CallableZeroCouponBond", None)
if CallableZeroCouponBond is not None:
    CallableZeroCouponBond.cleanPrice = (  # type: ignore[attr-defined]
        CallableZeroCouponBond.clean_price
    )
    CallableZeroCouponBond.dirtyPrice = (  # type: ignore[attr-defined]
        CallableZeroCouponBond.dirty_price
    )
    CallableZeroCouponBond.settlementDate = (  # type: ignore[attr-defined]
        CallableZeroCouponBond.settlement_date
    )
    CallableZeroCouponBond.maturityDate = (  # type: ignore[attr-defined]
        CallableZeroCouponBond.maturity_date
    )
    CallableZeroCouponBond.setTreePricingEngine = (  # type: ignore[attr-defined]
        CallableZeroCouponBond.set_tree_pricing_engine
    )
    if hasattr(CallableZeroCouponBond, "set_black_pricing_engine"):
        CallableZeroCouponBond.setBlackPricingEngine = (  # type: ignore[attr-defined]
            CallableZeroCouponBond.set_black_pricing_engine
        )
    if hasattr(CallableZeroCouponBond, "implied_volatility"):
        CallableZeroCouponBond.impliedVolatility = (  # type: ignore[attr-defined]
            CallableZeroCouponBond.implied_volatility
        )
    if hasattr(CallableZeroCouponBond, "oas"):
        CallableZeroCouponBond.OAS = CallableZeroCouponBond.oas  # type: ignore[attr-defined]
        CallableZeroCouponBond.cleanPriceOAS = (  # type: ignore[attr-defined]
            CallableZeroCouponBond.clean_price_oas
        )
        CallableZeroCouponBond.effectiveDuration = (  # type: ignore[attr-defined]
            CallableZeroCouponBond.effective_duration
        )
        CallableZeroCouponBond.effectiveConvexity = (  # type: ignore[attr-defined]
            CallableZeroCouponBond.effective_convexity
        )

def make_soft_callability(*args: Any, **kwargs: Any) -> Any:
    return _ql.make_soft_callability(*args, **kwargs)


SoftCallability = make_soft_callability
ConvertibleZeroCouponBond = getattr(_ql, "ConvertibleZeroCouponBond", None)
ConvertibleFixedCouponBond = getattr(_ql, "ConvertibleFixedCouponBond", None)
if ConvertibleZeroCouponBond is not None:
    ConvertibleZeroCouponBond.cleanPrice = (  # type: ignore[attr-defined]
        ConvertibleZeroCouponBond.clean_price
    )
    ConvertibleZeroCouponBond.dirtyPrice = (  # type: ignore[attr-defined]
        ConvertibleZeroCouponBond.dirty_price
    )
    ConvertibleZeroCouponBond.conversionRatio = (  # type: ignore[attr-defined]
        ConvertibleZeroCouponBond.conversion_ratio
    )
    ConvertibleZeroCouponBond.settlementDate = (  # type: ignore[attr-defined]
        ConvertibleZeroCouponBond.settlement_date
    )
    ConvertibleZeroCouponBond.maturityDate = (  # type: ignore[attr-defined]
        ConvertibleZeroCouponBond.maturity_date
    )
    ConvertibleZeroCouponBond.setBinomialPricingEngine = (  # type: ignore[attr-defined]
        ConvertibleZeroCouponBond.set_binomial_pricing_engine
    )
if ConvertibleFixedCouponBond is not None:
    ConvertibleFixedCouponBond.cleanPrice = (  # type: ignore[attr-defined]
        ConvertibleFixedCouponBond.clean_price
    )
    ConvertibleFixedCouponBond.dirtyPrice = (  # type: ignore[attr-defined]
        ConvertibleFixedCouponBond.dirty_price
    )
    ConvertibleFixedCouponBond.conversionRatio = (  # type: ignore[attr-defined]
        ConvertibleFixedCouponBond.conversion_ratio
    )
    ConvertibleFixedCouponBond.settlementDate = (  # type: ignore[attr-defined]
        ConvertibleFixedCouponBond.settlement_date
    )
    ConvertibleFixedCouponBond.maturityDate = (  # type: ignore[attr-defined]
        ConvertibleFixedCouponBond.maturity_date
    )
    ConvertibleFixedCouponBond.setBinomialPricingEngine = (  # type: ignore[attr-defined]
        ConvertibleFixedCouponBond.set_binomial_pricing_engine
    )
ConvertibleFloatingRateBond = getattr(_ql, "ConvertibleFloatingRateBond", None)
if ConvertibleFloatingRateBond is not None:
    ConvertibleFloatingRateBond.cleanPrice = (  # type: ignore[attr-defined]
        ConvertibleFloatingRateBond.clean_price
    )
    ConvertibleFloatingRateBond.dirtyPrice = (  # type: ignore[attr-defined]
        ConvertibleFloatingRateBond.dirty_price
    )
    ConvertibleFloatingRateBond.conversionRatio = (  # type: ignore[attr-defined]
        ConvertibleFloatingRateBond.conversion_ratio
    )
    ConvertibleFloatingRateBond.settlementDate = (  # type: ignore[attr-defined]
        ConvertibleFloatingRateBond.settlement_date
    )
    ConvertibleFloatingRateBond.maturityDate = (  # type: ignore[attr-defined]
        ConvertibleFloatingRateBond.maturity_date
    )
    ConvertibleFloatingRateBond.setBinomialPricingEngine = (  # type: ignore[attr-defined]
        ConvertibleFloatingRateBond.set_binomial_pricing_engine
    )

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
if Currency is not None:
    Currency.numericCode = Currency.numeric_code  # type: ignore[attr-defined]
    Currency.fractionSymbol = (  # type: ignore[attr-defined]
        Currency.fraction_symbol
    )
    Currency.fractionsPerUnit = (  # type: ignore[attr-defined]
        Currency.fractions_per_unit
    )
if FxForward is not None:
    FxForward.sourceNominal = (  # type: ignore[attr-defined]
        FxForward.source_nominal
    )
    FxForward.targetNominal = (  # type: ignore[attr-defined]
        FxForward.target_nominal
    )
    FxForward.sourceCurrency = (  # type: ignore[attr-defined]
        FxForward.source_currency
    )
    FxForward.targetCurrency = (  # type: ignore[attr-defined]
        FxForward.target_currency
    )
    FxForward.maturityDate = (  # type: ignore[attr-defined]
        FxForward.maturity_date
    )
    FxForward.paySourceCurrency = (  # type: ignore[attr-defined]
        FxForward.pay_source_currency
    )
    FxForward.forwardRate = FxForward.forward_rate  # type: ignore[attr-defined]
    FxForward.settlementDays = (  # type: ignore[attr-defined]
        FxForward.settlement_days
    )
    FxForward.settlementCalendar = (  # type: ignore[attr-defined]
        FxForward.settlement_calendar
    )
    FxForward.settlementDate = (  # type: ignore[attr-defined]
        FxForward.settlement_date
    )
    FxForward.isExpired = FxForward.is_expired  # type: ignore[attr-defined]
    FxForward.fairForwardRate = (  # type: ignore[attr-defined]
        FxForward.fair_forward_rate
    )
    FxForward.npvSourceCurrency = (  # type: ignore[attr-defined]
        FxForward.npv_source_currency
    )
    FxForward.npvTargetCurrency = (  # type: ignore[attr-defined]
        FxForward.npv_target_currency
    )
    FxForward.setPricingEngine = (  # type: ignore[attr-defined]
        FxForward.set_pricing_engine
    )

# Phase-40 quanto vanilla aliases.
QuantoVanillaOption = getattr(_ql, "QuantoVanillaOption", None)
if QuantoVanillaOption is not None:
    QuantoVanillaOption.setPricingEngine = (  # type: ignore[attr-defined]
        QuantoVanillaOption.set_pricing_engine
    )
    QuantoVanillaOption.isExpired = (  # type: ignore[attr-defined]
        QuantoVanillaOption.is_expired
    )

# Phase-41 / Phase-44 quanto-forward vanilla aliases.
QuantoForwardVanillaOption = getattr(_ql, "QuantoForwardVanillaOption", None)
if QuantoForwardVanillaOption is not None:
    QuantoForwardVanillaOption.setPricingEngine = (  # type: ignore[attr-defined]
        QuantoForwardVanillaOption.set_pricing_engine
    )
    if hasattr(QuantoForwardVanillaOption, "set_performance_pricing_engine"):
        QuantoForwardVanillaOption.setPerformancePricingEngine = (  # type: ignore[attr-defined]
            QuantoForwardVanillaOption.set_performance_pricing_engine
        )
    QuantoForwardVanillaOption.isExpired = (  # type: ignore[attr-defined]
        QuantoForwardVanillaOption.is_expired
    )

# Phase-42 quanto barrier aliases.
QuantoBarrierOption = getattr(_ql, "QuantoBarrierOption", None)
if QuantoBarrierOption is not None:
    QuantoBarrierOption.setPricingEngine = (  # type: ignore[attr-defined]
        QuantoBarrierOption.set_pricing_engine
    )
    QuantoBarrierOption.isExpired = (  # type: ignore[attr-defined]
        QuantoBarrierOption.is_expired
    )

# Phase-43 quanto double-barrier aliases.
QuantoDoubleBarrierOption = getattr(_ql, "QuantoDoubleBarrierOption", None)
if QuantoDoubleBarrierOption is not None:
    QuantoDoubleBarrierOption.setPricingEngine = (  # type: ignore[attr-defined]
        QuantoDoubleBarrierOption.set_pricing_engine
    )
    QuantoDoubleBarrierOption.isExpired = (  # type: ignore[attr-defined]
        QuantoDoubleBarrierOption.is_expired
    )

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
