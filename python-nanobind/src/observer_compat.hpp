#pragma once

// nanobind <-> QuantLib thread-safe observer build.
//
// With QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN, QuantLib::Observer derives from
// std::enable_shared_from_this<Observer>.  nanobind then takes its
// shared_from_this path for every bound class, which converts a
// shared_ptr<Observer> back to shared_ptr<T> with static_pointer_cast.  That
// does not compile when T reaches Observer through a *virtual* base (LazyObject,
// TermStructure, CalibratedModel, ... all do), so nanobind's detection is turned
// off for the types that are passed as shared_ptr<T> arguments.
//
// This is safe: Observer::Proxy::update() falls back to calling update() on the
// raw pointer when no shared owner has set up the weak reference, which is the
// case for objects owned by a Python wrapper.
//
// If a new binding fails with "cannot convert from pointer to base class
// 'QuantLib::Observer' to pointer to derived class 'X' because the base is
// virtual", add X to the list below.

#include <ql/qldefines.hpp>

#ifdef QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN

#include <nanobind/nanobind.h>

namespace QuantLib {
class BatesDetJumpModel;
class BatesDoubleExpDetJumpModel;
class BatesDoubleExpModel;
class BatesModel;
class CapHelper;
class CapletVarianceCurve;
class CashFlow;
class CmsCouponPricer;
class CmsSpreadCouponPricer;
class EuropeanOption;
class G2;
class GJRGARCHModel;
class Gsr;
class HestonModel;
class HestonModelHelper;
class HullWhite;
class InflationCouponPricer;
class LiborForwardModel;
class MarkovFunctional;
class PiecewiseTimeDependentHestonModel;
class RoughHestonModel;
class Stock;
class SwaptionHelper;
class YoYInflationCoupon;
class YoYInflationCouponPricer;
} // namespace QuantLib

namespace nanobind::detail {
#define QLNB_NO_SHARED_FROM_THIS(T) \
    template <> inline constexpr bool has_shared_from_this_v<QuantLib::T> = false;
QLNB_NO_SHARED_FROM_THIS(BatesDetJumpModel)
QLNB_NO_SHARED_FROM_THIS(BatesDoubleExpDetJumpModel)
QLNB_NO_SHARED_FROM_THIS(BatesDoubleExpModel)
QLNB_NO_SHARED_FROM_THIS(BatesModel)
QLNB_NO_SHARED_FROM_THIS(CapHelper)
QLNB_NO_SHARED_FROM_THIS(CapletVarianceCurve)
QLNB_NO_SHARED_FROM_THIS(CashFlow)
QLNB_NO_SHARED_FROM_THIS(CmsCouponPricer)
QLNB_NO_SHARED_FROM_THIS(CmsSpreadCouponPricer)
QLNB_NO_SHARED_FROM_THIS(EuropeanOption)
QLNB_NO_SHARED_FROM_THIS(G2)
QLNB_NO_SHARED_FROM_THIS(GJRGARCHModel)
QLNB_NO_SHARED_FROM_THIS(Gsr)
QLNB_NO_SHARED_FROM_THIS(HestonModel)
QLNB_NO_SHARED_FROM_THIS(HestonModelHelper)
QLNB_NO_SHARED_FROM_THIS(HullWhite)
QLNB_NO_SHARED_FROM_THIS(InflationCouponPricer)
QLNB_NO_SHARED_FROM_THIS(LiborForwardModel)
QLNB_NO_SHARED_FROM_THIS(MarkovFunctional)
QLNB_NO_SHARED_FROM_THIS(PiecewiseTimeDependentHestonModel)
QLNB_NO_SHARED_FROM_THIS(RoughHestonModel)
QLNB_NO_SHARED_FROM_THIS(Stock)
QLNB_NO_SHARED_FROM_THIS(SwaptionHelper)
QLNB_NO_SHARED_FROM_THIS(YoYInflationCoupon)
QLNB_NO_SHARED_FROM_THIS(YoYInflationCouponPricer)
#undef QLNB_NO_SHARED_FROM_THIS
} // namespace nanobind::detail

#endif
