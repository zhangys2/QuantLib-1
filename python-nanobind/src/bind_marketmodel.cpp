#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/models/marketmodels/correlations/expcorrelations.hpp>
#include <ql/models/marketmodels/correlations/timehomogeneousforwardcorrelation.hpp>
#include <ql/models/marketmodels/evolutiondescription.hpp>
#include <ql/models/marketmodels/models/abcdvol.hpp>
#include <ql/models/marketmodels/models/flatvol.hpp>
#include <ql/models/marketmodels/piecewiseconstantcorrelation.hpp>

using namespace QuantLib;

namespace {

struct PiecewiseConstantCorrelationHandle {
    ext::shared_ptr<PiecewiseConstantCorrelation> impl;

    explicit PiecewiseConstantCorrelationHandle(
        ext::shared_ptr<PiecewiseConstantCorrelation> impl_)
        : impl(std::move(impl_)) {}
};

} // namespace

void bind_marketmodel(nb::module_& m) {
    m.def(
        "exponential_correlations",
        &exponentialCorrelations,
        nb::arg("rate_times"),
        nb::arg("long_term_corr") = 0.5,
        nb::arg("beta") = 0.2,
        nb::arg("gamma") = 1.0,
        nb::arg("time") = 0.0,
        "Exponential forward-rate correlation matrix.");

    nb::class_<PiecewiseConstantCorrelationHandle>(m, "PiecewiseConstantCorrelationHandle");

    m.def(
        "time_homogeneous_forward_correlation",
        [](const Matrix& fwd_correlation, const std::vector<Time>& rate_times) {
            return PiecewiseConstantCorrelationHandle(
                ext::make_shared<TimeHomogeneousForwardCorrelation>(
                    fwd_correlation, rate_times));
        },
        nb::arg("fwd_correlation"),
        nb::arg("rate_times"),
        "Time-homogeneous piecewise-constant forward correlation.");

    nb::class_<EvolutionDescription>(m, "EvolutionDescription")
        .def(
            "__init__",
            [](EvolutionDescription* self,
               const std::vector<Time>& rate_times,
               const std::vector<Time>& evolution_times) {
                new (self) EvolutionDescription(rate_times, evolution_times);
            },
            nb::arg("rate_times"),
            nb::arg("evolution_times") = std::vector<Time>(),
            "Market-model evolution description.")
        .def("rate_times", &EvolutionDescription::rateTimes)
        .def("evolution_times", &EvolutionDescription::evolutionTimes)
        .def("number_of_rates", &EvolutionDescription::numberOfRates)
        .def("number_of_steps", &EvolutionDescription::numberOfSteps);

    nb::class_<FlatVol>(m, "FlatVol")
        .def(
            "__init__",
            [](FlatVol* self,
               const std::vector<Volatility>& volatilities,
               const PiecewiseConstantCorrelationHandle& correlation,
               const EvolutionDescription& evolution,
               Size number_of_factors,
               const std::vector<Rate>& initial_rates,
               const std::vector<Spread>& displacements) {
                new (self) FlatVol(
                    volatilities,
                    correlation.impl,
                    evolution,
                    number_of_factors,
                    initial_rates,
                    displacements);
            },
            nb::arg("volatilities"),
            nb::arg("correlation"),
            nb::arg("evolution"),
            nb::arg("number_of_factors"),
            nb::arg("initial_rates"),
            nb::arg("displacements"),
            "Flat-volatility market model with exponential correlation.")
        .def(
            "covariance",
            [](const FlatVol& model, Size step) {
                return Matrix(model.covariance(step));
            },
            nb::arg("step"),
            "Covariance matrix for the given evolution step.");

    nb::class_<AbcdVol>(m, "AbcdVol")
        .def(
            "__init__",
            [](AbcdVol* self,
               Real a,
               Real b,
               Real c,
               Real d,
               const std::vector<Real>& ks,
               const PiecewiseConstantCorrelationHandle& correlation,
               const EvolutionDescription& evolution,
               Size number_of_factors,
               const std::vector<Rate>& initial_rates,
               const std::vector<Spread>& displacements) {
                new (self) AbcdVol(
                    a,
                    b,
                    c,
                    d,
                    ks,
                    correlation.impl,
                    evolution,
                    number_of_factors,
                    initial_rates,
                    displacements);
            },
            nb::arg("a"),
            nb::arg("b"),
            nb::arg("c"),
            nb::arg("d"),
            nb::arg("ks"),
            nb::arg("correlation"),
            nb::arg("evolution"),
            nb::arg("number_of_factors"),
            nb::arg("initial_rates"),
            nb::arg("displacements"),
            "Abcd-volatility market model with exponential correlation.")
        .def(
            "covariance",
            [](const AbcdVol& model, Size step) {
                return Matrix(model.covariance(step));
            },
            nb::arg("step"),
            "Covariance matrix for the given evolution step.");
}
