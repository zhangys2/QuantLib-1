#include "bindings.hpp"

#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <limits>
#include <optional>

#include <ql/cashflows/dividend.hpp>
#include <ql/cashflows/iborcoupon.hpp>
#include <ql/exercise.hpp>
#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/instruments/asianoption.hpp>
#include <ql/instruments/averagetype.hpp>
#include <ql/instruments/barrieroption.hpp>
#include <ql/instruments/barriertype.hpp>
#include <ql/instruments/basketoption.hpp>
#include <ql/instruments/capfloor.hpp>
#include <ql/instruments/cliquetoption.hpp>
#include <ql/instruments/complexchooseroption.hpp>
#include <ql/instruments/compoundoption.hpp>
#include <ql/instruments/doublebarrieroption.hpp>
#include <ql/experimental/forward/analytichestonforwardeuropeanengine.hpp>
#include <ql/instruments/forwardvanillaoption.hpp>
#include <ql/instruments/doublebarriertype.hpp>
#include <ql/instruments/lookbackoption.hpp>
#include <ql/instruments/makecapfloor.hpp>
#include <ql/instruments/margrabeoption.hpp>
#include <ql/instruments/partialtimebarrieroption.hpp>
#include <ql/instruments/holderextensibleoption.hpp>
#include <ql/instruments/simplechooseroption.hpp>
#include <ql/instruments/payoffs.hpp>
#include <ql/instruments/quantobarrieroption.hpp>
#include <ql/experimental/barrieroption/mcdoublebarrierengine.hpp>
#include <ql/experimental/barrieroption/perturbativebarrieroptionengine.hpp>
#include <ql/experimental/barrieroption/quantodoublebarrieroption.hpp>
#include <ql/experimental/barrieroption/suowangdoublebarrierengine.hpp>
#include <ql/experimental/barrieroption/vannavolgabarrierengine.hpp>
#include <ql/quotes/deltavolquote.hpp>
#include <ql/instruments/softbarrieroption.hpp>
#include <ql/instruments/twoassetbarrieroption.hpp>
#include <ql/instruments/twoassetcorrelationoption.hpp>
#include <ql/experimental/varianceoption/integralhestonvarianceoptionengine.hpp>
#include <ql/experimental/varianceoption/varianceoption.hpp>
#include <ql/instruments/varianceswap.hpp>
#include <ql/instruments/writerextensibleoption.hpp>
#include <ql/experimental/exoticoptions/himalayaoption.hpp>
#include <ql/experimental/exoticoptions/mchimalayaengine.hpp>
#include <ql/experimental/exoticoptions/pagodaoption.hpp>
#include <ql/experimental/exoticoptions/mcpagodaengine.hpp>
#include <ql/experimental/exoticoptions/everestoption.hpp>
#include <ql/experimental/exoticoptions/mceverestengine.hpp>
#include <ql/experimental/finitedifferences/fdsimpleextoustorageengine.hpp>
#include <ql/experimental/processes/extendedornsteinuhlenbeckprocess.hpp>
#include <ql/models/equity/hestonmodel.hpp>
#include <ql/option.hpp>
#include <ql/quotes/simplequote.hpp>
#include <ql/pricingengines/asian/analytic_cont_geom_av_price.hpp>
#include <ql/pricingengines/asian/analytic_discr_geom_av_price.hpp>
#include <ql/pricingengines/asian/continuousarithmeticasianlevyengine.hpp>
#include <ql/pricingengines/asian/turnbullwakemanasianengine.hpp>
#include <ql/experimental/asian/analytic_cont_geom_av_price_heston.hpp>
#include <ql/experimental/asian/analytic_discr_geom_av_price_heston.hpp>
#include <ql/experimental/exoticoptions/continuousarithmeticasianvecerengine.hpp>
#include <ql/processes/hestonprocess.hpp>
#include <ql/pricingengines/barrier/analyticbarrierengine.hpp>
#include <ql/pricingengines/barrier/analyticbinarybarrierengine.hpp>
#include <ql/pricingengines/barrier/analyticdoublebarrierbinaryengine.hpp>
#include <ql/pricingengines/barrier/analyticdoublebarrierengine.hpp>
#include <ql/pricingengines/barrier/analyticpartialtimebarrieroptionengine.hpp>
#include <ql/pricingengines/barrier/analyticsoftbarrierengine.hpp>
#include <ql/pricingengines/barrier/analytictwoassetbarrierengine.hpp>
#include <ql/pricingengines/barrier/fdblackscholesbarrierengine.hpp>
#include <ql/pricingengines/barrier/fdhestondoublebarrierengine.hpp>
#include <ql/pricingengines/barrier/fdhestonbarrierengine.hpp>
#include <ql/pricingengines/barrier/mcbarrierengine.hpp>
#include <ql/pricingengines/basket/bjerksundstenslandspreadengine.hpp>
#include <ql/pricingengines/basket/choibasketengine.hpp>
#include <ql/pricingengines/basket/denglizhoubasketengine.hpp>
#include <ql/pricingengines/basket/fd2dblackscholesvanillaengine.hpp>
#include <ql/pricingengines/basket/fdndimblackscholesvanillaengine.hpp>
#include <ql/pricingengines/basket/gaussiancopulaspreadengine.hpp>
#include <ql/pricingengines/basket/kirkengine.hpp>
#include <ql/pricingengines/basket/mcamericanbasketengine.hpp>
#include <ql/pricingengines/basket/mceuropeanbasketengine.hpp>
#include <ql/pricingengines/basket/operatorsplittingspreadengine.hpp>
#include <ql/pricingengines/basket/pearsonspreadengine.hpp>
#include <ql/pricingengines/basket/singlefactorbsmbasketengine.hpp>
#include <ql/pricingengines/basket/stulzengine.hpp>
#include <ql/pricingengines/quanto/quantoengine.hpp>
#include <ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp>
#include <ql/termstructures/volatility/equityfx/blackvariancecurve.hpp>
#include <ql/termstructures/volatility/equityfx/blackvariancesurface.hpp>
#include <ql/pricingengines/cliquet/analyticcliquetengine.hpp>
#include <ql/pricingengines/exotic/analyticamericanmargrabeengine.hpp>
#include <ql/pricingengines/exotic/analyticcomplexchooserengine.hpp>
#include <ql/pricingengines/exotic/analyticcompoundoptionengine.hpp>
#include <ql/pricingengines/exotic/analyticeuropeanmargrabeengine.hpp>
#include <ql/pricingengines/exotic/analyticholderextensibleoptionengine.hpp>
#include <ql/pricingengines/exotic/analyticsimplechooserengine.hpp>
#include <ql/pricingengines/exotic/analytictwoassetcorrelationengine.hpp>
#include <ql/pricingengines/exotic/analyticwriterextensibleoptionengine.hpp>
#include <ql/pricingengines/forward/mcvarianceswapengine.hpp>
#include <ql/pricingengines/forward/replicatingvarianceswapengine.hpp>
#include <ql/pricingengines/forward/forwardengine.hpp>
#include <ql/pricingengines/forward/forwardperformanceengine.hpp>
#include <ql/pricingengines/vanilla/analyticeuropeanengine.hpp>
#include <ql/pricingengines/capfloor/blackcapfloorengine.hpp>
#include <ql/pricingengines/lookback/analyticcontinuousfixedlookback.hpp>
#include <ql/pricingengines/lookback/analyticcontinuousfloatinglookback.hpp>
#include <ql/pricingengines/lookback/analyticcontinuouspartialfixedlookback.hpp>
#include <ql/pricingengines/lookback/analyticcontinuouspartialfloatinglookback.hpp>
#include <ql/pricingengines/lookback/mclookbackengine.hpp>
#include <ql/processes/blackscholesprocess.hpp>
#include <ql/processes/stochasticprocessarray.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/date.hpp>
#include <ql/time/calendar.hpp>
#include <ql/time/daycounter.hpp>
#include <ql/time/daycounters/actual365fixed.hpp>
#include <ql/time/period.hpp>
#include <ql/time/schedule.hpp>

using namespace QuantLib;

namespace {

std::vector<ext::shared_ptr<GeneralizedBlackScholesProcess>> to_gbs_processes(
    const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>& processes) {
    std::vector<ext::shared_ptr<GeneralizedBlackScholesProcess>> out;
    out.reserve(processes.size());
    for (const auto& p : processes)
        out.push_back(p);
    return out;
}

ext::shared_ptr<StochasticProcessArray> to_process_array(
    const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>& processes,
    const Matrix& rho) {
    QL_REQUIRE(!processes.empty(), "no processes given");
    std::vector<ext::shared_ptr<StochasticProcess1D>> procs;
    procs.reserve(processes.size());
    for (const auto& p : processes)
        procs.push_back(p);
    return ext::make_shared<StochasticProcessArray>(procs, rho);
}

template <class Option>
void attach_mc_lookback_engine(
    Option& opt,
    const ext::shared_ptr<BlackScholesMertonProcess>& process,
    std::optional<Size> time_steps,
    std::optional<Size> steps_per_year,
    std::optional<Size> required_samples,
    std::optional<Real> required_tolerance,
    unsigned long seed,
    bool antithetic,
    bool brownian_bridge) {
    QL_REQUIRE(!(time_steps.has_value() && steps_per_year.has_value()),
               "set only one of time_steps or steps_per_year");
    QL_REQUIRE(
        !(required_samples.has_value() && required_tolerance.has_value()),
        "set only one of required_samples or required_tolerance");
    auto maker = MakeMCLookbackEngine<Option, PseudoRandom>(process)
                     .withSeed(seed)
                     .withAntitheticVariate(antithetic)
                     .withBrownianBridge(brownian_bridge);
    if (time_steps.has_value())
        maker.withSteps(*time_steps);
    else if (steps_per_year.has_value())
        maker.withStepsPerYear(*steps_per_year);
    else
        maker.withSteps(Size(200));
    if (required_samples.has_value())
        maker.withSamples(*required_samples);
    else if (required_tolerance.has_value())
        maker.withAbsoluteTolerance(*required_tolerance);
    else
        maker.withSamples(Size(8192));
    opt.setPricingEngine(maker);
}

void attach_mc_double_barrier_engine(
    DoubleBarrierOption& opt,
    const ext::shared_ptr<BlackScholesMertonProcess>& process,
    std::optional<Size> time_steps,
    std::optional<Size> steps_per_year,
    std::optional<Size> required_samples,
    std::optional<Real> required_tolerance,
    unsigned long seed,
    bool antithetic,
    bool brownian_bridge) {
    QL_REQUIRE(!(time_steps.has_value() && steps_per_year.has_value()),
               "set only one of time_steps or steps_per_year");
    QL_REQUIRE(
        !(required_samples.has_value() && required_tolerance.has_value()),
        "set only one of required_samples or required_tolerance");
    auto maker = MakeMCDoubleBarrierEngine<PseudoRandom>(process)
                     .withSeed(seed)
                     .withAntitheticVariate(antithetic)
                     .withBrownianBridge(brownian_bridge);
    if (time_steps.has_value())
        maker.withSteps(*time_steps);
    else if (steps_per_year.has_value())
        maker.withStepsPerYear(*steps_per_year);
    else
        maker.withSteps(Size(200));
    if (required_samples.has_value())
        maker.withSamples(*required_samples);
    else if (required_tolerance.has_value())
        maker.withAbsoluteTolerance(*required_tolerance);
    else
        maker.withSamples(Size(8192));
    opt.setPricingEngine(maker);
}

void attach_mc_barrier_engine(
    BarrierOption& opt,
    const ext::shared_ptr<BlackScholesMertonProcess>& process,
    std::optional<Size> time_steps,
    std::optional<Size> steps_per_year,
    std::optional<Size> required_samples,
    std::optional<Real> required_tolerance,
    unsigned long seed,
    bool antithetic,
    bool brownian_bridge,
    bool biased) {
    QL_REQUIRE(!(time_steps.has_value() && steps_per_year.has_value()),
               "set only one of time_steps or steps_per_year");
    QL_REQUIRE(
        !(required_samples.has_value() && required_tolerance.has_value()),
        "set only one of required_samples or required_tolerance");
    auto maker = MakeMCBarrierEngine<PseudoRandom>(process)
                     .withSeed(seed)
                     .withAntitheticVariate(antithetic)
                     .withBrownianBridge(brownian_bridge)
                     .withBias(biased);
    if (time_steps.has_value())
        maker.withSteps(*time_steps);
    else if (steps_per_year.has_value())
        maker.withStepsPerYear(*steps_per_year);
    else
        maker.withSteps(Size(200));
    if (required_samples.has_value())
        maker.withSamples(*required_samples);
    else if (required_tolerance.has_value())
        maker.withAbsoluteTolerance(*required_tolerance);
    else
        maker.withSamples(Size(8192));
    opt.setPricingEngine(maker);
}

} // namespace

