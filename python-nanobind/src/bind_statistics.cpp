// QuantLib's risk statistics (mean, moments, VaR, expected shortfall, ...) fed
// from NumPy arrays in one call.

#include "array_utils.hpp"
#include "bindings.hpp"

#include <nanobind/ndarray.h>

#include <ql/errors.hpp>
#include <ql/math/statistics/statistics.hpp>

#include <cstddef>

using namespace QuantLib;

namespace {

using namespace qlnb_arrays;

void add_values(Statistics& s, nb::handle values, nb::handle weights) {
    DoubleInput v(values, "float64", "values");
    if (weights.is_none()) {
        for (std::size_t i = 0; i < v.size; ++i)
            s.add(v.data[i]);
        return;
    }
    DoubleInput w(weights, "float64", "weights");
    const std::size_t n = common_size(v, w);
    for (std::size_t i = 0; i < n; ++i)
        s.add(v[i], w[i]);
}

} // namespace

void bind_statistics(nb::module_& m) {
    nb::class_<Statistics>(
        m, "RiskStatistics",
        "Weighted sample statistics with empirical and Gaussian risk measures\n"
        "(QuantLib's Statistics).  Percentiles are fractions, e.g. 0.99.")
        .def(nb::init<>())
        .def("add", [](Statistics& s, Real value, Real weight) { s.add(value, weight); },
             nb::arg("value"), nb::arg("weight") = 1.0)
        .def("add_values", &add_values, nb::arg("values"), nb::arg("weights") = nb::none(),
             "Add a float or 1-D array of values, with optional weights (length 1 or\n"
             "the same length).")
        .def("reset", &Statistics::reset)
        .def("samples", &Statistics::samples)
        .def("weight_sum", &Statistics::weightSum)
        .def("mean", &Statistics::mean)
        .def("variance", &Statistics::variance)
        .def("standard_deviation", &Statistics::standardDeviation)
        .def("error_estimate", &Statistics::errorEstimate)
        .def("skewness", &Statistics::skewness)
        .def("kurtosis", &Statistics::kurtosis)
        .def("min", &Statistics::min)
        .def("max", &Statistics::max)
        .def("percentile", &Statistics::percentile, nb::arg("percentile"))
        .def("top_percentile", &Statistics::topPercentile, nb::arg("percentile"))
        .def("semi_variance", &Statistics::semiVariance)
        .def("semi_deviation", &Statistics::semiDeviation)
        .def("downside_variance", &Statistics::downsideVariance)
        .def("downside_deviation", &Statistics::downsideDeviation)
        .def("regret", &Statistics::regret, nb::arg("target"))
        .def("potential_upside", &Statistics::potentialUpside, nb::arg("percentile"))
        .def("value_at_risk", &Statistics::valueAtRisk, nb::arg("percentile"))
        .def("expected_shortfall", &Statistics::expectedShortfall, nb::arg("percentile"))
        .def("shortfall", &Statistics::shortfall, nb::arg("target"))
        .def("average_shortfall", &Statistics::averageShortfall, nb::arg("target"))
        .def("gaussian_percentile", &Statistics::gaussianPercentile, nb::arg("percentile"))
        .def("gaussian_top_percentile", &Statistics::gaussianTopPercentile,
             nb::arg("percentile"))
        .def("gaussian_potential_upside", &Statistics::gaussianPotentialUpside,
             nb::arg("percentile"))
        .def("gaussian_value_at_risk", &Statistics::gaussianValueAtRisk,
             nb::arg("percentile"))
        .def("gaussian_expected_shortfall", &Statistics::gaussianExpectedShortfall,
             nb::arg("percentile"))
        .def("gaussian_shortfall", &Statistics::gaussianShortfall, nb::arg("target"))
        .def("gaussian_average_shortfall", &Statistics::gaussianAverageShortfall,
             nb::arg("target"))
        .def("gaussian_regret", &Statistics::gaussianRegret, nb::arg("target"))
        .def("gaussian_downside_variance", &Statistics::gaussianDownsideVariance)
        .def("gaussian_downside_deviation", &Statistics::gaussianDownsideDeviation);
}
