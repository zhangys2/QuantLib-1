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

set(QL_VARIANCECLOCK_PROBE_WRAP_OPTIONS
    malloc calloc realloc __cxa_allocate_exception
    open open64 openat fopen fopen64
    read pread write pwrite fread fwrite)

function(ql_add_varianceclock_probe target)
    set(omitted_hook "")
    if(ARGC GREATER 1)
        set(omitted_hook "${ARGV1}")
    endif()
    set(wrap_options)
    foreach(symbol IN LISTS QL_VARIANCECLOCK_PROBE_WRAP_OPTIONS)
        if(NOT "${symbol}" STREQUAL "${omitted_hook}")
            list(APPEND wrap_options "-Wl,--wrap=${symbol}")
        endif()
    endforeach()
    add_executable(${target}
        varianceclock_probe_controls.cpp
        varianceclock_probe_hooks.cpp)
    target_compile_features(${target} PRIVATE cxx_std_17)
    target_include_directories(${target} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
    target_link_options(${target} PRIVATE ${wrap_options} -static-libstdc++)
    if(NOT "${omitted_hook}" STREQUAL "")
        string(TOUPPER "${omitted_hook}" omitted_macro)
        target_compile_definitions(${target}
            PRIVATE "QL_VARIANCECLOCK_PROBE_OMIT_${omitted_macro}")
    endif()
endfunction()

function(ql_generate_varianceclock_mutant target mutation)
    set(source_file "${PROJECT_SOURCE_DIR}/ql/time/varianceclock.cpp")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${source_file}")
    file(READ "${source_file}" source)

    if("${mutation}" STREQUAL "query_alloc")
        set(before "VarianceClockView::remaining(VarianceClockInstant time,\n                                 const VarianceClockExpiryToken& expiry) const noexcept {\n        if (!generation_)")
        set(after "VarianceClockView::remaining(VarianceClockInstant time,\n                                 const VarianceClockExpiryToken& expiry) const noexcept {\n        void* probeAllocation = ::operator new(1);\n        ::operator delete(probeAllocation);\n        if (!generation_)")
        string(REPLACE "${before}" "${after}" mutated "${source}")
        string(REPLACE "#include <mutex>" "#include <mutex>\n#include <new>"
                       mutated "${mutated}")
    elseif("${mutation}" STREQUAL "disable_reclaim")
        string(REPLACE "if (generation->use_count() == 1) {"
                       "if (generation->use_count() == 0) {"
                       mutated "${source}")
    else()
        message(FATAL_ERROR "unknown variance-clock mutation: ${mutation}")
    endif()

    if("${mutated}" STREQUAL "${source}")
        message(FATAL_ERROR "variance-clock mutation did not change ${source_file}")
    endif()
    set(template "${CMAKE_CURRENT_BINARY_DIR}/${target}.cpp.in")
    file(WRITE "${template}" "${mutated}")
    configure_file("${template}" "${CMAKE_CURRENT_BINARY_DIR}/${target}.cpp" @ONLY)
endfunction()

function(ql_add_varianceclock_clock_probe target)
    set(clock_source "${PROJECT_SOURCE_DIR}/ql/time/varianceclock.cpp")
    if(ARGC GREATER 1)
        ql_generate_varianceclock_mutant(${target} "${ARGV1}")
        set(clock_source "${CMAKE_CURRENT_BINARY_DIR}/${target}.cpp")
    endif()
    ql_add_varianceclock_probe(${target})
    target_sources(${target} PRIVATE
        "${clock_source}"
        ${PROJECT_SOURCE_DIR}/ql/time/varianceclocktables.cpp)
    target_link_libraries(${target} PRIVATE ql_library)
    target_compile_definitions(${target}
        PRIVATE QL_VARIANCECLOCK_PROBE_CLOCK_CONTROLS)
endfunction()

# Green binary: every positive control must observe exactly one event.
ql_add_varianceclock_probe(variance_clock_probe)

# Runtime-red binary: the interposers still forward, but recording is
# compiled out, so every positive control must fail.  CTest treats a
# nonzero exit as success for this test.
ql_add_varianceclock_probe(variance_clock_probe_red)
target_compile_definitions(variance_clock_probe_red
    PRIVATE QL_VARIANCECLOCK_PROBE_DISABLED
            QL_VARIANCECLOCK_PROBE_BASE_CONTROLS_ONLY)

add_test(NAME variance_clock_probe_controls COMMAND variance_clock_probe)
add_test(NAME variance_clock_probe_runtime_red COMMAND variance_clock_probe_red)
set_tests_properties(variance_clock_probe_runtime_red
    PROPERTIES PASS_REGULAR_EXPRESSION "15 of 15 controls failed")

foreach(symbol IN LISTS QL_VARIANCECLOCK_PROBE_WRAP_OPTIONS)
    string(MAKE_C_IDENTIFIER "${symbol}" identifier)
    set(target "variance_clock_probe_missing_${identifier}")
    ql_add_varianceclock_probe(${target} "${symbol}")
    add_test(NAME "variance_clock_probe_missing_${identifier}" COMMAND ${target})
    set_tests_properties("variance_clock_probe_missing_${identifier}"
        PROPERTIES PASS_REGULAR_EXPRESSION
        "(^|\n)\\[FAIL\\] ${symbol} ")
endforeach()

ql_add_varianceclock_clock_probe(variance_clock_probe_clock)
ql_add_varianceclock_clock_probe(variance_clock_probe_clock_red)
target_compile_definitions(variance_clock_probe_clock_red
    PRIVATE QL_VARIANCECLOCK_PROBE_DISABLED)
add_test(NAME variance_clock_probe_clock_controls COMMAND variance_clock_probe_clock)
add_test(NAME variance_clock_probe_clock_runtime_red COMMAND variance_clock_probe_clock_red)
set_tests_properties(variance_clock_probe_clock_runtime_red
    PROPERTIES PASS_REGULAR_EXPRESSION
               "clock activation positive control observed no allocation")

ql_add_varianceclock_clock_probe(variance_clock_probe_clock_query_red query_alloc)
add_test(NAME variance_clock_probe_clock_query_runtime_red
    COMMAND variance_clock_probe_clock_query_red)
set_tests_properties(variance_clock_probe_clock_query_runtime_red
    PROPERTIES PASS_REGULAR_EXPRESSION
        "(^|\n)\\[FAIL\\] clock capture/query failed or observed allocation/I/O")

ql_add_varianceclock_clock_probe(variance_clock_probe_clock_reclaim_red disable_reclaim)
add_test(NAME variance_clock_probe_clock_reclaim_runtime_red
    COMMAND variance_clock_probe_clock_reclaim_red)
set_tests_properties(variance_clock_probe_clock_reclaim_runtime_red
    PROPERTIES PASS_REGULAR_EXPRESSION
        "(^|\n)\\[FAIL\\] clock reclaim positive control failed to reclaim")
