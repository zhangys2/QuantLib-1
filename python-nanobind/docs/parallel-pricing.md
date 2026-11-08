# Parallel pricing with `npv_many`

`qlnb.npv_many(instruments, threads=0, warmup=True)` prices a sequence of
instruments with the GIL released and returns a float64 NumPy array. With
several threads it spreads the book across native threads.

```python
import qlnb as ql
npvs = ql.npv_many(book)               # every hardware thread, if the build allows
npvs = ql.npv_many(book, threads=4)
npvs = ql.npv_many(book, threads=1)    # serial, GIL released
```

Supported instruments: `VanillaOption`, `EuropeanOption`, `FixedRateBond`.
Other types raise `TypeError`; add them in `src/bind_parallel.cpp`.

## Requires the thread-safe observer build

QuantLib's observer pattern is not thread-safe by default. Some engines create
temporary observers of shared market data while pricing (for example
`BinomialVanillaEngine` builds a temporary `GeneralizedBlackScholesProcess` on
every call). Threads then add and remove entries in the same quote's observer
set at the same time, which corrupts the heap. ThreadSanitizer reports this as
a race in `Observable::unregisterObserver`.

So multi-threaded use needs QuantLib built with
`QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN`:

```bash
CMAKE_ARGS="-DQLNB_THREAD_SAFE_OBSERVER=ON" pip install --no-build-isolation .
```

`qlnb.THREAD_SAFE_OBSERVER` tells you which kind of build you have. On a
default build:

| Call | Behaviour |
| --- | --- |
| `threads=0` (default) | runs serially |
| `threads=1` | runs serially |
| `threads>1` | raises `RuntimeError` |

so code that calls `npv_many(book)` is correct everywhere and only gets faster
where threading is allowed.

The wheels CI builds are default builds. The `threadsafe` job in
`.github/workflows/qlnb-wheels.yml` builds and tests a thread-safe build from
source; no thread-safe wheel is published yet.

## Contract

- Do not change quotes, curves, the evaluation date or pricing engines, or
  create and destroy objects that observe them, while a call is running.
- Instruments may share processes, curves and quotes. That is the normal layout
  and is covered by the tests.
- `warmup=True` prices the first instrument serially before starting threads.
  Some QuantLib objects initialise lazily inside `const` accessors (for example
  `GeneralizedBlackScholesProcess::localVolatility()` relinks a mutable handle),
  so this does it once for the setup the book shares. If the book has several
  distinct shared setups, price one instrument of each first.
- Results are bit-identical to pricing the same instruments one by one.
- A failure reports the element index: `RuntimeError: element 23: ...`.

## Cost of the thread-safe build

Thread-safe observers add locking and heap allocation to every register and
notify. Measured on 2000 instruments (noisy, 4-core machine):

| Operation | default | thread-safe |
| --- | --- | --- |
| build European options | 3.9 µs each | 7.5 µs each |
| build fixed-rate bonds | 7.6 µs each | 21.9 µs each |
| notify observers after a spot bump | 0.02 µs each | 0.31 µs each |
| bump spot and reprice (analytic) | 1.95 µs each | 2.95 µs each |
| first or cached `NPV()` | same | same |

Heavy engines are unaffected, except that engines which create temporary
observers on every call (binomial) pay the registration cost each time, about
9% serially in our measurements.

## Speedup

`python benchmarks/bench_parallel.py` on a 4-core machine, 800 American options
sharing one process:

| Engine | 1 thread | 2 threads | 4 threads |
| --- | --- | --- | --- |
| binomial, 200 steps | 318 ms | 156 ms (2.0x) | 85 ms (3.7x) |
| finite difference, 100x100 | 430 ms | 212 ms (2.0x) | 124 ms (3.5x) |

Cheap analytic instruments (about 1 µs each) gain little: thread start-up and
the serial warm-up dominate unless the book has well over 100,000 of them.

## Build note for the bindings

With thread-safe observers `QuantLib::Observer` derives from
`std::enable_shared_from_this`, and nanobind's `shared_ptr` caster then fails to
compile for classes that reach `Observer` through a virtual base. The fix is
`src/observer_compat.hpp`, which switches nanobind's shared-from-this handling
off for the affected types. If a new binding fails with "cannot convert from
pointer to base class 'QuantLib::Observer' ... because the base is virtual" in
the thread-safe build, add the class to the list there. The `threadsafe` CI job
keeps this from rotting.
