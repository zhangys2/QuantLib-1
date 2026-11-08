// Bulk random-number generation: QuantLib's own sequences filled into NumPy
// arrays in C++, so a draw costs nanoseconds instead of a Python call.
//
// These are QuantLib's generators, not NumPy's, so a given seed reproduces the
// exact numbers a QuantLib C++ or SWIG program draws.

#include "array_utils.hpp"
#include "bindings.hpp"

#include <nanobind/ndarray.h>

#include <ql/errors.hpp>
#include <ql/math/distributions/normaldistribution.hpp>
#include <ql/math/randomnumbers/haltonrsg.hpp>
#include <ql/math/randomnumbers/mt19937uniformrng.hpp>
#include <ql/math/randomnumbers/sobolrsg.hpp>

#include <cstddef>
#include <vector>

using namespace QuantLib;

namespace {

using namespace qlnb_arrays;

using F64Matrix = nb::ndarray<nb::numpy, double, nb::ndim<2>>;

F64Matrix make_matrix(std::size_t rows, std::size_t cols) {
    double* data = new double[rows * cols];
    nb::capsule owner(data, [](void* p) noexcept { delete[] static_cast<double*>(p); });
    return F64Matrix(data, {rows, cols}, owner);
}

// Mersenne Twister uniforms, and standard normals by inverse cumulative
// normal of the same stream.
class MersenneTwisterRng {
  public:
    explicit MersenneTwisterRng(unsigned long seed) : rng_(seed) {}

    F64Out uniform(std::size_t n) {
        auto out = make_output<double>(n);
        double* p = out.data();
        for (std::size_t i = 0; i < n; ++i)
            p[i] = rng_.nextReal();
        return out;
    }

    F64Out gaussian(std::size_t n) {
        auto out = make_output<double>(n);
        double* p = out.data();
        for (std::size_t i = 0; i < n; ++i)
            p[i] = icn_(rng_.nextReal());
        return out;
    }

  private:
    MersenneTwisterUniformRng rng_;
    InverseCumulativeNormal icn_;
};

class SobolSequence {
  public:
    SobolSequence(Size dimension, unsigned long seed)
    : rsg_(dimension, seed), dimension_(dimension) {}

    F64Matrix uniform(std::size_t points) {
        auto out = make_matrix(points, dimension_);
        double* p = out.data();
        for (std::size_t i = 0; i < points; ++i) {
            const std::vector<Real>& s = rsg_.nextSequence().value;
            for (std::size_t j = 0; j < dimension_; ++j)
                p[i * dimension_ + j] = s[j];
        }
        return out;
    }

    F64Matrix gaussian(std::size_t points) {
        auto out = make_matrix(points, dimension_);
        double* p = out.data();
        for (std::size_t i = 0; i < points; ++i) {
            const std::vector<Real>& s = rsg_.nextSequence().value;
            for (std::size_t j = 0; j < dimension_; ++j)
                p[i * dimension_ + j] = icn_(s[j]);
        }
        return out;
    }

    void skip_to(std::uint32_t n) { rsg_.skipTo(n); }
    Size dimension() const { return dimension_; }

  private:
    SobolRsg rsg_;
    Size dimension_;
    InverseCumulativeNormal icn_;
};

class HaltonSequence {
  public:
    HaltonSequence(Size dimension, unsigned long seed, bool random_start, bool random_shift)
    : rsg_(dimension, seed, random_start, random_shift), dimension_(dimension) {}

    F64Matrix uniform(std::size_t points) {
        auto out = make_matrix(points, dimension_);
        double* p = out.data();
        for (std::size_t i = 0; i < points; ++i) {
            const std::vector<Real>& s = rsg_.nextSequence().value;
            for (std::size_t j = 0; j < dimension_; ++j)
                p[i * dimension_ + j] = s[j];
        }
        return out;
    }

    F64Matrix gaussian(std::size_t points) {
        auto out = uniform(points);
        double* p = out.data();
        for (std::size_t i = 0; i < points * dimension_; ++i)
            p[i] = icn_(p[i]);
        return out;
    }

    Size dimension() const { return dimension_; }

  private:
    HaltonRsg rsg_;
    Size dimension_;
    InverseCumulativeNormal icn_;
};

F64Out inverse_cumulative_normal_array(nb::handle x, Real average, Real sigma) {
    DoubleInput in(x, "float64", "x");
    InverseCumulativeNormal icn(average, sigma);
    auto out = make_output<double>(in.size);
    double* p = out.data();
    for (std::size_t i = 0; i < in.size; ++i)
        p[i] = indexed(i, [&] { return icn(in.data[i]); });
    return out;
}

F64Out cumulative_normal_array(nb::handle x, Real average, Real sigma) {
    DoubleInput in(x, "float64", "x");
    CumulativeNormalDistribution cnd(average, sigma);
    auto out = make_output<double>(in.size);
    double* p = out.data();
    for (std::size_t i = 0; i < in.size; ++i)
        p[i] = indexed(i, [&] { return cnd(in.data[i]); });
    return out;
}

} // namespace

void bind_random(nb::module_& m) {
    nb::class_<MersenneTwisterRng>(
        m, "MersenneTwisterRng",
        "QuantLib's Mersenne Twister.  A fixed seed reproduces QuantLib's sequence;\n"
        "seed 0 lets QuantLib pick a clock-based seed.")
        .def(nb::init<unsigned long>(), nb::arg("seed") = 42)
        .def("uniform", &MersenneTwisterRng::uniform, nb::arg("n"),
             "n uniform draws in (0, 1) as a 1-D array.")
        .def("gaussian", &MersenneTwisterRng::gaussian, nb::arg("n"),
             "n standard normal draws (inverse cumulative normal of the uniforms).");

    nb::class_<SobolSequence>(m, "SobolSequence",
                              "Sobol low-discrepancy points (Jaeckel direction integers).")
        .def(nb::init<Size, unsigned long>(), nb::arg("dimension"), nb::arg("seed") = 42)
        .def("uniform", &SobolSequence::uniform, nb::arg("points"),
             "Next `points` points in (0, 1)^dimension as a (points, dimension) array.")
        .def("gaussian", &SobolSequence::gaussian, nb::arg("points"),
             "Next `points` points mapped to standard normals, shape (points, dimension).")
        .def("skip_to", &SobolSequence::skip_to, nb::arg("n"),
             "Skip ahead so the next point is point number n.")
        .def_prop_ro("dimension", &SobolSequence::dimension);

    nb::class_<HaltonSequence>(m, "HaltonSequence", "Halton low-discrepancy points.")
        .def(nb::init<Size, unsigned long, bool, bool>(), nb::arg("dimension"),
             nb::arg("seed") = 0, nb::arg("random_start") = true,
             nb::arg("random_shift") = false)
        .def("uniform", &HaltonSequence::uniform, nb::arg("points"),
             "Next `points` points in (0, 1)^dimension as a (points, dimension) array.")
        .def("gaussian", &HaltonSequence::gaussian, nb::arg("points"),
             "Next `points` points mapped to standard normals, shape (points, dimension).")
        .def_prop_ro("dimension", &HaltonSequence::dimension);

    m.def("inverse_cumulative_normal_array", &inverse_cumulative_normal_array, nb::arg("x"),
          nb::arg("average") = 0.0, nb::arg("sigma") = 1.0,
          "Inverse cumulative normal of a float or array of probabilities in (0, 1).");
    m.def("cumulative_normal_array", &cumulative_normal_array, nb::arg("x"),
          nb::arg("average") = 0.0, nb::arg("sigma") = 1.0,
          "Cumulative normal distribution of a float or array.");
}
