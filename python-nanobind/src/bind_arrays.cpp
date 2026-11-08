// NumPy array-in / array-out wrappers for cheap QuantLib operations.
//
// Dates are passed as int64 arrays of QuantLib serial numbers (the values
// returned by `Date.serial_number()` / `date_serials`).  Building a Python
// `Date` object per element costs about as much as the call itself, so a
// serial-number array is what lets a whole batch run in C++.
//
// Inputs that are conceptually scalar-or-array (strikes, forwards, ...) accept
// a float, a sequence or a 1-D ndarray and broadcast: every input must have
// length 1 or the common length n.

#include "bindings.hpp"

#include <nanobind/ndarray.h>
#include <nanobind/stl/vector.h>

#include <ql/compounding.hpp>
#include <ql/errors.hpp>
#include <ql/handle.hpp>
#include <ql/option.hpp>
#include <ql/pricingengines/blackformula.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/time/businessdayconvention.hpp>
#include <ql/time/calendar.hpp>
#include <ql/time/date.hpp>
#include <ql/time/daycounter.hpp>
#include <ql/time/frequency.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

using namespace QuantLib;

namespace {

using F64Out = nb::ndarray<nb::numpy, double, nb::ndim<1>>;
using I64Out = nb::ndarray<nb::numpy, std::int64_t, nb::ndim<1>>;
using BoolOut = nb::ndarray<nb::numpy, bool, nb::ndim<1>>;
using F64View = nb::ndarray<const double, nb::ndim<1>, nb::c_contig>;
using I64View = nb::ndarray<const std::int64_t, nb::ndim<1>, nb::c_contig>;

template <class T>
nb::ndarray<nb::numpy, T, nb::ndim<1>> make_output(std::size_t n) {
    // new T[0] is valid, so empty inputs give empty arrays.
    T* data = new T[n];
    nb::capsule owner(data, [](void* p) noexcept { delete[] static_cast<T*>(p); });
    return nb::ndarray<nb::numpy, T, nb::ndim<1>>(data, {n}, owner);
}

// A float64 / int64 1-D view of an arbitrary Python input.  `owner` keeps the
// converted array (and so `data`) alive.
template <class T, class View>
struct Input {
    nb::object owner;
    const T* data = nullptr;
    std::size_t size = 0;

    Input(nb::handle h, const char* dtype, const char* name) {
        nb::module_ np = nb::module_::import_("numpy");
        owner = np.attr("ascontiguousarray")(np.attr("atleast_1d")(h), dtype);
        View view;
        if (!nb::try_cast(owner, view, false))
            QL_FAIL(name << " must be a number or a 1-D array");
        data = view.data();
        size = view.shape(0);
    }

