#include "bindings.hpp"

#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <stdexcept>

#include <cmath>

#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/instruments/capfloor.hpp>
#include <ql/legacy/libormarketmodels/lfmhullwhiteparam.hpp>
#include <ql/legacy/libormarketmodels/lfmprocess.hpp>
#include <ql/legacy/libormarketmodels/lfmcovarproxy.hpp>
#include <ql/legacy/libormarketmodels/lfmswaptionengine.hpp>
#include <ql/legacy/libormarketmodels/lmexpcorrmodel.hpp>
#include <ql/legacy/libormarketmodels/lmextlinexpvolmodel.hpp>
#include <ql/legacy/libormarketmodels/lmfixedvolmodel.hpp>
#include <ql/legacy/libormarketmodels/lmlinexpcorrmodel.hpp>
#include <ql/legacy/libormarketmodels/lmlinexpvolmodel.hpp>
#include <ql/legacy/libormarketmodels/liborforwardmodel.hpp>
#include <ql/math/optimization/endcriteria.hpp>
#include <ql/math/optimization/levenbergmarquardt.hpp>
#include <ql/math/randomnumbers/rngtraits.hpp>
#include <ql/math/statistics/generalstatistics.hpp>
#include <ql/methods/montecarlo/multipathgenerator.hpp>
#include <ql/models/calibrationhelper.hpp>
#include <ql/models/model.hpp>
#include <ql/models/shortrate/calibrationhelpers/caphelper.hpp>
#include <ql/models/shortrate/calibrationhelpers/swaptionhelper.hpp>
#include <ql/models/shortrate/onefactormodels/markovfunctional.hpp>
#include <ql/pricingengines/capfloor/analyticcapfloorengine.hpp>
#include <ql/pricingengines/swaption/gaussian1dswaptionengine.hpp>
#include <ql/termstructures/volatility/optionlet/capletvariancecurve.hpp>
#include <ql/termstructures/volatility/volatilitytype.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/frequency.hpp>
#include <ql/timegrid.hpp>

using namespace QuantLib;

namespace {

using LfmPrRsg = PseudoRandom::rsg_type;

struct LfmMultiPathGeneratorHandle {
    MultiPathGenerator<LfmPrRsg> generator;

    explicit LfmMultiPathGeneratorHandle(
        MultiPathGenerator<LfmPrRsg> generator_)
        : generator(std::move(generator_)) {}

    static std::vector<std::vector<Real>> to_matrix(
        const MultiPathGenerator<LfmPrRsg>::sample_type& sample) {
        const MultiPath& path = sample.value;
        const Size n_assets = path.assetNumber();
        const Size n_times = path.pathSize();
        std::vector<std::vector<Real>> out(n_assets);
        for (Size k = 0; k < n_assets; ++k) {
            out[k].resize(n_times);
            for (Size t = 0; t < n_times; ++t)
                out[k][t] = path[k][t];
        }
        return out;
    }

    std::vector<std::vector<Real>> next() {
        return to_matrix(generator.next());
    }

    std::vector<std::vector<Real>> antithetic() {
        return to_matrix(generator.antithetic());
    }
};

} // namespace

