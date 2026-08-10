#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>

#include <ql/handle.hpp>
#include <ql/models/equity/batesmodel.hpp>
#include <ql/models/equity/hestonmodel.hpp>
#include <ql/processes/batesprocess.hpp>
#include <ql/processes/hestonprocess.hpp>
#include <ql/quote.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>

using namespace QuantLib;

void bind_heston(nb::module_& m) {
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
        .def("process", &HestonModel::process);

    m.def(
        "AnalyticHestonEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_heston_pricing_engine.");

    m.def(
        "FdHestonVanillaEngine",
        [](const ext::shared_ptr<HestonModel>& model) { return model; },
        nb::arg("model"),
        "Factory alias: pass the returned model to "
        "VanillaOption/EuropeanOption.set_fd_heston_pricing_engine.");

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
