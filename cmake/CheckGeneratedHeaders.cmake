if (NOT DEFINED QL_SOURCE_DIR OR NOT DEFINED QL_BINARY_DIR)
    message(FATAL_ERROR "QL_SOURCE_DIR and QL_BINARY_DIR must be set")
endif()

set(SOURCE_DIR "${QL_SOURCE_DIR}")
set(BINARY_DIR "${QL_BINARY_DIR}/generated-header-visibility-test")
file(REMOVE_RECURSE "${BINARY_DIR}")
include("${SOURCE_DIR}/cmake/GenerateHeaders.cmake")

file(READ "${BINARY_DIR}/ql/time/all.hpp" time_headers)
file(READ "${BINARY_DIR}/ql/utilities/all.hpp" utility_headers)
file(READ "${BINARY_DIR}/ql/quantlib.hpp" quantlib_header)

foreach (header IN ITEMS
        varianceclockbundle.hpp
        varianceclockbundlesource.hpp
        varianceclockbundletypes.hpp)
    string(FIND "${time_headers}" "#include <ql/time/${header}>" position)
    if (position EQUAL -1)
        message(FATAL_ERROR "Public time header ${header} is missing from all.hpp")
    endif()
endforeach()

foreach (header IN ITEMS
        varianceclockdetail.hpp
        varianceclockbundlecapture.hpp
        varianceclockbundledata.hpp
        varianceclockbundleevidence.hpp
        varianceclockcsv.hpp
        varianceclockmanifest.hpp)
    string(FIND "${time_headers}" "#include <ql/time/${header}>" position)
    if (NOT position EQUAL -1)
        message(FATAL_ERROR "Private time header ${header} leaked into all.hpp")
    endif()
endforeach()

if (utility_headers MATCHES "detail/")
    message(FATAL_ERROR "Private utilities/detail headers leaked into all.hpp")
endif()
if (EXISTS "${BINARY_DIR}/ql/utilities/detail/all.hpp")
    message(FATAL_ERROR "A private utilities/detail aggregate was generated")
endif()

foreach (header IN ITEMS ql/time/all.hpp ql/utilities/all.hpp)
    string(FIND "${quantlib_header}" "#include <${header}>" position)
    if (position EQUAL -1)
        message(FATAL_ERROR "Root umbrella is missing ${header}")
    endif()
endforeach()

# The names above are the headers known today. Check the rule behind them as well, against what
# ql/CMakeLists.txt actually installs: QL_HEADERS and QL_GENERATED_HEADERS are both installed
# verbatim. Every header an aggregate includes must therefore be in QL_HEADERS, be a generated
# aggregate listed in QL_GENERATED_HEADERS, or be the configured qldefines.hpp, and every
# generated aggregate must be listed. A future private header, or a generated aggregate that
# nobody declared, is then caught without being named.
# Reads the arguments of set(<name> ...) from ql/CMakeLists.txt as whole whitespace-separated
# tokens, so dotted names such as config.ansi.hpp are kept intact, and refuses anything that is
# not a plain .hpp path.
function(read_header_list name output)
    file(READ "${SOURCE_DIR}/ql/CMakeLists.txt" ql_cmake)
    string(REGEX MATCH "set\\(${name}[^)]*\\)" block "${ql_cmake}")
    if (NOT block)
        message(FATAL_ERROR "Could not read ${name} from ql/CMakeLists.txt")
    endif()
    string(REGEX REPLACE "^set\\(${name}[ \t\r\n]*" "" block "${block}")
    string(REGEX REPLACE "[ \t\r\n]*\\)$" "" block "${block}")
    string(REGEX REPLACE "[ \t\r\n]+" ";" block "${block}")
    foreach (token IN LISTS block)
        if (NOT token MATCHES "\\.hpp$")
            message(FATAL_ERROR "Unexpected entry '${token}' in ${name} in ql/CMakeLists.txt")
        endif()
    endforeach()
    set(${output} "${block}" PARENT_SCOPE)
endfunction()

read_header_list(QL_HEADERS installed_headers)
read_header_list(QL_GENERATED_HEADERS generated_entries)
list(FIND installed_headers "config.ansi.hpp" dotted_header)
if (dotted_header EQUAL -1)
    message(FATAL_ERROR "Dotted public-header names must remain whole list entries")
endif()
set(installed_aggregates "")
foreach (entry IN LISTS generated_entries)
    if (NOT entry MATCHES "^[$]{PROJECT_BINARY_DIR}/ql/")
        message(FATAL_ERROR "Unexpected entry '${entry}' in QL_GENERATED_HEADERS")
    endif()
    string(REGEX REPLACE "^[$]{PROJECT_BINARY_DIR}/ql/" "" entry "${entry}")
    list(APPEND installed_aggregates "${entry}")
endforeach()

file(GLOB_RECURSE aggregate_files "${BINARY_DIR}/ql/*all.hpp" "${BINARY_DIR}/ql/quantlib.hpp")
set(generated_aggregates "")
foreach (aggregate IN LISTS aggregate_files)
    file(RELATIVE_PATH aggregate_name "${BINARY_DIR}/ql" "${aggregate}")
    list(APPEND generated_aggregates "${aggregate_name}")
    list(FIND installed_aggregates "${aggregate_name}" declared)
    if (declared EQUAL -1)
        message(FATAL_ERROR
            "The generator wrote ql/${aggregate_name}, which is not in QL_GENERATED_HEADERS "
            "and so is not installed")
    endif()
    file(STRINGS "${aggregate}" include_lines REGEX "^#include <ql/")
    foreach (line IN LISTS include_lines)
        string(REGEX REPLACE "^#include <ql/(.*)>$" "\\1" included "${line}")
        if (included STREQUAL "qldefines.hpp")
            continue()
        endif()
        if (included MATCHES "(^|/)all\\.hpp$")
            list(FIND installed_aggregates "${included}" declared)
            set(kind "an aggregate that is not in QL_GENERATED_HEADERS")
        else()
            list(FIND installed_headers "${included}" declared)
            set(kind "a header that is not in QL_HEADERS")
        endif()
        if (declared EQUAL -1)
            message(FATAL_ERROR
                "ql/${aggregate_name} includes ql/${included}, ${kind}, so it is not installed")
        endif()
    endforeach()
endforeach()
foreach (entry IN LISTS installed_aggregates)
    list(FIND generated_aggregates "${entry}" generated)
    if (generated EQUAL -1)
        message(FATAL_ERROR
                "QL_GENERATED_HEADERS lists ql/${entry}, which the generator does not write")
    endif()
endforeach()
