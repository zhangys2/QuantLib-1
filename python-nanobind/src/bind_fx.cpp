#include "bindings.hpp"

#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>

#include <optional>
#include <sstream>

#include <ql/currency.hpp>
#include <ql/currencies/america.hpp>
#include <ql/indexes/equityindex.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/instruments/equitytotalreturnswap.hpp>
#include <ql/currencies/asia.hpp>
#include <ql/currencies/europe.hpp>
#include <ql/currencies/exchangeratemanager.hpp>
#include <ql/exercise.hpp>
#include <ql/exchangerate.hpp>
#include <ql/handle.hpp>
#include <ql/instruments/forwardvanillaoption.hpp>
#include <ql/instruments/fxforward.hpp>
#include <ql/instruments/payoffs.hpp>
#include <ql/instruments/quantoforwardvanillaoption.hpp>
#include <ql/instruments/quantovanillaoption.hpp>
#include <ql/instruments/vanillaoption.hpp>
#include <ql/money.hpp>
#include <ql/pricingengines/forward/discountingfxforwardengine.hpp>
#include <ql/pricingengines/swap/discountingswapengine.hpp>
#include <ql/pricingengines/forward/forwardengine.hpp>
#include <ql/pricingengines/forward/forwardperformanceengine.hpp>
#include <ql/pricingengines/quanto/quantoengine.hpp>
#include <ql/pricingengines/vanilla/analyticeuropeanengine.hpp>
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/quotes/simplequote.hpp>
#include <ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/calendar.hpp>
#include <ql/time/date.hpp>
#include <ql/time/daycounter.hpp>
#include <ql/time/schedule.hpp>

using namespace QuantLib;

