/*
 Copyright (C) 2026 QuantLib contributors

 This file is part of QuantLib, a free-software/open-source library
 for financial quantitative analysts and developers - http://quantlib.org/

 QuantLib is free software: you can redistribute it and/or modify it
 under the terms of the QuantLib license.  You should have received a
 copy of the license along with this program; if not, please email
 <quantlib-dev@lists.sf.net>. The license is also available online at
 <https://www.quantlib.org/license.shtml>.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the license for more details.
*/

#include <ql/errors.hpp>
#include <ql/time/varianceclock.hpp>
#include <ql/time/varianceclockdetail.hpp>
#include <mutex>
#include <new>
#include <utility>

namespace QuantLib {

    namespace {

        bool outsideCoverage(const detail::VarianceClockNumericEngine& engine,
                             VarianceClockInstant time) noexcept {
            return time < engine.coverageStart() || engine.coverageEnd() < time;
        }

#ifndef NDEBUG
        void assertNoLiveHandles(long references) {
            QL_ASSERT(references == 1, "variance-clock owner destroyed with live handles");
        }

        void assertNoLiveHandles(
            const std::vector<ext::shared_ptr<const detail::VarianceClockGeneration>>& generations) {
            for (const auto& generation : generations)
                assertNoLiveHandles(generation.use_count());
        }
#endif

    }

    Real varianceClockAsReal(const VarianceClockResult& result) {
        QL_REQUIRE(result.status == VarianceClockStatus::Ok ||
                       result.status == VarianceClockStatus::Expired,
                   "variance-clock result has no numeric value");
        return Real(result.weightedDays);
    }

    VarianceClockView::VarianceClockView(
        const ext::shared_ptr<const detail::VarianceClockGeneration>&
            generation) noexcept
    : generation_(generation) {}

    VarianceClockInstant VarianceClockView::coverageStart() const noexcept {
        return generation_ ? generation_->engine().coverageStart() : VarianceClockInstant();
    }

    VarianceClockInstant VarianceClockView::coverageEnd() const noexcept {
        return generation_ ? generation_->engine().coverageEnd() : VarianceClockInstant();
    }

    VarianceClockStatus
    VarianceClockView::prepareExpiry(VarianceClockInstant expiry,
                                     VarianceClockExpiryToken& result) const noexcept {
        if (!generation_)
            return VarianceClockStatus::InvalidView;
        if (!expiry.isValid())
            return VarianceClockStatus::InvalidInstant;
        const auto& engine = generation_->engine();
        if (outsideCoverage(engine, expiry))
            return VarianceClockStatus::OutOfCoverage;
        const auto position = engine.prepareExpiry(expiry);
        result.generation_ = generation_;
        result.expiry_ = position.time;
        result.run_ = position.run;
        result.slot_ = position.slot;
        return VarianceClockStatus::Ok;
    }

    VarianceClockResult
    VarianceClockView::cumulativeFromCoverageStart(VarianceClockInstant time) const noexcept {
        if (!generation_)
            return {VarianceClockStatus::InvalidView, 0.0};
        if (!time.isValid())
            return {VarianceClockStatus::InvalidInstant, 0.0};
        const auto& engine = generation_->engine();
        if (outsideCoverage(engine, time))
            return {VarianceClockStatus::OutOfCoverage, 0.0};
        if (time == engine.coverageStart())
            return {VarianceClockStatus::Ok, 0.0};
        const auto end = engine.prepareExpiry(time);
        if (!engine.isEligible(time, engine.coverageStart(), end))
            return {VarianceClockStatus::BeforeCalibration, 0.0};
        return {VarianceClockStatus::Ok, engine.cumulativeFromCoverageStart(end).weightedDays};
    }

    VarianceClockResult
    VarianceClockView::remaining(VarianceClockInstant time,
                                 const VarianceClockExpiryToken& expiry) const noexcept {
#ifdef QL_VARIANCECLOCK_PROBE_INJECT_QUERY_ALLOC
        void* probeAllocation = ::operator new(1);
        ::operator delete(probeAllocation);
#endif
        if (!generation_)
            return {VarianceClockStatus::InvalidView, 0.0};
        if (!expiry.generation_)
            return {VarianceClockStatus::InvalidToken, 0.0};
        if (generation_.get() != expiry.generation_.get())
            return {VarianceClockStatus::StaleToken, 0.0};
        if (!time.isValid())
            return {VarianceClockStatus::InvalidInstant, 0.0};
        const auto& engine = generation_->engine();
        if (outsideCoverage(engine, time))
            return {VarianceClockStatus::OutOfCoverage, 0.0};
        if (!(time < expiry.expiry_))
            return {VarianceClockStatus::Expired, 0.0};
        const detail::VarianceClockNumericPosition end{expiry.expiry_, expiry.run_, expiry.slot_};
        if (!engine.isEligible(time, time, end))
            return {VarianceClockStatus::BeforeCalibration, 0.0};
        return {VarianceClockStatus::Ok, engine.remaining(time, end).weightedDays};
    }

    VarianceClock::VarianceClock(std::unique_ptr<VarianceClockSnapshot> snapshot) {
        QL_REQUIRE(snapshot, "null variance-clock snapshot");
        generation_ = ext::make_shared<detail::VarianceClockGeneration>(std::move(snapshot));
    }

    VarianceClock::~VarianceClock() noexcept {
#ifndef NDEBUG
        if (generation_)
            assertNoLiveHandles(generation_.use_count());
        assertNoLiveHandles(retired_);
#endif
    }

    VarianceClockView VarianceClock::capture() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return VarianceClockView(generation_);
    }

    void VarianceClock::activate(std::unique_ptr<VarianceClockSnapshot> candidate) {
        QL_REQUIRE(candidate, "null variance-clock snapshot");
        auto next = ext::make_shared<detail::VarianceClockGeneration>(std::move(candidate));

        std::lock_guard<std::mutex> lock(mutex_);
        QL_REQUIRE(!shutdown_, "cannot activate a shut down variance clock");
        if (generation_) {
            retired_.reserve(retired_.size() + 1);
            retired_.push_back(generation_);
        }
        generation_ = std::move(next);
    }

    Size VarianceClock::reclaim() {
#ifdef QL_VARIANCECLOCK_PROBE_DISABLE_RECLAIM
        return 0;
#else
        std::vector<ext::shared_ptr<const detail::VarianceClockGeneration>> releasing;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            releasing.reserve(retired_.size());
            auto generation = retired_.begin();
            while (generation != retired_.end()) {
                if (generation->use_count() == 1) {
                    releasing.push_back(std::move(*generation));
                    generation = retired_.erase(generation);
                } else {
                    ++generation;
                }
            }
        }
        return static_cast<Size>(releasing.size());
#endif
    }

    bool VarianceClock::shutdown() {
        std::vector<ext::shared_ptr<const detail::VarianceClockGeneration>> releasing;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (shutdown_)
                return true;
            if (generation_ && generation_.use_count() != 1)
                return false;
            for (const auto& generation : retired_) {
                if (generation.use_count() != 1)
                    return false;
            }

            releasing.reserve(retired_.size() + (generation_ ? 1 : 0));
            if (generation_)
                releasing.push_back(std::move(generation_));
            for (auto& generation : retired_)
                releasing.push_back(std::move(generation));
            retired_.clear();
            shutdown_ = true;
        }
        return true;
    }

}
