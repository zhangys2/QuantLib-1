#include "bindings.hpp"

#include <nanobind/ndarray.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/cashflows/dividend.hpp>
#include <ql/exercise.hpp>
#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/instruments/dividendschedule.hpp>
#include <ql/methods/finitedifferences/utilities/fdmquantohelper.hpp>
#include <ql/instruments/bondforward.hpp>
#include <ql/instruments/bonds/fixedratebond.hpp>
#include <ql/instruments/forwardrateagreement.hpp>
#include <ql/instruments/payoffs.hpp>
#include <ql/instruments/vanillaoption.hpp>
#include <ql/math/randomnumbers/rngtraits.hpp>
#include <ql/methods/finitedifferences/meshers/fdmblackscholesmesher.hpp>
#include <ql/methods/finitedifferences/meshers/fdmmeshercomposite.hpp>
#include <ql/methods/finitedifferences/meshers/uniform1dmesher.hpp>
#include <ql/methods/finitedifferences/solvers/fdmblackscholessolver.hpp>
#include <ql/methods/finitedifferences/stepconditions/fdmstepconditioncomposite.hpp>
#include <ql/methods/finitedifferences/utilities/fdminnervaluecalculator.hpp>
#include <ql/methods/lattices/binomialtree.hpp>
#include <ql/methods/montecarlo/pathgenerator.hpp>
#include <ql/position.hpp>
#include <ql/models/equity/batesmodel.hpp>
#include <ql/models/equity/hestonmodel.hpp>
#include <ql/pricingengines/vanilla/analyticdigitalamericanengine.hpp>
#include <ql/pricingengines/vanilla/analyticdividendeuropeanengine.hpp>
#include <ql/pricingengines/vanilla/analytichestonengine.hpp>
#include <ql/pricingengines/vanilla/baroneadesiwhaleyengine.hpp>
#include <ql/pricingengines/vanilla/batesengine.hpp>
#include <ql/pricingengines/vanilla/binomialengine.hpp>
#include <ql/pricingengines/vanilla/cashdividendeuropeanengine.hpp>
#include <ql/pricingengines/vanilla/coshestonengine.hpp>
#include <ql/pricingengines/vanilla/exponentialfittinghestonengine.hpp>
#include <ql/pricingengines/vanilla/fdblackscholesvanillaengine.hpp>
#include <ql/pricingengines/vanilla/fdbatesvanillaengine.hpp>
#include <ql/pricingengines/vanilla/fdhestonvanillaengine.hpp>
#include <ql/pricingengines/vanilla/mceuropeanhestonengine.hpp>
#include <ql/utilities/null.hpp>

#include <nanobind/stl/optional.h>

#include <optional>
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/processes/hestonprocess.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/date.hpp>

#include <cmath>
#include <cstdint>
#include <utility>
#include <vector>

using namespace QuantLib;

