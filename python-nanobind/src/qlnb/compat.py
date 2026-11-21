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
from ._compat_aliases import _ALIASES, _STATIC_METHODS

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
    for class_name, alias, target in _ALIASES:
        cls = getattr(_ql, class_name, None)
        if cls is None or not isinstance(cls, type):
            continue
        for base in cls.__mro__:
            namespace = vars(base)
            if target in namespace:
                descriptor = namespace[target]
                if (class_name, alias) in _STATIC_METHODS:
                    descriptor = staticmethod(descriptor)
                setattr(cls, alias, descriptor)
                break

    perpetual_futures = getattr(_ql, "PerpetualFutures", None)
    if perpetual_futures is not None:
        payoff_type = getattr(_ql, "PerpetualFuturesPayoffType", None)
        funding_type = getattr(_ql, "PerpetualFuturesFundingType", None)
        if payoff_type is not None:
            perpetual_futures.Linear = payoff_type.Linear  # type: ignore[attr-defined]
            perpetual_futures.Inverse = payoff_type.Inverse  # type: ignore[attr-defined]
            perpetual_futures.Quanto = payoff_type.Quanto  # type: ignore[attr-defined]
        if funding_type is not None:
            perpetual_futures.FundingWithPreviousSpot = (
                funding_type.FundingWithPreviousSpot
            )  # type: ignore[attr-defined]
            perpetual_futures.FundingWithCurrentSpot = (
                funding_type.FundingWithCurrentSpot
            )  # type: ignore[attr-defined]


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
