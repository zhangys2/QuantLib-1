#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <cmath>

#include <ql/handle.hpp>
#include <ql/indexes/iborindex.hpp>
#include <ql/instruments/capfloor.hpp>
#include <ql/legacy/libormarketmodels/lfmhullwhiteparam.hpp>
#include <ql/legacy/libormarketmodels/lfmprocess.hpp>
#include <ql/legacy/libormarketmodels/lfmcovarproxy.hpp>
#include <ql/legacy/libormarketmodels/lmexpcorrmodel.hpp>
#include <ql/legacy/libormarketmodels/lmfixedvolmodel.hpp>
#include <ql/legacy/libormarketmodels/lmlinexpvolmodel.hpp>
#include <ql/legacy/libormarketmodels/liborforwardmodel.hpp>
#include <ql/models/model.hpp>
#include <ql/pricingengines/capfloor/analyticcapfloorengine.hpp>
#include <ql/termstructures/volatility/optionlet/capletvariancecurve.hpp>
#include <ql/termstructures/volatility/volatilitytype.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>

using namespace QuantLib;

void bind_lmm(nb::module_& m) {
    nb::class_<LiborForwardModelProcess>(m, "LiborForwardModelProcess")
        .def(nb::init<Size, const ext::shared_ptr<IborIndex>&>(),
             nb::arg("size"),
             nb::arg("index"))
        .def("size", &LiborForwardModelProcess::size)
        .def(
            "fixing_times",
            [](const LiborForwardModelProcess& p) {
                return p.fixingTimes();
            },
            "Fixing times used by the rolling forward measure.")
        .def(
            "fixing_dates",
            [](const LiborForwardModelProcess& p) { return p.fixingDates(); })
        .def("index",
             [](const LiborForwardModelProcess& p) {
                 return p.index();
             })
        .def(
            "set_covar_param",
            [](LiborForwardModelProcess& p,
               const ext::shared_ptr<LfmCovarianceProxy>& param) {
                p.setCovarParam(param);
            },
            nb::arg("covar_param"),
            "Attach LfmCovarianceProxy for process simulation.");

    nb::class_<LmFixedVolatilityModel>(m, "LmFixedVolatilityModel")
        .def(
            "__init__",
            [](LmFixedVolatilityModel* self,
               const std::vector<Real>& volatilities,
               const std::vector<Time>& start_times) {
                new (self) LmFixedVolatilityModel(
                    Array(volatilities.begin(), volatilities.end()),
                    start_times);
            },
            nb::arg("volatilities"),
            nb::arg("start_times"));

    nb::class_<LmExponentialCorrelationModel>(m, "LmExponentialCorrelationModel")
        .def(nb::init<Size, Real>(), nb::arg("size"), nb::arg("rho"));

    nb::class_<LmLinearExponentialVolatilityModel>(m,
                                                     "LmLinearExponentialVolatilityModel")
        .def(
            "__init__",
            [](LmLinearExponentialVolatilityModel* self,
               const std::vector<Time>& fixing_times,
               Real a,
               Real b,
               Real c,
               Real d) {
                new (self) LmLinearExponentialVolatilityModel(
                    fixing_times, a, b, c, d);
            },
            nb::arg("fixing_times"),
            nb::arg("a"),
            nb::arg("b"),
            nb::arg("c"),
            nb::arg("d"));

    nb::class_<LfmCovarianceProxy>(m, "LfmCovarianceProxy")
        .def(
            "__init__",
            [](LfmCovarianceProxy* self,
               const ext::shared_ptr<LmFixedVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LfmCovarianceProxy(vola_model, corr_model);
            },
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "__init__",
            [](LfmCovarianceProxy* self,
               const ext::shared_ptr<LmLinearExponentialVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LfmCovarianceProxy(vola_model, corr_model);
            },
            nb::arg("volatility_model"),
            nb::arg("correlation_model"));

    nb::class_<CapletVarianceCurve>(m, "CapletVarianceCurve")
        .def(nb::init<const Date&,
                      const std::vector<Date>&,
                      const std::vector<Volatility>&,
                      const DayCounter&,
                      VolatilityType,
                      Real>(),
             nb::arg("reference_date"),
             nb::arg("dates"),
             nb::arg("volatilities"),
             nb::arg("day_counter"),
             nb::arg("vol_type") = ShiftedLognormal,
             nb::arg("displacement") = 0.0);

    nb::class_<LiborForwardModel>(m, "LiborForwardModel")
        .def(
            "__init__",
            [](LiborForwardModel* self,
               const ext::shared_ptr<LiborForwardModelProcess>& process,
               const ext::shared_ptr<LmFixedVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LiborForwardModel(process, vola_model, corr_model);
            },
            nb::arg("process"),
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "__init__",
            [](LiborForwardModel* self,
               const ext::shared_ptr<LiborForwardModelProcess>& process,
               const ext::shared_ptr<LmLinearExponentialVolatilityModel>& vola_model,
               const ext::shared_ptr<LmExponentialCorrelationModel>& corr_model) {
                new (self) LiborForwardModel(process, vola_model, corr_model);
            },
            nb::arg("process"),
            nb::arg("volatility_model"),
            nb::arg("correlation_model"))
        .def(
            "s_0",
            &LiborForwardModel::S_0,
            nb::arg("alpha"),
            nb::arg("beta"),
            "Forward swap rate between libor indices alpha and beta.");

    m.def(
        "lm_fixed_volatilities_from_caplet_curve",
        [](const ext::shared_ptr<LiborForwardModelProcess>& process,
           const ext::shared_ptr<CapletVarianceCurve>& caplet_vol) {
            const Array variances =
                LfmHullWhiteParameterization(process, caplet_vol)
                    .covariance(0.0)
                    .diagonal();
            std::vector<Real> vols(variances.size());
            for (Size i = 0; i < variances.size(); ++i)
                vols[i] = std::sqrt(variances[i]);
            return vols;
        },
        nb::arg("process"),
        nb::arg("caplet_vol"),
        "Hull–White LMM volatilities from an optionlet volatility structure.");

    m.def(
        "make_lfm_cap",
        [](const ext::shared_ptr<LiborForwardModelProcess>& process,
           Rate strike,
           Real amount) {
            const Size n = process->size();
            return Cap(process->cashFlows(amount), std::vector<Rate>(n, strike));
        },
        nb::arg("process"),
        nb::arg("strike"),
        nb::arg("amount") = 1.0,
        "Build a Cap on the LiborForwardModelProcess cash-flow leg.");
}
