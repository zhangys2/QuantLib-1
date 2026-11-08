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
#include <ql/qldefines.hpp>

#include <algorithm>
#include <atomic>
#include <exception>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using namespace QuantLib;

namespace {

#ifdef QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN
constexpr bool kThreadSafeObserver = true;
#else
constexpr bool kThreadSafeObserver = false;
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
            std::string message;

            // Some QuantLib objects initialise lazily inside const accessors on
            // first use (e.g. GeneralizedBlackScholesProcess::localVolatility()
            // relinks a mutable handle).  Pricing the first instrument serially
            // performs that initialisation once for the setup it shares with the
            // rest of the book.
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
        "warmup=True prices the first instrument serially before starting threads; with\n"
        "several distinct shared setups (processes, curves) price one instrument of each\n"
        "yourself first.  Instruments, quotes, curves and the evaluation date must not be\n"
        "modified while the call runs.  Supported: VanillaOption, EuropeanOption,\n"
        "FixedRateBond.  Errors name the failing element index.");
}
