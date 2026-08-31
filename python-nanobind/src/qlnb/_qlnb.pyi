from typing import Iterable, Sequence, overload

class Month:
    January: Month
    February: Month
    March: Month
    April: Month
    May: Month
    June: Month
    July: Month
    August: Month
    September: Month
    October: Month
    November: Month
    December: Month

class TimeUnit:
    Days: TimeUnit
    Weeks: TimeUnit
    Months: TimeUnit
    Years: TimeUnit

class Frequency:
    NoFrequency: Frequency
    Once: Frequency
    Annual: Frequency
    Semiannual: Frequency
    Quarterly: Frequency
    Monthly: Frequency

class BusinessDayConvention:
    Following: BusinessDayConvention
    ModifiedFollowing: BusinessDayConvention
    Preceding: BusinessDayConvention
    ModifiedPreceding: BusinessDayConvention
    Unadjusted: BusinessDayConvention

class DateGeneration:
    Backward: DateGeneration
    Forward: DateGeneration
    TwentiethIMM: DateGeneration
    CDS: DateGeneration
    CDS2015: DateGeneration

class ProtectionSide:
    Buyer: ProtectionSide
    Seller: ProtectionSide

class Compounding:
    Simple: Compounding
    Compounded: Compounding
    Continuous: Compounding

class OptionType:
    Put: OptionType
    Call: OptionType

class SwapType:
    Receiver: SwapType
    Payer: SwapType

class Position:
    Long: Position
    Short: Position

class BarrierType:
    DownIn: BarrierType
    UpIn: BarrierType
    DownOut: BarrierType
    UpOut: BarrierType

class DoubleBarrierType:
    KnockIn: DoubleBarrierType
    KnockOut: DoubleBarrierType
    KIKO: DoubleBarrierType
    KOKI: DoubleBarrierType

class AverageType:
    Arithmetic: AverageType
    Geometric: AverageType

class CdsPricingModel:
    Midpoint: CdsPricingModel
    ISDA: CdsPricingModel

class CapFloorType:
    Cap: CapFloorType
    Floor: CapFloorType
    Collar: CapFloorType

class ActualActualConvention:
    ISDA: ActualActualConvention
    ISMA: ActualActualConvention
    Bond: ActualActualConvention

class Thirty360Convention:
    USA: Thirty360Convention
    BondBasis: Thirty360Convention
    European: Thirty360Convention
    EurobondBasis: Thirty360Convention
    Italian: Thirty360Convention
    German: Thirty360Convention
    ISMA: Thirty360Convention
    ISDA: Thirty360Convention
    NASD: Thirty360Convention

class UnitedStatesMarket:
    Settlement: UnitedStatesMarket
    NYSE: UnitedStatesMarket
    GovernmentBond: UnitedStatesMarket
    SOFR: UnitedStatesMarket

class GermanyMarket:
    Settlement: GermanyMarket
    FrankfurtStockExchange: GermanyMarket
    Xetra: GermanyMarket
    Eurex: GermanyMarket
    Euwax: GermanyMarket

class SettlementType:
    Physical: SettlementType
    Cash: SettlementType

class SettlementMethod:
    PhysicalOTC: SettlementMethod
    PhysicalCleared: SettlementMethod
    CollateralizedCashPrice: SettlementMethod
    ParYieldCurve: SettlementMethod

class Date:
    def __init__(self, day: int, month: Month, year: int) -> None: ...
    def day_of_month(self) -> int: ...
    def month(self) -> Month: ...
    def year(self) -> int: ...
    def weekday(self) -> int: ...
    def serial_number(self) -> int: ...
    def __add__(self, other: int | Period) -> Date: ...
    def __sub__(self, other: int | Period) -> Date: ...

class Period:
    def __init__(self, n: int, units: TimeUnit) -> None: ...
    def __init__(self, frequency: Frequency) -> None: ...  # type: ignore[misc]
    def length(self) -> int: ...
    def units(self) -> TimeUnit: ...
    def frequency(self) -> Frequency: ...
    def __mul__(self, n: int) -> Period: ...

class Settings:
    @staticmethod
    def instance() -> Settings: ...
    evaluation_date: Date
    include_todays_cash_flows: bool | None

class Quote:
    def value(self) -> float: ...
    def is_valid(self) -> bool: ...

class SimpleQuote(Quote):
    def __init__(self, value: float) -> None: ...
    def set_value(self, value: float) -> float: ...

class DeltaVolDeltaType:
    Spot: DeltaVolDeltaType
    Fwd: DeltaVolDeltaType
    PaSpot: DeltaVolDeltaType
    PaFwd: DeltaVolDeltaType

class DeltaVolAtmType:
    AtmNull: DeltaVolAtmType
    AtmSpot: DeltaVolAtmType
    AtmFwd: DeltaVolAtmType
    AtmDeltaNeutral: DeltaVolAtmType
    AtmVegaMax: DeltaVolAtmType
    AtmGammaMax: DeltaVolAtmType
    AtmPutCall50: DeltaVolAtmType

class DeltaVolQuote(Quote):
    @overload
    def __init__(
        self,
        delta: float,
        vol: QuoteHandle,
        maturity: float,
        delta_type: DeltaVolDeltaType,
    ) -> None: ...
    @overload
    def __init__(
        self,
        vol: QuoteHandle,
        delta_type: DeltaVolDeltaType,
        maturity: float,
        atm_type: DeltaVolAtmType,
    ) -> None: ...
    def value(self) -> float: ...
    def delta(self) -> float: ...
    def maturity(self) -> float: ...
    def atm_type(self) -> DeltaVolAtmType: ...
    def delta_type(self) -> DeltaVolDeltaType: ...
    def is_valid(self) -> bool: ...

class QuoteHandle:
    def __init__(self, value: Quote = ...) -> None: ...
    def empty(self) -> bool: ...
    def current_link(self) -> Quote: ...

class DayCounter:
    def name(self) -> str: ...
    def year_fraction(self, d1: Date, d2: Date) -> float: ...
    def day_count(self, d1: Date, d2: Date) -> int: ...

class Calendar:
    def name(self) -> str: ...
    def is_business_day(self, date: Date) -> bool: ...
    def is_holiday(self, date: Date) -> bool: ...
    def advance(
        self,
        date: Date,
        period: Period | int,
        convention: BusinessDayConvention = ...,
        end_of_month: bool = ...,
        unit: TimeUnit = ...,
    ) -> Date: ...
    def adjust(self, date: Date, convention: BusinessDayConvention = ...) -> Date: ...

class Schedule:
    def __init__(
        self,
        effective_date: Date,
        termination_date: Date,
        tenor: Period,
        calendar: Calendar,
        convention: BusinessDayConvention,
        termination_date_convention: BusinessDayConvention,
        rule: DateGeneration,
        end_of_month: bool,
    ) -> None: ...
    def __init__(  # type: ignore[misc]
        self,
        dates: Sequence[Date],
        calendar: Calendar = ...,
        convention: BusinessDayConvention = ...,
    ) -> None: ...
    def size(self) -> int: ...
    def __len__(self) -> int: ...
    def __getitem__(self, i: int) -> Date: ...
    def dates(self) -> list[Date]: ...
    def start_date(self) -> Date: ...
    def end_date(self) -> Date: ...

class InterestRate:
    def rate(self) -> float: ...
    def __float__(self) -> float: ...

class YieldTermStructureHandle:
    def empty(self) -> bool: ...
    def discount(self, date: Date, extrapolate: bool = ...) -> float: ...
    def reference_date(self) -> Date: ...
    def zero_rate(
        self,
        date: Date,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency = ...,
        extrapolate: bool = ...,
    ) -> InterestRate: ...

class RateHelper: ...

class IborIndex:
    def name(self) -> str: ...
    def tenor(self) -> Period: ...
    def fixing_calendar(self) -> Calendar: ...
    def day_counter(self) -> DayCounter: ...
    def fixing_days(self) -> int: ...
    def business_day_convention(self) -> BusinessDayConvention: ...
    def end_of_month(self) -> bool: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def fixing(
        self, fixing_date: Date, forecast_todays_fixing: bool = ...
    ) -> float: ...

class OvernightIndex:
    def name(self) -> str: ...
    def tenor(self) -> Period: ...
    def fixing_calendar(self) -> Calendar: ...
    def day_counter(self) -> DayCounter: ...
    def fixing_days(self) -> int: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def fixing(
        self, fixing_date: Date, forecast_todays_fixing: bool = ...
    ) -> float: ...

class BMAIndex:
    def __init__(self, handle: YieldTermStructureHandle = ...) -> None: ...
    def name(self) -> str: ...
    def tenor(self) -> Period: ...
    def fixing_calendar(self) -> Calendar: ...
    def day_counter(self) -> DayCounter: ...
    def fixing_days(self) -> int: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def fixing(
        self, fixing_date: Date, forecast_todays_fixing: bool = ...
    ) -> float: ...
    def is_valid_fixing_date(self, fixing_date: Date) -> bool: ...

class EquityIndex:
    def __init__(
        self,
        name: str,
        fixing_calendar: Calendar,
        currency: "Currency",
        interest: YieldTermStructureHandle = ...,
        dividend: YieldTermStructureHandle = ...,
        spot: QuoteHandle = ...,
    ) -> None: ...
    def name(self) -> str: ...
    def fixing_calendar(self) -> Calendar: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def fixing(
        self, fixing_date: Date, forecast_todays_fixing: bool = ...
    ) -> float: ...

