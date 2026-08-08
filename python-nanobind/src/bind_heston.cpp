#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>

#include <ql/handle.hpp>
#include <ql/models/equity/hestonmodel.hpp>
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
}
