#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/exercise.hpp>
#include <ql/experimental/callablebonds/blackcallablebondengine.hpp>
#include <ql/experimental/callablebonds/callablebond.hpp>
#include <ql/experimental/callablebonds/treecallablebondengine.hpp>
#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/instruments/bond.hpp>
#include <ql/instruments/bonds/convertiblebonds.hpp>
#include <ql/instruments/callabilityschedule.hpp>
#include <ql/methods/lattices/binomialtree.hpp>
#include <ql/models/shortrate/onefactormodels/hullwhite.hpp>
#include <ql/pricingengines/bond/binomialconvertibleengine.hpp>
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/quote.hpp>
#include <ql/quotes/simplequote.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/businessdayconvention.hpp>
#include <ql/time/calendar.hpp>
#include <ql/time/date.hpp>
#include <ql/time/daycounter.hpp>
#include <ql/time/schedule.hpp>

using namespace QuantLib;

void bind_callable(nb::module_& m) {
    // --- Phase 23: callable / puttable bonds ---
    // BondPrice / BondPriceType are registered in bind_instruments (Phase 72).

    nb::enum_<Callability::Type>(m, "CallabilityType")
        .value("Call", Callability::Call)
        .value("Put", Callability::Put);

    // Callability is Event (MI) — opaque type + factory returning shared_ptr.
    nb::class_<Callability>(m, "Callability")
        .def("price",
             [](const Callability& c) { return c.price(); })
        .def("type", [](const Callability& c) { return c.type(); })
        .def("date", [](const Callability& c) { return c.date(); });

    m.def(
        "make_callability",
        [](const Bond::Price& price,
           Callability::Type type,
           const Date& date) {
            return ext::shared_ptr<Callability>(
                ext::make_shared<Callability>(price, type, date));
        },
        nb::arg("price"),
        nb::arg("type"),
        nb::arg("date"),
        "Factory: BondPrice + CallabilityType + date → Callability.");

    m.def(
        "make_callability",
        [](Real amount,
           Bond::Price::Type price_type,
           Callability::Type type,
           const Date& date) {
            return ext::shared_ptr<Callability>(ext::make_shared<Callability>(
                Bond::Price(amount, price_type), type, date));
        },
        nb::arg("amount"),
        nb::arg("price_type"),
        nb::arg("type"),
        nb::arg("date"),
        "Factory: amount + BondPriceType + CallabilityType + date → "
        "Callability.");

    // CallableFixedRateBond is Bond/Instrument (MI) — standalone wrapper.
    nb::class_<CallableFixedRateBond>(m, "CallableFixedRateBond")
        .def(
            "__init__",
            [](CallableFixedRateBond* self,
               Natural settlement_days,
               Real face_amount,
               const Schedule& schedule,
               const std::vector<Rate>& coupons,
               const DayCounter& accrual_day_counter,
               BusinessDayConvention payment_convention,
               Real redemption,
               const Date& issue_date,
               const CallabilitySchedule& put_call_schedule) {
                new (self) CallableFixedRateBond(settlement_days,
                                                 face_amount,
                                                 schedule,
                                                 coupons,
                                                 accrual_day_counter,
                                                 payment_convention,
                                                 redemption,
                                                 issue_date,
                                                 put_call_schedule);
            },
            nb::arg("settlement_days"),
            nb::arg("face_amount"),
            nb::arg("schedule"),
            nb::arg("coupons"),
            nb::arg("accrual_day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("redemption") = 100.0,
            nb::arg("issue_date") = Date(),
            nb::arg("put_call_schedule") = CallabilitySchedule())
        .def("NPV", [](CallableFixedRateBond& b) { return b.NPV(); })
        .def("clean_price",
             [](CallableFixedRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](CallableFixedRateBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const CallableFixedRateBond& b) { return b.settlementDate(); })
        .def("maturity_date",
             [](const CallableFixedRateBond& b) { return b.maturityDate(); })
        .def(
            "implied_volatility",
            [](const CallableFixedRateBond& b,
               const Bond::Price& target_price,
               const Handle<YieldTermStructure>& discount_curve,
               Real accuracy,
               Size max_evaluations,
               Volatility min_vol,
               Volatility max_vol) {
                return b.impliedVolatility(target_price,
                                           discount_curve,
                                           accuracy,
                                           max_evaluations,
                                           min_vol,
                                           max_vol);
            },
            nb::arg("target_price"),
            nb::arg("discount_curve"),
            nb::arg("accuracy") = 1.0e-8,
            nb::arg("max_evaluations") = 200,
            nb::arg("min_vol") = 1.0e-4,
            nb::arg("max_vol") = 1.0,
            "Black fwd-yield implied volatility matching a target BondPrice.")
        // Phase 56: OAS / cleanPriceOAS / effective duration & convexity
        // (non-const; require a tree engine — Black engines ignore the spread).
        .def(
            "oas",
            [](CallableFixedRateBond& b,
               Real clean_price,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Date settlement_date,
               Real accuracy,
               Size max_iterations,
               Real guess) {
                return b.OAS(clean_price,
                             engine_ts,
                             day_counter,
                             compounding,
                             frequency,
                             settlement_date,
                             accuracy,
                             max_iterations,
                             guess);
            },
            nb::arg("clean_price"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            nb::arg("accuracy") = 1.0e-10,
            nb::arg("max_iterations") = 100,
            nb::arg("guess") = 0.0,
            "Option-adjusted spread matching clean_price (non-const; requires "
            "a tree pricing engine — Black engines ignore the OAS spread).")
        .def(
            "clean_price_oas",
            [](CallableFixedRateBond& b,
               Real oas,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Date settlement_date) {
                return b.cleanPriceOAS(oas,
                                       engine_ts,
                                       day_counter,
                                       compounding,
                                       frequency,
                                       settlement_date);
            },
            nb::arg("oas"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            "Clean price at a given OAS (non-const; requires a tree pricing "
            "engine).")
        .def(
            "effective_duration",
            [](CallableFixedRateBond& b,
               Real oas,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Real bump) {
                return b.effectiveDuration(oas,
                                           engine_ts,
                                           day_counter,
                                           compounding,
                                           frequency,
                                           bump);
            },
            nb::arg("oas"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("bump") = 2.0e-4,
            "Effective duration at OAS via ±bump parallel shifts of engine_ts.")
        .def(
            "effective_convexity",
            [](CallableFixedRateBond& b,
               Real oas,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Real bump) {
                return b.effectiveConvexity(oas,
                                            engine_ts,
                                            day_counter,
                                            compounding,
                                            frequency,
                                            bump);
            },
            nb::arg("oas"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("bump") = 2.0e-4,
            "Effective convexity at OAS via ±bump parallel shifts of "
            "engine_ts.")
        .def(
            "set_tree_pricing_engine",
            [](CallableFixedRateBond& b,
               const ext::shared_ptr<HullWhite>& model,
               Size time_steps,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<TreeCallableFixedRateBondEngine>(
                        model, time_steps, discount_curve));
            },
            nb::arg("model"),
            nb::arg("time_steps") = 240,
            nb::arg("discount_curve") = Handle<YieldTermStructure>(),
            "Attach TreeCallableFixedRateBondEngine on a HullWhite model.")
        .def(
            "set_black_pricing_engine",
            [](CallableFixedRateBond& b,
               const Handle<Quote>& fwd_yield_vol,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<BlackCallableFixedRateBondEngine>(
                        fwd_yield_vol, discount_curve));
            },
            nb::arg("fwd_yield_vol"),
            nb::arg("discount_curve"),
            "Attach BlackCallableFixedRateBondEngine (fwd yield vol).")
        .def(
            "set_black_pricing_engine",
            [](CallableFixedRateBond& b,
               Real fwd_yield_vol,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<BlackCallableFixedRateBondEngine>(
                        Handle<Quote>(
                            ext::make_shared<SimpleQuote>(fwd_yield_vol)),
                        discount_curve));
            },
            nb::arg("fwd_yield_vol"),
            nb::arg("discount_curve"),
            "Attach BlackCallableFixedRateBondEngine from a scalar fwd yield "
            "vol.");

    nb::class_<CallableZeroCouponBond>(m, "CallableZeroCouponBond")
        .def(
            "__init__",
            [](CallableZeroCouponBond* self,
               Natural settlement_days,
               Real face_amount,
               const Calendar& calendar,
               const Date& maturity_date,
               const DayCounter& day_counter,
               BusinessDayConvention payment_convention,
               Real redemption,
               const Date& issue_date,
               const CallabilitySchedule& put_call_schedule) {
                new (self) CallableZeroCouponBond(settlement_days,
                                                  face_amount,
                                                  calendar,
                                                  maturity_date,
                                                  day_counter,
                                                  payment_convention,
                                                  redemption,
                                                  issue_date,
                                                  put_call_schedule);
            },
            nb::arg("settlement_days"),
            nb::arg("face_amount"),
            nb::arg("calendar"),
            nb::arg("maturity_date"),
            nb::arg("day_counter"),
            nb::arg("payment_convention") = Following,
            nb::arg("redemption") = 100.0,
            nb::arg("issue_date") = Date(),
            nb::arg("put_call_schedule") = CallabilitySchedule())
        .def("NPV", [](CallableZeroCouponBond& b) { return b.NPV(); })
        .def("clean_price",
             [](CallableZeroCouponBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](CallableZeroCouponBond& b) { return b.dirtyPrice(); })
        .def("settlement_date",
             [](const CallableZeroCouponBond& b) {
                 return b.settlementDate();
             })
        .def("maturity_date",
             [](const CallableZeroCouponBond& b) { return b.maturityDate(); })
        .def(
            "implied_volatility",
            [](const CallableZeroCouponBond& b,
               const Bond::Price& target_price,
               const Handle<YieldTermStructure>& discount_curve,
               Real accuracy,
               Size max_evaluations,
               Volatility min_vol,
               Volatility max_vol) {
                return b.impliedVolatility(target_price,
                                           discount_curve,
                                           accuracy,
                                           max_evaluations,
                                           min_vol,
                                           max_vol);
            },
            nb::arg("target_price"),
            nb::arg("discount_curve"),
            nb::arg("accuracy") = 1.0e-8,
            nb::arg("max_evaluations") = 200,
            nb::arg("min_vol") = 1.0e-4,
            nb::arg("max_vol") = 1.0,
            "Black fwd-yield implied volatility matching a target BondPrice.")
        // Phase 56: OAS / cleanPriceOAS / effective duration & convexity.
        .def(
            "oas",
            [](CallableZeroCouponBond& b,
               Real clean_price,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Date settlement_date,
               Real accuracy,
               Size max_iterations,
               Real guess) {
                return b.OAS(clean_price,
                             engine_ts,
                             day_counter,
                             compounding,
                             frequency,
                             settlement_date,
                             accuracy,
                             max_iterations,
                             guess);
            },
            nb::arg("clean_price"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            nb::arg("accuracy") = 1.0e-10,
            nb::arg("max_iterations") = 100,
            nb::arg("guess") = 0.0,
            "Option-adjusted spread matching clean_price (non-const; requires "
            "a tree pricing engine — Black engines ignore the OAS spread).")
        .def(
            "clean_price_oas",
            [](CallableZeroCouponBond& b,
               Real oas,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Date settlement_date) {
                return b.cleanPriceOAS(oas,
                                       engine_ts,
                                       day_counter,
                                       compounding,
                                       frequency,
                                       settlement_date);
            },
            nb::arg("oas"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("settlement_date") = Date(),
            "Clean price at a given OAS (non-const; requires a tree pricing "
            "engine).")
        .def(
            "effective_duration",
            [](CallableZeroCouponBond& b,
               Real oas,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Real bump) {
                return b.effectiveDuration(oas,
                                           engine_ts,
                                           day_counter,
                                           compounding,
                                           frequency,
                                           bump);
            },
            nb::arg("oas"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("bump") = 2.0e-4,
            "Effective duration at OAS via ±bump parallel shifts of engine_ts.")
        .def(
            "effective_convexity",
            [](CallableZeroCouponBond& b,
               Real oas,
               const Handle<YieldTermStructure>& engine_ts,
               const DayCounter& day_counter,
               Compounding compounding,
               Frequency frequency,
               Real bump) {
                return b.effectiveConvexity(oas,
                                            engine_ts,
                                            day_counter,
                                            compounding,
                                            frequency,
                                            bump);
            },
            nb::arg("oas"),
            nb::arg("engine_ts"),
            nb::arg("day_counter"),
            nb::arg("compounding"),
            nb::arg("frequency"),
            nb::arg("bump") = 2.0e-4,
            "Effective convexity at OAS via ±bump parallel shifts of "
            "engine_ts.")
        .def(
            "set_tree_pricing_engine",
            [](CallableZeroCouponBond& b,
               const ext::shared_ptr<HullWhite>& model,
               Size time_steps,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<TreeCallableZeroCouponBondEngine>(
                        model, time_steps, discount_curve));
            },
            nb::arg("model"),
            nb::arg("time_steps") = 240,
            nb::arg("discount_curve") = Handle<YieldTermStructure>(),
            "Attach TreeCallableZeroCouponBondEngine on a HullWhite model.")
        .def(
            "set_black_pricing_engine",
            [](CallableZeroCouponBond& b,
               const Handle<Quote>& fwd_yield_vol,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<BlackCallableZeroCouponBondEngine>(
                        fwd_yield_vol, discount_curve));
            },
            nb::arg("fwd_yield_vol"),
            nb::arg("discount_curve"),
            "Attach BlackCallableZeroCouponBondEngine (fwd yield vol).")
        .def(
            "set_black_pricing_engine",
            [](CallableZeroCouponBond& b,
               Real fwd_yield_vol,
               const Handle<YieldTermStructure>& discount_curve) {
                b.setPricingEngine(
                    ext::make_shared<BlackCallableZeroCouponBondEngine>(
                        Handle<Quote>(
                            ext::make_shared<SimpleQuote>(fwd_yield_vol)),
                        discount_curve));
            },
            nb::arg("fwd_yield_vol"),
            nb::arg("discount_curve"),
            "Attach BlackCallableZeroCouponBondEngine from a scalar fwd yield "
            "vol.");

    // Phase 54: documentation aliases for Black callable engines.
    m.def(
        "BlackCallableFixedRateBondEngine",
        [](const Handle<Quote>& fwd_yield_vol,
           const Handle<YieldTermStructure>& discount_curve) {
            return discount_curve;
        },
        nb::arg("fwd_yield_vol"),
        nb::arg("discount_curve"),
        "Documentation alias — use "
        "CallableFixedRateBond.set_black_pricing_engine instead.");

    m.def(
        "BlackCallableZeroCouponBondEngine",
        [](const Handle<Quote>& fwd_yield_vol,
           const Handle<YieldTermStructure>& discount_curve) {
            return discount_curve;
        },
        nb::arg("fwd_yield_vol"),
        nb::arg("discount_curve"),
        "Documentation alias — use "
        "CallableZeroCouponBond.set_black_pricing_engine instead.");

    // --- Phase 57: convertible bonds (Tsiveriotis–Fernandes binomial) ---

    m.def(
        "make_soft_callability",
        [](Real amount,
           Bond::Price::Type price_type,
           const Date& date,
           Real trigger) {
            return ext::shared_ptr<Callability>(ext::make_shared<SoftCallability>(
                Bond::Price(amount, price_type), date, trigger));
        },
        nb::arg("amount"),
        nb::arg("price_type"),
        nb::arg("date"),
        nb::arg("trigger"),
        "Factory: SoftCallability (call with conversion trigger) → "
        "Callability.");

    nb::class_<ConvertibleZeroCouponBond>(m, "ConvertibleZeroCouponBond")
        .def(
            "__init__",
            [](ConvertibleZeroCouponBond* self,
               const EuropeanExercise& exercise,
               Real conversion_ratio,
               const CallabilitySchedule& callability,
               const Date& issue_date,
               Natural settlement_days,
               const DayCounter& day_counter,
               const Schedule& schedule,
               Real redemption) {
                new (self) ConvertibleZeroCouponBond(
                    ext::make_shared<EuropeanExercise>(exercise),
                    conversion_ratio,
                    callability,
                    issue_date,
                    settlement_days,
                    day_counter,
                    schedule,
                    redemption);
            },
            nb::arg("exercise"),
            nb::arg("conversion_ratio"),
            nb::arg("callability"),
            nb::arg("issue_date"),
            nb::arg("settlement_days"),
            nb::arg("day_counter"),
            nb::arg("schedule"),
            nb::arg("redemption") = 100.0)
        .def(
            "__init__",
            [](ConvertibleZeroCouponBond* self,
               const AmericanExercise& exercise,
               Real conversion_ratio,
               const CallabilitySchedule& callability,
               const Date& issue_date,
               Natural settlement_days,
               const DayCounter& day_counter,
               const Schedule& schedule,
               Real redemption) {
                new (self) ConvertibleZeroCouponBond(
                    ext::make_shared<AmericanExercise>(exercise),
                    conversion_ratio,
                    callability,
                    issue_date,
                    settlement_days,
                    day_counter,
                    schedule,
                    redemption);
            },
            nb::arg("exercise"),
            nb::arg("conversion_ratio"),
            nb::arg("callability"),
            nb::arg("issue_date"),
            nb::arg("settlement_days"),
            nb::arg("day_counter"),
            nb::arg("schedule"),
            nb::arg("redemption") = 100.0)
        .def("NPV", [](ConvertibleZeroCouponBond& b) { return b.NPV(); })
        .def("clean_price",
             [](ConvertibleZeroCouponBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](ConvertibleZeroCouponBond& b) { return b.dirtyPrice(); })
        .def("conversion_ratio",
             [](const ConvertibleZeroCouponBond& b) {
                 return b.conversionRatio();
             })
        .def("settlement_date",
             [](const ConvertibleZeroCouponBond& b) {
                 return b.settlementDate();
             })
        .def("maturity_date",
             [](const ConvertibleZeroCouponBond& b) { return b.maturityDate(); })
        .def(
            "set_binomial_pricing_engine",
            [](ConvertibleZeroCouponBond& b,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               const Handle<Quote>& credit_spread) {
                b.setPricingEngine(
                    ext::make_shared<BinomialConvertibleEngine<CoxRossRubinstein>>(
                        process, time_steps, credit_spread));
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("credit_spread"),
            "Attach BinomialConvertibleEngine<CoxRossRubinstein>.")
        .def(
            "set_binomial_pricing_engine",
            [](ConvertibleZeroCouponBond& b,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               Real credit_spread) {
                b.setPricingEngine(
                    ext::make_shared<BinomialConvertibleEngine<CoxRossRubinstein>>(
                        process,
                        time_steps,
                        Handle<Quote>(ext::make_shared<SimpleQuote>(credit_spread))));
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("credit_spread"),
            "Attach BinomialConvertibleEngine from a scalar credit spread.");

    nb::class_<ConvertibleFixedCouponBond>(m, "ConvertibleFixedCouponBond")
        .def(
            "__init__",
            [](ConvertibleFixedCouponBond* self,
               const EuropeanExercise& exercise,
               Real conversion_ratio,
               const CallabilitySchedule& callability,
               const Date& issue_date,
               Natural settlement_days,
               const std::vector<Rate>& coupons,
               const DayCounter& day_counter,
               const Schedule& schedule,
               Real redemption) {
                new (self) ConvertibleFixedCouponBond(
                    ext::make_shared<EuropeanExercise>(exercise),
                    conversion_ratio,
                    callability,
                    issue_date,
                    settlement_days,
                    coupons,
                    day_counter,
                    schedule,
                    redemption);
            },
            nb::arg("exercise"),
            nb::arg("conversion_ratio"),
            nb::arg("callability"),
            nb::arg("issue_date"),
            nb::arg("settlement_days"),
            nb::arg("coupons"),
            nb::arg("day_counter"),
            nb::arg("schedule"),
            nb::arg("redemption") = 100.0)
        .def(
            "__init__",
            [](ConvertibleFixedCouponBond* self,
               const AmericanExercise& exercise,
               Real conversion_ratio,
               const CallabilitySchedule& callability,
               const Date& issue_date,
               Natural settlement_days,
               const std::vector<Rate>& coupons,
               const DayCounter& day_counter,
               const Schedule& schedule,
               Real redemption) {
                new (self) ConvertibleFixedCouponBond(
                    ext::make_shared<AmericanExercise>(exercise),
                    conversion_ratio,
                    callability,
                    issue_date,
                    settlement_days,
                    coupons,
                    day_counter,
                    schedule,
                    redemption);
            },
            nb::arg("exercise"),
            nb::arg("conversion_ratio"),
            nb::arg("callability"),
            nb::arg("issue_date"),
            nb::arg("settlement_days"),
            nb::arg("coupons"),
            nb::arg("day_counter"),
            nb::arg("schedule"),
            nb::arg("redemption") = 100.0)
        .def("NPV", [](ConvertibleFixedCouponBond& b) { return b.NPV(); })
        .def("clean_price",
             [](ConvertibleFixedCouponBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](ConvertibleFixedCouponBond& b) { return b.dirtyPrice(); })
        .def("conversion_ratio",
             [](const ConvertibleFixedCouponBond& b) {
                 return b.conversionRatio();
             })
        .def("settlement_date",
             [](const ConvertibleFixedCouponBond& b) {
                 return b.settlementDate();
             })
        .def("maturity_date",
             [](const ConvertibleFixedCouponBond& b) { return b.maturityDate(); })
        .def(
            "set_binomial_pricing_engine",
            [](ConvertibleFixedCouponBond& b,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               const Handle<Quote>& credit_spread) {
                b.setPricingEngine(
                    ext::make_shared<BinomialConvertibleEngine<CoxRossRubinstein>>(
                        process, time_steps, credit_spread));
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("credit_spread"),
            "Attach BinomialConvertibleEngine<CoxRossRubinstein>.")
        .def(
            "set_binomial_pricing_engine",
            [](ConvertibleFixedCouponBond& b,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               Real credit_spread) {
                b.setPricingEngine(
                    ext::make_shared<BinomialConvertibleEngine<CoxRossRubinstein>>(
                        process,
                        time_steps,
                        Handle<Quote>(ext::make_shared<SimpleQuote>(credit_spread))));
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("credit_spread"),
            "Attach BinomialConvertibleEngine from a scalar credit spread.");

    nb::class_<ConvertibleFloatingRateBond>(m, "ConvertibleFloatingRateBond")
        .def(
            "__init__",
            [](ConvertibleFloatingRateBond* self,
               const EuropeanExercise& exercise,
               Real conversion_ratio,
               const CallabilitySchedule& callability,
               const Date& issue_date,
               Natural settlement_days,
               const ext::shared_ptr<IborIndex>& index,
               Natural fixing_days,
               const std::vector<Spread>& spreads,
               const DayCounter& day_counter,
               const Schedule& schedule,
               Real redemption) {
                const std::vector<Spread> ql_spreads =
                    spreads.empty() ? std::vector<Spread>{0.0} : spreads;
                new (self) ConvertibleFloatingRateBond(
                    ext::make_shared<EuropeanExercise>(exercise),
                    conversion_ratio,
                    callability,
                    issue_date,
                    settlement_days,
                    index,
                    fixing_days,
                    ql_spreads,
                    day_counter,
                    schedule,
                    redemption);
            },
            nb::arg("exercise"),
            nb::arg("conversion_ratio"),
            nb::arg("callability"),
            nb::arg("issue_date"),
            nb::arg("settlement_days"),
            nb::arg("index"),
            nb::arg("fixing_days"),
            nb::arg("spreads"),
            nb::arg("day_counter"),
            nb::arg("schedule"),
            nb::arg("redemption") = 100.0)
        .def(
            "__init__",
            [](ConvertibleFloatingRateBond* self,
               const AmericanExercise& exercise,
               Real conversion_ratio,
               const CallabilitySchedule& callability,
               const Date& issue_date,
               Natural settlement_days,
               const ext::shared_ptr<IborIndex>& index,
               Natural fixing_days,
               const std::vector<Spread>& spreads,
               const DayCounter& day_counter,
               const Schedule& schedule,
               Real redemption) {
                const std::vector<Spread> ql_spreads =
                    spreads.empty() ? std::vector<Spread>{0.0} : spreads;
                new (self) ConvertibleFloatingRateBond(
                    ext::make_shared<AmericanExercise>(exercise),
                    conversion_ratio,
                    callability,
                    issue_date,
                    settlement_days,
                    index,
                    fixing_days,
                    ql_spreads,
                    day_counter,
                    schedule,
                    redemption);
            },
            nb::arg("exercise"),
            nb::arg("conversion_ratio"),
            nb::arg("callability"),
            nb::arg("issue_date"),
            nb::arg("settlement_days"),
            nb::arg("index"),
            nb::arg("fixing_days"),
            nb::arg("spreads"),
            nb::arg("day_counter"),
            nb::arg("schedule"),
            nb::arg("redemption") = 100.0)
        .def("NPV", [](ConvertibleFloatingRateBond& b) { return b.NPV(); })
        .def("clean_price",
             [](ConvertibleFloatingRateBond& b) { return b.cleanPrice(); })
        .def("dirty_price",
             [](ConvertibleFloatingRateBond& b) { return b.dirtyPrice(); })
        .def("conversion_ratio",
             [](const ConvertibleFloatingRateBond& b) {
                 return b.conversionRatio();
             })
        .def("settlement_date",
             [](const ConvertibleFloatingRateBond& b) {
                 return b.settlementDate();
             })
        .def("maturity_date",
             [](const ConvertibleFloatingRateBond& b) { return b.maturityDate(); })
        .def(
            "set_binomial_pricing_engine",
            [](ConvertibleFloatingRateBond& b,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               const Handle<Quote>& credit_spread) {
                b.setPricingEngine(
                    ext::make_shared<BinomialConvertibleEngine<CoxRossRubinstein>>(
                        process, time_steps, credit_spread));
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("credit_spread"),
            "Attach BinomialConvertibleEngine<CoxRossRubinstein>.")
        .def(
            "set_binomial_pricing_engine",
            [](ConvertibleFloatingRateBond& b,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size time_steps,
               Real credit_spread) {
                b.setPricingEngine(
                    ext::make_shared<BinomialConvertibleEngine<CoxRossRubinstein>>(
                        process,
                        time_steps,
                        Handle<Quote>(ext::make_shared<SimpleQuote>(credit_spread))));
            },
            nb::arg("process"),
            nb::arg("time_steps"),
            nb::arg("credit_spread"),
            "Attach BinomialConvertibleEngine from a scalar credit spread.");

    m.def(
        "BinomialConvertibleEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process,
           Size time_steps,
           const Handle<Quote>& credit_spread) {
            return process;
        },
        nb::arg("process"),
        nb::arg("time_steps"),
        nb::arg("credit_spread"),
        "Documentation alias — use "
        "ConvertibleZeroCouponBond / ConvertibleFixedCouponBond / "
        "ConvertibleFloatingRateBond.set_binomial_pricing_engine instead.");
}
