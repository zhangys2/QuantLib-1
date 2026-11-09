# Free-threading readiness (qlnb)

Python 3.13+ free-threading (`python3.13t`, no GIL) is an emerging target for
native extensions. `qlnb` is **not yet validated** on free-threaded CPython in
default CI. This note records the current status and how to experiment locally.

## Status

| Area | Status |
| --- | --- |
| Default wheels / CI | GIL CPython only (Stable ABI / cp312 manylinux) |
| nanobind | Recent nanobind releases support free-threaded builds when compiled against a free-threaded interpreter |
| QuantLib observers | Thread-safe pattern is on by default (`QLNB_THREAD_SAFE_OBSERVER=ON`); opt out with `-C cmake.define.QLNB_THREAD_SAFE_OBSERVER=OFF` |
| qlnb Settings / Handles | Share process-wide QuantLib singletons — not free-thread safe without care |

Treat multi-threaded use of a single `qlnb` process as **experimental**. Prefer
one evaluation context per process, or serialize access to Settings / shared
handles.

See also [parallel-pricing.md](parallel-pricing.md) for `npv_many`, which
uses native threads with the GIL released and needs the same build option.

## QuantLib thread-safe observer pattern

QuantLib's observable/observer notifications race under threads unless built
with:

```text
QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN=ON
```

`qlnb` builds with this pattern **by default**. To opt out of it (a cheaper,
single-threaded build):

```bash
pip install --no-build-isolation . \
  -C cmake.define.QLNB_THREAD_SAFE_OBSERVER=OFF
```

`QLNB_THREAD_SAFE_OBSERVER=ON` (the default) forces
`QL_ENABLE_THREAD_SAFE_OBSERVER_PATTERN=ON` on the embedded QuantLib static
library (see `python-nanobind/CMakeLists.txt`).

This is necessary but not sufficient for free-threaded correctness: Python
code must still avoid concurrent mutation of shared Quotes, RelinkableHandles,
and `Settings.evaluation_date`.

## Optional CI job

`.github/workflows/qlnb-wheels.yml` includes a **disabled-by-default** job
`build_wheels_freethreading` (`if: false`). Enable it manually when a runner
image provides `python3.13t` / a free-threaded cibuildwheel tag. The default
matrix stays small (manylinux x86_64 only).

## Local experiment checklist

1. Install a free-threaded CPython (e.g. `python3.13t`).
2. Create a venv with that interpreter.
3. Build with `QLNB_THREAD_SAFE_OBSERVER=ON` and a matching nanobind.
4. Run `pytest` under that interpreter.
5. Do **not** assume Stable ABI (`abi3`) wheels from GIL builds are usable on
   free-threaded builds — rebuild against the free-threaded ABI.

## Follow-ups

- Validate nanobind free-threaded wheel tags once runners are available.
- Audit Settings / Handle usage for concurrent access patterns.
- Document any remaining global state (evaluation date, index fixings).
