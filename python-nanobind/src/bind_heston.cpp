#include "bindings.hpp"

#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <optional>

#include <ql/handle.hpp>
#include <ql/math/optimization/endcriteria.hpp>
#include <ql/math/optimization/levenbergmarquardt.hpp>
#include <ql/methods/finitedifferences/solvers/fdmbackwardsolver.hpp>
#include <ql/models/calibrationhelper.hpp>
#include <ql/models/equity/batesmodel.hpp>
#include <ql/models/equity/hestonmodel.hpp>
#include <ql/models/equity/hestonmodelhelper.hpp>
#include <ql/pricingengines/vanilla/analytichestonengine.hpp>
#include <ql/pricingengines/vanilla/coshestonengine.hpp>
#include <ql/pricingengines/vanilla/exponentialfittinghestonengine.hpp>
#include <ql/processes/batesprocess.hpp>
#include <ql/processes/hestonprocess.hpp>
#include <ql/quote.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/calendar.hpp>
#include <ql/time/period.hpp>
#include <ql/utilities/null.hpp>

#include <vector>

using namespace QuantLib;

void bind_heston(nb::module_& m) {
    // --- Phase 47: FD scheme descriptors (before FD engine setters) ---------
    nb::enum_<FdmSchemeDesc::FdmSchemeType>(m, "FdmSchemeType")
        .value("Hundsdorfer", FdmSchemeDesc::HundsdorferType)
        .value("Douglas", FdmSchemeDesc::DouglasType)
        .value("CraigSneyd", FdmSchemeDesc::CraigSneydType)
        .value("ModifiedCraigSneyd", FdmSchemeDesc::ModifiedCraigSneydType)
        .value("ImplicitEuler", FdmSchemeDesc::ImplicitEulerType)
        .value("ExplicitEuler", FdmSchemeDesc::ExplicitEulerType)
        .value("MethodOfLines", FdmSchemeDesc::MethodOfLinesType)
        .value("TrBDF2", FdmSchemeDesc::TrBDF2Type)
        .value("CrankNicolson", FdmSchemeDesc::CrankNicolsonType);

    nb::class_<FdmSchemeDesc>(m, "FdmSchemeDesc")
        .def(nb::init<FdmSchemeDesc::FdmSchemeType, Real, Real>(),
             nb::arg("type"),
             nb::arg("theta"),
             nb::arg("mu"))
        .def_ro("type", &FdmSchemeDesc::type)
        .def_ro("theta", &FdmSchemeDesc::theta)
        .def_ro("mu", &FdmSchemeDesc::mu)
        .def_static("Douglas", &FdmSchemeDesc::Douglas)
        .def_static("CrankNicolson", &FdmSchemeDesc::CrankNicolson)
        .def_static("ImplicitEuler", &FdmSchemeDesc::ImplicitEuler)
        .def_static("ExplicitEuler", &FdmSchemeDesc::ExplicitEuler)
        .def_static("CraigSneyd", &FdmSchemeDesc::CraigSneyd)
        .def_static("ModifiedCraigSneyd", &FdmSchemeDesc::ModifiedCraigSneyd)
        .def_static("Hundsdorfer", &FdmSchemeDesc::Hundsdorfer)
        .def_static("ModifiedHundsdorfer", &FdmSchemeDesc::ModifiedHundsdorfer)
        .def_static("MethodOfLines",
                    &FdmSchemeDesc::MethodOfLines,
                    nb::arg("eps") = 0.001,
                    nb::arg("rel_init_step_size") = 0.01)
        .def_static("TrBDF2", &FdmSchemeDesc::TrBDF2);

    // HestonProcess / HestonModel are MI-heavy via StochasticProcess /
    // CalibratedModel — bind as concrete types without exposing C++ bases.
    nb::enum_<HestonProcess::Discretization>(m, "HestonDiscretization")
        .value("PartialTruncation", HestonProcess::PartialTruncation)
        .value("FullTruncation", HestonProcess::FullTruncation)
        .value("Reflection", HestonProcess::Reflection)
        .value("NonCentralChiSquareVariance",
               HestonProcess::NonCentralChiSquareVariance)
        .value("QuadraticExponential", HestonProcess::QuadraticExponential)
        .value("QuadraticExponentialMartingale",
               HestonProcess::QuadraticExponentialMartingale)
        .value("BroadieKayaExactSchemeLobatto",
               HestonProcess::BroadieKayaExactSchemeLobatto)
        .value("BroadieKayaExactSchemeLaguerre",
               HestonProcess::BroadieKayaExactSchemeLaguerre)
        .value("BroadieKayaExactSchemeTrapezoidal",
               HestonProcess::BroadieKayaExactSchemeTrapezoidal);

    nb::class_<HestonProcess>(m, "HestonProcess")
        .def(nb::init<Handle<YieldTermStructure>,
                      Handle<YieldTermStructure>,
                      Handle<Quote>,
                      Real,
                      Real,
                      Real,
                      Real,
                      Real,
                      HestonProcess::Discretization>(),
             nb::arg("risk_free_rate"),
             nb::arg("dividend_yield"),
             nb::arg("s0"),
             nb::arg("v0"),
             nb::arg("kappa"),
             nb::arg("theta"),
             nb::arg("sigma"),
             nb::arg("rho"),
             nb::arg("discretization") =
                 HestonProcess::QuadraticExponentialMartingale)
        .def("v0", &HestonProcess::v0)
        .def("kappa", &HestonProcess::kappa)
        .def("theta", &HestonProcess::theta)
        .def("sigma", &HestonProcess::sigma)
        .def("rho", &HestonProcess::rho);

    // --- Phase 49: ComplexLogFormula (needed by exp-fitting engine args) ----
    nb::enum_<AnalyticHestonEngine::ComplexLogFormula>(
        m, "HestonComplexLogFormula")
        .value("Gatheral", AnalyticHestonEngine::Gatheral)
        .value("BranchCorrection", AnalyticHestonEngine::BranchCorrection)
        .value("AndersenPiterbarg", AnalyticHestonEngine::AndersenPiterbarg)
        .value("AndersenPiterbargOptCV",
               AnalyticHestonEngine::AndersenPiterbargOptCV)
        .value("AsymptoticChF", AnalyticHestonEngine::AsymptoticChF)
        .value("AngledContour", AnalyticHestonEngine::AngledContour)
        .value("AngledContourNoCV", AnalyticHestonEngine::AngledContourNoCV)
        .value("OptimalCV", AnalyticHestonEngine::OptimalCV);

    // --- Phase 48: calibration support (before HestonModel.calibrate) -------
    nb::enum_<BlackCalibrationHelper::CalibrationErrorType>(
        m, "CalibrationErrorType")
        .value("RelativePriceError",
               BlackCalibrationHelper::RelativePriceError)
        .value("PriceError", BlackCalibrationHelper::PriceError)
        .value("ImpliedVolError", BlackCalibrationHelper::ImpliedVolError);

    nb::enum_<EndCriteria::Type>(m, "EndCriteriaType")
        .value("None_", EndCriteria::None)  // C++ None; Python keyword-safe
        .value("MaxIterations", EndCriteria::MaxIterations)
        .value("StationaryPoint", EndCriteria::StationaryPoint)
        .value("StationaryFunctionValue", EndCriteria::StationaryFunctionValue)
        .value("StationaryFunctionAccuracy",
               EndCriteria::StationaryFunctionAccuracy)
        .value("ZeroGradientNorm", EndCriteria::ZeroGradientNorm)
        .value("FunctionEpsilonTooSmall", EndCriteria::FunctionEpsilonTooSmall)
        .value("Unknown", EndCriteria::Unknown);

    nb::class_<EndCriteria>(m, "EndCriteria")
        .def(nb::init<Size, Size, Real, Real, Real>(),
             nb::arg("max_iterations"),
             nb::arg("max_stationary_state_iterations"),
             nb::arg("root_epsilon"),
             nb::arg("function_epsilon"),
             nb::arg("gradient_norm_epsilon"))
        .def("max_iterations", &EndCriteria::maxIterations)
        .def("max_stationary_state_iterations",
             &EndCriteria::maxStationaryStateIterations)
        .def("root_epsilon", &EndCriteria::rootEpsilon)
        .def("function_epsilon", &EndCriteria::functionEpsilon)
        .def("gradient_norm_epsilon", &EndCriteria::gradientNormEpsilon);

    nb::class_<LevenbergMarquardt>(m, "LevenbergMarquardt")
        .def(nb::init<Real, Real, Real, bool>(),
             nb::arg("epsfcn") = 1.0e-8,
             nb::arg("xtol") = 1.0e-8,
             nb::arg("gtol") = 1.0e-8,
             nb::arg("use_cost_functions_jacobian") = false);

    nb::class_<HestonModelHelper>(m, "HestonModelHelper")
        .def(
            "__init__",
            [](HestonModelHelper* self,
               const Period& maturity,
               const Calendar& calendar,
               const Handle<Quote>& s0,
               Real strike_price,
               const Handle<Quote>& volatility,
               const Handle<YieldTermStructure>& risk_free_rate,
               const Handle<YieldTermStructure>& dividend_yield,
               BlackCalibrationHelper::CalibrationErrorType error_type) {
                new (self) HestonModelHelper(
                    maturity,
                    calendar,
                    s0,
                    strike_price,
                    volatility,
                    risk_free_rate,
                    dividend_yield,
                    error_type);
            },
            nb::arg("maturity"),
            nb::arg("calendar"),
            nb::arg("s0"),
            nb::arg("strike_price"),
            nb::arg("volatility"),
            nb::arg("risk_free_rate"),
            nb::arg("dividend_yield"),
            nb::arg("error_type") =
                BlackCalibrationHelper::RelativePriceError)
        .def(
            "__init__",
            [](HestonModelHelper* self,
               const Period& maturity,
               const Calendar& calendar,
               Real s0,
               Real strike_price,
               const Handle<Quote>& volatility,
               const Handle<YieldTermStructure>& risk_free_rate,
               const Handle<YieldTermStructure>& dividend_yield,
               BlackCalibrationHelper::CalibrationErrorType error_type) {
                new (self) HestonModelHelper(
                    maturity,
                    calendar,
                    s0,
                    strike_price,
                    volatility,
                    risk_free_rate,
                    dividend_yield,
                    error_type);
            },
            nb::arg("maturity"),
            nb::arg("calendar"),
            nb::arg("s0"),
            nb::arg("strike_price"),
            nb::arg("volatility"),
            nb::arg("risk_free_rate"),
            nb::arg("dividend_yield"),
            nb::arg("error_type") =
                BlackCalibrationHelper::RelativePriceError)
        .def("calibration_error", &HestonModelHelper::calibrationError)
        .def("market_value", &HestonModelHelper::marketValue)
        .def("model_value", &HestonModelHelper::modelValue)
        .def("maturity", &HestonModelHelper::maturity)
        .def(
            "set_pricing_engine",
            [](HestonModelHelper& helper,
               const ext::shared_ptr<HestonModel>& model,
               Size integration_order) {
                helper.setPricingEngine(ext::make_shared<AnalyticHestonEngine>(
                    model, integration_order));
            },
            nb::arg("model"),
            nb::arg("integration_order") = 144,
            "Attach AnalyticHestonEngine for calibration.")
        .def(
            "set_cos_heston_pricing_engine",
            [](HestonModelHelper& helper,
               const ext::shared_ptr<HestonModel>& model,
               Real L,
               Size N) {
                helper.setPricingEngine(
                    ext::make_shared<COSHestonEngine>(model, L, N));
            },
            nb::arg("model"),
            nb::arg("L") = 16.0,
            nb::arg("N") = Size(200),
            "Attach COSHestonEngine for calibration.")
        .def(
            "set_exponential_fitting_heston_pricing_engine",
            [](HestonModelHelper& helper,
               const ext::shared_ptr<HestonModel>& model,
               AnalyticHestonEngine::ComplexLogFormula control_variate,
               std::optional<Real> scaling,
               Real alpha) {
                helper.setPricingEngine(
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
            "Attach ExponentialFittingHestonEngine for calibration.");

    nb::class_<HestonModel>(m, "HestonModel")
        .def(
            "__init__",
            [](HestonModel* self,
               const ext::shared_ptr<HestonProcess>& process) {
                new (self) HestonModel(process);
            },
            nb::arg("process"))
        .def("v0", &HestonModel::v0)
        .def("kappa", &HestonModel::kappa)
        .def("theta", &HestonModel::theta)
        .def("sigma", &HestonModel::sigma)
        .def("rho", &HestonModel::rho)
        .def("process", &HestonModel::process)
        .def(
            "params",
            [](const HestonModel& model) {
                const Array a = model.params();
                return std::vector<Real>(a.begin(), a.end());
            },
            "Calibration parameter vector [theta, kappa, sigma, rho, v0].")
        .def(
            "set_params",
            [](HestonModel& model, const std::vector<Real>& params) {
                model.setParams(Array(params.begin(), params.end()));
            },
            nb::arg("params"))
        .def(
            "end_criteria",
            [](const HestonModel& model) { return model.endCriteria(); },
            "End-criteria result from the last calibrate() call.")
        .def(
            "calibrate",
            [](HestonModel& model,
               const std::vector<ext::shared_ptr<HestonModelHelper>>& helpers,
               LevenbergMarquardt& method,
               const EndCriteria& end_criteria) {
                std::vector<ext::shared_ptr<CalibrationHelper>> calib;
                calib.reserve(helpers.size());
                for (const auto& h : helpers) {
                    calib.push_back(
                        ext::static_pointer_cast<CalibrationHelper>(h));
                }
                model.calibrate(calib, method, end_criteria);
            },
            nb::arg("helpers"),
            nb::arg("method"),
            nb::arg("end_criteria"),
            "Calibrate to HestonModelHelper instruments (helpers must already "
            "have a pricing engine).");

    m.def(
        "AnalyticHestonEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_heston_pricing_engine.");

    m.def(
        "MCEuropeanHestonEngine",
        [](const ext::shared_ptr<HestonProcess>& process) { return process; },
        nb::arg("process"),
        "Factory alias: pass the returned process to "
        "VanillaOption/EuropeanOption.set_mc_heston_pricing_engine.");

    m.def(
        "FdHestonVanillaEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_fd_heston_pricing_engine.");

    // --- Phase 49: COS / exponential-fitting Heston engine factories --------
    m.def(
        "COSHestonEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_cos_heston_pricing_engine.");

    m.def(
        "ExponentialFittingHestonEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption."
        "set_exponential_fitting_heston_pricing_engine.");

    // --- Phase 39: Bates (Heston + jumps) -----------------------------------
    // BatesProcess / BatesModel inherit Heston types — bind as concrete
    // wrappers without exposing C++ bases (nanobind MI limitation).
    nb::class_<BatesProcess>(m, "BatesProcess")
        .def(nb::init<const Handle<YieldTermStructure>&,
                      const Handle<YieldTermStructure>&,
                      const Handle<Quote>&,
                      Real,
                      Real,
                      Real,
                      Real,
                      Real,
                      Real,
                      Real,
                      Real,
                      HestonProcess::Discretization>(),
             nb::arg("risk_free_rate"),
             nb::arg("dividend_yield"),
             nb::arg("s0"),
             nb::arg("v0"),
             nb::arg("kappa"),
             nb::arg("theta"),
             nb::arg("sigma"),
             nb::arg("rho"),
             nb::arg("jump_intensity"),
             nb::arg("nu"),
             nb::arg("delta"),
             nb::arg("discretization") = HestonProcess::FullTruncation)
        .def("v0", &BatesProcess::v0)
        .def("kappa", &BatesProcess::kappa)
        .def("theta", &BatesProcess::theta)
        .def("sigma", &BatesProcess::sigma)
        .def("rho", &BatesProcess::rho)
        .def("jump_intensity",
             &BatesProcess::lambda,
             "Jump intensity λ (C++ BatesProcess::lambda).")
        .def("nu", &BatesProcess::nu, "Mean log jump size.")
        .def("delta", &BatesProcess::delta, "Jump-size volatility.");

    nb::class_<BatesModel>(m, "BatesModel")
        .def(
            "__init__",
            [](BatesModel* self, const ext::shared_ptr<BatesProcess>& process) {
                new (self) BatesModel(process);
            },
            nb::arg("process"))
        .def("v0", &BatesModel::v0)
        .def("kappa", &BatesModel::kappa)
        .def("theta", &BatesModel::theta)
        .def("sigma", &BatesModel::sigma)
        .def("rho", &BatesModel::rho)
        .def("jump_intensity",
             &BatesModel::lambda,
             "Jump intensity λ (C++ BatesModel::lambda).")
        .def("nu", &BatesModel::nu)
        .def("delta", &BatesModel::delta);

    m.def(
        "BatesEngine",
        [](const ext::shared_ptr<BatesModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_bates_pricing_engine.");

    // --- Phase 45: FD Bates vanilla engine ----------------------------------
    m.def(
        "FdBatesVanillaEngine",
        [](const ext::shared_ptr<BatesModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_fd_bates_pricing_engine.");

    // --- Phase 46: Bates DetJump / DoubleExp variants -----------------------
    // Standalone concrete wrappers (BatesModel / HestonModel MI not exposed).
    nb::class_<BatesDetJumpModel>(m, "BatesDetJumpModel")
        .def(
            "__init__",
            [](BatesDetJumpModel* self,
               const ext::shared_ptr<BatesProcess>& process,
               Real kappa_lambda,
               Real theta_lambda) {
                new (self) BatesDetJumpModel(
                    process, kappa_lambda, theta_lambda);
            },
            nb::arg("process"),
            nb::arg("kappa_lambda") = 1.0,
            nb::arg("theta_lambda") = 0.1)
        .def("v0", &BatesDetJumpModel::v0)
        .def("kappa", &BatesDetJumpModel::kappa)
        .def("theta", &BatesDetJumpModel::theta)
        .def("sigma", &BatesDetJumpModel::sigma)
        .def("rho", &BatesDetJumpModel::rho)
        .def("jump_intensity",
             &BatesDetJumpModel::lambda,
             "Jump intensity λ (C++ BatesDetJumpModel::lambda).")
        .def("nu", &BatesDetJumpModel::nu)
        .def("delta", &BatesDetJumpModel::delta)
        .def("kappa_lambda", &BatesDetJumpModel::kappaLambda)
        .def("theta_lambda", &BatesDetJumpModel::thetaLambda);

    nb::class_<BatesDoubleExpModel>(m, "BatesDoubleExpModel")
        .def(
            "__init__",
            [](BatesDoubleExpModel* self,
               const ext::shared_ptr<HestonProcess>& process,
               Real jump_intensity,
               Real nu_up,
               Real nu_down,
               Real p) {
                new (self) BatesDoubleExpModel(
                    process, jump_intensity, nu_up, nu_down, p);
            },
            nb::arg("process"),
            nb::arg("jump_intensity") = 0.1,
            nb::arg("nu_up") = 0.1,
            nb::arg("nu_down") = 0.1,
            nb::arg("p") = 0.5)
        .def(
            "__init__",
            [](BatesDoubleExpModel* self,
               const ext::shared_ptr<BatesProcess>& process,
               Real jump_intensity,
               Real nu_up,
               Real nu_down,
               Real p) {
                new (self) BatesDoubleExpModel(
                    ext::static_pointer_cast<HestonProcess>(process),
                    jump_intensity,
                    nu_up,
                    nu_down,
                    p);
            },
            nb::arg("process"),
            nb::arg("jump_intensity") = 0.1,
            nb::arg("nu_up") = 0.1,
            nb::arg("nu_down") = 0.1,
            nb::arg("p") = 0.5)
        .def("v0", &BatesDoubleExpModel::v0)
        .def("kappa", &BatesDoubleExpModel::kappa)
        .def("theta", &BatesDoubleExpModel::theta)
        .def("sigma", &BatesDoubleExpModel::sigma)
        .def("rho", &BatesDoubleExpModel::rho)
        .def("jump_intensity",
             &BatesDoubleExpModel::lambda,
             "Jump intensity λ (C++ BatesDoubleExpModel::lambda).")
        .def("nu_up", &BatesDoubleExpModel::nuUp)
        .def("nu_down", &BatesDoubleExpModel::nuDown)
        .def("p", &BatesDoubleExpModel::p);

    nb::class_<BatesDoubleExpDetJumpModel>(m, "BatesDoubleExpDetJumpModel")
        .def(
            "__init__",
            [](BatesDoubleExpDetJumpModel* self,
               const ext::shared_ptr<HestonProcess>& process,
               Real jump_intensity,
               Real nu_up,
               Real nu_down,
               Real p,
               Real kappa_lambda,
               Real theta_lambda) {
                new (self) BatesDoubleExpDetJumpModel(
                    process,
                    jump_intensity,
                    nu_up,
                    nu_down,
                    p,
                    kappa_lambda,
                    theta_lambda);
            },
            nb::arg("process"),
            nb::arg("jump_intensity") = 0.1,
            nb::arg("nu_up") = 0.1,
            nb::arg("nu_down") = 0.1,
            nb::arg("p") = 0.5,
            nb::arg("kappa_lambda") = 1.0,
            nb::arg("theta_lambda") = 0.1)
        .def(
            "__init__",
            [](BatesDoubleExpDetJumpModel* self,
               const ext::shared_ptr<BatesProcess>& process,
               Real jump_intensity,
               Real nu_up,
               Real nu_down,
               Real p,
               Real kappa_lambda,
               Real theta_lambda) {
                new (self) BatesDoubleExpDetJumpModel(
                    ext::static_pointer_cast<HestonProcess>(process),
                    jump_intensity,
                    nu_up,
                    nu_down,
                    p,
                    kappa_lambda,
                    theta_lambda);
            },
            nb::arg("process"),
            nb::arg("jump_intensity") = 0.1,
            nb::arg("nu_up") = 0.1,
            nb::arg("nu_down") = 0.1,
            nb::arg("p") = 0.5,
            nb::arg("kappa_lambda") = 1.0,
            nb::arg("theta_lambda") = 0.1)
        .def("v0", &BatesDoubleExpDetJumpModel::v0)
        .def("kappa", &BatesDoubleExpDetJumpModel::kappa)
        .def("theta", &BatesDoubleExpDetJumpModel::theta)
        .def("sigma", &BatesDoubleExpDetJumpModel::sigma)
        .def("rho", &BatesDoubleExpDetJumpModel::rho)
        .def("jump_intensity",
             &BatesDoubleExpDetJumpModel::lambda,
             "Jump intensity λ (C++ BatesDoubleExpDetJumpModel::lambda).")
        .def("nu_up", &BatesDoubleExpDetJumpModel::nuUp)
        .def("nu_down", &BatesDoubleExpDetJumpModel::nuDown)
        .def("p", &BatesDoubleExpDetJumpModel::p)
        .def("kappa_lambda", &BatesDoubleExpDetJumpModel::kappaLambda)
        .def("theta_lambda", &BatesDoubleExpDetJumpModel::thetaLambda);

    m.def(
        "BatesDetJumpEngine",
        [](const ext::shared_ptr<BatesDetJumpModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_bates_det_jump_pricing_engine.");

    m.def(
        "BatesDoubleExpEngine",
        [](const ext::shared_ptr<BatesDoubleExpModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_bates_double_exp_pricing_engine.");

    m.def(
        "BatesDoubleExpDetJumpEngine",
        [](const ext::shared_ptr<BatesDoubleExpDetJumpModel>& model) {
            return model;
        },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption."
        "set_bates_double_exp_det_jump_pricing_engine.");
}
