// npv_many(): price many instruments with the GIL released, optionally across
// several native threads.
//
// Threading is only safe when QuantLib is built with
// QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN (CMake: -DQLNB_THREAD_SAFE_OBSERVER=ON).
// Engines such as BinomialVanillaEngine create temporary observers of shared
// market data while pricing; without the thread-safe pattern that races on the
// observable's observer set and corrupts the heap.  A default build therefore
// runs npv_many() serially and rejects threads > 1.
//
// Contract for callers: do not change quotes, curves, the evaluation date or the
// pricing engines while a call is running.  See docs/parallel-pricing.md.

#include "bindings.hpp"

#include <nanobind/ndarray.h>

#include <ql/errors.hpp>
#include <ql/instruments/bonds/fixedratebond.hpp>
#include <ql/instruments/europeanoption.hpp>
#include <ql/instruments/vanillaoption.hpp>
#include <ql/patterns/lazyobject.hpp>
#include <ql/patterns/observable.hpp>
#include <ql/qldefines.hpp>

#include <algorithm>
#include <atomic>
#include <exception>
#include <stdexcept>
#include <string>
#include <set>
#include <thread>
#include <unordered_set>
#include <vector>

using namespace QuantLib;

namespace {

#ifdef QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN
constexpr bool kThreadSafeObserver = true;
#else
constexpr bool kThreadSafeObserver = false;
#endif

#ifdef QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN

// QuantLib's LazyObject::calculate() is not thread-safe: a shared curve or
// surface that two threads reach for the first time at the same time can be read
// half initialised (an exception such as "null interest rate", or silently wrong
// numbers).  Everything an instrument depends on is reachable through the
// observer graph (instrument -> engine -> process / handles -> curves ...), so
// those shared lazy objects are calculated serially before the threads start.
//
// Observer::observables_ is private and has no accessor; reach it with the
// explicit-instantiation access idiom (instantiation ignores access control).
// Only built with thread-safe observers, which is the only case that threads.
using ObservableSet = std::set<ext::shared_ptr<Observable>>;
template <ObservableSet Observer::*Member>
struct ObserverAccess {
    friend ObservableSet const& registered_with(const Observer& o) { return o.*Member; }
};
template struct ObserverAccess<&Observer::observables_>;
ObservableSet const& registered_with(const Observer&);

// LazyObject::calculate() is protected; recalculate() is public but would also
// notify observers and invalidate the instruments, so use the same idiom.
using CalculateFn = void (LazyObject::*)() const;
template <CalculateFn Member>
struct LazyAccess {
    friend void calculate_now(const LazyObject& o) { (o.*Member)(); }
};
template struct LazyAccess<&LazyObject::calculate>;
void calculate_now(const LazyObject&);

void prime_dependencies(Observer& node, std::unordered_set<const Observable*>& seen) {
    for (const auto& dep : registered_with(node)) {
        Observable* observable = dep.get();
        if (!observable || !seen.insert(observable).second)
            continue;
        // Dependencies first, so a lazy object finds its own inputs calculated.
        if (auto* observer = dynamic_cast<Observer*>(observable))
            prime_dependencies(*observer, seen);
        if (auto* lazy = dynamic_cast<LazyObject*>(observable)) {
            try {
                calculate_now(*lazy);
            } catch (...) {
                // Pricing reports the error with the element index later.
            }
        }
    }
}

void prime_dependencies(const std::vector<Instrument*>& items) {
    std::unordered_set<const Observable*> seen;
    for (auto* item : items)
        prime_dependencies(*dynamic_cast<Observer*>(item), seen);
}

#endif

template <class T>
bool try_resolve(nb::handle h, Instrument*& out) {
    if (!nb::isinstance<T>(h))
        return false;
    out = static_cast<Instrument*>(nb::inst_ptr<T>(h));
    return true;
}

// Instruments are bound as independent classes (no common Python base), so the
// list of supported types is explicit.  Add a type here to support it.
Instrument* resolve(nb::handle h) {
    Instrument* p = nullptr;
    if (try_resolve<VanillaOption>(h, p) || try_resolve<EuropeanOption>(h, p) ||
        try_resolve<FixedRateBond>(h, p))
        return p;
    throw nb::type_error(
        "npv_many: unsupported instrument type (supported: VanillaOption, "
        "EuropeanOption, FixedRateBond)");
}

} // namespace

