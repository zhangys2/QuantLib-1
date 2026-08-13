#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/cashflows/couponpricer.hpp>
#include <ql/cashflows/dividend.hpp>
#include <ql/exercise.hpp>
#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/methods/finitedifferences/utilities/fdmquantohelper.hpp>
#include <ql/instruments/bonds/fixedratebond.hpp>
#include <ql/instruments/bonds/floatingratebond.hpp>
#include <ql/instruments/bonds/zerocouponbond.hpp>
#include <ql/instruments/dividendschedule.hpp>
#include <ql/instruments/europeanoption.hpp>
#include <ql/instruments/payoffs.hpp>
#include <ql/instruments/swap.hpp>
#include <ql/instruments/vanillaswap.hpp>
#include <ql/option.hpp>
#include <ql/pricingengines/bond/discountingbondengine.hpp>
#include <ql/pricingengines/swap/discountingswapengine.hpp>
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
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/termstructures/volatility/equityfx/blackconstantvol.hpp>
#include <ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/daycounter.hpp>
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
        .def("NPV", [](EuropeanOption& opt) { return opt.NPV(); })
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
    nb::class_<FixedRateBond>(m, "FixedRateBond")
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

    // Zero-coupon bond (standalone; Bond/Instrument use MI via LazyObject).
    nb::class_<ZeroCouponBond>(m, "ZeroCouponBond")
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

    // Floating-rate bond (standalone; Bond/Instrument use MI via LazyObject).
    // set_pricing_engine attaches DiscountingBondEngine and a BlackIborCouponPricer.
    nb::class_<FloatingRateBond>(m, "FloatingRateBond")
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
}
