#include "bindings.hpp"

#include <nanobind/stl/vector.h>

#include <ql/math/linearleastsquaresregression.hpp>
#include <ql/termstructures/volatility/abcd.hpp>

using namespace QuantLib;

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
        .def("maximum_volatility", &AbcdFunction::maximumVolatility)
        .def("short_term_volatility", &AbcdFunction::shortTermVolatility)
        .def("long_term_volatility", &AbcdFunction::longTermVolatility);

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