void bind_parallel(nb::module_& m) {
    m.attr("THREAD_SAFE_OBSERVER") = kThreadSafeObserver;

    m.def(
        "npv_many",
        [](nb::sequence instruments, int threads, bool warmup) {
            if (threads < 0)
                throw nb::value_error("npv_many: threads must be >= 0");
            if (threads > 1 && !kThreadSafeObserver)
                throw std::runtime_error(
                    "npv_many: threads > 1 needs a build with thread-safe observers "
                    "(CMake option QLNB_THREAD_SAFE_OBSERVER=ON); see "
                    "docs/parallel-pricing.md");

            const std::size_t n = nb::len(instruments);
            std::vector<nb::object> keep; // keeps every instrument alive
            std::vector<Instrument*> items;
            keep.reserve(n);
            items.reserve(n);
            for (std::size_t i = 0; i < n; ++i) {
                keep.emplace_back(instruments[i]);
                items.push_back(resolve(keep.back()));
            }

            // threads == 0 means "every hardware thread" where that is safe and
            // serial otherwise.
            std::size_t workers =
                threads > 0 ? static_cast<std::size_t>(threads)
                : kThreadSafeObserver ? std::max(1u, std::thread::hardware_concurrency())
                                      : 1;
            workers = std::max<std::size_t>(1, std::min(workers, n));

            std::vector<double> npv(n);
            std::atomic<bool> failed{false};

#ifdef QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN
            if (workers > 1) {
                nb::gil_scoped_release release;
                prime_dependencies(items);
            }
#endif
            std::string message;

            // Shared LazyObjects were calculated above.  Some other objects also
            // initialise mutable state inside const accessors on first use (e.g.
            // GeneralizedBlackScholesProcess::localVolatility() relinks a handle);
            // pricing the first instrument serially performs that once for the
            // setup it shares with the rest of the book.
            const std::size_t first = (warmup && n > 0) ? 1 : 0;
            std::atomic<std::size_t> next{first};

            auto record_failure = [&](std::size_t i, const std::exception& e) {
                if (!failed.exchange(true))
                    message = "element " + std::to_string(i) + ": " + e.what();
            };

            auto work = [&]() {
                constexpr std::size_t chunk = 16;
                for (;;) {
                    if (failed.load(std::memory_order_relaxed))
                        return;
                    const std::size_t lo = next.fetch_add(chunk);
                    if (lo >= n)
                        return;
                    const std::size_t hi = std::min(n, lo + chunk);
                    for (std::size_t i = lo; i < hi; ++i) {
                        try {
                            npv[i] = items[i]->NPV();
                        } catch (const std::exception& e) {
                            record_failure(i, e);
                            return;
                        }
                    }
                }
            };

            {
                nb::gil_scoped_release release;
                if (first == 1) {
                    try {
                        npv[0] = items[0]->NPV();
                    } catch (const std::exception& e) {
                        record_failure(0, e);
                    }
                }
                if (!failed) {
                    std::vector<std::thread> pool;
                    for (std::size_t t = 1; t < workers; ++t)
                        pool.emplace_back(work);
                    work();
                    for (auto& t : pool)
                        t.join();
                }
            }
            if (failed)
                throw std::runtime_error(message);

            double* data = new double[n];
            std::copy(npv.begin(), npv.end(), data);
            nb::capsule owner(data, [](void* p) noexcept { delete[] static_cast<double*>(p); });
            return nb::ndarray<nb::numpy, double, nb::ndim<1>>(data, {n}, owner);
        },
        nb::arg("instruments"), nb::arg("threads") = 0, nb::arg("warmup") = true,
        "NPV of each instrument as a float64 array, computed with the GIL released.\n\n"
        "threads=0 uses every hardware thread when the build has thread-safe observers\n"
        "(qlnb.THREAD_SAFE_OBSERVER) and runs serially otherwise; threads=1 is always\n"
        "serial; threads>1 raises RuntimeError on a build without thread-safe observers.\n"
        "Before starting threads, the lazily calculated objects the instruments share\n"
        "(curves, surfaces) are calculated, and warmup=True also prices the first\n"
        "instrument serially to initialise caches such as a process's local volatility.\n"
        "Instruments, quotes, curves and the evaluation date must not be modified while\n"
        "the call runs.  Supported: VanillaOption, EuropeanOption,\n"
        "FixedRateBond.  Errors name the failing element index.");
}
