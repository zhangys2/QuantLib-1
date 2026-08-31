#pragma once

#include <ql/handle.hpp>
#include <ql/termstructures/volatility/optionlet/optionletvolatilitystructure.hpp>
#include <ql/termstructures/volatility/swaption/swaptionvolstructure.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>
#include <ql/types.hpp>
#include <vector>

namespace qlnb {

QuantLib::Handle<QuantLib::YieldTermStructure> markov_functional_test_md0_yts();
QuantLib::Handle<QuantLib::SwaptionVolatilityStructure>
markov_functional_test_md0_swaption_vts();
QuantLib::Handle<QuantLib::OptionletVolatilityStructure>
markov_functional_test_md0_optionlet_vts();
std::vector<QuantLib::Real> markov_functional_test_md0_coterminal_helper_vols();

} // namespace qlnb