void bind_lmm(nb::module_& m) {
    nb::class_<LiborForwardModelProcess>(m, "LiborForwardModelProcess")
        .def(nb::init<Size, const ext::shared_ptr<IborIndex>&>(),
             nb::arg("size"),
             nb::arg("index"))
        .def("size", &LiborForwardModelProcess::size)
        .def("factors", &LiborForwardModelProcess::factors)
        .def(
            "fixing_times",
            [](const LiborForwardModelProcess& p) {
                return p.fixingTimes();
            },
            "Fixing times used by the rolling forward measure.")
        .def(
            "fixing_dates",
            [](const LiborForwardModelProcess& p) { return p.fixingDates(); })
        .def(
            "accrual_start_times",
            [](const LiborForwardModelProcess& p) {
                return p.accrualStartTimes();
            })
        .def(
            "accrual_end_times",
            [](const LiborForwardModelProcess& p) {
                return p.accrualEndTimes();
            })
        .def(
            "discount_bond",
            [](const LiborForwardModelProcess& p,
               const std::vector<Rate>& rates) {
                return p.discountBond(rates);
            },
            nb::arg("rates"),
            "Discount factors implied by a Libor rate vector.")
        .def("index",
             [](const LiborForwardModelProcess& p) {
                 return p.index();
             })
        .def(
            "set_covar_param",
            [](LiborForwardModelProcess& p,
               const ext::shared_ptr<LfmCovarianceProxy>& param) {
                p.setCovarParam(param);
            },
            nb::arg("covar_param"),
            "Attach LfmCovarianceProxy for process simulation.");

    nb::class_<TimeGrid>(m, "TimeGrid")
        .def(
            "__init__",
            [](TimeGrid* self, const std::vector<Time>& times, Size steps) {
                new (self) TimeGrid(times.begin(), times.end(), steps);
            },
            nb::arg("times"),
            nb::arg("steps"),
            "Time grid through mandatory times with the given step count.")
        .def("size", &TimeGrid::size)
        .def(
            "index",
            [](const TimeGrid& g, Time t) { return g.index(t); },
            nb::arg("t"))
        .def(
            "__getitem__",
            [](const TimeGrid& g, Size i) { return g[i]; },
            nb::arg("i"));

    nb::class_<LfmMultiPathGeneratorHandle>(m, "MultiPathGenerator")
        .def(
            "__init__",
            [](LfmMultiPathGeneratorHandle* self,
               const ext::shared_ptr<LiborForwardModelProcess>& process,
               const TimeGrid& grid,
               BigNatural seed,
               bool brownian_bridge) {
                auto rsg = PseudoRandom::make_sequence_generator(
                    process->factors() * (grid.size() - 1), seed);
                new (self) LfmMultiPathGeneratorHandle(
                    MultiPathGenerator<LfmPrRsg>(
                        process, grid, rsg, brownian_bridge));
            },
            nb::arg("process"),
            nb::arg("grid"),
            nb::arg("seed") = BigNatural(42),
            nb::arg("brownian_bridge") = false,
            "PseudoRandom MultiPathGenerator for LiborForwardModelProcess.")
        .def("next", &LfmMultiPathGeneratorHandle::next)
        .def("antithetic", &LfmMultiPathGeneratorHandle::antithetic);

    nb::class_<GeneralStatistics>(m, "GeneralStatistics")
        .def(nb::init<>())
        .def(
            "add",
            [](GeneralStatistics& s, Real value, Real weight) {
                s.add(value, weight);
            },
            nb::arg("value"),
            nb::arg("weight") = 1.0)
        .def("mean", &GeneralStatistics::mean)
        .def("error_estimate", &GeneralStatistics::errorEstimate)
        .def("samples", &GeneralStatistics::samples);

    nb::class_<LmFixedVolatilityModel>(m, "LmFixedVolatilityModel")
        .def(
            "__init__",
            [](LmFixedVolatilityModel* self,
               const std::vector<Real>& volatilities,
               const std::vector<Time>& start_times) {
                new (self) LmFixedVolatilityModel(
                    Array(volatilities.begin(), volatilities.end()),
                    start_times);
            },
            nb::arg("volatilities"),
            nb::arg("start_times"));

    nb::class_<LmExponentialCorrelationModel>(m, "LmExponentialCorrelationModel")
        .def(nb::init<Size, Real>(), nb::arg("size"), nb::arg("rho"))
        .def(
            "correlation",
            [](const LmExponentialCorrelationModel& model, Time t) {
                return model.correlation(t);
            },
            nb::arg("t"))
        .def(
            "pseudo_sqrt",
            [](const LmExponentialCorrelationModel& model, Time t) {
                return model.pseudoSqrt(t);
            },
            nb::arg("t"));

    nb::class_<LmLinearExponentialCorrelationModel>(m,
                                                     "LmLinearExponentialCorrelationModel")
        .def(nb::init<Size, Real, Real>(),
             nb::arg("size"),
             nb::arg("rho"),
             nb::arg("beta"))
        .def(
            "correlation",
            [](const LmLinearExponentialCorrelationModel& model, Time t) {
                return model.correlation(t);
            },
            nb::arg("t"))
        .def(
            "pseudo_sqrt",
            [](const LmLinearExponentialCorrelationModel& model, Time t) {
                return model.pseudoSqrt(t);
            },
            nb::arg("t"));

    nb::class_<LmLinearExponentialVolatilityModel>(m,
                                                     "LmLinearExponentialVolatilityModel")
        .def(
            "__init__",
            [](LmLinearExponentialVolatilityModel* self,
               const std::vector<Time>& fixing_times,
               Real a,
               Real b,
               Real c,
               Real d) {
                new (self) LmLinearExponentialVolatilityModel(
                    fixing_times, a, b, c, d);
            },
            nb::arg("fixing_times"),
            nb::arg("a"),
            nb::arg("b"),
            nb::arg("c"),
            nb::arg("d"))
        .def(
            "volatility",
            [](const LmLinearExponentialVolatilityModel& model, Time t) {
                const Array v = model.volatility(t);
                return std::vector<Real>(v.begin(), v.end());
            },
            nb::arg("t"),
            "Caplet volatility vector at time t.");

    nb::class_<LmExtLinearExponentialVolModel>(m, "LmExtLinearExponentialVolModel")
        .def(
            "__init__",
            [](LmExtLinearExponentialVolModel* self,
               const std::vector<Time>& fixing_times,
               Real a,
               Real b,
               Real c,
               Real d) {
                new (self) LmExtLinearExponentialVolModel(
                    fixing_times, a, b, c, d);
            },
            nb::arg("fixing_times"),
            nb::arg("a"),
            nb::arg("b"),
            nb::arg("c"),
            nb::arg("d"));

    nb::class_<LfmCovarianceProxy>(m, "LfmCovarianceProxy")
        .def(
            "__init__",
            [](LfmCovarianceProxy* self,
               const ext::shared_ptr<LmFixedVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LfmCovarianceProxy(vola_model, corr_model);
            },
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "__init__",
            [](LfmCovarianceProxy* self,
               const ext::shared_ptr<LmLinearExponentialVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LfmCovarianceProxy(vola_model, corr_model);
            },
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "__init__",
            [](LfmCovarianceProxy* self,
               const ext::shared_ptr<LmExtLinearExponentialVolModel>& vola_model,
               const ext::shared_ptr<LmLinearExponentialCorrelationModel>& corr_model) {
                new (self) LfmCovarianceProxy(vola_model, corr_model);
            },
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "covariance",
            [](const LfmCovarianceProxy& proxy, Time t) {
                return proxy.covariance(t);
            },
            nb::arg("t"))
        .def(
            "diffusion",
            [](const LfmCovarianceProxy& proxy, Time t) {
                return proxy.diffusion(t);
            },
            nb::arg("t"));

    nb::class_<CapletVarianceCurve>(m, "CapletVarianceCurve")
        .def(nb::init<const Date&,
                      const std::vector<Date>&,
                      const std::vector<Volatility>&,
                      const DayCounter&,
                      VolatilityType,
                      Real>(),
             nb::arg("reference_date"),
             nb::arg("dates"),
             nb::arg("volatilities"),
             nb::arg("day_counter"),
             nb::arg("vol_type") = ShiftedLognormal,
             nb::arg("displacement") = 0.0);

    nb::class_<LiborForwardModel>(m, "LiborForwardModel")
        .def(
            "__init__",
            [](LiborForwardModel* self,
               const ext::shared_ptr<LiborForwardModelProcess>& process,
               const ext::shared_ptr<LmFixedVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LiborForwardModel(process, vola_model, corr_model);
            },
            nb::arg("process"),
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "__init__",
            [](LiborForwardModel* self,
               const ext::shared_ptr<LiborForwardModelProcess>& process,
               const ext::shared_ptr<LmLinearExponentialVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LiborForwardModel(process, vola_model, corr_model);
            },
            nb::arg("process"),
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "__init__",
            [](LiborForwardModel* self,
               const ext::shared_ptr<LiborForwardModelProcess>& process,
               const ext::shared_ptr<LmExtLinearExponentialVolModel>& vola_model,
               const ext::shared_ptr<LmLinearExponentialCorrelationModel>& corr_model) {
                new (self) LiborForwardModel(process, vola_model, corr_model);
            },
            nb::arg("process"),
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "s_0",
            &LiborForwardModel::S_0,
            nb::arg("alpha"),
            nb::arg("beta"),
            "Forward swap rate between libor indices alpha and beta.")
        .def(
            "params",
            [](const LiborForwardModel& model) {
                const Array a = model.params();
                return std::vector<Real>(a.begin(), a.end());
            },
            "Calibration parameter vector from the LMM covariance models.")
        .def(
            "set_params",
            [](LiborForwardModel& model, const std::vector<Real>& params) {
                model.setParams(Array(params.begin(), params.end()));
            },
            nb::arg("params"))
        .def(
            "end_criteria",
            [](const LiborForwardModel& model) { return model.endCriteria(); },
            "End-criteria result from the last calibrate() call.")
        .def(
            "calibrate",
            [](LiborForwardModel& model,
               nb::list py_helpers,
               LevenbergMarquardt& method,
               const EndCriteria& end_criteria) {
                std::vector<ext::shared_ptr<CalibrationHelper>> calib;
                calib.reserve(py_helpers.size());
                for (nb::handle item : py_helpers) {
                    if (nb::isinstance<CapHelper>(item)) {
                        calib.push_back(ext::static_pointer_cast<CalibrationHelper>(
                            nb::cast<ext::shared_ptr<CapHelper>>(item)));
                    } else if (nb::isinstance<SwaptionHelper>(item)) {
                        calib.push_back(ext::static_pointer_cast<CalibrationHelper>(
                            nb::cast<ext::shared_ptr<SwaptionHelper>>(item)));
                    } else {
                        throw std::runtime_error(
                            "helpers must be CapHelper or SwaptionHelper instances");
                    }
                }
                model.calibrate(calib, method, end_criteria);
            },
            nb::arg("helpers"),
            nb::arg("method"),
            nb::arg("end_criteria"),
            "Calibrate to CapHelper/SwaptionHelper instruments (helpers must "
            "already have a pricing engine).");

    nb::class_<CapHelper>(m, "CapHelper")
        .def(
            "__init__",
            [](CapHelper* self,
               const Period& length,
               const Handle<Quote>& volatility,
               const ext::shared_ptr<IborIndex>& index,
               Frequency fixed_leg_frequency,
               const DayCounter& fixed_leg_day_counter,
               bool include_first_swaplet,
               const Handle<YieldTermStructure>& term_structure,
               BlackCalibrationHelper::CalibrationErrorType error_type,
               VolatilityType vol_type,
               Real shift) {
                new (self) CapHelper(
                    length,
                    volatility,
                    index,
                    fixed_leg_frequency,
                    fixed_leg_day_counter,
                    include_first_swaplet,
                    term_structure,
                    error_type,
                    vol_type,
                    shift);
            },
            nb::arg("length"),
            nb::arg("volatility"),
            nb::arg("index"),
            nb::arg("fixed_leg_frequency"),
            nb::arg("fixed_leg_day_counter"),
            nb::arg("include_first_swaplet"),
            nb::arg("term_structure"),
            nb::arg("error_type") =
                BlackCalibrationHelper::RelativePriceError,
            nb::arg("vol_type") = ShiftedLognormal,
            nb::arg("shift") = 0.0)
        .def("calibration_error", &CapHelper::calibrationError)
        .def("market_value", &CapHelper::marketValue)
        .def("model_value", &CapHelper::modelValue)
        .def(
            "set_lfm_pricing_engine",
            [](CapHelper& helper,
               const ext::shared_ptr<LiborForwardModel>& model,
               const Handle<YieldTermStructure>& discount_curve) {
                helper.setPricingEngine(ext::make_shared<AnalyticCapFloorEngine>(
                    ext::static_pointer_cast<AffineModel>(model),
                    discount_curve));
            },
            nb::arg("model"),
            nb::arg("discount_curve") = Handle<YieldTermStructure>(),
            "Attach AnalyticCapFloorEngine for LMM calibration.");

    nb::class_<SwaptionHelper>(m, "SwaptionHelper")
        .def(
            "__init__",
            [](SwaptionHelper* self,
               const Period& maturity,
               const Period& length,
               const Handle<Quote>& volatility,
               const ext::shared_ptr<IborIndex>& index,
               const Period& fixed_leg_tenor,
               const DayCounter& fixed_leg_day_counter,
               const DayCounter& floating_leg_day_counter,
               const Handle<YieldTermStructure>& term_structure,
               BlackCalibrationHelper::CalibrationErrorType error_type,
               std::optional<Real> strike,
               Real nominal,
               VolatilityType vol_type,
               Real shift) {
                new (self) SwaptionHelper(
                    maturity,
                    length,
                    volatility,
                    index,
                    fixed_leg_tenor,
                    fixed_leg_day_counter,
                    floating_leg_day_counter,
                    term_structure,
                    error_type,
                    strike.value_or(Null<Real>()),
                    nominal,
                    vol_type,
                    shift);
            },
            nb::arg("maturity"),
            nb::arg("length"),
            nb::arg("volatility"),
            nb::arg("index"),
            nb::arg("fixed_leg_tenor"),
            nb::arg("fixed_leg_day_counter"),
            nb::arg("floating_leg_day_counter"),
            nb::arg("term_structure"),
            nb::arg("error_type") =
                BlackCalibrationHelper::RelativePriceError,
            nb::arg("strike") = nb::none(),
            nb::arg("nominal") = 1.0,
            nb::arg("vol_type") = ShiftedLognormal,
            nb::arg("shift") = 0.0)
        .def("calibration_error", &SwaptionHelper::calibrationError)
        .def("market_value", &SwaptionHelper::marketValue)
        .def("model_value", &SwaptionHelper::modelValue)
        .def(
            "set_lfm_pricing_engine",
            [](SwaptionHelper& helper,
               const ext::shared_ptr<LiborForwardModel>& model,
               const Handle<YieldTermStructure>& discount_curve) {
                helper.setPricingEngine(
                    ext::make_shared<LfmSwaptionEngine>(model, discount_curve));
            },
            nb::arg("model"),
            nb::arg("discount_curve") = Handle<YieldTermStructure>(),
            "Attach LfmSwaptionEngine for LMM calibration.")
        .def(
            "set_gaussian1d_pricing_engine",
            [](SwaptionHelper& helper,
               const ext::shared_ptr<MarkovFunctional>& model,
               int integration_points,
               Real stddevs,
               bool extrapolate_payoff,
               bool flat_payoff_extrapolation) {
                helper.setPricingEngine(
                    ext::make_shared<Gaussian1dSwaptionEngine>(
                        model,
                        integration_points,
                        stddevs,
                        extrapolate_payoff,
                        flat_payoff_extrapolation));
            },
            nb::arg("model"),
            nb::arg("integration_points") = 64,
            nb::arg("stddevs") = 7.0,
            nb::arg("extrapolate_payoff") = true,
            nb::arg("flat_payoff_extrapolation") = false,
            "Attach Gaussian1dSwaptionEngine on a MarkovFunctional model.");

    m.def(
        "lm_fixed_volatilities_from_caplet_curve",
        [](const ext::shared_ptr<LiborForwardModelProcess>& process,
           const ext::shared_ptr<CapletVarianceCurve>& caplet_vol) {
            const Array variances =
                LfmHullWhiteParameterization(process, caplet_vol)
                    .covariance(0.0)
                    .diagonal();
            std::vector<Real> vols(variances.size());
            for (Size i = 0; i < variances.size(); ++i)
                vols[i] = std::sqrt(variances[i]);
            return vols;
        },
        nb::arg("process"),
        nb::arg("caplet_vol"),
        "Hull–White LMM volatilities from an optionlet volatility structure.");

    m.def(
        "make_lfm_cap",
        [](const ext::shared_ptr<LiborForwardModelProcess>& process,
           Rate strike,
           Real amount) {
            const Size n = process->size();
            return Cap(process->cashFlows(amount), std::vector<Rate>(n, strike));
        },
        nb::arg("process"),
        nb::arg("strike"),
        nb::arg("amount") = 1.0,
        "Build a Cap on the LiborForwardModelProcess cash-flow leg.");
}