namespace {

using PathArray = nb::ndarray<nb::numpy, double, nb::ndim<2>>;
using MeshArray = nb::ndarray<nb::numpy, double, nb::ndim<1>>;
using GridArray = nb::ndarray<nb::numpy, double, nb::ndim<2>>;

PathArray simulate_gbm_paths(
    const ext::shared_ptr<BlackScholesMertonProcess>& process,
    Time length,
    Size time_steps,
    Size samples,
    unsigned long seed) {
    QL_REQUIRE(process, "null process");
    QL_REQUIRE(length > 0.0, "non-positive path length");
    QL_REQUIRE(time_steps > 0, "time_steps must be positive");
    QL_REQUIRE(samples > 0, "samples must be positive");

    using rsg_type = PseudoRandom::rsg_type;
    rsg_type rsg = PseudoRandom::make_sequence_generator(time_steps, seed);
    PathGenerator<rsg_type> generator(
        process, length, time_steps, rsg, /*brownianBridge=*/false);

    const size_t cols = static_cast<size_t>(time_steps) + 1;
    auto* data = new double[static_cast<size_t>(samples) * cols];
    for (Size i = 0; i < samples; ++i) {
        const Path& path = generator.next().value;
        QL_REQUIRE(path.length() == cols, "unexpected path length");
        for (Size j = 0; j < cols; ++j) {
            data[static_cast<size_t>(i) * cols + static_cast<size_t>(j)] =
                path[j];
        }
    }

    nb::capsule owner(data, [](void* p) noexcept {
        delete[] static_cast<double*>(p);
    });
    return PathArray(data, {static_cast<size_t>(samples), cols}, owner);
}

MeshArray locations_to_numpy(const std::vector<Real>& locations) {
    const size_t n = locations.size();
    auto* data = new double[n];
    for (size_t i = 0; i < n; ++i)
        data[i] = locations[i];
    nb::capsule owner(data, [](void* p) noexcept {
        delete[] static_cast<double*>(p);
    });
    return MeshArray(data, {n}, owner);
}

MeshArray locations_to_numpy(const Array& locations) {
    const size_t n = locations.size();
    auto* data = new double[n];
    for (size_t i = 0; i < n; ++i)
        data[i] = locations[i];
    nb::capsule owner(data, [](void* p) noexcept {
        delete[] static_cast<double*>(p);
    });
    return MeshArray(data, {n}, owner);
}

MeshArray uniform_1d_mesher_locations(Real start, Real end, Size size) {
    Uniform1dMesher mesher(start, end, size);
    return locations_to_numpy(mesher.locations());
}

MeshArray fdm_black_scholes_mesher_locations(
    Size size,
    const ext::shared_ptr<BlackScholesMertonProcess>& process,
    Time maturity,
    Real strike) {
    QL_REQUIRE(process, "null process");
    auto mesher = ext::make_shared<FdmBlackScholesMesher>(
        size, process, maturity, strike);
    // Composite exposes the 1D locations along direction 0.
    FdmMesherComposite composite(mesher);
    return locations_to_numpy(composite.locations(0));
}

GridArray fdm_black_scholes_values(
    const ext::shared_ptr<BlackScholesMertonProcess>& process,
    Real strike,
    Time maturity,
    Option::Type option_type,
    Size t_grid,
    Size x_grid,
    Size damping_steps) {
    QL_REQUIRE(process, "null process");
    QL_REQUIRE(maturity > 0.0, "non-positive maturity");
    QL_REQUIRE(t_grid > 0 && x_grid > 1, "invalid FD grid sizes");

    const Date today = process->riskFreeRate()->referenceDate();
    const DayCounter dc = process->riskFreeRate()->dayCounter();
    // Map the requested maturity onto a calendar date so exercise stopping
    // times and the PDE horizon stay consistent.
    const Date exercise_date = today + Integer(std::lround(maturity * 365.0));
    const Time T = process->time(exercise_date);
    QL_REQUIRE(T > 0.0, "exercise date must be after the process reference");

    auto payoff = ext::make_shared<PlainVanillaPayoff>(option_type, strike);
    auto equity_mesher =
        ext::make_shared<FdmBlackScholesMesher>(x_grid, process, T, strike);
    auto mesher = ext::make_shared<FdmMesherComposite>(equity_mesher);
    auto calculator = ext::make_shared<FdmLogInnerValue>(payoff, mesher, 0);
    auto exercise = ext::make_shared<EuropeanExercise>(exercise_date);

    auto conditions = FdmStepConditionComposite::vanillaComposite(
        DividendSchedule(), exercise, mesher, calculator, today, dc);

    FdmSolverDesc solver_desc = {mesher,
                                 FdmBoundaryConditionSet(),
                                 conditions,
                                 calculator,
                                 T,
                                 t_grid,
                                 damping_steps};

    auto solver = ext::make_shared<FdmBlackScholesSolver>(
        Handle<GeneralizedBlackScholesProcess>(process),
        strike,
        solver_desc);

    const Array ln_s = mesher->locations(0);
    const size_t n = ln_s.size();
    auto* data = new double[n * 2];
    for (size_t i = 0; i < n; ++i) {
        const Real spot = std::exp(ln_s[i]);
        data[i * 2] = spot;
        data[i * 2 + 1] = solver->valueAt(spot);
    }
    nb::capsule owner(data, [](void* p) noexcept {
        delete[] static_cast<double*>(p);
    });
    return GridArray(data, {n, static_cast<size_t>(2)}, owner);
}

} // namespace

