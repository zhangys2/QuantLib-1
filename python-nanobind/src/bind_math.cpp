#include "bindings.hpp"

#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include <cmath>
#include <functional>

#include <ql/math/linearleastsquaresregression.hpp>
#include <ql/termstructures/volatility/abcd.hpp>
#include <ql/termstructures/volatility/abcdcalibration.hpp>

using namespace QuantLib;

namespace {

std::vector<std::function<Real(Real)>>
make_real_basis_functions(const std::vector<std::string>& basis) {
    std::vector<std::function<Real(Real)>> functions;
    functions.reserve(basis.size());
    for (const std::string& name : basis) {
        if (name == "const")
            functions.emplace_back([](Real) { return 1.0; });
        else if (name == "x")
            functions.emplace_back([](Real x) { return x; });
        else if (name == "x2")
            functions.emplace_back([](Real x) { return x * x; });
        else if (name == "sin")
            functions.emplace_back([](Real x) { return std::sin(x); });
        else
            QL_FAIL("unknown basis function: " << name);
    }
    return functions;
}

} // namespace

void bind_math(nb::module_& m) {
    nb::class_<AbcdFunction>(m, "AbcdFunction")
        .def(nb::init<Real, Real, Real, Real>(),
             nb::arg("a") = -0.06,
             nb::arg("b") = 0.17,
             nb::arg("c") = 0.54,
             nb::arg("d") = 0.17,
             "Abcd instantaneous volatility f(T-t) = (a + b(T-t)) exp(-c(T-t)) + d.")
        .def(
            "covariance",
            [](const AbcdFunction& f, Time t1, Time t2, Time T, Time S) {
                return f.covariance(t1, t2, T, S);
            },
            nb::arg("t1"),
            nb::arg("t2"),
            nb::arg("T"),
            nb::arg("S"),
            "Integrated instantaneous covariance between t1 and t2.")
        .def(
            "variance",
            [](const AbcdFunction& f, Time t_min, Time t_max, Time T) {
                return f.variance(t_min, t_max, T);
            },
            nb::arg("t_min"),
            nb::arg("t_max"),
            nb::arg("T"),
            "Integrated variance of the T-fixing rate between t_min and t_max.")
        .def(
            "volatility",
            [](const AbcdFunction& f, Time t_min, Time t_max, Time T) {
                return f.volatility(t_min, t_max, T);
            },
            nb::arg("t_min"),
            nb::arg("t_max"),
            nb::arg("T"),
            "Average volatility of the T-fixing rate between t_min and t_max.")
        .def("maximum_volatility", &AbcdFunction::maximumVolatility)
        .def("short_term_volatility", &AbcdFunction::shortTermVolatility)
        .def("long_term_volatility", &AbcdFunction::longTermVolatility);

    nb::class_<AbcdCalibration>(m, "AbcdCalibration")
        .def(
            "__init__",
            [](AbcdCalibration* self,
               const std::vector<Real>& times,
               const std::vector<Real>& black_vols,
               Real a_guess,
               Real b_guess,
               Real c_guess,
               Real d_guess) {
                new (self) AbcdCalibration(times, black_vols, a_guess, b_guess, c_guess, d_guess);
            },
            nb::arg("times"),
            nb::arg("black_vols"),
            nb::arg("a_guess") = -0.06,
            nb::arg("b_guess") = 0.17,
            nb::arg("c_guess") = 0.54,
            nb::arg("d_guess") = 0.17,
            "Calibrate Abcd parameters to a caplet/floor Black-volatility vector.")
        .def("compute", &AbcdCalibration::compute, "Run the calibration.")
        .def("error", &AbcdCalibration::error, "Root-mean-square calibration error.")
        .def("a", &AbcdCalibration::a)
        .def("b", &AbcdCalibration::b)
        .def("c", &AbcdCalibration::c)
        .def("d", &AbcdCalibration::d)
        .def(
            "k",
            [](const AbcdCalibration& cal,
               const std::vector<Real>& times,
               const std::vector<Real>& black_vols) { return cal.k(times, black_vols); },
            nb::arg("times"),
            nb::arg("black_vols"),
            "Per-tenor adjustment factors to match Black volatilities.")
        .def("end_criteria", &AbcdCalibration::endCriteria);

    nb::class_<LinearRegression>(m, "LinearRegression")
        .def(
            "__init__",
            [](LinearRegression* self,
               const std::vector<Real>& x,
               const std::vector<Real>& y,
               Real intercept) { new (self) LinearRegression(x, y, intercept); },
            nb::arg("x"),
            nb::arg("y"),
            nb::arg("intercept") = 1.0,
            "Simple linear regression y ~ intercept + x (1D Real samples).")
        .def(
            "__init__",
            [](LinearRegression* self,
               const std::vector<std::vector<Real>>& x,
               const std::vector<Real>& y,
               Real intercept) {
                std::vector<Array> samples;
                samples.reserve(x.size());
                for (const auto& row : x)
                    samples.emplace_back(row.begin(), row.end());
                new (self) LinearRegression(samples, y, intercept);
            },
            nb::arg("x"),
            nb::arg("y"),
            nb::arg("intercept") = 1.0,
            "Multi-dimensional regression y ~ intercept + x_0 + ... + x_{m-1}.")
        .def(
            "coefficients",
            [](const LinearRegression& regression) {
                const Array& a = regression.coefficients();
                return std::vector<Real>(a.begin(), a.end());
            },
            "Fitted regression coefficients.")
        .def(
            "standard_errors",
            [](const LinearRegression& regression) {
                const Array& errors = regression.standardErrors();
                return std::vector<Real>(errors.begin(), errors.end());
            },
            "Standard errors of the regression coefficients.")
        .def("dim", &LinearRegression::dim, "Number of regression parameters.")
        .def("size", &LinearRegression::size, "Number of sample points.");

    m.def(
        "linear_regression_with_basis",
        [](const std::vector<Real>& x,
           const std::vector<Real>& y,
           const std::vector<std::string>& basis) {
            const auto functions = make_real_basis_functions(basis);
            return LinearRegression(x, y, functions);
        },
        nb::arg("x"),
        nb::arg("y"),
        nb::arg("basis"),
        "Linear regression with named 1D basis functions "
        "(const, x, x2, sin).");
}
