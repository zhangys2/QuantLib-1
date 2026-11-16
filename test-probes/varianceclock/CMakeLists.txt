# Standalone variance-clock allocation and file-I/O probe.
#
# Built and run only by the Linux CMake build, and only when
# QL_BUILD_VARIANCECLOCK_PROBE is ON.  The probe is deliberately outside
# ql/ and test-suite/: it is not part of the library, the ordinary test
# suite, or any sanitizer run, and Autotools and Visual Studio carry it as
# non-built metadata only.
#
# The allocation, exception and I/O hooks depend on GNU ld --wrap, and the
# replaceable operator new hooks depend on the ELF/GNU toolchain; the parent
# directory refuses non-Linux systems.

add_library(varianceclock_probe_wrap INTERFACE)

set(QL_VARIANCECLOCK_PROBE_WRAP_OPTIONS
    -Wl,--wrap=malloc
    -Wl,--wrap=calloc
    -Wl,--wrap=realloc
    -Wl,--wrap=open
    -Wl,--wrap=read
    -Wl,--wrap=write
    -Wl,--wrap=__cxa_allocate_exception)

target_link_options(varianceclock_probe_wrap
    INTERFACE ${QL_VARIANCECLOCK_PROBE_WRAP_OPTIONS})

function(ql_add_varianceclock_probe target)
    add_executable(${target}
        varianceclock_probe_controls.cpp
        varianceclock_probe_hooks.cpp)
    target_compile_features(${target} PRIVATE cxx_std_17)
    target_include_directories(${target} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
    target_link_libraries(${target} PRIVATE varianceclock_probe_wrap)
endfunction()

# Green binary: every positive control must observe exactly one event.
ql_add_varianceclock_probe(variance_clock_probe)

# Runtime-red binary: the interposers still forward, but recording is
# compiled out, so every positive control must fail.  CTest treats a
# nonzero exit as success for this test.
ql_add_varianceclock_probe(variance_clock_probe_red)
target_compile_definitions(variance_clock_probe_red
    PRIVATE QL_VARIANCECLOCK_PROBE_DISABLED)

add_test(NAME variance_clock_probe_controls COMMAND variance_clock_probe)
add_test(NAME variance_clock_probe_runtime_red COMMAND variance_clock_probe_red)
set_tests_properties(variance_clock_probe_runtime_red
    PROPERTIES WILL_FAIL TRUE)