class FixedRateBond:
    def __init__(
        self,
        settlement_days: int,
        face_amount: float,
        schedule: Schedule,
        coupons: Sequence[float],
        accrual_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        redemption: float = ...,
        issue_date: Date = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    @overload
    def clean_price(self) -> float: ...
    @overload
    def clean_price(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def settlement_value(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...
    def bond_yield(
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
    def duration(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        type: DurationType = ...,
        settlement_date: Date = ...,
    ) -> float: ...
    def convexity(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def z_spread(
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
    def clean_price_from_z_spread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def accrued_amount(self, date: Date = ...) -> float: ...

class ZeroCouponBond:
    def __init__(
        self,
        settlement_days: int,
        calendar: Calendar,
        face_amount: float,
        maturity_date: Date,
        payment_convention: BusinessDayConvention = ...,
        redemption: float = ...,
        issue_date: Date = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    @overload
    def clean_price(self) -> float: ...
    @overload
    def clean_price(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def settlement_value(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...
    def bond_yield(
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
    def duration(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        type: DurationType = ...,
        settlement_date: Date = ...,
    ) -> float: ...
    def convexity(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def z_spread(
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
    def clean_price_from_z_spread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def accrued_amount(self, date: Date = ...) -> float: ...

class FloatingRateBond:
    def __init__(
        self,
        settlement_days: int,
        face_amount: float,
        schedule: Schedule,
        ibor_index: IborIndex,
        accrual_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
        gearings: Sequence[float] = ...,
        spreads: Sequence[float] = ...,
        caps: Sequence[float] = ...,
        floors: Sequence[float] = ...,
        in_arrears: bool = ...,
        redemption: float = ...,
        issue_date: Date = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    @overload
    def clean_price(self) -> float: ...
    @overload
    def clean_price(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def settlement_value(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...
    def bond_yield(
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
    def duration(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        type: DurationType = ...,
        settlement_date: Date = ...,
    ) -> float: ...
    def convexity(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def z_spread(
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
    def clean_price_from_z_spread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def accrued_amount(self, date: Date = ...) -> float: ...

class CmsRateBond:
    def __init__(
        self,
        settlement_days: int,
        face_amount: float,
        schedule: Schedule,
        swap_index: SwapIndex,
        payment_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
        gearings: Sequence[float] = ...,
        spreads: Sequence[float] = ...,
        caps: Sequence[float] = ...,
        floors: Sequence[float] = ...,
        in_arrears: bool = ...,
        redemption: float = ...,
        issue_date: Date = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    @overload
    def clean_price(self) -> float: ...
    @overload
    def clean_price(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def settlement_value(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...
    def set_cms_coupon_pricer(self, pricer: CmsCouponPricer) -> None: ...
    def bond_yield(
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
    def duration(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        type: DurationType = ...,
        settlement_date: Date = ...,
    ) -> float: ...
    def convexity(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def z_spread(
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
    def clean_price_from_z_spread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def accrued_amount(self, date: Date = ...) -> float: ...

class AmortizingFixedRateBond:
    def __init__(
        self,
        settlement_days: int,
        notionals: Sequence[float],
        schedule: Schedule,
        coupons: Sequence[float],
        accrual_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        issue_date: Date = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    @overload
    def clean_price(self) -> float: ...
    @overload
    def clean_price(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def settlement_value(self) -> float: ...
    def frequency(self) -> Frequency: ...
    def day_counter(self) -> DayCounter: ...
    def cashflow_amounts(self) -> list[float]: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...
    def bond_yield(
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
    def duration(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        type: DurationType = ...,
        settlement_date: Date = ...,
    ) -> float: ...
    def convexity(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def z_spread(
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
    def clean_price_from_z_spread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def accrued_amount(self, date: Date = ...) -> float: ...

class AmortizingFloatingRateBond:
    def __init__(
        self,
        settlement_days: int,
        notionals: Sequence[float],
        schedule: Schedule,
        ibor_index: IborIndex,
        accrual_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
        gearings: Sequence[float] = ...,
        spreads: Sequence[float] = ...,
        caps: Sequence[float] = ...,
        floors: Sequence[float] = ...,
        in_arrears: bool = ...,
        issue_date: Date = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    @overload
    def clean_price(self) -> float: ...
    @overload
    def clean_price(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def settlement_value(self) -> float: ...
    def cashflow_amounts(self) -> list[float]: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...
    def bond_yield(
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
    def duration(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        type: DurationType = ...,
        settlement_date: Date = ...,
    ) -> float: ...
    def convexity(
        self,
        yield_rate: float,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def z_spread(
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
    def clean_price_from_z_spread(
        self,
        discount_curve: YieldTermStructureHandle,
        z_spread: float,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
    ) -> float: ...
    def accrued_amount(self, date: Date = ...) -> float: ...

def sinking_schedule(
    start_date: Date,
    bond_length: Period,
    frequency: Frequency,
    payment_calendar: Calendar,
) -> Schedule: ...
def sinking_notionals(
    bond_length: Period,
    frequency: Frequency,
    coupon_rate: float,
    initial_notional: float,
) -> list[float]: ...

class VanillaSwap:
    def __init__(
        self,
        type: SwapType,
        nominal: float,
        fixed_schedule: Schedule,
        fixed_rate: float,
        fixed_day_count: DayCounter,
        float_schedule: Schedule,
        ibor_index: IborIndex,
        spread: float,
        floating_day_count: DayCounter,
    ) -> None: ...
    def NPV(self) -> float: ...
    def fair_rate(self) -> float: ...
    def fair_spread(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class NonstandardSwap:
    def __init__(self, vanilla_swap: VanillaSwap) -> None: ...
    def __init__(
        self,
        type: SwapType,
        fixed_nominal: list[float],
        floating_nominal: list[float],
        fixed_schedule: Schedule,
        fixed_rate: list[float],
        fixed_day_count: DayCounter,
        floating_schedule: Schedule,
        ibor_index: IborIndex,
        gearing: float,
        spread: float,
        floating_day_count: DayCounter,
        intermediate_capital_exchange: bool = ...,
        final_capital_exchange: bool = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> SwapType: ...
    def fixed_nominal(self) -> list[float]: ...
    def floating_nominal(self) -> list[float]: ...
    def fixed_rate(self) -> list[float]: ...
    def spread(self) -> float: ...
    def gearing(self) -> float: ...
    def fixed_schedule(self) -> Schedule: ...
    def floating_schedule(self) -> Schedule: ...
    def ibor_index(self) -> IborIndex: ...
    def fixed_day_count(self) -> DayCounter: ...
    def floating_day_count(self) -> DayCounter: ...
    def payment_convention(self) -> BusinessDayConvention: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class ConstNotionalCrossCurrencyFixedVsFloatingSwap:
    def __init__(
        self,
        type: SwapType,
        fixed_nominal: float,
        fixed_currency: Currency,
        fixed_schedule: Schedule,
        fixed_rate: float,
        fixed_day_count: DayCounter,
        fixed_payment_bdc: BusinessDayConvention,
        fixed_payment_lag: int,
        fixed_payment_calendar: Calendar,
        float_nominal: float,
        float_currency: Currency,
        float_schedule: Schedule,
        float_index: IborIndex,
        float_spread: float,
        float_payment_bdc: BusinessDayConvention,
        float_payment_lag: int,
        float_payment_calendar: Calendar,
    ) -> None: ...
    def NPV(self) -> float: ...
    def leg_npv(self, leg: int) -> float: ...
    def leg_bps(self, leg: int) -> float: ...
    def in_ccy_leg_npv(self, leg: int) -> float: ...
    def in_ccy_leg_bps(self, leg: int) -> float: ...
    def fair_rate(self) -> float: ...
    def fair_spread(self) -> float: ...
    def set_pricing_engine(
        self,
        domestic_currency: Currency,
        domestic_discount: YieldTermStructureHandle,
        foreign_currency: Currency,
        foreign_discount: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

class ConstNotionalCrossCurrencyBasisSwap:
    def __init__(
        self,
        pay_nominal: float,
        pay_currency: Currency,
        pay_schedule: Schedule,
        pay_index: IborIndex,
        pay_spread: float,
        pay_gearing: float,
        rec_nominal: float,
        rec_currency: Currency,
        rec_schedule: Schedule,
        rec_index: IborIndex,
        rec_spread: float,
        rec_gearing: float,
        pay_payment_lag: int = ...,
        rec_payment_lag: int = ...,
        pay_compound_spread: bool = ...,
        pay_lookback_days: int | None = ...,
        pay_observation_shift: bool = ...,
        pay_lockout_days: int = ...,
        pay_averaging_method: RateAveraging = ...,
        rec_compound_spread: bool = ...,
        rec_lookback_days: int | None = ...,
        rec_observation_shift: bool = ...,
        rec_lockout_days: int = ...,
        rec_averaging_method: RateAveraging = ...,
        telescopic_value_dates: bool = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        pay_nominal: float,
        pay_currency: Currency,
        pay_schedule: Schedule,
        pay_index: OvernightIndex,
        pay_spread: float,
        pay_gearing: float,
        rec_nominal: float,
        rec_currency: Currency,
        rec_schedule: Schedule,
        rec_index: OvernightIndex,
        rec_spread: float,
        rec_gearing: float,
        pay_payment_lag: int = ...,
        rec_payment_lag: int = ...,
        pay_compound_spread: bool = ...,
        pay_lookback_days: int | None = ...,
        pay_observation_shift: bool = ...,
        pay_lockout_days: int = ...,
        pay_averaging_method: RateAveraging = ...,
        rec_compound_spread: bool = ...,
        rec_lookback_days: int | None = ...,
        rec_observation_shift: bool = ...,
        rec_lockout_days: int = ...,
        rec_averaging_method: RateAveraging = ...,
        telescopic_value_dates: bool = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def leg_npv(self, leg: int) -> float: ...
    def leg_bps(self, leg: int) -> float: ...
    def in_ccy_leg_npv(self, leg: int) -> float: ...
    def in_ccy_leg_bps(self, leg: int) -> float: ...
    def fair_pay_spread(self) -> float: ...
    def fair_rec_spread(self) -> float: ...
    def set_pricing_engine(
        self,
        domestic_currency: Currency,
        domestic_discount: YieldTermStructureHandle,
        foreign_currency: Currency,
        foreign_discount: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

class ConstNotionalCrossCurrencySwap:
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def leg_npv(self, leg: int) -> float: ...
    def leg_bps(self, leg: int) -> float: ...
    def in_ccy_leg_npv(self, leg: int) -> float: ...
    def in_ccy_leg_bps(self, leg: int) -> float: ...
    def leg_currency(self, leg: int) -> Currency: ...
    def set_pricing_engine(
        self,
        domestic_currency: Currency,
        domestic_discount: YieldTermStructureHandle,
        foreign_currency: Currency,
        foreign_discount: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...

def make_fix_fix_xccy_swap(usd_nominal: float, spot_fx: float) -> ConstNotionalCrossCurrencySwap: ...

def make_float_float_xccy_swap(
    usd_nominal: float,
    spot_fx: float,
    usd_projection: YieldTermStructureHandle,
    gbp_projection: YieldTermStructureHandle,
) -> ConstNotionalCrossCurrencySwap: ...

def make_fix_float_xccy_swap(
    usd_nominal: float,
    spot_fx: float,
    usd_projection: YieldTermStructureHandle,
) -> ConstNotionalCrossCurrencySwap: ...

class AssetSwap:
    def __init__(
        self,
        pay_bond_coupon: bool,
        bond: FixedRateBond,
        bond_clean_price: float,
        ibor_index: IborIndex,
        spread: float,
        float_schedule: Schedule = ...,
        floating_day_count: DayCounter = ...,
        par_asset_swap: bool = ...,
        gearing: float = ...,
        non_par_repayment: float | None = ...,
        deal_maturity: Date = ...,
    ) -> None: ...
    def __init__(
        self,
        pay_bond_coupon: bool,
        bond: ZeroCouponBond,
        bond_clean_price: float,
        ibor_index: IborIndex,
        spread: float,
        float_schedule: Schedule = ...,
        floating_day_count: DayCounter = ...,
        par_asset_swap: bool = ...,
        gearing: float = ...,
        non_par_repayment: float | None = ...,
        deal_maturity: Date = ...,
    ) -> None: ...  # type: ignore[misc]
    def __init__(
        self,
        pay_bond_coupon: bool,
        bond: FloatingRateBond,
        bond_clean_price: float,
        ibor_index: IborIndex,
        spread: float,
        float_schedule: Schedule = ...,
        floating_day_count: DayCounter = ...,
        par_asset_swap: bool = ...,
        gearing: float = ...,
        non_par_repayment: float | None = ...,
        deal_maturity: Date = ...,
    ) -> None: ...  # type: ignore[misc]
    def __init__(
        self,
        pay_bond_coupon: bool,
        bond: CmsRateBond,
        bond_clean_price: float,
        ibor_index: IborIndex,
        spread: float,
        float_schedule: Schedule = ...,
        floating_day_count: DayCounter = ...,
        par_asset_swap: bool = ...,
        gearing: float = ...,
        non_par_repayment: float | None = ...,
        deal_maturity: Date = ...,
    ) -> None: ...  # type: ignore[misc]
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def fair_spread(self) -> float: ...
    def fair_clean_price(self) -> float: ...
    def fair_non_par_repayment(self) -> float: ...
    def floating_leg_BPS(self) -> float: ...
    def floating_leg_NPV(self) -> float: ...
    def par_swap(self) -> bool: ...
    def spread(self) -> float: ...
    def clean_price(self) -> float: ...
    def non_par_repayment(self) -> float: ...
    def pay_bond_coupon(self) -> bool: ...
    def set_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        include_settlement_date_flows: bool | None = ...,
        settlement_date: Date = ...,
        npv_date: Date = ...,
    ) -> None: ...

class ZeroCouponSwap:
    def __init__(
        self,
        type: SwapType,
        base_nominal: float,
        start_date: Date,
        maturity_date: Date,
        fixed_payment: float,
        ibor_index: IborIndex,
        payment_calendar: Calendar,
        payment_convention: BusinessDayConvention = ...,
        payment_delay: int = ...,
    ) -> None: ...
    def __init__(
        self,
        type: SwapType,
        base_nominal: float,
        start_date: Date,
        maturity_date: Date,
        fixed_rate: float,
        fixed_day_counter: DayCounter,
        ibor_index: IborIndex,
        payment_calendar: Calendar,
        payment_convention: BusinessDayConvention = ...,
        payment_delay: int = ...,
    ) -> None: ...  # type: ignore[misc]
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def type(self) -> SwapType: ...
    def base_nominal(self) -> float: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def fixed_payment(self) -> float: ...
    def fixed_leg_NPV(self) -> float: ...
    def floating_leg_NPV(self) -> float: ...
    def fair_fixed_payment(self) -> float: ...
    def fair_fixed_rate(self, day_counter: DayCounter) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class PerpetualFuturesPayoffType:
    Linear: PerpetualFuturesPayoffType
    Inverse: PerpetualFuturesPayoffType
    Quanto: PerpetualFuturesPayoffType

class PerpetualFuturesFundingType:
    FundingWithPreviousSpot: PerpetualFuturesFundingType
    FundingWithCurrentSpot: PerpetualFuturesFundingType

class PerpetualFuturesInterpType:
    PiecewiseConstant: PerpetualFuturesInterpType
    Linear: PerpetualFuturesInterpType
    CubicSpline: PerpetualFuturesInterpType

class PerpetualFutures:
    def __init__(
        self,
        payoff_type: PerpetualFuturesPayoffType,
        funding_type: PerpetualFuturesFundingType = ...,
        funding_frequency: Period = ...,
        calendar: Calendar = ...,
        day_counter: DayCounter = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
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

class RateAveraging:
    Simple: RateAveraging
    Compound: RateAveraging

class MultipleResetsSwap:
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def type(self) -> SwapType: ...
    def nominal(self) -> float: ...
    def fixed_rate(self) -> float: ...
    def spread(self) -> float: ...
    def resets_per_coupon(self) -> int: ...
    def averaging_method(self) -> RateAveraging: ...
    def fair_rate(self) -> float: ...
    def fair_spread(self) -> float: ...
    def fixed_leg_NPV(self) -> float: ...
    def floating_leg_NPV(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

def make_multiple_resets_swap(
    tenor: Period,
    ibor_index: IborIndex,
    resets_per_coupon: int,
    fixed_rate: float | None = ...,
    settlement_days: int | None = ...,
    nominal: float = ...,
    type: SwapType = ...,
    averaging_method: RateAveraging = ...,
    spread: float = ...,
) -> MultipleResetsSwap: ...

class FloatFloatSwap:
    def __init__(
        self,
        type: SwapType,
        nominal1: float,
        nominal2: float,
        schedule1: Schedule,
        index1: IborIndex,
        day_count1: DayCounter,
        schedule2: Schedule,
        index2: IborIndex,
        day_count2: DayCounter,
        intermediate_capital_exchange: bool = ...,
        final_capital_exchange: bool = ...,
        gearing1: float = ...,
        spread1: float = ...,
        capped_rate1: float | None = ...,
        floored_rate1: float | None = ...,
        gearing2: float = ...,
        spread2: float = ...,
        capped_rate2: float | None = ...,
        floored_rate2: float | None = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def type(self) -> SwapType: ...
    def nominal1(self) -> list[float]: ...
    def nominal2(self) -> list[float]: ...
    def spread1(self) -> list[float]: ...
    def spread2(self) -> list[float]: ...
    def gearing1(self) -> list[float]: ...
    def gearing2(self) -> list[float]: ...
    def fair_spread1(self) -> float: ...
    def fair_spread2(self) -> float: ...
    def leg_NPV(self, i: int) -> float: ...
    def leg_BPS(self, i: int) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

def make_float_float_swap(
    type: SwapType,
    nominal: float,
    index1: IborIndex,
    index2: IborIndex,
    discount_curve: YieldTermStructureHandle,
    spread1: float = ...,
    spread2: float = ...,
    length_in_years: int = ...,
    settlement_days: int = ...,
    calendar: Calendar = ...,
) -> FloatFloatSwap: ...

class OvernightIndexFuture:
    def __init__(
        self,
        overnight_index: OvernightIndex,
        value_date: Date,
        maturity_date: Date,
        convexity_adjustment: QuoteHandle = ...,
        averaging_method: RateAveraging = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def convexity_adjustment(self) -> float: ...
    def value_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...

def SofrFutureRateHelper(
    price: float,
    reference_month: Month,
    reference_year: int,
    reference_freq: Frequency,
    convexity_adjustment: float = ...,
) -> RateHelper: ...

class BMASwap:
    def __init__(
        self,
        type: SwapType,
        nominal: float,
        libor_schedule: Schedule,
        libor_fraction: float,
        libor_spread: float,
        libor_index: IborIndex,
        libor_day_count: DayCounter,
        bma_schedule: Schedule,
        bma_index: BMAIndex,
        bma_day_count: DayCounter,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def type(self) -> SwapType: ...
    def nominal(self) -> float: ...
    def libor_fraction(self) -> float: ...
    def libor_spread(self) -> float: ...
    def fair_libor_fraction(self) -> float: ...
    def fair_libor_spread(self) -> float: ...
    def libor_leg_NPV(self) -> float: ...
    def bma_leg_NPV(self) -> float: ...
    def libor_leg_BPS(self) -> float: ...
    def bma_leg_BPS(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

def make_bma_swap(
    type: SwapType,
    nominal: float,
    tenor: Period,
    libor_fraction: float,
    libor_spread: float,
    libor_index: IborIndex,
    bma_index: BMAIndex,
    discount_curve: YieldTermStructureHandle,
    settlement_days: int = ...,
    bma_frequency: Frequency = ...,
    bma_convention: BusinessDayConvention = ...,
    bma_day_count: DayCounter = ...,
) -> BMASwap: ...

def BMASwapRateHelper(
    libor_fraction: QuoteHandle,
    tenor: Period,
    settlement_days: int,
    calendar: Calendar,
    bma_period: Period,
    bma_convention: BusinessDayConvention,
    bma_day_count: DayCounter,
    bma_index: BMAIndex,
    ibor_index: IborIndex,
) -> RateHelper: ...

class SwingExercise:
    def __init__(self, dates: Sequence[Date]) -> None: ...
    def __init__(
        self, from_date: Date, to_date: Date, step_size_secs: int
    ) -> None: ...  # type: ignore[misc]
    def dates(self) -> list[Date]: ...
    def last_date(self) -> Date: ...
    def seconds(self) -> list[int]: ...

class VanillaForwardPayoff:
    def __init__(self, type: OptionType, strike: float) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...
    def name(self) -> str: ...

class VanillaSwingOption:
    def __init__(
        self,
        payoff: VanillaForwardPayoff,
        exercise: SwingExercise,
        min_exercise_rights: int,
        max_exercise_rights: int,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_fd_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

def FdSimpleBSSwingEngine(
    process: BlackScholesMertonProcess,
    t_grid: int = ...,
    x_grid: int = ...,
) -> BlackScholesMertonProcess: ...

class ExtendedOrnsteinUhlenbeckDiscretization:
    MidPoint: ExtendedOrnsteinUhlenbeckDiscretization
    Trapezodial: ExtendedOrnsteinUhlenbeckDiscretization
    GaussLobatto: ExtendedOrnsteinUhlenbeckDiscretization

class ExtendedOrnsteinUhlenbeckProcess:
    def __init__(
        self,
        speed: float,
        sigma: float,
        x0: float,
        b: float,
        discretization: ExtendedOrnsteinUhlenbeckDiscretization = ...,
    ) -> None: ...
    def x0(self) -> float: ...
    def speed(self) -> float: ...
    def volatility(self) -> float: ...

class VanillaStorageOption:
    def __init__(
        self,
        exercise: BermudanExercise,
        capacity: float,
        load: float,
        change_rate: float,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_fd_pricing_engine(
        self,
        process: ExtendedOrnsteinUhlenbeckProcess,
        risk_free_ts: YieldTermStructureHandle,
        t_grid: int = ...,
        x_grid: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

def FdSimpleExtOUStorageEngine(
    process: ExtendedOrnsteinUhlenbeckProcess,
    risk_free_ts: YieldTermStructureHandle,
    t_grid: int = ...,
    x_grid: int = ...,
) -> ExtendedOrnsteinUhlenbeckProcess: ...

class Stock:
    def __init__(self, quote: QuoteHandle) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...

class CompositeInstrument:
    def __init__(self) -> None: ...
    def add(self, instrument: Stock, multiplier: float = ...) -> None: ...
    def add(self, instrument: EuropeanOption, multiplier: float = ...) -> None: ...  # type: ignore[misc]
    def subtract(self, instrument: Stock, multiplier: float = ...) -> None: ...
    def subtract(
        self, instrument: EuropeanOption, multiplier: float = ...
    ) -> None: ...  # type: ignore[misc]
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...

class EquityTotalReturnSwap:
    def __init__(
        self,
        type: SwapType,
        nominal: float,
        schedule: Schedule,
        equity_index: EquityIndex,
        interest_rate_index: IborIndex | OvernightIndex,
        day_counter: DayCounter,
        margin: float,
        gearing: float = ...,
        payment_calendar: Calendar = ...,
        payment_convention: BusinessDayConvention = ...,
        payment_delay: int = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def type(self) -> SwapType: ...
    def nominal(self) -> float: ...
    def margin(self) -> float: ...
    def gearing(self) -> float: ...
    def payment_delay(self) -> int: ...
    def fair_margin(self) -> float: ...
    def equity_leg_NPV(self) -> float: ...
    def interest_rate_leg_NPV(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class EuropeanExercise:
    def __init__(self, date: Date) -> None: ...
    def last_date(self) -> Date: ...

class AmericanExercise:
    def __init__(
        self,
        earliest_date: Date,
        latest_date: Date,
        payoff_at_expiry: bool = ...,
    ) -> None: ...
    def __init__(self, latest_date: Date, payoff_at_expiry: bool = ...) -> None: ...  # type: ignore[misc]
    def last_date(self) -> Date: ...

class PlainVanillaPayoff:
    def __init__(self, type: OptionType, strike: float) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...

class CashOrNothingPayoff:
    def __init__(
        self, type: OptionType, strike: float, cash_payoff: float
    ) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...
    def cash_payoff(self) -> float: ...

class AssetOrNothingPayoff:
    def __init__(self, type: OptionType, strike: float) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...

class GapPayoff:
    def __init__(
        self, type: OptionType, strike: float, second_strike: float
    ) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...
    def second_strike(self) -> float: ...

class SuperFundPayoff:
    def __init__(self, strike: float, second_strike: float) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...
    def second_strike(self) -> float: ...

class SuperSharePayoff:
    def __init__(
        self, strike: float, second_strike: float, cash_payoff: float
    ) -> None: ...
    def strike(self) -> float: ...
    def option_type(self) -> OptionType: ...
    def second_strike(self) -> float: ...
    def cash_payoff(self) -> float: ...

class FloatingTypePayoff:
    def __init__(self, type: OptionType) -> None: ...
    def option_type(self) -> OptionType: ...

class PercentageStrikePayoff:
    def __init__(self, type: OptionType, moneyness: float) -> None: ...
    def strike(self) -> float: ...
    def moneyness(self) -> float: ...
    def option_type(self) -> OptionType: ...
    def optionType(self) -> OptionType: ...

class BlackScholesMertonProcess:
    def __init__(
        self,
        x0: QuoteHandle,
        dividend_ts: YieldTermStructureHandle,
        risk_free_ts: YieldTermStructureHandle,
        black_vol_ts: object,
    ) -> None: ...

class Merton76Process:
    def __init__(
        self,
        x0: QuoteHandle,
        dividend_ts: YieldTermStructureHandle,
        risk_free_ts: YieldTermStructureHandle,
        black_vol_ts: object,
        jump_intensity: QuoteHandle,
        log_mean_jump: QuoteHandle,
        log_jump_volatility: QuoteHandle,
    ) -> None: ...
    def x0(self) -> float: ...
    def jump_intensity(self) -> float: ...
    def log_mean_jump(self) -> float: ...
    def log_jump_volatility(self) -> float: ...

class VarianceGammaProcess:
    def __init__(
        self,
        s0: QuoteHandle,
        dividend_yield: YieldTermStructureHandle,
        risk_free_rate: YieldTermStructureHandle,
        sigma: float,
        nu: float,
        theta: float,
    ) -> None: ...
    def sigma(self) -> float: ...
    def nu(self) -> float: ...
    def theta(self) -> float: ...
    def x0(self) -> float: ...

class FFTVarianceGammaEngine:
    def __init__(
        self, process: VarianceGammaProcess, log_strike_spacing: float = ...
    ) -> None: ...
    def precalculate(self, options: Sequence[EuropeanOption]) -> None: ...

class FFTVanillaEngine:
    def __init__(
        self, process: BlackScholesMertonProcess, log_strike_spacing: float = ...
    ) -> None: ...
    def precalculate(self, options: Sequence[EuropeanOption]) -> None: ...

class HestonDiscretization:
    PartialTruncation: HestonDiscretization
    FullTruncation: HestonDiscretization
    Reflection: HestonDiscretization
    NonCentralChiSquareVariance: HestonDiscretization
    QuadraticExponential: HestonDiscretization
    QuadraticExponentialMartingale: HestonDiscretization
    BroadieKayaExactSchemeLobatto: HestonDiscretization
    BroadieKayaExactSchemeLaguerre: HestonDiscretization
    BroadieKayaExactSchemeTrapezoidal: HestonDiscretization

class HestonProcess:
    def __init__(
        self,
        risk_free_rate: YieldTermStructureHandle,
        dividend_yield: YieldTermStructureHandle,
        s0: QuoteHandle,
        v0: float,
        kappa: float,
        theta: float,
        sigma: float,
        rho: float,
        discretization: HestonDiscretization = ...,
    ) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...

class HestonComplexLogFormula:
    Gatheral: HestonComplexLogFormula
    BranchCorrection: HestonComplexLogFormula
    AndersenPiterbarg: HestonComplexLogFormula
    AndersenPiterbargOptCV: HestonComplexLogFormula
    AsymptoticChF: HestonComplexLogFormula
    AngledContour: HestonComplexLogFormula
    AngledContourNoCV: HestonComplexLogFormula
    OptimalCV: HestonComplexLogFormula

class CalibrationErrorType:
    RelativePriceError: CalibrationErrorType
    PriceError: CalibrationErrorType
    ImpliedVolError: CalibrationErrorType

class EndCriteriaType:
    None_: EndCriteriaType
    MaxIterations: EndCriteriaType
    StationaryPoint: EndCriteriaType
    StationaryFunctionValue: EndCriteriaType
    StationaryFunctionAccuracy: EndCriteriaType
    ZeroGradientNorm: EndCriteriaType
    FunctionEpsilonTooSmall: EndCriteriaType
    Unknown: EndCriteriaType

class EndCriteria:
    def __init__(
        self,
        max_iterations: int,
        max_stationary_state_iterations: int,
        root_epsilon: float,
        function_epsilon: float,
        gradient_norm_epsilon: float,
    ) -> None: ...
    def max_iterations(self) -> int: ...
    def max_stationary_state_iterations(self) -> int: ...
    def root_epsilon(self) -> float: ...
    def function_epsilon(self) -> float: ...
    def gradient_norm_epsilon(self) -> float: ...

class LevenbergMarquardt:
    def __init__(
        self,
        epsfcn: float = ...,
        xtol: float = ...,
        gtol: float = ...,
        use_cost_functions_jacobian: bool = ...,
    ) -> None: ...

class HestonModelHelper:
    def __init__(
        self,
        maturity: Period,
        calendar: Calendar,
        s0: QuoteHandle | float,
        strike_price: float,
        volatility: QuoteHandle,
        risk_free_rate: YieldTermStructureHandle,
        dividend_yield: YieldTermStructureHandle,
        error_type: CalibrationErrorType = ...,
    ) -> None: ...
    def calibration_error(self) -> float: ...
    def market_value(self) -> float: ...
    def model_value(self) -> float: ...
    def maturity(self) -> float: ...
    def set_pricing_engine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
    def setPricingEngine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
    def set_cos_heston_pricing_engine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...
    def setCosHestonPricingEngine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...
    def set_exponential_fitting_heston_pricing_engine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...
    def setExponentialFittingHestonPricingEngine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...

class HestonModel:
    def __init__(self, process: HestonProcess) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...
    def process(self) -> HestonProcess: ...
    def params(self) -> list[float]: ...
    def set_params(self, params: list[float]) -> None: ...
    def end_criteria(self) -> EndCriteriaType: ...
    def calibrate(
        self,
        helpers: list[HestonModelHelper],
        method: LevenbergMarquardt,
        end_criteria: EndCriteria,
    ) -> None: ...

def AnalyticHestonEngine(model: HestonModel) -> HestonModel: ...
def AnalyticPDFHestonEngine(model: HestonModel) -> HestonModel: ...
def MCEuropeanHestonEngine(process: HestonProcess) -> HestonProcess: ...
def FdHestonVanillaEngine(model: HestonModel) -> HestonModel: ...
def COSHestonEngine(model: HestonModel) -> HestonModel: ...
def ExponentialFittingHestonEngine(model: HestonModel) -> HestonModel: ...

class FdmSchemeType:
    Hundsdorfer: FdmSchemeType
    Douglas: FdmSchemeType
    CraigSneyd: FdmSchemeType
    ModifiedCraigSneyd: FdmSchemeType
    ImplicitEuler: FdmSchemeType
    ExplicitEuler: FdmSchemeType
    MethodOfLines: FdmSchemeType
    TrBDF2: FdmSchemeType
    CrankNicolson: FdmSchemeType

class FdmSchemeDesc:
    def __init__(self, type: FdmSchemeType, theta: float, mu: float) -> None: ...
    type: FdmSchemeType
    theta: float
    mu: float
    @staticmethod
    def Douglas() -> FdmSchemeDesc: ...
    @staticmethod
    def CrankNicolson() -> FdmSchemeDesc: ...
    @staticmethod
    def ImplicitEuler() -> FdmSchemeDesc: ...
    @staticmethod
    def ExplicitEuler() -> FdmSchemeDesc: ...
    @staticmethod
    def CraigSneyd() -> FdmSchemeDesc: ...
    @staticmethod
    def ModifiedCraigSneyd() -> FdmSchemeDesc: ...
    @staticmethod
    def Hundsdorfer() -> FdmSchemeDesc: ...
    @staticmethod
    def ModifiedHundsdorfer() -> FdmSchemeDesc: ...
    @staticmethod
    def MethodOfLines(
        eps: float = ..., rel_init_step_size: float = ...
    ) -> FdmSchemeDesc: ...
    @staticmethod
    def TrBDF2() -> FdmSchemeDesc: ...

class CashDividendModel:
    Spot: CashDividendModel
    Escrowed: CashDividendModel

class BlackVolTermStructureHandle:
    def empty(self) -> bool: ...

class FdmQuantoHelper:
    def __init__(
        self,
        domestic_rate: YieldTermStructureHandle,
        foreign_rate: YieldTermStructureHandle,
        fx_volatility: BlackVolTermStructureHandle | object,
        equity_fx_correlation: float,
        exch_rate_atm_level: float = ...,
    ) -> None: ...
    def quanto_adjustment(
        self, equity_vol: float, t1: float, t2: float
    ) -> float: ...

class BatesProcess:
    def __init__(
        self,
        risk_free_rate: YieldTermStructureHandle,
        dividend_yield: YieldTermStructureHandle,
        s0: QuoteHandle,
        v0: float,
        kappa: float,
        theta: float,
        sigma: float,
        rho: float,
        jump_intensity: float,
        nu: float,
        delta: float,
        discretization: HestonDiscretization = ...,
    ) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...
    def jump_intensity(self) -> float: ...
    def nu(self) -> float: ...
    def delta(self) -> float: ...

class BatesModel:
    def __init__(self, process: BatesProcess) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...
    def jump_intensity(self) -> float: ...
    def nu(self) -> float: ...
    def delta(self) -> float: ...

def BatesEngine(model: BatesModel) -> BatesModel: ...
def FdBatesVanillaEngine(model: BatesModel) -> BatesModel: ...

class BatesDetJumpModel:
    def __init__(
        self,
        process: BatesProcess,
        kappa_lambda: float = ...,
        theta_lambda: float = ...,
    ) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...
    def jump_intensity(self) -> float: ...
    def nu(self) -> float: ...
    def delta(self) -> float: ...
    def kappa_lambda(self) -> float: ...
    def theta_lambda(self) -> float: ...

class BatesDoubleExpModel:
    def __init__(
        self,
        process: HestonProcess | BatesProcess,
        jump_intensity: float = ...,
        nu_up: float = ...,
        nu_down: float = ...,
        p: float = ...,
    ) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...
    def jump_intensity(self) -> float: ...
    def nu_up(self) -> float: ...
    def nu_down(self) -> float: ...
    def p(self) -> float: ...

class BatesDoubleExpDetJumpModel:
    def __init__(
        self,
        process: HestonProcess | BatesProcess,
        jump_intensity: float = ...,
        nu_up: float = ...,
        nu_down: float = ...,
        p: float = ...,
        kappa_lambda: float = ...,
        theta_lambda: float = ...,
    ) -> None: ...
    def v0(self) -> float: ...
    def kappa(self) -> float: ...
    def theta(self) -> float: ...
    def sigma(self) -> float: ...
    def rho(self) -> float: ...
    def jump_intensity(self) -> float: ...
    def nu_up(self) -> float: ...
    def nu_down(self) -> float: ...
    def p(self) -> float: ...
    def kappa_lambda(self) -> float: ...
    def theta_lambda(self) -> float: ...

def BatesDetJumpEngine(model: BatesDetJumpModel) -> BatesDetJumpModel: ...
def BatesDoubleExpEngine(
    model: BatesDoubleExpModel,
) -> BatesDoubleExpModel: ...
def BatesDoubleExpDetJumpEngine(
    model: BatesDoubleExpDetJumpModel,
) -> BatesDoubleExpDetJumpModel: ...

class EuropeanOption:
    @overload
    def __init__(
        self, payoff: PlainVanillaPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: GapPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: SuperFundPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: SuperSharePayoff, exercise: EuropeanExercise
    ) -> None: ...
    def NPV(self) -> float: ...
    def error_estimate(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def implied_volatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_dividend_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...
    def setDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...
    def set_cash_dividend_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...
    def setCashDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...
    def set_fd_dividend_pricing_engine(
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
    def set_fd_quanto_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
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
    def set_fd_quanto_dividend_pricing_engine(
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
    def set_mc_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        required_samples: int,
        seed: int = ...,
        antithetic: bool = ...,
        brownian_bridge: bool = ...,
    ) -> None: ...
    def set_mc_heston_pricing_engine(
        self,
        process: HestonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int = ...,
        seed: int = ...,
        antithetic: bool = ...,
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
    def set_heston_pricing_engine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
    def set_cos_heston_pricing_engine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...
    def set_exponential_fitting_heston_pricing_engine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...
    def set_fd_heston_pricing_engine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_heston_dividend_pricing_engine(
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
    def set_fd_heston_quanto_pricing_engine(
        self,
        model: HestonModel,
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_heston_quanto_dividend_pricing_engine(
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
    def set_bates_pricing_engine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...
    def setBatesPricingEngine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...
    def set_variance_gamma_pricing_engine(
        self, process: VarianceGammaProcess, absolute_error: float = ...
    ) -> None: ...
    def setVarianceGammaPricingEngine(
        self, process: VarianceGammaProcess, absolute_error: float = ...
    ) -> None: ...
    @overload
    def set_fft_variance_gamma_pricing_engine(
        self, process: VarianceGammaProcess, log_strike_spacing: float = ...
    ) -> None: ...
    @overload
    def set_fft_variance_gamma_pricing_engine(
        self, engine: FFTVarianceGammaEngine
    ) -> None: ...
    @overload
    def set_fft_vanilla_pricing_engine(
        self, process: BlackScholesMertonProcess, log_strike_spacing: float = ...
    ) -> None: ...
    @overload
    def set_fft_vanilla_pricing_engine(
        self, engine: FFTVanillaEngine
    ) -> None: ...
    def set_fd_bates_pricing_engine(
        self,
        model: BatesModel,
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
    def set_fd_bates_dividend_pricing_engine(
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
    def set_bates_det_jump_pricing_engine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDetJumpPricingEngine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def set_bates_double_exp_pricing_engine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpPricingEngine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...
    def set_bates_double_exp_det_jump_pricing_engine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpDetJumpPricingEngine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...

class VanillaOption:
    def __init__(
        self, payoff: PlainVanillaPayoff, exercise: AmericanExercise
    ) -> None: ...
    def __init__(
        self, payoff: PlainVanillaPayoff, exercise: EuropeanExercise
    ) -> None: ...  # type: ignore[misc]
    def __init__(
        self, payoff: PlainVanillaPayoff, exercise: BermudanExercise
    ) -> None: ...  # type: ignore[misc]
    def __init__(
        self, payoff: CashOrNothingPayoff, exercise: EuropeanExercise
    ) -> None: ...  # type: ignore[misc]
    def __init__(
        self, payoff: CashOrNothingPayoff, exercise: AmericanExercise
    ) -> None: ...  # type: ignore[misc]
    def __init__(
        self, payoff: AssetOrNothingPayoff, exercise: AmericanExercise
    ) -> None: ...  # type: ignore[misc]
    def NPV(self) -> float: ...
    def error_estimate(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_digital_american_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_digital_american_ko_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_bjerksund_stensland_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_jump_diffusion_pricing_engine(
        self,
        process: Merton76Process,
        relative_accuracy: float = ...,
        max_iterations: int = ...,
    ) -> None: ...
    def set_cev_pricing_engine(
        self,
        f0: float,
        alpha: float,
        beta: float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...
    def set_fd_cev_pricing_engine(
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
    def set_dividend_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...
    def setDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
    ) -> None: ...
    def set_cash_dividend_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...
    def setCashDividendPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        cash_dividend_model: CashDividendModel = ...,
    ) -> None: ...
    def set_binomial_pricing_engine(
        self, process: BlackScholesMertonProcess, steps: int = ...
    ) -> None: ...
    def set_fd_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_dividend_pricing_engine(
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
    def set_fd_quanto_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
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
    def set_fd_quanto_dividend_pricing_engine(
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
    def set_heston_pricing_engine(
        self, model: HestonModel, integration_order: int = ...
    ) -> None: ...
    def set_pdf_heston_pricing_engine(
        self,
        model: HestonModel,
        gauss_lobatto_eps: float = ...,
        gauss_lobatto_integration_order: int = ...,
    ) -> None: ...
    def set_mc_heston_pricing_engine(
        self,
        process: HestonProcess,
        time_steps: int | None = ...,
        steps_per_year: int | None = ...,
        required_samples: int = ...,
        seed: int = ...,
        antithetic: bool = ...,
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
    def set_cos_heston_pricing_engine(
        self, model: HestonModel, L: float = ..., N: int = ...
    ) -> None: ...
    def set_exponential_fitting_heston_pricing_engine(
        self,
        model: HestonModel,
        control_variate: HestonComplexLogFormula = ...,
        scaling: float | None = ...,
        alpha: float = ...,
    ) -> None: ...
    def set_fd_heston_pricing_engine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_heston_dividend_pricing_engine(
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
    def set_fd_heston_quanto_pricing_engine(
        self,
        model: HestonModel,
        quanto_helper: FdmQuantoHelper,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_heston_quanto_dividend_pricing_engine(
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
    def set_bates_pricing_engine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...
    def setBatesPricingEngine(
        self, model: BatesModel, integration_order: int = ...
    ) -> None: ...
    def set_fd_bates_pricing_engine(
        self,
        model: BatesModel,
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
    def set_fd_bates_dividend_pricing_engine(
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
    def set_bates_det_jump_pricing_engine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDetJumpPricingEngine(
        self, model: BatesDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def set_bates_double_exp_pricing_engine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpPricingEngine(
        self, model: BatesDoubleExpModel, integration_order: int = ...
    ) -> None: ...
    def set_bates_double_exp_det_jump_pricing_engine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...
    def setBatesDoubleExpDetJumpPricingEngine(
        self, model: BatesDoubleExpDetJumpModel, integration_order: int = ...
    ) -> None: ...

class OvernightIndexedSwap:
    def NPV(self) -> float: ...
    def fair_rate(self) -> float: ...
    def fair_spread(self) -> float: ...
    def fixed_leg_NPV(self) -> float: ...
    def overnight_leg_NPV(self) -> float: ...
    def set_pricing_engine(self, discount_curve: YieldTermStructureHandle) -> None: ...

class ForwardRateAgreement:
    def __init__(
        self,
        index: IborIndex,
        value_date: Date,
        type: Position,
        strike_forward_rate: float,
        notional_amount: float,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...
    def __init__(
        self,
        index: IborIndex,
        value_date: Date,
        maturity_date: Date,
        type: Position,
        strike_forward_rate: float,
        notional_amount: float,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...  # type: ignore[misc]
    def NPV(self) -> float: ...
    def amount(self) -> float: ...
    def forward_rate(self) -> InterestRate: ...
    def fixing_date(self) -> Date: ...

class BondForward:
    def __init__(
        self,
        value_date: Date,
        maturity_date: Date,
        type: Position,
        strike: float,
        settlement_days: int,
        day_counter: DayCounter,
        calendar: Calendar,
        business_day_convention: BusinessDayConvention,
        bond: FixedRateBond,
        discount_curve: YieldTermStructureHandle = ...,
        income_discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def clean_forward_price(self) -> float: ...
    def forward_price(self) -> float: ...
    def forward_value(self) -> float: ...
    def spot_value(self) -> float: ...
    def spot_income(self, income_discount_curve: YieldTermStructureHandle) -> float: ...
    def settlement_date(self) -> Date: ...

class BarrierOption:
    @overload
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        rebate: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        rebate: float,
        payoff: PlainVanillaPayoff,
        exercise: AmericanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        rebate: float,
        payoff: CashOrNothingPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        rebate: float,
        payoff: CashOrNothingPayoff,
        exercise: AmericanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        rebate: float,
        payoff: AssetOrNothingPayoff,
        exercise: AmericanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def implied_volatility(
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
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_perturbative_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        order: int = ...,
        zero_gamma: bool = ...,
    ) -> None: ...
    def set_vanna_volga_pricing_engine(
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
    def set_binary_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_binomial_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int = ...,
        max_time_steps: int = ...,
    ) -> None: ...
    def set_fd_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_dividend_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        dividend_dates: Sequence[Date],
        dividend_amounts: Sequence[float],
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_heston_pricing_engine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def set_fd_heston_dividend_pricing_engine(
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
    def error_estimate(self) -> float: ...
    def set_mc_pricing_engine(
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

def FdBlackScholesBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def BinomialBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def FdHestonBarrierEngine(model: HestonModel) -> HestonModel: ...
def MCBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class TwoAssetBarrierOption:
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        rho: QuoteHandle | float,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        rho: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class TwoAssetCorrelationOption:
    def __init__(
        self,
        option_type: OptionType,
        strike1: float,
        strike2: float,
        exercise: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

class HimalayaOption:
    def __init__(
        self,
        fixing_dates: Sequence[Date],
        strike: float,
    ) -> None: ...
    def set_mc_pricing_engine(
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
    def NPV(self) -> float: ...
    def error_estimate(self) -> float: ...
    def is_expired(self) -> bool: ...
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

def MCHimalayaEngine(
    processes: Sequence[BlackScholesMertonProcess],
    rho: Matrix,
    required_samples: int | None = ...,
    required_tolerance: float | None = ...,
    seed: int = ...,
    antithetic: bool = ...,
    brownian_bridge: bool = ...,
    max_samples: int | None = ...,
) -> BlackScholesMertonProcess: ...

class PagodaOption:
    def __init__(
        self,
        fixing_dates: Sequence[Date],
        roof: float,
        fraction: float,
    ) -> None: ...
    def set_mc_pricing_engine(
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
    def NPV(self) -> float: ...
    def error_estimate(self) -> float: ...
    def is_expired(self) -> bool: ...
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

def MCPagodaEngine(
    processes: Sequence[BlackScholesMertonProcess],
    rho: Matrix,
    required_samples: int | None = ...,
    required_tolerance: float | None = ...,
    seed: int = ...,
    antithetic: bool = ...,
    brownian_bridge: bool = ...,
    max_samples: int | None = ...,
) -> BlackScholesMertonProcess: ...

class EverestOption:
    def __init__(
        self,
        notional: float,
        guarantee: float,
        exercise: EuropeanExercise,
    ) -> None: ...
    def set_mc_pricing_engine(
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
    def NPV(self) -> float: ...
    def yield_(self) -> float: ...
    def error_estimate(self) -> float: ...
    def is_expired(self) -> bool: ...

def MCEverestEngine(
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
) -> BlackScholesMertonProcess: ...

class MargrabeOption:
    @overload
    def __init__(
        self,
        quantity1: int,
        quantity2: int,
        exercise: EuropeanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        quantity1: int,
        quantity2: int,
        exercise: AmericanExercise,
    ) -> None: ...
    def set_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def set_american_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta1(self) -> float: ...
    def delta2(self) -> float: ...
    def gamma1(self) -> float: ...
    def gamma2(self) -> float: ...
    def theta(self) -> float: ...
    def is_expired(self) -> bool: ...
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

def AnalyticEuropeanMargrabeEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
) -> BlackScholesMertonProcess: ...

def AnalyticAmericanMargrabeEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
) -> BlackScholesMertonProcess: ...

class SimpleChooserOption:
    def __init__(
        self,
        choosing_date: Date,
        strike: float,
        exercise: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

def AnalyticSimpleChooserEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class ComplexChooserOption:
    def __init__(
        self,
        choosing_date: Date,
        strike_call: float,
        strike_put: float,
        call_exercise: EuropeanExercise,
        put_exercise: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

def AnalyticComplexChooserEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class HolderExtensibleOption:
    def __init__(
        self,
        type: OptionType,
        premium: float,
        second_expiry_date: Date,
        second_strike: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

def AnalyticHolderExtensibleOptionEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class WriterExtensibleOption:
    def __init__(
        self,
        payoff1: PlainVanillaPayoff,
        exercise1: EuropeanExercise,
        payoff2: PlainVanillaPayoff,
        exercise2: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

def AnalyticWriterExtensibleOptionEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class OperatorSplittingOrder:
    First: OperatorSplittingOrder
    Second: OperatorSplittingOrder

class SpreadBasketPayoff:
    def __init__(self, payoff: PlainVanillaPayoff) -> None: ...

class MinBasketPayoff:
    def __init__(self, payoff: PlainVanillaPayoff) -> None: ...

class MaxBasketPayoff:
    def __init__(self, payoff: PlainVanillaPayoff) -> None: ...

class AverageBasketPayoff:
    def __init__(
        self, payoff: PlainVanillaPayoff, weights: Sequence[float]
    ) -> None: ...

class BasketOption:
    @overload
    def __init__(
        self, payoff: SpreadBasketPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: MinBasketPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: MaxBasketPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: AverageBasketPayoff, exercise: EuropeanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: SpreadBasketPayoff, exercise: AmericanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: MinBasketPayoff, exercise: AmericanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: MaxBasketPayoff, exercise: AmericanExercise
    ) -> None: ...
    @overload
    def __init__(
        self, payoff: AverageBasketPayoff, exercise: AmericanExercise
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_kirk_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def set_bjerksund_stensland_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def set_pearson_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def set_operator_splitting_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        order: OperatorSplittingOrder = ...,
    ) -> None: ...
    def set_gaussian_copula_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
        n_points: int = ...,
    ) -> None: ...
    def set_fd_2d_pricing_engine(
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
    def set_stulz_pricing_engine(
        self,
        process1: BlackScholesMertonProcess,
        process2: BlackScholesMertonProcess,
        correlation: float,
    ) -> None: ...
    def set_choi_pricing_engine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        integration_lambda: float = ...,
        max_nr_integration_steps: int | None = ...,
        calc_fwd_delta: bool = ...,
        control_variate: bool = ...,
    ) -> None: ...
    def set_single_factor_pricing_engine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
    ) -> None: ...
    def set_deng_li_zhou_pricing_engine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
    ) -> None: ...
    def set_fd_ndim_pricing_engine(
        self,
        processes: Sequence[BlackScholesMertonProcess],
        rho: Matrix,
        x_grid: int = ...,
        t_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
        x_grids: Sequence[int] | None = ...,
    ) -> None: ...
    def set_mc_european_pricing_engine(
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
    def set_mc_american_pricing_engine(
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

def KirkEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
) -> BlackScholesMertonProcess: ...

def StulzEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
) -> BlackScholesMertonProcess: ...

def ChoiBasketEngine(
    processes: Sequence[BlackScholesMertonProcess],
    rho: Matrix,
    integration_lambda: float = ...,
    max_nr_integration_steps: int | None = ...,
    calc_fwd_delta: bool = ...,
    control_variate: bool = ...,
) -> BlackScholesMertonProcess: ...

def SingleFactorBsmBasketEngine(
    processes: Sequence[BlackScholesMertonProcess],
) -> BlackScholesMertonProcess: ...

def DengLiZhouBasketEngine(
    processes: Sequence[BlackScholesMertonProcess],
    rho: Matrix,
) -> BlackScholesMertonProcess: ...

def BjerksundStenslandSpreadEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
) -> BlackScholesMertonProcess: ...

def PearsonSpreadEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
) -> BlackScholesMertonProcess: ...

def OperatorSplittingSpreadEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
    order: OperatorSplittingOrder = ...,
) -> BlackScholesMertonProcess: ...

def GaussianCopulaSpreadEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
    n_points: int = ...,
) -> BlackScholesMertonProcess: ...

def Fd2dBlackScholesVanillaEngine(
    process1: BlackScholesMertonProcess,
    process2: BlackScholesMertonProcess,
    correlation: float,
    x_grid: int = ...,
    y_grid: int = ...,
    t_grid: int = ...,
    damping_steps: int = ...,
    scheme_desc: FdmSchemeDesc = ...,
    local_vol: bool = ...,
) -> BlackScholesMertonProcess: ...

def FdndimBlackScholesVanillaEngine(
    processes: Sequence[BlackScholesMertonProcess],
    rho: Matrix,
    x_grid: int = ...,
    t_grid: int = ...,
    damping_steps: int = ...,
    scheme_desc: FdmSchemeDesc = ...,
    x_grids: Sequence[int] | None = ...,
) -> BlackScholesMertonProcess: ...

def MCEuropeanBasketEngine(
    processes: Sequence[BlackScholesMertonProcess],
    rho: Matrix,
    time_steps: int | None = ...,
    steps_per_year: int | None = ...,
    required_samples: int | None = ...,
    required_tolerance: float | None = ...,
    seed: int = ...,
    antithetic: bool = ...,
    brownian_bridge: bool = ...,
) -> BlackScholesMertonProcess: ...

def MCAmericanBasketEngine(
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
) -> BlackScholesMertonProcess: ...

def BlackVarianceSurface(
    reference_date: Date,
    calendar: Calendar,
    dates: Sequence[Date],
    strikes: Sequence[float],
    black_vol_matrix: Matrix,
    day_counter: DayCounter,
) -> BlackVolTermStructureHandle: ...

def BlackVarianceCurve(
    reference_date: Date,
    dates: Sequence[Date],
    black_vol_curve: Sequence[float],
    day_counter: DayCounter,
    force_monotone_variance: bool = ...,
) -> BlackVolTermStructureHandle: ...

class VarianceSwap:
    def __init__(
        self,
        position: Position,
        strike: float,
        notional: float,
        start_date: Date,
        maturity_date: Date,
    ) -> None: ...
    def NPV(self) -> float: ...
    def variance(self) -> float: ...
    def is_expired(self) -> bool: ...
    def strike(self) -> float: ...
    def notional(self) -> float: ...
    def position(self) -> Position: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def set_replicating_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        call_strikes: Sequence[float],
        put_strikes: Sequence[float],
        dk: float = ...,
    ) -> None: ...
    def setReplicatingPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        call_strikes: Sequence[float],
        put_strikes: Sequence[float],
        dk: float = ...,
    ) -> None: ...
    def set_mc_pricing_engine(
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

def ReplicatingVarianceSwapEngine(
    process: BlackScholesMertonProcess,
    call_strikes: Sequence[float],
    put_strikes: Sequence[float],
    dk: float = ...,
) -> BlackScholesMertonProcess: ...

def MCVarianceSwapEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class VarianceOption:
    def __init__(
        self,
        payoff: PlainVanillaPayoff,
        notional: float,
        start_date: Date,
        maturity_date: Date,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def notional(self) -> float: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def set_integral_heston_pricing_engine(self, process: HestonProcess) -> None: ...

def IntegralHestonVarianceOptionEngine(
    process: HestonProcess,
) -> HestonProcess: ...

class CliquetOption:
    def __init__(
        self,
        payoff: PercentageStrikePayoff,
        exercise: EuropeanExercise,
        reset_dates: list[Date],
    ) -> None: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def isExpired(self) -> bool: ...

def AnalyticCliquetEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class ForwardVanillaOption:
    def __init__(
        self,
        moneyness: float,
        reset_date: Date,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_performance_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_heston_forward_pricing_engine(
        self, process: HestonProcess, integration_order: int = ...
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def is_expired(self) -> bool: ...
    def setPricingEngine(self, process: BlackScholesMertonProcess) -> None: ...
    def setPerformancePricingEngine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def isExpired(self) -> bool: ...

def ForwardVanillaEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

def ForwardPerformanceVanillaEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class CompoundOption:
    def __init__(
        self,
        mother_payoff: PlainVanillaPayoff,
        mother_exercise: EuropeanExercise,
        daughter_payoff: PlainVanillaPayoff,
        daughter_exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def theta(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...

def AnalyticCompoundOptionEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class SoftBarrierOption:
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier_lo: float,
        barrier_hi: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def implied_volatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...

class PartialBarrierRange:
    Start: PartialBarrierRange
    EndB1: PartialBarrierRange
    EndB2: PartialBarrierRange

class PartialTimeBarrierOption:
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier_range: PartialBarrierRange,
        barrier: float,
        rebate: float,
        cover_event_date: Date,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...

class DoubleBarrierOption:
    @overload
    def __init__(
        self,
        barrier_type: DoubleBarrierType,
        barrier_lo: float,
        barrier_hi: float,
        rebate: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        barrier_type: DoubleBarrierType,
        barrier_lo: float,
        barrier_hi: float,
        rebate: float,
        payoff: CashOrNothingPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        barrier_type: DoubleBarrierType,
        barrier_lo: float,
        barrier_hi: float,
        rebate: float,
        payoff: CashOrNothingPayoff,
        exercise: AmericanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def implied_volatility(
        self,
        target_price: float,
        process: BlackScholesMertonProcess,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
    ) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_suo_wang_pricing_engine(
        self, process: BlackScholesMertonProcess, series: int = ...
    ) -> None: ...
    def set_binomial_pricing_engine(
        self, process: BlackScholesMertonProcess, time_steps: int = ...
    ) -> None: ...
    def set_vanna_volga_pricing_engine(
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
    def set_binary_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_fd_heston_pricing_engine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...
    def error_estimate(self) -> float: ...
    def set_mc_pricing_engine(
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
    def setFdHestonPricingEngine(
        self,
        model: HestonModel,
        t_grid: int = ...,
        x_grid: int = ...,
        v_grid: int = ...,
        damping_steps: int = ...,
        scheme_desc: FdmSchemeDesc = ...,
    ) -> None: ...

def SuoWangDoubleBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def BinomialDoubleBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def FdHestonDoubleBarrierEngine(model: HestonModel) -> HestonModel: ...
def MCDoubleBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class CapFloor:
    def __init__(
        self,
        type: CapFloorType,
        schedule: Schedule,
        index: IborIndex,
        strike: float,
        nominal: float = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def type(self) -> CapFloorType: ...
    def set_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...
    def set_bachelier_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...
    def implied_volatility(
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

class Collar:
    def __init__(
        self,
        schedule: Schedule,
        index: IborIndex,
        cap_strike: float,
        floor_strike: float,
        nominal: float = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def type(self) -> CapFloorType: ...
    def set_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...
    def set_bachelier_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...
    def implied_volatility(
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

class Cap:
    def __init__(
        self,
        schedule: Schedule,
        index: IborIndex,
        strike: float,
        nominal: float = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def type(self) -> CapFloorType: ...
    def set_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...
    def set_bachelier_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...
    def implied_volatility(
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

class Floor:
    def __init__(
        self,
        schedule: Schedule,
        index: IborIndex,
        strike: float,
        nominal: float = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def type(self) -> CapFloorType: ...
    def set_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...
    def set_bachelier_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...
    def implied_volatility(
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

class BermudanExercise:
    def __init__(
        self, dates: Sequence[Date], payoff_at_expiry: bool = ...
    ) -> None: ...
    def dates(self) -> list[Date]: ...
    def last_date(self) -> Date: ...

class HullWhite:
    def __init__(
        self,
        term_structure: YieldTermStructureHandle,
        a: float = ...,
        sigma: float = ...,
    ) -> None: ...

class DefaultProbabilityTermStructureHandle:
    def empty(self) -> bool: ...
    def survival_probability(
        self, date: Date | float, extrapolate: bool = ...
    ) -> float: ...
    def hazard_rate(self, date: Date, extrapolate: bool = ...) -> float: ...
    def default_probability(
        self, date: Date, extrapolate: bool = ...
    ) -> float: ...
    def reference_date(self) -> Date: ...
    def max_date(self) -> Date: ...

class IsdaCdsNumericalFix:
    None: IsdaCdsNumericalFix
    Taylor: IsdaCdsNumericalFix

class IsdaCdsAccrualBias:
    HalfDayBias: IsdaCdsAccrualBias
    NoBias: IsdaCdsAccrualBias

class IsdaCdsForwardsInCouponPeriod:
    Flat: IsdaCdsForwardsInCouponPeriod
    Piecewise: IsdaCdsForwardsInCouponPeriod

class Gsr:
    @overload
    def __init__(
        self,
        term_structure: YieldTermStructureHandle,
        vol_step_dates: Sequence[Date],
        volatilities: Sequence[float],
        reversion: float,
        T: float = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        term_structure: YieldTermStructureHandle,
        vol_step_dates: Sequence[Date],
        volatilities: Sequence[float],
        reversions: Sequence[float],
        T: float = ...,
    ) -> None: ...
    def zerobond(
        self, maturity: float, t: float = ..., y: float = ...
    ) -> float: ...
    def numeraire_time(self) -> float: ...

class CreditDefaultSwap:
    def __init__(
        self,
        side: ProtectionSide,
        notional: float,
        spread: float,
        schedule: Schedule,
        payment_convention: BusinessDayConvention,
        day_counter: DayCounter,
        settles_accrual: bool = ...,
        pays_at_default_time: bool = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def fair_spread(self) -> float: ...
    def fair_upfront(self) -> float: ...
    def coupon_leg_NPV(self) -> float: ...
    def default_leg_NPV(self) -> float: ...
    def side(self) -> ProtectionSide: ...
    def notional(self) -> float: ...
    def running_spread(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...
    def set_isda_pricing_engine(
        self,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        discount_curve: YieldTermStructureHandle,
        numerical_fix: IsdaCdsNumericalFix = ...,
        accrual_bias: IsdaCdsAccrualBias = ...,
        forwards_in_coupon_period: IsdaCdsForwardsInCouponPeriod = ...,
    ) -> None: ...

class CdsOption:
    def __init__(
        self,
        swap: CreditDefaultSwap,
        exercise: EuropeanExercise,
        knocks_out: bool = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def atm_rate(self) -> float: ...
    def risky_annuity(self) -> float: ...
    def underlying(self) -> CreditDefaultSwap: ...
    def implied_volatility(
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
    def set_pricing_engine(
        self,
        probability: DefaultProbabilityTermStructureHandle,
        recovery_rate: float,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
    ) -> None: ...

class Swaption:
    @overload
    def __init__(
        self,
        swap: VanillaSwap,
        exercise: EuropeanExercise,
        delivery: SettlementType = ...,
        settlement_method: SettlementMethod = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        swap: VanillaSwap,
        exercise: BermudanExercise,
        delivery: SettlementType = ...,
        settlement_method: SettlementMethod = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> SwapType: ...
    def settlement_type(self) -> SettlementType: ...
    def settlement_method(self) -> SettlementMethod: ...
    def is_expired(self) -> bool: ...
    def implied_volatility(
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
    def set_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
        displacement: float = ...,
    ) -> None: ...
    def set_bachelier_pricing_engine(
        self,
        discount_curve: YieldTermStructureHandle,
        volatility: float,
        day_counter: DayCounter = ...,
    ) -> None: ...
    def set_tree_pricing_engine(
        self, model: HullWhite, time_steps: int = ...
    ) -> None: ...
    def set_jamshidian_pricing_engine(self, model: HullWhite) -> None: ...
    def set_gaussian1d_pricing_engine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
    ) -> None: ...
    def set_fd_hullwhite_pricing_engine(
        self,
        model: HullWhite,
        t_grid: int = ...,
        x_grid: int = ...,
        damping_steps: int = ...,
    ) -> None: ...

class NonstandardSwaption:
    def __init__(self, swaption: Swaption) -> None: ...
    def __init__(
        self,
        swap: NonstandardSwap,
        exercise: EuropeanExercise,
        delivery: SettlementType = ...,
        settlement_method: SettlementMethod = ...,
    ) -> None: ...
    def __init__(
        self,
        swap: NonstandardSwap,
        exercise: BermudanExercise,
        delivery: SettlementType = ...,
        settlement_method: SettlementMethod = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> SwapType: ...
    def settlement_type(self) -> SettlementType: ...
    def settlement_method(self) -> SettlementMethod: ...
    def is_expired(self) -> bool: ...
    def underlying_swap(self) -> NonstandardSwap: ...
    def set_gaussian1d_pricing_engine(
        self,
        model: Gsr,
        integration_points: int = ...,
        stddevs: float = ...,
        extrapolate_payoff: bool = ...,
        flat_payoff_extrapolation: bool = ...,
    ) -> None: ...

class ContinuousAveragingAsianOption:
    @overload
    def __init__(
        self,
        average_type: AverageType,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    @overload
    def __init__(
        self,
        average_type: AverageType,
        start_date: Date,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_heston_pricing_engine(
        self,
        process: HestonProcess,
        summation_cutoff: int = ...,
        xi_right_limit: float = ...,
    ) -> None: ...
    def set_vecer_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        current_average: QuoteHandle,
        start_date: Date,
        time_steps: int = ...,
        asset_steps: int = ...,
        z_min: float = ...,
        z_max: float = ...,
    ) -> None: ...
    def set_levy_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        current_average: QuoteHandle,
    ) -> None: ...

class DiscreteAveragingAsianOption:
    def __init__(
        self,
        average_type: AverageType,
        running_accumulator: float,
        past_fixings: int,
        fixing_dates: Sequence[Date],
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_turnbull_wakeman_pricing_engine(
        self, process: BlackScholesMertonProcess
    ) -> None: ...
    def set_choi_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        integration_lambda: float = ...,
        max_nr_integration_steps: int = ...,
    ) -> None: ...
    def set_heston_pricing_engine(
        self, process: HestonProcess, xi_right_limit: float = ...
    ) -> None: ...
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
    def isExpired(self) -> bool: ...

class DefaultProbabilityHelper: ...

def set_evaluation_date(date: Date) -> None: ...
def get_evaluation_date() -> Date: ...
def make_quote_handle(value: float) -> QuoteHandle: ...
def make_vanilla_swap(
    swap_tenor: Period,
    index: IborIndex,
    fixed_rate: float,
    effective_date: Date,
    fixed_leg_tenor: Period = ...,
    fixed_day_count: DayCounter = ...,
    type: SwapType = ...,
    nominal: float = ...,
    floating_spread: float = ...,
) -> VanillaSwap: ...
def make_ois(
    swap_tenor: Period,
    overnight_index: OvernightIndex,
    fixed_rate: float,
    forward_start: Period = ...,
    type: SwapType = ...,
    nominal: float = ...,
    overnight_spread: float = ...,
) -> OvernightIndexedSwap: ...
def discount_times(
    curve_handle: YieldTermStructureHandle,
    times: object,
    extrapolate: bool = ...,
) -> object: ...
def discount_dates(
    curve_handle: YieldTermStructureHandle,
    dates: Sequence[Date],
    extrapolate: bool = ...,
) -> object: ...
def BlackSwaptionEngine(
    discount_curve: YieldTermStructureHandle,
) -> YieldTermStructureHandle: ...
def BachelierSwaptionEngine(
    discount_curve: YieldTermStructureHandle,
) -> YieldTermStructureHandle: ...
def AnalyticEuropeanEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticDividendEuropeanEngine(
    process: BlackScholesMertonProcess,
    dividend_dates: Sequence[Date],
    dividend_amounts: Sequence[float],
) -> BlackScholesMertonProcess: ...
def CashDividendEuropeanEngine(
    process: BlackScholesMertonProcess,
    dividend_dates: Sequence[Date],
    dividend_amounts: Sequence[float],
    cash_dividend_model: CashDividendModel = ...,
) -> BlackScholesMertonProcess: ...
def FdBlackScholesVanillaEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
class FixedDividend:
    def __init__(self, amount: float, date: Date) -> None: ...
    def amount(self) -> float: ...
    def date(self) -> Date: ...
def DividendVector(
    dividend_dates: Sequence[Date],
    dividends: Sequence[float],
) -> list[FixedDividend]: ...
def BaroneAdesiWhaleyEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def BjerksundStenslandEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def JumpDiffusionEngine(process: Merton76Process) -> Merton76Process: ...
def AnalyticDigitalAmericanEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticDigitalAmericanKOEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def PerturbativeBarrierOptionEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticBinaryBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticSoftBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticPartialTimeBarrierOptionEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticDoubleBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticDoubleBarrierBinaryEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class ContinuousFloatingLookbackOption:
    def __init__(
        self,
        current_minmax: float,
        payoff: FloatingTypePayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def error_estimate(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_mc_pricing_engine(
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

class ContinuousFixedLookbackOption:
    def __init__(
        self,
        current_minmax: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def error_estimate(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_mc_pricing_engine(
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

def AnalyticContinuousFloatingLookbackEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticContinuousFixedLookbackEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class ContinuousPartialFloatingLookbackOption:
    def __init__(
        self,
        current_minmax: float,
        lambda_: float,
        lookback_period_end: Date,
        payoff: FloatingTypePayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def error_estimate(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_mc_pricing_engine(
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

class ContinuousPartialFixedLookbackOption:
    def __init__(
        self,
        lookback_period_start: Date,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def error_estimate(self) -> float: ...
    def set_pricing_engine(self, process: BlackScholesMertonProcess) -> None: ...
    def set_mc_pricing_engine(
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

def AnalyticContinuousPartialFloatingLookbackEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticContinuousPartialFixedLookbackEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def MCLookbackEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def BlackConstantVol(
    reference_date: Date,
    calendar: Calendar,
    volatility: float,
    day_counter: DayCounter,
) -> object: ...
def make_cap(
    tenor: Period,
    index: IborIndex,
    strike: float,
    nominal: float = ...,
    forward_start: Period = ...,
) -> CapFloor: ...
def make_floor(
    tenor: Period,
    index: IborIndex,
    strike: float,
    nominal: float = ...,
    forward_start: Period = ...,
) -> CapFloor: ...
def BachelierCapFloorEngine(
    discount_curve: YieldTermStructureHandle,
    volatility: float,
    day_counter: DayCounter = ...,
) -> YieldTermStructureHandle: ...
def BlackCapFloorEngine(
    discount_curve: YieldTermStructureHandle,
    volatility: float,
    day_counter: DayCounter = ...,
    displacement: float = ...,
) -> YieldTermStructureHandle: ...
def simulate_gbm_paths(
    process: BlackScholesMertonProcess,
    length: float,
    time_steps: int,
    samples: int,
    seed: int = ...,
) -> object: ...
def Actual365Fixed() -> DayCounter: ...
def Actual360() -> DayCounter: ...
def ActualActual(convention: ActualActualConvention = ...) -> DayCounter: ...
def Thirty360(convention: Thirty360Convention = ...) -> DayCounter: ...
def TARGET() -> Calendar: ...
def NullCalendar() -> Calendar: ...
def WeekendsOnly() -> Calendar: ...
def UnitedKingdom() -> Calendar: ...
def Switzerland() -> Calendar: ...
def Japan() -> Calendar: ...
def Germany(market: GermanyMarket = ...) -> Calendar: ...
def UnitedStates(market: UnitedStatesMarket = ...) -> Calendar: ...
def Turkey() -> Calendar: ...
class JointCalendarRule:
    JoinHolidays: JointCalendarRule
    JoinBusinessDays: JointCalendarRule

def JointCalendar(
    calendar1: Calendar,
    calendar2: Calendar,
    rule: JointCalendarRule = ...,
) -> Calendar: ...
def FlatForward(
    reference_date: Date, forward: float | QuoteHandle, day_counter: DayCounter
) -> YieldTermStructureHandle: ...
@overload
def FlatHazardRate(
    reference_date: Date, hazard_rate: float, day_counter: DayCounter
) -> DefaultProbabilityTermStructureHandle: ...
@overload
def FlatHazardRate(
    settlement_days: int,
    calendar: Calendar,
    hazard_rate: float,
    day_counter: DayCounter,
) -> DefaultProbabilityTermStructureHandle: ...
def InterpolatedHazardRateCurve(
    dates: Sequence[Date],
    hazard_rates: Sequence[float],
    day_counter: DayCounter,
    calendar: Calendar = ...,
) -> DefaultProbabilityTermStructureHandle: ...
def SpreadCdsHelper(
    running_spread: float,
    tenor: Period,
    settlement_days: int,
    calendar: Calendar,
    frequency: Frequency,
    payment_convention: BusinessDayConvention,
    rule: DateGeneration,
    day_counter: DayCounter,
    recovery_rate: float,
    discount_curve: YieldTermStructureHandle,
    settles_accrual: bool = ...,
    pays_at_default_time: bool = ...,
    model: CdsPricingModel = ...,
) -> DefaultProbabilityHelper: ...
def PiecewiseHazardRateCurve(
    reference_date: Date,
    helpers: Sequence[DefaultProbabilityHelper],
    day_counter: DayCounter,
) -> DefaultProbabilityTermStructureHandle: ...
def MidPointCdsEngine(
    probability: DefaultProbabilityTermStructureHandle,
) -> DefaultProbabilityTermStructureHandle: ...
def IsdaCdsEngine(
    probability: DefaultProbabilityTermStructureHandle,
) -> DefaultProbabilityTermStructureHandle: ...
def BlackCdsOptionEngine(
    probability: DefaultProbabilityTermStructureHandle,
) -> DefaultProbabilityTermStructureHandle: ...
def TreeSwaptionEngine(model: HullWhite) -> HullWhite: ...
def Gaussian1dSwaptionEngine(model: Gsr) -> Gsr: ...
def FdHullWhiteSwaptionEngine(model: HullWhite) -> HullWhite: ...
def AnalyticContinuousGeometricAveragePriceAsianEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def AnalyticDiscreteGeometricAveragePriceAsianEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def TurnbullWakemanAsianEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...
def ChoiAsianEngine(
    process: BlackScholesMertonProcess,
    integration_lambda: float = ...,
    max_nr_integration_steps: int = ...,
) -> BlackScholesMertonProcess: ...
def uniform_1d_mesher_locations(
    start: float, end: float, size: int
) -> object: ...
def fdm_black_scholes_mesher_locations(
    size: int,
    process: BlackScholesMertonProcess,
    maturity: float,
    strike: float,
) -> object: ...
def fdm_black_scholes_values(
    process: BlackScholesMertonProcess,
    strike: float,
    maturity: float,
    option_type: OptionType = ...,
    t_grid: int = ...,
    x_grid: int = ...,
    damping_steps: int = ...,
) -> object: ...
def DepositRateHelper(
    rate: float | QuoteHandle,
    tenor: Period,
    fixing_days: int,
    calendar: Calendar,
    convention: BusinessDayConvention,
    end_of_month: bool,
    day_counter: DayCounter,
) -> RateHelper: ...
def FraRateHelper(
    rate: float | QuoteHandle,
    months_to_start: int,
    months_to_end: int = ...,
    fixing_days: int = ...,
    calendar: Calendar = ...,
    convention: BusinessDayConvention = ...,
    end_of_month: bool = ...,
    day_counter: DayCounter = ...,
) -> RateHelper: ...
@overload
def FraRateHelper(
    rate: QuoteHandle,
    months_to_start: int,
    ibor_index: IborIndex,
) -> RateHelper: ...
def SwapRateHelper(
    rate: float | QuoteHandle,
    tenor: Period,
    calendar: Calendar,
    fixed_frequency: Frequency,
    fixed_convention: BusinessDayConvention,
    fixed_day_count: DayCounter,
    ibor_index: IborIndex,
) -> RateHelper: ...
def PiecewiseLogLinearDiscountCurve(
    reference_date: Date,
    helpers: Iterable[RateHelper],
    day_counter: DayCounter,
) -> YieldTermStructureHandle: ...
def PiecewiseLinearDiscountCurve(
    reference_date: Date,
    helpers: Iterable[RateHelper],
    day_counter: DayCounter,
) -> YieldTermStructureHandle: ...
def DiscountCurve(
    dates: Sequence[Date],
    discount_factors: Sequence[float],
    day_counter: DayCounter,
) -> YieldTermStructureHandle: ...
@overload
def Euribor3M() -> IborIndex: ...
@overload
def Euribor3M(handle: YieldTermStructureHandle) -> IborIndex: ...
@overload
def Euribor6M() -> IborIndex: ...
@overload
def Euribor6M(handle: YieldTermStructureHandle) -> IborIndex: ...
@overload
def Euribor1Y() -> IborIndex: ...
@overload
def Euribor1Y(handle: YieldTermStructureHandle) -> IborIndex: ...
@overload
def Sofr() -> OvernightIndex: ...
@overload
def Sofr(handle: YieldTermStructureHandle) -> OvernightIndex: ...
@overload
def Sonia() -> OvernightIndex: ...
@overload
def Sonia(handle: YieldTermStructureHandle) -> OvernightIndex: ...
@overload
def Estr() -> OvernightIndex: ...
@overload
def Estr(handle: YieldTermStructureHandle) -> OvernightIndex: ...
@overload
def Eonia() -> OvernightIndex: ...
@overload
def Eonia(handle: YieldTermStructureHandle) -> OvernightIndex: ...

class YieldCurveModel:
    Standard: YieldCurveModel
    ExactYield: YieldCurveModel
    ParallelShifts: YieldCurveModel
    NonParallelShifts: YieldCurveModel

class VolatilityType:
    ShiftedLognormal: VolatilityType
    Normal: VolatilityType

class SwaptionPriceType:
    Spot: SwaptionPriceType
    Forward: SwaptionPriceType

class SwapIndex:
    def name(self) -> str: ...
    def tenor(self) -> Period: ...
    def fixing_days(self) -> int: ...
    def fixing_calendar(self) -> Calendar: ...
    def day_counter(self) -> DayCounter: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def fixing(self, fixing_date: Date, forecast_today: bool = ...) -> float: ...
    def value_date(self, fixing_date: Date) -> Date: ...

class SwapSpreadIndex:
    def name(self) -> str: ...
    def fixing_days(self) -> int: ...
    def fixing_calendar(self) -> Calendar: ...
    def day_counter(self) -> DayCounter: ...
    def gearing1(self) -> float: ...
    def gearing2(self) -> float: ...
    def swap_index1(self) -> SwapIndex: ...
    def swap_index2(self) -> SwapIndex: ...
    def fixing(self, fixing_date: Date, forecast_today: bool = ...) -> float: ...
    def value_date(self, fixing_date: Date) -> Date: ...

class SwaptionVolatilityStructureHandle:
    def empty(self) -> bool: ...
    def volatility(
        self,
        option_date: Date,
        swap_tenor: Period,
        strike: float,
        extrapolate: bool = ...,
    ) -> float: ...

class CmsCouponPricer: ...

class CmsCoupon:
    def __init__(
        self,
        payment_date: Date,
        nominal: float,
        start_date: Date,
        end_date: Date,
        fixing_days: int,
        index: SwapIndex,
        gearing: float = ...,
        spread: float = ...,
        ref_period_start: Date = ...,
        ref_period_end: Date = ...,
        day_counter: DayCounter = ...,
        is_in_arrears: bool = ...,
    ) -> None: ...
    def rate(self) -> float: ...
    def amount(self) -> float: ...
    def nominal(self) -> float: ...
    def accrual_start_date(self) -> Date: ...
    def accrual_end_date(self) -> Date: ...
    def set_pricer(self, pricer: CmsCouponPricer) -> None: ...

class Swap:
    def NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def number_of_legs(self) -> int: ...
    def set_pricing_engine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...
    def set_cms_coupon_pricer(self, pricer: CmsCouponPricer) -> None: ...

@overload
def EuriborSwapIsdaFixA(
    tenor: Period, handle: YieldTermStructureHandle = ...
) -> SwapIndex: ...
@overload
def EuriborSwapIsdaFixA(
    tenor: Period,
    forwarding: YieldTermStructureHandle,
    discounting: YieldTermStructureHandle,
) -> SwapIndex: ...
def ConstantSwaptionVolatility(
    reference_date: Date,
    calendar: Calendar,
    bdc: BusinessDayConvention,
    volatility: float,
    day_counter: DayCounter,
    type: VolatilityType = ...,
    shift: float = ...,
) -> SwaptionVolatilityStructureHandle: ...
def AnalyticHaganPricer(
    swaption_vol: SwaptionVolatilityStructureHandle,
    model: YieldCurveModel,
    mean_reversion: QuoteHandle,
) -> CmsCouponPricer: ...
def NumericHaganPricer(
    swaption_vol: SwaptionVolatilityStructureHandle,
    model: YieldCurveModel,
    mean_reversion: QuoteHandle,
    lower_limit: float = ...,
    upper_limit: float = ...,
    precision: float = ...,
) -> CmsCouponPricer: ...
def make_cms(
    swap_tenor: Period,
    swap_index: SwapIndex,
    ibor_index: IborIndex,
    ibor_spread: float = ...,
    forward_start: Period = ...,
    discount_curve: YieldTermStructureHandle = ...,
    pricer: CmsCouponPricer | None = ...,
    nominal: float = ...,
) -> Swap: ...
def make_swap_spread_index(
    family_name: str,
    swap_index1: SwapIndex,
    swap_index2: SwapIndex,
    gearing1: float = ...,
    gearing2: float = ...,
) -> SwapSpreadIndex: ...
def LinearTsrPricer(
    swaption_vol: SwaptionVolatilityStructureHandle,
    mean_reversion: QuoteHandle,
    coupon_discount_curve: YieldTermStructureHandle = ...,
) -> CmsCouponPricer: ...
class CmsSpreadCouponPricer: ...
def LognormalCmsSpreadPricer(
    cms_pricer: CmsCouponPricer,
    correlation: QuoteHandle,
    coupon_discount_curve: YieldTermStructureHandle = ...,
    integration_points: int = ...,
) -> CmsSpreadCouponPricer: ...
class CmsSpreadCoupon:
    def __init__(
        self,
        payment_date: Date,
        nominal: float,
        start_date: Date,
        end_date: Date,
        fixing_days: int,
        index: SwapSpreadIndex,
        gearing: float = ...,
        spread: float = ...,
        ref_period_start: Date = ...,
        ref_period_end: Date = ...,
        day_counter: DayCounter = ...,
        is_in_arrears: bool = ...,
    ) -> None: ...
    def rate(self) -> float: ...
    def amount(self) -> float: ...
    def fixing_date(self) -> Date: ...
    def set_pricer(self, pricer: CmsSpreadCouponPricer) -> None: ...
class CappedFlooredCmsSpreadCoupon:
    def __init__(
        self,
        payment_date: Date,
        nominal: float,
        start_date: Date,
        end_date: Date,
        fixing_days: int,
        index: SwapSpreadIndex,
        gearing: float = ...,
        spread: float = ...,
        cap: float | None = ...,
        floor: float | None = ...,
        ref_period_start: Date = ...,
        ref_period_end: Date = ...,
        day_counter: DayCounter = ...,
        is_in_arrears: bool = ...,
    ) -> None: ...
    def rate(self) -> float: ...
    def amount(self) -> float: ...
    def set_pricer(self, pricer: CmsSpreadCouponPricer) -> None: ...

class CPIInterpolationType:
    Flat: CPIInterpolationType
    Linear: CPIInterpolationType

class ZeroInflationTermStructureHandle:
    def empty(self) -> bool: ...
    def zero_rate(self, date: Date, extrapolate: bool = ...) -> float: ...
    def base_date(self) -> Date: ...
    def max_date(self) -> Date: ...
    def frequency(self) -> Frequency: ...
    def reference_date(self) -> Date: ...
    def has_seasonality(self) -> bool: ...
    def set_seasonality(self, seasonality: object | None = ...) -> None: ...

class RelinkableZeroInflationTermStructureHandle:
    def empty(self) -> bool: ...
    def link_to(self, handle: ZeroInflationTermStructureHandle) -> None: ...
    def as_handle(self) -> ZeroInflationTermStructureHandle: ...
    def zero_rate(self, date: Date, extrapolate: bool = ...) -> float: ...
    def has_seasonality(self) -> bool: ...
    def set_seasonality(self, seasonality: object | None = ...) -> None: ...

class ZeroInflationIndex:
    def name(self) -> str: ...
    def frequency(self) -> Frequency: ...
    def availability_lag(self) -> Period: ...
    def last_fixing_date(self) -> Date: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def clear_fixings(self) -> None: ...
    def fixing(self, fixing_date: Date, forecast_today: bool = ...) -> float: ...

class ZeroInflationHelper: ...

class ZeroCouponInflationSwap:
    def __init__(
        self,
        type: SwapType,
        nominal: float,
        start_date: Date,
        maturity: Date,
        fix_calendar: Calendar,
        fix_convention: BusinessDayConvention,
        day_counter: DayCounter,
        fixed_rate: float,
        index: ZeroInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        adjust_inf_obs_dates: bool = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def fair_rate(self) -> float: ...
    def fixed_rate(self) -> float: ...
    def nominal(self) -> float: ...
    def type(self) -> SwapType: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def fixed_leg_NPV(self) -> float: ...
    def inflation_leg_NPV(self) -> float: ...
    def inflation_leg(self) -> list[object]: ...
    def fixed_leg(self) -> list[object]: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

@overload
def UKRPI(handle: ZeroInflationTermStructureHandle = ...) -> ZeroInflationIndex: ...
@overload
def UKRPI(
    handle: RelinkableZeroInflationTermStructureHandle,
) -> ZeroInflationIndex: ...
def EUHICP(
    handle: ZeroInflationTermStructureHandle = ...,
) -> ZeroInflationIndex: ...
def InterpolatedZeroInflationCurve(
    reference_date: Date,
    dates: Sequence[Date],
    rates: Sequence[float],
    frequency: Frequency,
    day_counter: DayCounter,
) -> ZeroInflationTermStructureHandle: ...
def FlatZeroInflationCurve(
    reference_date: Date,
    base_date: Date,
    max_date: Date,
    rate: float,
    frequency: Frequency,
    day_counter: DayCounter,
) -> ZeroInflationTermStructureHandle: ...
def ZeroCouponInflationSwapHelper(
    quote: QuoteHandle,
    observation_lag: Period,
    maturity: Date,
    calendar: Calendar,
    payment_convention: BusinessDayConvention,
    day_counter: DayCounter,
    index: ZeroInflationIndex,
    observation_interpolation: CPIInterpolationType,
) -> ZeroInflationHelper: ...
def PiecewiseZeroInflationCurve(
    reference_date: Date,
    base_date: Date,
    frequency: Frequency,
    day_counter: DayCounter,
    helpers: Sequence[ZeroInflationHelper],
) -> ZeroInflationTermStructureHandle: ...

class YoYInflationTermStructureHandle:
    def empty(self) -> bool: ...
    def yoy_rate(self, date: Date, extrapolate: bool = ...) -> float: ...
    def base_date(self) -> Date: ...
    def base_rate(self) -> float: ...
    def max_date(self) -> Date: ...
    def frequency(self) -> Frequency: ...
    def reference_date(self) -> Date: ...
    def has_seasonality(self) -> bool: ...
    def set_seasonality(self, seasonality: object | None = ...) -> None: ...

class RelinkableYoYInflationTermStructureHandle:
    def empty(self) -> bool: ...
    def link_to(self, handle: YoYInflationTermStructureHandle) -> None: ...
    def as_handle(self) -> YoYInflationTermStructureHandle: ...
    def yoy_rate(self, date: Date, extrapolate: bool = ...) -> float: ...
    def has_seasonality(self) -> bool: ...
    def set_seasonality(self, seasonality: object | None = ...) -> None: ...

class YoYInflationIndex:
    def name(self) -> str: ...
    def frequency(self) -> Frequency: ...
    def availability_lag(self) -> Period: ...
    def last_fixing_date(self) -> Date: ...
    def ratio(self) -> bool: ...
    def add_fixing(
        self, fixing_date: Date, fixing: float, force_overwrite: bool = ...
    ) -> None: ...
    def clear_fixings(self) -> None: ...
    def fixing(self, fixing_date: Date, forecast_today: bool = ...) -> float: ...

class YoYInflationHelper: ...

class YearOnYearInflationSwap:
    def __init__(
        self,
        type: SwapType,
        nominal: float,
        fixed_schedule: Schedule,
        fixed_rate: float,
        fixed_day_count: DayCounter,
        yoy_schedule: Schedule,
        yoy_index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        spread: float,
        yoy_day_count: DayCounter,
        payment_calendar: Calendar,
        payment_convention: BusinessDayConvention = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def fair_rate(self) -> float: ...
    def fair_spread(self) -> float: ...
    def fixed_rate(self) -> float: ...
    def spread(self) -> float: ...
    def nominal(self) -> float: ...
    def type(self) -> SwapType: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def fixed_leg_NPV(self) -> float: ...
    def yoy_leg_NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

@overload
def make_yoy_inflation_index(
    underlying: ZeroInflationIndex,
    handle: YoYInflationTermStructureHandle = ...,
) -> YoYInflationIndex: ...
@overload
def make_yoy_inflation_index(
    underlying: ZeroInflationIndex,
    handle: RelinkableYoYInflationTermStructureHandle,
) -> YoYInflationIndex: ...
@overload
def YYUKRPI(handle: YoYInflationTermStructureHandle = ...) -> YoYInflationIndex: ...
@overload
def YYUKRPI(
    handle: RelinkableYoYInflationTermStructureHandle,
) -> YoYInflationIndex: ...
def YYEUHICP(
    handle: YoYInflationTermStructureHandle = ...,
) -> YoYInflationIndex: ...
def InterpolatedYoYInflationCurve(
    reference_date: Date,
    dates: Sequence[Date],
    rates: Sequence[float],
    frequency: Frequency,
    day_counter: DayCounter,
) -> YoYInflationTermStructureHandle: ...
def FlatYoYInflationCurve(
    reference_date: Date,
    base_date: Date,
    max_date: Date,
    rate: float,
    frequency: Frequency,
    day_counter: DayCounter,
) -> YoYInflationTermStructureHandle: ...
def YearOnYearInflationSwapHelper(
    quote: QuoteHandle,
    observation_lag: Period,
    maturity: Date,
    calendar: Calendar,
    payment_convention: BusinessDayConvention,
    day_counter: DayCounter,
    index: YoYInflationIndex,
    observation_interpolation: CPIInterpolationType,
    nominal: YieldTermStructureHandle,
) -> YoYInflationHelper: ...
def PiecewiseYoYInflationCurve(
    reference_date: Date,
    base_date: Date,
    base_yoy_rate: float,
    frequency: Frequency,
    day_counter: DayCounter,
    helpers: Sequence[YoYInflationHelper],
) -> YoYInflationTermStructureHandle: ...

class YoYInflationCapFloorType:
    Cap: YoYInflationCapFloorType
    Floor: YoYInflationCapFloorType
    Collar: YoYInflationCapFloorType

class YoYOptionletVolatilitySurfaceHandle:
    def empty(self) -> bool: ...
    def volatility(
        self, date: Date, strike: float, extrapolate: bool = ...
    ) -> float: ...

class YoYInflationCapFloor:
    def __init__(
        self,
        type: YoYInflationCapFloorType,
        schedule: Schedule,
        index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        strike: float,
        payment_calendar: Calendar,
        day_counter: DayCounter,
        nominal: float = ...,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
        floor_strike: float | None = ...,
    ) -> None: ...
    def __init__(
        self,
        type: YoYInflationCapFloorType,
        yoy_leg: Sequence[object],
        strike: float,
        floor_strike: float | None = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> YoYInflationCapFloorType: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def set_pricing_engine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

class YoYInflationCap:
    def __init__(
        self,
        schedule: Schedule,
        index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        strike: float,
        payment_calendar: Calendar,
        day_counter: DayCounter,
        nominal: float = ...,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def __init__(
        self, yoy_leg: Sequence[object], strike: float
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> YoYInflationCapFloorType: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def set_pricing_engine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

class YoYInflationFloor:
    def __init__(
        self,
        schedule: Schedule,
        index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        strike: float,
        payment_calendar: Calendar,
        day_counter: DayCounter,
        nominal: float = ...,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def __init__(
        self, yoy_leg: Sequence[object], strike: float
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> YoYInflationCapFloorType: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def set_pricing_engine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

class YoYInflationCollar:
    def __init__(
        self,
        schedule: Schedule,
        index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        cap_strike: float,
        floor_strike: float,
        payment_calendar: Calendar,
        day_counter: DayCounter,
        nominal: float = ...,
        payment_convention: BusinessDayConvention = ...,
        fixing_days: int = ...,
    ) -> None: ...
    def __init__(
        self,
        yoy_leg: Sequence[object],
        cap_strike: float,
        floor_strike: float,
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> YoYInflationCapFloorType: ...
    def start_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def atm_rate(self, discount_curve: YieldTermStructureHandle) -> float: ...
    def set_pricing_engine(
        self,
        index: YoYInflationIndex,
        volatility: YoYOptionletVolatilitySurfaceHandle,
        nominal: YieldTermStructureHandle,
        model: str = ...,
    ) -> None: ...

def ConstantYoYOptionletVolatility(
    volatility: float,
    settlement_days: int,
    calendar: Calendar,
    bdc: BusinessDayConvention,
    day_counter: DayCounter,
    observation_lag: Period,
    frequency: Frequency,
    index_is_interpolated: bool = ...,
    min_strike: float = ...,
    max_strike: float = ...,
    vol_type: VolatilityType = ...,
    displacement: float = ...,
) -> YoYOptionletVolatilitySurfaceHandle: ...
def make_yoy_inflation_capfloor(
    type: YoYInflationCapFloorType,
    index: YoYInflationIndex,
    length_years: int,
    calendar: Calendar,
    observation_lag: Period,
    observation_interpolation: CPIInterpolationType,
    strike: float,
    nominal: float = ...,
    effective_date: Date = ...,
    day_counter: DayCounter = ...,
    payment_convention: BusinessDayConvention = ...,
) -> YoYInflationCapFloor: ...

def InterpolatedZeroCurve(
    dates: Sequence[Date],
    yields: Sequence[float],
    day_counter: DayCounter,
    interpolation: str = ...,
) -> YieldTermStructureHandle: ...
def ZeroCurve(
    dates: Sequence[Date],
    yields: Sequence[float],
    day_counter: DayCounter,
    interpolation: str = ...,
) -> YieldTermStructureHandle: ...
def GBPLibor(
    tenor: Period, handle: YieldTermStructureHandle = ...
) -> IborIndex: ...
def USDLibor(
    tenor: Period, handle: YieldTermStructureHandle = ...
) -> IborIndex: ...
def cpi_lagged_fixing(
    index: ZeroInflationIndex,
    date: Date,
    observation_lag: Period,
    interpolation: CPIInterpolationType,
) -> float: ...

class CPISwap:
    def __init__(
        self,
        type: SwapType,
        nominal: float,
        subtract_inflation_nominal: bool,
        spread: float,
        float_day_count: DayCounter,
        float_schedule: Schedule,
        float_roll: BusinessDayConvention,
        fixing_days: int,
        float_index: IborIndex | None,
        fixed_rate: float,
        base_cpi: float,
        fixed_day_count: DayCounter,
        fixed_schedule: Schedule,
        fixed_roll: BusinessDayConvention,
        observation_lag: Period,
        fixed_index: ZeroInflationIndex,
        observation_interpolation: CPIInterpolationType = ...,
        inflation_nominal: float = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def fair_rate(self) -> float: ...
    def fair_spread(self) -> float: ...
    def fixed_rate(self) -> float: ...
    def base_CPI(self) -> float: ...
    def spread(self) -> float: ...
    def nominal(self) -> float: ...
    def inflation_nominal(self) -> float: ...
    def type(self) -> SwapType: ...
    def fixed_leg_NPV(self) -> float: ...
    def float_leg_NPV(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

class CPIBond:
    def __init__(
        self,
        settlement_days: int,
        face_amount: float,
        base_cpi: float,
        observation_lag: Period,
        cpi_index: ZeroInflationIndex,
        observation_interpolation: CPIInterpolationType,
        schedule: Schedule,
        coupons: Sequence[float],
        accrual_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        issue_date: Date = ...,
        payment_calendar: Calendar = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def clean_price(self) -> float: ...
    def dirty_price(self) -> float: ...
    def base_CPI(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self, discount_curve: YieldTermStructureHandle
    ) -> None: ...

class Matrix:
    def __init__(
        self, rows: int, columns: int, data: Sequence[float]
    ) -> None: ...
    def rows(self) -> int: ...
    def columns(self) -> int: ...
    def at(self, row: int, column: int) -> float: ...

class CPICapFloorTermPriceSurfaceHandle:
    def empty(self) -> bool: ...
    def price(self, tenor: Period, strike: float) -> float: ...
    def cap_price(self, tenor: Period, strike: float) -> float: ...
    def floor_price(self, tenor: Period, strike: float) -> float: ...
    def atm_rate(self, maturity: Date) -> float: ...

class CPICapFloor:
    def __init__(
        self,
        type: OptionType,
        nominal: float,
        start_date: Date,
        base_cpi: float,
        maturity: Date,
        fix_calendar: Calendar,
        fix_convention: BusinessDayConvention,
        pay_calendar: Calendar,
        pay_convention: BusinessDayConvention,
        strike: float,
        index: ZeroInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def type(self) -> OptionType: ...
    def nominal(self) -> float: ...
    def strike(self) -> float: ...
    def fixing_date(self) -> Date: ...
    def pay_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self, price_surface: CPICapFloorTermPriceSurfaceHandle
    ) -> None: ...

def InterpolatedCPICapFloorTermPriceSurface(
    nominal: float,
    base_rate: float,
    observation_lag: Period,
    calendar: Calendar,
    bdc: BusinessDayConvention,
    day_counter: DayCounter,
    index: ZeroInflationIndex,
    observation_interpolation: CPIInterpolationType,
    nominal_curve: YieldTermStructureHandle,
    cap_strikes: Sequence[float],
    floor_strikes: Sequence[float],
    maturities: Sequence[Period],
    cap_prices: Matrix,
    floor_prices: Matrix,
) -> CPICapFloorTermPriceSurfaceHandle: ...

class Seasonality: ...

class MultiplicativePriceSeasonality(Seasonality):
    def __init__(
        self,
        seasonality_base_date: Date,
        frequency: Frequency,
        seasonality_factors: Sequence[float],
    ) -> None: ...
    def set(
        self,
        seasonality_base_date: Date,
        frequency: Frequency,
        seasonality_factors: Sequence[float],
    ) -> None: ...
    def seasonality_base_date(self) -> Date: ...
    def frequency(self) -> Frequency: ...
    def seasonality_factors(self) -> list[float]: ...
    def seasonality_factor(self, date: Date) -> float: ...

class KerkhofSeasonality(MultiplicativePriceSeasonality):
    def __init__(
        self,
        seasonality_base_date: Date,
        seasonality_factors: Sequence[float],
    ) -> None: ...

def inflation_period(
    date: Date, frequency: Frequency
) -> tuple[Date, Date]: ...

class CashFlow:
    def amount(self) -> float: ...
    def date(self) -> Date: ...
    def has_occurred(self, ref_date: Date = ...) -> bool: ...

class InflationCouponPricer: ...

class CPIVolatilitySurfaceHandle:
    def empty(self) -> bool: ...
    def volatility(
        self,
        date: Date,
        strike: float,
        observation_lag: Period = ...,
        extrapolate: bool = ...,
    ) -> float: ...
    def total_variance(
        self,
        date: Date,
        strike: float,
        observation_lag: Period = ...,
        extrapolate: bool = ...,
    ) -> float: ...
    def observation_lag(self) -> Period: ...
    def frequency(self) -> Frequency: ...
    def index_is_interpolated(self) -> bool: ...

def ConstantCPIVolatility(
    volatility: float,
    settlement_days: int,
    calendar: Calendar,
    bdc: BusinessDayConvention,
    day_counter: DayCounter,
    observation_lag: Period,
    frequency: Frequency,
    index_is_interpolated: bool = ...,
) -> CPIVolatilitySurfaceHandle: ...

class CPICouponPricer(InflationCouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: CPIVolatilitySurfaceHandle = ...,
    ) -> None: ...
    def set_caplet_volatility(
        self, caplet_vol: CPIVolatilitySurfaceHandle
    ) -> None: ...
    def caplet_volatility(self) -> CPIVolatilitySurfaceHandle: ...
    def caplet_price(self, effective_cap: float) -> float: ...
    def floorlet_price(self, effective_floor: float) -> float: ...
    def caplet_rate(self, effective_cap: float) -> float: ...
    def floorlet_rate(self, effective_floor: float) -> float: ...

class BlackCPICouponPricer(CPICouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: CPIVolatilitySurfaceHandle = ...,
    ) -> None: ...

class BachelierCPICouponPricer(CPICouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: CPIVolatilitySurfaceHandle = ...,
    ) -> None: ...

class CPICoupon(CashFlow):
    def __init__(
        self,
        base_cpi: float,
        payment_date: Date,
        nominal: float,
        start_date: Date,
        end_date: Date,
        index: ZeroInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        day_counter: DayCounter,
        fixed_rate: float,
    ) -> None: ...
    def rate(self) -> float: ...
    def fixed_rate(self) -> float: ...
    def base_CPI(self) -> float: ...
    def index_fixing(self) -> float: ...
    def adjusted_index_growth(self) -> float: ...
    def index_ratio(self, date: Date) -> float: ...
    def fixing_date(self) -> Date: ...
    def nominal(self) -> float: ...
    def set_pricer(self, pricer: InflationCouponPricer) -> None: ...
    def caplet_price(self, effective_cap: float) -> float: ...
    def floorlet_price(self, effective_floor: float) -> float: ...
    def caplet_rate(self, effective_cap: float) -> float: ...
    def floorlet_rate(self, effective_floor: float) -> float: ...

def make_cpi_leg(
    schedule: Schedule,
    index: ZeroInflationIndex,
    observation_lag: Period,
    day_counter: DayCounter,
    base_cpi: float | None = ...,
    base_date: Date = ...,
    notional: float = ...,
    fixed_rate: float = ...,
    payment_convention: BusinessDayConvention = ...,
    payment_calendar: Calendar = ...,
    observation_interpolation: CPIInterpolationType = ...,
    subtract_inflation_nominal: bool = ...,
) -> list[CashFlow]: ...
def set_cpi_coupon_pricer(
    leg: Sequence[CashFlow], pricer: InflationCouponPricer
) -> None: ...
def cashflows_npv(
    leg: Sequence[CashFlow],
    discount_curve: YieldTermStructureHandle,
    settlement: Date,
    include_settlement_date: bool = ...,
) -> float: ...
def cashflows_accrued_amount(
    leg: Sequence[CashFlow],
    settlement: Date,
    include_settlement_date: bool = ...,
) -> float: ...

class YoYInflationCouponPricer(InflationCouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: YoYOptionletVolatilitySurfaceHandle = ...,
    ) -> None: ...

class BlackYoYInflationCouponPricer(YoYInflationCouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: YoYOptionletVolatilitySurfaceHandle = ...,
    ) -> None: ...

class UnitDisplacedBlackYoYInflationCouponPricer(YoYInflationCouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: YoYOptionletVolatilitySurfaceHandle = ...,
    ) -> None: ...

class BachelierYoYInflationCouponPricer(YoYInflationCouponPricer):
    def __init__(
        self,
        nominal: YieldTermStructureHandle = ...,
        caplet_vol: YoYOptionletVolatilitySurfaceHandle = ...,
    ) -> None: ...

class YoYInflationCoupon(CashFlow):
    def __init__(
        self,
        payment_date: Date,
        nominal: float,
        start_date: Date,
        end_date: Date,
        fixing_days: int,
        index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        day_counter: DayCounter,
        gearing: float = ...,
        spread: float = ...,
    ) -> None: ...
    def rate(self) -> float: ...
    def gearing(self) -> float: ...
    def spread(self) -> float: ...
    def index_fixing(self) -> float: ...
    def adjusted_fixing(self) -> float: ...
    def fixing_date(self) -> Date: ...
    def nominal(self) -> float: ...
    def interpolation(self) -> CPIInterpolationType: ...
    def yoy_index(self) -> YoYInflationIndex: ...
    def set_pricer(self, pricer: InflationCouponPricer) -> None: ...

def make_yoy_inflation_leg(
    schedule: Schedule,
    payment_calendar: Calendar,
    index: YoYInflationIndex,
    observation_lag: Period,
    observation_interpolation: CPIInterpolationType,
    day_counter: DayCounter,
    notional: float = ...,
    fixing_days: int = ...,
    gearing: float = ...,
    spread: float = ...,
    payment_convention: BusinessDayConvention = ...,
    cap: float | None = ...,
    floor: float | None = ...,
) -> list[CashFlow]: ...
def set_yoy_coupon_pricer(
    leg: Sequence[CashFlow], pricer: InflationCouponPricer
) -> None: ...

class CappedFlooredYoYInflationCoupon(YoYInflationCoupon):
    def __init__(
        self,
        underlying: YoYInflationCoupon,
        cap: float | None = ...,
        floor: float | None = ...,
    ) -> None: ...
    def __init__(
        self,
        payment_date: Date,
        nominal: float,
        start_date: Date,
        end_date: Date,
        fixing_days: int,
        index: YoYInflationIndex,
        observation_lag: Period,
        observation_interpolation: CPIInterpolationType,
        day_counter: DayCounter,
        gearing: float = ...,
        spread: float = ...,
        cap: float | None = ...,
        floor: float | None = ...,
    ) -> None: ...
    def rate(self) -> float: ...
    def cap(self) -> float: ...
    def floor(self) -> float: ...
    def effective_cap(self) -> float: ...
    def effective_floor(self) -> float: ...
    def underlying_rate(self) -> float: ...
    def is_capped(self) -> bool: ...
    def is_floored(self) -> bool: ...
    def set_pricer(self, pricer: YoYInflationCouponPricer) -> None: ...

class IndexedCashFlow(CashFlow):
    def notional(self) -> float: ...
    def base_date(self) -> Date: ...
    def fixing_date(self) -> Date: ...
    def growth_only(self) -> bool: ...
    def base_fixing(self) -> float: ...
    def index_fixing(self) -> float: ...

class CPICashFlow(IndexedCashFlow):
    def __init__(
        self,
        notional: float,
        index: ZeroInflationIndex,
        base_date: Date,
        base_fixing: float,
        observation_date: Date,
        observation_lag: Period,
        interpolation: CPIInterpolationType,
        payment_date: Date,
        growth_only: bool = ...,
    ) -> None: ...
    def observation_date(self) -> Date: ...
    def observation_lag(self) -> Period: ...
    def interpolation(self) -> CPIInterpolationType: ...
    def frequency(self) -> Frequency: ...
    def cpi_index(self) -> ZeroInflationIndex: ...

class ZeroInflationCashFlow(IndexedCashFlow):
    def __init__(
        self,
        notional: float,
        index: ZeroInflationIndex,
        observation_interpolation: CPIInterpolationType,
        start_date: Date,
        end_date: Date,
        observation_lag: Period,
        payment_date: Date,
        growth_only: bool = ...,
    ) -> None: ...
    def zero_inflation_index(self) -> ZeroInflationIndex: ...
    def observation_interpolation(self) -> CPIInterpolationType: ...

class YoYCapFloorTermPriceSurfaceHandle:
    def empty(self) -> bool: ...
    def price(self, tenor: Period, strike: float) -> float: ...
    def cap_price(self, tenor: Period, strike: float) -> float: ...
    def floor_price(self, tenor: Period, strike: float) -> float: ...
    def atm_yoy_swap_rate(
        self, date: Date, extrapolate: bool = ...
    ) -> float: ...
    def atm_yoy_rate(self, date: Date, extrapolate: bool = ...) -> float: ...
    def atm_yoy_swap_time_rates(self) -> tuple[list[float], list[float]]: ...
    def atm_yoy_swap_date_rates(self) -> tuple[list[Date], list[float]]: ...
    def yoy_ts(self) -> YoYInflationTermStructureHandle: ...
    def cap_strikes(self) -> list[float]: ...
    def floor_strikes(self) -> list[float]: ...
    def maturities(self) -> list[Period]: ...
    def observation_lag(self) -> Period: ...

def InterpolatedYoYCapFloorTermPriceSurface(
    fixing_days: int,
    yy_lag: Period,
    yoy_index: YoYInflationIndex,
    observation_interpolation: CPIInterpolationType,
    nominal_curve: YieldTermStructureHandle,
    day_counter: DayCounter,
    calendar: Calendar,
    bdc: BusinessDayConvention,
    cap_strikes: Sequence[float],
    floor_strikes: Sequence[float],
    maturities: Sequence[Period],
    cap_prices: Matrix,
    floor_prices: Matrix,
) -> YoYCapFloorTermPriceSurfaceHandle: ...

class BondPriceType:
    Clean: BondPriceType
    Dirty: BondPriceType

class DurationType:
    Simple: DurationType
    Macaulay: DurationType
    Modified: DurationType

class BondPrice:
    def __init__(
        self, amount: float, type: BondPriceType = ...
    ) -> None: ...
    def amount(self) -> float: ...
    def type(self) -> BondPriceType: ...
    def is_valid(self) -> bool: ...

class CallabilityType:
    Call: CallabilityType
    Put: CallabilityType

class Callability:
    def price(self) -> BondPrice: ...
    def type(self) -> CallabilityType: ...
    def date(self) -> Date: ...

@overload
def make_callability(
    price: BondPrice, type: CallabilityType, date: Date
) -> Callability: ...
@overload
def make_callability(
    amount: float,
    price_type: BondPriceType,
    type: CallabilityType,
    date: Date,
) -> Callability: ...

class CallableFixedRateBond:
    def __init__(
        self,
        settlement_days: int,
        face_amount: float,
        schedule: Schedule,
        coupons: Sequence[float],
        accrual_day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        redemption: float = ...,
        issue_date: Date = ...,
        put_call_schedule: Sequence[Callability] = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def clean_price(self) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def implied_volatility(
        self,
        target_price: BondPrice,
        discount_curve: YieldTermStructureHandle,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
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
    def oas(
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
    def clean_price_oas(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
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
    def effective_duration(
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
    def effective_convexity(
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
    def set_tree_pricing_engine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...
    def set_black_pricing_engine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...
    def setBlackPricingEngine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

class CallableZeroCouponBond:
    def __init__(
        self,
        settlement_days: int,
        face_amount: float,
        calendar: Calendar,
        maturity_date: Date,
        day_counter: DayCounter,
        payment_convention: BusinessDayConvention = ...,
        redemption: float = ...,
        issue_date: Date = ...,
        put_call_schedule: Sequence[Callability] = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def clean_price(self) -> float: ...
    def dirty_price(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def implied_volatility(
        self,
        target_price: BondPrice,
        discount_curve: YieldTermStructureHandle,
        accuracy: float = ...,
        max_evaluations: int = ...,
        min_vol: float = ...,
        max_vol: float = ...,
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
    def oas(
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
    def clean_price_oas(
        self,
        oas: float,
        engine_ts: YieldTermStructureHandle,
        day_counter: DayCounter,
        compounding: Compounding,
        frequency: Frequency,
        settlement_date: Date = ...,
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
    def effective_duration(
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
    def effective_convexity(
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
    def set_tree_pricing_engine(
        self,
        model: HullWhite,
        time_steps: int = ...,
        discount_curve: YieldTermStructureHandle = ...,
    ) -> None: ...
    def set_black_pricing_engine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...
    def setBlackPricingEngine(
        self,
        fwd_yield_vol: QuoteHandle | float,
        discount_curve: YieldTermStructureHandle,
    ) -> None: ...

def BlackCallableFixedRateBondEngine(
    fwd_yield_vol: QuoteHandle,
    discount_curve: YieldTermStructureHandle,
) -> YieldTermStructureHandle: ...
def BlackCallableZeroCouponBondEngine(
    fwd_yield_vol: QuoteHandle,
    discount_curve: YieldTermStructureHandle,
) -> YieldTermStructureHandle: ...

def make_soft_callability(
    amount: float,
    price_type: BondPriceType,
    date: Date,
    trigger: float,
) -> Callability: ...

class ConvertibleZeroCouponBond:
    def __init__(
        self,
        exercise: EuropeanExercise | AmericanExercise,
        conversion_ratio: float,
        callability: Sequence[Callability],
        issue_date: Date,
        settlement_days: int,
        day_counter: DayCounter,
        schedule: Schedule,
        redemption: float = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def clean_price(self) -> float: ...
    def dirty_price(self) -> float: ...
    def conversion_ratio(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def set_binomial_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...
    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

class ConvertibleFixedCouponBond:
    def __init__(
        self,
        exercise: EuropeanExercise | AmericanExercise,
        conversion_ratio: float,
        callability: Sequence[Callability],
        issue_date: Date,
        settlement_days: int,
        coupons: Sequence[float],
        day_counter: DayCounter,
        schedule: Schedule,
        redemption: float = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def clean_price(self) -> float: ...
    def dirty_price(self) -> float: ...
    def conversion_ratio(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def set_binomial_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...
    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

class ConvertibleFloatingRateBond:
    def __init__(
        self,
        exercise: EuropeanExercise | AmericanExercise,
        conversion_ratio: float,
        callability: Sequence[Callability],
        issue_date: Date,
        settlement_days: int,
        index: IborIndex,
        fixing_days: int,
        spreads: Sequence[float],
        day_counter: DayCounter,
        schedule: Schedule,
        redemption: float = ...,
    ) -> None: ...
    def NPV(self) -> float: ...
    def clean_price(self) -> float: ...
    def dirty_price(self) -> float: ...
    def conversion_ratio(self) -> float: ...
    def settlement_date(self) -> Date: ...
    def maturity_date(self) -> Date: ...
    def set_binomial_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...
    def setBinomialPricingEngine(
        self,
        process: BlackScholesMertonProcess,
        time_steps: int,
        credit_spread: QuoteHandle | float,
    ) -> None: ...

def BinomialConvertibleEngine(
    process: BlackScholesMertonProcess,
    time_steps: int,
    credit_spread: QuoteHandle,
) -> BlackScholesMertonProcess: ...

# --- Phase 24: currencies / money / FX forward ---

class Currency:
    def __init__(self) -> None: ...
    def name(self) -> str: ...
    def code(self) -> str: ...
    def numeric_code(self) -> int: ...
    def symbol(self) -> str: ...
    def fraction_symbol(self) -> str: ...
    def fractions_per_unit(self) -> int: ...
    def empty(self) -> bool: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __mul__(self, value: float) -> Money: ...
    def __rmul__(self, value: float) -> Money: ...

def USDCurrency() -> Currency: ...
def TRYCurrency() -> Currency: ...
def EURCurrency() -> Currency: ...
def GBPCurrency() -> Currency: ...
def CHFCurrency() -> Currency: ...
def SGDCurrency() -> Currency: ...

class MoneyConversionType:
    NoConversion: MoneyConversionType
    BaseCurrencyConversion: MoneyConversionType
    AutomatedConversion: MoneyConversionType

def set_money_conversion(conversion_type: MoneyConversionType) -> None: ...
def get_money_conversion() -> MoneyConversionType: ...

class Money:
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, currency: Currency, value: float) -> None: ...
    @overload
    def __init__(self, value: float, currency: Currency) -> None: ...
    def currency(self) -> Currency: ...
    def value(self) -> float: ...
    def rounded(self) -> Money: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __mul__(self, x: float) -> Money: ...
    def __rmul__(self, x: float) -> Money: ...
    def __truediv__(self, x: float) -> Money: ...

class ExchangeRateType:
    Direct: ExchangeRateType
    Derived: ExchangeRateType

class ExchangeRate:
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self, source: Currency, target: Currency, rate: float
    ) -> None: ...
    def source(self) -> Currency: ...
    def target(self) -> Currency: ...
    def type(self) -> ExchangeRateType: ...
    def rate(self) -> float: ...
    def exchange(self, amount: Money) -> Money: ...
    @staticmethod
    def chain(r1: ExchangeRate, r2: ExchangeRate) -> ExchangeRate: ...

def exchange_rate_manager_clear() -> None: ...
def exchange_rate_manager_add(
    rate: ExchangeRate,
    start_date: Date = ...,
    end_date: Date = ...,
) -> None: ...
def exchange_rate_manager_lookup(
    source: Currency,
    target: Currency,
    date: Date = ...,
    type: ExchangeRateType = ...,
) -> ExchangeRate: ...

class FxForward:
    @overload
    def __init__(
        self,
        source_nominal: float,
        source_currency: Currency,
        target_nominal: float,
        target_currency: Currency,
        maturity_date: Date,
        pay_source_currency: bool,
        settlement_days: int = ...,
        payment_calendar: Calendar = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        source_nominal: float,
        source_currency: Currency,
        target_currency: Currency,
        forward_rate: float,
        maturity_date: Date,
        pay_source_currency: bool,
        settlement_days: int = ...,
        payment_calendar: Calendar = ...,
    ) -> None: ...
    def source_nominal(self) -> float: ...
    def target_nominal(self) -> float: ...
    def source_currency(self) -> Currency: ...
    def target_currency(self) -> Currency: ...
    def maturity_date(self) -> Date: ...
    def pay_source_currency(self) -> bool: ...
    def forward_rate(self) -> float: ...
    def settlement_days(self) -> int: ...
    def settlement_calendar(self) -> Calendar: ...
    def settlement_date(self) -> Date: ...
    def is_expired(self) -> bool: ...
    def NPV(self) -> float: ...
    def fair_forward_rate(self) -> float: ...
    def npv_source_currency(self) -> float: ...
    def npv_target_currency(self) -> float: ...
    @overload
    def set_pricing_engine(
        self,
        source_curve: YieldTermStructureHandle,
        target_curve: YieldTermStructureHandle,
        spot_fx: QuoteHandle,
    ) -> None: ...
    @overload
    def set_pricing_engine(
        self,
        source_curve: YieldTermStructureHandle,
        target_curve: YieldTermStructureHandle,
        spot_fx: float,
    ) -> None: ...

class QuantoVanillaOption:
    def __init__(
        self, payoff: PlainVanillaPayoff, exercise: EuropeanExercise
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def qvega(self) -> float: ...
    def qrho(self) -> float: ...
    def qlambda(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
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
    def isExpired(self) -> bool: ...

def QuantoEuropeanEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class QuantoForwardVanillaOption:
    def __init__(
        self,
        moneyness: float,
        reset_date: Date,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def qvega(self) -> float: ...
    def qrho(self) -> float: ...
    def qlambda(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def set_performance_pricing_engine(
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
    def setPerformancePricingEngine(
        self,
        process: BlackScholesMertonProcess,
        foreign_risk_free_rate: YieldTermStructureHandle,
        exchange_rate_volatility: object,
        correlation: QuoteHandle | float,
    ) -> None: ...
    def isExpired(self) -> bool: ...

def QuantoForwardEuropeanEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

def QuantoForwardPerformanceEuropeanEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class QuantoBarrierOption:
    def __init__(
        self,
        barrier_type: BarrierType,
        barrier: float,
        rebate: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def qvega(self) -> float: ...
    def qrho(self) -> float: ...
    def qlambda(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
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
    def isExpired(self) -> bool: ...

def QuantoBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

class QuantoDoubleBarrierOption:
    def __init__(
        self,
        barrier_type: DoubleBarrierType,
        barrier_lo: float,
        barrier_hi: float,
        rebate: float,
        payoff: PlainVanillaPayoff,
        exercise: EuropeanExercise,
    ) -> None: ...
    def NPV(self) -> float: ...
    def delta(self) -> float: ...
    def gamma(self) -> float: ...
    def vega(self) -> float: ...
    def qvega(self) -> float: ...
    def qrho(self) -> float: ...
    def qlambda(self) -> float: ...
    def is_expired(self) -> bool: ...
    def set_pricing_engine(
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
    def isExpired(self) -> bool: ...

def QuantoDoubleBarrierEngine(
    process: BlackScholesMertonProcess,
) -> BlackScholesMertonProcess: ...

__version__: str
