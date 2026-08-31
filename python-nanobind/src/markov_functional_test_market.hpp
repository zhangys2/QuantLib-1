#pragma once

#include <ql/handle.hpp>
#include <ql/termstructures/volatility/swaption/swaptionvolstructure.hpp>
#include <ql/termstructures/yieldtermstructure.hpp>

namespace qlnb {

QuantLib::Handle<QuantLib::YieldTermStructure> markov_functional_test_md0_yts();
QuantLib::Handle<QuantLib::SwaptionVolatilityStructure>
markov_functional_test_md0_swaption_vts();

} // namespace qlnb
