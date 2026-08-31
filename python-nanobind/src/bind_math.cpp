#include "bindings.hpp"

#include <nanobind/stl/vector.h>

#include <ql/math/linearleastsquaresregression.hpp>

using namespace QuantLib;

void bind_math(nb::module_& m) {
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
}
