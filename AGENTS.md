# AGENTS.md

## Cursor Cloud specific instructions

QuantLib is a single C++17 library (not a service). There is nothing long-running to
start: you build a shared library (`libQuantLib`) plus optional example executables and a
Boost.Test test-suite binary, then run those binaries directly. The only hard external
dependency is Boost (installed system-wide via the update script).

### Build / run / test / lint

All commands assume the repo root. The CMake presets in `CMakePresets.json` are the
canonical way to configure; `linux-gcc-release` is the default dev build (it enables
examples + test-suite via the `QL_BUILD_EXAMPLES`/`QL_BUILD_TEST_SUITE` options that
default to `ON` in `CMakeLists.txt`).

- Configure: `cmake --preset linux-gcc-release`
  (add `-DCMAKE_CXX_COMPILER_LAUNCHER=ccache` to reuse the ccache that the update script
  installs; add `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` if you want a `compile_commands.json`
  for clang-tidy).
- Build: `cmake --build build/linux-gcc-release -j$(nproc)`.
  Non-obvious: a full clean build of the whole library + all examples + the test-suite is
  large (~1000 translation units) and takes on the order of ~10-15 min on a 4-core VM.
  ccache makes rebuilds much faster.
- Run an example: binaries land under `build/linux-gcc-release/Examples/<Name>/<Name>`,
  e.g. `build/linux-gcc-release/Examples/EquityOption/EquityOption`.
- Test-suite binary: `build/linux-gcc-release/test-suite/quantlib-test-suite` (Boost.Test).
  - Full run: `./quantlib-test-suite` (long; many minutes).
  - Subset: `./quantlib-test-suite --run_test=QuantLibTests/<SuiteName>` (the top-level
    suite is `QuantLibTests`, e.g. `--run_test=QuantLibTests/AmericanOptionTests`).
  - List suites/cases: `./quantlib-test-suite --list_content`.
- Lint (clang-tidy, config in `.clang-tidy`): the canonical CI path is the
  `linux-ci-build-with-clang-tidy` preset built at `-j1`, which is extremely slow (it is a
  weekly CI job, not a per-change gate). For a quick standalone check, configure with
  `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` and run
  `clang-tidy-19 -p build/linux-gcc-release <file.cpp>`.
  - Non-obvious gotcha: standalone `clang-tidy-19` selects the newest installed GCC
    toolchain and needs the matching `libstdc++` headers, otherwise it fails with
    `'cstddef' file not found`. The update script installs both `libstdc++-14-dev` and
    `clang-tidy-19` so this resolves cleanly.

### Alternative build system

An Autotools build also exists (`./autogen.sh && ./configure && make`), but CMake is the
simplest path in this environment and is what the update script's dependencies target.