void bind_fx(nb::module_& m) {
    // --- Phase 24: currencies, money, exchange rates, FX forward ---

    // Currency subclasses slice to value Currency (no MI hierarchy in Python).
    nb::class_<Currency>(m, "Currency")
        .def(nb::init<>())
        .def("name", &Currency::name)
        .def("code", &Currency::code)
        .def("numeric_code", &Currency::numericCode)
        .def("symbol", &Currency::symbol)
        .def("fraction_symbol", &Currency::fractionSymbol)
        .def("fractions_per_unit", &Currency::fractionsPerUnit)
        .def("empty", &Currency::empty)
        .def("__eq__",
             [](const Currency& a, const Currency& b) { return a == b; })
        .def("__ne__",
             [](const Currency& a, const Currency& b) { return a != b; })
        .def("__repr__",
             [](const Currency& c) {
                 if (c.empty()) {
                     return std::string("Currency()");
                 }
                 return "Currency('" + c.code() + "')";
             })
        .def("__mul__",
             [](const Currency& c, Decimal value) { return value * c; })
        .def("__rmul__",
             [](const Currency& c, Decimal value) { return value * c; });

    m.def("USDCurrency", []() { return Currency(USDCurrency()); });
    m.def("EURCurrency", []() { return Currency(EURCurrency()); });
    m.def("GBPCurrency", []() { return Currency(GBPCurrency()); });
    m.def("TRYCurrency", []() { return Currency(TRYCurrency()); });
    m.def("SGDCurrency", []() { return Currency(SGDCurrency()); });

    nb::enum_<Money::ConversionType>(m, "MoneyConversionType")
        .value("NoConversion", Money::NoConversion)
        .value("BaseCurrencyConversion", Money::BaseCurrencyConversion)
        .value("AutomatedConversion", Money::AutomatedConversion);

    m.def(
        "set_money_conversion",
        [](Money::ConversionType type) {
            Money::Settings::instance().conversionType() = type;
        },
        nb::arg("conversion_type"),
        "Set Money::Settings conversion type (default NoConversion).");

    m.def(
        "get_money_conversion",
        []() { return Money::Settings::instance().conversionType(); },
        "Get Money::Settings conversion type.");

    nb::class_<Money>(m, "Money")
        .def(nb::init<>())
        .def(nb::init<Currency, Decimal>(),
             nb::arg("currency"),
             nb::arg("value"))
        .def(nb::init<Decimal, Currency>(),
             nb::arg("value"),
             nb::arg("currency"))
        .def("currency", &Money::currency)
        .def("value", &Money::value)
        .def("rounded", &Money::rounded)
        .def("__eq__", [](const Money& a, const Money& b) { return a == b; })
        .def("__ne__", [](const Money& a, const Money& b) { return a != b; })
        .def("__repr__",
             [](const Money& money) {
                 std::ostringstream oss;
                 oss << money;
                 return oss.str();
             })
        .def("__mul__",
             [](const Money& money, Decimal x) { return money * x; })
        .def("__rmul__",
             [](const Money& money, Decimal x) { return x * money; })
        .def("__truediv__",
             [](const Money& money, Decimal x) { return money / x; });

    nb::enum_<ExchangeRate::Type>(m, "ExchangeRateType")
        .value("Direct", ExchangeRate::Direct)
        .value("Derived", ExchangeRate::Derived);

    nb::class_<ExchangeRate>(m, "ExchangeRate")
        .def(nb::init<>())
        .def(nb::init<Currency, Currency, Decimal>(),
             nb::arg("source"),
             nb::arg("target"),
             nb::arg("rate"))
        .def("source", &ExchangeRate::source)
        .def("target", &ExchangeRate::target)
        .def("type", &ExchangeRate::type)
        .def("rate", &ExchangeRate::rate)
        .def("exchange", &ExchangeRate::exchange, nb::arg("amount"))
        .def_static("chain",
                    &ExchangeRate::chain,
                    nb::arg("r1"),
                    nb::arg("r2"));

    m.def(
        "exchange_rate_manager_clear",
        []() { ExchangeRateManager::instance().clear(); },
        "Clear rates added to ExchangeRateManager.");

    m.def(
        "exchange_rate_manager_add",
        [](const ExchangeRate& rate,
           const Date& start_date,
           const Date& end_date) {
            ExchangeRateManager::instance().add(rate, start_date, end_date);
        },
        nb::arg("rate"),
        nb::arg("start_date") = Date::minDate(),
        nb::arg("end_date") = Date::maxDate(),
        "Add an exchange rate to ExchangeRateManager.");

    m.def(
        "exchange_rate_manager_lookup",
        [](const Currency& source,
           const Currency& target,
           const Date& date,
           ExchangeRate::Type type) {
            return ExchangeRateManager::instance().lookup(
                source, target, date, type);
        },
        nb::arg("source"),
        nb::arg("target"),
        nb::arg("date") = Date(),
        nb::arg("type") = ExchangeRate::Derived,
        "Lookup an exchange rate from ExchangeRateManager.");

    // FxForward is Instrument (MI) — standalone concrete wrapper.
    nb::class_<FxForward>(m, "FxForward")
        .def(
            "__init__",
            [](FxForward* self,
               Real source_nominal,
               const Currency& source_currency,
               Real target_nominal,
               const Currency& target_currency,
               const Date& maturity_date,
               bool pay_source_currency,
               Natural settlement_days,
               const Calendar& payment_calendar) {
                new (self) FxForward(source_nominal,
                                     source_currency,
                                     target_nominal,
                                     target_currency,
                                     maturity_date,
                                     pay_source_currency,
                                     settlement_days,
                                     payment_calendar);
            },
            nb::arg("source_nominal"),
            nb::arg("source_currency"),
            nb::arg("target_nominal"),
            nb::arg("target_currency"),
            nb::arg("maturity_date"),
            nb::arg("pay_source_currency"),
            nb::arg("settlement_days") = 2,
            nb::arg("payment_calendar") = Calendar())
        .def(
            "__init__",
            [](FxForward* self,
               Real source_nominal,
               const Currency& source_currency,
               const Currency& target_currency,
               Real forward_rate,
               const Date& maturity_date,
               bool pay_source_currency,
               Natural settlement_days,
               const Calendar& payment_calendar) {
                new (self) FxForward(source_nominal,
                                     source_currency,
                                     target_currency,
                                     forward_rate,
                                     maturity_date,
                                     pay_source_currency,
                                     settlement_days,
                                     payment_calendar);
            },
            nb::arg("source_nominal"),
            nb::arg("source_currency"),
            nb::arg("target_currency"),
            nb::arg("forward_rate"),
            nb::arg("maturity_date"),
            nb::arg("pay_source_currency"),
            nb::arg("settlement_days") = 2,
            nb::arg("payment_calendar") = Calendar())
        .def("source_nominal", &FxForward::sourceNominal)
        .def("target_nominal", &FxForward::targetNominal)
        .def("source_currency", &FxForward::sourceCurrency)
        .def("target_currency", &FxForward::targetCurrency)
        .def("maturity_date", &FxForward::maturityDate)
        .def("pay_source_currency", &FxForward::paySourceCurrency)
        .def("forward_rate", &FxForward::forwardRate)
        .def("settlement_days", &FxForward::settlementDays)
        .def("settlement_calendar", &FxForward::settlementCalendar)
        .def("settlement_date", &FxForward::settlementDate)
        .def("is_expired", &FxForward::isExpired)
        .def("NPV", [](FxForward& fwd) { return fwd.NPV(); })
        .def("fair_forward_rate", &FxForward::fairForwardRate)
        .def("npv_source_currency", &FxForward::npvSourceCurrency)
        .def("npv_target_currency", &FxForward::npvTargetCurrency)
        .def(
            "set_pricing_engine",
            [](FxForward& fwd,
               const Handle<YieldTermStructure>& source_curve,
               const Handle<YieldTermStructure>& target_curve,
               const Handle<Quote>& spot_fx) {
                fwd.setPricingEngine(
                    ext::make_shared<DiscountingFxForwardEngine>(
                        source_curve, target_curve, spot_fx));
            },
            nb::arg("source_curve"),
            nb::arg("target_curve"),
            nb::arg("spot_fx"),
            "Attach DiscountingFxForwardEngine "
            "(spot_fx = target per unit of source).")
        .def(
            "set_pricing_engine",
            [](FxForward& fwd,
               const Handle<YieldTermStructure>& source_curve,
               const Handle<YieldTermStructure>& target_curve,
               Real spot_fx) {
                fwd.setPricingEngine(
                    ext::make_shared<DiscountingFxForwardEngine>(
                        source_curve,
                        target_curve,
                        Handle<Quote>(ext::make_shared<SimpleQuote>(spot_fx))));
            },
            nb::arg("source_curve"),
            nb::arg("target_curve"),
            nb::arg("spot_fx"),
            "Attach DiscountingFxForwardEngine from a scalar spot FX rate.");

    // --- Phase 40: quanto vanilla options (standalone; OneAssetOption MI) ---
    nb::class_<QuantoVanillaOption>(m, "QuantoVanillaOption")
        .def(
            "__init__",
            [](QuantoVanillaOption* self,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) QuantoVanillaOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Quanto vanilla (Haug p.105); payoff currency ≠ asset currency.")
        .def("NPV", [](QuantoVanillaOption& opt) { return opt.NPV(); })
        .def("delta", [](QuantoVanillaOption& opt) { return opt.delta(); })
        .def("gamma", [](QuantoVanillaOption& opt) { return opt.gamma(); })
        .def("vega", [](QuantoVanillaOption& opt) { return opt.vega(); })
        .def("qvega", &QuantoVanillaOption::qvega)
        .def("qrho", &QuantoVanillaOption::qrho)
        .def("qlambda", &QuantoVanillaOption::qlambda)
        .def("is_expired", &QuantoVanillaOption::isExpired)
        .def(
            "set_pricing_engine",
            [](QuantoVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               const Handle<Quote>& correlation) {
                opt.setPricingEngine(
                    ext::make_shared<
                        QuantoEngine<VanillaOption, AnalyticEuropeanEngine>>(
                        process,
                        foreign_risk_free_rate,
                        exchange_rate_volatility,
                        correlation));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach QuantoEngine<VanillaOption, AnalyticEuropeanEngine>.")
        .def(
            "set_pricing_engine",
            [](QuantoVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<
                        QuantoEngine<VanillaOption, AnalyticEuropeanEngine>>(
                        process,
                        foreign_risk_free_rate,
                        exchange_rate_volatility,
                        Handle<Quote>(
                            ext::make_shared<SimpleQuote>(correlation))));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach quanto engine from a scalar FX/asset correlation.");

    m.def(
        "QuantoEuropeanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias documentation token — prefer "
        "QuantoVanillaOption.set_pricing_engine(process, foreign_rfr, "
        "fx_vol, correlation).");

    // --- Phase 41: quanto-forward vanilla options -------------------------
    // ForwardVanillaOption / OneAssetOption MI — standalone concrete wrapper.
    using QuantoForwardEngine =
        QuantoEngine<ForwardVanillaOption,
                     ForwardVanillaEngine<AnalyticEuropeanEngine>>;
    // Phase 44: performance variant of the same instrument.
    using QuantoForwardPerformanceEngine =
        QuantoEngine<ForwardVanillaOption,
                     ForwardPerformanceVanillaEngine<AnalyticEuropeanEngine>>;

    nb::class_<QuantoForwardVanillaOption>(m, "QuantoForwardVanillaOption")
        .def(
            "__init__",
            [](QuantoForwardVanillaOption* self,
               Real moneyness,
               const Date& reset_date,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) QuantoForwardVanillaOption(
                    moneyness,
                    reset_date,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("moneyness"),
            nb::arg("reset_date"),
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Quanto forward-start vanilla; payoff strike ignored "
            "(moneyness * spot at reset).")
        .def("NPV",
             [](QuantoForwardVanillaOption& opt) { return opt.NPV(); })
        .def("delta",
             [](QuantoForwardVanillaOption& opt) { return opt.delta(); })
        .def("gamma",
             [](QuantoForwardVanillaOption& opt) { return opt.gamma(); })
        .def("vega",
             [](QuantoForwardVanillaOption& opt) { return opt.vega(); })
        .def("qvega", &QuantoForwardVanillaOption::qvega)
        .def("qrho", &QuantoForwardVanillaOption::qrho)
        .def("qlambda", &QuantoForwardVanillaOption::qlambda)
        .def("is_expired", &QuantoForwardVanillaOption::isExpired)
        .def(
            "set_pricing_engine",
            [](QuantoForwardVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               const Handle<Quote>& correlation) {
                opt.setPricingEngine(ext::make_shared<QuantoForwardEngine>(
                    process,
                    foreign_risk_free_rate,
                    exchange_rate_volatility,
                    correlation));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach QuantoEngine over ForwardVanillaEngine"
            "<AnalyticEuropeanEngine>.")
        .def(
            "set_pricing_engine",
            [](QuantoForwardVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               Real correlation) {
                opt.setPricingEngine(ext::make_shared<QuantoForwardEngine>(
                    process,
                    foreign_risk_free_rate,
                    exchange_rate_volatility,
                    Handle<Quote>(
                        ext::make_shared<SimpleQuote>(correlation))));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach quanto-forward engine from a scalar correlation.")
        .def(
            "set_performance_pricing_engine",
            [](QuantoForwardVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               const Handle<Quote>& correlation) {
                opt.setPricingEngine(
                    ext::make_shared<QuantoForwardPerformanceEngine>(
                        process,
                        foreign_risk_free_rate,
                        exchange_rate_volatility,
                        correlation));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach QuantoEngine over ForwardPerformanceVanillaEngine"
            "<AnalyticEuropeanEngine>.")
        .def(
            "set_performance_pricing_engine",
            [](QuantoForwardVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<QuantoForwardPerformanceEngine>(
                        process,
                        foreign_risk_free_rate,
                        exchange_rate_volatility,
                        Handle<Quote>(
                            ext::make_shared<SimpleQuote>(correlation))));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach quanto-forward-performance engine from a scalar "
            "correlation.");

    m.def(
        "QuantoForwardEuropeanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias documentation token — prefer "
        "QuantoForwardVanillaOption.set_pricing_engine(...).");

    m.def(
        "QuantoForwardPerformanceEuropeanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias documentation token — prefer "
        "QuantoForwardVanillaOption.set_performance_pricing_engine(...).");

    // --- Phase 94: EquityIndex + EquityTotalReturnSwap ----------------------
    // Index is Observable+Observer (MI) — standalone wrapper, same pattern as
    // IborIndex. Currency is registered in this function, so the factory lives
    // here rather than in bind_curves.
    nb::class_<EquityIndex>(m, "EquityIndex")
        .def(nb::init<std::string,
                      Calendar,
                      Currency,
                      Handle<YieldTermStructure>,
                      Handle<YieldTermStructure>,
                      Handle<Quote>>(),
             nb::arg("name"),
             nb::arg("fixing_calendar"),
             nb::arg("currency"),
             nb::arg("interest") = Handle<YieldTermStructure>(),
             nb::arg("dividend") = Handle<YieldTermStructure>(),
             nb::arg("spot") = Handle<Quote>())
        .def("name", [](const EquityIndex& i) { return i.name(); })
        .def("fixing_calendar",
             [](const EquityIndex& i) { return i.fixingCalendar(); })
        .def(
            "add_fixing",
            [](EquityIndex& i, const Date& fixing_date, Real fixing, bool force) {
                i.addFixing(fixing_date, fixing, force);
            },
            nb::arg("fixing_date"),
            nb::arg("fixing"),
            nb::arg("force_overwrite") = false)
        .def(
            "fixing",
            [](const EquityIndex& i, const Date& fixing_date, bool forecast_today) {
                return i.fixing(fixing_date, forecast_today);
            },
            nb::arg("fixing_date"),
            nb::arg("forecast_todays_fixing") = false);

    // EquityTotalReturnSwap is Swap/Instrument (MI via LazyObject) —
    // standalone wrapper. Overloads dispatch on arg 5: IborIndex vs
    // OvernightIndex. Engine is DiscountingSwapEngine.
    nb::class_<EquityTotalReturnSwap>(m, "EquityTotalReturnSwap")
        .def(
            "__init__",
            [](EquityTotalReturnSwap* self,
               Swap::Type type,
               Real nominal,
               Schedule schedule,
               const ext::shared_ptr<EquityIndex>& equity_index,
               const ext::shared_ptr<IborIndex>& interest_rate_index,
               const DayCounter& day_counter,
               Rate margin,
               Real gearing,
               const Calendar& payment_calendar,
               BusinessDayConvention payment_convention,
               Natural payment_delay) {
                new (self) EquityTotalReturnSwap(type,
                                                 nominal,
                                                 std::move(schedule),
                                                 equity_index,
                                                 interest_rate_index,
                                                 day_counter,
                                                 margin,
                                                 gearing,
                                                 payment_calendar,
                                                 payment_convention,
                                                 payment_delay);
            },
            nb::arg("type"),
            nb::arg("nominal"),
            nb::arg("schedule"),
            nb::arg("equity_index"),
            nb::arg("interest_rate_index"),
            nb::arg("day_counter"),
            nb::arg("margin"),
            nb::arg("gearing") = 1.0,
            nb::arg("payment_calendar") = Calendar(),
            nb::arg("payment_convention") = Unadjusted,
            nb::arg("payment_delay") = 0)
        .def(
            "__init__",
            [](EquityTotalReturnSwap* self,
               Swap::Type type,
               Real nominal,
               Schedule schedule,
               const ext::shared_ptr<EquityIndex>& equity_index,
               const ext::shared_ptr<OvernightIndex>& interest_rate_index,
               const DayCounter& day_counter,
               Rate margin,
               Real gearing,
               const Calendar& payment_calendar,
               BusinessDayConvention payment_convention,
               Natural payment_delay) {
                new (self) EquityTotalReturnSwap(type,
                                                 nominal,
                                                 std::move(schedule),
                                                 equity_index,
                                                 interest_rate_index,
                                                 day_counter,
                                                 margin,
                                                 gearing,
                                                 payment_calendar,
                                                 payment_convention,
                                                 payment_delay);
            },
            nb::arg("type"),
            nb::arg("nominal"),
            nb::arg("schedule"),
            nb::arg("equity_index"),
            nb::arg("interest_rate_index"),
            nb::arg("day_counter"),
            nb::arg("margin"),
            nb::arg("gearing") = 1.0,
            nb::arg("payment_calendar") = Calendar(),
            nb::arg("payment_convention") = Unadjusted,
            nb::arg("payment_delay") = 0)
        .def("NPV", [](EquityTotalReturnSwap& s) { return s.NPV(); })
        .def("is_expired",
             [](const EquityTotalReturnSwap& s) { return s.isExpired(); })
        .def("type", [](const EquityTotalReturnSwap& s) { return s.type(); })
        .def("nominal",
             [](const EquityTotalReturnSwap& s) { return s.nominal(); })
        .def("margin", [](const EquityTotalReturnSwap& s) { return s.margin(); })
        .def("gearing",
             [](const EquityTotalReturnSwap& s) { return s.gearing(); })
        .def("payment_delay",
             [](const EquityTotalReturnSwap& s) { return s.paymentDelay(); })
        .def("fair_margin",
             [](EquityTotalReturnSwap& s) { return s.fairMargin(); })
        .def("equity_leg_NPV",
             [](EquityTotalReturnSwap& s) { return s.equityLegNPV(); })
        .def("interest_rate_leg_NPV",
             [](EquityTotalReturnSwap& s) { return s.interestRateLegNPV(); })
        .def(
            "set_pricing_engine",
            [](EquityTotalReturnSwap& s,
               const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
            },
            nb::arg("discount_curve"),
            "Attach DiscountingSwapEngine.");
}
