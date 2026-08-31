#include "bindings.hpp"

#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <ql/indexes/iborindex.hpp>
#include <ql/indexes/swapindex.hpp>
#include <ql/models/shortrate/onefactormodels/markovfunctional.hpp>
#include <ql/termstructures/volatility/optionlet/optionletvolatilitystructure.hpp>
#include <ql/termstructures/volatility/swaption/swaptionvolstructure.hpp>

using namespace QuantLib;

namespace {

using MF = MarkovFunctional;

} // namespace

void bind_markov_functional(nb::module_& m) {
    nb::enum_<MF::ModelSettings::Adjustments>(m, "MarkovFunctionalAdjustment")
        .value("AdjustNone", MF::ModelSettings::AdjustNone)
        .value("AdjustDigitals", MF::ModelSettings::AdjustDigitals)
        .value("AdjustYts", MF::ModelSettings::AdjustYts)
        .value("ExtrapolatePayoffFlat", MF::ModelSettings::ExtrapolatePayoffFlat)
        .value("NoPayoffExtrapolation", MF::ModelSettings::NoPayoffExtrapolation)
        .value("KahaleSmile", MF::ModelSettings::KahaleSmile)
        .value("SmileExponentialExtrapolation",
               MF::ModelSettings::SmileExponentialExtrapolation)
        .value("KahaleInterpolation", MF::ModelSettings::KahaleInterpolation)
        .value("SmileDeleteArbitragePoints",
               MF::ModelSettings::SmileDeleteArbitragePoints)
        .value("SabrSmile", MF::ModelSettings::SabrSmile)
        .value("CustomSmile", MF::ModelSettings::CustomSmile)
        .export_values();

    nb::class_<MF::ModelSettings>(m, "MarkovFunctionalModelSettings")
        .def(nb::init<>())
        .def(
            "with_y_grid_points",
            &MF::ModelSettings::withYGridPoints,
            nb::arg("n"),
            nb::rv_policy::reference_internal)
        .def(
            "with_y_std_devs",
            &MF::ModelSettings::withYStdDevs,
            nb::arg("s"),
            nb::rv_policy::reference_internal)
        .def(
            "with_gauss_hermite_points",
            &MF::ModelSettings::withGaussHermitePoints,
            nb::arg("n"),
            nb::rv_policy::reference_internal)
        .def(
            "with_digital_gap",
            &MF::ModelSettings::withDigitalGap,
            nb::arg("d"),
            nb::rv_policy::reference_internal)
        .def(
            "with_market_rate_accuracy",
            &MF::ModelSettings::withMarketRateAccuracy,
            nb::arg("a"),
            nb::rv_policy::reference_internal)
        .def(
            "with_upper_rate_bound",
            &MF::ModelSettings::withUpperRateBound,
            nb::arg("u"),
            nb::rv_policy::reference_internal)
        .def(
            "with_lower_rate_bound",
            &MF::ModelSettings::withLowerRateBound,
            nb::arg("l"),
            nb::rv_policy::reference_internal)
        .def(
            "with_adjustments",
            [](MF::ModelSettings& s, MF::ModelSettings::Adjustments a) {
                return s.withAdjustments(static_cast<int>(a));
            },
            nb::arg("a"),
            nb::rv_policy::reference_internal)
        .def(
            "add_adjustment",
            [](MF::ModelSettings& s, MF::ModelSettings::Adjustments a) {
                return s.addAdjustment(static_cast<int>(a));
            },
            nb::arg("a"),
            nb::rv_policy::reference_internal)
        .def(
            "remove_adjustment",
            [](MF::ModelSettings& s, MF::ModelSettings::Adjustments a) {
                return s.removeAdjustment(static_cast<int>(a));
            },
            nb::arg("a"),
            nb::rv_policy::reference_internal)
        .def(
            "with_smile_moneyness_checkpoints",
            &MF::ModelSettings::withSmileMoneynessCheckpoints,
            nb::arg("m"),
            nb::rv_policy::reference_internal);

    nb::class_<MF::ModelOutputs>(m, "MarkovFunctionalModelOutputs")
        .def_ro("expiries", &MF::ModelOutputs::expiries_)
        .def_ro("tenors", &MF::ModelOutputs::tenors_)
        .def_ro("atm", &MF::ModelOutputs::atm_)
        .def_ro("annuity", &MF::ModelOutputs::annuity_)
        .def_ro("smile_strikes", &MF::ModelOutputs::smileStrikes_)
        .def_ro("market_call_premium", &MF::ModelOutputs::marketCallPremium_)
        .def_ro("market_put_premium", &MF::ModelOutputs::marketPutPremium_)
        .def_ro("market_raw_call_premium", &MF::ModelOutputs::marketRawCallPremium_)
        .def_ro("market_raw_put_premium", &MF::ModelOutputs::marketRawPutPremium_)
        .def_ro("market_zerorate", &MF::ModelOutputs::marketZerorate_)
        .def_ro("model_zerorate", &MF::ModelOutputs::modelZerorate_)
        .def_ro("model_call_premium", &MF::ModelOutputs::modelCallPremium_)
        .def_ro("model_put_premium", &MF::ModelOutputs::modelPutPremium_);

    nb::class_<MarkovFunctional>(m, "MarkovFunctional")
        .def(
            "__init__",
            [](MarkovFunctional* self,
               const Handle<YieldTermStructure>& term_structure,
               Real reversion,
               const std::vector<Date>& vol_step_dates,
               const std::vector<Real>& volatilities,
               const Handle<SwaptionVolatilityStructure>& swaption_vol,
               const std::vector<Date>& swaption_expiries,
               const std::vector<Period>& swaption_tenors,
               const ext::shared_ptr<SwapIndex>& swap_index_base,
               const MF::ModelSettings& model_settings) {
                new (self) MarkovFunctional(
                    term_structure,
                    reversion,
                    vol_step_dates,
                    volatilities,
                    swaption_vol,
                    swaption_expiries,
                    swaption_tenors,
                    swap_index_base,
                    model_settings);
            },
            nb::arg("term_structure"),
            nb::arg("reversion"),
            nb::arg("vol_step_dates"),
            nb::arg("volatilities"),
            nb::arg("swaption_vol"),
            nb::arg("swaption_expiries"),
            nb::arg("swaption_tenors"),
            nb::arg("swap_index_base"),
            nb::arg("model_settings"))
        .def(
            "__init__",
            [](MarkovFunctional* self,
               const Handle<YieldTermStructure>& term_structure,
               Real reversion,
               const std::vector<Date>& vol_step_dates,
               const std::vector<Real>& volatilities,
               const Handle<OptionletVolatilityStructure>& caplet_vol,
               const std::vector<Date>& caplet_expiries,
               const ext::shared_ptr<IborIndex>& ibor_index,
               const MF::ModelSettings& model_settings) {
                new (self) MarkovFunctional(
                    term_structure,
                    reversion,
                    vol_step_dates,
                    volatilities,
                    caplet_vol,
                    caplet_expiries,
                    ibor_index,
                    model_settings);
            },
            nb::arg("term_structure"),
            nb::arg("reversion"),
            nb::arg("vol_step_dates"),
            nb::arg("volatilities"),
            nb::arg("caplet_vol"),
            nb::arg("caplet_expiries"),
            nb::arg("ibor_index"),
            nb::arg("model_settings"))
        .def(
            "model_outputs",
            [](const MarkovFunctional& model) { return model.modelOutputs(); },
            "Calibration diagnostics (MarkovFunctional::ModelOutputs).")
        .def(
            "model_settings",
            [](const MarkovFunctional& model) { return model.modelSettings(); })
        .def("numeraire_date", &MarkovFunctional::numeraireDate)
        .def("numeraire_time", &MarkovFunctional::numeraireTime);
}
