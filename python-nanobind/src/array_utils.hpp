#pragma once

// Shared helpers for the NumPy array bindings: output allocation, scalar-or-array
// input conversion with NumPy broadcasting, and per-element error context.

#include "bindings.hpp"

#include <nanobind/ndarray.h>

#include <ql/errors.hpp>
#include <ql/time/date.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <exception>

namespace qlnb_arrays {

using namespace QuantLib;

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

inline Date to_date(std::int64_t serial) {
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

} // namespace qlnb_arrays