    T operator[](std::size_t i) const { return data[size == 1 ? 0 : i]; }
};

using DoubleInput = Input<double, F64View>;
using SerialInput = Input<std::int64_t, I64View>;

template <class... Inputs>
std::size_t common_size(const Inputs&... inputs) {
    // NumPy rules: length 1 broadcasts, and an empty input gives an empty result.
    std::size_t n = 1;
    ((n = std::max(n, inputs.size)), ...);
    if (((inputs.size == 0) || ...))
        n = 0;
    bool ok = true;
    ((ok = ok && (inputs.size == 1 || inputs.size == n)), ...);
    QL_REQUIRE(ok, "array arguments must have length 1 or a common length " << n);
    return n;
}

Date to_date(std::int64_t serial) {
    return Date(static_cast<Date::serial_type>(serial));
}

template <class F>
auto indexed(std::size_t i, F&& f) -> decltype(f()) {
    try {
        return f();
    } catch (const std::exception& e) {
        QL_FAIL("element " << i << ": " << e.what());
    }
}

I64Out date_serials_impl(const std::vector<Date>& dates) {
    auto out = make_output<std::int64_t>(dates.size());
    auto* p = out.data();
    for (std::size_t i = 0; i < dates.size(); ++i)
        p[i] = dates[i].serialNumber();
    return out;
}

std::vector<Date> dates_from_serials_impl(nb::handle serials) {
    SerialInput s(serials, "int64", "serials");
    std::vector<Date> out;
    out.reserve(s.size);
    for (std::size_t i = 0; i < s.size; ++i)
        out.push_back(indexed(i, [&] { return to_date(s.data[i]); }));
    return out;
}

F64Out discount_serials_impl(const Handle<YieldTermStructure>& h,
                             nb::handle serials,
                             bool extrapolate) {
    QL_REQUIRE(!h.empty(), "empty yield term structure handle");
    SerialInput s(serials, "int64", "serials");
    auto out = make_output<double>(s.size);
    double* p = out.data();
    for (std::size_t i = 0; i < s.size; ++i)
        p[i] = indexed(i, [&] { return h->discount(to_date(s.data[i]), extrapolate); });
    return out;
}

F64Out zero_rates_serials_impl(const Handle<YieldTermStructure>& h,
                               nb::handle serials,
                               const DayCounter& day_counter,
                               Compounding compounding,
                               Frequency frequency,
                               bool extrapolate) {
    QL_REQUIRE(!h.empty(), "empty yield term structure handle");
    SerialInput s(serials, "int64", "serials");
    auto out = make_output<double>(s.size);
    double* p = out.data();
    for (std::size_t i = 0; i < s.size; ++i) {
        p[i] = indexed(i, [&] {
            return h->zeroRate(to_date(s.data[i]), day_counter, compounding, frequency,
                               extrapolate)
                .rate();
        });
    }
    return out;
}

F64Out forward_rates_serials_impl(const Handle<YieldTermStructure>& h,
                                  nb::handle starts,
                                  nb::handle ends,
                                  const DayCounter& day_counter,
                                  Compounding compounding,
                                  Frequency frequency,
                                  bool extrapolate) {
    QL_REQUIRE(!h.empty(), "empty yield term structure handle");
    SerialInput d1(starts, "int64", "starts");
    SerialInput d2(ends, "int64", "ends");
    const std::size_t n = common_size(d1, d2);
    auto out = make_output<double>(n);
    double* p = out.data();
    for (std::size_t i = 0; i < n; ++i) {
        p[i] = indexed(i, [&] {
            return h->forwardRate(to_date(d1[i]), to_date(d2[i]), day_counter, compounding,
                                  frequency, extrapolate)
                .rate();
        });
    }
    return out;
}

F64Out year_fractions_serials_impl(const DayCounter& day_counter,
                                   nb::handle starts,
                                   nb::handle ends) {
    SerialInput d1(starts, "int64", "starts");
    SerialInput d2(ends, "int64", "ends");
    const std::size_t n = common_size(d1, d2);
    auto out = make_output<double>(n);
    double* p = out.data();
    for (std::size_t i = 0; i < n; ++i) {
        p[i] = indexed(i, [&] {
            return day_counter.yearFraction(to_date(d1[i]), to_date(d2[i]));
        });
    }
    return out;
}

I64Out adjust_serials_impl(const Calendar& calendar,
                           nb::handle serials,
                           BusinessDayConvention convention) {
    SerialInput s(serials, "int64", "serials");
    auto out = make_output<std::int64_t>(s.size);
    std::int64_t* p = out.data();
    for (std::size_t i = 0; i < s.size; ++i) {
        p[i] = indexed(i, [&] {
            return static_cast<std::int64_t>(
                calendar.adjust(to_date(s.data[i]), convention).serialNumber());
        });
    }
    return out;
}

BoolOut is_business_day_serials_impl(const Calendar& calendar, nb::handle serials) {
    SerialInput s(serials, "int64", "serials");
    auto out = make_output<bool>(s.size);
    bool* p = out.data();
    for (std::size_t i = 0; i < s.size; ++i)
        p[i] = indexed(i, [&] { return calendar.isBusinessDay(to_date(s.data[i])); });
    return out;
}

F64Out black_formula_array_impl(Option::Type option_type,
                                nb::handle strikes,
                                nb::handle forwards,
                                nb::handle std_devs,
                                nb::handle discounts,
                                nb::handle displacements) {
    DoubleInput k(strikes, "float64", "strike");
    DoubleInput f(forwards, "float64", "forward");
    DoubleInput sd(std_devs, "float64", "std_dev");
    DoubleInput df(discounts, "float64", "discount");
    DoubleInput disp(displacements, "float64", "displacement");
    const std::size_t n = common_size(k, f, sd, df, disp);
    auto out = make_output<double>(n);
    double* p = out.data();
    for (std::size_t i = 0; i < n; ++i) {
        p[i] = indexed(i, [&] {
            return blackFormula(option_type, k[i], f[i], sd[i], df[i], disp[i]);
        });
    }
    return out;
}

F64Out black_formula_implied_std_dev_array_impl(Option::Type option_type,
                                                nb::handle strikes,
                                                nb::handle forwards,
                                                nb::handle prices,
                                                nb::handle discounts,
                                                nb::handle displacements,
                                                Real guess,
                                                Real accuracy,
                                                Natural max_iterations) {
    DoubleInput k(strikes, "float64", "strike");
    DoubleInput f(forwards, "float64", "forward");
    DoubleInput pr(prices, "float64", "black_price");
    DoubleInput df(discounts, "float64", "discount");
    DoubleInput disp(displacements, "float64", "displacement");
    const std::size_t n = common_size(k, f, pr, df, disp);
    auto out = make_output<double>(n);
    double* p = out.data();
    for (std::size_t i = 0; i < n; ++i) {
        p[i] = indexed(i, [&] {
            return blackFormulaImpliedStdDev(option_type, k[i], f[i], pr[i], df[i], disp[i],
                                             guess, accuracy, max_iterations);
        });
    }
    return out;
}

} // namespace

