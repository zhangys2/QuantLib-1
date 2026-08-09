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
}