void bind_experimental(nb::module_& m) {
    // --- Barrier options (standalone; OneAssetOption uses MI) ---------------
    nb::enum_<Barrier::Type>(m, "BarrierType")
        .value("DownIn", Barrier::DownIn)
        .value("UpIn", Barrier::UpIn)
        .value("DownOut", Barrier::DownOut)
        .value("UpOut", Barrier::UpOut);

    // --- Asian options (standalone; OneAssetOption uses MI) -----------------
    nb::enum_<Average::Type>(m, "AverageType")
        .value("Arithmetic", Average::Arithmetic)
        .value("Geometric", Average::Geometric);

    nb::class_<ContinuousAveragingAsianOption>(m, "ContinuousAveragingAsianOption")
        .def(
            "__init__",
            [](ContinuousAveragingAsianOption* self,
               Average::Type average_type,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ContinuousAveragingAsianOption(
                    average_type,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("average_type"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](ContinuousAveragingAsianOption* self,
               Average::Type average_type,
               const Date& start_date,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ContinuousAveragingAsianOption(
                    average_type,
                    start_date,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("average_type"),
            nb::arg("start_date"),
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Seasoned continuous Asian (averaging already started).")
        .def("NPV",
             [](ContinuousAveragingAsianOption& opt) { return opt.NPV(); })
        .def("delta",
             [](ContinuousAveragingAsianOption& opt) { return opt.delta(); })
        .def("gamma",
             [](ContinuousAveragingAsianOption& opt) { return opt.gamma(); })
        .def(
            "set_pricing_engine",
            [](ContinuousAveragingAsianOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<
                        AnalyticContinuousGeometricAveragePriceAsianEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticContinuousGeometricAveragePriceAsianEngine.")
        .def(
            "set_heston_pricing_engine",
            [](ContinuousAveragingAsianOption& opt,
               const ext::shared_ptr<HestonProcess>& process,
               Size summation_cutoff,
               Real xi_right_limit) {
                opt.setPricingEngine(
                    ext::make_shared<
                        AnalyticContinuousGeometricAveragePriceAsianHestonEngine>(
                        process, summation_cutoff, xi_right_limit));
            },
            nb::arg("process"),
            nb::arg("summation_cutoff") = Size(50),
            nb::arg("xi_right_limit") = 100.0,
            "Attach AnalyticContinuousGeometricAveragePriceAsianHestonEngine.")
        .def(
            "set_vecer_pricing_engine",
            [](ContinuousAveragingAsianOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<Quote>& current_average,
               const Date& start_date,
               Size time_steps,
               Size asset_steps,
               Real z_min,
               Real z_max) {
                opt.setPricingEngine(
                    ext::make_shared<ContinuousArithmeticAsianVecerEngine>(
                        process,
                        current_average,
                        start_date,
                        time_steps,
                        asset_steps,
                        z_min,
                        z_max));
            },
            nb::arg("process"),
            nb::arg("current_average"),
            nb::arg("start_date"),
            nb::arg("time_steps") = Size(100),
            nb::arg("asset_steps") = Size(100),
            nb::arg("z_min") = -1.0,
            nb::arg("z_max") = 1.0,
            "Attach ContinuousArithmeticAsianVecerEngine.")
        .def(
            "set_levy_pricing_engine",
            [](ContinuousAveragingAsianOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<Quote>& current_average) {
                opt.setPricingEngine(
                    ext::make_shared<ContinuousArithmeticAsianLevyEngine>(
                        process, current_average));
            },
            nb::arg("process"),
            nb::arg("current_average"),
            "Attach ContinuousArithmeticAsianLevyEngine.");

    nb::class_<DiscreteAveragingAsianOption>(m, "DiscreteAveragingAsianOption")
        .def(
            "__init__",
            [](DiscreteAveragingAsianOption* self,
               Average::Type average_type,
               Real running_accumulator,
               Size past_fixings,
               const std::vector<Date>& fixing_dates,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) DiscreteAveragingAsianOption(
                    average_type,
                    running_accumulator,
                    past_fixings,
                    fixing_dates,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("average_type"),
            nb::arg("running_accumulator"),
            nb::arg("past_fixings"),
            nb::arg("fixing_dates"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV",
             [](DiscreteAveragingAsianOption& opt) { return opt.NPV(); })
        .def("delta",
             [](DiscreteAveragingAsianOption& opt) { return opt.delta(); })
        .def("gamma",
             [](DiscreteAveragingAsianOption& opt) { return opt.gamma(); })
        .def("is_expired",
             [](const DiscreteAveragingAsianOption& opt) {
                 return opt.isExpired();
             })
        .def(
            "set_pricing_engine",
            [](DiscreteAveragingAsianOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<
                        AnalyticDiscreteGeometricAveragePriceAsianEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticDiscreteGeometricAveragePriceAsianEngine.")
        .def(
            "set_turnbull_wakeman_pricing_engine",
            [](DiscreteAveragingAsianOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<TurnbullWakemanAsianEngine>(process));
            },
            nb::arg("process"),
            "Attach TurnbullWakemanAsianEngine (arithmetic average-price).")
        .def(
            "set_heston_pricing_engine",
            [](DiscreteAveragingAsianOption& opt,
               const ext::shared_ptr<HestonProcess>& process,
               Real xi_right_limit) {
                opt.setPricingEngine(
                    ext::make_shared<
                        AnalyticDiscreteGeometricAveragePriceAsianHestonEngine>(
                        process, xi_right_limit));
            },
            nb::arg("process"),
            nb::arg("xi_right_limit") = 100.0,
            "Attach AnalyticDiscreteGeometricAveragePriceAsianHestonEngine.");

    m.def(
        "AnalyticContinuousGeometricAveragePriceAsianEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for ContinuousAveragingAsianOption.set_pricing_engine.");

    m.def(
        "AnalyticDiscreteGeometricAveragePriceAsianEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for DiscreteAveragingAsianOption.set_pricing_engine.");

    m.def(
        "TurnbullWakemanAsianEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for "
        "DiscreteAveragingAsianOption.set_turnbull_wakeman_pricing_engine.");

    // --- Phase 128: DeltaVolQuote (FX smile quotes for Vanna/Volga) ---
    nb::enum_<DeltaVolQuote::DeltaType>(m, "DeltaVolDeltaType")
        .value("Spot", DeltaVolQuote::Spot)
        .value("Fwd", DeltaVolQuote::Fwd)
        .value("PaSpot", DeltaVolQuote::PaSpot)
        .value("PaFwd", DeltaVolQuote::PaFwd);

    nb::enum_<DeltaVolQuote::AtmType>(m, "DeltaVolAtmType")
        .value("AtmNull", DeltaVolQuote::AtmNull)
        .value("AtmSpot", DeltaVolQuote::AtmSpot)
        .value("AtmFwd", DeltaVolQuote::AtmFwd)
        .value("AtmDeltaNeutral", DeltaVolQuote::AtmDeltaNeutral)
        .value("AtmVegaMax", DeltaVolQuote::AtmVegaMax)
        .value("AtmGammaMax", DeltaVolQuote::AtmGammaMax)
        .value("AtmPutCall50", DeltaVolQuote::AtmPutCall50);

    nb::class_<DeltaVolQuote, Quote>(m, "DeltaVolQuote")
        .def(
            "__init__",
            [](DeltaVolQuote* self,
               Real delta,
               const Handle<Quote>& vol,
               Time maturity,
               DeltaVolQuote::DeltaType delta_type) {
                new (self) DeltaVolQuote(delta, vol, maturity, delta_type);
            },
            nb::arg("delta"),
            nb::arg("vol"),
            nb::arg("maturity"),
            nb::arg("delta_type"),
            "Standard delta vs vol quote.")
        .def(
            "__init__",
            [](DeltaVolQuote* self,
               const Handle<Quote>& vol,
               DeltaVolQuote::DeltaType delta_type,
               Time maturity,
               DeltaVolQuote::AtmType atm_type) {
                new (self) DeltaVolQuote(vol, delta_type, maturity, atm_type);
            },
            nb::arg("vol"),
            nb::arg("delta_type"),
            nb::arg("maturity"),
            nb::arg("atm_type"),
            "ATM delta-vol quote.")
        .def("value", &DeltaVolQuote::value)
        .def("delta", &DeltaVolQuote::delta)
        .def("maturity", &DeltaVolQuote::maturity)
        .def("atm_type", &DeltaVolQuote::atmType)
        .def("delta_type", &DeltaVolQuote::deltaType)
        .def("is_valid", &DeltaVolQuote::isValid);

    nb::class_<BarrierOption>(m, "BarrierOption")
        .def(
            "__init__",
            [](BarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier,
               Real rebate,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) BarrierOption(
                    barrier_type,
                    barrier,
                    rebate,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](BarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier,
               Real rebate,
               const CashOrNothingPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) BarrierOption(
                    barrier_type,
                    barrier,
                    rebate,
                    ext::make_shared<CashOrNothingPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](BarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier,
               Real rebate,
               const CashOrNothingPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) BarrierOption(
                    barrier_type,
                    barrier,
                    rebate,
                    ext::make_shared<CashOrNothingPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](BarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier,
               Real rebate,
               const AssetOrNothingPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) BarrierOption(
                    barrier_type,
                    barrier,
                    rebate,
                    ext::make_shared<AssetOrNothingPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV", [](BarrierOption& opt) { return opt.NPV(); })
        .def("delta", [](BarrierOption& opt) { return opt.delta(); })
        .def("gamma", [](BarrierOption& opt) { return opt.gamma(); })
        .def("vega", [](BarrierOption& opt) { return opt.vega(); })
        .def(
            "implied_volatility",
            [](BarrierOption& opt,
               Real target_price,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               Real accuracy,
               Size max_evaluations,
               Volatility min_vol,
               Volatility max_vol) {
                if (dividend_dates.empty())
                    return opt.impliedVolatility(target_price,
                                                 process,
                                                 accuracy,
                                                 max_evaluations,
                                                 min_vol,
                                                 max_vol);
                return opt.impliedVolatility(
                    target_price,
                    process,
                    DividendVector(dividend_dates, dividend_amounts),
                    accuracy,
                    max_evaluations,
                    min_vol,
                    max_vol);
            },
            nb::arg("target_price"),
            nb::arg("process"),
            nb::arg("dividend_dates") = std::vector<Date>(),
            nb::arg("dividend_amounts") = std::vector<Real>(),
            nb::arg("accuracy") = 1.0e-4,
            nb::arg("max_evaluations") = 100,
            nb::arg("min_vol") = 1.0e-7,
            nb::arg("max_vol") = 4.0,
            "Barrier implied vol (analytic if no dividends; FD BS if cash "
            "dividends).")
        .def(
            "set_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticBarrierEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticBarrierEngine (vanilla barrier).")
        .def(
            "set_perturbative_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Natural order,
               bool zero_gamma) {
                opt.setPricingEngine(
                    ext::make_shared<PerturbativeBarrierOptionEngine>(
                        process, order, zero_gamma));
            },
            nb::arg("process"),
            nb::arg("order") = Natural(1),
            nb::arg("zero_gamma") = false,
            "Attach PerturbativeBarrierOptionEngine (Recchioni).")
        .def(
            "set_vanna_volga_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<DeltaVolQuote>& atm_vol,
               const ext::shared_ptr<DeltaVolQuote>& vol25_put,
               const ext::shared_ptr<DeltaVolQuote>& vol25_call,
               const Handle<Quote>& spot_fx,
               const Handle<YieldTermStructure>& domestic_ts,
               const Handle<YieldTermStructure>& foreign_ts,
               bool adapt_van_delta,
               Real bs_price_with_smile) {
                opt.setPricingEngine(
                    ext::make_shared<VannaVolgaBarrierEngine>(
                        Handle<DeltaVolQuote>(atm_vol),
                        Handle<DeltaVolQuote>(vol25_put),
                        Handle<DeltaVolQuote>(vol25_call),
                        spot_fx,
                        domestic_ts,
                        foreign_ts,
                        adapt_van_delta,
                        bs_price_with_smile));
            },
            nb::arg("atm_vol"),
            nb::arg("vol25_put"),
            nb::arg("vol25_call"),
            nb::arg("spot_fx"),
            nb::arg("domestic_ts"),
            nb::arg("foreign_ts"),
            nb::arg("adapt_van_delta") = false,
            nb::arg("bs_price_with_smile") = 0.0,
            "Attach VannaVolgaBarrierEngine (FX barrier with smile).")
        .def(
            "set_binary_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticBinaryBarrierEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticBinaryBarrierEngine (cash/asset-or-nothing; "
            "American exercise, Haug p.176).")
        .def(
            "set_fd_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               Size t_grid,
               Size x_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdBlackScholesBarrierEngine>(
                        process, t_grid, x_grid, damping_steps, scheme_desc));
            },
            nb::arg("process"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdBlackScholesBarrierEngine (default Douglas scheme).")
        .def(
            "set_fd_dividend_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               Size t_grid,
               Size x_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdBlackScholesBarrierEngine>(
                        process,
                        DividendVector(dividend_dates, dividend_amounts),
                        t_grid,
                        x_grid,
                        damping_steps,
                        scheme_desc));
            },
            nb::arg("process"),
            nb::arg("dividend_dates"),
            nb::arg("dividend_amounts"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            "Attach FdBlackScholesBarrierEngine with discrete cash dividends.")
        .def(
            "set_fd_heston_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdHestonBarrierEngine>(
                    model, t_grid, x_grid, v_grid, damping_steps, scheme_desc));
            },
            nb::arg("model"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdHestonBarrierEngine (default Hundsdorfer scheme).")
        .def(
            "set_fd_heston_dividend_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               const std::vector<Date>& dividend_dates,
               const std::vector<Real>& dividend_amounts,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(ext::make_shared<FdHestonBarrierEngine>(
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
            "Attach FdHestonBarrierEngine with discrete cash dividends.")
        .def("error_estimate",
             [](BarrierOption& opt) { return opt.errorEstimate(); })
        .def(
            "set_mc_pricing_engine",
            [](BarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge,
               bool biased) {
                attach_mc_barrier_engine(
                    opt, process, time_steps, steps_per_year, required_samples,
                    required_tolerance, seed, antithetic, brownian_bridge,
                    biased);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 1UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            nb::arg("biased") = false,
            "Attach MakeMCBarrierEngine<PseudoRandom>.");

    m.def(
        "AnalyticBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to BarrierOption.set_pricing_engine.");

    m.def(
        "PerturbativeBarrierOptionEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "BarrierOption.set_perturbative_pricing_engine.");

    m.def(
        "AnalyticBinaryBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "BarrierOption.set_binary_pricing_engine.");

    m.def(
        "FdBlackScholesBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "BarrierOption.set_fd_pricing_engine.");

    m.def(
        "FdHestonBarrierEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "BarrierOption.set_fd_heston_pricing_engine.");

    m.def(
        "MCBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Documentation alias — use "
        "BarrierOption.set_mc_pricing_engine instead.");

    // --- Phase 42: quanto barrier options (standalone; BarrierOption MI) ----
    using QuantoBarrierEngine =
        QuantoEngine<BarrierOption, AnalyticBarrierEngine>;

    nb::class_<QuantoBarrierOption>(m, "QuantoBarrierOption")
        .def(
            "__init__",
            [](QuantoBarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier,
               Real rebate,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) QuantoBarrierOption(
                    barrier_type,
                    barrier,
                    rebate,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Quanto barrier option; payoff currency ≠ asset currency.")
        .def("NPV", [](QuantoBarrierOption& opt) { return opt.NPV(); })
        .def("delta", [](QuantoBarrierOption& opt) { return opt.delta(); })
        .def("gamma", [](QuantoBarrierOption& opt) { return opt.gamma(); })
        .def("vega", [](QuantoBarrierOption& opt) { return opt.vega(); })
        .def("qvega", &QuantoBarrierOption::qvega)
        .def("qrho", &QuantoBarrierOption::qrho)
        .def("qlambda", &QuantoBarrierOption::qlambda)
        .def("is_expired", &QuantoBarrierOption::isExpired)
        .def(
            "set_pricing_engine",
            [](QuantoBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               const Handle<Quote>& correlation) {
                opt.setPricingEngine(ext::make_shared<QuantoBarrierEngine>(
                    process,
                    foreign_risk_free_rate,
                    exchange_rate_volatility,
                    correlation));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach QuantoEngine<BarrierOption, AnalyticBarrierEngine>.")
        .def(
            "set_pricing_engine",
            [](QuantoBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               Real correlation) {
                opt.setPricingEngine(ext::make_shared<QuantoBarrierEngine>(
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
            "Attach quanto-barrier engine from a scalar correlation.");

    m.def(
        "QuantoBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias documentation token — prefer "
        "QuantoBarrierOption.set_pricing_engine(...).");

    // --- Phase 29: soft barrier options (standalone; OneAssetOption MI) -----
    nb::class_<SoftBarrierOption>(m, "SoftBarrierOption")
        .def(
            "__init__",
            [](SoftBarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier_lo,
               Real barrier_hi,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) SoftBarrierOption(
                    barrier_type,
                    barrier_lo,
                    barrier_hi,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier_lo"),
            nb::arg("barrier_hi"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV", [](SoftBarrierOption& opt) { return opt.NPV(); })
        .def("delta", [](SoftBarrierOption& opt) { return opt.delta(); })
        .def("gamma", [](SoftBarrierOption& opt) { return opt.gamma(); })
        .def("vega", [](SoftBarrierOption& opt) { return opt.vega(); })
        .def(
            "implied_volatility",
            [](SoftBarrierOption& opt,
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
            nb::arg("min_vol") = 1.0e-6,
            nb::arg("max_vol") = 4.0,
            "Implied Black vol matching a target NPV "
            "(AnalyticSoftBarrierEngine). min_vol defaults to 1e-6 "
            "(zero vol can NaN the soft-barrier formula).")
        .def(
            "set_pricing_engine",
            [](SoftBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticSoftBarrierEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticSoftBarrierEngine (Hart/Ross / Haug p.165).");

    m.def(
        "AnalyticSoftBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "SoftBarrierOption.set_pricing_engine.");

    // --- Phase 30: partial-time barrier options (standalone wrappers) -------
    nb::enum_<PartialBarrier::Range>(m, "PartialBarrierRange")
        .value("Start", PartialBarrier::Start)
        .value("EndB1", PartialBarrier::EndB1)
        .value("EndB2", PartialBarrier::EndB2);

    nb::class_<PartialTimeBarrierOption>(m, "PartialTimeBarrierOption")
        .def(
            "__init__",
            [](PartialTimeBarrierOption* self,
               Barrier::Type barrier_type,
               PartialBarrier::Range barrier_range,
               Real barrier,
               Real rebate,
               const Date& cover_event_date,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) PartialTimeBarrierOption(
                    barrier_type,
                    barrier_range,
                    barrier,
                    rebate,
                    cover_event_date,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier_range"),
            nb::arg("barrier"),
            nb::arg("rebate"),
            nb::arg("cover_event_date"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV", [](PartialTimeBarrierOption& opt) { return opt.NPV(); })
        .def("delta",
             [](PartialTimeBarrierOption& opt) { return opt.delta(); })
        .def("gamma",
             [](PartialTimeBarrierOption& opt) { return opt.gamma(); })
        .def(
            "set_pricing_engine",
            [](PartialTimeBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticPartialTimeBarrierOptionEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticPartialTimeBarrierOptionEngine (Haug). "
            "Knock-in partial-time end options are not covered.");

    m.def(
        "AnalyticPartialTimeBarrierOptionEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "PartialTimeBarrierOption.set_pricing_engine.");

    // --- Phase 32: two-asset barrier options (standalone; Option MI) --------
    nb::class_<TwoAssetBarrierOption>(m, "TwoAssetBarrierOption")
        .def(
            "__init__",
            [](TwoAssetBarrierOption* self,
               Barrier::Type barrier_type,
               Real barrier,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) TwoAssetBarrierOption(
                    barrier_type,
                    barrier,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV", [](TwoAssetBarrierOption& opt) { return opt.NPV(); })
        .def("is_expired", &TwoAssetBarrierOption::isExpired)
        .def(
            "set_pricing_engine",
            [](TwoAssetBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               const Handle<Quote>& rho) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticTwoAssetBarrierEngine>(
                        process1, process2, rho));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("rho"),
            "Attach AnalyticTwoAssetBarrierEngine "
            "(process1 = strike asset, process2 = barrier asset, "
            "rho = correlation).")
        .def(
            "set_pricing_engine",
            [](TwoAssetBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real rho) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticTwoAssetBarrierEngine>(
                        process1,
                        process2,
                        Handle<Quote>(ext::make_shared<SimpleQuote>(rho))));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("rho"),
            "Attach AnalyticTwoAssetBarrierEngine from a scalar correlation.");

    // --- Phase 33: two-asset correlation options (standalone; MultiAssetOption MI)
    nb::class_<TwoAssetCorrelationOption>(m, "TwoAssetCorrelationOption")
        .def(
            "__init__",
            [](TwoAssetCorrelationOption* self,
               Option::Type type,
               Real strike1,
               Real strike2,
               const EuropeanExercise& exercise) {
                new (self) TwoAssetCorrelationOption(
                    type,
                    strike1,
                    strike2,
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("option_type"),
            nb::arg("strike1"),
            nb::arg("strike2"),
            nb::arg("exercise"),
            "Pays asset-2 payoff only if asset 1 finishes in the money "
            "(Zhang / Haug analytic engine).")
        .def("NPV", [](TwoAssetCorrelationOption& opt) { return opt.NPV(); })
        .def("is_expired", &TwoAssetCorrelationOption::isExpired)
        .def(
            "set_pricing_engine",
            [](TwoAssetCorrelationOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               const Handle<Quote>& correlation) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticTwoAssetCorrelationEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach AnalyticTwoAssetCorrelationEngine "
            "(process1 = conditioning asset / strike1, "
            "process2 = payoff asset / strike2, "
            "correlation = asset correlation).")
        .def(
            "set_pricing_engine",
            [](TwoAssetCorrelationOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticTwoAssetCorrelationEngine>(
                        process1,
                        process2,
                        Handle<Quote>(
                            ext::make_shared<SimpleQuote>(correlation))));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach AnalyticTwoAssetCorrelationEngine from a scalar "
            "correlation.");

    // --- Phase 95: Himalaya options (standalone; MultiAssetOption MI)
    nb::class_<HimalayaOption>(m, "HimalayaOption")
        .def(
            "__init__",
            [](HimalayaOption* self,
               const std::vector<Date>& fixing_dates,
               Real strike) {
                QL_REQUIRE(!fixing_dates.empty(), "no fixing dates given");
                new (self) HimalayaOption(fixing_dates, strike);
            },
            nb::arg("fixing_dates"),
            nb::arg("strike"),
            "Himalaya basket: at each fixing take the best remaining "
            "performer into the average, then discard it; payoff is "
            "max(average - strike, 0).")
        .def("NPV", [](HimalayaOption& opt) { return opt.NPV(); })
        .def("error_estimate",
             [](HimalayaOption& opt) { return opt.errorEstimate(); })
        .def("is_expired", [](const HimalayaOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_mc_pricing_engine",
            [](HimalayaOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge,
               std::optional<Size> max_samples) {
                QL_REQUIRE(
                    !(required_samples.has_value() &&
                      required_tolerance.has_value()),
                    "set only one of required_samples or required_tolerance");
                auto maker =
                    MakeMCHimalayaEngine<PseudoRandom>(
                        to_process_array(processes, rho))
                        .withSeed(seed)
                        .withAntitheticVariate(antithetic)
                        .withBrownianBridge(brownian_bridge);
                if (required_samples.has_value())
                    maker.withSamples(*required_samples);
                else if (required_tolerance.has_value())
                    maker.withAbsoluteTolerance(*required_tolerance);
                else
                    maker.withSamples(Size(1023));
                if (max_samples.has_value())
                    maker.withMaxSamples(*max_samples);
                opt.setPricingEngine(maker);
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 86421UL,
            nb::arg("antithetic") = false,
            nb::arg("brownian_bridge") = false,
            nb::arg("max_samples") = nb::none(),
            "Attach MakeMCHimalayaEngine<PseudoRandom> "
            "(time grid from fixing_dates).");
    m.def(
        "MCHimalayaEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           std::optional<Size> /*required_samples*/,
           std::optional<Real> /*required_tolerance*/,
           unsigned long /*seed*/,
           bool /*antithetic*/,
           bool /*brownian_bridge*/,
           std::optional<Size> /*max_samples*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("required_samples") = nb::none(),
        nb::arg("required_tolerance") = nb::none(),
        nb::arg("seed") = 86421UL,
        nb::arg("antithetic") = false,
        nb::arg("brownian_bridge") = false,
        nb::arg("max_samples") = nb::none(),
        "Documentation alias — use "
        "HimalayaOption.set_mc_pricing_engine instead.");

    // --- Phase 96: Pagoda options (standalone; MultiAssetOption MI)
    nb::class_<PagodaOption>(m, "PagodaOption")
        .def(
            "__init__",
            [](PagodaOption* self,
               const std::vector<Date>& fixing_dates,
               Real roof,
               Real fraction) {
                new (self) PagodaOption(fixing_dates, roof, fraction);
            },
            nb::arg("fixing_dates"),
            nb::arg("roof"),
            nb::arg("fraction"),
            "Roofed Asian basket: fraction * min(roof, max(portfolio "
            "performance, 0)).")
        .def("NPV", [](PagodaOption& opt) { return opt.NPV(); })
        .def("error_estimate",
             [](PagodaOption& opt) { return opt.errorEstimate(); })
        .def("is_expired", [](const PagodaOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_mc_pricing_engine",
            [](PagodaOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge,
               std::optional<Size> max_samples) {
                QL_REQUIRE(
                    !(required_samples.has_value() &&
                      required_tolerance.has_value()),
                    "set only one of required_samples or required_tolerance");
                auto maker =
                    MakeMCPagodaEngine<PseudoRandom>(
                        to_process_array(processes, rho))
                        .withSeed(seed)
                        .withAntitheticVariate(antithetic)
                        .withBrownianBridge(brownian_bridge);
                if (required_samples.has_value())
                    maker.withSamples(*required_samples);
                else if (required_tolerance.has_value())
                    maker.withAbsoluteTolerance(*required_tolerance);
                else
                    maker.withSamples(Size(1023));
                if (max_samples.has_value())
                    maker.withMaxSamples(*max_samples);
                opt.setPricingEngine(maker);
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 86421UL,
            nb::arg("antithetic") = false,
            nb::arg("brownian_bridge") = false,
            nb::arg("max_samples") = nb::none(),
            "Attach MakeMCPagodaEngine<PseudoRandom> "
            "(time grid from fixing_dates).");
    m.def(
        "MCPagodaEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           std::optional<Size> /*required_samples*/,
           std::optional<Real> /*required_tolerance*/,
           unsigned long /*seed*/,
           bool /*antithetic*/,
           bool /*brownian_bridge*/,
           std::optional<Size> /*max_samples*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("required_samples") = nb::none(),
        nb::arg("required_tolerance") = nb::none(),
        nb::arg("seed") = 86421UL,
        nb::arg("antithetic") = false,
        nb::arg("brownian_bridge") = false,
        nb::arg("max_samples") = nb::none(),
        "Documentation alias — use "
        "PagodaOption.set_mc_pricing_engine instead.");

    // --- Phase 97: Everest options (standalone; MultiAssetOption MI)
    nb::class_<EverestOption>(m, "EverestOption")
        .def(
            "__init__",
            [](EverestOption* self,
               Real notional,
               Rate guarantee,
               const EuropeanExercise& exercise) {
                new (self) EverestOption(
                    notional,
                    guarantee,
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("notional"),
            nb::arg("guarantee"),
            nb::arg("exercise"),
            "Everest basket: notional * (guarantee + min performance) "
            "at European exercise.")
        .def("NPV", [](EverestOption& opt) { return opt.NPV(); })
        .def("yield_", [](EverestOption& opt) { return opt.yield(); },
             "Implied yield from NPV / (notional * discount) - 1.")
        .def("error_estimate",
             [](EverestOption& opt) { return opt.errorEstimate(); })
        .def("is_expired", [](const EverestOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_mc_pricing_engine",
            [](EverestOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge,
               std::optional<Size> max_samples) {
                QL_REQUIRE(
                    !(time_steps.has_value() && steps_per_year.has_value()),
                    "set only one of time_steps or steps_per_year");
                QL_REQUIRE(
                    !(required_samples.has_value() &&
                      required_tolerance.has_value()),
                    "set only one of required_samples or required_tolerance");
                auto maker =
                    MakeMCEverestEngine<PseudoRandom>(
                        to_process_array(processes, rho))
                        .withSeed(seed)
                        .withAntitheticVariate(antithetic)
                        .withBrownianBridge(brownian_bridge);
                if (time_steps.has_value())
                    maker.withSteps(*time_steps);
                else if (steps_per_year.has_value())
                    maker.withStepsPerYear(*steps_per_year);
                else
                    maker.withStepsPerYear(Size(1));
                if (required_samples.has_value())
                    maker.withSamples(*required_samples);
                else if (required_tolerance.has_value())
                    maker.withAbsoluteTolerance(*required_tolerance);
                else
                    maker.withSamples(Size(1023));
                if (max_samples.has_value())
                    maker.withMaxSamples(*max_samples);
                opt.setPricingEngine(maker);
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 86421UL,
            nb::arg("antithetic") = false,
            nb::arg("brownian_bridge") = false,
            nb::arg("max_samples") = nb::none(),
            "Attach MakeMCEverestEngine<PseudoRandom>.");
    m.def(
        "MCEverestEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           std::optional<Size> /*time_steps*/,
           std::optional<Size> /*steps_per_year*/,
           std::optional<Size> /*required_samples*/,
           std::optional<Real> /*required_tolerance*/,
           unsigned long /*seed*/,
           bool /*antithetic*/,
           bool /*brownian_bridge*/,
           std::optional<Size> /*max_samples*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("time_steps") = nb::none(),
        nb::arg("steps_per_year") = nb::none(),
        nb::arg("required_samples") = nb::none(),
        nb::arg("required_tolerance") = nb::none(),
        nb::arg("seed") = 86421UL,
        nb::arg("antithetic") = false,
        nb::arg("brownian_bridge") = false,
        nb::arg("max_samples") = nb::none(),
        "Documentation alias — use "
        "EverestOption.set_mc_pricing_engine instead.");

    // --- Phase 75: Margrabe exchange options (standalone; MultiAssetOption MI)
    nb::class_<MargrabeOption>(m, "MargrabeOption")
        .def(
            "__init__",
            [](MargrabeOption* self,
               Integer quantity1,
               Integer quantity2,
               const EuropeanExercise& exercise) {
                new (self) MargrabeOption(
                    quantity1,
                    quantity2,
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("quantity1"),
            nb::arg("quantity2"),
            nb::arg("exercise"),
            "Right to exchange quantity2 of asset 2 for quantity1 of asset 1 "
            "(European Margrabe 1978).")
        .def(
            "__init__",
            [](MargrabeOption* self,
               Integer quantity1,
               Integer quantity2,
               const AmericanExercise& exercise) {
                new (self) MargrabeOption(
                    quantity1,
                    quantity2,
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("quantity1"),
            nb::arg("quantity2"),
            nb::arg("exercise"),
            "Right to exchange quantity2 of asset 2 for quantity1 of asset 1 "
            "(American Margrabe / Bjerksund-Stensland reduction).")
        .def("NPV", [](MargrabeOption& opt) { return opt.NPV(); })
        .def("delta1", [](MargrabeOption& opt) { return opt.delta1(); })
        .def("delta2", [](MargrabeOption& opt) { return opt.delta2(); })
        .def("gamma1", [](MargrabeOption& opt) { return opt.gamma1(); })
        .def("gamma2", [](MargrabeOption& opt) { return opt.gamma2(); })
        .def("theta", [](MargrabeOption& opt) { return opt.theta(); })
        .def("is_expired", [](const MargrabeOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_pricing_engine",
            [](MargrabeOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticEuropeanMargrabeEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach AnalyticEuropeanMargrabeEngine (scalar asset correlation).")
        .def(
            "set_american_pricing_engine",
            [](MargrabeOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticAmericanMargrabeEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach AnalyticAmericanMargrabeEngine (scalar asset correlation).");

    m.def(
        "AnalyticEuropeanMargrabeEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        "Factory alias: pass process1, process2, correlation to "
        "MargrabeOption.set_pricing_engine.");
    m.def(
        "AnalyticAmericanMargrabeEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        "Factory alias: pass process1, process2, correlation to "
        "MargrabeOption.set_american_pricing_engine.");

    // --- Phase 76: simple / complex chooser options (standalone; OneAssetOption MI)
    nb::class_<SimpleChooserOption>(m, "SimpleChooserOption")
        .def(
            "__init__",
            [](SimpleChooserOption* self,
               const Date& choosing_date,
               Real strike,
               const EuropeanExercise& exercise) {
                new (self) SimpleChooserOption(
                    choosing_date,
                    strike,
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("choosing_date"),
            nb::arg("strike"),
            nb::arg("exercise"),
            "At choosing_date the holder picks call or put; same strike and "
            "European expiry for both (Haug pp.39-40).")
        .def("NPV", [](SimpleChooserOption& opt) { return opt.NPV(); })
        .def("is_expired", [](const SimpleChooserOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_pricing_engine",
            [](SimpleChooserOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticSimpleChooserEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticSimpleChooserEngine.");

    m.def(
        "AnalyticSimpleChooserEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "SimpleChooserOption.set_pricing_engine.");

    nb::class_<ComplexChooserOption>(m, "ComplexChooserOption")
        .def(
            "__init__",
            [](ComplexChooserOption* self,
               const Date& choosing_date,
               Real strike_call,
               Real strike_put,
               const EuropeanExercise& call_exercise,
               const EuropeanExercise& put_exercise) {
                new (self) ComplexChooserOption(
                    choosing_date,
                    strike_call,
                    strike_put,
                    ext::make_shared<EuropeanExercise>(call_exercise),
                    ext::make_shared<EuropeanExercise>(put_exercise));
            },
            nb::arg("choosing_date"),
            nb::arg("strike_call"),
            nb::arg("strike_put"),
            nb::arg("call_exercise"),
            nb::arg("put_exercise"),
            "At choosing_date the holder picks a call or put with distinct "
            "strikes and European expiries (Haug).")
        .def("NPV", [](ComplexChooserOption& opt) { return opt.NPV(); })
        .def("is_expired", [](const ComplexChooserOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_pricing_engine",
            [](ComplexChooserOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticComplexChooserEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticComplexChooserEngine.");

    m.def(
        "AnalyticComplexChooserEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "ComplexChooserOption.set_pricing_engine.");

    // --- Phase 83: holder / writer extensible options (standalone; OneAssetOption MI)
    nb::class_<HolderExtensibleOption>(m, "HolderExtensibleOption")
        .def(
            "__init__",
            [](HolderExtensibleOption* self,
               Option::Type type,
               Real premium,
               const Date& second_expiry_date,
               Real second_strike,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) HolderExtensibleOption(
                    type,
                    premium,
                    second_expiry_date,
                    second_strike,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("type"),
            nb::arg("premium"),
            nb::arg("second_expiry_date"),
            nb::arg("second_strike"),
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Holder may extend to a later expiry (new strike) by paying a "
            "premium (Haug).")
        .def("NPV", [](HolderExtensibleOption& opt) { return opt.NPV(); })
        .def("is_expired", [](const HolderExtensibleOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_pricing_engine",
            [](HolderExtensibleOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticHolderExtensibleOptionEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticHolderExtensibleOptionEngine.");

    m.def(
        "AnalyticHolderExtensibleOptionEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "HolderExtensibleOption.set_pricing_engine.");

    nb::class_<WriterExtensibleOption>(m, "WriterExtensibleOption")
        .def(
            "__init__",
            [](WriterExtensibleOption* self,
               const PlainVanillaPayoff& payoff1,
               const EuropeanExercise& exercise1,
               const PlainVanillaPayoff& payoff2,
               const EuropeanExercise& exercise2) {
                new (self) WriterExtensibleOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff1),
                    ext::make_shared<EuropeanExercise>(exercise1),
                    ext::make_shared<PlainVanillaPayoff>(payoff2),
                    ext::make_shared<EuropeanExercise>(exercise2));
            },
            nb::arg("payoff1"),
            nb::arg("exercise1"),
            nb::arg("payoff2"),
            nb::arg("exercise2"),
            "If OTM at the first expiry the writer extends to a later "
            "expiry with an amended strike (Haug).")
        .def("NPV", [](WriterExtensibleOption& opt) { return opt.NPV(); })
        .def("is_expired", [](const WriterExtensibleOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_pricing_engine",
            [](WriterExtensibleOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticWriterExtensibleOptionEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticWriterExtensibleOptionEngine.");

    m.def(
        "AnalyticWriterExtensibleOptionEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "WriterExtensibleOption.set_pricing_engine.");

    // --- Phase 78/79/82/84/85/86/87/88: basket options (standalone; MultiAssetOption MI)
    nb::enum_<OperatorSplittingSpreadEngine::Order>(m, "OperatorSplittingOrder")
        .value("First", OperatorSplittingSpreadEngine::First)
        .value("Second", OperatorSplittingSpreadEngine::Second);

    nb::class_<SpreadBasketPayoff>(m, "SpreadBasketPayoff")
        .def(
            "__init__",
            [](SpreadBasketPayoff* self, const PlainVanillaPayoff& payoff) {
                new (self) SpreadBasketPayoff(
                    ext::make_shared<PlainVanillaPayoff>(payoff));
            },
            nb::arg("payoff"),
            "Basket payoff on S1 - S2 wrapped around a vanilla call/put.");

    nb::class_<MinBasketPayoff>(m, "MinBasketPayoff")
        .def(
            "__init__",
            [](MinBasketPayoff* self, const PlainVanillaPayoff& payoff) {
                new (self) MinBasketPayoff(
                    ext::make_shared<PlainVanillaPayoff>(payoff));
            },
            nb::arg("payoff"),
            "Basket payoff on min(S1, S2) wrapped around a vanilla call/put.");

    nb::class_<MaxBasketPayoff>(m, "MaxBasketPayoff")
        .def(
            "__init__",
            [](MaxBasketPayoff* self, const PlainVanillaPayoff& payoff) {
                new (self) MaxBasketPayoff(
                    ext::make_shared<PlainVanillaPayoff>(payoff));
            },
            nb::arg("payoff"),
            "Basket payoff on max(S1, S2) wrapped around a vanilla call/put.");

    nb::class_<AverageBasketPayoff>(m, "AverageBasketPayoff")
        .def(
            "__init__",
            [](AverageBasketPayoff* self,
               const PlainVanillaPayoff& payoff,
               const std::vector<Real>& weights) {
                new (self) AverageBasketPayoff(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    Array(weights.begin(), weights.end()));
            },
            nb::arg("payoff"),
            nb::arg("weights"),
            "Weighted-sum basket payoff (weights may be negative).");

    nb::class_<BasketOption>(m, "BasketOption")
        .def(
            "__init__",
            [](BasketOption* self,
               const SpreadBasketPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<SpreadBasketPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Two-asset European spread basket (Kirk 1995).")
        .def(
            "__init__",
            [](BasketOption* self,
               const SpreadBasketPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<SpreadBasketPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Two-asset American spread basket.")
        .def(
            "__init__",
            [](BasketOption* self,
               const MinBasketPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<MinBasketPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Two-asset European min basket (Stulz 1982).")
        .def(
            "__init__",
            [](BasketOption* self,
               const MinBasketPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<MinBasketPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Two-asset American min basket.")
        .def(
            "__init__",
            [](BasketOption* self,
               const MaxBasketPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<MaxBasketPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Two-asset European max basket (Stulz 1982).")
        .def(
            "__init__",
            [](BasketOption* self,
               const MaxBasketPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<MaxBasketPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Two-asset American max basket.")
        .def(
            "__init__",
            [](BasketOption* self,
               const AverageBasketPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<AverageBasketPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "European weighted-sum basket (Choi 2018).")
        .def(
            "__init__",
            [](BasketOption* self,
               const AverageBasketPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) BasketOption(
                    ext::make_shared<AverageBasketPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            "American weighted-sum basket.")
        .def("NPV", [](BasketOption& opt) { return opt.NPV(); })
        .def("is_expired", [](const BasketOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_kirk_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<KirkEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach KirkEngine (futures-style spread; use q = r).")
        .def(
            "set_bjerksund_stensland_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<BjerksundStenslandSpreadEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach BjerksundStenslandSpreadEngine (futures-style; use q = r).")
        .def(
            "set_pearson_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<PearsonSpreadEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach PearsonSpreadEngine (1-D integration; use q = r).")
        .def(
            "set_operator_splitting_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation,
               OperatorSplittingSpreadEngine::Order order) {
                opt.setPricingEngine(
                    ext::make_shared<OperatorSplittingSpreadEngine>(
                        process1, process2, correlation, order));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            nb::arg("order") = OperatorSplittingSpreadEngine::Second,
            "Attach OperatorSplittingSpreadEngine (Lo 2015; use q = r).")
        .def(
            "set_gaussian_copula_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation,
               Size n_points) {
                opt.setPricingEngine(
                    ext::make_shared<GaussianCopulaSpreadEngine>(
                        process1, process2, correlation, n_points));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            nb::arg("n_points") = 64,
            "Attach GaussianCopulaSpreadEngine (Gauss-Hermite; use q = r).")
        .def(
            "set_fd_2d_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation,
               Size x_grid,
               Size y_grid,
               Size t_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc,
               bool local_vol) {
                opt.setPricingEngine(
                    ext::make_shared<Fd2dBlackScholesVanillaEngine>(
                        process1, process2, correlation,
                        x_grid, y_grid, t_grid, damping_steps,
                        scheme_desc, local_vol));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            nb::arg("x_grid") = 100,
            nb::arg("y_grid") = 100,
            nb::arg("t_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            nb::arg("local_vol") = false,
            "Attach Fd2dBlackScholesVanillaEngine (2-D PDE).")
        .def(
            "set_stulz_pricing_engine",
            [](BasketOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process1,
               const ext::shared_ptr<BlackScholesMertonProcess>& process2,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<StulzEngine>(
                        process1, process2, correlation));
            },
            nb::arg("process1"),
            nb::arg("process2"),
            nb::arg("correlation"),
            "Attach StulzEngine (min/max of two assets).")
        .def(
            "set_choi_pricing_engine",
            [](BasketOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               Real integration_lambda,
               std::optional<Size> max_nr_integration_steps,
               bool calc_fwd_delta,
               bool control_variate) {
                const Size max_steps =
                    max_nr_integration_steps.value_or(
                        std::numeric_limits<Size>::max());
                opt.setPricingEngine(
                    ext::make_shared<ChoiBasketEngine>(
                        to_gbs_processes(processes),
                        rho,
                        integration_lambda,
                        max_steps,
                        calc_fwd_delta,
                        control_variate));
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("integration_lambda") = 10.0,
            nb::arg("max_nr_integration_steps") = nb::none(),
            nb::arg("calc_fwd_delta") = false,
            nb::arg("control_variate") = false,
            "Attach ChoiBasketEngine (weighted-sum basket, Choi 2018).")
        .def(
            "set_single_factor_pricing_engine",
            [](BasketOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes) {
                opt.setPricingEngine(
                    ext::make_shared<SingleFactorBsmBasketEngine>(
                        to_gbs_processes(processes)));
            },
            nb::arg("processes"),
            "Attach SingleFactorBsmBasketEngine (one stochastic factor).")
        .def(
            "set_deng_li_zhou_pricing_engine",
            [](BasketOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho) {
                opt.setPricingEngine(
                    ext::make_shared<DengLiZhouBasketEngine>(
                        to_gbs_processes(processes), rho));
            },
            nb::arg("processes"),
            nb::arg("rho"),
            "Attach DengLiZhouBasketEngine (spread/basket closed form).")
        .def(
            "set_fd_ndim_pricing_engine",
            [](BasketOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               Size x_grid,
               Size t_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc,
               std::optional<std::vector<Size>> x_grids) {
                if (x_grids.has_value()) {
                    opt.setPricingEngine(
                        ext::make_shared<FdndimBlackScholesVanillaEngine>(
                            to_gbs_processes(processes),
                            rho,
                            *x_grids,
                            t_grid,
                            damping_steps,
                            scheme_desc));
                } else {
                    opt.setPricingEngine(
                        ext::make_shared<FdndimBlackScholesVanillaEngine>(
                            to_gbs_processes(processes),
                            rho,
                            x_grid,
                            t_grid,
                            damping_steps,
                            scheme_desc));
                }
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("x_grid") = 100,
            nb::arg("t_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
            nb::arg("x_grids") = nb::none(),
            "Attach FdndimBlackScholesVanillaEngine (n-D PDE, max 4 assets).")
        .def(
            "set_mc_european_pricing_engine",
            [](BasketOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                QL_REQUIRE(
                    !(time_steps.has_value() && steps_per_year.has_value()),
                    "set only one of time_steps or steps_per_year");
                QL_REQUIRE(
                    !(required_samples.has_value() &&
                      required_tolerance.has_value()),
                    "set only one of required_samples or required_tolerance");
                auto maker =
                    MakeMCEuropeanBasketEngine<PseudoRandom>(
                        to_process_array(processes, rho))
                        .withSeed(seed)
                        .withAntitheticVariate(antithetic)
                        .withBrownianBridge(brownian_bridge);
                if (time_steps.has_value())
                    maker.withSteps(*time_steps);
                else if (steps_per_year.has_value())
                    maker.withStepsPerYear(*steps_per_year);
                else
                    maker.withStepsPerYear(Size(1));
                if (required_samples.has_value())
                    maker.withSamples(*required_samples);
                else if (required_tolerance.has_value())
                    maker.withAbsoluteTolerance(*required_tolerance);
                else
                    maker.withSamples(Size(10000));
                opt.setPricingEngine(maker);
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 42UL,
            nb::arg("antithetic") = false,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCEuropeanBasketEngine<PseudoRandom>.")
        .def(
            "set_mc_american_pricing_engine",
            [](BasketOption& opt,
               const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
                   processes,
               const Matrix& rho,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge,
               std::optional<Size> calibration_samples) {
                QL_REQUIRE(
                    !(time_steps.has_value() && steps_per_year.has_value()),
                    "set only one of time_steps or steps_per_year");
                QL_REQUIRE(
                    !(required_samples.has_value() &&
                      required_tolerance.has_value()),
                    "set only one of required_samples or required_tolerance");
                auto maker =
                    MakeMCAmericanBasketEngine<PseudoRandom>(
                        to_process_array(processes, rho))
                        .withSeed(seed)
                        .withAntitheticVariate(antithetic)
                        .withBrownianBridge(brownian_bridge);
                if (time_steps.has_value())
                    maker.withSteps(*time_steps);
                else if (steps_per_year.has_value())
                    maker.withStepsPerYear(*steps_per_year);
                else
                    maker.withSteps(Size(52));
                if (required_samples.has_value())
                    maker.withSamples(*required_samples);
                else if (required_tolerance.has_value())
                    maker.withAbsoluteTolerance(*required_tolerance);
                else
                    maker.withSamples(Size(10000));
                if (calibration_samples.has_value())
                    maker.withCalibrationSamples(*calibration_samples);
                opt.setPricingEngine(maker);
            },
            nb::arg("processes"),
            nb::arg("rho"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 0UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            nb::arg("calibration_samples") = nb::none(),
            "Attach MakeMCAmericanBasketEngine<PseudoRandom> (LSM).");

    m.def(
        "KirkEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        "Factory alias: pass process1, process2, correlation to "
        "BasketOption.set_kirk_pricing_engine.");
    m.def(
        "BjerksundStenslandSpreadEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        "Factory alias: pass args to "
        "BasketOption.set_bjerksund_stensland_pricing_engine.");
    m.def(
        "PearsonSpreadEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        "Factory alias: pass args to "
        "BasketOption.set_pearson_pricing_engine.");
    m.def(
        "OperatorSplittingSpreadEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/,
           OperatorSplittingSpreadEngine::Order /*order*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        nb::arg("order") = OperatorSplittingSpreadEngine::Second,
        "Factory alias: pass args to "
        "BasketOption.set_operator_splitting_pricing_engine.");
    m.def(
        "GaussianCopulaSpreadEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/,
           Size /*n_points*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        nb::arg("n_points") = 64,
        "Factory alias: pass args to "
        "BasketOption.set_gaussian_copula_pricing_engine.");
    m.def(
        "Fd2dBlackScholesVanillaEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/,
           Size /*x_grid*/,
           Size /*y_grid*/,
           Size /*t_grid*/,
           Size /*damping_steps*/,
           const FdmSchemeDesc& /*scheme_desc*/,
           bool /*local_vol*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        nb::arg("x_grid") = 100,
        nb::arg("y_grid") = 100,
        nb::arg("t_grid") = 50,
        nb::arg("damping_steps") = 0,
        nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
        nb::arg("local_vol") = false,
        "Factory alias: pass args to "
        "BasketOption.set_fd_2d_pricing_engine.");
    m.def(
        "StulzEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process1,
           const ext::shared_ptr<BlackScholesMertonProcess>& /*process2*/,
           Real /*correlation*/) {
            return process1;
        },
        nb::arg("process1"),
        nb::arg("process2"),
        nb::arg("correlation"),
        "Factory alias: pass process1, process2, correlation to "
        "BasketOption.set_stulz_pricing_engine.");
    m.def(
        "ChoiBasketEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           Real /*integration_lambda*/,
           std::optional<Size> /*max_nr_integration_steps*/,
           bool /*calc_fwd_delta*/,
           bool /*control_variate*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("integration_lambda") = 10.0,
        nb::arg("max_nr_integration_steps") = nb::none(),
        nb::arg("calc_fwd_delta") = false,
        nb::arg("control_variate") = false,
        "Factory alias: pass args to "
        "BasketOption.set_choi_pricing_engine.");
    m.def(
        "SingleFactorBsmBasketEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        "Factory alias: pass args to "
        "BasketOption.set_single_factor_pricing_engine.");
    m.def(
        "DengLiZhouBasketEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        "Factory alias: pass args to "
        "BasketOption.set_deng_li_zhou_pricing_engine.");
    m.def(
        "FdndimBlackScholesVanillaEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           Size /*x_grid*/,
           Size /*t_grid*/,
           Size /*damping_steps*/,
           const FdmSchemeDesc& /*scheme_desc*/,
           std::optional<std::vector<Size>> /*x_grids*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("x_grid") = 100,
        nb::arg("t_grid") = 50,
        nb::arg("damping_steps") = 0,
        nb::arg("scheme_desc") = FdmSchemeDesc::Douglas(),
        nb::arg("x_grids") = nb::none(),
        "Factory alias: pass args to "
        "BasketOption.set_fd_ndim_pricing_engine.");
    m.def(
        "MCEuropeanBasketEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           std::optional<Size> /*time_steps*/,
           std::optional<Size> /*steps_per_year*/,
           std::optional<Size> /*required_samples*/,
           std::optional<Real> /*required_tolerance*/,
           unsigned long /*seed*/,
           bool /*antithetic*/,
           bool /*brownian_bridge*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("time_steps") = nb::none(),
        nb::arg("steps_per_year") = nb::none(),
        nb::arg("required_samples") = nb::none(),
        nb::arg("required_tolerance") = nb::none(),
        nb::arg("seed") = 42UL,
        nb::arg("antithetic") = false,
        nb::arg("brownian_bridge") = false,
        "Factory alias: pass args to "
        "BasketOption.set_mc_european_pricing_engine.");
    m.def(
        "MCAmericanBasketEngine",
        [](const std::vector<ext::shared_ptr<BlackScholesMertonProcess>>&
               processes,
           const Matrix& /*rho*/,
           std::optional<Size> /*time_steps*/,
           std::optional<Size> /*steps_per_year*/,
           std::optional<Size> /*required_samples*/,
           std::optional<Real> /*required_tolerance*/,
           unsigned long /*seed*/,
           bool /*antithetic*/,
           bool /*brownian_bridge*/,
           std::optional<Size> /*calibration_samples*/) {
            QL_REQUIRE(!processes.empty(), "no processes given");
            return processes.front();
        },
        nb::arg("processes"),
        nb::arg("rho"),
        nb::arg("time_steps") = nb::none(),
        nb::arg("steps_per_year") = nb::none(),
        nb::arg("required_samples") = nb::none(),
        nb::arg("required_tolerance") = nb::none(),
        nb::arg("seed") = 0UL,
        nb::arg("antithetic") = true,
        nb::arg("brownian_bridge") = false,
        nb::arg("calibration_samples") = nb::none(),
        "Factory alias: pass args to "
        "BasketOption.set_mc_american_pricing_engine.");

    // --- Phase 80/81: variance swap (standalone Instrument; replicating + MC)
    m.def(
        "BlackVarianceSurface",
        [](const Date& reference_date,
           const Calendar& calendar,
           const std::vector<Date>& dates,
           const std::vector<Real>& strikes,
           const Matrix& black_vol_matrix,
           const DayCounter& day_counter) {
            return Handle<BlackVolTermStructure>(
                ext::make_shared<BlackVarianceSurface>(
                    reference_date,
                    calendar,
                    dates,
                    strikes,
                    black_vol_matrix,
                    day_counter));
        },
        nb::arg("reference_date"),
        nb::arg("calendar"),
        nb::arg("dates"),
        nb::arg("strikes"),
        nb::arg("black_vol_matrix"),
        nb::arg("day_counter"),
        "Black variance surface handle (strike/expiry interpolated).");

    m.def(
        "BlackVarianceCurve",
        [](const Date& reference_date,
           const std::vector<Date>& dates,
           const std::vector<Volatility>& black_vol_curve,
           const DayCounter& day_counter,
           bool force_monotone_variance) {
            return Handle<BlackVolTermStructure>(
                ext::make_shared<BlackVarianceCurve>(
                    reference_date,
                    dates,
                    black_vol_curve,
                    day_counter,
                    force_monotone_variance));
        },
        nb::arg("reference_date"),
        nb::arg("dates"),
        nb::arg("black_vol_curve"),
        nb::arg("day_counter"),
        nb::arg("force_monotone_variance") = true,
        "Black variance curve handle (ATM vol vs expiry).");

    nb::class_<VarianceSwap>(m, "VarianceSwap")
        .def(
            "__init__",
            [](VarianceSwap* self,
               Position::Type position,
               Real strike,
               Real notional,
               const Date& start_date,
               const Date& maturity_date) {
                new (self) VarianceSwap(
                    position, strike, notional, start_date, maturity_date);
            },
            nb::arg("position"),
            nb::arg("strike"),
            nb::arg("notional"),
            nb::arg("start_date"),
            nb::arg("maturity_date"),
            "Forward variance swap (unseasoned). Strike is a variance level.")
        .def("NPV", [](VarianceSwap& swap) { return swap.NPV(); })
        .def("variance", [](VarianceSwap& swap) { return swap.variance(); })
        .def("is_expired", [](const VarianceSwap& swap) {
            return swap.isExpired();
        })
        .def("strike", [](const VarianceSwap& swap) { return swap.strike(); })
        .def("notional", [](const VarianceSwap& swap) {
            return swap.notional();
        })
        .def("position", [](const VarianceSwap& swap) {
            return swap.position();
        })
        .def("start_date", [](const VarianceSwap& swap) {
            return swap.startDate();
        })
        .def("maturity_date", [](const VarianceSwap& swap) {
            return swap.maturityDate();
        })
        .def(
            "set_replicating_pricing_engine",
            [](VarianceSwap& swap,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const std::vector<Real>& call_strikes,
               const std::vector<Real>& put_strikes,
               Real dk) {
                swap.setPricingEngine(
                    ext::make_shared<ReplicatingVarianceSwapEngine>(
                        process, dk, call_strikes, put_strikes));
            },
            nb::arg("process"),
            nb::arg("call_strikes"),
            nb::arg("put_strikes"),
            nb::arg("dk") = 5.0,
            "Attach ReplicatingVarianceSwapEngine (Demeterfi–Derman–Kamal–Zou).")
        .def(
            "set_mc_pricing_engine",
            [](VarianceSwap& swap,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                QL_REQUIRE(
                    !(time_steps.has_value() && steps_per_year.has_value()),
                    "set only one of time_steps or steps_per_year");
                QL_REQUIRE(
                    !(required_samples.has_value() &&
                      required_tolerance.has_value()),
                    "set only one of required_samples or required_tolerance");
                auto maker = MakeMCVarianceSwapEngine<PseudoRandom>(process)
                                 .withSeed(seed)
                                 .withAntitheticVariate(antithetic)
                                 .withBrownianBridge(brownian_bridge);
                if (time_steps.has_value())
                    maker.withSteps(*time_steps);
                else if (steps_per_year.has_value())
                    maker.withStepsPerYear(*steps_per_year);
                else
                    maker.withStepsPerYear(Size(250));
                if (required_samples.has_value())
                    maker.withSamples(*required_samples);
                else if (required_tolerance.has_value())
                    maker.withAbsoluteTolerance(*required_tolerance);
                else
                    maker.withSamples(Size(1023));
                swap.setPricingEngine(maker);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 42UL,
            nb::arg("antithetic") = false,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCVarianceSwapEngine<PseudoRandom> "
            "(defaults match the Derman MC suite: 250 steps/year, 1023 samples).");

    m.def(
        "ReplicatingVarianceSwapEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process,
           const std::vector<Real>& /*call_strikes*/,
           const std::vector<Real>& /*put_strikes*/,
           Real /*dk*/) {
            return process;
        },
        nb::arg("process"),
        nb::arg("call_strikes"),
        nb::arg("put_strikes"),
        nb::arg("dk") = 5.0,
        "Factory alias: pass args to "
        "VarianceSwap.set_replicating_pricing_engine.");

    m.def(
        "MCVarianceSwapEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Documentation alias — use "
        "VarianceSwap.set_mc_pricing_engine instead.");

    // --- Phase 110: VarianceOption + IntegralHestonVarianceOptionEngine ---
    nb::class_<VarianceOption>(m, "VarianceOption")
        .def(
            "__init__",
            [](VarianceOption* self,
               const PlainVanillaPayoff& payoff,
               Real notional,
               const Date& start_date,
               const Date& maturity_date) {
                new (self) VarianceOption(
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    notional,
                    start_date,
                    maturity_date);
            },
            nb::arg("payoff"),
            nb::arg("notional"),
            nb::arg("start_date"),
            nb::arg("maturity_date"),
            "Variance option on realized variance (unseasoned).")
        .def("NPV", [](VarianceOption& opt) { return opt.NPV(); })
        .def("is_expired", [](const VarianceOption& opt) {
            return opt.isExpired();
        })
        .def("notional", [](const VarianceOption& opt) { return opt.notional(); })
        .def("start_date", [](const VarianceOption& opt) {
            return opt.startDate();
        })
        .def("maturity_date", [](const VarianceOption& opt) {
            return opt.maturityDate();
        })
        .def(
            "set_integral_heston_pricing_engine",
            [](VarianceOption& opt,
               const ext::shared_ptr<HestonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<IntegralHestonVarianceOptionEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach IntegralHestonVarianceOptionEngine.");

    m.def(
        "IntegralHestonVarianceOptionEngine",
        [](const ext::shared_ptr<HestonProcess>& process) { return process; },
        nb::arg("process"),
        "Factory alias: pass args to "
        "VarianceOption.set_integral_heston_pricing_engine.");

    // --- Phase 34: cliquet / ratchet options (standalone; OneAssetOption MI)
    nb::class_<CliquetOption>(m, "CliquetOption")
        .def(
            "__init__",
            [](CliquetOption* self,
               const PercentageStrikePayoff& payoff,
               const EuropeanExercise& exercise,
               const std::vector<Date>& reset_dates) {
                new (self) CliquetOption(
                    ext::make_shared<PercentageStrikePayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise),
                    reset_dates);
            },
            nb::arg("payoff"),
            nb::arg("exercise"),
            nb::arg("reset_dates"),
            "Forward-starting (ratchet) option series; strike resets to a "
            "percentage of spot at each reset date (Haug p.37).")
        .def("NPV", [](CliquetOption& opt) { return opt.NPV(); })
        .def("delta", [](CliquetOption& opt) { return opt.delta(); })
        .def("gamma", [](CliquetOption& opt) { return opt.gamma(); })
        .def("vega", [](CliquetOption& opt) { return opt.vega(); })
        .def("is_expired", &CliquetOption::isExpired)
        .def(
            "set_pricing_engine",
            [](CliquetOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticCliquetEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticCliquetEngine.");

    m.def(
        "AnalyticCliquetEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "CliquetOption.set_pricing_engine.");

    // --- Phase 35: forward vanilla options (standalone; OneAssetOption MI) ---
    nb::class_<ForwardVanillaOption>(m, "ForwardVanillaOption")
        .def(
            "__init__",
            [](ForwardVanillaOption* self,
               Real moneyness,
               const Date& reset_date,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ForwardVanillaOption(
                    moneyness,
                    reset_date,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("moneyness"),
            nb::arg("reset_date"),
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Strike-resetting forward-start vanilla (Haug p.37). "
            "Payoff strike is ignored; moneyness * spot at reset is used.")
        .def("NPV", [](ForwardVanillaOption& opt) { return opt.NPV(); })
        .def("delta", [](ForwardVanillaOption& opt) { return opt.delta(); })
        .def("gamma", [](ForwardVanillaOption& opt) { return opt.gamma(); })
        .def("vega", [](ForwardVanillaOption& opt) { return opt.vega(); })
        .def("is_expired", &ForwardVanillaOption::isExpired)
        .def(
            "set_pricing_engine",
            [](ForwardVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<
                        ForwardVanillaEngine<AnalyticEuropeanEngine>>(
                        process));
            },
            nb::arg("process"),
            "Attach ForwardVanillaEngine<AnalyticEuropeanEngine>.")
        .def(
            "set_performance_pricing_engine",
            [](ForwardVanillaOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<ForwardPerformanceVanillaEngine<
                        AnalyticEuropeanEngine>>(process));
            },
            nb::arg("process"),
            "Attach ForwardPerformanceVanillaEngine<AnalyticEuropeanEngine>.")
        .def(
            "set_heston_forward_pricing_engine",
            [](ForwardVanillaOption& opt,
               const ext::shared_ptr<HestonProcess>& process,
               Size integration_order) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticHestonForwardEuropeanEngine>(
                        process, integration_order));
            },
            nb::arg("process"),
            nb::arg("integration_order") = Size(144),
            "Attach AnalyticHestonForwardEuropeanEngine.");

    m.def(
        "ForwardVanillaEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "ForwardVanillaOption.set_pricing_engine.");

    m.def(
        "ForwardPerformanceVanillaEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "ForwardVanillaOption.set_performance_pricing_engine.");

    // --- Phase 74: compound options (standalone; OneAssetOption MI) ---------
    nb::class_<CompoundOption>(m, "CompoundOption")
        .def(
            "__init__",
            [](CompoundOption* self,
               const PlainVanillaPayoff& mother_payoff,
               const EuropeanExercise& mother_exercise,
               const PlainVanillaPayoff& daughter_payoff,
               const EuropeanExercise& daughter_exercise) {
                new (self) CompoundOption(
                    ext::make_shared<PlainVanillaPayoff>(mother_payoff),
                    ext::make_shared<EuropeanExercise>(mother_exercise),
                    ext::make_shared<PlainVanillaPayoff>(daughter_payoff),
                    ext::make_shared<EuropeanExercise>(daughter_exercise));
            },
            nb::arg("mother_payoff"),
            nb::arg("mother_exercise"),
            nb::arg("daughter_payoff"),
            nb::arg("daughter_exercise"),
            "Option on option (Wystup / Haug). Mother is the compound "
            "option; daughter is the underlying vanilla.")
        .def("NPV", [](CompoundOption& opt) { return opt.NPV(); })
        .def("delta", [](CompoundOption& opt) { return opt.delta(); })
        .def("gamma", [](CompoundOption& opt) { return opt.gamma(); })
        .def("vega", [](CompoundOption& opt) { return opt.vega(); })
        .def("theta", [](CompoundOption& opt) { return opt.theta(); })
        .def("is_expired", [](const CompoundOption& opt) {
            return opt.isExpired();
        })
        .def(
            "set_pricing_engine",
            [](CompoundOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticCompoundOptionEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticCompoundOptionEngine (Wystup closed form).");

    m.def(
        "AnalyticCompoundOptionEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "CompoundOption.set_pricing_engine.");

    // --- Phase 25/26: double-barrier options (standalone; OneAssetOption MI)
    nb::enum_<DoubleBarrier::Type>(m, "DoubleBarrierType")
        .value("KnockIn", DoubleBarrier::KnockIn)
        .value("KnockOut", DoubleBarrier::KnockOut)
        .value("KIKO", DoubleBarrier::KIKO)
        .value("KOKI", DoubleBarrier::KOKI);

    nb::class_<DoubleBarrierOption>(m, "DoubleBarrierOption")
        .def(
            "__init__",
            [](DoubleBarrierOption* self,
               DoubleBarrier::Type barrier_type,
               Real barrier_lo,
               Real barrier_hi,
               Real rebate,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) DoubleBarrierOption(
                    barrier_type,
                    barrier_lo,
                    barrier_hi,
                    rebate,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier_lo"),
            nb::arg("barrier_hi"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](DoubleBarrierOption* self,
               DoubleBarrier::Type barrier_type,
               Real barrier_lo,
               Real barrier_hi,
               Real rebate,
               const CashOrNothingPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) DoubleBarrierOption(
                    barrier_type,
                    barrier_lo,
                    barrier_hi,
                    rebate,
                    ext::make_shared<CashOrNothingPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier_lo"),
            nb::arg("barrier_hi"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def(
            "__init__",
            [](DoubleBarrierOption* self,
               DoubleBarrier::Type barrier_type,
               Real barrier_lo,
               Real barrier_hi,
               Real rebate,
               const CashOrNothingPayoff& payoff,
               const AmericanExercise& exercise) {
                new (self) DoubleBarrierOption(
                    barrier_type,
                    barrier_lo,
                    barrier_hi,
                    rebate,
                    ext::make_shared<CashOrNothingPayoff>(payoff),
                    ext::make_shared<AmericanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier_lo"),
            nb::arg("barrier_hi"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV", [](DoubleBarrierOption& opt) { return opt.NPV(); })
        .def("delta", [](DoubleBarrierOption& opt) { return opt.delta(); })
        .def("gamma", [](DoubleBarrierOption& opt) { return opt.gamma(); })
        .def("vega", [](DoubleBarrierOption& opt) { return opt.vega(); })
        .def(
            "implied_volatility",
            [](DoubleBarrierOption& opt,
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
            nb::arg("max_vol") = 4.0,
            "Implied Black vol matching a target NPV "
            "(AnalyticDoubleBarrierEngine; European vanilla only).")
        .def(
            "set_pricing_engine",
            [](DoubleBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticDoubleBarrierEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticDoubleBarrierEngine (Ikeda/Kunitomo).")
        .def(
            "set_suo_wang_pricing_engine",
            [](DoubleBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               int series) {
                opt.setPricingEngine(
                    ext::make_shared<SuoWangDoubleBarrierEngine>(
                        process, series));
            },
            nb::arg("process"),
            nb::arg("series") = 5,
            "Attach SuoWangDoubleBarrierEngine (Wulin Suo / Yong Wang).")
        .def(
            "set_binary_pricing_engine",
            [](DoubleBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticDoubleBarrierBinaryEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticDoubleBarrierBinaryEngine (Hui / Haug p.180). "
            "Use European exercise for KnockIn/KnockOut; American for "
            "KIKO/KOKI.")
        .def(
            "set_fd_heston_pricing_engine",
            [](DoubleBarrierOption& opt,
               const ext::shared_ptr<HestonModel>& model,
               Size t_grid,
               Size x_grid,
               Size v_grid,
               Size damping_steps,
               const FdmSchemeDesc& scheme_desc) {
                opt.setPricingEngine(
                    ext::make_shared<FdHestonDoubleBarrierEngine>(
                        model,
                        t_grid,
                        x_grid,
                        v_grid,
                        damping_steps,
                        scheme_desc));
            },
            nb::arg("model"),
            nb::arg("t_grid") = 100,
            nb::arg("x_grid") = 100,
            nb::arg("v_grid") = 50,
            nb::arg("damping_steps") = 0,
            nb::arg("scheme_desc") = FdmSchemeDesc::Hundsdorfer(),
            "Attach FdHestonDoubleBarrierEngine (default Hundsdorfer scheme).")
        .def("error_estimate",
             [](DoubleBarrierOption& opt) { return opt.errorEstimate(); })
        .def(
            "set_mc_pricing_engine",
            [](DoubleBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                attach_mc_double_barrier_engine(
                    opt, process, time_steps, steps_per_year, required_samples,
                    required_tolerance, seed, antithetic, brownian_bridge);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 1UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCDoubleBarrierEngine<PseudoRandom>.");

    m.def(
        "AnalyticDoubleBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "DoubleBarrierOption.set_pricing_engine.");

    m.def(
        "SuoWangDoubleBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "DoubleBarrierOption.set_suo_wang_pricing_engine.");

    m.def(
        "AnalyticDoubleBarrierBinaryEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "DoubleBarrierOption.set_binary_pricing_engine.");

    m.def(
        "FdHestonDoubleBarrierEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "DoubleBarrierOption.set_fd_heston_pricing_engine.");

    m.def(
        "MCDoubleBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Documentation alias — use "
        "DoubleBarrierOption.set_mc_pricing_engine instead.");

    // --- Phase 43: quanto double-barrier options (standalone wrapper) -------
    using QuantoDoubleBarrierEngine =
        QuantoEngine<DoubleBarrierOption, AnalyticDoubleBarrierEngine>;

    nb::class_<QuantoDoubleBarrierOption>(m, "QuantoDoubleBarrierOption")
        .def(
            "__init__",
            [](QuantoDoubleBarrierOption* self,
               DoubleBarrier::Type barrier_type,
               Real barrier_lo,
               Real barrier_hi,
               Real rebate,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) QuantoDoubleBarrierOption(
                    barrier_type,
                    barrier_lo,
                    barrier_hi,
                    rebate,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("barrier_type"),
            nb::arg("barrier_lo"),
            nb::arg("barrier_hi"),
            nb::arg("rebate"),
            nb::arg("payoff"),
            nb::arg("exercise"),
            "Quanto double-barrier option; payoff currency ≠ asset currency.")
        .def("NPV",
             [](QuantoDoubleBarrierOption& opt) { return opt.NPV(); })
        .def("delta",
             [](QuantoDoubleBarrierOption& opt) { return opt.delta(); })
        .def("gamma",
             [](QuantoDoubleBarrierOption& opt) { return opt.gamma(); })
        .def("vega",
             [](QuantoDoubleBarrierOption& opt) { return opt.vega(); })
        .def("qvega", &QuantoDoubleBarrierOption::qvega)
        .def("qrho", &QuantoDoubleBarrierOption::qrho)
        .def("qlambda", &QuantoDoubleBarrierOption::qlambda)
        .def("is_expired", &QuantoDoubleBarrierOption::isExpired)
        .def(
            "set_pricing_engine",
            [](QuantoDoubleBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               const Handle<Quote>& correlation) {
                opt.setPricingEngine(
                    ext::make_shared<QuantoDoubleBarrierEngine>(
                        process,
                        foreign_risk_free_rate,
                        exchange_rate_volatility,
                        correlation));
            },
            nb::arg("process"),
            nb::arg("foreign_risk_free_rate"),
            nb::arg("exchange_rate_volatility"),
            nb::arg("correlation"),
            "Attach QuantoEngine<DoubleBarrierOption, "
            "AnalyticDoubleBarrierEngine>.")
        .def(
            "set_pricing_engine",
            [](QuantoDoubleBarrierOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               const Handle<YieldTermStructure>& foreign_risk_free_rate,
               const Handle<BlackVolTermStructure>& exchange_rate_volatility,
               Real correlation) {
                opt.setPricingEngine(
                    ext::make_shared<QuantoDoubleBarrierEngine>(
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
            "Attach quanto-double-barrier engine from a scalar correlation.");

    m.def(
        "QuantoDoubleBarrierEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias documentation token — prefer "
        "QuantoDoubleBarrierOption.set_pricing_engine(...).");

    // --- Phase 27: continuous lookbacks (standalone; OneAssetOption MI) -----
    nb::class_<ContinuousFloatingLookbackOption>(
        m, "ContinuousFloatingLookbackOption")
        .def(
            "__init__",
            [](ContinuousFloatingLookbackOption* self,
               Real current_minmax,
               const FloatingTypePayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ContinuousFloatingLookbackOption(
                    current_minmax,
                    ext::make_shared<FloatingTypePayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("current_minmax"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV",
             [](ContinuousFloatingLookbackOption& opt) { return opt.NPV(); })
        .def("delta",
             [](ContinuousFloatingLookbackOption& opt) { return opt.delta(); })
        .def("gamma",
             [](ContinuousFloatingLookbackOption& opt) { return opt.gamma(); })
        .def(
            "set_pricing_engine",
            [](ContinuousFloatingLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticContinuousFloatingLookbackEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticContinuousFloatingLookbackEngine.")
        .def("error_estimate",
             [](ContinuousFloatingLookbackOption& opt) {
                 return opt.errorEstimate();
             })
        .def(
            "set_mc_pricing_engine",
            [](ContinuousFloatingLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                attach_mc_lookback_engine(opt, process, time_steps, steps_per_year,
                                          required_samples, required_tolerance,
                                          seed, antithetic, brownian_bridge);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 1UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCLookbackEngine<ContinuousFloatingLookbackOption>.");

    nb::class_<ContinuousFixedLookbackOption>(m, "ContinuousFixedLookbackOption")
        .def(
            "__init__",
            [](ContinuousFixedLookbackOption* self,
               Real current_minmax,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ContinuousFixedLookbackOption(
                    current_minmax,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("current_minmax"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV",
             [](ContinuousFixedLookbackOption& opt) { return opt.NPV(); })
        .def("delta",
             [](ContinuousFixedLookbackOption& opt) { return opt.delta(); })
        .def("gamma",
             [](ContinuousFixedLookbackOption& opt) { return opt.gamma(); })
        .def(
            "set_pricing_engine",
            [](ContinuousFixedLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(
                    ext::make_shared<AnalyticContinuousFixedLookbackEngine>(
                        process));
            },
            nb::arg("process"),
            "Attach AnalyticContinuousFixedLookbackEngine.")
        .def("error_estimate",
             [](ContinuousFixedLookbackOption& opt) {
                 return opt.errorEstimate();
             })
        .def(
            "set_mc_pricing_engine",
            [](ContinuousFixedLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                attach_mc_lookback_engine(opt, process, time_steps, steps_per_year,
                                          required_samples, required_tolerance,
                                          seed, antithetic, brownian_bridge);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 1UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCLookbackEngine<ContinuousFixedLookbackOption>.");

    m.def(
        "AnalyticContinuousFloatingLookbackEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for ContinuousFloatingLookbackOption.set_pricing_engine.");

    m.def(
        "AnalyticContinuousFixedLookbackEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for ContinuousFixedLookbackOption.set_pricing_engine.");

    // --- Phase 28: partial-time continuous lookbacks (standalone wrappers) ---
    nb::class_<ContinuousPartialFloatingLookbackOption>(
        m, "ContinuousPartialFloatingLookbackOption")
        .def(
            "__init__",
            [](ContinuousPartialFloatingLookbackOption* self,
               Real current_minmax,
               Real lambda,
               const Date& lookback_period_end,
               const FloatingTypePayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ContinuousPartialFloatingLookbackOption(
                    current_minmax,
                    lambda,
                    lookback_period_end,
                    ext::make_shared<FloatingTypePayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("current_minmax"),
            nb::arg("lambda_"),
            nb::arg("lookback_period_end"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV",
             [](ContinuousPartialFloatingLookbackOption& opt) {
                 return opt.NPV();
             })
        .def("delta",
             [](ContinuousPartialFloatingLookbackOption& opt) {
                 return opt.delta();
             })
        .def("gamma",
             [](ContinuousPartialFloatingLookbackOption& opt) {
                 return opt.gamma();
             })
        .def(
            "set_pricing_engine",
            [](ContinuousPartialFloatingLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(ext::make_shared<
                    AnalyticContinuousPartialFloatingLookbackEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticContinuousPartialFloatingLookbackEngine.")
        .def("error_estimate",
             [](ContinuousPartialFloatingLookbackOption& opt) {
                 return opt.errorEstimate();
             })
        .def(
            "set_mc_pricing_engine",
            [](ContinuousPartialFloatingLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                attach_mc_lookback_engine(opt, process, time_steps, steps_per_year,
                                          required_samples, required_tolerance,
                                          seed, antithetic, brownian_bridge);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 1UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCLookbackEngine<"
            "ContinuousPartialFloatingLookbackOption>.");

    nb::class_<ContinuousPartialFixedLookbackOption>(
        m, "ContinuousPartialFixedLookbackOption")
        .def(
            "__init__",
            [](ContinuousPartialFixedLookbackOption* self,
               const Date& lookback_period_start,
               const PlainVanillaPayoff& payoff,
               const EuropeanExercise& exercise) {
                new (self) ContinuousPartialFixedLookbackOption(
                    lookback_period_start,
                    ext::make_shared<PlainVanillaPayoff>(payoff),
                    ext::make_shared<EuropeanExercise>(exercise));
            },
            nb::arg("lookback_period_start"),
            nb::arg("payoff"),
            nb::arg("exercise"))
        .def("NPV",
             [](ContinuousPartialFixedLookbackOption& opt) {
                 return opt.NPV();
             })
        .def("delta",
             [](ContinuousPartialFixedLookbackOption& opt) {
                 return opt.delta();
             })
        .def("gamma",
             [](ContinuousPartialFixedLookbackOption& opt) {
                 return opt.gamma();
             })
        .def(
            "set_pricing_engine",
            [](ContinuousPartialFixedLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process) {
                opt.setPricingEngine(ext::make_shared<
                    AnalyticContinuousPartialFixedLookbackEngine>(process));
            },
            nb::arg("process"),
            "Attach AnalyticContinuousPartialFixedLookbackEngine.")
        .def("error_estimate",
             [](ContinuousPartialFixedLookbackOption& opt) {
                 return opt.errorEstimate();
             })
        .def(
            "set_mc_pricing_engine",
            [](ContinuousPartialFixedLookbackOption& opt,
               const ext::shared_ptr<BlackScholesMertonProcess>& process,
               std::optional<Size> time_steps,
               std::optional<Size> steps_per_year,
               std::optional<Size> required_samples,
               std::optional<Real> required_tolerance,
               unsigned long seed,
               bool antithetic,
               bool brownian_bridge) {
                attach_mc_lookback_engine(opt, process, time_steps, steps_per_year,
                                          required_samples, required_tolerance,
                                          seed, antithetic, brownian_bridge);
            },
            nb::arg("process"),
            nb::arg("time_steps") = nb::none(),
            nb::arg("steps_per_year") = nb::none(),
            nb::arg("required_samples") = nb::none(),
            nb::arg("required_tolerance") = nb::none(),
            nb::arg("seed") = 1UL,
            nb::arg("antithetic") = true,
            nb::arg("brownian_bridge") = false,
            "Attach MakeMCLookbackEngine<"
            "ContinuousPartialFixedLookbackOption>.");

    m.def(
        "AnalyticContinuousPartialFloatingLookbackEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for "
        "ContinuousPartialFloatingLookbackOption.set_pricing_engine.");

    m.def(
        "AnalyticContinuousPartialFixedLookbackEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Factory alias for "
        "ContinuousPartialFixedLookbackOption.set_pricing_engine.");

    m.def(
        "MCLookbackEngine",
        [](const ext::shared_ptr<BlackScholesMertonProcess>& process) {
            return process;
        },
        nb::arg("process"),
        "Documentation alias — use "
        "Continuous*LookbackOption.set_mc_pricing_engine instead.");

    // --- Cap / Floor + Black engine (standalone; CapFloor uses MI) ----------
    nb::enum_<CapFloor::Type>(m, "CapFloorType")
        .value("Cap", CapFloor::Cap)
        .value("Floor", CapFloor::Floor)
        .value("Collar", CapFloor::Collar);

    nb::class_<CapFloor>(m, "CapFloor")
        .def(
            "__init__",
            [](CapFloor* self,
               CapFloor::Type type,
               const Schedule& schedule,
               const ext::shared_ptr<IborIndex>& index,
               Rate strike,
               Real nominal,
               Natural fixing_days) {
                QL_REQUIRE(type == CapFloor::Cap || type == CapFloor::Floor,
                           "CapFloor constructor supports Cap or Floor");
                const BusinessDayConvention conv = index->businessDayConvention();
                Leg leg = IborLeg(schedule, index)
                              .withNotionals(nominal)
                              .withPaymentDayCounter(index->dayCounter())
                              .withPaymentAdjustment(conv)
                              .withFixingDays(fixing_days);
                new (self) CapFloor(type, leg, std::vector<Rate>(1, strike));
            },
            nb::arg("type"),
            nb::arg("schedule"),
            nb::arg("index"),
            nb::arg("strike"),
            nb::arg("nominal") = 100.0,
            nb::arg("fixing_days") = 2,
            "Build a Cap/Floor from an Ibor schedule (includes all caplets).")
        .def("NPV", [](CapFloor& cf) { return cf.NPV(); })
        .def(
            "atm_rate",
            [](const CapFloor& cf, const Handle<YieldTermStructure>& discount) {
                return cf.atmRate(**discount);
            },
            nb::arg("discount_curve"))
        .def("start_date",
             [](const CapFloor& cf) { return cf.startDate(); })
        .def("maturity_date",
             [](const CapFloor& cf) { return cf.maturityDate(); })
        .def("type", [](const CapFloor& cf) { return cf.type(); })
        .def(
            "set_pricing_engine",
            [](CapFloor& cf,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility volatility,
               const DayCounter& day_counter,
               Real displacement) {
                cf.setPricingEngine(ext::make_shared<BlackCapFloorEngine>(
                    discount_curve, volatility, day_counter, displacement));
            },
            nb::arg("discount_curve"),
            nb::arg("volatility"),
            nb::arg("day_counter") = DayCounter(Actual365Fixed()),
            nb::arg("displacement") = 0.0)
        .def(
            "implied_volatility",
            [](const CapFloor& cf,
               Real target_price,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility guess,
               Real accuracy,
               Natural max_evaluations,
               Volatility min_vol,
               Volatility max_vol,
               VolatilityType vol_type,
               Real displacement) {
                return cf.impliedVolatility(target_price,
                                            discount_curve,
                                            guess,
                                            accuracy,
                                            max_evaluations,
                                            min_vol,
                                            max_vol,
                                            vol_type,
                                            displacement);
            },
            nb::arg("target_price"),
            nb::arg("discount_curve"),
            nb::arg("guess") = 0.10,
            nb::arg("accuracy") = 1.0e-4,
            nb::arg("max_evaluations") = 100,
            nb::arg("min_vol") = 1.0e-7,
            nb::arg("max_vol") = 4.0,
            nb::arg("vol_type") = ShiftedLognormal,
            nb::arg("displacement") = 0.0,
            "Implied Black/normal term volatility matching a target NPV.");

    // --- Phase 107: Collar (standalone CapFloor wrapper) ---
    nb::class_<Collar>(m, "Collar")
        .def(
            "__init__",
            [](Collar* self,
               const Schedule& schedule,
               const ext::shared_ptr<IborIndex>& index,
               Rate cap_strike,
               Rate floor_strike,
               Real nominal,
               Natural fixing_days) {
                const BusinessDayConvention conv = index->businessDayConvention();
                Leg leg = IborLeg(schedule, index)
                              .withNotionals(nominal)
                              .withPaymentDayCounter(index->dayCounter())
                              .withPaymentAdjustment(conv)
                              .withFixingDays(fixing_days);
                new (self) Collar(leg,
                                  std::vector<Rate>(1, cap_strike),
                                  std::vector<Rate>(1, floor_strike));
            },
            nb::arg("schedule"),
            nb::arg("index"),
            nb::arg("cap_strike"),
            nb::arg("floor_strike"),
            nb::arg("nominal") = 100.0,
            nb::arg("fixing_days") = 2,
            "Build a Collar from an Ibor schedule.")
        .def("NPV", [](Collar& c) { return c.NPV(); })
        .def(
            "atm_rate",
            [](const Collar& c, const Handle<YieldTermStructure>& discount) {
                return c.atmRate(**discount);
            },
            nb::arg("discount_curve"))
        .def("start_date", [](const Collar& c) { return c.startDate(); })
        .def("maturity_date", [](const Collar& c) { return c.maturityDate(); })
        .def("type", [](const Collar& c) { return c.type(); })
        .def(
            "set_pricing_engine",
            [](Collar& c,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility volatility,
               const DayCounter& day_counter,
               Real displacement) {
                c.setPricingEngine(ext::make_shared<BlackCapFloorEngine>(
                    discount_curve, volatility, day_counter, displacement));
            },
            nb::arg("discount_curve"),
            nb::arg("volatility"),
            nb::arg("day_counter") = DayCounter(Actual365Fixed()),
            nb::arg("displacement") = 0.0)
        .def(
            "implied_volatility",
            [](const Collar& c,
               Real target_price,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility guess,
               Real accuracy,
               Natural max_evaluations,
               Volatility min_vol,
               Volatility max_vol,
               VolatilityType vol_type,
               Real displacement) {
                return c.impliedVolatility(target_price,
                                           discount_curve,
                                           guess,
                                           accuracy,
                                           max_evaluations,
                                           min_vol,
                                           max_vol,
                                           vol_type,
                                           displacement);
            },
            nb::arg("target_price"),
            nb::arg("discount_curve"),
            nb::arg("guess") = 0.10,
            nb::arg("accuracy") = 1.0e-4,
            nb::arg("max_evaluations") = 100,
            nb::arg("min_vol") = 1.0e-7,
            nb::arg("max_vol") = 4.0,
            nb::arg("vol_type") = ShiftedLognormal,
            nb::arg("displacement") = 0.0);

    // --- Phase 108: Cap / Floor (standalone CapFloor wrappers) ---
    nb::class_<Cap>(m, "Cap")
        .def(
            "__init__",
            [](Cap* self,
               const Schedule& schedule,
               const ext::shared_ptr<IborIndex>& index,
               Rate strike,
               Real nominal,
               Natural fixing_days) {
                const BusinessDayConvention conv = index->businessDayConvention();
                Leg leg = IborLeg(schedule, index)
                              .withNotionals(nominal)
                              .withPaymentDayCounter(index->dayCounter())
                              .withPaymentAdjustment(conv)
                              .withFixingDays(fixing_days);
                new (self) Cap(leg, std::vector<Rate>(1, strike));
            },
            nb::arg("schedule"),
            nb::arg("index"),
            nb::arg("strike"),
            nb::arg("nominal") = 100.0,
            nb::arg("fixing_days") = 2,
            "Build a Cap from an Ibor schedule.")
        .def("NPV", [](Cap& c) { return c.NPV(); })
        .def(
            "atm_rate",
            [](const Cap& c, const Handle<YieldTermStructure>& discount) {
                return c.atmRate(**discount);
            },
            nb::arg("discount_curve"))
        .def("start_date", [](const Cap& c) { return c.startDate(); })
        .def("maturity_date", [](const Cap& c) { return c.maturityDate(); })
        .def("type", [](const Cap& c) { return c.type(); })
        .def(
            "set_pricing_engine",
            [](Cap& c,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility volatility,
               const DayCounter& day_counter,
               Real displacement) {
                c.setPricingEngine(ext::make_shared<BlackCapFloorEngine>(
                    discount_curve, volatility, day_counter, displacement));
            },
            nb::arg("discount_curve"),
            nb::arg("volatility"),
            nb::arg("day_counter") = DayCounter(Actual365Fixed()),
            nb::arg("displacement") = 0.0)
        .def(
            "implied_volatility",
            [](const Cap& c,
               Real target_price,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility guess,
               Real accuracy,
               Natural max_evaluations,
               Volatility min_vol,
               Volatility max_vol,
               VolatilityType vol_type,
               Real displacement) {
                return c.impliedVolatility(target_price,
                                           discount_curve,
                                           guess,
                                           accuracy,
                                           max_evaluations,
                                           min_vol,
                                           max_vol,
                                           vol_type,
                                           displacement);
            },
            nb::arg("target_price"),
            nb::arg("discount_curve"),
            nb::arg("guess") = 0.10,
            nb::arg("accuracy") = 1.0e-4,
            nb::arg("max_evaluations") = 100,
            nb::arg("min_vol") = 1.0e-7,
            nb::arg("max_vol") = 4.0,
            nb::arg("vol_type") = ShiftedLognormal,
            nb::arg("displacement") = 0.0);

    nb::class_<Floor>(m, "Floor")
        .def(
            "__init__",
            [](Floor* self,
               const Schedule& schedule,
               const ext::shared_ptr<IborIndex>& index,
               Rate strike,
               Real nominal,
               Natural fixing_days) {
                const BusinessDayConvention conv = index->businessDayConvention();
                Leg leg = IborLeg(schedule, index)
                              .withNotionals(nominal)
                              .withPaymentDayCounter(index->dayCounter())
                              .withPaymentAdjustment(conv)
                              .withFixingDays(fixing_days);
                new (self) Floor(leg, std::vector<Rate>(1, strike));
            },
            nb::arg("schedule"),
            nb::arg("index"),
            nb::arg("strike"),
            nb::arg("nominal") = 100.0,
            nb::arg("fixing_days") = 2,
            "Build a Floor from an Ibor schedule.")
        .def("NPV", [](Floor& c) { return c.NPV(); })
        .def(
            "atm_rate",
            [](const Floor& c, const Handle<YieldTermStructure>& discount) {
                return c.atmRate(**discount);
            },
            nb::arg("discount_curve"))
        .def("start_date", [](const Floor& c) { return c.startDate(); })
        .def("maturity_date", [](const Floor& c) { return c.maturityDate(); })
        .def("type", [](const Floor& c) { return c.type(); })
        .def(
            "set_pricing_engine",
            [](Floor& c,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility volatility,
               const DayCounter& day_counter,
               Real displacement) {
                c.setPricingEngine(ext::make_shared<BlackCapFloorEngine>(
                    discount_curve, volatility, day_counter, displacement));
            },
            nb::arg("discount_curve"),
            nb::arg("volatility"),
            nb::arg("day_counter") = DayCounter(Actual365Fixed()),
            nb::arg("displacement") = 0.0)
        .def(
            "implied_volatility",
            [](const Floor& c,
               Real target_price,
               const Handle<YieldTermStructure>& discount_curve,
               Volatility guess,
               Real accuracy,
               Natural max_evaluations,
               Volatility min_vol,
               Volatility max_vol,
               VolatilityType vol_type,
               Real displacement) {
                return c.impliedVolatility(target_price,
                                           discount_curve,
                                           guess,
                                           accuracy,
                                           max_evaluations,
                                           min_vol,
                                           max_vol,
                                           vol_type,
                                           displacement);
            },
            nb::arg("target_price"),
            nb::arg("discount_curve"),
            nb::arg("guess") = 0.10,
            nb::arg("accuracy") = 1.0e-4,
            nb::arg("max_evaluations") = 100,
            nb::arg("min_vol") = 1.0e-7,
            nb::arg("max_vol") = 4.0,
            nb::arg("vol_type") = ShiftedLognormal,
            nb::arg("displacement") = 0.0);

    m.def(
        "make_cap",
        [](const Period& tenor,
           const ext::shared_ptr<IborIndex>& index,
           Rate strike,
           Real nominal,
           const Period& forward_start) {
            CapFloor cap = MakeCapFloor(CapFloor::Cap, tenor, index, strike,
                                        forward_start)
                               .withNominal(nominal);
            return cap;
        },
        nb::arg("tenor"),
        nb::arg("index"),
        nb::arg("strike"),
        nb::arg("nominal") = 100.0,
        nb::arg("forward_start") = Period(0, Days),
        "Build a standard Cap via QuantLib::MakeCapFloor.");

    m.def(
        "make_floor",
        [](const Period& tenor,
           const ext::shared_ptr<IborIndex>& index,
           Rate strike,
           Real nominal,
           const Period& forward_start) {
            CapFloor floor = MakeCapFloor(CapFloor::Floor, tenor, index, strike,
                                          forward_start)
                                 .withNominal(nominal);
            return floor;
        },
        nb::arg("tenor"),
        nb::arg("index"),
        nb::arg("strike"),
        nb::arg("nominal") = 100.0,
        nb::arg("forward_start") = Period(0, Days),
        "Build a standard Floor via QuantLib::MakeCapFloor.");

    m.def(
        "BlackCapFloorEngine",
        [](const Handle<YieldTermStructure>& discount_curve,
           Volatility volatility,
           const DayCounter& day_counter,
           Real displacement) {
            // Token bundle for documentation parity with AnalyticEuropeanEngine.
            // Prefer CapFloor.set_pricing_engine(discount_curve, volatility, ...).
            return discount_curve;
        },
        nb::arg("discount_curve"),
        nb::arg("volatility"),
        nb::arg("day_counter") = DayCounter(Actual365Fixed()),
        nb::arg("displacement") = 0.0,
        "Documentation alias — use CapFloor.set_pricing_engine instead.");

    // --- Phase 103: Extended OU process (constant b) for storage options ---
    nb::enum_<ExtendedOrnsteinUhlenbeckProcess::Discretization>(
        m, "ExtendedOrnsteinUhlenbeckDiscretization")
        .value("MidPoint", ExtendedOrnsteinUhlenbeckProcess::MidPoint)
        .value("Trapezodial", ExtendedOrnsteinUhlenbeckProcess::Trapezodial)
        .value("GaussLobatto", ExtendedOrnsteinUhlenbeckProcess::GaussLobatto);

    nb::class_<ExtendedOrnsteinUhlenbeckProcess>(
        m, "ExtendedOrnsteinUhlenbeckProcess")
        .def(
            "__init__",
            [](ExtendedOrnsteinUhlenbeckProcess* self,
               Real speed,
               Volatility sigma,
               Real x0,
               Real b,
               ExtendedOrnsteinUhlenbeckProcess::Discretization discretization) {
                new (self) ExtendedOrnsteinUhlenbeckProcess(
                    speed,
                    sigma,
                    x0,
                    [b](Real) { return b; },
                    discretization);
            },
            nb::arg("speed"),
            nb::arg("sigma"),
            nb::arg("x0"),
            nb::arg("b"),
            nb::arg("discretization") =
                ExtendedOrnsteinUhlenbeckProcess::MidPoint,
            "Extended OU process with constant mean-reversion level b(t)=b.")
        .def("x0",
             [](const ExtendedOrnsteinUhlenbeckProcess& p) { return p.x0(); })
        .def("speed",
             [](const ExtendedOrnsteinUhlenbeckProcess& p) {
                 return p.speed();
             })
        .def("volatility",
             [](const ExtendedOrnsteinUhlenbeckProcess& p) {
                 return p.volatility();
             });
}