void bind_arrays(nb::module_& m) {
    m.def("date_serials", &date_serials_impl, nb::arg("dates"),
          "Serial numbers of a list of Date values as an int64 NumPy array.");
    m.def("dates_from_serials", &dates_from_serials_impl, nb::arg("serials"),
          "List of Date values from an int64 array of serial numbers.");

    m.def("discount_serials", &discount_serials_impl, nb::arg("curve_handle"),
          nb::arg("serials"), nb::arg("extrapolate") = false,
          "Discount factors at dates given as an int64 array of serial numbers.");
    m.def("zero_rates_serials", &zero_rates_serials_impl, nb::arg("curve_handle"),
          nb::arg("serials"), nb::arg("day_counter"), nb::arg("compounding"),
          nb::arg("frequency") = Annual, nb::arg("extrapolate") = false,
          "Zero rates at dates given as serial numbers (rate values only).");
    m.def("forward_rates_serials", &forward_rates_serials_impl, nb::arg("curve_handle"),
          nb::arg("starts"), nb::arg("ends"), nb::arg("day_counter"),
          nb::arg("compounding"), nb::arg("frequency") = Annual,
          nb::arg("extrapolate") = false,
          "Forward rates between serial-number dates (rate values only).\n"
          "starts / ends broadcast: length 1 or a common length.");
    m.def("year_fractions_serials", &year_fractions_serials_impl, nb::arg("day_counter"),
          nb::arg("starts"), nb::arg("ends"),
          "Year fractions between serial-number dates; starts / ends broadcast.");
    m.def("adjust_serials", &adjust_serials_impl, nb::arg("calendar"), nb::arg("serials"),
          nb::arg("convention") = Following,
          "Business-day adjusted dates, as an int64 array of serial numbers.");
    m.def("is_business_day_serials", &is_business_day_serials_impl, nb::arg("calendar"),
          nb::arg("serials"), "Boolean array: is each serial-number date a business day.");

    m.def("black_formula_array", &black_formula_array_impl, nb::arg("option_type"),
          nb::arg("strike"), nb::arg("forward"), nb::arg("std_dev"),
          nb::arg("discount") = 1.0, nb::arg("displacement") = 0.0,
          "Black (1976) formula over arrays.  strike, forward, std_dev, discount and\n"
          "displacement each take a float or a 1-D array and broadcast.");
    m.def("black_formula_implied_std_dev_array", &black_formula_implied_std_dev_array_impl,
          nb::arg("option_type"), nb::arg("strike"), nb::arg("forward"),
          nb::arg("black_price"), nb::arg("discount") = 1.0, nb::arg("displacement") = 0.0,
          nb::arg("guess") = 0.2, nb::arg("accuracy") = 1.0e-8,
          nb::arg("max_iterations") = 1000,
          "Black (1976) implied standard deviation over arrays; inputs broadcast.");
}
