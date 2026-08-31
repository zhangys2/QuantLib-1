#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/cashflows/couponpricer.hpp>
#include <ql/cashflows/dividend.hpp>
#include <ql/exercise.hpp>
#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/methods/finitedifferences/utilities/fdmquantohelper.hpp>
#include <ql/cashflows/duration.hpp>
#include <ql/cashflows/rateaveraging.hpp>
#include <ql/instruments/assetswap.hpp>
#include <ql/instruments/bmaswap.hpp>
#include <ql/instruments/bond.hpp>
#include <ql/instruments/floatfloatswap.hpp>
#include <ql/instruments/makemultipleresetsswap.hpp>
#include <ql/instruments/multipleresetsswap.hpp>
#include <ql/instruments/overnightindexfuture.hpp>
#include <ql/instruments/perpetualfutures.hpp>
#include <ql/instruments/zerocouponswap.hpp>
#include <ql/indexes/bmaindex.hpp>
#include <ql/indexes/swapindex.hpp>
#include <ql/termstructures/yield/overnightindexfutureratehelper.hpp>
#include <ql/termstructures/yield/ratehelpers.hpp>
#include <ql/pricingengines/futures/discountingperpetualfuturesengine.hpp>
#include <ql/instruments/bonds/amortizingfixedratebond.hpp>
#include <ql/instruments/bonds/amortizingfloatingratebond.hpp>
#include <ql/instruments/bonds/cmsratebond.hpp>
#include <ql/instruments/bonds/fixedratebond.hpp>
#include <ql/instruments/bonds/floatingratebond.hpp>
#include <ql/instruments/bonds/zerocouponbond.hpp>
#include <ql/instruments/compositeinstrument.hpp>
#include <ql/currencies/america.hpp>
#include <ql/currencies/europe.hpp>
#include <ql/cashflows/fixedratecoupon.hpp>
#include <ql/cashflows/iborcoupon.hpp>
#include <ql/cashflows/simplecashflow.hpp>
#include <ql/indexes/ibor/gbplibor.hpp>
#include <ql/indexes/ibor/usdlibor.hpp>
#include <ql/instruments/constnotionalcrosscurrencyswap.hpp>
#include <ql/instruments/constnotionalcrosscurrencybasisswap.hpp>
#include <ql/instruments/constnotionalcrosscurrencyfixedvsfloatingswap.hpp>
#include <ql/instruments/stock.hpp>
#include <ql/pricingengines/bond/bondfunctions.hpp>
#include <ql/instruments/dividendschedule.hpp>
#include <ql/instruments/europeanoption.hpp>
#include <ql/instruments/payoffs.hpp>
#include <ql/instruments/nonstandardswap.hpp>
#include <ql/instruments/swap.hpp>
#include <ql/instruments/vanillaswap.hpp>
#include <ql/instruments/vanillaswingoption.hpp>
#include <ql/instruments/vanillastorageoption.hpp>
#include <ql/option.hpp>
#include <ql/experimental/finitedifferences/fdsimpleextoustorageengine.hpp>
#include <ql/experimental/processes/extendedornsteinuhlenbeckprocess.hpp>
#include <ql/experimental/variancegamma/analyticvariancegammaengine.hpp>
#include <ql/experimental/variancegamma/variancegammaprocess.hpp>
#include <ql/pricingengines/bond/discountingbondengine.hpp>
#include <ql/pricingengines/swap/discountingconstnotionalcrosscurrencyswapengine.hpp>
#include <ql/pricingengines/swap/discountingswapengine.hpp>
#include <ql/pricingengines/vanilla/fdsimplebsswingengine.hpp>
#include <ql/models/equity/batesmodel.hpp>
#include <ql/models/equity/hestonmodel.hpp>
#include <ql/pricingengines/vanilla/analyticdividendeuropeanengine.hpp>
#include <ql/pricingengines/vanilla/analyticeuropeanengine.hpp>
#include <ql/pricingengines/vanilla/analytichestonengine.hpp>
#include <ql/pricingengines/vanilla/batesengine.hpp>
#include <ql/pricingengines/vanilla/cashdividendeuropeanengine.hpp>
#include <ql/pricingengines/vanilla/coshestonengine.hpp>
#include <ql/pricingengines/vanilla/exponentialfittinghestonengine.hpp>
#include <ql/pricingengines/vanilla/fdblackscholesvanillaengine.hpp>
#include <ql/pricingengines/vanilla/fdbatesvanillaengine.hpp>
#include <ql/pricingengines/vanilla/fdhestonvanillaengine.hpp>
#include <ql/pricingengines/vanilla/mceuropeanengine.hpp>
#include <ql/pricingengines/vanilla/mceuropeanhestonengine.hpp>
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/processes/hestonprocess.hpp>
#include <ql/settings.hpp>
#include <ql/termstructures/volatility/equityfx/blackconstantvol.hpp>
#include <ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/calendars/jointcalendar.hpp>
#include <ql/time/calendars/switzerland.hpp>
#include <ql/time/calendars/target.hpp>
#include <ql/time/calendars/turkey.hpp>
#include <ql/time/calendars/unitedkingdom.hpp>
#include <ql/time/calendars/unitedstates.hpp>
#include <ql/time/daycounter.hpp>
#include <ql/time/daycounters/actualactual.hpp>
#include <ql/time/schedule.hpp>
#include <ql/utilities/null.hpp>

#include <nanobind/stl/optional.h>

#include <optional>

using namespace QuantLib;

