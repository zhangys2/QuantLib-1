#include "bindings.hpp"

#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/math/interpolations/linearinterpolation.hpp>
#include <ql/pricingengines/blackformula.hpp>
#include <ql/termstructures/volatility/interpolatedsmilesection.hpp>
#include <ql/termstructures/volatility/kahalesmilesection.hpp>

using namespace QuantLib;

namespace {

using LinearSmileSection = InterpolatedSmileSection<Linear>;

struct LinearSmileSectionHandle {
    ext::shared_ptr<LinearSmileSection> section;

    explicit LinearSmileSectionHandle(ext::shared_ptr<LinearSmileSection> section_)
        : section(std::move(section_)) {}

    Real optionPrice(Rate strike) const { return section->optionPrice(strike); }
    Real atmLevel() const { return section->atmLevel(); }
};

} // namespace

void bind_smile(nb::module_& m) {
    m.def(
        "black_formula",
        [](Option::Type option_type,
           Real strike,
           Real forward,
           Real std_dev,
           Real discount,
           Real displacement) {
            return blackFormula(
                option_type, strike, forward, std_dev, discount, displacement);
        },
        nb::arg("option_type"),
        nb::arg("strike"),
        nb::arg("forward"),
        nb::arg("std_dev"),
        nb::arg("discount") = 1.0,
        nb::arg("displacement") = 0.0,
        "Black (1976) formula using stdDev = vol * sqrt(T).");

    m.def(
        "black_formula_implied_std_dev",
        [](Option::Type option_type,
           Real strike,
           Real forward,
           Real black_price,
           Real discount,
           Real displacement,
           Real guess,
           Real accuracy,
           Natural max_iterations) {
            return blackFormulaImpliedStdDev(
                option_type,
                strike,
                forward,
                black_price,
                discount,
                displacement,
                guess,
                accuracy,
                max_iterations);
        },
        nb::arg("option_type"),
        nb::arg("strike"),
        nb::arg("forward"),
        nb::arg("black_price"),
        nb::arg("discount") = 1.0,
        nb::arg("displacement") = 0.0,
        nb::arg("guess") = 0.2,
        nb::arg("accuracy") = 1e-8,
        nb::arg("max_iterations") = 1000,
        "Black (1976) implied standard deviation.");

    nb::class_<LinearSmileSectionHandle>(m, "LinearSmileSection")
        .def(
            "__init__",
            [](LinearSmileSectionHandle* self,
               Time expiry_time,
               const std::vector<Rate>& strikes,
               const std::vector<Real>& std_devs,
               Real atm_level) {
                new (self) LinearSmileSectionHandle(ext::make_shared<LinearSmileSection>(
                    expiry_time, strikes, std_devs, atm_level));
            },
            nb::arg("expiry_time"),
            nb::arg("strikes"),
            nb::arg("std_devs"),
            nb::arg("atm_level"))
        .def("option_price", &LinearSmileSectionHandle::optionPrice, nb::arg("strike"))
        .def("atm_level", &LinearSmileSectionHandle::atmLevel);

    nb::class_<KahaleSmileSection>(m, "KahaleSmileSection")
        .def(
            "__init__",
            [](KahaleSmileSection* self,
               const LinearSmileSectionHandle& source,
               std::optional<Real> atm,
               bool interpolate,
               bool exponential_extrapolation,
               bool delete_arbitrage_points,
               const std::vector<Real>& moneyness_grid) {
                new (self) KahaleSmileSection(
                    ext::static_pointer_cast<SmileSection>(source.section),
                    atm.value_or(Null<Real>()),
                    interpolate,
                    exponential_extrapolation,
                    delete_arbitrage_points,
                    moneyness_grid);
            },
            nb::arg("source"),
            nb::arg("atm") = nb::none(),
            nb::arg("interpolate") = false,
            nb::arg("exponential_extrapolation") = false,
            nb::arg("delete_arbitrage_points") = false,
            nb::arg("moneyness_grid") = std::vector<Real>{})
        .def("left_core_strike", &KahaleSmileSection::leftCoreStrike)
        .def("right_core_strike", &KahaleSmileSection::rightCoreStrike)
        .def(
            "option_price",
            [](KahaleSmileSection& section, Rate strike) {
                return section.optionPrice(strike);
            },
            nb::arg("strike"))
        .def(
            "digital_option_price",
            [](KahaleSmileSection& section, Rate strike) {
                return section.digitalOptionPrice(strike);
            },
            nb::arg("strike"));
}