void bind_pricing(nb::module_& m) {
    nb::class_<AmericanExercise>(m, "AmericanExercise")
        .def(nb::init<const Date&, const Date&, bool>(),
             nb::arg("earliest_date"),
             nb::arg("latest_date"),
             nb::arg("payoff_at_expiry") = false)
        .def(nb::init<const Date&, bool>(),
             nb::arg("latest_date"),
             nb::arg("payoff_at_expiry") = false)
        .def("last_date",
             [](const AmericanExercise& e) { return e.lastDate(); });

    // Standalone VanillaOption — American (BAW default) plus tree/FD engines.
    // Not declared as a Python subclass of Instrument/OneAssetOption (MI).
    nb::class_<VanillaOption>(m, "VanillaOption")
        .def(
            "__init__",
            [](VanillaOption* self,
               const PlainVanillaPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) VanillaOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](VanillaOption* self,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) VanillaOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](VanillaOption* self,
               const PlainVanillaPayoff& payoff,
               const BermudanExercise& exercise) {
                new (self) VanillaOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<BermudanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Vanilla option with Bermudan exercise (FD / tree engines).")
        .def(
            "__init__",
            [](VanillaOption* self,
               const CashOrNothingPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) VanillaOption(
                    ext::make_shared<CashOrNothingPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "American digital cash-or-nothing vanilla.")
        .def(
            "__init__",
            [](VanillaOption* self,
               const AssetOrNothingPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) VanillaOption(
                    ext::make_shared<AssetOrNothingPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "American digital asset-or-nothing vanilla.")
        .def("NPV", [](VanillaOption& opt) { return opt.NPV(); })
        .def("error_estimate",
             [](VanillaOption& opt) { return opt.errorEstimate(); })
        .def("delta", [](VanillaOption& opt) { return opt.delta(); })
        .def("gamma", [](VanillaOption& opt) { return opt.gamma(); })
        .def("vega", [](VanillaOption& opt) { return opt.vega(); })
        .def(
            "set_pricing_engine",
            [](VanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<BaroneAdesiWhaleyApproximationEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach Barone-Adesi-Whaley approximation engine (American).")
        .def(
            "set_digital_american_pricing_engine",
            [](VanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticDigitalAmericanEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticDigitalAmericanEngine (cash/asset digital American).")
        .def(
            "set_digital_american_ko_pricing_engine",
            [](VanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticDigitalAmericanKOEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticDigitalAmericanKOEngine (knock-out digital American).")
        .def(
            "set_dividend_pricing_engine",
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            "set_binomial_pricing_engine",
            [](VanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size steps) {
                opt.setPricingEngine(
                    ext::make_shared<BinomialVanillaEngine<CoxRossRubinstein>>(
                        process, steps));
            },
            nb::arg("process"),
            nb::arg("steps") = 801,
            "Attach Cox-Ross-Rubinstein binomial tree engine.")
        .def(
            "set_fd_pricing_engine",
            [](VanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size t_grid,
               Size x_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdBlackScholesVanillaEngine>(
                    process, t_grid, x_grid, damping_steps, scheme_desc));
            },
            nb::arg("process"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdBlackScholesVanillaEngine (default Douglas scheme).")
        .def(
            "set_fd_dividend_pricing_engine",
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            "set_heston_pricing_engine",
            [](VanillaOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               Size integration_order) {
                opt.setPricingEngine(ext::make_shared<AnalyticHestonEngine>(
                    model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach AnalyticHestonEngine (Laguerre / Gatheral).")
        .def(
            "set_mc_heston_pricing_engine",
            [](VanillaOption& opt,
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
            "set_cos_heston_pricing_engine",
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
            [](VanillaOption& opt,
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
        "BaroneAdesiWhaleyEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to VanillaOption.set_pricing_engine.");

    m.def(
        "AnalyticDigitalAmericanEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "VanillaOption.set_digital_american_pricing_engine.");

    m.def(
        "AnalyticDigitalAmericanKOEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "VanillaOption.set_digital_american_ko_pricing_engine.");

    nb::enum_<Position::Type>(m, "Position")
        .value("Long", Position::Long)
        .value("Short", Position::Short);

    // ForwardRateAgreement is MI-heavy via Instrument/LazyObject — standalone.
    nb::class_<ForwardRateAgreement>(m, "ForwardRateAgreement")
        .def(
            "__init__",
            [](ForwardRateAgreement* self,
               const ext::shared_ptr<IborIndex>& index,
               const Date& value_date,
               Position::Type type,
               Rate strike_forward_rate,
               Real notional_amount,
               const Handle<YieldTermStructure>& discount_curve) {
                new (self) ForwardRateAgreement(index,
                                                value_date,
                                                type,
                                                strike_forward_rate,
                                                notional_amount,
                                                discount_curve);
            },
            nb::arg("index"),
            nb::arg("value_date"),
            nb::arg("type"),
            nb::arg("strike_forward_rate"),
            nb::arg("notional_amount"),
            nb::arg("discount_curve") = Handle<YieldTermStructure>())
        .def(
            "__init__",
            [](ForwardRateAgreement* self,
               const ext::shared_ptr<IborIndex>& index,
               const Date& value_date,
               const Date& maturity_date,
               Position::Type type,
               Rate strike_forward_rate,
               Real notional_amount,
               const Handle<YieldTermStructure>& discount_curve) {
                new (self) ForwardRateAgreement(index,
                                                value_date,
                                                maturity_date,
                                                type,
                                                strike_forward_rate,
                                                notional_amount,
                                                discount_curve);
            },
            nb::arg("index"),
            nb::arg("value_date"),
            nb::arg("maturity_date"),
            nb::arg("type"),
            nb::arg("strike_forward_rate"),
            nb::arg("notional_amount"),
            nb::arg("discount_curve") = Handle<YieldTermStructure>())
        .def("NPV", [](ForwardRateAgreement& fra) { return fra.NPV(); })
        .def("amount", [](const ForwardRateAgreement& fra) { return fra.amount(); })
        .def("forward_rate",
             [](const ForwardRateAgreement& fra) { return fra.forwardRate(); })
        .def("fixing_date",
             [](const ForwardRateAgreement& fra) { return fra.fixingDate(); });

    // BondForward is Forward/Instrument (MI via LazyObject) — standalone wrapper.
    // Underlying FixedRateBond is copied into a shared_ptr; price it first.
    nb::class_<BondForward>(m, "BondForward")
        .def(
            "__init__",
            [](BondForward* self,
               const Date& value_date,
               const Date& maturity_date,
               Position::Type type,
               Real strike,
               Natural settlement_days,
               const DayCounter& day_counter,
               const Calendar& calendar,
               BusinessDayConvention business_day_convention,
               const FixedRateBond& bond,
               const Handle<YieldTermStructure>& discount_curve,
               const Handle<YieldTermStructure>& income_discount_curve) {
                new (self) BondForward(value_date,
                                       maturity_date,
                                       type,
                                       strike,
                                       settlement_days,
                                       day_counter,
                                       calendar,
                                       business_day_convention,
                                       ext::make_shared<FixedRateBond>(bond),
                                       discount_curve,
                                       income_discount_curve);
            },
            nb::arg("value_date"),
            nb::arg("maturity_date"),
            nb::arg("type"),
            nb::arg("strike"),
            nb::arg("settlement_days"),
            nb::arg("day_counter"),
            nb::arg("calendar"),
            nb::arg("business_day_convention"),
            nb::arg("bond"),
            nb::arg("discount_curve") = Handle<YieldTermStructure>(),
            nb::arg("income_discount_curve") = Handle<YieldTermStructure>())
        .def("NPV", [](BondForward& f) { return f.NPV(); })
        .def("is_expired", [](const BondForward& f) { return f.isExpired(); })
        .def("clean_forward_price",
             [](BondForward& f) { return f.cleanForwardPrice(); })
        .def("forward_price", [](BondForward& f) { return f.forwardPrice(); })
        .def("forward_value", [](BondForward& f) { return f.forwardValue(); })
        .def("spot_value", [](const BondForward& f) { return f.spotValue(); })
        .def(
            "spot_income",
            [](const BondForward& f,
               const Handle<YieldTermStructure>& income_discount_curve) {
                return f.spotIncome(income_discount_curve);
            },
            nb::arg("income_discount_curve"))
        .def("settlement_date",
             [](const BondForward& f) { return f.settlementDate(); });

    m.def("simulate_gbm_paths",
          &simulate_gbm_paths,
          nb::arg("process"),
          nb::arg("length"),
          nb::arg("time_steps"),
          nb::arg("samples"),
          nb::arg("seed") = 42UL,
          "Simulate GBM paths under a BlackScholesMertonProcess.\n"
          "Returns a NumPy array of shape (samples, time_steps+1).");

    m.def("uniform_1d_mesher_locations",
          &uniform_1d_mesher_locations,
          nb::arg("start"),
          nb::arg("end"),
          nb::arg("size"),
          "Return Uniform1dMesher locations as a NumPy 1-D array.");

    m.def("fdm_black_scholes_mesher_locations",
          &fdm_black_scholes_mesher_locations,
          nb::arg("size"),
          nb::arg("process"),
          nb::arg("maturity"),
          nb::arg("strike"),
          "Return FdmBlackScholesMesher (ln-S) locations as a NumPy 1-D array.");

    m.def("fdm_black_scholes_values",
          &fdm_black_scholes_values,
          nb::arg("process"),
          nb::arg("strike"),
          nb::arg("maturity"),
          nb::arg("option_type") = Option::Call,
          nb::arg("t_grid") = 100,
          nb::arg("x_grid") = 100,
          nb::arg("damping_steps") = 0,
          "Solve a European vanilla on an FD Black–Scholes grid and return a "
          "NumPy array of shape (x_grid, 2) with columns [spot, value].");
}