namespace {

Handle<BlackVolTermStructure> make_black_constant_vol_handle(
    const Date& reference_date,
    const Calendar& calendar,
    Volatility volatility,
    const DayCounter& day_counter) {
    return Handle<BlackVolTermStructure>(ext::make_shared<BlackConstantVol>(
        reference_date, calendar, volatility, day_counter));
}

template <class InstrumentT>
void composite_add(CompositeInstrument& composite,
                   const ext::shared_ptr<InstrumentT>& instrument,
                   Real multiplier) {
    composite.add(instrument, multiplier);
}

template <class InstrumentT>
void composite_subtract(CompositeInstrument& composite,
                        const ext::shared_ptr<InstrumentT>& instrument,
                        Real multiplier) {
    composite.subtract(instrument, multiplier);
}

template <class BondT>
void add_bond_analytics(nb::class_<BondT>& cls) {
    cls.def(
           "bond_yield",
           [](const BondT& b,
              Real price,
              const DayCounter& dc,
              Compounding compounding,
              Frequency frequency,
              const Date& settlement_date,
              Real accuracy,
              Size max_evaluations,
              Real guess,
              Bond::Price::Type price_type) {
               return b.yield(Bond::Price(price, price_type),
                              dc,
                              compounding,
                              frequency,
                              settlement_date,
                              accuracy,
                              max_evaluations,
                              guess);
           },
           nb::arg("price"),
           nb::arg("day_counter"),
           nb::arg("compounding"),
           nb::arg("frequency"),
           nb::arg("settlement_date") = Date(),
           nb::arg("accuracy") = 1.0e-8,
           nb::arg("max_evaluations") = 100,
           nb::arg("guess") = 0.05,
           nb::arg("price_type") = Bond::Price::Clean,
           "Yield given a quoted price (default Clean). Named bond_yield "
           "because yield is a Python keyword.")
        .def(
            "clean_price",
            [](const BondT& b,
               Rate yield_rate,
               const DayCounter& dc,
               Compounding compounding,
               Frequency frequency,
               const Date& settlement_date) {
                return b.cleanPrice(
                    yield_rate, dc, compounding, frequency, settlement_date);
            },
            nb::arg("yield_rate"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            "Clean price from a yield (Bond::cleanPrice).")
        .def(
            "duration",
            [](const BondT& b,
               Rate yield_rate,
               const DayCounter& dc,
               Compounding compounding,
               Frequency frequency,
               Duration::Type type,
               const Date& settlement_date) {
                return BondFunctions::duration(b,
                                               yield_rate,
                                               dc,
                                               compounding,
                                               frequency,
                                               type,
                                               settlement_date);
            },
            nb::arg("yield_rate"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("type") = Duration::Modified,
            nb::arg("settlement_date") = Date(),
            "Macaulay / modified / simple duration (BondFunctions).")
        .def(
            "convexity",
            [](const BondT& b,
               Rate yield_rate,
               const DayCounter& dc,
               Compounding compounding,
               Frequency frequency,
               const Date& settlement_date) {
                return BondFunctions::convexity(b,
                                                yield_rate,
                                                dc,
                                                compounding,
                                                frequency,
                                                settlement_date);
            },
            nb::arg("yield_rate"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            "Convexity (BondFunctions; not divided by 100).")
        .def(
            "z_spread",
            [](const BondT& b,
               Real price,
               const Handle<YieldTermStructure>& discount_curve,
               Compounding compounding,
               Frequency frequency,
               const Date& settlement_date,
               Real accuracy,
               Size max_evaluations,
               Rate guess,
               Bond::Price::Type price_type) {
                return BondFunctions::zSpread(b,
                                              Bond::Price(price, price_type),
                                              discount_curve.currentLink(),
                                              compounding,
                                              frequency,
                                              settlement_date,
                                              accuracy,
                                              max_evaluations,
                                              guess);
            },
            nb::arg("price"),
            nb::arg("discount_curve"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            nb::arg("accuracy") = 1.0e-10,
            nb::arg("max_evaluations") = 100,
            nb::arg("guess") = 0.0,
            nb::arg("price_type") = Bond::Price::Clean,
            "Z-spread matching a quoted price vs a discount curve.")
        .def(
            "clean_price_from_z_spread",
            [](const BondT& b,
               const Handle<YieldTermStructure>& discount_curve,
               Spread z_spread,
               Compounding compounding,
               Frequency frequency,
               const Date& settlement_date) {
                return BondFunctions::cleanPrice(b,
                                                 discount_curve.currentLink(),
                                                 z_spread,
                                                 compounding,
                                                 frequency,
                                                 settlement_date);
            },
            nb::arg("discount_curve"),
            nb::arg("z_spread"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            "Clean price from a z-spread over a discount curve.")
        .def(
            "accrued_amount",
            [](const BondT& b, const Date& d) { return b.accruedAmount(d); },
            nb::arg("date") = Date(),
            "Accrued amount at a date (default: bond settlement).");
}

} // namespace

namespace {

void init_const_notional_cross_currency_basis_swap(
    ConstNotionalCrossCurrencyBasisSwap* self,
    Real pay_nominal,
    const Currency& pay_currency,
    const Schedule& pay_schedule,
    const ext::shared_ptr<IborIndex>& pay_index,
    Spread pay_spread,
    Real pay_gearing,
    Real rec_nominal,
    const Currency& rec_currency,
    const Schedule& rec_schedule,
    const ext::shared_ptr<IborIndex>& rec_index,
    Spread rec_spread,
    Real rec_gearing,
    Integer pay_payment_lag,
    Integer rec_payment_lag,
    bool pay_compound_spread,
    std::optional<Natural> pay_lookback_days,
    bool pay_observation_shift,
    Natural pay_lockout_days,
    RateAveraging::Type pay_averaging_method,
    bool rec_compound_spread,
    std::optional<Natural> rec_lookback_days,
    bool rec_observation_shift,
    Natural rec_lockout_days,
    RateAveraging::Type rec_averaging_method,
    bool telescopic_value_dates) {
    const Natural payLookback =
        pay_lookback_days ? *pay_lookback_days : Null<Natural>();
    const Natural recLookback =
        rec_lookback_days ? *rec_lookback_days : Null<Natural>();
    new (self) ConstNotionalCrossCurrencyBasisSwap(
        pay_nominal,
        pay_currency,
        pay_schedule,
        pay_index,
        pay_spread,
        pay_gearing,
        rec_nominal,
        rec_currency,
        rec_schedule,
        rec_index,
        rec_spread,
        rec_gearing,
        pay_payment_lag,
        rec_payment_lag,
        pay_compound_spread,
        payLookback,
        pay_observation_shift,
        pay_lockout_days,
        pay_averaging_method,
        rec_compound_spread,
        recLookback,
        rec_observation_shift,
        rec_lockout_days,
        rec_averaging_method,
        telescopic_value_dates);
}

} // namespace

void bind_instruments(nb::module_& m) {
    nb::class_<Handle<BlackVolTermStructure>>(m, "BlackVolTermStructureHandle")
        .def(nb::init<>())
        .def("empty", &Handle<BlackVolTermStructure>::empty);

    // Phase 53: quanto adjustment helper for FD engines (Observable — no base).
    nb::class_<FdmQuantoHelper>(m, "FdmQuantoHelper")
        .def(
            "__init__",
            [](FdmQuantoHelper* self,
               const Handle<YieldTermStructure>& domestic_rate,
               const Handle<YieldTermStructure>& foreign_rate,
               const Handle<BlackVolTermStructure>& fx_volatility,
               Real equity_fx_correlation,
               Real exch_rate_atm_level) {
                new (self) FdmQuantoHelper(domestic_rate.currentLink(),
                                           foreign_rate.currentLink(),
                                           fx_volatility.currentLink(),
                                           equity_fx_correlation,
                                           exch_rate_atm_level);
            },
            nb::arg("domestic_rate"),
            nb::arg("foreign_rate"),
            nb::arg("fx_volatility"),
            nb::arg("equity_fx_correlation"),
            nb::arg("exch_rate_atm_level") = 1.0)
        .def(
            "quanto_adjustment",
            [](const FdmQuantoHelper& h,
               Volatility equity_vol,
               Time t1,
               Time t2) {
                return h.quantoAdjustment(equity_vol, t1, t2);
            },
            nb::arg("equity_vol"),
            nb::arg("t1"),
            nb::arg("t2"),
            "Quanto drift adjustment over [t1, t2] for a given equity vol.");

    // Phase 51: cash-dividend model for FdBlackScholesVanillaEngine.
    nb::enum_<FdBlackScholesVanillaEngine::CashDividendModel>(
        m, "CashDividendModel")
        .value("Spot", FdBlackScholesVanillaEngine::Spot)
        .value("Escrowed", FdBlackScholesVanillaEngine::Escrowed);

    m.def("BlackConstantVol",
          &make_black_constant_vol_handle,
          nb::arg("reference_date"),
          nb::arg("calendar"),
          nb::arg("volatility"),
          nb::arg("day_counter"));

    nb::class_<BlackScholesMertonProcess>(m, "BlackScholesMertonProcess")
        .def(nb::init<const Handle<Quote>&,
                      const Handle<YieldTermStructure>&,
                      const Handle<YieldTermStructure>&,
                      const Handle<BlackVolTermStructure>&>(),
             nb::arg("x0"),
             nb::arg("dividend_ts"),
             nb::arg("risk_free_ts"),
             nb::arg("black_vol_ts"));

    // --- Phase 118: VarianceGammaProcess ---
    nb::class_<VarianceGammaProcess>(m, "VarianceGammaProcess")
        .def(nb::init<Handle<Quote>,
                      Handle<YieldTermStructure>,
                      Handle<YieldTermStructure>,
                      Real,
                      Real,
                      Real>(),
             nb::arg("s0"),
             nb::arg("dividend_yield"),
             nb::arg("risk_free_rate"),
             nb::arg("sigma"),
             nb::arg("nu"),
             nb::arg("theta"))
        .def("sigma", [](const VarianceGammaProcess& p) { return p.sigma(); })
        .def("nu", [](const VarianceGammaProcess& p) { return p.nu(); })
        .def("theta", [](const VarianceGammaProcess& p) { return p.theta(); })
        .def("x0", [](const VarianceGammaProcess& p) { return p.x0(); });

    nb::enum_<Option::Type>(m, "OptionType")
        .value("Put", Option::Put)
        .value("Call", Option::Call);

    nb::class_<PlainVanillaPayoff>(m, "PlainVanillaPayoff")
        .def(nb::init<Option::Type, Real>(), nb::arg("type"), nb::arg("strike"))
        .def("strike", [](const PlainVanillaPayoff& p) { return p.strike(); })
        .def("option_type",
             [](const PlainVanillaPayoff& p) { return p.optionType(); });

    // Standalone binary payoffs (no Payoff / StrikedTypePayoff MI hierarchy).
    nb::class_<CashOrNothingPayoff>(m, "CashOrNothingPayoff")
        .def(nb::init<Option::Type, Real, Real>(),
             nb::arg("type"),
             nb::arg("strike"),
             nb::arg("cash_payoff"))
        .def("strike", [](const CashOrNothingPayoff& p) { return p.strike(); })
        .def("option_type",
             [](const CashOrNothingPayoff& p) { return p.optionType(); })
        .def("cash_payoff",
             [](const CashOrNothingPayoff& p) { return p.cashPayoff(); });

    nb::class_<AssetOrNothingPayoff>(m, "AssetOrNothingPayoff")
        .def(nb::init<Option::Type, Real>(),
             nb::arg("type"),
             nb::arg("strike"))
        .def("strike", [](const AssetOrNothingPayoff& p) { return p.strike(); })
        .def("option_type",
             [](const AssetOrNothingPayoff& p) { return p.optionType(); });

    // --- Phase 105: Gap / SuperFund / SuperShare payoffs ---
    nb::class_<GapPayoff>(m, "GapPayoff")
        .def(nb::init<Option::Type, Real, Real>(),
             nb::arg("type"),
             nb::arg("strike"),
             nb::arg("second_strike"))
        .def("strike", [](const GapPayoff& p) { return p.strike(); })
        .def("option_type", [](const GapPayoff& p) { return p.optionType(); })
        .def("second_strike", [](const GapPayoff& p) { return p.secondStrike(); });

    nb::class_<SuperFundPayoff>(m, "SuperFundPayoff")
        .def(nb::init<Real, Real>(),
             nb::arg("strike"),
             nb::arg("second_strike"))
        .def("strike", [](const SuperFundPayoff& p) { return p.strike(); })
        .def("option_type",
             [](const SuperFundPayoff& p) { return p.optionType(); })
        .def("second_strike",
             [](const SuperFundPayoff& p) { return p.secondStrike(); });

    nb::class_<SuperSharePayoff>(m, "SuperSharePayoff")
        .def(nb::init<Real, Real, Real>(),
             nb::arg("strike"),
             nb::arg("second_strike"),
             nb::arg("cash_payoff"))
        .def("strike", [](const SuperSharePayoff& p) { return p.strike(); })
        .def("option_type",
             [](const SuperSharePayoff& p) { return p.optionType(); })
        .def("second_strike",
             [](const SuperSharePayoff& p) { return p.secondStrike(); })
        .def("cash_payoff",
             [](const SuperSharePayoff& p) { return p.cashPayoff(); });

    // Floating-strike payoff for lookbacks (no TypePayoff MI hierarchy).
    nb::class_<FloatingTypePayoff>(m, "FloatingTypePayoff")
        .def(nb::init<Option::Type>(), nb::arg("type"))
        .def("option_type",
             [](const FloatingTypePayoff& p) { return p.optionType(); });

    // Percentage-of-spot strike (moneyness) for cliquets / forward-starting.
    nb::class_<PercentageStrikePayoff>(m, "PercentageStrikePayoff")
        .def(nb::init<Option::Type, Real>(),
             nb::arg("type"),
             nb::arg("moneyness"))
        .def("strike",
             [](const PercentageStrikePayoff& p) { return p.strike(); },
             "Moneyness stored as the payoff strike.")
        .def("moneyness",
             [](const PercentageStrikePayoff& p) { return p.strike(); })
        .def("option_type",
             [](const PercentageStrikePayoff& p) { return p.optionType(); });

    nb::class_<EuropeanExercise>(m, "EuropeanExercise")
        .def(nb::init<const Date&>(), nb::arg("date"))
        .def("last_date",
             [](const EuropeanExercise& e) { return e.lastDate(); });

    // FixedDividend inherits Dividend/CashFlow (MI) — concrete wrapper, no bases.
    nb::class_<FixedDividend>(m, "FixedDividend")
        .def(
            "__init__",
            [](FixedDividend* self, Real amount, const Date& date) {
                new (self) FixedDividend(amount, date);
            },
            nb::arg("amount"),
            nb::arg("date"))
        .def("amount", [](const FixedDividend& d) { return d.amount(); })
        .def("date", [](const FixedDividend& d) { return d.date(); });

    m.def(
        "DividendVector",
        [](const std::vector<Date>& dividend_dates,
           const std::vector<Real>& dividends) {
            auto schedule = DividendVector(dividend_dates, dividends);
            std::vector<ext::shared_ptr<FixedDividend>> out;
            out.reserve(schedule.size());
            for (const auto& d : schedule) {
                out.push_back(ext::dynamic_pointer_cast<FixedDividend>(d));
            }
            return out;
        },
        nb::arg("dividend_dates"),
        nb::arg("dividends"),
        "Build fixed cash dividends (DividendSchedule helper).");

    nb::class_<EuropeanOption>(m, "EuropeanOption")
        .def(
            "__init__",
            [](EuropeanOption* self,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) EuropeanOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](EuropeanOption* self,
               const GapPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) EuropeanOption(
                    ext::make_shared<GapPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](EuropeanOption* self,
               const SuperFundPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) EuropeanOption(
                    ext::make_shared<SuperFundPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](EuropeanOption* self,
               const SuperSharePayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) EuropeanOption(
                    ext::make_shared<SuperSharePayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV", [](EuropeanOption& opt) { return opt.NPV(); })
        .def("error_estimate",
             [](EuropeanOption& opt) { return opt.errorEstimate(); })
        .def("delta", [](EuropeanOption& opt) { return opt.delta(); })
        .def("gamma", [](EuropeanOption& opt) { return opt.gamma(); })
        .def("vega", [](EuropeanOption& opt) { return opt.vega(); })
        .def(
            "implied_volatility",
            [](EuropeanOption& opt,
               Real target_price,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Real accuracy,
               Size max_evaluations,
               Volatility min_vol,
               Volatility max_vol) {
                return opt.impliedVolatility(target_price,
                                             process,
                                             accuracy,
                                             max_evaluations,
                                             min_vol,
                                             max_vol);
            },
            nb::arg("target_price"),
            nb::arg("process"),
            nb::arg("accuracy") = 1.0e-4,
            nb::arg("max_evaluations") = 100,
            nb::arg("min_vol") = 1.0e-7,
            nb::arg("max_vol") = 4.0)
        .def(
            "set_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticEuropeanEngine>(process));
            },
            nb::arg("process"))
        .def(
            "set_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticDividendEuropeanEngine>(
                        process,
                        DividendVector(dividend_dates, dividend_amounts)));
            },
            nb::arg("process"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            "Attach AnalyticDividendEuropeanEngine (discrete cash dividends).")
        .def(
            "set_cash_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               FdBlackScholesVanillaEngine::CashDividendModel
                   cash_dividend_model) {
                opt.setPricingEngine(
                    ext::make_shared<CashDividendEuropeanEngine>(
                        process,
                        DividendVector(dividend_dates, dividend_amounts),
                        static_cast<CashDividendEuropeanEngine::CashDividendModel>(
                            cash_dividend_model)));
            },
            nb::arg("process"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("cash_dividend_model") =
                FdBlackScholesVanillaEngine::Spot,
            "Attach CashDividendEuropeanEngine (Spot / Escrowed).")
        .def(
            "set_fd_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               Size t_grid,
               Size x_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc,
               FdBlackScholesVanillaEngine::CashDividendModel
                   cash_dividend_model) {
                opt.setPricingEngine(
                    ext::make_shared<FdBlackScholesVanillaEngine>(
                        process,
                        DividendVector(dividend_dates, dividend_amounts),
                        t_grid,
                        x_grid,
                        damping_steps,
                        scheme_desc,
                        false,
                        -Null<Real>(),
                        cash_dividend_model));
            },
            nb::arg("process"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            nb::arg("cash_dividend_model") =
                FdBlackScholesVanillaEngine::Spot,
            "Attach FdBlackScholesVanillaEngine with discrete cash dividends.")
        .def(
            "set_fd_quanto_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const ext::shared_ptr<FdmQuantoHelper>& quanto_helper,
               Size t_grid,
               Size x_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdBlackScholesVanillaEngine>(
                        process, quanto_helper, t_grid, x_grid, damping_steps,
                        scheme_desc));
            },
            nb::arg("process"),
            nb::arg("quanto_helper"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdBlackScholesVanillaEngine with FdmQuantoHelper.")
        .def(
            "set_fd_quanto_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               const ext::shared_ptr<FdmQuantoHelper>& quanto_helper,
               Size t_grid,
               Size x_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdBlackScholesVanillaEngine>(
                        process,
                        DividendVector(dividend_dates, dividend_amounts),
                        quanto_helper,
                        t_grid,
                        x_grid,
                        damping_steps,
                        scheme_desc));
            },
            nb::arg("process"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("quanto_helper"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdBlackScholesVanillaEngine with dividends + quanto "
            "(Spot cash-dividend model only).")
        .def(
            "set_mc_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               Size required_samples,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                ext::shared_ptr<PricingEngine> engine =
                    MakeMCEuropeanEngine<PseudoRandom>(process)
                        .withSteps(time_steps)
                        .withSamples(required_samples)
                        .withSeed(seed)
                        .withAntitheticVariate(antithetic)
                        .withBrownianBridge(brownian_bridge);
                opt.setPricingEngine(engine);
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("required_samples"),
            nb::arg("seed") = 42UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false)
        .def(
            "set_mc_heston_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               Size required_samples,
               unsigned long seed,
               bool antithetic) {
                QL_REQUIRE(!(time_steps.has_value() && steps_per_year.has_value()),
                           "set only one of time_steps or steps_per_year");
                auto maker = MakeMCEuropeanHestonEngine<PseudoRandom>(process)
                                 .withSamples(required_samples)
                                 .withSeed(seed)
                                 .withAntitheticVariate(antithetic);
                if (time_steps.has_value())
                    maker.withSteps(*time_steps);
                else
                    maker.withStepsPerYear(steps_per_year.value_or(Size(11)));
                opt.setPricingEngine(maker);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = Size(50000),
            nb::arg("seed") = 1234UL,
            nb::arg("antithetic") = true,
            "Attach MakeMCEuropeanHestonEngine<PseudoRandom> "
            "(default steps_per_year=11).")
        .def(
            "set_heston_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               Size integration_order) {
                opt.setPricingEngine(ext::make_shared<AnalyticHestonEngine>(
                    model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach AnalyticHestonEngine (Laguerre / Gatheral).")
        .def(
            "set_cos_heston_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               Real L,
               Size N) {
                opt.setPricingEngine(
                    ext::make_shared<COSHestonEngine>(model, L, N));
            },
            nb::arg("model"),
            nb::arg("L") = 16.0,
            nb::arg("N") = Size(200),
            "Attach COSHestonEngine (Fourier-Cosine series).")
        .def(
            "set_exponential_fitting_heston_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               AnalyticHestonEngine::ComplexLogFormula control_variate,
               std::optional<Real> scaling,
               Real alpha) {
                opt.setPricingEngine(
                    ext::make_shared<ExponentialFittingHestonEngine>(
                        model,
                        control_variate,
                        scaling.value_or(Null<Real>()),
                        alpha));
            },
            nb::arg("model"),
            nb::arg("control_variate") =
                AnalyticHestonEngine::ComplexLogFormula::OptimalCV,
            nb::arg("scaling") = nb::none(),
            nb::arg("alpha") = -0.5,
            "Attach ExponentialFittingHestonEngine.")
        .def(
            "set_fd_heston_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdHestonVanillaEngine>(
                    model, t_grid, x_grid, v_grid, damping_steps, scheme_desc));
            },
            nb::arg("model"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdHestonVanillaEngine (default Hundsdorfer scheme).")
        .def(
            "set_fd_heston_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdHestonVanillaEngine>(
                    model,
                    DividendVector(dividend_dates, dividend_amounts),
                    t_grid,
                    x_grid,
                    v_grid,
                    damping_steps,
                    scheme_desc));
            },
            nb::arg("model"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdHestonVanillaEngine with discrete cash dividends.")
        .def(
            "set_fd_heston_quanto_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               const ext::shared_ptr<FdmQuantoHelper>& quanto_helper,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdHestonVanillaEngine>(
                    model, quanto_helper, t_grid, x_grid, v_grid,
                    damping_steps, scheme_desc));
            },
            nb::arg("model"),
            nb::arg("quanto_helper"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdHestonVanillaEngine with FdmQuantoHelper.")
        .def(
            "set_fd_heston_quanto_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               const ext::shared_ptr<FdmQuantoHelper>& quanto_helper,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdHestonVanillaEngine>(
                    model,
                    DividendVector(dividend_dates, dividend_amounts),
                    quanto_helper,
                    t_grid,
                    x_grid,
                    v_grid,
                    damping_steps,
                    scheme_desc));
            },
            nb::arg("model"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("quanto_helper"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdHestonVanillaEngine with dividends + quanto.")
        .def(
            "set_bates_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BatesModel>& model,
               Size integration_order) {
                opt.setPricingEngine(
                    ext::make_shared<BatesEngine>(model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach BatesEngine (Heston + log-normal jumps).")
        .def(
            "set_variance_gamma_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<VarianceGammaProcess>& process,
               Real absolute_error) {
                opt.setPricingEngine(
                    ext::make_shared<VarianceGammaEngine>(process, absolute_error));
            },
            nb::arg("process"),
            nb::arg("absolute_error") = 1e-5,
            "Attach VarianceGammaEngine (analytic integral VG).")
        .def(
            "set_fd_bates_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BatesModel>& model,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdBatesVanillaEngine>(
                    model, t_grid, x_grid, v_grid, damping_steps, scheme_desc));
            },
            nb::arg("model"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdBatesVanillaEngine (default Hundsdorfer / PIDE).")
        .def(
            "set_fd_bates_dividend_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BatesModel>& model,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdBatesVanillaEngine>(
                    model,
                    DividendVector(dividend_dates, dividend_amounts),
                    t_grid,
                    x_grid,
                    v_grid,
                    damping_steps,
                    scheme_desc));
            },
            nb::arg("model"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdBatesVanillaEngine with discrete cash dividends.")
        .def(
            "set_bates_det_jump_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BatesDetJumpModel>& model,
               Size integration_order) {
                opt.setPricingEngine(ext::make_shared<BatesDetJumpEngine>(
                    model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach BatesDetJumpEngine.")
        .def(
            "set_bates_double_exp_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BatesDoubleExpModel>& model,
               Size integration_order) {
                opt.setPricingEngine(ext::make_shared<BatesDoubleExpEngine>(
                    model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach BatesDoubleExpEngine.")
        .def(
            "set_bates_double_exp_det_jump_pricing_engine",
            [](EuropeanOption& opt,
               const ext::shared_ptr<BatesDoubleExpDetJumpModel>& model,
               Size integration_order) {
                opt.setPricingEngine(
                    ext::make_shared<BatesDoubleExpDetJumpEngine>(
                        model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach BatesDoubleExpDetJumpEngine.");

    m.def(
        "AnalyticEuropeanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"));

    m.def(
        "AnalyticDividendEuropeanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process,
           const std::vector<Date>& dividend_dates,
           const std::vector<Real>& dividend_amounts) {
            return process;
        },
        nb::arg("process"),
        nb::arg("dividend_dates"),
        nb::arg("dividend_amounts"),
        "Documentation alias — use EuropeanOption/VanillaOption."
        "set_dividend_pricing_engine instead.");

    m.def(
        "CashDividendEuropeanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process,
           const std::vector<Date>& dividend_dates,
           const std::vector<Real>& dividend_amounts,
           FdBlackScholesVanillaEngine::CashDividendModel cash_dividend_model) {
            return process;
        },
        nb::arg("process"),
        nb::arg("dividend_dates"),
        nb::arg("dividend_amounts"),
        nb::arg("cash_dividend_model") = FdBlackScholesVanillaEngine::Spot,
        "Documentation alias — use EuropeanOption/VanillaOption."
        "set_cash_dividend_pricing_engine instead.");

    m.def(
        "FdBlackScholesVanillaEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "VanillaOption.set_fd_pricing_engine or "
        "set_fd_dividend_pricing_engine.");

    // Bonds (standalone; Bond/Instrument use MI via LazyObject).
    // BondPrice lives here so yield / z-spread can take it before bind_callable.
    nb::enum_<Bond::Price::Type>(m, "BondPriceType")
        .value("Clean", Bond::Price::Clean)
        .value("Dirty", Bond::Price::Dirty);

    nb::class_<Bond::Price>(m, "BondPrice")
        .def(nb::init<Real, Bond::Price::Type>(),
             nb::arg("amount"),
             nb::arg("type") = Bond::Price::Clean)
        .def("amount", &Bond::Price::amount)
        .def("type", &Bond::Price::type)
        .def("is_valid", &Bond::Price::isValid);

    nb::enum_<Duration::Type>(m, "DurationType")
        .value("Simple", Duration::Simple)
        .value("Macaulay", Duration::Macaulay)
        .value("Modified", Duration::Modified);

    nb::class_<FixedRateBond> fixed_rate_bond(m, "FixedRateBond");
    fixed_rate_bond
        .def(
            "__init__",
            [](FixedRateBond* self,
               Natural settlement_days,
               Real face_amount,
               const Schedule& schedule,
               const std::vector<Rate>& coupons,
               const DayCounter& accrual_day_counter,
               BusinessDayConvention payment_convention,
               Real redemption,
               const Date& issue_date) {
                new (self) FixedRateBond(settlement_days,
                                         face_amount,
                                         schedule,
                                         coupons,
                                         accrual_day_counter,
                                         payment_convention,
                                         redemption,
                                         issue_date);
            },
            nb::arg("settlement_days"),
            nb::arg("face_amount"),
            nb::arg("schedule"),
            nb::arg("coupons"),
            nb::arg("accrual_day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("redemption") = 100.0,
            nb::arg("issue_date") = Date())
        .def("NPV", [](FixedRateBond& b) { return b.NPV(); })
        .def("clean_price", [](FixedRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price", [](FixedRateBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const FixedRateBond& b) { return b.settlementDate(); })
        .def("maturity_date",
             [](const FixedRateBond& b) { return b.maturityDate(); })
        .def("settlement_value",
             [](const FixedRateBond& b) { return b.settlementValue(); })
        .def(
            "set_pricing_engine",
            [](FixedRateBond& b, const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<DiscountingBondEngine>(discount_curve));
            },
            nb::arg("discount_curve"));
    add_bond_analytics(fixed_rate_bond);

    // Zero-coupon bond (standalone; Bond/Instrument use MI via LazyObject).
    nb::class_<ZeroCouponBond> zero_coupon_bond(m, "ZeroCouponBond");
    zero_coupon_bond
        .def(
            "__init__",
            [](ZeroCouponBond* self,
               Natural settlement_days,
               const Calendar& calendar,
               Real face_amount,
               const Date& maturity_date,
               BusinessDayConvention payment_convention,
               Real redemption,
               const Date& issue_date) {
                new (self) ZeroCouponBond(settlement_days,
                                          calendar,
                                          face_amount,
                                          maturity_date,
                                          payment_convention,
                                          redemption,
                                          issue_date);
            },
            nb::arg("settlement_days"),
            nb::arg("calendar"),
            nb::arg("face_amount"),
            nb::arg("maturity_date"),
            nb::arg("payment_convention") = Following,
            nb::arg("redemption") = 100.0,
            nb::arg("issue_date") = Date())
        .def("NPV", [](ZeroCouponBond& b) { return b.NPV(); })
        .def("clean_price", [](ZeroCouponBond& b) { return b.cleanPrice(); })
        .def("dirty_price", [](ZeroCouponBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const ZeroCouponBond& b) { return b.settlementDate(); })
        .def("maturity_date",
             [](const ZeroCouponBond& b) { return b.maturityDate(); })
        .def("settlement_value",
             [](const ZeroCouponBond& b) { return b.settlementValue(); })
        .def(
            "set_pricing_engine",
            [](ZeroCouponBond& b, const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<DiscountingBondEngine>(discount_curve));
            },
            nb::arg("discount_curve"));
    add_bond_analytics(zero_coupon_bond);

    // Floating-rate bond (standalone; Bond/Instrument use MI via LazyObject).
    // set_pricing_engine attaches DiscountingBondEngine and a BlackIborCouponPricer.
    nb::class_<FloatingRateBond> floating_rate_bond(m, "FloatingRateBond");
    floating_rate_bond
        .def(
            "__init__",
            [](FloatingRateBond* self,
               Natural settlement_days,
               Real face_amount,
               const Schedule& schedule,
               const ext::shared_ptr<IborIndex>& ibor_index,
               const DayCounter& accrual_day_counter,
               BusinessDayConvention payment_convention,
               Natural fixing_days,
               const std::vector<Real>& gearings,
               const std::vector<Spread>& spreads,
               const std::vector<Rate>& caps,
               const std::vector<Rate>& floors,
               bool in_arrears,
               Real redemption,
               const Date& issue_date) {
                const Natural ql_fixing_days =
                    (fixing_days == 0) ? Null<Natural>() : fixing_days;
                const std::vector<Real> ql_gearings =
                    gearings.empty() ? std::vector<Real>{1.0} : gearings;
                const std::vector<Spread> ql_spreads =
                    spreads.empty() ? std::vector<Spread>{0.0} : spreads;
                new (self) FloatingRateBond(settlement_days,
                                            face_amount,
                                            schedule,
                                            ibor_index,
                                            accrual_day_counter,
                                            payment_convention,
                                            ql_fixing_days,
                                            ql_gearings,
                                            ql_spreads,
                                            caps,
                                            floors,
                                            in_arrears,
                                            redemption,
                                            issue_date);
            },
            nb::arg("settlement_days"),
            nb::arg("face_amount"),
            nb::arg("schedule"),
            nb::arg("ibor_index"),
            nb::arg("accrual_day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("fixing_days") = 0,
            nb::arg("gearings") = std::vector<Real>(),
            nb::arg("spreads") = std::vector<Spread>(),
            nb::arg("caps") = std::vector<Rate>(),
            nb::arg("floors") = std::vector<Rate>(),
            nb::arg("in_arrears") = false,
            nb::arg("redemption") = 100.0,
            nb::arg("issue_date") = Date())
        .def("NPV", [](FloatingRateBond& b) { return b.NPV(); })
        .def("clean_price", [](FloatingRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price", [](FloatingRateBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const FloatingRateBond& b) { return b.settlementDate(); })
        .def("maturity_date",
             [](const FloatingRateBond& b) { return b.maturityDate(); })
        .def("settlement_value",
             [](const FloatingRateBond& b) { return b.settlementValue(); })
        .def(
            "set_pricing_engine",
            [](FloatingRateBond& b,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<DiscountingBondEngine>(discount_curve));
                setCouponPricer(b.cashflows(),
                                ext::make_shared<BlackIborCouponPricer>());
            },
            nb::arg("discount_curve"),
            "Attach DiscountingBondEngine and BlackIborCouponPricer on cashflows.");
    add_bond_analytics(floating_rate_bond);

    // CMS-rate bond (standalone; Bond/Instrument use MI via LazyObject).
    nb::class_<CmsRateBond> cms_rate_bond(m, "CmsRateBond");
    cms_rate_bond
        .def(
            "__init__",
            [](CmsRateBond* self,
               Natural settlement_days,
               Real face_amount,
               const Schedule& schedule,
               const ext::shared_ptr<SwapIndex>& swap_index,
               const DayCounter& payment_day_counter,
               BusinessDayConvention payment_convention,
               Natural fixing_days,
               const std::vector<Real>& gearings,
               const std::vector<Spread>& spreads,
               const std::vector<Rate>& caps,
               const std::vector<Rate>& floors,
               bool in_arrears,
               Real redemption,
               const Date& issue_date) {
                const Natural ql_fixing_days =
                    (fixing_days == 0) ? Null<Natural>() : fixing_days;
                const std::vector<Real> ql_gearings =
                    gearings.empty() ? std::vector<Real>{1.0} : gearings;
                const std::vector<Spread> ql_spreads =
                    spreads.empty() ? std::vector<Spread>{0.0} : spreads;
                new (self) CmsRateBond(settlement_days,
                                       face_amount,
                                       schedule,
                                       swap_index,
                                       payment_day_counter,
                                       payment_convention,
                                       ql_fixing_days,
                                       ql_gearings,
                                       ql_spreads,
                                       caps,
                                       floors,
                                       in_arrears,
                                       redemption,
                                       issue_date);
            },
            nb::arg("settlement_days"),
            nb::arg("face_amount"),
            nb::arg("schedule"),
            nb::arg("swap_index"),
            nb::arg("payment_day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("fixing_days") = 0,
            nb::arg("gearings") = std::vector<Real>{},
            nb::arg("spreads") = std::vector<Spread>{},
            nb::arg("caps") = std::vector<Rate>{},
            nb::arg("floors") = std::vector<Rate>{},
            nb::arg("in_arrears") = false,
            nb::arg("redemption") = 100.0,
            nb::arg("issue_date") = Date())
        .def("NPV", [](CmsRateBond& b) { return b.NPV(); })
        .def("clean_price", [](CmsRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price", [](CmsRateBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const CmsRateBond& b) { return b.settlementDate(); })
        .def("maturity_date",
             [](const CmsRateBond& b) { return b.maturityDate(); })
        .def("settlement_value",
             [](const CmsRateBond& b) { return b.settlementValue(); })
        .def(
            "set_pricing_engine",
            [](CmsRateBond& b, const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<DiscountingBondEngine>(discount_curve));
            },
            nb::arg("discount_curve"))
        .def(
            "set_cms_coupon_pricer",
            [](CmsRateBond& b, const ext::shared_ptr<CmsCouponPricer>& pricer) {
                setCouponPricer(b.cashflows(), pricer);
            },
            nb::arg("pricer"),
            "Attach a CmsCouponPricer to all CMS coupons on the bond.");
    add_bond_analytics(cms_rate_bond);

    // Amortizing fixed-rate bond (standalone; Bond/Instrument use MI via LazyObject).
    nb::class_<AmortizingFixedRateBond> amortizing_fixed_rate_bond(
        m, "AmortizingFixedRateBond");
    amortizing_fixed_rate_bond
        .def(
            "__init__",
            [](AmortizingFixedRateBond* self,
               Natural settlement_days,
               const std::vector<Real>& notionals,
               const Schedule& schedule,
               const std::vector<Rate>& coupons,
               const DayCounter& accrual_day_counter,
               BusinessDayConvention payment_convention,
               const Date& issue_date) {
                new (self) AmortizingFixedRateBond(settlement_days,
                                                   notionals,
                                                   schedule,
                                                   coupons,
                                                   accrual_day_counter,
                                                   payment_convention,
                                                   issue_date);
            },
            nb::arg("settlement_days"),
            nb::arg("notionals"),
            nb::arg("schedule"),
            nb::arg("coupons"),
            nb::arg("accrual_day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("issue_date") = Date())
        .def("NPV", [](AmortizingFixedRateBond& b) { return b.NPV(); })
        .def("clean_price",
             [](AmortizingFixedRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](AmortizingFixedRateBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const AmortizingFixedRateBond& b) {
                 return b.settlementDate();
             })
        .def("maturity_date",
             [](const AmortizingFixedRateBond& b) {
                 return b.maturityDate();
             })
        .def("settlement_value",
             [](const AmortizingFixedRateBond& b) {
                 return b.settlementValue();
             })
        .def("frequency",
             [](const AmortizingFixedRateBond& b) { return b.frequency(); })
        .def("day_counter",
             [](const AmortizingFixedRateBond& b) { return b.dayCounter(); })
        .def(
            "cashflow_amounts",
            [](const AmortizingFixedRateBond& b) {
                std::vector<Real> amounts;
                amounts.reserve(b.cashflows().size());
                for (const auto& cf : b.cashflows())
                    amounts.push_back(cf->amount());
                return amounts;
            },
            "Cash-flow amounts in schedule order (coupon, principal, …).")
        .def(
            "set_pricing_engine",
            [](AmortizingFixedRateBond& b,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<DiscountingBondEngine>(discount_curve));
            },
            nb::arg("discount_curve"));
    add_bond_analytics(amortizing_fixed_rate_bond);

    // Amortizing floating-rate bond (standalone; Bond/Instrument use MI).
    nb::class_<AmortizingFloatingRateBond> amortizing_floating_rate_bond(
        m, "AmortizingFloatingRateBond");
    amortizing_floating_rate_bond
        .def(
            "__init__",
            [](AmortizingFloatingRateBond* self,
               Natural settlement_days,
               const std::vector<Real>& notionals,
               const Schedule& schedule,
               const ext::shared_ptr<IborIndex>& ibor_index,
               const DayCounter& accrual_day_counter,
               BusinessDayConvention payment_convention,
               Natural fixing_days,
               const std::vector<Real>& gearings,
               const std::vector<Spread>& spreads,
               const std::vector<Rate>& caps,
               const std::vector<Rate>& floors,
               bool in_arrears,
               const Date& issue_date) {
                const Natural ql_fixing_days =
                    (fixing_days == 0) ? Null<Natural>() : fixing_days;
                const std::vector<Real> ql_gearings =
                    gearings.empty() ? std::vector<Real>{1.0} : gearings;
                const std::vector<Spread> ql_spreads =
                    spreads.empty() ? std::vector<Spread>{0.0} : spreads;
                new (self) AmortizingFloatingRateBond(settlement_days,
                                                      notionals,
                                                      schedule,
                                                      ibor_index,
                                                      accrual_day_counter,
                                                      payment_convention,
                                                      ql_fixing_days,
                                                      ql_gearings,
                                                      ql_spreads,
                                                      caps,
                                                      floors,
                                                      in_arrears,
                                                      issue_date);
            },
            nb::arg("settlement_days"),
            nb::arg("notionals"),
            nb::arg("schedule"),
            nb::arg("ibor_index"),
            nb::arg("accrual_day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("fixing_days") = 0,
            nb::arg("gearings") = std::vector<Real>{},
            nb::arg("spreads") = std::vector<Spread>{},
            nb::arg("caps") = std::vector<Rate>{},
            nb::arg("floors") = std::vector<Rate>{},
            nb::arg("in_arrears") = false,
            nb::arg("issue_date") = Date())
        .def("NPV", [](AmortizingFloatingRateBond& b) { return b.NPV(); })
        .def("clean_price",
             [](AmortizingFloatingRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](AmortizingFloatingRateBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const AmortizingFloatingRateBond& b) {
                 return b.settlementDate();
             })
        .def("maturity_date",
             [](const AmortizingFloatingRateBond& b) {
                 return b.maturityDate();
             })
        .def("settlement_value",
             [](const AmortizingFloatingRateBond& b) {
                 return b.settlementValue();
             })
        .def(
            "cashflow_amounts",
            [](const AmortizingFloatingRateBond& b) {
                std::vector<Real> amounts;
                amounts.reserve(b.cashflows().size());
                for (const auto& cf : b.cashflows())
                    amounts.push_back(cf->amount());
                return amounts;
            },
            "Cash-flow amounts in schedule order (coupon, principal, …).")
        .def(
            "set_pricing_engine",
            [](AmortizingFloatingRateBond& b,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<DiscountingBondEngine>(discount_curve));
                setCouponPricer(b.cashflows(),
                                ext::make_shared<BlackIborCouponPricer>());
            },
            nb::arg("discount_curve"),
            "Attach DiscountingBondEngine and BlackIborCouponPricer on cashflows.");
    add_bond_analytics(amortizing_floating_rate_bond);

    m.def(
        "sinking_schedule",
        [](const Date& start_date,
           const Period& bond_length,
           Frequency frequency,
           const Calendar& payment_calendar) {
            return sinkingSchedule(
                start_date, bond_length, frequency, payment_calendar);
        },
        nb::arg("start_date"),
        nb::arg("bond_length"),
        nb::arg("frequency"),
        nb::arg("payment_calendar"),
        "French-amortization schedule (sinkingSchedule).");

    m.def(
        "sinking_notionals",
        [](const Period& bond_length,
           Frequency frequency,
           Rate coupon_rate,
           Real initial_notional) {
            return sinkingNotionals(
                bond_length, frequency, coupon_rate, initial_notional);
        },
        nb::arg("bond_length"),
        nb::arg("frequency"),
        nb::arg("coupon_rate"),
        nb::arg("initial_notional"),
        "French-amortization notional schedule (sinkingNotionals).");

    nb::enum_<Swap::Type>(m, "SwapType")
        .value("Receiver", Swap::Receiver)
        .value("Payer", Swap::Payer);

    nb::class_<VanillaSwap>(m, "VanillaSwap")
        .def(
            "__init__",
            [](VanillaSwap* self,
               Swap::Type type,
               Real nominal,
               const Schedule& fixed_schedule,
               Rate fixed_rate,
               const DayCounter& fixed_day_count,
               const Schedule& float_schedule,
               const ext::shared_ptr<IborIndex>& ibor_index,
               Spread spread,
               const DayCounter& floating_day_count) {
                new (self) VanillaSwap(type,
                                       nominal,
                                       fixed_schedule,
                                       fixed_rate,
                                       fixed_day_count,
                                       float_schedule,
                                       ibor_index,
                                       spread,
                                       floating_day_count);
            },
            nb::arg("type"),
            nb::arg("nominal"),
            nb::arg("fixed_schedule"),
            nb::arg("fixed_rate"),
            nb::arg("fixed_day_count"),
            nb::arg("float_schedule"),
            nb::arg("ibor_index"),
            nb::arg("spread"),
            nb::arg("floating_day_count"))
        .def("NPV", [](VanillaSwap& s) { return s.NPV(); })
        .def("fair_rate", [](VanillaSwap& s) { return s.fairRate(); })
        .def("fair_spread", [](VanillaSwap& s) { return s.fairSpread(); })
        .def(
            "set_pricing_engine",
            [](VanillaSwap& s, const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
            },
            nb::arg("discount_curve"));

    // --- Phase 117: NonstandardSwap (period-dependent nominal / strike) ---
    nb::class_<NonstandardSwap>(m, "NonstandardSwap")
        .def(
            "__init__",
            [](NonstandardSwap* self, const VanillaSwap& from_vanilla) {
                new (self) NonstandardSwap(from_vanilla);
            },
            nb::arg("vanilla_swap"),
            "Build from a vanilla FixedVsFloatingSwap (per-period nominals/rates).")
        .def(
            "__init__",
            [](NonstandardSwap* self,
               Swap::Type type,
               const std::vector<Real>& fixed_nominal,
               const std::vector<Real>& floating_nominal,
               const Schedule& fixed_schedule,
               const std::vector<Real>& fixed_rate,
               const DayCounter& fixed_day_count,
               const Schedule& floating_schedule,
               const ext::shared_ptr<IborIndex>& ibor_index,
               Real gearing,
               Spread spread,
               const DayCounter& floating_day_count,
               bool intermediate_capital_exchange,
               bool final_capital_exchange) {
                new (self) NonstandardSwap(type,
                                           fixed_nominal,
                                           floating_nominal,
                                           fixed_schedule,
                                           fixed_rate,
                                           fixed_day_count,
                                           floating_schedule,
                                           ibor_index,
                                           gearing,
                                           spread,
                                           floating_day_count,
                                           intermediate_capital_exchange,
                                           final_capital_exchange);
            },
            nb::arg("type"),
            nb::arg("fixed_nominal"),
            nb::arg("floating_nominal"),
            nb::arg("fixed_schedule"),
            nb::arg("fixed_rate"),
            nb::arg("fixed_day_count"),
            nb::arg("floating_schedule"),
            nb::arg("ibor_index"),
            nb::arg("gearing"),
            nb::arg("spread"),
            nb::arg("floating_day_count"),
            nb::arg("intermediate_capital_exchange") = false,
            nb::arg("final_capital_exchange") = false)
        .def("NPV", [](NonstandardSwap& s) { return s.NPV(); })
        .def("type", [](const NonstandardSwap& s) { return s.type(); })
        .def("fixed_nominal",
             [](const NonstandardSwap& s) { return s.fixedNominal(); })
        .def("floating_nominal",
             [](const NonstandardSwap& s) { return s.floatingNominal(); })
        .def("fixed_rate",
             [](const NonstandardSwap& s) { return s.fixedRate(); })
        .def("spread", [](const NonstandardSwap& s) { return s.spread(); })
        .def("gearing", [](const NonstandardSwap& s) { return s.gearing(); })
        .def("fixed_schedule",
             [](const NonstandardSwap& s) -> const Schedule& { return s.fixedSchedule(); },
             nb::rv_policy::reference_internal)
        .def("floating_schedule",
             [](const NonstandardSwap& s) -> const Schedule& { return s.floatingSchedule(); },
             nb::rv_policy::reference_internal)
        .def("ibor_index",
             [](const NonstandardSwap& s) { return s.iborIndex(); })
        .def("fixed_day_count",
             [](const NonstandardSwap& s) -> const DayCounter& {
                 return s.fixedDayCount();
             },
             nb::rv_policy::reference_internal)
        .def("floating_day_count",
             [](const NonstandardSwap& s) -> const DayCounter& {
                 return s.floatingDayCount();
             },
             nb::rv_policy::reference_internal)
        .def("payment_convention",
             [](const NonstandardSwap& s) { return s.paymentConvention(); })
        .def(
            "set_pricing_engine",
            [](NonstandardSwap& s, const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
            },
            nb::arg("discount_curve"));

    // AssetSwap is Swap/Instrument (MI via LazyObject) — standalone wrapper.
    // Bond argument is copied into a shared_ptr; the original Python bond is
    // unchanged. IborLeg attaches BlackIborCouponPricer internally.
    nb::class_<AssetSwap>(m, "AssetSwap")
        .def(
            "__init__",
            [](AssetSwap* self,
               bool pay_bond_coupon,
               const FixedRateBond& bond,
               Real bond_clean_price,
               const ext::shared_ptr<IborIndex>& ibor_index,
               Spread spread,
               const Schedule& float_schedule,
               const DayCounter& floating_day_count,
               bool par_asset_swap,
               Real gearing,
               std::optional<Real> non_par_repayment,
               const Date& deal_maturity) {
                new (self) AssetSwap(pay_bond_coupon,
                                     ext::make_shared<FixedRateBond>(bond),
                                     bond_clean_price,
                                     ibor_index,
                                     spread,
                                     float_schedule,
                                     floating_day_count,
                                     par_asset_swap,
                                     gearing,
                                     non_par_repayment.value_or(Null<Real>()),
                                     deal_maturity);
            },
            nb::arg("pay_bond_coupon"),
            nb::arg("bond"),
            nb::arg("bond_clean_price"),
            nb::arg("ibor_index"),
            nb::arg("spread"),
            nb::arg("float_schedule") = Schedule(),
            nb::arg("floating_day_count") = DayCounter(),
            nb::arg("par_asset_swap") = true,
            nb::arg("gearing") = 1.0,
            nb::arg("non_par_repayment") = nb::none(),
            nb::arg("deal_maturity") = Date())
        .def(
            "__init__",
            [](AssetSwap* self,
               bool pay_bond_coupon,
               const ZeroCouponBond& bond,
               Real bond_clean_price,
               const ext::shared_ptr<IborIndex>& ibor_index,
               Spread spread,
               const Schedule& float_schedule,
               const DayCounter& floating_day_count,
               bool par_asset_swap,
               Real gearing,
               std::optional<Real> non_par_repayment,
               const Date& deal_maturity) {
                new (self) AssetSwap(pay_bond_coupon,
                                     ext::make_shared<ZeroCouponBond>(bond),
                                     bond_clean_price,
                                     ibor_index,
                                     spread,
                                     float_schedule,
                                     floating_day_count,
                                     par_asset_swap,
                                     gearing,
                                     non_par_repayment.value_or(Null<Real>()),
                                     deal_maturity);
            },
            nb::arg("pay_bond_coupon"),
            nb::arg("bond"),
            nb::arg("bond_clean_price"),
            nb::arg("ibor_index"),
            nb::arg("spread"),
            nb::arg("float_schedule") = Schedule(),
            nb::arg("floating_day_count") = DayCounter(),
            nb::arg("par_asset_swap") = true,
            nb::arg("gearing") = 1.0,
            nb::arg("non_par_repayment") = nb::none(),
            nb::arg("deal_maturity") = Date())
        .def(
            "__init__",
            [](AssetSwap* self,
               bool pay_bond_coupon,
               const FloatingRateBond& bond,
               Real bond_clean_price,
               const ext::shared_ptr<IborIndex>& ibor_index,
               Spread spread,
               const Schedule& float_schedule,
               const DayCounter& floating_day_count,
               bool par_asset_swap,
               Real gearing,
               std::optional<Real> non_par_repayment,
               const Date& deal_maturity) {
                new (self) AssetSwap(pay_bond_coupon,
                                     ext::make_shared<FloatingRateBond>(bond),
                                     bond_clean_price,
                                     ibor_index,
                                     spread,
                                     float_schedule,
                                     floating_day_count,
                                     par_asset_swap,
                                     gearing,
                                     non_par_repayment.value_or(Null<Real>()),
                                     deal_maturity);
            },
            nb::arg("pay_bond_coupon"),
            nb::arg("bond"),
            nb::arg("bond_clean_price"),
            nb::arg("ibor_index"),
            nb::arg("spread"),
            nb::arg("float_schedule") = Schedule(),
            nb::arg("floating_day_count") = DayCounter(),
            nb::arg("par_asset_swap") = true,
            nb::arg("gearing") = 1.0,
            nb::arg("non_par_repayment") = nb::none(),
            nb::arg("deal_maturity") = Date())
        .def(
            "__init__",
            [](AssetSwap* self,
               bool pay_bond_coupon,
               const CmsRateBond& bond,
               Real bond_clean_price,
               const ext::shared_ptr<IborIndex>& ibor_index,
               Spread spread,
               const Schedule& float_schedule,
               const DayCounter& floating_day_count,
               bool par_asset_swap,
               Real gearing,
               std::optional<Real> non_par_repayment,
               const Date& deal_maturity) {
                new (self) AssetSwap(pay_bond_coupon,
                                     ext::make_shared<CmsRateBond>(bond),
                                     bond_clean_price,
                                     ibor_index,
                                     spread,
                                     float_schedule,
                                     floating_day_count,
                                     par_asset_swap,
                                     gearing,
                                     non_par_repayment.value_or(Null<Real>()),
                                     deal_maturity);
            },
            nb::arg("pay_bond_coupon"),
            nb::arg("bond"),
            nb::arg("bond_clean_price"),
            nb::arg("ibor_index"),
            nb::arg("spread"),
            nb::arg("float_schedule") = Schedule(),
            nb::arg("floating_day_count") = DayCounter(),
            nb::arg("par_asset_swap") = true,
            nb::arg("gearing") = 1.0,
            nb::arg("non_par_repayment") = nb::none(),
            nb::arg("deal_maturity") = Date())
        .def("NPV", [](AssetSwap& s) { return s.NPV(); })
        .def("is_expired", [](const AssetSwap& s) { return s.isExpired(); })
        .def("fair_spread", [](AssetSwap& s) { return s.fairSpread(); })
        .def("fair_clean_price", [](AssetSwap& s) { return s.fairCleanPrice(); })
        .def("fair_non_par_repayment",
             [](AssetSwap& s) { return s.fairNonParRepayment(); })
        .def("floating_leg_BPS",
             [](AssetSwap& s) { return s.floatingLegBPS(); })
        .def("floating_leg_NPV",
             [](AssetSwap& s) { return s.floatingLegNPV(); })
        .def("par_swap", [](const AssetSwap& s) { return s.parSwap(); })
        .def("spread", [](const AssetSwap& s) { return s.spread(); })
        .def("clean_price", [](const AssetSwap& s) { return s.cleanPrice(); })
        .def("non_par_repayment",
             [](const AssetSwap& s) { return s.nonParRepayment(); })
        .def("pay_bond_coupon",
             [](const AssetSwap& s) { return s.payBondCoupon(); })
        .def(
            "set_pricing_engine",
            [](AssetSwap& s,
               const Handle<YieldTermStructure>& discount_curve,
               std::optional<bool> include_settlement_date_flows,
               const Date& settlement_date,
               const Date& npv_date) {
                s.setPricingEngine(ext::make_shared<DiscountingSwapEngine>(
                    discount_curve,
                    include_settlement_date_flows,
                    settlement_date,
                    npv_date));
            },
            nb::arg("discount_curve"),
            nb::arg("include_settlement_date_flows") = nb::none(),
            nb::arg("settlement_date") = Date(),
            nb::arg("npv_date") = Date(),
            "Attach DiscountingSwapEngine.");

    // ZeroCouponSwap is Swap/Instrument (MI via LazyObject) — standalone wrapper.
    // Overloads dispatch on arg 6: IborIndex (fixed payment) vs DayCounter (rate).
    nb::class_<ZeroCouponSwap>(m, "ZeroCouponSwap")
        .def(
            "__init__",
            [](ZeroCouponSwap* self,
               Swap::Type type,
               Real base_nominal,
               const Date& start_date,
               const Date& maturity_date,
               Real fixed_payment,
               const ext::shared_ptr<IborIndex>& ibor_index,
               const Calendar& payment_calendar,
               BusinessDayConvention payment_convention,
               Natural payment_delay) {
                new (self) ZeroCouponSwap(type,
                                          base_nominal,
                                          start_date,
                                          maturity_date,
                                          fixed_payment,
                                          ibor_index,
                                          payment_calendar,
                                          payment_convention,
                                          payment_delay);
            },
            nb::arg("type"),
            nb::arg("base_nominal"),
            nb::arg("start_date"),
            nb::arg("maturity_date"),
            nb::arg("fixed_payment"),
            nb::arg("ibor_index"),
            nb::arg("payment_calendar"),
            nb::arg("payment_convention") = Following,
            nb::arg("payment_delay") = 0)
        .def(
            "__init__",
            [](ZeroCouponSwap* self,
               Swap::Type type,
               Real base_nominal,
               const Date& start_date,
               const Date& maturity_date,
               Rate fixed_rate,
               const DayCounter& fixed_day_counter,
               const ext::shared_ptr<IborIndex>& ibor_index,
               const Calendar& payment_calendar,
               BusinessDayConvention payment_convention,
               Natural payment_delay) {
                new (self) ZeroCouponSwap(type,
                                          base_nominal,
                                          start_date,
                                          maturity_date,
                                          fixed_rate,
                                          fixed_day_counter,
                                          ibor_index,
                                          payment_calendar,
                                          payment_convention,
                                          payment_delay);
            },
            nb::arg("type"),
            nb::arg("base_nominal"),
            nb::arg("start_date"),
            nb::arg("maturity_date"),
            nb::arg("fixed_rate"),
            nb::arg("fixed_day_counter"),
            nb::arg("ibor_index"),
            nb::arg("payment_calendar"),
            nb::arg("payment_convention") = Following,
            nb::arg("payment_delay") = 0)
        .def("NPV", [](ZeroCouponSwap& s) { return s.NPV(); })
        .def("is_expired", [](const ZeroCouponSwap& s) { return s.isExpired(); })
        .def("type", [](const ZeroCouponSwap& s) { return s.type(); })
        .def("base_nominal", [](const ZeroCouponSwap& s) { return s.baseNominal(); })
        .def("start_date", [](const ZeroCouponSwap& s) { return s.startDate(); })
        .def("maturity_date",
             [](const ZeroCouponSwap& s) { return s.maturityDate(); })
        .def("fixed_payment",
             [](const ZeroCouponSwap& s) { return s.fixedPayment(); })
        .def("fixed_leg_NPV",
             [](ZeroCouponSwap& s) { return s.fixedLegNPV(); })
        .def("floating_leg_NPV",
             [](ZeroCouponSwap& s) { return s.floatingLegNPV(); })
        .def("fair_fixed_payment",
             [](ZeroCouponSwap& s) { return s.fairFixedPayment(); })
        .def(
            "fair_fixed_rate",
            [](ZeroCouponSwap& s, const DayCounter& day_counter) {
                return s.fairFixedRate(day_counter);
            },
            nb::arg("day_counter"))
        .def(
            "set_pricing_engine",
            [](ZeroCouponSwap& s,
               const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
            },
            nb::arg("discount_curve"),
            "Attach DiscountingSwapEngine.");

    // PerpetualFutures is Instrument/LazyObject (MI) — standalone wrapper.
    nb::enum_<PerpetualFutures::PayoffType>(m, "PerpetualFuturesPayoffType")
        .value("Linear", PerpetualFutures::Linear)
        .value("Inverse", PerpetualFutures::Inverse)
        .value("Quanto", PerpetualFutures::Quanto);

    nb::enum_<PerpetualFutures::FundingType>(m, "PerpetualFuturesFundingType")
        .value("FundingWithPreviousSpot",
               PerpetualFutures::FundingWithPreviousSpot)
        .value("FundingWithCurrentSpot",
               PerpetualFutures::FundingWithCurrentSpot);

    nb::enum_<DiscountingPerpetualFuturesEngine::InterpolationType>(
        m, "PerpetualFuturesInterpType")
        .value("PiecewiseConstant",
               DiscountingPerpetualFuturesEngine::PiecewiseConstant)
        .value("Linear", DiscountingPerpetualFuturesEngine::Linear)
        .value("CubicSpline", DiscountingPerpetualFuturesEngine::CubicSpline);

    nb::class_<PerpetualFutures>(m, "PerpetualFutures")
        .def(
            "__init__",
            [](PerpetualFutures* self,
               PerpetualFutures::PayoffType payoff_type,
               PerpetualFutures::FundingType funding_type,
               const Period& funding_frequency,
               const Calendar& calendar,
               const DayCounter& day_counter) {
                new (self) PerpetualFutures(payoff_type,
                                            funding_type,
                                            funding_frequency,
                                            calendar,
                                            day_counter);
            },
            nb::arg("payoff_type"),
            nb::arg("funding_type") = PerpetualFutures::FundingWithCurrentSpot,
            nb::arg("funding_frequency") = Period(8, Hours),
            nb::arg("calendar") = Calendar(NullCalendar()),
            nb::arg("day_counter") =
                DayCounter(ActualActual(ActualActual::ISDA)))
        .def("NPV", [](PerpetualFutures& f) { return f.NPV(); })
        .def("is_expired",
             [](const PerpetualFutures& f) { return f.isExpired(); })
        .def(
            "set_pricing_engine",
            [](PerpetualFutures& f,
               const Handle<YieldTermStructure>& domestic_curve,
               const Handle<YieldTermStructure>& foreign_curve,
               const Handle<Quote>& asset_spot,
               const std::vector<Time>& funding_times,
               const std::vector<Rate>& funding_rates,
               const std::vector<Spread>& interest_rate_diffs,
               DiscountingPerpetualFuturesEngine::InterpolationType
                   funding_interp_type,
               Real max_t) {
                f.setPricingEngine(
                    ext::make_shared<DiscountingPerpetualFuturesEngine>(
                        domestic_curve,
                        foreign_curve,
                        asset_spot,
                        funding_times,
                        funding_rates,
                        interest_rate_diffs,
                        funding_interp_type,
                        max_t));
            },
            nb::arg("domestic_curve"),
            nb::arg("foreign_curve"),
            nb::arg("asset_spot"),
            nb::arg("funding_times"),
            nb::arg("funding_rates"),
            nb::arg("interest_rate_diffs"),
            nb::arg("funding_interp_type") =
                DiscountingPerpetualFuturesEngine::PiecewiseConstant,
            nb::arg("max_t") = 60.0,
            "Attach DiscountingPerpetualFuturesEngine.");

    // MultipleResetsSwap is FixedVsFloatingSwap/Instrument (MI) — standalone.
    nb::enum_<RateAveraging::Type>(m, "RateAveraging")
        .value("Simple", RateAveraging::Simple)
        .value("Compound", RateAveraging::Compound);

    nb::class_<MultipleResetsSwap>(m, "MultipleResetsSwap")
        .def("NPV", [](MultipleResetsSwap& s) { return s.NPV(); })
        .def("is_expired",
             [](const MultipleResetsSwap& s) { return s.isExpired(); })
        .def("type", [](const MultipleResetsSwap& s) { return s.type(); })
        .def("nominal", [](const MultipleResetsSwap& s) { return s.nominal(); })
        .def("fixed_rate",
             [](const MultipleResetsSwap& s) { return s.fixedRate(); })
        .def("spread", [](const MultipleResetsSwap& s) { return s.spread(); })
        .def("resets_per_coupon",
             [](const MultipleResetsSwap& s) { return s.resetsPerCoupon(); })
        .def("averaging_method",
             [](const MultipleResetsSwap& s) { return s.averagingMethod(); })
        .def("fair_rate", [](MultipleResetsSwap& s) { return s.fairRate(); })
        .def("fair_spread",
             [](MultipleResetsSwap& s) { return s.fairSpread(); })
        .def("fixed_leg_NPV",
             [](MultipleResetsSwap& s) { return s.fixedLegNPV(); })
        .def("floating_leg_NPV",
             [](MultipleResetsSwap& s) { return s.floatingLegNPV(); })
        .def(
            "set_pricing_engine",
            [](MultipleResetsSwap& s,
               const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
            },
            nb::arg("discount_curve"),
            "Attach DiscountingSwapEngine.");

    m.def(
        "make_multiple_resets_swap",
        [](const Period& tenor,
           const ext::shared_ptr<IborIndex>& ibor_index,
           Size resets_per_coupon,
           std::optional<Rate> fixed_rate,
           std::optional<Natural> settlement_days,
           Real nominal,
           Swap::Type type,
           RateAveraging::Type averaging_method,
           Spread spread) {
            MakeMultipleResetsSwap maker(tenor, ibor_index, resets_per_coupon);
            maker.withType(type)
                .withNominal(nominal)
                .withFloatingLegSpread(spread)
                .withAveragingMethod(averaging_method);
            if (fixed_rate)
                maker.withFixedRate(*fixed_rate);
            if (settlement_days)
                maker.withSettlementDays(*settlement_days);
            return MultipleResetsSwap(maker);
        },
        nb::arg("tenor"),
        nb::arg("ibor_index"),
        nb::arg("resets_per_coupon"),
        nb::arg("fixed_rate") = nb::none(),
        nb::arg("settlement_days") = nb::none(),
        nb::arg("nominal") = 1.0,
        nb::arg("type") = Swap::Payer,
        nb::arg("averaging_method") = RateAveraging::Compound,
        nb::arg("spread") = 0.0,
        "Build a MultipleResetsSwap via QuantLib MakeMultipleResetsSwap "
        "(value copy). Omit fixed_rate to use the fair rate (NPV 0).");

    // FloatFloatSwap is Swap/Instrument (MI) — standalone concrete wrapper.
    nb::class_<FloatFloatSwap>(m, "FloatFloatSwap")
        .def(
            "__init__",
            [](FloatFloatSwap* self,
               Swap::Type type,
               Real nominal1,
               Real nominal2,
               const Schedule& schedule1,
               const ext::shared_ptr<IborIndex>& index1,
               const DayCounter& day_count1,
               const Schedule& schedule2,
               const ext::shared_ptr<IborIndex>& index2,
               const DayCounter& day_count2,
               bool intermediate_capital_exchange,
               bool final_capital_exchange,
               Real gearing1,
               Real spread1,
               std::optional<Real> capped_rate1,
               std::optional<Real> floored_rate1,
               Real gearing2,
               Real spread2,
               std::optional<Real> capped_rate2,
               std::optional<Real> floored_rate2) {
                new (self) FloatFloatSwap(
                    type, nominal1, nominal2, schedule1,
                    ext::static_pointer_cast<InterestRateIndex>(index1),
                    day_count1, schedule2,
                    ext::static_pointer_cast<InterestRateIndex>(index2),
                    day_count2, intermediate_capital_exchange,
                    final_capital_exchange, gearing1, spread1,
                    capped_rate1.value_or(Null<Real>()),
                    floored_rate1.value_or(Null<Real>()), gearing2, spread2,
                    capped_rate2.value_or(Null<Real>()),
                    floored_rate2.value_or(Null<Real>()));
            },
            nb::arg("type"),
            nb::arg("nominal1"),
            nb::arg("nominal2"),
            nb::arg("schedule1"),
            nb::arg("index1"),
            nb::arg("day_count1"),
            nb::arg("schedule2"),
            nb::arg("index2"),
            nb::arg("day_count2"),
            nb::arg("intermediate_capital_exchange") = false,
            nb::arg("final_capital_exchange") = false,
            nb::arg("gearing1") = 1.0,
            nb::arg("spread1") = 0.0,
            nb::arg("capped_rate1") = nb::none(),
            nb::arg("floored_rate1") = nb::none(),
            nb::arg("gearing2") = 1.0,
            nb::arg("spread2") = 0.0,
            nb::arg("capped_rate2") = nb::none(),
            nb::arg("floored_rate2") = nb::none())
        .def("NPV", [](FloatFloatSwap& s) { return s.NPV(); })
        .def("is_expired",
             [](const FloatFloatSwap& s) { return s.isExpired(); })
        .def("type", [](const FloatFloatSwap& s) { return s.type(); })
        .def("nominal1", [](const FloatFloatSwap& s) { return s.nominal1(); })
        .def("nominal2", [](const FloatFloatSwap& s) { return s.nominal2(); })
        .def("spread1", [](const FloatFloatSwap& s) { return s.spread1(); })
        .def("spread2", [](const FloatFloatSwap& s) { return s.spread2(); })
        .def("gearing1", [](const FloatFloatSwap& s) { return s.gearing1(); })
        .def("gearing2", [](const FloatFloatSwap& s) { return s.gearing2(); })
        .def("fair_spread1",
             [](FloatFloatSwap& s) { return s.fairSpread1(); })
        .def("fair_spread2",
             [](FloatFloatSwap& s) { return s.fairSpread2(); })
        .def("leg_NPV",
             [](FloatFloatSwap& s, Size i) { return s.legNPV(i); },
             nb::arg("i"))
        .def("leg_BPS",
             [](FloatFloatSwap& s, Size i) { return s.legBPS(i); },
             nb::arg("i"))
        .def(
            "set_pricing_engine",
            [](FloatFloatSwap& s,
               const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
                auto pricer = ext::make_shared<BlackIborCouponPricer>();
                setCouponPricer(s.leg1(), pricer);
                setCouponPricer(s.leg2(), pricer);
            },
            nb::arg("discount_curve"),
            "Attach DiscountingSwapEngine and BlackIborCouponPricer on "
            "both legs.");

    m.def(
        "make_float_float_swap",
        [](Swap::Type type,
           Real nominal,
           const ext::shared_ptr<IborIndex>& index1,
           const ext::shared_ptr<IborIndex>& index2,
           const Handle<YieldTermStructure>& discount_curve,
           Spread spread1,
           Spread spread2,
           Integer length_in_years,
           Natural settlement_days,
           const Calendar& calendar) {
            Date today = calendar.adjust(Settings::instance().evaluationDate());
            Date settlement =
                calendar.advance(today, settlement_days, Days);
            Date maturity = calendar.advance(settlement, length_in_years, Years,
                                             ModifiedFollowing);

            Schedule schedule1(settlement, maturity, index1->tenor(), calendar,
                               ModifiedFollowing, ModifiedFollowing,
                               DateGeneration::Forward, false);
            Schedule schedule2(settlement, maturity, index2->tenor(), calendar,
                               ModifiedFollowing, ModifiedFollowing,
                               DateGeneration::Forward, false);

            FloatFloatSwap swap(
                type, nominal, nominal, schedule1,
                ext::static_pointer_cast<InterestRateIndex>(index1),
                index1->dayCounter(), schedule2,
                ext::static_pointer_cast<InterestRateIndex>(index2),
                index2->dayCounter(), false, false, 1.0, spread1, Null<Real>(),
                Null<Real>(), 1.0, spread2, Null<Real>(), Null<Real>());
            swap.setPricingEngine(
                ext::make_shared<DiscountingSwapEngine>(discount_curve));
            auto pricer = ext::make_shared<BlackIborCouponPricer>();
            setCouponPricer(swap.leg1(), pricer);
            setCouponPricer(swap.leg2(), pricer);
            return swap;
        },
        nb::arg("type"),
        nb::arg("nominal"),
        nb::arg("index1"),
        nb::arg("index2"),
        nb::arg("discount_curve"),
        nb::arg("spread1") = 0.0,
        nb::arg("spread2") = 0.0,
        nb::arg("length_in_years") = 10,
        nb::arg("settlement_days") = 2,
        nb::arg("calendar") = Calendar(TARGET()),
        "Build a FloatFloatSwap matching FloatFloatSwapTests::CommonVars "
        "(DiscountingSwapEngine + BlackIborCouponPricer).");

    // OvernightIndexFuture is Instrument (no MI) — self-priced from the
    // overnight index curve + optional convexity quote.
    nb::class_<OvernightIndexFuture>(m, "OvernightIndexFuture")
        .def(
            "__init__",
            [](OvernightIndexFuture* self,
               const ext::shared_ptr<OvernightIndex>& overnight_index,
               const Date& value_date,
               const Date& maturity_date,
               const Handle<Quote>& convexity_adjustment,
               RateAveraging::Type averaging_method) {
                new (self) OvernightIndexFuture(
                    overnight_index, value_date, maturity_date,
                    convexity_adjustment, averaging_method);
            },
            nb::arg("overnight_index"),
            nb::arg("value_date"),
            nb::arg("maturity_date"),
            nb::arg("convexity_adjustment") = Handle<Quote>(),
            nb::arg("averaging_method") = RateAveraging::Compound)
        .def("NPV", [](OvernightIndexFuture& f) { return f.NPV(); })
        .def("is_expired",
             [](const OvernightIndexFuture& f) { return f.isExpired(); })
        .def("convexity_adjustment",
             [](const OvernightIndexFuture& f) {
                 return f.convexityAdjustment();
             })
        .def("value_date",
             [](const OvernightIndexFuture& f) { return f.valueDate(); })
        .def("maturity_date",
             [](const OvernightIndexFuture& f) { return f.maturityDate(); });

    m.def(
        "SofrFutureRateHelper",
        [](Real price,
           Month reference_month,
           Year reference_year,
           Frequency reference_freq,
           Real convexity_adjustment) {
            return ext::shared_ptr<RateHelper>(
                ext::make_shared<SofrFutureRateHelper>(
                    price, reference_month, reference_year, reference_freq,
                    convexity_adjustment));
        },
        nb::arg("price"),
        nb::arg("reference_month"),
        nb::arg("reference_year"),
        nb::arg("reference_freq"),
        nb::arg("convexity_adjustment") = 0.0,
        "CME SOFR futures rate helper (compounds third-Wed to third-Wed).");

    // BMASwap is Swap/Instrument (MI) — standalone concrete wrapper.
    nb::class_<BMASwap>(m, "BMASwap")
        .def(
            "__init__",
            [](BMASwap* self,
               Swap::Type type,
               Real nominal,
               const Schedule& libor_schedule,
               Real libor_fraction,
               Spread libor_spread,
               const ext::shared_ptr<IborIndex>& libor_index,
               const DayCounter& libor_day_count,
               const Schedule& bma_schedule,
               const ext::shared_ptr<BMAIndex>& bma_index,
               const DayCounter& bma_day_count) {
                new (self) BMASwap(type, nominal, libor_schedule, libor_fraction,
                                   libor_spread, libor_index, libor_day_count,
                                   bma_schedule, bma_index, bma_day_count);
            },
            nb::arg("type"),
            nb::arg("nominal"),
            nb::arg("libor_schedule"),
            nb::arg("libor_fraction"),
            nb::arg("libor_spread"),
            nb::arg("libor_index"),
            nb::arg("libor_day_count"),
            nb::arg("bma_schedule"),
            nb::arg("bma_index"),
            nb::arg("bma_day_count"))
        .def("NPV", [](BMASwap& s) { return s.NPV(); })
        .def("is_expired", [](const BMASwap& s) { return s.isExpired(); })
        .def("type", [](const BMASwap& s) { return s.type(); })
        .def("nominal", [](const BMASwap& s) { return s.nominal(); })
        .def("libor_fraction",
             [](const BMASwap& s) { return s.liborFraction(); })
        .def("libor_spread",
             [](const BMASwap& s) { return s.liborSpread(); })
        .def("fair_libor_fraction",
             [](BMASwap& s) { return s.fairLiborFraction(); })
        .def("fair_libor_spread",
             [](BMASwap& s) { return s.fairLiborSpread(); })
        .def("libor_leg_NPV",
             [](BMASwap& s) { return s.liborLegNPV(); })
        .def("bma_leg_NPV", [](BMASwap& s) { return s.bmaLegNPV(); })
        .def("libor_leg_BPS",
             [](BMASwap& s) { return s.liborLegBPS(); })
        .def("bma_leg_BPS", [](BMASwap& s) { return s.bmaLegBPS(); })
        .def(
            "set_pricing_engine",
            [](BMASwap& s,
               const Handle<YieldTermStructure>& discount_curve) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingSwapEngine>(discount_curve));
            },
            nb::arg("discount_curve"),
            "Attach DiscountingSwapEngine.");

    m.def(
        "make_bma_swap",
        [](Swap::Type type,
           Real nominal,
           const Period& tenor,
           Real libor_fraction,
           Spread libor_spread,
           const ext::shared_ptr<IborIndex>& libor_index,
           const ext::shared_ptr<BMAIndex>& bma_index,
           const Handle<YieldTermStructure>& discount_curve,
           Natural settlement_days,
           Frequency bma_frequency,
           BusinessDayConvention bma_convention,
           const DayCounter& bma_day_count) {
            Calendar calendar = JointCalendar(bma_index->fixingCalendar(),
                                              libor_index->fixingCalendar(),
                                              JoinHolidays);
            Date today = calendar.adjust(Settings::instance().evaluationDate());
            Date settlement =
                calendar.advance(today, settlement_days, Days);
            Date maturity = settlement + tenor;

            Schedule bma_schedule(settlement, maturity,
                                  Period(bma_frequency),
                                  bma_index->fixingCalendar(), bma_convention,
                                  bma_convention, DateGeneration::Backward,
                                  false);
            Schedule libor_schedule(
                settlement, maturity, libor_index->tenor(),
                libor_index->fixingCalendar(),
                libor_index->businessDayConvention(),
                libor_index->businessDayConvention(),
                DateGeneration::Backward, libor_index->endOfMonth());

            BMASwap swap(type, nominal, libor_schedule, libor_fraction,
                         libor_spread, libor_index, libor_index->dayCounter(),
                         bma_schedule, bma_index, bma_day_count);
            swap.setPricingEngine(
                ext::make_shared<DiscountingSwapEngine>(discount_curve));
            return swap;
        },
        nb::arg("type"),
        nb::arg("nominal"),
        nb::arg("tenor"),
        nb::arg("libor_fraction"),
        nb::arg("libor_spread"),
        nb::arg("libor_index"),
        nb::arg("bma_index"),
        nb::arg("discount_curve"),
        nb::arg("settlement_days") = 2,
        nb::arg("bma_frequency") = Quarterly,
        nb::arg("bma_convention") = Following,
        nb::arg("bma_day_count") =
            DayCounter(ActualActual(ActualActual::ISDA)),
        "Build a BMASwap matching PiecewiseYieldCurve BMA consistency setup.");

    m.def(
        "BMASwapRateHelper",
        [](const Handle<Quote>& libor_fraction,
           const Period& tenor,
           Natural settlement_days,
           const Calendar& calendar,
           const Period& bma_period,
           BusinessDayConvention bma_convention,
           const DayCounter& bma_day_count,
           const ext::shared_ptr<BMAIndex>& bma_index,
           const ext::shared_ptr<IborIndex>& ibor_index) {
            return ext::shared_ptr<RateHelper>(
                ext::make_shared<BMASwapRateHelper>(
                    libor_fraction, tenor, settlement_days, calendar,
                    bma_period, bma_convention, bma_day_count, bma_index,
                    ibor_index));
        },
        nb::arg("libor_fraction"),
        nb::arg("tenor"),
        nb::arg("settlement_days"),
        nb::arg("calendar"),
        nb::arg("bma_period"),
        nb::arg("bma_convention"),
        nb::arg("bma_day_count"),
        nb::arg("bma_index"),
        nb::arg("ibor_index"),
        "Rate helper for bootstrapping over BMA swap libor fractions.");

    // --- Phase 102: VanillaSwingOption (standalone; OneAssetOption MI) ---
    nb::class_<SwingExercise>(m, "SwingExercise")
        .def(
            "__init__",
            [](SwingExercise* self, const std::vector<Date>& dates) {
                new (self) SwingExercise(dates);
            },
            nb::arg("dates"),
            "Swing exercise on a fixed list of dates (seconds default 0).")
        .def(
            "__init__",
            [](SwingExercise* self,
               const Date& from_date,
               const Date& to_date,
               Size step_size_secs) {
                new (self) SwingExercise(from_date, to_date, step_size_secs);
            },
            nb::arg("from_date"),
            nb::arg("to_date"),
            nb::arg("step_size_secs"),
            "Swing exercise on a uniform date-time grid.")
        .def("dates", [](const SwingExercise& e) { return e.dates(); })
        .def("last_date", [](const SwingExercise& e) { return e.lastDate(); })
        .def("seconds", [](const SwingExercise& e) { return e.seconds(); });

    nb::class_<VanillaForwardPayoff>(m, "VanillaForwardPayoff")
        .def(nb::init<Option::Type, Real>(),
             nb::arg("type"),
             nb::arg("strike"))
        .def("strike",
             [](const VanillaForwardPayoff& p) { return p.strike(); })
        .def("option_type",
             [](const VanillaForwardPayoff& p) { return p.optionType(); })
        .def("name", [](const VanillaForwardPayoff& p) { return p.name(); });

    nb::class_<VanillaSwingOption>(m, "VanillaSwingOption")
        .def(
            "__init__",
            [](VanillaSwingOption* self,
               const VanillaForwardPayoff& payoff,
               const SwingExercise& exercise,
               Size min_exercise_rights,
               Size max_exercise_rights) {
                new (self) VanillaSwingOption(
                    ext::make_shared<VanillaForwardPayoff>(payoff),
                    ext::make_shared<SwingExercise>(exercise),
                    min_exercise_rights,
                    max_exercise_rights);
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            nb::arg("min_exercise_rights"),
            nb::arg("max_exercise_rights"),
            "Vanilla swing option with multiple exercise rights.")
        .def("NPV", [](VanillaSwingOption& opt) { return opt.NPV(); })
        .def("is_expired",
             [](const VanillaSwingOption& opt) { return opt.isExpired(); })
        .def(
            "set_fd_pricing_engine",
            [](VanillaSwingOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size t_grid,
               Size x_grid,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdSimpleBSSwingEngine>(
                        process, t_grid, x_grid, scheme_desc));
            },
            nb::arg("process"),
            nb::arg("t_grid") = 50,
            nb::arg("x_grid") = 100,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdSimpleBSSwingEngine.");
    m.def(
        "FdSimpleBSSwingEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process,
           Size /*t_grid*/,
           Size /*x_grid*/) { return process; },
        nb::arg("process"),
        nb::arg("t_grid") = 50,
        nb::arg("x_grid") = 100,
        "Documentation alias — use "
        "VanillaSwingOption.set_fd_pricing_engine instead.");

    // --- Phase 103: VanillaStorageOption (standalone; OneAssetOption MI) ---
    nb::class_<VanillaStorageOption>(m, "VanillaStorageOption")
        .def(
            "__init__",
            [](VanillaStorageOption* self,
               const BermudanExercise& exercise,
               Real capacity,
               Real load,
               Real change_rate) {
                new (self) VanillaStorageOption(
                    ext::make_shared<BermudanExercise>(exercise),
                    capacity,
                    load,
                    change_rate);
            },
            nb::arg("exercise"),
            nb::arg("capacity"),
            nb::arg("load"),
            nb::arg("change_rate"),
            "Vanilla storage option (Bermudan exercise, capacity/load limits).")
        .def("NPV", [](VanillaStorageOption& opt) { return opt.NPV(); })
        .def("is_expired",
             [](const VanillaStorageOption& opt) { return opt.isExpired(); })
        .def(
            "set_fd_pricing_engine",
            [](VanillaStorageOption& opt,
               const ext::shared_ptr<ExtendedOrnsteinUhlenbeckProcess>& process,
               const Handle<YieldTermStructure>& risk_free_ts,
               Size t_grid,
               Size x_grid,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdSimpleExtOUStorageEngine>(
                        process,
                        risk_free_ts.currentLink(),
                        t_grid,
                        x_grid,
                        Null<Size>(),
                        ext::shared_ptr<FdSimpleExtOUStorageEngine::Shape>(),
                        scheme_desc));
            },
            nb::arg("process"),
            nb::arg("risk_free_ts"),
            nb::arg("t_grid") = 50,
            nb::arg("x_grid") = 100,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdSimpleExtOUStorageEngine.");
    m.def(
        "FdSimpleExtOUStorageEngine",
        [](const ext::shared_ptr<ExtendedOrnsteinUhlenbeckProcess>& process,
           const Handle<YieldTermStructure>& /*risk_free_ts*/,
           Size /*t_grid*/,
           Size /*x_grid*/) { return process; },
        nb::arg("process"),
        nb::arg("risk_free_ts"),
        nb::arg("t_grid") = 50,
        nb::arg("x_grid") = 100,
        "Documentation alias — use "
        "VanillaStorageOption.set_fd_pricing_engine instead.");

    // --- Phase 104: Stock / CompositeInstrument (standalone Instrument wrappers) ---
    nb::class_<Stock>(m, "Stock")
        .def(
            "__init__",
            [](Stock* self, const Handle<Quote>& quote) { new (self) Stock(quote); },
            nb::arg("quote"),
            "Simple stock priced at a quote handle.")
        .def("NPV", [](Stock& s) { return s.NPV(); })
        .def("is_expired", [](const Stock& s) { return s.isExpired(); });

    nb::class_<CompositeInstrument>(m, "CompositeInstrument")
        .def(nb::init<>(), "Empty composite instrument (sum of weighted legs).")
        .def(
            "add",
            &composite_add<Stock>,
            nb::arg("instrument"),
            nb::arg("multiplier") = 1.0,
            "Add a Stock leg (shared with the Python instance).")
        .def(
            "add",
            &composite_add<EuropeanOption>,
            nb::arg("instrument"),
            nb::arg("multiplier") = 1.0,
            "Add a EuropeanOption leg (shared with the Python instance).")
        .def(
            "subtract",
            &composite_subtract<Stock>,
            nb::arg("instrument"),
            nb::arg("multiplier") = 1.0)
        .def(
            "subtract",
            &composite_subtract<EuropeanOption>,
            nb::arg("instrument"),
            nb::arg("multiplier") = 1.0)
        .def("NPV", [](CompositeInstrument& c) { return c.NPV(); })
        .def("is_expired",
             [](const CompositeInstrument& c) { return c.isExpired(); });

    // --- Phase 106: ConstNotionalCrossCurrencyFixedVsFloatingSwap ---
    nb::class_<ConstNotionalCrossCurrencyFixedVsFloatingSwap>(
        m, "ConstNotionalCrossCurrencyFixedVsFloatingSwap")
        .def(
            "__init__",
            [](ConstNotionalCrossCurrencyFixedVsFloatingSwap* self,
               Swap::Type type,
               Real fixed_nominal,
               const Currency& fixed_currency,
               const Schedule& fixed_schedule,
               Rate fixed_rate,
               const DayCounter& fixed_day_count,
               BusinessDayConvention fixed_payment_bdc,
               Natural fixed_payment_lag,
               const Calendar& fixed_payment_calendar,
               Real float_nominal,
               const Currency& float_currency,
               const Schedule& float_schedule,
               const ext::shared_ptr<IborIndex>& float_index,
               Spread float_spread,
               BusinessDayConvention float_payment_bdc,
               Natural float_payment_lag,
               const Calendar& float_payment_calendar) {
                new (self) ConstNotionalCrossCurrencyFixedVsFloatingSwap(
                    type,
                    fixed_nominal,
                    fixed_currency,
                    fixed_schedule,
                    fixed_rate,
                    fixed_day_count,
                    fixed_payment_bdc,
                    fixed_payment_lag,
                    fixed_payment_calendar,
                    float_nominal,
                    float_currency,
                    float_schedule,
                    float_index,
                    float_spread,
                    float_payment_bdc,
                    float_payment_lag,
                    float_payment_calendar);
            },
            nb::arg("type"),
            nb::arg("fixed_nominal"),
            nb::arg("fixed_currency"),
            nb::arg("fixed_schedule"),
            nb::arg("fixed_rate"),
            nb::arg("fixed_day_count"),
            nb::arg("fixed_payment_bdc"),
            nb::arg("fixed_payment_lag"),
            nb::arg("fixed_payment_calendar"),
            nb::arg("float_nominal"),
            nb::arg("float_currency"),
            nb::arg("float_schedule"),
            nb::arg("float_index"),
            nb::arg("float_spread"),
            nb::arg("float_payment_bdc"),
            nb::arg("float_payment_lag"),
            nb::arg("float_payment_calendar"))
        .def("NPV",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s) {
                 return s.NPV();
             })
        .def("leg_npv",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s, Size leg) {
                 return s.legNPV(leg);
             },
             nb::arg("leg"))
        .def("leg_bps",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s, Size leg) {
                 return s.legBPS(leg);
             },
             nb::arg("leg"))
        .def("in_ccy_leg_npv",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s, Size leg) {
                 return s.inCcyLegNPV(leg);
             },
             nb::arg("leg"))
        .def("in_ccy_leg_bps",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s, Size leg) {
                 return s.inCcyLegBPS(leg);
             },
             nb::arg("leg"))
        .def("fair_rate",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s) {
                 return s.fairRate();
             })
        .def("fair_spread",
             [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s) {
                 return s.fairSpread();
             })
        .def(
            "set_pricing_engine",
            [](ConstNotionalCrossCurrencyFixedVsFloatingSwap& s,
               const Currency& domestic_currency,
               const Handle<YieldTermStructure>& domestic_discount,
               const Currency& foreign_currency,
               const Handle<YieldTermStructure>& foreign_discount,
               const Handle<Quote>& spot_fx) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingConstNotionalCrossCurrencySwapEngine>(
                        domestic_currency,
                        domestic_discount,
                        foreign_currency,
                        foreign_discount,
                        spot_fx));
            },
            nb::arg("domestic_currency"),
            nb::arg("domestic_discount"),
            nb::arg("foreign_currency"),
            nb::arg("foreign_discount"),
            nb::arg("spot_fx"),
            "Attach DiscountingConstNotionalCrossCurrencySwapEngine.");

    // --- Phase 109: ConstNotionalCrossCurrencyBasisSwap ---
    nb::class_<ConstNotionalCrossCurrencyBasisSwap>(
        m, "ConstNotionalCrossCurrencyBasisSwap")
        .def(
            "__init__",
            [](ConstNotionalCrossCurrencyBasisSwap* self,
               Real pay_nominal,
               const Currency& pay_currency,
               const Schedule& pay_schedule,
               const ext::shared_ptr<IborIndex>& pay_index,
               Spread pay_spread,
               Real pay_gearing,
               Real rec_nominal,
               const Currency& rec_currency,
               const Schedule& rec_schedule,
               const ext::shared_ptr<IborIndex>& rec_index,
               Spread rec_spread,
               Real rec_gearing,
               Integer pay_payment_lag,
               Integer rec_payment_lag,
               bool pay_compound_spread,
               std::optional<Natural> pay_lookback_days,
               bool pay_observation_shift,
               Natural pay_lockout_days,
               RateAveraging::Type pay_averaging_method,
               bool rec_compound_spread,
               std::optional<Natural> rec_lookback_days,
               bool rec_observation_shift,
               Natural rec_lockout_days,
               RateAveraging::Type rec_averaging_method,
               bool telescopic_value_dates) {
                init_const_notional_cross_currency_basis_swap(
                    self,
                    pay_nominal,
                    pay_currency,
                    pay_schedule,
                    pay_index,
                    pay_spread,
                    pay_gearing,
                    rec_nominal,
                    rec_currency,
                    rec_schedule,
                    rec_index,
                    rec_spread,
                    rec_gearing,
                    pay_payment_lag,
                    rec_payment_lag,
                    pay_compound_spread,
                    pay_lookback_days,
                    pay_observation_shift,
                    pay_lockout_days,
                    pay_averaging_method,
                    rec_compound_spread,
                    rec_lookback_days,
                    rec_observation_shift,
                    rec_lockout_days,
                    rec_averaging_method,
                    telescopic_value_dates);
            },
            nb::arg("pay_nominal"),
            nb::arg("pay_currency"),
            nb::arg("pay_schedule"),
            nb::arg("pay_index"),
            nb::arg("pay_spread"),
            nb::arg("pay_gearing"),
            nb::arg("rec_nominal"),
            nb::arg("rec_currency"),
            nb::arg("rec_schedule"),
            nb::arg("rec_index"),
            nb::arg("rec_spread"),
            nb::arg("rec_gearing"),
            nb::arg("pay_payment_lag") = 0,
            nb::arg("rec_payment_lag") = 0,
            nb::arg("pay_compound_spread") = false,
            nb::arg("pay_lookback_days") = nb::none(),
            nb::arg("pay_observation_shift") = false,
            nb::arg("pay_lockout_days") = 0,
            nb::arg("pay_averaging_method") = RateAveraging::Compound,
            nb::arg("rec_compound_spread") = false,
            nb::arg("rec_lookback_days") = nb::none(),
            nb::arg("rec_observation_shift") = false,
            nb::arg("rec_lockout_days") = 0,
            nb::arg("rec_averaging_method") = RateAveraging::Compound,
            nb::arg("telescopic_value_dates") = false)
        .def(
            "__init__",
            [](ConstNotionalCrossCurrencyBasisSwap* self,
               Real pay_nominal,
               const Currency& pay_currency,
               const Schedule& pay_schedule,
               const ext::shared_ptr<OvernightIndex>& pay_index,
               Spread pay_spread,
               Real pay_gearing,
               Real rec_nominal,
               const Currency& rec_currency,
               const Schedule& rec_schedule,
               const ext::shared_ptr<OvernightIndex>& rec_index,
               Spread rec_spread,
               Real rec_gearing,
               Integer pay_payment_lag,
               Integer rec_payment_lag,
               bool pay_compound_spread,
               std::optional<Natural> pay_lookback_days,
               bool pay_observation_shift,
               Natural pay_lockout_days,
               RateAveraging::Type pay_averaging_method,
               bool rec_compound_spread,
               std::optional<Natural> rec_lookback_days,
               bool rec_observation_shift,
               Natural rec_lockout_days,
               RateAveraging::Type rec_averaging_method,
               bool telescopic_value_dates) {
                init_const_notional_cross_currency_basis_swap(
                    self,
                    pay_nominal,
                    pay_currency,
                    pay_schedule,
                    pay_index,
                    pay_spread,
                    pay_gearing,
                    rec_nominal,
                    rec_currency,
                    rec_schedule,
                    rec_index,
                    rec_spread,
                    rec_gearing,
                    pay_payment_lag,
                    rec_payment_lag,
                    pay_compound_spread,
                    pay_lookback_days,
                    pay_observation_shift,
                    pay_lockout_days,
                    pay_averaging_method,
                    rec_compound_spread,
                    rec_lookback_days,
                    rec_observation_shift,
                    rec_lockout_days,
                    rec_averaging_method,
                    telescopic_value_dates);
            },
            nb::arg("pay_nominal"),
            nb::arg("pay_currency"),
            nb::arg("pay_schedule"),
            nb::arg("pay_index"),
            nb::arg("pay_spread"),
            nb::arg("pay_gearing"),
            nb::arg("rec_nominal"),
            nb::arg("rec_currency"),
            nb::arg("rec_schedule"),
            nb::arg("rec_index"),
            nb::arg("rec_spread"),
            nb::arg("rec_gearing"),
            nb::arg("pay_payment_lag") = 0,
            nb::arg("rec_payment_lag") = 0,
            nb::arg("pay_compound_spread") = false,
            nb::arg("pay_lookback_days") = nb::none(),
            nb::arg("pay_observation_shift") = false,
            nb::arg("pay_lockout_days") = 0,
            nb::arg("pay_averaging_method") = RateAveraging::Compound,
            nb::arg("rec_compound_spread") = false,
            nb::arg("rec_lookback_days") = nb::none(),
            nb::arg("rec_observation_shift") = false,
            nb::arg("rec_lockout_days") = 0,
            nb::arg("rec_averaging_method") = RateAveraging::Compound,
            nb::arg("telescopic_value_dates") = false)
        .def("NPV",
             [](ConstNotionalCrossCurrencyBasisSwap& s) { return s.NPV(); })
        .def("leg_npv",
             [](ConstNotionalCrossCurrencyBasisSwap& s, Size leg) {
                 return s.legNPV(leg);
             },
             nb::arg("leg"))
        .def("leg_bps",
             [](ConstNotionalCrossCurrencyBasisSwap& s, Size leg) {
                 return s.legBPS(leg);
             },
             nb::arg("leg"))
        .def("in_ccy_leg_npv",
             [](ConstNotionalCrossCurrencyBasisSwap& s, Size leg) {
                 return s.inCcyLegNPV(leg);
             },
             nb::arg("leg"))
        .def("in_ccy_leg_bps",
             [](ConstNotionalCrossCurrencyBasisSwap& s, Size leg) {
                 return s.inCcyLegBPS(leg);
             },
             nb::arg("leg"))
        .def("fair_pay_spread",
             [](ConstNotionalCrossCurrencyBasisSwap& s) {
                 return s.fairPaySpread();
             })
        .def("fair_rec_spread",
             [](ConstNotionalCrossCurrencyBasisSwap& s) {
                 return s.fairRecSpread();
             })
        .def(
            "set_pricing_engine",
            [](ConstNotionalCrossCurrencyBasisSwap& s,
               const Currency& domestic_currency,
               const Handle<YieldTermStructure>& domestic_discount,
               const Currency& foreign_currency,
               const Handle<YieldTermStructure>& foreign_discount,
               const Handle<Quote>& spot_fx) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingConstNotionalCrossCurrencySwapEngine>(
                        domestic_currency,
                        domestic_discount,
                        foreign_currency,
                        foreign_discount,
                        spot_fx));
            },
            nb::arg("domestic_currency"),
            nb::arg("domestic_discount"),
            nb::arg("foreign_currency"),
            nb::arg("foreign_discount"),
            nb::arg("spot_fx"),
            "Attach DiscountingConstNotionalCrossCurrencySwapEngine.");

    // --- Phase 111: ConstNotionalCrossCurrencySwap ---
    nb::class_<ConstNotionalCrossCurrencySwap>(
        m, "ConstNotionalCrossCurrencySwap")
        .def("NPV",
             [](ConstNotionalCrossCurrencySwap& s) { return s.NPV(); })
        .def("is_expired",
             [](const ConstNotionalCrossCurrencySwap& s) {
                 return s.isExpired();
             })
        .def("leg_npv",
             [](ConstNotionalCrossCurrencySwap& s, Size leg) {
                 return s.legNPV(leg);
             },
             nb::arg("leg"))
        .def("leg_bps",
             [](ConstNotionalCrossCurrencySwap& s, Size leg) {
                 return s.legBPS(leg);
             },
             nb::arg("leg"))
        .def("in_ccy_leg_npv",
             [](ConstNotionalCrossCurrencySwap& s, Size leg) {
                 return s.inCcyLegNPV(leg);
             },
             nb::arg("leg"))
        .def("in_ccy_leg_bps",
             [](ConstNotionalCrossCurrencySwap& s, Size leg) {
                 return s.inCcyLegBPS(leg);
             },
             nb::arg("leg"))
        .def("leg_currency",
             [](const ConstNotionalCrossCurrencySwap& s, Size leg) {
                 return s.legCurrency(leg);
             },
             nb::arg("leg"))
        .def(
            "set_pricing_engine",
            [](ConstNotionalCrossCurrencySwap& s,
               const Currency& domestic_currency,
               const Handle<YieldTermStructure>& domestic_discount,
               const Currency& foreign_currency,
               const Handle<YieldTermStructure>& foreign_discount,
               const Handle<Quote>& spot_fx) {
                s.setPricingEngine(
                    ext::make_shared<DiscountingConstNotionalCrossCurrencySwapEngine>(
                        domestic_currency,
                        domestic_discount,
                        foreign_currency,
                        foreign_discount,
                        spot_fx));
            },
            nb::arg("domestic_currency"),
            nb::arg("domestic_discount"),
            nb::arg("foreign_currency"),
            nb::arg("foreign_discount"),
            nb::arg("spot_fx"),
            "Attach DiscountingConstNotionalCrossCurrencySwapEngine.");

    m.def(
        "make_fix_fix_xccy_swap",
        [](Real usd_nominal, Rate spot_fx) {
            Calendar payCalendar = JointCalendar(
                UnitedStates(UnitedStates::Settlement), Switzerland());
            const Date today = Settings::instance().evaluationDate();
            const Date startDate = payCalendar.advance(today, Period(2, Days));
            const Date endDate = payCalendar.advance(today, Period(5, Years));
            const BusinessDayConvention convention = Following;
            const DayCounter dc = Actual365Fixed();

            Schedule schedule(
                startDate,
                endDate,
                Period(3, Months),
                payCalendar,
                convention,
                convention,
                DateGeneration::Forward,
                false);

            const Rate usdRate = 0.0575;
            const Rate chfRate = 0.0201;

            Leg usdLeg = FixedRateLeg(schedule)
                             .withNotionals(usd_nominal)
                             .withCouponRates(usdRate, dc)
                             .withPaymentAdjustment(convention)
                             .withPaymentCalendar(payCalendar);
            const Date exchangeDate =
                payCalendar.adjust(schedule.dates().front(), convention);
            usdLeg.insert(
                usdLeg.begin(),
                ext::make_shared<SimpleCashFlow>(-usd_nominal, exchangeDate));
            usdLeg.push_back(ext::make_shared<SimpleCashFlow>(
                usd_nominal, usdLeg.back()->date()));

            const Real chfNominal = usd_nominal * spot_fx;
            Leg chfLeg = FixedRateLeg(schedule)
                             .withNotionals(chfNominal)
                             .withCouponRates(chfRate, dc)
                             .withPaymentAdjustment(convention)
                             .withPaymentCalendar(payCalendar);
            chfLeg.insert(
                chfLeg.begin(),
                ext::make_shared<SimpleCashFlow>(-chfNominal, exchangeDate));
            chfLeg.push_back(ext::make_shared<SimpleCashFlow>(
                chfNominal, chfLeg.back()->date()));

            return ConstNotionalCrossCurrencySwap(
                usdLeg, USDCurrency(), chfLeg, CHFCurrency());
        },
        nb::arg("usd_nominal"),
        nb::arg("spot_fx"),
        "Build fix/fix XCCY swap matching "
        "ConstNotionalCrossCurrencySwapTests::makeFixFixXCCYSwap.");

    // --- Phase 112: float/float XCCY factory ---
    m.def(
        "make_float_float_xccy_swap",
        [](Real usd_nominal,
           Rate spot_fx,
           const Handle<YieldTermStructure>& usd_projection,
           const Handle<YieldTermStructure>& gbp_projection) {
            Calendar payCalendar = JointCalendar(
                UnitedStates(UnitedStates::Settlement), UnitedKingdom());
            const Date today = Settings::instance().evaluationDate();
            const Date startDate = payCalendar.advance(today, Period(2, Days));
            const Date endDate = payCalendar.advance(today, Period(5, Years));
            const BusinessDayConvention convention = Following;

            Schedule schedule(
                startDate,
                endDate,
                Period(3, Months),
                payCalendar,
                convention,
                convention,
                DateGeneration::Forward,
                false);

            auto usdLibor3M = ext::make_shared<USDLibor>(
                Period(3, Months), usd_projection);
            Leg usdLeg = IborLeg(schedule, usdLibor3M)
                             .withNotionals(usd_nominal)
                             .withPaymentAdjustment(convention)
                             .withPaymentCalendar(payCalendar);
            const Date exchangeDate = payCalendar.adjust(schedule.dates().front());
            usdLeg.insert(
                usdLeg.begin(),
                ext::make_shared<SimpleCashFlow>(-usd_nominal, exchangeDate));
            usdLeg.push_back(ext::make_shared<SimpleCashFlow>(
                usd_nominal, usdLeg.back()->date()));

            const Real gbpNominal = usd_nominal * spot_fx;
            auto gbpLibor3M = ext::make_shared<GBPLibor>(
                Period(3, Months), gbp_projection);
            Leg gbpLeg = IborLeg(schedule, gbpLibor3M)
                             .withNotionals(gbpNominal)
                             .withPaymentAdjustment(convention)
                             .withPaymentCalendar(payCalendar);
            gbpLeg.insert(
                gbpLeg.begin(),
                ext::make_shared<SimpleCashFlow>(-gbpNominal, exchangeDate));
            gbpLeg.push_back(ext::make_shared<SimpleCashFlow>(
                gbpNominal, gbpLeg.back()->date()));

            return ConstNotionalCrossCurrencySwap(
                usdLeg, USDCurrency(), gbpLeg, GBPCurrency());
        },
        nb::arg("usd_nominal"),
        nb::arg("spot_fx"),
        nb::arg("usd_projection"),
        nb::arg("gbp_projection"),
        "Build float/float XCCY swap matching "
        "ConstNotionalCrossCurrencySwapTests::makeFloatFloatXCCYSwap.");

    // --- Phase 113: fix/float XCCY factory ---
    m.def(
        "make_fix_float_xccy_swap",
        [](Real usd_nominal,
           Rate spot_fx,
           const Handle<YieldTermStructure>& usd_projection) {
            Calendar payCalendar = JointCalendar(
                JointCalendar(UnitedStates(UnitedStates::Settlement),
                              UnitedKingdom()),
                Turkey());
            const Date today = Settings::instance().evaluationDate();
            const Date startDate = payCalendar.advance(today, Period(2, Days));
            const Date endDate = payCalendar.advance(today, Period(5, Years));
            const BusinessDayConvention convention = ModifiedFollowing;
            const BusinessDayConvention payConvention = Following;
            const DayCounter dc = Actual365Fixed();

            Schedule floatSchedule(
                startDate,
                endDate,
                Period(3, Months),
                payCalendar,
                convention,
                convention,
                DateGeneration::Backward,
                false);
            Schedule fixSchedule(
                startDate,
                endDate,
                Period(1, Years),
                payCalendar,
                convention,
                convention,
                DateGeneration::Backward,
                false);

            const Rate tryRate = 0.249;
            const Real tryNominal = usd_nominal * spot_fx;
            Leg tryLeg = FixedRateLeg(fixSchedule)
                             .withNotionals(tryNominal)
                             .withCouponRates(tryRate, dc)
                             .withPaymentAdjustment(payConvention)
                             .withPaymentCalendar(payCalendar);
            Date exchangeDate =
                payCalendar.adjust(fixSchedule.dates().front(), convention);
            tryLeg.insert(
                tryLeg.begin(),
                ext::make_shared<SimpleCashFlow>(-tryNominal, exchangeDate));
            tryLeg.push_back(ext::make_shared<SimpleCashFlow>(
                tryNominal, tryLeg.back()->date()));

            auto usdLibor3M = ext::make_shared<USDLibor>(
                Period(3, Months), usd_projection);
            Leg usdLeg = IborLeg(floatSchedule, usdLibor3M)
                             .withNotionals(usd_nominal)
                             .withPaymentAdjustment(payConvention)
                             .withPaymentCalendar(payCalendar);
            exchangeDate =
                payCalendar.adjust(floatSchedule.dates().front(), convention);
            usdLeg.insert(
                usdLeg.begin(),
                ext::make_shared<SimpleCashFlow>(-usd_nominal, exchangeDate));
            usdLeg.push_back(ext::make_shared<SimpleCashFlow>(
                usd_nominal, usdLeg.back()->date()));

            return ConstNotionalCrossCurrencySwap(
                tryLeg, TRYCurrency(), usdLeg, USDCurrency());
        },
        nb::arg("usd_nominal"),
        nb::arg("spot_fx"),
        nb::arg("usd_projection"),
        "Build fix/float XCCY swap matching "
        "ConstNotionalCrossCurrencySwapTests::makeFixFloatXCCYSwap.");
}
